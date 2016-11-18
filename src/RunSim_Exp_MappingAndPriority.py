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
    
    
    
        
# multiple runs with varying number of workflows
# basic video stats output at the end - to check efficiency of admission controller
def runExp_MappingAndPriSchemes(num_wfs = None,
                                
                                # randomise seed
                                forced_seed = None,
                                
                                # mapping and priority assignment scheme
                                run_full_fact_schemes = None,
                                mapping_scheme = None,
                                pri_ass_scheme = None                                
                               
                                ):        
    
    
    # param checking
    if ((num_wfs == None) or
        (run_full_fact_schemes == None) or
        (mapping_scheme == None) or
        (pri_ass_scheme == None)):
        sys.exit("runExp_MappingAndPriSchemes :: Error - invalid params")
        
    # init seed
    if(forced_seed != None):
        seed = forced_seed
    else:
        seed = 1087744070
    
    print "SEED === " + str(seed)    
             
    # fixed params
    SimParams.SLACK_FEEDBACK_ENABLED = False
    SimParams.AC_TEST_OPTION = AdmissionControllerOptions.AC_OPTION_NONE
    SimParams.NUM_WORKFLOWS = num_wfs
    SimParams.NUM_INPUTBUFFERS = num_wfs 
    
    # output directory
    ROOT_DATA_OUTPUT_DIR =   'experiment_data/mapping_and_pri_schemes/' + "seed_"+str(seed) + "/"    
    
    
    ## do i run allt he schemes (all permutations), or just a single scheme ?
    if (run_full_fact_schemes == True) :
    
        ##########################################
        # Run experiment - all schemes
        ##########################################
        
        ########### independent mapping and pri assignment
        ALL_MAPPING_SCHEMES = [2,5,8,9]
        ALL_PRIASS_SCHEMES = [0,1,2,4]
        
        for each_mapping_scheme in ALL_MAPPING_SCHEMES:
            for each_priass_scheme in ALL_PRIASS_SCHEMES:                
                
                ##########################################
                # Run experiment - multiple scheme
                ##########################################
                SimParams.COMBINED_MAPPING_AND_PRIASS = TaskMappingAndPriAssCombinedSchemes.TASKMAPPINGANDPRIASSCOMBINED_DISABLED
                SimParams.DYNAMIC_TASK_MAPPING_SCHEME = each_mapping_scheme
                SimParams.DYNAMIC_TASK_PRIASS_SCHEME = each_priass_scheme
                random.seed(seed)
                np.random.seed(seed)
                print "----------------------------------------------------------------------------------------------------------------------------"
                print "Running runExp_MappingAndPriSchemes : num_wf=" + str(num_wfs) + ", mapping="+str(each_mapping_scheme) + ", pri_ass="+str(each_priass_scheme) 
                print "----------------------------------------------------------------------------------------------------------------------------"
                
                FNAME_PREFIX = "Exp_m"+str(SimParams.DYNAMIC_TASK_MAPPING_SCHEME) + "_p"+str(SimParams.DYNAMIC_TASK_PRIASS_SCHEME) + "_"
                        
                env, last_scheduled_task_time = MMMSim.runMainSimulation()
                env.run(until=last_scheduled_task_time+SimParams.SIM_RUNTIME)
                print env.now        
                
                # name the report filenames
                tm_fname            = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_timeline.png"
                vs_bs_fname         = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_vsbs.js"
                util_fname          = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX +'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_util.js"
                wf_res_fname        = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_wfressumm.js"
                gops_opbuff_fname   = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_gopsopbuffsumm.js"
                
                rmtbl_dt_fname      = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_rmtbldt.js"
                ibuff_fname         = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_ibuff.js"
                obuff_fname         = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_obuff.js"
                nodetqs_fname       = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_nodetqs.js"
                rmtaskrelease_fname       = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_rmtaskrel.js"
                mappingandpriass_fname = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_mappingandpriass.js"
                
                
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
                MMMSim.SimMon.report_RMTaskReleaseInfo(dump_to_file=rmtaskrelease_fname)
                MMMSim.SimMon.report_MappingAndPriAssInfo(dump_to_file=mappingandpriass_fname)
                
                
                
        ########### combined mapping and pri assignment
        COMBINED_MAPPING_SCHEMES = [800, 801, 810]
        
        for each_combined_scheme in COMBINED_MAPPING_SCHEMES:
            SimParams.COMBINED_MAPPING_AND_PRIASS = each_combined_scheme
            
            random.seed(seed)
            np.random.seed(seed)
            print "----------------------------------------------------------------------------------------------------------------------------"
            print "Running runExp_MappingAndPriSchemes : num_wf=" + str(num_wfs) + ", mapping="+str(each_combined_scheme) + ", pri_ass="+str(each_combined_scheme) 
            print "----------------------------------------------------------------------------------------------------------------------------"
            
            FNAME_PREFIX = "Exp_m"+str(each_combined_scheme) + "_p"+str(each_combined_scheme) + "_"
                    
            env, last_scheduled_task_time = MMMSim.runMainSimulation()
            env.run(until=last_scheduled_task_time+SimParams.SIM_RUNTIME)
            print env.now        
            
            # name the report filenames
            tm_fname            = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_timeline.png"
            vs_bs_fname         = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_vsbs.js"
            util_fname          = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX +'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_util.js"
            wf_res_fname        = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_wfressumm.js"
            gops_opbuff_fname   = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_gopsopbuffsumm.js"
            
            rmtbl_dt_fname      = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_rmtbldt.js"
            ibuff_fname         = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_ibuff.js"
            obuff_fname         = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_obuff.js"
            nodetqs_fname       = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_nodetqs.js"
            rmtaskrelease_fname       = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_rmtaskrel.js"
            mappingandpriass_fname = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_mappingandpriass.js"
            
            
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
            
            
    else:
    
    
        ##########################################
        # Run experiment - single scheme
        ##########################################
        SimParams.DYNAMIC_TASK_MAPPING_SCHEME = mapping_scheme
        SimParams.DYNAMIC_TASK_PRIASS_SCHEME = pri_ass_scheme
        random.seed(seed)
        np.random.seed(seed)
        print "----------------------------------------------------------------------------------------------------------------------------"
        print "Running runExp_MappingAndPriSchemes : num_wf=" + str(num_wfs) + ", mapping="+str(mapping_scheme) + ", pri_ass="+str(pri_ass_scheme) 
        print "----------------------------------------------------------------------------------------------------------------------------"
        
        FNAME_PREFIX = "Exp_m"+str(SimParams.DYNAMIC_TASK_MAPPING_SCHEME) + "_p"+str(SimParams.DYNAMIC_TASK_PRIASS_SCHEME) + "_"
                
        env, last_scheduled_task_time = MMMSim.runMainSimulation()
        env.run(until=last_scheduled_task_time+SimParams.SIM_RUNTIME)
        print env.now        
        
        # name the report filenames
        tm_fname            = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_timeline.png"
        vs_bs_fname         = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_vsbs.js"
        util_fname          = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX +'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_util.js"
        wf_res_fname        = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_wfressumm.js"
        gops_opbuff_fname   = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_gopsopbuffsumm.js"
        
        rmtbl_dt_fname      = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_rmtbldt.js"
        ibuff_fname         = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_ibuff.js"
        obuff_fname         = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_obuff.js"
        nodetqs_fname       = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_nodetqs.js"
        rmtaskrelease_fname       = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_rmtaskrel.js"
                
        
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
        #MMMSim.SimMon.report_RMTaskReleaseInfo(dump_to_file=rmtaskrelease_fname)
        #MMMSim.SimMon.report_MappingAndPriAssInfo("")
        
                
    print "----"
    print ">> Experiment FINISHED"
    print "----"
   





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
parser.add_argument("--mapping_scheme", help="Semi-dynamic mapping scheme", type=int, default=-1)
parser.add_argument("--pri_ass_scheme", help="Semi-dynamic priority assignment scheme", type=int, default=-1)
parser.add_argument("--run_full_fact_schemes", help="Run all mapping and pri ass schemes", type=int, default=-1)

args = parser.parse_args()

####################################
## check which experiment to run ##
####################################

#### multiple workflows - variable heuristics ####
if(args.exp_type == "Exp_MappingAndPri"):
    
    if ((args.wf_num == -1) or \
        (args.forced_seed == -1) or \
        (args.mapping_scheme == -1) or \
        (args.pri_ass_scheme == -1) or \
        (args.run_full_fact_schemes == -1) ):
        
        parser.print_usage()
        sys.exit("invalid arguments : AC-test enable flags required")            
    else:
        
        # call experiment        
        runExp_MappingAndPriSchemes(num_wfs         = args.wf_num,            
                                    forced_seed     = args.forced_seed,
                                    mapping_scheme  = args.mapping_scheme,
                                    pri_ass_scheme  = args.pri_ass_scheme,
                                    run_full_fact_schemes = (True if (args.run_full_fact_schemes==1) else False),                                  
                                    )

elif(args.exp_type == "Exp_Simple"):   
    runSim_Simple()


else:
    parser.print_usage()
    sys.exit("invalid arguments")


