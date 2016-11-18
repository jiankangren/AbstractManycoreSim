import sys, os, csv, pprint, math
import argparse

import numpy as np
import random
import shutil
import time
import json
import datetime, time


## uncomment when running under CLI only version ##
import matplotlib
matplotlib.use('Agg')

from libProcessingElement.LocalScheduler import LocalRRScheduler,    \
                        LocalEDFScheduler, \
                        LocalMPEG2FrameEDFScheduler, \
                        LocalMPEG2FrameListScheduler, \
                        LocalMPEG2FramePriorityScheduler, \
                        LocalMPEG2FramePriorityScheduler_WithDepCheck, \
                        LocalHEVCFramePriorityScheduler_WithDepCheck, \
                        LocalHEVCTilePriorityScheduler_WithDepCheck 

from libResourceManager.RMTypes import RMTypes
from libProcessingElement.CPUTypes import CPUTypes
from libResourceManager.Mapper.MapperTypes import MapperTypes
from libTaskDispatcher.TDTypes import TDTypes

from libResourceManager.AdmissionControllerOptions import AdmissionControllerOptions
from libMappingAndScheduling.SemiDynamic.TaskMappingSchemes import TaskMappingSchemes
from libMappingAndScheduling.SemiDynamic.TaskSemiDynamicPrioritySchemes import TaskSemiDynamicPrioritySchemes
from libMappingAndScheduling.SemiDynamic.TaskMappingAndPriAssCombinedSchemes import TaskMappingAndPriAssCombinedSchemes
from libMappingAndScheduling.SemiDynamic.TaskTileMappingAndPriAssCombinedSchemes import TaskTileMappingAndPriAssCombinedSchemes
from libMappingAndScheduling.FullyDynamic.TaskMappingSchemesFullyDyn import TaskMappingSchemesFullyDyn
from libApplicationModel.Task import TaskModel
from util_scripts.gen_res_list import get_res_list

from SimParams import SimParams
import Multicore_MPEG_Model as MMMSim

import libApplicationModel.HEVCWorkloadParams as HEVCWLP


EXP_DATADIR = "experiment_data/hevc_mapping_highccr_test/"

NOC_SIZE = [(3,3), (5,5), (7,7), (9,9), (10,10)]

# name the report filenames
global_tm_fname                = "_timeline.png"
global_vs_bs_fname             = "_vsbs.js"
global_util_fname              = "_util.js"
global_wf_res_fname            = "_wfressumm.js"
global_gops_opbuff_fname       = "_gopsopbuffsumm.js"    
global_rmtbl_dt_fname          = "_rmtbldt.js"
global_ibuff_fname             = "_ibuff.js"
global_obuff_fname             = "_obuff.js"
global_nodetqs_fname           = "_nodetqs.js"
global_rmtaskrelease_fname     = "_rmtaskrel.js"
global_mappingandpriass_fname  = "_mappingandpriass.js"
global_flowscompleted_fname    = "_flwcompleted.js"
global_flowscompletedshort_fname = "_flwcompletedshort.js"
global_nodetaskexectime_fname  = "_nodetaskexectime.js"
global_schedtestresults_fname  = "_schedtestresults.js"
global_utilvsschedresults_fname  = "_utilvsschedresults.js"
global_rmtaskmappingtable_fname = "_rmtaskmappingtable.js"
global_rmvolatiletaskmappingtable_fname = "_rmvolatiletaskmappingtable.js"
global_processedctus_fname = "_processedctus.js"
global_taskscompleted_fname = "_taskscompleted.js"
global_mapperexecoverhead_fname = "_mapperexecoverhead.js"
global_smartmmcid_fname = "_smartmmcid.js"
global_jobccrinfo_fname = "_jobccrinfo.js"
global_linkusagereport_fname = "_linkusagereport.js"
global_ppmaperoptstageinfo_fname = "_ppmaperoptstageinfo.js"



# do we use ms signalling or not
def _get_feedback_status(cmbmppri_type):
    if cmbmppri_type in [TaskTileMappingAndPriAssCombinedSchemes.TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_LOWUTIL_WITHMONITORING_AVGCC_V1,
                         TaskTileMappingAndPriAssCombinedSchemes.TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_MOSTSLACK_WITHMONITORING_AVGCC_V1,
                         TaskTileMappingAndPriAssCombinedSchemes.TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_CLUSTLS_MOSTSLACK_WITHMONITORING_AVGCC]:
        
        return True
    else:
        return False


