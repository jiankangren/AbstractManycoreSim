import pprint
import sys

## local imports
#from SimParams import SimParams



class Task:
    
    def __init__(self, env, type, id, cc, mmc, rt, d, p, pr , crt):
        self.env = env
        
        # minimum model
        self.type = type
        self.id = id
        self.computationCost = cc
        self.maxMemConsumption = mmc
        self.releaseTime = rt
        self.deadline = d   # relative deadline
        self.period = p
        self.priority = pr
        self.status = TaskStatus.TASK_NULL
        self.worstCaseComputationCost = None
        self.avgCaseComputationCost = None
               
        # extras
        self.timeLeftTillCompletion = None
        self.timeLeftTillDeadline = None 
        self.taskStartTime = None
        self.taskCompleteTime = None
        self.taskMMCWRCompleteTime = None
        self.missedDeadlineFlag = None      
        self.dependencies = None
        self.scheduledDispatchTime = None   # preassigned
        self.dispatchTime = None    # actual dispatch time        
        self.dispatchDisabled = False # we can stop this task from being dispatched
        self.createdTime = crt
        self.initiallyScheduled = False # havent been scheduled upon creation
        self.estimatedLateness = None   
        self.remainingComputationCost = None
        self.worstCaseRemainingComputationCost = None
        self.avgCaseRemainingComputationCost = None
        self.lastActiveTime = None
        self.processingCore = None
        
        # for pre-emptive systems
        self.blockedBy = {}
        self.blockedCount = 0
        
        self.processInstance = None # ??
    
    
    def __repr__(self):
        debug = "<Task "         
        debug += " type=" + self.type
        debug += " id=" + str(self.id) 
        debug += " cc=" + str(self.computationCost)
        debug += " mmc=" + str(self.maxMemConsumption)
        debug += " rt=" + str(self.releaseTime)
        debug += " d=" + str(self.deadline)
        debug += " p=" + str(self.period)
        debug += " pri=" + str(self.priority)
        debug += " stat=" +  str(self.status)
        debug += " tltc=" +  str(self.timeLeftTillCompletion)
        debug += " tltd=" +  str(self.timeLeftTillDeadline)
        debug += " st=" +  str(self.taskStartTime)
        debug += " tct=" +  str(self.taskCompleteTime)
        debug += " mdf=" +  str(self.missedDeadlineFlag)
        debug += " />"
        
        return debug
    
    
