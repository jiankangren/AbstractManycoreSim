import pprint
import sys
import itertools
import simpy
import copy
import random
import time, timeit
import gc
from operator import itemgetter, attrgetter, methodcaller
import operator

import numpy as np
from collections import OrderedDict
import networkx as nx


#from __future__ import print_function
from sys import getsizeof, stderr
from itertools import chain
from collections import deque
try:
    from reprlib import repr
except ImportError:
    pass


from SimParams import SimParams
from TaskMappingSchemes import TaskMappingSchemes
from TaskSemiDynamicPrioritySchemes import TaskSemiDynamicPrioritySchemes
from TaskMappingAndPriAssCombinedSchemes import TaskMappingAndPriAssCombinedSchemes
from TaskTileMappingAndPriAssCombinedSchemes import TaskTileMappingAndPriAssCombinedSchemes
from TaskMappingSchemesImpl import TaskMappingSchemesImpl
from TaskSemiDynamicPrioritySchemesImpl import TaskSemiDynamicPrioritySchemesImpl
from libApplicationModel.MPEG2FrameTask import MPEG2FrameTask
from libNoCModel.NoCFlow import NoCFlow, FlowType
from libApplicationModel.HEVCFrameTask import HEVCFrameTask
from libApplicationModel.Task import TaskModel
import libApplicationModel.HEVCWorkloadParams as HEVCWLP
from MMC import MMC_SmartPortSelectionTypes
from MMCSelectionSchemesImpl import MMCSelectionSchemesImpl

CLUSTERING_CONSTRAINED_NHOPS = 2


# once a stream has entered the system, the frames of the GoPs are mapped. 
# this mapping is fixed throughout the lifetime of the video stream
class TaskTileMappingAndPriAssCombinedSchemesImpl:

    def __init__(self, env, RM_instance):  
        self.env = env
        self.RM_instance = RM_instance
        self.common_priass_schm = None
        
        self.mmc_selector = MMCSelectionSchemesImpl(self.env, self.RM_instance)
        
        # for tracking
        self.track_execution_overhead = []        
        self.track_ccr_level = {}
        
        self.start_timer_pytime = None
        self.start_timer_pyclock = None
        self.start_timer_pytimeit = None
        
        # 3-stage merge count
        self.pp_mapping_info = {}
    
    def taskTileMappPriAssCombinedSchemeHandler(self, strm_specs):
        
        #self.common_priass_schm = self.RM_instance.taskPriAssigner.taskSemiDynPriSch_getFramePriority_FCFS
        self.common_priass_schm = self.RM_instance.taskPriAssigner.taskSemiDynPriSch_getFramePriority_LowestResFirst
        
        if(SimParams.COMBINED_MAPPING_AND_PRIASS == TaskTileMappingAndPriAssCombinedSchemes.TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_RANDOM):
            #self.RM_instance.Mapper.volatileTaskMappingTable_RemoveExpiredTasks_v1()            
            (result1, result2, result3) =  self.taskTileMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPRandom(strm_specs)
        
        ## WITHOUT monitoring ##        
        elif(SimParams.COMBINED_MAPPING_AND_PRIASS == TaskTileMappingAndPriAssCombinedSchemes.TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_MOSTSLACK_VIA_VTMTBL):
            #self.RM_instance.Mapper.volatileTaskMappingTable_RemoveExpiredTasks_v1()            
            (result1, result2, result3) =  self.taskTileMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPMostSlackViaTmTbl_v1(strm_specs)
        
        elif(SimParams.COMBINED_MAPPING_AND_PRIASS == TaskTileMappingAndPriAssCombinedSchemes.TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_CLUSTLS_MOSTSLACK_VIA_VTMTBL):
            #self.RM_instance.Mapper.volatileTaskMappingTable_RemoveExpiredTasks_v1()            
            (result1, result2, result3) =  self.taskTileMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPClusteredTilesMostSlackViaTmTbl_v1(strm_specs)
            
        elif(SimParams.COMBINED_MAPPING_AND_PRIASS == TaskTileMappingAndPriAssCombinedSchemes.TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_CLUSTLS_MOSTSLACK_VIA_VTMTBL_V2):
            #self.RM_instance.Mapper.volatileTaskMappingTable_RemoveExpiredTasks_v1()
            (result1, result2, result3) =  self.taskTileMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPClusteredTilesMostSlackViaTmTbl_v2(strm_specs)
        
                
        elif(SimParams.COMBINED_MAPPING_AND_PRIASS == TaskTileMappingAndPriAssCombinedSchemes.TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_LOWUTIL_VIA_VTMTBL):
            #self.RM_instance.Mapper.volatileTaskMappingTable_RemoveExpiredTasks_woBlocking_v1()
            self.RM_instance.Mapper.volatileTaskMappingTable_RemoveExpiredTasks_v1()            
            (result1, result2, result3) =  self.taskTileMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPLowUtil_v1(strm_specs)
        
        
        # these are the extensions to LU and Clustered
        elif(SimParams.COMBINED_MAPPING_AND_PRIASS == TaskTileMappingAndPriAssCombinedSchemes.TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_LOWUTIL_VIA_VTMTBL_FIRSTFIT):        
            #self.RM_instance.Mapper.volatileTaskMappingTable_RemoveExpiredTasks_v1()  
            self.RM_instance.Mapper.volatileTaskMappingTable_RemoveExpiredTasks_v1()          
            (result1, result2, result3) =  self.taskTileMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPLowUtil_FF(strm_specs)
            
        elif(SimParams.COMBINED_MAPPING_AND_PRIASS == TaskTileMappingAndPriAssCombinedSchemes.TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_CLUSTLS_MOSTSLACK_VIA_VTMTBL_V2_FAKECP):
            #self.RM_instance.Mapper.volatileTaskMappingTable_RemoveExpiredTasks_v1()
            (result1, result2, result3) =  self.taskTileMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPClusteredTilesMostSlackViaTmTbl_v2(strm_specs, use_cp_type=1)
            
        
        elif(SimParams.COMBINED_MAPPING_AND_PRIASS == TaskTileMappingAndPriAssCombinedSchemes.TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_CLUSTLS_MOSTSLACK_VIA_VTMTBL_V2_IPBCP):
            #self.RM_instance.Mapper.volatileTaskMappingTable_RemoveExpiredTasks_v1()
            (result1, result2, result3) =  self.taskTileMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPClusteredTilesMostSlackViaTmTbl_v2(strm_specs, use_cp_type=2)
        
        
        elif(SimParams.COMBINED_MAPPING_AND_PRIASS == TaskTileMappingAndPriAssCombinedSchemes.TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_CLUSTLS_MOSTSLACK_VIA_VTMTBL_V3_IPBCP_FLMP):
            #self.RM_instance.Mapper.volatileTaskMappingTable_RemoveExpiredTasks_v1()
            (result1, result2, result3) =  self.taskTileMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPClusteredTilesMostSlackViaTmTbl_v3(strm_specs, use_cp_type=2, 
                                                                                                                                            )
                
        elif(SimParams.COMBINED_MAPPING_AND_PRIASS == TaskTileMappingAndPriAssCombinedSchemes.TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_CLUSTLS_MOSTSLACK_VIA_VTMTBL_V1_HEIRBFRGROUPS):
            #self.RM_instance.Mapper.volatileTaskMappingTable_RemoveExpiredTasks_v1()
            (result1, result2, result3) =  self.taskTileMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPClusteredTilesHierBGroupsViaTmTbl_v1(strm_specs)
        
        
        elif(SimParams.COMBINED_MAPPING_AND_PRIASS == TaskTileMappingAndPriAssCombinedSchemes.TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_CLUSTLS_MOSTSLACK_VIA_VTMTBL_V1_HEIRBFRGROUPS_FF):
            #self.RM_instance.Mapper.volatileTaskMappingTable_RemoveExpiredTasks_v1()
            (result1, result2, result3) =  self.taskTileMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPClusteredTilesHierBGroupsViaTmTbl_FF_v1(strm_specs)
        
        
        
        
        elif(SimParams.COMBINED_MAPPING_AND_PRIASS == TaskTileMappingAndPriAssCombinedSchemes.TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_CLUSTLS_MOSTSLACK_VIA_VTMTBL_V2_NOCCRFAKECP):
            #self.RM_instance.Mapper.volatileTaskMappingTable_RemoveExpiredTasks_v1()
            nhops_per_frame = strm_specs['gop_tasks'][0].getNumSubTasksTiles()
            (result1, result2, result3) =  self.taskTileMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPClusteredTilesMostSlackViaTmTbl_v2(strm_specs,
                                                                                                    use_cp_type=0, use_avgcc=False, use_fixed_nhops = True,                                                                                                    
                                                                                                    # possible hop values
                                                                                                    fixed_nhops_cp = 1,
                                                                                                    fixed_nhops_tiles = nhops_per_frame,
                                                                                                    fixed_nhops_children = 1,
                                                                                                    )
                
        elif(SimParams.COMBINED_MAPPING_AND_PRIASS == TaskTileMappingAndPriAssCombinedSchemes.TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_GROUPEDTILES_VIA_VTMTBL):
            #self.RM_instance.Mapper.volatileTaskMappingTable_RemoveExpiredTasks_v1()
            (result1, result2, result3) =  self.taskTileMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPClusteredTilesMostSlackViaTmTbl_LUGroupedTiles(strm_specs)
        
        elif(SimParams.COMBINED_MAPPING_AND_PRIASS == TaskTileMappingAndPriAssCombinedSchemes.TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_CLUSTLS_MOSTSLACK_VIA_VTMTBL_V2_FF):
            #self.RM_instance.Mapper.volatileTaskMappingTable_RemoveExpiredTasks_v1()
            (result1, result2, result3) =  self.taskTileMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPClusteredTilesMostSlackViaTmTbl_v2_FF(strm_specs)
        
        
        
        # kaushik et al. preprocessing method
        elif(SimParams.COMBINED_MAPPING_AND_PRIASS == TaskTileMappingAndPriAssCombinedSchemes.TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_KAUSHIK_PP_V2):
            #self.RM_instance.Mapper.volatileTaskMappingTable_RemoveExpiredTasks_v1()
            (result1, result2, result3) =  self.taskTileMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPKaushikPP_v2(strm_specs)
        
        
        ## joint mapping, pri, mmc selection ##
        elif(SimParams.COMBINED_MAPPING_AND_PRIASS == TaskTileMappingAndPriAssCombinedSchemes.TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_NN_MMC_CHILD_OPP_DIR_V1):
            #self.RM_instance.Mapper.volatileTaskMappingTable_RemoveExpiredTasks_v1()
            #(result1, result2, result3) =  self.taskTileMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPKaushikPP_v2(strm_specs)
            i=1            
        
        ## WITH monitoring ##        
        elif(SimParams.COMBINED_MAPPING_AND_PRIASS == TaskTileMappingAndPriAssCombinedSchemes.TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_LOWUTIL_WITHMONITORING_AVGCC_V1):            
            (result1, result2, result3) =  self.taskTileMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPLowUtil_v1(strm_specs, use_avgcc=True)
                 
        elif(SimParams.COMBINED_MAPPING_AND_PRIASS == TaskTileMappingAndPriAssCombinedSchemes.TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_MOSTSLACK_WITHMONITORING_AVGCC_V1):            
            (result1, result2, result3) =  self.taskTileMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPMostSlackViaTmTbl_v1(strm_specs,use_avgcc=True)
                
        elif(SimParams.COMBINED_MAPPING_AND_PRIASS == TaskTileMappingAndPriAssCombinedSchemes.TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_CLUSTLS_MOSTSLACK_WITHMONITORING_AVGCC):
            (result1, result2, result3) =  self.taskTileMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPClusteredTilesMostSlackViaTmTbl_v1(strm_specs, use_avgcc=True)
        
        
        
        
        
        else:
            sys.exit("Error: taskTileMappPriAssCombinedSchemeHandler:: Error: unknown MP scheme")
            
        
        return (result1, result2, result3)
    
    
    
    
    #####################################################################################
    # TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_RANDOM
    #####################################################################################
    # first the vid stream is assigned a frame-level semi-dynamic priority scheme
    # (PR: lowest res first)
    # then,
    # (MP: splits the tasks into tiles, assigns the tiles to PEs randomly)
    def taskTileMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPRandom(self, strm_specs):
        # build pseudo frame-mappings dict
        empty_frame_mappings = self._get_empty_frame_mappings_dict(strm_specs)
        
        # get frame level priorities
        frame_priorities = self.common_priass_schm(strm_specs,empty_frame_mappings)
                     
        # get list of nodes that are free 
        free_nodes_list = self.RM_instance.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL) 
        
        if(len(free_nodes_list)>0):    
            wf_id = strm_specs['wf_id']
            strm_id = strm_specs['vid_strm_id']
            gop_struct = strm_specs['gop_struct']
            gop_tasks = strm_specs['gop_tasks']
            
            # get tile tasks
            all_sorted_hevc_tile_tasks = self._get_sorted_tile_tasks(strm_specs, frame_priorities)

            copy_vtmtbl = self._get_deepcopy_volatiletaskmappingtable()
            copy_vnoctt = self.RM_instance.flow_table.getVNOCTT_copy()
            
            # timing
            if (SimParams.TRACK_MAPPER_EXECOVERHEAD == True):
                self._record_time_start()
            
            # for each item check if it can be accomodated into bin_i           
            tile_pri_assignment = {} 
            tile_to_node_mapping = OrderedDict()            
            for each_tile_task_id, each_tile_task in all_sorted_hevc_tile_tasks.iteritems():
                # assign to node with max cumslack
                selected_node_id = random.choice(free_nodes_list).get_id()                
                
                # update local copy of vtmtbl
                if (selected_node_id not in copy_vtmtbl):
                    copy_vtmtbl[selected_node_id] = [self._get_vtmtbl_targettiletask_entry(each_tile_task, selected_node_id, 
                                                                                       each_tile_task.get_priority())]
                else:
                    copy_vtmtbl[selected_node_id].append(self._get_vtmtbl_targettiletask_entry(each_tile_task, selected_node_id, 
                                                                                           each_tile_task.get_priority()))                                
                # update frame mapping struct                
                tile_to_node_mapping[each_tile_task_id] = selected_node_id
                
                # record pri-ass for the tile
                tile_pri_assignment[each_tile_task_id] = each_tile_task.get_priority()            
            
            
            # update mmc node mapping table
            mmc_mapping = self._map_to_mmc_mappingtbl(tile_to_node_mapping, all_sorted_hevc_tile_tasks, copy_vnoctt)
            
            # timing
            if (SimParams.TRACK_MAPPER_EXECOVERHEAD == True):
                self._record_time_stop()
            
            self.mmc_selector._populate_VNOCTT(gop_tasks, all_sorted_hevc_tile_tasks, 
                                   tile_to_node_mapping, mmc_mapping, 
                                   gop_tasks[0].get_adaptiveGoP_Obj(), 
                                   gop_tasks[0].getNumSubTasksTiles())
            
            
            
            # update the processing core on the tile tasks objects
            for each_t_id, each_t in all_sorted_hevc_tile_tasks.iteritems():
                all_sorted_hevc_tile_tasks[each_t_id].set_processingCore(tile_to_node_mapping[each_t_id])
            
            
            # update task mapping table    
            self._map_to_vidstrm_tile_mappingtbl_overwrite(tile_to_node_mapping, tile_pri_assignment, wf_id, strm_id)                            
            
            return (tile_to_node_mapping, tile_pri_assignment, self.tiletasks_list_to_dict(all_sorted_hevc_tile_tasks.values()))
        else:
            return (None, None)
    
    
    #############################################################################################
    # TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_CLUSTLS_MOSTSLACK_VIA_VTMTBL_V2
    #############################################################################################
    # first the vid stream is assigned a frame-level semi-dynamic priority scheme
    # (PR: lowest res first)
    # then,
    # (MP: splits the tasks into tiles, assigns the tiles to the PEs)
    # use only WCRS heuristic - cluster tiles together
    def taskTileMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPClusteredTilesMostSlackViaTmTbl_v2(self, strm_specs,
                                                                                                    use_cp_type=0, 
                                                                                                    use_avgcc=False,
                                                                                                    
                                                                                                    # for situaions where hop count is zero
                                                                                                    # do we 'only' take 1 PE (high blocking) or
                                                                                                    # make it flexible so that neughbours can 
                                                                                                    # be selected (at random)
                                                                                                    # this param tells how much flexibility
                                                                                                    use_flexi_hop0_placement = -1,
                                                                                                    
                                                                                                    # possible hop values
                                                                                                    use_fixed_nhops = False,
                                                                                                    fixed_nhops_cp = -1,
                                                                                                    fixed_nhops_tiles = -1,
                                                                                                    fixed_nhops_children = -1,
                                                                                                    ):
        # build pseudo frame-mappings dict
        empty_frame_mappings = self._get_empty_frame_mappings_dict(strm_specs)
        
        # get frame level priorities
        frame_priorities = self.common_priass_schm(strm_specs,empty_frame_mappings)
                     
        # get list of nodes that are free
        free_nodes_list_nids = [n.get_id() for n in self.RM_instance.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL)]
        #inner_nodes = self.RM_instance.interconnect.getInnerNodes_1border()
        inner_nodes = free_nodes_list_nids         
        
        # initialise pass_flags
        special_condition_1_cp = False
        
        if(len(inner_nodes)>0):    
            wf_id = strm_specs['wf_id']
            strm_id = strm_specs['vid_strm_id']
            gop_tasks = strm_specs['gop_tasks']            
            
            # (1) sort tasks into dependency order - perform topological sort on the graph
            # (2) map critical path tasks together
            # (3) map tile and child tasks at nhop distances
            all_sorted_hevc_tile_tasks = self._get_sorted_tile_tasks(strm_specs, frame_priorities)
            
            copy_vtmtbl = self._get_deepcopy_volatiletaskmappingtable()            
            copy_vnoctt = self.RM_instance.flow_table.getVNOCTT_copy()
                      
            # timing
            if (SimParams.TRACK_MAPPER_EXECOVERHEAD == True):
                self._record_time_start()
                       
            #copy_vmtblusagetbl = self._get_deepcopy_nodeusage_volatiletaskmappingtable()                
            
            n_tiles_all = len(all_sorted_hevc_tile_tasks.keys())
            temp_tile_id = all_sorted_hevc_tile_tasks.keys()[0]
            n_tiles_per_frame = all_sorted_hevc_tile_tasks[temp_tile_id].getNumSubTasksTiles()
            
            cp_fix_list = self._get_critical_path(use_cp_type, gop_tasks[0].get_adaptiveGoP_Obj())                                
            cp_tile_task_ids = [t.get_id() for tid, t in all_sorted_hevc_tile_tasks.iteritems() if t.get_frameIXinGOP() in cp_fix_list]
            cp_gop_seq = [ft.get_frameType() for ft in gop_tasks if ft.get_frameIXinGOP() in cp_fix_list]
            
            if (use_fixed_nhops == False):            
                (NHOPS_CP, 
                 NHOPS_TILES, 
                 NHOPS_CHILDREN) = self._get_ccr_specific_nhops(gop_tasks, n_tiles_all, n_tiles_per_frame, cp_str=cp_gop_seq)
            else:
                if (fixed_nhops_cp == -1) or (fixed_nhops_tiles == -1) or (fixed_nhops_children == -1):
                    sys.exit("Error - taskTileMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPClusteredTilesMostSlackViaTmTbl_v2 :: invalid nhops")
                else:
                    NHOPS_CP = fixed_nhops_cp
                    NHOPS_TILES =  fixed_nhops_tiles
                    NHOPS_CHILDREN = fixed_nhops_children
            
            print (NHOPS_CP,  NHOPS_TILES, NHOPS_CHILDREN)
            
            # ----------------- intelligent bit : start ---------------------------------------------------------------------                       
            tile_pri_assignment = {} 
            tile_to_node_mapping = OrderedDict() 
            tile_00_node_id = None
            
            for each_tile_task_id, each_tile_task in all_sorted_hevc_tile_tasks.iteritems():
                ### CRITICAL-PATH TASKS ###    
                if each_tile_task_id in cp_tile_task_ids:
                    if tile_00_node_id == None: # first tile of root task                        
                        selected_node_id = self._get_node_with_min_lowpriblocking(copy_vtmtbl, inner_nodes, each_tile_task.get_priority(),
                                                                                copy_vmtblusagetbl=None, 
                                                                                use_avgcc=use_avgcc, selection_type='least_util',
                                                                                running_tile_mappings = tile_to_node_mapping,
                                                                                number_of_total_tiles = n_tiles_all)                        
                        tile_00_node_id = selected_node_id
                    
                    # other tiles of other tasks in CP
                    else:
                        nearest_nhop_node_nids = self.RM_instance.interconnect.getNodesNHops_fast(tile_00_node_id,NHOPS_CP)                               
                        if len(nearest_nhop_node_nids) == 0: nearest_nhop_node_nids.append(tile_00_node_id) # if empty add the target pe
                                         
                        if len(nearest_nhop_node_nids)>1:
                            # get node with max_wcrs (default to LU if none)
                            selected_node_id = self._get_node_with_min_lowpriblocking(copy_vtmtbl, nearest_nhop_node_nids, 
                                                                                      each_tile_task.get_priority(),
                                                                                copy_vmtblusagetbl=None, 
                                                                                use_avgcc=use_avgcc, selection_type='least_util',
                                                                                running_tile_mappings = tile_to_node_mapping,
                                                                                number_of_total_tiles = n_tiles_all)                            
                        else:
                            # if flexible placement is enabled, then dont always choose a single node #
                            if use_flexi_hop0_placement == -1:
                                selected_node_id = nearest_nhop_node_nids[0]
                            elif use_flexi_hop0_placement > 0:
                                tmp_selction = self.RM_instance.interconnect.getNodesNHops_fast(nearest_nhop_node_nids[0], 1,
                                                                                                limit_result=use_flexi_hop0_placement)
                                tmp_selction.append(nearest_nhop_node_nids[0])
                                selected_node_id = np.random.choice(tmp_selction) #@UndefinedVariable
                            else:
                                sys.exit("Error - taskTileMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPClusteredTilesMostSlackViaTmTbl_v2 :: invalid use_flexi_hop0_placement")
                    
                ### NON - CRITICAL-PATH TASKS ### 
                else:                    
                    # map tile 0 of a task to the closest parent
                    if ("_0" in each_tile_task_id): 
                        # get parent with highest data volume                     
                        # sort parents according to their payload
                        # find nhop nodes for each parent, and then find the intersection between these nodes      
                        tile_task_parents = each_tile_task.get_expected_data_from_parents()   
                        significant_parent_tid = self._get_parent_with_highest_probable_payload(tile_task_parents, all_sorted_hevc_tile_tasks)
                        
                        p_nid = tile_to_node_mapping[significant_parent_tid] # nid of highest payload parent
                        
                        assert(p_nid < (SimParams.NOC_W*SimParams.NOC_H)), "%d, %d" %(p_nid, SimParams.NOC_W*SimParams.NOC_H)  
                                                 
                        set_nhops_p_i = self.RM_instance.interconnect.getNodesNHops_fast(p_nid,NHOPS_CHILDREN)                        
                        if len(set_nhops_p_i) == 0: set_nhops_p_i.append(p_nid) # if empty add the target pe
                        
                        selected_node_id = self._get_node_with_min_lowpriblocking(copy_vtmtbl, set_nhops_p_i, 
                                                                                each_tile_task.get_priority(),
                                                                                copy_vmtblusagetbl=None, 
                                                                                use_avgcc=use_avgcc, 
                                                                                selection_type='least_util',
                                                                                running_tile_mappings = tile_to_node_mapping,
                                                                                number_of_total_tiles = n_tiles_all)
                        
                    else:
                        # map other tiles close to the first tile of task
                        tile_x0_task_id = "%d_%d" % (each_tile_task.getTileParentFrameId(), 0) 
                        if tile_x0_task_id not in tile_to_node_mapping: sys.exit("Error - order of tiles invalid")
                        tile_x0_node_id = tile_to_node_mapping[tile_x0_task_id]
                        set_nhops_tile_x0_i = self.RM_instance.interconnect.getNodesNHops_fast(tile_x0_node_id,NHOPS_TILES) # nodes close to first tile of task                        
                        if len(set_nhops_tile_x0_i) == 0: set_nhops_tile_x0_i.append(tile_x0_node_id) # if empty add the target pe
                        
                        # we search these nodes for the one with the highest worst-case slack
                        if len(set_nhops_tile_x0_i)>1:
                            selected_node_id = self._get_node_with_min_lowpriblocking(copy_vtmtbl, set_nhops_tile_x0_i, 
                                                                                    each_tile_task.get_priority(),
                                                                                    copy_vmtblusagetbl=None, 
                                                                                    use_avgcc=use_avgcc, selection_type='least_util',
                                                                                    running_tile_mappings = tile_to_node_mapping,
                                                                                    number_of_total_tiles = n_tiles_all)
                        else:           
                            # if flexible placement is enabled, then dont always choose a single node #                 
                            if use_flexi_hop0_placement == -1:
                                selected_node_id = set_nhops_tile_x0_i[0]
                            elif use_flexi_hop0_placement > 0:
                                tmp_selction = self.RM_instance.interconnect.getNodesNHops_fast(set_nhops_tile_x0_i[0], 1,
                                                                                                limit_result=use_flexi_hop0_placement)
                                tmp_selction.append(set_nhops_tile_x0_i[0])
                                selected_node_id = np.random.choice(tmp_selction) #@UndefinedVariable
                            else:
                                sys.exit("Error - taskTileMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPClusteredTilesMostSlackViaTmTbl_v2 :: invalid use_flexi_hop0_placement")
     
                            
                assert(selected_node_id != None), ", no node was selected !!"
                
                ## updates to local copies of structures ##                
                # update local copy of vtmtbl
                if (selected_node_id not in copy_vtmtbl):
                    copy_vtmtbl[selected_node_id] = [self._get_vtmtbl_targettiletask_entry(each_tile_task, selected_node_id, 
                                                                                       each_tile_task.get_priority())]
                else:
                    copy_vtmtbl[selected_node_id].append(self._get_vtmtbl_targettiletask_entry(each_tile_task, selected_node_id, 
                                                                                           each_tile_task.get_priority()))    
                # update local copy of node usage table
                #copy_vmtblusagetbl[selected_node_id] += each_tile_task.get_worstCaseComputationCost()                
                                            
                # update frame mapping struct
                tile_task_id = each_tile_task.get_id()
                tile_to_node_mapping[tile_task_id] = selected_node_id
                
                # record pri-ass for the tile
                tile_pri_assignment[tile_task_id] = each_tile_task.get_priority()
            
           
            # ----------------- intelligent bit : end  ---------------------------------------------------------------------
            
            # update mmc node mapping table
            mmc_mapping = self._map_to_mmc_mappingtbl(tile_to_node_mapping, all_sorted_hevc_tile_tasks, copy_vnoctt)
            
            # timing
            if (SimParams.TRACK_MAPPER_EXECOVERHEAD == True):
                self._record_time_stop()
            
            
            self.mmc_selector._populate_VNOCTT(gop_tasks, all_sorted_hevc_tile_tasks, 
                                   tile_to_node_mapping, mmc_mapping, 
                                   gop_tasks[0].get_adaptiveGoP_Obj(), 
                                   gop_tasks[0].getNumSubTasksTiles())
            
            # update the processing core on the tile tasks objects
            for each_t_id, each_t in all_sorted_hevc_tile_tasks.iteritems():
                all_sorted_hevc_tile_tasks[each_t_id].set_processingCore(tile_to_node_mapping[each_t_id])            
            
            assert (len(all_sorted_hevc_tile_tasks.keys()) == (gop_tasks[0].getNumSubTasksTiles()*len(gop_tasks[0].get_gopstructure()))), \
             ":: incorrect number of tiles - %d, %d" %(len(all_sorted_hevc_tile_tasks.keys()),
                                                    (gop_tasks[0].getNumSubTasksTiles()*len(gop_tasks[0].get_gopstructure())))
               
            # update task mapping table    
            self._map_to_vidstrm_tile_mappingtbl_overwrite(tile_to_node_mapping, tile_pri_assignment, wf_id, strm_id)     
                                               
            return (tile_to_node_mapping, tile_pri_assignment, self.tiletasks_list_to_dict(all_sorted_hevc_tile_tasks.values()))
        else:
            return (None, None)    
    
    #############################################################################################
    # TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_CLUSTLS_MOSTSLACK_VIA_VTMTBL_V3_IPBCP_FLMP
    #############################################################################################
    # first the vid stream is assigned a frame-level semi-dynamic priority scheme
    # (PR: lowest res first)
    # then,
    # (MP: splits the tasks into tiles, assigns the tiles to the PEs)
    # use only WCRS heuristic - cluster tiles together
    def taskTileMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPClusteredTilesMostSlackViaTmTbl_v3(self, strm_specs,
                                                                                                    use_cp_type=0, 
                                                                                                    use_avgcc=False,
                                                                                                    
                                                                                                    # for situaions where hop count is zero
                                                                                                    # do we 'only' take 1 PE (high blocking) or
                                                                                                    # make it flexible so that neughbours can 
                                                                                                    # be selected (at random)
                                                                                                    # this param tells how much flexibility
                                                                                                    use_flexi_hop0_placement = -1,
                                                                                                    
                                                                                                    # possible hop values
                                                                                                    use_fixed_nhops = False,
                                                                                                    fixed_nhops_cp = -1,
                                                                                                    fixed_nhops_tiles = -1,
                                                                                                    fixed_nhops_children = -1,
                                                                                                    ):
        # build pseudo frame-mappings dict
        empty_frame_mappings = self._get_empty_frame_mappings_dict(strm_specs)
        
        # get frame level priorities
        frame_priorities = self.common_priass_schm(strm_specs,empty_frame_mappings)
                     
        # get list of nodes that are free
        free_nodes_list_nids = [n.get_id() for n in self.RM_instance.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL)]
        #inner_nodes = self.RM_instance.interconnect.getInnerNodes_1border()
        inner_nodes = free_nodes_list_nids         
        
        # initialise pass_flags
        special_condition_1_cp = False
        
        if(len(inner_nodes)>0):    
            wf_id = strm_specs['wf_id']
            strm_id = strm_specs['vid_strm_id']
            gop_tasks = strm_specs['gop_tasks']            
            
            # (1) sort tasks into dependency order - perform topological sort on the graph
            # (2) map critical path tasks together
            # (3) map tile and child tasks at nhop distances
            all_sorted_hevc_tile_tasks = self._get_sorted_tile_tasks(strm_specs, frame_priorities)
            
            copy_vtmtbl = self._get_deepcopy_volatiletaskmappingtable()
            copy_vnoctt = self.RM_instance.flow_table.getVNOCTT_copy()
            #copy_vmtblusagetbl = self._get_deepcopy_nodeusage_volatiletaskmappingtable()
                   
            # timing
            if (SimParams.TRACK_MAPPER_EXECOVERHEAD == True):
                self._record_time_start()
            
            n_tiles_all = len(all_sorted_hevc_tile_tasks.keys())
            temp_tile_id = all_sorted_hevc_tile_tasks.keys()[0]
            n_tiles_per_frame = all_sorted_hevc_tile_tasks[temp_tile_id].getNumSubTasksTiles()
            
            cp_fix_list = self._get_critical_path(use_cp_type, gop_tasks[0].get_adaptiveGoP_Obj())                                
            cp_tile_task_ids = [t.get_id() for tid, t in all_sorted_hevc_tile_tasks.iteritems() if t.get_frameIXinGOP() in cp_fix_list]
            cp_gop_seq = [ft.get_frameType() for ft in gop_tasks if ft.get_frameIXinGOP() in cp_fix_list]
            
            if (use_fixed_nhops == False):            
                (NHOPS_CP, 
                 NHOPS_TILES, 
                 NHOPS_CHILDREN) = self._get_ccr_specific_nhops(gop_tasks, n_tiles_all, n_tiles_per_frame, cp_str=cp_gop_seq)
            else:
                if (fixed_nhops_cp == -1) or (fixed_nhops_tiles == -1) or (fixed_nhops_children == -1):
                    sys.exit("Error - taskTileMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPClusteredTilesMostSlackViaTmTbl_v2 :: invalid nhops")
                else:
                    NHOPS_CP = fixed_nhops_cp
                    NHOPS_TILES =  fixed_nhops_tiles
                    NHOPS_CHILDREN = fixed_nhops_children
                    
            
            print (NHOPS_CP,  NHOPS_TILES, NHOPS_CHILDREN)
            
            # ----------------- intelligent bit : start ---------------------------------------------------------------------                       
            tile_pri_assignment = {} 
            tile_to_node_mapping = OrderedDict() 
            tile_00_node_id = None
            
            for each_tile_task_id, each_tile_task in all_sorted_hevc_tile_tasks.iteritems():
                ### CRITICAL-PATH TASKS ###    
                if each_tile_task_id in cp_tile_task_ids:
                    if tile_00_node_id == None: # first tile of root task                        
                        selected_node_id = self._get_node_min_balanced_blocking(copy_vtmtbl, inner_nodes, each_tile_task.get_priority(), 
                                                                                each_tile_task.get_worstCaseComputationCost(),
                                                                                copy_vmtblusagetbl=None, 
                                                                                use_avgcc=use_avgcc, selection_type='least_util',
                                                                                running_tile_mappings = tile_to_node_mapping,
                                                                                number_of_total_tiles = n_tiles_all)                        
                        tile_00_node_id = selected_node_id
                    
                    # other tiles of other tasks in CP
                    else:
                        nearest_nhop_node_nids = self.RM_instance.interconnect.getNodesNHops_fast(tile_00_node_id,NHOPS_CP)
                        nearest_nhop_node_nids.append(tile_00_node_id)                        
                        if len(nearest_nhop_node_nids)>1:
                            # get node with max_wcrs (default to LU if none)
                            selected_node_id = self._get_node_min_balanced_blocking(copy_vtmtbl, nearest_nhop_node_nids, 
                                                                                      each_tile_task.get_priority(), 
                                                                                each_tile_task.get_worstCaseComputationCost(),
                                                                                copy_vmtblusagetbl=None, 
                                                                                use_avgcc=use_avgcc, selection_type='least_util',
                                                                                running_tile_mappings = tile_to_node_mapping,
                                                                                number_of_total_tiles = n_tiles_all)                            
                        else:
                            # if flexible placement is enabled, then dont always choose a single node #
                            if use_flexi_hop0_placement == -1:
                                selected_node_id = nearest_nhop_node_nids[0]
                            elif use_flexi_hop0_placement > 0:
                                tmp_selction = self.RM_instance.interconnect.getNodesNHops_fast(nearest_nhop_node_nids[0], 1,
                                                                                                limit_result=use_flexi_hop0_placement)
                                tmp_selction.append(nearest_nhop_node_nids[0])
                                selected_node_id = np.random.choice(tmp_selction) #@UndefinedVariable
                            else:
                                sys.exit("Error - taskTileMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPClusteredTilesMostSlackViaTmTbl_v2 :: invalid use_flexi_hop0_placement")
                    
                ### NON - CRITICAL-PATH TASKS ### 
                else:                    
                    # map tile 0 of a task to the closest parent
                    if ("_0" in each_tile_task_id): 
                        # get parent with highest data volume                     
                        # sort parents according to their payload
                        # find nhop nodes for each parent, and then find the intersection between these nodes      
                        tile_task_parents = each_tile_task.get_expected_data_from_parents()              
                        sorted_parents_by_payload_list = sorted(tile_task_parents.items(), key=itemgetter(1)) # tuples (pid, payload)                        
                        
                        assert len(sorted_parents_by_payload_list) >0
                        p_nid = tile_to_node_mapping[sorted_parents_by_payload_list[0][0]] # nid of highest payload parent
                        assert(p_nid < (SimParams.NOC_W*SimParams.NOC_H)), "%d, %d" %(p_nid, SimParams.NOC_W*SimParams.NOC_H)  
                                                 
                        set_nhops_p_i = self.RM_instance.interconnect.getNodesNHops_fast(p_nid,NHOPS_CHILDREN)
                        set_nhops_p_i.append(p_nid)
                        
                        selected_node_id = self._get_node_min_balanced_blocking(copy_vtmtbl, set_nhops_p_i, 
                                                                                      each_tile_task.get_priority(), 
                                                                                each_tile_task.get_worstCaseComputationCost(),
                                                                                copy_vmtblusagetbl=None, 
                                                                                use_avgcc=use_avgcc, 
                                                                                selection_type='least_util',
                                                                                running_tile_mappings = tile_to_node_mapping,
                                                                                number_of_total_tiles = n_tiles_all)
                        
                    else:
                        # map other tiles close to the first tile of task
                        tile_x0_task_id = "%d_%d" % (each_tile_task.getTileParentFrameId(), 0) 
                        if tile_x0_task_id not in tile_to_node_mapping: sys.exit("Error - order of tiles invalid")
                        tile_x0_node_id = tile_to_node_mapping[tile_x0_task_id]
                        set_nhops_tile_x0_i = self.RM_instance.interconnect.getNodesNHops_fast(tile_x0_node_id,NHOPS_TILES) # nodes close to first tile of task
                        set_nhops_tile_x0_i.append(tile_x0_node_id)
                        
                        # we search these nodes for the one with the highest worst-case slack
                        if len(set_nhops_tile_x0_i)>1:
                            selected_node_id = self._get_node_min_balanced_blocking(copy_vtmtbl, set_nhops_tile_x0_i, 
                                                                                      each_tile_task.get_priority(),                                                                                       
                                                                                each_tile_task.get_worstCaseComputationCost(),
                                                                        copy_vmtblusagetbl=None, 
                                                                        use_avgcc=use_avgcc, selection_type='least_util',
                                                                        running_tile_mappings = tile_to_node_mapping,
                                                                        number_of_total_tiles = n_tiles_all)
                        else:           
                            # if flexible placement is enabled, then dont always choose a single node #                 
                            if use_flexi_hop0_placement == -1:
                                selected_node_id = set_nhops_tile_x0_i[0]
                            elif use_flexi_hop0_placement > 0:
                                tmp_selction = self.RM_instance.interconnect.getNodesNHops_fast(set_nhops_tile_x0_i[0], 1,
                                                                                                limit_result=use_flexi_hop0_placement)
                                tmp_selction.append(set_nhops_tile_x0_i[0])
                                selected_node_id = np.random.choice(tmp_selction) #@UndefinedVariable
                            else:
                                sys.exit("Error - taskTileMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPClusteredTilesMostSlackViaTmTbl_v2 :: invalid use_flexi_hop0_placement")
     
                            
                assert(selected_node_id != None), ", no node was selected !!"
                
                ## updates to local copies of structures ##                
                # update local copy of vtmtbl
                if (selected_node_id not in copy_vtmtbl):
                    copy_vtmtbl[selected_node_id] = [self._get_vtmtbl_targettiletask_entry(each_tile_task, selected_node_id, 
                                                                                       each_tile_task.get_priority())]
                else:
                    copy_vtmtbl[selected_node_id].append(self._get_vtmtbl_targettiletask_entry(each_tile_task, selected_node_id, 
                                                                                           each_tile_task.get_priority()))    
                # update local copy of node usage table
                #copy_vmtblusagetbl[selected_node_id] += each_tile_task.get_worstCaseComputationCost()                
                                            
                # update frame mapping struct
                tile_task_id = each_tile_task.get_id()
                tile_to_node_mapping[tile_task_id] = selected_node_id
                
                # record pri-ass for the tile
                tile_pri_assignment[tile_task_id] = each_tile_task.get_priority()
                
            # ----------------- intelligent bit : end  ---------------------------------------------------------------------
            
            # update mmc node mapping table
            mmc_mapping = self._map_to_mmc_mappingtbl(tile_to_node_mapping, all_sorted_hevc_tile_tasks, copy_vnoctt)
            
           
            # timing
            if (SimParams.TRACK_MAPPER_EXECOVERHEAD == True):
                self._record_time_stop()
                
            
            self.mmc_selector._populate_VNOCTT(gop_tasks, all_sorted_hevc_tile_tasks, 
                                   tile_to_node_mapping, mmc_mapping, 
                                   gop_tasks[0].get_adaptiveGoP_Obj(), 
                                   gop_tasks[0].getNumSubTasksTiles())
            
            
            
            # update the processing core on the tile tasks objects
            for each_t_id, each_t in all_sorted_hevc_tile_tasks.iteritems():
                all_sorted_hevc_tile_tasks[each_t_id].set_processingCore(tile_to_node_mapping[each_t_id])            
            
            assert (len(all_sorted_hevc_tile_tasks.keys()) == (gop_tasks[0].getNumSubTasksTiles()*len(gop_tasks[0].get_gopstructure()))), \
             ":: incorrect number of tiles - %d, %d" %(len(all_sorted_hevc_tile_tasks.keys()),
                                                    (gop_tasks[0].getNumSubTasksTiles()*len(gop_tasks[0].get_gopstructure())))
               
            # update task mapping table    
            self._map_to_vidstrm_tile_mappingtbl_overwrite(tile_to_node_mapping, tile_pri_assignment, wf_id, strm_id)     
                                               
            return (tile_to_node_mapping, tile_pri_assignment, self.tiletasks_list_to_dict(all_sorted_hevc_tile_tasks.values()))
        else:
            return (None, None)
    
    
    
    
    #################################################################################################
    # TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_CLUSTLS_MOSTSLACK_VIA_VTMTBL_V1_HEIRBFRGROUPS
    #################################################################################################
    # first the vid stream is assigned a frame-level semi-dynamic priority scheme
    # (PR: lowest res first)
    # then,
    # (MP: splits the tasks into tiles, assigns the tiles to the PEs)
    # cluster B-groups together
    def taskTileMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPClusteredTilesHierBGroupsViaTmTbl_v1(self, strm_specs,                                                                                                     
                                                                                                    use_avgcc=False):
        
        # build pseudo frame-mappings dict
        empty_frame_mappings = self._get_empty_frame_mappings_dict(strm_specs)
        
        # get frame level priorities
        frame_priorities = self.common_priass_schm(strm_specs,empty_frame_mappings)
                     
        # get list of nodes that are free
        free_nodes_list_nids = [n.get_id() for n in self.RM_instance.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL)]
        #inner_nodes = self.RM_instance.interconnect.getInnerNodes_1border()
        inner_nodes = free_nodes_list_nids         
        
                
        
        if(len(inner_nodes)>0):    
            wf_id = strm_specs['wf_id']
            strm_id = strm_specs['vid_strm_id']
            gop_tasks = strm_specs['gop_tasks']            
            
            # (1) sort tasks into dependency order - perform topological sort on the graph
            # (2) map critical path tasks together
            # (3) map tile and child tasks at nhop distances
            all_sorted_hevc_tile_tasks = self._get_sorted_tile_tasks(strm_specs, frame_priorities)
            
            copy_vtmtbl = self._get_deepcopy_volatiletaskmappingtable()
            copy_vnoctt = self.RM_instance.flow_table.getVNOCTT_copy()
            #copy_vmtblusagetbl = self._get_deepcopy_nodeusage_volatiletaskmappingtable() 
            
                    
            # timing
            if (SimParams.TRACK_MAPPER_EXECOVERHEAD == True):
                self._record_time_start()
            
            n_tiles_all = len(all_sorted_hevc_tile_tasks.keys())
            temp_tile_id = all_sorted_hevc_tile_tasks.keys()[0]
            n_tiles_per_frame = all_sorted_hevc_tile_tasks[temp_tile_id].getNumSubTasksTiles()
                        
            # get b-groups
            bgroupings_2dlist, bgroupings_dict = gop_tasks[0].get_adaptiveGoP_Obj().getGroupedGop(all_sorted_hevc_tile_tasks[temp_tile_id].get_gopstructure())
            
            cp_str = "I" + "P"*gop_tasks[0].get_gopstructure().count("P")
            
            (NHOPS_GP, 
             NHOPS_GT 
             ) = self._get_ccr_specific_nhops_bgroup_mapping(gop_tasks, n_tiles_all, n_tiles_per_frame, cp_str=cp_str)
            
            print (NHOPS_GP,  NHOPS_GT)
            
            # ----------------- intelligent bit : start ---------------------------------------------------------------------                       
            tile_pri_assignment = {} 
            tile_to_node_mapping = OrderedDict() 
            tile_00_node_id = None
            
            #pprint.pprint(bgroupings_dict)
            
            ############################################
            # Step 1 : Assign tile tasks into B-groups
            ############################################   
            group_tile_tasks = {}         
            for each_tile_task_id, each_tile_task in all_sorted_hevc_tile_tasks.iteritems():
                selected_node_id = None
                gop_level_task_lbl =  each_tile_task.get_frameType() + str(each_tile_task.get_frameIXinGOP())                
                bgroup_ix = bgroupings_dict[gop_level_task_lbl][0]
                bgroup_primetask = bgroupings_dict[gop_level_task_lbl][1]
                bgroup_primetask_gopix = int(bgroup_primetask[1:])
                bgroup_primetask_tile_taskid = "%d_0" % gop_tasks[bgroup_primetask_gopix].get_id()
                
                ## set group ix
                all_sorted_hevc_tile_tasks[each_tile_task_id].set_bpyramid_ix(bgroup_ix)
                
                ## set group primary task                
                all_sorted_hevc_tile_tasks[each_tile_task_id].set_bpyramid_primary_task(
                                                                                        (bgroup_primetask_tile_taskid, bgroup_primetask)   # tuple                                                                                     
                                                                                       )
                
                if bgroup_ix not in group_tile_tasks:
                    group_tile_tasks[bgroup_ix] = [each_tile_task_id]
                else:
                    group_tile_tasks[bgroup_ix].append(each_tile_task_id)
                
            
            #######################################################
            # Step 2 : Map tile tasks to PEs, according to Bgroups
            #######################################################
            group_mapped_node_ids = {}
            for each_tile_task_id, each_tile_task in all_sorted_hevc_tile_tasks.iteritems():
                current_bgroup_ix = each_tile_task.get_bpyramid_ix()
                #### first group ?
                if current_bgroup_ix == 0:
                    
                    # primary task of first group ? (i.e. I0_0)
                    if each_tile_task.get_id() == each_tile_task.get_bpyramid_primary_task()[0]:
                        selected_node_id = self._get_node_with_min_lowpriblocking(copy_vtmtbl, inner_nodes, each_tile_task.get_priority(),
                                                                            copy_vmtblusagetbl=None, 
                                                                            use_avgcc=use_avgcc, selection_type='least_util',
                                                                            running_tile_mappings = tile_to_node_mapping,
                                                                            number_of_total_tiles = n_tiles_all)
                        
                        #print "here - pt of fg"
                    
                    
                    # other task of first group ?
                    else:
                        pe_of_group_primarytask = tile_to_node_mapping[each_tile_task.get_bpyramid_primary_task()[0]]
                        possible_nodes = self.RM_instance.interconnect.getNodesNHops_fast(pe_of_group_primarytask, NHOPS_GT) # nodes close to first tile of task                            
                        possible_nodes.append(pe_of_group_primarytask)
                        selected_node_id = self._get_node_lowest_util_viavmtbl(copy_vtmtbl, possible_nodes)
                        
                        #print "here - ot of fg"
                
                #### other group ?
                else:                                        
                    # primary task of other group ?
                    if each_tile_task.get_id() == each_tile_task.get_bpyramid_primary_task()[0]:
                        prev_group_ix = current_bgroup_ix-1
                        prev_group_ptask_tile_id = group_tile_tasks[prev_group_ix][0]  
                                                
                        pe_of_prev_group_primarytask = tile_to_node_mapping[prev_group_ptask_tile_id]
                        possible_nodes_set_1 = self.RM_instance.interconnect.getNodesExactNHops_fast(pe_of_prev_group_primarytask, NHOPS_GP) # nodes close to first tile of task
                        
                        assert(len(possible_nodes_set_1)>0), "possible_nodes_set_1 is empty : " + str(NHOPS_GP) + ", " + str(pe_of_prev_group_primarytask)
                        
                        set_nodes_already_used_by_allprev_groups = set(list(itertools.chain(*[v for k,v in group_mapped_node_ids.iteritems() if k != current_bgroup_ix])))
                        set_nodes_already_used_by_prevgroup = set(list(itertools.chain(*[v for k,v in group_mapped_node_ids.iteritems() if k == current_bgroup_ix-1])))
                                                                        
                        # PE ranking based search
                        pe_ranks = {}
                        pe_ranks_more_space = {}
                        for each_node_id in possible_nodes_set_1:
                            valid_nhopgt_nodes = self.RM_instance.interconnect.getNodesNHops_fast(each_node_id, NHOPS_GT)
                            unsed_nodes = set(valid_nhopgt_nodes) - set_nodes_already_used_by_allprev_groups
                            if len(unsed_nodes) >0:
                                rank = float(len(unsed_nodes))/float(len(valid_nhopgt_nodes))
                                pe_ranks[each_node_id] = rank
                            else:
                                unsed_nodes = set(valid_nhopgt_nodes) - set_nodes_already_used_by_prevgroup
                                rank = float(len(unsed_nodes))/float(len(valid_nhopgt_nodes))
                                pe_ranks[each_node_id] = rank
                                
                            # more space direction ?
                            pe_ranks_more_space[each_node_id] = len(valid_nhopgt_nodes)
                                
                        
                        # if none have pe_ranks (positive int), we map to the direction which has most space
                        if set(pe_ranks.values()) == set([0]):
                            pe_ranks = pe_ranks_more_space
                            
