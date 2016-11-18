import pprint
import sys
import math
import itertools
import simpy
from collections import OrderedDict

## local imports
from libMappingAndScheduling.MappingPolicy import MappingPolicy
from libBuffer.Buffer import Buffer
from libProcessingElement.CPUNode_ClosedLoop_wIBuffering import CPUNode_ClosedLoop_wIBuffering
from libProcessingElement.Node import NodeStatus
from libApplicationModel.MPEG2FrameTask import MPEG2FrameTask
from libNoCModel.NoCFlowTable import NoCFlowTable, NoCFlow
from SimParams import SimParams
from libDebug.Debug import Debug, DebugCat
from libResourceManager.Mapper.ScheduleAndMap_TT import ScheduleAndMap_TT



class RunTimeTaskManager_TT:
    
    def __init__(self, env, polling_delay, mapping_policy, node_network, input_buffers, output_buffer, interconnect):        
        self.env = env        
        self.polling_delay = polling_delay        
        self.mapping_policy = mapping_policy
        self.label = "ResourceManager::"
        self.status = RMStatus.RM_SLEEPING 
        
        # runtime taskmanager needs to have a view of the system resources      
        self.node_network = node_network
        self.input_buffers = input_buffers
        self.output_buffer = output_buffer
        self.interconnect = interconnect
        
        # tracking video stream info
        self.video_streams = {}
        
        # also need to keep track of the task-to-node mapping
        # all the nodes will also have this table
        self.task_mapping_table = {}    # {key : {data}}
        
        ## flow table - contains all the flows related to the tasks
        self.flow_table = NoCFlowTable()
        
        # slack reclaimation table - all slacks amounts for completed tasks will get stored here
        self.slack_reclaim_table = {}
        
        self.max_tasks = None   # maximum num of tasks in simulation run    
        self.last_scheduled_task_time = None    # what time is the last task scheduled at    
                
        # semaphore for the mapping table
        self.mutex_tmtbl = simpy.Container(self.env, capacity=1, init=0)
        
        # Start the run process everytime an instance is created.        
        self.processInstance = env.process(self.run())
        
        self.Mapper =   ScheduleAndMap_TT(env, self )
        
        
        
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
                self.Mapper.scheduleAndMapTasks_MultiStream()
                self.updateSlaveMappingTables(self.task_mapping_table)

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
                self.updateEstimatedLateness()
                list_of_nodes_to_interrupt = []
                
                
            else:
                Debug.PPrint("%f"%self.env.now + "," + self.label + "," + 'run::, : Inputbuffers empty!', DebugCat.DEBUG_CAT_RMINFO)
                
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
            except simpy.Interrupt: # if sleeping - now gets woken up
                self.status = RMStatus.NODE_JUSTWOKEUP
                Debug.PPrint("%f"%self.env.now + "," + self.label + "," + 'run::, : I got interrupted, was sleeping', DebugCat.DEBUG_CAT_INTERRUPT)
                                
                                
                                
    #######################################
    ## Admission Control
    #######################################
    
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
            # check if any of the tasks in the input buffer is late
            if(self._inputBuffs_numtasks_late() > 0):
                return False
            else:
                if (self.countDroppedTasks() > 0):
                    return False
                else:
                    if(self.isJobSchedulable(stream_specs) == True):
                        if(self.VideoStreamInfo_anyStreamsLate() > 0):
                            return False
                        else:
                            return True
                    else:
                        return False
            
    
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
     
    
    
           
            
    #######################################
    ## Dealing with the slack reclaim table 
    #######################################
    
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
    
    
    #######################################
    ## Dealing with the task-mapping table
    #######################################
    
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
        self.updateSlaveMappingTables(self.task_mapping_table)
        
    def updateSlaveMappingTables(self, master_mapping_table):        
        # slave tables
        for each_node in self.node_network.get_Nodes():
            each_node.updateMappingTable(master_mapping_table)
            
            
    def removeMapppingTableEntry(self, task_id):
        del self.task_mapping_table[task_id]
        
        self.updateSlaveMappingTables(self.task_mapping_table)
            
            
    #######################################
    ## Manipulating the global input buffer
    #######################################
    
    
    def InputBuffer_isFull(self, offset=0, id=0):
        return (self.input_buffers[id].simpy_container_instance.level >= (self.input_buffers[id].simpy_container_instance.capacity - offset))
    
    
    def InputBuffer_get(self,n, ibuffid=0):
        self.input_buffers[ibuffid].simpy_container_instance.get(n)
        
    # are all input buffers empty ?
    def _allInputBuffers_Empty(self):
        result = True
        for each_ibuff in self.input_buffers:
            if(each_ibuff.isEmpty() == False):
                result = False
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
    def updateEstimatedLateness(self):
        for each_ibuff_id in xrange(len(self.input_buffers)):
            for (each_task_key, each_task_val) in self.input_buffers[each_ibuff_id].get_BufferItemsList().items():
                
                current_time = self.env.now
                dispatched_time = each_task_val.get_dispatchTime()
                end_to_end_deadline = float(len(each_task_val.get_gopstructure())) * float((1.0/each_task_val.get_framerate())) 
                
                estimated_lateness = float((current_time - dispatched_time)) - float(end_to_end_deadline)
                
                each_task_val.set_estimatedLateness(estimated_lateness)
    
    def _inputBuffs_numtasks_late(self):
        
        count = 0
        
        for each_ibuff_id in xrange(len(self.input_buffers)):
            for (each_task_key, each_task_val) in self.input_buffers[each_ibuff_id].get_BufferItemsList().items():
                lateness = each_task_val.get_estimatedLateness()
                
                if(lateness > 0):
                    count+=1
                    
        return count
        
            
    
    #######################################
    ## Getters/Setters
    #######################################
    
    ## getters
    def get_processInstance(self):
        return self.processInstance    
    def get_maxTasks(self):
        return self.max_tasks
    def get_lastscheduledtask_time(self):
        return self.last_scheduled_task_time
    
    ## setters
    def set_maxTasks(self, max_tasks):
        self.max_tasks = max_tasks
    def set_lastscheduledtask_time(self, lstt):
        self.last_scheduled_task_time = lstt
    
    #######################################
    ## Interact with processing nodes
    #######################################
    
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
                if(each_node.get_status() == NodeStatus.NODE_IDLE):
                    #print(self.label + "::WakeSleepingNodes: node="+str(each_node.get_id()))
                    # interrupt the sleeping node
                    each_node.processInstance.interrupt()
        else:
            for each_node in list_of_nodes:
                if(each_node.get_status() == NodeStatus.NODE_IDLE):
                    #print(self.label + "::WakeSleepingNodes: node="+str(each_node.get_id()))
                    # interrupt the sleeping node
                    each_node.processInstance.interrupt()
                
    def WakeSingleSleepingNode(self, node):        
        if(node.get_status() == NodeStatus.NODE_IDLE):
            #print(self.label + "::WakeSingleSleepingNode: node="+str(node.get_id()))
            # interrupt the sleeping node
            node.processInstance.interrupt()
           
    
    
    
    
    #######################################
    ## Simulation interaction
    #######################################
    
    # check if all tasks have been dispatched
    # check if all processing nodes are idle
    # check if input buffers are empty
    def endSimulation(self):
        
        result = True
        
        if(self.last_scheduled_task_time < self.env.now): # last task has been dispatched
            
            # check nodes
            for each_node in self.node_network.get_Nodes():
                if(each_node.get_status() != NodeStatus.NODE_IDLE):
                    result = False
                    break
                
            # check nodes task q
            for each_node in self.node_network.get_Nodes():
                if(each_node.isTaskQEmpty() == False):
                    result = False
                    break
            
            # check input buffers are empty
            if(self._allInputBuffers_Empty() == False):
                result = False
                
        else:
            result = False
            
        return result
        
    
    #######################################
    ## For Debug
    #######################################        
    def showTaskMappingTable(self, nodeid=None):
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
            
            
            
            
            
        
class RMStatus:
    RM_SLEEPING       = 1     # i.e sleeping
    RM_BUSYWAITING    = 2     # i.e waiting for someone else/resource
    RM_BUSY           = 3     # i.e busy computing
    RM_ACTIVE         = 4     # i.e. ready and doing work    
    NODE_JUSTWOKEUP   = 5
    