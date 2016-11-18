import pprint
import sys
import random
import itertools
import datetime, time
import simpy
from collections import OrderedDict

## local imports

from libBuffer.Buffer import Buffer
from libProcessingElement.CPUNode_OpenLoop import CPUNode_OpenLoop
from libProcessingElement.CPUNode_ClosedLoop_woIBuffering import CPUNode_ClosedLoop_woIBuffering
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

class RunTimeTaskManager_ClosedLoop_woIBuffering(RunTimeTaskManager_ClosedLoop_wIBuffering):
    
    def __init__(self, env, polling_delay, mapping_policy, 
                 node_network, input_buffers, output_buffer, 
                 interconnect,
                 task_dispatcher, run_simpy_process = True):  
        
        RunTimeTaskManager_ClosedLoop_wIBuffering.__init__(self, env, polling_delay, mapping_policy, 
                 node_network, input_buffers, output_buffer, 
                 interconnect,
                 task_dispatcher, run_simpy_process=False)
        
        self.label = "ResourceManager_ClosedLoop_woIBuffering::"
        
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
       
        while True:
            self.status = RMStatus.RM_ACTIVE
            #print(self.label + ' : waking up and doing work at:  %f' % self.env.now)
            
            ## perform task mapping ##
            # the RM will map a block of N tasks at once (specified in SimParams)
            if(self._allInputBuffers_Empty() == False):                
                
                
                #print "here 1 "
                ### SCHEDULE and MAP : combined
                ### we are going to release all tasks of this jobs right away, and let the cpu nodes
                ### deal with when to run them, depending on their priorities
                
                self.Mapper.mapNewGoPTasks()    # take mapping selection from the stream mapping table
                
                self.Mapper.scheduleTasks()
                
                ## find if there is any tasks that should be released now.
                for each_inbuff_id in xrange(len(self.input_buffers)):                   
                    for (each_task_key, each_task_val) in self.input_buffers[each_inbuff_id].get_BufferItemsList().items():
                        next_task_to_map = self.input_buffers[each_inbuff_id].get_BufferItemsList()[each_task_key]
                        #print next_task_to_map
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
                                    if(isinstance(node_to_map, CPUNode_ClosedLoop_woIBuffering) == True):
                                        result = node_to_map.add_Task(next_task_to_map)
                                        
                                        # track the task release
                                        self.track_taskRelease(next_task_to_map, node_to_map)
                                        
                                        if(result == False):
                                            self.showTaskMappingTable(nodeid=node_to_map.get_id())
                                            sys.exit()                                            
                                    else:
                                        print("%f"%self.env.now + "," + self.label + "," + 'run::, : Not a CPU node (node_id: '+ str(node_to_map_id)  +')')
                                        self.showTaskMappingTable()
                                        print type(node_to_map)
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
    ## Simulation interaction
    ##########################################################################################################################
        
    
    ##########################################################################################################################
    ## For Debug
    ##########################################################################################################################
            
    
    
    ##########################################################################################################################
    # Runtime application management
    ##########################################################################################################################
    
    
    
    ##########################################################################################################################
    # Related to tracking
    ##########################################################################################################################


