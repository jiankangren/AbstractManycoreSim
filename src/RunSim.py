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
from SimParams import SimParams


import Multicore_MPEG_Model as MMMSim


NUM_WORKFLOWS = range(8, 17, 2)
#NUM_WORKFLOWS = [12]
NUM_NODES = [2,4,8,16,32]
NOC_XY = [(2,1), (2,2), (2,4), (2,8), (2,16)]


# lateness vs. number of cores
def runSim_Simple(num_wfs):
    
    print random.random()
    
    sim_start_time = time.clock()
    print "runSim_Simple :: start_time = " + str(sim_start_time)
    
    # init seed
    #seed = random.randint(0, sys.maxint)
    #print "SEED === " + str(seed)    
    random.seed(1234)
    np.random.seed(1234)
    #random.seed(1909964230)
    #random.seed(seed)
    
    # fixed params
    SimParams.SLACK_FEEDBACK_ENABLED = False   
    SimParams.LOG_OUTPUT_SCHED_TEST_REPORT    = False
    
    SimParams.NUM_WORKFLOWS = num_wfs
    SimParams.NUM_INPUTBUFFERS = num_wfs
    SimParams.AC_TEST_OPTION = AdmissionControllerOptions.AC_OPTION_SCHEDTEST_TASKSONLY_ONLY
    SimParams.WCRT_SCHEDULABILITY_TEST_PERCENTAGE = 100.0
        
    env, last_scheduled_task_time = MMMSim.runMainSimulation()
    env.run(until=last_scheduled_task_time+SimParams.SIM_RUNTIME)
    print env.now
    
    sim_end_time = time.clock()
    print "runSim_Simple :: end_time = " + str(sim_end_time)
    print "runSim_Simple :: time taken = " + str(sim_end_time-sim_start_time)
    
    
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
    
    
    

# for the same workload - we check different percentages of the schedulability test
def runACTest_PercentageSchedulable_vs_DeadlineMiss(sched_perc):
    
    NUM_RUNS = 30
    percentage_list = range(0, 80, 5)
    
    # fixed params
    SimParams.SLACK_FEEDBACK_ENABLED = False
    SimParams.NUM_WORKFLOWS = 11
    SimParams.NUM_INPUTBUFFERS = 11 
    SimParams.AC_TEST_OPTION = AdmissionControllerOptions.AC_OPTION_SCHEDTEST_ONLY
    
    for each_run in xrange(NUM_RUNS):    
        
        # init seed
        seed = random.randint(0, sys.maxint)
        print "SEED === " + str(seed)    
        #random.seed(1087744070)
        #random.seed(1909964230)
        random.seed(seed)    
        
        sim_start_time = time.clock()
        print "runSim_Simple :: start_time = " + str(sim_start_time)
            
        #############################################################
        # run simulation for the given schedulability test percentage
        #############################################################
        
        SimParams.WCRT_SCHEDULABILITY_TEST_PERCENTAGE = float(sched_perc)
        
        random.seed(seed)
        print "----------------------------------------------------------"
        print "Running Test : percentage=" + str(sched_perc) + "%, actest = hybrid_v1"
        print "----------------------------------------------------------"
        FNAME_PREFIX = "ACTest_sched_p" + str(sched_perc) + "_"
        EXP_OUTPUT_FOLDER = "experiment_data/sched_percentage_compare/" + "seed_" + str(seed) + "/"
        
        if not os.path.exists(EXP_OUTPUT_FOLDER):
            os.makedirs(EXP_OUTPUT_FOLDER)        
              
        env, last_scheduled_task_time = MMMSim.runMainSimulation()
        env.run(until=last_scheduled_task_time+SimParams.SIM_RUNTIME)
        print env.now
        
        sim_end_time = time.clock()
        print "runSim_Simple :: end_time = " + str(sim_end_time)
        print "runSim_Simple :: time taken = " + str(sim_end_time-sim_start_time)
        
        tm_fname = EXP_OUTPUT_FOLDER +  FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_timeline.png"
        vs_bs_fname = EXP_OUTPUT_FOLDER +  FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + ".js"
        util_fname = EXP_OUTPUT_FOLDER +  FNAME_PREFIX +'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES)
        wf_res_fname = EXP_OUTPUT_FOLDER +  FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_wfressumm.js"
        gops_opbuff_fname = EXP_OUTPUT_FOLDER +  FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_gopsopbuffsumm.js"
        rmtbl_dt_fname = EXP_OUTPUT_FOLDER +  FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_rmtbldt.js"
        
        (wf_results_summary, gops_in_outputbuff_summary) = MMMSim.SimMon.report_DecodedWorkflows_Summary(timeline_fname=tm_fname, 
                                                                                                         wf_res_summary_fname = wf_res_fname, 
                                                                                                        gops_opbuff_summary_fname = gops_opbuff_fname,
                                                                                                        rmtbl_dt_summary_fname = rmtbl_dt_fname,
                                                                                                        output_format = "json")
        
        MMMSim.SimMon.report_VideoStream_BasicStats(wf_results_summary, vs_bs_fname)
        #MMMSim.SimMon.report_InstUtilisation(dump_to_file=util_fname)
    
        



