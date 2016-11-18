import pprint
import sys
import itertools
import simpy
import random
from operator import itemgetter

## local imports
from libMappingAndScheduling.MappingPolicy import MappingPolicy
from libBuffer.Buffer import Buffer
from libProcessingElement.CPUNode_ClosedLoop_wIBuffering import CPUNode_ClosedLoop_wIBuffering
from libProcessingElement.Node import NodeStatus
from libApplicationModel.MPEG2FrameTask import MPEG2FrameTask
from libApplicationModel.Task import TaskStatus
from libNoCModel.NoCFlowTable import NoCFlowTable
from libNoCModel.NoCFlow import NoCFlow, FlowType
from SimParams import SimParams
from libDebug.Debug import Debug, DebugCat
from ScheduleAndMap_ClosedLoop_wIBuffering import ScheduleAndMap_ClosedLoop_wIBuffering



class ScheduleAndMap_OpenLoop(ScheduleAndMap_ClosedLoop_wIBuffering):
    
    def __init__(self, env, RM_instance):  
        
        ScheduleAndMap_ClosedLoop_wIBuffering.__init__(self, env, RM_instance)
        self.label = "ScheduleAndMap_OpenLoop"        
        
       
    # map all unmapped tasks in the input buffers
    def mapNewGoPTasks(self, all_ibuff_tasks):
        #all_ibuff_tasks = list(itertools.chain.from_iterable([sublist.get_BufferItemsList().values() for sublist in self.RM_instance.input_buffers]))
        
        #for i_buff_id in xrange(len(self.RM_instance.input_buffers)):            
        #    wf_id = i_buff_id            
        #    for (each_task_id, each_task) in self.RM_instance.input_buffers[i_buff_id].get_BufferItemsList().items():
        #        
        for each_task in all_ibuff_tasks:            
            Ti = each_task
            stream_id = Ti.get_video_stream_id()
            gop_fr_ix = Ti.get_frameIXinGOP()
            i_buff_id = each_task.get_wfid()
            each_task_id = Ti.get_id()
            wf_id = i_buff_id
            
            ## SEMI_DYNAMIC_APPROACH : ## 
            # in this mode, we assume all the tasks of a video stream
            # is premapped upon admission of the video stream
            if(SimParams.MAPPING_PREMAPPING_ENABLED == True):                                    
                self.mapNewGoPTasks_SemiDynamicMapping_withoutMSSignalling(each_task_id, 
                                                                           i_buff_id, 
                                                                           wf_id, stream_id, gop_fr_ix, Ti,
                                                                           task_status = TaskStatus.TASK_MAPPED,
                                                                           task_release_time = self.env.now)
            
            ## FULLY_DYNAMIC_APPROACH : ##
            # in this mode, we assume all the jobs of a video stream are assigned mapping,
            # when they are dispatched by the task dispatcher, not beforehand.
            # assumes that the RM has global knowledge
            else:
                self.mapNewGoPTasks_FullyDynamicMapping_withoutMSSignalling(each_task_id, Ti,
                                                                            task_status = TaskStatus.TASK_MAPPED,
                                                                            task_release_time = self.env.now)
                        
                
    
    # go through all unscheduled tasks and schedule them to be released NOW.
    def scheduleTasks(self,all_ibuff_tasks):
        print "scheduleTasks:: Enter"
        #all_ibuff_tasks = list(itertools.chain.from_iterable([sublist.get_BufferItemsList().values() for sublist in self.RM_instance.input_buffers]))
        
        
        #for i_buff_id in xrange(len(self.RM_instance.input_buffers)):
            # get unscheduled iframe from this input buffer
        #    unscheduled_tasks = self._getAllUnscheduledTaskID_In_InputBuff(i_buff_id)
        #    if unscheduled_tasks != None:
        for Ti in all_ibuff_tasks:                        
            if(Ti != None): 
                if(Ti.get_initiallyScheduled() == False):
                    
    #                ###### debug ####
    #                if(Ti.get_id() == 0):
    #                    print "48 here --- "
    #                    print self.env.now                    
    #                #################                
                    
                    # check if the i-frame has been mapped or not, if not mapped, then pick a node to map onto
                    # find node that is currently free
                    if(Ti.get_id() in self.RM_instance.task_mapping_table):
                        if(self.RM_instance.task_mapping_table[Ti.get_id()]['node_id'] != None):
                            selected_node_id = self.RM_instance.task_mapping_table[Ti.get_id()]['node_id']
                        else:
                            sys.exit('mapping-error - premapping, did not work ! - 1')                        
                    else:
                        sys.exit('mapping-error - premapping, did not work ! - 2')
                        
                    if(selected_node_id != None):                    
                        rel_time = self.env.now
                        tm_entry = {
                                    'node_id' : selected_node_id,
                                    'release_time' : rel_time,                            
                                    'wcc' : Ti.get_worstCaseComputationCost(),
                                    'status' : TaskStatus.TASK_NULL,
                                    'pri' : Ti.get_priority(),
                                    'deps_completed' : [],
                                    'strm_key' : "%d_%d_%d" % (Ti.get_wfid(), Ti.get_video_stream_id(), Ti.get_unique_gop_id())
                                    }                                                        
                        self.RM_instance.task_mapping_table[Ti.get_id()] = tm_entry
                            
                        ## update input buffer task
                        i_buff_id = Ti.get_wfid()
                        self.RM_instance.input_buffers[i_buff_id].get_BufferItemsList()[Ti.get_id()].set_releaseTime(rel_time)
                        if(self.RM_instance.input_buffers[i_buff_id].get_BufferItemsList()[Ti.get_id()].get_initiallyScheduled() == False):
                            self.RM_instance.input_buffers[i_buff_id].get_BufferItemsList()[Ti.get_id()].set_initiallyScheduled(True)
                        
                    else:
                        sys.exit('mapping-error - premapping, did not work ! - 3')

    
    

    ## add all mapped tasks to the flow table, the respective flows ##
    def addTo_RM_FlowTable(self, finished_taskList, releaseTime, debug_which_cpu):
        debug_ftl = [x.get_id() for x in finished_taskList]        
        Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'addTo_RM_FlowTable::, : Enter - fin_tsk_lst='+str(debug_ftl) + ", which_cpu="+str(debug_which_cpu), DebugCat.DEBUG_CAT_MAPPERINFO)
        
        num_flows_added = []        
        for each_task in finished_taskList:
            
            task_mapped_nodeid = self.RM_instance.task_mapping_table[each_task.get_id()]['node_id']            
            child_tasks_ids = each_task.get_children()  #ids
            child_tasks_ixs = each_task.get_children_frames() #ixs
            child_tasks_id_ix_rel = self._get_tid_tix_dict(child_tasks_ids, child_tasks_ixs)
            
