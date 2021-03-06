import sys, os, csv, pprint, math
import argparse

import numpy as np
import random
import shutil
import time
from util_scripts.psbased_remapping_random_params_generation import generate_random_params

## uncomment when running under CLI only version ##
#import matplotlib
#matplotlib.use('Agg')

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import scipy.stats
from matplotlib.colors import ListedColormap, NoNorm
from matplotlib import mlab
from itertools import cycle # for automatic markers

import matplotlib.cm as cm
from matplotlib.font_manager import FontProperties

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

from SimParams import SimParams


import Multicore_MPEG_Model as MMMSim


NUM_WORKFLOWS = range(8, 17, 2)
#NUM_WORKFLOWS = [12]
NUM_NODES = [2,4,8,16,32]
NOC_XY = [(2,1), (2,2), (2,4), (2,8), (2,16)]
    
    
# remapping on/off experiment
def runSim_RandomRemappingBasic(run_rm_off=True, run_rm_on=True, seed=1234, multiseeds=False):
       
    print "SEED === " + str(seed)    
        
    ###############        
    # fixed params
    ###############
    SimParams.NOC_W = 10
    SimParams.NOC_H = 10
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
            
    if(multiseeds==True):
        #DATA_FOLDER = "experiment_data/remapping_randombased/"+"seed_"+str(seed)+"/"
		DATA_FOLDER = "experiment_data/remapping_random_initial_mapping/remapping_randombased/"+"seed_"+str(seed)+"/"
    else:        
        DATA_FOLDER = "experiment_data/remapping_randombased/"
        
    # name the report filenames
    tm_fname                = "test__timeline.png"
    vs_bs_fname             = "test__vsbs.js"
    util_fname              = "test__util.js"
    wf_res_fname            = "test__wfressumm.js"
    gops_opbuff_fname       = "test__gopsopbuffsumm.js"
    
    rmtbl_dt_fname          = "test__rmtbldt.js"
    ibuff_fname             = "test__ibuff.js"
    obuff_fname             = "test__obuff.js"
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
    rmdebuginfo_1           = "test__remappingdebuginfo_1.js"
    
    
    if(run_rm_off == True):
        ################################
        # Random Remapping disabled
        ################################        
        SimParams.DYNAMIC_TASK_REMAPPING_ENABLED = False        
        SimParams.DYNAMIC_TASK_REMAPPING_SCHEME = TaskRemapDecentSchemes.TASKREMAPPINGDECENTSCHEMES_NONE
        FNAME_PREFIX = DATA_FOLDER+"RMOFF_"
        random.seed(seed)
        np.random.seed(seed)
        print "----------------------------------------------------------------------------------------------------------------------------"
        print "Running runSim_RandomRemappingBasic : num_wf=" + str(SimParams.NUM_WORKFLOWS) + \
                ", Remapping_disabled"
        print "----------------------------------------------------------------------------------------------------------------------------"
                
        env, last_scheduled_task_time = MMMSim.runMainSimulation()
        env.run(until=last_scheduled_task_time+SimParams.SIM_RUNTIME)
        print env.now        
        
        (wf_results_summary, gops_in_outputbuff_summary) = MMMSim.SimMon.report_DecodedWorkflows_Summary(timeline_fname         =FNAME_PREFIX+tm_fname, 
                                                                                                         wf_res_summary_fname   = FNAME_PREFIX+wf_res_fname, 
                                                                                                        gops_opbuff_summary_fname = FNAME_PREFIX+gops_opbuff_fname,
                                                                                                        rmtbl_dt_summary_fname    = FNAME_PREFIX+rmtbl_dt_fname,
                                                                                                        output_format = "json")
        
        #MMMSim.SimMon.report_VideoStream_BasicStats(wf_results_summary, FNAME_PREFIX+vs_bs_fname)
        #MMMSim.SimMon.report_InstUtilisation(dump_to_file=FNAME_PREFIX+util_fname)
        #MMMSim.SimMon.report_InputBuffer(dump_to_file=FNAME_PREFIX+ibuff_fname)
        #MMMSim.SimMon.report_NodeTQs(dump_to_file=FNAME_PREFIX+nodetqs_fname)
        MMMSim.SimMon.report_OutputBufferContents(dump_to_file=FNAME_PREFIX+obuff_fname)
        #MMMSim.SimMon.report_RMTaskReleaseInfo(dump_to_file=FNAME_PREFIX+rmtaskrelease_fname)
        #MMMSim.SimMon.report_MappingAndPriAssInfo(dump_to_file=FNAME_PREFIX+mappingandpriass_fname)
        #MMMSim.SimMon.report_FlowsCompleted(dump_to_file=FNAME_PREFIX+flowscompleted_fname)
        #MMMSim.SimMon.report_NodeTaskExecTimeline(dump_to_file=FNAME_PREFIX+nodetaskexectime_fname)
        
        #MMMSim.SimMon.report_FlowsAdded(dump_to_file=FNAME_PREFIX+flowsadded_fname)
        MMMSim.SimMon.report_TaskRemappingInfo(dump_to_file=FNAME_PREFIX+trminfo_fname)
        #MMMSim.SimMon.report_NodeCumSlack(dump_to_file=FNAME_PREFIX+nodecumslack_fname)        
        #MMMSim.SimMon.report_NodeImportedTasks(dump_to_file=FNAME_PREFIX+node_importedtasks)
   
    
    if(run_rm_on == True): 
        ################################
        # PS-based Remapping enabled
        ################################        
        SimParams.DYNAMIC_TASK_REMAPPING_ENABLED = True
        SimParams.CPUNODE_MONITOR_TASKSET_SLACK = True
        SimParams.DYNAMIC_TASK_REMAPPING_SCHEME = TaskRemapDecentSchemes.TASKREMAPPINGDECENTSCHEMES_RANDOM_ANY
        SimParams.DYNAMIC_TASK_REMAPPING_SAMPLING_INTERVAL              = 4.6
        FNAME_PREFIX = DATA_FOLDER+"RMON_"
        random.seed(seed)
        np.random.seed(seed)
        print "----------------------------------------------------------------------------------------------------------------------------"
        print "Running runSim_RandomRemappingBasic : num_wf=" + str(SimParams.NUM_WORKFLOWS) + \
                ", Remapping_enabled"
        print "----------------------------------------------------------------------------------------------------------------------------"
                
        env, last_scheduled_task_time = MMMSim.runMainSimulation()
        env.run(until=last_scheduled_task_time+SimParams.SIM_RUNTIME)
        print env.now        
        
        (wf_results_summary, gops_in_outputbuff_summary) = MMMSim.SimMon.report_DecodedWorkflows_Summary(timeline_fname         =FNAME_PREFIX+tm_fname, 
                                                                                                         wf_res_summary_fname   = FNAME_PREFIX+wf_res_fname, 
                                                                                                        gops_opbuff_summary_fname = FNAME_PREFIX+gops_opbuff_fname,
                                                                                                        rmtbl_dt_summary_fname    = FNAME_PREFIX+rmtbl_dt_fname,
                                                                                                        output_format = "json")
        
        #MMMSim.SimMon.report_VideoStream_BasicStats(wf_results_summary, FNAME_PREFIX+vs_bs_fname)
        #MMMSim.SimMon.report_InstUtilisation(dump_to_file=FNAME_PREFIX+util_fname)
        #MMMSim.SimMon.report_InputBuffer(dump_to_file=FNAME_PREFIX+ibuff_fname)
        #MMMSim.SimMon.report_NodeTQs(dump_to_file=FNAME_PREFIX+nodetqs_fname)
        MMMSim.SimMon.report_OutputBufferContents(dump_to_file=FNAME_PREFIX+obuff_fname)
        #MMMSim.SimMon.report_RMTaskReleaseInfo(dump_to_file=FNAME_PREFIX+rmtaskrelease_fname)
        #MMMSim.SimMon.report_MappingAndPriAssInfo(dump_to_file=FNAME_PREFIX+mappingandpriass_fname)
        #MMMSim.SimMon.report_FlowsCompleted(dump_to_file=FNAME_PREFIX+flowscompleted_fname)
        MMMSim.SimMon.report_NodeTaskExecTimeline(dump_to_file=FNAME_PREFIX+nodetaskexectime_fname)        
        #MMMSim.SimMon.report_FlowsAdded(dump_to_file=FNAME_PREFIX+flowsadded_fname)
        MMMSim.SimMon.report_TaskRemappingInfo(dump_to_file=FNAME_PREFIX+trminfo_fname)
        MMMSim.SimMon.report_NodeCumSlack(dump_to_file=FNAME_PREFIX+nodecumslack_fname)        
        MMMSim.SimMon.report_NodeImportedTasks(dump_to_file=FNAME_PREFIX+node_importedtasks)
        
   
 