# multiple runs with varying number of workflows
# basic video stats output at the end - to check efficiency of admission controller
def runACTest_multiWorkflows(num_wfs):        
        
    # init seed
    #seed = random.randint(0, sys.maxint)
    seed = 1087744070
    print "SEED === " + str(seed)    
    #random.seed(1963493565)
    #random.seed(1234)    
             
    # fixed params
    SimParams.SLACK_FEEDBACK_ENABLED = False
    SimParams.NUM_WORKFLOWS = num_wfs
    SimParams.NUM_INPUTBUFFERS = num_wfs
    
    
    ##########################################
    # ac_test : None
    ##########################################
    random.seed(seed)
    np.random.seed(seed)
    print "----------------------------------------------------------"
    print "Running Test : num_wf=" + str(num_wfs) + ", actest = none"
    print "----------------------------------------------------------"
    
    FNAME_PREFIX = "ACTest_none_"
      
    SimParams.AC_TEST_OPTION = AdmissionControllerOptions.AC_OPTION_NONE        
    env, last_scheduled_task_time = MMMSim.runMainSimulation()
    env.run(until=last_scheduled_task_time+SimParams.SIM_RUNTIME)
    print env.now
    
    tm_fname = 'experiment_data/vs_ac_test/' +  FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_timeline.png"
    vs_bs_fname = 'experiment_data/vs_ac_test/' +  FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + ".js"
    util_fname = 'experiment_data/vs_ac_test/' +  FNAME_PREFIX +'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES)
    wf_res_fname = 'experiment_data/vs_ac_test/' +  FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_wfressumm.js"
    gops_opbuff_fname = 'experiment_data/vs_ac_test/' +  FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_gopsopbuffsumm.js"
    rmtbl_dt_fname = 'experiment_data/vs_ac_test/' +  FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_rmtbldt.js"
    
    (wf_results_summary, gops_in_outputbuff_summary) = MMMSim.SimMon.report_DecodedWorkflows_Summary(timeline_fname=tm_fname, 
                                                                                                     wf_res_summary_fname = wf_res_fname, 
                                                                                                    gops_opbuff_summary_fname = gops_opbuff_fname,
                                                                                                    rmtbl_dt_summary_fname = rmtbl_dt_fname,
                                                                                                    output_format = "json")
    
    MMMSim.SimMon.report_VideoStream_BasicStats(wf_results_summary, vs_bs_fname)
    MMMSim.SimMon.report_InstUtilisation(dump_to_file=util_fname)
    
    
    ##########################################
    # ac_test : heuristics only
    ##########################################
    random.seed(seed)
    np.random.seed(seed)
    print "----------------------------------------------------------"
    print "Running Test : num_wf=" + str(num_wfs) + ", actest = heuristics_only"
    print "----------------------------------------------------------"
    
    FNAME_PREFIX = "ACTest_heu_"
      
    SimParams.AC_TEST_OPTION = AdmissionControllerOptions.AC_OPTION_HEURISTIC_ONLY        
    env, last_scheduled_task_time = MMMSim.runMainSimulation()
    env.run(until=last_scheduled_task_time+SimParams.SIM_RUNTIME)
    print env.now
    
    tm_fname = 'experiment_data/vs_ac_test/' +  FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_timeline.png"
    vs_bs_fname = 'experiment_data/vs_ac_test/' +  FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + ".js"
    util_fname = 'experiment_data/vs_ac_test/' +  FNAME_PREFIX +'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES)
    wf_res_fname = 'experiment_data/vs_ac_test/' +  FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_wfressumm.js"
    gops_opbuff_fname = 'experiment_data/vs_ac_test/' +  FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_gopsopbuffsumm.js"
    rmtbl_dt_fname = 'experiment_data/vs_ac_test/' +  FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_rmtbldt.js"
    
    (wf_results_summary, gops_in_outputbuff_summary) = MMMSim.SimMon.report_DecodedWorkflows_Summary(timeline_fname=tm_fname, 
                                                                                                     wf_res_summary_fname = wf_res_fname, 
                                                                                                    gops_opbuff_summary_fname = gops_opbuff_fname,
                                                                                                    rmtbl_dt_summary_fname = rmtbl_dt_fname,
                                                                                                    output_format = "json")
    
    MMMSim.SimMon.report_VideoStream_BasicStats(wf_results_summary, vs_bs_fname)
    MMMSim.SimMon.report_InstUtilisation(dump_to_file=util_fname)
    
    
    ##########################################
    # ac_test : schedulability test only
    ##########################################
    random.seed(seed)
    np.random.seed(seed)
    print "----------------------------------------------------------"
    print "Running Test : num_wf=" + str(num_wfs) + ", actest = schedulability_only"
    print "----------------------------------------------------------"
    FNAME_PREFIX = "ACTest_sched_"
      
    SimParams.AC_TEST_OPTION = AdmissionControllerOptions.AC_OPTION_SCHEDTEST_ONLY        
    env, last_scheduled_task_time = MMMSim.runMainSimulation()
    env.run(until=last_scheduled_task_time+SimParams.SIM_RUNTIME)
    print env.now
    
    tm_fname = 'experiment_data/vs_ac_test/' +  FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_timeline.png"
    vs_bs_fname = 'experiment_data/vs_ac_test/' +  FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + ".js"
    util_fname = 'experiment_data/vs_ac_test/' +  FNAME_PREFIX +'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES)
    wf_res_fname = 'experiment_data/vs_ac_test/' +  FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_wfressumm.js"
    gops_opbuff_fname = 'experiment_data/vs_ac_test/' +  FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_gopsopbuffsumm.js"
    rmtbl_dt_fname = 'experiment_data/vs_ac_test/' +  FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_rmtbldt.js"
    
    (wf_results_summary, gops_in_outputbuff_summary) = MMMSim.SimMon.report_DecodedWorkflows_Summary(timeline_fname=tm_fname, 
                                                                                                     wf_res_summary_fname = wf_res_fname, 
                                                                                                    gops_opbuff_summary_fname = gops_opbuff_fname,
                                                                                                    rmtbl_dt_summary_fname = rmtbl_dt_fname,
                                                                                                    output_format = "json")
    MMMSim.SimMon.report_VideoStream_BasicStats(wf_results_summary, vs_bs_fname)
    MMMSim.SimMon.report_InstUtilisation(dump_to_file=util_fname)
    
    
