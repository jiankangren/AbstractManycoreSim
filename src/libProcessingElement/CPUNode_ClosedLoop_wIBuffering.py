import pprint
import sys
import copy
import numpy as np
import simpy
import inspect

## local imports
from Node import Node
from SimParams import SimParams
from Node import NodeStatus
from libApplicationModel.Task import TaskModel, TaskStatus
from libMappingAndScheduling.Decentralised.PSAlgorithm import PSAlgorithmProps 
from libMappingAndScheduling.Decentralised.CastilhosClusterProtocol import CastilhosClusterProtocolProps
from libNoCModel.NoCFlowTable import NoCFlowTable
from libNoCModel.NoCFlow import NoCFlow, FlowType
from libMappingAndScheduling.Decentralised.TaskRemapDecentSchemesImpl import TaskRemapDecentSchemesImpl

from libBuffer.Buffer import Buffer, BufferType
from libDebug.Debug import Debug, DebugCat



class CPU_RMStatus:
    RM_SLEEPING       = 1     # i.e sleeping
    RM_BUSYWAITING    = 2     # i.e waiting for someone else/resource
    RM_BUSY           = 3     # i.e busy computing
    RM_ACTIVE         = 4     # i.e. ready and doing work    
    NODE_JUSTWOKEUP   = 5


class CPUNode_ClosedLoop_wIBuffering(Node):
    
    def __init__(self, env, id, tq_size, run_simpy_process = True):
        Node.__init__(self, env, 'CPUNode', id)              
        self.label = self.type + "-" + str(self.id)
        self.taskQueue = []
        self.currentRunningTaskID = None
        
        # semaphore for the taskQ
        self.mutex_tq = simpy.Container(self.env, capacity=1, init=0)
        
        self.taskQueueSize = tq_size
        
        self.memWrite = 0   # how much of data has been written to shared memory by this node ?
        self._memWriteCounter = 0
        self.tasks_that_missed_deadline_by_other_cores = []
        
        self.IDLE_SLEEP_TIME = SimParams.CPU_IDLE_SLEEP_TIME        
        self.scheduler = SimParams.LOCAL_SCHEDULER_TYPE
        
        # the dependency buffer will contain just task_ids of completed tasks, not the actual task itself
        self.dependency_buff = Buffer(env, BufferType.BUFFER_TYPE_INPUT, size=SimParams.CPUNODE_DEPENDANCY_BUFF_SIZE, safe_level=SimParams.CPUNODE_DEPENDANCY_BUFF_SAFE_LEVEL)
        
        # additional properties for the PS algorithm
        self.psalgoprops = PSAlgorithmProps(self.env, self)
        
        # additional properties for the CCP (Castilhos cluster algorithm)
        self.ccpprops = CastilhosClusterProtocolProps(self.env, self)
        
        # decentralised task remapping algorithm (optional)
        self.taskremapping_decent_scheme_instance =  TaskRemapDecentSchemesImpl(self.env, self)
                
        # used for tracking
        self.completedTasks = []        
        self.track_idle_time = 0.0
        self.track_idle_periods = [] # longer idle periods are preferable for dynamic power saving
        self.tasks_that_missed_deadline = []
        self.average_blocking_rate = 0.0
        self.task_execution_timeline = []
        self.track_total_system_slack = {
                                         'mapped_tasks' : [],
                                         'current_cum_slack' : [],
                                         'current_normalised_cum_slack' : []
                                         }     # based on the tasks mapped on to this node, what is the system slack ? 
               
        self.track_imported_tasks = {}
        self.track_completed_ctus = {} # only for hevc
        self.track_flows_sent_to_own_depbuff = []
        
        # Start the run process everytime an instance is created.
        if(run_simpy_process == True):        
            p = env.process(self.getRun(SimParams.TASK_MODEL))
            self.set_processInstance(p)       

       
    def getRun(self, task_model):
        if task_model == TaskModel.TASK_MODEL_MHEG2_FRAME_LEVEL:
            Debug.PPrint("%f"%self.env.now + "," + self.label + "," + "getRun::," + "TaskModel.TASK_MODEL_MHEG2_FRAME_LEVEL", DebugCat.DEBUG_CAT_CPUINFO_VERBOSE)
            return self.run_MPEG2FrameTask_ExecutionLoop()
        
        elif task_model == TaskModel.TASK_MODEL_MHEG2_FRAME_TT_LEVEL:
            Debug.PPrint("%f"%self.env.now + "," + self.label + "," + "getRun::," + "TaskModel.TASK_MODEL_MHEG2_FRAME_TT_LEVEL", DebugCat.DEBUG_CAT_CPUINFO_VERBOSE)
            return self.run_MPEG2FrameTask_TT_ExecutionLoop()
        
        elif task_model == TaskModel.TASK_MODEL_MHEG2_FRAME_ET_LEVEL:
            Debug.PPrint("%f"%self.env.now + "," + self.label + "," + "getRun::," + "TaskModel.TASK_MODEL_MHEG2_FRAME_ET_LEVEL", DebugCat.DEBUG_CAT_CPUINFO_VERBOSE)
            return self.run_MPEG2FrameTask_ET_ExecutionLoop()
        
        elif task_model == TaskModel.TASK_MODEL_MHEG2_GOP_LEVEL:
            Debug.PPrint("%f"%self.env.now + "," + self.label + "," + "getRun::," + "TaskModel.TASK_MODEL_MHEG2_GOP_LEVEL", DebugCat.DEBUG_CAT_CPUINFO_VERBOSE)
            return self.run_MPEG2GOPTask_ExecutionLoop()
        
        else:
            return None
    
    
    
    
    #######################    
    # Buffer management
    #######################
    
    def OutputBuff_put(self, n):
        self.outputBuffInstance.simpy_container_instance.put(n)

    def OutputBuff_areAllTasksInside(self):
#         if SimParams.HEVC_TILELEVEL_SPLITTING_ENABLE == True:
#             if(self.outputBuffInstance.get_level() == self.resource_manager_instance.get_maxTasks()):
#                 return True
#             else:
#                 return False
#         else:
#             return False
        return False
            
    def dependencyBuff_put(self,completed_task):
        if(self.dependency_buff.isFull() == False):
            self.dependency_buff.add_Item(completed_task, completed_task.get_id())
            self.dependency_buff.simpy_container_instance.put(1)
            return True # successfully entered into buff
        else:            
            return False # buffer is full
    
    def dependencyBuff_getLevel(self):
        return len(self.dependency_buff.get_BuffContents())
        
    
    def dependencyBuff_IsTaskInBuff(self,task_id):
        for each_task in self.dependency_buff.get_BuffContents():
            if(each_task.get_id() == task_id):
                return True        
        return False
    
    def dependencyBuff_setTaskStatus(self,task_id, status):
        
        self.dependency_buff.get_BufferItemsList()[task_id].set_status(status)
        
#        for k,each_task in self.dependency_buff.get_BufferItemsList().iteritems():
#            if(each_task.get_id() == task_id):
#                each_task.set_status(status)
        
    
    def dependencyBuff_removeTask(self, task_id):
        self.dependency_buff.remove_Item_byKey(task_id)
        self.dependency_buff.simpy_container_instance.get(1)
    
    
    def dependencyBuff_checkTaskDeps(self, task):
        
        dependencies = task.get_dependencies()
        
        dep_buff_ids = [x.get_id() for x in self.dependency_buff.get_BuffContents()]
                
        for each_dep_id in dependencies:
            if each_dep_id not in dep_buff_ids:
                return False
        
        return True
        
    
        
    # finished task, are there any in the taskQ waiting, that 
    # still needs me ??
    # if true - don't remove, else remove
    def dependencyBuff_cleanUp(self, finished_task):
        
        # combine all buffers
        all_ibuffs = {}
        for d in self.resource_manager_instance.input_buffers: all_ibuffs.update(d.get_BufferItemsList())
        
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
            
            # no one in the taskQ needs it, now check if any of 
            # the deps are needed by tasks in the task_mapping_table (not yet released)
            if(drop == True):                
                if(len(all_ibuffs) >0): # are the ibuffs empty ?
                    for (t_id, val) in self.resource_manager_instance.task_mapping_table.iteritems():
                        for task_in_inputbuff in all_ibuffs.values():
                            if(each_finished_tasks_deps_id in task_in_inputbuff.get_dependencies()): # tasks
                                if(val['node_id'] == self.id) and \
                                (val['status'] != TaskStatus.TASK_COMPLETED):
                                    drop = False
                                    break
                
                    
                
