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
from libApplicationModel.MPEG2FrameTask import MPEG2FrameTask
from libNoCModel.NoCFlow import NoCFlow, FlowType
from libApplicationModel.HEVCFrameTask import HEVCFrameTask
from libApplicationModel.Task import TaskModel
import libApplicationModel.HEVCWorkloadParams as HEVCWLP
from MMC import MMC_SmartPortSelectionTypes

# once a stream has entered the system, the frames of the GoPs are mapped. 
# this mapping is fixed throughout the lifetime of the video stream
class MMCSelectionSchemesImpl:

    def __init__(self, env, RM_instance):  
        self.env = env
        self.RM_instance = RM_instance
        
        
        
    ######################################################################################
    ######################################################################################
    # Functions to do with MMC selection
    ######################################################################################
    ######################################################################################
    
    # take both distance and utilisation into account
    def getRandom_MMCPort(self, src_node_id, local_traffic_table=None):        
        selected_mmc_node_id = self.RM_instance.mmc.random_mmc_node_selection.next() # pregenerated to avoid having to call rand        
        return selected_mmc_node_id
    
    # default : assumes all nodes at edges has access to the MMC in that edge
    # heuristic : distance
    def getClosestMMCPort(self, src_node_id):  
        #print "getClosestMMCPort:: enter"         
        mmc_node_dist = {}         
        for each_nid in self.RM_instance.mmc.mmc_connected_node_ids:
            if each_nid not in mmc_node_dist:
                mmc_node_dist[each_nid] = len(self.RM_instance.interconnect.getPrecalcRouteXY(src_node_id, each_nid)) # task->MMC route
        
        # find closest node        
        selected_mmc_node_id = self._get_key_with_min_val_from_dict(mmc_node_dist)        
        return selected_mmc_node_id
    
    
    ##############################
    #### Slow implementations ####
    ##############################
    
    # take both distance and utilisation into account
    def getLUDistCombined_MMCPort(self, src_node_id, local_copy_vnoctt, local_traffic_table=None):
        #print "getLUDistCombined_MMCPort:: enter"                
        mmc_node_metric = {}
        max_route_dist = 0.0
        max_route_load = 0.0         
        for each_nid in self.RM_instance.mmc.mmc_connected_node_ids:
            if each_nid not in mmc_node_metric:
                route_to_mmc_node = self.RM_instance.interconnect.getPrecalcRouteXY(src_node_id, each_nid) # task->MMC route
                flows_in_route = self._get_flows_in_route_v3(route_to_mmc_node,
                                                             local_copy_vnoctt).values()
                #print [f.get_id() for f in flows_in_route]
                route_flow_cum_payload = np.sum([f.get_payload() for f in flows_in_route])
                distance = len(route_to_mmc_node)                                        
                mmc_node_metric[each_nid] = [route_flow_cum_payload, distance]
                
                if route_flow_cum_payload > max_route_load : max_route_load = route_flow_cum_payload
                if distance > max_route_dist : max_route_dist = distance                
        
        if max_route_load==0.0: max_route_load=1.0
        if max_route_dist==0.0: max_route_dist=1.0
        
        # normalise the measured metrics
        combined_metric_all_routes = {}
        for k,v in mmc_node_metric.iteritems():
            metric_1_load = float(v[0])/float(max_route_load)
            metric_2_load = float(v[1])/float(max_route_dist)
            combined_normalised_metric = metric_1_load + metric_2_load
            mmc_node_metric[k] = [metric_1_load, metric_2_load, combined_normalised_metric]
            combined_metric_all_routes[k] = combined_normalised_metric
        
        # find min util
        selected_mmc_node_id = self._get_key_with_min_val_from_dict(combined_metric_all_routes)
        return selected_mmc_node_id
        
    
    
    # path with min cumulative payload
    def getLUroute_MMCPort(self, src_node_id, local_copy_vnoctt, local_traffic_table=None):                
        #start_time = time.clock()
        #print "-------- new task ---------"
        mmc_node_metric = {}         
        for each_nid in self.RM_instance.mmc.mmc_connected_node_ids:
            if each_nid not in mmc_node_metric:
                route_to_mmc_node = self.RM_instance.interconnect.getPrecalcRouteXY(src_node_id, each_nid) # task->MMC route
                route_flow_cum_payload = self._get_route_total_flw_payload(route_to_mmc_node, local_copy_vnoctt)                        
                mmc_node_metric[each_nid] = route_flow_cum_payload
                
                #print route_to_mmc_node, route_flow_cum_payload
                
        
        # find min util
        selected_mmc_node_id = self._get_key_with_min_val_from_dict(mmc_node_metric)
        
        #end_time = time.clock()
        #print "time_spent = ", (end_time - start_time), ", selected_mmc_node_id =", selected_mmc_node_id
        
        return selected_mmc_node_id
        
    
    # path with min cumulative payload
    def getLMroute_MMCPort(self, src_node_id, local_copy_vnoctt, local_traffic_table=None):                
        mmc_node_metric = {}         
        for each_nid in self.RM_instance.mmc.mmc_connected_node_ids:
            if each_nid not in mmc_node_metric:
                route_to_mmc_node = self.RM_instance.interconnect.getPrecalcRouteXY(src_node_id, each_nid)  # task->MMC route               
                route_weight = len(self._get_flows_in_route_v3(route_to_mmc_node, local_copy_vnoctt).values())                                
                mmc_node_metric[each_nid] = route_weight
        
        # find min weight
        selected_mmc_node_id = self._get_key_with_min_val_from_dict(mmc_node_metric)
        return selected_mmc_node_id
        
    
    
    
    
    ##############################
    #### Fast implementations ####
    ##############################
    # take both distance and utilisation into account
    def getRandom_MMCPort_FF(self, tile_mapping):
        result = {}
        for each_tile_task_id, selected_nid in tile_mapping.iteritems():        
            selected_mmc_node_id = self.RM_instance.mmc.random_mmc_node_selection.next() # pregenerated to avoid having to call rand
            result[each_tile_task_id] = selected_mmc_node_id
            self.RM_instance.mmc.set_mmc_task_mapping(each_tile_task_id, selected_mmc_node_id)
        return result
    
    
    def getMapMMCIteratively_FF(self, tile_mapping, sorted_mmc_list):
        result = {}
        iter_sorted_mmc_list = itertools.cycle(sorted_mmc_list)
        for each_tile_task_id, selected_nid in tile_mapping.iteritems():        
            selected_mmc_id = iter_sorted_mmc_list.next()
            result[each_tile_task_id] = selected_mmc_id
            # update task to mmcnode mapping
            assert(selected_mmc_id != None)
            self.RM_instance.mmc.set_mmc_task_mapping(each_tile_task_id, selected_mmc_id)
        return result
    
    def getMapMMCIteratively_FF_listinput(self, tile_mapping_list, sorted_mmc_list):
        result = {}
        iter_sorted_mmc_list = itertools.cycle(sorted_mmc_list)
        for each_tile_task_id in tile_mapping_list:        
            selected_mmc_id = iter_sorted_mmc_list.next()
            result[each_tile_task_id] = selected_mmc_id
            
            # update task to mmcnode mapping
            assert(selected_mmc_id != None)
            self.RM_instance.mmc.set_mmc_task_mapping(each_tile_task_id, selected_mmc_id)
        
        return result
    
    
    
