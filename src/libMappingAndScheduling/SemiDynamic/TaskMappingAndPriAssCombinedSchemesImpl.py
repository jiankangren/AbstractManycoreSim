import pprint
import sys
import itertools
import simpy
import copy
import random
from operator import itemgetter
import numpy as np
from collections import OrderedDict

from SimParams import SimParams
from TaskMappingSchemes import TaskMappingSchemes
from TaskSemiDynamicPrioritySchemes import TaskSemiDynamicPrioritySchemes
from TaskMappingAndPriAssCombinedSchemes import TaskMappingAndPriAssCombinedSchemes
from TaskMappingSchemesImpl import TaskMappingSchemesImpl
from TaskSemiDynamicPrioritySchemesImpl import TaskSemiDynamicPrioritySchemesImpl
from libApplicationModel.MPEG2FrameTask import MPEG2FrameTask
from libNoCModel.NoCFlow import NoCFlow
from libApplicationModel.HEVCFrameTask import HEVCFrameTask
from libApplicationModel.Task import TaskModel

# once a stream has entered the system, the frames of the GoPs are mapped. 
# this mapping is fixed throughout the lifetime of the video stream
class TaskMappingAndPriAssCombinedSchemesImpl:

    def __init__(self, env, RM_instance):  
        self.env = env
        self.RM_instance = RM_instance
    
    
    def taskMappPriAssCombinedSchemeHandler(self, strm_specs):
        
        ## related to impact scoring ##
        if SimParams.COMBINED_MAPPING_AND_PRIASS == TaskMappingAndPriAssCombinedSchemes.TASKMAPPINGANDPRIASSCOMBINED_IMPACTSCORING_V1:
            (result1, result2) =  self.taskMappPriAssCombinedSchImpl_getFrameMnP_ImpactScoring_V1(strm_specs)
                    
        elif SimParams.COMBINED_MAPPING_AND_PRIASS == TaskMappingAndPriAssCombinedSchemes.TASKMAPPINGANDPRIASSCOMBINED_IMPACTSCORING_V2:
            (result1, result2) =  self.taskMappPriAssCombinedSchImpl_getFrameMnP_ImpactScoring_V2(strm_specs)
            
        elif SimParams.COMBINED_MAPPING_AND_PRIASS == TaskMappingAndPriAssCombinedSchemes.TASKMAPPINGANDPRIASSCOMBINED_IMPACTSCORING_V3:            
            (result1, result2) =  self.taskMappPriAssCombinedSchImpl_getFrameMnP_ImpactScoring_V3(strm_specs)        
        
        ## related to shortest tq first ##
        elif SimParams.COMBINED_MAPPING_AND_PRIASS == TaskMappingAndPriAssCombinedSchemes.TASKMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_SHRTQFIRST_LEASTBLTIME_V1:            
            (result1, result2) =  self.taskMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPShrTQwithBlTime_V1(strm_specs)        
        
        ## related to response time ##
        elif SimParams.COMBINED_MAPPING_AND_PRIASS == TaskMappingAndPriAssCombinedSchemes.TASKMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_LEASERESPTIMEANDCONGESTED_V1:            
            (result1, result2) =  self.taskMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPLeastRespTimeAndCongested(strm_specs)        
      
        ## related to nearest-neighbour ##
        elif SimParams.COMBINED_MAPPING_AND_PRIASS == TaskMappingAndPriAssCombinedSchemes.TASKMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_NNWITHLEASTBLOCKING_V1:            
            (result1, result2) =  self.taskMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPNNWithLeastBlocking(strm_specs)        
                
        elif SimParams.COMBINED_MAPPING_AND_PRIASS == TaskMappingAndPriAssCombinedSchemes.TASKMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_CARVALHO_BN:
            (result1, result2) =  self.taskMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPCarvalho_BN(strm_specs)    
        
        elif SimParams.COMBINED_MAPPING_AND_PRIASS == TaskMappingAndPriAssCombinedSchemes.TASKMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_CARVALHO_BN_V2:
            (result1, result2) =  self.taskMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPCarvalho_BN_V2(strm_specs)
            
        elif SimParams.COMBINED_MAPPING_AND_PRIASS == TaskMappingAndPriAssCombinedSchemes.TASKMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_KAUSHIK_PP:            
            (result1, result2) =  self.taskMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPKaushik_PP(strm_specs)    
        
        
        ## related to nearest-neighbour ##
        elif SimParams.COMBINED_MAPPING_AND_PRIASS == TaskMappingAndPriAssCombinedSchemes.TASKMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_NNLEASTUTILISED_TOPNPERCENT:            
            (result1, result2) =  self.taskMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPNNWithLeastUtilised_TopNPercent(strm_specs)        
              
      
        ## hrt-video related ##
        elif SimParams.COMBINED_MAPPING_AND_PRIASS == TaskMappingAndPriAssCombinedSchemes.TASKMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_LOWCOMMUNICATION_V1:                       
            (result1, result2) =  self.taskMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPLowComms_V1(strm_specs) 
        
        elif SimParams.COMBINED_MAPPING_AND_PRIASS == TaskMappingAndPriAssCombinedSchemes.TASKMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_LOWCOMMUNICATION_V2:                                   
            (result1, result2) =  self.taskMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPLowComms_V2(strm_specs) 
        
        elif SimParams.COMBINED_MAPPING_AND_PRIASS == TaskMappingAndPriAssCombinedSchemes.TASKMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_TIGHTFIT_V1:                       
            (result1, result2) =  self.taskMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPTightFit_V1(strm_specs)   
        
        
        ## all tasks on a single node ##
        elif SimParams.COMBINED_MAPPING_AND_PRIASS == TaskMappingAndPriAssCombinedSchemes.TASKMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_SINGLENODE_LOWEST_UTIL:                       
            (result1, result2) =  self.taskMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPSingleCore_LowestUtil(strm_specs)   

        
        ## low res pri, random mapping ##        
        elif SimParams.COMBINED_MAPPING_AND_PRIASS == TaskMappingAndPriAssCombinedSchemes.TASKMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_RANDOMMAPPING:                       
            (result1, result2) =  self.taskMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPRandom(strm_specs)   
            
        elif(SimParams.COMBINED_MAPPING_AND_PRIASS == TaskMappingAndPriAssCombinedSchemes.TASKMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_MOSTSLACK_VIA_VTMTBL):            
            (result1, result2) =  self.taskMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPMostSlack_ViaTMTBL(strm_specs)

        else:
            sys.exit("taskMappPriAssCombinedSchemeHandler:: Error: unknown MP scheme")
            
        
        return (result1, result2)
    
    
    
    #####################################################################################
    # TASKMAPPINGANDPRIASSCOMBINED_IMPACTSCORING_V1
    #####################################################################################
    # first the vid stream is assigned a frame-level semi-dynamic priority scheme
    # (PR: lowest res first)
    # then an impact based cost function is applied to each node
    # - impact on self AND others
    # the node with the lowest cost function result gets chosen
    def taskMappPriAssCombinedSchImpl_getFrameMnP_ImpactScoring_V1(self, strm_specs):
        
        # build pseudo frame-mappings dict
        empty_frame_mappings = self._get_empty_frame_mappings_dict(strm_specs)
        
        # get frame level priorities
        frame_priorities = self.RM_instance.taskPriAssigner.taskSemiDynPriSch_getFramePriority_LowestResFirst(strm_specs, empty_frame_mappings)
                     
        # get list of nodes that are free 
        free_nodes_list = self.RM_instance.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL)
        
        wf_id = strm_specs['wf_id']
        strm_id = strm_specs['vid_strm_id']
        gop_struct = strm_specs['gop_struct']        
        frames_mapping_priass_combined = {} # final combined frame level mapping and tq priorities 
        local_nodespecific_info = {}    # tasks mapped according to RM_strm_mapping_table, live tq info etc.
        
        if len(free_nodes_list) > 0:
        
            # populate node specific task info
            for each_node in free_nodes_list:            
                node_id = each_node.get_id()
                if (node_id not in local_nodespecific_info):
                
                    local_nodespecific_info[node_id] = {                                                               
                                                       'NodeObj' :  each_node,
                                                       
                                                       ## tasks existing and mapped on to this node according to the RM:runtimeapp logger ##
                                                       'RMAppMappedTasks' : [ task for task in self.RM_instance.RunTimeApps.getTasks() \
                                                                             if (task.get_processingCore() == node_id) ],
                                                        
                                                       ## tasks currently in the node tq ##
                                                       'NodeTQ' : [t for t in each_node.get_TaskQueue()],
                                                       
                                                       ## tasks currently in the input buffers ##
                                                       'IBuffs' : self._get_tasks_from_ibuffs(node_id)                                                                      
                                                       }
            
            # for each frame, go through each node and evaluate the cost-function
            # then select mapping accordingly        
            for fr_ix, each_f in enumerate(gop_struct):
                node_and_costfunction_dict = {}            
                fr_pri = frame_priorities[fr_ix]
                
                for node_key, node_val in local_nodespecific_info.iteritems():
                    
                    # calculate the cost function based on impact
                    # to_self     : impact factor to the target task by this mapping
                    # to_others   : impact factor to other tasks by this mapping 
                    node_costfunc = self._get_factor_impact_to_self(node_val, fr_pri, fr_ix, strm_specs, cc_type="avgccc") + \
                                    self._get_factor_impact_to_others(node_val, fr_pri, fr_ix, strm_specs)
                                
                    if node_key not in node_and_costfunction_dict:
                        node_and_costfunction_dict[node_key] = node_costfunc
                
                # now make the selection
                min_cf =  min(node_and_costfunction_dict.itervalues())
                selected_node_id = [k for k,v in node_and_costfunction_dict.iteritems() if v == min_cf][0]
                
                # assign
                frames_mapping_priass_combined[fr_ix] = selected_node_id
                ## update dict ##
                pseudo_task = self._get_pseudo_task(fr_ix, fr_pri, selected_node_id, strm_specs )
                local_nodespecific_info[selected_node_id]['RMAppMappedTasks'].append(pseudo_task)
                #local_nodespecific_info[selected_node_id]['IBuffs'].append(pseudo_task)
                local_nodespecific_info[selected_node_id]['NodeTQ'].append(pseudo_task)
                
            self._map_to_vidstrm_mappingtbl(frames_mapping_priass_combined, wf_id, strm_id)                
            return (frames_mapping_priass_combined, frame_priorities)
                
        else:
            return (None, None)
            
    
    
    #####################################################################################
    # TASKMAPPINGANDPRIASSCOMBINED_IMPACTSCORING_V2
    #####################################################################################
    # first the vid stream is assigned a frame-level semi-dynamic priority scheme
    # (PR: lowest res first)
    # then an impact based cost function is applied to each node
    # - impact only to self
    # the node with the lowest cost function result gets chosen
    def taskMappPriAssCombinedSchImpl_getFrameMnP_ImpactScoring_V2(self, strm_specs):
        
        # build pseudo frame-mappings dict
        empty_frame_mappings = self._get_empty_frame_mappings_dict(strm_specs)
        
        # get frame level priorities
        frame_priorities = self.RM_instance.taskPriAssigner.taskSemiDynPriSch_getFramePriority_LowestResFirst(strm_specs, empty_frame_mappings)
                     
        # get list of nodes that are free 
        free_nodes_list = self.RM_instance.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL)
        
        wf_id = strm_specs['wf_id']
        strm_id = strm_specs['vid_strm_id']
        gop_struct = strm_specs['gop_struct']        
        frames_mapping_priass_combined = {} # final combined frame level mapping and tq priorities 
        local_nodespecific_info = {}    # tasks mapped according to RM_strm_mapping_table, live tq info etc.
        
        if len(free_nodes_list) > 0:
        
            # populate node specific task info
            for each_node in free_nodes_list:            
                node_id = each_node.get_id()
                if (node_id not in local_nodespecific_info):
                
                    local_nodespecific_info[node_id] = {                                                               
                                                       'NodeObj' :  each_node,
                                                       
                                                       ## tasks existing and mapped on to this node according to the RM:runtimeapp logger ##
                                                       'RMAppMappedTasks' : [ task for task in self.RM_instance.RunTimeApps.getTasks() \
                                                                             if (task.get_processingCore() == node_id) ],
                                                        
                                                       ## tasks currently in the node tq ##
                                                       'NodeTQ' : [t for t in each_node.get_TaskQueue()],
                                                       
                                                       ## tasks currently in the input buffers ##
                                                       'IBuffs' : self._get_tasks_from_ibuffs(node_id)                                                                      
                                                       }
            
            # for each frame, go through each node and evaluate the cost-function
            # then select mapping accordingly        
            for fr_ix, each_f in enumerate(gop_struct):
                node_and_costfunction_dict = {}            
                fr_pri = frame_priorities[fr_ix]
                
                for node_key, node_val in local_nodespecific_info.iteritems():
                    
                    # calculate the cost function based on impact
                    # to_self     : impact factor to the target task by this mapping
                    # to_others   : impact factor to other tasks by this mapping 
                    node_costfunc = self._get_factor_impact_to_self(node_val, fr_pri, fr_ix, strm_specs,cc_type="avgccc")
                                
                    if node_key not in node_and_costfunction_dict:
                        node_and_costfunction_dict[node_key] = node_costfunc
                
                # now make the selection
                min_cf =  min(node_and_costfunction_dict.itervalues())
                selected_node_id = [k for k,v in node_and_costfunction_dict.iteritems() if v == min_cf][0]
                
                # assign
                frames_mapping_priass_combined[fr_ix] = selected_node_id
                ## update dict ##
                pseudo_task = self._get_pseudo_task(fr_ix, fr_pri, selected_node_id, strm_specs )
                local_nodespecific_info[selected_node_id]['RMAppMappedTasks'].append(pseudo_task)
                #local_nodespecific_info[selected_node_id]['IBuffs'].append(pseudo_task)
                local_nodespecific_info[selected_node_id]['NodeTQ'].append(pseudo_task)
                
            self._map_to_vidstrm_mappingtbl(frames_mapping_priass_combined, wf_id, strm_id)
                
            return (frames_mapping_priass_combined, frame_priorities)
                
        else:
            return (None, None)
            
    
    #####################################################################################
    # TASKMAPPINGANDPRIASSCOMBINED_IMPACTSCORING_V3
    #####################################################################################
    # first the vid stream is assigned a frame-level semi-dynamic priority scheme
    # (PR: lowest res first)
    # then an impact based cost function is applied to each node
    # - impact only to self, only accounting for nodeTQ blocking time and Ibuff waiting time
    # the node with the lowest cost function result gets chosen
    def taskMappPriAssCombinedSchImpl_getFrameMnP_ImpactScoring_V3(self, strm_specs):
        
        # build pseudo frame-mappings dict
        empty_frame_mappings = self._get_empty_frame_mappings_dict(strm_specs)
        
        # get frame level priorities
        frame_priorities = self.RM_instance.taskPriAssigner.taskSemiDynPriSch_getFramePriority_LowestResFirst(strm_specs, empty_frame_mappings)
                     
        # get list of nodes that are free 
        free_nodes_list = self.RM_instance.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL)
        
        wf_id = strm_specs['wf_id']
        strm_id = strm_specs['vid_strm_id']
        gop_struct = strm_specs['gop_struct']        
        frames_mapping_priass_combined = {} # final combined frame level mapping and tq priorities 
        local_nodespecific_info = {}    # tasks mapped according to RM_strm_mapping_table, live tq info etc.
        
        if len(free_nodes_list) > 0:
        
            # populate node specific task info
            for each_node in free_nodes_list:            
                node_id = each_node.get_id()
                if (node_id not in local_nodespecific_info):
                
                    local_nodespecific_info[node_id] = {                                                               
                                                       'NodeObj' :  each_node,
                                                       
                                                       ## tasks existing and mapped on to this node according to the RM:runtimeapp logger ##
                                                       'RMAppMappedTasks' : [ task for task in self.RM_instance.RunTimeApps.getTasks() \
                                                                             if (task.get_processingCore() == node_id) ],
                                                        
                                                       ## tasks currently in the node tq ##
                                                       'NodeTQ' : [t for t in each_node.get_TaskQueue()],
                                                       
                                                       ## tasks currently in the input buffers ##
                                                       'IBuffs' : self._get_tasks_from_ibuffs(node_id)                                                                      
                                                       }
            
            # for each frame, go through each node and evaluate the cost-function
            # then select mapping accordingly        
            for fr_ix, each_f in enumerate(gop_struct):
                node_and_costfunction_dict = {}            
                fr_pri = frame_priorities[fr_ix]
                
                for node_key, node_val in local_nodespecific_info.iteritems():
                    
                    # calculate the cost function based on impact
                    # to_self     : impact factor to the target task by this mapping
                    # to_others   : impact factor to other tasks by this mapping 
                    node_costfunc = self._get_factor_impact_to_self(node_val, fr_pri, fr_ix, strm_specs, 
                                                                    check_RMAppMappedTasks = False,
                                                                    check_NodeTQ = True,
                                                                    check_IBuffs = True,
                                                                    cc_type="avgccc")
                                
                    if node_key not in node_and_costfunction_dict:
                        node_and_costfunction_dict[node_key] = node_costfunc
                
                # now make the selection
                min_cf =  min(node_and_costfunction_dict.itervalues())
                selected_node_id = [k for k,v in node_and_costfunction_dict.iteritems() if v == min_cf][0]
                
                # assign
                frames_mapping_priass_combined[fr_ix] = selected_node_id
                ## update dict ##
                pseudo_task = self._get_pseudo_task(fr_ix, fr_pri, selected_node_id, strm_specs )
                local_nodespecific_info[selected_node_id]['RMAppMappedTasks'].append(pseudo_task)
                #local_nodespecific_info[selected_node_id]['IBuffs'].append(pseudo_task)
                local_nodespecific_info[selected_node_id]['NodeTQ'].append(pseudo_task)
                
            self._map_to_vidstrm_mappingtbl(frames_mapping_priass_combined, wf_id, strm_id)
                
            return (frames_mapping_priass_combined, frame_priorities)
                
        else:
            return (None, None)
            
    
    #####################################################################################
    # TASKMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_SHRTQFIRST_LEASTBLTIME_V1
    #####################################################################################
    # first the vid stream is assigned a frame-level semi-dynamic priority scheme
    # (PR: lowest res first)
    # then,
    # (MP: Shortest Task Queue with lowest blocking time)    
    def taskMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPShrTQwithBlTime_V1(self, strm_specs):
        
        # build pseudo frame-mappings dict
        empty_frame_mappings = self._get_empty_frame_mappings_dict(strm_specs)
        
        # get frame level priorities
        frame_priorities = self.RM_instance.taskPriAssigner.taskSemiDynPriSch_getFramePriority_LowestResFirst(strm_specs, empty_frame_mappings)
                     
        # get list of nodes that are free 
        free_nodes_list = self.RM_instance.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL)
        
        node_and_tqstats_dict = {}        
        # maintain a (node, tqlevel) dict internally
        for node in free_nodes_list: 
            node_and_tqstats_dict[node.get_id()] = {
                                                    'tq_level' : node.getTaskQ_level(), 
                                                    'task_list' : node.get_TaskQueue()                                                                                                   
                                                    }            
        
        # we have more than one option        
        if(len(free_nodes_list)>0):        
            wf_id = strm_specs['wf_id']
            strm_id = strm_specs['vid_strm_id']
            gop_struct = strm_specs['gop_struct']        
            frames_mapping_priass_combined = {}            
            
            # find the lowest tq, and if there are multiple of the same tq size, then we check the remaining cc
            for fr_ix, each_f in enumerate(gop_struct):
                
                # first we find the nodes with min tq size
                min_tqval = min([v['tq_level'] for v in node_and_tqstats_dict.itervalues()])
                nodes_with_min_tq = {}
                for each_item_key, each_item_val in node_and_tqstats_dict.iteritems():
                    if (each_item_val['tq_level'] == min_tqval):
                        nodes_with_min_tq[each_item_key] = each_item_val                        
                
                # now out of the results, we find the which will give the lowest blocking time for the target task
                if (len(nodes_with_min_tq) >0):                    
                    
                    # we have more than one candidate, now we select one randomly                    
                    selected_node_id = self._get_node_with_min_blocking_time(frame_priorities[fr_ix], nodes_with_min_tq)                                       
                    frames_mapping_priass_combined[fr_ix] = selected_node_id # assign
                    node_and_tqstats_dict[selected_node_id]['tq_level'] = node_and_tqstats_dict[selected_node_id]['tq_level']+1 # update dict              
            
            # copy selection to vidstream mapping table
            self._map_to_vidstrm_mappingtbl(frames_mapping_priass_combined, wf_id, strm_id)

            return (frames_mapping_priass_combined, frame_priorities)
                
        else:
            return (None, None)
    
    
    #####################################################################################
    # TASKMAPPINGANDPRIASSCOMBINED_LEAST_RESPONSETIMEANDCONGESTIONNODE
    #####################################################################################
    # first the vid stream is assigned a frame-level semi-dynamic priority scheme
    # (PR: lowest res first)
    # then,
    # (MP: Shortest Task Queue with lowest blocking time, and node that has lowest congestion rating)   
    def taskMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPLeastRespTimeAndCongested(self, strm_specs):
        
        # build pseudo frame-mappings dict
        empty_frame_mappings = self._get_empty_frame_mappings_dict(strm_specs)
        
        # get frame level priorities
        frame_priorities = self.RM_instance.taskPriAssigner.taskSemiDynPriSch_getFramePriority_LowestResFirst(strm_specs, empty_frame_mappings)
                     
        # get list of nodes that are free 
        free_nodes_list = self.RM_instance.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL)
        
        # we have more than one option        
        if(len(free_nodes_list)>0):
        
            wf_id = strm_specs['wf_id']
            strm_id = strm_specs['vid_strm_id']
            gop_struct = strm_specs['gop_struct']        
            frames_mapping_priass_combined = {}            
            
            local_application_tasks = self.RM_instance.RunTimeApps.getTasks()
            
            # find the lowest tq, and if there are multiple of the same tq size, then we check the remaining cc
            for fr_ix, each_f in enumerate(gop_struct):                
                
                # for this task, determine the least response time
                # considering only the task blocking within the node tq
                nodes_with_cf = {}
                node_with_cf_list = []
                node_specific_congestion_rating = {}
                
                nextid = self.RM_instance.flow_table.nextid  
                for each_node in free_nodes_list:
                    
                    # get the response time for this task on this processing core
                    pseudo_task = self._get_pseudo_task(fr_ix, frame_priorities[fr_ix], each_node.get_id(), strm_specs, tid=fr_ix)
                    interference_set = pseudo_task.getInterferenceSet(local_application_tasks)                    
                    pseudo_task_wcet = pseudo_task.getResponseTime(interference_set)                                     
                    
                    # get the congestion rating for this node for this task   
                    node_congestion_rating =  self.RM_instance.RunTimeApps.getNodeCongestionRating(each_node.get_id(), task_pri=None, nextid=None)                    
                    node_specific_congestion_rating[each_node.get_id()] = node_congestion_rating
                    
                    # construct and record cost function
                    #cost_function = pseudo_task_wcet + node_congestion_rating
                    cost_function = pseudo_task_wcet
                    #cost_function = node_congestion_rating
                    #nodes_with_cf[each_node.get_id()] = cost_function                    
                    node_with_cf_list.append({'id' : each_node.get_id(),
                                             'congestion_rating' : node_congestion_rating,
                                             't_wcet' : pseudo_task_wcet
                                             })
                    
                # now make the selection
                #min_cf =  min(nodes_with_cf.itervalues())
                #selected_node_id = random.choice([k for k,v in nodes_with_cf.iteritems() if v == min_cf])         
                node_with_cf_list.sort(key=lambda x: (x['t_wcet'], x['congestion_rating']), reverse=False)       
                selected_node_id = node_with_cf_list[0]['id']             
                pseudo_task = self._get_pseudo_task(fr_ix, frame_priorities[fr_ix], selected_node_id, strm_specs, tid=fr_ix)
                local_application_tasks.append(pseudo_task)
                
                # assign
                frames_mapping_priass_combined[fr_ix] = selected_node_id
                
            self._map_to_vidstrm_mappingtbl(frames_mapping_priass_combined, wf_id, strm_id)
                            
            return (frames_mapping_priass_combined, frame_priorities)
                
        else:
            return (None, None)
    
    
    
    
    #####################################################################################
    # TASKMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_NNWITHLEASTBLOCKING_V1
    #####################################################################################
    # first the vid stream is assigned a frame-level semi-dynamic priority scheme
    # (PR: lowest res first)
    # then,
    # (MP: nearest neighbour with least blocking)   
    def taskMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPNNWithLeastBlocking(self, strm_specs):
        
        # build pseudo frame-mappings dict
        empty_frame_mappings = self._get_empty_frame_mappings_dict(strm_specs)
        
        # get frame level priorities
        frame_priorities = self.RM_instance.taskPriAssigner.taskSemiDynPriSch_getFramePriority_LowestResFirst(strm_specs, empty_frame_mappings)
                     
        # get list of nodes that are free 
        free_nodes_list = self.RM_instance.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL)
        
        node_and_assigned_tasks = {}        
        # maintain a (node, tqlevel) dict internally
        for node in free_nodes_list: 
            node_and_assigned_tasks[node.get_id()] = {
                                                      'task_list' : self.RM_instance.RunTimeApps.getNodeToTaskMapping(node_id=node.get_id())
                                                    }         
        
        # we have more than one option        
        if(len(free_nodes_list)>0):
        
            wf_id = strm_specs['wf_id']
            strm_id = strm_specs['vid_strm_id']
            gop_struct = strm_specs['gop_struct']        
            frames_mapping_priass_combined = {}            
            
            pseudo_task_objs = []
            
            # find the lowest tq, and if there are multiple of the same tq size, then we check the remaining cc
            for fr_ix, each_f in enumerate(gop_struct):     
                pseudo_task = self._get_pseudo_task(fr_ix, frame_priorities[fr_ix], 0, strm_specs, tid=fr_ix)
                
                # if this is the first task, we assign it to the lowest blocking node
                if(pseudo_task.get_frameIXinGOP() == 0):                    
                    selected_node_id =self._get_node_with_min_blocking_time_viaRuntimeApp(frame_priorities[fr_ix], node_and_assigned_tasks)
                    # assign
                    frames_mapping_priass_combined[fr_ix] = selected_node_id
                    # set processing node
                    pseudo_task.set_processingCore(selected_node_id)
                    # add to local structure
                    node_and_assigned_tasks[selected_node_id]['task_list'].append(pseudo_task)
                    # add to task objs
                    pseudo_task_objs.append(pseudo_task)
                    
                else:
                    # get immediate parent ix
                    parent_ix = pseudo_task.get_my_closest_parent()
                    parent_task = self._get_task_from_runtimeapp_tasklist(wf_id, strm_id, parent_ix, pseudo_task_objs)
                    parent_ix_node_id = parent_task.get_processingCore()
                    parent_ix_node_neighbour_list = self.RM_instance.interconnect.getNeighboursTwoHop(parent_ix_node_id)
                    nn_node_and_assigned_tasks = {}

                    if(len(parent_ix_node_neighbour_list)>0):
                        for k,v in node_and_assigned_tasks.iteritems():
                            if(k in parent_ix_node_neighbour_list):
                                nn_node_and_assigned_tasks[k] = v
                        selected_node_id = self._get_node_with_min_blocking_time_viaRuntimeApp(frame_priorities[fr_ix], nn_node_and_assigned_tasks)                        
                    else:
                        selected_node_id = self._get_node_with_min_blocking_time_viaRuntimeApp(frame_priorities[fr_ix], node_and_assigned_tasks)
                        
                        
                    # assign
                    frames_mapping_priass_combined[fr_ix] = selected_node_id
                    # set processing node
                    pseudo_task.set_processingCore(selected_node_id)
                    # add to local structure
                    node_and_assigned_tasks[selected_node_id]['task_list'].append(pseudo_task)
                    # add to task objs
                    pseudo_task_objs.append(pseudo_task)     
    
            self._map_to_vidstrm_mappingtbl(frames_mapping_priass_combined, wf_id, strm_id)                            
            return (frames_mapping_priass_combined, frame_priorities)
        else:
            return (None, None)
            
    
    
    #####################################################################################
    # TASKMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_NNLEASTUTILISED_TOPNPERCENT
    #####################################################################################
    # first the vid stream is assigned a frame-level semi-dynamic priority scheme
    # (PR: lowest res first)
    # then,
    # (MP: nearest node and least utilised),    
    def taskMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPNNWithLeastUtilised_TopNPercent(self, strm_specs):
        
        TOP_PERCENT = 0.1
        
        # build pseudo frame-mappings dict
        empty_frame_mappings = self._get_empty_frame_mappings_dict(strm_specs)
        
        # get frame level priorities
        frame_priorities = self.RM_instance.taskPriAssigner.taskSemiDynPriSch_getFramePriority_LowestResFirst(strm_specs, empty_frame_mappings)
                     
        # get list of nodes that are free 
        free_nodes_list = self.RM_instance.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL)
        
        node_and_utils = {}        
        # maintain a (node, tqlevel) dict internally
        for node in free_nodes_list: 
            node_and_utils[node.get_id()] = {
                                                      'util' : self.RM_instance.RunTimeApps.getNodeEstimatedUtilisation(node_id=node.get_id())
                                                    }         
        
        # we have more than one option        
        if(len(free_nodes_list)>0):
        
            wf_id = strm_specs['wf_id']
            strm_id = strm_specs['vid_strm_id']
            gop_struct = strm_specs['gop_struct']        
            frames_mapping_priass_combined = {}            
            
            pseudo_task_objs = []
            
            # find the lowest tq, and if there are multiple of the same tq size, then we check the remaining cc
            for fr_ix, each_f in enumerate(gop_struct):     
                pseudo_task = self._get_pseudo_task(fr_ix, frame_priorities[fr_ix], 0, strm_specs, tid=fr_ix)
                
                # if this is the first task, we assign it to the lowest blocking node
                if(pseudo_task.get_frameIXinGOP() == 0):                    
                    selected_node_id = self._get_node_with_min_utilisation(node_and_utils)
                    # assign
                    frames_mapping_priass_combined[fr_ix] = selected_node_id
                    # set processing node
                    pseudo_task.set_processingCore(selected_node_id)
                    # add to local structure
                    util = float(pseudo_task.get_worstCaseComputationCost()/pseudo_task.get_period())
                    node_and_utils[selected_node_id]['util'] += util
                    # add to task objs
                    pseudo_task_objs.append(pseudo_task)
                    
                else:
                    # get immediate parent ix
                    parent_ix = pseudo_task.get_my_closest_parent()
                    parent_task = self._get_task_from_runtimeapp_tasklist(wf_id, strm_id, parent_ix, pseudo_task_objs)
                    parent_ix_node_id = parent_task.get_processingCore()                    
                    topn_nodes_withlowest_util = self._get_nodes_with_min_utilisation_topnpercent(node_and_utils, TOP_PERCENT)
                    closest_to_parentixnode_withlowestutil_nodeid = self._get_closest_to_nodeid(topn_nodes_withlowest_util, parent_ix_node_id)
                    selected_node_id = closest_to_parentixnode_withlowestutil_nodeid
                        
                    # assign
                    frames_mapping_priass_combined[fr_ix] = selected_node_id
                    # set processing node
                    pseudo_task.set_processingCore(selected_node_id)
                    # add to local structure
                    util = float(pseudo_task.get_worstCaseComputationCost()/pseudo_task.get_period())
                    node_and_utils[selected_node_id]['util'] += util
                    # add to task objs
                    pseudo_task_objs.append(pseudo_task)     
    
            self._map_to_vidstrm_mappingtbl(frames_mapping_priass_combined, wf_id, strm_id)                            
            return (frames_mapping_priass_combined, frame_priorities)
        else:
            return (None, None)
            
    
    #####################################################################################
    # TASKMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_CARVALHO_BN
    #####################################################################################
    # first the vid stream is assigned a frame-level semi-dynamic priority scheme
    # (PR: lowest res first)
    # then,
    # (MP: best neighbour according to carvalho)  
    def taskMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPCarvalho_BN(self, strm_specs):
        
        # build pseudo frame-mappings dict
        empty_frame_mappings = self._get_empty_frame_mappings_dict(strm_specs)
        
        # get frame level priorities
        frame_priorities = self.RM_instance.taskPriAssigner.taskSemiDynPriSch_getFramePriority_LowestResFirst(strm_specs, empty_frame_mappings)
                     
        # get list of nodes that are free 
        free_nodes_list = self.RM_instance.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL)
        
        node_and_utils = {}  
        # maintain a (node, tqlevel) dict internally
        for node in free_nodes_list: 
            node_and_utils[node.get_id()] = {
                                              'mapped_tasks' : list([ task for task in self.RM_instance.RunTimeApps.getTasks() \
                                                                             if (task.get_processingCore() == node.get_id()) ]),
                                              'util' : self.RM_instance.RunTimeApps.getNodeEstimatedUtilisation(node_id=node.get_id())
                                            }      
        # maintain a link to flow dict internally
        link_to_flow_mapping = dict(self.RM_instance.RunTimeApps.getLinkToFlowMapping(self.RM_instance.RunTimeApps.getFlows()))
                
        # we have more than one option        
        if(len(free_nodes_list)>0):
        
            wf_id = strm_specs['wf_id']
            strm_id = strm_specs['vid_strm_id']
            gop_struct = strm_specs['gop_struct']        
            frames_mapping_priass_combined = {}     
            pseudo_task_objs = []
            
            for fr_ix, each_f in enumerate(gop_struct):   
                pseudo_task = self._get_pseudo_task(fr_ix, frame_priorities[fr_ix], 0, strm_specs, tid=fr_ix, ai=self.env.now)
                
                if(pseudo_task.get_frameIXinGOP() == 0):
                    selected_node_id = self.RM_instance.RunTimeApps.getNodeLowestMappedTasks()
                    # assign
                    frames_mapping_priass_combined[fr_ix] = selected_node_id
                    # set processing node
                    pseudo_task.set_processingCore(selected_node_id)
                    # add to local structure
                    util = float(pseudo_task.get_worstCaseComputationCost()/pseudo_task.get_period())
                    node_and_utils[selected_node_id]['util'] += util
                    node_and_utils[selected_node_id]['mapped_tasks'].append(pseudo_task)
                    # add to task objs
                    pseudo_task_objs.append(pseudo_task)
                else:
                    # get immediate parent ix
                    parent_ix = pseudo_task.get_my_closest_parent()
                    parent_task = self._get_task_from_runtimeapp_tasklist(wf_id, strm_id, parent_ix, pseudo_task_objs)
                    parent_ix_node_id = parent_task.get_processingCore()           
                    selected_node_id = None
                    for each_hop_count in xrange(1,(SimParams.NOC_W-1)+ (SimParams.NOC_H-1)):                         
                        nhop_neighbour_node_ids = self.RM_instance.interconnect.getNodesExactNHops(parent_ix_node_id, each_hop_count)                        
                        temp_node_and_mptasks = {}
                        for nid in nhop_neighbour_node_ids:                            
                            temp_node_and_mptasks[nid] = node_and_utils[nid]

                        # are any of the neighbours 'free' ? i.e. nodes that can accomodate this task
                        selected_node_ids = self._get_nodes_that_can_accomodate_targettask(pseudo_task, temp_node_and_mptasks)
                                                
                        # if there are more than one node that can accomodate this task, then check for path load as a heuristic
                        if(len(selected_node_ids)>1):
                            node_mapped_pathcost = {}
                            # search according to route load                         
                            for each_nn_id in selected_node_ids:
                                route_load = self.RM_instance.RunTimeApps.getRouteLoad(parent_ix_node_id, each_nn_id, link_to_flow_mapping)
                                node_mapped_pathcost[each_nn_id] = route_load
                            min_rotue_cost = min(node_mapped_pathcost.values())
                            selected_node_id = [k for k,v in node_mapped_pathcost.iteritems() if v == min_rotue_cost][0]
                            break
                        elif(len(selected_node_ids)==1):
                            selected_node_id = selected_node_ids[0]
                            break
                        elif(len(selected_node_ids)==0):
                            continue
                     
                    # we purely use path load
                    if(selected_node_id == None) or (selected_node_id == []): # no nodes found
                        all_hop_neighbours = self.RM_instance.interconnect.getNodesNHops(parent_ix_node_id, SimParams.NOC_W)                            
                        node_mapped_pathcost = {}
                        # search according to route load                         
                        for each_nn_id in all_hop_neighbours:
                            route_load = self.RM_instance.RunTimeApps.getRouteLoad(parent_ix_node_id, each_nn_id, link_to_flow_mapping)
                            node_mapped_pathcost[each_nn_id] = route_load
                        min_rotue_cost = min(node_mapped_pathcost.values())
                        selected_node_id = [k for k,v in node_mapped_pathcost.iteritems() if v == min_rotue_cost][0]
                        
                           
                    # assign
                    frames_mapping_priass_combined[fr_ix] = selected_node_id
                    # set processing node
                    pseudo_task.set_processingCore(selected_node_id)
                    # add to local structure
                    util = float(pseudo_task.get_worstCaseComputationCost()/pseudo_task.get_period())
                    node_and_utils[selected_node_id]['util'] += util
                    node_and_utils[selected_node_id]['mapped_tasks'].append(pseudo_task)
                    # add to task objs
                    pseudo_task_objs.append(pseudo_task)     
                    # update link to flow table
                    link_to_flow_mapping = self._update_link_to_flow_mapping(link_to_flow_mapping, 
                                                                             self.RM_instance.interconnect.getRouteHopCount(parent_ix_node_id, selected_node_id),
                                                                             1,
                                                                             selected_node_id, parent_ix_node_id)
        
            self._map_to_vidstrm_mappingtbl(frames_mapping_priass_combined, wf_id, strm_id)                            
            return (frames_mapping_priass_combined, frame_priorities)
        else:
            return (None, None)
    
    
    
    
    #####################################################################################
    # TASKMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_CARVALHO_BN_V2
    #####################################################################################
    # first the vid stream is assigned a frame-level semi-dynamic priority scheme
    # (PR: lowest res first)
    # then,
    # (MP: best neighbour according to carvalho)  
    def taskMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPCarvalho_BN_V2(self, strm_specs):
        
        # build pseudo frame-mappings dict
        empty_frame_mappings = self._get_empty_frame_mappings_dict(strm_specs)
        
        # get frame level priorities
        frame_priorities = self.RM_instance.taskPriAssigner.taskSemiDynPriSch_getFramePriority_LowestResFirst(strm_specs, empty_frame_mappings)
                     
        # get list of nodes that are free 
        free_nodes_list = self.RM_instance.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL)
        
        node_and_utils = {}  
        # maintain a (node, tqlevel) dict internally
        for node in free_nodes_list: 
            node_and_utils[node.get_id()] = { 
                                              'util' : self.RM_instance.RunTimeApps.getNodeEstimatedUtilisation(node_id=node.get_id())
                                            }      
        # maintain a link to flow dict internally
        link_to_flow_mapping = dict(self.RM_instance.RunTimeApps.getLinkToFlowMapping(all_flows=self.RM_instance.RunTimeApps.getFlows()))
                
        # we have more than one option        
        if(len(free_nodes_list)>0):
        
            wf_id = strm_specs['wf_id']
            strm_id = strm_specs['vid_strm_id']
            gop_struct = strm_specs['gop_struct']        
            frames_mapping_priass_combined = {}     
            pseudo_task_objs = []
            
            for fr_ix, each_f in enumerate(gop_struct):   
                pseudo_task = self._get_pseudo_task(fr_ix, frame_priorities[fr_ix], 0, strm_specs, tid=fr_ix, ai=self.env.now)
                
                if(pseudo_task.get_frameIXinGOP() == 0):
                    selected_node_id = self._get_node_with_min_utilisation(node_and_utils)
                    # assign
                    frames_mapping_priass_combined[fr_ix] = selected_node_id
                    # set processing node
                    pseudo_task.set_processingCore(selected_node_id)
                    # add to local structure
                    util = float(pseudo_task.get_worstCaseComputationCost()/pseudo_task.get_period())
                    node_and_utils[selected_node_id]['util'] += util                    
                    # add to task objs
                    pseudo_task_objs.append(pseudo_task)
                else:
                    # get immediate parent ix
                    parent_ix = pseudo_task.get_my_closest_parent()
                    parent_task = self._get_task_from_runtimeapp_tasklist(wf_id, strm_id, parent_ix, pseudo_task_objs)
                    parent_ix_node_id = parent_task.get_processingCore()           
                    selected_node_id = None
                    for each_hop_count in xrange(1,(SimParams.NOC_W-1)+ (SimParams.NOC_H-1)):                         
                        nhop_neighbour_node_ids = self.RM_instance.interconnect.getNodesExactNHops(parent_ix_node_id, each_hop_count)                        
                        temp_node_and_mptasks = {}
                        for nid in nhop_neighbour_node_ids:                            
                            temp_node_and_mptasks[nid] = node_and_utils[nid]
                        
                        # select nodes with low util (lower than avg) from these nodes list
                        selected_node_ids = self._get_nodes_below_avg_utilisation(node_and_utils,temp_node_and_mptasks)
                                                
                        # if there are more than one node that can accomodate this task, then check for path load as a heuristic
                        if(len(selected_node_ids)>1):
                            node_mapped_pathcost = {}
                            # search according to route load                         
                            for each_nn_id in selected_node_ids:
                                route_load = self.RM_instance.RunTimeApps.getRouteLoad(parent_ix_node_id, each_nn_id, link_to_flow_mapping)
                                node_mapped_pathcost[each_nn_id] = route_load
                            min_route_cost = min(node_mapped_pathcost.values())
                            selected_node_id = [k for k,v in node_mapped_pathcost.iteritems() if v == min_route_cost][0]
                            break
                        elif(len(selected_node_ids)==1):
                            selected_node_id = selected_node_ids[0]
                            break
                        elif(len(selected_node_ids)==0):
                            continue
                     
                    # we purely use path load
                    if(selected_node_id == None) or (selected_node_id == []): # no nodes found
                        all_hop_neighbours = self.RM_instance.interconnect.getNodesNHops(parent_ix_node_id, SimParams.NOC_W)                            
                        node_mapped_pathcost = {}
                        # search according to route load                         
                        for each_nn_id in all_hop_neighbours:
                            route_load = self.RM_instance.RunTimeApps.getRouteLoad(parent_ix_node_id, each_nn_id, link_to_flow_mapping)
                            node_mapped_pathcost[each_nn_id] = route_load
                        min_rotue_cost = min(node_mapped_pathcost.values())
                        selected_node_id = [k for k,v in node_mapped_pathcost.iteritems() if v == min_rotue_cost][0]
                        
                           
                    # assign
                    frames_mapping_priass_combined[fr_ix] = selected_node_id
                    # set processing node
                    pseudo_task.set_processingCore(selected_node_id)
                    # add to local structure
                    util = float(pseudo_task.get_worstCaseComputationCost()/pseudo_task.get_period())
                    node_and_utils[selected_node_id]['util'] += util                    
                    # add to task objs
                    pseudo_task_objs.append(pseudo_task)     
                    # update link to flow table
                    link_to_flow_mapping = self._update_link_to_flow_mapping(link_to_flow_mapping, 
                                                                             self.RM_instance.interconnect.getRouteHopCount(parent_ix_node_id, selected_node_id),
                                                                             1,
                                                                             selected_node_id, parent_ix_node_id)
            
            
            self._map_to_vidstrm_mappingtbl(frames_mapping_priass_combined, wf_id, strm_id)                            
            return (frames_mapping_priass_combined, frame_priorities)
        else:
            return (None, None)
    
    
    
    
    
    
    #####################################################################################
    # TASKMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_KAUSHIK_PP
    #####################################################################################
    # first the vid stream is assigned a frame-level semi-dynamic priority scheme
    # (PR: lowest res first)
    # then,
    # (MP: using Kaushik et al. algorithm, based on a preprocessing stage + closest node to parent