#                for (t_id, val) in self.resource_manager_instance.task_mapping_table.iteritems():   
#                    for each_ibuff_id in xrange(len(self.resource_manager_instance.input_buffers)):    
#                        if(t_id in self.resource_manager_instance.input_buffers[each_ibuff_id].get_BufferItemsList()):              
#                            task_in_inputbuff = self.resource_manager_instance.input_buffers[each_ibuff_id].get_BufferItemsList()[t_id]                    
#                            if(each_finished_tasks_deps_id in task_in_inputbuff.get_dependencies()): # tasks
#                                if(val['node_id'] == self.id) and \
#                                (val['status'] != TaskStatus.TASK_COMPLETED):
#                                    drop = False
#                                    break  
                
                if(drop == True):
                    self.dependencyBuff_removeTask(each_finished_tasks_deps_id)
                else:
                    #print "not dropping!!"
                    i=1
    
    
    #######################    
    # task queue management
    #######################
    def add_Task(self, Task):
        if(len(self.taskQueue) < self.taskQueueSize):
            
            # update actual tasks interference patterns
#            for idx, each_task in enumerate(self.taskQueue):
#                if(each_task.get_priority() <= Task.get_priority()):
#                    Task.addBlockedBy(each_task)                    
#                else:
#                    self.taskQueue[idx].addBlockedBy(each_task)
            
            self.taskQueue.append(Task)            
            return True
        else:
            print("%.11f"%self.env.now + "," + self.label + "," + 'add_Task::, TaskQ FULL!, new_task_id='+str(Task.get_id()))
            pprint.pprint(self.taskQueue)
            return False
               
    def getTaskQ_level(self):
        return len(self.taskQueue)
    
    def getTaskQ_availableCapacity(self):
        if(len(self.taskQueue) < SimParams.CPUNODE_TASKQ_SAFE_LEVEL):
            return (SimParams.CPUNODE_TASKQ_SAFE_LEVEL - len(self.taskQueue)) 
        else:
            return 0    # no more space
        
        
    def get_TaskLateness(self, task):        
        dispatched_time = task.get_dispatchTime()        
        est_lateness = float(float((self.env.now - dispatched_time)) - float(task.get_end_to_end_deadline()))
        
        return est_lateness
        
    def markTaskAsCompleted(self, task):
        # add to completed tasks
        self.completedTasks.append(task)
    
    # mark task as active in RM's Task mapping table
    def setTaskStatus_inRM_TMTbl(self, task_id, task_status):
        # first map child tasks
        self.lock_RM_TMtbl()
        
        if(task_id in self.resource_manager_instance.task_mapping_table):
            self.resource_manager_instance.task_mapping_table[task_id]['status'] = task_status
        
        self.release_RM_TMtbl()
    
    def setTaskStatus(self, tq_ix, task_id, status):
        self.setTaskStatus_inRM_TMTbl(task_id, status)   # set task status
        self.taskQueue[tq_ix].set_status(status)        
        
    # actual task remaining time
    def updateTaskRemainingCompCost(self, tq_ix):
        last_active_time = self.taskQueue[tq_ix].get_lastActiveTime()        
        start_time = self.taskQueue[tq_ix].get_taskStartTime()
        remaining_comp_cost = self.taskQueue[tq_ix].get_remainingComputationCost()        
        
        rt = remaining_comp_cost - (self.env.now - last_active_time)        
        self.taskQueue[tq_ix].set_remainingComputationCost(rt)
    
    # task remaining time based on worst-case estimates
    def updateTaskWorstCaseRemainingCompCost(self, tq_ix):
        last_active_time = self.taskQueue[tq_ix].get_lastActiveTime()        
        start_time = self.taskQueue[tq_ix].get_taskStartTime()
        remaining_wc_comp_cost = self.taskQueue[tq_ix].get_worstCaseRemainingComputationCost()        
        
        rwct = remaining_wc_comp_cost - (self.env.now - last_active_time)        
        self.taskQueue[tq_ix].set_worstCaseRemainingComputationCost(rwct)
    
    # task remaining time based on avg-case estimates
    def updateTaskAvgCaseRemainingCompCost(self, tq_ix):
        last_active_time = self.taskQueue[tq_ix].get_lastActiveTime()        
        start_time = self.taskQueue[tq_ix].get_taskStartTime()
        remaining_avgc_comp_cost = self.taskQueue[tq_ix].get_avgCaseRemainingComputationCost()        
        
        ravgct = remaining_avgc_comp_cost - (self.env.now - last_active_time)        
        self.taskQueue[tq_ix].set_avgCaseRemainingComputationCost(ravgct)
        
    
    def remove_Task(self, ix=0):
        
        temp_finished_task = self.taskQueue[ix]        

        # update the interference to the other tasks        
#        for tq_idx, each_task in enumerate(self.taskQueue):
#            if temp_finished_task in self.taskQueue[tq_idx].get_blockedBy():
#                self.taskQueue[tq_idx].removeBlockedBy(temp_finished_task)
       
        
        #print(self.label + ' : Now removing task - at %f' % (self.env.now))        
        #Debug.PPrint("%f"%self.env.now + "," + self.label + "," + "remove_Task::," + "removing task : "+str(each_task.get_id()), DebugCat.DEBUG_CAT_CPUINFO)
         
        # remove from task Q
        del self.taskQueue[ix]    
        
    def numLateTasksInTQ(self, lateness_ratio = 1.0):
        count = 0
        for tq_idx, each_task in enumerate(self.taskQueue):
            if each_task.isLate(self.env.now, lateness_ratio = lateness_ratio) == True:
                count += 1
        
        return count
    
    def proportionOfLateTasksInTQ(self, lateness_ratio = SimParams.DYNAMIC_TASK_REMAPPING_TASK_LATE_ESTIM_LATENESS_RATIO):
        if(len(self.taskQueue)>0):
            num_late_tasks = self.numLateTasksInTQ(lateness_ratio=lateness_ratio)        
            return float(float(num_late_tasks)/float(len(self.taskQueue)))
        else:
            return 0.0
    
    def proportionOfLateTasksInTQ_KG(self):
        if(len(self.taskQueue)>0):
            num_late_tasks = self.numLateTasksInTQ_KG()        
            return float(float(num_late_tasks)/float(len(self.taskQueue)))
        else:
            return 0.0
    
    
    def numLateTasksInTQ_KG(self, ddtype="EQF"):
        count = 0
        for tq_idx, each_task in enumerate(self.taskQueue):
            if each_task.isLate_KG(self.env.now, ddtype = ddtype) == True:
                count += 1
        
        return count

    
    def numLateTasksInTQ_Div_x(self, ddtype="EQF"):
        count = 0
        for tq_idx, each_task in enumerate(self.taskQueue):
            if each_task.isLate_Div_x(self.env.now) == True:
                count += 1
        
        return count
    
    
    
    def min_max_avg_TaskLatenessinTQ_KG(self, ddtype="EQF"):
        total_task_lateness = 0.0
        task_lateness_list = []
        for tq_idx, each_task in enumerate(self.taskQueue):
            total_task_lateness += each_task.estimatedLateness_KG(self.env.now)
            task_lateness_list.append(each_task.estimatedLateness_KG(self.env.now))
        
        if(len(task_lateness_list) >0):    
            min_lateness = min(task_lateness_list)        
            max_lateness = max(task_lateness_list)  
            avg_lateness = float(total_task_lateness/len(self.taskQueue))
        else:
            min_lateness = None
            max_lateness = None
            avg_lateness = None
            
        result = {
                  'min' : min_lateness,
                  'max' : max_lateness,
                  'avg' : avg_lateness
                  }
        
        return result
            
    
      
    def isTaskQEmpty(self):
        return len(self.taskQueue) == 0
    
    def isTaskQFull(self):
        return len(self.taskQueue) == self.taskQueueSize          
        
    def get_Task(self,ix):
        return self.taskQueue[ix]
    
    def get_TaskQueue(self):
        return self.taskQueue
    
    def get_NumTasksInTQ(self):
        return len(self.taskQueue)
    
    def get_TotalCompletedTasks(self):
        return len(self.completedTasks)
    
    
    def get_TotalTaskExecutionTime(self):
        cc = 0
        for each_task in self.completedTasks:
            cc = cc +  each_task.get_computationCost()            
        return cc
    
    # actual total remaining task exec time
    def get_TotalRemainingTaskExecutionTime(self):
        cc = 0
        for each_task in self.taskQueue:
            cc = cc +  each_task.get_remainingComputationCost()            
        return cc
    
    # worst-case remaining computation cost (costs are calculated based on the WCET)
    def get_WorstCaseTotalRemainingTaskExecutionTime(self):
        wccc = 0
        for each_task in self.taskQueue:
            wccc = wccc +  each_task.get_worstCaseRemainingComputationCost()            
        return wccc
    
    
    # avg-case remaining computation cost (costs are calculated based on the avg.)
    def get_AvgCaseTotalRemainingTaskExecutionTime(self):
        avgccc = 0
        for each_task in self.taskQueue:
            avgccc = avgccc +  each_task.get_avgCaseRemainingComputationCost()            
        return avgccc
    

    def get_TQWorstCaseUtilisation(self):
        wc_util = 0.0
        for each_task in self.taskQueue:
            wc_util += float(each_task.get_worstCaseComputationCost() / each_task.get_period())
        return wc_util

    
    # the total lateness of the tasks in the task queue    
    def get_cumulativeTaskLateness(self):
        cum_lateness = 0.0
        for each_task in self.taskQueue:
            
            # calculate lateness
            current_time = self.env.now
            dispatched_time = each_task.get_dispatchTime()            
            end_to_end_deadline = each_task.get_end_to_end_deadline()
            
            estimated_lateness = float(float((current_time - dispatched_time)) - float(end_to_end_deadline))
            
            if(estimated_lateness > 0.0):
                cum_lateness += estimated_lateness
        
        
        return cum_lateness
    
    # return taskqueue task information    
    def get_TQTaskInfo(self):
        # node tq info:            
        #  - task ugid
        #  - task rem cc (avg, wcc)
        #  - task pri
        #  - task dt, rt
        tq_task_info = []
        for each_task in self.taskQueue:
            tq_task_info.append( 
                [
                 each_task.get_id(),    #0
                 each_task.get_priority(), #1 
                 each_task.get_unique_gop_id(), #2
                 [each_task.get_avgCaseRemainingComputationCost(), each_task.get_worstCaseRemainingComputationCost()], #3
                 [each_task.get_dispatchTime(), each_task.get_releaseTime(), each_task.get_taskStartTime()] #4
                ])
            
        return tq_task_info
            
    
    
    #################################    
    # Local system slack monitoring
    #################################
    
    def calculate_SystemSlack_viaTQ(self):
        cumulative_slack = 0.0
        cumulative_slack_wrt_dispatchtime = 0.0
        
        if(SimParams.CPUNODE_MONITOR_TASKSET_SLACK == True):            
            for each_task in self.taskQueue:
                #task_absolute_deadline = each_task.getEstimatedDeadline_EQF()
                task_absolute_deadline =  each_task.getEstimatedAbsoluteDeadline_ratioBased()   
                task_slack_current = task_absolute_deadline - self.env.now # either positive or negative
                task_slack_wrt_dt = task_absolute_deadline - each_task.get_dispatchTime()
                
