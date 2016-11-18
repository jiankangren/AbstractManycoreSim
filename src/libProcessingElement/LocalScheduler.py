import pprint
import sys
import json
from libApplicationModel.Task import TaskStatus

## local imports


class LocalRRScheduler(object):
    
    LABEL = "LocalRRScheduler"
    def nextTask(self, task_q, ix_orig):
        
        ix = ix_orig
        # reset pointer
        ix = ix + 1
        if(ix >= len(task_q)):   # if reached end, then wrap around
            ix=0
            
        return (ix, task_q[ix])
    
    
class LocalEDFScheduler(object):
    
    LABEL = "LocalEDFScheduler"
    def nextTask(self, task_q, ix_orig):        
        # reset pointers
        ix = 0
        sel_ix = 0
        selected_task = task_q[0]   # default start point to compare        
        
        if(len(task_q) == 0):
            return (sel_ix, selected_task) 
        else:
            # go through all the tasks in the list and determine the closest deadline
            # get a list with timelefttilldeadline ascending order      
            for each_task in task_q:
                if(each_task.get_timeLeftTillDeadline() < selected_task.get_timeLeftTillDeadline()):
                    selected_task = each_task
                    sel_ix = ix                
                ix = ix+1
                
            return (sel_ix, selected_task)


## special local scheduler for MPEG-frame task model - takes form of : Non-preemptive EDF
# (1) sort local task q in EDF-order
# (2) check if top-task has all needed dependencies
# (3) if YES, then return, if NO, check next task         
class LocalMPEG2FrameEDFScheduler(object):
    
    LABEL = "LocalMPEG2FrameEDFScheduler"
    def nextTask(self, task_q, ix_orig, dep_storage_buff, time_now):        
        
        # create temporary list of dicts        
        new_task_q = []
        for idx, each_task in enumerate(task_q):
            temp = {
                    'ix'    : idx,
                    'task'  : each_task
                    }
            new_task_q.append(temp)
        
        # sort list in EDF order - according to absolute deadline
        edf_sorted_task_q = sorted(new_task_q, key=lambda x: x['task'].get_absDeadline(), reverse=False)        
        
        # go through each task and see if all dependencies are present to start execution
        for each_task in edf_sorted_task_q:
            if(self._hasAllDeps(dep_storage_buff, each_task['task']) == True):
                return (each_task['ix'], each_task['task'])
        
        return (None, None)
            
            
    def _hasAllDeps(self,dep_storage_buff, task):
        
        task_ids_in_dep_storage_buff = []
        task_dep_taskids = task.get_dependencies()
        
        if(len(task_dep_taskids) > 0):
        
            for each_task in dep_storage_buff:
                task_ids_in_dep_storage_buff.append(each_task.get_id())
            
            if(len(task_ids_in_dep_storage_buff) >0 and len(task_dep_taskids) >0):
                
                set_common = list(set(task_ids_in_dep_storage_buff) & set(task_dep_taskids))
                
                # if all the dependencies we need are here return true, else false
                if(len(set_common) == len(task_dep_taskids)):
                    return True
                else:
                    return False
            else:
                return False
        
        
        else:   # task doesn't have any dependencies (e.g. Iframe) :)
            return True
        
        
## special local scheduler for MPEG-frame task model - basic List scheduler
# (1) returns whatever is in the list next
# (2) check if top-task has all needed dependencies
# (3) if YES, then return, if NO, check next task         
class LocalMPEG2FrameListScheduler(object):
    
    LABEL = "LocalMPEG2FrameListScheduler"
    def nextTask(self, task_q, ix_orig, dep_storage_buff, time_now):        
        
        # create temporary list of dicts        
        new_task_q = []
        for idx, each_task in enumerate(task_q):
            temp = {
                    'ix'    : idx,
                    'task'  : each_task
                    }
            new_task_q.append(temp)
        
        # no sorting !
        task_q_list = new_task_q  
        
        # go through each task and see if all dependencies are present to start execution
        for each_task in task_q_list:
            if(self._hasAllDeps(dep_storage_buff, each_task['task']) == True):
                return (each_task['ix'], each_task['task'])
        
        return (None, None)
            
            
    def _hasAllDeps(self,dep_storage_buff, task):
        
        task_ids_in_dep_storage_buff = []
        task_dep_taskids = task.get_dependencies()
        
        if(len(task_dep_taskids) > 0):        
            for each_task in dep_storage_buff:
                task_ids_in_dep_storage_buff.append(each_task.get_id())
            
            if(len(task_ids_in_dep_storage_buff) >0 and len(task_dep_taskids) >0):                
                set_common = list(set(task_ids_in_dep_storage_buff) & set(task_dep_taskids))
                
                # if all the dependencies we need are here return true, else false
                if(len(set_common) == len(task_dep_taskids)):
                    return True
                else:
                    return False
            else:
                return False
        else:   # task doesn't have any dependencies (e.g. Iframe) :)
            return True
        
