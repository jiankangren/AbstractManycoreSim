import sys, os, csv, pprint, math
import argparse
import json

import numpy as np
import random
import shutil
import time
from util_scripts.psbased_remapping_random_params_generation import generate_random_params

import simpy

## uncomment when running under CLI only version ##
import matplotlib
matplotlib.use('Agg')

from libProcessingElement.LocalScheduler import LocalRRScheduler,    \
                        LocalEDFScheduler, \
                        LocalMPEG2FrameEDFScheduler, \
                        LocalMPEG2FrameListScheduler, \
                        LocalMPEG2FramePriorityScheduler, \
                        LocalMPEG2FramePriorityScheduler_WithDepCheck 

from libResourceManager.RMTypes import RMTypes
from libProcessingElement.CPUTypes import CPUTypes
from libResourceManager.Mapper.MapperTypes import MapperTypes
from libTaskDispatcher.TDTypes import TDTypes

from libResourceManager.AdmissionControllerOptions import AdmissionControllerOptions
from libMappingAndScheduling.SemiDynamic.TaskMappingSchemes import TaskMappingSchemes
from libMappingAndScheduling.SemiDynamic.TaskSemiDynamicPrioritySchemes import TaskSemiDynamicPrioritySchemes
from libMappingAndScheduling.SemiDynamic.TaskMappingAndPriAssCombinedSchemes import TaskMappingAndPriAssCombinedSchemes 
from libMappingAndScheduling.Decentralised.TaskRemapDecentSchemes import TaskRemapDecentSchemes
from libMappingAndScheduling.Decentralised.TaskRemapDecentSchemesImpl import TaskRemapDecentSchemesImpl
from SimParams import SimParams


import Multicore_MPEG_Model as MMMSim


NUM_WORKFLOWS = range(8, 17, 2)
#NUM_WORKFLOWS = [12]
NUM_NODES = [2,4,8,16,32]
NOC_XY = [(2,1), (2,2), (2,4), (2,8), (2,16)]

NOC_H = 4
NOC_W = 4


# name the report filenames
tm_fname                = "test__timeline.png"
vs_bs_fname             = "test__vsbs.js"
util_fname              = "test__util.js"
wf_res_fname            = "test__wfressumm.js"
gops_opbuff_fname       = "test__gopsopbuffsumm.js"
gops_opbuff_short_fname = "test__gopsopbuffsummshort.js"
rmtbl_dt_fname          = "test__rmtbldt.js"
ibuff_fname             = "test__ibuff.js"
obuff_fname             = "test__obuff.js"
obuff_short_fname       = "test__obuffshort.js"
nodetqs_fname           = "test__nodetqs.js"
rmtaskrelease_fname     = "test__rmtaskrel.js"
mappingandpriass_fname  = "test__mappingandpriass.js"
flowscompleted_fname    = "test__flwcompleted.js"
nodetaskexectime_fname  = "test__nodetaskexectime.js" 
psalgo_nodeprops        = "test__psalgonodeprops.js"
flowsadded_fname        = "test__flwsadded.js"
trminfo_fname           = "test__taskremappinginfo.js"
nodecumslack_fname      = "test__nodecumslack.js"
node_importedtasks      = "test__nodeimportedtasks.js"

