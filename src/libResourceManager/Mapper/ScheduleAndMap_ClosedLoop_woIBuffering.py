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
from libMappingAndScheduling.FullyDynamic.TaskMappingSchemesFullyDynImpl import TaskMappingSchemesFullyDynImpl


class ScheduleAndMap_ClosedLoop_woIBuffering(ScheduleAndMap_ClosedLoop_wIBuffering):
    
    def __init__(self, env, RM_instance):  
        
        ScheduleAndMap_ClosedLoop_wIBuffering.__init__(self, env, RM_instance)
        self.label = "ScheduleAndMap_ClosedLoop_woIBuffering"
        self.FullyDynamicMappingHandler =  TaskMappingSchemesFullyDynImpl(self.env, self.RM_instance)       
        
       
    # map all unmapped tasks in the input buffers
    def mapNewGoPTasks(self):
        
        if (SimParams.MAPPING_PREMAPPING_ENABLED == True):
            for i_buff_id in xrange(len(self.RM_instance.input_buffers)):            
                wf_id = i_buff_id            
                for (each_task_id, each_task) in self.RM_instance.input_buffers[i_buff_id].get_BufferItemsList().items():
                    Ti = each_task
                    stream_id = Ti.get_video_stream_id()
                    gop_fr_ix = Ti.get_frameIXinGOP()
                    
                    ## SEMI_DYNAMIC_APPROACH : ## 
                    # in this mode, we assume all the tasks of a video stream
                    # is premapped upon admission of the video stream
                    self.mapNewGoPTasks_SemiDynamicMapping_withoutMSSignalling(each_task_id, 
                                                                                   i_buff_id, 
                                                                                   wf_id, stream_id, gop_fr_ix, Ti,
                                                                                   task_status = TaskStatus.TASK_MAPPED,
                                                                                   task_release_time = self.env.now)
            
        
        else:
            # collect unmapped tasks
            unmapped_tasks = []
            for i_buff_id in xrange(len(self.RM_instance.input_buffers)):            
                wf_id = i_buff_id            
                for (each_task_id, each_task) in self.RM_instance.input_buffers[i_buff_id].get_BufferItemsList().items():
                    unmapped_tasks.append(each_task)
            
            # no new unmapped tasks ??
            if len(unmapped_tasks) != 0:            
                # check if all tasks are part of the same stream and gop
                if len(unmapped_tasks) != len(unmapped_tasks[0].get_gopstructure()):
                    sys.exit(self.label + "::mapNewGoPTasks: error ! invalid number of unmapped tasks")
                else:                
                    stream_specs = self._getStreamSpecs(unmapped_tasks[0])
                    
                    # map stream tasks
                    frame_mappings = self.FullyDynamicMappingHandler.taskMappingSchemeHandler(stream_specs)
                
           
                    for each_t in unmapped_tasks:
                        Ti = each_t
                        wf_id = Ti.get_wfid()
                        stream_id = Ti.get_video_stream_id()
                        gop_fr_ix = Ti.get_frameIXinGOP()
                        ## FULLY_DYNAMIC_APPROACH : ##
                        # in this mode, we assume all the jobs of a video stream are assigned mapping,
                        # when they are dispatched by the task dispatcher, not beforehand.                
                        self.mapNewGoPTasks_FullyDynamicMapping_withoutMSSignalling_v2(wf_id, stream_id, gop_fr_ix, Ti, 
                                                                      task_status = TaskStatus.TASK_NULL,
                                                                      task_release_time = None)
                    
                
    
    # go through all unscheduled tasks and schedule them to be released NOW.
    def scheduleTasks(self):
        
        for i_buff_id in xrange(len(self.RM_instance.input_buffers)):
            # get unscheduled iframe from this input buffer
            unscheduled_tasks = self._getAllUnscheduledTaskID_In_InputBuff(i_buff_id)
            if unscheduled_tasks != None:
                for Ti in unscheduled_tasks:
                        
                    if(Ti != None): 
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
                                        'deps_completed' : []
                                        }                                                        
                            self.RM_instance.task_mapping_table[Ti.get_id()] = tm_entry
                                
                            ## update input buffer task
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
            
            
    ## this gets called when a flow has completed ##
    def DataFlowComplete(self, flow):
        
        Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'DataFlowComplete::, : Enter - flowid='+str(flow.get_id()), DebugCat.DEBUG_CAT_MAPPERINFO)
        
        # set the status of the task in dep buffer to transmission complete
        dst_node_id = flow.get_destination()
        dst_node = self.RM_instance.node_network.get_Node(dst_node_id)
        
        # notify the destination node that the data has finished transmitting
        #dst_node.processInstance.interrupt('FLWCOMPLETE_'+str(flow.get_id()))
        self.env.process(self._interruptNodeAfterDelay(dst_node, flow.get_id(), message='FLWCOMPLETE_'+str(flow.get_id())))
        
        # notify RM regarding data flow completion, RM needs to update it's global view
        self.env.process(self._notifyRMRegardingDataFlowCompletion_viaAnotherFlow_AfterDelay(flow))
        
        return []
        
    
    
    ## this gets called when a MS signalling flow has completed
    # this function looks at the payload metadata to find the information
    def MSSignallingFlowComplete(self, flow, type):
        
        Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'MSSignallingFlowComplete::, : Enter - flowid='+str(flow.get_id()), DebugCat.DEBUG_CAT_MAPPERINFO)
        
        if(type == FlowType.FLOWTYPE_MASTERSLAVESIGNALLING_TASKCOMPLETE):
            payload_metadata = flow.get_payload_metadata()            
            finished_task_id = payload_metadata['finished_task_id']
            node_id = payload_metadata['node_id']
            if(finished_task_id in self.RM_instance.task_mapping_table):
                self.RM_instance.task_mapping_table[finished_task_id]['status'] = TaskStatus.TASK_COMPLETED
            
            # update the valatile tm table
            self.volatileTaskMappingTable_RemoveSpecificTask(finished_task_id, node_id)
            
            
        elif(type == FlowType.FLOWTYPE_MASTERSLAVESIGNALLING_FLOWCOMPLETE):
            # mark dependancies
            # this completed flow may serve two dependancies - need to take this into account
            src_task_id = flow.get_payload_metadata()['finished_flow_src_task_id']
            dst_task_ids = flow.get_payload_metadata()['finished_flow_dst_task_ids']            
        
            for dst_task_id in dst_task_ids:            
                if(src_task_id not in self.RM_instance.task_mapping_table[dst_task_id]['deps_completed']):
                    self.RM_instance.task_mapping_table[dst_task_id]['deps_completed'].append(src_task_id)
        else:
            sys.exit(self.label+":: MSSignallingFlowComplete : error")
        
        return []
        
                                                
    ########################################
    ## Helper functions
    ########################################
    def _getStreamSpecs(self, task):
        video_specs = {
               "wf_id" : task.get_wfid(),
               "vid_strm_id" : task.get_video_stream_id(),
               "frame_h" : task.get_frame_h(),
               "frame_w" : task.get_frame_w(),
               "fps" : task.get_framerate(),
               "gop_struct" : task.get_gopstructure(),
               "wcc_I" : task.get_wccIFrame(),
               "wcc_P" : task.get_wccPFrame(),
               "wcc_B" : task.get_wccBFrame(),
               "avgcc_I" : task.get_avgccIFrame(),
               "avgcc_P" : task.get_avgccPFrame(),
               "avgcc_B" : task.get_avgccBFrame(),               
               "decoded_frame_size" : task.get_completedTaskSize()                
               }
        return video_specs
    
      
    def _interruptNodeAfterDelay(self, node, flwid, message=""):
        yield self.env.timeout(SimParams.INTERRUPT_NODE_AFTER_DELAY)   # delay
        node.processInstance.interrupt(message)
    
    
    
    def _notifyRMRegardingDataFlowCompletion_viaAnotherFlow_AfterDelay(self, completed_flow):
        
        if(SimParams.MS_SIGNALLING_NOTIFY_FLOW_COMPLETE_ENABLE == True):
                
            yield self.env.timeout(SimParams.INTERRUPT_RM_AFTER_DELAY)   # delay (to stop flow being updated too quickly)
            
            Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'_notifyRMRegardingDataFlowCompletion_viaAnotherFlow_AfterDelay::, : finished_flow='+str(completed_flow.get_id()), DebugCat.DEBUG_CAT_MSSIGNALLING)
            
            ## notify the RM regarding flow completion (emit another flow to RM)        
            src_task_id =  completed_flow.get_respectiveSrcTaskId()
            dst_task_ids = []    # could be alot of dst tasks, mapped on the same dst core
            dst_task_ids =  completed_flow.get_respectiveDstTaskId()        
            
            # construct flow
            src_node_id = completed_flow.get_destination()
            dst_node_id = SimParams.RESOURCEMANAGER_NODEID
            release_time = self.env.now
            nextid = self.RM_instance.flow_table.nextid                    
            route = self.RM_instance.interconnect.getRouteXY(dst_node_id, src_node_id)
            priority = SimParams.NOC_FLOW_MS_SIGNALLING_MAXPRIORITY + nextid
            basic_latency = self.RM_instance.interconnect.getRouteCostXY(dst_node_id, 
                                                                        src_node_id,
                                                                        SimParams.NOC_PAYLOAD_32BYTES)
            payload = SimParams.NOC_PAYLOAD_32BYTES
            endTime_wrt_BL = release_time + basic_latency
            payload_metadata = {
                                'finished_flow_id' : completed_flow.get_id(),
                                'finished_flow_endtime' : self.env.now,
                                'finished_flow_src_task_id' : src_task_id,
                                'finished_flow_dst_task_ids' : dst_task_ids
                                }
                        
            newflow = NoCFlow(nextid,
                           None,
                           None,
                           None, # list of dst task ids
                           None, # list of dst task ixs
                           src_node_id, 
                           dst_node_id, 
                           route,
                           priority, 
                           None, 
                           basic_latency, 
                           payload,
                           endTime_wrt_BL,
                           type=FlowType.FLOWTYPE_MASTERSLAVESIGNALLING_FLOWCOMPLETE,                           
                           payload_metadata=payload_metadata)
            
            
            self.lock_RM_FLWtbl()
            # add to the flow table
            self.RM_instance.flow_table.addFlow(newflow, release_time, basic_latency)               
            self.release_RM_FLWtbl()
            
            # update the table        
            self.RM_instance.flow_table.updateTable(fire=True)  
            
        
        
        
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
    
    
        
        
        
        
    