#    ############################################
#    # ac_test : combined heuristics + sched test (hybrid-v1)
#    ############################################
#    random.seed(seed)
#    print "----------------------------------------------------------"
#    print "Running Test : num_wf=" + str(num_wfs) + ", actest = hybrid_v1"
#    print "----------------------------------------------------------"
#    FNAME_PREFIX = "ACTest_hybv1_"
#      
#    SimParams.AC_TEST_OPTION = AdmissionControllerOptions.AC_OPTION_HYB_HEU_SCHD_V1        
#    env, last_scheduled_task_time = MMMSim.runMainSimulation()
#    env.run(until=last_scheduled_task_time+SimParams.SIM_RUNTIME)
#    print env.now
#    
#    tm_fname = 'experiment_data/vs_ac_test/' +  FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_timeline.png"
#    vs_bs_fname = 'experiment_data/vs_ac_test/' +  FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + ".js"
#    util_fname = 'experiment_data/vs_ac_test/' +  FNAME_PREFIX +'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES)
#    wf_res_fname = 'experiment_data/vs_ac_test/' +  FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_wfressumm.js"
#    gops_opbuff_fname = 'experiment_data/vs_ac_test/' +  FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_gopsopbuffsumm.js"
#    rmtbl_dt_fname = 'experiment_data/vs_ac_test/' +  FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_rmtbldt.js"
#    
#    (wf_results_summary, gops_in_outputbuff_summary) = MMMSim.SimMon.report_DecodedWorkflows_Summary(timeline_fname=tm_fname, 
#                                                                                                     wf_res_summary_fname = wf_res_fname, 
#                                                                                                    gops_opbuff_summary_fname = gops_opbuff_fname,
#                                                                                                    rmtbl_dt_summary_fname = rmtbl_dt_fname,
#                                                                                                    output_format = "json")
#    
#    MMMSim.SimMon.report_VideoStream_BasicStats(wf_results_summary, vs_bs_fname)
#    MMMSim.SimMon.report_InstUtilisation(dump_to_file=util_fname)
        
        
# multiple runs with varying number of workflows
# basic video stats output at the end - to check efficiency of admission controller
def runACTest_multiWorkflows_VariableHeuristics(num_wfs,
                                                Test_None = False,
                                                Test_Determ = False,
                                                Test_Determ_tasksonly = False,
                                                Test_VH_single = False,
                                                Test_VH_range = False, 
                                                Test_KG = False,
                                                
                                                # randomise seed
                                                forced_seed = None,
                                                
                                                # used for Test_VH_single                                                
                                                Ibuff_ratio = None,
                                                TQbuff_ratio = None,
                                                ):        
        
    # init seed
    if(forced_seed != None):
        seed = forced_seed
    else:
        #seed = random.randint(0, sys.maxint)
        seed = 1087744070
    
    print "SEED === " + str(seed)    
    #random.seed(1963493565)
    #random.seed(1234)    
             
    # fixed params
    SimParams.SLACK_FEEDBACK_ENABLED = False
    SimParams.NUM_WORKFLOWS = num_wfs
    SimParams.NUM_INPUTBUFFERS = num_wfs  
    
    ROOT_DATA_OUTPUT_DIR =   'experiment_data/vs_ac_test/' + "seed_"+str(seed) + "/"
    
    
    ## check and make directory ##
    #_makeDir(ROOT_DATA_OUTPUT_DIR)
    
    
    
    ##########################################
    # ac_test : None
    ##########################################
    if(Test_None == True):
        random.seed(seed)
        np.random.seed(seed)
        print "----------------------------------------------------------"
        print "Running Test : num_wf=" + str(num_wfs) + ", actest = none"
        print "----------------------------------------------------------"
        
        FNAME_PREFIX = "ACTest_none_"
          
        SimParams.AC_TEST_OPTION = AdmissionControllerOptions.AC_OPTION_NONE        
        env, last_scheduled_task_time = MMMSim.runMainSimulation()
        env.run(until=last_scheduled_task_time+SimParams.SIM_RUNTIME)
        print env.now
        
        tm_fname            = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_timeline.png"
        vs_bs_fname         = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_vsbs.js"
        util_fname          = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX +'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_util.js"
        wf_res_fname        = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_wfressumm.js"
        gops_opbuff_fname   = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_gopsopbuffsumm.js"
        rmtbl_dt_fname      = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_rmtbldt.js"
        
        (wf_results_summary, gops_in_outputbuff_summary) = MMMSim.SimMon.report_DecodedWorkflows_Summary(timeline_fname=tm_fname, 
                                                                                                         wf_res_summary_fname = wf_res_fname, 
                                                                                                        gops_opbuff_summary_fname = gops_opbuff_fname,
                                                                                                        rmtbl_dt_summary_fname = rmtbl_dt_fname,
                                                                                                        output_format = "json")
        
        MMMSim.SimMon.report_VideoStream_BasicStats(wf_results_summary, vs_bs_fname)
        MMMSim.SimMon.report_InstUtilisation(dump_to_file=util_fname)
        
    
    ####################################################
    # ac_test : schedulability test only (tasks + flows)
    ####################################################
    if(Test_Determ == True):
        random.seed(seed)
        np.random.seed(seed)
        print "----------------------------------------------------------"
        print "Running Test : num_wf=" + str(num_wfs) + ", actest = schedulability_only"
        print "----------------------------------------------------------"
        FNAME_PREFIX = "ACTest_sched_"
          
        SimParams.AC_TEST_OPTION = AdmissionControllerOptions.AC_OPTION_SCHEDTEST_ONLY        
        env, last_scheduled_task_time = MMMSim.runMainSimulation()
        env.run(until=last_scheduled_task_time+SimParams.SIM_RUNTIME)
        print env.now
        
        tm_fname                = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_timeline.png"
        vs_bs_fname             = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_vsbs.js"
        util_fname              = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX +'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES)  + "_util.js"
        wf_res_fname            = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_wfressumm.js"
        gops_opbuff_fname       = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_gopsopbuffsumm.js"
        rmtbl_dt_fname          = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_rmtbldt.js"
        
        (wf_results_summary, gops_in_outputbuff_summary) = MMMSim.SimMon.report_DecodedWorkflows_Summary(timeline_fname=tm_fname, 
                                                                                                         wf_res_summary_fname = wf_res_fname, 
                                                                                                        gops_opbuff_summary_fname = gops_opbuff_fname,
                                                                                                        rmtbl_dt_summary_fname = rmtbl_dt_fname,
                                                                                                        output_format = "json")
        MMMSim.SimMon.report_VideoStream_BasicStats(wf_results_summary, vs_bs_fname)
        MMMSim.SimMon.report_InstUtilisation(dump_to_file=util_fname)
        
    ####################################################
    # ac_test : schedulability test only (tasks only)
    ####################################################
    if(Test_Determ_tasksonly == True):
        random.seed(seed)
        np.random.seed(seed)
        print "----------------------------------------------------------"
        print "Running Test : num_wf=" + str(num_wfs) + ", actest = schedulability_tasks_only"
        print "----------------------------------------------------------"
        FNAME_PREFIX = "ACTest_schedtasksonly_"
          
        SimParams.AC_TEST_OPTION = AdmissionControllerOptions.AC_OPTION_SCHEDTEST_TASKSONLY_ONLY        
        env, last_scheduled_task_time = MMMSim.runMainSimulation()
        env.run(until=last_scheduled_task_time+SimParams.SIM_RUNTIME)
        print env.now
        
        tm_fname                = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_timeline.png"
        vs_bs_fname             = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_vsbs.js"
        util_fname              = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX +'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES)  + "_util.js"
        wf_res_fname            = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_wfressumm.js"
        gops_opbuff_fname       = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_gopsopbuffsumm.js"
        rmtbl_dt_fname          = ROOT_DATA_OUTPUT_DIR + FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_rmtbldt.js"
        
        (wf_results_summary, gops_in_outputbuff_summary) = MMMSim.SimMon.report_DecodedWorkflows_Summary(timeline_fname=tm_fname, 
                                                                                                         wf_res_summary_fname = wf_res_fname, 
                                                                                                        gops_opbuff_summary_fname = gops_opbuff_fname,
                                                                                                        rmtbl_dt_summary_fname = rmtbl_dt_fname,
                                                                                                        output_format = "json")
        MMMSim.SimMon.report_VideoStream_BasicStats(wf_results_summary, vs_bs_fname)
        MMMSim.SimMon.report_InstUtilisation(dump_to_file=util_fname)

    #############################################################
    # ac_test : variable heuristics-thresholded (range of values)
    #############################################################
    if(Test_VH_range == True):
    
        IBUFF_TASKS_LATENESS_RATIO_RANGE    = [0.1, 0.3, 0.5, 0.7, 0.9, 1.0]
        TQ_TASKS_LATENESS_RATIO_RANGE       = [0.1, 0.3, 0.5, 0.7, 0.9, 1.0]
        
        for each_ibuff_ratio in IBUFF_TASKS_LATENESS_RATIO_RANGE:
            for each_tq_ratio in TQ_TASKS_LATENESS_RATIO_RANGE:
                                        
                random.seed(seed)
                np.random.seed(seed)
                print "--------------------------------------------------------------------------"
                print "Running Test : num_wf=" + str(num_wfs) + ", actest = heuristics_thresholded"
                print "--------------------------------------------------------------------------"
                
                FNAME_PREFIX = "ACTest_heuth_" + "iblr" + str(each_ibuff_ratio) + "_tqlr" + str(each_tq_ratio) + "_"
                  
                SimParams.AC_TEST_OPTION = AdmissionControllerOptions.AC_OPTION_HEURISTIC_THRESHOLDED            
                SimParams.AC_TEST_IBUFF_TASK_LATENESS_RATIO = each_ibuff_ratio        
                SimParams.AC_TEST_TQ_TASK_LATENESS_RATIO = each_tq_ratio
                                    
                env, last_scheduled_task_time = MMMSim.runMainSimulation()
                env.run(until=last_scheduled_task_time+SimParams.SIM_RUNTIME)
                print env.now
                
                tm_fname                = ROOT_DATA_OUTPUT_DIR +  FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_timeline.png"
                vs_bs_fname             = ROOT_DATA_OUTPUT_DIR +  FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_vsbs.js"
                util_fname              = ROOT_DATA_OUTPUT_DIR +  FNAME_PREFIX +'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES)  + "_util.js"
                wf_res_fname            = ROOT_DATA_OUTPUT_DIR +  FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_wfressumm.js"
                gops_opbuff_fname       = ROOT_DATA_OUTPUT_DIR +  FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_gopsopbuffsumm.js"
                rmtbl_dt_fname          = ROOT_DATA_OUTPUT_DIR +  FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_rmtbldt.js"
                
                (wf_results_summary, gops_in_outputbuff_summary) = MMMSim.SimMon.report_DecodedWorkflows_Summary(timeline_fname=tm_fname, 
                                                                                                                 wf_res_summary_fname = wf_res_fname, 
                                                                                                                gops_opbuff_summary_fname = gops_opbuff_fname,
                                                                                                                rmtbl_dt_summary_fname = rmtbl_dt_fname,
                                                                                                                output_format = "json")
                
                MMMSim.SimMon.report_VideoStream_BasicStats(wf_results_summary, vs_bs_fname)
                MMMSim.SimMon.report_InstUtilisation(dump_to_file=util_fname)
                
        
        
    #############################################################
    # ac_test : variable heuristics-thresholded (range of values)
    #############################################################
    if(Test_VH_single == True):
        
        if(Ibuff_ratio != None) or (TQbuff_ratio != None):
        
            random.seed(seed)
            np.random.seed(seed)
            print "--------------------------------------------------------------------------"
            print "Running Test : num_wf=" + str(num_wfs) + ", actest = heuristics_thresholded"
            print "--------------------------------------------------------------------------"
            
            FNAME_PREFIX = "ACTest_heuth_" + "iblr" + str(Ibuff_ratio) + "_tqlr" + str(TQbuff_ratio) + "_"
              
            SimParams.AC_TEST_OPTION = AdmissionControllerOptions.AC_OPTION_HEURISTIC_THRESHOLDED            
            SimParams.AC_TEST_IBUFF_TASK_LATENESS_RATIO = Ibuff_ratio        
            SimParams.AC_TEST_TQ_TASK_LATENESS_RATIO = TQbuff_ratio
                                
            env, last_scheduled_task_time = MMMSim.runMainSimulation()
            env.run(until=last_scheduled_task_time+SimParams.SIM_RUNTIME)
            print env.now
            
            tm_fname                = ROOT_DATA_OUTPUT_DIR +  FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_timeline.png"
            vs_bs_fname             = ROOT_DATA_OUTPUT_DIR +  FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_vsbs.js"
            util_fname              = ROOT_DATA_OUTPUT_DIR +  FNAME_PREFIX +'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES)  + "_util.js"
            wf_res_fname            = ROOT_DATA_OUTPUT_DIR +  FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_wfressumm.js"
            gops_opbuff_fname       = ROOT_DATA_OUTPUT_DIR +  FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_gopsopbuffsumm.js"
            rmtbl_dt_fname          = ROOT_DATA_OUTPUT_DIR +  FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_rmtbldt.js"
            
            (wf_results_summary, gops_in_outputbuff_summary) = MMMSim.SimMon.report_DecodedWorkflows_Summary(timeline_fname=tm_fname, 
                                                                                                             wf_res_summary_fname = wf_res_fname, 
                                                                                                            gops_opbuff_summary_fname = gops_opbuff_fname,
                                                                                                            rmtbl_dt_summary_fname = rmtbl_dt_fname,
                                                                                                            output_format = "json")
            
            MMMSim.SimMon.report_VideoStream_BasicStats(wf_results_summary, vs_bs_fname)
            MMMSim.SimMon.report_InstUtilisation(dump_to_file=util_fname)
            
        else:
            sys.exit("Error - ibuff, tqbuff ratios not supplied")
            
    
    ##########################################################
    # ac_test : heuristic based - using KG deadline assignment
    ##########################################################
    if(Test_KG == True):
        
        ## ------------------ deadline assignment - KG-ES --------------------------------------   
        random.seed(seed)
        np.random.seed(seed)
        print "--------------------------------------------------------------------------"
        print "Running Test : num_wf=" + str(num_wfs) + ", actest = heuristics_KG_ES"
        print "--------------------------------------------------------------------------"
        
        FNAME_PREFIX = "ACTest_heukgES_" 
        
        SimParams.AC_TEST_OPTION = AdmissionControllerOptions.AC_OPTION_HEURISTIC_KAO_DEADLINE_ES         
        
        env, last_scheduled_task_time = MMMSim.runMainSimulation()
        env.run(until=last_scheduled_task_time+SimParams.SIM_RUNTIME)
        print env.now
        
        tm_fname                = ROOT_DATA_OUTPUT_DIR +  FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_timeline.png"
        vs_bs_fname             = ROOT_DATA_OUTPUT_DIR +  FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_vsbs.js"
        util_fname              = ROOT_DATA_OUTPUT_DIR +  FNAME_PREFIX +'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES)  + "_util.js"
        wf_res_fname            = ROOT_DATA_OUTPUT_DIR +  FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_wfressumm.js"
        gops_opbuff_fname       = ROOT_DATA_OUTPUT_DIR +  FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_gopsopbuffsumm.js"
        rmtbl_dt_fname          = ROOT_DATA_OUTPUT_DIR +  FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_rmtbldt.js"
                 
        (wf_results_summary, gops_in_outputbuff_summary) = MMMSim.SimMon.report_DecodedWorkflows_Summary(timeline_fname=tm_fname, 
                                                                                                         wf_res_summary_fname = wf_res_fname, 
                                                                                                        gops_opbuff_summary_fname = gops_opbuff_fname,
                                                                                                        rmtbl_dt_summary_fname = rmtbl_dt_fname,
                                                                                                        output_format = "json")
        
        MMMSim.SimMon.report_VideoStream_BasicStats(wf_results_summary, vs_bs_fname)
        MMMSim.SimMon.report_InstUtilisation(dump_to_file=util_fname)
        
        ## ------------------ deadline assignment - KG-EQF --------------------------------------
        random.seed(seed)
        np.random.seed(seed)
        print "--------------------------------------------------------------------------"
        print "Running Test : num_wf=" + str(num_wfs) + ", actest = heuristics_KG_EQF"
        print "--------------------------------------------------------------------------"
        
        FNAME_PREFIX = "ACTest_heukgEQF_" 
        
        SimParams.AC_TEST_OPTION = AdmissionControllerOptions.AC_OPTION_HEURISTIC_KAO_DEADLINE_EQF         
        
        env, last_scheduled_task_time = MMMSim.runMainSimulation()
        env.run(until=last_scheduled_task_time+SimParams.SIM_RUNTIME)
        print env.now
        
        tm_fname                = ROOT_DATA_OUTPUT_DIR +  FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_timeline.png"
        vs_bs_fname             = ROOT_DATA_OUTPUT_DIR +  FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_vsbs.js"
        util_fname              = ROOT_DATA_OUTPUT_DIR +  FNAME_PREFIX +'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES)  + "_util.js"
        wf_res_fname            = ROOT_DATA_OUTPUT_DIR +  FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_wfressumm.js"
        gops_opbuff_fname       = ROOT_DATA_OUTPUT_DIR +  FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_gopsopbuffsumm.js"
        rmtbl_dt_fname          = ROOT_DATA_OUTPUT_DIR +  FNAME_PREFIX + 'wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES) + "_rmtbldt.js"
        
        (wf_results_summary, gops_in_outputbuff_summary) = MMMSim.SimMon.report_DecodedWorkflows_Summary(timeline_fname=tm_fname, 
                                                                                                         wf_res_summary_fname = wf_res_fname, 
                                                                                                        gops_opbuff_summary_fname = gops_opbuff_fname,
                                                                                                        rmtbl_dt_summary_fname = rmtbl_dt_fname,
                                                                                                        output_format = "json")
        
        MMMSim.SimMon.report_VideoStream_BasicStats(wf_results_summary, vs_bs_fname)
        MMMSim.SimMon.report_InstUtilisation(dump_to_file=util_fname)
        
        
        


