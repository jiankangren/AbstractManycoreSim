import pprint
import sys
import copy

import simpy

## local imports
from Node import Node
from CPUNode_ClosedLoop_wIBuffering import CPUNode_ClosedLoop_wIBuffering
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


class CPUNode_OpenLoop_HEVC_FrameLvl(CPUNode_ClosedLoop_wIBuffering):
    
    def __init__(self, env, id, tq_size, run_simpy_process = True):
        CPUNode_ClosedLoop_wIBuffering.__init__(self, env, id, tq_size, run_simpy_process=False)
        
        self.label = "CPUNode_OpenLoop_HEVC_FrameLvl" + "-" + str(self.id)
        
        # Start the run process everytime an instance is created.
        if(run_simpy_process == True):        
            p = env.process(self.run_HEVCFrameTask_ExecutionLoop())
            self.set_processInstance(p)        
    
            
    
    #######################    
    # task queue management
    #######################
    def updateTaskRemainingCTU_CC(self, tq_ix, elapsed_time):
        self.taskQueue[tq_ix].updateRemainingCTU_ComputationCost(elapsed_time)
        
    #######################    
    # Buffer management
    #######################    
    
    def dependencyBuff_getAll(self):
        return self.dependency_buff.get_BufferItemsList()
        
    
    def dependencyBuff_put(self, completed_task, target_task_id, data_size):
        assert (completed_task != None)
        assert (target_task_id != None)
        #print "completed_task.get_id(): ", completed_task.get_id()
        
        # key --> target task id that needs the dep
        # item --> parent task id 
        
        if(self.dependency_buff.isFull() == False):                         
            self.dependency_buff.append_Item(completed_task.get_id(), target_task_id)
            #self.dependency_buff.append_Item(target_task_id, completed_task.get_id())
            self.dependency_buff.simpy_container_instance.put(1)
            return True # successfully entered into buff
        else:            
            return False # buffer is full
    
    # old
    def dependencyBuff_put_v1(self, completed_task, target_task_id, data_size):
        if(self.dependency_buff.isFull() == False):             
            dep_entry = [target_task_id, data_size]
            self.dependency_buff.add_Item(dep_entry, completed_task.get_id())
            self.dependency_buff.simpy_container_instance.put(1)
            return True # successfully entered into buff
        else:            
            return False # buffer is full
    
    def dependencyBuff_getLevel(self):
        return len(self.dependency_buff.get_BuffContents())
        
    # this is a bit tricky
    # technically if two frames are depending on the same PU in another frame
    # then this needs to perform that check, however we ignore this scenario
    def dependencyBuff_IsTaskInBuff(self,task_id):              
        return False
    
    def dependencyBuff_setTaskStatus(self,task_id, status):        
        sys.exit("dependencyBuff_setTaskStatus:: not implemented yet!")
    
    def dependencyBuff_removeTask(self, task_id):
        #self.dependency_buff.remove_Item_byKey(task_id)
        #self.dependency_buff.simpy_container_instance.get(1)
        sys.exit("dependencyBuff_removeTask:: not implemented yet!")
    
    def dependencyBuff_removeDepPU(self, pu_id):
        #print pu_id
        self.dependency_buff.remove_Item_byKey(pu_id)
        self.dependency_buff.simpy_container_instance.get(1)
    
    def dependencyBuff_checkTaskDeps(self, task):
        sys.exit("dependencyBuff_checkTaskDeps:: not implemented yet!")
    
    
    def dependencyBuff_cleanUp(self, finished_task):
        if(finished_task.get_frameType()!="I"):
            #pprint.pprint(self.dependency_buff.get_BufferItemsList())        
            self.dependencyBuff_removeDepPU(finished_task.get_id())
    
    # old
    def dependencyBuff_cleanUp_v1(self, finished_task):        
        # get finished tasks, dependencies
        finished_task_parent_ids = finished_task.get_expected_data_from_parents().keys()
        
        # get all deps in dep buff with the correct key
        keys_to_rem = []
        for each_parent_id in finished_task_parent_ids:
            k = [k for k,v in self.dependency_buff.get_BufferItemsList().iteritems() 
                                if (k == each_parent_id) and (v[0]==finished_task.get_id())]
            if len(k) != 0:
                keys_to_rem.append(k)
                        
        for each_del_k in keys_to_rem:
            self.dependencyBuff_removeDepPU(each_del_k)
    
          
       
