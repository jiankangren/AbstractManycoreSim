import pprint
import sys
import math
import random
import itertools
import datetime, time
import simpy
from collections import OrderedDict

## local imports
from libMappingAndScheduling.MappingPolicy import MappingPolicy
from libBuffer.Buffer import Buffer
from libProcessingElement.CPUNode_ClosedLoop_wIBuffering import CPUNode_ClosedLoop_wIBuffering
from libProcessingElement.Node import NodeStatus
from libApplicationModel.MPEG2FrameTask import MPEG2FrameTask
from libNoCModel.NoCFlowTable import NoCFlowTable
from libNoCModel.NoCFlow import NoCFlow, FlowType
from SimParams import SimParams
from AdmissionControllerOptions import AdmissionControllerOptions
from libDebug.Debug import Debug, DebugCat
from libResourceManager.Mapper.ScheduleAndMap_ClosedLoop_wIBuffering import ScheduleAndMap_ClosedLoop_wIBuffering
from libResourceManager.Mapper.ScheduleAndMap_ClosedLoop_woIBuffering import ScheduleAndMap_ClosedLoop_woIBuffering
from libResourceManager.Mapper.ScheduleAndMap_OpenLoop import ScheduleAndMap_OpenLoop
from libResourceManager.Mapper.ScheduleAndMap_OpenLoop_HEVCTile import ScheduleAndMap_OpenLoop_HEVCTile
from libResourceManager.Mapper.MapperTypes import MapperTypes
from libApplicationModel.Task import TaskStatus
from libApplicationModel.Task import TaskModel
from RuntimeApplicationInfo import RuntimeApplicationInfo, VideoStreamInfo
from libNoCModel.NoCSchedulabilityAnalysis import NoCSchedulabilityAnalysis
from libMappingAndScheduling.SemiDynamic.TaskMappingSchemesImpl import TaskMappingSchemesImpl
from libMappingAndScheduling.SemiDynamic.TaskSemiDynamicPrioritySchemesImpl import TaskSemiDynamicPrioritySchemesImpl
from libMappingAndScheduling.SemiDynamic.TaskMappingAndPriAssCombinedSchemesImpl import TaskMappingAndPriAssCombinedSchemesImpl
from libMappingAndScheduling.SemiDynamic.TaskTileMappingAndPriAssCombinedSchemes import TaskTileMappingAndPriAssCombinedSchemes
from libMappingAndScheduling.SemiDynamic.TaskTileMappingAndPriAssCombinedSchemesImpl import TaskTileMappingAndPriAssCombinedSchemesImpl
from libMappingAndScheduling.Decentralised.PSAlgorithm import PSAlgorithm
from libMappingAndScheduling.Decentralised.PSAlgorithmViewer import PSAlgorithmViewer
from libMappingAndScheduling.Decentralised.CastilhosClusterProtocol import CastilhosClusterProtocol



from MMC import MMC




class RunTimeTaskManager_ClosedLoop_wIBuffering:
    
    def __init__(self, env, polling_delay, mapping_policy, 
                 node_network, input_buffers, output_buffer, 
                 interconnect,
                 task_dispatcher, run_simpy_process=True):        
        self.env = env        
        self.polling_delay = polling_delay        
        self.mapping_policy = mapping_policy
        self.label = "ResourceManager_ClosedLoop_wIBuffering::"
        self.status = RMStatus.RM_SLEEPING
        
        self.initrandom_seed = None
        
        # runtime taskmanager needs to have a view of the system resources      
        self.node_network = node_network
        self.input_buffers = input_buffers
        self.output_buffer = output_buffer
        self.interconnect = interconnect
        self.task_dispatcher = task_dispatcher
        self.mmc = MMC(self.env, SimParams.MMC_CONTROLLER_LOCATIONS, 
                       self.node_network, self.interconnect, 
                       SimParams.NOC_H, SimParams.NOC_W, self)
        
        # tracking video stream info
        self.video_streams = {}
        
        # also need to keep track of the task-to-node mapping
        # all the nodes will also have this table
        self.task_mapping_table = {}    # {key : {data}}
        self.node_to_task_mapped_count = {k: 0 for k in range(SimParams.NUM_NODES)}
        self.vidstream_frames_mapping_table = {}   # static mapping table for frames, upon start of stream        
        self.volatile_task_mapping_table = {
                                            # items from this task mapping table can be removed
                                            'runtime_task_mapping': {}, 
                                            # keeps track of amount of execution time allocated to specific nodes
                                            'node_usage_field' : {nid: 0 for nid in xrange(SimParams.NOC_H*SimParams.NOC_W)} 
                                            }   
        self.volatile_task_mapping_table_lastrefreshed=self.env.now
        
        # table to store noc traffic - temporarily
        self.volatile_noc_traffic_table = {} # linkid : flw details
                 
        # this table keeps track of the computation cost of the completed video streams
        # this gets updated when a task complete msg is received
        self.completed_task_monitoring_info = {}
                
        # slack reclaimation table - all slacks amounts for completed tasks will get stored here
        self.slack_reclaim_table = {}
        
        self.max_tasks = None   # maximum num of tasks in simulation run    
        self.last_scheduled_task_time = None    # what time is the last task scheduled at    
        self.last_scheduled_video_stream = None
                
        # semaphore for the mapping table
        self.mutex_tmtbl = simpy.Container(self.env, capacity=1, init=0)
        
        # this does the mapping and scheduling functionality
        self.Mapper =   self.getMapperClass(env, self)
        
        ## flow table - contains all the flows related to the tasks
        self.flow_table = NoCFlowTable(self.env, self, self.Mapper, self.node_network)
        self.flow_priority_offset = None
        
        # this is used to maintain the runtime applications
        self.RunTimeApps = RuntimeApplicationInfo(env, self)        
        
        # used for schedulability tests
        self.NoCSchedulabilityAnalyser = NoCSchedulabilityAnalysis(self.env, self.RunTimeApps, self)        
        
        # selection of the mapping and priority assignment schemes
        self.taskPreMapper =   TaskMappingSchemesImpl(self.env, self)
        self.taskPriAssigner =   TaskSemiDynamicPrioritySchemesImpl(self.env, self) 
        self.taskMapperAndPriAssignerCombo = TaskMappingAndPriAssCombinedSchemesImpl(self.env, self)       
        self.taskTileMapperAndPriAssignerCombo = TaskTileMappingAndPriAssCombinedSchemesImpl(self.env, self) # used when hevc tile level task splitting
        
        # pheromone-signalling algorithm implementation
        self.PSAlgo = PSAlgorithm(env, self)
        #self.PSAlgo.init()
        
        # Castilhos cluster prot
        self.CCProt = CastilhosClusterProtocol(self)
        self.CCProt.constructClusters()
                
        # related to hevc
        self.total_number_of_tiles_generated = None 
        
        # used for tracking :
        self.track_taskrelease = []    
        self.track_mappingandpriass = []   
        self.track_hevc_ctus_released = {}  
        
        # Start the run process everytime an instance is created.        
        if(run_simpy_process==True):
            self.processInstance = env.process(self.run())
        
    
    def getMapperClass(self, env, rm):
        if(SimParams.SIM_ENTITY_MAPPER_CLASS == MapperTypes.OPENLOOP):
            return ScheduleAndMap_OpenLoop(env, rm)
        elif(SimParams.SIM_ENTITY_MAPPER_CLASS == MapperTypes.CLOSEDLOOP_WITH_IBUFFERING):
            return ScheduleAndMap_ClosedLoop_wIBuffering(env, rm)   
        elif(SimParams.SIM_ENTITY_MAPPER_CLASS == MapperTypes.CLOSEDLOOP_WITHOUT_IBUFFERING):
            return ScheduleAndMap_ClosedLoop_woIBuffering(env, rm)    
        elif (SimParams.SIM_ENTITY_MAPPER_CLASS == MapperTypes.OPENLOOP_WITH_HEVCTILE):            
            return ScheduleAndMap_OpenLoop_HEVCTile(env, rm)
        
            
        else:
            sys.exit('getMapperClass::error')
    
        
    ##########################################################################################################################
    ## Getters/Setters
    ##########################################################################################################################
    
    ## getters
    def get_processInstance(self):
        return self.processInstance    
    def get_maxTasks(self):
        return self.max_tasks
    def get_lastscheduledtask_time(self):
        return self.last_scheduled_task_time
    def get_initrandomseed(self):
        return self.initrandom_seed    
    def get_volatile_task_mapping_table(self):
        return self.volatile_task_mapping_table
    def get_total_number_of_tiles_generated(self):
        return self.total_number_of_tiles_generated
    
    ## setters
    def set_maxTasks(self, max_tasks):
        self.max_tasks = max_tasks
    def set_lastscheduledtask_time(self, lstt):
        self.last_scheduled_task_time = lstt
    def set_flowpriorityoffset(self, fpo):
        self.flow_priority_offset = fpo   
    def set_taskdispatcher_instance(self, td):
        self.task_dispatcher = td
    def set_lastscheduled_vs(self, lvs):
        self.last_scheduled_video_stream = lvs
        
    def set_initrandomseed(self, rs):
        self.initrandom_seed = rs
    def set_total_number_of_tiles_generated(self, ttg):
        self.total_number_of_tiles_generated = ttg
        
        
    ##########################################################################################################################
    ## Main execution loop
    ##########################################################################################################################  
    def run(self):
        
        print("%f"%self.env.now + "," + self.label + "," + ' : run starting')
        list_of_nodes_to_interrupt = []
                
        while True:
            self.status = RMStatus.RM_ACTIVE
            #print(self.label + ' : waking up and doing work at:  %f' % self.env.now)
            
            ## perform task mapping ##
            # the RM will map a block of N tasks at once (specified in SimParams)
            #if(self.mapping_policy.getNumOfFreeTaskQSlots() >= SimParams.RESOURCEMANAGER_ALLOC_NUM_TASKS):
            if(self._allInputBuffers_Empty() == False):                
                
                ### SCHEDULE and MAP : combined
                ### assign release times for all the tasks in the global input queue(s) 
                ### assign task mapping for all the tasks in the global input queue(s)
                #self.Mapper.scheduleAndMapTasks_MultiStream()
                
                self.Mapper.mapNewGoPTasks()    # take mapping selection from the stream mapping table
                
                self.lock_RM_TMtbl()
                self.Mapper.scheduleGOPStart()
                self.release_RM_TMtbl()                 
                
                #self.updateSlaveMappingTables(self.task_mapping_table)

                ## find if there is any tasks that should be released now.
                for each_inbuff_id in xrange(len(self.input_buffers)):                   
                    for (each_task_key, each_task_val) in self.input_buffers[each_inbuff_id].get_BufferItemsList().items():
                        next_task_to_map = self.input_buffers[each_inbuff_id].get_BufferItemsList()[each_task_key]
                        if(each_task_val.get_releaseTime() == self.env.now):
                            if(each_task_key in self.task_mapping_table):                        
                                node_to_map_id = self.task_mapping_table[each_task_key]['node_id']
                      
                                if(node_to_map_id != None):
                                    node_to_map = self.node_network.get_Nodes()[node_to_map_id]
                                else:
                                    print(self.label + ' : node_id is None, at: ' + str(self.env.now) )                                   
                                    sys.exit()
                                
                                if(node_to_map != None):
                                    
                                    Debug.PPrint("%f"%self.env.now + "," + self.label + "," + 'run::, : releasing task=%d, to nodeid=%d' % (each_task_key,node_to_map_id), DebugCat.DEBUG_CAT_RMINFO)
                                    
                                    # if cpu node add to it's taskq
                                    if(isinstance(node_to_map, CPUNode_ClosedLoop_wIBuffering) == True):
                                        result = node_to_map.add_Task(next_task_to_map)
                                        
                                        # track the task release
                                        self.track_taskRelease(next_task_to_map, node_to_map)
                                        
                                        if(result == False):
                                            self.showTaskMappingTable(nodeid=node_to_map.get_id())
                                            sys.exit()                                            
                                    else:
                                        print("%f"%self.env.now + "," + self.label + "," + 'run::, : Not a CPU node (node_id: '+ str(node_to_map_id)  +')')
                                        self.showTaskMappingTable()
                                        sys.exit()
                                        
                                    # remove task from input buffer
                                    self.input_buffers[each_inbuff_id].remove_Item_byKey(next_task_to_map.get_id())
                                
                                    # decrement simpy container counter                    
                                    self.InputBuffer_get(1,ibuffid=each_inbuff_id)
                                    
                                    # set the task status on the tm table
                                    self.setTaskStatus_inRM_TMTbl(next_task_to_map.get_id(), TaskStatus.TASK_DISPATCHED)
                                    
                                    # add node to the list of nodes to wake up
                                    list_of_nodes_to_interrupt = self.WakeSleepingNodesAddNode(list_of_nodes_to_interrupt, node_to_map)
                                else:
                                    Debug.PPrint("%f"%self.env.now + "," + self.label + "," + 'run::, : All nodes are BUSY!', DebugCat.DEBUG_CAT_RMINFO)
                                    #i=1
                            else:
                                print(self.label + ' ERROR: task ' + str(each_task_key) + ' not yet mapped, but ready to be released - at: '+ str(self.env.now))
                                sys.exit()
                                
                        else:
                            #print(self.label + ' : task ' + each_task_key + ' not yet ready to be released at: '+ str(self.env.now))
                            i=1                    
                    
                self.WakeSleepingNodes(list_of_nodes=list_of_nodes_to_interrupt)                
                list_of_nodes_to_interrupt = []                
                
            else:
                Debug.PPrint("%f"%self.env.now + "," + self.label + "," + 'run::, : Inputbuffers empty!', DebugCat.DEBUG_CAT_RMINFO_VERBOSE)
                
            ## go back to sleep - can be interrupted
            try:
                #pprint.pprint(self.task_mapping_table)
                #sys.exit()
                
                # find out when the closest scheduled task is at
                next_release_time = self.earliestTaskReleaseTime_In_InputBuff()
                if(next_release_time != None):
                    self.status = RMStatus.RM_SLEEPING
                    yield self.env.timeout(float(next_release_time) - float(self.env.now))
                else:
                    self.status = RMStatus.RM_SLEEPING
                    yield self.env.timeout(self.polling_delay)
            except simpy.Interrupt as interrupt: # if sleeping - now gets woken up
                self.status = RMStatus.NODE_JUSTWOKEUP
                cause = interrupt.cause
                Debug.PPrint("%.15f"%self.env.now + "," + self.label + "," + 'run::, : I got interrupted, was sleeping, cause='+cause, DebugCat.DEBUG_CAT_INTERRUPT)
                    
                    
                                
                                
                                
    ##########################################################################################################################
    ## Admission Control
    ##########################################################################################################################
    