## special local scheduler for MPEG-frame task model - basic List scheduler
# (1) returns whatever is in the list next
# (2) check if highest priority task has all needed dependencies
# (3) if YES, then return, if NO, return None        
class LocalMPEG2FramePriorityScheduler(object):
    
    LABEL = "LocalMPEG2FramePriorityScheduler"
    
    def nextTask(self, task_q, ix_orig, dep_storage_buff, time_now):
        
        ## create temporary list of dicts        
        new_task_q = []
        for idx, each_task in enumerate(task_q):
            temp = {
                    'ix'    : idx,
                    'task'  : each_task
                    }
            new_task_q.append(temp)
        
        # no sorting !
        task_q_list = new_task_q
        
        #pprint.pprint([x['task'].get_priority() for x in task_q_list])
        
        ## find highest priority task in taskQ
        pri_sorted_task_q = sorted(task_q_list, key=lambda x: x['task'].get_priority(), reverse=True) # desc order
        
        #pprint.pprint([x['task'].get_priority() for x in pri_sorted_task_q])
        
        high_pri_task = pri_sorted_task_q[0]['task']
        high_pri_task_ix = pri_sorted_task_q[0]['ix']
        
        ## check if have all deps ?
        if(self._hasAllDeps(dep_storage_buff, high_pri_task) == True):
            return (high_pri_task_ix, high_pri_task)
        else:
            return (None, None)
        
    
            
    def _hasAllDeps(self,dep_storage_buff, task):
        
        task_ids_in_dep_storage_buff = []
        task_dep_taskids = task.get_dependencies()
        
        if(len(task_dep_taskids) > 0):        
            for each_task in dep_storage_buff:
                task_ids_in_dep_storage_buff.append(each_task.get_id())
            
            if(len(task_ids_in_dep_storage_buff) >0 and len(task_dep_taskids) >0):                
                set_common = list(set(task_ids_in_dep_storage_buff) & set(task_dep_taskids))
                
                # if all the dependencies we need are here return true, else false
                if(len(set_common) == len(task_dep_taskids)):
                    return True
                else:
                    return False
            else:
                return False
        else:   # task doesn't have any dependencies (e.g. Iframe) :)
            return True
        


class LocalMPEG2FramePriorityScheduler_WithDepCheck(object):
    
    LABEL = "LocalMPEG2FramePriorityScheduler_WithDepCheck"
    
    def nextTask(self, task_q, ix_orig, dep_storage_buff, time_now):
        #print "LocalMPEG2FramePriorityScheduler_WithDepCheck::nextTask : enter"
        
        ## create temporary list of dicts        
        new_task_q = []
        for idx, each_task in enumerate(task_q):
            temp = {
                    'ix'    : idx,
                    'task'  : each_task,
                    }
            
            if(each_task.get_frameType() in ["P", "B"]): # only P/B frames have deps
                if(each_task.get_taskStartTime() == None): # we don't need to check for deps if we have already started this task
                    if(self._hasAllDeps(dep_storage_buff, each_task) == True):
                        new_task_q.append(temp)
                else:
                    new_task_q.append(temp)
            else:                
                new_task_q.append(temp)                
                
        
        if(len(new_task_q)>0):            
            # no sorting !
            task_q_list = new_task_q
            
            ## find highest priority task in taskQ
            ## larger values ===> higher priority
            pri_sorted_task_q = sorted(task_q_list, key=lambda x: x['task'].get_priority(), reverse=True) # desc order
            
            high_pri_task = pri_sorted_task_q[0]['task']
            high_pri_task_ix = pri_sorted_task_q[0]['ix']
            
            return (high_pri_task_ix, high_pri_task)            
        else:
            return (None, None)
        
    def _hasAllDeps(self,dep_storage_buff, task):
        
        task_ids_in_dep_storage_buff = []
        task_dep_taskids = task.get_dependencies()
        
        if(len(task_dep_taskids) > 0):   
            