#                print "**"
#                print "now=" + str(self.env.now)
#                print task_absolute_deadline
#                print each_task.get_dispatchTime()
#                print "**"
                
                # accumulate
                cumulative_slack += task_slack_current
                cumulative_slack_wrt_dispatchtime += task_slack_wrt_dt
            
            if(cumulative_slack_wrt_dispatchtime>0.0):
                normalised_cum_slack = float(cumulative_slack/cumulative_slack_wrt_dispatchtime)                
            else:
                normalised_cum_slack = 0.0
        
#            print "--"
#            print len(self.taskQueue)
#            print cumulative_slack
#            print cumulative_slack_wrt_dispatchtime
#            print normalised_cum_slack
#            print "--"
        
        # return calculated result            
        self.track_total_system_slack['current_normalised_cum_slack'].append(normalised_cum_slack)
                
        return normalised_cum_slack
                
                
                
    # calculate the system slack
    # - when a set number of tasks of a job is assigned to this core,
    #   based on the task completion time, there will be a system slack.
    # - this can be calculated periodically when a new video stream is admitted
    def calculate_SystemSlack_wrt_est_relD(self, normalised=True, norm_cumslack_tracker_pos=-1, return_all_norm_cumslack_list = False):
        if(SimParams.CPUNODE_MONITOR_TASKSET_SLACK == True):
            cumulative_slack_wrt_est_relD = 0.0
            cumulative_est_relD = 0.0    
             
            for each_task in self.track_total_system_slack['mapped_tasks']:
                
                if(each_task.get_taskCompleteTime() != None) and (each_task.get_taskStartTime() != None):
                    actual_execution_time = each_task.get_taskCompleteTime() - each_task.get_taskStartTime()
                    actual_response_time = each_task.get_taskCompleteTime() - each_task.get_dispatchTime()
                    wcet = each_task.get_worstCaseComputationCost()     
                    
                    # task slack according to estimated relative deadline
                    task_estimated_relative_deadline = each_task.getEstimatedRelativeDeadline_ratioBased()                    
                    #task_estimated_relative_deadline = each_task.getEstimatedRelativeDeadline_Div_x()
                    #task_estimated_absolute_deadline = each_task.getEstimatedDeadline_EQF()
                    
                    task_slack_wrt_est_relD = task_estimated_relative_deadline - actual_response_time
                    cumulative_slack_wrt_est_relD += task_slack_wrt_est_relD
                    cumulative_est_relD += task_estimated_relative_deadline # this is the most slack a task can have                    
                  
            if(cumulative_est_relD > 0.0):
                normalised_cummulative_slack_wrt_est_relD = float(float(cumulative_slack_wrt_est_relD)/float(cumulative_est_relD))
            else:
                normalised_cummulative_slack_wrt_est_relD = 0.0            
            
            self.track_total_system_slack['current_normalised_cum_slack'].append(normalised_cummulative_slack_wrt_est_relD)
            #self.track_total_system_slack['current_cum_slack'].append(cumulative_slack_wrt_est_relD)
            
            # return calculated result
            if(normalised == False):
                #return self.track_total_system_slack['current_cum_slack'][-1]
                return cumulative_slack_wrt_est_relD
            else:
                if(return_all_norm_cumslack_list == False):
                    return self.track_total_system_slack['current_normalised_cum_slack'][norm_cumslack_tracker_pos]
                else:
                    return self.track_total_system_slack['current_normalised_cum_slack']
                           
        else:
            return None        
    
    
    
    # calculate the system slack
    # - when a set number of tasks of a job is assigned to this core,
    #   based on the task completion time, there will be a system slack.
    # - this can be calculated periodically when a new video stream is admitted
    def calculate_SystemSlack(self, normalised=True, norm_cumslack_tracker_pos=-1, return_all_norm_cumslack_list = False):
        if(SimParams.CPUNODE_MONITOR_TASKSET_SLACK == True):
            cumulative_slack = 0.0
            cumulative_wc_total_computation_cost = 0.0           
            debug_track_task_slacks = [] 
            for each_task in self.track_total_system_slack['mapped_tasks']:
                
                if(each_task.get_taskCompleteTime() != None) and (each_task.get_taskStartTime() != None):
                    actual_execution_time = each_task.get_taskCompleteTime() - each_task.get_taskStartTime()
                    wcet = each_task.get_worstCaseComputationCost()     
                    slack = wcet-actual_execution_time 
                    
                    cumulative_wc_total_computation_cost += wcet
                    cumulative_slack += slack
                    
                    debug_track_task_slacks.append((self._get_stream_data_for_task(each_task), each_task.get_taskCompleteTime(), each_task.get_taskStartTime(), 
                                                    actual_execution_time, wcet, slack, cumulative_slack))

            self.track_total_system_slack['current_cum_slack'].append(cumulative_slack)
            
            # we normalise it w.r.t to the total worstcase computation costs
            if(cumulative_wc_total_computation_cost>0):            
                normalised_cumslack = float(self.track_total_system_slack['current_cum_slack'][-1]/cumulative_wc_total_computation_cost)
                self.track_total_system_slack['current_normalised_cum_slack'].append(normalised_cumslack)              
            else:
                self.track_total_system_slack['current_normalised_cum_slack'].append(0.0)
            
            # return calculated result
            if(normalised == False):
                return self.track_total_system_slack['current_cum_slack'][-1]
            else:
                if(return_all_norm_cumslack_list == False):
                    return self.track_total_system_slack['current_normalised_cum_slack'][norm_cumslack_tracker_pos]
                else:
                    return self.track_total_system_slack['current_normalised_cum_slack']
                           
        else:
            return None
        
        
            
    def update_SystemSlack_addTask(self, new_aperiodic_task):
#         print "update_SystemSlack_addTask: enter"
#         print self.get_id()
#         print new_aperiodic_task
        
        ## debug ##