#    def mapStreamFrames_None(self, strm_specs):
#        free_nodes_list_ascorder = self.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL)
#        if (len(free_nodes_list_ascorder) == 0):
#            return None
#        else:
#            return 1
#        
#    
#    
#    # once a stream has entered the system, the frames of the GoPs are mapped. 
#    # this mapping is fixed throughout the lifetime of the video stream
#    def mapStreamFrames_LowestTQ(self, strm_specs):
#        
#        # get list of nodes that are free 
#        free_nodes_list_ascorder = self.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL)        
#        node_and_tqlevel_dict = {}        
#        # maintain a (node, tqlevel) dict internally
#        for node in free_nodes_list_ascorder: 
#            node_and_tqlevel_dict[node.get_id()] = node.getTaskQ_level()
#        
#        
#        if(len(free_nodes_list_ascorder)>0):
#        
#            wf_id = strm_specs['wf_id']
#            strm_id = strm_specs['vid_strm_id']
#            gop_struct = strm_specs['gop_struct']        
#            frames_mapping = {}
#            
#            # find the lowest tq
#            for f_ix, each_f in enumerate(gop_struct):
#                min_tqval = min(node_and_tqlevel_dict.itervalues()) 
#                selected_node_id = [k for k, v in node_and_tqlevel_dict.iteritems() if v == min_tqval][0]
#                
#                frames_mapping[f_ix] = selected_node_id # assign
#                
#                node_and_tqlevel_dict[selected_node_id] = node_and_tqlevel_dict[selected_node_id]+1 # update dict
#            
#            if wf_id in self.vidstream_frames_mapping_table:            
#                if(strm_id not in self.vidstream_frames_mapping_table[wf_id]):
#                    self.vidstream_frames_mapping_table[wf_id][strm_id] = {}
#                    self.vidstream_frames_mapping_table[wf_id][strm_id]['frames_mapping'] = frames_mapping
#            else:
#                self.vidstream_frames_mapping_table[wf_id] = {}
#                self.vidstream_frames_mapping_table[wf_id][strm_id] = {}
#                self.vidstream_frames_mapping_table[wf_id][strm_id]['frames_mapping'] = frames_mapping
#                
#            return frames_mapping
#        else:
#            return None
#    
#    
#    # once a stream has entered the system, the frames of the GoPs are mapped. 
#    # this mapping is fixed throughout the lifetime of the video stream
#    def mapStreamFrames_Random(self, strm_specs):
#        
#        # get list of nodes that are free 
#        free_nodes_list = self.getNodes_TQNonFull()
#        
#        if(len(free_nodes_list)>0):
#        
#            wf_id = strm_specs['wf_id']
#            strm_id = strm_specs['vid_strm_id']
#            gop_struct = strm_specs['gop_struct']        
#            frames_mapping = {}
#            
#            for f_ix, each_f in enumerate(gop_struct):
#                selected_node = random.choice(free_nodes_list)
#                frames_mapping[f_ix] = selected_node.get_id()        
#            
#            if wf_id in self.vidstream_frames_mapping_table:            
#                if(strm_id not in self.vidstream_frames_mapping_table[wf_id]):
#                    self.vidstream_frames_mapping_table[wf_id][strm_id] = {}
#                    self.vidstream_frames_mapping_table[wf_id][strm_id]['frames_mapping'] = frames_mapping
#            else:
#                self.vidstream_frames_mapping_table[wf_id] = {}
#                self.vidstream_frames_mapping_table[wf_id][strm_id] = {}
#                self.vidstream_frames_mapping_table[wf_id][strm_id]['frames_mapping'] = frames_mapping
#                
#            return frames_mapping
#        else:
#            return None




        
    def _getPreMappedProcessingCore(self, wf_id, strm_id, gop_ix):
        
        try:
            node_id = self.vidstream_frames_mapping_table[wf_id][strm_id]['frames_mapping'][gop_ix]
            return node_id
        except:   
            return None
            
    
    
    # this function is called to check if a new video stream can be admitted into the system
    #    video_specs = {
    #                    "wf_id,
    #                    "frame_h" , "frame_w", "fps"
    #                    "gop_struct"         
    #                   }
    def StreamAdmission_NewVideo(self, stream_specs):
        
        self.updateEstimatedLateness()
        
        # if the respective stream buffer is full then disallow immediately
        if(self.InputBuffer_isFull(offset=SimParams.TASKDISPATCHER_BLOCK_SIZE, id=stream_specs['wf_id']) == True):
            return False
        else:
            #return True
            # check if any of the tasks in the input buffer is late
            if(self._inputBuffs_numtasks_late() > 0):
                return False
            else:
                if (self.countDroppedTasks() > 0):
                    return False
                else:
                    if(self.isJobSchedulable(stream_specs) == True):    # only for crossbar
                        if(self.VideoStreamInfo_anyStreamsLate() > 0):
                            return False
                        else:
                            return True
                    else:
                        return False
    
    
    ## admission control functions ##
    def StreamAdmission_NewVideo_ET(self, stream_specs):
        
        Debug.PPrint("%f"%self.env.now + "," + self.label + "," + 'StreamAdmission_NewVideo_ET::, : ac_test_option=' + str(SimParams.AC_TEST_OPTION), DebugCat.DEBUG_CAT_RMINFO)
              
        
        # if the respective stream buffer is full then disallow immediately
        if(self.InputBuffer_isFull(offset=SimParams.TASKDISPATCHER_BLOCK_SIZE, id=stream_specs['wf_id'], use_safe_level=True) == True):
            return False
        else:
            
            ################################
            # No admission control
            ################################
            if(SimParams.AC_TEST_OPTION == AdmissionControllerOptions.AC_OPTION_NONE):                    
                return True       
            
            
            #######################################################
            # No admission control - with schedulability analysis
            #######################################################
            elif(SimParams.AC_TEST_OPTION == AdmissionControllerOptions.AC_OPTION_NONE_WITH_SCHEDTEST): 
                # perform sched test
                self.NoCSchedulabilityAnalyser.checkSchedulability_directly_criticalPath(stream_specs)
                self.NoCSchedulabilityAnalyser.recordUtilVsSchedStats()               
                return True
            
            #######################################################
            # No admission control - with schedulability analysis
            #######################################################
            elif(SimParams.AC_TEST_OPTION == AdmissionControllerOptions.AC_OPTION_NONE_WITH_SCHEDTEST_WITHMMC): 
                # perform sched test
                self.NoCSchedulabilityAnalyser.checkSchedulability_directly_criticalPath_withMMCDataRDWR(stream_specs)
                #self.NoCSchedulabilityAnalyser.recordUtilVsSchedStats()               
                return True
            
            
            #######################################################
            # No admission control - no schedulability test
            #######################################################
            elif(SimParams.AC_TEST_OPTION == AdmissionControllerOptions.AC_OPTION_NONE_WITH_WITHMMC): 
                # perform sched test
                #self.NoCSchedulabilityAnalyser.checkSchedulability_directly_criticalPath_withMMCDataRDWR(stream_specs)
                #self.NoCSchedulabilityAnalyser.recordUtilVsSchedStats()               
                return True
            
            
            #######################################################
            # No admission control -  but schedulability test
            # performed when last vid stream is admitted
            #######################################################
            elif(SimParams.AC_TEST_OPTION == AdmissionControllerOptions.AC_OPTION_NONE_WITH_LASTVS_SCHEDTEST_WITHMMC):
                
                # if this is the last video stream then admit and perform sched-test, else just admit
                if ((stream_specs['wf_id'] == self.last_scheduled_video_stream[0]) and
                    (stream_specs['vid_strm_id'] == self.last_scheduled_video_stream[1])):
                    self.NoCSchedulabilityAnalyser.checkSchedulability_directly_criticalPath_withMMCDataRDWR(stream_specs)
                    return True
                else:                    
                    r=1
