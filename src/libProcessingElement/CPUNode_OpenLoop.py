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


class CPUNode_OpenLoop(CPUNode_ClosedLoop_wIBuffering):
    
    def __init__(self, env, id, tq_size, run_simpy_process = True):
        CPUNode_ClosedLoop_wIBuffering.__init__(self, env, id, tq_size, run_simpy_process=False)
        
        self.label = "CPUNode_OpenLoop" + "-" + str(self.id)
        
        # Start the run process everytime an instance is created.
        if(run_simpy_process == True):        
            p = env.process(self.run_MPEG2FrameTask_ExecutionLoop())
            self.set_processInstance(p)        

    #######################    
    # Buffer management
    #######################
    
    # finished task, are there any in the taskQ waiting, that 
    # still needs me ??
    # if true - don't remove, else remove
    def dependencyBuff_cleanUp(self, finished_task):
       
        # get finished tasks, dependencies
        finished_tasks_deps = finished_task.get_dependencies()
        
        # check if any of the deps are needed by tasks in the:
        # - taskQ buffer
        # - task_mapping table
        for each_finished_tasks_deps_id in finished_tasks_deps:
            drop = True
            for each_task_in_taskq in self.taskQueue:
                if(each_finished_tasks_deps_id in each_task_in_taskq.get_dependencies()):
                    drop = False
                    break
                
            if(drop == True):
                self.dependencyBuff_removeTask(each_finished_tasks_deps_id)
            else:
                #print "not dropping!!"
                i=1
    
    
######################################################
#    TASK EXECUTION LOOPS
######################################################

    # non-preemptive - event triggered
    def run_MPEG2FrameTask_ExecutionLoop(self):
        Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'run_MPEG2FrameTask_ExecutionLoop::, : run starting', DebugCat.DEBUG_CAT_CPUINFO)
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
                (task_tq_ix, task) = self.scheduler.nextTask(self.taskQueue, task_tq_ix, self.dependency_buff.get_BuffContents(), self.env.now)
                
                if (task != None):                
                    ## process the next task ##
                    
                    # set task start-time, remaining time
                    if(task.get_taskStartTime() == None):
                        task.set_taskStartTime(self.env.now)
                        self.taskQueue[task_tq_ix].set_taskStartTime(self.env.now)
                        
                    Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'run_MPEG2FrameTask_ExecutionLoop::, : Now running Task - %s' % (task._debugShortLabel()), DebugCat.DEBUG_CAT_CPUINFO)
                    
                    # pre-emptive mode, therefore task runs till completion or until interrupted                    
                    try:                                    
                        ##############################
                        ## Start computation
                        ##############################
                        self.track_TaskExecution(task, "run")
                        # set task status
                        self.status = NodeStatus.NODE_BUSY    # set node status
                        self.setTaskStatus(task_tq_ix, task.get_id(), TaskStatus.TASK_RUNNING)                                                               
                        
                        # set last activation time
                        self.taskQueue[task_tq_ix].set_lastActiveTime(self.env.now)                                                
                        
                        self.currentRunningTaskID = task   # set current running task
                        runtime = self.taskQueue[task_tq_ix].get_remainingComputationCost()                   
                        yield self.env.timeout(runtime)                        
                        
                        Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'run_MPEG2FrameTask_ExecutionLoop::, : Finished task - %s' % (task._debugShortLabel()), DebugCat.DEBUG_CAT_CPUINFO)
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
                        self.sendCompletedTaskToOtherNodes(task)                    
                        
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
                                            
                    ## interruption while task is being executed ##
                    except simpy.Interrupt:
                        
                        Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'run_MPEG2FrameTask_ExecutionLoop::, : I got interrupted !! but I was BUSY computing, tid=' + str(task.get_id()) , DebugCat.DEBUG_CAT_LOCALSCHED_PREEMPT)
                        
                        #### task computation gets pre-empted by another higher priority task ####
                        # set the currently running task to null
                        self.currentRunningTaskID = None
                        
                        # suspend the task
                        self.setTaskStatus(task_tq_ix, task.get_id(), TaskStatus.TASK_SUSPENDED)
                        
                        # update the remaining computation cost
                        self.updateTaskRemainingCompCost(task_tq_ix)
                        self.updateTaskWorstCaseRemainingCompCost(task_tq_ix)
                        self.updateTaskAvgCaseRemainingCompCost(task_tq_ix)
                                       
                else:
                    try:
                        # taskQ is not empty - but none of the tasks are ready to run (missing deps ??)
                        # so go to sleep
                        Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'run_MPEG2FrameTask_ExecutionLoop::, : : None of the tasks in this CPU, has all their deps, going to sleep', DebugCat.DEBUG_CAT_INTERRUPT)