#         if(new_aperiodic_task.get_id() == 1055):
#             print "---"
#             print "update_SystemSlack_addTask :: adding 1055"
#             curframe = inspect.currentframe()
#             calframe = inspect.getouterframes(curframe, 2)
#             print 'caller name:', calframe[1][3]
#             print "CPU-"+str(self.get_id())
#             print "---"
#         #############
                
        if(SimParams.CPUNODE_MONITOR_TASKSET_SLACK == True):
            tix = self._sslocateMappedTask(new_aperiodic_task)            
            obj_copy =  copy.copy(new_aperiodic_task)
                                
            #add task iff task does not already exist
            if(tix == None):
                self.track_total_system_slack['mapped_tasks'].append(obj_copy)
                #pprint.pprint(self.track_total_system_slack['mapped_tasks'])
            else:
                #pprint.pprint(self.track_total_system_slack['mapped_tasks'])
                #sys.exit(self.label + "::update_SystemSlack_addTask: error - task already exists ")
                print self.label+":: Warning::update_SystemSlack_addTask : task already exists !"                
                pprint.pprint(new_aperiodic_task)
        #i=1
    
    def update_SystemSlack_removeTask(self, aperiodic_task):                
        if(SimParams.CPUNODE_MONITOR_TASKSET_SLACK == True):
            tix = self._sslocateMappedTask(aperiodic_task)        
            # add task iff task does not already exist
            if(tix != None):
                del self.track_total_system_slack['mapped_tasks'][tix]
            else:
                #pprint.pprint(self.track_total_system_slack['mapped_tasks'])
                #sys.exit(self.label + "::update_SystemSlack_removeTask: error - task not found ")
                print "Warning::update_SystemSlack_removeTask : task not found!"
                pprint.pprint(aperiodic_task)
       
            
    def update_SystemSlack_setStartTime(self, aperiodic_task, st):        
        if(SimParams.CPUNODE_MONITOR_TASKSET_SLACK == True):
            tix = self._sslocateMappedTask(aperiodic_task)        
            if(tix != None):
                self.track_total_system_slack['mapped_tasks'][tix].set_taskStartTime(st)
            else:
                #sys.exit(self.label + "::update_SystemSlack_setStartTime: error - task not found ")
                # maybe this task was already remapped ?? so ignore
                i=1
                                
            ## debug ##
#             if((aperiodic_task.get_wfid()==5) and
#                (aperiodic_task.get_video_stream_id()==0) and
#                (aperiodic_task.get_frameIXinGOP()==0)):
#                 print "--t_start--"
#                 print self.env.now
#                 print aperiodic_task
#                 print "--t_start--"
            ############
    
        
    def update_SystemSlack_setEndTime(self, finished_task, et):
        if(SimParams.CPUNODE_MONITOR_TASKSET_SLACK == True):
            tix = self._sslocateMappedTask(finished_task)        
            if(tix != None):
                self.track_total_system_slack['mapped_tasks'][tix].set_taskCompleteTime(et)
            else:
                # maybe this task was already remapped ?? so ignore
                i=1
            
#            pprint.pprint(finished_task)
#            pprint.pprint(self.track_total_system_slack['mapped_tasks'])
#            pprint.pprint(self.taskremapping_decent_scheme_instance.track_remaped_numtasks)
#            sys.exit(self.label + "::update_SystemSlack_setEndTime: error - task not found ")

            ## debug ##
#             if((finished_task.get_wfid()==5) and
#                (finished_task.get_video_stream_id()==0) and
#                (finished_task.get_frameIXinGOP()==0)):
#                 print "--t_end--"
#                 print self.env.now
#                 print finished_task
#                 print "--t_end--"                
            ############
    
    # set : start, end, dispatch times, actualcost
    def update_SystemSlack_setTaskStartEnd(self, task, st,et, dt, accc):
        if(SimParams.CPUNODE_MONITOR_TASKSET_SLACK == True):
            tix = self._sslocateMappedTask(task)  
            if(tix != None):
                self.track_total_system_slack['mapped_tasks'][tix].set_taskStartTime(st)
                self.track_total_system_slack['mapped_tasks'][tix].set_taskCompleteTime(et)
                self.track_total_system_slack['mapped_tasks'][tix].set_dispatchTime(dt)
                self.track_total_system_slack['mapped_tasks'][tix].set_computationCost(accc)                                               
            else:
                i=1    
      
    
#     def update_SystemSlack_setActualCompCost(self, task, accc):
#         if(SimParams.CPUNODE_MONITOR_TASKSET_SLACK == True):
#             tix = self._sslocateMappedTask(task)  
#             if(tix != None):                
#                 self.track_total_system_slack['mapped_tasks'][tix].set_dispatchTime(dt)                               
#             else:
#                 i=1    
    
     
    def get_SystemSlack_MappedTasks(self):
        return self.track_total_system_slack['mapped_tasks']
    
    
    def get_SystemSlack_GetLateTasks(self):
        
        late_tasks = []
        for each_task in self.track_total_system_slack['mapped_tasks']:
            if(each_task.get_taskCompleteTime() != None) and (each_task.get_taskStartTime() != None):                    
                actual_response_time = each_task.get_taskCompleteTime() - each_task.get_dispatchTime()
                wcet = each_task.get_worstCaseComputationCost()     
                    
                # task slack according to estimated relative deadline
                task_estimated_relative_deadline = each_task.getEstimatedRelativeDeadline_ratioBased()       
                task_slack_wrt_est_relD = task_estimated_relative_deadline - actual_response_time
                
                if(task_slack_wrt_est_relD<0.0):
                    late_tasks.append(each_task)
        
        return late_tasks
                        
    
        
        
    # helpers    
    def _sslocateMappedTask(self, task):        
        tix = None
        for ix, each_task in enumerate(self.track_total_system_slack['mapped_tasks']):
            if(each_task.get_wfid() == task.get_wfid() and
               each_task.get_video_stream_id() == task.get_video_stream_id() and
               each_task.get_frameIXinGOP() == task.get_frameIXinGOP()):
                tix = ix
                break
        return tix
    
    
    def _get_stream_data_for_task(self, task):        
        result = {
                  'wfid' : task.get_wfid(),
                  'vs_id': task.get_video_stream_id(),
                  'fix': task.get_frameIXinGOP()
                  }
        return result
    
    
    
    ##########################################################################    
    # Imported tasks - upon remapping, the node takes on tasks of other nodes
    ##########################################################################
    def importedTasks_addTask(self, remapping_iter_counter, importer_node_id, imported_task, time):
        entry = {
                 'importer_node_id' :  importer_node_id,
                 'imported_task'    :  [imported_task.get_wfid(), imported_task.get_video_stream_id(), imported_task.get_frameIXinGOP()],
                 'time' : time                     
                 }
        if(remapping_iter_counter not in self.track_imported_tasks):        
            self.track_imported_tasks[remapping_iter_counter] = []
            self.track_imported_tasks[remapping_iter_counter].append(entry)
        else:            
            self.track_imported_tasks[remapping_iter_counter].append(entry)
        
        
    def importedTasks_countTasks(self, remapping_iter_counter):        
        if(remapping_iter_counter in self.track_imported_tasks):
            count = len(self.track_imported_tasks[remapping_iter_counter])
        else:
            count = 0            
        return count
    
    
    def totalImportedTasks(self):
        count = len(self.track_imported_tasks.values())
        return count
    
    
    
    #######################    
    # memory i/o management
    #######################
    
    def get_memWrite(self):
        return self.memWrite
    
    def flushMemoryWriteCounter(self):
        ## every x times he wakes up we flush the memwrite
        if(self._memWriteCounter > SimParams.MEMWRITE_FLUSH_WINDOW):
            self._memWriteCounter = 0
            self.memWrite = 0
        else:
            self._memWriteCounter = self._memWriteCounter + 1
    
    
    
    #######################    
    # tracking    
    #######################
    def track_TaskExecution(self, task, event):
        if(SimParams.TRACK_TASKEXECTIMELINE == True):
            entry = {
                     "t"  : self.env.now, # time
                     "tid": task.get_id(), # task id
                     "ft" : task.get_frameType(), # frame type
                     "wf_strm_ugid" : [task.get_wfid(), task.get_video_stream_id(), task.get_unique_gop_id()],
                     "e"  : event
                     }
            self.task_execution_timeline.append(entry)
    
    
    # these are the flows that are not transmitted, because the
    # child/children are mapped on the same node
    def track_FlowsSentToOwnDepBuff(self, finished_task_id, child_task_id):
        self.track_flows_sent_to_own_depbuff.append(
                                                    [finished_task_id, child_task_id]
                                                    )
    
    
    def track_NodeIdlePeriods(self, idle_period, task_q_empty_status):
        #i = 1 if task_q_empty_status == True else 0
        self.track_idle_periods.append(idle_period)      