#                     pprint.pprint(stream_specs['wf_id'])
#                     pprint.pprint(stream_specs['vid_strm_id'])
#                     pprint.pprint(self.last_scheduled_video_stream[0])
#                     pprint.pprint(self.last_scheduled_video_stream[1])
                    
                    return True
            
            #####################################
            # Heuristic based test - thresholded
            #####################################
            elif(SimParams.AC_TEST_OPTION == AdmissionControllerOptions.AC_OPTION_HEURISTIC_THRESHOLDED):                 
                self.updateEstimatedLateness(lateness_ratio = SimParams.AC_TEST_IBUFF_TASK_LATENESS_RATIO)
                if(self._inputBuffs_numtasks_late() > 0):  # check if any of the tasks in the input buffer is late
                    return False
                else:
                    if (self.countDroppedTasks() > 0):  # any tasks in the other streams dropped ?
                        return False
                    else:
                        if(self.areNodesOverCapacity() == False):   # taskqs full, dep buffs full etc.
                            if(self.areNodeQueuedTasksLate(lateness_ratio = SimParams.AC_TEST_TQ_TASK_LATENESS_RATIO) == True): # any tasks in the task q already late ?
                                return False
                            else:
#                                if(self.VideoStreamInfo_anyStreamsLate() > 0): # any of the existing streams late ?
#                                    return False
#                                else:
#                                    return True
                                return True
                        else:
                            return False
            
            #########################################
            # Heuristic based test - kao_deadline_EQF
            #########################################
            elif(SimParams.AC_TEST_OPTION == AdmissionControllerOptions.AC_OPTION_HEURISTIC_KAO_DEADLINE_EQF):                 
                self.updateEstimatedLateness_KaoDeadlineCalc(ddtype = "EQF")
                if(self._inputBuffs_numtasks_late() > 0):  # check if any of the tasks in the input buffer is late
                    return False
                else:
                    if (self.countDroppedTasks() > 0):  # any tasks in the other streams dropped ?
                        return False
                    else:
                        if(self.areNodesOverCapacity() == False):   # taskqs full, dep buffs full etc.
                            if(self.areNodeQueuedTasksLate_KG(ddtype="EQF") == True): # any tasks in the task q already late ?
                                return False
                            else:
#                                if(self.VideoStreamInfo_anyStreamsLate() > 0): # any of the existing streams late ?
#                                    return False
#                                else:
#                                    return True
                                return True
                        else:
                            return False
            
            
            #########################################
            # Heuristic based test - kao_deadline_ES
            #########################################
            elif(SimParams.AC_TEST_OPTION == AdmissionControllerOptions.AC_OPTION_HEURISTIC_KAO_DEADLINE_ES):                 
                self.updateEstimatedLateness_KaoDeadlineCalc(ddtype = "ES")
                if(self._inputBuffs_numtasks_late() > 0):  # check if any of the tasks in the input buffer is late
                    return False
                else:
                    if (self.countDroppedTasks() > 0):  # any tasks in the other streams dropped ?
                        return False
                    else:
                        if(self.areNodesOverCapacity() == False):   # taskqs full, dep buffs full etc.
                            if(self.areNodeQueuedTasksLate_KG(ddtype = "ES") == True): # any tasks in the task q already late ?
                                return False
                            else:
#                                if(self.VideoStreamInfo_anyStreamsLate() > 0): # any of the existing streams late ?
#                                    return False
#                                else:
#                                    return True
                                return True
                        else:
                            return False
            
            
            
            ################################
            # Heuristic based only
            ################################
            elif(SimParams.AC_TEST_OPTION == AdmissionControllerOptions.AC_OPTION_HEURISTIC_ONLY):                 
                self.updateEstimatedLateness()
                if(self._inputBuffs_numtasks_late() > 0):  # check if any of the tasks in the input buffer is late
                    return False
                else:
                    if (self.countDroppedTasks() > 0):  # any tasks in the other streams dropped ?
                        return False
                    else:
                        if(self.areNodesOverCapacity() == False):   # taskqs full, dep buffs full etc.
                            if(self.areNodeQueuedTasksLate() == True): # any tasks in the task q already late ?
                                return False
                            else:
#                                if(self.VideoStreamInfo_anyStreamsLate() > 0): # any of the existing streams late ?
#                                    return False
#                                else:
#                                    return True
                                return True
                        else:
                            return False            
            
            
            ###################################################
            # Schedulability test based only (tasks and flows)
            ###################################################
            elif(SimParams.AC_TEST_OPTION == AdmissionControllerOptions.AC_OPTION_SCHEDTEST_ONLY):
                #return True
                #if(self.NoCSchedulabilityAnalyser.checkSchedulability_onlyDIPrecheck(stream_specs) == True): #perform the schedulability tests
                if(self.NoCSchedulabilityAnalyser.checkSchedulability(stream_specs) == True):
                    return True
                else:
                    return False
            
            ##########################################################
            # Schedulability test based only (direct to critical path)
            ##########################################################
            elif(SimParams.AC_TEST_OPTION == AdmissionControllerOptions.AC_OPTION_SCHEDTEST_DIRECT_TO_CRITICALPATH):
                #return True
                #if(self.NoCSchedulabilityAnalyser.checkSchedulability_onlyDIPrecheck(stream_specs) == True): #perform the schedulability tests
                if(self.NoCSchedulabilityAnalyser.checkSchedulability_directly_criticalPath(stream_specs) == True):
                    self.NoCSchedulabilityAnalyser.recordUtilVsSchedStats()
                    return True
                else:
                    self.NoCSchedulabilityAnalyser.recordUtilVsSchedStats()
                    return False
            
            ######################################################################
            # Schedulability test based only (direct to critical path) (with mmc)
            ######################################################################
            elif(SimParams.AC_TEST_OPTION == AdmissionControllerOptions.AC_OPTION_SCHEDTEST_DIRECT_TO_CRITICALPATH_WITHMMC):
                #return True
                #if(self.NoCSchedulabilityAnalyser.checkSchedulability_onlyDIPrecheck(stream_specs) == True): #perform the schedulability tests
                if(self.NoCSchedulabilityAnalyser.checkSchedulability_directly_criticalPath_withMMCDataRDWR(stream_specs) == True):
                    self.NoCSchedulabilityAnalyser.recordUtilVsSchedStats()
                    return True
                else:
                    self.NoCSchedulabilityAnalyser.recordUtilVsSchedStats()
                    return False
            
            ###################################################
            # Schedulability test based only (tasks only)
            ###################################################
            elif(SimParams.AC_TEST_OPTION == AdmissionControllerOptions.AC_OPTION_SCHEDTEST_TASKSONLY_ONLY):
                #return True
                if(self.NoCSchedulabilityAnalyser.checkSchedulability_onlyDIPrecheck_OnlyCompCost(stream_specs) == True): #perform the schedulability tests
                    return True
                else:
                    return False
            
            #########################################
            # Hybrid Heuristic + Schedulability - v1
            #########################################
            elif(SimParams.AC_TEST_OPTION == AdmissionControllerOptions.AC_OPTION_HYB_HEU_SCHD_V1):
                self.updateEstimatedLateness()
                if(self._inputBuffs_numtasks_late() > 0): # check if any of the tasks in the input buffer is late
                    return False
                else:
                    if (self.countDroppedTasks() > 0):  # any tasks in the other streams dropped ?
                        return False
                    else:
                        if(self.areNodesOverCapacity() == False):   # taskqs full, dep buffs full etc.
                            if(self.areNodeQueuedTasksLate() == True): # any tasks in the task q already late ?
                                return False
                            else:
