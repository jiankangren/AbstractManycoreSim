# system imports
import simpy
import os, sys
import pprint
from time import gmtime, strftime
import time, random
import numpy as np
import pickle

# local imports
from SimParams import SimParams
from MMC import MMC
from libNoCModel.NodeNetwork import NodeNetwork

from libApplicationModel.Workflow import Workflow
from libApplicationModel.WorkflowGenerator import WorkflowGenerator
from libApplicationModel.AziziMOGATestbenchGenerator import AziziMOGATestbenchGenerator
from libApplicationModel.DataPreloader import DataPreloader 


from libBuffer.Buffer import Buffer, BufferType
from libMappingAndScheduling.Random_MappingPolicy import Random_MappingPolicy, Random_Basic_MappingPolicy
from libMappingAndScheduling.FirstFree_MappingPolicy import FirstFree_MappingPolicy
from libMappingAndScheduling.LeastDataIO_MappingPolicy import LeastDataIO_MappingPolicy


from SimDataMonitor import SimDataMonitor
from libNoCModel.OnChipInterconnect_CrossbarMesh import CrossbarMesh
from libNoCModel.OnChipInterconnect_NoC import NoC      
from libNoCModel.NoCSchedulabilityAnalysis import NoCSchedulabilityAnalysis  

# import different types of classes for different configurations
from libProcessingElement.CPUTypes import CPUTypes
from libProcessingElement.CPUNode_OpenLoop import CPUNode_OpenLoop
from libProcessingElement.CPUNode_ClosedLoop_wIBuffering import CPUNode_ClosedLoop_wIBuffering
from libProcessingElement.CPUNode_ClosedLoop_woIBuffering import CPUNode_ClosedLoop_woIBuffering
from libProcessingElement.CPUNode_OpenLoop_HEVC_FrameLvl import CPUNode_OpenLoop_HEVC_FrameLvl
from libProcessingElement.CPUNode_OpenLoop_HEVC_TileLvl import CPUNode_OpenLoop_HEVC_TileLvl

from libTaskDispatcher.TDTypes import TDTypes
from libTaskDispatcher.TaskDispatcher_OpenLoop import TaskDispatcher_OpenLoop
from libTaskDispatcher.TaskDispatcher_ClosedLoop_wIBuffering import TaskDispatcher_ClosedLoop_wIBuffering
from libTaskDispatcher.TaskDispatcher_ClosedLoop_woIBuffering import TaskDispatcher_ClosedLoop_woIBuffering
from libTaskDispatcher.TaskDispatcher_OpenLoop_HEVCFrame import TaskDispatcher_OpenLoop_HEVCFrame
from libTaskDispatcher.TaskDispatcher_OpenLoop_HEVCTile import TaskDispatcher_OpenLoop_HEVCTile

from libResourceManager.RMTypes import RMTypes
from libResourceManager.RunTimeTaskManager_OpenLoop import RunTimeTaskManager_OpenLoop
from libResourceManager.RunTimeTaskManager_ClosedLoop_wIBuffering import RunTimeTaskManager_ClosedLoop_wIBuffering
from libResourceManager.RunTimeTaskManager_ClosedLoop_woIBuffering import RunTimeTaskManager_ClosedLoop_woIBuffering



SimMon = None