#            ## DEBUG ##
#            if(each_task.get_id() == 721):
#                pprint.pprint(child_tasks_ids)#
#                #pprint.pprint(self.RM_instance.task_mapping_table)
#                                
#            ###########                
            
            # find unique flows
            # e.g. if task has two children both mapped on same node, then we only have 1 flow
            dst_node_list = []
            temp_destinations_dict = {}            
            for each_child_id in child_tasks_ids:
                child_task_nodeid = self.RM_instance.task_mapping_table[each_child_id]['node_id']
                
                if(child_task_nodeid not in temp_destinations_dict):
                    temp_destinations_dict[child_task_nodeid] = [each_child_id]
                else:
                    temp_destinations_dict[child_task_nodeid].append(each_child_id) 
                
                if(child_task_nodeid not in dst_node_list):
                    dst_node_list.append(child_task_nodeid)                    
                    
#                    ## DEBUG ##
#                    if(each_task.get_id() == 721):
#                        print "each_child_id = " + str(each_child_id)
#                        print "child_task_nodeid = " + str(child_task_nodeid)
#                        pprint.pprint(temp_destinations_dict)
#                        print "dst_node_list = " + str(dst_node_list)
#                    ###########
                    
                    # new flow
                    if(child_task_nodeid != task_mapped_nodeid):
                        nextid = self.RM_instance.flow_table.nextid                    
                        route = self.RM_instance.interconnect.getRouteXY(task_mapped_nodeid, child_task_nodeid)
                        #priority = random.randint(0,SimParams.NOC_FLOW_PRIORITY_LEVELS)
                        #priority = each_task.get_priority()
                        priority = each_task.get_priority() + (self.RM_instance.flow_priority_offset+100) + nextid
                        basicLatency = self.RM_instance.interconnect.getRouteCostXY(task_mapped_nodeid, 
                                                                                    child_task_nodeid,
                                                                                    each_task.get_completedTaskSize())
                        payload = each_task.get_completedTaskSize()
                        endTime_wrt_BL = releaseTime + basicLatency
                        
                        newflow = NoCFlow(nextid,
                                       each_task,
                                       each_task.get_id(),
                                       temp_destinations_dict[child_task_nodeid],
                                       self._get_tixs_from_tids(temp_destinations_dict[child_task_nodeid], child_tasks_id_ix_rel),
                                       task_mapped_nodeid, 
                                       child_task_nodeid, 
                                       route,
                                       priority, 
                                       None, 
                                       basicLatency, 
                                       payload,
                                       endTime_wrt_BL,
                                       type=FlowType.FLOWTYPE_DATA)
                        
