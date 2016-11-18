import pprint
import sys
import copy

import simpy

## local imports
from Node import Node
from CPUNode_ClosedLoop_wIBuffering import CPUNode_ClosedLoop_wIBuffering
from CPUNode_OpenLoop_HEVC_FrameLvl import CPUNode_OpenLoop_HEVC_FrameLvl
from SimParams import SimParams
from Node import NodeStatus
from libApplicationModel.Task import TaskModel, TaskStatus
from libMappingAndScheduling.Decentralised.PSAlgorithm import PSAlgorithmProps 
from libMappingAndScheduling.Decentralised.TaskRemapDecentSchemesImpl import TaskRemapDecentSchemesImpl

from libBuffer.Buffer import Buffer, BufferType
from libDebug.Debug import Debug, DebugCat


class CPU_RMStatus:
    RM_SLEEPING       = 1     # i.e sleeping
    RM_BUSYWAITING    = 2     # i.e waiting for someone else/resource
    RM_BUSY           = 3     # i.e busy computing
    RM_ACTIVE         = 4     # i.e. ready and doing work    
    NODE_JUSTWOKEUP   = 5


class CPUNode_OpenLoop_HEVC_TileLvl(CPUNode_OpenLoop_HEVC_FrameLvl):
    
    def __init__(self, env, id, tq_size, run_simpy_process = True):
        CPUNode_OpenLoop_HEVC_FrameLvl.__init__(self, env, id, tq_size, run_simpy_process=False)
        
        self.label = "CPUNode_OpenLoop_HEVC_TileLvl" + "-" + str(self.id)
        
        # Start the run process everytime an instance is created.
        if(run_simpy_process == True):        
            p = env.process(self.run_HEVCTileTask_ExecutionLoop())
            self.set_processInstance(p)        
    
            
    
    #######################    
    # task queue management
    #######################
    
        
    #######################    
    # Buffer management
    #######################    
    
    def dependencyBuff_put(self, completed_task, target_task_id, data_size):
        assert (completed_task != None)
        assert (target_task_id != None)
        #print "completed_task.get_id(): ", completed_task.get_id()
        
        # key --> target task id that needs the dep
        # item --> parent task id 
        
        if(self.dependency_buff.isFull() == False):                         
            
            # put to dep buffer
            self.dependency_buff.append_Item(completed_task.get_id(), target_task_id)            
            self.dependency_buff.simpy_container_instance.put(1)
            
            # check and mark task deps fullfilled
            self.scheduler.markTasksDeps(completed_task.get_id(), 
                                         target_task_id, 
                                         self.taskQueue, 
                                         self.dependency_buff.get_BufferItemsList(),
                                         time_now=self.env.now)
            
            
            return True # successfully entered into buff
        else:            
            return False # buffer is full
    
       
