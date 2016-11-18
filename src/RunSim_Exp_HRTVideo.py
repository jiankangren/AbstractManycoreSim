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

from libApplicationModel.Task import TaskModel

from SimParams import SimParams

import Multicore_MPEG_Model as MMMSim


NUM_WORKFLOWS = range(8, 17, 2)
#NUM_WORKFLOWS = [12]
NUM_NODES = [2,4,8,16,32]
NOC_XY = [(2,1), (2,2), (2,4), (2,8), (2,16)]


EXP_DATADIR = "experiment_data/hrt_video/"


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

# basic test - openloop
def runSim_Simple():
    
    seed = 99108    
    
    print "SEED === " + str(seed)    
             
    # fixed params
    SimParams.SLACK_FEEDBACK_ENABLED = False
    
    SimParams.NOC_W = 3
    SimParams.NOC_H = 3
    SimParams.NUM_NODES = (SimParams.NOC_W * SimParams.NOC_H)
    
    #dvb_resolutions = [(320,240),(320,240),(320,240),(320,240),(320,240)]
    dvb_resolutions = [(480,576),(480,576),(480,576),(480,576),(480,576)]
    
    SimParams.LOCAL_SCHEDULER_TYPE = LocalMPEG2FramePriorityScheduler_WithDepCheck()
    SimParams.SIM_ENTITY_RESOURCEMANAGER_CLASS    = RMTypes.OPENLOOP
    SimParams.SIM_ENTITY_CPUNODE_CLASS            = CPUTypes.OPENLOOP
    SimParams.SIM_ENTITY_MAPPER_CLASS             = MapperTypes.OPENLOOP
    SimParams.SIM_ENTITY_TASKDISPATCHER_CLASS     = TDTypes.OPENLOOP
    SimParams.DVB_RESOLUTIONS = dvb_resolutions
    SimParams.NUM_WORKFLOWS                 = 4
    SimParams.NUM_INPUTBUFFERS              = SimParams.NUM_WORKFLOWS
    SimParams.DVB_RESOLUTIONS_FIXED         = dvb_resolutions
    SimParams.DVB_RESOLUTIONS_SELECTED_RANDOM        = False
    
    SimParams.AC_TEST_OPTION = AdmissionControllerOptions.AC_OPTION_NONE_WITH_SCHEDTEST_WITHMMC
    SimParams.DYNAMIC_TASK_MAPPING_SCHEME = TaskMappingSchemes.TASKMAPPINGSCHEMES_LOWEST_UTILISATION
    SimParams.DYNAMIC_TASK_PRIASS_SCHEME  =  TaskSemiDynamicPrioritySchemes.TASKSEMIDYNAMICPRIORITYSCHEMES_LOWRES_FIRST    
    SimParams.COMBINED_MAPPING_AND_PRIASS = TaskMappingAndPriAssCombinedSchemes.TASKMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_KAUSHIK_PP
    
    
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
    schedtestresults_fname  = EXP_DATADIR+FNAME_PREFIX+"test__schedtestresults.js"        
    
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
    MMMSim.SimMon.report_WCRT_TasksAndFlows_viaSchedAnalysis(dump_to_file=schedtestresults_fname)
    
    