###################################################################################################
#        SCENARIO based runsim for different types of AC/mappers/CCR/noc size
###################################################################################################
def runSim_TileMapping(    
                           forced_seed = None,
                           cmbmppri_type=None,
                           wl_config=None, # we assume 1 vid per wf
                       ):
    
    seed = forced_seed  
    print "SEED === " + str(seed)    
    
    random.seed(seed)
    np.random.seed(seed)
    
    # get resolution list
    res_list = get_res_list(wl_config)
    
    # fixed params
    SimParams.SIM_RUNTIME = 10000
    SimParams.HEVC_DUMP_FRAME_DATAFILE = False
    SimParams.HEVC_LOAD_FRAME_DATAFILE = False
    SimParams.HEVC_FRAME_GENRAND_SEED = seed
    SimParams.HEVC_TILELEVEL_SPLITTING_ENABLE = True
    SimParams.LOCAL_SCHEDULER_TYPE = LocalHEVCTilePriorityScheduler_WithDepCheck()    
    SimParams.SIM_ENTITY_RESOURCEMANAGER_CLASS    = RMTypes.OPENLOOP
    SimParams.SIM_ENTITY_CPUNODE_CLASS            = CPUTypes.OPENLOOP_HEVC_TILE_LEVEL
    SimParams.TASK_MODEL                          = TaskModel.TASK_MODEL_HEVC_TILE_LEVEL
    SimParams.SIM_ENTITY_MAPPER_CLASS             = MapperTypes.OPENLOOP_WITH_HEVCTILE
    SimParams.SIM_ENTITY_TASKDISPATCHER_CLASS     = TDTypes.OPENLOOP_WITH_HEVCTILE    
    
    SimParams.MS_SIGNALLING_NOTIFY_FLOW_COMPLETE_ENABLE = False
    SimParams.MS_SIGNALLING_NOTIFY_TASK_COMPLETE_ENABLE = False
    SimParams.RESOURCEMANAGER_USE_VOLATILE_TMTBL = True    
    SimParams.MAPPING_PREMAPPING_ENABLED = True
    SimParams.MMC_SMART_NODE_SELECTION_ENABLE = True
    SimParams.MMC_SMART_NODE_SELECTION_TYPE = 0 # MMCP-Dist
    SimParams.MMC_ENABLE_DATATRANSMISSION_MODELLING = True
    SimParams.HEVC_GOPGEN_USEPROBABILISTIC_MODEL = True
    SimParams.USE_VIDSTRM_SPECIFIC_FRAMERATE = True
    
    SimParams.NOC_W                                 = 8
    SimParams.NOC_H                                 = 8       
    SimParams.NUM_NODES                             = (SimParams.NOC_W * SimParams.NOC_H)
       