##########################################################
# PSBased remapping - OFF
##########################################################
def runSim_RemappingMCParamsTest_RMOFF(seed=77379):
    
    # fixed params
    SimParams.NOC_W = NOC_W
    SimParams.NOC_H = NOC_W
    SimParams.NUM_NODES = (SimParams.NOC_W * SimParams.NOC_H)
    SimParams.NUM_WORKFLOWS = SimParams.NUM_NODES + 3
    SimParams.NUM_INPUTBUFFERS = SimParams.NUM_WORKFLOWS
    SimParams.LOCAL_SCHEDULER_TYPE = LocalMPEG2FramePriorityScheduler_WithDepCheck()
    SimParams.SIM_ENTITY_RESOURCEMANAGER_CLASS    = RMTypes.OPENLOOP
    SimParams.SIM_ENTITY_CPUNODE_CLASS            = CPUTypes.OPENLOOP
    SimParams.SIM_ENTITY_MAPPER_CLASS             = MapperTypes.OPENLOOP
    SimParams.SIM_ENTITY_TASKDISPATCHER_CLASS     = TDTypes.OPENLOOP    
    SimParams.COMBINED_MAPPING_AND_PRIASS = TaskMappingAndPriAssCombinedSchemes.TASKMAPPINGANDPRIASSCOMBINED_DISABLED
    SimParams.DYNAMIC_TASK_MAPPING_SCHEME = TaskMappingSchemes.TASKMAPPINGSCHEMES_LOWEST_UTILISATION
    SimParams.DYNAMIC_TASK_PRIASS_SCHEME =  TaskSemiDynamicPrioritySchemes.TASKSEMIDYNAMICPRIORITYSCHEMES_LOWRES_FIRST
                
    DATA_FOLDER = "experiment_data/remapping_psbased_montecarlo/"+"seed_"+str(seed)+"/"
        
    SimParams.PSALGO_ENABLED = False
    SimParams.DYNAMIC_TASK_REMAPPING_ENABLED = False
    SimParams.DYNAMIC_TASK_REMAPPING_SCHEME = TaskRemapDecentSchemes.TASKREMAPPINGDECENTSCHEMES_NONE
    SimParams.CPUNODE_MONITOR_TASKSET_SLACK = False
    SimParams.PSALGO_VIEWER_ENABLED = False
    SimParams.MMC_ENABLE_DATATRANSMISSION_MODELLING = False    
    
    FNAME_PREFIX = DATA_FOLDER+"RMOFF_"
    fname_param_prefix = FNAME_PREFIX
    
    # check if the simulation has run already before continuing, by checking if 
    # one of the output file exists
    check_fname = fname_param_prefix+obuff_short_fname 
    print "Checking file exists : " + str(check_fname)
    if(_check_file_exists(check_fname) == True):
        print "Simulation already exists ! "
    else:        
        random.seed(seed)
        np.random.seed(seed)
        print "----------------------------------------------------------------------------------------------------------------------------"
        print "Running runSim_RemappingMCParamsTest_RMOFF : num_wf=" + str(SimParams.NUM_WORKFLOWS)
        print fname_param_prefix
        print "SEED === " + str(seed)
        print "----------------------------------------------------------------------------------------------------------------------------"
                
        env, last_scheduled_task_time = MMMSim.runMainSimulation()
        env.run(until=last_scheduled_task_time+SimParams.SIM_RUNTIME)
        print env.now        
        
        (wf_results_summary, gops_in_outputbuff_summary) = MMMSim.SimMon.report_DecodedWorkflows_Summary(timeline_fname         =fname_param_prefix+tm_fname, 
                                                                                                         wf_res_summary_fname   = fname_param_prefix+wf_res_fname, 
                                                                                                        gops_opbuff_summary_fname = fname_param_prefix+gops_opbuff_fname,
                                                                                                        rmtbl_dt_summary_fname    = fname_param_prefix+rmtbl_dt_fname,
                                                                                                        gops_opbuff_summary_short_fname = fname_param_prefix+gops_opbuff_short_fname,
                                                                                                        output_format = "json")
        
        MMMSim.SimMon.report_OutputBufferContents_short(dump_to_file=fname_param_prefix+obuff_short_fname)
        MMMSim.SimMon.report_TaskRemappingInfo(dump_to_file=fname_param_prefix+trminfo_fname)
        

