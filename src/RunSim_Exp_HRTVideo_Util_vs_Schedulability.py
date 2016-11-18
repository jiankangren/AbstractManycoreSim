import sys, os, csv, pprint, math
import argparse

import numpy as np
import random
import shutil
import time

## uncomment when running under CLI only version ##
import matplotlib
matplotlib.use('Agg')

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

from util_scripts.resolution_combos import generate_resolution_combos

from SimParams import SimParams

import Multicore_MPEG_Model as MMMSim


NUM_WORKFLOWS = range(8, 17, 2)
#NUM_WORKFLOWS = [12]
NUM_NODES = [2,4,8,16,32]
NOC_XY = [(2,1), (2,2), (2,4), (2,8), (2,16)]


EXP_DATADIR = "experiment_data/hrt_video/util_vs_sched/"

# name the report filenames
global_tm_fname                     = "test__timeline.png"
global_vs_bs_fname                  = "test__vsbs.js"
global_util_fname                   = "test__util.js"
global_utilshort_fname              = "test__utilshort.js"
global_wf_res_fname                 = "test__wfressumm.js"
global_gops_opbuff_fname            = "test__gopsopbuffsumm.js"
global_gops_opbuff_short_fname      = "test__gopsopbuffsummshort.js"    
global_rmtbl_dt_fname               = "test__rmtbldt.js"
global_ibuff_fname                  = "test__ibuff.js"
global_obuff_fname                  = "test__obuff.js"
global_obuffshort_fname             = "test__obuffshort.js"
global_nodetqs_fname                = "test__nodetqs.js"
global_rmtaskrelease_fname          = "test__rmtaskrel.js"
global_mappingandpriass_fname       = "test__mappingandpriass.js"
global_flowscompleted_fname         = "test__flwcompleted.js"
global_nodetaskexectime_fname       = "test__nodetaskexectime.js"
global_schedtestresults_fname       = "test__schedtestresults.js"
global_schedtestresultsshort_fname  = "test__schedtestresultsshort.js"
global_utilvsschedresults_fname     = "test__utilvsschedresults.js"
global_utilvsschedresultsshort_fname = "test__utilvsschedresultsshort.js"

# basic test - openloop
def runSim_Simple():
    
    seed = 99108    
    
    print "SEED === " + str(seed)    
             
    # fixed params
    SimParams.SLACK_FEEDBACK_ENABLED = False
    
    SimParams.NOC_W = 3
    SimParams.NOC_H = 3
    SimParams.NUM_NODES = (SimParams.NOC_W * SimParams.NOC_H)
    
    dvb_resolutions = [(320,240),(320,240),(320,240),(320,240),(320,240)]
    
    SimParams.LOCAL_SCHEDULER_TYPE = LocalMPEG2FramePriorityScheduler_WithDepCheck()
    SimParams.SIM_ENTITY_RESOURCEMANAGER_CLASS    = RMTypes.OPENLOOP
    SimParams.SIM_ENTITY_CPUNODE_CLASS            = CPUTypes.OPENLOOP
    SimParams.SIM_ENTITY_MAPPER_CLASS             = MapperTypes.OPENLOOP
    SimParams.SIM_ENTITY_TASKDISPATCHER_CLASS     = TDTypes.OPENLOOP
    SimParams.DVB_RESOLUTIONS = dvb_resolutions
    SimParams.NUM_WORKFLOWS                 = 5
    SimParams.NUM_INPUTBUFFERS              = SimParams.NUM_WORKFLOWS
    SimParams.DVB_RESOLUTIONS_FIXED         = dvb_resolutions
    SimParams.DVB_RESOLUTIONS_SELECTED_RANDOM        = False
    
    SimParams.AC_TEST_OPTION = AdmissionControllerOptions.AC_OPTION_NONE
    SimParams.DYNAMIC_TASK_MAPPING_SCHEME = TaskMappingSchemes.TASKMAPPINGSCHEMES_LOWEST_UTILISATION
    SimParams.DYNAMIC_TASK_PRIASS_SCHEME  =  TaskSemiDynamicPrioritySchemes.TASKSEMIDYNAMICPRIORITYSCHEMES_LOWRES_FIRST    
    SimParams.COMBINED_MAPPING_AND_PRIASS = TaskMappingAndPriAssCombinedSchemes.TASKMAPPINGANDPRIASSCOMBINED_DISABLED
    
    
    random.seed(seed)
    np.random.seed(seed)
    print "----------------------------------------------------------------------------------------------------------------------------"
    print "Running runSim_Simple_OpenLoop : num_wf=" + str(SimParams.NUM_WORKFLOWS) + \
            ", noc_h="+str(SimParams.NOC_H)+","+"noc_w="+str(SimParams.NOC_W) + \
            ", mapping="+str(SimParams.DYNAMIC_TASK_MAPPING_SCHEME) + \
            ", pri_ass="+str(SimParams.DYNAMIC_TASK_PRIASS_SCHEME) 
    print "----------------------------------------------------------------------------------------------------------------------------"
            
    env, last_scheduled_task_time = MMMSim.runMainSimulation()
    env.run(until=last_scheduled_task_time+SimParams.SIM_RUNTIME)
    print env.now        
    
    FNAME_PREFIX = "OL_"+str(SimParams.NOC_H)+"_"+str(SimParams.NOC_W)+"_"
    
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
    MMMSim.SimMon.report_InputBuffer(dump_to_file=ibuff_fname)
    MMMSim.SimMon.report_NodeTQs(dump_to_file=nodetqs_fname)
    MMMSim.SimMon.report_OutputBufferContents(dump_to_file=obuff_fname)    
    MMMSim.SimMon.report_FlowsCompleted(dump_to_file=flowscompleted_fname)
    MMMSim.SimMon.report_NodeTaskExecTimeline(dump_to_file=nodetaskexectime_fname)
    


