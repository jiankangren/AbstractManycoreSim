import pprint
import traceback
import sys
import csv
import itertools
import simpy
import random
import json
from operator import itemgetter
from collections import OrderedDict

from SimParams import SimParams
from TaskMappingSchemes import TaskMappingSchemes
from libApplicationModel.MPEG2FrameTask import MPEG2FrameTask
from libApplicationModel.HEVCFrameTask import HEVCFrameTask
from libApplicationModel.Task import TaskModel



# once a stream has entered the system, the frames of the GoPs are mapped. 
# this mapping is fixed throughout the lifetime of the video stream
class TaskMappingSchemesImpl:

    def __init__(self, env, RM_instance):  
        self.env = env
        self.RM_instance = RM_instance
    
    
    def taskMappingSchemeHandler(self, strm_specs):
        if SimParams.DYNAMIC_TASK_MAPPING_SCHEME == TaskMappingSchemes.TASKMAPPINGSCHEMES_NONE:
            result =  self.taskMappingSchImpl_getFrameMapping_None(strm_specs)
            
        elif SimParams.DYNAMIC_TASK_MAPPING_SCHEME == TaskMappingSchemes.TASKMAPPINGSCHEMES_RANDOM:
            result =  self.taskMappingSchImpl_getFrameMapping_Random(strm_specs)
            
        elif SimParams.DYNAMIC_TASK_MAPPING_SCHEME == TaskMappingSchemes.TASKMAPPINGSCHEMES_SHORTEST_TQ:
            result =  self.taskMappingSchImpl_getFrameMapping_ShortestTQ(strm_specs)
        
        elif SimParams.DYNAMIC_TASK_MAPPING_SCHEME == TaskMappingSchemes.TASKMAPPINGSCHEMES_HIGHEST_THROUGHPUT:
            result =  self.taskMappingSchImpl_getFrameMapping_HighestThroughput(strm_specs)
        