#                                if(self.VideoStreamInfo_anyStreamsLate() > 0): # any of the existing streams late ?
#                                    return False
#                                else:                                    
                                if(self.NoCSchedulabilityAnalyser.checkSchedulability_onlyDIPrecheck(stream_specs) == True): #perform the schedulability tests
                                    return True
                                else:
                                    return False
                        else:
                            return False
            
            
            #########################################
            # Hybrid Schedulability + Heuristic - v2
            #########################################
            elif(SimParams.AC_TEST_OPTION == AdmissionControllerOptions.AC_OPTION_HYB_HEU_SCHD_V2):
                self.updateEstimatedLateness()
                if(self.NoCSchedulabilityAnalyser.checkSchedulability(stream_specs) == True): #perform the schedulability tests
                    return True
                else:
                    
                    if(self._inputBuffs_numtasks_late() > 0):  # check if any of the tasks in the input buffer is late
                        return False
                    else:
                        if (self.countDroppedTasks() > 0):  # any tasks in the other streams dropped ?
                            return False
                        else:
                            if(self.areNodesOverCapacity() == False):   # taskqs full, dep buffs full etc.
                                if(self.areNodeQueuedTasksLate() == True): # any tasks in the task q already late ?
                                    return False
                                else:
    #                                if(self.VideoStreamInfo_anyStreamsLate() > 0): # any of the existing streams late ?
    #                                    return False
    #                                else:
    #                                    return True
                                    return True
                            else:
                                return False
            
            
            
            
            else:
                sys.exit("StreamAdmission_NewVideo_ET:: error - undefined admission test")
    
    
    
    def isLastVS(self, stream_specs):
        i=1
    
    
    # list of tasks that couldn't be taken in, because buffer was full or other reasons
    # called by the task-dispatcher
    def addDroppedTask(self, tasks, wf_id):
        
        for each_task in tasks:        
            if(wf_id in self.video_streams):            
                if(each_task.get_video_stream_id() in self.video_streams[wf_id]):                    
                    if('dropped_task_ids' in self.video_streams[wf_id][each_task.get_video_stream_id()]):
                        self.video_streams[wf_id][each_task.get_video_stream_id()]['dropped_task_ids'].append(each_task.get_id())
                    else:                        
                        self.video_streams[wf_id][each_task.get_video_stream_id()] = {
                                                                                      'dropped_task_ids' : [each_task.get_id()]
                                                                                      }
                        
                else:
                    self.video_streams[wf_id][each_task.get_video_stream_id()] = {}
                    self.video_streams[wf_id][each_task.get_video_stream_id()] = {
                                                                                 'dropped_task_ids' : [each_task.get_id()]
                                                                                 }
            else:
                self.video_streams[wf_id] = {}
                self.video_streams[wf_id][each_task.get_video_stream_id()] = {}
                self.video_streams[wf_id][each_task.get_video_stream_id()] = {
                                                                             'dropped_task_ids' : [each_task.get_id()]
                                                                             }
    
    
    # how many tasks have been dropped in the current video stream in specified workflow
    def countDroppedTasks(self, wf_id=None):
        if wf_id != None:
            if(self.input_buffers[wf_id].isEmpty() == False):
                current_video_stream_id = self.input_buffers[wf_id].get_BufferItemsList().items()[0].get_video_stream_id()            
                if(current_video_stream_id in self.video_streams[wf_id]):
                    return len(self.video_streams[wf_id][current_video_stream_id]['dropped_task_ids'])
                else:
                    return 0            
            else:            
                return 0     
        else:   # find any dropped tasks in currently decoding streams
            count = 0            
            for each_wf_id in xrange(len(self.input_buffers)):
                if(self.input_buffers[each_wf_id].isEmpty() == False):
                    # find currently decoding video stream id
                    top_task_in_buffer = self.input_buffers[each_wf_id].get_BufferItemsList().items()[0][1]
                    current_video_stream_id = top_task_in_buffer.get_video_stream_id()            
                    if (each_wf_id in self.video_streams):
                        if(current_video_stream_id in self.video_streams[each_wf_id]):
                            if('dropped_task_ids' in self.video_streams[each_wf_id][current_video_stream_id]):
                                count += len(self.video_streams[each_wf_id][current_video_stream_id]['dropped_task_ids'])        
                        
            return count 
    
    def totalDroppedTasks(self):
        count = 0
        for wf_id, wf_val in self.video_streams.iteritems():          
            for vs_id, vs_val in enumerate(wf_val):                
                if('dropped_task_ids' in self.video_streams[wf_id][vs_val]):
                    count += len(self.video_streams[wf_id][vs_val]['dropped_task_ids'])
        
        return count
        
    
    # are any of the nodes over capacity ? i.e. dep-buff are full, task-q full etc.
    def areNodesOverCapacity(self):
        for each_node in self.node_network.get_Nodes():
            if(each_node.dependencyBuff_getLevel() >= SimParams.CPUNODE_DEPENDANCY_BUFF_SAFE_LEVEL) or \
            (each_node.getTaskQ_level() >= SimParams.CPUNODE_TASKQ_SAFE_LEVEL):
                return True            
        
        return False
    
    def numTasksInCPUTaskQs(self):
        count = []
        
        for each_node in self.node_network.get_Nodes():
            count.append(each_node.getTaskQ_level())
        
        return count
    
    def getNodeTQWCUtils(self):
        node_wcutils = {}
        for each_node in self.node_network.get_Nodes():
            node_wcutils[each_node.get_id()] = each_node.get_TQWorstCaseUtilisation()
        
        return node_wcutils  
        
        
            
    
    def areNodeQueuedTasksLate(self, lateness_ratio = 1.0):
        for each_node in self.node_network.get_Nodes():        
            if(each_node.numLateTasksInTQ(lateness_ratio = lateness_ratio) > 0):
                return True
        
        return False
        
    
    def areNodeQueuedTasksLate_KG(self, ddtype= "EQF"):
        for each_node in self.node_network.get_Nodes():        
            if(each_node.numLateTasksInTQ_KG(ddtype = ddtype) > 0):
                return True
        
        return False
    
    
        
                       
                
    # estimated waiting time (till release of GOP first I-frame) of new video stream   
    # based on which node is available to earliest , based on the task mapping table
    def nextAvailableReleaseTimeSlot(self):
        
        (next_free_node, next_free_node_time) = self.Mapper._findFirstFreeFromNodeList()
        
        return next_free_node_time
    
    # will the gop miss it's end-to-end deadline if admitted ?
    # very primitive version
    def isJobSchedulable(self, stream_specs):
        
        best_release_time = self.nextAvailableReleaseTimeSlot()        
        time_now = self.env.now        
        job_end_to_end_rel_deadline =  float(len(stream_specs['gop_struct']))/float(stream_specs['fps'])
        
        if ((best_release_time - time_now) > job_end_to_end_rel_deadline):
            return False
        else:
            # calculate worst-case response time
            # -- assume communication latency incured for all tasks (i.e. assume mapped on different cores)
            # -- assume having parallelism (therefore use critical path)
            wcc_I = stream_specs['wcc_I']
            wcc_P = stream_specs['wcc_P']
            wcc_B = stream_specs['wcc_B']            
            
            # find computation cost (on the critical path)
            comp_cost = 0.0
            for each_task_type in SimParams.GOP_CRITICAL_PATH:
                if each_task_type == "I":
                    comp_cost += float(wcc_I)
                elif each_task_type == "P":
                    comp_cost += float(wcc_P)
                elif each_task_type == "B":
                    comp_cost += float(wcc_B)
                     
            basic_latency = self.interconnect.getRouteCost(None, None, stream_specs['decoded_frame_size'])
            #comms_latency = float(len(stream_specs['gop_struct'])-1) * basic_latency              
            comms_latency = 7.0 * basic_latency
        
            est_job_wc_resp_time = comp_cost + comms_latency
            
            if (est_job_wc_resp_time > job_end_to_end_rel_deadline):
                return False
            else:
                return True
    
    
    
    def UpdateVideoStreamInfo_taskCompleted(self,task):       
        
        wf_id = task.get_wfid()
        videostream_id = task.get_video_stream_id()
        gop_id = task.get_parentGopId()
        
        # add task to structure
        task_info = {
                     'id' : task.get_id(),
                     'dt' :  task.get_dispatchTime(),
                     'ct' :  task.get_taskCompleteTime(),
                     }
        
        if(wf_id in self.video_streams):
            if(videostream_id in self.video_streams[wf_id]):
                if(gop_id in self.video_streams[wf_id][videostream_id]):
                    self.video_streams[wf_id][videostream_id][gop_id]['completed_tasks'].append(task_info)
                else:
                    self.video_streams[wf_id][videostream_id][gop_id] = {}
                    self.video_streams[wf_id][videostream_id][gop_id]['completed_tasks'] = [task_info]
            else:
                self.video_streams[wf_id][videostream_id] = {}
                self.video_streams[wf_id][videostream_id][gop_id] = {}
                self.video_streams[wf_id][videostream_id][gop_id]['completed_tasks'] = [task_info]    
        else:
            self.video_streams[wf_id] = {}
            self.video_streams[wf_id][videostream_id] = {}
            self.video_streams[wf_id][videostream_id][gop_id] = {}
            self.video_streams[wf_id][videostream_id][gop_id]['completed_tasks'] = [task_info]
        
        # measure gop-lateness
        dispatch_times = []
        completed_times = []
        if(task.get_frameIXinGOP() == len(task.get_gopstructure())-1):
            
            gop_end_to_end_deadline = float(len(task.get_gopstructure()))/float(task.get_framerate())
            
            for each_task in self.video_streams[wf_id][videostream_id][gop_id]['completed_tasks']:
                dispatch_times.append(each_task['dt'])
                completed_times.append(each_task['ct'])
                
            gop_lateness =  max(completed_times) - (min(dispatch_times) + gop_end_to_end_deadline)  
            self.video_streams[wf_id][videostream_id][gop_id]['gop_lateness'] = gop_lateness
        
    
    # have any of the currently running video streams' gops missed their deadline
    def VideoStreamInfo_anyStreamsLate(self):
        count = 0            
        for each_wf_id in xrange(len(self.input_buffers)):
            if(self.input_buffers[each_wf_id].isEmpty() == False):
                # find currently decoding video stream id
                top_task_in_buffer = self.input_buffers[each_wf_id].get_BufferItemsList().items()[0][1]
                current_video_stream_id = top_task_in_buffer.get_video_stream_id()            
                if (each_wf_id in self.video_streams):
                    if(current_video_stream_id in self.video_streams[each_wf_id]):
                        
                        for each_completed_gop_id in self.video_streams[each_wf_id][current_video_stream_id]:
                            if ('gop_lateness' in self.video_streams[each_wf_id][current_video_stream_id][each_completed_gop_id]):
                                if(self.video_streams[each_wf_id][current_video_stream_id][each_completed_gop_id]['gop_lateness'] > 0):
                                    count += 1                   
                    
        return count      
     
    
    def getNodes_TQNonFull(self, safe_level = SimParams.CPUNODE_TASKQ_SIZE):
        nodes_list = []
        for each_node in self.node_network.get_Nodes():            
            if(each_node.getTaskQ_level() < safe_level):
                nodes_list.append(each_node)
                
        return nodes_list
        
    def getNodes_TQAscendingOrder(self):
        
        nodes_list = []
        for each_node in self.node_network.get_Nodes():            
            if(each_node.getTaskQ_level() < SimParams.CPUNODE_TASKQ_SIZE):
                nodes_list.append(each_node)
                
        if( len(nodes_list) > 0):
            # sort free nodes list according to their TQ level (ascending)
            sorted_node_list = sorted(nodes_list, key=lambda x: x.each_node.getTaskQ_level(), reverse=False)    
            
            return sorted_node_list
                
        else:
            return []
            
    def getNode_viaNodeID(self, node_id):
        node = self.node_network.get_Nodes()[node_id]
        return node
            
        
               
            
    ##########################################################################################################################
    ## Dealing with the slack reclaim table 
    ##########################################################################################################################
    
    # add a new completed task to the slack reclaim table
    def addToSlackReclaimTable(self, finished_task_id, mapped_node_id, finished_task_time):
        
        original_release_time = 0.0
        original_wcc = 0.0
        original_node_id = 0
        
        for (task_id,val) in self.task_mapping_table.iteritems():
            if(finished_task_id == task_id):
                original_release_time = val['release_time']
                original_wcc = val['wcc']
                original_node_id = val['node_id']
                break;
        
        # check for same node ?
        if(original_node_id != mapped_node_id):
            print(self.label + ' : addToSlackReclaimTable: incorrect Node_ID! (%d, %d), at : %f' % (mapped_node_id, original_node_id, self.env.now))
            sys.exit()        
        
        slack = (original_release_time + original_wcc) - finished_task_time
        
        if(slack == 0):
            return False            
        if(slack < 0):
            print(self.label + ' : addToSlackReclaimTable: negative slack! , at : %f' % (self.env.now))
            sys.exit()
            
        entry = {
                 'task_id' : finished_task_id,
                 'node_id' : mapped_node_id,
                 'actual_completed_time' : finished_task_time,
                 'original_release_time' : original_release_time,
                 'original_wcc' : original_wcc,
                 'slack' : slack,
                 'reclaimed' : False                 
                 }        
        self.slack_reclaim_table[finished_task_id] = entry
        
        return True
    
    
    # adjust the input buffer and task-mapping tables, based on reclaimed slack
    # finished task : Ti
    # (1) get Ti's children (i.e. who needs Ti ?)
    # (2) try to bring fwd all Ti's children 
    # (3) try to bring fwd task in front of Ti, mapped on same node
    def reclaimSlack(self, finished_task):
        
        did_task_mapping_table_change = False
        
        # get slack-reclaim-table-entry
        srt_entry = self.slack_reclaim_table[finished_task.get_id()]        
        
        # (1) get Ti's children
        #Ti_children = finished_task.get_which_tasks_needs_me()
        Ti_children = finished_task.get_my_closest_children()
        Ti_children.sort()        
        
        # (2) try to bring fwd Ti's children
        if (len(Ti_children) > 0): # not a B-frame
            for each_child_task_id in Ti_children:
                if(each_child_task_id in self.task_mapping_table):
                    if(self._canChildTaskBeBroughtFwdByXticks(each_child_task_id, finished_task.get_id(), srt_entry['slack']) == True):
                       