###################################################################################################
#        SCENARIO based runsim for different types of ACtests and mappers
###################################################################################################
def runSim_AC_MP_Type(                       
                       forced_seed = None,                       
                       fname_prefix=None,
                       ac_type=None,
                       mp_type=None,
                       pr_type=None,
                       num_wfs=None,
                       res_list=None,
                       cmbmppri_type=None
                       ):
    
    seed = forced_seed    
    
    print "SEED === " + str(seed)    
    random.seed(seed)
    np.random.seed(seed)
    np.random.shuffle(res_list) # shuffle in place
    print "here -1"
    print res_list
        
    # fixed params    
    SimParams.NOC_W = 3
    SimParams.NOC_H = 3
    SimParams.NUM_NODES = (SimParams.NOC_W * SimParams.NOC_H)
    SimParams.LOCAL_SCHEDULER_TYPE = LocalMPEG2FramePriorityScheduler_WithDepCheck()
    SimParams.SIM_ENTITY_RESOURCEMANAGER_CLASS    = RMTypes.OPENLOOP
    SimParams.SIM_ENTITY_CPUNODE_CLASS            = CPUTypes.OPENLOOP
    SimParams.SIM_ENTITY_MAPPER_CLASS             = MapperTypes.OPENLOOP
    SimParams.SIM_ENTITY_TASKDISPATCHER_CLASS     = TDTypes.OPENLOOP
    SimParams.NUM_WORKFLOWS                       = num_wfs
    SimParams.NUM_INPUTBUFFERS                    = SimParams.NUM_WORKFLOWS
    SimParams.DVB_RESOLUTIONS_FIXED               = res_list    
    SimParams.DVB_RESOLUTIONS_SELECTED_RANDOM     = False
    SimParams.WCRT_FLOW_CALC_MAX_RECURSION_DEPTH=3
    SimParams.WCRT_FLOW_USE_TIMEOUT = False
    SimParams.WCRT_FLOW_USE_LIMITED_RECURSION_DEPTH = True
        
    SimParams.AC_TEST_OPTION                = ac_type
    SimParams.DYNAMIC_TASK_MAPPING_SCHEME   = mp_type
    SimParams.DYNAMIC_TASK_PRIASS_SCHEME    = pr_type    
    SimParams.COMBINED_MAPPING_AND_PRIASS   = cmbmppri_type
    
    
    subdir = "seed_"+str(seed) + "/"
    subdir = subdir + "ac"+str(ac_type)+"mp"+str(mp_type)+"pr"+str(pr_type)+"cmb"+str(cmbmppri_type)+"/"
    FNAME_PREFIX = fname_prefix+str(SimParams.NOC_H)+"_"+str(SimParams.NOC_W)+"_"
    check_fname = _get_fname(EXP_DATADIR+subdir, FNAME_PREFIX)['utilvsschedresultsshort_fname']
    
    print "Checking file exists : " + str(check_fname)
    
    if(_check_file_exists(check_fname) == True):
        print "Simulation already exists.."
    else:
        print res_list
        random.seed(seed)
        np.random.seed(seed)
        print "----------------------------------------------------------------------------------------------------------------------------"
        print "Running runSim-"+ fname_prefix  +": num_wf=" + str(SimParams.NUM_WORKFLOWS) + \
                ", noc_h="+str(SimParams.NOC_H)+","+"noc_w="+str(SimParams.NOC_W) + \
                ", mapping="+str(SimParams.DYNAMIC_TASK_MAPPING_SCHEME) + \
                ", pri_ass="+str(SimParams.DYNAMIC_TASK_PRIASS_SCHEME) + \
                ", combined="+str(SimParams.COMBINED_MAPPING_AND_PRIASS) + \
                ", seed="+str(forced_seed)
        print "----------------------------------------------------------------------------------------------------------------------------"
        
        
        #subdir = ""
        
        env, last_scheduled_task_time = MMMSim.runMainSimulation(initial_rand_seed=seed)
        env.run(until=last_scheduled_task_time+SimParams.SIM_RUNTIME)
        print env.now        
        
        FNAME_PREFIX = fname_prefix+str(SimParams.NOC_H)+"_"+str(SimParams.NOC_W)+"_"
        
        _makeDir(EXP_DATADIR+subdir)
        
        # get filenames
        filenames = _get_fname(EXP_DATADIR+subdir, FNAME_PREFIX)        
        # name the report filenames
        _dump_captured_data(filenames)
        