#         if len(self.track_idle_periods) == 0:
#             self.track_idle_periods.append([idle_period,task_q_empty_status])
#         else:
#             if (task_q_empty_status == False):
#                 # if the last entry was a taskq empty then append, else add to the last entry idle time
#                 if(self.track_idle_periods[-1][1] == False):
#                     self.track_idle_periods[-1][0] += idle_period
#                 else:
#                     self.track_idle_periods.append([idle_period,task_q_empty_status])
#             else:
#                 self.track_idle_periods.append([idle_period,task_q_empty_status])
    
######################################################
#    TASK EXECUTION LOOPS
#    The Node has a seperate execution loop function
#    for different Task-Types
######################################################

    # non-preemptive - event triggered
    def run_MPEG2FrameTask_ET_ExecutionLoop(self):
        Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'run_MPEG2FrameTask_ET_ExecutionLoop::, : run starting', DebugCat.DEBUG_CAT_CPUINFO)
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
                
                # clean task-Q, w.r.t missed deadlines by other tasks
                #self.check_taskDeadlineMissedbyOtherCores()
                
                # get next task from scheduler
                (task_tq_ix, task) = self.scheduler.nextTask(self.taskQueue, task_tq_ix, self.dependency_buff.get_BuffContents(), self.env.now)
                
                if (task != None):                
                    ## process the next task ##
                    
                    # set task start-time, remaining time
                    if(task.get_taskStartTime() == None):
                        task.set_taskStartTime(self.env.now)
                        self.taskQueue[task_tq_ix].set_taskStartTime(self.env.now)
                        #self.update_SystemSlack_setStartTime(task, self.env.now)
                        
                    Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'run_MPEG2FrameTask_ET_ExecutionLoop::, : Now running Task - %s' % (task._debugShortLabel()), DebugCat.DEBUG_CAT_CPUINFO)
                    
                    # pre=emptive mode, therefore task runs till completion or until interrupted                    
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
                        ## notify RM to populate the 
                        ## mapping and flow tables
                        ##############################
                        
                        # first map child tasks
#                        self.lock_RM_TMtbl()
#                        self.lock_RM_FLWtbl()            
#                        self.resource_manager_instance.Mapper.mapChildTasks(task)   
#                        self.release_RM_TMtbl()
#                        self.release_RM_FLWtbl()       
                        
                        # then try to release them
                        self.lock_RM_TMtbl()
                        self.lock_RM_FLWtbl()                        
                        #new_scheduled_tasks = self.resource_manager_instance.Mapper.releaseChildTasks_v1(task, self.get_id())
                        #new_scheduled_tasks = self.resource_manager_instance.Mapper.releaseChildTasks(task, self.get_id())
                        new_scheduled_tasks = self.resource_manager_instance.Mapper.releaseChildTasks_RWTPr_PriSorted(task, self.get_id())
                        self.release_RM_TMtbl()
                        self.release_RM_FLWtbl()                 
                        
                        if(len(new_scheduled_tasks) > 0):                        
                            Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'run_MPEG2FrameTask_ET_ExecutionLoop:: scheduled new tasks, so going to interrupt RM', DebugCat.DEBUG_CAT_CPUINFO)
                            when_to_interrupt = self.env.now + SimParams.SYNCH_TIME_OFFSET
                            self.env.process(self.interruptRMAfterDelay(when_to_interrupt, task.get_id()))
                            #self.env.process(self.interruptRMImmediately())                            
                    
                        ##############################
                        ## Task is now finished
                        ##############################
                        ## TODO:: (1) send output to other nodes - with induced network delay
                        self.sendCompletedTaskToOtherNodes_ET(task)                    
                        
                        ## (2) send output to output buffer and sleep accordingly
                        # update memory write
                        self.memWrite = self.memWrite + task.get_maxMemConsumption()
                        
                        # go to sleep for the time equal to writing to shared mem                    
                        self.status = NodeStatus.NODE_BUSY_DATAIO    # set node status
                        # remove from taskq
                        
                        #print(self.label + ' : Now removing task (%d)- at %f' % (task.get_id(), self.env.now))
                        self.remove_Task(task_tq_ix)                     
                        
                        # tell RM that task has finished
                        self.resource_manager_instance.UpdateVideoStreamInfo_taskCompleted(task)                    
                        
                        # update slack in slack-reclaim-table
                        if(SimParams.SLACK_FEEDBACK_ENABLED == True):
                            if(self.resource_manager_instance.addToSlackReclaimTable(task.get_id(), self.get_id(), self.env.now) == True):
                                # tell RM to update his task tables, based on reclaimed_slack
                                
                                self.lock_RM_TMtbl()                       
                                (result, interrupt_time) = self.resource_manager_instance.reclaimSlack(task)
                                self.release_RM_TMtbl() 
                                                            
                                if(result == True):
                                    self.env.process(self.interruptRMAfterDelay(interrupt_time, task.get_id()))
                        
                        # signal RM regarding end of stream processing
                        self.notifyRM_endofStream(task)
                        
                        # send the completed task to the output buffer
                        self.env.process(self.sendTaskToOutputBuffAfterDelay(task, task_tq_ix))
                        
                        # remove dependencies                    
                        self.dependencyBuff_cleanUp(task)                        
                        
                                            
                    ## interruption while task is being executed ##
                    except simpy.Interrupt:
                        
                        Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'run_MPEG2FrameTask_ET_ExecutionLoop::, : I got interrupted !! but I was BUSY computing, tid=' + str(task.get_id()) , DebugCat.DEBUG_CAT_LOCALSCHED_PREEMPT)
                        
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
                        print(self.label + ' : None of the tasks in this CPU, has all their deps -  at %f' % self.env.now)
                        pprint.pprint(self.taskQueue)
                        pprint.pprint(self.resource_manager_instance.task_mapping_table)
                        sys.exit()
                        
                        self.status = NodeStatus.NODE_IDLE # set node status                  
                        #print(self.label + ' : my task-q is empty! at %d' % self.env.now)
                        yield self.env.timeout(self.IDLE_SLEEP_TIME)
                    except simpy.Interrupt:
                        self.status = NodeStatus.NODE_JUSTWOKEUP # set node status
                        Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'run_MPEG2FrameTask_ET_ExecutionLoop::, : I got interrupted (again) now!', DebugCat.DEBUG_CAT_INTERRUPT) 
                    
                
            else:   ## TASK-Q IS EMPTY !!
                try:
                    #print "((1) %d)env=%f" % (self.id, self.env.now)
                    # set node status
                    self.status = NodeStatus.NODE_IDLE                    
                    node_idle_time_start = self.env.now
                    #print(self.label + ' : my task-q is empty! at %d' % self.env.now)
                    yield self.env.timeout(self.IDLE_SLEEP_TIME)
                except simpy.Interrupt:
                    self.status = NodeStatus.NODE_JUSTWOKEUP # set node status
                    Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'run_MPEG2FrameTask_ET_ExecutionLoop::, : I got interrupted now - was sleeping!', DebugCat.DEBUG_CAT_INTERRUPT)
    
                node_idle_time_stop = self.env.now
                
                #print "((2) %d)env=%f" % (self.id, self.env.now)
                #print "cpu-" + str(self.id) + " - idle_time = " + str(node_idle_time_stop - node_idle_time_start)
                
                # update node idle time
                self.track_idle_time += (node_idle_time_stop - node_idle_time_start)
                
    