######################################################
#    TASK EXECUTION LOOPS
######################################################

    # non-preemptive - event triggered
    def run_HEVCTileTask_ExecutionLoop(self):
        Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'run_HEVCTileTask_ExecutionLoop::, : run starting', DebugCat.DEBUG_CAT_CPUINFO)
        task_tq_ix = 0
        while True:
            # set node status
            self.status = NodeStatus.NODE_ACTIVE
            #######################################################
            ## check taskq, select next task to execute based on
            ## local scheduling policy
            #######################################################
            if(self.isTaskQEmpty() == False):
                
                # set node status
                self.status = NodeStatus.NODE_ACTIVE
                
                # get next task from scheduler
                (task_tq_ix, task) = self.scheduler.nextTask(self.taskQueue, task_tq_ix, self.dependency_buff.get_BufferItemsList(), self.env.now)
                
                if (task != None):                
                    ## process the next task ##
                    
                    # set task start-time, remaining time
                    if(task.get_taskStartTime() == None):
                        task.set_taskStartTime(self.env.now)
                        self.taskQueue[task_tq_ix].set_taskStartTime(self.env.now)
                        
                    #Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'run_HEVCTileTask_ExecutionLoop::, : Now running Task - %s' % (task._debugShortLabel()), DebugCat.DEBUG_CAT_CPUINFO)
                    
                    # pre-emptive mode, therefore task runs till completion or until interrupted     
                    # task execution time can be at different granularities
                    # if the task is 
                    try:                                    
                        ##############################
                        ## Start computation
                        ##############################                        
                        # set task status
                        self.track_TaskExecution(task, "run")
                        self.status = NodeStatus.NODE_BUSY    # set node status
                        self.setTaskStatus(task_tq_ix, task.get_id(), TaskStatus.TASK_RUNNING)                                                               
                        
                        starttime_task_computation = self.env.now                  
                        
                        self.currentRunningTaskID = task   # set current running task
                        runtime = self.taskQueue[task_tq_ix].getRemainingCTU_ComputationCost()                 
                        
                         
                        if (runtime > 0):  
                            yield self.env.timeout(runtime)                        
                        
                        #Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'run_HEVCTileTask_ExecutionLoop::, : Finished task sub processing unit - %s' % (task._debugShortLabel()), DebugCat.DEBUG_CAT_CPUINFO)
                        #Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'run_HEVCFrameTask_ExecutionLoop::, : Finished task sub processing unit - %s' % (task._debugShortLabel()), DebugCat.DEBUG_CAT_CPUINFO_VERBOSE)
                        
                        
                        ##############################
                        ## CTU execution completed
                        ##############################
                        
                        hevc_task_next_processing_unit_ref = task.getNextProcessingUnitRef()
                        
                        completed_processing_unit_ref = task.getCurrentlyProcessingUnitRef()
                        self.track_CompletedCTUs(completed_processing_unit_ref, task)
                                                
                        if(hevc_task_next_processing_unit_ref != None): # we need to process the next unit, unless there is no more
                            task.setRemainingCTU_ComputationCost(0)
                            
                            # this sets the next processing unit properties
                            self.taskQueue[task_tq_ix].setCurrentlyProcessingUnitRef(hevc_task_next_processing_unit_ref)
                            continue
                        
                        else:                             
                            Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'run_HEVCTileTask_ExecutionLoop::, : Finished Complete Task (Tile) - %s' % (task._debugShortLabel()), DebugCat.DEBUG_CAT_CPUINFO)
                            
                            ##############################
                            ## Full Task completed
                            ##############################
                            task.nullifyCurrentlyProcessingUnitRef()     # clear refs
                            self.status = NodeStatus.NODE_IDLE  # set node status
                                    
                            ##############################
                            ## Set task specific params 
                            ##############################
                            self.track_TaskExecution(task, "end")                    
                            # set task complete time
                            task.set_taskCompleteTime(self.env.now)
                            self.taskQueue[task_tq_ix].set_taskCompleteTime(self.env.now)
                            self.taskQueue[task_tq_ix].set_remainingComputationCost(0.0)
                            #self.update_SystemSlack_setEndTime(task, self.env.now)
                            self.update_SystemSlack_setTaskStartEnd(task, 
                                                                    self.taskQueue[task_tq_ix].get_taskStartTime(), 
                                                                    self.taskQueue[task_tq_ix].get_taskCompleteTime(),
                                                                    self.taskQueue[task_tq_ix].get_dispatchTime(),
                                                                    self.taskQueue[task_tq_ix].get_computationCost())
                            
                            ##############################
                            ## record task as completed
                            ############################## 
                            self.markTaskAsCompleted(task)
                            task.set_estimatedLateness(self.get_TaskLateness(task))
                            self.setTaskStatus(task_tq_ix, task.get_id(), TaskStatus.TASK_COMPLETED)
                            
                            # notify RM about task being complete
                            self.notifyRMTaskCompletion(task)
                          
                            ##############################
                            ## Task is now finished
                            ##############################
                            ## TODO:: (1) send output to other nodes - with induced network delay
                            self.sendCompletedPUToOtherNodes(task)                    
                            
                            ## (2) send output to output buffer
                            # update memory write
                            self.memWrite = self.memWrite + task.get_maxMemConsumption()
                            
                            # go to sleep for the time equal to writing to shared mem                    
                            self.status = NodeStatus.NODE_BUSY_DATAIO    # set node status
                            # remove from taskq
                            
                            #print(self.label + ' : Now removing task (%d)- at %f' % (task.get_id(), self.env.now))
                            self.remove_Task(task_tq_ix)                     
                            
                            # signal RM regarding end of stream processing
                            #self.notifyRM_endofStream(task)
                            
                            # signal cluster manager
                            self.ccpprops.updateCM_taskComplete(task)
                            
                            # send the completed task to the output buffer                        
                            if(SimParams.MMC_ENABLE_DATATRANSMISSION_MODELLING == True):
                                self.resource_manager_instance.mmc.startNodeToMMCDataTransfer(task, self)
                            else:
                                self.env.process(self.sendTaskToOutputBuffAfterDelay(task, task_tq_ix))
                            
                            # remove dependencies                    
                            self.dependencyBuff_cleanUp(task)
                    
                    
                    
                    ##############################
                    ## Interrupt Received
                    ##############################                         
                    ## interruption while task is being executed ##
                    except simpy.Interrupt:
                        
                        Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'run_HEVCTileTask_ExecutionLoop::, : I got interrupted !! but I was BUSY computing, tid=' + str(task.get_id()) , DebugCat.DEBUG_CAT_LOCALSCHED_PREEMPT)
                        
                        interrupttime_task_computation = self.env.now  
                        
                        #### task computation gets pre-empted by another higher priority task ####
                        # set the currently running task to null
                        self.currentRunningTaskID = None
                        
                        # suspend the task
                        self.setTaskStatus(task_tq_ix, task.get_id(), TaskStatus.TASK_SUSPENDED)
                        time_elapsed = interrupttime_task_computation -  starttime_task_computation
                        
                        # hevc-related computation time
                        self.updateTaskRemainingCTU_CC(task_tq_ix, time_elapsed)
                        
                        # update the remaining computation cost
                        #self.updateTaskRemainingCompCost(task_tq_ix)
                        #self.updateTaskWorstCaseRemainingCompCost(task_tq_ix)
                        #self.updateTaskAvgCaseRemainingCompCost(task_tq_ix)
                                       
                else: ## TASK-Q NOT EMPTY, but NO TASKS READY TO RUN !! 
                    try:
                        self.status = NodeStatus.NODE_IDLE # set node status       
                        node_idle_time_start = self.env.now           
                        #print(self.label + ' : my task-q is empty! at %d' % self.env.now)
                        yield self.env.timeout(self.IDLE_SLEEP_TIME)
                    except simpy.Interrupt as interrupt:
                        self.status = NodeStatus.NODE_JUSTWOKEUP # set node status
                        Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'run_HEVCTileTask_ExecutionLoop::, : I got interrupted, I was sleeping!', DebugCat.DEBUG_CAT_INTERRUPT) 
                    
                    node_idle_time_stop = self.env.now
                    # update node idle time
                    idle_duration = node_idle_time_stop - node_idle_time_start
                    self.track_idle_time += idle_duration
                    self.track_NodeIdlePeriods(idle_duration, False)
            else:   ## TASK-Q IS EMPTY !!
                try:                    
                    # set node status
                    self.status = NodeStatus.NODE_IDLE                    
                    node_idle_time_start = self.env.now
                    #print(self.label + ' : my task-q is empty! at %d' % self.env.now)
                    Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'run_HEVCTileTask_ExecutionLoop::, : task queue is empty!', DebugCat.DEBUG_CAT_CPUINFO)                    
                    yield self.env.timeout(self.IDLE_SLEEP_TIME)
                except simpy.Interrupt as interrupt:
                    self.status = NodeStatus.NODE_JUSTWOKEUP # set node status
                    Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'run_HEVCTileTask_ExecutionLoop::, : I got interrupted now - was sleeping!', DebugCat.DEBUG_CAT_INTERRUPT)
    
                node_idle_time_stop = self.env.now  
                # update node idle time
                idle_duration = node_idle_time_stop - node_idle_time_start
                self.track_idle_time += idle_duration                
                self.track_NodeIdlePeriods(idle_duration, True)

     
                
    
    
    ########################
    # tracking
    ########################
    
    




            
    
        