# lateness vs. number of cores
def runLatenessExp_multiCores():
    
    # fixed params
    SimParams.NUM_WORKFLOWS = 16
    SimParams.NUM_INPUTBUFFERS = 16
    SimParams.SLACK_FEEDBACK_ENABLED = False
    
    # feedback = true
    for i in xrange(5):
    #for i in [4]:
        
        print "i = " + str(NUM_NODES[i])
        
        SimParams.NUM_NODES = NUM_NODES[i]
        SimParams.NOC_H = NOC_XY[i][0]
        SimParams.NOC_W = NOC_XY[i][1]        
        
        env = MMMSim.runMainSimulation()
        env.run(until=SimParams.SIM_RUNTIME)
        
        fname = 'experiment_data/lateness/FbTrue_wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES)
        MMMSim.SimMon.report_OutputBuffer_Contents_ByGOP(dump_to_file=fname)
        #MMMSim.SimMon.report_InstUtilisation(dump_to_file=fname)
        
        
   


def runLatenessExp_multiWorkflows():
    
    # feedback = true
    for each_wf_num in NUM_WORKFLOWS:

        # set params
        SimParams.SLACK_FEEDBACK_ENABLED = True
        SimParams.NUM_WORKFLOWS = each_wf_num
        SimParams.NUM_INPUTBUFFERS = each_wf_num
        
        env = MMMSim.runMainSimulation()
        env.run(until=SimParams.SIM_RUNTIME)
        
        fname = 'experiment_data/lateness/FbTrue_wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES)
        #MMMSim.SimMon.report_OutputBuffer_Contents_ByGOP(dump_to_file=fname)
        MMMSim.SimMon.report_InstUtilisation(dump_to_file=fname)
        
        
    # feedback = false
    for each_wf_num in NUM_WORKFLOWS:

        # set params
        SimParams.SLACK_FEEDBACK_ENABLED = False
        SimParams.NUM_WORKFLOWS = each_wf_num
        SimParams.NUM_INPUTBUFFERS = each_wf_num
        
        env = MMMSim.runMainSimulation()
        env.run(until=SimParams.SIM_RUNTIME)
        
        fname = 'experiment_data/lateness/FbFalse_wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES)
        #MMMSim.SimMon.report_OutputBuffer_Contents_ByGOP(dump_to_file=fname)
        MMMSim.SimMon.report_InstUtilisation(dump_to_file=fname)



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