def runMainSimulation(initial_rand_seed=1234, dump_workload=True):
    
    global SimMon
    
    ############################################################
    ############################################################
    #########    MAIN SIMULATION ENTRY POINT        ############
    ############################################################
    ############################################################
    
    ################################
    # INITIALISE SIMULATION
    ################################
    # start phase
    print os.path.basename(__file__) + ":: Simulation Start " + "(" + strftime("%H:%M:%S", gmtime()) + ")"    
    
    # create environment
    env = simpy.Environment()
    
    ################################
    # Log, report, debug cleanup
    ################################
    NoCSchedulabilityAnalysis.cleanOutputReports("schedulability_tests")
    
    ################################
    # Preload any data files
    ################################
    DataPreloader.preload_data_files()    
    
    ################################
    # MODEL ALL NODES ON SYSTEM
    # (Modelled as simpy-processes)
    ################################
    Node_Network_test = NodeNetwork() 
    for n in xrange(SimParams.NUM_NODES):
        node = getNodeClass(env, n, tq_size = SimParams.CPUNODE_TASKQ_SIZE)
        Node_Network_test.addNode(node)
        
    ################################
    # MODEL ON-CHIP-INTERCONNECT
    ################################   
    Mesh2DNOC =  NoC(Node_Network_test.get_Nodes(), SimParams.NOC_W, SimParams.NOC_H)
    Mesh2DNOC.construct()
    #print Mesh2DNOC
    #Mesh2DNOC.testNetwork()
    
    ################################
    # Give various access to the nodes
    ################################ 
    Node_Network_test.set_nodeNetworkAccess(Mesh2DNOC)
    
    ################################
    # GENERATE WORKFLOWS
    ################################
    random.seed(initial_rand_seed)
    np.random.seed(initial_rand_seed)
    Workflows = WorkflowGenerator(env, SimParams.NUM_WORKFLOWS, 
                      SimParams.WFGEN_MIN_VIDS_PER_WF, SimParams.WFGEN_MAX_VIDS_PER_WF,
                      SimParams.WFGEN_MIN_GOPS_PER_VID, SimParams.WFGEN_MAX_GOPS_PER_VID,
                      SimParams.WFGEN_MIN_INTER_VIDEO_GAP, SimParams.WFGEN_MAX_INTER_VIDEO_GAP,
                      None,
                      None )
        
    Workflows.generate_workflows()
    #Workflows.setTaskPriorities_AllUnique()
    MultipleWorkflows = []
    total_num_tasks = 0
    total_num_tiles = 0
    for each_wf_key, each_wf_val in Workflows.workflows.iteritems():
        wf = Workflow(env, each_wf_key, None, None, None)
        wf.set_stream_content(each_wf_val)
        total_num_tiles += wf.getTotalTiles()
        total_num_tasks += len(Workflows.workflows[each_wf_key])
        MultipleWorkflows.append(wf)
    
    if(dump_workload==True):
        Workflows.dumpWorkflowsToFile()    
    #Workflows.showTaskTimeLine(len(MultipleWorkflows), show_vid_blocks=True)
    #WorkflowGenerator.plot_show()
    
    # draw histogram of task-exec times
    #Workflow.plot_TaskComputationCostHistogram(MultipleWorkflows, 2, ftype="B", wf_ids=[10])
    #WorkflowGenerator.plot_show()
    
    print "--- finished generating tasks"
    print "total_num_tasks:: " , total_num_tasks
    
    #sys.exit()
    
#    MultipleWorkflows = []
#    total_num_tasks = 0
#    stream_id = 0
#    for i in xrange(SimParams.NUM_WORKFLOWS):
#        wf = Workflow(env, stream_id, (SimParams.FRAME_DEFAULT_W, SimParams.FRAME_DEFAULT_H), SimParams.FRAME_RATE, SimParams.GOP_STRUCTURE)
#        size = wf.populateWorkflow()
#        total_num_tasks = total_num_tasks + size
#        
#        MultipleWorkflows.append(wf)
#        
#        # set new stream-id (100 offset)
#        stream_id = stream_id + 1
    
#     Workflow.plot_TaskComputationCostHistogram(MultipleWorkflows, ftype="I", fig_id=1, wf_ids = range(SimParams.NUM_WORKFLOWS))
#     Workflow.plot_TaskComputationCostHistogram(MultipleWorkflows, ftype="P", fig_id=2, wf_ids = range(SimParams.NUM_WORKFLOWS))
#     Workflow.plot_TaskComputationCostHistogram(MultipleWorkflows, ftype="B", fig_id=3, wf_ids = range(SimParams.NUM_WORKFLOWS))
#     Workflow.plot_show()
#     sys.exit()
#      
    
    
#    Workflow.plot_TaskComputationCostHistogram_step(MultipleWorkflows, fig_id=1, wf_ids = range(SimParams.NUM_WORKFLOWS))
#    Workflow.plot_show()
#    sys.exit()
    
    # ---- UNCOMMENT to produce azizi testbench ----
