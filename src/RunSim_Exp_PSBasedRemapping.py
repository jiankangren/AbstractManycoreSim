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
from libApplicationModel.Task import TaskModel

from SimParams import SimParams


import Multicore_MPEG_Model as MMMSim


NUM_WORKFLOWS = range(8, 17, 2)
#NUM_WORKFLOWS = [12]
NUM_NODES = [2,4,8,16,32]
NOC_XY = [(2,1), (2,2), (2,4), (2,8), (2,16)]


# simple ps-remapping test
def runSim_Simple():
    
    seed = 99108    
    
    print "SEED === " + str(seed)    
             
    # fixed params
    SimParams.NOC_W = 4
    SimParams.NOC_H = 4
    SimParams.NUM_NODES = (SimParams.NOC_W * SimParams.NOC_H)
    SimParams.NUM_WORKFLOWS = SimParams.NUM_NODES * 2
    SimParams.NUM_INPUTBUFFERS = SimParams.NUM_WORKFLOWS
    SimParams.PSALGO_ENABLED = True
    SimParams.PSALGO_VIEWER_ENABLED = False
    SimParams.DYNAMIC_TASK_REMAPPING_ENABLED = True
    SimParams.DYNAMIC_TASK_REMAPPING_SCHEME = TaskRemapDecentSchemes.TASKREMAPPINGDECENTSCHEMES_RANDOM_QUEEN
    SimParams.CPUNODE_MONITOR_TASKSET_SLACK = True
    SimParams.LOCAL_SCHEDULER_TYPE = LocalMPEG2FramePriorityScheduler_WithDepCheck()
    SimParams.SIM_ENTITY_RESOURCEMANAGER_CLASS    = RMTypes.OPENLOOP
    SimParams.SIM_ENTITY_CPUNODE_CLASS            = CPUTypes.OPENLOOP
    SimParams.SIM_ENTITY_MAPPER_CLASS             = MapperTypes.OPENLOOP
    SimParams.SIM_ENTITY_TASKDISPATCHER_CLASS     = TDTypes.OPENLOOP
    
    SimParams.TASK_MODEL                          = TaskModel.TASK_MODEL_MHEG2_FRAME_ET_LEVEL
    SimParams.TASKSET_MODEL = TaskModel.TASK_MODEL_MHEG2_FRAME_ET_LEVEL
    
    SimParams.COMBINED_MAPPING_AND_PRIASS = TaskMappingAndPriAssCombinedSchemes.TASKMAPPINGANDPRIASSCOMBINED_DISABLED
    SimParams.DYNAMIC_TASK_MAPPING_SCHEME = TaskMappingSchemes.TASKMAPPINGSCHEMES_LOWEST_UTILISATION
	
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
    
    
# remapping on/off experiment
def runSim_RemappingBasic(run_rm_off=True, run_rm_on=True, seed=1234, multiseeds=False, noc_w=10, noc_h=10):
       
    print "---SEED === " + str(seed)    
        
    ###############        
    # fixed params
    ###############
    SimParams.NOC_W = noc_w
    SimParams.NOC_H = noc_h
    SimParams.NUM_NODES = (SimParams.NOC_W * SimParams.NOC_H)
    SimParams.NUM_WORKFLOWS = SimParams.NUM_NODES + 3
    #SimParams.NUM_WORKFLOWS = 3
    SimParams.NUM_INPUTBUFFERS = SimParams.NUM_WORKFLOWS
    SimParams.LOCAL_SCHEDULER_TYPE = LocalMPEG2FramePriorityScheduler_WithDepCheck()
    SimParams.SIM_ENTITY_RESOURCEMANAGER_CLASS    = RMTypes.OPENLOOP
    SimParams.SIM_ENTITY_CPUNODE_CLASS            = CPUTypes.OPENLOOP
    SimParams.SIM_ENTITY_MAPPER_CLASS             = MapperTypes.OPENLOOP
    SimParams.SIM_ENTITY_TASKDISPATCHER_CLASS     = TDTypes.OPENLOOP
    SimParams.TASK_MODEL                          = TaskModel.TASK_MODEL_MHEG2_FRAME_ET_LEVEL    
    SimParams.TASKSET_MODEL = TaskModel.TASK_MODEL_MHEG2_FRAME_ET_LEVEL