#                             for each_node_id in possible_nodes_set_1:
#                                 valid_nhopgt_nodes = self.RM_instance.interconnect.getNodesNHops_fast(each_node_id, NHOPS_GT)
#                                 pe_ranks[each_node_id] = len(valid_nhopgt_nodes)

                        
                        assert(len(pe_ranks.values()) > 0), "pe_ranks still is empty !!" + str(NHOPS_GP) + ", " + str(len(possible_nodes_set_1))
                        
                        # get max ranked nodes list
                        max_rank = np.max(pe_ranks.values())
                        possible_nodes = [k for k,v in pe_ranks.iteritems() if v == max_rank]
                        selected_node_id = self._get_node_with_min_lowpriblocking(copy_vtmtbl, possible_nodes, each_tile_task.get_priority(),
                                                                            copy_vmtblusagetbl=None, 
                                                                            use_avgcc=use_avgcc, selection_type='least_util',
                                                                            running_tile_mappings = tile_to_node_mapping,
                                                                            number_of_total_tiles = n_tiles_all)
                        #print "here - pt of og"
                        
                    
                    # other task of other group ?
                    else:
                        pe_of_group_primarytask = tile_to_node_mapping[each_tile_task.get_bpyramid_primary_task()[0]]
                        possible_nodes = self.RM_instance.interconnect.getNodesNHops_fast(pe_of_group_primarytask, NHOPS_GT) # nodes close to first tile of task                            
                        possible_nodes.append(pe_of_group_primarytask)
                        selected_node_id = self._get_node_lowest_util_viavmtbl(copy_vtmtbl, possible_nodes)
                
                        #print "here - ot of og"
                        
                        
                        
                # check mapped node is not None            
                assert(selected_node_id != None), ", no node was selected !!"
                
                ## updates to local copies of structures ##                
                # update local copy of vtmtbl
                if (selected_node_id not in copy_vtmtbl):
                    copy_vtmtbl[selected_node_id] = [self._get_vtmtbl_targettiletask_entry(each_tile_task, selected_node_id, 
                                                                                       each_tile_task.get_priority())]
                else:
                    copy_vtmtbl[selected_node_id].append(self._get_vtmtbl_targettiletask_entry(each_tile_task, selected_node_id, 
                                                                                           each_tile_task.get_priority()))    
                # update local copy of node usage table
                #copy_vmtblusagetbl[selected_node_id] += each_tile_task.get_worstCaseComputationCost()                
                                            
                # update frame mapping struct
                tile_task_id = each_tile_task.get_id()
                tile_to_node_mapping[tile_task_id] = selected_node_id
                
                if current_bgroup_ix not in group_mapped_node_ids:
                    group_mapped_node_ids[current_bgroup_ix] = [selected_node_id]
                else:
                    group_mapped_node_ids[current_bgroup_ix].append(selected_node_id)
                
                
                # record pri-ass for the tile
                tile_pri_assignment[tile_task_id] = each_tile_task.get_priority()
                
            # ----------------- intelligent bit : end  ---------------------------------------------------------------------
            
            # update mmc node mapping table
            mmc_mapping = self._map_to_mmc_mappingtbl(tile_to_node_mapping, all_sorted_hevc_tile_tasks, copy_vnoctt)
            
            # timing
            if (SimParams.TRACK_MAPPER_EXECOVERHEAD == True):
                self._record_time_stop()
            
            
            self.mmc_selector._populate_VNOCTT(gop_tasks, all_sorted_hevc_tile_tasks, 
                                   tile_to_node_mapping, mmc_mapping, 
                                   gop_tasks[0].get_adaptiveGoP_Obj(), 
                                   gop_tasks[0].getNumSubTasksTiles())
            
            # update the processing core on the tile tasks objects
            for each_t_id, each_t in all_sorted_hevc_tile_tasks.iteritems():
                all_sorted_hevc_tile_tasks[each_t_id].set_processingCore(tile_to_node_mapping[each_t_id])            
            
            assert (len(all_sorted_hevc_tile_tasks.keys()) == (gop_tasks[0].getNumSubTasksTiles()*len(gop_tasks[0].get_gopstructure()))), \
             ":: incorrect number of tiles - %d, %d" %(len(all_sorted_hevc_tile_tasks.keys()),
                                                    (gop_tasks[0].getNumSubTasksTiles()*len(gop_tasks[0].get_gopstructure())))
               
            # update task mapping table    
            self._map_to_vidstrm_tile_mappingtbl_overwrite(tile_to_node_mapping, tile_pri_assignment, wf_id, strm_id)     
                                               
            return (tile_to_node_mapping, tile_pri_assignment, self.tiletasks_list_to_dict(all_sorted_hevc_tile_tasks.values()))
        else:
            return (None, None)
        
    
    
    
    #################################################################################################
    # TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_CLUSTLS_MOSTSLACK_VIA_VTMTBL_V1_HEIRBFRGROUPS_FF
    #################################################################################################
    # first the vid stream is assigned a frame-level semi-dynamic priority scheme
    # (PR: lowest res first)
    # then,
    # (MP: splits the tasks into tiles, assigns the tiles to the PEs)
    # cluster B-groups together
    def taskTileMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPClusteredTilesHierBGroupsViaTmTbl_FF_v1(self, strm_specs,                                                                                                     
                                                                                                    use_avgcc=False):
        
        # build pseudo frame-mappings dict
        empty_frame_mappings = self._get_empty_frame_mappings_dict(strm_specs)
        
        # get frame level priorities
        frame_priorities = self.common_priass_schm(strm_specs,empty_frame_mappings)
                     
        # get list of nodes that are free
        free_nodes_list_nids = [n.get_id() for n in self.RM_instance.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL)]
        #inner_nodes = self.RM_instance.interconnect.getInnerNodes_1border()
        inner_nodes = free_nodes_list_nids         
                        
        
        if(len(inner_nodes)>0):    
            wf_id = strm_specs['wf_id']
            strm_id = strm_specs['vid_strm_id']
            gop_tasks = strm_specs['gop_tasks']            
            
            # (1) sort tasks into dependency order - perform topological sort on the graph
            # (2) map critical path tasks together
            # (3) map tile and child tasks at nhop distances
            all_sorted_hevc_tile_tasks = self._get_sorted_tile_tasks(strm_specs, frame_priorities)
            
            copy_vtmtbl = self._get_deepcopy_volatiletaskmappingtable()
            copy_vnoctt = self.RM_instance.flow_table.getVNOCTT_copy()
            #copy_vmtblusagetbl = self._get_deepcopy_nodeusage_volatiletaskmappingtable()  
                    
            # timing
            if (SimParams.TRACK_MAPPER_EXECOVERHEAD == True):
                self._record_time_start()
            
            n_tiles_all = len(all_sorted_hevc_tile_tasks.keys())
            temp_tile_id = all_sorted_hevc_tile_tasks.keys()[0]
            n_tiles_per_frame = all_sorted_hevc_tile_tasks[temp_tile_id].getNumSubTasksTiles()
                        
            # get b-groups
            bgroupings_2dlist, bgroupings_dict = gop_tasks[0].get_adaptiveGoP_Obj().getGroupedGop(all_sorted_hevc_tile_tasks[temp_tile_id].get_gopstructure())
              
            (NHOPS_GP, 
             NHOPS_GT 
             ) = self._get_ccr_specific_nhops_bgroup_mapping(gop_tasks, n_tiles_all, n_tiles_per_frame)
            
            print (NHOPS_GP,  NHOPS_GT)
            
            # ----------------- intelligent bit : start ---------------------------------------------------------------------                       
            tile_pri_assignment = {} 
            tile_to_node_mapping = OrderedDict() 
            
            
            #pprint.pprint(bgroupings_dict)
            
            ############################################
            # Step 1 : Assign tile tasks into B-groups
            ############################################   
            group_tile_tasks = {}         
            for each_tile_task_id, each_tile_task in all_sorted_hevc_tile_tasks.iteritems():
                selected_node_id = None
                gop_level_task_lbl =  each_tile_task.get_frameType() + str(each_tile_task.get_frameIXinGOP())                
                bgroup_ix = bgroupings_dict[gop_level_task_lbl][0]
                bgroup_primetask = bgroupings_dict[gop_level_task_lbl][1]
                bgroup_primetask_gopix = int(bgroup_primetask[1:])
                bgroup_primetask_tile_taskid = "%d_0" % gop_tasks[bgroup_primetask_gopix].get_id()
                
                ## set group ix
                all_sorted_hevc_tile_tasks[each_tile_task_id].set_bpyramid_ix(bgroup_ix)
                
                ## set group primary task                
                all_sorted_hevc_tile_tasks[each_tile_task_id].set_bpyramid_primary_task(
                                                                                        (bgroup_primetask_tile_taskid, bgroup_primetask)   # tuple                                                                                     
                                                                                       )
                
                if bgroup_ix not in group_tile_tasks:
                    group_tile_tasks[bgroup_ix] = [each_tile_task_id]
                else:
                    group_tile_tasks[bgroup_ix].append(each_tile_task_id)
                
            
            #######################################################
            # Step 2 : get sorted PEs (util, min LP tasks) 
            #######################################################
            
            sorted_nodes_in_numlptasksorder = self._get_nodes_sorted_lowpriblockingorder(copy_vtmtbl, 
                                                                                         inner_nodes, 
                                                                                         all_sorted_hevc_tile_tasks[temp_tile_id].get_priority())
            
            #sorted_nodes_in_luorder = self._get_nodes_sorted_LU_order(copy_vtmtbl, 
            #                                                          inner_nodes)
            
            
            
            #######################################################
            # Step 3 : Map tile tasks to PEs, according to Bgroups
            #######################################################
            group_mapped_node_ids = {}
            sorted_pes_for_fg_ot = [] # cycle list
            sorted_pes_for_og_ot = [] # cycle list
            
            track_all_group_PEs = []
            track_prev_group_PEs = []
            
            for each_tile_task_id, each_tile_task in all_sorted_hevc_tile_tasks.iteritems():
                current_bgroup_ix = each_tile_task.get_bpyramid_ix()
                #### first group ?
                if current_bgroup_ix == 0:
                    
                    # primary task of first group ? (i.e. I0_0)
                    if each_tile_task.get_id() == each_tile_task.get_bpyramid_primary_task()[0]:
                        selected_node_id = sorted_nodes_in_numlptasksorder[0]
                                                
                        # obtain sorted PEs for the other tasks in the first group
                        tmp_sorted_pes_for_fg_ot =  self.RM_instance.interconnect.getNodesNHops_fast(selected_node_id, NHOPS_GT)
                        tmp_sorted_pes_for_fg_ot.append(selected_node_id)
                        #tmp_sorted_pes_for_fg_ot.sort(key=sorted_nodes_in_luorder.index)                        
                        sorted_pes_for_fg_ot = itertools.cycle(tmp_sorted_pes_for_fg_ot)
                        
                    
                    # other task of first group ?
                    else: 
                        selected_node_id = sorted_pes_for_fg_ot.next()
                       
                
                #### other group ?
                else:                                        
                    # primary task of other group ?
                    if each_tile_task.get_id() == each_tile_task.get_bpyramid_primary_task()[0]: 
                        prev_group_ix = current_bgroup_ix-1
                        prev_group_ptask_tile_id = group_tile_tasks[prev_group_ix][0]  
                                                
                        pe_of_prev_group_primarytask = tile_to_node_mapping[prev_group_ptask_tile_id]
                        possible_nodes_set_1 = self.RM_instance.interconnect.getNodesExactNHops_fast(pe_of_prev_group_primarytask, NHOPS_GP) # nodes close to first tile of task
                        
                        assert(len(possible_nodes_set_1)>0), "possible_nodes_set_1 is empty : " + str(NHOPS_GP) + ", " + str(pe_of_prev_group_primarytask)
                        
                        