#     task_clustering = [
#         [0],
#         [1],
#         [2,3],
#         [4],
#         [5,6,11],
#         [7],
#         [8,9,10]
#         ] 
    def taskMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPKaushik_PP(self, strm_specs):
        
        # build pseudo frame-mappings dict
        empty_frame_mappings = self._get_empty_frame_mappings_dict(strm_specs)
        
        # get frame level priorities
        frame_priorities = self.RM_instance.taskPriAssigner.taskSemiDynPriSch_getFramePriority_LowestResFirst(strm_specs, empty_frame_mappings)
                     
        # get list of nodes that are free 
        free_nodes_list = self.RM_instance.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL)
        
        node_and_utils= {}
        # maintain a (node, tqlevel) dict internally
        for node in free_nodes_list: 
            node_and_utils[node.get_id()] = {
                                              'util' : self.RM_instance.RunTimeApps.getNodeEstimatedUtilisation(node_id=node.get_id())
                                            }      
        
        # we have more than one option        
        if(len(free_nodes_list)>0):
            wf_id = strm_specs['wf_id']
            strm_id = strm_specs['vid_strm_id']
            gop_struct = strm_specs['gop_struct']        
            frames_mapping_priass_combined = {}
            pseudo_task_objs = []            
            
            ### if Comp.Cost >> Comm.Cost ###
            if(self._get_ccr_of_taskgraph(strm_specs) < 1.0):
                for fr_ix, each_f in enumerate(gop_struct):     
                    pseudo_task = self._get_pseudo_task(fr_ix, frame_priorities[fr_ix], 0, strm_specs, tid=fr_ix, ai=self.env.now)
                    
                    if(pseudo_task.get_frameIXinGOP() == 0):
                        selected_node_id = self._get_node_with_min_utilisation(node_and_utils)
                        # assign
                        frames_mapping_priass_combined[fr_ix] = selected_node_id
                        # set processing node
                        pseudo_task.set_processingCore(selected_node_id)
                        # add to local structure
                        util = float(pseudo_task.get_worstCaseComputationCost()/pseudo_task.get_period())
                        node_and_utils[selected_node_id]['util'] += util
                        # add to task objs
                        pseudo_task_objs.append(pseudo_task)
                    else:
                        # get immediate parent ix
                        parent_ix = pseudo_task.get_my_closest_parent()
                        parent_task = self._get_task_from_runtimeapp_tasklist(wf_id, strm_id, parent_ix, pseudo_task_objs)
                        parent_ix_node_id = parent_task.get_processingCore()
                        #parent_ix_node_neighbour_list = self.RM_instance.interconnect.getNeighboursTwoHop(parent_ix_node_id) # first hop nodes from parent
                        parent_ix_node_neighbour_list = self.RM_instance.interconnect.getNodesNHops(parent_ix_node_id, 2) # first hop nodes from parent
                        
                        
                        if(pseudo_task.get_frameIXinGOP() == 3):
                            selected_node_id = self._get_task_from_runtimeapp_tasklist(wf_id, strm_id, 2, pseudo_task_objs).get_processingCore()
                        elif(pseudo_task.get_frameIXinGOP() in [6,11]):
                            selected_node_id = self._get_task_from_runtimeapp_tasklist(wf_id, strm_id, 5, pseudo_task_objs).get_processingCore()                        
                        elif(pseudo_task.get_frameIXinGOP() in [9,10]):
                            selected_node_id = self._get_task_from_runtimeapp_tasklist(wf_id, strm_id, 8, pseudo_task_objs).get_processingCore()
                        else:
                            temp_node_and_utils = {}
                            for nid in parent_ix_node_neighbour_list:
                                temp_node_and_utils[nid] = {
                                                        'util' : node_and_utils[nid]
                                                        }                    
                            # select lowest util from nn
                            closest_node_with_lowest_util = self._get_node_with_min_utilisation(temp_node_and_utils)
                            #closest_node_with_lowest_util = random.choice(temp_node_and_utils.keys())
                            selected_node_id = closest_node_with_lowest_util      
                                          
                        # assign
                        frames_mapping_priass_combined[fr_ix] = selected_node_id
                        # set processing node
                        pseudo_task.set_processingCore(selected_node_id)
                        # add to local structure
                        util = float(pseudo_task.get_worstCaseComputationCost()/pseudo_task.get_period())
                        node_and_utils[selected_node_id]['util'] += util
                        # add to task objs
                        pseudo_task_objs.append(pseudo_task)
                
                self._map_to_vidstrm_mappingtbl(frames_mapping_priass_combined, wf_id, strm_id)                            
                return (frames_mapping_priass_combined, frame_priorities)
            
            
            ### if Comm.Cost >> Comp.Cost ###
            else:
                for fr_ix, each_f in enumerate(gop_struct):     
                    pseudo_task = self._get_pseudo_task(fr_ix, frame_priorities[fr_ix], 0, strm_specs, tid=fr_ix, ai=self.env.now)
                    
                    if(pseudo_task.get_frameIXinGOP() == 0):
                        selected_node_id = self._get_node_with_min_utilisation(node_and_utils)
                        # assign
                        frames_mapping_priass_combined[fr_ix] = selected_node_id
                        # set processing node
                        pseudo_task.set_processingCore(selected_node_id)
                        # add to local structure
                        util = float(pseudo_task.get_worstCaseComputationCost()/pseudo_task.get_period())
                        node_and_utils[selected_node_id]['util'] += util
                        # add to task objs
                        pseudo_task_objs.append(pseudo_task)
                    else:
                        # get immediate parent ix
                        parent_ix = pseudo_task.get_my_closest_parent()
                        parent_task = self._get_task_from_runtimeapp_tasklist(wf_id, strm_id, parent_ix, pseudo_task_objs)
                        parent_ix_node_id = parent_task.get_processingCore()
                        #parent_ix_node_neighbour_list = self.RM_instance.interconnect.getNeighboursTwoHop(parent_ix_node_id) # first hop nodes from parent
                        parent_ix_node_neighbour_list = self.RM_instance.interconnect.getNodesNHops(parent_ix_node_id, 2) # first hop nodes from parent
                        
                        if(pseudo_task.get_frameIXinGOP() == 1):
                            selected_node_id = self._get_task_from_runtimeapp_tasklist(wf_id, strm_id, 0, pseudo_task_objs).get_processingCore()                        
                        elif(pseudo_task.get_frameIXinGOP() in [3,11]):
                            selected_node_id = self._get_task_from_runtimeapp_tasklist(wf_id, strm_id, 2, pseudo_task_objs).get_processingCore()
                        elif(pseudo_task.get_frameIXinGOP() in [7]):
                            selected_node_id = self._get_task_from_runtimeapp_tasklist(wf_id, strm_id, 4, pseudo_task_objs).get_processingCore()
                        elif(pseudo_task.get_frameIXinGOP() in [8,9,10]):
                            selected_node_id = self._get_task_from_runtimeapp_tasklist(wf_id, strm_id, 6, pseudo_task_objs).get_processingCore()                        
                        else: # 0,2,4,5,6
                            temp_node_and_utils = {}
                            for nid in parent_ix_node_neighbour_list:
                                temp_node_and_utils[nid] = {
                                                        'util' : node_and_utils[nid]
                                                        }                    
                            # select lowest util from nn
                            closest_node_with_lowest_util = self._get_node_with_min_utilisation(temp_node_and_utils)
                            #closest_node_with_lowest_util = random.choice(temp_node_and_utils.keys())
                            selected_node_id = closest_node_with_lowest_util      
                                          
                        # assign
                        frames_mapping_priass_combined[fr_ix] = selected_node_id
                        # set processing node
                        pseudo_task.set_processingCore(selected_node_id)
                        # add to local structure
                        util = float(pseudo_task.get_worstCaseComputationCost()/pseudo_task.get_period())
                        node_and_utils[selected_node_id]['util'] += util
                        # add to task objs
                        pseudo_task_objs.append(pseudo_task)
                
                self._map_to_vidstrm_mappingtbl(frames_mapping_priass_combined, wf_id, strm_id)                            
                return (frames_mapping_priass_combined, frame_priorities)
            
        else:
            return (None, None)   
            
        
        
    
    
    
    
    
    
    
    
    
    
    #####################################################################################
    # TASKMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_LOWCOMMUNICATION_V1
    #####################################################################################
    # first the vid stream is assigned a frame-level semi-dynamic priority scheme
    # (PR: lowest res first)
    # then,
    # (MP: map all the I,P tasks together, then B frames seperate - lum)  
    def taskMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPLowComms_V1(self, strm_specs):
     
        # build pseudo frame-mappings dict
        empty_frame_mappings = self._get_empty_frame_mappings_dict(strm_specs)
        
        # get frame level priorities
        frame_priorities = self.RM_instance.taskPriAssigner.taskSemiDynPriSch_getFramePriority_LowestResFirst(strm_specs, empty_frame_mappings)
                     
        # get list of nodes that are free 
        free_nodes_list = self.RM_instance.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL)
        
        node_and_utils = {}        
        # maintain a (node, tqlevel) dict internally
        for node in free_nodes_list: 
            node_and_utils[node.get_id()] = {
                                                      'util' : self.RM_instance.RunTimeApps.getNodeEstimatedUtilisation(node_id=node.get_id())
                                                    }         
        
        # we have more than one option        
        if(len(free_nodes_list)>0):
        
            wf_id = strm_specs['wf_id']
            strm_id = strm_specs['vid_strm_id']
            gop_struct = strm_specs['gop_struct']        
            frames_mapping_priass_combined = {}            
            
            pseudo_task_objs = []            
            I_P_selected_node = None
            B_selected_nodelist = []
            
            # we map the I, P frames (those that have children), to the lowest util node,
            # B frames (leaf nodes) are mapped to the nearest neighbour of it's parent
            for fr_ix, each_f in enumerate(gop_struct):     
                pseudo_task = self._get_pseudo_task(fr_ix, frame_priorities[fr_ix], 0, strm_specs, tid=fr_ix)
                                
                if(pseudo_task.get_frameType() in ["I", "P"]):
                    
                    if(I_P_selected_node == None):
                        selected_node_id = self._get_node_with_min_utilisation(node_and_utils)
                        I_P_selected_node = selected_node_id
                    else:
                        selected_node_id = I_P_selected_node
                        
                    # assign
                    frames_mapping_priass_combined[fr_ix] = selected_node_id
                    # set processing node
                    pseudo_task.set_processingCore(selected_node_id)
                    # add to local structure
                    util = float(pseudo_task.get_worstCaseComputationCost()/pseudo_task.get_period())
                    node_and_utils[selected_node_id]['util'] += util
                    # add to task objs
                    pseudo_task_objs.append(pseudo_task)
                else: # B-frame                   
                    # get immediate parent ix
                    parent_ix = pseudo_task.get_my_closest_parent()
                    parent_task = self._get_task_from_runtimeapp_tasklist(wf_id, strm_id, parent_ix, pseudo_task_objs)
                    parent_ix_node_id = parent_task.get_processingCore()
                    parent_ix_node_neighbour_list = self.RM_instance.interconnect.getNeighboursTwoHop(parent_ix_node_id) # first hop nodes from parent
                    
                    temp_node_and_utils = {}
                    for nid in parent_ix_node_neighbour_list:
                        temp_node_and_utils[nid] = {
                                                'util' : node_and_utils[nid]
                                                }
                    
                    # select lowest util from nn
                    closest_node_with_lowest_util = self._get_node_with_min_utilisation(temp_node_and_utils)
                    selected_node_id = closest_node_with_lowest_util
                    B_selected_nodelist.append(selected_node_id)
                    # assign
                    frames_mapping_priass_combined[fr_ix] = selected_node_id
                    # set processing node
                    pseudo_task.set_processingCore(selected_node_id)
                    # add to local structure
                    util = float(pseudo_task.get_worstCaseComputationCost()/pseudo_task.get_period())
                    node_and_utils[selected_node_id]['util'] += util
                    # add to task objs
                    pseudo_task_objs.append(pseudo_task)
                    
    
            self._map_to_vidstrm_mappingtbl(frames_mapping_priass_combined, wf_id, strm_id)                            
            return (frames_mapping_priass_combined, frame_priorities)
        else:
            return (None, None)
    
    
    
    #####################################################################################
    # TASKMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_LOWCOMMUNICATION_V2 - IPC
    #####################################################################################
    # first the vid stream is assigned a frame-level semi-dynamic priority scheme
    # (PR: lowest res first)
    # then,
    # (MP: map all the I,P tasks together, then B frames seperate - tight)  
    def taskMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPLowComms_V2(self, strm_specs):
     
        # build pseudo frame-mappings dict
        empty_frame_mappings = self._get_empty_frame_mappings_dict(strm_specs)
        
        # get frame level priorities
        frame_priorities = self.RM_instance.taskPriAssigner.taskSemiDynPriSch_getFramePriority_LowestResFirst(strm_specs, empty_frame_mappings)
                     
        # get list of nodes that are free 
        free_nodes_list = self.RM_instance.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL)
        
        node_and_utils = {}        
        # maintain a (node, tqlevel) dict internally
        for node in free_nodes_list: 
            node_and_utils[node.get_id()] = {
                                                      'mapped_tasks' : list([ task for task in self.RM_instance.RunTimeApps.getTasks() \
                                                                             if (task.get_processingCore() == node.get_id()) ]),
                                                      'util' : self.RM_instance.RunTimeApps.getNodeEstimatedUtilisation(node_id=node.get_id())
                                            }         
        
        # we have more than one option        
        if(len(free_nodes_list)>0):
        
            wf_id = strm_specs['wf_id']
            strm_id = strm_specs['vid_strm_id']
            gop_struct = strm_specs['gop_struct']        
            frames_mapping_priass_combined = {}            
            
            pseudo_task_objs = []            
            I_P_selected_node = None
            B_selected_nodelist = []
            
            # we map the I, P frames (those that have children), to the lowest util node,
            # B frames (leaf nodes) are mapped to the nearest neighbour of it's parent
            for fr_ix, each_f in enumerate(gop_struct):     
                pseudo_task = self._get_pseudo_task(fr_ix, frame_priorities[fr_ix], 0, strm_specs, tid=fr_ix, ai=self.env.now)
                                
                if(pseudo_task.get_frameType() in ["I", "P"]):
                    
                    if(I_P_selected_node == None):
                        selected_node_id = self._get_node_with_min_utilisation(node_and_utils)
                        I_P_selected_node = selected_node_id
                    else:
                        selected_node_id = I_P_selected_node
                        
                    # assign
                    frames_mapping_priass_combined[fr_ix] = selected_node_id
                    # set processing node
                    pseudo_task.set_processingCore(selected_node_id)
                    # add to local structure
                    util = float(pseudo_task.get_worstCaseComputationCost()/pseudo_task.get_period())
                    node_and_utils[selected_node_id]['util'] += util
                    node_and_utils[selected_node_id]['mapped_tasks'].append(pseudo_task)
                    # add to task objs
                    pseudo_task_objs.append(pseudo_task)
                else: # B-frame                   
                    # get immediate parent ix
                    parent_ix = pseudo_task.get_my_closest_parent()
                    parent_task = self._get_task_from_runtimeapp_tasklist(wf_id, strm_id, parent_ix, pseudo_task_objs)
                    parent_ix_node_id = parent_task.get_processingCore()
                    
                    # based on the graphs ccr select hop count
                    if(self._get_ccr_of_taskgraph(strm_specs) < 1.0): # Comp.Cost >> Comm.Cost
                        ccr_specific_hop_count = 2
                    else: # Comm.Cost >> Comp.Cost
                        ccr_specific_hop_count = 1
                    
                    parent_ix_node_neighbour_list = self.RM_instance.interconnect.getNodesNHops(parent_ix_node_id, ccr_specific_hop_count) # n hop nodes from parent
                    
                    # add parent node id to the list - take it also into account
                    parent_ix_node_neighbour_list.append(parent_ix_node_id)
                    
                    temp_node_and_utils = {}
                    for nid in parent_ix_node_neighbour_list:
                        temp_node_and_utils[nid] = {
                                                'util' : node_and_utils[nid]['util'],
                                                'mapped_tasks' : node_and_utils[nid]['mapped_tasks']
                                                }
                    
                    # select lowest slack from nn
                    closest_node_with_lowest_util = self._get_node_with_least_slack_result_for_targettask(pseudo_task, temp_node_and_utils)[0]
                    selected_node_id = closest_node_with_lowest_util
                    B_selected_nodelist.append(selected_node_id)
                    # assign
                    frames_mapping_priass_combined[fr_ix] = selected_node_id
                    # set processing node
                    pseudo_task.set_processingCore(selected_node_id)
                    # add to local structure
                    util = float(pseudo_task.get_worstCaseComputationCost()/pseudo_task.get_period())
                    node_and_utils[selected_node_id]['util'] += util
                    node_and_utils[selected_node_id]['mapped_tasks'].append(pseudo_task)
                    # add to task objs
                    pseudo_task_objs.append(pseudo_task)
                    
    
            self._map_to_vidstrm_mappingtbl(frames_mapping_priass_combined, wf_id, strm_id)                            
            return (frames_mapping_priass_combined, frame_priorities)
        else:
            return (None, None)
    
    
    #####################################################################################
    # TASKMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_TIGHTFIT_V1 - LWCRS
    #####################################################################################
    # first the vid stream is assigned a frame-level semi-dynamic priority scheme
    # (PR: lowest res first)
    # then,
    # (MP: take into account the possible slack, and tightly pack the tasks to cores)
    # utilisation will be high on a certain number of cores and lower on others  (non-uniform)
    def taskMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPTightFit_V1(self, strm_specs):
     
        # build pseudo frame-mappings dict
        empty_frame_mappings = self._get_empty_frame_mappings_dict(strm_specs)
        
        # get frame level priorities
        frame_priorities = self.RM_instance.taskPriAssigner.taskSemiDynPriSch_getFramePriority_LowestResFirst(strm_specs, empty_frame_mappings)
                     
        # get list of nodes that are free 
        free_nodes_list = self.RM_instance.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL)
        
        node_and_mappedtasks = OrderedDict()        
        # maintain a (node, tqlevel) dict internally
        for node in free_nodes_list: 
            node_and_mappedtasks[node.get_id()] = {
                                                    'mapped_tasks' : list([ task for task in self.RM_instance.RunTimeApps.getTasks() \
                                                                             if (task.get_processingCore() == node.get_id()) ]),
                                                    'util' : self.RM_instance.RunTimeApps.getNodeEstimatedUtilisation(node_id=node.get_id())
                                                  }         
        
        # we have more than one option        
        if(len(free_nodes_list)>0):
        
            wf_id = strm_specs['wf_id']
            strm_id = strm_specs['vid_strm_id']
            gop_struct = strm_specs['gop_struct']        
            frames_mapping_priass_combined = {}            
            
            pseudo_task_objs = []
            for fr_ix, each_f in enumerate(gop_struct):
                pseudo_task = self._get_pseudo_task(fr_ix, frame_priorities[fr_ix], 0, strm_specs, tid=fr_ix, ai=self.env.now)                
                parent_task_ix =  pseudo_task.get_my_closest_parent()
                if(parent_task_ix == None): # I-frame
                    selected_node_id = self._get_node_with_least_slack_result_for_targettask(pseudo_task, node_and_mappedtasks)[0]
                    
                    # assign
                    frames_mapping_priass_combined[fr_ix] = selected_node_id
                    # set processing node
                    pseudo_task.set_processingCore(selected_node_id)
                    # add to local structure
                    util = float(pseudo_task.get_worstCaseComputationCost()/pseudo_task.get_period())
                    node_and_mappedtasks[selected_node_id]['util'] += util
                    node_and_mappedtasks[selected_node_id]['mapped_tasks'].append(pseudo_task)
                    # add to task objs
                    pseudo_task_objs.append(pseudo_task)
                else: # P/B- frame
                    parent_task = self._get_task_from_runtimeapp_tasklist(wf_id, strm_id, parent_task_ix, pseudo_task_objs)
                    parent_ix_node_id = parent_task.get_processingCore()
                    for hop_count in xrange(1,2):
                        nhop_neighbour_node_ids = self.RM_instance.interconnect.getNodesNHops(parent_ix_node_id,hop_count)
                        #nhop_neighbour_node_ids.append(parent_ix_node_id) # we include parent nodeid as well
                        nhop_neighbour_node_ids[:0] = [parent_ix_node_id] # we include parent nodeid as well                        
                        temp_node_and_mapped_tasks = OrderedDict()
                        for k,v in node_and_mappedtasks.iteritems():
                            if k in nhop_neighbour_node_ids: temp_node_and_mapped_tasks[k]=v
                                
                        (search_result_node_id, found_bool) = self._get_node_with_least_slack_result_for_targettask(pseudo_task, temp_node_and_mapped_tasks)
                        if(found_bool==True):
                            selected_node_id = search_result_node_id
                            break
                        else:
                            selected_node_id = None
                            continue
                        
                    if(selected_node_id == None) or (selected_node_id == []): # if no node on the network can accomodate, then go for lowest util
                        nearest_nodes_ids = self.RM_instance.interconnect.getNodesNHops(parent_ix_node_id,1)
                        temp_nodes_and_utils = {k: node_and_mappedtasks[k] for k in tuple(nearest_nodes_ids)}
                        selected_node_id = self._get_node_with_min_utilisation(temp_nodes_and_utils)
                        
                    # assign
                    frames_mapping_priass_combined[fr_ix] = selected_node_id
                    # set processing node
                    pseudo_task.set_processingCore(selected_node_id)
                    # add to local structure
                    util = float(pseudo_task.get_worstCaseComputationCost()/pseudo_task.get_period())
                    node_and_mappedtasks[selected_node_id]['util'] += util
                    node_and_mappedtasks[selected_node_id]['mapped_tasks'].append(pseudo_task)
                    # add to task objs
                    pseudo_task_objs.append(pseudo_task)
                
            self._map_to_vidstrm_mappingtbl(frames_mapping_priass_combined, wf_id, strm_id)                            
            return (frames_mapping_priass_combined, frame_priorities)
        else:
            return (None, None)
    
    
    
    #####################################################################################
    # TASKMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_SINGLENODE_LOWEST_UTIL
    #####################################################################################
    # first the vid stream is assigned a frame-level semi-dynamic priority scheme
    # (PR: lowest res first)
    # then,
    # (MP: map all tasks to a single core - the lowest utilised)
    def taskMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPSingleCore_LowestUtil(self, strm_specs):
        # build pseudo frame-mappings dict
        empty_frame_mappings = self._get_empty_frame_mappings_dict(strm_specs)
        
        # get frame level priorities
        frame_priorities = self.RM_instance.taskPriAssigner.taskSemiDynPriSch_getFramePriority_LowestResFirst(strm_specs, empty_frame_mappings)
                     
        # get list of nodes that are free 
        free_nodes_list = self.RM_instance.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL)
        
        node_and_utils = OrderedDict()        
        # maintain a (node, tqlevel) dict internally
        for node in free_nodes_list: 
            node_and_utils[node.get_id()] = { 
                                                    'util' : self.RM_instance.RunTimeApps.getNodeEstimatedUtilisation(node_id=node.get_id())
                                                  }         
        
        # we have more than one option        
        if(len(free_nodes_list)>0):
    
            wf_id = strm_specs['wf_id']
            strm_id = strm_specs['vid_strm_id']
            gop_struct = strm_specs['gop_struct']        
            frames_mapping_priass_combined = {} 
    
            # find lowest utilised node
            selected_node_id = self._get_node_with_min_utilisation(node_and_utils)
    
            pseudo_task_objs = []
            for fr_ix, each_f in enumerate(gop_struct):                    
                # assign
                frames_mapping_priass_combined[fr_ix] = selected_node_id
                
            self._map_to_vidstrm_mappingtbl(frames_mapping_priass_combined, wf_id, strm_id)                            
            return (frames_mapping_priass_combined, frame_priorities)
        else:
            return (None, None)
    
    
    
    #####################################################################################
    # TASKMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_RANDOMMAPPING
    #####################################################################################
    # first the vid stream is assigned a frame-level semi-dynamic priority scheme
    # (PR: lowest res first)
    # then,
    # (MP: map all tasks to a random cores)
    def taskMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPRandom(self, strm_specs):
        # build pseudo frame-mappings dict
        empty_frame_mappings = self._get_empty_frame_mappings_dict(strm_specs)
        
        # get frame level priorities
        frame_priorities = self.RM_instance.taskPriAssigner.taskSemiDynPriSch_getFramePriority_LowestResFirst(strm_specs, empty_frame_mappings)
                     
        # get list of nodes that are free 
        free_nodes_list = self.RM_instance.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL)

        # we have more than one option        
        if(len(free_nodes_list)>0):
    
            wf_id = strm_specs['wf_id']
            strm_id = strm_specs['vid_strm_id']
            gop_struct = strm_specs['gop_struct']        
            frames_mapping_priass_combined = {} 
            
            for fr_ix, each_f in enumerate(gop_struct):                    
                selected_node = random.choice(free_nodes_list) # random selection
                frames_mapping_priass_combined[fr_ix] = selected_node.get_id()
                
            self._map_to_vidstrm_mappingtbl_overwrite(frames_mapping_priass_combined, wf_id, strm_id)                            
            return (frames_mapping_priass_combined, frame_priorities)
        else:
            return (None, None)
    
    
    
    
    
    #####################################################################################
    # TASKMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_MOSTSLACK_VIA_VTMTBL
    #####################################################################################
    # first the vid stream is assigned a frame-level semi-dynamic priority scheme
    # (PR: lowest res first)
    # then,
    # (MP: map tasks to the PE that gives highest slack - determined via the volatile task mapping table)
    def taskMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPMostSlack_ViaTMTBL(self, strm_specs):
        # build pseudo frame-mappings dict
        empty_frame_mappings = self._get_empty_frame_mappings_dict(strm_specs)
        
        # get frame level priorities
        frame_priorities = self.RM_instance.taskPriAssigner.taskSemiDynPriSch_getFramePriority_LowestResFirst(strm_specs, empty_frame_mappings)
                     
        # get list of nodes that are free 
        free_nodes_list = self.RM_instance.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL)
       
        copy_vtmtbl = self._get_deepcopy_volatiletaskmappingtable()
        #copy_vnoctt = self.RM_instance.flow_table.getVNOCTT_copy()
        
        if(len(free_nodes_list)>0):    
            wf_id = strm_specs['wf_id']
            strm_id = strm_specs['vid_strm_id']
            gop_struct = strm_specs['gop_struct']        
            frames_mapping_priass_combined = {} 
            
            for fr_ix, each_f in enumerate(gop_struct):                
                pseudo_task = self._get_pseudo_task(fr_ix, frame_priorities[fr_ix], 0, strm_specs)
                pseudo_task_pri = frame_priorities[fr_ix]  
                node_level_cumremslack = {}
                for each_node in free_nodes_list:
                    node_cum_remslack = self._get_node_cumulative_rem_slack_viavtmtbl(pseudo_task, each_node.get_id(), pseudo_task_pri, copy_vtmtbl)[1]
                    node_level_cumremslack[each_node.get_id()] = node_cum_remslack
                