##########################################################
# PSBased remapping - ON
##########################################################
# remapping on full fact params test
def runSim_RemappingMCParamsTest_RMON(seed=77379,
                                 param_rand_TQN = None,           
                                 param_rand_TDECAY = None,
                                 param_rand_THRESHOLDQN = None, 
                                 param_rand_THRESHOLDHOPCOUNT = None,
                                 param_rand_THRESHOLDQN_RAT_DECREASE = None,
                                 param_rand_THRESHOLDQN_RAT_INCREASE = None,               
                                 param_rand_KHOPDECAY = None,            
                                 param_rand_KTIMEDECAY = None,             
                                 param_rand_HQN = None,              
                                 param_rand_INITHD = None,
                                 param_rand_REMAP_PERIOD = None,                                            
                                 param_rand_LATENESS_RATIO = None,
                                 fname_param = None
                                 ):
    
    if( (param_rand_TQN == None) or           
        (param_rand_TDECAY == None) or               
        (param_rand_THRESHOLDQN == None) or 
        (param_rand_THRESHOLDQN_RAT_DECREASE == None) or
        (param_rand_THRESHOLDQN_RAT_INCREASE == None) or 
        (param_rand_THRESHOLDHOPCOUNT == None) or           
        (param_rand_KHOPDECAY == None) or            
        (param_rand_KTIMEDECAY == None) or            
        (param_rand_HQN == None) or              
        (param_rand_INITHD == None) or
        (param_rand_REMAP_PERIOD == None) or 
        (fname_param == None) or                                            
        (param_rand_LATENESS_RATIO == None)
        ):        
        sys.exit('runSim_RemappingMCParamsTest_RMON:: not enough params !!')
       
    print "SEED === " + str(seed)    
        
    # fixed params
    SimParams.NOC_W = NOC_W
    SimParams.NOC_H = NOC_W
    SimParams.NUM_NODES = (SimParams.NOC_W * SimParams.NOC_H)
    SimParams.NUM_WORKFLOWS = SimParams.NUM_NODES + 3
    SimParams.NUM_INPUTBUFFERS = SimParams.NUM_WORKFLOWS
    SimParams.LOCAL_SCHEDULER_TYPE = LocalMPEG2FramePriorityScheduler_WithDepCheck()
    SimParams.SIM_ENTITY_RESOURCEMANAGER_CLASS    = RMTypes.OPENLOOP
    SimParams.SIM_ENTITY_CPUNODE_CLASS            = CPUTypes.OPENLOOP
    SimParams.SIM_ENTITY_MAPPER_CLASS             = MapperTypes.OPENLOOP
    SimParams.SIM_ENTITY_TASKDISPATCHER_CLASS     = TDTypes.OPENLOOP    
    SimParams.COMBINED_MAPPING_AND_PRIASS = TaskMappingAndPriAssCombinedSchemes.TASKMAPPINGANDPRIASSCOMBINED_DISABLED
    SimParams.DYNAMIC_TASK_MAPPING_SCHEME = TaskMappingSchemes.TASKMAPPINGSCHEMES_LOWEST_UTILISATION
    SimParams.DYNAMIC_TASK_PRIASS_SCHEME =  TaskSemiDynamicPrioritySchemes.TASKSEMIDYNAMICPRIORITYSCHEMES_LOWRES_FIRST
        
    DATA_FOLDER = "experiment_data/remapping_psbased_montecarlo/"+"seed_"+str(seed)+"/"
        
    SimParams.PSALGO_ENABLED = True
    SimParams.DYNAMIC_TASK_REMAPPING_ENABLED = True
    SimParams.DYNAMIC_TASK_REMAPPING_SCHEME = TaskRemapDecentSchemes.TASKREMAPPINGDECENTSCHEMES_LOWESTBLOCKING_QUEEN_VIA_SYSSLACK
    SimParams.CPUNODE_MONITOR_TASKSET_SLACK = True
    SimParams.PSALGO_VIEWER_ENABLED = False
    SimParams.MMC_ENABLE_DATATRANSMISSION_MODELLING = False
        
    FNAME_PREFIX = DATA_FOLDER+"RMON_"
    
    