parser = argparse.ArgumentParser(__file__, description="Run specified experiment on abstract simulator")
parser.add_argument("--exp_type", "-t", help="Experiment Type", default=None)
parser.add_argument("--wf_num", "-w", help="Number of workflows", type=int, default=-1)
parser.add_argument("--sched_perc", "-s", help="schedulability percentage", type=int, default=-1)

# specific for the different type of ac-tests
parser.add_argument("--test_none", help="Enable/Disable (1/0) No-AC test", type=int, default=-1)
parser.add_argument("--test_determ", help="Enable/Disable (1/0) Determ. test", type=int, default=-1)
parser.add_argument("--test_determ_taskonly", help="Enable/Disable (1/0) Determ. test (tasks only)", type=int, default=-1)
parser.add_argument("--test_vh_range", help="Enable/Disable (1/0) Heu_VH_range test", type=int, default=-1)
parser.add_argument("--test_vh_single", help="Enable/Disable (1/0) Heu_VH_single test", type=int, default=-1)
parser.add_argument("--heuvh_iblr", help="HeuVH - Ibuff lateness raio", type=float, default=-1.0)
parser.add_argument("--heuvh_tqlr", help="HeuVH - TQ lateness raio", type=float, default=-1.0)
parser.add_argument("--forced_seed", help="experiment - seed", type=int, default=-1)


