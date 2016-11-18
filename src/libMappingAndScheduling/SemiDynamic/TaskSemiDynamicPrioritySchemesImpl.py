import pprint
import sys
import itertools
import simpy
import random

from libApplicationModel.Task import TaskModel
from libApplicationModel.MPEG2FrameTask import MPEG2FrameTask
from libApplicationModel.HEVCFrameTask import HEVCFrameTask
from SimParams import SimParams
from TaskSemiDynamicPrioritySchemes import TaskSemiDynamicPrioritySchemes
        
class TaskSemiDynamicPrioritySchemesImpl:
    
    def __init__(self, env, RM_instance):  
        self.env = env
        self.RM_instance = RM_instance
    
    
    def taskSemiDynPriSchemeHandler(self, strm_specs, frame_mappings):
        if (SimParams.DYNAMIC_TASK_PRIASS_SCHEME == TaskSemiDynamicPrioritySchemes.TASKSEMIDYNAMICPRIORITYSCHEMES_LOWEST_TQ_PRI):
            result =  self.taskSemiDynPriSch_getFramePriority_LowestTQPri(strm_specs, frame_mappings)
            
        elif (SimParams.DYNAMIC_TASK_PRIASS_SCHEME == TaskSemiDynamicPrioritySchemes.TASKSEMIDYNAMICPRIORITYSCHEMES_GLOBALLY_LOWEST_TQ_PRI):
            result =  self.taskSemiDynPriSch_getFramePriority_GlobalLowestTQPri(strm_specs, frame_mappings)
            
        elif (SimParams.DYNAMIC_TASK_PRIASS_SCHEME == TaskSemiDynamicPrioritySchemes.TASKSEMIDYNAMICPRIORITYSCHEMES_NONE):
            result =  self.taskSemiDynPriSch_getFramePriority_None(strm_specs, frame_mappings)
            
        elif (SimParams.DYNAMIC_TASK_PRIASS_SCHEME == TaskSemiDynamicPrioritySchemes.TASKSEMIDYNAMICPRIORITYSCHEMES_HIGHRES_FIRST):
            result =  self.taskSemiDynPriSch_getFramePriority_HighestResFirst(strm_specs, frame_mappings)
            
        elif (SimParams.DYNAMIC_TASK_PRIASS_SCHEME == TaskSemiDynamicPrioritySchemes.TASKSEMIDYNAMICPRIORITYSCHEMES_LOWRES_FIRST):
            result =  self.taskSemiDynPriSch_getFramePriority_LowestResFirst(strm_specs, frame_mappings)
            
        elif (SimParams.DYNAMIC_TASK_PRIASS_SCHEME == TaskSemiDynamicPrioritySchemes.TASKSEMIDYNAMICPRIORITYSCHEMES_FCFS):
            result =  self.taskSemiDynPriSch_getFramePriority_FCFS(strm_specs, frame_mappings)
        
        
        else:
            sys.exit("taskSemiDynPriSchemeHandler:: Error: unknown task pri ass scheme")
            
        
        return result
        
    
    
    
    #####################################################################################
    # TASKSEMIDYNAMICPRIORITYSCHEMES_NONE
    #####################################################################################
    def taskSemiDynPriSch_getFramePriority_None(self, strm_specs, frame_mappings):
        return None
    
    #####################################################################################
    # TASKSEMIDYNAMICPRIORITYSCHEMES_LOWEST_TQ_PRI
    #####################################################################################
    # target task has to get lowest priority in the task queue 
    # already existing tasks will always get higher priority than the new tasks
    # new task will get lowest task pri in queue
    def taskSemiDynPriSch_getFramePriority_LowestTQPri(self, strm_specs, frame_mappings):
        
        pri_assignments = {}
        node_highest_pri_dict = {}  # we need to keep track of temporary pri assignments
        
        for each_frame_ix, each_frame_selected_node_id in frame_mappings.iteritems():
            
            if each_frame_selected_node_id not in node_highest_pri_dict:            
                # find lowest TQ priority in selected node
                selected_node = self.RM_instance.node_network.get_Node(each_frame_selected_node_id)
                
                task_priorities = [each_task.get_priority() for each_task in selected_node.get_TaskQueue()]
                if(len(task_priorities) > 0): 
                    lowest_pri = min(task_priorities)
                else:
                    # if there are no tasks in the queue, then we give the highest priority
                    # as tasks are served, numerically highest priority first.
                    lowest_pri = SimParams.MAX_TASK_PRIORITY 
                
                pri_assignments[each_frame_ix] = lowest_pri-1                
                node_highest_pri_dict[each_frame_selected_node_id] = pri_assignments[each_frame_ix] # now the lowest pri in this node has changed
                
            else:
            
                pri_assignments[each_frame_ix] = node_highest_pri_dict[each_frame_selected_node_id] - 1
                node_highest_pri_dict[each_frame_selected_node_id] = pri_assignments[each_frame_ix] # now the lowest pri in this node has changed
        
        return pri_assignments
        
    
    #####################################################################################
    # TASKSEMIDYNAMICPRIORITYSCHEMES_GLOBAL_LOWEST_TQ_PRI
    #####################################################################################
    # target task has to get lowest priority out of *all* the task queues in the system
    # already existing tasks will always get higher priority than the new tasks
    def taskSemiDynPriSch_getFramePriority_GlobalLowestTQPri(self, strm_specs, frame_mappings):
        
        pri_assignments = {}
        node_highest_pri_dict = {}  # we need to keep track of temporary pri assignments
        
        for each_frame_ix, each_frame_selected_node_id in frame_mappings.iteritems():
            
            if each_frame_selected_node_id not in node_highest_pri_dict:            
                # find lowest TQ priority in all nodes
                globally_lowest_pri = self._findGloballyLowestTQPri()
                                
                pri_assignments[each_frame_ix] = globally_lowest_pri-1                
                node_highest_pri_dict[each_frame_selected_node_id] = pri_assignments[each_frame_ix] # now the lowest pri in this node has changed
                
            else:
            
                pri_assignments[each_frame_ix] = node_highest_pri_dict[each_frame_selected_node_id] - 1
                node_highest_pri_dict[each_frame_selected_node_id] = pri_assignments[each_frame_ix] # now the lowest pri in this node has changed
        
        return pri_assignments
    
            
    
    #####################################################################################
    # TASKSEMIDYNAMICPRIORITYSCHEMES_HIGHRES_FIRST
    #####################################################################################
    # goal : we don't want low-res vids to block high-res vids
    # stratergy : pri = (w*h) + frame_ix_pri + (arr_time * offset)
    def taskSemiDynPriSch_getFramePriority_HighestResFirst(self, strm_specs, frame_mappings):
        
        pri_assignments = {}
        node_highest_pri_dict = {}
        OFFSET = 10
        
        target_vid_resolution = strm_specs['frame_h'] * strm_specs['frame_w'] 
        
        # stratergy : pri = (w*h) + frame_ix_pri + (arr_time * offset)
        for each_frame_ix, each_frame_selected_node_id in frame_mappings.iteritems():            
            pri_assignments[each_frame_ix] = (target_vid_resolution - self._get_frame_pri(strm_specs['gop_struct'], each_frame_ix, strm_specs)) + (self.env.now * OFFSET)
            
        
        return pri_assignments    
    
    #####################################################################################
    # TASKSEMIDYNAMICPRIORITYSCHEMES_LOWRES_FIRST
    #####################################################################################
    # goal : we don't want low-res tasks to block high-res tasks
    # high pri number ==> higher priority
    # stratergy : pri = (MAX_TASK_PRI - (w*h) + frame_ix_pri + (arr_time * offset))    
    def taskSemiDynPriSch_getFramePriority_LowestResFirst(self, strm_specs, frame_mappings):
        pri_assignments = {}
        node_highest_pri_dict = {}
        OFFSET = 10         
        
        target_vid_resolution = strm_specs['frame_h'] * strm_specs['frame_w'] 
        
        # stratergy : pri = (MAX_TASK_PRI - (w*h) + frame_ix_pri + (arr_time * offset))
        for each_frame_ix, each_frame_selected_node_id in frame_mappings.iteritems():                        
            pri_assignments[each_frame_ix] = SimParams.MAX_TASK_PRIORITY - ((target_vid_resolution - self._get_frame_pri(strm_specs['gop_struct'], each_frame_ix, strm_specs)) + 
                                                                (self.env.now * OFFSET))
            
        
        return pri_assignments 
    
    
    #####################################################################################
    # TASKSEMIDYNAMICPRIORITYSCHEMES_FCFS
    #####################################################################################
    # goal : we don't want low-res tasks to block high-res tasks
    # high pri number ==> higher priority
    # stratergy : pri = (MAX_TASK_PRI - ((arr_time + frame_ix_pri*0.000001) * offset))    
    def taskSemiDynPriSch_getFramePriority_FCFS(self, strm_specs, frame_mappings):
        pri_assignments = {}
        node_highest_pri_dict = {}
        OFFSET = 10         
        
