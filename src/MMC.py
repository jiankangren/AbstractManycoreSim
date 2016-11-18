import pprint
import sys
import itertools

## local imports
from SimParams import SimParams
import numpy as np
import time
import random
from libDebug.Debug import Debug, DebugCat
from libNoCModel.NoCFlow import NoCFlow, FlowType
from libResourceManager.Mapper.MapperTypes import MapperTypes

class MMC:
    def __init__(self, env, mmc_locations, node_network, interconnect, noc_h, noc_w, RMInstance):
        self.label = "MMC"
        self.env = env
        self.noc_w =  noc_w
        self.noc_h =  noc_h
        self.mmc_locations = mmc_locations        
        self.node_network = node_network
        self.interconnect = interconnect
        self.RMInstance = RMInstance
        
        self.mmc_to_node_data_transfer_started_task_ids = []
        
        # nodes connected to MMCs
        self.mmc_connected_node_ids = self.get_MMCConnectedNodeIds()
        
        # task to mmc mapping
        self.mmc_task_to_mmcnode_mapping = {}
        self.mmc_vid_to_mmcnode_mapping = {}
        self.mmc_job_to_mmcnode_mapping = {}
        
        # random mmc node selection, pregen
        # if we do this at runtime, then it will offset 
        # the other random calls which happens at runtime
        self.random_mmc_node_selection = itertools.cycle(np.random.choice(self.mmc_connected_node_ids, size=1000))
    
    
    # determine which PEs are connected to the MMCs
    def get_MMCConnectedNodeIds(self):                