###################################################################################################
#        SCENARIO based runsim for4 different types of ACtests and mappers
###################################################################################################
def runSim_Scenario(                       
                       forced_seed = None,
                       scenario_exp_folder = None,
                       scenario_id = None,
                       dvb_resolutions = None,
                       dvb_resolutions_fixed = [],
                       dvb_resolutions_selected_random=True,
                       num_workflows = None,                       
                       run_noac_lum = True,
                       run_schedac_lum  = True,
                       run_noac_improvedm = True,
                       run_schedac_improvedm = True,
                       
                       ):
    
    seed = forced_seed    
    
    SCENARIO_ID = scenario_id
    
    print "SEED === " + str(seed)    
             
    # fixed params
    SimParams.SLACK_FEEDBACK_ENABLED = False
    
    SimParams.NOC_W = 3
    SimParams.NOC_H = 3
    SimParams.NUM_NODES = (SimParams.NOC_W * SimParams.NOC_H)
    SimParams.LOCAL_SCHEDULER_TYPE = LocalMPEG2FramePriorityScheduler_WithDepCheck()
    SimParams.SIM_ENTITY_RESOURCEMANAGER_CLASS    = RMTypes.OPENLOOP
    SimParams.SIM_ENTITY_CPUNODE_CLASS            = CPUTypes.OPENLOOP
    SimParams.SIM_ENTITY_MAPPER_CLASS             = MapperTypes.OPENLOOP
    SimParams.SIM_ENTITY_TASKDISPATCHER_CLASS     = TDTypes.OPENLOOP
    SimParams.DVB_RESOLUTIONS = dvb_resolutions
    SimParams.NUM_WORKFLOWS                 = num_workflows
    SimParams.NUM_INPUTBUFFERS              = SimParams.NUM_WORKFLOWS
    SimParams.DVB_RESOLUTIONS_FIXED         = dvb_resolutions_fixed
    SimParams.DVB_RESOLUTIONS_SELECTED_RANDOM        = dvb_resolutions_selected_random

    SimParams.DVB_RESOLUTIONS = [(720,576), (544,576), (528,576), (480,576), (426,240), (320,240), (240,180)] 
        

    if(run_noac_lum == True):
        ############################
        #### No AC - LU Mapping ####
        ############################    
        SimParams.AC_TEST_OPTION                = AdmissionControllerOptions.AC_OPTION_NONE_WITH_SCHEDTEST_WITHMMC
        SimParams.DYNAMIC_TASK_MAPPING_SCHEME   = TaskMappingSchemes.TASKMAPPINGSCHEMES_LOWEST_UTILISATION
        SimParams.DYNAMIC_TASK_PRIASS_SCHEME    = TaskSemiDynamicPrioritySchemes.TASKSEMIDYNAMICPRIORITYSCHEMES_LOWRES_FIRST    
        SimParams.COMBINED_MAPPING_AND_PRIASS   = TaskMappingAndPriAssCombinedSchemes.TASKMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_LOWCOMMUNICATION_V2
        
        random.seed(seed)
        np.random.seed(seed)
        print "----------------------------------------------------------------------------------------------------------------------------"
        print "Running runSim_Scenario_V1 (NOCAC_LUM): num_wf=" + str(SimParams.NUM_WORKFLOWS) + \
                ", noc_h="+str(SimParams.NOC_H)+","+"noc_w="+str(SimParams.NOC_W) + \
                ", mapping="+str(SimParams.DYNAMIC_TASK_MAPPING_SCHEME) + \
                ", pri_ass="+str(SimParams.DYNAMIC_TASK_PRIASS_SCHEME) + \
                ", combined="+str(SimParams.COMBINED_MAPPING_AND_PRIASS) 
        print "----------------------------------------------------------------------------------------------------------------------------"
                
        env, last_scheduled_task_time = MMMSim.runMainSimulation()
        env.run(until=last_scheduled_task_time+SimParams.SIM_RUNTIME)
        print env.now        
        
        FNAME_PREFIX = SCENARIO_ID+"NOAC_LUM_"+str(SimParams.NOC_H)+"_"+str(SimParams.NOC_W)+"_"
        
        # get filenames
        filenames = _get_fname(EXP_DATADIR+scenario_exp_folder, FNAME_PREFIX)        
        # name the report filenames
        _dump_captured_data(filenames)
        
        
        

    if(run_schedac_lum==True):
        ####################################
        #### SCHED_ONLY AC - LU Mapping ####
        ####################################
        SimParams.AC_TEST_OPTION                = AdmissionControllerOptions.AC_OPTION_SCHEDTEST_DIRECT_TO_CRITICALPATH_WITHMMC
        SimParams.DYNAMIC_TASK_MAPPING_SCHEME   = TaskMappingSchemes.TASKMAPPINGSCHEMES_LOWEST_UTILISATION
        SimParams.DYNAMIC_TASK_PRIASS_SCHEME    = TaskSemiDynamicPrioritySchemes.TASKSEMIDYNAMICPRIORITYSCHEMES_LOWRES_FIRST    
        SimParams.COMBINED_MAPPING_AND_PRIASS   = TaskMappingAndPriAssCombinedSchemes.TASKMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_LOWCOMMUNICATION_V2
        
        random.seed(seed)
        np.random.seed(seed)
        print "----------------------------------------------------------------------------------------------------------------------------"
        print "Running runSim_Scenario_V1 (SCHEDONLYAC_LUM): num_wf=" + str(SimParams.NUM_WORKFLOWS) + \
                ", noc_h="+str(SimParams.NOC_H)+","+"noc_w="+str(SimParams.NOC_W) + \
                ", mapping="+str(SimParams.DYNAMIC_TASK_MAPPING_SCHEME) + \
                ", pri_ass="+str(SimParams.DYNAMIC_TASK_PRIASS_SCHEME) + \
                ", combined="+str(SimParams.COMBINED_MAPPING_AND_PRIASS) 
        print "----------------------------------------------------------------------------------------------------------------------------"
                
        env, last_scheduled_task_time = MMMSim.runMainSimulation()
        env.run(until=last_scheduled_task_time+SimParams.SIM_RUNTIME)
        print env.now        
        
        FNAME_PREFIX = SCENARIO_ID+"SCHEDONLYAC_LUM_"+str(SimParams.NOC_H)+"_"+str(SimParams.NOC_W)+"_"
        
        # get filenames
        filenames = _get_fname(EXP_DATADIR+scenario_exp_folder, FNAME_PREFIX)        
        # name the report filenames
        _dump_captured_data(filenames)

    

    if(run_noac_improvedm==True):
        ##################################
        #### No AC - Improved Mapping ####
        ##################################
        SimParams.AC_TEST_OPTION                = AdmissionControllerOptions.AC_OPTION_NONE_WITH_SCHEDTEST_WITHMMC
        SimParams.DYNAMIC_TASK_MAPPING_SCHEME   = TaskMappingSchemes.TASKMAPPINGSCHEMES_SHORTEST_TQ_VIARUNTIMEAPP
        SimParams.DYNAMIC_TASK_PRIASS_SCHEME    = TaskSemiDynamicPrioritySchemes.TASKSEMIDYNAMICPRIORITYSCHEMES_LOWRES_FIRST    
        SimParams.COMBINED_MAPPING_AND_PRIASS   = TaskMappingAndPriAssCombinedSchemes.TASKMAPPINGANDPRIASSCOMBINED_DISABLED
        
        random.seed(seed)
        np.random.seed(seed)
        print "----------------------------------------------------------------------------------------------------------------------------"
        print "Running runSim_Scenario_V1 (NOCAC_IMPROVEDM): num_wf=" + str(SimParams.NUM_WORKFLOWS) + \
                ", noc_h="+str(SimParams.NOC_H)+","+"noc_w="+str(SimParams.NOC_W) + \
                ", mapping="+str(SimParams.DYNAMIC_TASK_MAPPING_SCHEME) + \
                ", pri_ass="+str(SimParams.DYNAMIC_TASK_PRIASS_SCHEME) + \
                ", combined="+str(SimParams.COMBINED_MAPPING_AND_PRIASS) 
        print "----------------------------------------------------------------------------------------------------------------------------"
                
        env, last_scheduled_task_time = MMMSim.runMainSimulation()
        env.run(until=last_scheduled_task_time+SimParams.SIM_RUNTIME)
        print env.now        
        
        FNAME_PREFIX = SCENARIO_ID+"NOCAC_IMPROVEDM_"+str(SimParams.NOC_H)+"_"+str(SimParams.NOC_W)+"_"
        
        # get filenames
        filenames = _get_fname(EXP_DATADIR+scenario_exp_folder, FNAME_PREFIX)        
        # name the report filenames
        _dump_captured_data(filenames)
        


    if(run_schedac_improvedm==True):
        ##########################################
        #### SCHED_ONLY AC - Improved Mapping ####
        ##########################################
        SimParams.AC_TEST_OPTION                = AdmissionControllerOptions.AC_OPTION_SCHEDTEST_DIRECT_TO_CRITICALPATH_WITHMMC
        SimParams.DYNAMIC_TASK_MAPPING_SCHEME   = TaskMappingSchemes.TASKMAPPINGSCHEMES_SHORTEST_TQ_VIARUNTIMEAPP
        SimParams.DYNAMIC_TASK_PRIASS_SCHEME    = TaskSemiDynamicPrioritySchemes.TASKSEMIDYNAMICPRIORITYSCHEMES_LOWRES_FIRST    
        SimParams.COMBINED_MAPPING_AND_PRIASS   = TaskMappingAndPriAssCombinedSchemes.TASKMAPPINGANDPRIASSCOMBINED_DISABLED
        
        random.seed(seed)
        np.random.seed(seed)
        print "----------------------------------------------------------------------------------------------------------------------------"
        print "Running runSim_Scenario_V1 (SCHEDONLYAC_IMPROVEDM): num_wf=" + str(SimParams.NUM_WORKFLOWS) + \
                ", noc_h="+str(SimParams.NOC_H)+","+"noc_w="+str(SimParams.NOC_W) + \
                ", mapping="+str(SimParams.DYNAMIC_TASK_MAPPING_SCHEME) + \
                ", pri_ass="+str(SimParams.DYNAMIC_TASK_PRIASS_SCHEME) + \
                ", combined="+str(SimParams.COMBINED_MAPPING_AND_PRIASS) 
        print "----------------------------------------------------------------------------------------------------------------------------"
                
        env, last_scheduled_task_time = MMMSim.runMainSimulation()
        env.run(until=last_scheduled_task_time+SimParams.SIM_RUNTIME)
        print env.now        
        
        FNAME_PREFIX = SCENARIO_ID+"SCHEDONLYAC_IMPROVEDM_"+str(SimParams.NOC_H)+"_"+str(SimParams.NOC_W)+"_"
        
        # get filenames
        filenames = _get_fname(EXP_DATADIR+scenario_exp_folder, FNAME_PREFIX)        
        # name the report filenames
        _dump_captured_data(filenames)