#    SimParams.LOCAL_SCHEDULER_TYPE = LocalMPEG2FramePriorityScheduler()
#    SimParams.SIM_ENTITY_RESOURCEMANAGER_CLASS    = RMTypes.CLOSEDLOOP_WITH_IBUFFERING
#    SimParams.SIM_ENTITY_CPUNODE_CLASS            = CPUTypes.CLOSEDLOOP_WITH_IBUFFERING
#    SimParams.SIM_ENTITY_MAPPER_CLASS             = MapperTypes.CLOSEDLOOP_WITH_IBUFFERING
#    SimParams.SIM_ENTITY_TASKDISPATCHER_CLASS     = TDTypes.CLOSEDLOOP_WITH_IBUFFERING
    
    SimParams.COMBINED_MAPPING_AND_PRIASS = TaskMappingAndPriAssCombinedSchemes.TASKMAPPINGANDPRIASSCOMBINED_DISABLED
    SimParams.DYNAMIC_TASK_MAPPING_SCHEME = TaskMappingSchemes.TASKMAPPINGSCHEMES_LOWEST_UTILISATION
    SimParams.DYNAMIC_TASK_PRIASS_SCHEME =  TaskSemiDynamicPrioritySchemes.TASKSEMIDYNAMICPRIORITYSCHEMES_LOWRES_FIRST
    
    noc_size_dir = "noc_" + str(noc_w) + "x" + str(noc_h) + "/"    
    
    if(multiseeds==True):
        DATA_FOLDER = "experiment_data/remapping_psbased/"+"seed_"+str(seed)+"/"
    else:        
        #DATA_FOLDER = "experiment_data/remapping_psbased/"
        DATA_FOLDER = "experiment_data/remapping_nocsize/remapping_psbased/" + noc_size_dir
        
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
    rmdebuginfo_1      = "test__remappingdebuginfo_1.js"
    
    
    if(run_rm_off == True):
        ################################
        # PS-based Remapping disabled
        ################################
        SimParams.PSALGO_ENABLED = False
        SimParams.DYNAMIC_TASK_REMAPPING_ENABLED = False
        SimParams.DYNAMIC_TASK_REMAPPING_SCHEME = TaskRemapDecentSchemes.TASKREMAPPINGDECENTSCHEMES_NONE        
        SimParams.CPUNODE_MONITOR_TASKSET_SLACK = False
        SimParams.PSALGO_VIEWER_ENABLED = False
        SimParams.MMC_ENABLE_DATATRANSMISSION_MODELLING = False
        FNAME_PREFIX = DATA_FOLDER+"RMOFF_"
        random.seed(seed)
        np.random.seed(seed)
        print "----------------------------------------------------------------------------------------------------------------------------"
        print "Running runSim_RemappingBasic : num_wf=" + str(SimParams.NUM_WORKFLOWS) + \
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
        MMMSim.SimMon.report_FlowsCompleted(dump_to_file=FNAME_PREFIX+flowscompleted_fname)
        #MMMSim.SimMon.report_NodeTaskExecTimeline(dump_to_file=FNAME_PREFIX+nodetaskexectime_fname)
        MMMSim.SimMon.report_PSAlgoNodePSProps(dump_to_file=FNAME_PREFIX+psalgo_nodeprops)
        #MMMSim.SimMon.report_FlowsAdded(dump_to_file=FNAME_PREFIX+flowsadded_fname)
        MMMSim.SimMon.report_TaskRemappingInfo(dump_to_file=FNAME_PREFIX+trminfo_fname)
        MMMSim.SimMon.report_NodeCumSlack(dump_to_file=FNAME_PREFIX+nodecumslack_fname)        
        MMMSim.SimMon.report_NodeImportedTasks(dump_to_file=FNAME_PREFIX+node_importedtasks)
   
    
    if(run_rm_on == True): 
        ################################
        # PS-based Remapping enabled
        ################################
        SimParams.PSALGO_ENABLED = True
        SimParams.DYNAMIC_TASK_REMAPPING_ENABLED = True
        SimParams.DYNAMIC_TASK_REMAPPING_SCHEME = TaskRemapDecentSchemes.TASKREMAPPINGDECENTSCHEMES_LOWESTBLOCKING_QUEEN_VIA_SYSSLACK
        SimParams.CPUNODE_MONITOR_TASKSET_SLACK = True
        SimParams.PSALGO_VIEWER_ENABLED = True
        SimParams.MMC_ENABLE_DATATRANSMISSION_MODELLING = False
        SimParams.PSALGO_PSFLOWPAYLOADSIZE =16	

        
        # --------------------------------------------------------------------------------
        ## FOR MMC - enabled ##
        # params taken from mc-test : perm_0.22_0.0629_20.0_0.3_0.3_4.6_
        # perm_0.12_0.18_0.2_0.15_
        #SimParams.PSALGO_TQN = 0.22
        #SimParams.PSALGO_TDECAY = 0.0629
        #SimParams.PSALGO_THRESHOLDQN = 20.0
        #SimParams.PSALGO_THRESHOLDHOPCOUNT = 2        
        #SimParams.DYNAMIC_TASK_REMAPPING_SAMPLING_INTERVAL = 4.6
        #SimParams.PSALGO_HQN = 14
        #SimParams.PSALGO_DYNAMIC_THRESHOLDQN_RATIO = [0.12, 0.18]
        #SimParams.PSALGO_KHOPDECAY = 0.2
        #SimParams.PSALGO_KTIMEDECAY = 0.15        
        # --------------------------------------------------------------------------------
        
        # --------------------------------------------------------------------------------
        ## FOR MMC - disabled ##
        ## "param": "perm_0.1_0.025_3_6.9_5_0.203_0.3_0.15_0.05_"
        #SimParams.PSALGO_TQN = 0.1
        #SimParams.PSALGO_TDECAY = 0.025
        #SimParams.PSALGO_THRESHOLDQN = 9.0
        #SimParams.PSALGO_THRESHOLDHOPCOUNT = 3
        #SimParams.DYNAMIC_TASK_REMAPPING_SAMPLING_INTERVAL = 6.9
        #SimParams.PSALGO_HQN = 5
        #SimParams.PSALGO_DYNAMIC_THRESHOLDQN_RATIO = [0.203, 0.3]
        #SimParams.PSALGO_KHOPDECAY = 0.15
        #SimParams.PSALGO_KTIMEDECAY = 0.05
        # --------------------------------------------------------------------------------
     

        # --------------------------------------------------------------------------------
        ## FOR MMC - disabled ##
        ## perm_0.22_0.055_3_6.9_18_0.107_0.01_0.15_0.3_
        #SimParams.PSALGO_TQN = 0.22
        #SimParams.PSALGO_TDECAY = 0.055
        SimParams.PSALGO_TQN = 0.05
        SimParams.PSALGO_TDECAY = 0.025
        SimParams.PSALGO_THRESHOLDQN = 20.0
        SimParams.PSALGO_THRESHOLDHOPCOUNT = 3
        SimParams.DYNAMIC_TASK_REMAPPING_SAMPLING_INTERVAL = 6.9
        SimParams.PSALGO_HQN = 18
        SimParams.PSALGO_DYNAMIC_THRESHOLDQN_RATIO = [0.107, 0.01]
        SimParams.PSALGO_KHOPDECAY = 0.15
        SimParams.PSALGO_KTIMEDECAY = 0.3
        # --------------------------------------------------------------------------------


    
        FNAME_PREFIX = DATA_FOLDER+"RMON_"
        random.seed(seed)
        np.random.seed(seed)
        print "----------------------------------------------------------------------------------------------------------------------------"
        print "Running runSim_RemappingBasic : num_wf=" + str(SimParams.NUM_WORKFLOWS) + \
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
        MMMSim.SimMon.report_FlowsCompleted(dump_to_file=FNAME_PREFIX+flowscompleted_fname)
        MMMSim.SimMon.report_NodeTaskExecTimeline(dump_to_file=FNAME_PREFIX+nodetaskexectime_fname)
        MMMSim.SimMon.report_PSAlgoNodePSProps(dump_to_file=FNAME_PREFIX+psalgo_nodeprops)
        #MMMSim.SimMon.report_FlowsAdded(dump_to_file=FNAME_PREFIX+flowsadded_fname)
        MMMSim.SimMon.report_TaskRemappingInfo(dump_to_file=FNAME_PREFIX+trminfo_fname)
        MMMSim.SimMon.report_NodeCumSlack(dump_to_file=FNAME_PREFIX+nodecumslack_fname)        
        MMMSim.SimMon.report_NodeImportedTasks(dump_to_file=FNAME_PREFIX+node_importedtasks)
        MMMSim.SimMon.report_PSRemappDebugInfo_1(dump_to_file=FNAME_PREFIX+rmdebuginfo_1)
   
    