#         # stratergy : pri = (MAX_TASK_PRI - (frame_ix_pri + (arr_time * offset)))
#         for each_frame_ix, each_frame_selected_node_id in frame_mappings.iteritems():            
#             pri_assignments[each_frame_ix] = SimParams.MAX_TASK_PRIORITY - (-1*self._get_frame_pri(strm_specs['gop_struct'], each_frame_ix, strm_specs) + 
#                                                                 (self.env.now * OFFSET))        
        
        for each_frame_ix, each_frame_selected_node_id in frame_mappings.iteritems():                        
            pri_assignments[each_frame_ix] = SimParams.MAX_TASK_PRIORITY - ((self.env.now+self._get_frame_pri(strm_specs['gop_struct'], each_frame_ix, strm_specs)) * OFFSET)
                                       
        
        return pri_assignments 
    
    
    
    
    #####################################################################################
    #####################################################################################    
    # HELPER FUNCTIONS    
    #####################################################################################
    #####################################################################################
    
    # find lowest pri in all task queues in the system
    def _findGloballyLowestTQPri(self):
        all_live_task_pri = []
        
        for each_node in self.RM_instance.node_network.get_Nodes():
            each_node_tq_pris = [each_task.get_priority() for each_task in each_node.get_TaskQueue()]
            all_live_task_pri.extend(each_node_tq_pris)
        
        if(len(all_live_task_pri) >0 ):
            globally_lowest_pri = min(all_live_task_pri)
        else:
            # if there are no tasks in the system, then we pick the max pri value by default.
            globally_lowest_pri = SimParams.MAX_TASK_PRIORITY
        
        return globally_lowest_pri
            
        
    
    def _get_frame_pri(self, gopseq, fr_ix, strm_specs):        
        if (SimParams.TASK_MODEL == TaskModel.TASK_MODEL_MHEG2_FRAME_ET_LEVEL):
            return MPEG2FrameTask.calc_FramePriorityInsideGOP(fr_ix)
            
        elif(SimParams.TASK_MODEL in [TaskModel.TASK_MODEL_HEVC_FRAME_LEVEL, TaskModel.TASK_MODEL_HEVC_TILE_LEVEL]): 
            if "gop_tasks" in strm_specs : 
                adaptivegop_obj = strm_specs["gop_tasks"][0].get_adaptiveGoP_Obj()
            else: 
                adaptivegop_obj=None
            return HEVCFrameTask.calc_FramePriorityInsideGOP(fr_ix, adaptivegop_obj, gopseq=gopseq)
            
        
    
    