import sys, os, csv, pprint, math
import argparse

import numpy as np
import random
import shutil
import time
import json

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

#from util_scripts.resolution_combos import generate_resolution_combos
#from util_scripts.ccr_ranges import get_properties_fixed_ccs_fixed_ccr_range

from SimParams import SimParams

import Multicore_MPEG_Model as MMMSim


EXP_DATADIR = "experiment_data/hrt_video/noc_scale_noschedtest/"

NOC_SIZE = [(3,3), (5,5), (7,7), (9,9), (10,10)]

# name the report filenames
global_tm_fname                = "test__timeline.png"
global_vs_bs_fname             = "test__vsbs.js"
global_util_fname              = "test__util.js"
global_wf_res_fname            = "test__wfressumm.js"
global_gops_opbuff_fname       = "test__gopsopbuffsumm.js"    
global_rmtbl_dt_fname          = "test__rmtbldt.js"
global_ibuff_fname             = "test__ibuff.js"
global_obuff_fname             = "test__obuff.js"
global_nodetqs_fname           = "test__nodetqs.js"
global_rmtaskrelease_fname     = "test__rmtaskrel.js"
global_mappingandpriass_fname  = "test__mappingandpriass.js"
global_flowscompleted_fname    = "test__flwcompleted.js"
global_nodetaskexectime_fname  = "test__nodetaskexectime.js"
global_schedtestresults_fname  = "test__schedtestresults.js"
global_utilvsschedresults_fname  = "test__utilvsschedresults.js"