#                        if(each_child_task_id == 218):
#                            print str(each_child_task_id)
#                            print str(finished_task.get_id())
#                            pprint.pprint(Ti_children)
#                            print '1prev_rel_time' + str(self.task_mapping_table[each_child_task_id]['release_time'])
                        
                        final_release_time = self.task_mapping_table[each_child_task_id]['release_time'] - srt_entry['slack']
                        
                        # update mapping table
                        if(final_release_time > self.env.now):
                            self.task_mapping_table[each_child_task_id]['release_time'] = final_release_time
                        else:
                            final_release_time = final_release_time + 0.0001 
                            self.task_mapping_table[each_child_task_id]['release_time'] = final_release_time 
#                        
#                        if(each_child_task_id == 218):
#                            print str(each_child_task_id)
#                            print '1now_rel_time' + str(self.task_mapping_table[each_child_task_id]['release_time'])
#                            print("" + ' : time now = %f' % (self.env.now))
                       
                        #update input buffer
                        for each_ibuff_id in xrange(len(self.input_buffers)):
                            if(each_child_task_id in self.input_buffers[each_ibuff_id].get_BufferItemsList()):
                                self.input_buffers[each_ibuff_id].get_BufferItemsList()[each_child_task_id].set_releaseTime(final_release_time)
                                break
                        
                        did_task_mapping_table_change = True
                        
        # (3) try to bring fwd task in front of Ti, mapped on same node
        (result, task_infront_id) = self._canTaskInFrontBeBroughtFwdByXticks(srt_entry, srt_entry['node_id'], srt_entry['slack'])
        if(result == True):                 
            if(task_infront_id not in Ti_children): 
                               
#                if(task_infront_id == 218):
#                    #print str(task_infront_id)
#                    pprint.pprint(Ti_children)
#                    print task_infront_id
#                    print str(finished_task.get_id())
#                    print '2prev_rel_time' + str(self.task_mapping_table[task_infront_id]['release_time'])
                                      
                final_release_time = self.task_mapping_table[task_infront_id]['release_time'] - srt_entry['slack']
                
                # update mapping table
                if(final_release_time > self.env.now):
                    self.task_mapping_table[task_infront_id]['release_time'] = final_release_time
                else:
                    final_release_time = final_release_time + 0.0001 
                    self.task_mapping_table[task_infront_id]['release_time'] = final_release_time 
               
#                if(task_infront_id == 218):
#                    print str(task_infront_id)
#                    print '2now_rel_time' + str(self.task_mapping_table[task_infront_id]['release_time'])
#                    print("" + ' : time now = %f' % (self.env.now))
                
                #update input buffer
                for each_ibuff_id in xrange(len(self.input_buffers)):
                    if(task_infront_id in self.input_buffers[each_ibuff_id].get_BufferItemsList()):
                        self.input_buffers[each_ibuff_id].get_BufferItemsList()[task_infront_id].set_releaseTime(final_release_time)
                        break                                   
                
                did_task_mapping_table_change = True
        
        
        if(did_task_mapping_table_change == True):
            next_release_time = self.earliestTaskReleaseTime_In_InputBuff()            
            return (True, next_release_time)
        else:
            return (False, None)
                   
    
    # used to see if the task in front can be brought fwd by xticks
    def _canTaskInFrontBeBroughtFwdByXticks(self, srt_entry, node_id, xticks):
        
        tt_id = srt_entry['task_id']
        tt_release_time = srt_entry['original_release_time']       
        
        if(tt_id in self.task_mapping_table):
            
            ## find task in front
            tasks_infront_target_task__tid = []
            tasks_infront_target_task__rtime = []
            for (tid,val) in self.task_mapping_table.iteritems():
                if(val['node_id'] == node_id):
                    if(val['release_time'] > tt_release_time):
                        tasks_infront_target_task__tid.append(tid)
                        tasks_infront_target_task__rtime.append(val['release_time'])
            
            # if no tasks in front then return false
            if(len(tasks_infront_target_task__rtime)==0):
                return (False, None)            
            
            index = tasks_infront_target_task__rtime.index(min(tasks_infront_target_task__rtime))
            task_directly_infront_tt_id = tasks_infront_target_task__tid[index]
            
            ## find if this task can be brought fwd, based on it's dependencies            
            for each_ibuff_id in xrange(len(self.input_buffers)):
                if(task_directly_infront_tt_id in self.input_buffers[each_ibuff_id].get_BufferItemsList()):
                    Ti = self.input_buffers[each_ibuff_id].get_BufferItemsList()[task_directly_infront_tt_id]
                    break
            
            # find max dep-parent
            if (len(Ti.get_dependencies()) > 0):
                Ti_dep_max = max(Ti.get_dependencies())
            else:
                Ti_dep_max = None
            
#            if(task_directly_infront_tt_id == 218):
#                print "--"
#                print "front " + str(task_directly_infront_tt_id)
#                print Ti_dep_max
#                print (Ti_dep_max in self.task_mapping_table)
#                print "--"
                
            if(Ti_dep_max != None):
                
                # for now use the child task size , later we need to modify this to be the parent task size !!
                num_flits = math.ceil(Ti.get_completedTaskSize()/SimParams.NOC_FLIT_BYTES)        
                num_hops = 1        
                
                # old version
                #cost = ((num_hops * SimParams.NOC_ARBITRATION_COST) + num_flits) * SimParams.NOC_PERIOD
                
                routers = num_hops
                cost = (float(num_hops) * SimParams.NOC_PERIOD) + \
                        (float(routers) * SimParams.NOC_ARBITRATION_COST) + \
                        (float(num_flits) * SimParams.NOC_PERIOD)                
                
                # search task_mapping table
                if(Ti_dep_max in self.task_mapping_table):
                    
                    # check if dep is in another node
                    if(self.task_mapping_table[Ti_dep_max]['node_id'] != self.task_mapping_table[task_directly_infront_tt_id]['node_id']):
                        
                        Te = self.task_mapping_table[Ti_dep_max]['release_time'] + self.task_mapping_table[Ti_dep_max]['wcc'] + cost                    
                        max_gap = Te - self.task_mapping_table[task_directly_infront_tt_id]['release_time']
                    else:
                        Te = self.task_mapping_table[Ti_dep_max]['release_time'] + self.task_mapping_table[Ti_dep_max]['wcc'] + 0                    
                        max_gap = Te - self.task_mapping_table[task_directly_infront_tt_id]['release_time']
                    
                    if(max_gap > xticks):
                        return (True, task_directly_infront_tt_id)
                    else:
                        return (False, None)
                    
                else:
                    # no task dep max in mapping table, so probably has finished
                    # but need to check if it's on it's way to another node - transmission time !??
                    
                    # check for transmission time in slack-table
                    if(Ti_dep_max in self.slack_reclaim_table):
                        if(self.slack_reclaim_table[Ti_dep_max]['node_id'] == self.task_mapping_table[task_directly_infront_tt_id]['node_id']):
                            return (True, task_directly_infront_tt_id)
                        else:
                                                
                            max_gap = cost
                        
                            if(max_gap < xticks):
                                return (True, task_directly_infront_tt_id)
                            else:
                                return (False, None)      
                    else:   # assume we have to account for transmission - being safe !!
                        max_gap = cost
                        
                        if(max_gap < xticks):
                            return (True, task_directly_infront_tt_id)
                        else:
                            return (False, None)
                    
            else: # no dependancies ? then it must be an I-frame, hence check if the task_id-1's finish time
                return (True, task_directly_infront_tt_id)
        else:
            return (False, None)
                
    
    # used to check if dependent tasks can be brought fwd
    def _canChildTaskBeBroughtFwdByXticks(self, target_task_id, finished_task_id, x_ticks):
        
        # find target_tasks, release time and mapped_node
        tt_release_time = 0.0
        tt_mapped_node = 0
        
        for (tid,val) in self.task_mapping_table.iteritems():
            if(tid == target_task_id):
                tt_release_time = val['release_time']
                tt_mapped_node = val['node_id']
                break
                
        # get list of all tasks mapped onto tt_mapped_node and whose release time is before tt_release_time
        tasks_behind_target_task__tid = []
        tasks_behind_target_task__rtime = []        
        for (tid,val) in self.task_mapping_table.iteritems():
            if(val['node_id'] == tt_mapped_node):
                if(val['release_time'] < tt_release_time):
                    tasks_behind_target_task__tid.append(tid)
                    tasks_behind_target_task__rtime.append(val['release_time'])                    
        
        if(len(tasks_behind_target_task__rtime) > 0):
        
            index = tasks_behind_target_task__rtime.index(max(tasks_behind_target_task__rtime))
            task_directly_behind_tt_id = tasks_behind_target_task__tid[index]
            
            # is this task the target_task
            if(task_directly_behind_tt_id == finished_task_id):
                return True
            else:
            
                diff_delta =  self.task_mapping_table[target_task_id]['release_time'] - \
                                (self.task_mapping_table[task_directly_behind_tt_id]['release_time'] + \
                                 self.task_mapping_table[task_directly_behind_tt_id]['wcc'])
                                
                if(diff_delta < x_ticks):
                    return False
                else:
                    return True
        else:
            return True
    
    
    ##########################################################################################################################
    ## Dealing with the task-mapping table
    ##########################################################################################################################
    
    # find node with least mapped tasks
    def getTaskMappingTable_MostFree(self):
        
        node_to_task_freq = []
        node_to_task_list = []
        
        # basically build a reverse - mapping_table        
        for each_node_id in range(SimParams.NUM_NODES):
            count = 0
            temp_list = []            
            for (task_id,val) in self.task_mapping_table.iteritems():
                if(val['node_id'] == each_node_id):
                    count += 1
                    temp_list.append(task_id)
            
            node_to_task_freq.append(count)
            node_to_task_list.append(temp_list)
            
        min_node_id = node_to_task_freq.index(min(node_to_task_freq))
        
        # find when the above node will be available next
        largest_task_id = max(node_to_task_list[min_node_id])
        
        next_available_time = self.input_buffers[0].get_BufferItemsList()[largest_task_id].get_releaseTime() + \
                            self.input_buffers[0].get_BufferItemsList()[largest_task_id].get_worstCaseComputationCost()
        
        return (min_node_id, next_available_time)
           
    
    # find the next available time of the specified node
    def getNode_NextAvailable(self, nid):
        
        node_to_task_list = []  
        for (task_id,val) in self.task_mapping_table.iteritems():
            if(val['node_id'] == nid):
                node_to_task_list.append(task_id)
                
        # find when the above node will be available next
        largest_task_id = max(node_to_task_list)
        
        next_available_time = self.input_buffers[0].get_BufferItemsList()[largest_task_id].get_releaseTime() + \
                            self.input_buffers[0].get_BufferItemsList()[largest_task_id].get_worstCaseComputationCost()
                            
        return next_available_time
                            
    
    # updates local table AND the slave tables
    def updateMappingTables(self, task_id, node_id):
        # local table
        entry = {
                 'node_id' : node_id,
                 'release_time' : None
                 }
        self.task_mapping_table[task_id] = entry      
        # slave tables
        #self.updateSlaveMappingTables(self.task_mapping_table)
        
    def updateSlaveMappingTables(self, master_mapping_table):        
        # slave tables
        for each_node in self.node_network.get_Nodes():
            each_node.updateMappingTable(master_mapping_table)
            
            
    def removeMapppingTableEntry(self, task_id):
        del self.task_mapping_table[task_id]
        
        #self.updateSlaveMappingTables(self.task_mapping_table)
    
    # set the tasks status in RM's Task mapping table
    def setTaskStatus_inRM_TMTbl(self, task_id, task_status):
        self.lock_RM_TMtbl()
        if(task_id in self.task_mapping_table):
            self.task_mapping_table[task_id]['status'] = task_status       
        self.release_RM_TMtbl()
            
    ##########################################################################################################################
    ## Manipulating the global input buffer
    ##########################################################################################################################
        
    def InputBuffer_isFull(self, offset=0, id=0, use_safe_level=False):
        
        if(use_safe_level == True):
            return (self.input_buffers[id].simpy_container_instance.level >= (self.input_buffers[id].safe_level - offset))            
        else:        
            return (self.input_buffers[id].simpy_container_instance.level >= (self.input_buffers[id].simpy_container_instance.capacity - offset))
    
        
    def InputBuffer_get(self,n, ibuffid=0):
        self.input_buffers[ibuffid].simpy_container_instance.get(n)
        
    # are all input buffers empty ?
    def _allInputBuffers_Empty(self):
        result = True
        for each_ibuff in self.input_buffers:
            if not each_ibuff.isEmpty():
                result = False
                break
        return result
     
    