#                         #set_nodes_already_used_by_allprev_groups = set(list(itertools.chain(*[v for k,v in group_mapped_node_ids.iteritems() if k != current_bgroup_ix])))
#                         #set_nodes_already_used_by_prevgroup = set(list(itertools.chain(*[v for k,v in group_mapped_node_ids.iteritems() if k == current_bgroup_ix-1])))
#                         
#                         assert(len(track_prev_group_PEs) > 0), "Error: track_prev_group_PEs"
#                         assert(len(track_all_group_PEs) > 0), "Error: track_all_group_PEs"                        
#                         set_nodes_already_used_by_allprev_groups = set(track_all_group_PEs) # faster
#                         set_nodes_already_used_by_prevgroup = set(track_prev_group_PEs) # faster
#                                                                         
#                         # PE ranking based search
#                         pe_ranks = {}
#                         pe_ranks_more_space = {}
#                         for each_node_id in possible_nodes_set_1:
#                             valid_nhopgt_nodes = self.RM_instance.interconnect.getNodesNHops_fast(each_node_id, NHOPS_GT)
#                             unsed_nodes = set(valid_nhopgt_nodes) - set_nodes_already_used_by_allprev_groups
#                             if len(unsed_nodes) >0:
#                                 rank = float(len(unsed_nodes))/float(len(valid_nhopgt_nodes))
#                                 pe_ranks[each_node_id] = rank
#                             else:
#                                 unsed_nodes = set(valid_nhopgt_nodes) - set_nodes_already_used_by_prevgroup
#                                 rank = float(len(unsed_nodes))/float(len(valid_nhopgt_nodes))
#                                 pe_ranks[each_node_id] = rank
#                             
#                             # more space direction ?
#                             pe_ranks_more_space[each_node_id] = len(valid_nhopgt_nodes)
#                                                     
#                         # if none have pe_ranks, we map to the direction which has most space
#                         if set(pe_ranks.values()) == set([0]):
#                             pe_ranks = pe_ranks_more_space                            
#                             
#                         assert(len(pe_ranks.values()) > 0), "pe_ranks still is empty !!" + str(NHOPS_GP) + ", " + str(len(possible_nodes_set_1))
#                         
#                         # get max ranked nodes list
#                         max_rank = np.max(pe_ranks.values())
#                         possible_nodes = [k for k,v in pe_ranks.iteritems() if v == max_rank]
                        
                        unused_nodes_prev =  set(possible_nodes_set_1) - set(track_prev_group_PEs)
                        unsed_nodes_all = set(possible_nodes_set_1) - set(track_all_group_PEs)
                        
                        if len(unsed_nodes_all)>0:                        
                            possible_nodes = list(unsed_nodes_all)
                        elif len(unused_nodes_prev)>0:
                            possible_nodes = list(unused_nodes_prev)
                        else:
                            possible_nodes = possible_nodes_set_1
                        
                        assert(len(possible_nodes)>0), "Error - possible_nodes empty"
                        
                        possible_nodes.sort(key=sorted_nodes_in_numlptasksorder.index)
                        selected_node_id = possible_nodes[0]
                        
                        
#                         selected_node_id = self._get_node_with_min_lowpriblocking(copy_vtmtbl, possible_nodes, each_tile_task.get_priority(),
#                                                                             copy_vmtblusagetbl=None, 
#                                                                             use_avgcc=use_avgcc, selection_type='least_util',
#                                                                             running_tile_mappings = tile_to_node_mapping,
#                                                                             number_of_total_tiles = n_tiles_all)
                        
                        # obtain sorted PEs for the other tasks in the other group
                        tmp_sorted_pes_for_og_ot =  self.RM_instance.interconnect.getNodesNHops_fast(selected_node_id, NHOPS_GT)
                        tmp_sorted_pes_for_og_ot.append(selected_node_id)
                        #tmp_sorted_pes_for_og_ot.sort(key=sorted_nodes_in_luorder.index)                        
                        sorted_pes_for_og_ot = itertools.cycle(tmp_sorted_pes_for_og_ot) 
                        
                        track_prev_group_PEs = [] # reset
                        
                    # other task of other group ?
                    else:
                        selected_node_id = sorted_pes_for_og_ot.next()
                
                        
                        
                # check mapped node is not None            
                assert(selected_node_id != None), ", no node was selected !!"
                
                ## updates to local copies of structures ##                
                # update local copy of vtmtbl
                if (selected_node_id not in copy_vtmtbl):
                    copy_vtmtbl[selected_node_id] = [self._get_vtmtbl_targettiletask_entry(each_tile_task, selected_node_id, 
                                                                                       each_tile_task.get_priority())]
                else:
                    copy_vtmtbl[selected_node_id].append(self._get_vtmtbl_targettiletask_entry(each_tile_task, selected_node_id, 
                                                                                           each_tile_task.get_priority()))    
                # update local copy of node usage table
                #copy_vmtblusagetbl[selected_node_id] += each_tile_task.get_worstCaseComputationCost()                
                                            
                # update frame mapping struct
                tile_task_id = each_tile_task.get_id()
                tile_to_node_mapping[tile_task_id] = selected_node_id
                
                if current_bgroup_ix not in group_mapped_node_ids:
                    group_mapped_node_ids[current_bgroup_ix] = [selected_node_id]
                else:
                    group_mapped_node_ids[current_bgroup_ix].append(selected_node_id)
                
                track_all_group_PEs.append(selected_node_id)
                track_prev_group_PEs.append(selected_node_id)
                
                
                # record pri-ass for the tile
                tile_pri_assignment[tile_task_id] = each_tile_task.get_priority()
                
            # ----------------- intelligent bit : end  ---------------------------------------------------------------------
            
            # update mmc node mapping table
            mmc_mapping = self._map_to_mmc_mappingtbl(tile_to_node_mapping, all_sorted_hevc_tile_tasks, copy_vnoctt)
            
            # timing
            if (SimParams.TRACK_MAPPER_EXECOVERHEAD == True):
                self._record_time_stop()
            
            
            self.mmc_selector._populate_VNOCTT(gop_tasks, all_sorted_hevc_tile_tasks, 
                                   tile_to_node_mapping, mmc_mapping, 
                                   gop_tasks[0].get_adaptiveGoP_Obj(), 
                                   gop_tasks[0].getNumSubTasksTiles())
           
            
            # update the processing core on the tile tasks objects
            for each_t_id, each_t in all_sorted_hevc_tile_tasks.iteritems():
                all_sorted_hevc_tile_tasks[each_t_id].set_processingCore(tile_to_node_mapping[each_t_id])            
            
            assert (len(all_sorted_hevc_tile_tasks.keys()) == (gop_tasks[0].getNumSubTasksTiles()*len(gop_tasks[0].get_gopstructure()))), \
             ":: incorrect number of tiles - %d, %d" %(len(all_sorted_hevc_tile_tasks.keys()),
                                                    (gop_tasks[0].getNumSubTasksTiles()*len(gop_tasks[0].get_gopstructure())))
               
            # update task mapping table    
            self._map_to_vidstrm_tile_mappingtbl_overwrite(tile_to_node_mapping, tile_pri_assignment, wf_id, strm_id)     
                                               
            return (tile_to_node_mapping, tile_pri_assignment, self.tiletasks_list_to_dict(all_sorted_hevc_tile_tasks.values()))
        else:
            return (None, None)
    
    
    
    #####################################################################################
    # TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_CLUSTLS_MOSTSLACK_VIA_VTMTBL_V2_FF
    #####################################################################################
    # first the vid stream is assigned a frame-level semi-dynamic priority scheme
    # (PR: lowest res first)
    # then,
    # (MP: splits the tasks into tiles, assigns the tiles to the PEs)
    # use only WCRS heuristic - cluster tiles together
    def taskTileMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPClusteredTilesMostSlackViaTmTbl_v2_FF(self, strm_specs,
                                                                                                    use_cp_type=0, 
                                                                                                    use_avgcc=False,
                                                                                                    
                                                                                                    # possible hop values
                                                                                                    use_fixed_nhops = False,
                                                                                                    fixed_nhops_cp = -1,
                                                                                                    fixed_nhops_tiles = -1,
                                                                                                    fixed_nhops_children = -1,
                                                                                                    ):
        
        # build pseudo frame-mappings dict
        empty_frame_mappings = self._get_empty_frame_mappings_dict(strm_specs)
        
        # get frame level priorities
        frame_priorities = self.common_priass_schm(strm_specs,empty_frame_mappings)
                     
        # get list of nodes that are free
        free_nodes_list_nids = [n.get_id() for n in self.RM_instance.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL)]
        #inner_nodes = self.RM_instance.interconnect.getInnerNodes_1border()
        inner_nodes = free_nodes_list_nids         
        num_inner_nodes = len(inner_nodes)        
        
        if(len(inner_nodes)>0):    
            wf_id = strm_specs['wf_id']
            strm_id = strm_specs['vid_strm_id']
            gop_tasks = strm_specs['gop_tasks']            
            
            # (1) sort tasks into dependency order - perform topological sort on the graph
            # (2) map critical path tasks together
            # (3) map tile and child tasks at nhop distances
            all_sorted_hevc_tile_tasks = self._get_sorted_tile_tasks(strm_specs, frame_priorities)

            copy_vtmtbl = self._get_deepcopy_volatiletaskmappingtable()
            copy_vnoctt = self.RM_instance.flow_table.getVNOCTT_copy()
                        
            # timing
            if (SimParams.TRACK_MAPPER_EXECOVERHEAD == True):
                self._record_time_start()
            
            n_tiles_all = len(all_sorted_hevc_tile_tasks.keys())
            temp_tile_id = all_sorted_hevc_tile_tasks.keys()[0]
            n_tiles_per_frame = all_sorted_hevc_tile_tasks[temp_tile_id].getNumSubTasksTiles()
            
            sorted_nodes_in_numlptasksorder = self._get_nodes_sorted_lowpriblockingorder(copy_vtmtbl, 
                                                                                         inner_nodes, 
                                                                                         all_sorted_hevc_tile_tasks[temp_tile_id].get_priority())
            
            #print sorted_nodes_in_numlptasksorder
                
            cp_fix_list = self._get_critical_path(use_cp_type, gop_tasks[0].get_adaptiveGoP_Obj())                    
            cp_tile_task_ids = [t.get_id() for tid, t in all_sorted_hevc_tile_tasks.iteritems() if t.get_frameIXinGOP() in cp_fix_list]
            cp_gop_seq = [ft.get_frameType() for ft in gop_tasks if ft.get_frameIXinGOP() in cp_fix_list]
            
            if (use_fixed_nhops == False):            
                (NHOPS_CP, 
                 NHOPS_TILES, 
                 NHOPS_CHILDREN) = self._get_ccr_specific_nhops(gop_tasks, n_tiles_all, n_tiles_per_frame, cp_str=cp_gop_seq)
            else:
                if (fixed_nhops_cp == -1) or (fixed_nhops_tiles == -1) or (fixed_nhops_children == -1):
                    sys.exit("Error - taskTileMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPClusteredTilesMostSlackViaTmTbl_v2 :: invalid nhops")
                else:
                    NHOPS_CP = fixed_nhops_cp
                    NHOPS_TILES =  fixed_nhops_tiles
                    NHOPS_CHILDREN = fixed_nhops_children
                    
            
            print (NHOPS_CP,  NHOPS_TILES, NHOPS_CHILDREN)
            
            # ----------------- intelligent bit : start ---------------------------------------------------------------------                       
            tile_pri_assignment = {} 
            tile_to_node_mapping = OrderedDict() 
            tile_00_node_id = None
            
            counter_A = 0
            counter_B = 0       
            counter_C = 0     
            tile_neighbours = {}
            
            for each_tile_task_id, each_tile_task in all_sorted_hevc_tile_tasks.iteritems():
                
                ### CRITICAL-PATH TASKS ###    
                if each_tile_task_id in cp_tile_task_ids:
                    if tile_00_node_id == None: # first tile of root task                        
                        selected_node_id = sorted_nodes_in_numlptasksorder[0]
                        tile_00_node_id = selected_node_id
                        
                        # below is done for the other tiles of CP                        
                        tmp_tile_00_neighbours = self.RM_instance.interconnect.getNodesNHops_fast(tile_00_node_id,NHOPS_CP) # nodes close to first tile of task
                        if len(tmp_tile_00_neighbours) == 0: tmp_tile_00_neighbours.append(tile_00_node_id)
                        t_key = "tile_00"
                        #tmp_tile_00_neighbours.sort(key=sorted_nodes_in_numlptasksorder.index)
                        tile_neighbours[t_key] = tmp_tile_00_neighbours
                        
                    # other tiles of other tasks in CP
                    else:                        
                        if "tile_00" not in tile_neighbours: sys.exit("Error - tile order - part 1")
                        if len(tile_neighbours["tile_00"])>1:                                                       
                            if counter_A >= len(tile_neighbours["tile_00"]): counter_A=0                            
                            selected_node_id =  tile_neighbours["tile_00"][counter_A]
                            counter_A +=1                                                    
                        else:
                            selected_node_id = tile_neighbours["tile_00"][0]
                
                ### NON - CRITICAL-PATH TASKS ### 
                else:
                    # map tile 0 of a non-cp task to the closest parent (parent with highest payload)
                    if ("_0" in each_tile_task_id): 
                        # get parent with highest data volume,                                             
                        # find nhop nodes for each parent, and then find the intersection between these nodes      
                        tile_task_parents = each_tile_task.get_expected_data_from_parents()              
                        #sorted_parents_by_payload_list = sorted(tile_task_parents.items(), key=itemgetter(1)) # tuples (pid, payload)                        
                        p_nid = tile_to_node_mapping[tile_task_parents.keys()[0]]                     
                        
                        #assert len(sorted_parents_by_payload_list) >0
                        #p_nid = tile_to_node_mapping[sorted_parents_by_payload_list[0][0]] # nid of highest payload parent
                        #assert(p_nid < (SimParams.NOC_W*SimParams.NOC_H)), "%d, %d" %(p_nid, SimParams.NOC_W*SimParams.NOC_H)  
                        
                        set_nhops_p_i = []           
                        set_nhops_p_i = self.RM_instance.interconnect.getNodesNHops_fast(p_nid,NHOPS_CHILDREN)                        
                        if len(set_nhops_p_i) == 0: set_nhops_p_i.append(p_nid)                    
                        set_nhops_p_i.sort(key=sorted_nodes_in_numlptasksorder.index)
                        
                        if counter_B >= len(set_nhops_p_i): counter_B=0
                        selected_node_id = set_nhops_p_i[counter_B]
                        counter_B +=1
                                                
                        # below is done for the other tiles of non-CP, non-0x tiles 
                        tmp_tile_0x_neighbours = self.RM_instance.interconnect.getNodesNHops_fast(selected_node_id,NHOPS_TILES) # nodes close to first tile of task
                        if len(tmp_tile_0x_neighbours) == 0 : tmp_tile_0x_neighbours.append(selected_node_id)
                        t_key = each_tile_task_id
                        #tmp_tile_0x_neighbours.sort(key=sorted_nodes_in_numlptasksorder.index)                        
                        tile_neighbours[t_key] = tmp_tile_0x_neighbours
                                                
                    else:
                        # map other tiles close to the first tile of task
                        tile_x0_task_id = "%d_%d" % (each_tile_task.getTileParentFrameId(), 0) 
                        #if tile_x0_task_id not in tile_to_node_mapping: sys.exit("Error - tile order - part 3")                        
                        #if tile_x0_task_id not in tile_neighbours: sys.exit("Error - tile order - part 4")
                        
                        if len(tile_neighbours[tile_x0_task_id])>1:
                            if counter_C >= len(tile_neighbours[tile_x0_task_id]): counter_C=0 
                            selected_node_id = tile_neighbours[tile_x0_task_id][counter_C]
                            counter_C +=1          
                        else:
                            selected_node_id = tile_neighbours[tile_x0_task_id][0]
                            
                
                assert(selected_node_id != None), ", no node was selected !!"
                
                ## updates to local copies of structures ##                
                                            
                # update frame mapping struct
                tile_task_id = each_tile_task.get_id()
                tile_to_node_mapping[tile_task_id] = selected_node_id
                
                # record pri-ass for the tile
                tile_pri_assignment[tile_task_id] = each_tile_task.get_priority()
                
            # ----------------- intelligent bit : end  ---------------------------------------------------------------------
            
            # update mmc node mapping table
            mmc_mapping = self._map_to_mmc_mappingtbl(tile_to_node_mapping, all_sorted_hevc_tile_tasks, copy_vnoctt)
            
            
            
            # timing
            if (SimParams.TRACK_MAPPER_EXECOVERHEAD == True):
                self._record_time_stop()
                
            
            self.mmc_selector._populate_VNOCTT(gop_tasks, all_sorted_hevc_tile_tasks, 
                                   tile_to_node_mapping, mmc_mapping, 
                                   gop_tasks[0].get_adaptiveGoP_Obj(), 
                                   gop_tasks[0].getNumSubTasksTiles())
            
            
            # update the processing core on the tile tasks objects
            for each_t_id, each_t in all_sorted_hevc_tile_tasks.iteritems():
                all_sorted_hevc_tile_tasks[each_t_id].set_processingCore(tile_to_node_mapping[each_t_id])
            
            assert (len(all_sorted_hevc_tile_tasks.keys()) == (gop_tasks[0].getNumSubTasksTiles()*len(gop_tasks[0].get_gopstructure()))), \
             ":: incorrect number of tiles - %d, %d" %(len(all_sorted_hevc_tile_tasks.keys()),
                                                    (gop_tasks[0].getNumSubTasksTiles()*len(gop_tasks[0].get_gopstructure())))
            
            # update task mapping table    
            self._map_to_vidstrm_tile_mappingtbl_overwrite(tile_to_node_mapping, tile_pri_assignment, wf_id, strm_id)  
                                      
            return (tile_to_node_mapping, tile_pri_assignment, self.tiletasks_list_to_dict(all_sorted_hevc_tile_tasks.values()))
        else:
            return (None, None)
    
    
    
    
    
    #####################################################################################
    # TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_LOWUTIL_VIA_VTMTBL
    #####################################################################################
    # first the vid stream is assigned a frame-level semi-dynamic priority scheme
    # (PR: lowest res first)
    # then,
    # (MP: splits the tasks into tiles, assigns the tiles to the PEs)
    def taskTileMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPLowUtil_v1(self, strm_specs, use_avgcc=False):
        # build pseudo frame-mappings dict
        empty_frame_mappings = self._get_empty_frame_mappings_dict(strm_specs)
        
        # get frame level priorities
        frame_priorities = self.common_priass_schm(strm_specs,empty_frame_mappings)
                     
        # get list of nodes that are free 
        free_nodes_list = self.RM_instance.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL)  
        free_nodes_list_nids = [n.get_id() for n in free_nodes_list]

        if(len(free_nodes_list)>0):    
            wf_id = strm_specs['wf_id']
            strm_id = strm_specs['vid_strm_id']            
            gop_tasks = strm_specs['gop_tasks']
            
            # (1) sort tasks into dependency order - perform topological sort on the graph            
            # (3) each task is added to the PE with lowest util                
            all_sorted_hevc_tile_tasks = self._get_sorted_tile_tasks(strm_specs, frame_priorities)
            
            # ----------------- intelligent bit : start ---------------------------------------------------------------------
            # for each item check if it can be accomodated into bin_i           
            # timing
            copy_vtmtbl = self._get_deepcopy_volatiletaskmappingtable()
            copy_vnoctt = self.RM_instance.flow_table.getVNOCTT_copy()
            
            if (SimParams.TRACK_MAPPER_EXECOVERHEAD == True):
                self._record_time_start()
            
            tile_pri_assignment = {} 
            tile_to_node_mapping = OrderedDict()             
            for each_tile_task_id, each_tile_task in all_sorted_hevc_tile_tasks.iteritems():
                # assign to node with max cumslack
                selected_node_id = self._get_node_lowest_util_viavmtbl(copy_vtmtbl, free_nodes_list_nids, use_avgcc=use_avgcc)
                
                # update local copy of vtmtbl
                if (selected_node_id not in copy_vtmtbl):
                    copy_vtmtbl[selected_node_id] = [self._get_vtmtbl_targettiletask_entry(each_tile_task, selected_node_id, 
                                                                                       each_tile_task.get_priority())]
                else:
                    copy_vtmtbl[selected_node_id].append(self._get_vtmtbl_targettiletask_entry(each_tile_task, selected_node_id, 
                                                                                           each_tile_task.get_priority()))   