#                        print(self.label + ' : None of the tasks in this CPU, has all their deps -  at %f' % self.env.now)
#                        pprint.pprint(self.taskQueue)
#                        pprint.pprint(self.resource_manager_instance.task_mapping_table)
#                        sys.exit()

                        self.status = NodeStatus.NODE_IDLE # set node status       
                        node_idle_time_start = self.env.now           
                        #print(self.label + ' : my task-q is empty! at %d' % self.env.now)
                        yield self.env.timeout(self.IDLE_SLEEP_TIME)
                    except simpy.Interrupt:
                        self.status = NodeStatus.NODE_JUSTWOKEUP # set node status
                        Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'run_MPEG2FrameTask_ExecutionLoop::, : I got interrupted, I was sleeping!', DebugCat.DEBUG_CAT_INTERRUPT) 
                    
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
                    Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'run_MPEG2FrameTask_ExecutionLoop::, : task queue is empty!', DebugCat.DEBUG_CAT_CPUINFO)
                    #pprint.pprint(self.taskQueue)
                    yield self.env.timeout(self.IDLE_SLEEP_TIME)
                except simpy.Interrupt:
                    self.status = NodeStatus.NODE_JUSTWOKEUP # set node status
                    Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'run_MPEG2FrameTask_ExecutionLoop::, : I got interrupted now - was sleeping!', DebugCat.DEBUG_CAT_INTERRUPT)
    
                node_idle_time_stop = self.env.now
                
                #print "((2) %d)env=%f" % (self.id, self.env.now)
                #print "cpu-" + str(self.id) + " - idle_time = " + str(node_idle_time_stop - node_idle_time_start)
                
                # update node idle time
                self.track_idle_time += (node_idle_time_stop - node_idle_time_start)

     
                
    def sendCompletedTaskToOtherNodes(self, task):
       
        Debug.PPrint("%.15f"%self.env.now + "," + self.label + "," +'sendCompletedTaskToOtherNodes_ET::, Enter (taskid=%d)' % (task.get_id()), DebugCat.DEBUG_CAT_CPUINFO)
        
        # need to maintain temp_distribution list so that we don't duplicate any transmissions
        # e.g. P, B mapped to core-B, I mapped to core-A, so A sends task *twice* to core-B - WRONG !!
        temp_distribution_list = []
        
        # which tasks needs this task ?
        dependent_tasks_list = task.get_which_tasks_needs_me()    
        
        ## check if all of the dep tasks have a mapped core, else raise error
        for each_dep_t in dependent_tasks_list:
            node_id = self.getTaskMappedNode(each_dep_t)
            if(node_id == None):
                print(self.label + ' sendCompletedTaskToOtherNodes : each_task_id -'+str(each_dep_t) + ' not yet mapped!, curr_task='+str(task.get_id()))
                sys.exit()
            else:
                
                # send to node, but before sending we need to check if
                # we have already sent it before..
                if(self.node_network.get_Nodes()[node_id].dependencyBuff_IsTaskInBuff(task.get_id()) == False):                
                
                    # check if child is mapped on same node
                    # if true, put to self nodes dep buffer and mark dep check list in RMTM table
                    if(node_id == self.get_id()):
                        task.set_status(TaskStatus.TASK_DATA_TRANSMISSION_COMPLETE)
                        result = self.dependencyBuff_put(task)
                        if(result == False):
                            print(self.label + ' sendCompletedTaskToOtherNodes_ET : node-'+ str(self.get_id()) + ", --- dep_buff is FULL ! at " +  str(self.env.now))
                            sys.exit()                            
                        self._markDepsCompleted_InRMTMTbl(task.get_id(), each_dep_t)
        
        self.lock_RM_FLWtbl()
        self.lock_RM_TMtbl()                           
                                                            
        self.resource_manager_instance.Mapper.addTo_RM_FlowTable([task], self.env.now, self.get_id())
        
        #self.resource_manager_instance.mutex_tmtbl.get(1)      # release lock      
        #self.resource_manager_instance.flow_table.mutex.get(1)   # release lock   
        
        self.release_RM_FLWtbl()
        self.release_RM_TMtbl()           
        