#     SimParams.DVB_RESOLUTIONS_FIXED               = [
# #                                                      (3840,2160),
#                                                     (2560,1440), 
# #                                                      (1920,1080),
# #                                                      (1280,720),
# #                                                      (854,480),
# #                                                      (640,360),
#                                                     (512,288),
#                                                     ]*1
# # #     
    
    SimParams.DVB_RESOLUTIONS_FIXED               = res_list
    SimParams.NUM_WORKFLOWS                       = len(SimParams.DVB_RESOLUTIONS_FIXED)
    SimParams.NUM_INPUTBUFFERS                    = SimParams.NUM_WORKFLOWS
    SimParams.DVB_RESOLUTIONS_SELECTED_RANDOM     = False    
    
    SimParams.WFGEN_MIN_GOPS_PER_VID = 5 
    SimParams.WFGEN_MAX_GOPS_PER_VID = 5
    SimParams.WFGEN_INITIAL_VID_GAP_MIN = 0.0
    SimParams.WFGEN_INITIAL_VID_GAP_MAX = 0.05    
        
    CCR_TYPE = "lowcc_normal_mem_considered"      # {normal, normal_mem_considered, lowcc_normal_mem_considered}
    
    
    ### for normal CC ###    
    if CCR_TYPE == "normal":
        cc_scale_down = 1.66 # this makes the CCR go High
        SimParams.CLSTR_TILE_PARAM_CCR_RANGES_LOW = 0.11 # less than this
        SimParams.CLSTR_TILE_PARAM_CCR_RANGES_MED = (0.11, 0.14) # between these values
        SimParams.CLSTR_TILE_PARAM_CCR_RANGES_HIGH = 0.14 # higher than this
        SimParams.CLSTR_TILE_PARAM_KAUSHIKS_ALGO_COMMS_SCALEUP_FACTOR = 1.0 # we use a scale factor because always the (comm. cost < comp. cost)
        
        SimParams.CLSTR_TILE_PARAM_BGROUP_CCR_RANGES_LOW = 0.11 # less than this
        SimParams.CLSTR_TILE_PARAM_BGROUP_CCR_RANGES_MED = (0.11, 0.14) # between these values
        SimParams.CLSTR_TILE_PARAM_BGROUP_CCR_RANGES_HIGH = 0.14 # higher than this
        SimParams.CLSTR_TILE_PARAM_BGROUP_NGT_HOPS = (4,1,1) # NGT hop count (low, med, high ccr ranges)
        
    
    ### for normal low CC - @0.60 ###
    elif CCR_TYPE == "normal_mem_considered":        
        cc_scale_down = 1.0 # this makes the CCR go High
        SimParams.CLSTR_TILE_PARAM_CCR_RANGES_LOW = 0.18 # less than this
        SimParams.CLSTR_TILE_PARAM_CCR_RANGES_MED = (0.18, 0.23) # between these values
        SimParams.CLSTR_TILE_PARAM_CCR_RANGES_HIGH = 0.23 # higher than this
        SimParams.CLSTR_TILE_PARAM_KAUSHIKS_ALGO_COMMS_SCALEUP_FACTOR = 1.0 # we use a scale factor because always the (comm. cost < comp. cost)
        
        SimParams.CLSTR_TILE_PARAM_BGROUP_CCR_RANGES_LOW = 0.18 # less than this
        SimParams.CLSTR_TILE_PARAM_BGROUP_CCR_RANGES_MED = (0.18, 0.23) # between these values
        SimParams.CLSTR_TILE_PARAM_BGROUP_CCR_RANGES_HIGH = 0.23 # higher than this
        SimParams.CLSTR_TILE_PARAM_BGROUP_NGT_HOPS = (4,1,1) # NGT hop count (low, med, high ccr ranges)
        
    
    ### for special very low CC - @0.60*0.1 ###
    elif CCR_TYPE == "lowcc_normal_mem_considered":
        cc_scale_down = 0.1 # low values makes the CCR go high
        SimParams.CLSTR_TILE_PARAM_CCR_RANGES_LOW = 1.8 # less than this
        SimParams.CLSTR_TILE_PARAM_CCR_RANGES_MED = (1.8, 2.3) # between these values
        SimParams.CLSTR_TILE_PARAM_CCR_RANGES_HIGH = 2.3 # higher than this
        SimParams.CLSTR_TILE_PARAM_KAUSHIKS_ALGO_COMMS_SCALEUP_FACTOR = 1.0 # we use a scale factor because always the (comm. cost < comp. cost)
        
        SimParams.CLSTR_TILE_PARAM_BGROUP_CCR_RANGES_LOW = 1.8 # less than this
        SimParams.CLSTR_TILE_PARAM_BGROUP_CCR_RANGES_MED = (1.8, 2.3) # between these values
        SimParams.CLSTR_TILE_PARAM_BGROUP_CCR_RANGES_HIGH = 2.3 # higher than this
        SimParams.CLSTR_TILE_PARAM_BGROUP_NGT_HOPS = (4,1,1) # NGT hop count (low, med, high ccr ranges)
    
    else: 
        sys.exit("Error - CCR_TYPE: "+ CCR_TYPE)
    
    
    HEVCWLP.HEVCWLPARAMS_SCALE_FACTOR['ICU'] = (HEVCWLP.HEVCWLPARAMS_SCALE_FACTOR['ICU'][0]*float(cc_scale_down), HEVCWLP.HEVCWLPARAMS_SCALE_FACTOR['ICU'][1]*float(cc_scale_down))
    HEVCWLP.HEVCWLPARAMS_SCALE_FACTOR['PCU'] = (HEVCWLP.HEVCWLPARAMS_SCALE_FACTOR['PCU'][0]*float(cc_scale_down), HEVCWLP.HEVCWLPARAMS_SCALE_FACTOR['PCU'][1]*float(cc_scale_down))
    HEVCWLP.HEVCWLPARAMS_SCALE_FACTOR['BCU'] = (HEVCWLP.HEVCWLPARAMS_SCALE_FACTOR['BCU'][0]*float(cc_scale_down), HEVCWLP.HEVCWLPARAMS_SCALE_FACTOR['BCU'][1]*float(cc_scale_down))
    HEVCWLP.HEVCWLPARAMS_SCALE_FACTOR['SkipCU'] = (HEVCWLP.HEVCWLPARAMS_SCALE_FACTOR['SkipCU'][0]*float(cc_scale_down), HEVCWLP.HEVCWLPARAMS_SCALE_FACTOR['SkipCU'][1]*float(cc_scale_down))
    
    print "HEVCWLP.HEVCWLPARAMS_SCALE_FACTOR:: ---"
    pprint.pprint(HEVCWLP.HEVCWLPARAMS_SCALE_FACTOR)
    print "-------------"
       
    # -- variable params --
    SimParams.COMBINED_MAPPING_AND_PRIASS = cmbmppri_type
    SimParams.DYNAMIC_TASK_MAPPING_SCHEME = TaskMappingSchemes.TASKMAPPINGSCHEMES_NONE    # this will be overridden
    SimParams.DYNAMIC_TASK_PRIASS_SCHEME =  TaskSemiDynamicPrioritySchemes.TASKSEMIDYNAMICPRIORITYSCHEMES_NONE    
        
    pprint.pprint(SimParams.DVB_RESOLUTIONS_FIXED)
    pprint.pprint(SimParams.NUM_WORKFLOWS)
    
    # getting the reporing file name prefix    
    exp_key = "ac"+str(SimParams.AC_TEST_OPTION) + \
                            "mp"+str(SimParams.DYNAMIC_TASK_MAPPING_SCHEME)+ \
                            "pr"+str(SimParams.DYNAMIC_TASK_PRIASS_SCHEME)+ \
                            "cmb"+str(SimParams.COMBINED_MAPPING_AND_PRIASS) + \
                            "mmp"+str(SimParams.MMC_SMART_NODE_SELECTION_TYPE)
                            
    subdir1 = EXP_DATADIR + wl_config + "/" + exp_key + "/"    
    subdir2 = subdir1 + "seed_"+str(seed)+"/"
    final_subdir = subdir2
    fname_prefix = "HEVCTileSplitTest__"  + exp_key + "_"    
    final_fname = fname_prefix+str(SimParams.NOC_H)+"_"+str(SimParams.NOC_W)+"_"
    
    check_fname = _get_fname(final_subdir, final_fname)['taskscompleted_fname']
    
    print "Checking file exists : " + str(check_fname)
    if(_check_file_exists(check_fname) == True):        
        print "Simulation already exists.."
    else:
        
        print "----------------------------------------------------------------------------------------------------------------------------"
        print subdir2
        print "Running HEVCTile_Mapping-runSim_TileMapping-"+ fname_prefix  +": num_wf=" + str(SimParams.NUM_WORKFLOWS) + \
                ", noc_h="+str(SimParams.NOC_H)+","+"noc_w="+str(SimParams.NOC_W) + ", " + \
                exp_key + \
                ", seed="+str(seed)         
        print "----------------------------------------------------------------------------------------------------------------------------"
        
        print "Start-time(actual): ", datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        
        env, last_scheduled_task_time = MMMSim.runMainSimulation(initial_rand_seed=seed, dump_workload=False)
        env.run(until=last_scheduled_task_time+SimParams.SIM_RUNTIME)
        print "Simulation Ended at : %.15f" % env.now        
        print "End-time: ", datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        
        _makeDir(final_subdir)
        
        # get filenames
        filenames = _get_fname(final_subdir, final_fname)        
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
    flowscompletedshort_fname = exp_dir + fname_prefix + global_flowscompletedshort_fname
    nodetaskexectime_fname  = exp_dir + fname_prefix + global_nodetaskexectime_fname
    schedtestresults_fname  = exp_dir + fname_prefix + global_schedtestresults_fname    
    utilvsschedresults_fname  = exp_dir + fname_prefix + global_utilvsschedresults_fname
    rmtaskmappingtable_fname = exp_dir + fname_prefix + global_rmtaskmappingtable_fname
    rmvolatiletaskmappingtable_fname = exp_dir + fname_prefix + global_rmvolatiletaskmappingtable_fname
    processedctus_fname = exp_dir + fname_prefix + global_processedctus_fname
    taskscompleted_fname = exp_dir + fname_prefix + global_taskscompleted_fname
    mapperexecoverhead_fname = exp_dir + fname_prefix + global_mapperexecoverhead_fname
    smartmmcid_fname = exp_dir + fname_prefix + global_smartmmcid_fname
    jobccrinfo_fname = exp_dir + fname_prefix + global_jobccrinfo_fname
    linkusagereport_fname = exp_dir + fname_prefix + global_linkusagereport_fname
    ppmaperoptstageinfo_fname = exp_dir + fname_prefix + global_ppmaperoptstageinfo_fname
    
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
            "flowscompletedshort_fname"    : flowscompletedshort_fname,
            "nodetaskexectime_fname"  : nodetaskexectime_fname,
            "schedtestresults_fname"  : schedtestresults_fname,
            "utilvsschedresults_fname"  : utilvsschedresults_fname, 
            "rmtaskmappingtable_fname" : rmtaskmappingtable_fname,
            "rmvolatiletaskmappingtable_fname" : rmvolatiletaskmappingtable_fname,          
            "processedctus_fname" : processedctus_fname,
            "taskscompleted_fname" : taskscompleted_fname,
            "mapperexecoverhead_fname" : mapperexecoverhead_fname,
            "smartmmcid_fname" : smartmmcid_fname,
            "jobccrinfo_fname" : jobccrinfo_fname,
            "linkusagereport_fname" : linkusagereport_fname,
            "ppmaperoptstageinfo_fname" : ppmaperoptstageinfo_fname,
        }
    
    return result 
    