#     def _allInputBuffer_hasLastTaskDispatched(self):
#         
#         if(self.get_lastscheduledtask_time() > self.env.now):
#             return True
#         else:
#             return False
#         
    
    
    
    def _printIbuffContents(self):
        result = True
        for each_ibuff in self.input_buffers:
            if(each_ibuff.isEmpty() == False):
                result = False
                pprint.pprint(each_ibuff.get_BufferItemsList())
                break
            
        return result 
    
    
    # based on time_now : i.e. closest time when compared to NOW                    
        
    def earliestTaskReleaseTime_In_InputBuff(self):
        reltime_list = []
        if(self._allInputBuffers_Empty() == False):       
            for each_ibuff_id in xrange(len(self.input_buffers)):
                
                for (each_task_key, each_task_val) in self.input_buffers[each_ibuff_id].get_BufferItemsList().items():
                    
                    #pprint.pprint(each_task_val.get_releaseTime())
                    if(each_task_val.get_releaseTime() > self.env.now):            
                        reltime_list.append(each_task_val.get_releaseTime())                            
            
            if(len(reltime_list) > 0):
                return min(reltime_list)
            else:
                return None
        else:
            return None          
    
    
    ## update estimated lateness in all tasks in the input buffers
    def updateEstimatedLateness_KaoDeadlineCalc(self, ddtype = "EQF"):
        for each_ibuff_id in xrange(len(self.input_buffers)):
            for (each_task_key, each_task_val) in self.input_buffers[each_ibuff_id].get_BufferItemsList().items():
                
                current_time = self.env.now
                #dispatched_time = each_task_val.get_dispatchTime()
                
                if(ddtype == "EQF"):
                    absolute_deadline = each_task_val.getEstimatedDeadline_EQF()
                elif(ddtype == "ES"):
                    absolute_deadline = each_task_val.getEstimatedDeadline_ES()
                else:
                    sys.exit("updateEstimatedLateness_KaoDeadlineCalc - unknown ddtype")
                
                #print "absolute_deadline = " + str(absolute_deadline)
                
                estimated_lateness = float(current_time - absolute_deadline)     # positive lateness is bad !
                
                #each_task_val.set_estimatedLateness(estimated_lateness)
                self.input_buffers[each_ibuff_id].get_BufferItemsList()[each_task_key].set_estimatedLateness(estimated_lateness)
    
    
    ## update estimated lateness in all tasks in the input buffers
    def updateEstimatedLateness(self, lateness_ratio = 1.0):
        for each_ibuff_id in xrange(len(self.input_buffers)):
            for (each_task_key, each_task_val) in self.input_buffers[each_ibuff_id].get_BufferItemsList().items():
                
                current_time = self.env.now
                dispatched_time = each_task_val.get_dispatchTime()
                #end_to_end_deadline = float(len(each_task_val.get_gopstructure())) * float((1.0/each_task_val.get_framerate()))
                end_to_end_deadline = each_task_val.get_end_to_end_deadline()
                
                if(lateness_ratio == None):
                    lateness_threshold = 1.0
                
                estimated_lateness = float((current_time - dispatched_time)) - float(lateness_ratio * end_to_end_deadline)
                
                #each_task_val.set_estimatedLateness(estimated_lateness)
                self.input_buffers[each_ibuff_id].get_BufferItemsList()[each_task_key].set_estimatedLateness(estimated_lateness)
     
    def _inputBuffs_numtasks_late(self):
        
        count = 0
        
        for each_ibuff_id in xrange(len(self.input_buffers)):
            for (each_task_key, each_task_val) in self.input_buffers[each_ibuff_id].get_BufferItemsList().items():
                lateness = each_task_val.get_estimatedLateness()
                
                if(lateness > 0.0):
                    count+=1
                    
        return count
        
            
    
    
    
    #######################################
    ## Interact with processing nodes
    #######################################
    # this is a callback - called when mmc->node flow has completed
    def putTaskToNodeTQ(self, completed_flow):        
        #print "putTaskToNodeTQ::Enter"        
        node = completed_flow.get_payload_metadata()['mapped_node']
        task = completed_flow.get_payload_metadata()['target_task']
        ibuff_id = completed_flow.get_payload_metadata()['ibuff_id']
                
        # if cpu node add to it's taskq        
        result = node.add_Task(task)
       
        # track the task release
        self.track_taskRelease(task, node)
        
        # track hevc ctus released
        self.track_HEVC_CTUsReleased(task)
        
        if(result == False):
            self.showTaskMappingTable(nodeid=node.get_id())
            sys.exit()                                            
        
        # remove task from mmc data transfer list
        if(SimParams.MMC_ENABLE_DATATRANSMISSION_MODELLING == True):
            self.mmc.remove_task_mmc_to_node_tr_list(task.get_id())
        
        
        # remove task from input buffer
        self.input_buffers[ibuff_id].remove_Item_byKey(task.get_id())
    
        # decrement simpy container counter                    
        self.InputBuffer_get(1,ibuffid=ibuff_id)
        
        # set the task status on the tm table
        #self.setTaskStatus_inRM_TMTbl(task.get_id(), TaskStatus.TASK_DISPATCHED)
        if(task.get_id() in self.task_mapping_table):
            self.task_mapping_table[task.get_id()]['status'] = TaskStatus.TASK_DISPATCHED
         
        # notify the node that the task is now mapped
        self.WakeSingleSleepingNode(node)
                
        return []
    
    
    # this is called when MMC is not modelled
    def putTaskToNodeTQ_MMCNonModelled(self, node, task, ibuff_id):        
                
        # if cpu node add to it's taskq        
        result = node.add_Task(task)
       
        # track the task release
        self.track_taskRelease(task, node)
        
        if(result == False):
            self.showTaskMappingTable(nodeid=node.get_id())
            sys.exit()                                            
        
        # remove task from input buffer
        self.input_buffers[ibuff_id].remove_Item_byKey(task.get_id())
    
        # decrement simpy container counter                    
        self.InputBuffer_get(1,ibuffid=ibuff_id)
        
        # set the task status on the tm table
        #self.setTaskStatus_inRM_TMTbl(task.get_id(), TaskStatus.TASK_DISPATCHED)
        if(task.get_id() in self.task_mapping_table):
            self.task_mapping_table[task.get_id()]['status'] = TaskStatus.TASK_DISPATCHED
         
        # notify the node that the task is now mapped
        self.WakeSingleSleepingNode(node)
         
    
    ## if node is not in this list, then add to list
    def WakeSleepingNodesAddNode(self, list, node):
        for each_item in list:
            if(each_item.get_id() == node.get_id()):
                return list
        
        list.append(node)
        return list    
    
    ## wake invactive nodes ##    
    def WakeSleepingNodes(self, list_of_nodes=None):
        if (list_of_nodes == None): # empty list so we wake up all nodes
            for each_node in self.node_network.get_Nodes():
                if(each_node.get_status() in [NodeStatus.NODE_IDLE, NodeStatus.NODE_BUSY]):
                #if(each_node.get_status() in [NodeStatus.NODE_IDLE]):    
                    #print(self.label + "::WakeSleepingNodes: node="+str(each_node.get_id()))
                    # interrupt the sleeping node
                    each_node.processInstance.interrupt()
        else:
            for each_node in list_of_nodes:
                if(each_node.get_status() in [NodeStatus.NODE_IDLE, NodeStatus.NODE_BUSY]):
                #if(each_node.get_status() in [NodeStatus.NODE_IDLE]):  
                    #print(self.label + "::WakeSleepingNodes: node="+str(each_node.get_id()))
                    # interrupt the sleeping node
                    each_node.processInstance.interrupt()
                
    def WakeSingleSleepingNode(self, node):        
        if(node.get_status() in [NodeStatus.NODE_IDLE, NodeStatus.NODE_BUSY]):
        #if(node.get_status() in [NodeStatus.NODE_IDLE]):
            #print(self.label + "::WakeSingleSleepingNode: node="+str(node.get_id()))
            # interrupt the sleeping node
            node.processInstance.interrupt()
    
    # this can be used for example at the end 
    # of a simulation to finalise the idle time counter
    def WakeAllNodes(self):
        for each_node in self.node_network.get_Nodes():
            each_node.processInstance.interrupt()
    
    
    
    def startRemapAlgoOnNodes(self, node_list=None):        
        if node_list != None:
            for each_node_id in node_list:
                each_node = self.node_network.get_Nodes()[each_node_id]
                each_node.taskremapping_decent_scheme_instance.startRemappingAlgo(each_node_id)
        else:
            for each_node in self.node_network.get_Nodes():
                each_node.taskremapping_decent_scheme_instance.startRemappingAlgo(each_node.get_id())
            
            
    
    
    
    ##########################################################################################################################
    ## Simulation interaction
    ##########################################################################################################################
    
    # check if all tasks have been dispatched
    # check if all processing nodes are idle
    # check if input buffers are empty
    # check if any flows outstanding
    def endSimulation(self):
        
        result = True
        
        #if(self.task_dispatcher._areAllWorkflowsEmpty() == True): # all workflows are empty
        if(self._hasLastTaskBeenDispatched() == True):
            # check nodes
