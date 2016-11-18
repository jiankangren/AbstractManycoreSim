import pprint
import sys
import itertools
import simpy
import random
import numpy as np
import copy
from operator import itemgetter

from SimParams import SimParams
from TaskRemapDecentSchemes import TaskRemapDecentSchemes
from libApplicationModel.MPEG2FrameTask import MPEG2FrameTask
from libDebug.Debug import Debug, DebugCat
from libMappingAndScheduling.Decentralised.PSAlgorithm import PSAlgorithmNodetype
from libNoCModel.NoCFlowTable import NoCFlowTable
from libNoCModel.NoCFlow import NoCFlow, FlowType

class TaskRemapDecentSchemesImpl:

    def __init__(self, env, node_instance):  
        self.label = "TaskRemapDecentSchemesImpl"
        self.env = env
        self.node_instance = node_instance
        self.RM_instance = None        
        self.process_instance_remapping_period = None
        self.remapping_algo_started = False
        self.remapping_algo_starttime = None        
        self.remaped_check_count = 0
        
        # tracking
        self.track_remaped_numtasks = [] # tasks that were remapped
        
        # for debugging
        self.track_nodetqinfo_at_remapping_instant = []
    
    # this can be used to start the algorithm half way through the simulation
    def startRemappingAlgo(self, node_id):        
        if(SimParams.DYNAMIC_TASK_REMAPPING_ENABLED == True):
            self.RM_instance = self.node_instance.resource_manager_instance        
            if(self.remapping_algo_started == False):            
                self.remapping_algo_starttime = self.env.now
                self.remapping_algo_started = True
                self.process_instance_remapping_period = self.env.process(self.runRemappingScheme(node_id))
        
        
    def runRemappingScheme(self, node_id):        
        print "runRemappingScheme: Enter"
        while True:
            result = self.taskReMappingSchemeHandler(node_id)                        
            # wait for TQN seconds
            yield self.env.timeout(SimParams.DYNAMIC_TASK_REMAPPING_SAMPLING_INTERVAL + (self.node_instance.get_id() * SimParams.DYNAMIC_TASK_REMAPPING_SAMPLING_INTERVAL_OFFSET))            
            
            # update ps-viewer
            #self.RM_instance.PSAlgoViewer.updatePlevel()
    
    def taskReMappingSchemeHandler(self, node_id):
        if (SimParams.DYNAMIC_TASK_REMAPPING_SCHEME == TaskRemapDecentSchemes.TASKREMAPPINGDECENTSCHEMES_NONE):
            result =  self.taskReMappingDecentSchImpl_None(node_id)        
        
        elif (SimParams.DYNAMIC_TASK_REMAPPING_SCHEME == TaskRemapDecentSchemes.TASKREMAPPINGDECENTSCHEMES_CENTRAL_REMAPPER_V1):
            result =  self.taskReMappingDecentSchImpl_CentralRemapper_V1(node_id)           
        
        elif (SimParams.DYNAMIC_TASK_REMAPPING_SCHEME == TaskRemapDecentSchemes.TASKREMAPPINGDECENTSCHEMES_RANDOM_ANY):
            result =  self.taskReMappingDecentSchImpl_RandomAny(node_id)           
        
        elif (SimParams.DYNAMIC_TASK_REMAPPING_SCHEME == TaskRemapDecentSchemes.TASKREMAPPINGDECENTSCHEMES_RANDOM_NEIGHBOUR):
            result =  self.taskReMappingDecentSchImpl_RandomNeighbour(node_id)           
                      
        elif (SimParams.DYNAMIC_TASK_REMAPPING_SCHEME == TaskRemapDecentSchemes.TASKREMAPPINGDECENTSCHEMES_NEIGHBOUR_HIGHEST_PSLEVEL):
            result =  self.taskReMappingDecentSchImpl_HighestPSLevelNeighbour(node_id)            
        
        elif (SimParams.DYNAMIC_TASK_REMAPPING_SCHEME == TaskRemapDecentSchemes.TASKREMAPPINGDECENTSCHEMES_RANDOM_QUEEN):
            result =  self.taskReMappingDecentSchImpl_RandomQueen(node_id)            
        
        elif (SimParams.DYNAMIC_TASK_REMAPPING_SCHEME == TaskRemapDecentSchemes.TASKREMAPPINGDECENTSCHEMES_RANDOM_QUEEN_VIA_SYSSLACK):
            result =  self.taskReMappingDecentSchImpl_RandomQueen_viaSysSlack(node_id)        
        
        elif(SimParams.DYNAMIC_TASK_REMAPPING_SCHEME == TaskRemapDecentSchemes.TASKREMAPPINGDECENTSCHEMES_LOWESTBLOCKING_QUEEN):
            result = self.taskReMappingDecentSchImpl_LowestBlockingQueen(node_id)
        
        elif(SimParams.DYNAMIC_TASK_REMAPPING_SCHEME == TaskRemapDecentSchemes.TASKREMAPPINGDECENTSCHEMES_LOWESTBLOCKING_QUEEN_VIA_SYSSLACK):
            result = self.taskReMappingDecentSchImpl_LowestBlockingQueen_viaSysSlack(node_id)
            
        elif(SimParams.DYNAMIC_TASK_REMAPPING_SCHEME == TaskRemapDecentSchemes.TASKREMAPPINGDECENTSCHEMES_CCP_REMAPPING):
            cluster_id = self.node_instance.ccpprops.get_cluster_id()
            result = self.taskReMappingDecentSchImpl_CCP_Remapping(node_id, cluster_id)
            
        
        else:
            sys.exit("taskReMappingSchemeHandler:: Error: unknown task mapping scheme")
            
        self.remaped_check_count += 1
        
        return result
    
    # notify RM regarding change to the remapping table
    def notify_RM_mappingChange(self, remapped_task_node_id_tuples):
        
        Debug.PPrint("%.15f"%self.env.now + "," + self.label + "," + 'notify_RM_mappingChange:: Enter' , DebugCat.DEBUG_CAT_TASKREMAPPING_NOTIFICATION)
        
        src_node_id = self.node_instance.get_id()
        dst_node_id = SimParams.RESOURCEMANAGER_NODEID
        release_time = self.env.now
        nextid = self.RM_instance.flow_table.nextid                    
        route = self.RM_instance.interconnect.getRouteXY(dst_node_id, src_node_id)
        priority = SimParams.NOC_FLOW_MS_SIGNALLING_MAXPRIORITY + nextid        
        basic_latency = self.RM_instance.interconnect.getRouteCostXY(dst_node_id, 
                                                                    src_node_id,
                                                                    SimParams.NOC_PAYLOAD_8BYTES)
        payload = SimParams.NOC_PAYLOAD_8BYTES
        endTime_wrt_BL = release_time + basic_latency
        
        # construct payload
        payload_metadata = []
        for each_remap_tuple in remapped_task_node_id_tuples:
            
            #pprint.pprint(each_remap_tuple)
            
            task = each_remap_tuple[0]
            old_node_id = each_remap_tuple[1]
            new_node_id = each_remap_tuple[2]
        
            temp_payload_metadata = {
                            'remapped_task' : task,  # we only need the ids (wf, strm, task), but we send the whole obj for simplicity                            
                            'remapped_old_node_id' : old_node_id,
                            'remapped_new_node_id' : new_node_id,
                            }
            
            payload_metadata.append(temp_payload_metadata)
                   
        # construct flow
        newflow = NoCFlow(nextid,
                       None,
                       None,
                       None, # list of dst task ids
                       src_node_id, 
                       dst_node_id, 
                       route,
                       priority, 
                       None, 
                       basic_latency, 
                       payload,
                       endTime_wrt_BL,
                       type=FlowType.FLOWTYPE_REMAPPING_NOTIFY_DISPATCHER,                           
                       payload_metadata=payload_metadata)
        
        self.RM_instance.lock_RM_FLWtbl()
        # add to the flow table
        self.RM_instance.flow_table.addFlow(newflow, release_time, basic_latency)                        
        self.RM_instance.release_RM_FLWtbl()
        
        # update the table        
        self.RM_instance.flow_table.updateTable(fire=True)   
        
        
    # make necessary updates to the remapping data structures in RM, RMApp, nodes etc.
    def applyTaskRemapping(self, remapped_task_list):
        #print "applyTaskRemapping: Enter"
        #pprint.pprint(remapped_task_list)
        
        if(len(remapped_task_list)==0):
            return False
        
        # do we model the update notification flow ?
        if(SimParams.DYNAMIC_TASK_MAPPING_MODEL_MPTBL_UPDATE_NOTIFICATION == True):#
            self.notify_RM_mappingChange(remapped_task_list)
            
        # we don't model the update notification flow
        else:
            for each_item in remapped_task_list:                
                task = each_item[0]
                old_node_id = each_item[1]
                new_node_id = each_item[2]
                                
                self._update_vidstrm_mappingtbl(task.get_frameIXinGOP(), 
                                                task.get_wfid(), 
                                                task.get_video_stream_id(), 
                                                new_node_id)                        
                # update runtime app - runtime task's processing core
                (updated_task, old_node_id) = self.RM_instance.RunTimeApps.updateTaskProcessingCore(task.get_frameIXinGOP(), 
                                                                        task.get_wfid(), 
                                                                        task.get_video_stream_id(), 
                                                                        new_node_id)                        
                if(updated_task != None) and (old_node_id!= None):
                    # update runtime app - task to node mapping table
                    self.RM_instance.RunTimeApps.updateTaskToNodeMappingTbl(updated_task,old_node_id,new_node_id)
        
        # common actions - updating system slack
        for each_item in remapped_task_list:
            task = each_item[0]
            old_node_id = each_item[1]
            new_node_id = each_item[2]
            
            # update nodes slack tracking - strictly speaking, this should be done by the dispatcher ?
            self.RM_instance.node_network.get_Nodes()[old_node_id].update_SystemSlack_removeTask(task)
            self.RM_instance.node_network.get_Nodes()[new_node_id].update_SystemSlack_addTask(task)                    
            # update queens import list                                    
            self.RM_instance.node_network.get_Nodes()[new_node_id].importedTasks_addTask(self.remaped_check_count, self.node_instance.get_id(), task, self.env.now)
                                    
            # for tracking
            self._track_remapped_tasks(task, old_node_id, new_node_id)
            
            
    
    
    
    #####################################################################################
    # TASKREMAPPINGDECENTSCHEMES_NONE
    #####################################################################################
    def taskReMappingDecentSchImpl_None(self, node_id):        
        return None
   
    
    
    #####################################################################################
    # TASKREMAPPINGDECENTSCHEMES_CENTRAL_REMAPPER_V1
    #####################################################################################
    def taskReMappingDecentSchImpl_CentralRemapper_V1(self, node_id):        
        return None
                
        
   
    
    #####################################################################################
    # TASKREMAPPINGDECENTSCHEMES_RANDOM_ANY
    #####################################################################################
    def taskReMappingDecentSchImpl_RandomAny(self, node_id):        
        Debug.PPrint("%.15f"%self.env.now + "," + self.label + "," + 'taskReMappingDecentSchImpl_RandomAny:: node=[%d] : going to remap!!' % (self.node_instance.get_id()), DebugCat.DEBUG_CAT_TASKREMAPPING)
        
        # get node
        node = self.RM_instance.node_network.get_Nodes()[node_id]                
        # we need to decide which task to remap ?
        late_tasks = node.get_SystemSlack_GetLateTasks()
        num_tasks_late_in_tq = len(late_tasks)
        total_tasks_in_tq = len(node.get_SystemSlack_MappedTasks())
        
        remapped_tasks_list = []
        selected_tasks = []
        if(total_tasks_in_tq>0):
            proportion_of_tasks_late_in_tq = float(float(num_tasks_late_in_tq)/float(total_tasks_in_tq))            
            if(proportion_of_tasks_late_in_tq >= SimParams.DYNAMIC_TASK_REMAPPING_THRESHOLD_PERCENTAGE):
                # get task(s) to remap  
                node_tq_lateness_sorted = sorted(late_tasks, key=lambda t: t.estimatedLateness_ratiobased(self.env.now, 
                                                                                              lateness_ratio=SimParams.DYNAMIC_TASK_REMAPPING_TASK_LATE_ESTIM_LATENESS_RATIO),
                                                                                              reverse=True)                        
                if(len(node_tq_lateness_sorted) > SimParams.DYNAMIC_TASK_REMAPPING_OFFLOAD_NUMTASKS):
                    selected_tasks = node_tq_lateness_sorted[0:SimParams.DYNAMIC_TASK_REMAPPING_OFFLOAD_NUMTASKS]                            
                else:
                    selected_tasks = node_tq_lateness_sorted
                    
                # randomly select any other node to remap to
                node_list = [node for node in self.RM_instance.node_network.get_Nodes() if node.get_id() != node_id]
                selected_node = random.choice(node_list)
                selected_node_id = selected_node.get_id()
                
                                                
                # rearrange RM tables
                for selected_task in selected_tasks:                                    
                    remapped_tasks_list.append([selected_task, node_id, selected_node_id])
                        
                if(selected_node_id != None):                                
                    remapped_tasks_list.append([selected_task, node_id, selected_node_id])                                  
                else:
                    Debug.PPrint("%.15f"%self.env.now + "," + self.label + "," + 'taskReMappingDecentSchImpl_RandomAny:: node=[%d] : no nodes available!!' % (node_id), DebugCat.DEBUG_CAT_TASKREMAPPING)
            
            # update the required remapping data structures
            if(len(remapped_tasks_list)>0):
                self.applyTaskRemapping(remapped_tasks_list)                
                #self._debug_node_info(selected_task, self.node_instance.get_id(), selected_node_id)
                
                 
        else:
            Debug.PPrint("%.15f"%self.env.now + "," + self.label + "," + 'taskReMappingDecentSchImpl_RandomAny:: node=[%d] : no late tasks!' % (node_id), DebugCat.DEBUG_CAT_TASKREMAPPING)
                   
                        
                        
        
    #####################################################################################
    # TASKREMAPPINGDECENTSCHEMES_RANDOM_NEIGHBOUR
    #####################################################################################
    def taskReMappingDecentSchImpl_RandomNeighbour(self, node_id):
        Debug.PPrint("%.15f"%self.env.now + "," + self.label + "," + 'taskReMappingDecentSchImpl_RandomNeighbour:: node=[%d] : going to remap!!' % (self.node_instance.get_id()), DebugCat.DEBUG_CAT_TASKREMAPPING)
        
        # get node
        node = self.RM_instance.node_network.get_Nodes()[node_id]                
        # we need to decide which task to remap ?
        late_tasks = node.get_SystemSlack_GetLateTasks()
        num_tasks_late_in_tq = len(late_tasks)
        total_tasks_in_tq = len(node.get_SystemSlack_MappedTasks())
        
        remapped_tasks_list = [] 
        selected_tasks = []
        if(total_tasks_in_tq>0):
            proportion_of_tasks_late_in_tq = float(float(num_tasks_late_in_tq)/float(total_tasks_in_tq))            
            if(proportion_of_tasks_late_in_tq >= SimParams.DYNAMIC_TASK_REMAPPING_THRESHOLD_PERCENTAGE):
                # get task(s) to remap  
                node_tq_lateness_sorted = sorted(late_tasks, key=lambda t: t.estimatedLateness_ratiobased(self.env.now, 
                                                                                              lateness_ratio=SimParams.DYNAMIC_TASK_REMAPPING_TASK_LATE_ESTIM_LATENESS_RATIO),
                                                                                              reverse=True)                        
                if(len(node_tq_lateness_sorted) > SimParams.DYNAMIC_TASK_REMAPPING_OFFLOAD_NUMTASKS):
                    selected_tasks = node_tq_lateness_sorted[0:SimParams.DYNAMIC_TASK_REMAPPING_OFFLOAD_NUMTASKS]                            
                else:
                    selected_tasks = node_tq_lateness_sorted
                    
                # randomly select a neighbour to remap to
                neighbour_nodes = self.RM_instance.interconnect.getNeighbours(node_id)
                neighbour_node_ids = [nn_id for nn_id in neighbour_nodes.values() if nn_id != None]
                selected_node_id = random.choice(neighbour_node_ids)
                                
                                               
                # rearrange RM tables
                for selected_task in selected_tasks:                                    
                    remapped_tasks_list.append([selected_task, node_id, selected_node_id])
                        
                if(selected_node_id != None):                                
                    remapped_tasks_list.append([selected_task, node_id, selected_node_id])                                  
                else:
                    Debug.PPrint("%.15f"%self.env.now + "," + self.label + "," + 'taskReMappingDecentSchImpl_RandomNeighbour:: node=[%d] : no nodes available!!' % (node_id), DebugCat.DEBUG_CAT_TASKREMAPPING)
            
            # update the required remapping data structures
            if(len(remapped_tasks_list)>0):
                self.applyTaskRemapping(remapped_tasks_list)                
                #self._debug_node_info(selected_task, self.node_instance.get_id(), selected_node_id)
                
                 
        else:
            Debug.PPrint("%.15f"%self.env.now + "," + self.label + "," + 'taskReMappingDecentSchImpl_RandomNeighbour:: node=[%d] : no late tasks!' % (node_id), DebugCat.DEBUG_CAT_TASKREMAPPING)
                   
                
        
    
    #####################################################################################
    # TASKREMAPPINGDECENTSCHEMES_NEIGHBOUR_HIGHEST_PSLEVEL
    #####################################################################################
    def taskReMappingDecentSchImpl_HighestPSLevelNeighbour(self, node_id):
        if(self.remaped_check_count > 0):
            # get node
            node = self.RM_instance.node_network.get_Nodes()[node_id]
            
            # we need to decide when to remap ?
            if(node.numLateTasksInTQ_KG() >= SimParams.DYNAMIC_TASK_REMAPPING_THRESHOLD):
            
                # get task(s) to remap
                node_tq = self.RM_instance.node_network.get_Nodes()[node_id].get_TaskQueue()
                node_tq_lateness_sorted = sorted(node_tq, key=lambda t: t.estimatedLateness_KG(self.env.now), reverse=True)
                if(len(node_tq_lateness_sorted) > SimParams.DYNAMIC_TASK_REMAPPING_OFFLOAD_NUMTASKS):
                    selected_tasks = node_tq_lateness_sorted[0:SimParams.DYNAMIC_TASK_REMAPPING_OFFLOAD_NUMTASKS]
                else:
                    selected_tasks = node_tq_lateness_sorted
                
                #max_task_lateness = max([task.estimatedLateness_KG(self.env.now) for task in node_tq])
                #selected_task = [t for t in node_tq if t.estimatedLateness_KG(self.env.now) == max_task_lateness][0]
                
                # which neighbour to pass to ?
                neighbour_nodes = self.RM_instance.interconnect.getNeighbours(node_id)
                neighbour_node_ids = [nn_id for nn_id in neighbour_nodes.values() if nn_id != None]
                max_pslevel = max([self.RM_instance.node_network.get_Nodes()[nn_id].psalgoprops.get_pheramone_level() 
                                   for nn_id in neighbour_node_ids])
                selected_node_id = [nn_id for nn_id in neighbour_node_ids 
                                 if self.RM_instance.node_network.get_Nodes()[nn_id].psalgoprops.get_pheramone_level() == max_pslevel][0]  
                
                selected_node = self.RM_instance.node_network.get_Nodes()[selected_node_id]
                
                # rearrange RM tables
                for selected_task in selected_tasks:
                    self._update_vidstrm_mappingtbl(selected_task.get_frameIXinGOP(), 
                                                    selected_task.get_wfid(), 
                                                    selected_task.get_video_stream_id(), 
                                                    selected_node_id)
                    
                    # update runtime app - runtime task's processing core
                    (updated_task, old_node_id) = self.RM_instance.RunTimeApps.updateTaskProcessingCore(selected_task.get_frameIXinGOP(), 
                                                                            selected_task.get_wfid(), 
                                                                            selected_task.get_video_stream_id(), 
                                                                            selected_node_id)                    
                    
                    if(updated_task != None) and (old_node_id!= None):
                        # update runtime app - task to node mapping table
                        self.RM_instance.RunTimeApps.updateTaskToNodeMappingTbl(updated_task,old_node_id,selected_node_id)  
                    
                        # update nodes slack tracking
                        self.RM_instance.node_network.get_Nodes()[old_node_id].update_SystemSlack_removeTask(updated_task)
                        self.RM_instance.node_network.get_Nodes()[selected_node_id].update_SystemSlack_addTask(updated_task)
                    
                    # for tracking
                    self._track_remapped_tasks(updated_task, old_node_id, selected_node_id)
                
    #####################################################################################
    # TASKREMAPPINGDECENTSCHEMES_RANDOM_QUEEN
    #####################################################################################
    def taskReMappingDecentSchImpl_RandomQueen(self, node_id):
        if(self.remaped_check_count > 0):            
            #Debug.PPrint("%.15f"%self.env.now + "," + self.label + "," + 'taskReMappingDecentSchImpl_RandomQueen:: node=[%d] : going to remap!!' % (self.node_instance.get_id()), DebugCat.DEBUG_CAT_TASKREMAPPING)
            
            # get node
            node = self.RM_instance.node_network.get_Nodes()[node_id]
            
            if(node.psalgoprops.get_node_type() != PSAlgorithmNodetype.QUEEN_BEE):
            
                # we need to decide when to remap ?
                num_tasks_late_in_tq = node.numLateTasksInTQ(lateness_ratio=SimParams.DYNAMIC_TASK_REMAPPING_TASK_LATE_ESTIM_LATENESS_RATIO)
                #num_tasks_late_in_tq = node.numLateTasksInTQ_KG()
                #num_tasks_late_in_tq = node.numLateTasksInTQ_Div_x()
                #late_tasks = node.get_SystemSlack_GetLateTasks()
                #num_tasks_late_in_tq = len(late_tasks)
                                
                total_tasks_in_tq = node.getTaskQ_level()
                
                if(total_tasks_in_tq>0):
                    proportion_of_tasks_late_in_tq = float(float(num_tasks_late_in_tq)/float(total_tasks_in_tq))            
                    if(proportion_of_tasks_late_in_tq >= SimParams.DYNAMIC_TASK_REMAPPING_THRESHOLD_PERCENTAGE):
                        # get task(s) to remap
                        node_tq = self.RM_instance.node_network.get_Nodes()[node_id].get_TaskQueue()
                        
                        node_tq_lateness_sorted = sorted(node_tq, key=lambda t: t.estimatedLateness_ratiobased(self.env.now, 
                                                                                                      lateness_ratio=SimParams.DYNAMIC_TASK_REMAPPING_TASK_LATE_ESTIM_LATENESS_RATIO),
                                                          reverse=True)
                        #node_tq_lateness_sorted = sorted(node_tq, key=lambda t: t.estimatedLateness_KG(self.env.now), reverse=True)
                        #node_tq_lateness_sorted = sorted(node_tq, key=lambda t: t.estimatedLateness_Div_x(self.env.now), reverse=True)

                        if(len(node_tq_lateness_sorted) > SimParams.DYNAMIC_TASK_REMAPPING_OFFLOAD_NUMTASKS):
                            selected_tasks = node_tq_lateness_sorted[0:SimParams.DYNAMIC_TASK_REMAPPING_OFFLOAD_NUMTASKS]                            
                        else:
                            selected_tasks = node_tq_lateness_sorted
            
                        # which queen to pass to, select randomly from queen list ?
                        if(len(self.node_instance.psalgoprops.get_nearest_queen_pos()) > 0):
                            #selected_node_id = random.choice(self.node_instance.psalgoprops.get_nearest_queen_pos())
                            selected_node_id = self._get_seqentially_from_qlist(self.node_instance.psalgoprops.get_nearest_queen_pos())
                            if selected_node_id != None:
                                selected_node = self.RM_instance.node_network.get_Nodes()[selected_node_id]
                                
                                remapped_tasks_list = []                                
                                # rearrange RM tables
                                for selected_task in selected_tasks:                                    
                                    remapped_tasks_list.append([selected_task, self.node_instance.get_id(), selected_node_id])
                                
                                # update the required remapping data structures
                                self.applyTaskRemapping(remapped_tasks_list)
                                    
                                                        
                        else:
                            Debug.PPrint("%.15f"%self.env.now + "," + self.label + "," + 'taskReMappingDecentSchImpl_RandomQueen:: node=[%d] : queen list empty!!' % (self.node_instance.get_id()), DebugCat.DEBUG_CAT_TASKREMAPPING)
                    else:
                        Debug.PPrint("%.15f"%self.env.now + "," + self.label + "," + 'taskReMappingDecentSchImpl_RandomQueen:: node=[%d] : not enough tasks late to remap!!' % (self.node_instance.get_id()), DebugCat.DEBUG_CAT_TASKREMAPPING)
            
            else:
                #Debug.PPrint("%.15f"%self.env.now + "," + self.label + "," + 'taskReMappingDecentSchImpl_RandomQueen:: node=[%d] : i am a queen, so not going to do any remapping!!' % (self.node_instance.get_id()), DebugCat.DEBUG_CAT_TASKREMAPPING)
                i=1
    
    
    
    
    
    
    #####################################################################################
    # TASKREMAPPINGDECENTSCHEMES_RANDOM_QUEEN_VIA_SYSSLACK
    #####################################################################################
    def taskReMappingDecentSchImpl_RandomQueen_viaSysSlack(self, node_id):
        if(self.remaped_check_count > 0):            
            #Debug.PPrint("%.15f"%self.env.now + "," + self.label + "," + 'taskReMappingDecentSchImpl_RandomQueen:: node=[%d] : going to remap!!' % (self.node_instance.get_id()), DebugCat.DEBUG_CAT_TASKREMAPPING)
            
            # get node
            node = self.RM_instance.node_network.get_Nodes()[node_id]
            
            if(node.psalgoprops.get_node_type() != PSAlgorithmNodetype.QUEEN_BEE):
            
                # we need to decide when to remap ?
                late_tasks = node.get_SystemSlack_GetLateTasks()
                num_tasks_late_in_tq = len(late_tasks)
                                
                #total_tasks_in_tq = node.getTaskQ_level()
                total_tasks_in_tq = len(node.get_SystemSlack_MappedTasks())
                
                if(total_tasks_in_tq>0):
                    proportion_of_tasks_late_in_tq = float(float(num_tasks_late_in_tq)/float(total_tasks_in_tq))            
                    if(proportion_of_tasks_late_in_tq >= SimParams.DYNAMIC_TASK_REMAPPING_THRESHOLD_PERCENTAGE):
                        # get task(s) to remap
                                                
                        node_tq_lateness_sorted = sorted(late_tasks, key=lambda t: t.estimatedLateness_ratiobased(self.env.now, 
                                                                                                      lateness_ratio=SimParams.DYNAMIC_TASK_REMAPPING_TASK_LATE_ESTIM_LATENESS_RATIO),
                                                          reverse=True)
                        
                        if(len(node_tq_lateness_sorted) > SimParams.DYNAMIC_TASK_REMAPPING_OFFLOAD_NUMTASKS):
                            selected_tasks = node_tq_lateness_sorted[0:SimParams.DYNAMIC_TASK_REMAPPING_OFFLOAD_NUMTASKS]                            
                        else:
                            selected_tasks = node_tq_lateness_sorted
            
                        # which queen to pass to, select randomly from queen list ?
                        if(len(self.node_instance.psalgoprops.get_nearest_queen_pos()) > 0):
                            #selected_node_id = random.choice(self.node_instance.psalgoprops.get_nearest_queen_pos())
                            selected_node_id = self._get_seqentially_from_qlist(self.node_instance.psalgoprops.get_nearest_queen_pos())
                            if selected_node_id != None:
                                selected_node = self.RM_instance.node_network.get_Nodes()[selected_node_id]
                                
                                remapped_tasks_list = []                                
                                # rearrange RM tables
                                for selected_task in selected_tasks:                                    
                                    remapped_tasks_list.append([selected_task, self.node_instance.get_id(), selected_node_id])
                                
                                # update the required remapping data structures
                                self.applyTaskRemapping(remapped_tasks_list)
                                                    
                        else:
                            Debug.PPrint("%.15f"%self.env.now + "," + self.label + "," + 'taskReMappingDecentSchImpl_RandomQueen:: node=[%d] : queen list empty!!' % (self.node_instance.get_id()), DebugCat.DEBUG_CAT_TASKREMAPPING)
                    else:
                        Debug.PPrint("%.15f"%self.env.now + "," + self.label + "," + 'taskReMappingDecentSchImpl_RandomQueen:: node=[%d] : not enough tasks late to remap!!' % (self.node_instance.get_id()), DebugCat.DEBUG_CAT_TASKREMAPPING)
            
            else:
                #Debug.PPrint("%.15f"%self.env.now + "," + self.label + "," + 'taskReMappingDecentSchImpl_RandomQueen:: node=[%d] : i am a queen, so not going to do any remapping!!' % (self.node_instance.get_id()), DebugCat.DEBUG_CAT_TASKREMAPPING)
                i=1
    
    
    #####################################################################################
    # TASKREMAPPINGDECENTSCHEMES_LOWESTBLOCKING_QUEEN
    #####################################################################################
    def taskReMappingDecentSchImpl_LowestBlockingQueen(self, node_id):
        Debug.PPrint("%.15f"%self.env.now + "," + self.label + "," + 'taskReMappingDecentSchImpl_LowestBlockingQueen:: node=[%d] : going to remap!!' % (self.node_instance.get_id()), DebugCat.DEBUG_CAT_TASKREMAPPING)
        if(self.remaped_check_count > 0):
            # get node
            node = self.RM_instance.node_network.get_Nodes()[node_id]        
            if(node.psalgoprops.get_node_type() != PSAlgorithmNodetype.QUEEN_BEE):
            
                # we need to decide when to remap ?
                if(node.numLateTasksInTQ(lateness_ratio=SimParams.DYNAMIC_TASK_REMAPPING_TASK_LATE_ESTIM_LATENESS_RATIO) >= SimParams.DYNAMIC_TASK_REMAPPING_THRESHOLD):           
                    # get task(s) to remap
                    node_tq = self.RM_instance.node_network.get_Nodes()[node_id].get_TaskQueue()
                    #node_tq_only_bframes = [t for t in node_tq if t.get_frameType() == "P"]                    
                    node_tq_lateness_sorted = sorted(node_tq, 
                                                     key=lambda t: t.estimatedLateness_ratiobased(self.env.now, 
                                                                                                  lateness_ratio=SimParams.DYNAMIC_TASK_REMAPPING_TASK_LATE_ESTIM_LATENESS_RATIO), reverse=True)
                    
                    if(len(node_tq_lateness_sorted) > SimParams.DYNAMIC_TASK_REMAPPING_OFFLOAD_NUMTASKS):
                        selected_tasks = node_tq_lateness_sorted[0:SimParams.DYNAMIC_TASK_REMAPPING_OFFLOAD_NUMTASKS]
                    else:
                        selected_tasks = node_tq_lateness_sorted
                    
                    # which queen to pass to, select queen that will give the lowest blocking
                    if(len(self.node_instance.psalgoprops.get_nearest_queen_pos()) > 0):
                       
                        remapped_tasks_list = []
                        # rearrange RM tables
                        for selected_task in selected_tasks:                        
                            selected_node_id = self._get_lowest_blocking_q_from_qlist(self.node_instance.psalgoprops.get_nearest_queens_list(),
                                                                                      selected_task.get_priority())     
                            if(selected_node_id != None):                                
                                remapped_tasks_list.append([selected_task, self.node_instance.get_id(), selected_node_id])                                  
                            else:
                                Debug.PPrint("%.15f"%self.env.now + "," + self.label + "," + 'taskReMappingDecentSchImpl_LowestBlockingQueen:: node=[%d] : no queens available!!' % (self.node_instance.get_id()), DebugCat.DEBUG_CAT_TASKREMAPPING)
                    
                        # update the required remapping data structures
                        self.applyTaskRemapping(remapped_tasks_list)
                             
                    else:
                        Debug.PPrint("%.15f"%self.env.now + "," + self.label + "," + 'taskReMappingDecentSchImpl_LowestBlockingQueen:: node=[%d] : queen list empty!!' % (self.node_instance.get_id()), DebugCat.DEBUG_CAT_TASKREMAPPING)
            else:
                #Debug.PPrint("%.15f"%self.env.now + "," + self.label + "," + 'taskReMappingDecentSchImpl_LowestBlockingQueen:: node=[%d] : i am a queen, so not going to do any remapping!!' % (self.node_instance.get_id()), DebugCat.DEBUG_CAT_TASKREMAPPING)
                i=1
                
    #####################################################################################
    # TASKREMAPPINGDECENTSCHEMES_LOWESTBLOCKING_QUEEN_VIASYSSLACK
    #####################################################################################
    def taskReMappingDecentSchImpl_LowestBlockingQueen_viaSysSlack(self, node_id):
        Debug.PPrint("%.15f"%self.env.now + "," + self.label + "," + 'taskReMappingDecentSchImpl_LowestBlockingQueen_viaSysSlack:: node=[%d] : going to remap!!' % (self.node_instance.get_id()), DebugCat.DEBUG_CAT_TASKREMAPPING)
        if(self.remaped_check_count > 0):
            # get node
            node = self.RM_instance.node_network.get_Nodes()[node_id]        
            if(node.psalgoprops.get_node_type() != PSAlgorithmNodetype.QUEEN_BEE):
                            
                # we need to decide when to remap ?
                late_tasks = node.get_SystemSlack_GetLateTasks()
                num_tasks_late_in_tq = len(late_tasks)
                total_tasks_in_tq = len(node.get_SystemSlack_MappedTasks())
                
                selected_tasks = []
                if(total_tasks_in_tq>0):
                    proportion_of_tasks_late_in_tq = float(float(num_tasks_late_in_tq)/float(total_tasks_in_tq))            
                    if(proportion_of_tasks_late_in_tq >= SimParams.DYNAMIC_TASK_REMAPPING_THRESHOLD_PERCENTAGE):
                        # get task(s) to remap  
                        node_tq_lateness_sorted = sorted(late_tasks, key=lambda t: t.estimatedLateness_ratiobased(self.env.now, 
                                                                                                      lateness_ratio=SimParams.DYNAMIC_TASK_REMAPPING_TASK_LATE_ESTIM_LATENESS_RATIO),
                                                                                                      reverse=True)                        
                        if(len(node_tq_lateness_sorted) > SimParams.DYNAMIC_TASK_REMAPPING_OFFLOAD_NUMTASKS):
                            selected_tasks = node_tq_lateness_sorted[0:SimParams.DYNAMIC_TASK_REMAPPING_OFFLOAD_NUMTASKS]                            
                        else:
                            selected_tasks = node_tq_lateness_sorted                        
                    
                    # which queen to pass to, select queen that will give the lowest blocking
                    if(len(self.node_instance.psalgoprops.get_nearest_queen_pos()) > 0):                        
                        remapped_tasks_list = []
                        # rearrange RM tables
                        for selected_task in selected_tasks:                        
                            #selected_node_id = self._get_lowest_blocking_q_from_qlist(self.node_instance.psalgoprops.get_nearest_queens_list(),
                            #                                                           selected_task.get_priority())
                        