parser.add_argument("--test_kg", help="Enable/Disable (1/0) Heu_KG test", type=int, default=-1)

args = parser.parse_args()

####################################
## check which experiment to run ##
####################################

#### simple test ####
if(args.exp_type == "Exp_ACTest_Simple"):
    if(args.wf_num == -1):
        parser.print_usage()
        sys.exit("invalid arguments")
    else:
        runSim_Simple(args.wf_num)        


#### multiple workflows ####
elif(args.exp_type == "Exp_ACTest_MultiWorkflow"):
    if(args.wf_num == -1):
        parser.print_usage()
        sys.exit("invalid arguments")
    else:
        runACTest_multiWorkflows(args.wf_num)

#### multiple workflows - variable heuristics ####
elif(args.exp_type == "Exp_ACTest_MultiWorkflow_VH"):
    if(args.wf_num == -1):
        parser.print_usage()
        sys.exit("invalid arguments")
    else:
        if ((args.test_none == -1) or \
            (args.test_determ == -1) or \
            (args.test_kg == -1) or \
            (args.test_vh_single == -1) or \
            (args.test_vh_range == -1) or \
            (args.forced_seed == -1)            
            ):
            
            parser.print_usage()
            sys.exit("invalid arguments : AC-test enable flags required")            
        else:
            
            # if single, check if the ratios are supplied
            if (args.test_vh_single == 1):
                if (args.heuvh_iblr != -1.0) and (args.heuvh_tqlr != -1.0):
                    runACTest_multiWorkflows_VariableHeuristics(args.wf_num, 
                                                                Test_None               =   (True if (args.test_none==1) else False),
                                                                Test_Determ             =   (True if (args.test_determ==1) else False),
                                                                Test_Determ_tasksonly   = (True if (args.test_determ_taskonly==1) else False),
                                                                Test_VH_single          =   True,
                                                                Test_VH_range           =   False,
                                                                Test_KG                 =   (True if (args.test_kg==1) else False),
                                                                
                                                                forced_seed             =   args.forced_seed,
                                                                
                                                                Ibuff_ratio             =   args.heuvh_iblr,
                                                                TQbuff_ratio            =   args.heuvh_tqlr 
                                                                )
                else:
                    parser.print_usage()
                    sys.exit("invalid arguments : ibuff, tqbuff ratios not supplied")
            
            # all others just need bool
            else:
                runACTest_multiWorkflows_VariableHeuristics(args.wf_num, 
                                                                Test_None       =   (True if (args.test_none==1) else False),
                                                                Test_Determ     =   (True if (args.test_determ==1) else False),
                                                                Test_Determ_tasksonly   = (True if (args.test_determ_taskonly==1) else False),
                                                                Test_VH_single  =   (True if (args.test_vh_single==1) else False),
                                                                Test_VH_range   =   (True if (args.test_vh_range==1) else False),
                                                                Test_KG         =   (True if (args.test_kg==1) else False)   ,
                                                                
                                                                forced_seed     =   args.forced_seed,                                                             
                                                                )
            
            
    
#### Schedulability percentage experiment ####
elif(args.exp_type == "Exp_SchedPercentages"):
    if(args.sched_perc == -1):
        parser.print_usage()
        sys.exit("invalid arguments")
    else:        
        runACTest_PercentageSchedulable_vs_DeadlineMiss(args.sched_perc)
    
    
else:
    parser.print_usage()
    sys.exit("invalid arguments")




#runSim_Simple()
#runACTest_multiWorkflows()
#runACTest_PercentageSchedulable_vs_DeadlineMiss()