def _dump_captured_data(filenames):
    (wf_results_summary, gops_in_outputbuff_summary) = MMMSim.SimMon.report_DecodedWorkflows_Summary(timeline_fname=filenames["tm_fname"], 
                                                                                                         wf_res_summary_fname = filenames["wf_res_fname"], 
                                                                                                        gops_opbuff_summary_fname = filenames["gops_opbuff_fname"],
                                                                                                        rmtbl_dt_summary_fname = filenames["rmtbl_dt_fname"],
                                                                                                        output_format = "json", 
                                                                                                        task_model_type = TaskModel.TASK_MODEL_HEVC_TILE_LEVEL)
         
    
    MMMSim.SimMon.report_InstUtilisation(dump_to_file=filenames["util_fname"])
    MMMSim.SimMon.report_OutputBufferContents(dump_to_file=filenames["obuff_fname"])    
    #MMMSim.SimMon.report_FlowsCompleted(dump_to_file=filenames["flowscompleted_fname"])
    MMMSim.SimMon.report_FlowsCompleted_short(dump_to_file=filenames["flowscompletedshort_fname"])
    MMMSim.SimMon.report_HEVC_NumCTU()
    MMMSim.SimMon.report_RMTaskMappingTable(dump_to_file=filenames["rmtaskmappingtable_fname"])
    MMMSim.SimMon.report_VerifyFlows_HEVCTileLvl()
    #MMMSim.SimMon.report_RMVolatileTaskMappingTable(dump_to_file=filenames["rmvolatiletaskmappingtable_fname"])
    MMMSim.SimMon.report_NodeTasksCompleted(dump_to_file=filenames["taskscompleted_fname"])
    MMMSim.SimMon.report_MappingExecOverhead(dump_to_file=filenames["mapperexecoverhead_fname"])
    MMMSim.SimMon.report_JobCCRInfo(dump_to_file=filenames["jobccrinfo_fname"])
    #MMMSim.SimMon.report_LinkUsageInfo(dump_to_file=filenames["linkusagereport_fname"])
    
    MMMSim.SimMon.report_PPTileMapperOptStage_Info(dump_to_file=filenames["ppmaperoptstageinfo_fname"])

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
parser.add_argument("--wl_config", help="workload config", default=None)
parser.add_argument("--cmbmppri_type", help="combined mapping and pri-assignment type", type=int, default=-1)
parser.add_argument("--forced_seed", help="forced seed", type=int, default=-1)


args = parser.parse_args()
pprint.pprint(args)


####################################
## check which experiment to run ##
####################################

# if (args.forced_seed==-1):
#     seed=1234
# else:
#     seed = args.forced_seed

if (args.wl_config == None) or (args.forced_seed == -1) or (args.cmbmppri_type == -1):
    sys.exit("Arguments invalid")


# construct filename
runSim_TileMapping(
               forced_seed = args.forced_seed,
               cmbmppri_type = args.cmbmppri_type,
               wl_config = args.wl_config                                                         
              )
    