#     AzizMOGATB = AziziMOGATestbenchGenerator(Workflows.workflows)
#     AzizMOGATB.set_flow_pri_offset(max(Workflows.get_used_pri_values()))
#     organised_wfs = AzizMOGATB.constructWfLevelTasks()    
#     tb_text = AzizMOGATB.outputTestBench(organised_wfs, 'MOGATestBenches/HdVidTestbench_test_050515.txt')
#     sys.exit()
#      
#     #pprint.pprint(tb_text)
    # ----
    
    ################################
    # Create I/O Buffers
    # (Modelled as simpy-containers)
    ################################
    # one input buffer mapped onto one workflow
    InputBuffers = []
    for i in xrange(SimParams.NUM_INPUTBUFFERS):
        IPBuff = Buffer(env, BufferType.BUFFER_TYPE_INPUT, size=SimParams.INPUT_BUFF_SIZE, safe_level=SimParams.INPUT_BUFF_SAFE_LEVEL) # 50 slot input buff
        InputBuffers.append(IPBuff)
    
    OutputBuffer = Buffer(env, BufferType.BUFFER_TYPE_OUTPUT, size=SimParams.OUTPUT_BUFF_SIZE)  # large num slot output buff
    
    # give all nodes access to outputbuff
    Node_Network_test.set_outputBuffInstance(OutputBuffer)
    
    ################################
    # Create Resource Manager
    # with a bunch of policies to test
    # (Modelled as simpy-process)
    ################################
    # pick a policy
    RM_Policy = Random_MappingPolicy(Node_Network_test, InputBuffers)
    RMB_Policy = Random_Basic_MappingPolicy(Node_Network_test, InputBuffers)
    FF_Policy = FirstFree_MappingPolicy(Node_Network_test, InputBuffers)
    LDIO_Policy = LeastDataIO_MappingPolicy(Node_Network_test, InputBuffers)
    
    # create resource manager with that policy
    ResourceManager = getRMClass(env, 
                                 pd=SimParams.RESOURCEMANAGER_POLL_RATE, 
                                 mp = FF_Policy,
                                 nn = Node_Network_test, 
                                 ib = InputBuffers, 
                                 ob = OutputBuffer,
                                 inter = Mesh2DNOC,
                                 td = None)
    
    ResourceManager.set_maxTasks(total_num_tasks)
    ResourceManager.set_lastscheduledtask_time(Workflows.getLastScheduledTask().get_scheduledDispatchTime())
    ResourceManager.set_flowpriorityoffset(max(Workflows.get_used_pri_values()))    
    ResourceManager.set_lastscheduled_vs(Workflows.getLastScheduledVideoStream())
    ResourceManager.set_initrandomseed(initial_rand_seed)
    ResourceManager.set_total_number_of_tiles_generated(total_num_tiles)
    
    # give node network access to RM
    Node_Network_test.set_resourceManagerInstance(ResourceManager)
    
    ################################
    # Create Task Dispatcher
    # He takes a task from task pool and
    # transfers to input buff
    # (Modelled as simpy-process)
    ################################
    Task_Dispatcher = getTDClass(env,InputBuffers,None, MultipleWorkflows, SimParams.TASKDISPATCH_RATE, ResourceManager)
    ResourceManager.set_taskdispatcher_instance(Task_Dispatcher)
    
    ################################
    # Create Simulation monitoring instance
    # (Modelled as simpy-process)
    ################################
    SimMon = SimDataMonitor(env,
                            Node_Network_test,
                            Mesh2DNOC, 
                            InputBuffers, 
                            OutputBuffer, 
                            Task_Dispatcher, 
                            Workflows, 
                            ResourceManager)
    SimMon.last_scheduled_dispatchtime =  Workflows.getLastScheduledTask().get_scheduledDispatchTime()
    SimMon.first_scheduled_dispatchtime = Workflows.getFirstScheduledTask().get_scheduledDispatchTime()
    
    ################################
    # START SIMULATION
    ################################
    #env.run(until=SimParams.SIM_RUNTIME)
    return (env, ResourceManager.get_lastscheduledtask_time())
   
    #print " "
    #print os.path.basename(__file__) + ":: Simulation End " + "(" + strftime("%H:%M:%S", gmtime()) + ")"


def getNodeClass(env, n, tq_size = SimParams.CPUNODE_TASKQ_SIZE):
    if(SimParams.SIM_ENTITY_CPUNODE_CLASS == CPUTypes.OPENLOOP):
        return CPUNode_OpenLoop(env, n, tq_size = SimParams.CPUNODE_TASKQ_SIZE)    
    elif(SimParams.SIM_ENTITY_CPUNODE_CLASS == CPUTypes.CLOSEDLOOP_WITH_IBUFFERING):
        return CPUNode_ClosedLoop_wIBuffering(env, n, tq_size = SimParams.CPUNODE_TASKQ_SIZE)    
    elif(SimParams.SIM_ENTITY_CPUNODE_CLASS == CPUTypes.CLOSEDLOOP_WITHOUT_IBUFFERING):
        return CPUNode_ClosedLoop_woIBuffering(env, n, tq_size = SimParams.CPUNODE_TASKQ_SIZE) 
    elif(SimParams.SIM_ENTITY_CPUNODE_CLASS == CPUTypes.OPENLOOP_HEVC_FRAME_LEVEL):
        return CPUNode_OpenLoop_HEVC_FrameLvl(env, n, tq_size = SimParams.CPUNODE_TASKQ_SIZE)
    elif(SimParams.SIM_ENTITY_CPUNODE_CLASS == CPUTypes.OPENLOOP_HEVC_TILE_LEVEL):
        return CPUNode_OpenLoop_HEVC_TileLvl(env, n, tq_size = SimParams.CPUNODE_TASKQ_SIZE)
    else:
        sys.exit("getNodeClass: error")