#                 print "---"
#                 print     copy_vtmtbl
#                 print "---"                         
                # update frame mapping struct
                tile_task_id = each_tile_task.get_id()
                tile_to_node_mapping[tile_task_id] = selected_node_id
                
                # record pri-ass for the tile
                tile_pri_assignment[tile_task_id] = each_tile_task.get_priority()
            
            # ----------------- intelligent bit : end  ---------------------------------------------------------------------
            
            # update mmc node mapping table
            mmc_mapping = self._map_to_mmc_mappingtbl(tile_to_node_mapping, all_sorted_hevc_tile_tasks, copy_vnoctt)
            
            # timing
            if (SimParams.TRACK_MAPPER_EXECOVERHEAD == True):
                self._record_time_stop()
            
            self.mmc_selector._populate_VNOCTT(gop_tasks, all_sorted_hevc_tile_tasks, 
                                   tile_to_node_mapping, mmc_mapping, 
                                   gop_tasks[0].get_adaptiveGoP_Obj(), 
                                   gop_tasks[0].getNumSubTasksTiles())            
            
            # update the processing core on the tile tasks objects
            for each_t_id, each_t in all_sorted_hevc_tile_tasks.iteritems():
                all_sorted_hevc_tile_tasks[each_t_id].set_processingCore(tile_to_node_mapping[each_t_id])
            
            assert (len(all_sorted_hevc_tile_tasks.keys()) == (gop_tasks[0].getNumSubTasksTiles()*len(gop_tasks[0].get_gopstructure()))), \
             ":: incorrect number of tiles - %d, %d" %(len(all_sorted_hevc_tile_tasks.keys()),
                                                    (gop_tasks[0].getNumSubTasksTiles()*len(gop_tasks[0].get_gopstructure())))

            # update task mapping table    
            self._map_to_vidstrm_tile_mappingtbl_overwrite(tile_to_node_mapping, tile_pri_assignment, wf_id, strm_id)      
                                  
            return (tile_to_node_mapping, tile_pri_assignment, self.tiletasks_list_to_dict(all_sorted_hevc_tile_tasks.values()))
        else:
            return (None, None)
    
    
    #####################################################################################
    # TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_LOWUTIL_VIA_VTMTBL_FIRSTFIT
    #####################################################################################
    # first the vid stream is assigned a frame-level semi-dynamic priority scheme
    # (PR: lowest res first)
    # then,
    # (MP: splits the tasks into tiles, assigns the tiles to the PEs) - sort nodes only once
    def taskTileMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPLowUtil_FF(self, strm_specs, use_avgcc=False):
        # build pseudo frame-mappings dict
        empty_frame_mappings = self._get_empty_frame_mappings_dict(strm_specs)        
        # get frame level priorities
        frame_priorities = self.common_priass_schm(strm_specs,empty_frame_mappings)
                     
        # get list of nodes that are free 
        free_nodes_list = self.RM_instance.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL)  
        free_nodes_list_nids = [n.get_id() for n in free_nodes_list]
        
        if(len(free_nodes_list)>0):    
            wf_id = strm_specs['wf_id']
            strm_id = strm_specs['vid_strm_id']            
            gop_tasks = strm_specs['gop_tasks']
            
            # (1) sort tasks into dependency order - perform topological sort on the graph            
            # (3) each task is added to the PE with lowest util                
            all_sorted_hevc_tile_tasks = self._get_sorted_tile_tasks(strm_specs, frame_priorities)
            
            copy_vtmtbl = self._get_deepcopy_volatiletaskmappingtable()
            copy_vnoctt = self.RM_instance.flow_table.getVNOCTT_copy()
            
            # ----------------- intelligent bit : start ---------------------------------------------------------------------
            # for each item check if it can be accomodated into bin_i           
            # timing
            if (SimParams.TRACK_MAPPER_EXECOVERHEAD == True):
                self._record_time_start()
                
            sorted_nid_list = self._get_nodes_sorted_LU_order(copy_vtmtbl,free_nodes_list_nids, use_avgcc=use_avgcc)
                        
            tile_pri_assignment = {} 
            tile_to_node_mapping = OrderedDict()             
            nid_pointer = 0
            for each_tile_task_id, each_tile_task in all_sorted_hevc_tile_tasks.iteritems():
                
                if nid_pointer >= len(sorted_nid_list):
                    nid_pointer=0
                
                # assign to node in sorted list
                selected_node_id = sorted_nid_list[nid_pointer]
                
                # no update to vmtbl copy done here
                        
                # update frame mapping struct
                tile_task_id = each_tile_task.get_id()
                tile_to_node_mapping[tile_task_id] = selected_node_id
                
                # record pri-ass for the tile
                tile_pri_assignment[tile_task_id] = each_tile_task.get_priority()
                
                nid_pointer+=1
            # ----------------- intelligent bit : end  ---------------------------------------------------------------------
            
            # update mmc node mapping table
            mmc_mapping = self._map_to_mmc_mappingtbl(tile_to_node_mapping, all_sorted_hevc_tile_tasks, copy_vnoctt)
            
            # timing
            if (SimParams.TRACK_MAPPER_EXECOVERHEAD == True):
                self._record_time_stop()
            
            
            self.mmc_selector._populate_VNOCTT(gop_tasks, all_sorted_hevc_tile_tasks, 
                                   tile_to_node_mapping, mmc_mapping, 
                                   gop_tasks[0].get_adaptiveGoP_Obj(), 
                                   gop_tasks[0].getNumSubTasksTiles())
            
            # update the processing core on the tile tasks objects
            for each_t_id, each_t in all_sorted_hevc_tile_tasks.iteritems():
                all_sorted_hevc_tile_tasks[each_t_id].set_processingCore(tile_to_node_mapping[each_t_id])
            
            assert (len(all_sorted_hevc_tile_tasks.keys()) == (gop_tasks[0].getNumSubTasksTiles()*len(gop_tasks[0].get_gopstructure()))), \
             ":: incorrect number of tiles - %d, %d" %(len(all_sorted_hevc_tile_tasks.keys()),
                                                    (gop_tasks[0].getNumSubTasksTiles()*len(gop_tasks[0].get_gopstructure())))

            # update task mapping table    
            self._map_to_vidstrm_tile_mappingtbl_overwrite(tile_to_node_mapping, tile_pri_assignment, wf_id, strm_id)       
                                 
            return (tile_to_node_mapping, tile_pri_assignment, self.tiletasks_list_to_dict(all_sorted_hevc_tile_tasks.values()))
        else:
            return (None, None)
    
    #####################################################################################
    # TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_GROUPEDTILES_VIA_VTMTBL
    #####################################################################################
    # first the vid stream is assigned a frame-level semi-dynamic priority scheme
    # (PR: lowest res first)
    # then,
    # (MP: splits the tasks into tiles, assigns the tiles to the PEs)
    def taskTileMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPClusteredTilesMostSlackViaTmTbl_LUGroupedTiles(self, strm_specs, use_avgcc=False):
        # build pseudo frame-mappings dict
        empty_frame_mappings = self._get_empty_frame_mappings_dict(strm_specs)
        
        # get frame level priorities
        frame_priorities = self.common_priass_schm(strm_specs,empty_frame_mappings)
                     
        # get list of nodes that are free 
        free_nodes_list = self.RM_instance.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL)  
        free_nodes_list_nids = [n.get_id() for n in free_nodes_list]

        if(len(free_nodes_list)>0):    
            wf_id = strm_specs['wf_id']
            strm_id = strm_specs['vid_strm_id']            
            gop_tasks = strm_specs['gop_tasks']
            
            # (1) sort tasks into dependency order - perform topological sort on the graph            
            # (3) each task is added to the PE with lowest util                
            all_sorted_hevc_tile_tasks = self._get_sorted_tile_tasks(strm_specs, frame_priorities)
            
            # ----------------- intelligent bit : start ---------------------------------------------------------------------
            # for each item check if it can be accomodated into bin_i           
            # timing
            copy_vtmtbl = self._get_deepcopy_volatiletaskmappingtable()
            copy_vnoctt = self.RM_instance.flow_table.getVNOCTT_copy()
            
            if (SimParams.TRACK_MAPPER_EXECOVERHEAD == True):
                self._record_time_start()
            
            tile_pri_assignment = {} 
            tile_to_node_mapping = OrderedDict()             
            for each_tile_task_id, each_tile_task in all_sorted_hevc_tile_tasks.iteritems():
                
                if "_0" in each_tile_task_id:
                    # assign to node with max cumslack
                    selected_node_id = self._get_node_lowest_util_viavmtbl(copy_vtmtbl, free_nodes_list_nids, use_avgcc=use_avgcc)      
                else:                    
                    # map other tiles close to the first tile of task
                    tile_x0_task_id = "%d_%d" % (each_tile_task.getTileParentFrameId(), 0)
                    if tile_x0_task_id not in tile_to_node_mapping: sys.exit("Error - order of tiles invalid")
                    tile_x0_nid =  tile_to_node_mapping[tile_x0_task_id]
                    selected_node_id = tile_x0_nid
                
                # update local copy of vtmtbl
                if (selected_node_id not in copy_vtmtbl):
                    copy_vtmtbl[selected_node_id] = [self._get_vtmtbl_targettiletask_entry(each_tile_task, selected_node_id, 
                                                                                       each_tile_task.get_priority())]
                else:
                    copy_vtmtbl[selected_node_id].append(self._get_vtmtbl_targettiletask_entry(each_tile_task, selected_node_id, 
                                                                                           each_tile_task.get_priority())) 
                
                # update frame mapping struct
                tile_task_id = each_tile_task.get_id()
                tile_to_node_mapping[tile_task_id] = selected_node_id
                
                # record pri-ass for the tile
                tile_pri_assignment[tile_task_id] = each_tile_task.get_priority()
            
            # ----------------- intelligent bit : end  ---------------------------------------------------------------------
            
            # update mmc node mapping table
            mmc_mapping = self._map_to_mmc_mappingtbl(tile_to_node_mapping, all_sorted_hevc_tile_tasks, copy_vnoctt)
            
            # timing
            if (SimParams.TRACK_MAPPER_EXECOVERHEAD == True):
                self._record_time_stop()
            
            self.mmc_selector._populate_VNOCTT(gop_tasks, all_sorted_hevc_tile_tasks, 
                                   tile_to_node_mapping, mmc_mapping, 
                                   gop_tasks[0].get_adaptiveGoP_Obj(), 
                                   gop_tasks[0].getNumSubTasksTiles())            
            
            # update the processing core on the tile tasks objects
            for each_t_id, each_t in all_sorted_hevc_tile_tasks.iteritems():
                all_sorted_hevc_tile_tasks[each_t_id].set_processingCore(tile_to_node_mapping[each_t_id])
            
            assert (len(all_sorted_hevc_tile_tasks.keys()) == (gop_tasks[0].getNumSubTasksTiles()*len(gop_tasks[0].get_gopstructure()))), \
             ":: incorrect number of tiles - %d, %d" %(len(all_sorted_hevc_tile_tasks.keys()),
                                                    (gop_tasks[0].getNumSubTasksTiles()*len(gop_tasks[0].get_gopstructure())))

            # update task mapping table    
            self._map_to_vidstrm_tile_mappingtbl_overwrite(tile_to_node_mapping, tile_pri_assignment, wf_id, strm_id)       
                                 
            return (tile_to_node_mapping, tile_pri_assignment, self.tiletasks_list_to_dict(all_sorted_hevc_tile_tasks.values()))
        else:
            return (None, None)
    
    
    
    
    
    #####################################################################################
    # TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_KAUSHIK_PP_V2
    #####################################################################################
    # first the vid stream is assigned a frame-level semi-dynamic priority scheme
    # (PR: lowest res first)
    # then,
    # (MP: splits the tasks into tiles, assigns the tiles to the PEs)
    # use only WCRS heuristic - cluster tiles together
    def taskTileMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPKaushikPP_v2(self, strm_specs):
        ':type nxDAG_tiles_copy: DiGraph'
        
        # build pseudo frame-mappings dict
        empty_frame_mappings = self._get_empty_frame_mappings_dict(strm_specs)
        
        # get frame level priorities
        frame_priorities = self.common_priass_schm(strm_specs,empty_frame_mappings)
                     
        # get list of nodes that are free
        free_nodes_list_nids = [n.get_id() for n in self.RM_instance.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL)]
        #inner_nodes = self.RM_instance.interconnect.getInnerNodes_1border()
        inner_nodes = free_nodes_list_nids         
        
        if(len(inner_nodes)>0):    
            wf_id = strm_specs['wf_id']
            strm_id = strm_specs['vid_strm_id']
            gop_tasks = strm_specs['gop_tasks']     
            
            # init merge counter
            vid_res_str = "%dx%d" % (gop_tasks[0].get_frame_w(), gop_tasks[0].get_frame_h()) 
            pp_mapping_info_key = "%s_%d_%d_%d"%(vid_res_str,wf_id, strm_id, gop_tasks[0].get_unique_gop_id())
            self.pp_mapping_info[pp_mapping_info_key] = {
                                                              'stage1':None, 'stage2':None, 'stage3':None,
                                                              'before_num_nodes_and_edges' : None,
                                                              'after_num_nodes_and_edges' : None,                                                              
                                                        }       
            
            # (1) sort tasks into dependency order - perform topological sort on the graph
            # (2) map critical path tasks together
            # (3) map tile and child tasks at nhop distances
            all_sorted_hevc_tile_tasks = self._get_sorted_tile_tasks(strm_specs, frame_priorities)
            
            copy_vtmtbl = self._get_deepcopy_volatiletaskmappingtable()
            copy_vnoctt = self.RM_instance.flow_table.getVNOCTT_copy()
            #copy_vmtblusagetbl = self._get_deepcopy_nodeusage_volatiletaskmappingtable()                
            
            n_tiles_all = len(all_sorted_hevc_tile_tasks.keys())
            temp_tile_id = all_sorted_hevc_tile_tasks.keys()[0]
            n_tiles_per_frame = all_sorted_hevc_tile_tasks[temp_tile_id].getNumSubTasksTiles()
            
            # ----------------- intelligent bit : start ---------------------------------------------------------------------                       
            tile_pri_assignment = {} 
            tile_to_node_mapping = OrderedDict() 
            
            # get weighted gop nxDAG
            gop_adap_obj = gop_tasks[0].get_adaptiveGoP_Obj()
            frame_dec_size_bytes = gop_tasks[0].get_maxMemConsumption()            
            gop_max_comcost = self.RM_instance.interconnect.getRouteCost(None, None, 
                                                                        frame_dec_size_bytes, 
                                                                        nhops=(SimParams.NOC_H-1) + (SimParams.NOC_W-1))  
            
#             print "weights:"
#             print gop_tasks[0].get_wccIFrame(), gop_tasks[0].get_wccPFrame(), gop_tasks[0].get_wccBFrame()
            
            gop_adap_obj.applyWeights(gop_max_comcost*float(SimParams.CLSTR_TILE_PARAM_KAUSHIKS_ALGO_COMMS_SCALEUP_FACTOR),
                                      gop_tasks[0].get_wccIFrame(), 
                                      gop_tasks[0].get_wccPFrame(),
                                      gop_tasks[0].get_wccBFrame())
            
            # convert nxDAG_gop to nxDAG_tiles
            gop_adap_obj.splitDAG2Tiles(n_tiles_per_frame)
            nxDAG_tiles = gop_adap_obj.get_networkxDG_weighted_split()
            
            #pprint.pprint(nxDAG_tiles.nodes(data=True))
            #sys.exit()
            
            assert(len(nxDAG_tiles.nodes())== len(all_sorted_hevc_tile_tasks.keys())), "Error - mapper : tile partitions not correct!"
            
            
            ################################################################
            ## Preprocessing stage : cluster the tile tasks               ##
            ## * if there are multiple edges with same weight, we         ##
            ##   pick the edge with the lowest cumulative node weights    ##        
            ################################################################
            nxDAG_tiles_copy = nxDAG_tiles.copy()
            track_temp_merge_time_taken = [0.0, 0.0, 0.0]
            
            # track
            self.pp_mapping_info[pp_mapping_info_key]['before_num_nodes_and_edges'] = (
                                                                                     len(nxDAG_tiles_copy.nodes()),
                                                                                     len(nxDAG_tiles_copy.edges()),
                                                                                     )
            
            # timing            
            if (SimParams.TRACK_MAPPER_EXECOVERHEAD == True): # we start a bit late, because we assume the graph creation not part of PP algo.
                self._record_time_start()
            
            
            ################################
            #### Stage 1 : optimisation ####
            ################################
            # combine nodes until communication is not the bottleneck
            
            (max_cload_edge, max_cload) = self._nxdg_choose_edge_with_max_weight(gop_adap_obj, nxDAG_tiles_copy) # comm
            (max_pload_node, max_pload) = self._nxdg_choose_node_with_max_weight(gop_adap_obj, nxDAG_tiles_copy) # comp
            
            print "(max_cload, max_pload, ratio) =", max_cload, max_pload, max_pload/max_cload
            
            print "KK: start of stage 1 : num nodes : ", len(nxDAG_tiles_copy.nodes())
            print "---- > PP : stage 1"
            curr_stage_merge_count = 0
            while(max_pload <= max_cload): # is this needed ??
                #print len(nxDAG_tiles_copy.nodes()), len(nxDAG_tiles_copy.edges())
                
                # if only a single node, then break
                if len(nxDAG_tiles_copy.nodes()) == 1:
                    break;
                else:                
                    (max_cload_edge, max_cload) = self._nxdg_choose_edge_with_max_weight(gop_adap_obj, nxDAG_tiles_copy)
                    (max_pload_node, max_pload) = self._nxdg_choose_node_with_max_weight(gop_adap_obj, nxDAG_tiles_copy)
                    
                    #print max_cload_edge, max_cload
                    
                    #print "---------------"
                    #pprint.pprint(nx.get_edge_attributes(nxDAG_tiles_copy, 'weight'))
                    #print "---------------"
                    
                    
                    
                    if (max_pload < max_cload): # same logic as while loop condition (but inverted)
                        # find nodes belonging to edge : max_cload_edge
                        node_tp = max_cload_edge[0]
                        node_tq = max_cload_edge[1]
                        pload_tp = gop_adap_obj.get_node_weight(nxDAG_tiles_copy, node_tp)
                        pload_tq = gop_adap_obj.get_node_weight(nxDAG_tiles_copy, node_tq)
                        
                        if ((pload_tp + pload_tq) <= max_cload):
                            ## merge nodes (node_tp) and (node_tq)                        
                            nodes = [node_tp, node_tq]
                            new_node = "%s;%s" % (node_tp, node_tq)                        
                            attr_dict = {'weight' : (pload_tp + pload_tq)}
                            nxDAG_tiles_copy, mtt = gop_adap_obj.merge_nodes(nxDAG_tiles_copy, nodes, new_node, attr_dict) # merge and update graph
                            curr_stage_merge_count+=1
                            track_temp_merge_time_taken[0] += mtt[0]
                            track_temp_merge_time_taken[1] += mtt[1]
                            track_temp_merge_time_taken[2] += mtt[2]
                        else:
                            break; # break and go to second stage of optimisation
                    else:
                        pass                
                
            # update tracking
            self.pp_mapping_info[pp_mapping_info_key]['stage1'] = curr_stage_merge_count
            
            
            
#             ### checking ###
#             # check if there are any nodes are isolated
#             print "KK: end of stage 1 : num nodes : ", len(nxDAG_tiles_copy.nodes())
#             num_nodes_without_io_edges = []
#             for each_node in nxDAG_tiles_copy.nodes():
#                 num_out_edges = len(nxDAG_tiles_copy.out_edges(nbunch=[each_node]))
#                 num_in_edges = len(nxDAG_tiles_copy.in_edges(nbunch=[each_node]))                
#                 if (num_out_edges == 0) and (num_in_edges == 0):
#                     num_nodes_without_io_edges.append(each_node)
#                         
#             if len(num_nodes_without_io_edges)>0:
#                 pprint.pprint(num_nodes_without_io_edges)    
#                 sys.exit("taskTileMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPKaushikPP_v2: Error - stage 1, has isolated nodes : " +str(len(num_nodes_without_io_edges)))
#             ### checking ###
            
            print "KK: end of stage 1 : num nodes=%d, merge_count=%d"% (len(nxDAG_tiles_copy.nodes()), curr_stage_merge_count)
            
            print "----------- After Stage 1::--------" 
            #pprint.pprint(nxDAG_tiles_copy.nodes())
            #raw_input('Press any key to continue..')
            
            ################################
            #### Stage 2 : optimisation ####
            ################################            
            # merge communicating tasks together as long as combined load < maxpload            
            # sort nodes by weight
            #print "---- > PP : stage 2"
            curr_stage_merge_count=0
            if len(nxDAG_tiles_copy.nodes()) != 1:            
                # get all node combinations of the edges in the TG
                #node_combinations = self._nxdg_get_sorted_combined_loads_of_edges(gop_adap_obj, nxDAG_tiles_copy)
                (max_cload_edge, max_cload) = self._nxdg_choose_edge_with_max_weight(gop_adap_obj, nxDAG_tiles_copy) # comm
                (max_pload_node, max_pload) = self._nxdg_choose_node_with_max_weight(gop_adap_obj, nxDAG_tiles_copy) # comp
                
                combined_nodes_min_tuple, combined_load_min = self._nxdg_get_min_combined_loads_of_edges(gop_adap_obj, nxDAG_tiles_copy)
                
                i = 0
                while (combined_load_min <= max_pload):
                    #print "here -- ",i
                    if nx.number_of_nodes(nxDAG_tiles_copy) == 1:
                        break;
                    else:
                        (node_tp, node_tq) = combined_nodes_min_tuple                                
                        nodes = [node_tp, node_tq]
                        new_node = "%s;%s" % (node_tp, node_tq)                        
                        attr_dict = {'weight' : combined_load_min}
                        nxDAG_tiles_copy, mtt = gop_adap_obj.merge_nodes(nxDAG_tiles_copy, nodes, new_node, attr_dict) # merge and update graph
                        curr_stage_merge_count+=1
                        track_temp_merge_time_taken[0] += mtt[0]
                        track_temp_merge_time_taken[1] += mtt[1]
                        track_temp_merge_time_taken[2] += mtt[2]
                        
                        if nx.number_of_nodes(nxDAG_tiles_copy) == 1:
                            break;
                        else:                        
                            # find new min combined load
                            combined_nodes_min_tuple, combined_load_min = self._nxdg_get_min_combined_loads_of_edges(gop_adap_obj, nxDAG_tiles_copy)
                            #print combined_nodes_min_tuple
                    i+=1                            
            else:
                pass  
            
            
            # update tracking
            self.pp_mapping_info[pp_mapping_info_key]['stage2'] = curr_stage_merge_count
            
            