#            task_ids_in_dep_storage_buff = [each_task.get_id() for each_task in dep_storage_buff 
#                                            if ((each_task.get_status() not in [TaskStatus.TASK_DATA_TRANSMISSION_IN_PROGRESS])) and
#                                            (each_task.get_id() in task_dep_taskids)]
             
            task_ids_in_dep_storage_buff = set([each_task.get_id() for each_task in dep_storage_buff])
             
#            for each_task in dep_storage_buff:
#                if(each_task.get_status() not in [TaskStatus.TASK_DATA_TRANSMISSION_IN_PROGRESS]):
#                    task_ids_in_dep_storage_buff.append(each_task.get_id())
            
#            if(len(task_ids_in_dep_storage_buff) >0 and len(task_dep_taskids) >0):                
            set_common = list(set(task_ids_in_dep_storage_buff) & set(task_dep_taskids))
                
                # if all the dependencies we need are here return true, else false
            if(len(set_common) == len(task_dep_taskids)):
                return True
            else:
                return False

#                if(len(task_ids_in_dep_storage_buff)==len(task_dep_taskids)):
#                    return True
#                else:
#                    return False
#
#            else:
#                return False
        else:   # task doesn't have any dependencies (e.g. Iframe) :)
            return True






# in HEVC the deps are at the Slice/CTU/PU level, but for now we work at the frame level
class LocalHEVCFramePriorityScheduler_WithDepCheck(object):
    
    LABEL = "LocalHEVCFramePriorityScheduler_WithDepCheck"    
    
    def nextTask(self, task_q, ix_orig, dep_storage_buff, time_now):
        #print "LocalHEVCFramePriorityScheduler_WithDepCheck::nextTask : enter"
        
        if len(task_q) == 0:
            return (None, None)
        
        ## create temporary list of dicts        
        new_task_q = []
        for idx, each_task in enumerate(task_q):
            temp = {
                    'ix'    : idx,
                    'task'  : each_task,
                    }
            
            if(each_task.get_frameType() in ["P", "B"]): # only P/B frames have deps
                if(each_task.get_taskStartTime() == None): # we don't need to check for deps if we have already started this task
                    if(self._hasAllDeps(dep_storage_buff, each_task) == True):
                        new_task_q.append(temp)
                else:
                    new_task_q.append(temp)
            else:                
                new_task_q.append(temp)                
                
        
        if(len(new_task_q)>0):            
            # no sorting !
            task_q_list = new_task_q
            
            ## find highest priority task in taskQ
            ## larger values ===> higher priority
            pri_sorted_task_q = sorted(task_q_list, key=lambda x: x['task'].get_priority(), reverse=True) # desc order
            
            high_pri_task = pri_sorted_task_q[0]['task']
            high_pri_task_ix = pri_sorted_task_q[0]['ix']
            
            return (high_pri_task_ix, high_pri_task)            
        else:
            return (None, None)
        
        
    
    # this gets all frames that have the deps for the current processing unit    
    def _hasAllDeps(self,dep_storage_buff, task):
        ':type task: HEVCFrameTask'
        if task.get_id() in dep_storage_buff:
            completed_deps_set = set(dep_storage_buff[task.get_id()])
        else:
            completed_deps_set = set([])
        
        task_deps = task.get_dependencies()
        
#         print "---"
#         print "dep_storage_buff : ", json.dumps(dep_storage_buff)
#         print "task_deps : ", task_deps
#         print "---"
        
        if ((len(task_deps)==0) and task.get_frameType() != "I"):
            sys.exit('_hasAllDeps: Error - there are no deps')
                        
        required_deps_set = set(task_deps)
        return (completed_deps_set == required_deps_set)
        
        ## below code can be used for CTU level dep checking
        # can the task proceed to execute
#         if(task.isCTUDepsComplete(task.getCurrentlyProcessingUnitRef()['slice_id'], 
#                                   task.getCurrentlyProcessingUnitRef()['ctu_id'])):
#             return True
#         else:
#             return False
#         