# remapping on full fact params test
def runSim_RemappingFullFactParams(run_rm_off=True, run_rm_on=True, seed=77379, multiseeds=False,
                                   each_tqn = None,
                                   param_thresholdqn = None,
                                   param_thrhc = None,
                                   param_remapperiod = None,
                                   param_dynthrqnratinc = None,
                                   param_dynthrqnratdec = None
                                   ):
       
    print "SEED === " + str(seed)    
        
    ###############        
    # fixed params
    ###############
    SimParams.NOC_W = 4
    SimParams.NOC_H = 4
    SimParams.NUM_NODES = (SimParams.NOC_W * SimParams.NOC_H)
    SimParams.NUM_WORKFLOWS = SimParams.NUM_NODES + 1
    SimParams.NUM_INPUTBUFFERS = SimParams.NUM_WORKFLOWS
    
    if(multiseeds==True):
        DATA_FOLDER = "experiment_data/remapping_psbased_fullfactorial/"+"seed_"+str(seed)+"/"
    else:        
        DATA_FOLDER = "experiment_data/remapping_psbased_fullfactorial/"
    
    
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
    
    
    if(run_rm_off == True):
        ################################
        # PS-based Remapping disabled
        ################################
        SimParams.PSALGO_ENABLED = False
        SimParams.DYNAMIC_TASK_REMAPPING_ENABLED = False
        SimParams.DYNAMIC_TASK_REMAPPING_SCHEME = TaskRemapDecentSchemes.TASKREMAPPINGDECENTSCHEMES_LOWESTBLOCKING_QUEEN_VIA_SYSSLACK
        SimParams.CPUNODE_MONITOR_TASKSET_SLACK = False
        SimParams.PSALGO_VIEWER_ENABLED = False
        FNAME_PREFIX = DATA_FOLDER+"RMOFF_"
        random.seed(seed)
        np.random.seed(seed)
        print "----------------------------------------------------------------------------------------------------------------------------"
        print "Running runSim_RemappingBasic : num_wf=" + str(SimParams.NUM_WORKFLOWS) + \
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
        
        
        MMMSim.SimMon.report_OutputBufferContents(dump_to_file=FNAME_PREFIX+obuff_fname)
        MMMSim.SimMon.report_TaskRemappingInfo(dump_to_file=FNAME_PREFIX+trminfo_fname)
        MMMSim.SimMon.report_PSAlgoNodePSProps(dump_to_file=FNAME_PREFIX+psalgo_nodeprops)
        
    if(run_rm_on == True):
        ################################
        # PS-based Remapping enabled
        ################################
        
        SimParams.PSALGO_ENABLED = True
        SimParams.DYNAMIC_TASK_REMAPPING_ENABLED = True
        SimParams.DYNAMIC_TASK_REMAPPING_SCHEME = TaskRemapDecentSchemes.TASKREMAPPINGDECENTSCHEMES_LOWESTBLOCKING_QUEEN_VIA_SYSSLACK
        SimParams.CPUNODE_MONITOR_TASKSET_SLACK = True
        SimParams.PSALGO_VIEWER_ENABLED = False
        FNAME_PREFIX = DATA_FOLDER+"RMON_"
        
        TQN = [0.072, 0.24, 0.48, 0.96]    
        THRESHOLDQN = [2.0, 9.0, 15.0]
        REMAP_PERIOD = [float(SimParams.FR25_GOPLEN12_E2EDEADLINE * 1.98),
                        float(SimParams.FR25_GOPLEN12_E2EDEADLINE * 2.98), 
                        float(SimParams.FR25_GOPLEN12_E2EDEADLINE * 4.98)]
        THRESHOLDHOPCOUNT = [2,5,8]
        DYN_THRQN_RATIO_INC = [0.1, 0.5, 0.7]
        DYN_THRQN_RATIO_DEC = [0.1, 0.5, 0.7]
        
        # loop through all permutations of the params
        for each_tqn in TQN:
            for each_thresholdqn in THRESHOLDQN:              
                    for each_remapperiod in REMAP_PERIOD:    
                        for each_thrhc in THRESHOLDHOPCOUNT:
                            for each_dynthrqnratinc in DYN_THRQN_RATIO_INC:
                                for each_dynthrqnratdec in DYN_THRQN_RATIO_DEC:                            
                                                                        
                                    # set params                                            
                                    SimParams.PSALGO_TQN                                            = each_tqn           
                                    SimParams.PSALGO_TDECAY                                         = float(each_tqn/2.5)               
                                    SimParams.PSALGO_THRESHOLDQN                                    = each_thresholdqn                                
                                    SimParams.PSALGO_THRESHOLDHOPCOUNT                              = each_thrhc
                                    SimParams.DYNAMIC_TASK_REMAPPING_SAMPLING_INTERVAL              = each_remapperiod
                                    SimParams.PSALGO_DYNAMIC_THRESHOLDQN_RATIO                      = [each_dynthrqnratinc, each_dynthrqnratdec]
                                    
                                    fname_param_prefix = FNAME_PREFIX + str(each_tqn) + \
                                                            "_" + str(each_thresholdqn) + \
                                                            "_" + str(each_thrhc) + \
                                                            "_" + str(each_remapperiod) + \
                                                            "_" + str(each_dynthrqnratinc) + \
                                                            "_" + str(each_dynthrqnratdec) + "_"
                                                            
                                    
                                    # check if the simulation has run already before continuing
                                    check_fname = fname_param_prefix+tm_fname 
                                    print "Checking file exists : " + str(check_fname)
                                    if(_check_file_exists(check_fname) == True):
                                        print "Simulation already exists ! "
                                    else:
                                    
                                        random.seed(seed)
                                        np.random.seed(seed)
                                        print "----------------------------------------------------------------------------------------------------------------------------"
                                        print "Running runSim_Simple : num_wf=" + str(SimParams.NUM_WORKFLOWS) + \
                                                ", Remapping_enabled"
                                        print fname_param_prefix
                                        print "----------------------------------------------------------------------------------------------------------------------------"
                                                
                                        env, last_scheduled_task_time = MMMSim.runMainSimulation()
                                        env.run(until=last_scheduled_task_time+SimParams.SIM_RUNTIME)
                                        print env.now        
                                        
                                        (wf_results_summary, gops_in_outputbuff_summary) = MMMSim.SimMon.report_DecodedWorkflows_Summary(timeline_fname         =fname_param_prefix+tm_fname, 
                                                                                                                                         wf_res_summary_fname   = fname_param_prefix+wf_res_fname, 
                                                                                                                                        gops_opbuff_summary_fname = fname_param_prefix+gops_opbuff_fname,
                                                                                                                                        rmtbl_dt_summary_fname    = fname_param_prefix+rmtbl_dt_fname,
                                                                                                                                        output_format = "json")
                                        
                                        MMMSim.SimMon.report_OutputBufferContents(dump_to_file=fname_param_prefix+obuff_fname)
                                        MMMSim.SimMon.report_TaskRemappingInfo(dump_to_file=fname_param_prefix+trminfo_fname)
                                        MMMSim.SimMon.report_PSAlgoNodePSProps(dump_to_file=fname_param_prefix+psalgo_nodeprops)
    
            
   