#             ### checking ###
#             # check if there are any nodes are isolated
#             print "KK: end of stage 2 : num nodes : ", len(nxDAG_tiles_copy.nodes())
#             num_nodes_without_io_edges = []
#             for each_node in nxDAG_tiles_copy.nodes():
#                 num_out_edges = len(nxDAG_tiles_copy.out_edges(nbunch=[each_node]))
#                 num_in_edges = len(nxDAG_tiles_copy.in_edges(nbunch=[each_node]))                
#                 if (num_out_edges == 0) and (num_in_edges == 0):
#                     num_nodes_without_io_edges.append(each_node)
#                         
#             if len(num_nodes_without_io_edges)>0:
#                 pprint.pprint(num_nodes_without_io_edges)    
#                 sys.exit("taskTileMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPKaushikPP_v2: Error - stage 2, has isolated nodes : " +str(len(num_nodes_without_io_edges)))
#             ### checking ###
            
            
            print "KK: end of stage 2 : num nodes=%d, merge_count=%d"% (len(nxDAG_tiles_copy.nodes()), curr_stage_merge_count)
            print "----------- After Stage 2::--------" 
            #pprint.pprint(nxDAG_tiles_copy.nodes())
            #raw_input('Press any key to continue..')
            
            ################################
            #### Stage 3 : optimisation ####
            ################################            
            # merge *non-communicating* tasks together as long as combined load < maxpload AND max(edges_weights) < maxpload
            
            curr_stage_merge_count=0
            if len(nxDAG_tiles_copy.nodes()) != 1:
                loop_count = 0
                sorted_comb_i = 0
                (max_pload_node, max_pload) = self._nxdg_choose_node_with_max_weight(gop_adap_obj, nxDAG_tiles_copy) # comp
                sorted_comb_nodes = self._nxdg_get_sorted_combined_loads(gop_adap_obj, nxDAG_tiles_copy)
                min_combo_node, min_combo_node_pload = sorted_comb_nodes[sorted_comb_i]
                
                print "min_combo_node_pload, max_pload", min_combo_node_pload, max_pload
                
                while(min_combo_node_pload <= max_pload):                    
                    if nx.number_of_nodes(nxDAG_tiles_copy) == 1:
                        break; # stop loop no edges !
                    else:
                                                
                        # temp merge procedure
                        (node_tp, node_tq) = min_combo_node                                
                        nodes = [node_tp, node_tq]
                        new_node = "%s;%s" % (node_tp, node_tq)                        
                        attr_dict = {'weight' : min_combo_node_pload}
                        temp_nxDAG_tiles_copy = nxDAG_tiles_copy.copy() # make temp copy                        
                        temp_nxDAG_tiles_copy, mtt = gop_adap_obj.merge_nodes(temp_nxDAG_tiles_copy, nodes, new_node, attr_dict) # temporarily merge and update graph
                        curr_stage_merge_count+=1                        
                        track_temp_merge_time_taken[0] += mtt[0]
                        track_temp_merge_time_taken[1] += mtt[1]
                        track_temp_merge_time_taken[2] += mtt[2]
                        
                        if nx.number_of_nodes(nxDAG_tiles_copy) > 1:
                            # after merge, check if the max edge is less than maxpload
                            max_cload = gop_adap_obj.get_edges_max_weight(temp_nxDAG_tiles_copy).items()[0][1]
                            if max_cload < max_pload: # if we merge, then max c cost is still less than max p cost, therefore merge
                                # merge those nodes together
                                nxDAG_tiles_copy, mtt = gop_adap_obj.merge_nodes(nxDAG_tiles_copy, nodes, new_node, attr_dict) # merge and update graph
                                curr_stage_merge_count+=1
                                track_temp_merge_time_taken[0] += mtt[0]
                                track_temp_merge_time_taken[1] += mtt[1]
                                track_temp_merge_time_taken[2] += mtt[2]
                                
                                # query again
                                sorted_comb_i = 0
                                (max_pload_node, max_pload) = self._nxdg_choose_node_with_max_weight(gop_adap_obj, nxDAG_tiles_copy) # comp
                                sorted_comb_nodes = self._nxdg_get_sorted_combined_loads(gop_adap_obj, nxDAG_tiles_copy)
                                min_combo_node, min_combo_node_pload = sorted_comb_nodes[sorted_comb_i]
                                                                
                            else: # we can't combine, because combined comm cost is too high                                
                                #print "can't combine : ", max_cload, max_pload
                                if sorted_comb_i < len(sorted_comb_nodes): 
                                    sorted_comb_i +=1                                
                                    min_combo_node, min_combo_node_pload = sorted_comb_nodes[sorted_comb_i]
                                else:
                                    break; # stop loop (have run out of combos)
                                
                        else: # we can't combine, because then will be a single node, therefore only 2 nodes now in TG (leave them as is)
                            break;
                                                    
                        loop_count +=1
                        if (loop_count % 10000) == 0:
                            pprint.pprint(nxDAG_tiles_copy.nodes())
                            sys.exit("taskTileMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPKaushikPP_v2:: Error - something went wrong, looped too much")
                        else:
                            pass
            else:
                pass
            
            
            # update tracking
            self.pp_mapping_info[pp_mapping_info_key]['stage3'] = curr_stage_merge_count
            #pprint.pprint(track_temp_merge_time_taken)
            #raw_input('Press any key to continue..')
            
#             ### checking ###
#             # check if there are any nodes are isolated
#             print "KK: end of stage 3 : num nodes : ", len(nxDAG_tiles_copy.nodes())
#             num_nodes_without_io_edges = []
#             for each_node in nxDAG_tiles_copy.nodes():
#                 num_out_edges = len(nxDAG_tiles_copy.out_edges(nbunch=[each_node]))
#                 num_in_edges = len(nxDAG_tiles_copy.in_edges(nbunch=[each_node]))                
#                 if (num_out_edges == 0) and (num_in_edges == 0):
#                     num_nodes_without_io_edges.append(each_node)
#                         
#             if len(num_nodes_without_io_edges)>0:
#                 pprint.pprint(num_nodes_without_io_edges)    
#                 sys.exit("taskTileMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPKaushikPP_v2: Error - stage 3, has isolated nodes : " +str(len(num_nodes_without_io_edges)))
#             ### checking ###
                        
            print "KK: end of stage 3 : num nodes=%d, merge_count=%d"% (len(nxDAG_tiles_copy.nodes()), curr_stage_merge_count)
            print "----------- After Stage 3::--------"
             
            #pprint.pprint(nxDAG_tiles_copy.nodes())
            #raw_input('Press any key to continue..')
            
            # track
            self.pp_mapping_info[pp_mapping_info_key]['after_num_nodes_and_edges'] = (
                                                                                     len(nxDAG_tiles_copy.nodes()),
                                                                                     len(nxDAG_tiles_copy.edges()),
                                                                                     )
            
            
            ### Offset timing calculation : start ####
            offset_clock_start_timer_pytime = time.time()
            offset_clock_start_timer_pyclock = time.clock()
            offset_clock_start_timer_pytimeit = timeit.default_timer()
            ###
            
            ########################################################
            ## Mapping Phase : map tasks into processing elements ##
            ## * map all tasks close to their parents - 1/2 hop     ##
            ########################################################
            # need to maintain a nxlabel to task hashtable
            temp_nx_to_task_table = {}
            for each_tile_task_id, each_tile_task in all_sorted_hevc_tile_tasks.iteritems():
                each_tile_task_nx_label = self._get_tile_task_nx_label(each_tile_task)
                temp_nx_to_task_table[each_tile_task_nx_label] = each_tile_task
            
            # mapping phase starts here     
            pp_tasks_to_node_mapping = {}
            for each_tile_task_id, each_tile_task in all_sorted_hevc_tile_tasks.iteritems():                
                each_tile_task_nx_label = self._get_tile_task_nx_label(each_tile_task)
                
                if each_tile_task_nx_label not in pp_tasks_to_node_mapping: # never mapped before
                    
                    parents =  nxDAG_tiles.predecessors(each_tile_task_nx_label)
                    if len(parents) == 0: # root
                        selected_node_id = self._get_node_lowest_util_viavmtbl(copy_vtmtbl, free_nodes_list_nids) 
                        pp_tasks_to_node_mapping[each_tile_task_nx_label] = selected_node_id
                        
                        # update vtmtbl (local)
                        copy_vtmtbl = self._kaushik_helper_update_copy_vtmtbl(copy_vtmtbl, selected_node_id, each_tile_task)
                        
                        # get other nodes mapped with this nx_node, map them too to the same PE
                        other_tasks_list = self._nxdg_find_other_nodes_clustered_with_target_node(nxDAG_tiles_copy, 
                                                                                             each_tile_task_nx_label)
                        for each_other_task_nx_lbl in other_tasks_list:
                            pp_tasks_to_node_mapping[each_other_task_nx_lbl] = selected_node_id
                            # update vtmtbl (local)
                            copy_vtmtbl = self._kaushik_helper_update_copy_vtmtbl(copy_vtmtbl, selected_node_id, temp_nx_to_task_table[each_other_task_nx_lbl])                                        
                    else:
                        parent_task_nx_lbl = parents[0]
                        parent_node_id = pp_tasks_to_node_mapping[parent_task_nx_lbl]
                        nearby_nodes = self.RM_instance.interconnect.getNodesNHops_fast(parent_node_id,2)
                        
                        # try to limit the search into PEs not been used before
                        unsed_PEs_list =   list(set(nearby_nodes) - set(pp_tasks_to_node_mapping.values()))
                        
                        if len(unsed_PEs_list) != 0: # if there are some unused nodes, use those !                      
                            selected_node_id = self._get_node_lowest_util_viavmtbl(copy_vtmtbl, unsed_PEs_list)      
                        else:
                            selected_node_id = self._get_node_lowest_util_viavmtbl(copy_vtmtbl, nearby_nodes)
                        
                        pp_tasks_to_node_mapping[each_tile_task_nx_label] = selected_node_id
                        # update vtmtbl (local)
                        copy_vtmtbl = self._kaushik_helper_update_copy_vtmtbl(copy_vtmtbl, selected_node_id, each_tile_task)
                        
                        # get other nodes mapped with this nx_node, map them too to the same PE
                        other_tasks_list = self._nxdg_find_other_nodes_clustered_with_target_node(nxDAG_tiles_copy, 
                                                                                             each_tile_task_nx_label)
                        for each_other_task_nx_lbl in other_tasks_list:
                            pp_tasks_to_node_mapping[each_other_task_nx_lbl] = selected_node_id
                            # update vtmtbl (local)
                            copy_vtmtbl = self._kaushik_helper_update_copy_vtmtbl(copy_vtmtbl, selected_node_id, temp_nx_to_task_table[each_other_task_nx_lbl])
                        
                else: # already mapped before
                    pass
                
            
            ## checking ##
            assert(len(pp_tasks_to_node_mapping.keys()) == len(all_sorted_hevc_tile_tasks.keys())), "taskTileMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPKaushikPP_v2: Error" + \
                                                                                                    " in mapping phase :\n" + \
                                                                                                    pprint.pformat(nxDAG_tiles_copy.nodes(), indent=4) + \
                                                                                                    "\n-----\n" + \
                                                                                                    pprint.pformat(pp_tasks_to_node_mapping.nodes(), indent=4)
                         
            ########################################################
            ## Internal mapping                                   ##
            ########################################################                        
            # the keys in the above mapping dict are strings of clustered tasks
            # need to make a one to one mapping of tasks and PEs
            for each_tile_task_id, each_tile_task in all_sorted_hevc_tile_tasks.iteritems():
                selected_node_id = None
                each_tile_task_nx_label = self._get_tile_task_nx_label(each_tile_task)
                for each_pp_task, nid in pp_tasks_to_node_mapping.iteritems():
                    if each_tile_task_nx_label in each_pp_task:
                        selected_node_id = nid
                        break
                    else:
                        pass
                
                assert(selected_node_id != None), ", no node was selected !! \n %s \n %s"% (pp_tasks_to_node_mapping.__repr__(),
                                                                                            each_tile_task_nx_label)
                
                ## updates to local copies of structures ##                                                         
                # update frame mapping struct
                tile_task_id = each_tile_task.get_id()
                tile_to_node_mapping[tile_task_id] = selected_node_id
                
                # record pri-ass for the tile
                tile_pri_assignment[tile_task_id] = each_tile_task.get_priority()
            
            print "--> PP: All stages finished : num_tg_nodes=%d, num_unique_PEs_used=%d" %(
                                                                                           len(nxDAG_tiles_copy.nodes()),
                                                                                           len(set(tile_to_node_mapping.values()))
                                                                                           )
            
            ### Offset timing calculation : start ####
            offset_clock_stop_timer_pytime = time.time()
            offset_clock_stop_timer_pyclock = time.clock()
            offset_clock_stop_timer_pytimeit = timeit.default_timer()
            
            pp_offset_pytime = (offset_clock_stop_timer_pytime - offset_clock_start_timer_pytime)
            pp_offset_pyclock = (offset_clock_stop_timer_pyclock - offset_clock_start_timer_pyclock)
            pp_offset_pytimeit = (offset_clock_stop_timer_pytimeit - offset_clock_start_timer_pytimeit)
                        
            # take into account temporary merging time (this is extra time that should be taken off due to non-optimised implementation)
            pp_offset_pytime += (track_temp_merge_time_taken[0]*0.2)
            pp_offset_pyclock += (track_temp_merge_time_taken[1]*0.2)
            pp_offset_pytimeit += (track_temp_merge_time_taken[2]*0.2)            
            ###
            
            # ----------------- intelligent bit : end  ---------------------------------------------------------------------
            
            # update mmc node mapping table
            mmc_mapping = self._map_to_mmc_mappingtbl(tile_to_node_mapping, all_sorted_hevc_tile_tasks, copy_vnoctt)
                        
            # timing
            if (SimParams.TRACK_MAPPER_EXECOVERHEAD == True):
                self._record_time_stop(offset_pytime=pp_offset_pytime, 
                                       offset_pyclock=pp_offset_pyclock, 
                                       offset_pytimeit=pp_offset_pytimeit,                                       
                                       )
            
            self.mmc_selector._populate_VNOCTT(gop_tasks, all_sorted_hevc_tile_tasks, 
                                   tile_to_node_mapping, mmc_mapping, 
                                   gop_tasks[0].get_adaptiveGoP_Obj(), 
                                   gop_tasks[0].getNumSubTasksTiles())
            
            
            # update the processing core on the tile tasks objects
            for each_t_id, each_t in all_sorted_hevc_tile_tasks.iteritems():
                all_sorted_hevc_tile_tasks[each_t_id].set_processingCore(tile_to_node_mapping[each_t_id])
            
            
            assert (len(all_sorted_hevc_tile_tasks.keys()) == (gop_tasks[0].getNumSubTasksTiles()*len(gop_tasks[0].get_gopstructure()))), \
             ":: incorrect number of tiles - %d, %d" %(len(all_sorted_hevc_tile_tasks.keys()),
                                                    (gop_tasks[0].getNumSubTasksTiles()*len(gop_tasks[0].get_gopstructure())))
     
            
               
            # update task mapping table    
            self._map_to_vidstrm_tile_mappingtbl_overwrite(tile_to_node_mapping, tile_pri_assignment, wf_id, strm_id)     
                                               
            return (tile_to_node_mapping, tile_pri_assignment, self.tiletasks_list_to_dict(all_sorted_hevc_tile_tasks.values()))
        else:
            return (None, None)
    
    
    
    
    def _kaushik_helper_update_copy_vtmtbl(self, copy_vtmtbl, selected_node_id, each_tile_task):
        # update local copy of vtmtbl
        if (selected_node_id not in copy_vtmtbl):
            copy_vtmtbl[selected_node_id] = [self._get_vtmtbl_targettiletask_entry(each_tile_task, selected_node_id, 
                                                                               each_tile_task.get_priority())]
        else:
            copy_vtmtbl[selected_node_id].append(self._get_vtmtbl_targettiletask_entry(each_tile_task, selected_node_id, 
                                                                                   each_tile_task.get_priority()))        
        return copy_vtmtbl
    
        
    #####################################################################################
    # TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_LOWMAPPEDWITHMONITORING_V1
    #####################################################################################
    # first the vid stream is assigned a frame-level semi-dynamic priority scheme
    # (PR: lowest res first)
    # then,
    # (MP: splits the tasks into tiles, assigns the tiles to the PEs)
    def taskTileMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPLowMappedWithMonitoring_v1(self, strm_specs):
        # build pseudo frame-mappings dict
        empty_frame_mappings = self._get_empty_frame_mappings_dict(strm_specs)        
        # get frame level priorities
        frame_priorities = self.common_priass_schm(strm_specs,empty_frame_mappings)                     
        # get list of nodes that are free 
        free_nodes_list = self.RM_instance.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL)       
        copy_vtmtbl = self._get_deepcopy_volatiletaskmappingtable()
        copy_vnoctt = self.RM_instance.flow_table.getVNOCTT_copy()

        if(len(free_nodes_list)>0):    
            wf_id = strm_specs['wf_id']
            strm_id = strm_specs['vid_strm_id']
            gop_tasks = strm_specs['gop_tasks']
                        
            # (1) sort tasks into dependency order - perform topological sort on the graph
            # (2) sort bins in descending order of cumulative WCRS - reordering is every time a new task is added
            # (3) each task is added to the PE with max cum. WCRS            
            
            all_sorted_hevc_tile_tasks = self._get_sorted_tile_tasks(strm_specs, frame_priorities)
            
            # ----------------- intelligent bit : start ---------------------------------------------------------------------
            # for each item check if it can be accomodated into bin_i           
            tile_pri_assignment = {} 
            tile_to_node_mapping = OrderedDict()             
            for each_tile_task_id, each_tile_task in all_sorted_hevc_tile_tasks.iteritems():
                # assign to node with max cumslack
                selected_node_id = self._get_node_lowest_mapped_viavmtbl(copy_vtmtbl, free_nodes_list)
                
                # update local copy of vtmtbl
                if (selected_node_id not in copy_vtmtbl):
                    copy_vtmtbl[selected_node_id] = [self._get_vtmtbl_targettiletask_entry(each_tile_task, selected_node_id, 
                                                                                       each_tile_task.get_priority())]
                else:
                    copy_vtmtbl[selected_node_id].append(self._get_vtmtbl_targettiletask_entry(each_tile_task, selected_node_id, 
                                                                                           each_tile_task.get_priority()))   
#                 print "---"
#                 print     copy_vtmtbl
#                 print "---"                         
                # update frame mapping struct
                tile_task_id = each_tile_task.get_id()
                tile_to_node_mapping[tile_task_id] = selected_node_id
                
                # record pri-ass for the tile
                tile_pri_assignment[tile_task_id] = each_tile_task.get_priority()
            
            # ----------------- intelligent bit : end  ---------------------------------------------------------------------
            
            # update the processing core on the tile tasks objects
            for each_t_id, each_t in all_sorted_hevc_tile_tasks.iteritems():
                all_sorted_hevc_tile_tasks[each_t_id].set_processingCore(tile_to_node_mapping[each_t_id])
            
            
            assert (len(all_sorted_hevc_tile_tasks.keys()) == (gop_tasks[0].getNumSubTasksTiles()*len(gop_tasks[0].get_gopstructure()))), \
             ":: incorrect number of tiles - %d, %d" %(len(all_sorted_hevc_tile_tasks.keys()),
                                                    (gop_tasks[0].getNumSubTasksTiles()*len(gop_tasks[0].get_gopstructure())))
            
#             pprint.pprint(tile_to_node_mapping)
#             sys.exit()
                        
            # update task mapping table    
            self._map_to_vidstrm_tile_mappingtbl_overwrite(tile_to_node_mapping, tile_pri_assignment, wf_id, strm_id)  
            
            # update mmc node mapping table
            mmc_mapping = self._map_to_mmc_mappingtbl(tile_to_node_mapping, all_sorted_hevc_tile_tasks, copy_vnoctt)
            
            self.mmc_selector._populate_VNOCTT(gop_tasks, all_sorted_hevc_tile_tasks, 
                                   tile_to_node_mapping, mmc_mapping, 
                                   gop_tasks[0].get_adaptiveGoP_Obj(), 
                                   gop_tasks[0].getNumSubTasksTiles())
                                      
            return (tile_to_node_mapping, tile_pri_assignment, self.tiletasks_list_to_dict(all_sorted_hevc_tile_tasks.values()))
        else:
            return (None, None)
    
    
    #####################################################################################
    # TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_CLUSTLS_MOSTSLACK_VIA_VTMTBL
    #####################################################################################
    # first the vid stream is assigned a frame-level semi-dynamic priority scheme
    # (PR: lowest res first)
    # then,
    # (MP: splits the tasks into tiles, assigns the tiles to the PEs)
    # use only WCRS heuristic - cluster tiles together
    def taskTileMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPClusteredTilesMostSlackViaTmTbl_v1(self, strm_specs, use_avgcc=False):
        # build pseudo frame-mappings dict
        empty_frame_mappings = self._get_empty_frame_mappings_dict(strm_specs)
        
        # get frame level priorities
        frame_priorities = self.common_priass_schm(strm_specs,empty_frame_mappings)
                     
        # get list of nodes that are free 
        free_nodes_list = self.RM_instance.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL)
        free_nodes_list_nids = [n.get_id() for n in free_nodes_list]
        inner_nodes = self.RM_instance.interconnect.getInnerNodes_1border()         
        copy_vtmtbl = self._get_deepcopy_volatiletaskmappingtable()
        copy_vnoctt = self.RM_instance.flow_table.getVNOCTT_copy()
        copy_vmtblusagetbl = self._get_deepcopy_nodeusage_volatiletaskmappingtable()
        
        if(len(inner_nodes)>0):    
            wf_id = strm_specs['wf_id']
            strm_id = strm_specs['vid_strm_id']
            gop_struct = strm_specs['gop_struct']
            gop_tasks = strm_specs['gop_tasks']
            
            NHOPS_1 = 1
            NHOPS_2 = 2
            
            # (1) sort tasks into dependency order - perform topological sort on the graph
            # (2) map tasks such that tiles are clustered together and close to parent tasks
            all_sorted_hevc_tile_tasks = self._get_sorted_tile_tasks(strm_specs, frame_priorities)
            n_tiles_all = len(all_sorted_hevc_tile_tasks.keys())
            temp_tile_id = all_sorted_hevc_tile_tasks.keys()[0]
            n_tiles_per_frame = all_sorted_hevc_tile_tasks[temp_tile_id].getNumSubTasksTiles()
            
            
            gc.disable()
            start_time = timeit.default_timer()
            
                        
            (NHOPS_TILE_PARTITIONS, 
             NHOPS_CHILDREN_TASKS, 
             CONSTRAINED_NODE_CNT) = self._get_best_num_hops_vidstream_specific(gop_tasks, n_tiles_all, n_tiles_per_frame)          
             
            print (NHOPS_TILE_PARTITIONS,  NHOPS_CHILDREN_TASKS, CONSTRAINED_NODE_CNT)
            
            # ----------------- intelligent bit : start ---------------------------------------------------------------------                       
            tile_pri_assignment = {} 
            tile_to_node_mapping = OrderedDict()    
            
            tile_00_node_id = None
            rnd_neighbour_nodes_tile_00 = None
                     
            for each_tile_task_id, each_tile_task in all_sorted_hevc_tile_tasks.iteritems():
                
                tile_task_parents = each_tile_task.get_expected_data_from_parents()
                tile_task_ftype = each_tile_task.get_frameType()
                selected_node_id= None
                
                ### FIRST TILE OF ROOT NODE ###
                # if this task is tile0 of root node, ignore and use the WCRS heuristic to find first node
                if tile_task_ftype=="I" and ("_0" in each_tile_task_id):                    
                    # assign to node with max cumslack
                    selected_node_id = self._get_node_with_max_wcrs_default_LU(copy_vtmtbl, inner_nodes, 
                                                                    copy_vmtblusagetbl=copy_vmtblusagetbl, 
                                                                    use_avgcc=use_avgcc, selection_type='node_usage_min',
                                                                    running_tile_mappings = tile_to_node_mapping,
                                                                    number_of_total_tiles = n_tiles_all)
#                       
#                     selected_node_id = self._get_node_lowest_util_viavmtbl(copy_vtmtbl, inner_nodes, use_avgcc=use_avgcc,
#                                                                            running_tile_mappings=tile_to_node_mapping,
#                                                                            number_of_total_tiles=n_tiles)
                    
                    neighbour_nodes_tile_00 = self.RM_instance.interconnect.getNodesNHops(selected_node_id,1) 
                    rnd_neighbour_nodes_tile_00 = random.choice(neighbour_nodes_tile_00)
                    tile_00_node_id = selected_node_id
                    
                    
                else:                    
                    ### OTHER TILES OF ROOT NODE ###                                                   
                    if len(tile_task_parents.keys()) == 0: # does this task have parents ? # only I-frames don't                        
                        # set node N-hop distance from tile 0:
                        tile_00_id  = "%d_%d" % (each_tile_task.getTileParentFrameId(), 0) 
                        tile_00_node_id = tile_to_node_mapping[tile_00_id]
                        
                        nearest_nhop_node_nids = self.RM_instance.interconnect.getNodesNHops(tile_00_node_id,NHOPS_TILE_PARTITIONS)
                        # include parent nodeid into search list
                        nearest_nhop_node_nids.append(tile_00_node_id)
                        
                        # we search these nodes for the one with the highest worst-case slack
                        selected_node_id = self._get_node_with_max_wcrs_default_LU(copy_vtmtbl, nearest_nhop_node_nids, 
                                                                        copy_vmtblusagetbl=copy_vmtblusagetbl, 
                                                                        use_avgcc=use_avgcc, selection_type='node_usage_min',
                                                                        running_tile_mappings = tile_to_node_mapping,
                                                                        number_of_total_tiles = n_tiles_all)
                          
#                         selected_node_id = self._get_node_lowest_util_viavmtbl(copy_vtmtbl, nearest_nhop_node_nids, use_avgcc=use_avgcc,
#                                                                                running_tile_mappings=tile_to_node_mapping,
#                                                                                number_of_total_tiles=n_tiles)
                        
                        
                    ### OTHER TILES OF NON-ROOT NODEs ###                    
                    else:                        
                        # sort parents according to their payload we find the X number of parents with highest payload
                        # find nhop nodes for each parent, and then find the intersection between these nodes
                        X_num_parents = 2
                        sorted_parents_by_payload_list = sorted(tile_task_parents.items(), key=itemgetter(1)) # tuples (pid, payload)                        
                        if len(sorted_parents_by_payload_list) > X_num_parents:                        
#                             #print "cluster_mapper -- 4"
                            list_of_sets = []                            
                            for i in xrange(X_num_parents):
                                p_nid = tile_to_node_mapping[sorted_parents_by_payload_list[i][0]]
                                assert(p_nid < (SimParams.NOC_W*SimParams.NOC_H)), "%d, %d" %(p_nid, SimParams.NOC_W*SimParams.NOC_H)                           
                                set_nhops_p_i = self.RM_instance.interconnect.getNodesNHops(p_nid,NHOPS_CHILDREN_TASKS)
                                set_nhops_p_i.append(p_nid)
                                set_nhops_p_i = set(set_nhops_p_i)
                                list_of_sets.append(set_nhops_p_i)
                            
                            # intersections between all nodes
                            set_node_intersection = list(set.intersection(*list_of_sets))
                            if len(set_node_intersection)>0:                               
                                # we search these nodes for the one with the highest worst-case slack
                                selected_node_id = self._get_node_with_max_wcrs_default_LU(copy_vtmtbl, set_node_intersection, 
                                                                                copy_vmtblusagetbl=copy_vmtblusagetbl, 
                                                                                use_avgcc=use_avgcc, selection_type='node_usage_min',
                                                                                running_tile_mappings = tile_to_node_mapping,
                                                                                number_of_total_tiles = n_tiles_all)
                                