def _get_fname(exp_dir, fname_prefix):
    tm_fname                = exp_dir + fname_prefix + global_tm_fname
    vs_bs_fname             = exp_dir + fname_prefix + global_vs_bs_fname
    util_fname              = exp_dir + fname_prefix + global_util_fname
    utilshort_fname         = exp_dir + fname_prefix + global_utilshort_fname
    wf_res_fname            = exp_dir + fname_prefix + global_wf_res_fname
    gops_opbuff_fname       = exp_dir + fname_prefix + global_gops_opbuff_fname
    gops_opbuff_short_fname = exp_dir + fname_prefix + global_gops_opbuff_short_fname  
    rmtbl_dt_fname          = exp_dir + fname_prefix + global_rmtbl_dt_fname
    ibuff_fname             = exp_dir + fname_prefix + global_ibuff_fname
    obuff_fname             = exp_dir + fname_prefix + global_obuff_fname
    obuffshort_fname        = exp_dir + fname_prefix + global_obuffshort_fname
    nodetqs_fname           = exp_dir + fname_prefix + global_nodetqs_fname
    rmtaskrelease_fname     = exp_dir + fname_prefix + global_rmtaskrelease_fname
    mappingandpriass_fname  = exp_dir + fname_prefix + global_mappingandpriass_fname
    flowscompleted_fname    = exp_dir + fname_prefix + global_flowscompleted_fname
    nodetaskexectime_fname  = exp_dir + fname_prefix + global_nodetaskexectime_fname
    schedtestresults_fname  = exp_dir + fname_prefix + global_schedtestresults_fname    
    schedtestresultsshort_fname  = exp_dir + fname_prefix + global_schedtestresultsshort_fname
    utilvsschedresults_fname  = exp_dir + fname_prefix + global_utilvsschedresults_fname
    utilvsschedresultsshort_fname = exp_dir + fname_prefix + global_utilvsschedresultsshort_fname
    
    
    result = {
            "tm_fname"                : tm_fname,
            "vs_bs_fname"             : vs_bs_fname,
            "util_fname"              : util_fname,            
            "utilshort_fname"         : utilshort_fname,                        
            "wf_res_fname"            : wf_res_fname,
            "gops_opbuff_fname"       : gops_opbuff_fname,
            "gops_opbuff_short_fname" : gops_opbuff_short_fname,
            "rmtbl_dt_fname"          : rmtbl_dt_fname,
            "ibuff_fname"             : ibuff_fname,
            "obuff_fname"             : obuff_fname,
            "obuffshort_fname"        : obuffshort_fname, 
            "nodetqs_fname"           : nodetqs_fname,
            "rmtaskrelease_fname"     : rmtaskrelease_fname,
            "mappingandpriass_fname"  : mappingandpriass_fname,
            "flowscompleted_fname"    : flowscompleted_fname,
            "nodetaskexectime_fname"  : nodetaskexectime_fname,
            "schedtestresults_fname"  : schedtestresults_fname,
            "schedtestresultsshort_fname" : schedtestresultsshort_fname,
            "utilvsschedresults_fname"  : utilvsschedresults_fname,
            "utilvsschedresultsshort_fname" : utilvsschedresultsshort_fname          
        }
    
    return result 
    