#    def __eq__(self, other):
#        return self.id == other.id
        
        
    
    ## setters ##
    def set_computationCost(self, cc):
        self.computationCost = cc            
    def set_maxMemConsumption(self,mmc):
        self.maxMemConsumption = mmc            
    def set_releaseTime(self,rt):
        self.releaseTime = rt            
    def set_deadline(self, d):
        self.deadline = d            
    def set_period(self, p):
        self.period = p     
    def set_timeLeftTillCompletion(self, tltc):
        self.timeLeftTillCompletion = tltc         
    def set_timeLeftTillDeadline(self, tltd):
        self.timeLeftTillDeadline = tltd        
    def set_processInstance(self, p):
        self.processInstance = p        
    def set_priority(self, pr):
        self.priority = pr        
    def set_taskStartTime(self, st):
        self.taskStartTime = st        
    def set_taskCompleteTime(self, ct):
        self.taskCompleteTime = ct    
    def set_taskMMCWRCompleteTime(self, ct):
        self.taskMMCWRCompleteTime = ct        
    def set_dependencies(self,deps):
        self.dependencies = deps    
    def set_missedDeadlineFlag(self, mdf):
        self.missedDeadlineFlag = mdf        
    def set_dispatchTime(self, dt):
        self.dispatchTime = dt    
    def set_scheduledDispatchTime(self, sdt):
        self.scheduledDispatchTime = sdt        
    def set_createdTime(self, crt):
        self.createdTime = crt    
    def set_worstCaseComputationCost(self, wcc):
        self.worstCaseComputationCost = wcc      
    def set_avgCaseComputationCost(self, avgcc):
        self.avgCaseComputationCost = avgcc
    def set_initiallyScheduled(self,inischd):
        self.initiallyScheduled = inischd        
    def set_dispatchDisabled(self,dispdis):
        self.dispatchDisabled = dispdis
    def set_estimatedLateness(self, estlate):
        self.estimatedLateness = estlate
    def set_remainingComputationCost(self, rcc):
        self.remainingComputationCost = rcc
    def set_worstCaseRemainingComputationCost(self, wccc):
        self.worstCaseRemainingComputationCost = wccc
    def set_avgCaseRemainingComputationCost(self, avgccc):
        self.avgCaseRemainingComputationCost = avgccc        
    def set_status(self, s):
        self.status = s
    def set_lastActiveTime(self, lat):
        self.lastActiveTime = lat
    def set_processingCore(self, pc):
        self.processingCore = pc
        
    def addBlockedBy(self, taskj):
        if taskj.get_id() not in self.blockedBy:
            self.blockedBy[taskj.get_id()] = taskj
    def removeBlockedBy(self, taskj):
        if taskj.get_id() in self.blockedBy:
            #self.blockedBy.remove(taskj)
            del self.blockedBy[taskj.get_id()]
    
    def check_missedDeadline(self):
        
        if(self.taskCompleteTime < (self.releaseTime + self.deadline)):
            self.missedDeadlineFlag = False
        else:
            self.missedDeadlineFlag = True
        
        return self.missedDeadlineFlag
        
    
    def willTaskMissItsDeadline(self, time_now):
        if(time_now + self.computationCost) < (self.releaseTime + self.deadline):
            return False
        else:
            return True
            
    
    def incrementBlockedCount(self):
        self.blockedCount += 1
    
    
    ## getters
    def get_id(self):
        return self.id
    def get_computationCost(self):
        return self.computationCost
    def get_maxMemConsumption(self):
        return self.maxMemConsumption    
    def get_taskStartTime(self):
        return self.taskStartTime
    def get_taskCompleteTime(self):
        return self.taskCompleteTime 
    def get_taskMMCWRCompleteTime(self):
        return self.taskMMCWRCompleteTime      
    def get_releaseTime(self):
        return self.releaseTime    
    def get_deadline(self):
        return self.deadline
    def get_timeLeftTillDeadline(self):
        return self.timeLeftTillDeadline
    def get_missedDeadlineFlag(self):
        return self.missedDeadlineFlag
    def get_dependencies(self):
        return self.dependencies
    def get_type(self):
        return self.type
    def get_worstCaseComputationCost(self):
        return self.worstCaseComputationCost
    def get_avgCaseComputationCost(self):
        return self.avgCaseComputationCost
    def get_initiallyScheduled(self):
        return self.initiallyScheduled
    def get_dispatchTime(self):
        return self.dispatchTime
    def get_scheduledDispatchTime(self):
        return self.scheduledDispatchTime
    def get_dispatchDisabled(self):
        return self.dispatchDisabled
    def get_estimatedLateness(self):
        return self.estimatedLateness
    def get_remainingComputationCost(self):
        return self.remainingComputationCost
    def get_worstCaseRemainingComputationCost(self):
        return self.worstCaseRemainingComputationCost
    def get_avgCaseRemainingComputationCost(self):
        return self.avgCaseRemainingComputationCost        
    def get_priority(self):
        return self.priority
    def get_lastActiveTime(self):
        return self.lastActiveTime
    def get_blockedBy(self):
        return self.blockedBy.values()
    def get_processingCore(self):
        return self.processingCore
    def get_period(self):
        return self.period
    def get_status(self):
        return self.status
    def get_blockedCount(self):
        return self.blockedCount
    
    
       
    ## compute task - i.e reduce time_left_till_completion by quntum size
    def compute(self, quantum):
        
        if(self.timeLeftTillCompletion > quantum):        
            self.timeLeftTillCompletion = self.timeLeftTillCompletion - quantum        
        elif(self.timeLeftTillCompletion == quantum):
            self.timeLeftTillCompletion = 0
        else:
            self.timeLeftTillCompletion = self.timeLeftTillCompletion
        
        # round to zero
        #if self.timeLeftTillCompletion < 0:
        #    self.timeLeftTillCompletion = 0            
        
        return self.timeLeftTillCompletion
        
class TaskStatus:
    TASK_NULL                           = 1     # task hasn't been dispatched yet
    TASK_DISPATCHED                     = 2
    TASK_RUNNING                        = 3
    TASK_BLOCKED                        = 4
    TASK_SUSPENDED                      = 5   
    TASK_COMPLETED                      = 6
    TASK_READY_WAITING                  = 7
    TASK_MARKED_FOR_RELEASE             = 8
    TASK_UNMAPPED                       = 9
    TASK_MAPPED                         = 10
    TASK_MAPPEDANDPRIASSIGNED           = 11
    TASK_DATA_TRANSMISSION_IN_PROGRESS  = 12
    TASK_DATA_TRANSMISSION_COMPLETE     = 13
    
    
class TaskModel:
    TASK_MODEL_MHEG2_GOP_LEVEL      = 1
    TASK_MODEL_MHEG2_FRAME_LEVEL    = 2
    TASK_MODEL_MHEG2_FRAME_TT_LEVEL = 3
    TASK_MODEL_MHEG2_FRAME_ET_LEVEL = 4
    TASK_MODEL_MHEG2_SLICE_LEVEL    = 5
    TASK_MODEL_MHEG2_FRAME_ET_LEVEL_INTERRELATEDGOPS = 6    
    TASK_MODEL_HEVC_FRAME_LEVEL     = 7
    TASK_MODEL_HEVC_TILE_LEVEL     = 8
    
    
    @staticmethod
    def taskModelSpecs(model):
        
        task_model_attribs = {}
        
        if (model == TaskModel.TASK_MODEL_MHEG2_GOP_LEVEL):
            task_model_attribs = {
                                  'dispatch_amount'     : 1, # 1 gop
                                  'have_dependencies'   : False                                  
                                  }
            
            
        elif(model == TaskModel.TASK_MODEL_MHEG2_FRAME_LEVEL):   
            task_model_attribs = {
                                  'dispatch_amount'     : 12, # all frames in gop gop
                                  'have_dependencies'   : True                                  
                                  }
        else:
            sys.exit("Error: TaskModel:taskModelSpecs:: Error - unknown task model")
            
        return task_model_attribs
            
            
    