#                                 selected_node_id = self._get_node_lowest_util_viavmtbl(copy_vtmtbl, 
#                                                                                        set_node_intersection, 
#                                                                                        use_avgcc=use_avgcc,
#                                                                                        running_tile_mappings=tile_to_node_mapping,
#                                                                                        number_of_total_tiles=n_tiles)
                                 
                                
                            # there is no intersection
                            else:
                                most_payload_p = sorted_parents_by_payload_list[0] # tuple
                                p_nid = tile_to_node_mapping[most_payload_p[0]]                                
                                set_nhops_p_i = self.RM_instance.interconnect.getNodesNHops(p_nid,NHOPS_CHILDREN_TASKS)                                
                                set_nhops_p_i.append(p_nid)
                                selected_node_id = self._get_node_with_max_wcrs_default_LU(copy_vtmtbl, set_nhops_p_i,
                                                                                copy_vmtblusagetbl=copy_vmtblusagetbl, 
                                                                                use_avgcc=use_avgcc, selection_type='node_usage_min',
                                                                                running_tile_mappings = tile_to_node_mapping,
                                                                                number_of_total_tiles = n_tiles_all)
                                 

#                                 selected_node_id = self._get_node_lowest_util_viavmtbl(copy_vtmtbl, 
#                                                                                        set_nhops_p_i, 
#                                                                                        use_avgcc=use_avgcc,
#                                                                                        running_tile_mappings=tile_to_node_mapping,
#                                                                                        number_of_total_tiles=n_tiles)         
                                
                                
                        else: # case where only one parent tile (very small tile splittings)
                            p_nid = tile_to_node_mapping[sorted_parents_by_payload_list[0][0]] # parent with highest payload
                            selected_node_id = self._get_node_with_max_wcrs_default_LU(copy_vtmtbl, 
                                                                            self.RM_instance.interconnect.getNodesNHops(p_nid,NHOPS_1), 
                                                                            copy_vmtblusagetbl=copy_vmtblusagetbl, 
                                                                            use_avgcc=use_avgcc, selection_type='node_usage_min',
                                                                            running_tile_mappings = tile_to_node_mapping,
                                                                            number_of_total_tiles = n_tiles_all)
                            
                
                assert(selected_node_id != None), ", no node was selected !!"
                
                ## updates to local copies of structures ##                
                # update local copy of vtmtbl
                if (selected_node_id not in copy_vtmtbl):
                    copy_vtmtbl[selected_node_id] = [self._get_vtmtbl_targettiletask_entry(each_tile_task, selected_node_id, 
                                                                                       each_tile_task.get_priority())]
                else:
                    copy_vtmtbl[selected_node_id].append(self._get_vtmtbl_targettiletask_entry(each_tile_task, selected_node_id, 
                                                                                           each_tile_task.get_priority()))    
                # update local copy of node usage table
                copy_vmtblusagetbl[selected_node_id] += each_tile_task.get_worstCaseComputationCost()                
                                            
                # update frame mapping struct
                tile_task_id = each_tile_task.get_id()
                tile_to_node_mapping[tile_task_id] = selected_node_id
                
                # record pri-ass for the tile
                tile_pri_assignment[tile_task_id] = each_tile_task.get_priority()
                
            # ----------------- intelligent bit : end  ---------------------------------------------------------------------
            
            # update the processing core on the tile tasks objects
            for each_t_id, each_t in all_sorted_hevc_tile_tasks.iteritems():
                all_sorted_hevc_tile_tasks[each_t_id].set_processingCore(tile_to_node_mapping[each_t_id])
            
            
            assert (len(all_sorted_hevc_tile_tasks.keys()) == (gop_tasks[0].getNumSubTasksTiles()*len(gop_tasks[0].get_gopstructure()))), \
             ":: incorrect number of tiles - %d, %d" %(len(all_sorted_hevc_tile_tasks.keys()),
                                                    (gop_tasks[0].getNumSubTasksTiles()*len(gop_tasks[0].get_gopstructure())))
            
            
            if (len(set(tile_to_node_mapping.values())) <= 1):            
                print "tile_to_node_mapping :"
                pprint.pprint(tile_to_node_mapping)
                #sys.exit()
                print "copy_vtmtbl :"
                pprint.pprint(copy_vtmtbl)
                print "node_usage :"
                pprint.pprint(self._get_deepcopy_nodeusage_volatiletaskmappingtable())
            
            assert (len(set(tile_to_node_mapping.values())) > 1), ", something wrong - all nodes selected are the same : nid=%d" % list(set(tile_to_node_mapping.values()))[0]
            
            # update mmc node mapping table
            mmc_mapping = self._map_to_mmc_mappingtbl(tile_to_node_mapping, all_sorted_hevc_tile_tasks, copy_vnoctt)
            
            self.mmc_selector._populate_VNOCTT(gop_tasks, all_sorted_hevc_tile_tasks, 
                                   tile_to_node_mapping, mmc_mapping, 
                                   gop_tasks[0].get_adaptiveGoP_Obj(), 
                                   gop_tasks[0].getNumSubTasksTiles())
            
            elapsed = timeit.default_timer() - start_time
            print "ElapsedTime = %.20f" %  elapsed
            gc.enable()
               
            # update task mapping table    
            self._map_to_vidstrm_tile_mappingtbl_overwrite(tile_to_node_mapping, tile_pri_assignment, wf_id, strm_id)     
                                   
            return (tile_to_node_mapping, tile_pri_assignment, self.tiletasks_list_to_dict(all_sorted_hevc_tile_tasks.values()))
        else:
            return (None, None)
    
    
    #####################################################################################
    # TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_MOSTSLACK_VIA_VTMTBL
    #####################################################################################
    # first the vid stream is assigned a frame-level semi-dynamic priority scheme
    # (PR: lowest res first)
    # then,
    # (MP: splits the tasks into tiles, assigns the tiles to the PEs)
    # use only WCRS heuristic - no indication of communication cost awareness
    def taskTileMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPMostSlackViaTmTbl_v1(self, strm_specs, use_avgcc=False):
        # build pseudo frame-mappings dict
        empty_frame_mappings = self._get_empty_frame_mappings_dict(strm_specs)
        
        # get frame level priorities
        frame_priorities = self.common_priass_schm(strm_specs,empty_frame_mappings)
                     
        # get list of nodes that are free 
        free_nodes_list = self.RM_instance.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL) 
        free_nodes_list_nids = [n.get_id() for n in free_nodes_list]      
        copy_vtmtbl = self._get_deepcopy_volatiletaskmappingtable()
        copy_vnoctt = self.RM_instance.flow_table.getVNOCTT_copy()
        
#         print "---- map --"
#         pprint.pprint(copy_vtmtbl)
#         print "---- map --"        
        
        if(len(free_nodes_list)>0):    
            wf_id = strm_specs['wf_id']
            strm_id = strm_specs['vid_strm_id']
            gop_struct = strm_specs['gop_struct']
            gop_tasks = strm_specs['gop_tasks']
            
            # (1) sort tasks into dependency order - perform topological sort on the graph
            # (2) sort bins in descending order of cumulative WCRS - reordering is every time a new task is added
            # (3) each task is added to the PE with max cum. WCRS            
            
            all_sorted_hevc_tile_tasks = self._get_sorted_tile_tasks(strm_specs, frame_priorities)
            n_tiles = len(all_sorted_hevc_tile_tasks.keys())
            # ----------------- intelligent bit : start ---------------------------------------------------------------------
            # for each item check if it can be accomodated into bin_i           
            tile_pri_assignment = {} 
            tile_to_node_mapping = OrderedDict()             
            for each_tile_task_id, each_tile_task in all_sorted_hevc_tile_tasks.iteritems():
                # assign to node with max cumslack
                selected_node_id = self._get_node_with_max_wcrs(copy_vtmtbl, free_nodes_list_nids, use_avgcc=use_avgcc,
                                                                running_tile_mappings = tile_to_node_mapping,
                                                                number_of_total_tiles = n_tiles)
                
                # update local copy of vtmtbl
                if (selected_node_id not in copy_vtmtbl):
                    copy_vtmtbl[selected_node_id] = [self._get_vtmtbl_targettiletask_entry(each_tile_task, selected_node_id, 
                                                                                       each_tile_task.get_priority())]
                else:
                    copy_vtmtbl[selected_node_id].append(self._get_vtmtbl_targettiletask_entry(each_tile_task, selected_node_id, 
                                                                                           each_tile_task.get_priority()))                                
                # update frame mapping struct
                tile_task_id = each_tile_task.get_id()
                tile_to_node_mapping[tile_task_id] = selected_node_id
                
                # record pri-ass for the tile
                tile_pri_assignment[tile_task_id] = each_tile_task.get_priority()
            
            # ----------------- intelligent bit : end  ---------------------------------------------------------------------
            
            # update the processing core on the tile tasks objects
            for each_t_id, each_t in all_sorted_hevc_tile_tasks.iteritems():
                all_sorted_hevc_tile_tasks[each_t_id].set_processingCore(tile_to_node_mapping[each_t_id])
            
            
            assert (len(all_sorted_hevc_tile_tasks.keys()) == (gop_tasks[0].getNumSubTasksTiles()*len(gop_tasks[0].get_gopstructure()))), \
             ":: incorrect number of tiles - %d, %d" %(len(all_sorted_hevc_tile_tasks.keys()),
                                                    (gop_tasks[0].getNumSubTasksTiles()*len(gop_tasks[0].get_gopstructure())))
            
            
            # update mmc node mapping table
            mmc_mapping = self._map_to_mmc_mappingtbl(tile_to_node_mapping, all_sorted_hevc_tile_tasks, copy_vnoctt)
            
            self.mmc_selector._populate_VNOCTT(gop_tasks, all_sorted_hevc_tile_tasks, 
                                   tile_to_node_mapping, mmc_mapping, 
                                   gop_tasks[0].get_adaptiveGoP_Obj(), 
                                   gop_tasks[0].getNumSubTasksTiles())
                        
            # update task mapping table    
            self._map_to_vidstrm_tile_mappingtbl_overwrite(tile_to_node_mapping, tile_pri_assignment, wf_id, strm_id)     
                                   
            return (tile_to_node_mapping, tile_pri_assignment, self.tiletasks_list_to_dict(all_sorted_hevc_tile_tasks.values()))
        else:
            return (None, None)
    
    
    
    #####################################################################################
    #####################################################################################
    # HELPER functions
    #####################################################################################
    
    #####################################################
    # Helpers: misc
    #####################################################
    def constrained_sum_sample_pos(self, n, total):
        #random.seed(SimParams.HEVC_FRAME_GENRAND_SEED)
        """Return a randomly chosen list of n positive integers summing to total.
        Each such list is equally likely to occur."""
        # source : http://stackoverflow.com/questions/3589214/generate-multiple-random-numbers-to-equal-a-value-in-python
        dividers = sorted(random.sample(xrange(1, total), n - 1))
        return [a - b for a, b in zip(dividers + [total], [0] + dividers)]   
    
    
    def tiletasks_list_to_dict(self, all_tiletasks):
        tiletasks_dict = OrderedDict()
        for each_tile_t in all_tiletasks:
            if each_tile_t.getTileParentFrameId() not in tiletasks_dict:
                tiletasks_dict[each_tile_t.getTileParentFrameId()] = []
                tiletasks_dict[each_tile_t.getTileParentFrameId()].append(each_tile_t)
            else:
                tiletasks_dict[each_tile_t.getTileParentFrameId()].append(each_tile_t)
        
        return tiletasks_dict
    
    
    def get_pyobj_total_size(self, o, handlers={}, verbose=False):
        """ Returns the approximate memory footprint an object and all of its contents.
    
        Automatically finds the contents of the following builtin containers and
        their subclasses:  tuple, list, deque, dict, set and frozenset.
        To search other containers, add handlers to iterate over their contents:
    
            handlers = {SomeContainerClass: iter,
                        OtherContainerClass: OtherContainerClass.get_elements}
    
        """
        dict_handler = lambda d: chain.from_iterable(d.items())
        all_handlers = {tuple: iter,
                        list: iter,
                        deque: iter,
                        dict: dict_handler,
                        set: iter,
                        frozenset: iter,
                       }
        all_handlers.update(handlers)     # user handlers take precedence
        seen = set()                      # track which object id's have already been seen
        default_size = getsizeof(0)       # estimate sizeof object without __sizeof__
    
        def sizeof(o):
            if id(o) in seen:       # do not double count the same object
                return 0
            seen.add(id(o))
            #print(s, type(o), repr(o))  ## , file=stderr)`
            s = getsizeof(o, default_size)
    
            #if verbose:
            #    print(s, type(o), repr(o), file=stderr)
    
            for typ, handler in all_handlers.items():
                if isinstance(o, typ):
                    s += sum(map(sizeof, handler(o)))
                    break
            return s
    
        return sizeof(o)
    
    
    def _record_time_start(self):
        # disable garbage collector
        gc.disable()
        # record
        self.start_timer_pytime = time.time()
        self.start_timer_pyclock = time.clock()
        self.start_timer_pytimeit = timeit.default_timer()
    
    def _record_time_stop(self, offset_pytime=0.0, offset_pyclock=0.0, offset_pytimeit=0.0):
        now_timer_pytime = time.time()
        now_timer_pyclock = time.clock()
        now_timer_pytimeit = timeit.default_timer()
        
        elapsed_timer_pytime = (now_timer_pytime - self.start_timer_pytime) - offset_pytime  
        elapsed_timer_pyclock = (now_timer_pyclock - self.start_timer_pyclock) - offset_pyclock
        elapsed_timer_pytimeit = (now_timer_pytimeit - self.start_timer_pytimeit) - offset_pytimeit
        
        # reset        
        #self.timer_pytime = None
        #self.timer_pyclock = None
        #self.timer_pytimeit = None
        
        self.start_timer_pytime = None
        self.start_timer_pyclock = None
        self.start_timer_pytimeit = None
        
        # track the elapsed time
        self.track_execution_overhead.append([elapsed_timer_pytime,
                                              elapsed_timer_pyclock,
                                              elapsed_timer_pytimeit
                                              ])
        
        # enable garbage collector
        gc.enable()
    
    
    
    #####################################################
    # Helpers: nx graph related helpers
    #####################################################
    
    # if there are multiple edges with eqv. weights, we pick the edge with the 
    # lowest cumumlative node weights.
    def _nxdg_choose_edge_with_max_weight(self, gop_adap_obj, nxdg):
        #maxcload_edges_dict = gop_adap_obj.get_edges_max_weight(nxdg)        
        
        all_edges_dict = nx.get_edge_attributes(nxdg, 'weight')
        all_node_weights = nx.get_node_attributes(nxdg, 'weight')
        max_w =  np.max(all_edges_dict.values())
        all_edges_with_max_weight = [k for k,v in all_edges_dict.iteritems() if v == max_w]
        # output keys + vals
        maxcload_edges_dict = {}
        for each_edge in all_edges_with_max_weight:
            combined_node_weight = (all_node_weights[each_edge[0]]+all_node_weights[each_edge[1]]) 
            maxcload_edges_dict[each_edge] = (max_w, combined_node_weight)
        
        # if morre than one edge, find one with lowest comb node weight
        if len(maxcload_edges_dict.keys()) > 1:   
            min_combined_node_weight = np.min([v[1] for k,v in maxcload_edges_dict.iteritems()])
            min_v_e= [k for k,v in maxcload_edges_dict.iteritems() if v[1] == min_combined_node_weight][0]
            edge_weight = all_edges_dict[min_v_e]
            return (min_v_e, edge_weight)
        else:
            return (maxcload_edges_dict.keys()[0], maxcload_edges_dict.values()[0][0])
             
        
            
    # if there are multiple nodes with equivalent weights, we pick the first one
    def _nxdg_choose_node_with_max_weight(self,gop_adap_obj, nxdg):
        maxpload_nodes_dict = gop_adap_obj.get_nodes_max_weight(nxdg)
        
        if len(maxpload_nodes_dict.keys()) > 1:  
            k = sorted(maxpload_nodes_dict.keys())[0] # we sort and take the first one
            return (k, maxpload_nodes_dict[k])
        else:
            return (maxpload_nodes_dict.keys()[0], maxpload_nodes_dict.values()[0])
            
    
    # get n nodes with lowest weight
    def _nxdg_choose_n_nodes_with_min_weight(self,gop_adap_obj, nxdg, n):
        sorted_nodes_by_weight_increasing_tuples = gop_adap_obj.get_nodes_sorted_weight(nxdg)        
        if len(sorted_nodes_by_weight_increasing_tuples) < n:
            return sorted_nodes_by_weight_increasing_tuples
        else:
            return sorted_nodes_by_weight_increasing_tuples[:n]
    
    # get n edges with lowest weight
    def _nxdg_choose_n_edges_with_min_weight(self,gop_adap_obj, nxdg, n):
        sorted_edges_by_weight_increasing_tuples = gop_adap_obj.get_edges_sorted_weight(nxdg)        
        if len(sorted_edges_by_weight_increasing_tuples) < n:
            return sorted_edges_by_weight_increasing_tuples
        else:
            return sorted_edges_by_weight_increasing_tuples[:n]
    
    # for all nodes in the network, find combined load of every two nodes (couples)
    def _nxdg_get_sorted_combined_loads(self,gop_adap_obj, nxdg, rev=False):
        result = {}
        combos_str = []
        for each_n_i, data_n_i in nxdg.nodes(data='weight'):
            for each_n_j, data_n_j in nxdg.nodes(data='weight'):
                
                # checking (same combo shouldn't be counted twice)
                fwd_npair_str = "%s--%s" %(each_n_i, each_n_j)
                bwd_npair_str = "%s--%s" %(each_n_j, each_n_i)
                
                if (fwd_npair_str not in combos_str) and \
                    (bwd_npair_str not in combos_str) and \
                    (each_n_i != each_n_j):
                                                     
                        combined_weight = data_n_i['weight'] + data_n_j['weight']
                        node_tuple_k = (each_n_i, each_n_j)
                        result[node_tuple_k] = combined_weight
                        combos_str.append("%s--%s" %(each_n_i, each_n_j))        
                
                
        # sort
        sorted_result = sorted(result.items(), key=operator.itemgetter(1), reverse=rev)   # list of tuples
        
        return sorted_result
        
    # for all nodes in the network, find combined processing load of every two nodes (couples)
    def _nxdg_get_sorted_combined_loads_of_edges(self,gop_adap_obj, nxdg):
        result = {}
        for each_ti, each_tj, data in nxdg.edges(data='weight'):
            each_ti_w = gop_adap_obj.get_node_weight(nxdg, each_ti)
            each_tj_w = gop_adap_obj.get_node_weight(nxdg, each_tj)            
            combined_load = each_ti_w + each_tj_w            
            node_tuple_k = (each_ti, each_tj)
            result[node_tuple_k] = combined_load
        
        return result
    
    
    # find the two nodes in the nx which have the smallest combined load
    def _nxdg_get_min_combined_loads_of_edges(self,gop_adap_obj, nxdg):
        result = {}
        node_weights = nx.get_node_attributes(nxdg, 'weight')