#                         ## DEBUG ##
#                        if(each_task.get_id() == 721):
#                            print newflow
#                        ###########
                        
                        # add to the flow table
                        self.RM_instance.flow_table.addFlow(newflow, releaseTime, basicLatency)                        
                        num_flows_added.append(newflow.get_id())
                        
        # update the table
        if(len(num_flows_added) > 0):
            self.RM_instance.flow_table.updateTable(fire=True)   # one update for many additions
            
    
    
    ## add all mapped tasks to the flow table, the respective flows ##
    def addTo_RM_FlowTable_HEVC_FrameLevel(self, finished_taskList, releaseTime, debug_which_cpu):
        debug_ftl = [x.get_id() for x in finished_taskList]        
        Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'addTo_RM_FlowTable::, : Enter - fin_tsk_lst='+str(debug_ftl) + ", which_cpu="+str(debug_which_cpu), DebugCat.DEBUG_CAT_MAPPERINFO)
        
        TEMP_BYTE_OFFSET = 32
        
        num_flows_added = []        
        for each_task in finished_taskList:
            
            task_mapped_nodeid = self.RM_instance.task_mapping_table[each_task.get_id()]['node_id']     
            child_tasks_info = each_task.get_expected_data_to_children() # children and the data payload size
            
            # if we are sending two flows to the same node, corresponding to two child tasks, 
            # then we have to make sure the payload is different (i.e. TEMP_BYTE_OFFSET), else there will be event firing isues            
            temp_node_id_payload_dict = {}         
            for each_child_id, each_child_payload in child_tasks_info.iteritems():
                child_task_nodeid = self.RM_instance.task_mapping_table[each_child_id]['node_id']
                
                flow_payload = each_child_payload
                
                if child_task_nodeid in temp_node_id_payload_dict: # redundancy
                    if (each_child_payload == temp_node_id_payload_dict[child_task_nodeid]): # same payload
                        temp_node_id_payload_dict[child_task_nodeid] += TEMP_BYTE_OFFSET
                        flow_payload += TEMP_BYTE_OFFSET
                else: 
                    temp_node_id_payload_dict[child_task_nodeid] = each_child_payload
                
                
                # new flow
                if(child_task_nodeid != task_mapped_nodeid):
                    nextid = self.RM_instance.flow_table.nextid                    
                    route = self.RM_instance.interconnect.getRouteXY(task_mapped_nodeid, child_task_nodeid)                        
                    priority = each_task.get_priority() + (self.RM_instance.flow_priority_offset+100) + nextid
                    payload = flow_payload
                    basicLatency = self.RM_instance.interconnect.getRouteCostXY(task_mapped_nodeid, 
                                                                                child_task_nodeid,
                                                                                payload)
                    payload_metadata = {
                                        'child_id' : each_child_id,
                                        'each_child_payload' : each_child_payload,                                        
                                        }
                    endTime_wrt_BL = releaseTime + basicLatency
                    
                    newflow = NoCFlow(nextid,
                                   each_task,
                                   each_task.get_id(),
                                   [each_child_id],
                                   None, #self._get_tixs_from_tids(temp_destinations_dict[child_task_nodeid], child_tasks_id_ix_rel),
                                   task_mapped_nodeid, 
                                   child_task_nodeid, 
                                   route,
                                   priority, 
                                   None, 
                                   basicLatency, 
                                   payload,
                                   endTime_wrt_BL,
                                   type=FlowType.FLOWTYPE_DATA_HEVC,
                                   payload_metadata=payload_metadata)
                    
                    # add to the flow table
                    self.RM_instance.flow_table.addFlow(newflow, releaseTime, basicLatency)                        
                    num_flows_added.append(newflow.get_id())
                        
        # update the table
        if(len(num_flows_added) > 0):
            self.RM_instance.flow_table.updateTable(fire=True)   # one update for many additions
    
    
         
    ## this gets called when a flow has completed ##
    def DataFlowComplete(self, flow):
        
        Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'DataFlowComplete::, : Enter - flowid='+str(flow.get_id()), DebugCat.DEBUG_CAT_MAPPERINFO)
        
        # set the status of the task in dep buffer to transmission complete
        dst_node_id = flow.get_destination()
        dst_node = self.RM_instance.node_network.get_Node(dst_node_id)
        
        # notify the destination node that the data has finished transmitting
        self.env.process(self._interruptNodeAfterDelay(dst_node, flow.get_id()))
        
        return []
        
                                                
    ########################################
    ## Helper functions
    ########################################  
    
    
    def _interruptNodeAfterDelay(self, node, flwid):
        yield self.env.timeout(SimParams.INTERRUPT_NODE_AFTER_DELAY)   # delay
        node.processInstance.interrupt('FLWCOMPLETE_'+str(flwid))
        
    # we assume all tasks in the input buff are unscheduled
    def _getAllUnscheduledTaskID_In_InputBuff(self, ib_id): 
        #print self.RM_instance.input_buffers[ib_id].get_BufferItemsList().values()       
        #result =  [x for x in self.RM_instance.input_buffers[ib_id].get_BufferItemsList().values() if ((x.get_initiallyScheduled() == False))]
        
        result = self.RM_instance.input_buffers[ib_id].get_BufferItemsList().values()
        
        #print result        
        if(len(result) > 0):
            return result
        else:
            return None
        
        
    #######################################
    ## Cleanup functions for: 
    ## - task mapping table
    ## - flow table
    #######################################
        
    
    
    ######################################################
    # Shared resources locking mechanisms
    #  - RM task mapping table
    #  - RM flow table
    ######################################################
    
        
        
        
        
        
    