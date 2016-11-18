import sys, os, csv, pprint, math
import argparse

import numpy as np
import random
import shutil
import time

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


# lateness vs. number of cores
def runSim_Simple():
    
    seed = 99108    
    
    print "SEED === " + str(seed)    
             
    # fixed params
    SimParams.SLACK_FEEDBACK_ENABLED = False
        
    SimParams.NOC_W = 4
    SimParams.NOC_H = 4
    SimParams.NUM_NODES = (SimParams.NOC_W * SimParams.NOC_H)
    SimParams.NUM_WORKFLOWS = SimParams.NUM_NODES + 3
    SimParams.NUM_INPUTBUFFERS = SimParams.NUM_WORKFLOWS
    SimParams.PSALGO_ENABLED = True
    SimParams.DYNAMIC_TASK_REMAPPING_ENABLED = True
    SimParams.DYNAMIC_TASK_REMAPPING_SCHEME = TaskRemapDecentSchemes.TASKREMAPPINGDECENTSCHEMES_RANDOM_QUEEN
    SimParams.CPUNODE_MONITOR_TASKSET_SLACK = True
    
    random.seed(seed)
    np.random.seed(seed)
    print "----------------------------------------------------------------------------------------------------------------------------"
    print "Running runSim_Simple : num_wf=" + str(SimParams.NUM_WORKFLOWS) + \
            ", mapping="+str(SimParams.DYNAMIC_TASK_MAPPING_SCHEME) + \
            ", pri_ass="+str(SimParams.DYNAMIC_TASK_PRIASS_SCHEME) 
    print "----------------------------------------------------------------------------------------------------------------------------"
            
    env, last_scheduled_task_time = MMMSim.runMainSimulation()
    env.run(until=last_scheduled_task_time+SimParams.SIM_RUNTIME)
    print env.now        
    
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
            
    
    (wf_results_summary, gops_in_outputbuff_summary) = MMMSim.SimMon.report_DecodedWorkflows_Summary(timeline_fname=tm_fname, 
                                                                                                     wf_res_summary_fname = wf_res_fname, 
                                                                                                    gops_opbuff_summary_fname = gops_opbuff_fname,
                                                                                                    rmtbl_dt_summary_fname = rmtbl_dt_fname,
                                                                                                    output_format = "json")
    
    MMMSim.SimMon.report_VideoStream_BasicStats(wf_results_summary, vs_bs_fname)
    MMMSim.SimMon.report_InstUtilisation(dump_to_file=util_fname)
    MMMSim.SimMon.report_InputBuffer(dump_to_file=ibuff_fname)
    MMMSim.SimMon.report_NodeTQs(dump_to_file=nodetqs_fname)
    MMMSim.SimMon.report_OutputBufferContents(dump_to_file=obuff_fname)
    MMMSim.SimMon.report_RMTaskReleaseInfo(dump_to_file=rmtaskrelease_fname)
    MMMSim.SimMon.report_MappingAndPriAssInfo(dump_to_file=mappingandpriass_fname)
    MMMSim.SimMon.report_FlowsCompleted(dump_to_file=flowscompleted_fname)
    MMMSim.SimMon.report_NodeTaskExecTimeline(dump_to_file=nodetaskexectime_fname)
    MMMSim.SimMon.report_PSAlgoNodePSProps(dump_to_file=psalgo_nodeprops)
    MMMSim.SimMon.report_FlowsAdded(dump_to_file=flowsadded_fname)
    MMMSim.SimMon.report_TaskRemappingInfo(dump_to_file=trminfo_fname)
    MMMSim.SimMon.report_NodeCumSlack(dump_to_file=nodecumslack_fname)
    
   



def _makeDir(directory):
    try:
        os.stat(directory)
    except:
        os.makedirs(directory)



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

#### multiple workflows - variable heuristics ####
if(args.exp_type == "Exp_Simple"):   
    runSim_Simple()


else:
    parser.print_usage()
    sys.exit("invalid arguments")