###################################################################################################
#        SCENARIO based runsim for different types of AC/mappers/CCR/noc size
###################################################################################################
def runSim_varNoCScale_varCCR(                       
                       forced_seed = None,                       
                       fname_prefix=None,
                       ac_type=None,
                       mp_type=None,
                       pr_type=None,                       
                       cmbmppri_type=None,
                       use_ccr_file_input = True
                       ):
    
    seed = forced_seed  
    print "SEED === " + str(seed)    
    
    random.seed(seed)
    np.random.seed(seed)
    
    # shuffle the res list
    fixed_res_list = [(230,180), (528,576), (240,180), (240,180), (576, 720), (320,240), (320,240)]
    np.random.shuffle(fixed_res_list)
             
    # fixed params
    SimParams.LOCAL_SCHEDULER_TYPE = LocalMPEG2FramePriorityScheduler_WithDepCheck()    
    SimParams.SIM_ENTITY_RESOURCEMANAGER_CLASS    = RMTypes.OPENLOOP
    SimParams.SIM_ENTITY_CPUNODE_CLASS            = CPUTypes.OPENLOOP
    SimParams.SIM_ENTITY_MAPPER_CLASS             = MapperTypes.OPENLOOP
    SimParams.SIM_ENTITY_TASKDISPATCHER_CLASS     = TDTypes.OPENLOOP    
    SimParams.AC_TEST_OPTION                = ac_type
    SimParams.DYNAMIC_TASK_MAPPING_SCHEME   = mp_type
    SimParams.DYNAMIC_TASK_PRIASS_SCHEME    = pr_type    
    SimParams.COMBINED_MAPPING_AND_PRIASS   = cmbmppri_type
    
    # now we perform a range of tests for varying CCR
    if(use_ccr_file_input == True): # get the ccr values from file ?
        fname = 'util_scripts/ccr_list_allwfs_output_0.001_2.0_s'+ str(forced_seed) + '.js'    
        json_data=open(fname)
        file_data = json.load(json_data) 
        seed_specific_data = file_data[str(forced_seed)]
        
        #sorted_ccr_entries = sorted(ccr_data, key=lambda k: k['ccr'])
    else:
        sys.exit("Error- not implemented yet!")

    
    offset = 0
    for each_wf_k, each_wf_v in seed_specific_data.iteritems():
        noc_h = int(np.sqrt(int(each_wf_k)-offset))
        if noc_h != 9:
       	    continue
        wf_nums = int(each_wf_k)
        
        SimParams.NOC_W                                 = noc_h
        SimParams.NOC_H                                 = noc_h        
        SimParams.NUM_NODES                             = (SimParams.NOC_W * SimParams.NOC_H)
        SimParams.NUM_WORKFLOWS                         = wf_nums
        SimParams.NUM_INPUTBUFFERS                      = SimParams.NUM_WORKFLOWS
        SimParams.DVB_RESOLUTIONS_FIXED                 = each_wf_v["res_list"]
        SimParams.DVB_RESOLUTIONS_SELECTED_RANDOM       = False
        
        if(len(SimParams.DVB_RESOLUTIONS_FIXED) != SimParams.NUM_WORKFLOWS):
            pprint.pprint(SimParams.DVB_RESOLUTIONS_FIXED)
            pprint.pprint(SimParams.NUM_WORKFLOWS)
            sys.exit("Error ! wfs did not match res_list")
        
        sorted_ccr_entries = each_wf_v["ccr_list"].values()
        
        # perform one simulation run per ccrn entry
        for each_ccr_entry in sorted_ccr_entries:
            
            SimParams.NOC_PERIOD = float(each_ccr_entry['noc_period'])
            SimParams.CPU_EXEC_SPEED_RATIO = float(each_ccr_entry['cpu_exec_speed_ratio'])
            
            subdir = "seed_"+str(seed)+"/" + "noc_h" + str(noc_h) + "/" 
            subdir = subdir + "ccr_" + str(round(each_ccr_entry['ccr'], 4)) + "/"
            if round(each_ccr_entry['ccr'], 4) < 1.4:
                continue
            FNAME_PREFIX = fname_prefix+str(SimParams.NOC_H)+"_"+str(SimParams.NOC_W)+"_"
            check_fname = _get_fname(EXP_DATADIR+subdir, FNAME_PREFIX)['utilvsschedresults_fname']
            
            print "Checking file exists : " + str(check_fname)
            
            if(_check_file_exists(check_fname) == True):
                print "Simulation already exists.."
            else:
                
                random.seed(seed)
                np.random.seed(seed)
                print "----------------------------------------------------------------------------------------------------------------------------"
                print subdir
                print "Running runSim-"+ fname_prefix  +": num_wf=" + str(SimParams.NUM_WORKFLOWS) + \
                        ", noc_h="+str(SimParams.NOC_H)+","+"noc_w="+str(SimParams.NOC_W) + \
                        ", mapping="+str(SimParams.DYNAMIC_TASK_MAPPING_SCHEME) + \
                        ", pri_ass="+str(SimParams.DYNAMIC_TASK_PRIASS_SCHEME) + \
                        ", combined="+str(SimParams.COMBINED_MAPPING_AND_PRIASS) + \
                        ", seed="+str(forced_seed)
                print "----------------------------------------------------------------------------------------------------------------------------"
                
                
                #subdir = ""
                
                env, last_scheduled_task_time = MMMSim.runMainSimulation()
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
    wf_res_fname            = exp_dir + fname_prefix + global_wf_res_fname
    gops_opbuff_fname       = exp_dir + fname_prefix + global_gops_opbuff_fname    
    rmtbl_dt_fname          = exp_dir + fname_prefix + global_rmtbl_dt_fname
    ibuff_fname             = exp_dir + fname_prefix + global_ibuff_fname
    obuff_fname             = exp_dir + fname_prefix + global_obuff_fname
    nodetqs_fname           = exp_dir + fname_prefix + global_nodetqs_fname
    rmtaskrelease_fname     = exp_dir + fname_prefix + global_rmtaskrelease_fname
    mappingandpriass_fname  = exp_dir + fname_prefix + global_mappingandpriass_fname
    flowscompleted_fname    = exp_dir + fname_prefix + global_flowscompleted_fname
    nodetaskexectime_fname  = exp_dir + fname_prefix + global_nodetaskexectime_fname
    schedtestresults_fname  = exp_dir + fname_prefix + global_schedtestresults_fname    
    utilvsschedresults_fname  = exp_dir + fname_prefix + global_utilvsschedresults_fname
    
    result = {
            "tm_fname"                : tm_fname,
            "vs_bs_fname"             : vs_bs_fname,
            "util_fname"              : util_fname,
            "wf_res_fname"            : wf_res_fname,
            "gops_opbuff_fname"       : gops_opbuff_fname,    
            "rmtbl_dt_fname"          : rmtbl_dt_fname,
            "ibuff_fname"             : ibuff_fname,
            "obuff_fname"             : obuff_fname,
            "nodetqs_fname"           : nodetqs_fname,
            "rmtaskrelease_fname"     : rmtaskrelease_fname,
            "mappingandpriass_fname"  : mappingandpriass_fname,
            "flowscompleted_fname"    : flowscompleted_fname,
            "nodetaskexectime_fname"  : nodetaskexectime_fname,
            "schedtestresults_fname"  : schedtestresults_fname,
            "utilvsschedresults_fname"  : utilvsschedresults_fname,          
        }
    
    return result 
    