#         mmc_connected_nodes = []
#         if SimParams.MMC_CONTROLLER_NUM_PER_SIDE != 1:                   
# #             # for each boundary get the nodes connected to the mmc
# #             for each_mmc_boundary in self.mmc_locations:
# #                 node_ids = self.interconnect.getBoundaryNodes(each_mmc_boundary.upper())            
# #                 for each_nid in node_ids:
# #                     if each_nid not in mmc_connected_nodes:
# #                         mmc_connected_nodes.append(each_nid)
#             sys.exit("get_MMCConnectedNodeIds:: Error ! not implmented yet.. (MMC_CONTROLLER_NUM_PER_SIDE)")
# 
#         else:
#             # for each boundary get the nodes connected to the mmc
#             for each_mmc_boundary in self.mmc_locations:
#                 node_ids = self.interconnect.getBoundaryNodes(each_mmc_boundary.upper())
#                 if SimParams.MMC_CONTROLLER_NUM_PORTS == 2:                
#                     # two ports per side per controller, we assume only 1 mmc per side
#                     ix_nid_div_2 = float(len(node_ids))/2.0                
#                     if SimParams.NOC_W % 2 == 0: # even
#                         side_mmc_connected_nodes_ids = [node_ids[int(ix_nid_div_2-1)], node_ids[int(ix_nid_div_2)]]                     
#                     else: # odd
#                         side_mmc_connected_nodes_ids = [node_ids[int(ix_nid_div_2-1)], node_ids[int(ix_nid_div_2)]]
#                     
#                     for each_nid in side_mmc_connected_nodes_ids:
#                         if each_nid not in mmc_connected_nodes:
#                             mmc_connected_nodes.append(each_nid)
#                 else:
#                     sys.exit("get_MMCConnectedNodeIds:: Error ! not implmented yet.. (MMC_CONTROLLER_NUM_PORTS)")
        
        mmc_connected_nodes = self.interconnect.get_mmc_node_ids()
        
        return mmc_connected_nodes
        
        
    
    
    def remove_task_mmc_to_node_tr_list(self, tid):
        if tid in self.mmc_to_node_data_transfer_started_task_ids:
            self.mmc_to_node_data_transfer_started_task_ids.remove(tid)
    
    def set_RMInstance(self, rmi):
        self.RMInstance = rmi
    
    
    def set_mmc_task_mapping(self, task_id, mmc_node_id):
        if task_id in self.mmc_task_to_mmcnode_mapping:
            sys.exit("MMC::set_mmc_task_mapping: Error ! - taskid already exists")
        else:
            self.mmc_task_to_mmcnode_mapping[task_id] = mmc_node_id
            
    
    
    ###################################################################
    ### Handler to handle calls from runtime managers                ##
    ###################################################################
    
    # manage mmc selection - either using a lookup table or default
    def getMMCPort_handler(self, task_id, mapped_node_id):        
        if SimParams.MMC_SMART_NODE_SELECTION_ENABLE == True: # use lookup table
            if task_id in self.mmc_task_to_mmcnode_mapping:
                #print "getMMCPort_handler:: using premapped mmc"
                selected_mmc_node_id = self.mmc_task_to_mmcnode_mapping[task_id]
            else:
                sys.exit("getMMCPort_handler:: Error - no task id given, smart mmc node selection enabled")                
        else:
            selected_mmc_node_id = self.getClosestMMCPort(mapped_node_id)            
            
        return selected_mmc_node_id
            
    
    ########################################################
    # MMC to/from transfers
    ########################################################    
    def startListofTaskDataTransfers(self, list_of_transfers):
        for each_list_entry in list_of_transfers:
            task = each_list_entry['task']
            node = each_list_entry['node']
            ibuff_id = each_list_entry['ibuff_id']
            
            self.startMMCTONodeDataTransfer(task, node, ibuff_id)
            
        self.RMInstance.flow_table.updateTable(fire=True)
    
    
    def startListofTaskDataTransfers_NonModelled(self, list_of_transfers):
        for each_list_entry in list_of_transfers:
            task = each_list_entry['task']
            node = each_list_entry['node']
            ibuff_id = each_list_entry['ibuff_id']
            
            self.RMInstance.putTaskToNodeTQ_MMCNonModelled(node, task, ibuff_id)
            
    
    # when a task data is requested from the node
    # task data is needed to start task execution
    def startMMCTONodeDataTransfer(self, task, node, ibuff_id):
                
        #src_node_id = self.getClosestMMCPort(node.get_id())
        src_node_id = self.getMMCPort_handler(task.get_id(), node.get_id())
        dst_node_id = node.get_id()
        
        Debug.PPrint("%f"%self.env.now + "," + self.label + "," +
                     'startMMCTONodeDataTransfer:: before GOP execution, : task=%s, %s->%s' % (str(task.get_id()), str(src_node_id), str(dst_node_id)),
                     DebugCat.DEBUG_CAT_MMCNODEDATATRANSFER)
        
        release_time = self.env.now
        nextid = self.RMInstance.flow_table.nextid                    
        route = self.RMInstance.interconnect.getRouteXY(src_node_id, dst_node_id)
        priority = SimParams.MMC_DATAREAD_FLOW_PRIORITY + nextid        
        payload = task.get_mpeg_tasksize()
        basic_latency = self.RMInstance.interconnect.getRouteCostXY(src_node_id, dst_node_id,
                                                                    payload)
        
        endTime_wrt_BL = release_time + basic_latency
        payload_metadata = {
                            'target_task' : task,
                            'mapped_node' : node,
                            'ibuff_id' : ibuff_id                            
                            }
                    
        newflow = NoCFlow(nextid,
                       None,
                       None,
                       None, # list of dst task ids
                       None, # list of dst task ixs
                       src_node_id, 
                       dst_node_id, 
                       route,
                       priority, 
                       None, 
                       basic_latency, 
                       payload,
                       endTime_wrt_BL,
                       type=FlowType.FLOWTYPE_MMCTONODE_DATATRANSFER_RD,                           
                       payload_metadata=payload_metadata)
        
        self.mmc_to_node_data_transfer_started_task_ids.append(task.get_id()) # temporarily record 
        
        self.RMInstance.lock_RM_FLWtbl()
        # add to the flow table
        self.RMInstance.flow_table.addFlow(newflow, release_time, basic_latency)                        
        self.RMInstance.release_RM_FLWtbl()
        
        # update the table        
        #self.RMInstance.flow_table.updateTable(fire=True) 
    
    
    # when a task has completed, we send the picture output to the main memory
    def startNodeToMMCDataTransfer(self, finished_task, node):        
        src_node_id = node.get_id()
        #dst_node_id = self.getClosestMMCPort(src_node_id)
        dst_node_id = self.getMMCPort_handler(finished_task.get_id(), node.get_id())
        
        Debug.PPrint("%f"%self.env.now + "," + self.label + "," +
                     'startNodeToMMCDataTransfer:: after task finishes execution, : task=%s, %s->%s' % (str(finished_task.get_id()), 
                                                                                                        str(src_node_id), str(dst_node_id)),
                                                                                                        DebugCat.DEBUG_CAT_MMCNODEDATATRANSFER)
        
        release_time = self.env.now
        nextid = self.RMInstance.flow_table.nextid                    
        route = self.RMInstance.interconnect.getRouteXY(src_node_id, dst_node_id)
        #priority = SimParams.MMC_DATAWRITE_FLOW_PRIORITY + nextid
        
        if SimParams.SIM_ENTITY_MAPPER_CLASS == MapperTypes.OPENLOOP_WITH_HEVCTILE: # this changed for hevc tile experiments
            #priority = sys.maxint - (finished_task.get_priority() + (self.RMInstance.flow_priority_offset+100) + nextid)
            priority = finished_task.get_priority() + (self.RMInstance.flow_priority_offset+100) + nextid
        else:
            priority = finished_task.get_priority() + (self.RMInstance.flow_priority_offset+100) + nextid
        
        payload = finished_task.get_completedTaskSize()
        basic_latency = self.RMInstance.interconnect.getRouteCostXY(src_node_id, dst_node_id,
                                                                    payload)
        
        endTime_wrt_BL = release_time + basic_latency
        payload_metadata = {
                            'finished_task' : finished_task,
                            'src_node' : node,                                                        
                            }
                    
        newflow = NoCFlow(nextid,
                       None,
                       None,
                       None, # list of dst task ids
                       None, # list of dst task ixs
                       src_node_id, 
                       dst_node_id, 
                       route,
                       priority, 
                       None, 
                       basic_latency, 
                       payload,
                       endTime_wrt_BL,
                       type=FlowType.FLOWTYPE_MMCTONODE_DATATRANSFER_WR,                           
                       payload_metadata=payload_metadata,
                       creation_time=self.env.now)
        
        self.RMInstance.lock_RM_FLWtbl()
        # add to the flow table
        self.RMInstance.flow_table.addFlow(newflow, release_time, basic_latency)                        
        self.RMInstance.release_RM_FLWtbl()
            
        # update the table        
        self.RMInstance.flow_table.updateTable(fire=True) 
    
    
    ########################################################
    # Default MMC selection
    ########################################################
    # default : assumes all nodes at edges has access to the MMC in that edge
    # heuristic : distance
    def getClosestMMCPort(self, src_node_id):  
        #print "getClosestMMCPort:: enter"         
        mmc_node_dist = {}         
        for each_nid in self.mmc_connected_node_ids:
            if each_nid not in mmc_node_dist:
                mmc_node_dist[each_nid] = len(self.interconnect.getPrecalcRouteXY(src_node_id, each_nid)) # task->MMC route
        
        # find closest node        
        selected_mmc_node_id = self._get_key_with_min_val_from_dict(mmc_node_dist)        
        return selected_mmc_node_id
    
        
    def _get_key_with_min_val_from_dict(self, param_dict):
        # find closest node
        min_val = min(param_dict.values())
        list_suitable_keys = [k for k,v in param_dict.iteritems() if v == min_val]
        sorted_suitable_keys = sorted(list_suitable_keys)        
        result_k = sorted_suitable_keys[0]
        return result_k
    
            
        
        
