import pprint
import sys
import itertools
import simpy
import random
import numpy as np
import copy
from operator import itemgetter

from SimParams import SimParams
from TaskMappingSchemesFullyDyn import TaskMappingSchemesFullyDyn
from libApplicationModel.MPEG2FrameTask import MPEG2FrameTask

# once a stream has entered the system, the frames of the GoPs are mapped. 
# this mapping is fixed throughout the lifetime of the video stream
class TaskMappingSchemesFullyDynImpl:

    def __init__(self, env, RM_instance):  
        self.env = env
        self.RM_instance = RM_instance
    
    
    def taskMappingSchemeHandler(self, strm_specs):
        if SimParams.FULLYDYNAMIC_TASK_MAPPING_SCHEME == TaskMappingSchemesFullyDyn.TASKMAPPINGSCHEMESFULLYDYN_NONE:
            result =  self.taskMappingSchImpl_getFrameMapping_None(strm_specs)
            
        elif SimParams.FULLYDYNAMIC_TASK_MAPPING_SCHEME == TaskMappingSchemesFullyDyn.TASKMAPPINGSCHEMESFULLYDYN_RANDOM:
            result =  self.taskMappingSchImpl_getFrameMapping_Random(strm_specs)
        
        elif SimParams.FULLYDYNAMIC_TASK_MAPPING_SCHEME == TaskMappingSchemesFullyDyn.TASKMAPPINGSCHEMESFULLYDYN_LOWESTUTIL_NEARESTPARENT:
            result =  self.taskMappingSchImpl_getFrameMapping_LowestUtilNearestParent(strm_specs)
        
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
    # TASKMAPPINGSCHEMESFULLYDYN_LOWESTUTIL_NEARESTPARENT
    #####################################################################################
    # assign a node randomly, out of the ones that have capacity in tq
    def taskMappingSchImpl_getFrameMapping_LowestUtilNearestParent(self, strm_specs):
        i=1
        frames_mapping = {}
        
        # get list of nodes that are free 
        free_nodes_list_ascorder = self.RM_instance.getNodes_TQNonFull(safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL)        
        
        if(len(free_nodes_list_ascorder)>0):
            
            # get node utils
            all_node_utils = copy.deepcopy(self.RM_instance.getNodeTQWCUtils())        
            
            wf_id = strm_specs['wf_id']
            strm_id = strm_specs['vid_strm_id']
            gop_struct = strm_specs['gop_struct']        
            
            # for each frame, go through each node and evaluate the cost-function
            # then select mapping accordingly        
            for fr_ix, each_f in enumerate(gop_struct):
                
                lowest_node_util = min([v for k,v in all_node_utils.iteritems()])                
                nodesids_with_lowest_util = [k for k,v in all_node_utils.iteritems() if v == lowest_node_util]
                    
                # if I-frame treat different, if another frame, we have a choice
                closest_parent_frix_in_dag = self._get_pseudo_task(fr_ix, -1, 0, strm_specs ).get_my_closest_parent()
                if(closest_parent_frix_in_dag == None):
                    selected_node_id = nodesids_with_lowest_util[0] # don't care which node
                else:       
                    
                    # get closest N hop neighbours of the parent task
                    N=2
                    N_hop_neighbours_of_parenttask_nid = self.RM_instance.interconnect.getNodesNHops(frames_mapping[closest_parent_frix_in_dag],N)
                    
                    # select node with lowest util from the neighbour selection
                    temp_neighbour_node_utils = {}
                    for each_nid in N_hop_neighbours_of_parenttask_nid:                        
                        temp_neighbour_node_utils[each_nid] = all_node_utils[each_nid]
                    
                    # find min util
                    min_nn_util = np.min(temp_neighbour_node_utils.values())
                    nid_min_nn_util = [k for k,v in temp_neighbour_node_utils.iteritems() if v==min_nn_util][0]
                    selected_node_id = nid_min_nn_util
                
                # assign
                frames_mapping[fr_ix] = selected_node_id
                ## update dict ##
                pseudo_task = self._get_pseudo_task(fr_ix, -1, selected_node_id, strm_specs )
                pseudo_task_util = float(pseudo_task.get_worstCaseComputationCost()/pseudo_task.get_period())                             
                all_node_utils[selected_node_id] += pseudo_task_util
                
            # update mapping table    
            self._map_to_vidstrm_mappingtbl(frames_mapping, wf_id, strm_id)                    
            return frames_mapping
        else:
            return None
        
    
    
    
    #####################################################################################
    #####################################################################################
    # HELPER functions
    #####################################################################################
    def _map_to_vidstrm_mappingtbl(self, frames_mapping, wf_id, strm_id):
        if wf_id in self.RM_instance.vidstream_frames_mapping_table:            
            if(strm_id not in self.RM_instance.vidstream_frames_mapping_table[wf_id]):
                self.RM_instance.vidstream_frames_mapping_table[wf_id][strm_id] = {}
                self.RM_instance.vidstream_frames_mapping_table[wf_id][strm_id]['frames_mapping'] = frames_mapping
            else: #overwrite
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

        
        