#         elif SimParams.DYNAMIC_TASK_MAPPING_SCHEME == TaskMappingSchemes.TASKMAPPINGSCHEMES_LOWEST_THROUGHPUT:
#             result =  self.taskMappingSchImpl_getFrameMapping_Random(strm_specs)
        
        elif SimParams.DYNAMIC_TASK_MAPPING_SCHEME == TaskMappingSchemes.TASKMAPPINGSCHEMES_LOWEST_REMAININGWCCC:
            result =  self.taskMappingSchImpl_getFrameMapping_LowestRemainingWCCC(strm_specs)            
        
        elif SimParams.DYNAMIC_TASK_MAPPING_SCHEME == TaskMappingSchemes.TASKMAPPINGSCHEMES_HIGHEST_REMAININGWCCC:
            result =  self.taskMappingSchImpl_getFrameMapping_HighestRemainingWCCC(strm_specs)
                    
        elif SimParams.DYNAMIC_TASK_MAPPING_SCHEME == TaskMappingSchemes.TASKMAPPINGSCHEMES_HYB_SHORTESTTQ_AND_LOWESTREMAININGWCCC:
            result =  self.taskMappingSchImpl_getFrameMapping_HybShortestTQAndLowestRemainingWCCC(strm_specs)
            
        elif SimParams.DYNAMIC_TASK_MAPPING_SCHEME == TaskMappingSchemes.TASKMAPPINGSCHEMES_HYB_SHORTESTTQ_AND_LOWESTREMAININGAVGCCC:
            result =  self.taskMappingSchImpl_getFrameMapping_HybShortestTQAndLowestRemainingAvgCCC(strm_specs)
        
        elif SimParams.DYNAMIC_TASK_MAPPING_SCHEME == TaskMappingSchemes.TASKMAPPINGSCHEMES_HYB_SHORTESTTQ_AND_RANDOM:
            result =  self.taskMappingSchImpl_getFrameMapping_HybShortestTQAndRandom(strm_specs)
        
        elif SimParams.DYNAMIC_TASK_MAPPING_SCHEME == TaskMappingSchemes.TASKMAPPINGSCHEMES_LOWEST_UTILISATION_NEARESTPARENT:
            result =  self.taskMappingSchImpl_getFrameMapping_LowestUtilNearestParent(strm_specs)
        
        elif SimParams.DYNAMIC_TASK_MAPPING_SCHEME == TaskMappingSchemes.TASKMAPPINGSCHEMES_LOWEST_UTILISATION:
            result =  self.taskMappingSchImpl_getFrameMapping_LowestUtil(strm_specs)        
        
        elif SimParams.DYNAMIC_TASK_MAPPING_SCHEME == TaskMappingSchemes.TASKMAPPINGSCHEMES_SHORTEST_TQ_VIARUNTIMEAPP:
            result =  self.taskMappingSchImpl_getFrameMapping_ShortestTQ_viaRuntimeApp(strm_specs)
            
        elif SimParams.DYNAMIC_TASK_MAPPING_SCHEME == TaskMappingSchemes.TASKMAPPINGSCHEMES_CUSTOM_LOADFROMFILE:
            result =  self.taskMappingSchImpl_getFrameMapping_CustomLoadFromFile(strm_specs)
            
        
        else:
            sys.exit("taskMappingSchemeHandler:: Error: unknown task mapping scheme")
            
        
        return result
    
    
    #####################################################################################
    # TASKMAPPINGSCHEMES_RANDOM
    #####################################################################################
    # assign a node randomly, out of the ones that have capacity in tq
    def taskMappingSchImpl_getFrameMapping_None(self, strm_specs):
        
        free_nodes_list_ascorder = self.RM_instance.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL)
        if (len(free_nodes_list_ascorder) == 0):
            return None
        else:
            return 1
    
    
    #####################################################################################
    # TASKMAPPINGSCHEMES_RANDOM
    #####################################################################################
    # assign a node randomly, out of the ones that have capacity in tq
    def taskMappingSchImpl_getFrameMapping_Random(self, strm_specs):
        
        # get list of nodes that are free 
        free_nodes_list = self.RM_instance.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL)
        
        if(len(free_nodes_list)>0):
        
            wf_id = strm_specs['wf_id']
            strm_id = strm_specs['vid_strm_id']
            gop_struct = strm_specs['gop_struct']        
            frames_mapping = {}
            
            for f_ix, each_f in enumerate(gop_struct):
                selected_node = random.choice(free_nodes_list)
                frames_mapping[f_ix] = selected_node.get_id()        
            
            self._map_to_vidstrm_mappingtbl(frames_mapping, wf_id, strm_id)
                
            return frames_mapping
        else:
            return None    
    
    
    #####################################################################################
    # TASKMAPPINGSCHEMES_SHORTEST_TQ
    #####################################################################################
    # node with the min amount of tasks in its tq is selected
    def taskMappingSchImpl_getFrameMapping_ShortestTQ(self, strm_specs):
        
        # get list of nodes that are free 
        free_nodes_list_ascorder = self.RM_instance.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL)        
        node_and_tqlevel_dict = {}        
        # maintain a (node, tqlevel) dict internally
        for node in free_nodes_list_ascorder: 
            node_and_tqlevel_dict[node.get_id()] = node.getTaskQ_level()
                
        if(len(free_nodes_list_ascorder)>0):
        
            wf_id = strm_specs['wf_id']
            strm_id = strm_specs['vid_strm_id']
            gop_struct = strm_specs['gop_struct']        
            frames_mapping = {}
            
            # find the lowest tq
            for f_ix, each_f in enumerate(gop_struct):
                min_tqval = min(node_and_tqlevel_dict.itervalues()) 
                
                nodes_with_min_tq = [k for k, v in node_and_tqlevel_dict.iteritems() if v == min_tqval]
                
                #print "taskMappingSchImpl_getFrameMapping_ShortestTQ :: num nodes with min tq" + str(len(nodes_with_min_tq))
                selected_node_id = nodes_with_min_tq[0]
                
                #selected_node_id = [k for k, v in node_and_tqlevel_dict.iteritems() if v == min_tqval][0]
                
                frames_mapping[f_ix] = selected_node_id # assign                
                node_and_tqlevel_dict[selected_node_id] = node_and_tqlevel_dict[selected_node_id]+1 # update dict
            
            self._map_to_vidstrm_mappingtbl(frames_mapping, wf_id, strm_id)
                
            return frames_mapping
        else:
            return None        
        
    
    
    #####################################################################################
    # TASKMAPPINGSCHEMES_SHORTEST_TQ_VIARUNTIMEAPP
    #####################################################################################
    # node with the min amount of tasks in its tq is selected
    def taskMappingSchImpl_getFrameMapping_ShortestTQ_viaRuntimeApp(self, strm_specs):
        
        # get list of nodes that are free 
        free_nodes_list_ascorder = self.RM_instance.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL)        
        node_and_tqlevel_dict = {}        
        # maintain a (node, tqlevel) dict internally
        for node in free_nodes_list_ascorder: 
            node_and_tqlevel_dict[node.get_id()] = len(self.RM_instance.RunTimeApps.getNodeToTaskMapping(node_id=node.get_id()))
                
        if(len(free_nodes_list_ascorder)>0):
        
            wf_id = strm_specs['wf_id']
            strm_id = strm_specs['vid_strm_id']
            gop_struct = strm_specs['gop_struct']        
            frames_mapping = {}
            
            # find the lowest tq
            for f_ix, each_f in enumerate(gop_struct):
                min_tqval = min(node_and_tqlevel_dict.itervalues()) 
                
                nodes_with_min_tq = [k for k, v in node_and_tqlevel_dict.iteritems() if v == min_tqval]
                
                #print "taskMappingSchImpl_getFrameMapping_ShortestTQ :: num nodes with min tq" + str(len(nodes_with_min_tq))
                selected_node_id = nodes_with_min_tq[0]
                
                #selected_node_id = [k for k, v in node_and_tqlevel_dict.iteritems() if v == min_tqval][0]
                
                frames_mapping[f_ix] = selected_node_id # assign                
                node_and_tqlevel_dict[selected_node_id] = node_and_tqlevel_dict[selected_node_id]+1 # update dict
            
            self._map_to_vidstrm_mappingtbl(frames_mapping, wf_id, strm_id)
                
            return frames_mapping
        else:
            return None
    
    
    
        
    #####################################################################################
    # TASKMAPPINGSCHEMES_HIGHEST_THROUGHPUT
    #####################################################################################
    # find the node which has the highest number of completed tasks
    def taskMappingSchImpl_getFrameMapping_HighestThroughput(self, strm_specs):
        
        # get list of nodes that are free 
        free_nodes_list_ascorder = self.RM_instance.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL)        
        node_and_cttotal_dict = {}        
        # maintain a (node, tqlevel) dict internally (temp)
        for node in free_nodes_list_ascorder: 
            node_and_cttotal_dict[node.get_id()] = node.get_TotalCompletedTasks()
                
        if(len(free_nodes_list_ascorder)>0):
        
            wf_id = strm_specs['wf_id']
            strm_id = strm_specs['vid_strm_id']
            gop_struct = strm_specs['gop_struct']        
            frames_mapping = {}
            
            # find the node with highest completed tasks
            for f_ix, each_f in enumerate(gop_struct):
                max_tqval = max(node_and_cttotal_dict.itervalues()) 
                selected_node_id = [k for k, v in node_and_cttotal_dict.iteritems() if v == max_tqval][0]
                
                frames_mapping[f_ix] = selected_node_id # assign                
                node_and_cttotal_dict[selected_node_id] = node_and_cttotal_dict[selected_node_id]+1 # update dict
            
            self._map_to_vidstrm_mappingtbl(frames_mapping, wf_id, strm_id)
                
            return frames_mapping
        else:
            return None               
        
        
    #####################################################################################
    # TASKMAPPINGSCHEMES_LOWEST_THROUGHPUT
    #####################################################################################
    # find the node which has the lowest number of completed tasks
    def taskMappingSchImpl_getFrameMapping_LowestThroughput(self, strm_specs):
        
        # get list of nodes that are free 
        free_nodes_list_ascorder = self.RM_instance.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL)        
        node_and_cttotal_dict = {}        
        # maintain a (node, tqlevel) dict internally (temp)
        for node in free_nodes_list_ascorder: 
            node_and_cttotal_dict[node.get_id()] = node.get_TotalCompletedTasks()
                
        if(len(free_nodes_list_ascorder)>0):
        
            wf_id = strm_specs['wf_id']
            strm_id = strm_specs['vid_strm_id']
            gop_struct = strm_specs['gop_struct']        
            frames_mapping = {}
            
            # find the node with highest completed tasks
            for f_ix, each_f in enumerate(gop_struct):
                min_tqval = min(node_and_cttotal_dict.itervalues()) 
                selected_node_id = [k for k, v in node_and_cttotal_dict.iteritems() if v == min_tqval][0]
                
                frames_mapping[f_ix] = selected_node_id # assign                
                node_and_cttotal_dict[selected_node_id] = node_and_cttotal_dict[selected_node_id]+1 # update dict
            
                self._map_to_vidstrm_mappingtbl(frames_mapping, wf_id, strm_id)
                
            return frames_mapping
        else:
            return None
    
    
    #####################################################################################
    # TASKMAPPINGSCHEMES_LOWEST_REMAININGWCCC
    #####################################################################################
    # find the node which has the lowest total remaining computation cost (worst-case)
    def taskMappingSchImpl_getFrameMapping_LowestRemainingWCCC(self, strm_specs):
        
        # get list of nodes that are free 
        free_nodes_list_ascorder = self.RM_instance.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL)        
        node_and_totalremcc_dict = {}        
        # maintain a (node, tqlevel) dict internally (temp)
        for node in free_nodes_list_ascorder: 
            node_and_totalremcc_dict[node.get_id()] = node.get_WorstCaseTotalRemainingTaskExecutionTime()
                
        if(len(free_nodes_list_ascorder)>0):
        
            wf_id = strm_specs['wf_id']
            strm_id = strm_specs['vid_strm_id']
            gop_struct = strm_specs['gop_struct']        
            frames_mapping = {}
            
            # find the node with highest completed tasks
            for f_ix, each_f in enumerate(gop_struct):
                min_tqval = min(node_and_totalremcc_dict.itervalues()) 
                selected_node_id = [k for k, v in node_and_totalremcc_dict.iteritems() if v == min_tqval][0]
                
                frames_mapping[f_ix] = selected_node_id # assign                
                node_and_totalremcc_dict[selected_node_id] = node_and_totalremcc_dict[selected_node_id] + \
                                                                self._get_wcc_of_frame(f_ix, strm_specs) # update dict           
            
            self._map_to_vidstrm_mappingtbl(frames_mapping, wf_id, strm_id)
                
            return frames_mapping
        else:
            return None
        
        
    #####################################################################################
    # TASKMAPPINGSCHEMES_HIGHEST_REMAININGWCCC
    #####################################################################################
    # find the node which has the lowest total remaining computation cost (worst-case)
    def taskMappingSchImpl_getFrameMapping_HighestRemainingWCCC(self, strm_specs):
        
        # get list of nodes that are free 
        free_nodes_list_ascorder = self.RM_instance.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL)        
        node_and_totalremcc_dict = {}        
        # maintain a (node, tqlevel) dict internally (temp)
        for node in free_nodes_list_ascorder: 
            node_and_totalremcc_dict[node.get_id()] = node.get_WorstCaseTotalRemainingTaskExecutionTime()
                
        if(len(free_nodes_list_ascorder)>0):
        
            wf_id = strm_specs['wf_id']
            strm_id = strm_specs['vid_strm_id']
            gop_struct = strm_specs['gop_struct']        
            frames_mapping = {}
            
            # find the node with highest completed tasks
            for f_ix, each_f in enumerate(gop_struct):
                max_tqval = max(node_and_totalremcc_dict.itervalues()) 
                selected_node_id = [k for k, v in node_and_totalremcc_dict.iteritems() if v == max_tqval][0]
                
                frames_mapping[f_ix] = selected_node_id # assign                
                node_and_totalremcc_dict[selected_node_id] = node_and_totalremcc_dict[selected_node_id] + \
                                                                self._get_wcc_of_frame(f_ix, strm_specs) # update dict
            
            self._map_to_vidstrm_mappingtbl(frames_mapping, wf_id, strm_id)
                        
            return frames_mapping
        else:
            return None
            
    
    
    #####################################################################################
    # TASKMAPPINGSCHEMES_HYB_SHORTESTTQ_AND_LOWESTREMAININGWCCC
    #####################################################################################
    # node with the min amount of tasks in its tq is selected
    # if there are multiple nodes of the same size task queue, then the remaining 
    # computation cost (worst-case) is compared
        
    def taskMappingSchImpl_getFrameMapping_HybShortestTQAndLowestRemainingWCCC(self, strm_specs):
        # get list of nodes that are free 
        free_nodes_list_ascorder = self.RM_instance.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL)        
        node_and_tqstats_dict = {}        
        # maintain a (node, tqlevel) dict internally
        for node in free_nodes_list_ascorder: 
            node_and_tqstats_dict[node.get_id()] = {
                                                    'tq_level' : node.getTaskQ_level(),
                                                    'rem_total_cc' :  node.get_WorstCaseTotalRemainingTaskExecutionTime()
                                                    }            
                
        if(len(free_nodes_list_ascorder)>0):
        
            wf_id = strm_specs['wf_id']
            strm_id = strm_specs['vid_strm_id']
            gop_struct = strm_specs['gop_struct']        
            frames_mapping = {}
            
            # find the lowest tq, and if there are multiple of the same tq size, then we check the remaining cc
            for f_ix, each_f in enumerate(gop_struct):
                
                # first we find the nodes with min tq size
                min_tqval = min([v['tq_level'] for v in node_and_tqstats_dict.itervalues()])
                nodes_with_min_tq = {}
                for each_item_key, each_item_val in node_and_tqstats_dict.iteritems():
                    if (each_item_val['tq_level'] == min_tqval):
                        nodes_with_min_tq[each_item_key] = each_item_val
                        
                
                # now out of the results, we find the lowest remaining cc, and select this.
                if (len(nodes_with_min_tq) >0):
                    # we have more than one candidate, now we check for lowest_rem_cc
                    min_remcc =  min([v['rem_total_cc'] for v in nodes_with_min_tq.itervalues()])
                    nodes_with_min_tq_and_minremcc = [k for k, v in nodes_with_min_tq.iteritems() if v['rem_total_cc'] == min_remcc]
                    
                    selected_node_id = nodes_with_min_tq_and_minremcc[0]
                    frames_mapping[f_ix] = selected_node_id # assign                
                    node_and_tqstats_dict[selected_node_id]['tq_level'] = node_and_tqstats_dict[selected_node_id]['tq_level']+1 # update dict
                    node_and_tqstats_dict[selected_node_id]['rem_total_cc'] = node_and_tqstats_dict[selected_node_id]['rem_total_cc'] + \
                                                                            self._get_wcc_of_frame(f_ix, strm_specs) # update dict
              
            
            # copy selection to vidstream mapping table
            self._map_to_vidstrm_mappingtbl(frames_mapping, wf_id, strm_id)
                
            return frames_mapping
        else:
            return None 
        
    
    #####################################################################################
    # TASKMAPPINGSCHEMES_HYB_SHORTESTTQ_AND_LOWESTREMAININGAVGCCC
    #####################################################################################
    # node with the min amount of tasks in its tq is selected
    # if there are multiple nodes of the same size task queue, then the remaining 
    # computation cost (worst-case) is compared
    def taskMappingSchImpl_getFrameMapping_HybShortestTQAndLowestRemainingAvgCCC(self, strm_specs):
        
        # get list of nodes that are free 
        free_nodes_list_ascorder = self.RM_instance.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL)        
        node_and_tqstats_dict = {}        
        # maintain a (node, tqlevel) dict internally
        for node in free_nodes_list_ascorder: 
            node_and_tqstats_dict[node.get_id()] = {
                                                    'tq_level' : node.getTaskQ_level(),
                                                    'rem_total_cc' :  node.get_AvgCaseTotalRemainingTaskExecutionTime()
                                                    }            
                
        if(len(free_nodes_list_ascorder)>0):
        
            wf_id = strm_specs['wf_id']
            strm_id = strm_specs['vid_strm_id']
            gop_struct = strm_specs['gop_struct']        
            frames_mapping = {}
            
            # find the lowest tq, and if there are multiple of the same tq size, then we check the remaining cc
            for f_ix, each_f in enumerate(gop_struct):
                
                # first we find the nodes with min tq size
                min_tqval = min([v['tq_level'] for v in node_and_tqstats_dict.itervalues()])
                nodes_with_min_tq = {}
                for each_item_key, each_item_val in node_and_tqstats_dict.iteritems():
                    if (each_item_val['tq_level'] == min_tqval):
                        nodes_with_min_tq[each_item_key] = each_item_val
                        
                
                # now out of the results, we find the lowest remaining cc, and select this.
                if (len(nodes_with_min_tq) >0):
                    # we have more than one candidate, now we check for lowest_rem_cc
                    min_remcc =  min([v['rem_total_cc'] for v in nodes_with_min_tq.itervalues()])
                    nodes_with_min_tq_and_minremcc = [k for k, v in nodes_with_min_tq.iteritems() if v['rem_total_cc'] == min_remcc]
                    
                    selected_node_id = nodes_with_min_tq_and_minremcc[0]
                    frames_mapping[f_ix] = selected_node_id # assign                
                    node_and_tqstats_dict[selected_node_id]['tq_level'] = node_and_tqstats_dict[selected_node_id]['tq_level']+1 # update dict
                    node_and_tqstats_dict[selected_node_id]['rem_total_cc'] = node_and_tqstats_dict[selected_node_id]['rem_total_cc'] + \
                                                                            self._get_avgcc_of_frame(f_ix, strm_specs) # update dict
              
            
            # copy selection to vidstream mapping table
            self._map_to_vidstrm_mappingtbl(frames_mapping, wf_id, strm_id)
                
            return frames_mapping
        else:
            return None
    
    
    #####################################################################################
    # TASKMAPPINGSCHEMES_HYB_SHORTESTTQ_AND_RANDOM
    #####################################################################################
    # node with the min amount of tasks in its tq is selected
    # if there are multiple nodes of the same size task queue, then a node is selected at random
    def taskMappingSchImpl_getFrameMapping_HybShortestTQAndRandom(self, strm_specs):
        
        # get list of nodes that are free 
        free_nodes_list_ascorder = self.RM_instance.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL)        
        node_and_tqstats_dict = {}        
        # maintain a (node, tqlevel) dict internally
        for node in free_nodes_list_ascorder: 
            node_and_tqstats_dict[node.get_id()] = {
                                                    'tq_level' : node.getTaskQ_level(),                                                    
                                                    }            
                
        if(len(free_nodes_list_ascorder)>0):
        
            wf_id = strm_specs['wf_id']
            strm_id = strm_specs['vid_strm_id']
            gop_struct = strm_specs['gop_struct']        
            frames_mapping = {}
            
            # find the lowest tq, and if there are multiple of the same tq size, then we check the remaining cc
            for f_ix, each_f in enumerate(gop_struct):
                
                # first we find the nodes with min tq size
                min_tqval = min([v['tq_level'] for v in node_and_tqstats_dict.itervalues()])
                nodes_with_min_tq = {}
                for each_item_key, each_item_val in node_and_tqstats_dict.iteritems():
                    if (each_item_val['tq_level'] == min_tqval):
                        nodes_with_min_tq[each_item_key] = each_item_val                        
                
                # now out of the results, we find the lowest remaining cc, and select this.
                if (len(nodes_with_min_tq) >0):
                    # we have more than one candidate, now we select one randomly                    
                    selected_node_id = random.choice(nodes_with_min_tq.keys())
                    frames_mapping[f_ix] = selected_node_id # assign                
                    node_and_tqstats_dict[selected_node_id]['tq_level'] = node_and_tqstats_dict[selected_node_id]['tq_level']+1 # update dict              
            
            # copy selection to vidstream mapping table
            self._map_to_vidstrm_mappingtbl(frames_mapping, wf_id, strm_id)
                
            return frames_mapping
        else:
            return None
        
        
    #####################################################################################
    # TASKMAPPINGSCHEMES_LOWEST_UTILISATION
    #####################################################################################
    # node with the lowest utilisation - wrt to the information in the runtimeapp
    def taskMappingSchImpl_getFrameMapping_LowestUtil(self, strm_specs):
        
        # get list of nodes that are free 
        free_nodes_list_ascorder = self.RM_instance.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL)        
        local_nodespecific_info = OrderedDict()        
        
        all_node_utils = self.RM_instance.RunTimeApps.getNodeEstimatedUtilisation()
        
        # populate node specific task info
        for each_node in free_nodes_list_ascorder:            
            node_id = each_node.get_id()
            if (node_id not in local_nodespecific_info):
            
                local_nodespecific_info[node_id] = {                                                               
                                                   'NodeObj' :  each_node,                                                   
                                                   ## tasks existing and mapped on to this node according to the RM:runtimeapp logger ##
                                                   'RMAppMappedTasks' : [ task for task in self.RM_instance.RunTimeApps.getTasks() \
                                                                         if (task.get_processingCore() == node_id) ],                                                    
                                                    'RMAppMappedTasks_nodeUtil' :   all_node_utils[node_id],                                                    
                                                   ## tasks currently in the node tq ##
                                                   'NodeTQ' : [t for t in each_node.get_TaskQueue()],                                                                           
                                                   }
        
        if(len(free_nodes_list_ascorder)>0):
            
            wf_id = strm_specs['wf_id']
            strm_id = strm_specs['vid_strm_id']
            gop_struct = strm_specs['gop_struct']        
            frames_mapping = {}
            
            # for each frame, go through each node and evaluate the cost-function
            # then select mapping accordingly        
            for fr_ix, each_f in enumerate(gop_struct):
                
                lowest_node_util = min([v['RMAppMappedTasks_nodeUtil'] for k,v in local_nodespecific_info.iteritems()])                
                nodesids_with_lowest_util = [k for k,v in local_nodespecific_info.iteritems() if v['RMAppMappedTasks_nodeUtil'] == lowest_node_util]
                selected_node_id = nodesids_with_lowest_util[0]

                # assign
                frames_mapping[fr_ix] = selected_node_id
                ## update dict ##
                pseudo_task = self._get_pseudo_task(fr_ix, -1, selected_node_id, strm_specs )
                pseudo_task_util = float(pseudo_task.get_worstCaseComputationCost()/pseudo_task.get_period())
                local_nodespecific_info[selected_node_id]['RMAppMappedTasks'].append(pseudo_task)                
                local_nodespecific_info[selected_node_id]['NodeTQ'].append(pseudo_task)                
                local_nodespecific_info[selected_node_id]['RMAppMappedTasks_nodeUtil'] += pseudo_task_util
                
            self._map_to_vidstrm_mappingtbl(frames_mapping, wf_id, strm_id)                    
            return frames_mapping
        else:
            return None
    
    #####################################################################################
    # TASKMAPPINGSCHEMES_LOWEST_UTILISATION_NEARESTPARENT
    #####################################################################################
    # node with the lowest utilisation - wrt to the information in the runtimeapp
    def taskMappingSchImpl_getFrameMapping_LowestUtilNearestParent(self, strm_specs):
        
        # get list of nodes that are free 
        free_nodes_list_ascorder = self.RM_instance.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL)        
        local_nodespecific_info = {}        
        
        all_node_utils = self.RM_instance.RunTimeApps.getNodeEstimatedUtilisation()
        
        # populate node specific task info
        for each_node in free_nodes_list_ascorder:            
            node_id = each_node.get_id()
            if (node_id not in local_nodespecific_info):
            
                local_nodespecific_info[node_id] = {                                                               
                                                   'NodeObj' :  each_node,                                                   
                                                   ## tasks existing and mapped on to this node according to the RM:runtimeapp logger ##
                                                   'RMAppMappedTasks' : [ task for task in self.RM_instance.RunTimeApps.getTasks() \
                                                                         if (task.get_processingCore() == node_id) ],                                                    
                                                    'RMAppMappedTasks_nodeUtil' :   all_node_utils[node_id],                                                    
                                                   ## tasks currently in the node tq ##
                                                   'NodeTQ' : [t for t in each_node.get_TaskQueue()],                                                                           
                                                   }
        
        if(len(free_nodes_list_ascorder)>0):
            
            wf_id = strm_specs['wf_id']
            strm_id = strm_specs['vid_strm_id']
            gop_struct = strm_specs['gop_struct']        
            frames_mapping = {}
            
            # for each frame, go through each node and evaluate the cost-function
            # then select mapping accordingly        
            for fr_ix, each_f in enumerate(gop_struct):
                
                lowest_node_util = min([v['RMAppMappedTasks_nodeUtil'] for k,v in local_nodespecific_info.iteritems()])                
                nodesids_with_lowest_util = [k for k,v in local_nodespecific_info.iteritems() if v['RMAppMappedTasks_nodeUtil'] == lowest_node_util]
                    
                # if I-frame treat different, if another frame, we have a choice
                closest_parent_frix_in_dag = self._get_pseudo_task(fr_ix, -1, 0, strm_specs ).get_my_closest_parent()
                if(closest_parent_frix_in_dag == None):
                    selected_node_id = nodesids_with_lowest_util[0] # don't care which node
                else:       
                    # if we have many nodes with same util levels, then compare route costs
                    if(len(nodesids_with_lowest_util) > 0):
                        node_route_len = {}
                        for each_node_id in nodesids_with_lowest_util:                                
                            route = self.RM_instance.interconnect.getRouteHopCount(frames_mapping[closest_parent_frix_in_dag], each_node_id)
                            node_route_len[each_node_id] = len(route)
                        
                        min_route_len = min([v for k,v in node_route_len.iteritems()]) 
                        selected_node_id = [k for k,v in node_route_len.iteritems() if v == min_route_len][0]
                                
                    else:
                        selected_node_id = nodesids_with_lowest_util[0]
                
                
                
                #selected_node_id = nodesids_with_lowest_util[0]
   
                # assign
                frames_mapping[fr_ix] = selected_node_id
                ## update dict ##
                pseudo_task = self._get_pseudo_task(fr_ix, -1, selected_node_id, strm_specs )
                pseudo_task_util = float(pseudo_task.get_worstCaseComputationCost()/pseudo_task.get_period())
                local_nodespecific_info[selected_node_id]['RMAppMappedTasks'].append(pseudo_task)                
                local_nodespecific_info[selected_node_id]['NodeTQ'].append(pseudo_task)                
                local_nodespecific_info[selected_node_id]['RMAppMappedTasks_nodeUtil'] += pseudo_task_util
                
            self._map_to_vidstrm_mappingtbl(frames_mapping, wf_id, strm_id)                    
            return frames_mapping
        else:
            return None
    
    #####################################################################################
    # TASKMAPPINGSCHEMES_CUSTOM_LOADFROMFILE
    #####################################################################################
    def taskMappingSchImpl_getFrameMapping_CustomLoadFromFile(self, strm_specs):
                
        #fname = SimParams.DYNAMIC_TASK_MAPPING_FROMFILE_FNAME
        
        
        # get cc
        cc=0
        for res in SimParams.DVB_RESOLUTIONS_FIXED:
            cc += res[0] *  res[1]
        
        num_wfs = SimParams.NUM_WORKFLOWS
        noc_h = SimParams.NOC_H
        noc_w = SimParams.NOC_W   
        noc_size = str(noc_h) + "x" + str(noc_w) 
        s = 1234    
        wfgen_random_seed = self.RM_instance.get_initrandomseed()
        
        
        dir = "MOGATestbenches/best_sols/"
        