#    # non-preemptive - time triggered
#    def run_MPEG2FrameTask_TT_ExecutionLoop(self):
#        Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'run_MPEG2FrameTask_TT_ExecutionLoop::, : run starting', DebugCat.DEBUG_CAT_CPUINFO)
#        ix = 0
#        while True:
#            # set node status
#            self.status = NodeStatus.NODE_ACTIVE
#            #######################################################
#            ## check taskq, select next task to execute based on
#            ## local scheduling policy
#            #######################################################
#            if(self.isTaskQEmpty() == False):
#                # set node status
#                self.status = NodeStatus.NODE_ACTIVE
#                
#                # clean task-Q, w.r.t missed deadlines by other tasks
#                self.check_taskDeadlineMissedbyOtherCores()
#                
#                # get next task from scheduler
#                (ix, task) = self.scheduler.nextTask(self.taskQueue, ix, self.dependency_buff.get_BuffContents(), self.env.now)
#                
#                if (task != None):                
#                    ## process the next task ##
#                    
#                    # set task start-time
#                    if(task.get_taskStartTime() == None):
#                        task.set_taskStartTime(self.env.now)
#                        
#                    Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'run_MPEG2FrameTask_TT_ExecutionLoop::, : Now running Task - %s' % (task._debugShortLabel()), DebugCat.DEBUG_CAT_CPUINFO)
#                    
#                    # non-preemptive mode, therefore task runs till completion
#                    # going to sleep till the time of computation time
#                    
#                    task.compute(task.get_computationCost())
#                    self.status = NodeStatus.NODE_BUSY    # set node status  
#                    try:              
#                        yield self.env.timeout(task.get_computationCost())
#                    except simpy.Interrupt:
#                        print(self.label + ' : I got interrupted !! but I was BUSY computing ! - status = '+ str(self.status))
#                        sys.exit()
#                                
#                    ##############################
#                    ## Set task specific params 
#                    ##############################                    
#                    # set task complete time
#                    task.set_taskCompleteTime(self.env.now)
#                    
#                    ##############################
#                    ## record task as completed
#                    ############################## 
#                    self.markTaskAsCompleted(task)
#                
#                    ##############################
#                    ## Task is now finished
#                    ##############################
#                    ## TODO:: (1) send output to other nodes - with induced network delay
#                    self.sendCompletedTaskToOtherNodes(task)                    
#                    
#                    ## (2) send output to output buffer and sleep accordingly
#                    # update memory write
#                    self.memWrite = self.memWrite + task.get_maxMemConsumption()
#                    
#                    # go to sleep for the time equal to writing to shared mem                    
#                    self.status = NodeStatus.NODE_BUSY_DATAIO    # set node status
#                    # remove from taskq
#                    
#                    #print(self.label + ' : Now removing task (%d)- at %f' % (task.get_id(), self.env.now))
#                    self.remove_Task(ix) 
#                    
#                    
#                    # tell RM that task has finished
#                    self.resource_manager_instance.UpdateVideoStreamInfo_taskCompleted(task)
#                    
#                    
#                    # update slack in slack-reclaim-table
#                    if(SimParams.SLACK_FEEDBACK_ENABLED == True):
#                        if(self.resource_manager_instance.addToSlackReclaimTable(task.get_id(), self.get_id(), self.env.now) == True):
#                            # tell RM to update his task tables, based on reclaimed_slack
#                            
#                            while(self.resource_manager_instance.mutex_tmtbl.level == 1):
#                                i=1 # busy wait                                
#                            
#                            self.resource_manager_instance.mutex_tmtbl.put(1)                            
#                            (result, interrupt_time) = self.resource_manager_instance.reclaimSlack(task)
#                            self.resource_manager_instance.mutex_tmtbl.get(1)
#                            
#                                                        
#                            if(result == True):
#                                self.env.process(self.interruptRMAfterDelay(interrupt_time, task.get_id()))
#                    
#                    
#                    # removes from the task mapping table
#                    while(self.resource_manager_instance.mutex_tmtbl.level == 1):
#                        i=1 # busy wait   
#                    self.resource_manager_instance.mutex_tmtbl.put(1)                                  
#                    self.resource_manager_instance.removeMapppingTableEntry(task.get_id())    
#                    self.resource_manager_instance.mutex_tmtbl.get(1)               
#                    
#                    # send the completed task to the output buffer
#                    self.env.process(self.sendTaskToOutputBuffAfterDelay(task, ix))                    
#                    
#                    # remove dependencies
#                    # TODO::
#                    self.dependencyBuff_cleanUp(task)                    
#                else:
#                    try:
#                        # taskQ is not empty - but none of the tasks are ready to run (missing deps ??)
#                        # so go to sleep
#                        print(self.label + ' : None of the tasks in this CPU, has all their deps -  at %f' % self.env.now)
#                        pprint.pprint(self.taskQueue)
#                        pprint.pprint(self.resource_manager_instance.task_mapping_table)
#                        sys.exit()
#                        
#                        self.status = NodeStatus.NODE_IDLE # set node status                  
#                        #print(self.label + ' : my task-q is empty! at %d' % self.env.now)
#                        yield self.env.timeout(self.IDLE_SLEEP_TIME)
#                    except simpy.Interrupt:
#                        self.status = NodeStatus.NODE_JUSTWOKEUP # set node status
#                        Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'run_MPEG2FrameTask_TT_ExecutionLoop::, : I got interrupted (again) now!', DebugCat.DEBUG_CAT_INTERRUPT) 
#                    
#                
#            else:   ## TASK-Q IS EMPTY !!
#                try:
#                    # set node status
#                    self.status = NodeStatus.NODE_IDLE                    
#                    #print(self.label + ' : my task-q is empty! at %d' % self.env.now)
#                    yield self.env.timeout(self.IDLE_SLEEP_TIME)
#                except simpy.Interrupt:
#                    self.status = NodeStatus.NODE_JUSTWOKEUP # set node status
#                    Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'run_MPEG2FrameTask_TT_ExecutionLoop::, : I got interrupted now!', DebugCat.DEBUG_CAT_INTERRUPT)
#    
    # non-preemptive