def _makeDir(directory):
    try:
        os.stat(directory)
    except:
        os.makedirs(directory)

def _check_file_exists(fname):
    return os.path.exists(fname)


############################################################################
############################################################################
##                MAIN SCRIPT SECTION
############################################################################
############################################################################
sys.setrecursionlimit(1500)

# collect command line params
parser = argparse.ArgumentParser(__file__, description="Run specified experiment on abstract simulator")
parser.add_argument("--exp_type", "-t", help="Experiment Type", default=None)   # which experiment ?

# params for mapping + pri ass exp
parser.add_argument("--wf_num", "-w", help="Number of workflows", type=int, default=-1)
parser.add_argument("--forced_seed", help="experiment - seed", type=int, default=-1)
args = parser.parse_args()

####################################
## check which experiment to run ##
####################################

# basic rm on/off
if(args.exp_type == "Exp_RemappingBasic"):
    if(args.forced_seed != -1):
        runSim_RandomRemappingBasic(run_rm_off=True, run_rm_on=True, seed=args.forced_seed, multiseeds=True)
    else:
        runSim_RandomRemappingBasic(run_rm_off=True, run_rm_on=True)

else:
    #parser.print_usage()
    #sys.exit("invalid arguments")
    runSim_RandomRemappingBasic(run_rm_off=True, run_rm_on=True)
    