#                 print "--"
#                 pprint.pprint(free_nodes_list)
#                 print "--"
#                 pprint.pprint(node_level_cumremslack)
#                 print "--"
                
                # get node which gives most cumslack
                max_cumslack =  np.max(node_level_cumremslack.values())                  
                selected_node_id = [k for k,v in node_level_cumremslack.iteritems() if v==max_cumslack][0]
                
                # update local copy of vtmtbl
                if (selected_node_id not in copy_vtmtbl):
                    copy_vtmtbl[selected_node_id] = [self._get_vtmtbl_targettask_entry(pseudo_task, selected_node_id, pseudo_task_pri)]
                else:
                    copy_vtmtbl[selected_node_id].append(self._get_vtmtbl_targettask_entry(pseudo_task, selected_node_id, pseudo_task_pri))
            
                # update frame mapping struct
                frames_mapping_priass_combined[fr_ix] = selected_node_id
                
                
            # update task mapping table    
            self._map_to_vidstrm_mappingtbl_overwrite(frames_mapping_priass_combined, wf_id, strm_id)                            
            return (frames_mapping_priass_combined, frame_priorities)
        else:
            return (None, None)
    
    
    
    
    #####################################################################################
    # TASKMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_TASKSPLITTING_V1
    #####################################################################################
    # first the vid stream is assigned a frame-level semi-dynamic priority scheme
    # (PR: lowest res first)
    # then,
    # (MP: splits the tasks into tiles, assigns the tiles to the PEs)
    def taskMappPriAssCombinedSchImpl_getFrameMnP_PRLowRes_MPTaskSplitting_v1(self, strm_specs):
        # build pseudo frame-mappings dict
        empty_frame_mappings = self._get_empty_frame_mappings_dict(strm_specs)
        
        # get frame level priorities
        frame_priorities = self.RM_instance.taskPriAssigner.taskSemiDynPriSch_getFramePriority_LowestResFirst(strm_specs, empty_frame_mappings)
                     
        # get list of nodes that are free 
        free_nodes_list = self.RM_instance.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL)       
        copy_vtmtbl = self._get_deepcopy_volatiletaskmappingtable()     
        #copy_vnoctt = self.RM_instance.flow_table.getVNOCTT_copy()   
        
        if(len(free_nodes_list)>0):    
            wf_id = strm_specs['wf_id']
            strm_id = strm_specs['vid_strm_id']
            gop_struct = strm_specs['gop_struct']
            
            # (1) sort tasks into dependency order - perform topological sort on the graph
            # (2) sort bins in descending order of cumulative WCRS - reordering is every time a new task is added
            # (3) each task is added to the PE with max cum. WCRS            
            
            # split all the tasks in the GOP into tiles
            # this version of the mapping produces more tasks as well as the mapping/pri-ass
            gop_tasks = strm_specs['gop_tasks']
            sorted_gop_tasks = self._get_sorted_goptasks_dep_order(gop_tasks)
            all_sorted_hevc_tile_tasks = []
            for each_task in sorted_gop_tasks:
                hevc_tile_tasks_per_frame = self._get_tiles_of_tasks(each_task, strm_specs, each_task.get_frameIXinGOP())
                all_sorted_hevc_tile_tasks.extend(hevc_tile_tasks_per_frame)
        
            # for each item check if it can be accomodated into bin_i           
            tile_pri_assignment = {} 
            tile_to_node_mapping = {}            
            for each_tile_task in all_sorted_hevc_tile_tasks:
                # assign to node with max cumslack
                selected_node_id = self._get_node_with_max_wcrs(copy_vtmtbl)
                
                # update local copy of vtmtbl
                if (selected_node_id not in copy_vtmtbl):
                    copy_vtmtbl[selected_node_id] = [self._get_vtmtbl_targettask_entry(each_tile_task, selected_node_id, 
                                                                                       each_tile_task.get_priority())]
                else:
                    copy_vtmtbl[selected_node_id].append(self._get_vtmtbl_targettask_entry(each_tile_task, selected_node_id, 
                                                                                           each_tile_task.get_priority()))                                
                # update frame mapping struct
                tile_task_id = each_tile_task.get_id()
                tile_to_node_mapping[tile_task_id] = selected_node_id
                
                # record pri-ass for the tile
                tile_pri_assignment[tile_task_id] = each_tile_task.get_priority()
                
            # update task mapping table    
            self._map_to_vidstrm_tile_mappingtbl_overwrite(tile_to_node_mapping, tile_pri_assignment, wf_id, strm_id)                            
            return (tile_to_node_mapping, tile_pri_assignment)
        else:
            return (None, None)
    
    
    #####################################################################################
    #####################################################################################
    # HELPER functions
    #####################################################################################
    
    
    #####################################################
    # Helpers: get info from volative task mapping table
    #####################################################
        
    # get the cumulative remaining slack for target node, after mapping new task
    def _get_node_cumulative_rem_slack_viavtmtbl(self, target_task, target_node_id, target_task_pri, copy_vtmtbl):
                
        # insert target task
        if (target_task != None):
            target_task_entry = self._get_vtmtbl_targettask_entry(target_task, target_node_id, target_task_pri)        
            if target_node_id not in copy_vtmtbl:
                copy_vtmtbl[target_node_id] = [target_task_entry]
            else:
                copy_vtmtbl[target_node_id].append(target_task_entry)
                        
        # calculate the cumulative remaining slack for that node        
        node_level_cumslack = []
        node_taskslist = copy_vtmtbl[target_node_id]
        if len(node_taskslist)>0:
            (node_level_cumslack, sum_node_level_cumslack) = self._get_node_wcremcumslack(node_taskslist)            
        else:
            node_level_cumslack=[sys.maxint]                      
        return (node_level_cumslack, np.sum(node_level_cumslack))
    
    
    def _get_node_wcremcumslack(self, node_taskslist):
        node_level_cumslack=[]
        for each_task in node_taskslist:
            cummulative_wccc_high_pri_tasks = np.sum([t['wcc'] for t in node_taskslist if t['pri']>each_task['pri']])
            task_rem_slack =  each_task['deadline'] - (each_task['wcc'] + cummulative_wccc_high_pri_tasks)
            node_level_cumslack.append(task_rem_slack)    
        return (node_level_cumslack, np.sum(node_level_cumslack))
        
    def _get_node_with_max_wcrs(self, copy_vtmtbl):
        node_level_cumslack = {}
        for each_node_id, each_node_tasklist in copy_vtmtbl.iteritems():
            (node_level_cumslack_pertask, node_level_cumslack) = self._get_node_wcremcumslack(each_node_tasklist)
            node_level_cumslack[each_node_id] = node_level_cumslack
        
        # get max node with cumslack
        if len(node_level_cumslack.keys())>0:
            max_val = np.max(node_level_cumslack.values())
            selected_node_id = [k for k,v in node_level_cumslack.iteritems() if v==max_val][0]
            return selected_node_id
        else:
            return 0 # first node            
          
    def _get_vtmtbl_targettask_entry(self, target_task, target_node_id, target_task_pri):
        entry = {
            'task_id' : target_task.get_id(), 
            'node_id' : target_node_id,
            'release_time': self.env.now,
            'wcc' : target_task.get_worstCaseComputationCost(),
            'status' : -1,
            'pri': target_task_pri,
            'deadline' : target_task.getEstimatedRelativeDeadline_Div_x(), # hevc has large tasks, so can't use EQF
            'deps_completed' : []
        }
        return entry
        
    def _get_deepcopy_volatiletaskmappingtable(self):
        temp_vtmtbl = dict(self.RM_instance.get_volatile_task_mapping_table())
        new_vtmtbl = {}
        for k,v in temp_vtmtbl['runtime_task_mapping'].iteritems():
            new_vtmtbl[k] = copy.deepcopy(v)
        return new_vtmtbl
        
    
    #####################################################
    # Helpers: slack calculation helpers
    #####################################################
        
    def _get_node_with_least_slack_result_for_targettask(self, target_task, nodes_with_mappedtasks):
        list_of_nodes_with_slackvalues = OrderedDict()
        for each_node_id, each_node_mappedtasks in nodes_with_mappedtasks.iteritems():
            result = self._get_task_to_node_packing_results(target_task, each_node_id, each_node_mappedtasks['mapped_tasks'])
            # will any of the existing tasks get affected ?
            if(result['__self_okay_bool'] == True) and (result['__others_okay_bool'] == True):
                list_of_nodes_with_slackvalues[each_node_id] = result['estimated_wc_remaining_slack__self'] + np.sum(result['estimated_wc_remaining_slack__others'])
        
        found_leastslack_node = False
        if(len(list_of_nodes_with_slackvalues)>0):               
            min_slack_val = min(list_of_nodes_with_slackvalues.values())
            selected_node_id =  [k for k,v in list_of_nodes_with_slackvalues.iteritems() if v == min_slack_val][0]
            found_leastslack_node = True
        else: # if none of the nodes can accomodate this task, then we select the lowest utilised
            selected_node_id = self._get_node_with_min_utilisation(nodes_with_mappedtasks)
            found_leastslack_node = False
            
        return (selected_node_id, found_leastslack_node)
            
    
    def _get_nodes_that_can_accomodate_targettask(self, target_task, nodes_with_mappedtasks):
        list_of_nodes_with_slackvalues = OrderedDict()
        acceptable_nodes = []
        for each_node_id, each_node_mappedtasks in nodes_with_mappedtasks.iteritems():
            result = self._get_task_to_node_packing_results(target_task, each_node_id, each_node_mappedtasks['mapped_tasks'])
            # will any of the existing tasks get affected ?
            if(result['__self_okay_bool'] == True) and (result['__others_okay_bool'] == True):
                acceptable_nodes.append(each_node_id)
        
        return acceptable_nodes
    
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
    
    def _get_task_from_runtimeapp_tasklist(self, wf_id, strm_id, ix, task_list):        
        for each_task in task_list:
            if(
               (each_task.get_video_stream_id() == strm_id) and
               (each_task.get_wfid() == wf_id) and
               (each_task.get_frameIXinGOP() == ix)
               ):
                return each_task
        return None
            
    ###########################################################
    # Helpers: get tasks with higher/lower priority, from ibuff
    ###########################################################    
    def _get_tasks_with_higher_priority(self, task_list, target_task, ignore_own_vidstrm_tasks = False):        
        result_list = []
        for each_task in task_list:
            if(ignore_own_vidstrm_tasks==False):
                if(each_task.get_priority() > target_task.get_priority()):
                    result_list.append(each_task)
            else:
                # only add to the high pri list if the tasks are of another stream
                curr_wfstrm_key = str(target_task.get_wfid()) + "_" + str(target_task.get_video_stream_id())  
                each_task_wfstrm_key = str(each_task.get_wfid()) + "_" + str(each_task.get_video_stream_id())              
                if(curr_wfstrm_key != each_task_wfstrm_key):
                    if(each_task.get_priority() > target_task.get_priority()):
                            result_list.append(each_task)
                else:
                    if(each_task.get_frameIXinGOP() in target_task.get_possible_interfering_frame()):                    
                        if(each_task.get_priority() > target_task.get_priority()):
                            result_list.append(each_task)
        return result_list
        
    def _get_tasks_with_lower_priority(self, task_list, target_task, ignore_own_vidstrm_tasks=False):        
        result_list = []
        for each_task in task_list:
            if(ignore_own_vidstrm_tasks==False):
                if(each_task.get_priority() < target_task.get_priority()):
                    result_list.append(each_task)
            else:
                # only add to the high pri list if the tasks are of another stream
                curr_wfstrm_key = str(target_task.get_wfid()) + "_" + str(target_task.get_video_stream_id())  
                each_task_wfstrm_key = str(each_task.get_wfid()) + "_" + str(each_task.get_video_stream_id())              
                if(curr_wfstrm_key != each_task_wfstrm_key):
                    if(each_task.get_priority() < target_task.get_priority()):
                            result_list.append(each_task)
                else:
                    if(target_task.get_frameIXinGOP() in each_task.get_possible_interfering_frame()):                    
                        if(each_task.get_priority() < target_task.get_priority()):
                            result_list.append(each_task)                        
        return result_list
    
    
    # get tasks in the input buffer, if matching a given premapped node-id    
    def _get_tasks_from_ibuffs(self, node_id):        
        tasks_premapped_to_node = []        
        for each_inbuff_id in xrange(len(self.RM_instance.input_buffers)):                   
            for (each_task_id, each_task) in self.RM_instance.input_buffers[each_inbuff_id].get_BufferItemsList().items():
                if(each_task.get_processingCore() == node_id):
                    tasks_premapped_to_node.append(each_task)        
        return tasks_premapped_to_node
        
    #####################################################
    # Helpers: find a specific node
    #####################################################      
    def _get_node_with_min_blocking_time(self, task_pri, node_list):        
        blocking_time_pernode = {}        
        for k,v in node_list.iteritems():
            node_total_bltime = np.sum([task.get_worstCaseRemainingComputationCost() for task in v['task_list'] if task.get_priority() > task_pri])            
            blocking_time_pernode[k] = node_total_bltime        
            min_bltime =  min(blocking_time_pernode.itervalues())
            selected_node_id = [k for k,v in blocking_time_pernode.iteritems() if v == min_bltime][0]        
        return selected_node_id       
    
    
    def _get_nodes_with_min_utilisation_topnpercent(self, node_list_with_util, top_percentage):                
        # sort according to utilisation
        temp_nodeslist = [{'nid': k, 'util':v} for k,v in node_list_with_util.iteritems()]
        temp_nodeslist_sorted = sorted(temp_nodeslist, key=itemgetter('util'), reverse=False)
                
        # get the top percentage
        count = int(top_percentage*len(node_list_with_util))
        if (count == 0) : count = 1
        result_node_list = [x['nid'] for x in temp_nodeslist_sorted[:count]]                
        return result_node_list
        
    
    def _get_node_with_min_utilisation(self,node_list_with_util):        
        min_util =  min(v['util'] for v in node_list_with_util.values())
        selected_node_id = [k for k,v in node_list_with_util.iteritems() if v['util'] == min_util][0]                
        return selected_node_id
    
    def _get_nodes_below_avg_utilisation(self, node_list_with_util, subset_node_list_with_util):
        avg_util = np.mean([v['util'] for v in node_list_with_util.values()])
        nodes_below_avg_util = [k for k, v in subset_node_list_with_util.iteritems() if v['util'] < avg_util]
        return  nodes_below_avg_util
    
    def _get_nodes_with_n_utilisation(self,node_list_with_util, n):
        selected_node_ids = [k for k,v in node_list_with_util.iteritems() if v['util'] == n]               
        return selected_node_ids
            
    def _get_closest_to_nodeid(self, node_list, dst_node_id):
        node_and_distance_list = {}
        for each_node_id in node_list:
            cost = self.RM_instance.interconnect.getRouteCostXY(each_node_id, dst_node_id, 100000)
            node_and_distance_list[each_node_id] = cost
        
        # find closest out of the given nodes
        mindist =  min(node_and_distance_list.values())
        selected_node_id = [k for k,v in node_and_distance_list.iteritems() if v == mindist][0]        
        return selected_node_id
                
    def _get_node_with_min_blocking_time_viaRuntimeApp(self, task_pri, node_list):        
        blocking_time_pernode = {}        
        for k,v in node_list.iteritems():
            if(len(v['task_list']) > 0):
                node_total_bltime = np.sum([task.get_worstCaseComputationCost() for task in v['task_list'] if task.get_priority() > task_pri])            
                blocking_time_pernode[k] = node_total_bltime
            else: blocking_time_pernode[k] = 0.0
                    
            min_bltime =  min(blocking_time_pernode.itervalues())
            selected_node_id = [k for k,v in blocking_time_pernode.iteritems() if v == min_bltime][0]                    
        return selected_node_id 
    
    def _update_link_to_flow_mapping(self, current_link_to_flow_mapping_table, new_route, num_new_flows, dst_nid, src_nid):        
        # what new flows emit from this
        for each_link in new_route:
            if(each_link.get_id() in current_link_to_flow_mapping_table):
                current_link_to_flow_mapping_table[each_link.get_id()].append(self._get_pseudo_flow(src_nid, dst_nid))
            else:
                current_link_to_flow_mapping_table[each_link.get_id()] = [self._get_pseudo_flow(src_nid, dst_nid)]        
        return current_link_to_flow_mapping_table
    
    #####################################################
    # Helpers: update mapping tables
    #####################################################
    def _map_to_vidstrm_mappingtbl(self, frames_mapping, wf_id, strm_id):        
        if wf_id in self.RM_instance.vidstream_frames_mapping_table:            
            if(strm_id not in self.RM_instance.vidstream_frames_mapping_table[wf_id]):
                self.RM_instance.vidstream_frames_mapping_table[wf_id][strm_id] = {}
                self.RM_instance.vidstream_frames_mapping_table[wf_id][strm_id]['frames_mapping'] = frames_mapping
        else:
            self.RM_instance.vidstream_frames_mapping_table[wf_id] = {}
            self.RM_instance.vidstream_frames_mapping_table[wf_id][strm_id] = {}
            self.RM_instance.vidstream_frames_mapping_table[wf_id][strm_id]['frames_mapping'] = frames_mapping    
    
    # same as above, but completely overwrites previous stream mapping
    def _map_to_vidstrm_mappingtbl_overwrite(self, frames_mapping, wf_id, strm_id):                
        if wf_id not in self.RM_instance.vidstream_frames_mapping_table:
            self.RM_instance.vidstream_frames_mapping_table[wf_id] = {}        
        if strm_id not in self.RM_instance.vidstream_frames_mapping_table[wf_id]:
            self.RM_instance.vidstream_frames_mapping_table[wf_id][strm_id] = {}            
        # apply new mapping
        self.RM_instance.vidstream_frames_mapping_table[wf_id][strm_id]['frames_mapping'] = frames_mapping
    
    
    def _map_to_vidstrm_tile_mappingtbl_overwrite(self, frames_mapping, pri_assignment, wf_id, strm_id):  
        if wf_id not in self.RM_instance.vidstream_frames_mapping_table:
            self.RM_instance.vidstream_frames_mapping_table[wf_id] = {}        
        if strm_id not in self.RM_instance.vidstream_frames_mapping_table[wf_id]:
            self.RM_instance.vidstream_frames_mapping_table[wf_id][strm_id] = {}            
        # apply new mapping
        self.RM_instance.vidstream_frames_mapping_table[wf_id][strm_id] = {}
        self.RM_instance.vidstream_frames_mapping_table[wf_id][strm_id]['frames_mapping'] = frames_mapping
        self.RM_instance.vidstream_frames_mapping_table[wf_id][strm_id]['pri_ass'] = pri_assignment
    
    
    
    
    
    
    
    
    
    
    
    #####################################################
    # Helpers: get properties of frame task
    #####################################################            
    def _get_wcc_of_frame(self, frame_ix, strm_specs, frame_type=None):
        if(frame_type==None):
            frame_type = strm_specs['gop_struct'][frame_ix]        
        if (frame_type == "I"): wcc = strm_specs['wcc_I']
        elif (frame_type == "P"): wcc = strm_specs['wcc_P']
        elif (frame_type == "B"): wcc = strm_specs['wcc_B']
        else: sys.exit("TaskMappingSchemesImpl:: _get_wcc_of_frame:: Error")        
        return wcc
    
    def _get_avgccc_of_frame(self, frame_ix, strm_specs):
        frame_type = strm_specs['gop_struct'][frame_ix]        
        if (frame_type == "I"): avgccc = strm_specs['avgcc_I']
        elif (frame_type == "P"): avgccc = strm_specs['avgcc_P']
        elif (frame_type == "B"): avgccc = strm_specs['avgcc_B']
        else: sys.exit("TaskMappingSchemesImpl:: _get_wcc_of_frame:: Error")        
        return avgccc
    
    def _get_avgcc_of_frame(self, frame_ix, strm_specs):
        frame_type = strm_specs['gop_struct'][frame_ix]        
        if (frame_type == "I"): avgcc = strm_specs['avgcc_I']
        elif (frame_type == "P"): avgcc = strm_specs['avgcc_P']
        elif (frame_type == "B"): avgcc = strm_specs['avgcc_B']
        else: sys.exit("TaskMappingSchemesImpl:: _get_wcc_of_frame:: Error")        
        return avgcc
    
    def _get_empty_frame_mappings_dict(self, strm_specs):
        d = {}
        for i in xrange(len(strm_specs['gop_struct'])):
            d[i] = None        
        return d
            
    #####################################################
    # Helpers: impact factors
    #####################################################  
    def _get_factor_impact_to_others(self, node_info, fr_pri, fr_ix, strm_specs):       
        # which tasks already mapped have a lower priority than given frame priority ?
        other_tasks_affected_RMApp = [task for task in node_info['RMAppMappedTasks'] if task.get_priority() <= fr_pri]
        other_tasks_affected_NodeTQ = [task for task in node_info['NodeTQ'] if task.get_priority() <= fr_pri]
        other_tasks_affected_IBuffs = [task for task in node_info['IBuffs'] if task.get_priority() <= fr_pri]
        
        # normalise the above values
        normalised_other_tasks_affected_RMApp = float(len(other_tasks_affected_RMApp)) / float(SimParams.CPUNODE_TASKQ_SIZE)
        normalised_other_tasks_affected_NodeTQ = float(len(other_tasks_affected_NodeTQ)) / float(SimParams.CPUNODE_TASKQ_SIZE)   
        normalised_other_tasks_affected_IBuffs = float(len(other_tasks_affected_IBuffs)) / float(SimParams.CPUNODE_TASKQ_SIZE)
        
        # impact factor is the multiplication
        impact_factor = float(normalised_other_tasks_affected_RMApp * 
                              normalised_other_tasks_affected_NodeTQ * 
                              normalised_other_tasks_affected_IBuffs)        
        return impact_factor
    
    def _get_factor_impact_to_self(self, node_info, fr_pri, fr_ix, strm_specs, 
                                   check_RMAppMappedTasks = True,
                                   check_NodeTQ = True,
                                   check_IBuffs = True,
                                   cc_type="wccc"
                                   ):        
        blockingby_total_interferers_RMApp = [0.0]
        blockingby_total_interferers_NodeTQ = [0.0]
        blockingby_total_interferers_IBuffs = [0.0]
                
        if(cc_type=="wccc"):
            # which tasks already mapped have a lower priority than given frame priority ?
            blockingby_total_interferers_RMApp.extend([task.get_worstCaseComputationCost() for task in node_info['RMAppMappedTasks'] if task.get_priority() > fr_pri])
            blockingby_total_interferers_NodeTQ.extend([task.get_worstCaseComputationCost() for task in node_info['NodeTQ'] if task.get_priority() > fr_pri])
            blockingby_total_interferers_IBuffs.extend([task.get_worstCaseComputationCost() for task in node_info['IBuffs'] if task.get_priority() > fr_pri])
        elif(cc_type=="avgccc"):
            # which tasks already mapped have a lower priority than given frame priority ?
            blockingby_total_interferers_RMApp.extend([task.get_avgCaseComputationCost() for task in node_info['RMAppMappedTasks'] if task.get_priority() > fr_pri])
            blockingby_total_interferers_NodeTQ.extend([task.get_avgCaseComputationCost() for task in node_info['NodeTQ'] if task.get_priority() > fr_pri])
            blockingby_total_interferers_IBuffs.extend([task.get_avgCaseComputationCost() for task in node_info['IBuffs'] if task.get_priority() > fr_pri])
        else:
            sys.exit("_get_factor_impact_to_self:: Error, cc_type invalid")
        
        impact_factor = (np.sum(blockingby_total_interferers_RMApp) if check_RMAppMappedTasks==True else 0.0)  + \
                        (np.sum(blockingby_total_interferers_NodeTQ) if check_NodeTQ==True else 0.0) + \
                        (np.sum(blockingby_total_interferers_IBuffs) if check_IBuffs==True else 0.0)        
        return impact_factor
    
    #####################################################
    # Helpers: get pseudo task/flow
    #####################################################  
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
            pseudo_task.set_dispatchTime(self.env.now)
        
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
            pseudo_task.set_dispatchTime(self.env.now)
            pseudo_task.set_wccIFrame(strm_specs['wcc_I'])
            pseudo_task.set_wccPFrame(strm_specs['wcc_P'])
            pseudo_task.set_wccBFrame(strm_specs['wcc_B'])
        return pseudo_task

    def _get_pseudo_flow(self, src_node_id, dst_node_id):        
        id = 0        
        route = self.RM_instance.interconnect.getRouteXY(src_node_id, dst_node_id)        
        priority = -1
        payload = 100
        basicLatency = self.RM_instance.interconnect.getRouteCostXY(src_node_id, dst_node_id, payload)
        newflow = NoCFlow(id,
                       None, None,
                       [0],
                       [-1],
                       src_node_id, 
                       dst_node_id, 
                       route,
                       priority, 
                       None, 
                       basicLatency, 
                       payload,
                       None,
                       type=-1)
        return newflow
    
    #####################################################
    # Helpers: task splitting
    #####################################################
    
    #get all tile-level tasks for the given target task 
    def _get_tiles_of_tasks(self, target_task, strm_specs, fr_ix, fr_pri_list):
        ':type hevc_frame_task: HEVCFrameTask'
        gop_tasks = strm_specs['gop_tasks']
        hevc_frame_task = gop_tasks[fr_ix]
        
        number_of_tiles = hevc_frame_task.getNumSubTasksTiles()        
        tile_block_partitions = hevc_frame_task.getTileLevel_block_partitions()
        
        new_tile_tasks = {}        
        for tile_id in xrange(number_of_tiles):
            tile_id = hevc_frame_task.get_id() + "_" + tile_id
            num_ctus_in_tile = np.sum([len(s['ctus'].keys()) for s_ix, s in tile_block_partitions[tile_id].iteritems()]) 
            (tile_w, tile_h) = hevc_frame_task.getTileDimensions(num_ctus_in_tile)
            
            num_slices_in_tile = len(tile_block_partitions[tile_id].keys())
            hevc_tile_task = HEVCFrameTask(env = self.env,                                   
                                        id = tile_id,
                                        frame_type = strm_specs['gop_struct'][fr_ix], 
                                        task_granularity = "tile",
                                        frame_ix_in_gop = fr_ix,  # need change ?                                  
                                        gop_struct = strm_specs['gop_struct'], # need change ?
                                        video_stream_id = strm_specs['vid_strm_id'],
                                        wf_id = strm_specs['wf_id'],
                                        frame_h = tile_h, frame_w = tile_w,
                                        frame_rate = strm_specs['fps'],
                                        priority = hevc_frame_task.get_priority(),
                                        num_slices_per_frame = -1,
                                        num_tiles_per_frame =  -1,
                                        interleaved_slice_types = None,
                                        num_ctu_per_slice=-1,
                                        adaptiveGoP_Obj=None,     
                                        load_data_from_file = False,
                                        construct_partitions = False,
                                        hevc_cc=0.0                                       
                                        )
            # manually assign properties 
            tile_wccc = hevc_frame_task.getTileWCCC_viaFiarProportions(tile_h, tile_w)
            hevc_tile_task.set_worstCaseComputationCost(tile_wccc)           
            hevc_tile_task.set_worstCaseRemainingComputationCost(tile_wccc)
            hevc_tile_task.set_avgCaseComputationCost(self._get_avgcc_of_frame(fr_ix, strm_specs)/float(number_of_tiles))
            hevc_tile_task.set_scheduledDispatchTime(self.env.now)
            hevc_tile_task.set_isHeadVideoGop(hevc_frame_task.get_isHeadVideoGop())
            hevc_tile_task.set_isTailVideoGop(hevc_frame_task.get_isTailVideoGop())
            hevc_tile_task.set_priority(fr_pri_list[fr_ix])
            hevc_tile_task.set_period(hevc_tile_task.get_end_to_end_deadline())
            hevc_tile_task.set_dispatchTime(self.env.now)
            hevc_tile_task.set_wccIFrame(None)
            hevc_tile_task.set_wccPFrame(None)
            hevc_tile_task.set_wccBFrame(None)    
            
            
            new_tile_tasks.append(hevc_tile_task)
    
            # properties that are set later
            # - tile dependencies : data to children, data from parents
            # - mapped processing core
    
    def _get_sorted_goptasks_dep_order(self, gop_tasks):
        sorted_ixs = gop_tasks.get_adaptiveGoP_Obj().getDecodingOrder()[0]
        sorted_gop_tasklist = []
        for ix in sorted_ixs:
            sorted_gop_tasklist.append(gop_tasks[ix])
        return sorted_gop_tasklist
    
    
    
    
    #####################################################
    # Helpers: calc CCR
    #####################################################
    def _get_ccr_of_taskgraph(self, strm_specs):        
        frame_h = strm_specs['frame_h']
        frame_w = strm_specs['frame_w']                
        # computation cost
        iframe_cc = strm_specs['wcc_I']
        pframe_cc = strm_specs['wcc_P']
        bframe_cc = strm_specs['wcc_B']     
        mean_computation_cost = float(iframe_cc + pframe_cc + bframe_cc)/3.0
        sum_computation_cost_all_tasks = (iframe_cc*1.0) + (pframe_cc*3.0) + (bframe_cc*8.0)
        mean_computation_cost_all_tasks = (iframe_cc) + (pframe_cc) + (bframe_cc)        
        # communication cost
        max_hop_count = (SimParams.NOC_W-1) + (SimParams.NOC_H-1)         
        payload = ((frame_h * frame_w) * 16)/8 
        arb_cost = SimParams.NOC_PERIOD *7
        noc_flow_cc = NoCFlow.getCommunicationCost(payload, max_hop_count, SimParams.NOC_PERIOD, arb_cost)
        num_edges = 19
        noc_flow_cc_all_edges = (noc_flow_cc * num_edges)        
        # CCR : communication to computation            
        ccr = (noc_flow_cc_all_edges/sum_computation_cost_all_tasks)        
        return ccr
        
        
    