#     def getLUroute_MMCPort_FF(self, tile_mapping, sorted_mmc_list):
#         result = {}
#         iter_sorted_mmc_list = itertools.cycle(sorted_mmc_list)
#         for each_tile_task_id, selected_nid in tile_mapping.iteritems():        
#             selected_mmc_id = iter_sorted_mmc_list.next()
#             result[each_tile_task_id] = selected_mmc_id
#             # update task to mmcnode mapping
#             self.RM_instance.mmc.set_mmc_task_mapping(each_tile_task_id, selected_mmc_id)
#         return result
#         
#     
#     def getLMroute_MMCPort_FF(self, tile_mapping, sorted_mmc_list):
#         result = {}
#         iter_sorted_mmc_list = itertools.cycle(sorted_mmc_list)
#         for each_tile_task_id, selected_nid in tile_mapping.iteritems():        
#             selected_mmc_id = iter_sorted_mmc_list.next()
#             result[each_tile_task_id] = selected_mmc_id
#             # update task to mmcnode mapping
#             self.RM_instance.mmc.set_mmc_task_mapping(each_tile_task_id, selected_mmc_id)
#         return result    
        
    
    def getMapMMCIteratively_InvParent(self, tile_mapping, sorted_tile_tasks):
        result = {} # tileid to mmcid mapping
        
        all_mmcids = self.RM_instance.mmc.mmc_connected_node_ids
        circular_all_mmcids = itertools.cycle(all_mmcids)        
        
        for each_tile_task_id, each_tile_task in sorted_tile_tasks.iteritems(): # sorted in topological order
            tile_task = each_tile_task            
            tile_task_parent_ids = tile_task.get_expected_data_from_parents().keys()
            num_tiles_per_frame = tile_task.getNumSubTasksTiles()
            
            if len(tile_task_parent_ids) == 0: # most probably an I-frame tile
                selected_mmc_id = circular_all_mmcids.next()
            else:
                if ("_0" in each_tile_task_id): # first tile
                    
                    # find mmcs not used by parents
                    mmcsids_used_by_allparents = [result[pid] for pid in tile_task_parent_ids]
                    mmcs_unused = list(set(all_mmcids) - set(mmcsids_used_by_allparents))
                    
                    if len(mmcs_unused)<num_tiles_per_frame: # if not enough then fill by other mmcs
                        while(len(mmcs_unused)<num_tiles_per_frame):
                            mmcs_unused.append(circular_all_mmcids.next())
                            
                            if len(mmcs_unused) == num_tiles_per_frame:
                                break
                            else:
                                pass                            
                    else:
                        pass
                    
                    circular_mmcs_unused = itertools.cycle(mmcs_unused)
                    selected_mmc_id = circular_mmcs_unused.next()                    
                
                else:                    
                    selected_mmc_id = circular_mmcs_unused.next()
                        
            # set mmc mapping
            result[each_tile_task_id] = selected_mmc_id
            
            # update task to mmcnode mapping
            assert(selected_mmc_id != None)
            self.RM_instance.mmc.set_mmc_task_mapping(each_tile_task_id, selected_mmc_id)        
        
        assert(len(result.keys()) == len(sorted_tile_tasks.keys()))
        
        return result
    
    

    
     
    
    
    #####################################################
    # Main handler function
    #####################################################
    
    def map_to_mmc_mappingtbl(self, tile_mapping, sorted_tile_tasks, copy_vnoctt):
        result = {}        
        
        ######################################################
        # Default MMC selection
        ######################################################
        if SimParams.MMC_SMART_NODE_SELECTION_ENABLE == False:
            print "------- Warning ! : SimParams.MMC_SMART_NODE_SELECTION_ENABLE == False"            
            for each_tile_task_id, selected_nid in tile_mapping.iteritems():
                mmc_nid = self.getClosestMMCPort(selected_nid) # default
                result[each_tile_task_id] = mmc_nid
            return result       
        
        else:
            # get rid of obsolete flows
            #self.RM_instance.flow_table.refresh_simple_VNOCTT()
            
            if SimParams.MMC_SMART_NODE_SELECTION_TYPE == MMC_SmartPortSelectionTypes.MMC_SMARTPORTSELTYPE_IDEAL_V1:
                local_rtli_tbl = self.RM_instance.flow_table.getRealTimeLinkInfo_copy()
            
            ## mmc node selection at the task level ##
            if SimParams.MMC_PORT_ASSIGNMENT_LEVEL == 0: #{0=task, 1=job, 2=video} 
                
                ######################################################
                # Slow MMC selection versions using approximate 
                # flow status calculations
                ######################################################                
                if SimParams.MMC_SMART_NODE_SELECTION_TYPE < 30:
                
                    # now update volatile traffic table with latest flows
                    for each_tile_task_id, selected_nid in tile_mapping.iteritems():
                        # select the mmc port, basec on the chosen algorithm
                        if SimParams.MMC_SMART_NODE_SELECTION_TYPE == MMC_SmartPortSelectionTypes.MMC_SMARTPORTSELTYPE_DIST:
                            mmc_nid = self.getClosestMMCPort(selected_nid)
                        elif SimParams.MMC_SMART_NODE_SELECTION_TYPE == MMC_SmartPortSelectionTypes.MMC_SMARTPORTSELTYPE_LM:
                            mmc_nid = self.getLMroute_MMCPort(selected_nid, copy_vnoctt)
                        elif SimParams.MMC_SMART_NODE_SELECTION_TYPE == MMC_SmartPortSelectionTypes.MMC_SMARTPORTSELTYPE_LU:
                            mmc_nid = self.getLUroute_MMCPort(selected_nid, copy_vnoctt)
                        elif SimParams.MMC_SMART_NODE_SELECTION_TYPE == MMC_SmartPortSelectionTypes.MMC_SMARTPORTSELTYPE_LUDISTCOMBINED:                        
                            mmc_nid = self.getLUDistCombined_MMCPort(selected_nid, copy_vnoctt)
                        elif SimParams.MMC_SMART_NODE_SELECTION_TYPE == MMC_SmartPortSelectionTypes.MMC_SMARTPORTSELTYPE_RANDOM:
                            mmc_nid = self.getRandom_MMCPort(selected_nid)  
                            
                        # here we use LU selection, but based on real-time link util table    
                        elif SimParams.MMC_SMART_NODE_SELECTION_TYPE == MMC_SmartPortSelectionTypes.MMC_SMARTPORTSELTYPE_IDEAL_V1:
                            mmc_nid = self.getLUroute_MMCPort(selected_nid, local_rtli_tbl)
                            
                        else:
                            sys.exit("_map_to_mmc_mappingtbl:: Error - invalid choice")
                        
                        
                        # update task to mmcnode mapping
                        self.RM_instance.mmc.set_mmc_task_mapping(each_tile_task_id, mmc_nid)
                        
                        # update local link to flw table (only for certain selection techniques)
                        if SimParams.MMC_SMART_NODE_SELECTION_TYPE in [
                                                                       MMC_SmartPortSelectionTypes.MMC_SMARTPORTSELTYPE_LM,
                                                                       MMC_SmartPortSelectionTypes.MMC_SMARTPORTSELTYPE_LU,
                                                                       MMC_SmartPortSelectionTypes.MMC_SMARTPORTSELTYPE_LUDISTCOMBINED,
                                                                       ]:                                                             
                            
                            tmp_new_mmcrdwr_flws = self._get_mmc_related_pseudo_flows(sorted_tile_tasks[each_tile_task_id], 
                                                                                  mmc_nid, selected_nid, gop_uid=0)[0]
                            
                            # update local copy of vnoctt
                            for each_flw in tmp_new_mmcrdwr_flws:
                                copy_vnoctt = self._update_copy_vnoctt(each_flw, copy_vnoctt)
                                
                        elif SimParams.MMC_SMART_NODE_SELECTION_TYPE in [
                                                                       MMC_SmartPortSelectionTypes.MMC_SMARTPORTSELTYPE_IDEAL_V1
                                                                       ]:                            
                            tmp_new_mmcrdwr_flws = self._get_mmc_related_pseudo_flows(sorted_tile_tasks[each_tile_task_id], 
                                                                                  mmc_nid, selected_nid, gop_uid=0)[0]
                            # update local copy of rtli table
                            for each_flw in tmp_new_mmcrdwr_flws:
                                local_rtli_tbl = self._update_copy_vnoctt(each_flw, local_rtli_tbl)
                        else:
                            pass # no update necessary
                        
                        # save selected mmc id
                        result[each_tile_task_id] = mmc_nid
                
                    return result
                
                
                
                ########################################################
                # Fast MMC selection versions using sorted, approximate
                # flow table (sort of like FF mapping)
                ########################################################       
                else:
                    # central point of all mappings
                    #task_mapping_central_nid = self._get_central_point_all_task_mappings(tile_mapping)                    
                    
                    #####################################
                    ### Sorted LUs map tasks iteratively
                    #####################################                    
                    if SimParams.MMC_SMART_NODE_SELECTION_TYPE == MMC_SmartPortSelectionTypes.MMC_SMARTPORTSELTYPE_LU_FF:
                        # sort the mmcs according to utilisation (total flow payload)
                        sorted_mmcs_by_lu = self._get_sorted_mmc_nodes_LUroute(copy_vnoctt, default_source_nid = None)                        
                        # map them : this also updates rm mmc mapping table
                        result = self.getMapMMCIteratively_FF(tile_mapping, sorted_mmcs_by_lu)
                        return result 
                    
                    elif SimParams.MMC_SMART_NODE_SELECTION_TYPE == MMC_SmartPortSelectionTypes.MMC_SMARTPORTSELTYPE_LM_FF:                                                
                        # sort the mmcs according to utilisation (total flow payload)
                        sorted_mmcs_by_lm = self._get_sorted_mmc_nodes_LMroute(copy_vnoctt, default_source_nid = None)                        
                        # map them : this also updates rm mmc mapping table
                        result = self.getMapMMCIteratively_FF(tile_mapping, sorted_mmcs_by_lm)
                        return result
                    
                    # using real-time information                    
                    elif SimParams.MMC_SMART_NODE_SELECTION_TYPE == MMC_SmartPortSelectionTypes.MMC_SMARTPORTSELTYPE_IDEAL_FF_V1:                                                
                        # get ideal link to flow relationship table (real-time)
                        realtime_noctt = self.RM_instance.flow_table.getRealTimeLinkInfo()                        
                        sorted_mmcs = self._get_sorted_mmc_nodes_LUroute(realtime_noctt, default_source_nid = None)                        
                        # map them : this also updates rm mmc mapping table
                        result = self.getMapMMCIteratively_FF(tile_mapping, sorted_mmcs)
                        return result
                    
                    #####################################
                    ### tasks are ordered corner inwards
                    #####################################
                    elif SimParams.MMC_SMART_NODE_SELECTION_TYPE == MMC_SmartPortSelectionTypes.MMC_SMARTPORTSELTYPE_LU_CORNERIN_FF:
                        sorted_mmcs_by_lu = self._get_sorted_mmc_nodes_LUroute(copy_vnoctt, default_source_nid = None)                        
                        result = self.getMapMMCIteratively_FF_listinput(self._get_corner_inwards_list_values(tile_mapping.keys()), sorted_mmcs_by_lu)
                        return result
                        
                    elif SimParams.MMC_SMART_NODE_SELECTION_TYPE == MMC_SmartPortSelectionTypes.MMC_SMARTPORTSELTYPE_LM_CORNERIN_FF:                        
                        sorted_mmcs_by_lm = self._get_sorted_mmc_nodes_LMroute(copy_vnoctt, default_source_nid = None)                        
                        result = self.getMapMMCIteratively_FF_listinput(self._get_corner_inwards_list_values(tile_mapping.keys()), sorted_mmcs_by_lm)
                        return result
                           
                    #####################################
                    ### priority related selection
                    #####################################
                    elif SimParams.MMC_SMART_NODE_SELECTION_TYPE == MMC_SmartPortSelectionTypes.MMC_SMARTPORTSELTYPE_LOWBLOCKING_PROPORTIONAL_FF:
                        task_pri = sorted_tile_tasks[tile_mapping.keys()[0]].get_priority()
                        #target_pri = sys.maxint - (task_pri + (self.RM_instance.flow_priority_offset+100) + 0)
                        target_pri = task_pri + (self.RM_instance.flow_priority_offset+100) + 0
                        num_tasks = len(sorted_tile_tasks.keys())
                        sorted_mmcs_by_lb = self._get_scaled_mmc_list_with_low_blocking(copy_vnoctt, target_pri, num_tasks, default_source_nid = None)
                        result = self.getMapMMCIteratively_FF_listinput(self._get_corner_inwards_list_values(tile_mapping.keys()), sorted_mmcs_by_lb)                        
                        return result
                    
                    #####################################
                    ### random selection - fast impl
                    #####################################
                    elif SimParams.MMC_SMART_NODE_SELECTION_TYPE == MMC_SmartPortSelectionTypes.MMC_SMARTPORTSELTYPE_RANDOM_FF:
                        result = self.getRandom_MMCPort_FF(tile_mapping)
                        return result
                                        
                    #####################################
                    ### mmc selection different to the parent
                    #####################################
                    elif SimParams.MMC_SMART_NODE_SELECTION_TYPE == MMC_SmartPortSelectionTypes.MMC_SMARTPORTSELTYPE_INV_PARENT:
                        result = self.getMapMMCIteratively_InvParent(tile_mapping, sorted_tile_tasks)
                        return result
                    
                    else:
                        sys.exit("Error! unknown MMC selection")
                    
                    
            ## mmc node selection at the video level ##
            elif SimParams.MMC_PORT_ASSIGNMENT_LEVEL == 1:
                sys.exit("_map_to_mmc_mappingtbl: Error : not implemented yet !")
            
            ## mmc node selection at the video level ##
            elif SimParams.MMC_PORT_ASSIGNMENT_LEVEL == 2:  
                sys.exit("_map_to_mmc_mappingtbl: Error : not implemented yet !")
                
                
        
                
    
    def _local_traffic_table_add_flw(self, new_flw, tmp_traffic_table):        
        flow_route_links = new_flw.get_route()        
        for each_link in flow_route_links:
            tbl_k = each_link.get_id()
            if tbl_k not in tmp_traffic_table:
                tmp_traffic_table[tbl_k] = [new_flw]
            else:
                tmp_traffic_table[tbl_k].append(new_flw)
        return tmp_traffic_table
    
    
    def _update_copy_vnoctt(self, new_flw, copy_vnoctt):
        flow_route_links = new_flw.get_route()        
        for each_link in flow_route_links:
            tbl_k = each_link.get_id()
            if tbl_k not in copy_vnoctt:
                copy_vnoctt[tbl_k] = [new_flw]
            else:
                copy_vnoctt[tbl_k].append(new_flw)
        return copy_vnoctt
        
    
    
    
               
            
    #####################################################################################
    #####################################################################################
    # HELPER functions
    #####################################################################################
    
    #####################################################
    # Helpers: misc
    #####################################################
    def _normalise_val_minmax(self, x, x_min, x_max):
        if x_min == x_max : return 1.0
        else:
            x_norm = (float(x) - float(x_min))/(float(x_max) - float(x_min))
            return x_norm
    
    def _normalise_val_zscore(self, x, x_mean, x_std):
        z = (float(x) - float(x_mean))/(float(x_std))
        return z
    
    def _get_key_with_min_val_from_dict(self, param_dict):
        # find closest node
        min_val = np.min(param_dict.values())
        list_suitable_keys = [k for k,v in param_dict.iteritems() if v == min_val]
        sorted_suitable_keys = sorted(list_suitable_keys)        
        result_k = sorted_suitable_keys[0]
        return result_k
    
    # change the order of a list outer corners to inwards           
    def _get_corner_inwards_list_values(self, generic_list):
        result_list = []
        len_generic_list = len(generic_list)-1
        if len(generic_list)%2 == 0: # even
            for ix, x in enumerate(generic_list):
                i = ix
                j = len_generic_list-ix
                if j > i:
                    result_list.append(generic_list[i])
                    result_list.append(generic_list[j])
                else:                    
                    break;
        else: # odd
            for ix, x in enumerate(generic_list):
                i = ix
                j = len_generic_list-ix
                if i < len_generic_list/2:
                    result_list.append(generic_list[i])
                    result_list.append(generic_list[j])
                elif i == len_generic_list/2:
                    result_list.append(generic_list[i])
                    break;
                else:                    
                    break;
                    
       
        assert(len(result_list) == len(generic_list))
        assert(set(result_list) == set(generic_list))
        
        return result_list
               
                 
    #####################################################
    # Helpers: find all flows of GoP, add to noc volatile
    # traffic table
    #####################################################
    
    # populate the VNOCTT with a given list of sorted tile tasks 
    def _populate_VNOCTT(self, gop_tasks, sorted_tile_tasks, 
                                   mapping_assignment, mmc_assignment, 
                                   adaptive_gop_obj, num_tiles):
        
        # get flows 
        new_flows_list = self._get_gop_flows_withOffsets(gop_tasks, sorted_tile_tasks, 
                                                         mapping_assignment, mmc_assignment, 
                                                         adaptive_gop_obj, num_tiles)
        
        for each_f in new_flows_list:
            self.RM_instance.flow_table.add_VNOCTT(each_f)
            
        return len(new_flows_list)
        
    
    # gop_tasks : tasks in the original gop in gop seq order (list)
    # mapping_assignment : dict - tiletaskid: nid    
    # mmc_assignment : dict - tiletaskid: mmc_id
    def _get_gop_flows_withOffsets(self, gop_tasks, sorted_tile_tasks, 
                                   mapping_assignment, mmc_assignment, 
                                   adaptive_gop_obj, num_tiles):
        all_gop_flows = []        
        gop_tasks_dict = {}
        for t in gop_tasks:
            gop_tasks_dict[t.get_id()] = t
        
        #pprint.pprint(gop_tasks_dict)
        
        gop_decoding_order_frix = adaptive_gop_obj.getDecodingOrder()[0] # expensive
        
        gop_uid = gop_tasks[0].get_unique_gop_id()        
        tt_i = 0
        local_flw_id = 0
        for each_tile_task_id, each_tile_task in sorted_tile_tasks.iteritems():
            src_nid = mapping_assignment[each_tile_task_id]
            orig_src_t_tid = int(each_tile_task_id[:each_tile_task_id.index('_')])
            src_t_ftype = gop_tasks_dict[orig_src_t_tid].get_frameType()
            scr_t_dec_order_ix = gop_decoding_order_frix.index(each_tile_task.get_frameIXinGOP())
            mmc_node_id = mmc_assignment[each_tile_task_id]            
            
            avg_comp_cost_goptasks = (gop_tasks[0].get_wccIFrame() + gop_tasks[0].get_wccPFrame() + gop_tasks[0].get_wccBFrame())/3.0
            avg_flw_cost_gopflows =  (np.sum(HEVCWLP.HEVCWLPARAMS_DATAPAYLOAD_MEDIAN_PROPORTIONS[gop_tasks[0].get_video_genre()].values())/5.0) * \
                                    (gop_tasks[0].get_completedTaskSize())
            root_to_srctask_cum_task_wccc =  (scr_t_dec_order_ix+1) * avg_comp_cost_goptasks
            root_to_srctask_cum_flw_wccc =  scr_t_dec_order_ix * avg_flw_cost_gopflows
            flw_rel_time = self.env.now + (root_to_srctask_cum_task_wccc + root_to_srctask_cum_flw_wccc)
                        
            # (1) flows related to task-to-task edges
            for each_child_id, child_payload in each_tile_task.get_expected_data_to_children().iteritems():
                dst_nid = mapping_assignment[each_child_id]        
                
                if src_nid != dst_nid:                        
                    orig_dst_t_tid = int(each_child_id[:each_child_id.index('_')])
                    
                    dst_t_ftype = gop_tasks_dict[orig_dst_t_tid].get_frameType()
                    data_node2node_type =  dst_t_ftype + "<-" + src_t_ftype
            
                    payload_ub = gop_tasks[0].get_frame_h() * gop_tasks[0].get_frame_w()
                    payload_ub_proportion = HEVCWLP.HEVCWLPARAMS_DATAPAYLOAD_MEDIAN_PROPORTIONS[gop_tasks[0].get_video_genre()][data_node2node_type]                    
                    wc_proportion = 1.0        # worst-case proportion
                                
                    #node2node_avg_payload = (float(payload_ub) * payload_ub_proportion) * 3 # bytes per pixel # this is avg.case
                    node2node_avg_payload = (float(payload_ub) * wc_proportion) * 3 # bytes per pixel # this is worst.case
                    
                    new_tile_payload = node2node_avg_payload
                    
                    #flw_pri = sys.maxint - (each_tile_task.get_priority() + (self.RM_instance.flow_priority_offset+100) + tt_i) 
                    flw_pri = each_tile_task.get_priority() + (self.RM_instance.flow_priority_offset+100) + tt_i
                    
                    new_flow = self._get_pseudo_flow(gop_uid, each_tile_task_id, local_flw_id,
                                                     src_nid, dst_nid, 
                                                     flw_pri, 
                                                     flw_rel_time, new_tile_payload)
                    all_gop_flows.append(new_flow)
            
                    tt_i +=1
                    local_flw_id +=1
                else:
                    pass # child and parent on same core
            
            
            # (2) + (3) : get mmc related flows (RD + WR)            
            (new_mmc_rel_flws, 
             tmp_tt_i, tmp_local_flw_id) = self._get_mmc_related_pseudo_flows(each_tile_task, mmc_node_id, src_nid, 
                                                                             param_tt_i=tt_i, 
                                                                             param_local_flw_id=local_flw_id,
                                                                             gop_uid=gop_uid)
            all_gop_flows.extend(new_mmc_rel_flws)
            
            tt_i = tmp_tt_i        
            local_flw_id = tmp_local_flw_id
        
        return all_gop_flows
    
    
    
    def _get_mmc_related_pseudo_flows(self, tile_task, mmc_node_id, src_nid, gop_uid=0,
                                      param_tt_i=0, param_local_flw_id=0):
        all_mmcrelated_flows = [] 
        
        tile_task_id = tile_task.get_id()
        
        # (2) flows related to mmc-to-task edges           
        release_time = self.env.now
        priority = SimParams.MMC_DATAREAD_FLOW_PRIORITY + param_tt_i        
        payload = tile_task.get_mpeg_tasksize()                           
        new_flow = self._get_pseudo_flow(gop_uid, tile_task_id, param_local_flw_id, 
                                         mmc_node_id, src_nid, 
                                         priority, release_time, payload)
        all_mmcrelated_flows.append(new_flow)
                
        param_tt_i +=1
        param_local_flw_id +=1
        
        
        # higher flow pri numbers == lower priority   
        # (3) flows related to task-to-mmc edges            
        release_time = self.env.now + tile_task.get_worstCaseComputationCost()
        priority = tile_task.get_priority() + (self.RM_instance.flow_priority_offset+100) + param_tt_i  
        #priority = sys.maxint - (tile_task.get_priority() + (self.RM_instance.flow_priority_offset+100) + param_tt_i)
        payload = tile_task.get_completedTaskSize()            
        new_flow = self._get_pseudo_flow(gop_uid, tile_task_id, param_local_flw_id, 
                                         src_nid, mmc_node_id, 
                                         tile_task.get_priority(), 
                                         release_time, payload)
        
        all_mmcrelated_flows.append(new_flow)
        
        param_tt_i +=1
        param_local_flw_id +=1
        
        return (all_mmcrelated_flows, param_tt_i, param_local_flw_id)
    
    
    def _get_gop_flows(self, gop_tasks, sorted_tile_tasks, mapping_assignment, mmc_assignment, adaptive_gop_obj, num_tiles):        
        all_gop_flows = []
        gop_tasks_dict = {}
        for t in gop_tasks:
            gop_tasks_dict[t.get_id()] = t
        
        gop_uid = gop_tasks[0].get_unique_gop_id()
        
        tt_i = 0
        local_flw_id = 0
        for each_tile_task_id, each_tile_task in sorted_tile_tasks.iteritems():
            src_nid = mapping_assignment[each_tile_task_id]
            orig_src_t_tid = each_tile_task_id[:each_tile_task_id.index('_')]
            src_t_ftype = gop_tasks_dict[orig_src_t_tid].get_frameType()            
            mmc_node_id = mmc_assignment[each_tile_task_id]
            flw_rel_time = self.env.now 
                        
            # (1) flows related to task-to-task edges
            for each_child_id, child_payload in each_tile_task.get_expected_data_to_children().iteritems():
                dst_nid = mapping_assignment[each_child_id]                
                
                if (src_nid != dst_nid):                
                    orig_dst_t_tid = each_child_id[:each_child_id.index('_')]                    
                    dst_t_ftype = gop_tasks_dict[orig_dst_t_tid].get_frameType()
                    data_node2node_type =  dst_t_ftype + "<-" + src_t_ftype
            
                    payload_ub = gop_tasks[0].get_frame_h() * gop_tasks[0].get_frame_w()
                    payload_ub_proportion = HEVCWLP.HEVCWLPARAMS_DATAPAYLOAD_MEDIAN_PROPORTIONS[gop_tasks[0].get_video_genre()][data_node2node_type]
                    node2node_avg_payload = (float(payload_ub) * payload_ub_proportion) * 3 # bytes per pixel
                    new_tile_payload = node2node_avg_payload
                    
                    #flw_pri = sys.maxint - (each_tile_task.get_priority() + (self.RM_instance.flow_priority_offset+100) + tt_i) 
                    flw_pri = each_tile_task.get_priority() + (self.RM_instance.flow_priority_offset+100) + tt_i
                    
                    new_flow = self._get_pseudo_flow(gop_uid, each_tile_task_id, local_flw_id, src_nid, dst_nid, 
                                                     flw_pri, 
                                                     flw_rel_time, new_tile_payload)
                    all_gop_flows.append(new_flow)
            
                    tt_i +=1
                    local_flw_id +=1
                else:
                    pass # child and parent in same core
                
        # (2) flows related to mmc-to-task edges           
            release_time = self.env.now            
            priority = SimParams.MMC_DATAREAD_FLOW_PRIORITY + tt_i        
            payload = each_tile_task.get_mpeg_tasksize()                                    
            new_flow = self._get_pseudo_flow(gop_uid, each_tile_task_id, local_flw_id, mmc_node_id, src_nid, 
                                             priority, release_time, payload)
            all_gop_flows.append(new_flow)
            
            tt_i +=1
            local_flw_id +=1
            
        # (3) flows related to task-to-mmc edges            
            release_time = flw_rel_time
            priority = each_tile_task.get_priority() + (self.RM_instance.flow_priority_offset+100) + tt_i
            #priority = sys.maxint - (each_tile_task.get_priority() + (self.RM_instance.flow_priority_offset+100) + tt_i)
            payload = each_tile_task.get_completedTaskSize()            
            new_flow = self._get_pseudo_flow(gop_uid, each_tile_task_id, local_flw_id, src_nid, mmc_node_id, 
                                             priority, release_time, payload)
            all_gop_flows.append(new_flow)            
        
            tt_i +=1
            local_flw_id +=1
            
        
        return all_gop_flows
            
    
    
    def _get_pseudo_flow(self, gop_uid, tid, local_flw_id, src_node_id, dst_node_id, pri, rt, pl):        
        #id = "g%d_f%d" % (gop_uid,local_flw_id) # does not take into account task id - not accurate !
        
        id = "g%d_t%s_f%d" % (gop_uid,str(tid),local_flw_id)        
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
            
            
            
        
        
    def _get_flows_in_route(self, route):        
        flows_in_route = {}
        for each_link in route:
            if each_link.get_id() in self.RMInstance.volatile_noc_traffic_table:            
                for each_flw in self.RMInstance.volatile_noc_traffic_table[each_link.get_id()]:
                    k = each_flw.get_id()
                    if k not in flows_in_route:
                        flows_in_route[k] = each_flw
                    else:
                        pass
            else:
                pass
                
        return flows_in_route
    
    
    def _get_flows_in_route_v2(self, route, local_traffic_table=None):
        all_flws_in_route = [] # duplicates allowed
        result_flws_table = {}
        for each_link in route:
            each_link_id = each_link.get_id()
            if each_link_id in self.RMInstance.volatile_noc_traffic_table:
                all_flws_in_route.extend(self.RMInstance.volatile_noc_traffic_table[each_link_id])
            else:
                pass
            
            # if there is another traffic table supplied (apart from the VNOCTT)
            # then search this too
            if local_traffic_table != None:
                if each_link_id in local_traffic_table:
                    all_flws_in_route.extend(local_traffic_table[each_link_id])
                else:
                    pass
            else:
                pass
        
        # removes duplicates (can use sets, but not sure if sets can work on list of flows)
        for f in all_flws_in_route:
            f_id = f.get_id()
            if f_id not in result_flws_table:
                result_flws_table[f_id] = f
            else:
                pass
            
        return result_flws_table
        
        
    def _get_flows_in_route_v3(self, route, local_copy_vnoctt):
        all_flws_in_route = [] # duplicates allowed
        result_flws_table = {}
        for each_link in route:
            each_link_id = each_link.get_id()
            if each_link_id in local_copy_vnoctt:
                all_flws_in_route.extend(local_copy_vnoctt[each_link_id])
            else:
                pass
            
        # removes duplicates (can use sets, but not sure if sets can work on list of flows)
        for f in all_flws_in_route:
            f_id = f.get_id()
            if f_id not in result_flws_table:
                result_flws_table[f_id] = f
            else:
                pass
            
        return result_flws_table    
        
    def _get_route_total_flw_payload(self, route, link_to_flw_mapping_table):        
        unique_flw_dict = {} 
        flws = list(itertools.chain.from_iterable([link_to_flw_mapping_table[lnk.get_id()] 
                                                   for lnk in route if lnk.get_id() in link_to_flw_mapping_table]))
        total_payload = 0.0
        # remove dupdlicates
        for f in flws:
            fid = f.get_id()
            if fid not in unique_flw_dict:
                unique_flw_dict[fid] = f
                total_payload += f.get_payload()
            else: 
                pass
            
        return total_payload
    
    
    def _get_route_total_flws(self, route, link_to_flw_mapping_table):        
        unique_flw_dict = {} 
        flws = list(itertools.chain.from_iterable([link_to_flw_mapping_table[lnk.get_id()] 
                                                   for lnk in route if lnk.get_id() in link_to_flw_mapping_table]))        
        # remove dupdlicates
        for f in flws:
            fid = f.get_id()
            if fid not in unique_flw_dict:
                unique_flw_dict[fid] = f                
            else: 
                pass
            
        return len(unique_flw_dict.keys())
    
    
    def _get_route_total_lpflws(self, route, link_to_flw_mapping_table, target_pri):        
        unique_flw_dict = {} 
        flws = list(itertools.chain.from_iterable([link_to_flw_mapping_table[lnk.get_id()] 
                                                   for lnk in route if lnk.get_id() in link_to_flw_mapping_table]))        
        # remove dupdlicates
        for f in flws:
            fid = f.get_id()
            fpri = f.get_priority()
            if fid not in unique_flw_dict:
                if fpri > target_pri: # NB: higher the pri number, lower the priority
                    unique_flw_dict[fid] = f
                else:
                    pass                
            else: 
                pass            
        return len(unique_flw_dict.keys())
    
    def _get_route_total_hpflws(self, route, link_to_flw_mapping_table, target_pri):        
        unique_flw_dict = {} 
        flws = list(itertools.chain.from_iterable([link_to_flw_mapping_table[lnk.get_id()] 
                                                   for lnk in route if lnk.get_id() in link_to_flw_mapping_table]))        
        # remove dupdlicates
        for f in flws:
            fid = f.get_id()
            fpri = f.get_priority()
            if fid not in unique_flw_dict:
                if fpri < target_pri: # NB: higher the pri number, lower the priority
                    unique_flw_dict[fid] = f
                else:
                    pass                
            else: 
                pass            
        return len(unique_flw_dict.keys())
    
    def _get_sorted_mmc_nodes_LUroute(self, local_copy_vnoctt, default_source_nid = None):
        mmc_with_metric = {}
        sorted_mmcids_with_metric = None
        # if a source node is provided
        if default_source_nid != None:            
            for each_nid in self.RM_instance.mmc.mmc_connected_node_ids:
                if each_nid not in mmc_with_metric:
                    route_to_mmc_node = self.RM_instance.interconnect.getPrecalcRouteXY(default_source_nid, each_nid) # task->MMC route    
                    route_flow_cum_payload = self._get_route_total_flw_payload(route_to_mmc_node, local_copy_vnoctt)                        
                    mmc_with_metric[each_nid] = route_flow_cum_payload
            
            # sort mmcs according to total flow payload
            sorted_mmcids_with_metric = sorted(mmc_with_metric, key=mmc_with_metric.get)
            
        # if a source node is not provided we only check the mmc links
        else:
            for each_nid in self.RM_instance.mmc.mmc_connected_node_ids:
                mmc_specific_link =  self.RM_instance.interconnect.getPrecalcRouteXY(each_nid.replace("MMC", ""), each_nid)
                route_flow_cum_payload = self._get_route_total_flw_payload(mmc_specific_link, local_copy_vnoctt)
                mmc_with_metric[each_nid] = route_flow_cum_payload
            
            # testing
            #print "--> mmc_with_metric.values() :" , pprint.pformat(mmc_with_metric.values())
            
            # sort mmcs according to total flow payload
            sorted_mmcids_with_metric = sorted(mmc_with_metric, key=mmc_with_metric.get)
        
        return sorted_mmcids_with_metric
        
    
    def _get_sorted_mmc_nodes_LMroute(self, local_copy_vnoctt, default_source_nid = None):
        mmc_with_metric = {}
        sorted_mmcids_with_metric = None
        # if a source node is provided
        if default_source_nid != None:            
            for each_nid in self.RM_instance.mmc.mmc_connected_node_ids:
                if each_nid not in mmc_with_metric:
                    route_to_mmc_node = self.RM_instance.interconnect.getPrecalcRouteXY(default_source_nid, each_nid) # task->MMC route    
                    route_flow_cum_flws = self._get_route_total_flws(route_to_mmc_node, local_copy_vnoctt)                        
                    mmc_with_metric[each_nid] = route_flow_cum_flws
            
            # sort mmcs according to total flow payload
            sorted_mmcids_with_metric = sorted(mmc_with_metric, key=mmc_with_metric.get)
            
        # if a source node is not provided we only check the mmc links
        else:
            for each_nid in self.RM_instance.mmc.mmc_connected_node_ids:
                mmc_specific_link =  self.RM_instance.interconnect.getPrecalcRouteXY(each_nid.replace("MMC", ""), each_nid)
                route_flow_cum_flws = self._get_route_total_flws(mmc_specific_link, local_copy_vnoctt)
                mmc_with_metric[each_nid] = route_flow_cum_flws
            
            # testing
            #print "--> mmc_with_metric.values() :" , pprint.pformat(mmc_with_metric.values())
            
            # sort mmcs according to total flow payload
            sorted_mmcids_with_metric = sorted(mmc_with_metric, key=mmc_with_metric.get)
        
        return sorted_mmcids_with_metric
    
    
    
    def _get_scaled_mmc_list_with_low_blocking(self, local_copy_vnoctt, target_pri, num_tasks, default_source_nid = None):
        result_scaled_mmcs_list = []
        mmc_with_metric = {}
        norm_mmc_list = {}
        norm_mmc_scaled_nums = {}
        if default_source_nid != None:
            for each_nid in self.RM_instance.mmc.mmc_connected_node_ids:
                if each_nid not in mmc_with_metric:
                    route_to_mmc_node = self.RM_instance.interconnect.getPrecalcRouteXY(default_source_nid, each_nid) # task->MMC route
                    num_hp_flows = self._get_route_total_hpflws(route_to_mmc_node, local_copy_vnoctt, target_pri)
                    if num_hp_flows == 0: num_hp_flows = 1 # gets rid of issues with zero
                    mmc_with_metric[each_nid] = num_hp_flows
                else:
                    pass
        else:
            for each_nid in self.RM_instance.mmc.mmc_connected_node_ids:
                if each_nid not in mmc_with_metric:
                    mmc_specific_link =  self.RM_instance.interconnect.getPrecalcRouteXY(each_nid.replace("MMC", ""), each_nid)
                    num_hp_flows = self._get_route_total_hpflws(mmc_specific_link, local_copy_vnoctt, target_pri)
                    if num_hp_flows == 0: num_hp_flows = 1 # gets rid of issues with zero
                    mmc_with_metric[each_nid] = num_hp_flows
                else:
                    pass
                
        # get sum
        v_mean = np.mean(mmc_with_metric.values())
        
        sorted_mmcids_with_metric = itertools.cycle(sorted(mmc_with_metric, key=mmc_with_metric.get, reverse=False))
        
        res_count = 0
        while(res_count < num_tasks):
            mmc_id = sorted_mmcids_with_metric.next()
            mmc_val = mmc_with_metric[mmc_id]
            if mmc_val <= v_mean:
                result_scaled_mmcs_list.extend([mmc_id]*2) # more tasks if this mmc has lower blocking
                res_count +=2
            else:
                result_scaled_mmcs_list.extend([mmc_id]*1)
                res_count +=1
            
            if res_count >= num_tasks:
                break;
            else:
                pass
            
        
        