###################################################################################################
#        SCENARIO based runsim for4 different types of ACtests and mappers - COMPACT
###################################################################################################
def runSim_Scenario_v2(                       
                       forced_seed = None,
                       scenario_exp_folder = None,
                       scenario_id = None,
                       dvb_resolutions = None,
                       dvb_resolutions_fixed = [],
                       dvb_resolutions_selected_random=True,
                       num_workflows = None,                       
                       run_noac_lum = True,
                       run_schedac_lum  = True,
                       run_noac_improvedm = True,
                       run_schedac_improvedm = True,
                       
                       ):
    
    seed = forced_seed    
    
    SCENARIO_ID = scenario_id
    
    print "SEED === " + str(seed)    
             
    # fixed params
    SimParams.SLACK_FEEDBACK_ENABLED = False
    
    SimParams.NOC_W = 3
    SimParams.NOC_H = 3
    SimParams.NUM_NODES = (SimParams.NOC_W * SimParams.NOC_H)
    SimParams.LOCAL_SCHEDULER_TYPE = LocalMPEG2FramePriorityScheduler_WithDepCheck()
    SimParams.SIM_ENTITY_RESOURCEMANAGER_CLASS    = RMTypes.OPENLOOP
    SimParams.SIM_ENTITY_CPUNODE_CLASS            = CPUTypes.OPENLOOP
    SimParams.SIM_ENTITY_MAPPER_CLASS             = MapperTypes.OPENLOOP
    SimParams.SIM_ENTITY_TASKDISPATCHER_CLASS     = TDTypes.OPENLOOP
    SimParams.DVB_RESOLUTIONS = dvb_resolutions
    SimParams.NUM_WORKFLOWS                 = num_workflows
    SimParams.NUM_INPUTBUFFERS              = SimParams.NUM_WORKFLOWS
    SimParams.DVB_RESOLUTIONS_FIXED         = dvb_resolutions_fixed
    SimParams.DVB_RESOLUTIONS_SELECTED_RANDOM        = dvb_resolutions_selected_random
        

    if(run_noac_lum == True):
        ############################
        #### No AC - LU Mapping ####
        ############################    
        SimParams.AC_TEST_OPTION                = AdmissionControllerOptions.AC_OPTION_NONE_WITH_SCHEDTEST_WITHMMC
        SimParams.DYNAMIC_TASK_MAPPING_SCHEME   = TaskMappingSchemes.TASKMAPPINGSCHEMES_LOWEST_UTILISATION
        SimParams.DYNAMIC_TASK_PRIASS_SCHEME    = TaskSemiDynamicPrioritySchemes.TASKSEMIDYNAMICPRIORITYSCHEMES_LOWRES_FIRST    
        SimParams.COMBINED_MAPPING_AND_PRIASS   = TaskMappingAndPriAssCombinedSchemes.TASKMAPPINGANDPRIASSCOMBINED_DISABLED
        
        random.seed(seed)
        np.random.seed(seed)
        print "----------------------------------------------------------------------------------------------------------------------------"
        print "Running runSim_Scenario_V1 (NOCAC_LUM): num_wf=" + str(SimParams.NUM_WORKFLOWS) + \
                ", noc_h="+str(SimParams.NOC_H)+","+"noc_w="+str(SimParams.NOC_W) + \
                ", mapping="+str(SimParams.DYNAMIC_TASK_MAPPING_SCHEME) + \
                ", pri_ass="+str(SimParams.DYNAMIC_TASK_PRIASS_SCHEME) + \
                ", combined="+str(SimParams.COMBINED_MAPPING_AND_PRIASS) 
        print "----------------------------------------------------------------------------------------------------------------------------"
                
        env, last_scheduled_task_time = MMMSim.runMainSimulation()
        env.run(until=last_scheduled_task_time+SimParams.SIM_RUNTIME)
        print env.now        
        
        FNAME_PREFIX = SCENARIO_ID+"NOAC_LUM_"+str(SimParams.NOC_H)+"_"+str(SimParams.NOC_W)+"_"
        
        # get filenames
        filenames = _get_fname(EXP_DATADIR+scenario_exp_folder, FNAME_PREFIX)        
        # name the report filenames
        _dump_captured_data(filenames)
        
        
        

    if(run_schedac_lum==True):
        ####################################
        #### SCHED_ONLY AC - LU Mapping ####
        ####################################
        SimParams.AC_TEST_OPTION                = AdmissionControllerOptions.AC_OPTION_SCHEDTEST_DIRECT_TO_CRITICALPATH_WITHMMC
        SimParams.DYNAMIC_TASK_MAPPING_SCHEME   = TaskMappingSchemes.TASKMAPPINGSCHEMES_LOWEST_UTILISATION
        SimParams.DYNAMIC_TASK_PRIASS_SCHEME    = TaskSemiDynamicPrioritySchemes.TASKSEMIDYNAMICPRIORITYSCHEMES_LOWRES_FIRST    
        SimParams.COMBINED_MAPPING_AND_PRIASS   = TaskMappingAndPriAssCombinedSchemes.TASKMAPPINGANDPRIASSCOMBINED_DISABLED
        
        random.seed(seed)
        np.random.seed(seed)
        print "----------------------------------------------------------------------------------------------------------------------------"
        print "Running runSim_Scenario_V1 (SCHEDONLYAC_LUM): num_wf=" + str(SimParams.NUM_WORKFLOWS) + \
                ", noc_h="+str(SimParams.NOC_H)+","+"noc_w="+str(SimParams.NOC_W) + \
                ", mapping="+str(SimParams.DYNAMIC_TASK_MAPPING_SCHEME) + \
                ", pri_ass="+str(SimParams.DYNAMIC_TASK_PRIASS_SCHEME) + \
                ", combined="+str(SimParams.COMBINED_MAPPING_AND_PRIASS) 
        print "----------------------------------------------------------------------------------------------------------------------------"
                
        env, last_scheduled_task_time = MMMSim.runMainSimulation()
        env.run(until=last_scheduled_task_time+SimParams.SIM_RUNTIME)
        print env.now        
        
        FNAME_PREFIX = SCENARIO_ID+"SCHEDONLYAC_LUM_"+str(SimParams.NOC_H)+"_"+str(SimParams.NOC_W)+"_"
        
        # get filenames
        filenames = _get_fname(EXP_DATADIR+scenario_exp_folder, FNAME_PREFIX)        
        # name the report filenames
        _dump_captured_data(filenames)

    

    if(run_noac_improvedm==True):
        ##################################
        #### No AC - Improved Mapping ####
        ##################################
        SimParams.AC_TEST_OPTION                = AdmissionControllerOptions.AC_OPTION_NONE_WITH_SCHEDTEST_WITHMMC
        SimParams.DYNAMIC_TASK_MAPPING_SCHEME   = TaskMappingSchemes.TASKMAPPINGSCHEMES_LOWEST_UTILISATION
        SimParams.DYNAMIC_TASK_PRIASS_SCHEME    = TaskSemiDynamicPrioritySchemes.TASKSEMIDYNAMICPRIORITYSCHEMES_LOWRES_FIRST    
        SimParams.COMBINED_MAPPING_AND_PRIASS   = TaskMappingAndPriAssCombinedSchemes.TASKMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_TIGHTFIT_V1
        
        random.seed(seed)
        np.random.seed(seed)
        print "----------------------------------------------------------------------------------------------------------------------------"
        print "Running runSim_Scenario_V1 (NOCAC_IMPROVEDM): num_wf=" + str(SimParams.NUM_WORKFLOWS) + \
                ", noc_h="+str(SimParams.NOC_H)+","+"noc_w="+str(SimParams.NOC_W) + \
                ", mapping="+str(SimParams.DYNAMIC_TASK_MAPPING_SCHEME) + \
                ", pri_ass="+str(SimParams.DYNAMIC_TASK_PRIASS_SCHEME) + \
                ", combined="+str(SimParams.COMBINED_MAPPING_AND_PRIASS) 
        print "----------------------------------------------------------------------------------------------------------------------------"
                
        env, last_scheduled_task_time = MMMSim.runMainSimulation()
        env.run(until=last_scheduled_task_time+SimParams.SIM_RUNTIME)
        print env.now        
        
        FNAME_PREFIX = SCENARIO_ID+"NOCAC_IMPROVEDM_"+str(SimParams.NOC_H)+"_"+str(SimParams.NOC_W)+"_"
        
        # get filenames
        filenames = _get_fname(EXP_DATADIR+scenario_exp_folder, FNAME_PREFIX)        
        # name the report filenames
        _dump_captured_data(filenames)
        


    if(run_schedac_improvedm==True):
        ##########################################
        #### SCHED_ONLY AC - Improved Mapping ####
        ##########################################
        SimParams.AC_TEST_OPTION                = AdmissionControllerOptions.AC_OPTION_SCHEDTEST_DIRECT_TO_CRITICALPATH_WITHMMC
        SimParams.DYNAMIC_TASK_MAPPING_SCHEME   = TaskMappingSchemes.TASKMAPPINGSCHEMES_LOWEST_UTILISATION
        SimParams.DYNAMIC_TASK_PRIASS_SCHEME    = TaskSemiDynamicPrioritySchemes.TASKSEMIDYNAMICPRIORITYSCHEMES_LOWRES_FIRST    
        SimParams.COMBINED_MAPPING_AND_PRIASS   = TaskMappingAndPriAssCombinedSchemes.TASKMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_TIGHTFIT_V1
        
        random.seed(seed)
        np.random.seed(seed)
        print "----------------------------------------------------------------------------------------------------------------------------"
        print "Running runSim_Scenario_V1 (SCHEDONLYAC_IMPROVEDM): num_wf=" + str(SimParams.NUM_WORKFLOWS) + \
                ", noc_h="+str(SimParams.NOC_H)+","+"noc_w="+str(SimParams.NOC_W) + \
                ", mapping="+str(SimParams.DYNAMIC_TASK_MAPPING_SCHEME) + \
                ", pri_ass="+str(SimParams.DYNAMIC_TASK_PRIASS_SCHEME) + \
                ", combined="+str(SimParams.COMBINED_MAPPING_AND_PRIASS) 
        print "----------------------------------------------------------------------------------------------------------------------------"
                
        env, last_scheduled_task_time = MMMSim.runMainSimulation()
        env.run(until=last_scheduled_task_time+SimParams.SIM_RUNTIME)
        print env.now        
        
        FNAME_PREFIX = SCENARIO_ID+"SCHEDONLYAC_IMPROVEDM_"+str(SimParams.NOC_H)+"_"+str(SimParams.NOC_W)+"_"
        
        # get filenames
        filenames = _get_fname(EXP_DATADIR+scenario_exp_folder, FNAME_PREFIX)        
        # name the report filenames
        _dump_captured_data(filenames)



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
    SimParams.DVB_RESOLUTIONS                     = res_list
    SimParams.DVB_RESOLUTIONS_SELECTED_RANDOM     = True
    SimParams.CPU_EXEC_SPEED_RATIO = 0.8
    SimParams.NOC_PERIOD           =  0.0000001 #10 mhz
    #SimParams.NOC_PERIOD           =  0.00000142 #.7 mhz
    SimParams.WFGEN_MIN_GOPS_PER_VID = 200 
    SimParams.WFGEN_MAX_GOPS_PER_VID = 200  
    
    SimParams.AC_TEST_OPTION                = ac_type
    SimParams.DYNAMIC_TASK_MAPPING_SCHEME   = mp_type
    SimParams.DYNAMIC_TASK_PRIASS_SCHEME    = pr_type    
    SimParams.COMBINED_MAPPING_AND_PRIASS   = cmbmppri_type
    
    # non-hevc stuff
    SimParams.HEVC_TILELEVEL_SPLITTING_ENABLE = False
    SimParams.TASK_MODEL                      = TaskModel.TASK_MODEL_MHEG2_FRAME_ET_LEVEL
    SimParams.HEVC_GOPGEN_USEPROBABILISTIC_MODEL = False
    SimParams.TASKSET_MODEL = TaskModel.TASK_MODEL_MHEG2_FRAME_ET_LEVEL
    
    
    sub_exp_dir = "multiseed_random_res/"
    #subdir = "ac"+str(ac_type)+"mp"+str(mp_type)+"pr"+str(pr_type)+"cmb"+str(cmbmppri_type)+"/"
    subdir = "seed_"+str(seed) +"/" 
    FNAME_PREFIX = fname_prefix+str(SimParams.NOC_H)+"_"+str(SimParams.NOC_W)+"_"
    check_fname = _get_fname(EXP_DATADIR+sub_exp_dir+subdir, FNAME_PREFIX)['utilvsschedresults_fname']
    
    print "Checking file exists : " + str(check_fname)
    
    if(_check_file_exists(check_fname) == True):
        print "Simulation already exists.."
    else:
        
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
        
        env, last_scheduled_task_time = MMMSim.runMainSimulation()
        env.run(until=last_scheduled_task_time+SimParams.SIM_RUNTIME)
        print env.now        
        
        FNAME_PREFIX = fname_prefix+str(SimParams.NOC_H)+"_"+str(SimParams.NOC_W)+"_"
        
        _makeDir(EXP_DATADIR+sub_exp_dir+subdir)
        
        # get filenames
        filenames = _get_fname(EXP_DATADIR+sub_exp_dir+subdir, FNAME_PREFIX)        
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
            "utilvsschedresults_fname" : utilvsschedresults_fname          
        }
    
    return result 
    