# remapping on full fact params test
def runSim_RemappingMonteCarloParamsTest(run_rm_off=True, run_rm_on=True, seed=77379, multiseeds=False):
       
    print "SEED === " + str(seed)    
        
    ###############        
    # fixed params
    ###############
    SimParams.NOC_W = 4
    SimParams.NOC_H = 4
    SimParams.NUM_NODES = (SimParams.NOC_W * SimParams.NOC_H)
    SimParams.NUM_WORKFLOWS = SimParams.NUM_NODES + 1
    SimParams.NUM_INPUTBUFFERS = SimParams.NUM_WORKFLOWS
    
    if(multiseeds==True):
        DATA_FOLDER = "experiment_data/remapping_psbased_montecarlo/"+"seed_"+str(seed)+"/"
    else:        
        DATA_FOLDER = "experiment_data/remapping_psbased_montecarlo/"
    
    
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
    
    
    ################################
    # PS-based Remapping disabled
    ################################
    SimParams.PSALGO_ENABLED = False
    SimParams.DYNAMIC_TASK_REMAPPING_ENABLED = False
    SimParams.DYNAMIC_TASK_REMAPPING_SCHEME = TaskRemapDecentSchemes.TASKREMAPPINGDECENTSCHEMES_RANDOM_QUEEN
    SimParams.CPUNODE_MONITOR_TASKSET_SLACK = False
    SimParams.PSALGO_VIEWER_ENABLED = False
    FNAME_PREFIX = DATA_FOLDER+"RMOFF_"
    random.seed(seed)
    np.random.seed(seed)
    print "----------------------------------------------------------------------------------------------------------------------------"
    print "Running runSim_RemappingBasic : num_wf=" + str(SimParams.NUM_WORKFLOWS) + \
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
    #MMMSim.SimMon.report_PSAlgoNodePSProps(dump_to_file=FNAME_PREFIX+psalgo_nodeprops)
    #MMMSim.SimMon.report_FlowsAdded(dump_to_file=FNAME_PREFIX+flowsadded_fname)
    MMMSim.SimMon.report_TaskRemappingInfo(dump_to_file=FNAME_PREFIX+trminfo_fname)
    #MMMSim.SimMon.report_NodeCumSlack(dump_to_file=FNAME_PREFIX+nodecumslack_fname)        
    #MMMSim.SimMon.report_NodeImportedTasks(dump_to_file=FNAME_PREFIX+node_importedtasks)
    

    ################################
    # PS-based Remapping enabled
    ################################
    
    SimParams.PSALGO_ENABLED = True
    SimParams.DYNAMIC_TASK_REMAPPING_ENABLED = True
    SimParams.DYNAMIC_TASK_REMAPPING_SCHEME = TaskRemapDecentSchemes.TASKREMAPPINGDECENTSCHEMES_LOWESTBLOCKING_QUEEN
    SimParams.CPUNODE_MONITOR_TASKSET_SLACK = True
    SimParams.PSALGO_VIEWER_ENABLED = False
    FNAME_PREFIX = DATA_FOLDER+"RMON_"
    
    # get randomly generated params
    pregenerated_random_params = generate_random_params()
    
    for each_k, each_param_entry in pregenerated_random_params.iteritems():
                                                                                    
        # set params                                            
        SimParams.PSALGO_TQN                                            = each_param_entry["rand_TQN"]           
        SimParams.PSALGO_TDECAY                                         = each_param_entry["rand_TDECAY"]               
        SimParams.PSALGO_THRESHOLDQN                                    = each_param_entry["rand_THRESHOLDQN"]               
        SimParams.PSALGO_KHOPDECAY                                      = each_param_entry["rand_KHOPDECAY"]            
        SimParams.PSALGO_KTIMEDECAY                                     = each_param_entry["rand_KTIMEDECAY"]             
        SimParams.PSALGO_HQN                                            = each_param_entry["rand_HQN"]              
        SimParams.PSALGO_INITIALHORMONEAMNT_WORKER                      = each_param_entry["rand_INITHD"]              
        SimParams.PSALGO_INITIALHORMONEAMNT_QUEEN                       = each_param_entry["rand_INITHD"] 
        SimParams.DYNAMIC_TASK_REMAPPING_SAMPLING_INTERVAL              = each_param_entry["rand_REMAP_PERIOD"]                                            
        SimParams.DYNAMIC_TASK_REMAPPING_TASK_LATE_ESTIM_LATENESS_RATIO = each_param_entry["rand_LATENESS_RATIO"]
        
        fname_param_prefix = FNAME_PREFIX + str(each_param_entry["rand_TQN"]) + \
                                "_" + str(each_param_entry["rand_TDECAY"]) + \
                                "_" + str(each_param_entry["rand_THRESHOLDQN"]) + \
                                "_" + str(each_param_entry["rand_KHOPDECAY"]) + \
                                "_" + str(each_param_entry["rand_KTIMEDECAY"]) + \
                                "_" + str(each_param_entry["rand_HQN"]) + \
                                "_" + str(each_param_entry["rand_INITHD"]) + \
                                "_" + str(each_param_entry["rand_REMAP_PERIOD"]) + \
                                "_" + str(each_param_entry["rand_LATENESS_RATIO"]) + "_"
        
        # check if the simulation has run already before continuing
        check_fname = fname_param_prefix+tm_fname 
        print "Checking file exists : " + str(check_fname)
        if(_check_file_exists(check_fname) == True):
            print "Simulation already exists ! "
        else:        
            random.seed(seed)
            np.random.seed(seed)
            print "----------------------------------------------------------------------------------------------------------------------------"
            print "Running runSim_Simple : num_wf=" + str(SimParams.NUM_WORKFLOWS) + \
                    ", Remapping_enabled"
            print fname_param_prefix
            print "----------------------------------------------------------------------------------------------------------------------------"
                    
            env, last_scheduled_task_time = MMMSim.runMainSimulation()
            env.run(until=last_scheduled_task_time+SimParams.SIM_RUNTIME)
            print env.now        
            
            (wf_results_summary, gops_in_outputbuff_summary) = MMMSim.SimMon.report_DecodedWorkflows_Summary(timeline_fname         =fname_param_prefix+tm_fname, 
                                                                                                             wf_res_summary_fname   = fname_param_prefix+wf_res_fname, 
                                                                                                            gops_opbuff_summary_fname = fname_param_prefix+gops_opbuff_fname,
                                                                                                            rmtbl_dt_summary_fname    = fname_param_prefix+rmtbl_dt_fname,
                                                                                                            output_format = "json")
            
            #MMMSim.SimMon.report_VideoStream_BasicStats(wf_results_summary, FNAME_PREFIX+vs_bs_fname)
            #MMMSim.SimMon.report_InstUtilisation(dump_to_file=FNAME_PREFIX+util_fname)
            #MMMSim.SimMon.report_InputBuffer(dump_to_file=FNAME_PREFIX+ibuff_fname)
            #MMMSim.SimMon.report_NodeTQs(dump_to_file=FNAME_PREFIX+nodetqs_fname)
            MMMSim.SimMon.report_OutputBufferContents(dump_to_file=fname_param_prefix+obuff_fname)
            #MMMSim.SimMon.report_RMTaskReleaseInfo(dump_to_file=FNAME_PREFIX+rmtaskrelease_fname)
            #MMMSim.SimMon.report_MappingAndPriAssInfo(dump_to_file=FNAME_PREFIX+mappingandpriass_fname)
            #MMMSim.SimMon.report_FlowsCompleted(dump_to_file=FNAME_PREFIX+flowscompleted_fname)
            #MMMSim.SimMon.report_NodeTaskExecTimeline(dump_to_file=FNAME_PREFIX+nodetaskexectime_fname)
            #MMMSim.SimMon.report_PSAlgoNodePSProps(dump_to_file=fname_param_prefix+psalgo_nodeprops)
            #MMMSim.SimMon.report_FlowsAdded(dump_to_file=FNAME_PREFIX+flowsadded_fname)
            MMMSim.SimMon.report_TaskRemappingInfo(dump_to_file=fname_param_prefix+trminfo_fname)
            #MMMSim.SimMon.report_NodeCumSlack(dump_to_file=fname_param_prefix+nodecumslack_fname)        
            #MMMSim.SimMon.report_NodeImportedTasks(dump_to_file=fname_param_prefix+node_importedtasks)










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