#                             selected_node_id = self._get_balanced_blocking_q_from_qlist(self.node_instance.psalgoprops.get_nearest_queens_list(),
#                                                                                       selected_task.get_priority(),selected_task.get_worstCaseComputationCost(),
#                                                                                       node)

                            
#                             selected_node_id = self._get_balanced_blocking_q_from_qlist_v1(self.node_instance.psalgoprops.get_nearest_queens_list(),
#                                                                                        selected_task.get_priority(),  node)
                            
                            if(SimParams.PSALGO_MODEL_QSTATUS_CHECK_MSGS == True):
                                possible_q_list = self._construct_possible_remapp_qlist(self.node_instance.psalgoprops.get_nearest_queens_list(),
                                                                                        selected_task.get_priority(),  node)
                                self.node_instance.psalgoprops.sendQueenStatusMessageRequest(possible_q_list)
                            
                            
                            selected_node_id = self._get_balanced_blocking_q_from_qlist_v3(self.node_instance.psalgoprops.get_nearest_queens_list(),
                                                                                        selected_task.get_priority(),  node)
                             
                            
                            if(selected_node_id != None):                                
                                remapped_tasks_list.append([selected_task, self.node_instance.get_id(), selected_node_id])                                  
                            else:
                                Debug.PPrint("%.15f"%self.env.now + "," + self.label + "," + 'taskReMappingDecentSchImpl_LowestBlockingQueen_viaSysSlack:: node=[%d] : no queens available!!' % (self.node_instance.get_id()), DebugCat.DEBUG_CAT_TASKREMAPPING)
                        
                        # update the required remapping data structures
                        if(len(remapped_tasks_list)>0):
                            self.applyTaskRemapping(remapped_tasks_list)
                            
                            self._debug_node_info(selected_task, self.node_instance.get_id(), selected_node_id)
                            
                             
                    else:
                        Debug.PPrint("%.15f"%self.env.now + "," + self.label + "," + 'taskReMappingDecentSchImpl_LowestBlockingQueen_viaSysSlack:: node=[%d] : queen list empty!!' % (self.node_instance.get_id()), DebugCat.DEBUG_CAT_TASKREMAPPING)
            else:
                #Debug.PPrint("%.15f"%self.env.now + "," + self.label + "," + 'taskReMappingDecentSchImpl_LowestBlockingQueen:: node=[%d] : i am a queen, so not going to do any remapping!!' % (self.node_instance.get_id()), DebugCat.DEBUG_CAT_TASKREMAPPING)
                i=1
    
    #####################################################################################
    # TASKREMAPPINGDECENTSCHEMES_CCP_LMP_REMAPPING
    #####################################################################################
    # go through each node, find tasks that require remapping - late tasks
    # check to see if any other core in the cluster can give lower blocking
    def taskReMappingDecentSchImpl_CCP_Remapping(self, node_id, cluster_id):        
        if(self.node_instance.ccpprops.get_cluster_manager_node_id() == self.node_instance.get_id()):
            Debug.PPrint("%.15f"%self.env.now + "," + self.label + \
                         "," + 'taskReMappingDecentSchImpl_CCP_LMPRemapping:: node=[%d] : going to remap!!' % (self.node_instance.get_id()), DebugCat.DEBUG_CAT_TASKREMAPPING)
        
            nodes_in_cluster = self.node_instance.ccpprops.getClusterNodes(cluster_id)
            
            #pprint.pprint(nodes_in_cluster)
            
            # build a dict of late tasks per cpu-node
            cluster_late_tasks = {}
            for each_node in nodes_in_cluster:
                #print each_node
                late_tasks = each_node.get_SystemSlack_GetLateTasks()
                num_tasks_late_in_tq = len(late_tasks)
                total_tasks_in_tq = len(each_node.get_SystemSlack_MappedTasks())
                if(total_tasks_in_tq>0):
                        proportion_of_tasks_late_in_tq = float(float(num_tasks_late_in_tq)/float(total_tasks_in_tq))
                                   
                        if(proportion_of_tasks_late_in_tq >= 0.5):
                            node_tq_lateness_sorted = sorted(late_tasks, key=lambda t: t.estimatedLateness_ratiobased(self.env.now, 
                                                                                                          lateness_ratio=SimParams.DYNAMIC_TASK_REMAPPING_TASK_LATE_ESTIM_LATENESS_RATIO),
                                                                                                          reverse=True)
                            if (len(node_tq_lateness_sorted) > 0):
                                selected_task = node_tq_lateness_sorted[0]
                                cluster_late_tasks[selected_task.get_id()] = {                                                                              
                                                                              "nodeid": each_node.get_id(),
                                                                              "task" : selected_task,                                                                               
                                                                              }
            
            # dict containing nodes and tasks
            temp_cluster_monitoring_info = copy.copy(self.node_instance.ccpprops.get_cluster_monitoring_info())
            cluster_monitoring_info = self._get_clusterinfo_deepcopy(temp_cluster_monitoring_info)
            
            # go through each late task and see if we can remap them
            remapped_tasks_list = []          
            list_tasks_unremapped = []  
            for tid, v in cluster_late_tasks.iteritems():
                each_task = v["task"]
                old_node_id = v["nodeid"]
                current_blocking = self._get_current_blocking(cluster_monitoring_info[old_node_id]["MPTasks"], 
                                                              each_task.get_priority(), wccc=False)
                current_util = self._get_current_util(cluster_monitoring_info[old_node_id]["MPTasks"], wccc=False)
                
                if(SimParams.CCP_ENABLE_IMPROVEMENT == True):
                    lowest_blocking_node_id = self._get_balanced_blocking_node_from_nodelist_v1(cluster_monitoring_info, each_task.get_priority(), 
                                                                                            current_blocking,  old_node_id,
                                                                                            use_wccc=False, hop_count = 2)
                else:                
                    #lowest_blocking_node_id = self._get_lowest_acc_blocking_node_from_nodelist(cluster_monitoring_info, each_task.get_priority())
                    #lowest_blocking_node_id = self._get_lowest_wcc_blocking_node_from_nodelist(cluster_monitoring_info, each_task.get_priority())
                    lowest_blocking_node_id = self._get_lowest_util_node(cluster_monitoring_info, current_util)
                
                if (lowest_blocking_node_id != old_node_id) and (lowest_blocking_node_id != None):
                    # add to remapped list
                    remapped_tasks_list.append([each_task, old_node_id, lowest_blocking_node_id])
                    # update cluster monitoring information
                    cluster_monitoring_info[old_node_id]["MPTasks"] = self._remove_task_from_list(cluster_monitoring_info[old_node_id]["MPTasks"], each_task)
                    if(lowest_blocking_node_id in cluster_monitoring_info):
                        cluster_monitoring_info[lowest_blocking_node_id]["MPTasks"].append(each_task) 
                  