def _check_file_exists(fname):
    return os.path.exists(fname)

def _dump_captured_data(filenames):
    (wf_results_summary, gops_in_outputbuff_summary) = MMMSim.SimMon.report_DecodedWorkflows_Summary(timeline_fname=filenames["tm_fname"], 
                                                                                                         wf_res_summary_fname = filenames["wf_res_fname"], 
                                                                                                        gops_opbuff_summary_fname = filenames["gops_opbuff_fname"],
                                                                                                        rmtbl_dt_summary_fname = filenames["rmtbl_dt_fname"],
                                                                                                        output_format = "json")
        
    MMMSim.SimMon.report_VideoStream_BasicStats(wf_results_summary, filenames["vs_bs_fname"])
    MMMSim.SimMon.report_InstUtilisation(dump_to_file=filenames["util_fname"])
    MMMSim.SimMon.report_InputBuffer(dump_to_file=filenames["ibuff_fname"])
    MMMSim.SimMon.report_NodeTQs(dump_to_file=filenames["nodetqs_fname"])
    MMMSim.SimMon.report_OutputBufferContents(dump_to_file=filenames["obuff_fname"])    
    MMMSim.SimMon.report_FlowsCompleted(dump_to_file=filenames["flowscompleted_fname"])
    MMMSim.SimMon.report_NodeTaskExecTimeline(dump_to_file=filenames["nodetaskexectime_fname"])
    MMMSim.SimMon.report_WCRT_TasksAndFlows_viaSchedAnalysis(dump_to_file=filenames["schedtestresults_fname"])
    MMMSim.SimMon.report_MappingAndPriAssInfo(dump_to_file=filenames["mappingandpriass_fname"])
    



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

