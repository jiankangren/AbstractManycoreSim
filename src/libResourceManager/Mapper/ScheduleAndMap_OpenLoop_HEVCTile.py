import pprint
import sys
import itertools
import simpy
import random
from operator import itemgetter
import traceback

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
from ScheduleAndMap_OpenLoop import ScheduleAndMap_OpenLoop 



class ScheduleAndMap_OpenLoop_HEVCTile(ScheduleAndMap_OpenLoop):
    
    def __init__(self, env, RM_instance):  
        
        ScheduleAndMap_OpenLoop.__init__(self, env, RM_instance)
        self.label = "ScheduleAndMap_OpenLoop_HEVCTile"        
        
       
    # map all unmapped tasks in the input buffers
    def mapNewGoPTasks(self, all_ibuff_tasks):
        print "mapNewGoPTasks:: Enter"
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
                self.mapNewGoPTasks_FullyDynamicMapping_withoutMSSignalling(each_task_id, 
                                                                           i_buff_id, 
                                                                           wf_id, stream_id, gop_fr_ix, Ti,
                                                                           task_status = TaskStatus.TASK_MAPPED,
                                                                           task_release_time = self.env.now)
        
        #print "mapNewGoPTasks:: Exit"
                        
                
    
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
                    
                    # higher flow pri numbers == lower priority                       
                    priority = each_task.get_priority() + (self.RM_instance.flow_priority_offset+100) + nextid
                    #priority = sys.maxint - (each_task.get_priority() + (self.RM_instance.flow_priority_offset+100) + nextid)                    
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
        
    
    
    # map the tile tasks, copy from video stream mapping table to local task mapping table
    def mapNewGoPTasks_FullyDynamicMapping_withoutMSSignalling(self, each_task_id, i_buff_id, wf_id, stream_id, gop_fr_ix, Ti, 
                                                              task_status = TaskStatus.TASK_NULL,
                                                              task_release_time = None):
        # is task already mapped ?                
        if Ti.get_id() not in self.RM_instance.task_mapping_table:            
            try:
                selected_node_id = self.RM_instance.vidstream_frames_mapping_table[wf_id][stream_id]['frames_mapping'][Ti.get_id()] 
                #print selected_node_id               
                tm_entry = {
                                'node_id' : selected_node_id,
                                'release_time' : task_release_time,                            
                                'wcc' : Ti.get_worstCaseComputationCost(),
                                'status' : task_status,
                                'pri' : Ti.get_priority(),
                                'deps_completed' : [],
                                'strm_key' : "%d_%d_%d" % (Ti.get_wfid(), Ti.get_video_stream_id(), Ti.get_unique_gop_id())
                                }                                                        
                self.RM_instance.task_mapping_table[Ti.get_id()] = tm_entry 
                self.volatileTaskMappingTable_addEntry(tm_entry, Ti) # add to volatile table, used for openloop mapping   
                
                #print "mapNewGoPTasks_FullyDynamicMapping_withoutMSSignalling : mapped tid = ", Ti.get_id()
                            
            except Exception, e:
                traceback.print_exc()
                print self.env.now
                pprint.pprint(self.RM_instance.vidstream_frames_mapping_table)
                print "ti_id =" + str(Ti.get_id())
                print Ti.get_parentGopId()
                print (wf_id, stream_id)
                pprint.pprint(self.RM_instance.input_buffers[i_buff_id].get_BufferItemsList().items())
                sys.exit(self.label + "::" + 'mapNewGoPTasks:: mapNewGoPTasks_FullyDynamicMapping_withoutMSSignalling: error !!')
    
    
    
                                            
    ########################################
    ## Helper functions
    ########################################  
        
        
    #######################################
    ## Cleanup functions for: 
    ## - task mapping table
    ## - flow table
    #######################################
        
    ## this gets called when a MS signalling flow has completed
    # this function looks at the payload metadata to find the information
    def MSSignallingFlowComplete(self, flow, type):
        
        Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'MSSignallingFlowComplete::, : Enter - flowid='+str(flow.get_id()), DebugCat.DEBUG_CAT_MAPPERINFO)
        
        if(type == FlowType.FLOWTYPE_MASTERSLAVESIGNALLING_TASKCOMPLETE):
            payload_metadata = flow.get_payload_metadata()            
            finished_task_id = payload_metadata['finished_task_id']
            node_id = payload_metadata['node_id']
            strm_info_wfid = payload_metadata['finished_task_strm_info'][0]
            strm_info_vidid = payload_metadata['finished_task_strm_info'][1]
            finished_task_cc = payload_metadata['finished_task_info'][0]
            finished_task_ftype = payload_metadata['finished_task_info'][1]
            finished_task_pri = payload_metadata['finished_task_info'][2]
            
            if(finished_task_id in self.RM_instance.task_mapping_table):
                self.RM_instance.task_mapping_table[finished_task_id]['status'] = TaskStatus.TASK_COMPLETED
            
            # update the valatile tm table
            self.volatileTaskMappingTable_RemoveSpecificTask(finished_task_id, node_id)
            
            # update rm task complete cc tracking table
            self._update_task_completed_info(strm_info_wfid, strm_info_vidid, finished_task_ftype, finished_task_cc)
            
        else:
            sys.exit(self.label+":: MSSignallingFlowComplete : error")
        
        return []
    
    
    def _update_task_completed_info(self, wf_id, vid_id, ftype, t_cc):
        key = "%d_%d"%(wf_id,vid_id)        
        if key not in self.RM_instance.completed_task_monitoring_info:
            self.RM_instance.completed_task_monitoring_info[key]={}        
        if ftype not in self.RM_instance.completed_task_monitoring_info[key]:
            self.RM_instance.completed_task_monitoring_info[key][ftype] = []
        
        self.RM_instance.completed_task_monitoring_info[key][ftype].append(t_cc)
        
            
       
    
    ######################################################
    # Shared resources locking mechanisms
    #  - RM task mapping table
    #  - RM flow table
    ######################################################
    
        
        
        
        
        
    