class MMC_SmartPortSelectionTypes:
    # default
    MMC_SMARTPORTSELTYPE_DIST                                       = 0
    
    ##### slow implementations
    MMC_SMARTPORTSELTYPE_LU                                         = 1
    MMC_SMARTPORTSELTYPE_LM                                         = 2
    MMC_SMARTPORTSELTYPE_LUDISTCOMBINED                             = 3
    MMC_SMARTPORTSELTYPE_RANDOM                                     = 4
    MMC_SMARTPORTSELTYPE_IDEAL_V1                                   = 5 # use the real-time flow table
    
    
    
    ##### fast implementations (similar to first fit - the input is first sorted)
    MMC_SMARTPORTSELTYPE_LU_FF                                      = 30
    MMC_SMARTPORTSELTYPE_LM_FF                                      = 31 # fair
    MMC_SMARTPORTSELTYPE_IDEAL_FF_V1                                = 32
    
    # corner-in variants of lu_ff and lm_ff
    MMC_SMARTPORTSELTYPE_LU_CORNERIN_FF                            = 33
    MMC_SMARTPORTSELTYPE_LM_CORNERIN_FF                            = 34
    
    # priority related
    MMC_SMARTPORTSELTYPE_BALANCEDPRI_PROPORTIONAL_FF               = 35
    MMC_SMARTPORTSELTYPE_LOWBLOCKING_PROPORTIONAL_FF               = 36 # blocking-aware
    
    # fast random
    MMC_SMARTPORTSELTYPE_RANDOM_FF                                 = 37
    
    
    # checking parent/children
    MMC_SMARTPORTSELTYPE_INV_PARENT                                = 38 # mmc selected opposite to the parent
    
    
    
    
    
    
    
        
    
    
    