#                         print "====================="
#                         pprint.pprint(cluster_monitoring_info[lowest_blocking_node_id]["MPTasks"])
#                         print "---"
#                         pprint.pprint(self.node_instance.ccpprops.get_cluster_monitoring_info()[lowest_blocking_node_id]["MPTasks"])
#                         print "====================="                             
                    else:
                        cluster_monitoring_info[lowest_blocking_node_id]= {
                                                                            "MPTasks" : [each_task]                
                                                                           }
                        
                ### LOAN REQUEST ###        
                ##### no new node found, send message to other CMs #### 
                else:
                    temp = [each_task, old_node_id, current_blocking, current_util]
                    list_tasks_unremapped.append(temp)                    
                    
            # update the required remapping data structures
            if(len(remapped_tasks_list)>0):
                self.applyTaskRemapping(remapped_tasks_list)                
                #self._debug_node_info(selected_task, self.node_instance.get_id(), selected_node_id)
            else:
                Debug.PPrint("%.15f"%self.env.now + "," + self.label + "," + \
                             'taskReMappingDecentSchImpl_CCP_LMPRemapping:: node=[%d] : no late tasks in cluster!' % (self.node_instance.get_id()), DebugCat.DEBUG_CAT_TASKREMAPPING)            
            
            # wait and send loan request
            # check if there are other cluster managers first, else no one to send the request to ?
            if(len(self.node_instance.ccpprops.get_list_cluster_manager_ids()) >1):
                if(len(list_tasks_unremapped)>0):
                    self.env.process(self._ccp_send_loan_request_after_delay(list_tasks_unremapped))
        else:            
            #sys.exit("taskReMappingDecentSchImpl_CCP_LMPRemapping :: Error! this is not a cluster manager = " + str(self.node_instance.get_id()))
            i=1 # ignore
    
    
    def _get_clusterinfo_deepcopy(self, cluster_info):
        cm_info = {}
        
        for each_node_k, each_node_v in cluster_info.iteritems():            
            mapped_tasks = []
            for each_task in each_node_v["MPTasks"]:
                new_task = self._clone_task(each_task, each_node_k)
                mapped_tasks.append(new_task)
                
            if(each_node_k not in cm_info):                
                cm_info[each_node_k] = {}
                cm_info[each_node_k]['MPTasks'] = mapped_tasks
        
        return cm_info
        
    
    
                           
                                              
    #####################################################################################
    # TASKREMAPPINGDECENTSCHEMES_CCP_LMP_REMAPPING_V2
    #####################################################################################
    # go through each node, find tasks that require remapping - late tasks
    # 1) get late tasks from each node - sort into lateness order
    # 2) get avg cluster util
    # 3) map late task to lowest util node
    def taskReMappingDecentSchImpl_CCP_Remapping_V2(self, node_id, cluster_id):        
        if(self.node_instance.ccpprops.get_cluster_manager_node_id() == self.node_instance.get_id()):
            Debug.PPrint("%.15f"%self.env.now + "," + self.label + \
                         "," + 'taskReMappingDecentSchImpl_CCP_LMPRemapping:: node=[%d] : going to remap!!' % (self.node_instance.get_id()), DebugCat.DEBUG_CAT_TASKREMAPPING)
        
            nodes_in_cluster = self.node_instance.ccpprops.getClusterNodes(cluster_id)
            
            #pprint.pprint(nodes_in_cluster)
            
            # build a dict of late tasks per cpu-node
            cluster_late_tasks = {}
            for each_node in nodes_in_cluster:
                #print each_node
                late_tasks = each_node.get_SystemSlack_GetLateTasks()
                num_tasks_late_in_tq = len(late_tasks)
                total_tasks_in_tq = len(each_node.get_SystemSlack_MappedTasks())
                if(total_tasks_in_tq>0):
                        proportion_of_tasks_late_in_tq = float(float(num_tasks_late_in_tq)/float(total_tasks_in_tq)) 
                        
                        #print proportion_of_tasks_late_in_tq
                                   
                        if(proportion_of_tasks_late_in_tq >= SimParams.DYNAMIC_TASK_REMAPPING_THRESHOLD_PERCENTAGE):
                            node_tq_lateness_sorted = sorted(late_tasks, key=lambda t: t.estimatedLateness_ratiobased(self.env.now, 
                                                                                                          lateness_ratio=SimParams.DYNAMIC_TASK_REMAPPING_TASK_LATE_ESTIM_LATENESS_RATIO),
                                                                                                          reverse=True)
                            if (len(node_tq_lateness_sorted) > 0):
                                selected_task = node_tq_lateness_sorted[0]
                                cluster_late_tasks[selected_task.get_id()] = {                                                                              
                                                                              "nodeid": each_node.get_id(),
                                                                              "task" : selected_task,                                                                               
                                                                              }
            
            # dict containing nodes and tasks
            cluster_monitoring_info = dict(self.node_instance.ccpprops.get_cluster_monitoring_info())
            
            # go through each late task and see if we can remap them
            remapped_tasks_list = []          
            list_tasks_unremapped = []  
            for tid, v in cluster_late_tasks.iteritems():
                each_task = v["task"]
                old_node_id = v["nodeid"]
                lowest_blocking_node_id = self._get_lowest_wcc_blocking_node_from_nodelist(cluster_monitoring_info, each_task.get_priority())
                
                if(lowest_blocking_node_id != old_node_id):
                    # add to remapped list
                    remapped_tasks_list.append([each_task, old_node_id, lowest_blocking_node_id])
                    # update cluster monitoring information
                    cluster_monitoring_info[old_node_id]["MPTasks"] = self._remove_task_from_list(cluster_monitoring_info[old_node_id]["MPTasks"], each_task)
                    if(lowest_blocking_node_id in cluster_monitoring_info):
                        cluster_monitoring_info[lowest_blocking_node_id]["MPTasks"].append(each_task)
                    else:
                        cluster_monitoring_info[lowest_blocking_node_id]= {
                                                                            "MPTasks" : [each_task]                
                                                                           }
                ### LOAN REQUEST ###        
                ##### no new node found, send message to other CMs #### 
                else:
                    temp = [each_task, old_node_id, self._get_current_blocking(cluster_monitoring_info[old_node_id]["MPTasks"], each_task.get_priority())]
                    list_tasks_unremapped.append(temp)                    
                    
            # update the required remapping data structures
            if(len(remapped_tasks_list)>0):
                self.applyTaskRemapping(remapped_tasks_list)                
                #self._debug_node_info(selected_task, self.node_instance.get_id(), selected_node_id)
            else:
                Debug.PPrint("%.15f"%self.env.now + "," + self.label + "," + \
                             'taskReMappingDecentSchImpl_CCP_LMPRemapping:: node=[%d] : no late tasks in cluster!' % (self.node_instance.get_id()), DebugCat.DEBUG_CAT_TASKREMAPPING)            
            # wait and send loan request
            if(len(list_tasks_unremapped)>0):
                self.env.process(self._ccp_send_loan_request_after_delay(list_tasks_unremapped))
        else:            
            #sys.exit("taskReMappingDecentSchImpl_CCP_LMPRemapping :: Error! this is not a cluster manager = " + str(self.node_instance.get_id()))
            i=1 # ignore
        
    
    
    
    #####################################################################################
    # TASKREMAPPINGDECENTSCHEMES_CCP_LOAN - REQ/REPLY
    #####################################################################################    
    # loan request recieved by other cluster managers, then they start searching 
    # for a suitable loan from their cluster
    def taskReMappingDecentSchImpl_CCP_LoanReq(self, node_id, loan_req_flow, reserved_node_ids):
        if(self.node_instance.ccpprops.get_cluster_manager_node_id() == self.node_instance.get_id()):
            Debug.PPrint("%.15f"%self.env.now + "," + self.label + "," + \
                             'taskReMappingDecentSchImpl_CCP_LoanReq:: node=[%d] : enter!' % (self.node_instance.get_id()), DebugCat.DEBUG_CAT_CCPROTOCOL)
            
            remote_late_task =  loan_req_flow.get_payload_metadata()['late_task']
            original_blocking = loan_req_flow.get_payload_metadata()['current_blocking']       
            
            # dict containing nodes and tasks
            temp_cluster_monitoring_info = copy.copy(self.node_instance.ccpprops.get_cluster_monitoring_info())
            cluster_monitoring_info_orig = self._get_clusterinfo_deepcopy(temp_cluster_monitoring_info)                 
            #cluster_monitoring_info = dict(self.node_instance.ccpprops.get_cluster_monitoring_info())
            
            #print "reserved_node_ids: "
            #print reserved_node_ids
            
            # remove reserved nodes
            cluster_monitoring_info = {}
            for each_nid, each_cminfo_v in cluster_monitoring_info_orig.iteritems():
                if each_nid not in reserved_node_ids:
                    cluster_monitoring_info[each_nid] = cluster_monitoring_info_orig[each_nid]
            
            if(len(cluster_monitoring_info.keys()) >0):
                # find lowest blocking node and then check if it's blocking factor is less than original blocking
                lowest_blocking_node_id = self._get_lowest_wcc_blocking_node_from_nodelist(cluster_monitoring_info, remote_late_task.get_priority())
                lowest_blocking_node_mapped_tasks = cluster_monitoring_info[lowest_blocking_node_id]['MPTasks']
                new_blocking_factor = np.sum([t.get_worstCaseComputationCost() for t in lowest_blocking_node_mapped_tasks if t.get_priority() > remote_late_task.get_priority()])
                
                if(new_blocking_factor < original_blocking):
                    return lowest_blocking_node_id
                else:
                    return None
            else:
                return None
        else:
            sys.exit("taskReMappingDecentSchImpl_CCP_LoanReq :: Error! this is not a cluster manager")
    
    
    def taskReMappingDecentSchImpl_CCP_LoanReq_v2(self, node_id, loan_req_flow, reserved_node_ids, old_node_util):
        if(self.node_instance.ccpprops.get_cluster_manager_node_id() == self.node_instance.get_id()):
            Debug.PPrint("%.15f"%self.env.now + "," + self.label + "," + \
                             'taskReMappingDecentSchImpl_CCP_LoanReq:: node=[%d] : enter!' % (self.node_instance.get_id()), DebugCat.DEBUG_CAT_CCPROTOCOL)
            
            remote_late_task =  loan_req_flow.get_payload_metadata()['late_task']
            original_blocking = loan_req_flow.get_payload_metadata()['current_blocking']   
            old_node_id = loan_req_flow.get_payload_metadata()['slave_node_id']    
            old_node_util = loan_req_flow.get_payload_metadata()['current_util']
            
            # dict containing nodes and tasks
            temp_cluster_monitoring_info = copy.copy(self.node_instance.ccpprops.get_cluster_monitoring_info())
            cluster_monitoring_info_orig = self._get_clusterinfo_deepcopy(temp_cluster_monitoring_info)                 
            #cluster_monitoring_info = dict(self.node_instance.ccpprops.get_cluster_monitoring_info())
            
            #print "reserved_node_ids: "
            #print reserved_node_ids
            
            # remove reserved nodes
            cluster_monitoring_info = {}
            for each_nid, each_cminfo_v in cluster_monitoring_info_orig.iteritems():
                if each_nid not in reserved_node_ids:
                    cluster_monitoring_info[each_nid] = cluster_monitoring_info_orig[each_nid]
            
            if(len(cluster_monitoring_info.keys()) >0):
                # find lowest blocking node and then check if it's blocking factor is less than original blocking
                #lowest_blocking_node_id = self._get_lowest_wcc_blocking_node_from_nodelist(cluster_monitoring_info, remote_late_task.get_priority())
                
                if(SimParams.CCP_ENABLE_IMPROVEMENT == True):
                    lowest_blocking_node_id = self._get_balanced_blocking_node_from_nodelist_v1(cluster_monitoring_info, remote_late_task.get_priority(), 
                                                                                            original_blocking, old_node_id, use_wccc=False)
                else:
                    #lowest_blocking_node_id = self._get_lowest_acc_blocking_node_from_nodelist(cluster_monitoring_info, remote_late_task.get_priority())
                    lowest_blocking_node_id = self._get_lowest_util_node(cluster_monitoring_info, old_node_util)
                    
                return lowest_blocking_node_id
                
            else:
                return None
        else:
            sys.exit("taskReMappingDecentSchImpl_CCP_LoanReq :: Error! this is not a cluster manager")
    
       
       
    # received all replies from node, now pick the nearest slave node
    def taskReMappingDecentSchImpl_CCP_LoanReply(self, remote_slave_list, old_node_id, late_task):
        if(self.node_instance.ccpprops.get_cluster_manager_node_id() == self.node_instance.get_id()):
            Debug.PPrint("%.15f"%self.env.now + "," + self.label + "," + \
                             'taskReMappingDecentSchImpl_CCP_LoanReply:: node=[%d] : enter!' % (self.node_instance.get_id()), DebugCat.DEBUG_CAT_CCPROTOCOL)
            late_task_location = old_node_id
            
            #pprint.pprint(remote_slave_list)            
            slave_distance = {}
            for remote_cm_id, remote_slave_id in remote_slave_list.iteritems():
                if(remote_slave_id != self.node_instance.ccpprops.SLAVE_NOT_FOUND):
                    route = self.RM_instance.interconnect.getRouteXY(late_task_location, remote_slave_id)
                    if(len(route)<=SimParams.CCP_REMOTE_SLAVE_HOPCOUNT):
                        slave_distance[remote_slave_id] = len(route)                        
            
            # look for new remote slave node to remap
            if(len(slave_distance.keys())>0):
                # we found a new node to remap
                min_dist = np.min([v for k,v in slave_distance.iteritems()])
                selected_node_id =  [k for k,v in slave_distance.iteritems() if v==min_dist][0]        
                # notify dispatcher
                remapped_tasks_list = [[late_task, old_node_id, selected_node_id]]            
                self.applyTaskRemapping(remapped_tasks_list)            
                
                # which cluster does this node belong to ?
                selected_node_cluster_id = self.node_instance.ccpprops.getClusterbyNodeID(selected_node_id)
                selected_node_cluster_manager_id = self.node_instance.ccpprops.getClusterManagerByClusterID(selected_node_cluster_id)
                                
                return selected_node_cluster_manager_id 
            else:
                return None
        else:
            sys.exit("taskReMappingDecentSchImpl_CCP_LoanReply :: Error! this is not a cluster manager")
    
    
    
    
    
               
    #####################################################################################
    #####################################################################################
    # HELPER functions
    #####################################################################################  
    
    # construct possible offload queen-list
    def _construct_possible_remapp_qlist(self, queen_list, curr_task_pri, old_node):
        potential_queens = {}
        current_blocking = np.sum([t.get_worstCaseComputationCost() 
                                       for t in old_node.get_SystemSlack_MappedTasks() 
                                       if t.get_priority() > curr_task_pri])
        
        # select the queens that will give less blocking than current blocking
        for k, each_q in queen_list.iteritems():
            # we check if the queen hadn't had any remappings already
            tq_list = each_q['qn_tq_info']            
            blocking_to_self = np.sum([t.get_worstCaseComputationCost() for t in tq_list if t.get_priority() > curr_task_pri])
            blocking_to_others = [t for t in tq_list if t.get_priority() < curr_task_pri]
                
            if(blocking_to_self < current_blocking):
                potential_queens[k] = len(blocking_to_others)
        
        if(len(potential_queens.keys()) > 0):            
            selected_qn_ids = [k for k,v in potential_queens.iteritems()]
            
            return selected_qn_ids
        else:
            return []
    
    
    
    # utilisation of mapped tasks, using actual execution time  
    def _get_actual_utilisation_mapped_tasks(self, node_id):
        node = self.RM_instance.node_network.get_Nodes()[node_id]
        task_q = node.get_SystemSlack_MappedTasks()
        
        cum_util = 0.0
        for each_t in task_q:
            if(each_t.get_taskCompleteTime() != None) and (each_t.get_taskStartTime() != None):
                actual_execution_time = each_t.get_taskCompleteTime() - each_t.get_taskStartTime()
                u = float(actual_execution_time / each_t.get_period())
                cum_util.append(u)
        
        return np.sum(cum_util)
            
        
    def _get_actual_avg_cluster_util(self, cluster_node_ids):
        total_util = 0.0
        for each_node_id in cluster_node_ids:
            node_util = self._get_actual_utilisation_mapped_tasks(each_node_id)
            total_util += node_util
        
        num_nodes = float(len(cluster_node_ids))
        
        if (num_nodes > 0):
            return (total_util/num_nodes)
        else:
            return 0.0
        
    def _get_actual_min_cluster_util(self, cluster_node_ids):
        total_util = 0.0
        for each_node_id in cluster_node_ids:
            node_util = self._get_actual_utilisation_mapped_tasks(each_node_id)
            total_util += node_util
        
            
    def _ccp_send_loan_request_after_delay(self, list_tasks_unremapped):
        
        # wait..
        yield self.env.timeout(SimParams.CCP_LOAN_DELIVERY_MSG_SEND_OFFSET)
        
        #pprint.pprint(list_tasks_unremapped)
        
        ## now service the late tasks that can't be mapped - ask other cluster managers
        if(len(list_tasks_unremapped)>0):
            count = 0
            for each_unremapped_late_task in list_tasks_unremapped:                    
                if(count <SimParams.CCP_LOAN_TASK_AMOUNT):
                    self.node_instance.ccpprops.loanRequest_sendMsg(each_unremapped_late_task[0], 
                                                                    each_unremapped_late_task[1], 
                                                                    each_unremapped_late_task[2], 
                                                                    each_unremapped_late_task[3],
                                                                    update_flw_table = False)                    
                    count += 1
            
            self.RM_instance.flow_table.updateTable(fire=True)
       
    
    def _remove_task_from_list(self, target_list, task_to_be_removed):
        tix = None
        new_list = list(target_list)
        for ix, each_task in enumerate(target_list):
            if(each_task.get_wfid() == task_to_be_removed.get_wfid() and
               each_task.get_video_stream_id() == task_to_be_removed.get_video_stream_id() and
               each_task.get_frameIXinGOP() == task_to_be_removed.get_frameIXinGOP()):
                tix = ix
                break
            
        if(tix != None):            
            del new_list[tix]
            
            return new_list
        else:
            #sys.exit("_remove_task_from_list:: Error !!")
            i=1 
            return new_list
        
    
    
    def _get_current_blocking(self, node_mappedtask_list, target_task_pri, wccc=True):
        if(wccc==True):
            t_all_cc = [t.get_worstCaseComputationCost() for t in node_mappedtask_list if t.get_priority() > target_task_pri]
        else:
            t_all_cc = [(t.get_computationCost()) for t in node_mappedtask_list 
                                    if 
                                    (t.get_priority() > target_task_pri) and
                                    (t.get_taskCompleteTime() != None) and
                                    (t.get_taskStartTime() != None)
                                    ]
        return np.sum(t_all_cc)
    
    
    def _get_current_util(self, node_mappedtask_list, wccc=True):
        if(wccc==True):
            t_all_util = np.sum([(t.get_worstCaseComputationCost()/t.get_period()) 
                          for t in node_mappedtask_list])
        else:
            t_all_util = np.sum([(t.get_computationCost()/t.get_period()) 
                          for t in node_mappedtask_list
                          if (t.get_computationCost() != None)])
        
        return t_all_util
        
        
    
    # wc blocking
    def _get_lowest_wcc_blocking_node_from_nodelist(self, cluster_node_list, target_task_pri):
        
        if len(cluster_node_list.keys()) == 1:
            return cluster_node_list.keys()[0]
            
        cluster_nodes = {}
        for k, v in cluster_node_list.iteritems():
            nid = k
            mapped_tasks = v['MPTasks']
            t_all_wccc = [t.get_worstCaseComputationCost() for t in mapped_tasks if t.get_priority() > target_task_pri]            
            cluster_nodes[k] = np.sum(t_all_wccc)
        
        if(len(cluster_nodes.keys()) != 0):
            min_blocking_result = min(cluster_nodes.values())
            selected_node_id = [k for k,v in cluster_nodes.iteritems() if v==min_blocking_result][0]
            
            return selected_node_id
        else:
            return None
            
    # actual blocking
    def _get_lowest_acc_blocking_node_from_nodelist(self, cluster_node_list, target_task_pri):
        cluster_nodes = {}
        for k, v in cluster_node_list.iteritems():
            nid = k
            mapped_tasks = v['MPTasks']
            
            t_all_wccc = []
            for each_t in mapped_tasks:
                if(each_t.get_taskCompleteTime() != None) and (each_t.get_taskStartTime() != None):
                    if(each_t.get_priority()>target_task_pri):
                        actual_exec_cost = each_t.get_taskCompleteTime() - each_t.get_taskStartTime() 
                        t_all_wccc.append(actual_exec_cost)
            cluster_nodes[k] = np.sum(t_all_wccc)
                        
        if(len(cluster_nodes.keys()) != 0):
            min_blocking_result = min(cluster_nodes.values())
            selected_node_id = [k for k,v in cluster_nodes.iteritems() if v==min_blocking_result][0]
            
            return selected_node_id
        else:
            return None
        
        
    def _get_lowest_util_node(self, cluster_node_list, old_node_util, wccc=False):
        cluster_nodes = {}
        for k, v in cluster_node_list.iteritems():
            nid = k
            mapped_tasks = v['MPTasks']
            
            t_all_util = []
            for each_t in mapped_tasks:
                if (wccc == False):
                    if(each_t.get_computationCost() != None):                    
                        actual_util = (each_t.get_computationCost()/each_t.get_period())
                        t_all_util.append(actual_util)
                else:             
                    actual_util = (each_t.get_worstCaseComputationCost()/each_t.get_period())
                    t_all_util.append(actual_util)
                    
            cluster_nodes[k] = np.sum(t_all_util)
        
        #get min util node
        if(len(cluster_nodes.keys()) != 0):
            min_util_result = min(cluster_nodes.values())
            selected_node_id = [k for k,v in cluster_nodes.iteritems() if v==min_util_result][0]            
            if(min_util_result < old_node_util):
                return selected_node_id
            else:
                return None
        else:
            return None
        
        
    # balanced blocking
    def _get_balanced_blocking_node_from_nodelist_v1(self, cluster_node_list, target_task_pri, current_blocking, old_node_id, use_wccc=True, \
                                                     hop_count=(SimParams.NOC_H + SimParams.NOC_W)):
        cluster_nodes = {}
        for k, v in cluster_node_list.iteritems():
            route = self.RM_instance.interconnect.getRouteXY(old_node_id, k)
            if(len(route) < hop_count):            
                if(self._get_node_slack_wrt_est_relD(cluster_node_list, k) >0):            
                    nid = k
                    mapped_tasks = v['MPTasks']                
                    # get actual self-blocking
                    actual_self_blocking = np.sum([(t.get_computationCost()) for t in mapped_tasks 
                                                                    if( 
                                                                    (t.get_taskCompleteTime() != None) and 
                                                                    (t.get_taskStartTime() != None) and
                                                                    (t.get_priority() > target_task_pri)
                                                                    )])
                    # get worst-case blocking
                    worstcase_self_blocking = np.sum([t.get_worstCaseComputationCost() for t in mapped_tasks 
                                                                    if(                                                            
                                                                    (t.get_priority() > target_task_pri)
                                                                    )])                
                    if(use_wccc==True):
                        self_blocking = worstcase_self_blocking
                    else:
                        self_blocking = actual_self_blocking
                    
                    # get others blocking
                    num_others_blocking = len([ t for t in mapped_tasks if (t.get_priority() < target_task_pri) ])
                    
                    # only take this node, if the blocking it induces is lower
                    if (self_blocking < current_blocking):
                        cluster_nodes[nid] = num_others_blocking                
                        
        if(len(cluster_nodes.keys()) != 0):
            min_others_blocking = min(cluster_nodes.values())
            selected_node_id = [k for k,v in cluster_nodes.iteritems() if v==min_others_blocking][0]
            
            return selected_node_id
        else:
            return None
        
       
        
    
    
    def _get_node_slack_wrt_est_relD(self, cluster_node_list, node_id, normalised=True):
        
        mapped_tasks = cluster_node_list[node_id]['MPTasks']
        cumulative_slack_wrt_est_relD = 0.0
        cumulative_est_relD = 0.0
        for each_task in mapped_tasks:
            if(each_task.get_taskCompleteTime() != None) and (each_task.get_taskStartTime() != None):
                actual_execution_time = each_task.get_taskCompleteTime() - each_task.get_taskStartTime()
                actual_response_time = each_task.get_taskCompleteTime() - each_task.get_dispatchTime()
                wcet = each_task.get_worstCaseComputationCost()     
                
                # task slack according to estimated relative deadline
                task_estimated_relative_deadline = each_task.getEstimatedRelativeDeadline_ratioBased()             
                
                task_slack_wrt_est_relD = task_estimated_relative_deadline - actual_response_time
                cumulative_slack_wrt_est_relD += task_slack_wrt_est_relD
                cumulative_est_relD += task_estimated_relative_deadline # this is the most slack a task can have                    
              
        if(cumulative_est_relD > 0.0):
            normalised_cummulative_slack_wrt_est_relD = float(float(cumulative_slack_wrt_est_relD)/float(cumulative_est_relD))
        else:
            normalised_cummulative_slack_wrt_est_relD = 0.0            
       
        if(normalised == False):
            return cumulative_slack_wrt_est_relD
        else:
            return normalised_cummulative_slack_wrt_est_relD
           
           
           
    
    def _get_lowest_blocking_q_from_qlist(self, queen_list, curr_task_pri):
        queens = {}
        for k, each_q in queen_list.iteritems():
            # we check if the queen hadn't had any remappings already
            if(self.RM_instance.node_network.get_Nodes()[k].importedTasks_countTasks(self.remaped_check_count) < SimParams.DYNAMIC_TASK_REMAPPING_MAX_IMPORTS):
                tq_list = each_q['qn_tq_info']            
                t_all_wccc = [t.get_worstCaseComputationCost() for t in tq_list if t.get_priority() > curr_task_pri]            
                queens[k] = np.sum(t_all_wccc)
        
        if(len(queens.keys()) != 0):
            min_blocking_result = min(queens.values())
            selected_qn_id = [k for k,v in queens.iteritems() if v==min_blocking_result][0]
            
            return selected_qn_id
        else:
            return None
        
    
    def _get_highest_blocking_q_from_qlist(self, queen_list, curr_task_pri):
        queens = {}
        for k, each_q in queen_list.iteritems():
            # we check if the queen hadn't had any remappings already
            if(self.RM_instance.node_network.get_Nodes()[k].importedTasks_countTasks(self.remaped_check_count) < SimParams.DYNAMIC_TASK_REMAPPING_MAX_IMPORTS):
                tq_list = each_q['qn_tq_info']            
                t_all_wccc = [t.get_worstCaseComputationCost() for t in tq_list if t.get_priority() > curr_task_pri]            
                queens[k] = np.sum(t_all_wccc)
        
        if(len(queens.keys()) != 0):
            max_blocking_result = max(queens.values())
            selected_qn_id = [k for k,v in queens.iteritems() if v==max_blocking_result][0]
            
            return selected_qn_id
        else:
            return None
        
    
    def _get_balanced_blocking_q_from_qlist(self, queen_list, curr_task_pri, curr_task_wccc, old_node):
        queens = {}
        for k, each_q in queen_list.iteritems():
            # we check if the queen hadn't had any remappings already
            if(self.RM_instance.node_network.get_Nodes()[k].importedTasks_countTasks(self.remaped_check_count) < SimParams.DYNAMIC_TASK_REMAPPING_MAX_IMPORTS):
                tq_list = each_q['qn_tq_info']            
                blocking_to_self = [t.get_worstCaseComputationCost() for t in tq_list if t.get_priority() > curr_task_pri]
                blocking_to_others = [t for t in tq_list if t.get_priority() < curr_task_pri]                
                cost_funct = np.sum(blocking_to_self) + (curr_task_wccc * len(blocking_to_others))                
                queens[k] = cost_funct
        
        if(len(queens.keys()) != 0):
            min_blocking_result = min(queens.values())
            selected_qn_id = [k for k,v in queens.iteritems() if v==min_blocking_result][0]
            
            return selected_qn_id
        else:
            return None
    
    
    # is current blocking more than the queens blocking, if true, then remap !
    def _get_balanced_blocking_q_from_qlist_v1(self, queen_list, curr_task_pri, old_node):
        queens = {}
        for k, each_q in queen_list.iteritems():
            # we check if the queen hadn't had any remappings already
            if(self.RM_instance.node_network.get_Nodes()[k].importedTasks_countTasks(self.remaped_check_count) < SimParams.DYNAMIC_TASK_REMAPPING_MAX_IMPORTS):
                tq_list = each_q['qn_tq_info']            
                blocking_to_self = [t.get_worstCaseComputationCost() for t in tq_list if t.get_priority() > curr_task_pri]
                queens[k] = np.sum(blocking_to_self)
         
        if(len(queens.keys()) != 0):
            min_blocking_result = min(queens.values())            
            # blocking incurred in current mapping
            #[t.get_worstCaseComputationCost() for t in old_node.get_SystemSlack_MappedTasks() if t.get_priority() > curr_task_pri]
            current_blocking = np.sum([t.get_worstCaseComputationCost() for t in old_node.get_SystemSlack_MappedTasks() if t.get_priority() > curr_task_pri])
             
            if(current_blocking > min_blocking_result):            
                selected_qn_id = [k for k,v in queens.iteritems() if v==min_blocking_result][0]            
                return selected_qn_id   
            else:
                return None
        else:
            return None
        
    
    
    # is current blocking more than the queens blocking, if true, then remap !
    def _get_balanced_blocking_q_from_qlist_v2(self, queen_list, curr_task_pri, old_node):
        queens = {}
        for k, each_q in queen_list.iteritems():
            # we check if the queen hadn't had any remappings already
            if(self.RM_instance.node_network.get_Nodes()[k].importedTasks_countTasks(self.remaped_check_count) < SimParams.DYNAMIC_TASK_REMAPPING_MAX_IMPORTS):
                tq_list = each_q['qn_tq_info']           
                
                blocking_to_self = []
                for each_t in tq_list:
                    if each_t.get_priority() > curr_task_pri:
                        # do we have the actual times ? if so, use these
                        if(each_t.get_taskCompleteTime() != None) and (each_t.get_taskStartTime() != None):
                            actual_execution_time = each_t.get_taskCompleteTime() - each_t.get_taskStartTime()
                            blocking_to_self.append(actual_execution_time)
                        else:
                            blocking_to_self.append(actual_execution_time)
                 
                queens[k] = np.sum(blocking_to_self)
         
        if(len(queens.keys()) != 0):
            min_blocking_result = min(queens.values())            
            # blocking incurred in current mapping
            #[t.get_worstCaseComputationCost() for t in old_node.get_SystemSlack_MappedTasks() if t.get_priority() > curr_task_pri]
            current_blocking = np.sum([t.get_worstCaseComputationCost() for t in old_node.get_SystemSlack_MappedTasks() if t.get_priority() > curr_task_pri])
             
            if(current_blocking > min_blocking_result):            
                selected_qn_id = [k for k,v in queens.iteritems() if v==min_blocking_result][0]            
                return selected_qn_id   
            else:
                return None
        else:
            return None
    
    
    
    def _get_balanced_blocking_q_from_qlist_v3(self, queen_list, curr_task_pri, old_node):
        potential_queens = {}
        current_blocking = np.sum([t.get_worstCaseComputationCost() 
                                       for t in old_node.get_SystemSlack_MappedTasks() 
                                       if t.get_priority() > curr_task_pri])
        
        # select the queens that will give less blocking than current blocking
        for k, each_q in queen_list.iteritems():
            # we check if the queen hadn't had any remappings already
            if(self.RM_instance.node_network.get_Nodes()[k].importedTasks_countTasks(self.remaped_check_count) < SimParams.DYNAMIC_TASK_REMAPPING_MAX_IMPORTS):
                tq_list = each_q['qn_tq_info']            
                blocking_to_self = np.sum([t.get_worstCaseComputationCost() for t in tq_list if t.get_priority() > curr_task_pri])
                blocking_to_others = [t for t in tq_list if t.get_priority() < curr_task_pri]
                
                if(blocking_to_self < current_blocking):
                    potential_queens[k] = len(blocking_to_others)
        
        if(len(potential_queens.keys()) > 0):
            min_blocking_others = min(potential_queens.values())
            selected_qn_id = [k for k,v in potential_queens.iteritems() if v==min_blocking_others][0]
            
            return selected_qn_id
        else:
            return None
    
    
    def _get_balanced_blocking_q_from_qlist_v4(self, queen_list, curr_task_pri, old_node):
        potential_queens = {}
        current_blocking = np.sum([t.get_worstCaseComputationCost() 
                                       for t in old_node.get_SystemSlack_MappedTasks() 
                                       if t.get_priority() > curr_task_pri])
        
        curr_num_low_pri_tasks = len([t for t in old_node.get_SystemSlack_MappedTasks() 
                                       if t.get_priority() < curr_task_pri])
        
        # select the queens that will give less blocking than current blocking
        for k, each_q in queen_list.iteritems():
            # we check if the queen hadn't had any remappings already
            if(self.RM_instance.node_network.get_Nodes()[k].importedTasks_countTasks(self.remaped_check_count) < SimParams.DYNAMIC_TASK_REMAPPING_MAX_IMPORTS):
                tq_list = each_q['qn_tq_info']            
                blocking_to_self = np.sum([t.get_worstCaseComputationCost() for t in tq_list if t.get_priority() > curr_task_pri])
                q_num_low_pri_tasks = len([t for t in tq_list if t.get_priority() < curr_task_pri])
                
                if(blocking_to_self <= current_blocking):
                    if(q_num_low_pri_tasks < curr_num_low_pri_tasks):
                        potential_queens[k] = blocking_to_self
        
        if(len(potential_queens.keys()) > 0):
            min_blocking_self = min(potential_queens.values())
            selected_qn_id = [k for k,v in potential_queens.iteritems() if v==min_blocking_self][0]
            
            return selected_qn_id
        else:
            return None
    
    
    
    
    
    
    def _get_seqentially_from_qlist(self, queen_list):
        chosen_queen = None
        for each_q_node_id in queen_list:
            if(self.RM_instance.node_network.get_Nodes()[each_q_node_id].importedTasks_countTasks(self.remaped_check_count) < SimParams.DYNAMIC_TASK_REMAPPING_MAX_IMPORTS):
                chosen_queen = each_q_node_id
                break
        
        return chosen_queen
    
    
    
    
    def _track_remapped_tasks(self, task, old_node_id, new_node_id):        
        if(SimParams.TRACK_TASK_REMAPPING == True):            
                        
            #queen_node_info = self._debug_queen_info(new_node_id, task)
            queen_node_info = {}
            entry = {
                     't' : self.env.now,
                     'task_info' : ([task.get_frameType(),
                                     task.get_priority(),
                                     task.get_frameIXinGOP(),
                                    task.get_wfid(), 
                                    task.get_video_stream_id()] if task != None else None),
                     'old_nid' : old_node_id,
                     'new_nid' : new_node_id,
                     'queen_pos' : self.node_instance.psalgoprops.get_nearest_queen_pos(),
                     'queen_node_info' : queen_node_info
                                                               
                     }
            