# in HEVC the deps are at the Slice/CTU/PU level, but for now we work at the tile level
class LocalHEVCTilePriorityScheduler_WithDepCheck(object):
    
    LABEL = "LocalHEVCTilePriorityScheduler_WithDepCheck"    
    
    # enum for task deps completed status
    TASKDEPS_INCOMPLETE = 0
    TASKDEPS_COMPLETE = 1
    TASKDEPS_UNKNOWN = 2
    
    
    
    def __init__(self):
        self.tasks_deps_status = {}
    
    def nextTask(self, task_q, ix_orig, dep_storage_buff, time_now):
        #print "LocalHEVCFramePriorityScheduler_WithDepCheck::nextTask : enter"
        
        if len(task_q) == 0:
            return (None, None)
        
        ## create temporary list of dicts        
        new_task_q = []
        for idx, each_task in enumerate(task_q):
            temp = {
                    'ix'    : idx,
                    'task'  : each_task,
                    }
            task_id = each_task.get_id()
            if(each_task.get_frameType() in ["P", "B"]): # only P/B frames have deps
                if(each_task.get_taskStartTime() == None): # we don't need to check for deps if we have already started this task
                    
                    if task_id in self.tasks_deps_status: # check in table
                        if self.tasks_deps_status[task_id] == self.TASKDEPS_COMPLETE:
                            new_task_q.append(temp)
                        elif self.tasks_deps_status[task_id] == self.TASKDEPS_INCOMPLETE:
                            pass
                        elif self.tasks_deps_status[task_id] == self.TASKDEPS_UNKNOWN: # task status unclear
                            if(self._hasAllDeps(dep_storage_buff, each_task) == True):
                                new_task_q.append(temp)
                            else:
                                pass                        
                    else:                        
                        if(self._hasAllDeps(dep_storage_buff, each_task) == True): # task not in table
                            new_task_q.append(temp)
                        else:
                            pass
                else:
                    new_task_q.append(temp)
            else:                
                new_task_q.append(temp)                
                
        
        if(len(new_task_q)>0):            
            # no sorting !
            task_q_list = new_task_q
            
            ## find highest priority task in taskQ
            ## larger values ===> higher priority
            pri_sorted_task_q = sorted(task_q_list, key=lambda x: x['task'].get_priority(), reverse=True) # desc order
            
            high_pri_task = pri_sorted_task_q[0]['task']
            high_pri_task_ix = pri_sorted_task_q[0]['ix']
            
            return (high_pri_task_ix, high_pri_task)            
        else:
            return (None, None)
        
        
    
    def markTasksDeps(self, completed_task_id, target_task_id, task_q, dep_storage_buff, time_now=None):        
        task = None
        tq_ix = None
        # locate task obj
        for ix, t in enumerate(task_q): # check in task q
            if t.get_id() == target_task_id:
                task = t
                tq_ix = ix
                break
        
        # set task deps status    
        if (task==None): 
            self.tasks_deps_status[target_task_id] = self.TASKDEPS_UNKNOWN
        else:
            if (self._hasAllDeps(dep_storage_buff, task)==True):
                self.tasks_deps_status[target_task_id] = self.TASKDEPS_COMPLETE
                
                # set the time which all deps were complete
                if (tq_ix != None) and (time_now!=None):                    
                    task_q[tq_ix].set_deps_allcomplete_time(time_now)
                else:
                    pass
                
            else:
                self.tasks_deps_status[target_task_id] = self.TASKDEPS_INCOMPLETE
            
            
            
            
                
         
    
    
    # this gets all frames that have the deps for the current processing unit    
    def _hasAllDeps(self,dep_storage_buff, task):
        ':type task: HEVCFrameTask'
        if task.get_id() in dep_storage_buff:
            completed_deps_set = set(dep_storage_buff[task.get_id()])
        else:
            completed_deps_set = set([])
        
        task_deps = task.get_dependencies()
        
#         print "---"
#         print "dep_storage_buff : ", json.dumps(dep_storage_buff)
#         print "task_deps : ", task_deps
#         print "---"
        
        if ((len(task_deps)==0) and task.get_frameType() != "I"):
            sys.exit('_hasAllDeps: Error - there are no deps')
                        
        required_deps_set = set(task_deps)
        return (completed_deps_set == required_deps_set)
        
        ## below code can be used for CTU level dep checking
        # can the task proceed to execute
#         if(task.isCTUDepsComplete(task.getCurrentlyProcessingUnitRef()['slice_id'], 
#                                   task.getCurrentlyProcessingUnitRef()['ctu_id'])):
#             return True
#         else:
#             return False
#         

    


