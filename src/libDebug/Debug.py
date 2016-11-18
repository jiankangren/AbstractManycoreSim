import pprint
import sys
from time import gmtime, strftime

import simpy

## local imports
from SimParams import SimParams



class Debug:
    
    @staticmethod
    def PPrint(msg, category):
        
        wall_clock_time_now = strftime("[%H:%M:%S] , ", gmtime())
        
        msg = wall_clock_time_now + msg
        
        if(category == DebugCat.DEBUG_CAT_INTERRUPT) and (SimParams.DEBUG_LVL_CAT_INTERRUPT == True) :
            print msg
        elif(category == DebugCat.DEBUG_CAT_TRANSMIT) and (SimParams.DEBUG_LVL_CAT_TRANSMIT == True) :
            print msg
        elif(category == DebugCat.DEBUG_CAT_CPUINFO) and (SimParams.DEBUG_LVL_CAT_CPUINFO == True) :
            print msg
        elif(category == DebugCat.DEBUG_CAT_CPUINFO_VERBOSE) and (SimParams.DEBUG_LVL_CAT_CPUINFO_VERBOSE == True) :
            print msg
        elif(category == DebugCat.DEBUG_CAT_RMINFO) and (SimParams.DEBUG_LVL_CAT_RMINFO == True) :
            print msg
        elif(category == DebugCat.DEBUG_CAT_TDINFO) and (SimParams.DEBUG_LVL_CAT_TDINFO == True) :
            print msg        
        elif(category == DebugCat.DEBUG_CAT_TDDROPPEDTASKS) and (SimParams.DEBUG_LVL_CAT_TDDROPPEDTASKS == True) :
            print msg        
        elif(category == DebugCat.DEBUG_CAT_MAPPERINFO) and (SimParams.DEBUG_LVL_CAT_MAPPERINFO == True) :
            print msg
        elif(category == DebugCat.DEBUG_CAT_RMINFO_VERBOSE) and (SimParams.DEBUG_LVL_CAT_RMINFO_VERBOSE == True) :
            print msg
        elif(category == DebugCat.DEBUG_CAT_NOCFLWTBLINFO) and (SimParams.DEBUG_LVL_CAT_NOCFLWTBLINFO == True) :
            print msg
        elif(category == DebugCat.DEBUG_CAT_SCHEDANALYSIS) and (SimParams.DEBUG_LVL_CAT_SCHEDANALYSIS == True) :
            print msg
        elif(category == DebugCat.DEBUG_CAT_NOCFLOW) and (SimParams.DEBUG_LVL_CAT_NOCFLOW == True) :
            print msg
        elif(category == DebugCat.DEBUG_CAT_RUNTIMEAPP) and (SimParams.DEBUG_LVL_CAT_RUNTIMEAPP == True) :
            print msg
        elif(category == DebugCat.DEBUG_CAT_LOCALSCHED_PREEMPT) and (SimParams.DEBUG_LVL_CAT_LOCALSCHED_PREEMPT == True) :
            print msg            
        elif(category == DebugCat.DEBUG_CAT_PSALGO) and (SimParams.DEBUG_LVL_CAT_PSALGO == True) :            
            print msg
        elif(category == DebugCat.DEBUG_CAT_TASKREMAPPING) and (SimParams.DEBUG_LVL_CAT_TASKREMAPPING == True) :                        
            print msg            
        elif(category == DebugCat.DEBUG_CAT_TASKREMAPPING_NOTIFICATION) and (SimParams.DEBUG_LVL_CAT_TASKREMAPPING_NOTIFICATION == True) :
            print msg
        elif(category == DebugCat.DEBUG_CAT_MSSIGNALLING) and (SimParams.DEBUG_LVL_CAT_MSSIGNALLING == True):
            print msg            
        elif(category == DebugCat.DEBUG_CAT_MMCNODEDATATRANSFER) and (SimParams.DEBUG_LVL_CAT_MMCNODEDATATRANSFER == True):
            print msg        
        elif(category == DebugCat.DEBUG_CAT_CCPROTOCOL) and (SimParams.DEBUG_LVL_CAT_CCPROTOCOL == True):            
            print msg
        
        
        
        sys.stdout.flush()   
            
        


class DebugCat:
    DEBUG_CAT_INTERRUPT                 = 0
    DEBUG_CAT_TRANSMIT                  = 1
    DEBUG_CAT_SCHEDANALYSIS             = 2
    DEBUG_CAT_RUNTIMEAPP                = 3
    
    DEBUG_CAT_CPUINFO                   = 20
    DEBUG_CAT_RMINFO                    = 21 
    DEBUG_CAT_RMINFO_VERBOSE            = 22   
    DEBUG_CAT_TDINFO                    = 23
    DEBUG_CAT_TDDROPPEDTASKS            = 24
    DEBUG_CAT_MAPPERINFO                = 25
    DEBUG_CAT_NOCFLWTBLINFO             = 26
    DEBUG_CAT_NOCFLOW                   = 27
    DEBUG_CAT_LOCALSCHED_PREEMPT        = 28
    DEBUG_CAT_TASKREMAPPING             = 29
    DEBUG_CAT_TASKREMAPPING_NOTIFICATION    = 30    
    DEBUG_CAT_PSALGO                    = 31
    DEBUG_CAT_MSSIGNALLING              = 32
    DEBUG_CAT_MMCNODEDATATRANSFER       = 33
    DEBUG_CAT_CCPROTOCOL                = 34
    DEBUG_CAT_CPUINFO_VERBOSE           = 35
    
    