#    def run_MPEG2FrameTask_ExecutionLoop(self):
#        Debug.PPrint(self.label + ' : run starting at %f' % self.env.now, DebugCat.DEBUG_CAT_CPUINFO)
#        ix = 0
#        while True:
#            # set node status
#            self.status = NodeStatus.NODE_ACTIVE
#            #######################################################
#            ## check taskq, select next task to execute based on
#            ## local scheduling policy
#            #######################################################
#            if(self.isTaskQEmpty() == False):
#                # set node status
#                self.status = NodeStatus.NODE_ACTIVE
#                
#                # clean task-Q, w.r.t missed deadlines by other tasks
#                self.check_taskDeadlineMissedbyOtherCores()
#                
#                # get next task from scheduler
#                (ix, task) = self.scheduler.nextTask(self.taskQueue, ix, self.dependency_buff.get_BuffContents(), self.env.now)
#                
#                if (task != None):                
#                    ## process the next task ##
#                    
#                    # set task start-time
#                    if(task.get_taskStartTime() == None):
#                        task.set_taskStartTime(self.env.now)
#                        
#                    Debug.PPrint(self.label + ' : Now running Task - %s at %f' % (task._debugShortLabel() , self.env.now), DebugCat.DEBUG_CAT_CPUINFO)
#                    
#                    # non-preemptive mode, therefore task runs till completion
#                    # going to sleep till the time of computation time
#                    # but first need to check if deadline won't pass after executing
#                    if(task.willTaskMissItsDeadline(self.env.now) == True):              
#                        
#                        Debug.PPrint(self.label + ' : Task '+ str(task.get_id())+' will probably miss its deadline.., abd=' + str(task.get_absDeadline()), DebugCat.DEBUG_CAT_CPUINFO)
#                        task.set_missedDeadlineFlag(True)
#                        # add to drop task list
#                        self.tasks_that_missed_deadline.append(task)
#                        # remove from taskq
#                        self.remove_Task(ix)
#                        # notify other dependent nodes
#                        # TODO::
#                        self.notifyOtherNodes_TaskDeadlineMiss(task)
#                        
#                    else:
#                        task.compute(task.get_computationCost())
#                        self.status = NodeStatus.NODE_BUSY    # set node status  
#                        try:              
#                            yield self.env.timeout(task.get_computationCost())
#                        except simpy.Interrupt:
#                            print(self.label + ' : I got interrupted !! but I was BUSY computing ! - status = '+ str(self.status))
#                            sys.exit()
#                                    
#                        ##############################
#                        ## Set task specific params 
#                        ##############################                    
#                        # set task complete time
#                        task.set_taskCompleteTime(self.env.now)
#                        
#                        ##############################
#                        ## record task as completed
#                        ############################## 
#                        self.markTaskAsCompleted(task)
#                    
#                        ##############################
#                        ## Task is now finished
#                        ##############################
#                        ## TODO:: (1) send output to other nodes - with induced network delay
#                        self.sendCompletedTaskToOtherNodes(task)                    
#                        
#                        ## (2) send output to output buffer and sleep accordingly
#                        # update memory write
#                        self.memWrite = self.memWrite + task.get_maxMemConsumption()
#                        
#                        # go to sleep for the time equal to writing to shared mem                    
#                        self.status = NodeStatus.NODE_BUSY_DATAIO    # set node status
#                        # remove from taskq
#                        self.remove_Task(ix)
#                        # send the completed task to the output buffer
#                        self.env.process(self.sendTaskToOutputBuffAfterDelay(task, ix))               
#                        
#                        # remove dependencies
#                        # TODO::
#                        self.dependencyBuff_cleanUp(task)                    
#                else:
#                    try:
#                        # taskQ is not empty - but none of the tasks are ready to run (missing deps ??)
#                        # so go to sleep
#                        #print(self.label + ' : None of the tasks in this CPU, has all their deps -  at %f' % self.env.now) 
#                        self.status = NodeStatus.NODE_IDLE # set node status                  
#                        #print(self.label + ' : my task-q is empty! at %d' % self.env.now)
#                        yield self.env.timeout(self.IDLE_SLEEP_TIME)
#                    except simpy.Interrupt:
#                        self.status = NodeStatus.NODE_JUSTWOKEUP # set node status
#                        Debug.PPrint(self.label + ' : I got interrupted (again) now! at %f' % self.env.now, DebugCat.DEBUG_CAT_INTERRUPT) 
#                    
#                
#            else:   ## TASK-Q IS EMPTY !!
#                try:
#                    # set node status
#                    self.status = NodeStatus.NODE_IDLE                    
#                    #print(self.label + ' : my task-q is empty! at %d' % self.env.now)
#                    yield self.env.timeout(self.IDLE_SLEEP_TIME)
#                except simpy.Interrupt:
#                    self.status = NodeStatus.NODE_JUSTWOKEUP # set node status
#                    Debug.PPrint(self.label + ' : I got interrupted now! at %f' % self.env.now, DebugCat.DEBUG_CAT_INTERRUPT)                
#                    
    
                
    ######################################################
    # Task dependency management
    # send/receive completed tasks
    ######################################################
    def sendTaskToOutputBuffAfterDelay(self, task, ix):
        
        max_mem_consumption_mb = float(float(task.get_maxMemConsumption())/float((1024.0*1024.0)))
        mem_transfer_delay = SimParams.SHARED_MEM_WRITE_TIME_PER_MB * (max_mem_consumption_mb)                    
        yield self.env.timeout(mem_transfer_delay)       
       
        # add to output buff
        self.outputBuffInstance.add_Item(task, task.get_id())                    
        self.OutputBuff_put(1)   
        
        self.resource_manager_instance.Mapper.taskMappingTable_Remove(task)     
        
        if(self.OutputBuff_areAllTasksInside()):
            print("%f"%self.env.now + "," + self.label + "," +'sendTaskToOutputBuffAfterDelay::, : SIMULATION FINISHED  (max tasks in output buff)!')
            simpy.core._stop_simulate(1)
            #self.env.exit()
            #sys.exit("All tasks simulated")
        else:
            if(self.resource_manager_instance.endSimulation() == True):
                print("%f"%self.env.now + "," + self.label + "," +'sendTaskToOutputBuffAfterDelay::, : SIMULATION FINISHED (RM says end of sim)!')
                simpy.core._stop_simulate(1)
            
    
    def sendTaskToOutputBuffAfterMMCWRFlowCompletion(self, completed_flow):
        #print "sendTaskToOutputBuffAfterMMCWRFlowCompletion:: Enter"
        finished_task = completed_flow.get_payload_metadata()['finished_task']
        node = completed_flow.get_payload_metadata()['src_node']
        
        # timestamp
        finished_task.set_taskMMCWRCompleteTime(self.env.now)
        
        # add to output buff
        self.outputBuffInstance.add_Item(finished_task, finished_task.get_id())                    
        self.OutputBuff_put(1)
        
        # update rm tmtbl
        self.resource_manager_instance.Mapper.taskMappingTable_Remove(finished_task)
        
        if(self.OutputBuff_areAllTasksInside()):
            print("%f"%self.env.now + "," + self.label + "," +
                  'sendTaskToOutputBuffAfterMMCWRFlowCompletion::, : SIMULATION FINISHED  (max tasks in output buff)!')
            #pprint.pprint(self.env._queue)
            #self.resource_manager_instance._report_outstanding_resources()            
            self.resource_manager_instance.mutex_tmtbl.get(1)      # release lock
            self.resource_manager_instance.flow_table.mutex.get(1)
            simpy.core._stop_simulate(1)            
        else:
            if(self.resource_manager_instance.endSimulation() == True):
                print("%f"%self.env.now + "," + self.label + "," +
                      'sendTaskToOutputBuffAfterMMCWRFlowCompletion::, : SIMULATION FINISHED (RM says end of sim)!')
                
                # interrupt nodes to finalise the idle time counters
                self.resource_manager_instance.WakeAllNodes()
                
                # release locks
                self.resource_manager_instance.mutex_tmtbl.get(1) 
                self.resource_manager_instance.flow_table.mutex.get(1)
                
                simpy.core._stop_simulate(1)
            else:
                #self.resource_manager_instance._report_outstanding_resources()
                a=1
        
        return []
           
    
    def sendTaskToNodeAfterDelay(self, task, node, delay, flow_id):            
            
            yield self.env.timeout(delay)   # delay            
            # put to dest node's  dep-buff
            result = node.dependencyBuff_put(task)
            if(result == True):
                Debug.PPrint("%f"%self.env.now + "," + self.label + "," +
                             'sendTaskToNodeAfterDelay::, : task-'+ str(task.get_id()) + 
                             ' successfully transmitted to Node-'+str(node.get_id()) + 
                             ', with TxDelay='+str(delay), DebugCat.DEBUG_CAT_TRANSMIT)
                
                # notify RM that the flow has completed
                self.lock_RM_FLWtbl()
                self.lock_RM_TMtbl() 
                new_released_tasks = self.resource_manager_instance.Mapper.DataFlowComplete(flow_id)
                self.release_RM_FLWtbl()
                self.release_RM_TMtbl() 
                
                if(len(new_released_tasks) > 0):                    
                    when_to_interrupt = self.env.now + SimParams.SYNCH_TIME_OFFSET
                    self.env.process(self.interruptRMAfterDelay(when_to_interrupt, -1))
                
            else:
                print("%f"%self.env.now + "," + self.label + "," +
                      'sendTaskToNodeAfterDelay::, : node-'+ str(node.get_id()) + ", --- dep_buff is FULL ! ")
                pprint.pprint(node.dependency_buff.get_BuffContents())
                pprint.pprint(self.resource_manager_instance.task_mapping_table)
                sys.exit()
                
            
            # if node is asleep wake him up !!
            #if(node.get_status() == NodeStatus.NODE_IDLE):                  
            #    node.processInstance.interrupt()
    