parser.add_argument("--forced_seed", help="seed", type=int, default=-1)
args = parser.parse_args()



####################################
## check which experiment to run ##
####################################
#runSim_Simple()


mapping_types = [(10,4,0), (10,4,840), (10,4,841)]

### scenario - 1 : low res , 6 streams
# runSim_Scenario(
#                    forced_seed = 99108,
#                    scenario_exp_folder = "scenario_1/",
#                    scenario_id = "SCV1_",
#                    dvb_resolutions = [],
#                    dvb_resolutions_fixed = [(320,240),(240,180),(230,180),(230,173),(176,132)],
#                    dvb_resolutions_selected_random=False,
#                    num_workflows = 5,
#                    run_noac_lum = True,
#                    run_schedac_lum  = True,
#                    run_noac_improvedm = True,
#                    run_schedac_improvedm = True,
#                    )
#     
# # # ### scenario - 2 : med res , 3 streams
# runSim_Scenario(
#                    forced_seed = 99108,
#                    scenario_exp_folder = "scenario_2/",
#                    scenario_id = "SCV2_",
#                    dvb_resolutions = [],
#                    dvb_resolutions_fixed = [(480,576),(426,240),(320,240)],
#                    dvb_resolutions_selected_random=False,
#                    num_workflows = 3,
#                    run_noac_lum=True,
#                    run_schedac_lum  = True,
#                    run_noac_improvedm = True,
#                    run_schedac_improvedm = True,
#                    )
#   
# # # ### scenario - 3 : med res , 3 streams
# runSim_Scenario(
#                    forced_seed = 99108,
#                    scenario_exp_folder = "scenario_3/",
#                    scenario_id = "SCV3_",
#                    dvb_resolutions = [],
#                    dvb_resolutions_fixed = [(720,576),(528,576),(480,576)],
#                    dvb_resolutions_selected_random=False,
#                    num_workflows = 2,
#                    run_noac_lum = True,
#                    run_schedac_lum  = True,
#                    run_noac_improvedm = True,
#                    run_schedac_improvedm = True,
#                    )