#     # --------------------------------------------------------------------------------
#     # params taken from mc-test : perm_0.22_0.0629_20.0_0.3_0.3_4.6_
#     SimParams.PSALGO_TQN                                            = 0.22           
#     SimParams.PSALGO_TDECAY                                         = 0.0629               
#     SimParams.PSALGO_THRESHOLDQN                                    = 20.0
#     #SimParams.PSALGO_DYNAMIC_THRESHOLDQN_RATIO                      = [0.3, 0.3]
#     SimParams.DYNAMIC_TASK_REMAPPING_SAMPLING_INTERVAL              = 4.6
#     SimParams.PSALGO_THRESHOLDHOPCOUNT                              = 2
#     # --------------------------------------------------------------------------------
            
    # set params from arguments                                           
    SimParams.PSALGO_TQN                                            = param_rand_TQN           
    SimParams.PSALGO_TDECAY                                         = param_rand_TDECAY               
    #SimParams.PSALGO_THRESHOLDQN                                    = param_rand_THRESHOLDQN
    SimParams.PSALGO_DYNAMIC_THRESHOLDQN_RATIO                      = [param_rand_THRESHOLDQN_RAT_INCREASE, param_rand_THRESHOLDQN_RAT_DECREASE]                  
    SimParams.PSALGO_THRESHOLDHOPCOUNT                              = param_rand_THRESHOLDHOPCOUNT
    SimParams.PSALGO_KHOPDECAY                                      = param_rand_KHOPDECAY            
    SimParams.PSALGO_KTIMEDECAY                                     = param_rand_KTIMEDECAY             
    SimParams.PSALGO_HQN                                            = param_rand_HQN              
    #SimParams.PSALGO_INITIALHORMONEAMNT_WORKER                      = param_rand_INITHD              
    #SimParams.PSALGO_INITIALHORMONEAMNT_QUEEN                       = param_rand_INITHD 
    SimParams.DYNAMIC_TASK_REMAPPING_SAMPLING_INTERVAL              = param_rand_REMAP_PERIOD                                            
    #SimParams.DYNAMIC_TASK_REMAPPING_TASK_LATE_ESTIM_LATENESS_RATIO = param_rand_LATENESS_RATIO
        
#     fname_param_prefix = FNAME_PREFIX + str(param_rand_TQN) + \
#                             "_" + str(param_rand_TDECAY) + \
#                             "_" + str(param_rand_THRESHOLDQN) + \
#                             "_" + str(param_rand_THRESHOLDHOPCOUNT) + \
#                             "_" + str(param_rand_THRESHOLDQN_RAT_INCREASE) + \
#                             "_" + str(param_rand_THRESHOLDQN_RAT_DECREASE) + \
#                             "_" + str(param_rand_REMAP_PERIOD) + "_"

    fname_param_prefix = FNAME_PREFIX + fname_param + "_"
    
    # check if the simulation has run already before continuing, by checking if 
    # one of the output file exists     
    check_fname = fname_param_prefix + "resultssummary.js"
    print "Checking file exists : " + str(check_fname)
            
    run_sim = False
    if(_check_file_exists(check_fname) == True):        
        if(_is_resultssummary_error(check_fname) == False):
            print "Simulation already exists ! "
            run_sim = False
        else:
            run_sim = True
    else:
        run_sim = True
        
    if(run_sim == True):    
        random.seed(seed)
        np.random.seed(seed)
        print "----------------------------------------------------------------------------------------------------------------------------"
        print "Running runSim_RemappingMCParamsTest_RMON : num_wf=" + str(SimParams.NUM_WORKFLOWS)
        print fname_param_prefix
        print "SEED === " + str(seed)
        print "----------------------------------------------------------------------------------------------------------------------------"
                
        env, last_scheduled_task_time = MMMSim.runMainSimulation()
        env.run(until=last_scheduled_task_time+SimParams.SIM_RUNTIME)
        print env.now        
        
        (wf_results_summary, gops_in_outputbuff_summary) = MMMSim.SimMon.report_DecodedWorkflows_Summary(timeline_fname         =fname_param_prefix+tm_fname, 
                                                                                                         wf_res_summary_fname   = fname_param_prefix+wf_res_fname, 
                                                                                                        gops_opbuff_summary_fname = fname_param_prefix+gops_opbuff_fname,
                                                                                                        rmtbl_dt_summary_fname    = fname_param_prefix+rmtbl_dt_fname,
                                                                                                        gops_opbuff_summary_short_fname = fname_param_prefix+gops_opbuff_short_fname,
                                                                                                        output_format = "json")
        
        MMMSim.SimMon.report_OutputBufferContents_short(dump_to_file=fname_param_prefix+obuff_short_fname)
        MMMSim.SimMon.report_TaskRemappingInfo(dump_to_file=fname_param_prefix+trminfo_fname)

        