#         fname = dir + "HdVidTestbench_" + str(noc_h) + "x" + str(noc_w) + "_s" + str(s) + "_" + \
#                 "wfs" + str(num_wfs) + "_cc" + str(cc) + "_bestsol.txt" 
         
        fname = dir + "HRT_Mapping_results_summary.js"
        
        # get task mappings 
        mappings_by_line = []
        json_data=open(fname)
        file_data = json.load(json_data)
        for each_entry_k, each_entry_v in file_data.iteritems():
            if ((each_entry_v['cc'] == cc) and 
                (each_entry_v['noc_size'] == noc_size) and
                (each_entry_v['seed'] == wfgen_random_seed)):
                    mappings_by_line = each_entry_v['best_sol_mapping']  
                    print "taskMappingSchImpl_getFrameMapping_CustomLoadFromFile:: found custom mapping!!"
                    break      
        
        if len(mappings_by_line) == 0:
            sys.exit("taskMappingSchImpl_getFrameMapping_CustomLoadFromFile:: mappings_by_line = 0")
            
        
        #print "taskMappingSchImpl_getFrameMapping_CustomLoadFromFile"
        # build mapping table - for all videos
        custom_mapping_table = OrderedDict()
        
#         print "--"
#         pprint.pprint(mappings_by_line)
#         print "--"
        
        for each_line in mappings_by_line:
            row = each_line.split(',')
            task_name = row[0]
            xpos = int(row[1])  
            ypos = int(row[2])
            
            # split into wf, strmid, gopix
            [t, wfid, strmid, gopix] = task_name.split("_")
            
            wfid = int(wfid)
            strmid = int(strmid)
            gopix = int(gopix)
            
            if wfid not in custom_mapping_table:
                custom_mapping_table[wfid] = OrderedDict()
                custom_mapping_table[wfid][strmid]= OrderedDict()
                custom_mapping_table[wfid][strmid][gopix] = self.RM_instance.interconnect.getNodeIdByXYPos(xpos, ypos)
            else:
                if strmid not in custom_mapping_table[wfid]:                        
                    custom_mapping_table[wfid][strmid]= OrderedDict()
                    custom_mapping_table[wfid][strmid][gopix] = self.RM_instance.interconnect.getNodeIdByXYPos(xpos, ypos)
                else:
                    custom_mapping_table[wfid][strmid][gopix] = self.RM_instance.interconnect.getNodeIdByXYPos(xpos, ypos)
            
            
            # debug #
            #print "t_", wfid, strmid, gopix, " : ",  custom_mapping_table[wfid][strmid][gopix]            
            # debug #
                
        #print "---------------"        
        #print(json.dumps(custom_mapping_table, indent=4))
                        
        # apply mapping for this video stream
        wf_id = strm_specs['wf_id']
        strm_id = strm_specs['vid_strm_id']
        gop_struct = strm_specs['gop_struct']        
        frames_mapping = {}        
        
        for fr_ix, each_f in enumerate(gop_struct):
            try :
                frames_mapping[fr_ix] = custom_mapping_table[wf_id][strm_id][fr_ix]
            except Exception, e:
                emsg = sys.exc_info()[0]
                print e
                print traceback.format_exc()
                sys.exit("Error :: taskMappingSchImpl_getFrameMapping_CustomLoadFromFile")        
        
        self._map_to_vidstrm_mappingtbl(frames_mapping, wf_id, strm_id)
        return frames_mapping
    
    
    #####################################################################################
    #####################################################################################
    # HELPER functions
    #####################################################################################
    def _map_to_vidstrm_mappingtbl(self, frames_mapping, wf_id, strm_id):
        if wf_id in self.RM_instance.vidstream_frames_mapping_table:            
            if(strm_id not in self.RM_instance.vidstream_frames_mapping_table[wf_id]):
                self.RM_instance.vidstream_frames_mapping_table[wf_id][strm_id] = {}
                self.RM_instance.vidstream_frames_mapping_table[wf_id][strm_id]['frames_mapping'] = frames_mapping
        else:
            self.RM_instance.vidstream_frames_mapping_table[wf_id] = {}
            self.RM_instance.vidstream_frames_mapping_table[wf_id][strm_id] = {}
            self.RM_instance.vidstream_frames_mapping_table[wf_id][strm_id]['frames_mapping'] = frames_mapping
                