######################################################
#    TASK EXECUTION LOOPS
######################################################

    # non-preemptive - event triggered
    def run_HEVCFrameTask_ExecutionLoop(self):
        Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'run_HEVCFrameTask_ExecutionLoop::, : run starting', DebugCat.DEBUG_CAT_CPUINFO)
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
                        
                    Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'run_HEVCFrameTask_ExecutionLoop::, : Now running Task - %s' % (task._debugShortLabel()), DebugCat.DEBUG_CAT_CPUINFO)
                    
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
                        yield self.env.timeout(runtime)                        
                        
                        Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'run_HEVCFrameTask_ExecutionLoop::, : Finished task sub processing unit - %s' % (task._debugShortLabel()), DebugCat.DEBUG_CAT_CPUINFO_VERBOSE)
                        #Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'run_HEVCFrameTask_ExecutionLoop::, : Finished task sub processing unit - %s' % (task._debugShortLabel()), DebugCat.DEBUG_CAT_CPUINFO)
                        
                        
                        ##############################
                        ## CTU execution completed
                        ##############################
                        
                        hevc_task_next_processing_unit_ref = task.getNextProcessingUnitRef()
                                                
                        if(hevc_task_next_processing_unit_ref != None): # we need to process the next unit, unless there is no more
                            task.setRemainingCTU_ComputationCost(0)
                            completed_processing_unit_ref = task.getCurrentlyProcessingUnitRef()
                            self.track_CompletedCTUs(completed_processing_unit_ref, task)                            
                                                        
                            # this sets the next processing unit properties
                            self.taskQueue[task_tq_ix].setCurrentlyProcessingUnitRef(hevc_task_next_processing_unit_ref)
                            continue
                        
                        else: 
                            
                            Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'run_HEVCFrameTask_ExecutionLoop::, : Finished Complete Task - %s' % (task._debugShortLabel()), DebugCat.DEBUG_CAT_CPUINFO)
                            
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
                            self.notifyRM_endofStream(task)
                            
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
                        
                        Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'run_HEVCFrameTask_ExecutionLoop::, : I got interrupted !! but I was BUSY computing, tid=' + str(task.get_id()) , DebugCat.DEBUG_CAT_LOCALSCHED_PREEMPT)
                        
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
                                       
                else:
                    try:
                        # taskQ is not empty - but none of the tasks are ready to run (missing deps ??)
                        # so go to sleep
                        #Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'run_HEVCFrameTask_ExecutionLoop::, : : None of the tasks in this CPU, has all their deps, going to sleep', DebugCat.DEBUG_CAT_INTERRUPT)
#                        print(self.label + ' : None of the tasks in this CPU, has all their deps -  at %f' % self.env.now)
                        #pprint.pprint(self.taskQueue)