#         for each_ti, each_tj, data in nxdg.edges(data='weight'):
#             each_ti_w = node_weights[each_ti]
#             each_tj_w = node_weights[each_tj]            
#             combined_load = each_ti_w + each_tj_w            
#             node_tuple_k = (each_ti, each_tj)
#             result[node_tuple_k] = combined_load
        
        result = { (n1,n2): node_weights[n1]+node_weights[n2] for (n1,n2, data) in nxdg.edges(data='weight')} # dict comprehension
        
        min_v = np.min(result.values())
        min_v_nodes = [k for k,v in result.iteritems() if v == min_v][0]
        
        return (min_v_nodes, min_v)
    
    
    # are the two nodes communicating ?
    def _nxdg_are_nodes_communicating(self, node0, node1, nxdg):
        all_edges_tuples_list = nxdg.edges()        
        flag=False
        for n0, n1 in all_edges_tuples_list:
            if (n0 == node0) and (n1 == node1):
                flag=True
                break
            elif (n0 == node1) and (n1 == node0):
                flag=True
                break
            else:
                pass
            
        return flag
    
    # who are the other tile tasks grouped with target tile task ??
    def _nxdg_find_other_nodes_clustered_with_target_node(self, nxdg, target_node_nxlbl):        
        other_tile_tasks_nxlbls = None
        for each_node in nxdg.nodes():
            temp_other_tile_tasks_nxlbls = each_node.split(";")
            if (target_node_nxlbl in temp_other_tile_tasks_nxlbls): # found grouping
                other_tile_tasks_nxlbls = temp_other_tile_tasks_nxlbls                 
                break
            else:
                pass
            
        assert(other_tile_tasks_nxlbls != None), "_nxdg_find_other_nodes_clustered_with_target_node: Error"
        
        return other_tile_tasks_nxlbls
    
    
    #####################################################
    # Helpers: finding the best distance from parents
    #####################################################   
    
    def _get_parent_with_highest_probable_payload(self, tile_task_parents, all_tile_tasks_dict):
        temp_parents_dict = {
                             "I" :[], "P" : [], "B" :[]
                             }
        for each_p_tid, payload in tile_task_parents.iteritems():
            p_ftype = all_tile_tasks_dict[each_p_tid].get_frameType()
            if p_ftype == "I" : 
                temp_parents_dict["I"].append(each_p_tid)
            elif p_ftype == "P" :
                temp_parents_dict["P"].append(each_p_tid)
            elif p_ftype == "B" :
                temp_parents_dict["B"].append(each_p_tid)
            else:
                sys.exit("_get_parent_with_highest_probable_payload: Error - ftype not known" + p_ftype)
        
        if len(temp_parents_dict["I"]) > 0:
            return temp_parents_dict["I"][0]
        elif len(temp_parents_dict["P"]) > 0:
            return temp_parents_dict["P"][0]
        elif len(temp_parents_dict["B"]) > 0:
            return temp_parents_dict["B"][0]
        else:
            pprint.pprint(temp_parents_dict)
            sys.exit("_get_parent_with_highest_probable_payload: Error - temp_parents_dict is blank")
        
            
        
        
    
     
    def _get_best_num_hops_vidstream_specific(self, gop_tasks, n_tiles_all, n_tiles_per_frame):        
        max_task_wccc = np.max([t.get_worstCaseComputationCost() for t in gop_tasks])        
        gop_e2e = float(len(gop_tasks))/float(gop_tasks[0].get_framerate())
        num_temporal_levels_in_stream = gop_tasks[0].get_adaptiveGoP_Obj().get_numTemporalLevels() # degree of max-parallelism ?
        stream_res = [gop_tasks[0].get_frame_h(), gop_tasks[0].get_frame_w()] 
        
        frame_size_bytes = gop_tasks[0].get_maxMemConsumption()
        flow_basic_latency = self.RM_instance.interconnect.getRouteCost(None, 
                                                                        None, 
                                                                        frame_size_bytes, 
                                                                        nhops=SimParams.NOC_H + SimParams.NOC_W)
        
        total_edges_cost =  gop_tasks[0].get_adaptiveGoP_Obj().getTotalEdges() * flow_basic_latency
        total_nodes_cost = len(gop_tasks) * max_task_wccc
        ratio_ccr = float(total_edges_cost)/float(total_nodes_cost)             
        
        
        print "----> stream_res, ccr : ", stream_res, ratio_ccr        
        
        
        if gop_e2e < (max_task_wccc*num_temporal_levels_in_stream): # in this case, go for maximum parallelism
            #nhops_tile_partitions = np.min([int(SimParams.NOC_W*2), n_tiles_per_frame])
            #nhops_children_tasks = np.min([int(SimParams.NOC_W*2), n_tiles_per_frame])
            
            nhops_tile_partitions = SimParams.NOC_W*2
            nhops_children_tasks = SimParams.NOC_W*2
            
            constrained_node_count = 0
        else:
            if (ratio_ccr > 3):
                nhops_tile_partitions = 1
                nhops_children_tasks = 1
                constrained_node_count = 0
            elif (ratio_ccr > 2):                
                nhops_tile_partitions = 1
                nhops_children_tasks = 1
                constrained_node_count = 0
            else:
                nhops_tile_partitions = np.min([int(round(float(SimParams.NOC_W))), n_tiles_per_frame])
                nhops_children_tasks = np.min([int(round(float(SimParams.NOC_W))), n_tiles_per_frame])
                constrained_node_count = 0
        
        return (nhops_tile_partitions, nhops_children_tasks, constrained_node_count) 
            
        
    
    
    def _get_gop_ccr(self, gop_tasks, n_tiles_all, n_tiles_per_frame, cp_str=None):
        # find ccr 
        max_task_wccc = np.max([t.get_worstCaseComputationCost() for t in gop_tasks])
        
        Iwcc =  gop_tasks[0].get_wccIFrame()
        Pwcc =  gop_tasks[0].get_wccPFrame()
        Bwcc =  gop_tasks[0].get_wccBFrame()
        
        frame_size_bytes = gop_tasks[0].get_maxMemConsumption()
        
        flow_basic_latency = self.RM_instance.interconnect.getRouteCost(None, None, 
                                                                        frame_size_bytes, 
                                                                        nhops=(SimParams.NOC_H-1) + (SimParams.NOC_W-1))                                                                        
        
        total_edges_cost =  float(gop_tasks[0].get_adaptiveGoP_Obj().getTotalEdges()) * flow_basic_latency
        
        total_nodes_cost = 0.0
        for each_t in gop_tasks:
            if each_t.get_frameType() == "I":  total_nodes_cost += Iwcc
            elif each_t.get_frameType() == "P":  total_nodes_cost += Pwcc
            elif each_t.get_frameType() == "B":  total_nodes_cost += Bwcc
            else:
                sys.exit("Error - _get_gop_ccr - here 1")
        
        # cal cp task cost - if cp given
        cp_total_cost = 0.0
        if cp_str != None:            
            for ft in cp_str:
                if ft == "I":  cp_total_cost += Iwcc
                elif ft == "P":  cp_total_cost += Pwcc
                elif ft == "B":  cp_total_cost += Bwcc
                else:
                    sys.exit("Error - _get_gop_ccr - here 1")
                    
                # add the flow cost
                cp_total_cost += (len(cp_str) * flow_basic_latency)
        else:
            pass
            
        
        #total_nodes_cost = len(gop_tasks) * max_task_wccc
        ratio_ccr = float(total_edges_cost)/float(total_nodes_cost)
        return ratio_ccr, Iwcc, Pwcc, Bwcc, flow_basic_latency, total_edges_cost, total_nodes_cost, cp_total_cost
        
    
    
    def _get_ccr_specific_nhops(self, gop_tasks, n_tiles_all, n_tiles_per_frame, cp_str = None):        
        
        (ratio_ccr, Iwcc, Pwcc, Bwcc, 
         flow_basic_latency, total_edges_cost, 
         total_nodes_cost, cp_tot_cost) = self._get_gop_ccr(gop_tasks, 
                                                              n_tiles_all, n_tiles_per_frame,
                                                              cp_str=cp_str)
                     
        NOC_W = float(SimParams.NOC_W)
        e2ed = gop_tasks[0].get_end_to_end_deadline()
        
        # if cp deadline won't be missed 
        if cp_tot_cost < e2ed:        
            # low CCR, high parallelisation
            if (ratio_ccr < SimParams.CLSTR_TILE_PARAM_CCR_RANGES_LOW):
                nhops_cp = np.max([int(NOC_W*2), n_tiles_per_frame])
                nhops_tile = np.max([int(NOC_W*2), n_tiles_per_frame])
                nhops_children = np.max([int(NOC_W*2), n_tiles_per_frame])            
            
            # med CCR, load-balance
            elif (ratio_ccr <= SimParams.CLSTR_TILE_PARAM_CCR_RANGES_MED[1]) and (ratio_ccr >= SimParams.CLSTR_TILE_PARAM_CCR_RANGES_MED[0]):
                nhops_cp = 2
                nhops_tile = np.max([int(round(NOC_W/2.0)), n_tiles_per_frame])
                nhops_children = np.max([int(round(NOC_W/2.0)), n_tiles_per_frame])                
            
            # high CCR, maximum clusterisation
            elif (ratio_ccr > SimParams.CLSTR_TILE_PARAM_CCR_RANGES_HIGH):
                nhops_cp = 2
                nhops_tile = 2
                nhops_children = 2
            else:
                sys.exit("Error - _get_ccr_specific_nhops : unknown ccr")
                
        # if cp deadline will be missed - increased parallelisation (spread tiles out)
        else:
            # low CCR, high parallelisation
            if (ratio_ccr < SimParams.CLSTR_TILE_PARAM_CCR_RANGES_LOW):
                nhops_cp = np.max([int(NOC_W*2), n_tiles_per_frame])
                nhops_tile = np.max([int(NOC_W*2), n_tiles_per_frame])
                nhops_children = np.max([int(NOC_W*2), n_tiles_per_frame])            
            
            # med CCR, load-balance
            elif (ratio_ccr <= SimParams.CLSTR_TILE_PARAM_CCR_RANGES_MED[1]) and (ratio_ccr >= SimParams.CLSTR_TILE_PARAM_CCR_RANGES_MED[0]):
                nhops_cp =  np.ceil(n_tiles_per_frame/2.0)
                nhops_tile = n_tiles_per_frame
                nhops_children = np.ceil(n_tiles_per_frame/2.0)
                          
            # high CCR, maximum clusterisation
            elif (ratio_ccr > SimParams.CLSTR_TILE_PARAM_CCR_RANGES_HIGH):
                nhops_cp = np.ceil(n_tiles_per_frame/2.0)
                nhops_tile = np.ceil(n_tiles_per_frame/2.0)
                nhops_children = np.ceil(n_tiles_per_frame/2.0)
            else:
                sys.exit("Error - _get_ccr_specific_nhops : unknown ccr")
            
        
        ############
        # track ccr
        ############
        vid_resolution =  "%dx%d" % (gop_tasks[0].get_frame_h(),gop_tasks[0].get_frame_w())
        entry = {
                 'n_n': len(gop_tasks), 'n_e': gop_tasks[0].get_adaptiveGoP_Obj().getTotalEdges(),
                 'Iwcc': Iwcc, 
                 'Pwcc': Pwcc, 
                 'Bwcc': Bwcc, 
                 'max_bl': flow_basic_latency,
                 'gopseq': gop_tasks[0].get_gopstructure(),
                 'vid_genre' : gop_tasks[0].get_video_genre(),                 
                 'tot_e_c': total_edges_cost, 'tot_n_c': total_nodes_cost,
                 'ccr': ratio_ccr,
                 'nhops': [nhops_cp, nhops_tile, nhops_children],
                 'e2ed_test': 1 if (cp_tot_cost < e2ed) else 0
                 }
        
        if vid_resolution not in self.track_ccr_level:
            self.track_ccr_level[vid_resolution] = [entry]
        else:
            self.track_ccr_level[vid_resolution].append(entry)
        
        return (nhops_cp, nhops_tile, nhops_children)
    
    
    def _get_ccr_specific_nhops_bgroup_mapping(self, gop_tasks, n_tiles_all, n_tiles_per_frame, cp_str=None):        
        
        (ratio_ccr, Iwcc, Pwcc, Bwcc,flow_basic_latency, 
         total_edges_cost, total_nodes_cost, cp_tot_cost) = self._get_gop_ccr(gop_tasks, n_tiles_all, n_tiles_per_frame, cp_str=cp_str)
                     
        NOC_W = float(SimParams.NOC_W)
        e2ed = gop_tasks[0].get_end_to_end_deadline()
        
        if cp_tot_cost < e2ed:
            # low CCR, high parallelisation
            if (ratio_ccr < SimParams.CLSTR_TILE_PARAM_BGROUP_CCR_RANGES_LOW):
                nhops_group_tiles = SimParams.CLSTR_TILE_PARAM_BGROUP_NGT_HOPS[0]
                nhops_group_parent = nhops_group_tiles + 1
            
            # med CCR, load-balance
            elif (ratio_ccr <= SimParams.CLSTR_TILE_PARAM_BGROUP_CCR_RANGES_MED[1]) and (ratio_ccr >= SimParams.CLSTR_TILE_PARAM_BGROUP_CCR_RANGES_MED[0]):
                nhops_group_tiles = SimParams.CLSTR_TILE_PARAM_BGROUP_NGT_HOPS[1]
                nhops_group_parent = nhops_group_tiles + 1
            
            # high CCR, maximum clusterisation
            elif (ratio_ccr > SimParams.CLSTR_TILE_PARAM_BGROUP_CCR_RANGES_HIGH):
                nhops_group_tiles = SimParams.CLSTR_TILE_PARAM_BGROUP_NGT_HOPS[2]
                nhops_group_parent = nhops_group_tiles + 1
                
            else:
                sys.exit("Error - _get_ccr_specific_nhops_bgroup_mapping : unknown ccr")
        
        
        # need to scatter tasks more
        else:
            # low CCR, high parallelisation
            if (ratio_ccr < SimParams.CLSTR_TILE_PARAM_BGROUP_CCR_RANGES_LOW):
                nhops_group_tiles = SimParams.CLSTR_TILE_PARAM_BGROUP_NGT_HOPS[0]+2
                nhops_group_parent = nhops_group_tiles + 1
            
            # med CCR, load-balance
            elif (ratio_ccr <= SimParams.CLSTR_TILE_PARAM_BGROUP_CCR_RANGES_MED[1]) and (ratio_ccr >= SimParams.CLSTR_TILE_PARAM_BGROUP_CCR_RANGES_MED[0]):
                nhops_group_tiles = SimParams.CLSTR_TILE_PARAM_BGROUP_NGT_HOPS[1]+2
                nhops_group_parent = nhops_group_tiles + 1
            
            # high CCR, maximum clusterisation
            elif (ratio_ccr > SimParams.CLSTR_TILE_PARAM_BGROUP_CCR_RANGES_HIGH):
                nhops_group_tiles = SimParams.CLSTR_TILE_PARAM_BGROUP_NGT_HOPS[2]+2
                nhops_group_parent = nhops_group_tiles + 1
                
            else:
                sys.exit("Error - _get_ccr_specific_nhops_bgroup_mapping : unknown ccr")
            
        ############
        # track ccr
        ############
        vid_resolution =  "%dx%d" % (gop_tasks[0].get_frame_h(),gop_tasks[0].get_frame_w())
        entry = {
                 'n_n': len(gop_tasks), 'n_e': gop_tasks[0].get_adaptiveGoP_Obj().getTotalEdges(),
                 'Iwcc': Iwcc, 
                 'Pwcc': Pwcc, 
                 'Bwcc': Bwcc, 
                 'max_bl': flow_basic_latency,
                 'gopseq': gop_tasks[0].get_gopstructure(),  
                 'vid_genre' : gop_tasks[0].get_video_genre(),                  
                 'tot_e_c': total_edges_cost, 'tot_n_c': total_nodes_cost,
                 'ccr': ratio_ccr,
                 'nhops': [nhops_group_parent, nhops_group_tiles],
                 'e2ed_test': 1 if (cp_tot_cost < e2ed) else 0
                 }
        
        if vid_resolution not in self.track_ccr_level:
            self.track_ccr_level[vid_resolution] = [entry]
        else:
            self.track_ccr_level[vid_resolution].append(entry)
        
        return (nhops_group_parent, nhops_group_tiles)
    
    
    
    #####################################################
    # Helpers: get critical path
    #####################################################
    def _get_critical_path(self, cp_type, adaptive_gop_obj):
        if cp_type == 0:                
            cp_fix_list = adaptive_gop_obj.getCriticalPath_v2() # real critical path
        elif cp_type == 1: # fake CP - metric : fanout
            cp_fix_list = adaptive_gop_obj.getPseudoCriticalPath_v1() # pseudo CP (fanout)
        elif cp_type == 2: # fake CP - metric : I+P+(generalised B) together
            cp_fix_list = adaptive_gop_obj.getPseudoCriticalPath_v2(include_gen_b=False) # pseudo CP
        else:
            sys.exit("_get_critical_path:: Error - not implemented")
        
        return cp_fix_list
    
    
    #####################################################
    # Helpers: get info from volative task mapping table
    #####################################################
    
    def _get_node_lowest_util_viavmtbl(self, copy_vmtbl,free_nodes_list, use_avgcc=False,
                                       running_tile_mappings=None,
                                       number_of_total_tiles=None):
                
        # check if we have to clean the target nodes
        # do should not allow all tiles to be on one node
        if (running_tile_mappings!=None) and (number_of_total_tiles!=None):
            free_nodes_list = self._remove_overcrowded_target_nodes(free_nodes_list, running_tile_mappings, number_of_total_tiles)
                
        node_util = {}
        for nid in free_nodes_list:            
            if nid in copy_vmtbl:
                if use_avgcc==False:          # use avgcc or wcc ?      
                    sum_cc = np.sum([t['wcc'] for t in copy_vmtbl[nid]])
                else:
                    sum_cc = np.sum([self._get_avgcc_from_rmmonitoring(t) for t in copy_vmtbl[nid]])
                node_util[nid] = sum_cc
            else:
                node_util[nid] = 0.0
        
        if len(node_util.keys())>0:
            min_util = np.min(node_util.values())
            min_util_nids = [k for k,v in node_util.iteritems() if v==min_util]
            
