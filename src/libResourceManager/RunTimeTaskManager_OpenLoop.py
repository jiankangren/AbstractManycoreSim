import pprint
import sys
import json
import random
import itertools
import datetime, time
import simpy
from collections import OrderedDict

## local imports

from libBuffer.Buffer import Buffer
from libProcessingElement.CPUNode_OpenLoop import CPUNode_OpenLoop
from libProcessingElement.Node import NodeStatus
from libApplicationModel.MPEG2FrameTask import MPEG2FrameTask
from libNoCModel.NoCFlowTable import NoCFlowTable
from libNoCModel.NoCFlow import NoCFlow, FlowType
from AdmissionControllerOptions import AdmissionControllerOptions
from libDebug.Debug import Debug, DebugCat
from libResourceManager.Mapper.ScheduleAndMap_ClosedLoop_wIBuffering import ScheduleAndMap_ClosedLoop_wIBuffering
from libApplicationModel.Task import TaskStatus
from RuntimeApplicationInfo import RuntimeApplicationInfo, VideoStreamInfo
from libNoCModel.NoCSchedulabilityAnalysis import NoCSchedulabilityAnalysis
from libMappingAndScheduling.SemiDynamic.TaskMappingSchemesImpl import TaskMappingSchemesImpl
from libMappingAndScheduling.SemiDynamic.TaskSemiDynamicPrioritySchemesImpl import TaskSemiDynamicPrioritySchemesImpl
from libMappingAndScheduling.SemiDynamic.TaskMappingAndPriAssCombinedSchemesImpl import TaskMappingAndPriAssCombinedSchemesImpl
from libMappingAndScheduling.Decentralised.PSAlgorithm import PSAlgorithm
from libMappingAndScheduling.Decentralised.PSAlgorithmViewer import PSAlgorithmViewer
from RunTimeTaskManager_ClosedLoop_wIBuffering import RunTimeTaskManager_ClosedLoop_wIBuffering, RMStatus
from libResourceManager.Mapper.ScheduleAndMap_OpenLoop import ScheduleAndMap_OpenLoop
from SimParams import SimParams