# psalgo related params
parser.add_argument("--tqn", help="param_rand_TQN", type=float, default=1.0)
parser.add_argument("--tdecay", help="param_rand_TDECAY", type=float, default=1.0)
parser.add_argument("--thresholdqn", help="param_rand_THRESHOLDQN", type=float, default=-1.0)
parser.add_argument("--thresholdqn_r_d", help="param_rand_THRESHOLDQN_RAT_DECREASE", type=float, default=-1.0)
parser.add_argument("--thresholdqn_r_i", help="param_rand_THRESHOLDQN_RAT_INCREASE", type=float, default=-1.0)
parser.add_argument("--khopdec", help="param_rand_KHOPDECAY", type=float, default=1.0)
parser.add_argument("--ktimedec", help="param_rand_KTIMEDECAY", type=float, default=1.0)
parser.add_argument("--hqn", help="param_rand_HQN", type=int, default=-1)
parser.add_argument("--inithd", help="param_rand_INITHD", type=int, default=-1)
parser.add_argument("--remap_p", help="param_rand_REMAP_PERIOD", type=float, default=1.0)
parser.add_argument("--late_rat", help="param_rand_LATENESS_RATIO", type=float, default=1.0)

# noc size
parser.add_argument("--noc_w", help="noc_w", type=int, default=-1)
parser.add_argument("--noc_h", help="noc_h", type=int, default=-1)

