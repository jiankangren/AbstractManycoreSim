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

from SimParams import SimParams

import Multicore_MPEG_Model as MMMSim


NUM_WORKFLOWS = range(8, 17, 2)
#NUM_WORKFLOWS = [12]
NUM_NODES = [2,4,8,16,32]
NOC_XY = [(2,1), (2,2), (2,4), (2,8), (2,16)]


EXP_DATADIR = "experiment_data/nearestneighbour_vs_nocsize/"



# basic test - openloop
def runSim_Simple_OpenLoop_NNTest(noc_h, noc_w, combined_mapping_option, normal_mapping_scheme, normal_priass_scheme):
    
    seed = 99108    
    
    print "SEED === " + str(seed)    
             
    # fixed params
    SimParams.SLACK_FEEDBACK_ENABLED = False
    
    SimParams.NOC_W = noc_w
    SimParams.NOC_H = noc_h
    SimParams.NUM_NODES = (SimParams.NOC_W * SimParams.NOC_H)
    SimParams.NUM_WORKFLOWS = SimParams.NUM_NODES * 2
    SimParams.NUM_INPUTBUFFERS = SimParams.NUM_WORKFLOWS
    SimParams.LOCAL_SCHEDULER_TYPE = LocalMPEG2FramePriorityScheduler_WithDepCheck()
    
    SimParams.SIM_ENTITY_RESOURCEMANAGER_CLASS    = RMTypes.OPENLOOP
    SimParams.SIM_ENTITY_CPUNODE_CLASS            = CPUTypes.OPENLOOP
    SimParams.SIM_ENTITY_MAPPER_CLASS             = MapperTypes.OPENLOOP
    SimParams.SIM_ENTITY_TASKDISPATCHER_CLASS     = TDTypes.OPENLOOP
    
    # assign mapping scheme
    SimParams.DYNAMIC_TASK_MAPPING_SCHEME =  normal_mapping_scheme
    SimParams.DYNAMIC_TASK_PRIASS_SCHEME =  normal_priass_scheme
    SimParams.COMBINED_MAPPING_AND_PRIASS = combined_mapping_option      
        
    random.seed(seed)
    np.random.seed(seed)
    print "----------------------------------------------------------------------------------------------------------------------------"
    print "Running runSim_Simple_OpenLoop : num_wf=" + str(SimParams.NUM_WORKFLOWS) + \
            ", noc_h="+str(noc_h)+","+"noc_w="+str(noc_w) + \
            ", mapping="+str(SimParams.DYNAMIC_TASK_MAPPING_SCHEME) + \
            ", pri_ass="+str(SimParams.DYNAMIC_TASK_PRIASS_SCHEME) + \
            ", combined_mapping="+str(SimParams.COMBINED_MAPPING_AND_PRIASS)            
    print "----------------------------------------------------------------------------------------------------------------------------"
            
    env, last_scheduled_task_time = MMMSim.runMainSimulation()
    env.run(until=last_scheduled_task_time+SimParams.SIM_RUNTIME)
    print env.now        
    
    FNAME_PREFIX = "Mapping_" + \
                    str(SimParams.DYNAMIC_TASK_MAPPING_SCHEME) + "_" + \
                    str(SimParams.DYNAMIC_TASK_PRIASS_SCHEME) + "_" + \
                    str(SimParams.COMBINED_MAPPING_AND_PRIASS) + "_" + \
                    str(noc_h)+"_"+str(noc_w)+"_"
    
    # name the report filenames
    tm_fname                = EXP_DATADIR+FNAME_PREFIX+"test__timeline.png"
    vs_bs_fname             = EXP_DATADIR+FNAME_PREFIX+"test__vsbs.js"
    util_fname              = EXP_DATADIR+FNAME_PREFIX+"test__util.js"
    wf_res_fname            = EXP_DATADIR+FNAME_PREFIX+"test__wfressumm.js"
    gops_opbuff_fname       = EXP_DATADIR+FNAME_PREFIX+"test__gopsopbuffsumm.js"
    
    rmtbl_dt_fname          = EXP_DATADIR+FNAME_PREFIX+"test__rmtbldt.js"
    ibuff_fname             = EXP_DATADIR+FNAME_PREFIX+"test__ibuff.js"
    obuff_fname             = EXP_DATADIR+FNAME_PREFIX+"test__obuff.js"
    nodetqs_fname           = EXP_DATADIR+FNAME_PREFIX+"test__nodetqs.js"
    rmtaskrelease_fname     = EXP_DATADIR+FNAME_PREFIX+"test__rmtaskrel.js"
    mappingandpriass_fname  = EXP_DATADIR+FNAME_PREFIX+"test__mappingandpriass.js"
    flowscompleted_fname    = EXP_DATADIR+FNAME_PREFIX+"test__flwcompleted.js"
    nodetaskexectime_fname  = EXP_DATADIR+FNAME_PREFIX+"test__nodetaskexectime.js"
            
    
    (wf_results_summary, gops_in_outputbuff_summary) = MMMSim.SimMon.report_DecodedWorkflows_Summary(timeline_fname=tm_fname, 
                                                                                                     wf_res_summary_fname = wf_res_fname, 
                                                                                                    gops_opbuff_summary_fname = gops_opbuff_fname,
                                                                                                    rmtbl_dt_summary_fname = rmtbl_dt_fname,
                                                                                                    output_format = "json")
    
    MMMSim.SimMon.report_VideoStream_BasicStats(wf_results_summary, vs_bs_fname)
    MMMSim.SimMon.report_InstUtilisation(dump_to_file=util_fname)
    MMMSim.SimMon.report_NodeTQs(dump_to_file=nodetqs_fname)
    MMMSim.SimMon.report_OutputBufferContents(dump_to_file=obuff_fname)
    MMMSim.SimMon.report_FlowsCompleted(dump_to_file=flowscompleted_fname)
 


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


# params for mapping + pri ass exp
parser.add_argument("--noc_h", help="NoC height", type=int, default=-1)
parser.add_argument("--noc_w", help="NoC width", type=int, default=-1)

parser.add_argument("--mp_sch", help="mapping scheme", type=int, default=-1)
parser.add_argument("--pr_sch", help="priass scheme", type=int, default=-1)
parser.add_argument("--com_sch", help="combined scheme", type=int, default=-1)


args = parser.parse_args()

####################################
## check which experiment to run ##
####################################

if(args.noc_h == -1) or (args.noc_w == -1):
    parser.print_usage()
    sys.exit("invalid arguments")
else:
    
    # run experiment
    runSim_Simple_OpenLoop_NNTest(args.noc_h, args.noc_w,
                                   args.com_sch,
                                   args.mp_sch,
                                   args.pr_sch)    
   