#         # normalise and invert
#         if v_min == v_max:
#             for k,v in mmc_with_metric.iteritems():
#                 norm_mmc_scaled_nums[k] = 0.5                
#         else:            
#             for k,v in mmc_with_metric.iteritems():
#                 norm_mmc_scaled_nums[k] = 1.0 - self._normalise_val_minmax(v, v_min, v_max)
#         
#         print "+++"
#         pprint.pprint(norm_mmc_scaled_nums)
#         print "+++"
#         
#         v_sum = np.sum(norm_mmc_scaled_nums.values())
#         # normalise again
#         for k,v in norm_mmc_scaled_nums.iteritems():
#             norm_mmc_scaled_nums[k] = (float(v)/float(v_sum))
#         
#         print "+++"
#         pprint.pprint(norm_mmc_scaled_nums)
#         print "+++"
#         
#         sorted_mmcids_with_metric = sorted(norm_mmc_scaled_nums, key=norm_mmc_scaled_nums.get, reverse=True)
#         
#         for each_nid in sorted_mmcids_with_metric:
#             each_v = norm_mmc_scaled_nums[each_nid]                        
#             n = int(np.ceil(each_v * float(num_tasks)))            
#             result_scaled_mmcs_list.extend([each_nid]*n)
#         
#         print "---"
#         print "num_tasks : ", num_tasks
#         #print "scaled mmc list :"
#         pprint.pprint(result_scaled_mmcs_list)
#         pprint.pprint(mmc_with_metric)
#         print "num_result : ", len(result_scaled_mmcs_list)
#         print "---"
        
        assert(len(result_scaled_mmcs_list) >= num_tasks)
        
        return result_scaled_mmcs_list
        
        
        
    
    # centroid of multiple points are average value of x's and y's    
    def _get_central_point_all_task_mappings(self, tile_mapping):
        sum_xy = [0,0]
        total_num_tasks = len(tile_mapping.keys())
        for each_tile_task_id, selected_nid in tile_mapping.iteritems():
            (n_x, n_y) =  self.RM_instance.interconnect.getXYPosByNodeId(selected_nid)
            sum_xy[0] += n_x
            sum_xy[1] += n_y
        average_n_xy = int(round(float(sum_xy[0])/float(total_num_tasks)))
        return average_n_xy
    
        