#        
#        print "---"
#        pprint.pprint(frames_mapping)
#        pprint.pprint(self.RM_instance.vidstream_frames_mapping_table)            
#        print "---"
#            
    def _get_wcc_of_frame(self, frame_ix, strm_specs):
        frame_type = strm_specs['gop_struct'][frame_ix]
        
        if (frame_type == "I"):
            wcc = strm_specs['wcc_I']
        elif (frame_type == "P"):
            wcc = strm_specs['wcc_P']
        elif (frame_type == "B"):
            wcc = strm_specs['wcc_B']
        else:
            sys.exit("TaskMappingSchemesImpl:: _get_wcc_of_frame:: Error")
        
        return wcc
    
    def _get_avgcc_of_frame(self, frame_ix, strm_specs):
        frame_type = strm_specs['gop_struct'][frame_ix]
        
        if (frame_type == "I"):
            avgcc = strm_specs['avgcc_I']
        elif (frame_type == "P"):
            avgcc = strm_specs['avgcc_P']
        elif (frame_type == "B"):
            avgcc = strm_specs['avgcc_B']
        else:
            sys.exit("TaskMappingSchemesImpl:: _get_wcc_of_frame:: Error")
        
        return avgcc
    
    
    
    
    
    def _get_pseudo_task(self, ix, pri, node_id, strm_specs, tid=0):
        
        pseudo_task = None
        
        if (SimParams.TASK_MODEL == TaskModel.TASK_MODEL_MHEG2_FRAME_ET_LEVEL):
            pseudo_task = MPEG2FrameTask(self.env, tid,
                 frame_h = strm_specs['frame_h'], frame_w = strm_specs['frame_w'],
                 frame_rate = strm_specs['fps'],
                 frame_type = strm_specs['gop_struct'][ix],
                 frame_ix_in_gop = ix,
                 gop_struct = strm_specs['gop_struct'],
                 video_stream_id = strm_specs['vid_strm_id'],
                 wf_id = strm_specs['wf_id'])
                
            pseudo_task.set_processingCore(node_id)
            pseudo_task.set_priority(pri)
            pseudo_task.set_worstCaseComputationCost(self._get_wcc_of_frame(ix, strm_specs))
            pseudo_task.set_avgCaseComputationCost(self._get_avgcc_of_frame(ix, strm_specs))        
            pseudo_task.set_period(pseudo_task.get_end_to_end_deadline())
        
        elif (SimParams.TASKSET_MODEL in [TaskModel.TASK_MODEL_HEVC_FRAME_LEVEL,TaskModel.TASK_MODEL_HEVC_TILE_LEVEL] ):            
            pseudo_task = HEVCFrameTask(env = self.env,                                   
                                    id = tid,
                                    frame_type = strm_specs['gop_struct'][ix],
                                    frame_ix_in_gop = ix,                                    
                                    gop_struct = strm_specs['gop_struct'],
                                    video_stream_id = strm_specs['vid_strm_id'],
                                    wf_id = strm_specs['wf_id'],
                                    frame_h = strm_specs['frame_h'], frame_w = strm_specs['frame_w'],
                                    priority = pri,
                                    num_slices_per_frame = -1,
                                    num_tiles_per_frame =  -1,
                                    interleaved_slice_types = ["Is", "Bs", "Bs" , "Ps"],
                                    num_ctu_per_slice=-1,
                                    adaptiveGoP_Obj=None,     
                                    load_data_from_file = False,
                                    construct_partitions = False,
                                    hevc_cc=0.0                                       
                                    )
            
            pseudo_task.set_processingCore(node_id)
            pseudo_task.set_priority(pri)
            pseudo_task.set_worstCaseComputationCost(self._get_wcc_of_frame(ix, strm_specs))
            pseudo_task.set_avgCaseComputationCost(self._get_avgcc_of_frame(ix, strm_specs))        
            pseudo_task.set_period(pseudo_task.get_end_to_end_deadline())
        
                
        return pseudo_task

        
        