#                        pprint.pprint(self.resource_manager_instance.task_mapping_table)
#                        sys.exit()

                        self.status = NodeStatus.NODE_IDLE # set node status       
                        node_idle_time_start = self.env.now           
                        #print(self.label + ' : my task-q is empty! at %d' % self.env.now)
                        yield self.env.timeout(self.IDLE_SLEEP_TIME)
                    except simpy.Interrupt:
                        self.status = NodeStatus.NODE_JUSTWOKEUP # set node status
                        Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'run_HEVCFrameTask_ExecutionLoop::, : I got interrupted, I was sleeping!', DebugCat.DEBUG_CAT_INTERRUPT) 
                    
                    node_idle_time_stop = self.env.now
                    # update node idle time
                    self.track_idle_time += (node_idle_time_stop - node_idle_time_start)
            else:   ## TASK-Q IS EMPTY !!
                try:
                    #print "((1) %d)env=%f" % (self.id, self.env.now)
                    # set node status
                    self.status = NodeStatus.NODE_IDLE                    
                    node_idle_time_start = self.env.now
                    #print(self.label + ' : my task-q is empty! at %d' % self.env.now)
                    Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'run_HEVCFrameTask_ExecutionLoop::, : task queue is empty!', DebugCat.DEBUG_CAT_CPUINFO)
                    #pprint.pprint(self.taskQueue)
                    yield self.env.timeout(self.IDLE_SLEEP_TIME)
                except simpy.Interrupt:
                    self.status = NodeStatus.NODE_JUSTWOKEUP # set node status
                    Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'run_HEVCFrameTask_ExecutionLoop::, : I got interrupted now - was sleeping!', DebugCat.DEBUG_CAT_INTERRUPT)
    
                node_idle_time_stop = self.env.now
                
                #print "((2) %d)env=%f" % (self.id, self.env.now)
                #print "cpu-" + str(self.id) + " - idle_time = " + str(node_idle_time_stop - node_idle_time_start)
                
                # update node idle time
                self.track_idle_time += (node_idle_time_stop - node_idle_time_start)

     
                
    def sendCompletedTaskToOtherNodes(self, task):
       
        Debug.PPrint("%.15f"%self.env.now + "," + self.label + "," +'sendCompletedTaskToOtherNodes_ET::, Enter (taskid=%s)' % (str(task.get_id())), DebugCat.DEBUG_CAT_CPUINFO)        
        print "not implemented yet !! "
        sys.exit()
    
    
    # every time a PU/CTU is completed this is invoked
    # (for now we invoke this when a task is completed)
    def sendCompletedPUToOtherNodes(self, task):
       
        Debug.PPrint("%.15f"%self.env.now + "," + self.label + "," +'sendCompletedPUToOtherNodes::, Enter (taskid=%s)' % (str(task.get_id())), DebugCat.DEBUG_CAT_CPUINFO_VERBOSE)
        
        # need to maintain temp_distribution list so that we don't duplicate any transmissions
        # e.g. P, B mapped to core-B, I mapped to core-A, so A sends task *twice* to core-B - WRONG !!
        temp_distribution_list = []
        
        # which tasks needs this task ?
        dependent_tasks_list = task.get_expected_data_to_children()
        
        #print "dependent_tasks_list :" , dependent_tasks_list, task
        
        ## check if all of the dep tasks have a mapped core, else raise error
        for each_dep_t, each_dep_data_size in dependent_tasks_list.iteritems():
            node_id = self.getTaskMappedNode(each_dep_t)
            if(node_id == None):
                print(self.label + ' sendCompletedTaskToOtherNodes : each_task_id -'+str(each_dep_t) + ' not yet mapped!, curr_task='+str(task.get_id()))
                sys.exit()
            else:
                
                # send to node, but before sending we need to check if
                # we have already sent it before..
                if(self.node_network.get_Nodes()[node_id].dependencyBuff_IsTaskInBuff(task.get_id()) == False):    # for now, this always returns false            
                
                    # check if child is mapped on same node
                    # if true, put to self nodes dep buffer and mark dep check list in RMTM table
                    if(node_id == self.get_id()):
                        task.set_status(TaskStatus.TASK_DATA_TRANSMISSION_COMPLETE)                        
                        result = self.dependencyBuff_put(task, each_dep_t, each_dep_data_size)
                        
                        self.track_FlowsSentToOwnDepBuff(task.get_id(), each_dep_t)
                        
                        if(result == False):
                            print(self.label + ' sendCompletedTaskToOtherNodes_ET : node-'+ str(self.get_id()) + ", --- dep_buff is FULL ! at " +  str(self.env.now))
                            sys.exit()
                        #else:                                                                                    
                        #    self._markDepsCompleted_InRMTMTbl(task.get_id(), each_dep_t)
        
        if(len(dependent_tasks_list.keys()) > 0):
            self.lock_RM_FLWtbl()
            self.lock_RM_TMtbl()                                
            self.resource_manager_instance.Mapper.addTo_RM_FlowTable_HEVC_FrameLevel([task], self.env.now, self.get_id())
            self.release_RM_FLWtbl()
            self.release_RM_TMtbl()           
    
    
    ########################
    # tracking
    ########################
    
    
    def track_CompletedCTUs(self, finished_pu_ref, task):
        task_id = task.get_id()
        ctu_id = finished_pu_ref['ctu_id']
        if task_id not in self.track_completed_ctus:
            self.track_completed_ctus[task_id] = [ctu_id]
        else:
            self.track_completed_ctus[task_id].append(ctu_id)
            






            
    
        