#            for each_node in self.node_network.get_Nodes():
#                if(each_node.get_status() != NodeStatus.NODE_IDLE):
#                    result = False
#                    break
                
            # check nodes task q
            for each_node in self.node_network.get_Nodes():
                if(each_node.isTaskQEmpty() == False):
                    result = False
                    break
            
            # check input buffers are empty
            if(self._allInputBuffers_Empty() == False):
                result = False  

            # any data flows outstanding in flow table?        
            set_flw_tbl_entries = set([f.getFlow().get_type() for f in self.flow_table.flowEntries.values()])
            set_important_flow_types = set([FlowType.FLOWTYPE_DATA, 
                                        FlowType.FLOWTYPE_DATA_HEVC, 
                                        FlowType.FLOWTYPE_MMCTONODE_DATATRANSFER_RD,
                                        FlowType.FLOWTYPE_MMCTONODE_DATATRANSFER_WR])
            
            if len(set_flw_tbl_entries.intersection(set_important_flow_types)) >0:
                result = False
            
            # check task mapping table for outstanding tasks
            for (tid,val) in self.task_mapping_table.iteritems():
                if(val['status'] in [TaskStatus.TASK_DISPATCHED, TaskStatus.TASK_MARKED_FOR_RELEASE, TaskStatus.TASK_READY_WAITING, TaskStatus.TASK_SUSPENDED, TaskStatus.TASK_RUNNING] ):
                    result = False
                    break
                
            
            
        else:
            result = False
            
        return result
        
    
    def _hasLastTaskBeenDispatched(self):
        if (self.last_scheduled_task_time < self.env.now):
            return True
        else:
            return False
    
    
    def _report_outstanding_resources(self):
        print "---------- task Qs : "
        for each_node in self.node_network.get_Nodes():
            print "CPU: " + str(each_node.get_id())
            pprint.pprint(each_node.get_TaskQueue())
        
        print "---------- Ibuffs : "
        print self._allInputBuffers_Empty()
        
        
        print "---------- flow table : "
        for f in self.flow_table.flowEntries.values():
            print f
    
#         print "---------- tmtbl : "
#         result = True
#         for (tid,val) in self.task_mapping_table.iteritems():
#                 if(val['status'] in [TaskStatus.TASK_DISPATCHED, TaskStatus.TASK_MARKED_FOR_RELEASE, TaskStatus.TASK_READY_WAITING, TaskStatus.TASK_SUSPENDED, TaskStatus.TASK_RUNNING] ):
#                     result = False
#                     break
#         print result
#         pprint.pprint(self.task_mapping_table)
    
    ##########################################################################################################################
    ## For Debug
    ##########################################################################################################################
    def showTaskMappingTable(self, nodeid=None):
        print "showTaskMappingTable"
        if(nodeid == None):
            print "RunTimeTaskManager::showTaskMappingTable"
            print "----------------------------------------"
            pprint.pprint(self.task_mapping_table)
            print "----------------------------------------"
        else:
            records = {}
            for (task_id,val) in self.task_mapping_table.iteritems():
                if(val['node_id'] == nodeid):
                    records[task_id] = val
            
            pprint.pprint(records)
            
    
    
    ##########################################################################################################################
    # Runtime application management
    ##########################################################################################################################
    
    # called each time an existing vid stream ends
    def RuntimeApp_removeStream(self, wf_id, stream_id):
        
        Debug.PPrint("%f"%self.env.now + "," + self.label + "," + 'RuntimeApp_removeStream::, : wf_id=%d, stream_id=%d' % (wf_id,stream_id), DebugCat.DEBUG_CAT_RUNTIMEAPP)
        
        app_tasks = self.RunTimeApps.getTasks()
        app_flows = self.RunTimeApps.getFlows()
        
        # remove all tasks corresponding to the given wf + strm ids
        for each_t in app_tasks:
            # remove task if in specific stream + wfid
            if(each_t.get_wfid() == wf_id) and (each_t.get_video_stream_id() == stream_id):
                self.RunTimeApps.removeTask(each_t)
                
        # remove all flows corresponding to the given wf + strm ids
        for each_f in app_flows:
            
            if(each_f.get_respectiveSrcTask()!=None):
                # get the stream and wfid that the flow belongs to
                flw_wf_id = each_f.get_respectiveSrcTask().get_wfid()
                flw_strm_id = each_f.get_respectiveSrcTask().get_video_stream_id()               
                if(flw_wf_id == wf_id) and (flw_strm_id == stream_id):
                    self.RunTimeApps.removeFlow(each_f)
            else: # else check the metadata
                # get the stream and wfid that the flow belongs to
                flw_wf_id = each_f.get_payload_metadata()['wf_id']
                flw_strm_id = each_f.get_payload_metadata()['vid_strm_id']
                if(flw_wf_id == wf_id) and (flw_strm_id == stream_id):
                    self.RunTimeApps.removeFlow(each_f)
                
        # remove corresponding stream
        stream_key = str(wf_id) + "_" + str(stream_id)  # hash
        self.RunTimeApps.removeStream(stream_key)
        
    
    
    # called each time a new vid stream enters the system
    def RuntimeApp_addStream(self, wf_id, gop_tasks,  entry_time):     
        
        ############################
        # Add stream to runtime app
        ############################        
        # get the first task currently in the wf
        for each_t in gop_tasks:
            if ((each_t.get_frameIXinGOP() == 0)):
                vs_iframe_task = each_t
                break
                       
        start_time = entry_time
        gop_structure = vs_iframe_task.get_gopstructure()
        resolution = (vs_iframe_task.get_frame_h(), vs_iframe_task.get_frame_w())
        arrival_rate_ub = vs_iframe_task.get_end_to_end_deadline()
        frame_rate = vs_iframe_task.get_framerate()
        stream_id = vs_iframe_task.get_video_stream_id()    
        
        
        strm_specs = {
                      'frame_h': resolution[0],
                      'frame_w': resolution[1],
                      'fps': frame_rate,
                      'gop_struct': gop_structure,
                      'vid_strm_id': stream_id,
                      'wf_id': wf_id
                      }
        
        Debug.PPrint("%f"%self.env.now + "," + self.label + "," + 'RuntimeApp_addStream::, : wf_id=%d, stream_id=%d' % (wf_id,stream_id), DebugCat.DEBUG_CAT_RUNTIMEAPP)    
        
        # find properties of the video stream that has just entered the system       
        new_vid_stream = VideoStreamInfo(stream_id,
                                         wf_id,
                                         gop_structure, 
                                         resolution,
                                         arrival_rate_ub,
                                         frame_rate,
                                         start_time)
        
        # add stream to the runtime app 
        stream_key = str(wf_id) + "_" + str(stream_id)  # hash
        self.RunTimeApps.addStream(stream_key, new_vid_stream)   
        flows_next_id = self.flow_table.nextid
        ############################
        # Add tasks to runtime app
        ############################        
        # find all tasks corresponding to the new vid stream (hopefully number of tasks equiv to gop-len)