#            print "---- Remapping occured ----"
#            pprint.pprint(entry)
#            print "---------------------------"
            # track remaped tasks
            self.track_remaped_numtasks.append(entry)
            
        
    def _update_vidstrm_mappingtbl(self, frame_gopix, wf_id, strm_id, new_node_id):
        #pprint.pprint(frames_mapping)
        if wf_id in self.RM_instance.vidstream_frames_mapping_table:            
            if(strm_id in self.RM_instance.vidstream_frames_mapping_table[wf_id]):                
                self.RM_instance.vidstream_frames_mapping_table[wf_id][strm_id]['frames_mapping'][frame_gopix] = new_node_id
            else:
                sys.exit("TaskRemapDecentSchemesImpl::_update_vidstrm_mappingtbl: error, strm_id does not exit")
        else:
            sys.exit("TaskRemapDecentSchemesImpl::_update_vidstrm_mappingtbl: error, wf_id does not exit")
  
        
    
    def _get_pseudo_task(self, ix, pri, node_id, strm_specs, tid=0):
                
        pseudo_task = MPEG2FrameTask(self.env, tid,
                 frame_h = strm_specs['frame_h'], frame_w = strm_specs['frame_w'], \
                 frame_rate = strm_specs['fps'], \
                 frame_type = strm_specs['gop_struct'][ix], \
                 frame_ix_in_gop = ix, \
                 gop_struct = strm_specs['gop_struct'], \
                 video_stream_id = strm_specs['vid_strm_id'], \
                 wf_id = strm_specs['wf_id'])
                
        pseudo_task.set_processingCore(node_id)
        pseudo_task.set_priority(pri)
        pseudo_task.set_worstCaseComputationCost(self._get_wcc_of_frame(ix, strm_specs))
        pseudo_task.set_avgCaseComputationCost(self._get_avgcc_of_frame(ix, strm_specs))        
        pseudo_task.set_period(pseudo_task.get_end_to_end_deadline())
                
        return pseudo_task
    
    
    
    def _clone_task(self, orig_task, node_id, tid=0):
        
        frame_h = orig_task.get_frame_h()
        frame_w = orig_task.get_frame_w()
        frame_rate = orig_task.get_framerate()
        frame_type = orig_task.get_frameType()
        gop_struct = orig_task.get_gopstructure()
        gop_ix = orig_task.get_frameIXinGOP()
        vid_strm_id = orig_task.get_video_stream_id()
        wf_id = orig_task.get_wfid()     
        pri = orig_task.get_priority()
        wccc = orig_task.get_worstCaseComputationCost()
        avgcc = orig_task.get_avgCaseComputationCost()
        period = orig_task.get_period()       
        complete_time = orig_task.get_taskCompleteTime()
        start_time = orig_task.get_taskStartTime()
        dispatch_time = orig_task.get_dispatchTime()
        accc = orig_task.get_computationCost()
         
        
        pseudo_task = MPEG2FrameTask(self.env, tid,
                 frame_h = frame_h, frame_w = frame_w, \
                 frame_rate = frame_rate, \
                 frame_type = frame_type, \
                 frame_ix_in_gop = gop_ix, \
                 gop_struct = gop_struct, \
                 video_stream_id = vid_strm_id, \
                 wf_id = wf_id)
                
        pseudo_task.set_processingCore(node_id)
        pseudo_task.set_priority(pri)
        pseudo_task.set_worstCaseComputationCost(wccc)
        pseudo_task.set_avgCaseComputationCost(avgcc)        
        pseudo_task.set_period(period)
        pseudo_task.set_taskCompleteTime(complete_time)
        pseudo_task.set_taskStartTime(start_time)
        pseudo_task.set_dispatchTime(dispatch_time)
        pseudo_task.set_computationCost(accc)
        
                
        return pseudo_task


    def _debug_queen_info(self, queen_node_id, new_task):
        
        queen_info_dict = {}
        
        # current state of the queen ?
        # - cumulative lateness
        # - number of tasks in tq
        tq_cum_lateness = []
        for each_task in self.RM_instance.node_network.get_Nodes()[queen_node_id].get_TaskQueue():
            tq_cum_lateness.append(each_task.estimatedLateness_ratiobased(self.env.now, lateness_ratio=SimParams.DYNAMIC_TASK_REMAPPING_TASK_LATE_ESTIM_LATENESS_RATIO))
            
        queen_info_dict['tq_cum_lateness'] = tq_cum_lateness
        queen_info_dict['tqsize'] = self.RM_instance.node_network.get_Nodes()[queen_node_id].get_TaskQueue()
        
        # what are the tasks that will get affected on the queen (will be blocked by remapping) ?
        blocked_tasks = []
        for each_task in self.RM_instance.node_network.get_Nodes()[queen_node_id].get_TaskQueue():
            if each_task.get_priority() < new_task.get_priority():
                t = {
                     'id' : each_task.get_id(),
                     'pri' : each_task.get_priority(),
                     'type' : each_task.get_frameType(),
                     'wf_strm_id' : (each_task.get_wfid(), each_task.get_video_stream_id()),
                     'estL' :  each_task.estimatedLateness_ratiobased(self.env.now, lateness_ratio=SimParams.DYNAMIC_TASK_REMAPPING_TASK_LATE_ESTIM_LATENESS_RATIO)
                     }
            
                blocked_tasks.append(t)
        
        queen_info_dict["blocked_tasks"] = blocked_tasks
        
        # Which tasks already mapped on the queen node will affect the new task ?
        blocking_tasks = []
        for each_task in self.RM_instance.node_network.get_Nodes()[queen_node_id].get_TaskQueue():
            if each_task.get_priority() > new_task.get_priority():
                t = {
                     'id' : each_task.get_id(),
                     'pri' : each_task.get_priority(),
                     'type' : each_task.get_frameType(),
                     'wf_strm_id' : (each_task.get_wfid(), each_task.get_video_stream_id()),
                     'estL' :  each_task.estimatedLateness_ratiobased(self.env.now, lateness_ratio=SimParams.DYNAMIC_TASK_REMAPPING_TASK_LATE_ESTIM_LATENESS_RATIO)
                     }
            
                blocking_tasks.append(t)
                
        queen_info_dict["blocking_tasks"] = blocking_tasks
        
        
        return queen_info_dict
    
    
    
    
    def _debug_node_info(self, remapped_task, old_node_id, new_node_id):
        
        new_node = self.RM_instance.node_network.get_Nodes()[new_node_id]
        old_node = self.RM_instance.node_network.get_Nodes()[old_node_id]

        records = [] 
        all_node_props = []       
        for each_node in self.RM_instance.node_network.get_Nodes():
            
            # higher-pri tasks, combined wccc
            hp_wccc = np.sum([t.get_worstCaseComputationCost() for t in each_node.get_TaskQueue() if t.get_priority() > remapped_task.get_priority()])            
            # lower-pri tasks (how many)
            lp_count = len([t for t in each_node.get_TaskQueue() if t.get_priority() < remapped_task.get_priority()])            
            # total tq size
            tq_size_now = len(each_node.get_TaskQueue())
            
            each_node_properties = [each_node.get_id(), hp_wccc, lp_count, tq_size_now]            
            all_node_props.append(each_node_properties)
        
        entry = {
                  't' : self.env.now,
                  'all_node_props' : all_node_props,
                  'remapped_task_id' : remapped_task.get_id(),
                  'remapped_task_pri' : remapped_task.get_priority(),
                  'remapped_task_type' : remapped_task.get_frameType(),
                  'new_node_id' : new_node.get_id(),
                  'old_node_id' : old_node.get_id(), 
                  'q_list' :  self.node_instance.psalgoprops.get_nearest_queen_pos()              
                  }
            
        self.track_nodetqinfo_at_remapping_instant.append(entry)
            
            
        
        
    
    
    
    
        