#             # get one with least mapped tasks
#             if len(min_util_nids)>1:
#                 node_tasks = {}
#                 for nid in min_util_nids:
#                     if nid in copy_vmtbl:
#                         node_tasks[nid] = len(copy_vmtbl[nid])
#                     else:
#                         node_tasks[nid] = 0
#                 
#                 min_nt =  np.min(node_tasks.values())
#                 min_nt_nid = [k for k,v in node_tasks.iteritems() if v==min_nt]
#                 
#                 result_nid = min_nt_nid[0]
#             else:
#                 result_nid = min_util_nids[0]

            result_nid = min_util_nids[0]
            
        else:
            #min_util_nid = 0
            sys.exit("Error - _get_node_lowest_util_viavmtbl: len(node_util.keys())>0 == FALSE")
        
        return result_nid 
    
    
    
    
    def _get_nodes_sorted_LU_order(self, copy_vmtbl, nodes_list_nids, use_avgcc=False):
        node_util_tuple = []
        for nid in nodes_list_nids:
            if nid in copy_vmtbl:
                if use_avgcc==False:          # use avgcc or wcc ?      
                    sum_cc = np.sum([t['wcc'] for t in copy_vmtbl[nid]])
                else:
                    sum_cc = np.sum([self._get_avgcc_from_rmmonitoring(t) for t in copy_vmtbl[nid]])
                node_util_tuple.append((nid,sum_cc))
            else:
                node_util_tuple.append((nid,0.0))
        
        sorted_nid_by_sumcc = sorted(node_util_tuple, key=lambda nid: nid[1])        
        sorted_nid_list = [nid[0] for nid in sorted_nid_by_sumcc]
        
        return sorted_nid_list
    
    
    
    # try to get avg from RM, if no data, then get wcc
    def _get_avgcc_from_rmmonitoring(self, t):        
        t_strm_key = t['strm_key']
        t_ftype = t['ftype']        
        if t_strm_key in self.RM_instance.completed_task_monitoring_info:
            if t_ftype in self.RM_instance.completed_task_monitoring_info[t_strm_key]:
                avg_cc = np.mean(self.RM_instance.completed_task_monitoring_info[t_strm_key][t_ftype])
                return avg_cc
            else:
                return t['wcc']
        else:
            return t['wcc']
    
        
    def _get_node_lowest_mapped_viavmtbl(self, copy_vmtbl,free_nodes_list):        
        node_tm = {}
        for node in free_nodes_list:
            nid = node.get_id()
            if nid in copy_vmtbl:
                num_t = len(copy_vmtbl[nid])
                node_tm[nid] = num_t
            else:
                node_tm[nid] = 0
        
        if len(node_tm.keys())>0:
            min_tm = np.min(node_tm.values())
            min_tm_nid = [k for k,v in node_tm.iteritems() if v==min_tm][0]
        else:
            min_tm_nid = 0
        
        return min_tm_nid 
    
    
    def _get_node_wcremcumslack(self, node_taskslist, use_avgcc, debug=False):
        node_level_cumslack=[] 
        temp_node_taskslist = copy.deepcopy(node_taskslist)    
           
        for each_task in node_taskslist:
            if (use_avgcc==False):    
                cummulative_wccc_high_pri_tasks = np.sum([t['wcc'] for t in temp_node_taskslist if t['pri']>=each_task['pri']])
                task_rem_slack =  each_task['deadline'] - (each_task['wcc'] + cummulative_wccc_high_pri_tasks)
            else:
                cummulative_avgccc_high_pri_tasks = np.sum([self._get_avgcc_from_rmmonitoring(t) for t in temp_node_taskslist if t['pri']>=each_task['pri']])
                task_rem_slack =  each_task['deadline'] - (self._get_avgcc_from_rmmonitoring(each_task) + cummulative_avgccc_high_pri_tasks)
                        
            node_level_cumslack.append(task_rem_slack)        
       
        return (node_level_cumslack, np.sum(node_level_cumslack))
    
        
    def _get_node_with_max_wcrs(self, copy_vtmtbl, target_node_ids, 
                                copy_vmtblusagetbl=None, 
                                use_avgcc=False, selection_type='default',
                                running_tile_mappings = None,
                                number_of_total_tiles = None
                                ):
        node_level_cumslack = {}
        TEMP_LARGE_CUMSLACK = 100000
        
        selected_node_id = None
        assert (target_node_ids != None)
        
        # check if we have to clean the target nodes
        # do should not allow all tiles to be on one node
        if (running_tile_mappings!=None) and (number_of_total_tiles!=None):
            target_node_ids = self._remove_overcrowded_target_nodes(target_node_ids, running_tile_mappings, number_of_total_tiles)
                
        for each_node_id in target_node_ids:                        
            if each_node_id in copy_vtmtbl : each_node_tasklist = copy_vtmtbl[each_node_id]
            else: each_node_tasklist = []
            
            if len(each_node_tasklist)>0:
                (node_level_cumslack_pertask, sum_node_level_cumslack) = self._get_node_wcremcumslack(each_node_tasklist,use_avgcc)
                node_level_cumslack[each_node_id] = sum_node_level_cumslack                
            else:
                node_level_cumslack[each_node_id] = TEMP_LARGE_CUMSLACK
        
        # get max node with cumslack
        if len(node_level_cumslack.keys())>0:
            max_val = np.max(node_level_cumslack.values())
            possible_nodes_withmax_cumslack = [k for k,v in node_level_cumslack.iteritems() if v==max_val]
                        
            if selection_type=='default':
                selected_node_id = possible_nodes_withmax_cumslack[0]
            elif selection_type=='random':            
                selected_node_id = random.choice(possible_nodes_withmax_cumslack)
            elif selection_type=='node_usage_min':
                if copy_vmtblusagetbl == None: sys.exit('Error: missing copy_vmtblusagetbl')
                selected_node_id = self._get_least_used_node_from_vmtblusagetable(copy_vmtblusagetbl, 
                                                                                  node_id_list=possible_nodes_withmax_cumslack)
                            
        else:
            if selection_type == 'default':
                selected_node_id = 0
            elif selection_type == 'random':
                assert(len(target_node_ids)>0)
                selected_node_id = random.choice(target_node_ids)
            elif selection_type == 'node_usage_min':
                if copy_vmtblusagetbl == None: sys.exit('Error: missing copy_vmtblusagetbl')
                selected_node_id = self._get_least_used_node_from_vmtblusagetable(copy_vmtblusagetbl, 
                                                                                  node_id_list=target_node_ids)                
        
        assert(selected_node_id != None)
        
        return selected_node_id            
    
    
    
    
    
    # search for the node with gives the max wcrs (cumulative)
    # if the cum_wcrs is negative (i.e. no remaining slack on the node), then select via LU    
    def _get_node_with_max_wcrs_default_LU(self, copy_vtmtbl, target_node_ids, 
                                copy_vmtblusagetbl=None, 
                                use_avgcc=False, selection_type='default',
                                running_tile_mappings = None,
                                number_of_total_tiles = None
                                ):
        node_level_cumslack = {}
        TEMP_LARGE_CUMSLACK = 100000
        
        selected_node_id = None
        assert (target_node_ids != None)
        
        # check if we have to clean the target nodes
        # do should not allow all tiles to be on one node
        if (running_tile_mappings!=None) and (number_of_total_tiles!=None):
            target_node_ids = self._remove_overcrowded_target_nodes(target_node_ids, running_tile_mappings, number_of_total_tiles)
                
        for each_node_id in target_node_ids:                        
            if each_node_id in copy_vtmtbl : each_node_tasklist = copy_vtmtbl[each_node_id]
            else: each_node_tasklist = []
            
            if len(each_node_tasklist)>0:
                (node_level_cumslack_pertask, sum_node_level_cumslack) = self._get_node_wcremcumslack(each_node_tasklist,use_avgcc)                
                if sum_node_level_cumslack > 0:
                    node_level_cumslack[each_node_id] = sum_node_level_cumslack
                else:
                    pass # this node has no positive cum_wcrs                
            else: # this is when the node has no tasks mapped at the moment
                node_level_cumslack[each_node_id] = TEMP_LARGE_CUMSLACK
        
        # get max node with cumslack
        if len(node_level_cumslack.keys())>0:
            max_val = np.max(node_level_cumslack.values())
            possible_nodes_withmax_cumslack = [k for k,v in node_level_cumslack.iteritems() if v==max_val]
                        
            if selection_type=='default':
                selected_node_id = possible_nodes_withmax_cumslack[0]
            elif selection_type=='random':            
                selected_node_id = random.choice(possible_nodes_withmax_cumslack)
            elif selection_type=='node_usage_min':
                if copy_vmtblusagetbl == None: sys.exit('Error: missing copy_vmtblusagetbl')
                selected_node_id = self._get_least_used_node_from_vmtblusagetable(copy_vmtblusagetbl, 
                                                                                  node_id_list=possible_nodes_withmax_cumslack)
        
        # none of the nodes have remaining cumslack                
        else:
            selected_node_id = self._get_node_lowest_util_viavmtbl(copy_vtmtbl,target_node_ids, use_avgcc=use_avgcc,
                                                                   running_tile_mappings=running_tile_mappings,
                                                                   number_of_total_tiles=number_of_total_tiles)            
        
        assert(selected_node_id != None)
        
        return selected_node_id            
    
    
    
    # get node which gives the lowest blocking to other low-pri tasks
    # 
    def _get_node_with_min_lowpriblocking(self, copy_vtmtbl, target_node_ids, target_task_pri,
                                copy_vmtblusagetbl=None, 
                                use_avgcc=False, selection_type='default',
                                running_tile_mappings = None,
                                number_of_total_tiles = None):
        node_level_num_lp_tasks = {}
        
        selected_node_id = None
        assert (target_node_ids != None)
        
        if len(target_node_ids) == 1:
            return target_node_ids[0]
        
        # check if we have to clean the target nodes
        # do should not allow all tiles to be on one node
        if (running_tile_mappings!=None) and (number_of_total_tiles!=None):
            target_node_ids = self._remove_overcrowded_target_nodes(target_node_ids, running_tile_mappings, number_of_total_tiles)
                
        for each_node_id in target_node_ids:                        
            if each_node_id in copy_vtmtbl : each_node_tasklist = copy_vtmtbl[each_node_id]
            else: each_node_tasklist = []
            
            if len(each_node_tasklist)>0:
                num_lp_tasks = len([t for t in each_node_tasklist if t['pri']<=target_task_pri]) # less than OR equal to
                #util =  np.sum([t['wcc'] for t in each_node_tasklist if t['pri']<target_task_pri])                
                node_level_num_lp_tasks[each_node_id] = num_lp_tasks           
            else: # this is when the node has no tasks mapped at the moment
                node_level_num_lp_tasks[each_node_id] = -1
        
        # sort nodes 2 criteria : num_lptasks, util    
        #sorted_nodes = sorted(node_level_num_lp_tasks, key=itemgetter('nlp', 'util')) 
        #selected_node_id = sorted_nodes[0]
                
        min_val = np.min(node_level_num_lp_tasks.values())
        possible_nodes_withmin = [k for k,v in node_level_num_lp_tasks.iteritems() if v==min_val]
         
        if selection_type=='default':
            selected_node_id = possible_nodes_withmin[0]
        elif selection_type=='random':            
            selected_node_id = random.choice(possible_nodes_withmin)
         
        elif selection_type=='least_util':
            selected_node_id = self._get_node_lowest_util_viavmtbl(copy_vtmtbl, possible_nodes_withmin, use_avgcc=use_avgcc)                
         
        elif selection_type=='node_usage_min':                
            if copy_vmtblusagetbl == None: sys.exit('Error: missing copy_vmtblusagetbl')                
            selected_node_id = self._get_least_used_node_from_vmtblusagetable(copy_vmtblusagetbl, 
                                                                              node_id_list=possible_nodes_withmin)
        elif selection_type=='node_usage_max':                
            if copy_vmtblusagetbl == None: sys.exit('Error: missing copy_vmtblusagetbl')                
            selected_node_id = self._get_most_used_node_from_vmtblusagetable(copy_vmtblusagetbl, 
                                                                              node_id_list=possible_nodes_withmin)
         
        else:
            sys.exit('Error: _get_node_with_min_lowpriblocking : invalid selection_type')
            
        assert(selected_node_id != None)        
        return selected_node_id           
        
    
    def _get_node_min_balanced_blocking(self, copy_vtmtbl, target_node_ids, target_task_pri, target_task_wcc,
                                copy_vmtblusagetbl=None, 
                                use_avgcc=False, selection_type='default',
                                running_tile_mappings = None,
                                number_of_total_tiles = None):
        
        node_level_impact_factor = {}        
        selected_node_id = None
        assert (target_node_ids != None)
                
        if len(target_node_ids) == 1:
            return target_node_ids[0]
        
        # check if we have to clean the target nodes
        # do should not allow all tiles to be on one node
        if (running_tile_mappings!=None) and (number_of_total_tiles!=None):
            target_node_ids = self._remove_overcrowded_target_nodes(target_node_ids, running_tile_mappings, number_of_total_tiles)
        
        for each_node_id in target_node_ids:                        
            if each_node_id in copy_vtmtbl : each_node_tasklist = copy_vtmtbl[each_node_id]
            else: each_node_tasklist = []
            
            if len(each_node_tasklist)>0:                                
                impact_self = np.sum([t['wcc'] for t in each_node_tasklist if t['pri']>target_task_pri])
                impact_others = len([t['wcc'] for t in each_node_tasklist if t['pri']<target_task_pri])
                node_level_impact_factor[each_node_id] = {
                                                          "Imp_self" : impact_self,
                                                          "Imp_others" : impact_others,
                                                          "norm_Imp_others" : None,
                                                          "norm_Imp_self" : None,
                                                          "final_impact_score" : None,
                                                          }
                
            else: # this is when the node has no tasks mapped at the moment
                return each_node_id
        
        # normalise the impact values
        all_vals_imp_self = [v["Imp_self"] for v in node_level_impact_factor.values()] 
        all_vals_imp_others = [v["Imp_others"] for v in node_level_impact_factor.values()]
                                
        #mean_imp_self = np.min(all_vals_imp_self)
        #mean_imp_others = np.min(all_vals_imp_others)        
        #std_imp_self = np.min(all_vals_imp_self)
        #std_imp_others = np.min(all_vals_imp_others)
        
        # normalise self
        min_imp_self = np.min(all_vals_imp_self)
        max_imp_self = np.max(all_vals_imp_self)
        min_imp_others = np.min(all_vals_imp_others)        
        max_imp_others = np.max(all_vals_imp_others)
        for each_nid, impact in node_level_impact_factor.iteritems():
            node_level_impact_factor[each_nid]["norm_Imp_self"] =  self._normalise_val_minmax(impact['Imp_self'], 
                                                                                              min_imp_self, max_imp_self)        
        # normalise others
        for each_nid, impact in node_level_impact_factor.iteritems():
            node_level_impact_factor[each_nid]["norm_Imp_others"] =  self._normalise_val_minmax(impact['Imp_others'], 
                                                                                                min_imp_others, max_imp_others)
        
        # assign final impact score
        for each_nid, impact in node_level_impact_factor.iteritems():
            node_level_impact_factor[each_nid]["final_impact_score"] = impact["norm_Imp_self"] + impact["norm_Imp_others"]
        
        # select node with min final impact score
        min_imp_score = np.min([v["final_impact_score"] for k,v in node_level_impact_factor.iteritems()])
        possible_nodes_withmin = [k for k,v in node_level_impact_factor.iteritems() if v["final_impact_score"] == min_imp_score]
        
        if selection_type=='default':
            selected_node_id = possible_nodes_withmin[0]
        elif selection_type=='random':            
            selected_node_id = random.choice(possible_nodes_withmin)
         
        elif selection_type=='least_util':
            selected_node_id = self._get_node_lowest_util_viavmtbl(copy_vtmtbl, possible_nodes_withmin, use_avgcc=use_avgcc)                
         
        elif selection_type=='node_usage_min':                
            if copy_vmtblusagetbl == None: sys.exit('_get_node_min_balanced_blocking: Error: missing copy_vmtblusagetbl')                
            selected_node_id = self._get_least_used_node_from_vmtblusagetable(copy_vmtblusagetbl, 
                                                                              node_id_list=possible_nodes_withmin)
        elif selection_type=='node_usage_max':                
            if copy_vmtblusagetbl == None: sys.exit('_get_node_min_balanced_blocking: Error: missing copy_vmtblusagetbl')                
            selected_node_id = self._get_most_used_node_from_vmtblusagetable(copy_vmtblusagetbl, 
                                                                              node_id_list=possible_nodes_withmin)
        
        
        return selected_node_id
        
    
    
    def _normalise_val_minmax(self, x, x_min, x_max):
        if x_min == x_max : return 1.0
        else:
            x_norm = (float(x) - float(x_min))/(float(x_max) - float(x_min))
            return x_norm
    
    def _normalise_val_zscore(self, x, x_mean, x_std):
        z = (float(x) - float(x_mean))/(float(x_std))
        return z
    
        
    # get node which gives the lowest blocking to other low-pri tasks
    def _get_nodes_sorted_lowpriblockingorder(self, copy_vtmtbl, target_node_ids, target_task_pri,
                                            copy_vmtblusagetbl=None, 
                                            use_avgcc=False,
                                            running_tile_mappings = None,
                                            number_of_total_tiles = None):
        node_level_num_lp_tasks = []
        
        #selected_node_id = None
        assert (target_node_ids != None)
        
        if len(target_node_ids) == 1:
            return target_node_ids[0]
        
        # check if we have to clean the target nodes
        # do should not allow all tiles to be on one node
        if (running_tile_mappings!=None) and (number_of_total_tiles!=None):
            target_node_ids = self._remove_overcrowded_target_nodes(target_node_ids, running_tile_mappings, number_of_total_tiles)
                
        for each_node_id in target_node_ids:                        
            if each_node_id in copy_vtmtbl : each_node_tasklist = copy_vtmtbl[each_node_id]
            else: each_node_tasklist = []
            
            if len(each_node_tasklist)>0:
                num_lp_tasks = len([t for t in each_node_tasklist if t['pri']<target_task_pri])
                #util_all_tasks = np.sum([t['wcc'] for t in each_node_tasklist])                
                node_level_num_lp_tasks.append((each_node_id, num_lp_tasks, -1))
                               
            else: # this is when the node has no tasks mapped at the moment
                node_level_num_lp_tasks.append((each_node_id, -1, -1))
        
        # sort according to two criteria : {num_lp_tasks, util}
        sorted_node_level_num_lp_tasks = sorted(node_level_num_lp_tasks, key=itemgetter(1))
        
        result_sorted_nids = [n[0] for n in sorted_node_level_num_lp_tasks]
                
        return result_sorted_nids            
    
    
    
    # no node should be given more than 30% of the tiles
    def _remove_overcrowded_target_nodes(self, target_node_ids, curr_tile_mappings, n_total_tiles):
        
        # calc mapping threshold
        if len(target_node_ids) == 0:
            sys.exit("Error: _remove_overcrowded_target_nodes : target_node_ids is zero")
        elif len(target_node_ids) == 1:
            return target_node_ids
        elif len(target_node_ids) == 2:
            MAPPING_THRESHOLD = 0.51
        elif len(target_node_ids) == 3:
            MAPPING_THRESHOLD = 0.34
        elif len(target_node_ids) > 3:
            MAPPING_THRESHOLD = 0.3            
            
        # build freq table
        node_tile_freq = {}        
        for each_tile_id, node_id in curr_tile_mappings.iteritems():
            if node_id in node_tile_freq:                
                node_tile_freq[node_id] += 1
            else:
                node_tile_freq[node_id] = 0
        invalid_nodes_list=[]
        for nid,freq in node_tile_freq.iteritems():
            if (float(freq)/float(n_total_tiles))>=MAPPING_THRESHOLD:
                invalid_nodes_list.append(nid)
        
        new_target_nodeids_list = list(set(target_node_ids) - set(invalid_nodes_list))
        
        assert(len(new_target_nodeids_list)>0), ", %d, %d"%(len(target_node_ids), len(invalid_nodes_list))
        
        return new_target_nodeids_list
                
    
    def _get_all_nodes_cum_wcrs(self, copy_vtmtbl):   
        node_level_cumslack={}     
        for each_node_id, each_node_tasklist in copy_vtmtbl.iteritems():
            node_level_cumslack[each_node_id] = self._get_node_wcremcumslack(each_node_tasklist,False)[1]
            
    
    def _get_least_used_node_from_vmtblusagetable(self, copy_vmtblusagetbl, node_id_list=None, random_select=True):
        
        if node_id_list==None:
            node_id_list = range(SimParams.NOC_H*SimParams.NOC_W)        
        
        min_usage = np.min([copy_vmtblusagetbl[nid] for nid in node_id_list])
        min_usage_nodes = [nid for nid in node_id_list if copy_vmtblusagetbl[nid]==min_usage]
        
        if (random_select == True):
            selected_nid = random.choice(min_usage_nodes)
        else:
            selected_nid = min_usage_nodes[0]
                
        return selected_nid
    
    
    def _get_most_used_node_from_vmtblusagetable(self, copy_vmtblusagetbl, node_id_list=None, random_select=True):
        
        if node_id_list==None:
            node_id_list = range(SimParams.NOC_H*SimParams.NOC_W)        
        
        max_usage = np.max([copy_vmtblusagetbl[nid] for nid in node_id_list])
        max_usage_nodes = [nid for nid in node_id_list if copy_vmtblusagetbl[nid]==max_usage]
        
        if (random_select == True):
            selected_nid = random.choice(max_usage_nodes)
        else:
            selected_nid = max_usage_nodes[0]
                
        return selected_nid
    
    
   
    
    # helper function used to create a temp entry to the volatile task mapping table (local copy)
    #### IMPORTANT : if you add any entries here - you have to update the SchedulingAndMapping functions #####   
    def _get_vtmtbl_targettiletask_entry(self, target_task, target_node_id, target_task_pri):
        entry = {
            'task_id' : target_task.get_id(), 
            'node_id' : target_node_id,
            'release_time': self.env.now,
            'wcc' : target_task.get_worstCaseComputationCost(),
            'status' : -1,
            'pri': target_task_pri,
            'deadline' : target_task.get_relative_deadline(),
            'deps_completed' : [],
            'ftype' : target_task.get_frameType(),
            'strm_key' : "%d_%d" % (target_task.get_wfid(), target_task.get_video_stream_id())            
        }
        
        return entry
        
    def _get_deepcopy_volatiletaskmappingtable(self):        
        if SimParams.RESOURCEMANAGER_USE_VOLATILE_TMTBL == False:
            sys.exit("Error: _get_deepcopy_volatiletaskmappingtable::Error - SimParams.RESOURCEMANAGER_USE_VOLATILE_TMTBL == False")
                    
        temp_vtmtbl = dict(self.RM_instance.get_volatile_task_mapping_table())
        new_vtmtbl = {}      
        for k,v in temp_vtmtbl['runtime_task_mapping'].iteritems():
            new_vtmtbl[k] = copy.deepcopy(v)
        return new_vtmtbl
    
    
    def _get_deepcopy_nodeusage_volatiletaskmappingtable(self):
        if SimParams.RESOURCEMANAGER_USE_VOLATILE_TMTBL == False:
            sys.exit("Error: _get_nodeusage_from_volatiletaskmappingtable::Error - SimParams.RESOURCEMANAGER_USE_VOLATILE_TMTBL == False")
        
        temp_vtmtbl = dict(self.RM_instance.get_volatile_task_mapping_table())
        node_usage = {}
        for k,v in temp_vtmtbl['node_usage_field'].iteritems():
            node_usage[k] = copy.deepcopy(v)            
        return node_usage 
    
    
    
    #####################################################
    # Helpers: slack calculation helpers
    #####################################################
    
    def _get_task_to_node_packing_results(self, target_task, node_id, tasks_mapped_on_node):        
        ########
        # if this task is mapped to this node, how much delayed will it get ?
        # and with this delay, will it still meet it's subtask deadline ?
        ########        
        # the slack calculation does not take into account communication
        target_task_estimated_slack =  target_task.getEstimatedSlack_EQF()
        #print target_task_estimated_slack
        
        # amount of blocking (worst-case)
        higher_pri_tasks = self._get_tasks_with_higher_priority(tasks_mapped_on_node, target_task, ignore_own_vidstrm_tasks=True)
        cummulative_wccc_high_pri_tasks = self._get_estimated_worstcase_blocking(higher_pri_tasks)
        
        estimated_self_remaining_slack = (target_task_estimated_slack - cummulative_wccc_high_pri_tasks)
        self_okay = True if (estimated_self_remaining_slack > 0.0) else False
        
        ########
        # if this task is mapped to this node, how much blocking will it cause to Other tasks ?        
        ########        
        lower_pri_tasks = self._get_tasks_with_lower_priority(tasks_mapped_on_node, target_task, ignore_own_vidstrm_tasks=True)
        estimated_others_remaining_slack = []
        new_list_with_target_task_inserted = list(tasks_mapped_on_node)
        new_list_with_target_task_inserted.append(target_task)
        
        for each_task in lower_pri_tasks:
            higher_pri_tasks = self._get_tasks_with_higher_priority(new_list_with_target_task_inserted, each_task, ignore_own_vidstrm_tasks=True)
            cummulative_wccc_high_pri_tasks = self._get_estimated_worstcase_blocking(higher_pri_tasks)
            est_remaining_slack = each_task.getEstimatedSlack_EQF()-cummulative_wccc_high_pri_tasks
            estimated_others_remaining_slack.append(est_remaining_slack)
            
        result = {
                  'estimated_wc_remaining_slack__self' : estimated_self_remaining_slack,
                  'estimated_wc_remaining_slack__others' :  estimated_others_remaining_slack,
                  '__self_okay_bool' : self_okay,
                  '__others_okay_bool' : all(est_slack >0.0 for est_slack in estimated_others_remaining_slack),
                  }        
        return result
    
    def _get_estimated_worstcase_blocking(self, high_pri_tasklist):
        est_cum_wc_bl = 0.0
        for each_high_pri_task in high_pri_tasklist:
            est_cum_wc_bl += each_high_pri_task.get_worstCaseComputationCost()        
        return  est_cum_wc_bl
    
    #####################################################
    # Helpers: update mapping tables
    #####################################################
    def _map_to_vidstrm_tile_mappingtbl_overwrite(self, frames_mapping, pri_assignment, wf_id, strm_id):  
        if wf_id not in self.RM_instance.vidstream_frames_mapping_table:
            self.RM_instance.vidstream_frames_mapping_table[wf_id] = {}        
        if strm_id not in self.RM_instance.vidstream_frames_mapping_table[wf_id]:
            self.RM_instance.vidstream_frames_mapping_table[wf_id][strm_id] = {}            
        # apply new mapping
        self.RM_instance.vidstream_frames_mapping_table[wf_id][strm_id] = {}
        self.RM_instance.vidstream_frames_mapping_table[wf_id][strm_id]['frames_mapping'] = frames_mapping
        self.RM_instance.vidstream_frames_mapping_table[wf_id][strm_id]['pri_ass'] = pri_assignment
    
    
    def _map_to_mmc_mappingtbl(self, tile_mapping, sorted_tile_tasks, copy_vnoctt):
        result = self.mmc_selector.map_to_mmc_mappingtbl(tile_mapping, sorted_tile_tasks, copy_vnoctt) # routed to different class method
        return result
                
   
    #####################################################
    # Helpers: get properties of frame task
    #####################################################            
    def _get_wcc_of_frame(self, frame_ix, strm_specs, frame_type=None):
        if(frame_type==None):
            frame_type = strm_specs['gop_struct'][frame_ix]        
        if (frame_type == "I"): wcc = strm_specs['wcc_I']
        elif (frame_type == "P"): wcc = strm_specs['wcc_P']
        elif (frame_type == "B"): wcc = strm_specs['wcc_B']
        else: sys.exit("Error: TaskMappingSchemesImpl:: _get_wcc_of_frame:: Error")        
        return wcc
    
    def _get_avgcc_of_frame(self, frame_ix, strm_specs):
        frame_type = strm_specs['gop_struct'][frame_ix]        
        if (frame_type == "I"): avgcc = strm_specs['avgcc_I']
        elif (frame_type == "P"): avgcc = strm_specs['avgcc_P']
        elif (frame_type == "B"): avgcc = strm_specs['avgcc_B']
        else: sys.exit("Error: TaskMappingSchemesImpl:: _get_wcc_of_frame:: Error")        
        return avgcc
    
    def _get_empty_frame_mappings_dict(self, strm_specs):
        d = {}
        for i in xrange(len(strm_specs['gop_struct'])): d[i] = None        
        return d
    
    #####################################################
    # Helpers: task splitting
    #####################################################    
    def _get_tile_task_nx_label(self, tile_task):
        task_tile_id = tile_task.get_hevc_tile_id()
        task_gfrix = tile_task.get_frameIXinGOP()
        task_type = tile_task.get_frameType()
        return "%s%s_%s" %(task_type, task_gfrix, task_tile_id)
         
    
    
    def _get_sorted_tile_tasks(self, strm_specs, frame_priorities):
        
        # split all the tasks in the GOP into tiles
        # this version of the mapping produces more tasks as well as the mapping/pri-ass
        gop_tasks = strm_specs['gop_tasks']
        sorted_gop_tasks = self._get_sorted_goptasks_dep_order(gop_tasks)
        all_sorted_hevc_tile_tasks = OrderedDict()
        frame_to_tile_task_grouping = {}            
        for each_task in sorted_gop_tasks:
            hevc_tile_tasks_per_frame = self._get_tiles_of_tasks(each_task, 
                                                                 strm_specs, 
                                                                 each_task.get_frameIXinGOP(), 
                                                                 frame_priorities)
            all_sorted_hevc_tile_tasks.update(hevc_tile_tasks_per_frame)
            
            # construct a original frame to split tile task mapping      
            frame_to_tile_task_grouping[each_task.get_id()] = [tt.get_id() for tt in hevc_tile_tasks_per_frame.values()]
        
        # construct gop tile partitions
        gop_tile_partitions = { 
                               'orig_task_ids' : [t.get_id() for t in sorted_gop_tasks],
                               'new_tasks' : frame_to_tile_task_grouping
                               }        
        # set extra task properties of the generated tiles
        self._set_extra_properties_of_tile_tasks(sorted_gop_tasks, all_sorted_hevc_tile_tasks, gop_tile_partitions)
        
        return all_sorted_hevc_tile_tasks
    
    
    
    def _set_extra_properties_of_tile_tasks(self, sorted_gop_tasks, all_sorted_hevc_tile_tasks, gop_tile_partitions):        
        ## setting extra properties of the tile tasks ##
        # at this point we got all the task splittings, so we calculate the dependencies to/from each tile from each parent tile
        all_sorted_hevc_tile_tasks = self._pop_new_tiletasks_data_dependencies(sorted_gop_tasks, 
                                                                              all_sorted_hevc_tile_tasks, 
                                                                              gop_tile_partitions['new_tasks'])
        
        all_sorted_hevc_tile_tasks = self._pop_new_tiletasks_dependencies(all_sorted_hevc_tile_tasks, 
                                                                          gop_tile_partitions['new_tasks'])
        
        
        theoretical_number_of_tile_tasks = sorted_gop_tasks[0].getNumSubTasksTiles() * len(sorted_gop_tasks)
        assert(theoretical_number_of_tile_tasks == len(all_sorted_hevc_tile_tasks.values())), \
        "TaskTileMappingAndPriAssCombinedSchemesImpl: Error - tile splitting incorrect"
    
    
    #get all tile-level tasks for the given target task 
    def _get_tiles_of_tasks(self, target_task, strm_specs, fr_ix, fr_pri_list):
        ':type hevc_frame_task: HEVCFrameTask'
        gop_tasks = strm_specs['gop_tasks']
        hevc_frame_task = gop_tasks[fr_ix]
        
        number_of_tiles = hevc_frame_task.getNumSubTasksTiles()        
        
        assert ((number_of_tiles != 0) and (number_of_tiles!=None))
        
        #print "_get_tiles_of_tasks :: number_of_tiles :", number_of_tiles
        
        tile_frame_block_partitions = hevc_frame_task.getTileLevel_block_partitions()
        
        new_tile_tasks = OrderedDict()
        #print hevc_frame_task        
        for tile_ix in xrange(number_of_tiles):
            #print "tile_ix = ", tile_ix
            tile_tid = str(hevc_frame_task.get_id()) + "_" + str(tile_ix)
#             num_ctus_in_tile = np.sum([len(s['ctus'].keys()) 
#                                        for s_ix, s in tile_frame_block_partitions[tile_ix].iteritems()]) 
            
            num_ctus_in_tile = hevc_frame_task.getNumCTUinTile(tile_ix)            
            (tile_w, tile_h) = hevc_frame_task.getTileDimensions(num_ctus_in_tile)
            
            num_slices_in_tile = len(tile_frame_block_partitions[tile_ix].keys())
            hevc_tile_task = HEVCFrameTask(env = self.env,                                   
                                        id = tile_tid,
                                        frame_type = strm_specs['gop_struct'][fr_ix], 
                                        task_granularity = "tile",
                                        frame_ix_in_gop = fr_ix,  # need change ?         
                                        unique_gop_id = hevc_frame_task.get_unique_gop_id(),                         
                                        gop_struct = strm_specs['gop_struct'], # need change ?
                                        video_stream_id = strm_specs['vid_strm_id'],
                                        wf_id = strm_specs['wf_id'],
                                        frame_h = tile_h, frame_w = tile_w,
                                        frame_rate = hevc_frame_task.get_framerate(),
                                        priority = hevc_frame_task.get_priority(),
                                        num_slices_per_frame = -1,
                                        num_tiles_per_frame =  -1,
                                        interleaved_slice_types = None,
                                        num_ctu_per_slice=-1,
                                        adaptiveGoP_Obj=None,     
                                        load_data_from_file = False,
                                        construct_partitions = False,
                                        hevc_cc=0.0,     
                                        tile_parent_frame_task_id =  hevc_frame_task.get_id()                                 
                                        )
            # manually assign properties 
            tile_wccc = hevc_frame_task.getTileWCCC_viaFiarProportions(tile_h, tile_w, 
                                                                       hevc_frame_task.get_frame_h(),
                                                                       hevc_frame_task.get_frame_w(),
                                                                       hevc_frame_task.get_worstCaseComputationCost()
                                                                       )
            
            hevc_tile_task.set_worstCaseComputationCost(tile_wccc)           
            hevc_tile_task.set_worstCaseRemainingComputationCost(tile_wccc)
            hevc_tile_task.set_avgCaseComputationCost(self._get_avgcc_of_frame(fr_ix, strm_specs)/float(number_of_tiles))
            hevc_tile_task.set_scheduledDispatchTime(self.env.now)
            hevc_tile_task.set_isHeadVideoGop(hevc_frame_task.get_isHeadVideoGop())
            hevc_tile_task.set_isTailVideoGop(hevc_frame_task.get_isTailVideoGop())
            hevc_tile_task.set_priority(fr_pri_list[fr_ix])
            hevc_tile_task.set_period(hevc_frame_task.get_end_to_end_deadline())
            hevc_tile_task.set_dispatchTime(self.env.now)
            hevc_tile_task.set_wccIFrame(None)
            hevc_tile_task.set_wccPFrame(None)
            hevc_tile_task.set_wccBFrame(None)    
            hevc_tile_task.set_frame_block_partitions(tile_frame_block_partitions[tile_ix])
            hevc_tile_task.set_frame_tile_partitions(hevc_frame_task.get_frame_tile_partitions())
            mpeg_task_size = hevc_tile_task.getTileLevel_MpegTaskSize(hevc_frame_task.get_mpeg_tasksize(), 
                                                                      tile_w, tile_h,
                                                                      hevc_frame_task.get_frame_w(), hevc_frame_task.get_frame_h())
            hevc_tile_task.set_mpeg_tasksize(mpeg_task_size)
            tile_relD =  hevc_tile_task.getTileEstimatedRelativeDeadline_viaFairProportions(tile_h, tile_w, 
                                                                                            hevc_frame_task.get_frame_h(),
                                                                                            hevc_frame_task.get_frame_w(),
                                                                                            hevc_frame_task.getEstimatedRelativeDeadline_Div_x())
            
            hevc_tile_task.set_relative_deadline(tile_relD)
            hevc_tile_task.setTileInitialProcessingUnitRef(hevc_tile_task.get_frame_block_partitions()) # resets the current_processing_unit_ref
            
            hevc_tile_task.set_hevc_tile_id(tile_ix)
            
            # actual computation cost related
            cc = hevc_tile_task.calc_FrameComputationTime()
            hevc_tile_task.set_computationCost(cc)
            hevc_tile_task.set_remainingComputationCost(cc)
            hevc_tile_task.set_timeLeftTillCompletion(cc)
            
            # properties that are set later
            # - tile dependencies : data to children, data from parents
            # - mapped processing core
            tmp_empty_dict = {}
            hevc_tile_task.set_expected_data_from_parents({})
            hevc_tile_task.set_expected_data_to_children({})
            hevc_tile_task.set_processingCore(None)
            hevc_tile_task.set_dependencies(hevc_frame_task.get_dependencies())
            
            # add to structure
            new_tile_tasks[hevc_tile_task.get_id()]=hevc_tile_task
            
        return new_tile_tasks
    
    def _get_sorted_goptasks_dep_order(self, gop_tasks):
        sorted_ixs = gop_tasks[0].get_adaptiveGoP_Obj().getDecodingOrder()[0]
        sorted_gop_tasklist = []
        for ix in sorted_ixs:
            sorted_gop_tasklist.append(gop_tasks[ix])
        return sorted_gop_tasklist
 
    
    ## expensive - 4 nested loops !!
    def _pop_new_tiletasks_data_dependencies(self, sorted_orig_gop_tasks, all_hevc_tile_tasks_dict, gop_tile_partitions):        
        # loop through each task in original gop tasks
        for each_old_p_task in sorted_orig_gop_tasks:            
            # loop through each child task
            for each_old_c_task_id, each_old_c_data_vol in each_old_p_task.get_expected_data_to_children().iteritems():            
                num_p = gop_tile_partitions[each_old_p_task.get_id()] # new parents tiles
                num_c = gop_tile_partitions[each_old_c_task_id] # new children tiles
                
                # previous one to one edge has now been split into (num_p * num_c) edges
                total_edges = len(num_p) * len(num_c)
                                
                assert(total_edges <= each_old_c_data_vol), \
                "_pop_new_tiletasks_data_to_children:: data to children is very small.. %d, %d" %(total_edges, each_old_c_data_vol) 
                                
                # split total data volume amongst all the edges                
                partitioned_data_volume = self.constrained_sum_sample_pos(total_edges, each_old_c_data_vol)
                
                assert(len(partitioned_data_volume) == total_edges), "_get_new_tiletasks_data_to_children: Error - 1"
                
                # update the hevc tile task deps
                i=0
                for each_new_p_id in num_p:
                    for each_new_c_id in num_c:                        
                        ## update actual property in HEVC frame class
                        all_hevc_tile_tasks_dict[each_new_p_id].update_expected_data_to_children(each_new_c_id, partitioned_data_volume[i])
                        
                        ## update actual property in HEVC frame class
                        all_hevc_tile_tasks_dict[each_new_c_id].update_expected_data_from_parent(each_new_p_id, partitioned_data_volume[i])
                        i+=1
        
        return all_hevc_tile_tasks_dict
    
    def _pop_new_tiletasks_dependencies(self, all_hevc_tile_tasks_dict, gop_tile_partitions):
        for each_tile_task_id, each_tile_task in all_hevc_tile_tasks_dict.iteritems():
            old_deps = each_tile_task.get_dependencies()
            new_dep_tix=[]
            for tix in old_deps:
                new_dep_tix.extend(gop_tile_partitions[tix])            
            all_hevc_tile_tasks_dict[each_tile_task_id].set_dependencies(new_dep_tix)
            
        return all_hevc_tile_tasks_dict
            
            
             
    #####################################################
    # Helpers: flows
    #####################################################
    
    def _get_pseudo_flow(self, gop_uid, local_flw_id, src_node_id, dst_node_id, pri, rt, pl):        
        id = "g%d_f%d" % (gop_uid,local_flw_id)        
        route = self.RM_instance.interconnect.getRouteXY(src_node_id, dst_node_id)        
        priority = pri
        payload = pl
        basicLatency = self.RM_instance.interconnect.getRouteCostXY(src_node_id, dst_node_id, payload)
        release_time = rt # to find
        creation_time = release_time        
        endTime_wrt_BL = release_time + basicLatency
        newflow = NoCFlow(id,
                           None,
                           None,                           
                           None, # list of dst task ids
                           None, # list of dst task ixs
                           src_node_id, 
                           dst_node_id, 
                           route,
                           priority, 
                           None, 
                           basicLatency, 
                           payload,
                           endTime_wrt_BL,
                           type=FlowType.FLOWTYPE_MASTERSLAVESIGNALLING_TASKCOMPLETE, 
                           creation_time=creation_time                         
                           )        
        return newflow
            
            
            
            
            
            
        
        
        
        
        
        
        
        
    
    
        