#        task_list = []
#        for each_t in gop_tasks: 
#            if(each_t.get_video_stream_id() == stream_id) and (each_t.get_scheduledDispatchTime() == entry_time):
#                task_list.append(each_t)
                
        if(len(gop_tasks) != len(vs_iframe_task.get_gopstructure())):
            sys.exit('RuntimeApp_addStream:: wrong gop len')            
            
        ## set extra params for these tasks, and add to the runtime application model
        for each_t in gop_tasks:
            # period
            each_t.set_period(each_t.get_end_to_end_deadline())
            # processing core
            selected_node = self._getPreMappedProcessingCore(wf_id, each_t.get_video_stream_id() , each_t.get_frameIXinGOP())
            
            if selected_node == None:                
                sys.exit("RuntimeApp_addStream:: Error ! : can't get premapped core")
            
            each_t.set_processingCore(selected_node)            
            
            # add task to runtime app
            self.RunTimeApps.addTask(each_t)             
        
            ############################
            # Add flows to runtime app
            ############################            
            flows = self._getFlowsPerTask(each_t, flows_next_id)            
            if(len(flows)>0):
                for f in flows:                    
                    # set release jitter in all the tasks
                    source_task = f.get_respectiveSrcTask()
                    rj = source_task.getResponseTime(source_task.getInterferenceSet_withPrCnst(self.RunTimeApps.getTasks()))
                    f.set_releaseJitter(rj)
                    
                    # add flow to runtime app
                    self.RunTimeApps.addFlow(f) 
                flows_next_id+=len(flows)    
                    
        
        #################################
        # Add MMC-task and task->MMC,
        # tasks and flows
        #################################
        if(SimParams.MMC_ENABLE_DATATRANSMISSION_MODELLING == True):
            # two extra tasks : MMC_data_RD, MMC_data_WR
            tid = gop_tasks[0].get_id()*(-1)+(-1)
            task_mmc_data_rd = self._get_pseudo_task(-2, 0, -1, strm_specs, 'MMC_RD', tid=tid)        
            self.RunTimeApps.addTask(task_mmc_data_rd)
            tid = gop_tasks[0].get_id()*(-1)+(-2)
            task_mmc_data_wr = self._get_pseudo_task(-1, 0, -1, strm_specs, 'MMC_WR', tid=tid)
            self.RunTimeApps.addTask(task_mmc_data_wr)
            
            # one flow EACH from [mmc->every_gop_task (Data_RD)]
            for each_gop_task in gop_tasks:
                f = self._getPseudoFlow_MMCToNode_DataRD(each_gop_task, flows_next_id, strm_specs)
                self.RunTimeApps.addFlow(f)
                flows_next_id+=1
            
            # one flow EACH from [every_gop_task->mmc (Data_WR)]
            for each_gop_task in gop_tasks:
                f = self._getPseudoFlow_NodeToMMC_DataWR(each_gop_task, flows_next_id, strm_specs)
                self.RunTimeApps.addFlow(f)
                flows_next_id+=1
        
        ############################
        # show real-time analysis
        ############################ 
        
        if(SimParams.LOG_OUTPUT_SCHED_TEST_REPORT == True):                  
            ts = datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d%H%M%S')
            fname = "schedulability_tests/" + "sched_test_report_" + str(wf_id) + "_" + str(stream_id) + "__" + ts +".xml"
            self.NoCSchedulabilityAnalyser.outputReport_ShiAndBurns(fname)
            
    
    
    
    def _get_pseudo_task(self, ix, pri, node_id, strm_specs, ftype, tid=0, wccc=0.0, avgccc=0.0):
                
        pseudo_task = MPEG2FrameTask(self.env, tid, 
                 frame_h = strm_specs['frame_h'], frame_w = strm_specs['frame_w'], \
                 frame_rate = strm_specs['fps'], \
                 frame_type = ftype, \
                 frame_ix_in_gop = ix, \
                 gop_struct = strm_specs['gop_struct'], \
                 video_stream_id = strm_specs['vid_strm_id'], \
                 wf_id = strm_specs['wf_id'])
                
        pseudo_task.set_processingCore(node_id)
        pseudo_task.set_priority(pri)
        pseudo_task.set_worstCaseComputationCost(wccc)
        pseudo_task.set_avgCaseComputationCost(avgccc)        
        pseudo_task.set_period(float(float(len(strm_specs['gop_struct']))*float(1.0/strm_specs['fps'])))
                
        return pseudo_task
    
    
    # conditions for a flow originating from Task Ti:
    # - Ti has children : {Ti_child} 
    # - child is on a different node than Ti's processing node
    def _getFlowsPerTask(self, source_task, flowstable_next_id):        
        
        num_flows_added = []
        
        Ti = source_task
        wf_id = Ti.get_wfid()
        strm_id = Ti.get_video_stream_id()
        
        task_mapped_nodeid = self._getPreMappedProcessingCore(wf_id, strm_id, Ti.get_frameIXinGOP())
        child_frame_ixs = Ti.get_children_frames()  #ids
       
        # find unique flows
        # e.g. if task has two children both mapped on same node, then we only have 1 flow
        flow_list = []
        dst_node_list = []
        temp_destinations_dict = {}  
        nextid = flowstable_next_id         # not sure about this ?? 
        for each_child_frame_ixs in child_frame_ixs:
            child_task_nodeid = self._getPreMappedProcessingCore(wf_id, strm_id, each_child_frame_ixs)
            
            if(child_task_nodeid not in temp_destinations_dict):
                temp_destinations_dict[child_task_nodeid] = [each_child_frame_ixs]
            else:
                temp_destinations_dict[child_task_nodeid].append(each_child_frame_ixs) 
            
            if(child_task_nodeid not in dst_node_list):
                dst_node_list.append(child_task_nodeid)                    
                
                # new flow
                if(child_task_nodeid != task_mapped_nodeid):
                    id = Ti.get_id()
                    route = self.interconnect.getRouteXY(task_mapped_nodeid, child_task_nodeid)
                    priority = Ti.get_priority() + (self.flow_priority_offset+100) + nextid
                    nextid += 1
                    basicLatency = self.interconnect.getRouteCostXY(task_mapped_nodeid, 
                                                                                child_task_nodeid,
                                                                                Ti.get_completedTaskSize())
                    payload = Ti.get_completedTaskSize()
                    
                    newflow = NoCFlow(id,
                                   Ti,
                                   Ti.get_id(),
                                   temp_destinations_dict[child_task_nodeid], #ids
                                   temp_destinations_dict[child_task_nodeid], #ixs
                                   task_mapped_nodeid, 
                                   child_task_nodeid, 
                                   route,
                                   priority, 
                                   None, 
                                   basicLatency, 
                                   payload,
                                   None,
                                   type=FlowType.FLOWTYPE_DATA,
                                   payload_metadata={'wf_id': Ti.get_wfid(), 
                                         'vid_strm_id': Ti.get_video_stream_id(),
                                         'gop_ix' : Ti.get_frameIXinGOP()
                                         })
                    newflow.set_period(Ti.get_end_to_end_deadline())                    
                    flow_list.append(newflow)                    
        
        return flow_list

    
    def _getPseudoFlow_MMCToNode_DataRD(self, dst_task, nextid, strm_specs):
        id = 0
        dst_task_premapped_nodeid = self._getPreMappedProcessingCore(dst_task.get_wfid(), dst_task.get_video_stream_id(), dst_task.get_frameIXinGOP())
        #closest_mmc_port_id = self.mmc.getClosestMMCPort(dst_task_premapped_nodeid)
        closest_mmc_port_id = self.getMMCPort_handler(dst_task.get_id(), dst_task_premapped_nodeid)
        route = self.interconnect.getRouteXY(closest_mmc_port_id, dst_task_premapped_nodeid)        
        priority = SimParams.MMC_DATAREAD_FLOW_PRIORITY + nextid
        payload = dst_task.get_mpeg_tasksize()
        basicLatency = self.interconnect.getRouteCostXY(closest_mmc_port_id, 
                                                                    dst_task_premapped_nodeid,
                                                                    payload)
        newflow = NoCFlow(id,
                       None,
                       None,
                       [dst_task.get_frameIXinGOP()],
                       [dst_task.get_frameIXinGOP()],
                       closest_mmc_port_id, 
                       dst_task_premapped_nodeid, 
                       route,
                       priority, 
                       None, 
                       basicLatency, 
                       payload,
                       None,
                       type=FlowType.FLOWTYPE_MMCTONODE_DATATRANSFER_RD,
                       payload_metadata={'wf_id': strm_specs['wf_id'], 
                                         'vid_strm_id': strm_specs['vid_strm_id'],
                                         'gop_ix' : dst_task.get_frameIXinGOP(),
                                         'dst_task_id' : dst_task.get_id(),
                                         'r_jitter' : None,
                                         'src_t_ix' : -2,
                                         'dst_t_ix' : dst_task.get_frameIXinGOP(),
                                         
                                         }
                          )
        newflow.set_period(dst_task.get_end_to_end_deadline())
        
        return newflow
    
    
    def _getPseudoFlow_NodeToMMC_DataWR(self, src_task, nextid, strm_specs):
        id = 0
        src_task_premapped_nodeid = self._getPreMappedProcessingCore(src_task.get_wfid(), src_task.get_video_stream_id(), src_task.get_frameIXinGOP())
        #closest_mmc_port_id = self.mmc.getClosestMMCPort(src_task_premapped_nodeid)
        closest_mmc_port_id = self.getMMCPort_handler(src_task.get_id(), src_task_premapped_nodeid)
        route = self.interconnect.getRouteXY(src_task_premapped_nodeid, closest_mmc_port_id)        
        #priority = SimParams.MMC_DATAREAD_FLOW_PRIORITY + nextid
        priority = src_task.get_priority() + (self.flow_priority_offset+100) + nextid
        payload = src_task.get_completedTaskSize()
        basicLatency = self.interconnect.getRouteCostXY(src_task_premapped_nodeid, 
                                                                    closest_mmc_port_id,
                                                                    payload)  
        newflow = NoCFlow(id,
                       None,
                       None,
                       [-1],
                       [-1],
                       src_task_premapped_nodeid, 
                       closest_mmc_port_id, 
                       route,
                       priority, 
                       None, 
                       basicLatency, 
                       payload,
                       None,
                       type=FlowType.FLOWTYPE_MMCTONODE_DATATRANSFER_WR,
                       payload_metadata={'wf_id': strm_specs['wf_id'], 
                                         'vid_strm_id': strm_specs['vid_strm_id'],
                                         'gop_ix' : src_task.get_frameIXinGOP(),
                                         'src_task' : src_task,
                                         'r_jitter' : None,
                                         'src_t_ix' : src_task.get_frameIXinGOP(),
                                         'dst_t_ix' : -1,
                                         })
        newflow.set_period(src_task.get_end_to_end_deadline())
        
        return newflow
            
    ##########################################################################################################################
    # Shared resources locking mechanisms
    #  - RM task mapping table
    #  - RM flow table
    ##########################################################################################################################
    
    def lock_RM_TMtbl(self):
        while(self.mutex_tmtbl.level == 1):
            i=1 # busy wait                                                            
        self.mutex_tmtbl.put(1) # obtain lock
        
    def release_RM_TMtbl(self):
        self.mutex_tmtbl.get(1) # release lock
        
    def lock_RM_FLWtbl(self):
        while(self.flow_table.mutex.level == 1):
            i=1 # busy wait                                       
        self.flow_table.mutex.put(1)   # obtain lock   
    
    def release_RM_FLWtbl(self):
        self.flow_table.mutex.get(1) # release lock        
            
    
    
    ##########################################################################################################################
    # Related to tracking
    ##########################################################################################################################
    def track_taskRelease(self, task, node):
        if(SimParams.TRACK_RMTASKRELEASE == True):
            entry = {
                     'time' : self.env.now,
                     'task_id' : task.get_id(),
                     'node' : node.get_id()
                     }
            self.track_taskrelease.append(entry)
    
    def track_MappingAndPriAss(self, strm_specs, frames_mapping, pri_ass):
        if(SimParams.TRACK_MAPPINGANDPRIASSINFO == True):
            entry = {                 
                     'time' : self.env.now,
                     
                     # decision
                     'strm_specs'   : strm_specs,
                     'fr_mapp'      : frames_mapping,
                     'fr_priass'    : pri_ass,
                     
                     # current resource information
                     'nTQInfo'  : [each_node.get_TQTaskInfo() for each_node in self.node_network.get_Nodes()],                 
                     'ibTQInfo' : [each_ibuff.get_BuffTaskInfo() for ix, each_ibuff in enumerate(self.input_buffers)]                     
                     }
            
            self.track_mappingandpriass.append(entry)
            
    def track_HEVC_CTUsReleased(self, hevc_task):        
        if SimParams.TASK_MODEL == TaskModel.TASK_MODEL_HEVC_TILE_LEVEL:
            if hevc_task.get_id() in self.track_hevc_ctus_released:
                sys.exit(self.label + ":: track_HEVC_CTUsReleased : this task has been previously released : " + str(hevc_task.get_id()))
            else:            
                self.track_hevc_ctus_released[hevc_task.get_id()] = hevc_task.calc_num_CTU_via_block_partitions()
            
            
##########################################################################################################################
# Resource manager status enum class
##########################################################################################################################        
class RMStatus:
    RM_SLEEPING             = 1     # i.e sleeping
    RM_BUSYWAITING          = 2     # i.e waiting for someone else/resource
    RM_BUSY                 = 3     # i.e busy computing
    RM_ACTIVE               = 4     # i.e. ready and doing work    
    RM_NOTIFY_TASKCOMPLETED = 5
    RM_NOTIFY_FLOWCOMPLETED = 6
    
    NODE_JUSTWOKEUP         = 7
    