def _dump_captured_data(filenames):
    (wf_results_summary, gops_in_outputbuff_summary) = MMMSim.SimMon.report_DecodedWorkflows_Summary(timeline_fname=filenames["tm_fname"], 
                                                                                                         wf_res_summary_fname = filenames["wf_res_fname"], 
                                                                                                        gops_opbuff_summary_fname = filenames["gops_opbuff_fname"],
                                                                                                        rmtbl_dt_summary_fname = filenames["rmtbl_dt_fname"],
                                                                                                        output_format = "json")
        
    MMMSim.SimMon.report_VideoStream_BasicStats(wf_results_summary, filenames["vs_bs_fname"])
    MMMSim.SimMon.report_InstUtilisation(dump_to_file=filenames["util_fname"])
    #MMMSim.SimMon.report_InputBuffer(dump_to_file=filenames["ibuff_fname"])
    #MMMSim.SimMon.report_NodeTQs(dump_to_file=filenames["nodetqs_fname"])
    MMMSim.SimMon.report_OutputBufferContents(dump_to_file=filenames["obuff_fname"])    
    #MMMSim.SimMon.report_FlowsCompleted(dump_to_file=filenames["flowscompleted_fname"])
    #MMMSim.SimMon.report_NodeTaskExecTimeline(dump_to_file=filenames["nodetaskexectime_fname"])
    MMMSim.SimMon.report_WCRT_TasksAndFlows_viaSchedAnalysis(dump_to_file=filenames["schedtestresults_fname"])
    MMMSim.SimMon.report_MappingAndPriAssInfo(dump_to_file=filenames["mappingandpriass_fname"])
    MMMSim.SimMon.report_StreamUtil_vs_sched(dump_to_file=filenames["utilvsschedresults_fname"])
    



def _makeDir(directory):
    try:
        os.stat(directory)
    except:
        try:
            os.makedirs(directory)
        except OSError, e:
            print str(e)
            pass
        

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
parser.add_argument("--ac_type", help="admission control type", type=int, default=-1)
parser.add_argument("--mp_type", help="mapping type", type=int, default=-1)
parser.add_argument("--pr_type", help="pri assignment type", type=int, default=-1)
parser.add_argument("--cmbmppri_type", help="combined mapping and pri-assignment type", type=int, default=-1)
parser.add_argument("--forced_seed", help="forced seed", type=int, default=-1)

args = parser.parse_args()

####################################
## check which experiment to run ##
####################################

# construct filename
if(args.fname_prefix==None):
    final_fname_prefix = "HRTVid_" + \
                     "AC"+ str(args.ac_type) + "_" + \
                     "MP"+ str(args.mp_type) + "_" + \
                     "PR"+ str(args.pr_type) + "_" + \
                     "CMB"+ str(args.cmbmppri_type) + "_"
else:
    final_fname_prefix = args.fname_prefix                     
                     

runSim_varNoCScale_varCCR(
                   forced_seed = args.forced_seed,
                   fname_prefix=final_fname_prefix,
                   ac_type=args.ac_type,
                   mp_type=args.mp_type,
                   pr_type=args.pr_type,
                   cmbmppri_type=args.cmbmppri_type,
                   use_ccr_file_input = True                                          
                  )
    