class RunTimeTaskManager_OpenLoop(RunTimeTaskManager_ClosedLoop_wIBuffering):
    
    def __init__(self, env, polling_delay, mapping_policy, 
                 node_network, input_buffers, output_buffer, 
                 interconnect,
                 task_dispatcher, run_simpy_process = True):  
        
        RunTimeTaskManager_ClosedLoop_wIBuffering.__init__(self, env, polling_delay, mapping_policy, 
                 node_network, input_buffers, output_buffer, 
                 interconnect,
                 task_dispatcher, run_simpy_process=False)
        
        self.label = "ResourceManager_OpenLoop::"
        
        # Start the run process everytime an instance is created.        
        if(run_simpy_process==True):
            self.processInstance = env.process(self.run())
        
        
    ##########################################################################################################################
    ## Getters/Setters
    ##########################################################################################################################
    
        
    ##########################################################################################################################
    ## Main execution loop
    ##########################################################################################################################  
    def run(self):
        
        print("%f"%self.env.now + "," + self.label + "," + ' : run starting')
        list_of_nodes_to_interrupt = []
        list_of_data_transfers = []
        
        while True:
            self.status = RMStatus.RM_ACTIVE
            #print(self.label + ' : waking up and doing work at:  %f' % self.env.now)
            
            ## perform task mapping ##
            # the RM will map a block of N tasks at once (specified in SimParams)
            #if(self._allInputBuffers_Empty() == False):
            if(self._hasLastTaskBeenDispatched() == False):                

                ### SCHEDULE and MAP : combined
                ### we are going to release all tasks of this jobs right away, and let the cpu nodes
                ### deal with when to run them, depending on their priorities
                
                # get all tasks in ibuffs
                all_ibuff_tasks = list(itertools.chain.from_iterable([sublist.get_BufferItemsList().values() for sublist in self.input_buffers]))
                
                #for each_ib in self.input_buffers:
                #    pprint.pprint(each_ib.get_BufferItemsList().values())
                
                
                if len(all_ibuff_tasks) == 0:
                    print self.label + ":: all_ibuff_tasks - empty"
                
                # map and schedule tasks
                self.Mapper.mapNewGoPTasks(all_ibuff_tasks)    # take mapping selection from the stream mapping table                
                self.Mapper.scheduleTasks(all_ibuff_tasks)
                
                ## find if there is any tasks that should be released now.                        
                for each_task in all_ibuff_tasks:
                    each_task_val = each_task
                    each_task_key = each_task.get_id()
                    each_inbuff_id = each_task.get_wfid()
                    next_task_to_map = each_task_val
                    
                    #print next_task_to_map
                    
                    assert (each_task_val.get_releaseTime() != None), ":: the task was not scheduled properly - tid=%d" % each_task_val.get_id()
                    
                    if(each_task_val.get_releaseTime() == self.env.now): # release time set in Mapper.scheduleTasks()
                        if(each_task_key in self.task_mapping_table):                        
                            node_to_map_id = self.task_mapping_table[each_task_key]['node_id']
                  
                            if(node_to_map_id != None):
                                node_to_map = self.node_network.get_Nodes()[node_to_map_id]
                            else:
                                print(self.label + ' : node_id is None, at: ' + str(self.env.now) )                                   
                                sys.exit()

                            if(node_to_map != None):
                                
                                Debug.PPrint("%f"%self.env.now + "," + self.label + "," + 'run::, : releasing task=%s, to nodeid=%d' % (str(each_task_key),node_to_map_id), DebugCat.DEBUG_CAT_RMINFO)                                    
                                list_of_data_transfers.append(
                                                              {
                                                               'task' : next_task_to_map,
                                                               'node' : node_to_map,
                                                               'ibuff_id' : each_inbuff_id
                                                               }
                                                              )

                            else:
                                Debug.PPrint("%f"%self.env.now + "," + self.label + "," + 'run::, : All nodes are BUSY!', DebugCat.DEBUG_CAT_RMINFO)
                                #i=1
                        else:
                            print(self.label + ' ERROR: task ' + str(each_task_key) + ' not yet mapped, but ready to be released - at: '+ str(self.env.now))
                            sys.exit()
                            
                    else:
                        #print(self.label + ' WARNING : task ' + each_task_key + 
                        #      ' already released and waiting MMC transfer -  t_rt= %.16f, now= %.16f' %(each_task_val.get_releaseTime(), self.env.now))
                        
                        if (each_task.get_id() not in self.mmc.mmc_to_node_data_transfer_started_task_ids):
                            sys.exit("Error : task not in mmc transfer queue, so release time is incorrect..")
                            
                                   
                    
                
                # transmit the tasks - to the PEs
                if(SimParams.MMC_ENABLE_DATATRANSMISSION_MODELLING == True):
                    self.mmc.startListofTaskDataTransfers(list_of_data_transfers)
                else:
                    self.mmc.startListofTaskDataTransfers_NonModelled(list_of_data_transfers)
                
                list_of_data_transfers = []             
                
            else:
                Debug.PPrint("%f"%self.env.now + "," + self.label + "," + 'run::, : Inputbuffers empty!', DebugCat.DEBUG_CAT_RMINFO_VERBOSE)
                
            ## go back to sleep - can be interrupted
            try:
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
                #print "-- RM interrupted at %.15f" % self.env.now
                    
                    
               
    
    ##########################################################################################################################
    ## Simulation interaction
    ##########################################################################################################################
        
    
    ##########################################################################################################################
    ## For Debug
    ##########################################################################################################################
            
    
    
    ##########################################################################################################################
    # Runtime application management
    ##########################################################################################################################
    
    def received_Remapping_Request(self, flow_payload):
        #pprint.pprint(flow_payload)
        Debug.PPrint("%f"%self.env.now + "," + self.label + "," + \
                     'received_Remapping_Request::, : task:%d, o_nid:%d, n_nid:%d' % (flow_payload[0]['remapped_task'].get_id(),
                                                                                       flow_payload[0]['remapped_old_node_id'],
                                                                                       flow_payload[0]['remapped_new_node_id']
                                                                                       ), DebugCat.DEBUG_CAT_TASKREMAPPING_NOTIFICATION)
        
        for each_remapping_tuple in flow_payload:
            
            task_id = each_remapping_tuple['remapped_task'].get_id()
            wf_id = each_remapping_tuple['remapped_task'].get_wfid()
            strm_id = each_remapping_tuple['remapped_task'].get_video_stream_id()
            frame_gopix = each_remapping_tuple['remapped_task'].get_frameIXinGOP()
            old_node_id = each_remapping_tuple['remapped_old_node_id']
            new_node_id = each_remapping_tuple['remapped_new_node_id']
            
            ## update task-mapping table on RM
            if wf_id in self.vidstream_frames_mapping_table:            
                if(strm_id in self.vidstream_frames_mapping_table[wf_id]):                
                    self.vidstream_frames_mapping_table[wf_id][strm_id]['frames_mapping'][frame_gopix] = new_node_id
                else:
                    sys.exit(self.label +  "::received_Remapping_Request: error, strm_id does not exist")
            else:
                sys.exit(self.label +  "::received_Remapping_Request: error, wf_id does not exist")            
            
            ## update runtime app data structures            
            (updated_task, old_node_id) = self.RunTimeApps.updateTaskProcessingCore(frame_gopix, 
                                                                    wf_id, 
                                                                    strm_id, 
                                                                    new_node_id)                        
            if(updated_task != None) and (old_node_id!= None):
                # update runtime app - task to node mapping table
                self.RunTimeApps.updateTaskToNodeMappingTbl(updated_task,old_node_id,new_node_id)
                
    
        return []
    
    
    
    
    ##########################################################################################################################
    # Related to tracking
    ##########################################################################################################################