def _makeDir(directory):
    try:
        os.stat(directory)
    except:
        os.makedirs(directory)

def _check_file_exists(fname):
    return os.path.exists(fname)


def _is_resultssummary_error(fname):
    json_data=open(fname)
    file_data = json.load(json_data)
    
    if("GOP_Error" in file_data["result_gopl"]):
        return True
    else:
        return False
    
                    


############################################################################
############################################################################
##                MAIN SCRIPT SECTION
############################################################################
############################################################################
sys.setrecursionlimit(1500)

# collect command line params
parser = argparse.ArgumentParser(__file__, description="Run specified experiment on abstract simulator")
parser.add_argument("--forced_seed", help="experiment - seed", type=int, default=-1)
parser.add_argument("--exp_type", help="experiment type", default=None)

# psalgo related params
parser.add_argument("--tqn", help="param_rand_TQN", type=float, default=1.0)
parser.add_argument("--tdecay", help="param_rand_TDECAY", type=float, default=1.0)
parser.add_argument("--thresholdqn", help="param_rand_THRESHOLDQN", type=float, default=-1.0)
parser.add_argument("--thresholdhc", help="param_rand_THRESHOLDHOPCOUNT", type=int, default=-1)
parser.add_argument("--thresholdqn_r_d", help="param_rand_THRESHOLDQN_RAT_DECREASE", type=float, default=-1.0)
parser.add_argument("--thresholdqn_r_i", help="param_rand_THRESHOLDQN_RAT_INCREASE", type=float, default=-1.0)
parser.add_argument("--khopdec", help="param_rand_KHOPDECAY", type=float, default=1.0)
parser.add_argument("--ktimedec", help="param_rand_KTIMEDECAY", type=float, default=1.0)
parser.add_argument("--hqn", help="param_rand_HQN", type=int, default=-1)
parser.add_argument("--inithd", help="param_rand_INITHD", type=int, default=-1)
parser.add_argument("--remap_p", help="param_rand_REMAP_PERIOD", type=float, default=1.0)
parser.add_argument("--late_rat", help="param_rand_LATENESS_RATIO", type=float, default=1.0)
parser.add_argument("--fname_param", help="param_FNAME_PARAM", default=None)


args = parser.parse_args()

####################################
## check which experiment to run ##
####################################
if(args.exp_type == "RMOFF"):
    runSim_RemappingMCParamsTest_RMOFF(seed=args.forced_seed)

elif(args.exp_type == "RMON"):
    runSim_RemappingMCParamsTest_RMON(seed=args.forced_seed,
                                 param_rand_TQN = args.tqn,           
                                 param_rand_TDECAY = args.tdecay,               
                                 param_rand_THRESHOLDQN_RAT_DECREASE = args.thresholdqn_r_d,
                                 param_rand_THRESHOLDQN = args.thresholdqn,
                                 param_rand_THRESHOLDHOPCOUNT = args.thresholdhc,   
                                 param_rand_THRESHOLDQN_RAT_INCREASE = args.thresholdqn_r_i,            
                                 param_rand_KHOPDECAY = args.khopdec,            
                                 param_rand_KTIMEDECAY = args.ktimedec,             
                                 param_rand_HQN = args.hqn,              
                                 param_rand_INITHD = args.inithd,
                                 param_rand_REMAP_PERIOD = args.remap_p,                                            
                                 param_rand_LATENESS_RATIO = args.late_rat,
                                 fname_param = args.fname_param)
else:
    sys.exit("Error ! invalid exp type")