args = parser.parse_args()

####################################
## check which experiment to run ##
####################################
if(args.exp_type == "Exp_Simple"):   
    runSim_Simple()

# basic rm on/off
elif(args.exp_type == "Exp_RemappingBasic"):
    if(args.forced_seed != -1):
        runSim_RemappingBasic(run_rm_off=True, run_rm_on=True, seed=args.forced_seed, multiseeds=True)
    else:
        runSim_RemappingBasic(run_rm_off=False, run_rm_on=True, noc_w=args.noc_w, noc_h=args.noc_h)

# full factorial param test on rm_on
elif(args.exp_type == "Exp_RemappingFullFact"):
    if(args.forced_seed != -1):
        runSim_RemappingFullFactParams(run_rm_off=True, run_rm_on=True, seed=args.forced_seed, multiseeds=True)
    else:
        runSim_RemappingFullFactParams(run_rm_off=True, run_rm_on=True)

# monte-carlo param test on rm_on
elif(args.exp_type == "Exp_RemappingMonteCarlo"):
    if(args.forced_seed != -1):
        runSim_RemappingMonteCarloParamsTest(run_rm_off=True, run_rm_on=True, seed=args.forced_seed, multiseeds=True)
    else:
        runSim_RemappingMonteCarloParamsTest(run_rm_off=True, run_rm_on=True)

else:
    #parser.print_usage()
    #sys.exit("invalid arguments")
    runSim_RemappingBasic(run_rm_off=True, run_rm_on=True)