def getTDClass(env, ib, tsp, mwf, rate, rm):
    if(SimParams.SIM_ENTITY_TASKDISPATCHER_CLASS == TDTypes.OPENLOOP):
        return TaskDispatcher_OpenLoop(env,ib,tsp, mwf, rate, rm)    
    elif(SimParams.SIM_ENTITY_TASKDISPATCHER_CLASS == TDTypes.CLOSEDLOOP_WITH_IBUFFERING):
        return TaskDispatcher_ClosedLoop_wIBuffering(env,ib,tsp, mwf, rate, rm)
    elif(SimParams.SIM_ENTITY_TASKDISPATCHER_CLASS == TDTypes.CLOSEDLOOP_WITHOUT_IBUFFERING):
        return TaskDispatcher_ClosedLoop_woIBuffering(env,ib,tsp, mwf, rate, rm)
    elif(SimParams.SIM_ENTITY_TASKDISPATCHER_CLASS == TDTypes.OPENLOOP_WITH_HEVCFRAME):
        return TaskDispatcher_OpenLoop_HEVCFrame(env,ib,tsp, mwf, rate, rm)
    elif(SimParams.SIM_ENTITY_TASKDISPATCHER_CLASS == TDTypes.OPENLOOP_WITH_HEVCTILE):        
        return TaskDispatcher_OpenLoop_HEVCTile(env,ib,tsp, mwf, rate, rm)
    
    else:
        sys.exit("getTDClass: error")

def getRMClass(env, pd=None, mp=None, nn=None, ib=None, ob=None, inter=None, td=None, mmc=None):
    if(SimParams.SIM_ENTITY_RESOURCEMANAGER_CLASS == RMTypes.OPENLOOP):
        return RunTimeTaskManager_OpenLoop(env, 
                       polling_delay=pd, 
                       mapping_policy = mp,
                       node_network = nn, 
                       input_buffers = ib, 
                       output_buffer = ob,
                       interconnect = inter,                       
                       task_dispatcher = td)
    elif(SimParams.SIM_ENTITY_RESOURCEMANAGER_CLASS == RMTypes.CLOSEDLOOP_WITH_IBUFFERING):                       
        return RunTimeTaskManager_ClosedLoop_wIBuffering(env, 
                       polling_delay=pd, 
                       mapping_policy = mp,
                       node_network = nn, 
                       input_buffers = ib, 
                       output_buffer = ob,
                       interconnect = inter,
                       task_dispatcher = td)
    elif(SimParams.SIM_ENTITY_RESOURCEMANAGER_CLASS == RMTypes.CLOSEDLOOP_WITHOUT_IBUFFERING):
        return RunTimeTaskManager_ClosedLoop_woIBuffering(env, 
                       polling_delay=pd, 
                       mapping_policy = mp,
                       node_network = nn, 
                       input_buffers = ib, 
                       output_buffer = ob,
                       interconnect = inter,
                       task_dispatcher = td)
        
    else:
        sys.exit("getRMClass: error")

#############################
# Run Simulation
#############################
#runMainSimulation()
    
#############################
# GET SIM_END STATS
#############################

# show some sim analysis
#print "###########################################################"
#print "STATS"
#print "###########################################################"
#print ""
#SimMon.plot_InputBuffer()
#SimMon.plot_OutputBuffer()
#SimMon.plot_NodeTaskQs()

#SimMon.show_CompletedTaskAnalysis()
#SimMon.plot_TasksMissedDeadline_perCore()
#SimMon.plot_TasksMissedDeadline_perTask()

#fname = 'experiment_data/lateness/wf'+str(SimParams.NUM_WORKFLOWS)+'_cores'+str(SimParams.NUM_NODES)
#SimMon.show_OutputBuffer_Contents_ByGOP(dump_to_file=fname)
#SimMon.show_CPU_utilisation()

#pprint.pprint(ResourceManager.slack_reclaim_table)

#SimMon.plot_InstUtilisation()
#SimMon.plot_showall()