#    def sendCompletedTaskToOtherNodes(self, task):
#        
#        print self.label + ": sendCompletedTaskToOtherNodes:: Enter : taskid =" + str(task.get_id()) 
#        
#        # need to maintain temp_distribution list so that we don't duplicate any transmissions
#        # e.g. P, B mapped to core-B, I mapped to core-A, so A sends task *twice* to core-B - WRONG !!
#        temp_distribution_list = []
#        
#        # which tasks needs this task ?
#        dependent_tasks_list = task.get_which_tasks_needs_me()
#        
#        # which nodes should this task be sent to ?
#        for each_task_id in dependent_tasks_list:
#            
#            node_id = self.getTaskMappedNode(each_task_id)
#            #print  "node_id : " + str(node_id)          
#            if(node_id != None):
#                if((node_id in temp_distribution_list) == False):
#                    temp_distribution_list.append(node_id)
#                    
#                    # send to node, but before sending we need to check if
#                    # we have already sent it before..
#                    if(self.node_network.get_Nodes()[node_id].dependencyBuff_IsTaskInBuff(task.get_id()) == False):
#                        
#                        # check if source == dest (no transmission needed!)
#                        if(self.get_id() == node_id):
#                            result = self.dependencyBuff_put(task)
#                            
#                            self._markDepsCompleted_InRMTMTbl(task.get_id(), each_task_id)
#                            
#                            if(result == False):
#                                print(self.label + ' sendCompletedTaskToOtherNodes : node-'+ str(self.get_id()) + ", --- dep_buff is FULL ! at " +  str(self.env.now))
#                                sys.exit()
#                            #else:
#                            #    # mark dependancies completed
#                            #    if(task.get_id() not in self.resource_manager_instance.task_mapping_table[each_child_task_id]['deps_completed']):
#                                
#                        else:                        
#                            
#                            
#                            #### (3) add a flow table entry
#                            # finished task to all it's children tasks - previous step
#                            # should have mapped all children tasks
#                            
#                            while(self.resource_manager_instance.flow_table.mutex.level == 1):
#                                i=1 # busy wait                                       
#                            self.resource_manager_instance.flow_table.mutex.put(1)   # obtain lock    
#                            while(self.resource_manager_instance.mutex_tmtbl.level == 1):
#                                i=1 # busy wait                                                            
#                            self.resource_manager_instance.mutex_tmtbl.put(1)      # obtain lock                           
#                                                                                
#                            self.resource_manager_instance.Mapper.addTo_RM_FlowTable([task], self.env.now, self.get_id())
#                            
#                            self.resource_manager_instance.mutex_tmtbl.get(1)      # obtain lock      
#                            self.resource_manager_instance.flow_table.mutex.get(1)   # obtain lock                            
#                            
#                            #delay = self.onchip_network.getRouteCost(self.get_id(), node_id, task.get_completedTaskSize())
#                            
#                            # update RM flow table                            
##                            (flow_id, flow) = self.resource_manager_instance.flow_table.get_flow(src_task_id=task.get_id(), 
##                                                                                                 dst_task_id=each_task_id,
##                                                                               src_node_id=self.get_id(), 
##                                                                               dst_node_id=node_id)
##                            self.resource_manager_instance.flow_table.set_releaseTime(self.env.now, flow_id=flow_id)
##                            self.resource_manager_instance.flow_table.set_active(True, flow_id=flow_id)                                             
##                            self.env.process(self.sendTaskToNodeAfterDelay(task, self.node_network.get_Nodes()[node_id], delay, flow_id))
#            
#            else:
#                print(self.label + ' sendCompletedTaskToOtherNodes : each_task_id -'+str(each_task_id) + ' not yet mapped!, curr_task='+str(task.get_id()))
#                sys.exit()
    
    
    def sendCompletedTaskToOtherNodes_ET(self, task):
       
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
                print(self.label + ' sendCompletedTaskToOtherNodes_ET : each_task_id -'+str(each_dep_t) + ' not yet mapped!, curr_task='+str(task.get_id()))
                sys.exit()
            else:
                
                # send to node, but before sending we need to check if
                # we have already sent it before..
                if(self.node_network.get_Nodes()[node_id].dependencyBuff_IsTaskInBuff(task.get_id()) == False):                
                
                    # check if child is mapped on same node
                    # if true, put to self nodes dep buffer and mark dep check list in RMTM table
                    if(node_id == self.get_id()):
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
                            
    
    
    
    # all cores maintain a list, which tracks task-deadlines missed by other cores
    # if a task deadline is missed by the current core, then this function is called
    # this function then adds the missed-task into the relevent other cores' task-missed list
    def notifyOtherNodes_TaskDeadlineMiss(self, task):
         
        # which tasks needs this task ?
        dependent_tasks_list = task.get_which_tasks_needs_me()
        
        # which nodes should be notified ?
        for each_task_id in dependent_tasks_list:            
            node_id = self.getTaskMappedNode(each_task_id)
            if node_id != None:
                nn = self.node_network.get_Nodes()      
                nn[node_id].tasks_that_missed_deadline_by_other_cores.append(task.get_id())
                
    # all cores maintain a list, which tracks task-deadlines missed by other cores
    # this list needs to be checked, to see if before processing the next task if a dependent
    # task is missed ? 
    def check_taskDeadlineMissedbyOtherCores(self):
        needed_dep_tasks = []
        
        tasks_in_q = self.taskQueue
        
        # get all dependent tasks required
        for ix, each_task in enumerate(tasks_in_q):
            
            dep_tasks = each_task.get_dependencies()
            
            # get common elements in two lists
            if((dep_tasks != None) and (self.tasks_that_missed_deadline_by_other_cores != None)):
            
                common = list(set(dep_tasks).intersection(self.tasks_that_missed_deadline_by_other_cores))
                
                if( len(common) > 0): # if there are common, then drop task from taskQ
                    each_task.set_missedDeadlineFlag(True)
                    # add to drop task list
                    self.tasks_that_missed_deadline.append(each_task)
                    # remove from taskq
                    self.remove_Task(ix)
    
        
    def interruptRMAfterDelay(self, when_to_interrupt, finished_task_id):
        
        delay = when_to_interrupt - self.env.now
        
        if(delay > 0):
            yield self.env.timeout(delay)   # delay   
        
            if(self.resource_manager_instance.status == CPU_RMStatus.RM_SLEEPING):
                Debug.PPrint("%.15f"%self.env.now + "," + self.label + "," +'interruptRMAfterDelay::, interrupting RM (finished_task_id=%d)' % (finished_task_id), DebugCat.DEBUG_CAT_INTERRUPT)
                self.resource_manager_instance.processInstance.interrupt("CPU-"+str(self.get_id()))
        
    
    def interruptRMImmediately(self):
        if(self.resource_manager_instance.status == CPU_RMStatus.RM_SLEEPING):
            Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'interruptRMImmediately::, interrupting RM ', DebugCat.DEBUG_CAT_INTERRUPT)
            self.resource_manager_instance.processInstance.interrupt("CPU-"+str(self.get_id()))
    
    
    def _markDepsCompleted_InRMTMTbl(self, fin_task_id, child_task_id):
        self.lock_RM_TMtbl()  
                     
        if(fin_task_id not in self.resource_manager_instance.task_mapping_table[child_task_id]['deps_completed']):
            self.resource_manager_instance.task_mapping_table[child_task_id]['deps_completed'].append(fin_task_id)
        
        self.release_RM_TMtbl()
        
        
        
    ######################################################
    # Shared resources locking mechanisms
    #  - RM task mapping table
    #  - RM flow table
    ######################################################
    
    def lock_RM_TMtbl(self):
        while(self.resource_manager_instance.mutex_tmtbl.level == 1):
            i=1 # busy wait                                                            
        self.resource_manager_instance.mutex_tmtbl.put(1) # obtain lock
        
    def release_RM_TMtbl(self):
        self.resource_manager_instance.mutex_tmtbl.get(1) # release lock
        
    def lock_RM_FLWtbl(self):
#         curframe = inspect.currentframe()
#         calframe = inspect.getouterframes(curframe, 2)
#         print 'lock_RM_FLWtbl:: caller name:', calframe[1][3]
        while(self.resource_manager_instance.flow_table.mutex.level == 1):
            i=1 # busy wait                                       
        self.resource_manager_instance.flow_table.mutex.put(1)   # obtain lock   
    
    def release_RM_FLWtbl(self):
#         curframe = inspect.currentframe()
#         calframe = inspect.getouterframes(curframe, 2)
#         print 'release_RM_FLWtbl:: caller name:', calframe[1][3]
        self.resource_manager_instance.flow_table.mutex.get(1) # release lock
    
    ######################################################
    # Related to runtime application management
    ######################################################
    
    def notifyRM_endofStream(self, task):
        
        if(task.get_isTailVideoGop() == True):
            if(task.get_frameIXinGOP() == (len(task.get_gopstructure())-1)):
                
                #sys.exit("here")                
        
                wf_id = task.get_wfid()
                strm_id = task.get_video_stream_id()
                
                self.resource_manager_instance.RuntimeApp_removeStream(wf_id, strm_id)
                
    # just a notification, to update the RM's global view
    def notifyRMTaskCompletion(self, finished_task):
        
        if(SimParams.MS_SIGNALLING_NOTIFY_TASK_COMPLETE_ENABLE == True):
        
            Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'notifyRMTaskCompletion::, : finished_task='+str(finished_task.get_id()), DebugCat.DEBUG_CAT_MSSIGNALLING)
            
            src_node_id = self.get_id()
            dst_node_id = SimParams.RESOURCEMANAGER_NODEID
            release_time = self.env.now
            nextid = self.resource_manager_instance.flow_table.nextid                    
            route = self.resource_manager_instance.interconnect.getRouteXY(dst_node_id, src_node_id)
            priority = SimParams.NOC_FLOW_MS_SIGNALLING_MAXPRIORITY + nextid        
            basic_latency = self.resource_manager_instance.interconnect.getRouteCostXY(dst_node_id, 
                                                                        src_node_id,
                                                                        SimParams.NOC_PAYLOAD_32BYTES)
            payload = SimParams.NOC_PAYLOAD_32BYTES
            endTime_wrt_BL = release_time + basic_latency
            payload_metadata = {
                                'finished_task_id' : finished_task.get_id(),
                                'node_id' : self.get_id(),                                
                                #'finished_task_starttime' : finished_task.get_taskStartTime(),
                                #'finished_task_endtime' : finished_task.get_taskCompleteTime(),
                                
                                # info : cc, ftype, pri
                                'finished_task_info' : [finished_task.get_computationCost(),
                                                        finished_task.get_frameType(),
                                                        finished_task.get_priority()
                                                        ],
                                                        
                                'finished_task_strm_info' : [finished_task.get_wfid(), finished_task.get_video_stream_id()]
                                }
                        
            newflow = NoCFlow(nextid,
                           finished_task,
                           finished_task.get_id(),
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
                           type=FlowType.FLOWTYPE_MASTERSLAVESIGNALLING_TASKCOMPLETE,                           
                           payload_metadata=payload_metadata)
            
            self.lock_RM_FLWtbl()
            # add to the flow table
            self.resource_manager_instance.flow_table.addFlow(newflow, release_time, basic_latency)                        
            self.release_RM_FLWtbl()
            
            # update the table        
            self.resource_manager_instance.flow_table.updateTable(fire=True)   
                
                
    ######################################################
    # Misc help
    ######################################################
    def _trunc(self, f, n):        
        if n > 15:
            sys.exit("_trunc: error")        
        s = "%.15f" % f
        ss = s[:-(15-n)]        
        return float(ss)