# # ### scenario - 4 : med res , 4 streams
# runSim_Scenario(
#                    forced_seed = 99108,
#                    scenario_exp_folder = "scenario_4/",
#                    scenario_id = "SCV4_",
#                    dvb_resolutions = [],
#                    dvb_resolutions_fixed = [(230,173),(176,132),(426,240),(528,576), (426,240), (320,240), (320,240), (176,132)],
#                    dvb_resolutions_selected_random=False,
#                    num_workflows = 6,
#                    run_noac_lum = True,
#                    run_schedac_lum  = True,
#                    run_noac_improvedm = True,
#                    run_schedac_improvedm = True,
#                    )

types_of_tests = [                      
                    ## Deterministic - AC ##

                    #{'ac':11, 'mp':0, 'pr':4, 'cmb':840 }, # determ, lumm
                    #{'ac':12, 'mp':13, 'pr':4, 'cmb':0 , 'lbl': "Custom"}, # determ, improved
                    {'ac':12, 'mp':0, 'pr':4, 'cmb':841 , 'lbl': "IPC"}, # determ, improved
                    {'ac':12, 'mp':0, 'pr':4, 'cmb':842 , 'lbl': "LWCRS"}, # determ, improved
                    #{'ac':12, 'mp':0, 'pr':4, 'cmb':832 , 'lbl': "BN"}, # determ, improved
                    {'ac':12, 'mp':0, 'pr':4, 'cmb':833 , 'lbl': "PP"}, # determ, improved
                    {'ac':12, 'mp':0, 'pr':4, 'cmb':834 , 'lbl': "BN"}, # determ, improved                   
                            
                    {'ac':12, 'mp':10, 'pr':4, 'cmb':0 , 'lbl': "LU"}, # determ, improved
                    {'ac':12, 'mp':12, 'pr':4, 'cmb':0 , 'lbl': "LM"}, # determ, improved
                      
                      ]

for each_test_type in types_of_tests:
    final_fname_prefix = "HRTVid_" + \
                     "AC"+ str(each_test_type['ac']) + "_" + \
                     "MP"+ str(each_test_type['mp']) + "_" + \
                     "PR"+ str(each_test_type['pr']) + "_" + \
                     "CMB"+ str(each_test_type['cmb']) + "_"

    runSim_AC_MP_Type(                       
                           forced_seed = args.forced_seed,                       
                           fname_prefix=final_fname_prefix,
                           ac_type=each_test_type['ac'],
                           mp_type=each_test_type['mp'],
                           pr_type=each_test_type['pr'],
                           num_wfs=2,
                           #res_list=[(544,576), (528,576), (480,576), (426,240), (320,240), (240,180), (230,180)],
                           #res_list=[(720,576), (544,576), (528,576), (480,576), (426,240), (320,240), (240,180)],
                           res_list=[(720,576), (230,180)],
                           #res_list=[(1280,720), (230,180)],
                           
                           cmbmppri_type=each_test_type['cmb'],
                           )