def _dump_captured_data(filenames):
    (wf_results_summary, gops_in_outputbuff_summary) = MMMSim.SimMon.report_DecodedWorkflows_Summary(timeline_fname=filenames["tm_fname"], 
                                                                                                        wf_res_summary_fname = None, 
                                                                                                        gops_opbuff_summary_fname = filenames["gops_opbuff_fname"],
                                                                                                        gops_opbuff_summary_short_fname = filenames["gops_opbuff_short_fname"],
                                                                                                        rmtbl_dt_summary_fname = filenames["rmtbl_dt_fname"],
                                                                                                        output_format = "json")
        
    MMMSim.SimMon.report_VideoStream_BasicStats(wf_results_summary, filenames["vs_bs_fname"])
    #MMMSim.SimMon.report_InstUtilisation(dump_to_file=filenames["util_fname"])
    MMMSim.SimMon.report_InstUtilisationShort(dump_to_file=filenames["utilshort_fname"])    
    #MMMSim.SimMon.report_InputBuffer(dump_to_file=filenames["ibuff_fname"])
    #MMMSim.SimMon.report_NodeTQs(dump_to_file=filenames["nodetqs_fname"])
    #MMMSim.SimMon.report_OutputBufferContents(dump_to_file=filenames["obuff_fname"])  
    #MMMSim.SimMon.report_OutputBufferContents_short(dump_to_file=filenames["obuffshort_fname"])  
    #MMMSim.SimMon.report_FlowsCompleted(dump_to_file=filenames["flowscompleted_fname"])
    #MMMSim.SimMon.report_NodeTaskExecTimeline(dump_to_file=filenames["nodetaskexectime_fname"])
    #MMMSim.SimMon.report_WCRT_TasksAndFlows_viaSchedAnalysis(dump_to_file=filenames["schedtestresults_fname"])
    MMMSim.SimMon.report_WCRT_TasksAndFlows_viaSchedAnalysis_short(dump_to_file=filenames["schedtestresultsshort_fname"])
    #MMMSim.SimMon.report_MappingAndPriAssInfo(dump_to_file=filenames["mappingandpriass_fname"])
    #MMMSim.SimMon.report_StreamUtil_vs_sched(dump_to_file=filenames["utilvsschedresults_fname"])
    MMMSim.SimMon.report_StreamUtil_vs_sched_short(dump_to_file=filenames["utilvsschedresultsshort_fname"])
    



def _makeDir(directory):
    try:
        os.stat(directory)
    except:
        os.makedirs(directory)

def _check_file_exists(fname):
    return os.path.exists(fname)

# format : "720x576,544x576,528x576,480x576,426x240,320x240,240x180"
def _reslist_convert(str_res_list):
    res_list = []
    if(str_res_list.count(',')>0):
        res_combos = str_res_list.split(',')
        if(len(res_combos)>1):
            for each_r in res_combos:
                res_h_w = each_r.split('x')
                int_res_h = int(res_h_w[0]) 
                int_res_w = int(res_h_w[1])
                res_list.append((int_res_h, int_res_w))
        else:
            sys.exit("_reslist_convert:: Error")
    else:
        res_h_w = str_res_list.split('x')
        int_res_h = int(res_h_w[0]) 
        int_res_w = int(res_h_w[1])
        res_list.append((int_res_h, int_res_w))
        
        
    return res_list

############################################################################
############################################################################
##                MAIN SCRIPT SECTION
############################################################################
############################################################################

sys.setrecursionlimit(1500)

# collect command line params
parser = argparse.ArgumentParser(__file__, description="Run specified experiment on abstract simulator")

parser = argparse.ArgumentParser(__file__, description="Run specified experiment on abstract simulator")
parser.add_argument("--fname_prefix", help="filename prefix", default=None)
parser.add_argument("--num_wfs", help="number of max workflows", type=int, default=-1)
parser.add_argument("--ac_type", help="admission control type", type=int, default=-1)
parser.add_argument("--mp_type", help="mapping type", type=int, default=-1)
parser.add_argument("--pr_type", help="pri assignment type", type=int, default=-1)
parser.add_argument("--cmbmppri_type", help="combined mapping and pri-assignment type", type=int, default=-1)
parser.add_argument("--forced_seed", help="forced seed", type=int, default=-1)
parser.add_argument("--cc_uid", help="cc unique id", default=None)
parser.add_argument("--res_list", help="resolution list", default=None)



args = parser.parse_args()

####################################
## check which experiment to run ##
####################################
    
#pprint.pprint(args.res_list)
print args.num_wfs

# construct res list
converted_res_list = _reslist_convert(args.res_list) 
print converted_res_list

if(args.fname_prefix==None):
    final_fname_prefix = "HRTVid_" + \
                     "AC"+ str(args.ac_type) + "_" + \
                     "MP"+ str(args.mp_type) + "_" + \
                     "PR"+ str(args.pr_type) + "_" + \
                     "CMB"+ str(args.cmbmppri_type) + "_" +\
                     "cc"+ str(args.cc_uid) + "_"
else:
    final_fname_prefix = args.fname_prefix                     
                     

if(args.forced_seed == -1):
    forced_seed = 1234
else:
    forced_seed = args.forced_seed

runSim_AC_MP_Type(
                   forced_seed = forced_seed,
                   fname_prefix=final_fname_prefix,
                   ac_type=args.ac_type,
                   mp_type=args.mp_type,
                   pr_type=args.pr_type,
                   cmbmppri_type=args.cmbmppri_type,
                   num_wfs = args.num_wfs,
                   res_list = converted_res_list                       
                  )
    
