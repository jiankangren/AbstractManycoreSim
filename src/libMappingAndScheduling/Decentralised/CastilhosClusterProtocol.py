import pprint
import sys
import itertools
import simpy
import math, random
from operator import itemgetter
import numpy as np
import inspect
import copy

from SimParams import SimParams
from libDebug.Debug import Debug, DebugCat
from libNoCModel.NoCFlow import NoCFlow, FlowType
from libMappingAndScheduling.Decentralised.PSAlgorithmViewer import PSAlgorithmViewer


#############################################################################################
## Cluster protocol setup class - initialisation functions
#############################################################################################
class CastilhosClusterProtocol:
    def __init__(self, RMInstance):
        self.label = "CastilhosClusterProtocol"        
        self.RMInstance = RMInstance
    
    def constructClusters(self):
        if(SimParams.CCP_ENABLE == True):
            if(self._verifyClusterParams() == True):
                
                # create the cluster groups
                cluster_size = SimParams.CCP_CLUSTER_SIZE[0] * SimParams.CCP_CLUSTER_SIZE[1]
                noc_size = SimParams.NOC_H * SimParams.NOC_W
                
                num_clusters = int(noc_size/cluster_size)
                c_rows = SimParams.CCP_CLUSTER_SIZE[0]
                c_cols = SimParams.CCP_CLUSTER_SIZE[1]
                
                all_node_ids_2darr = np.arange(noc_size).reshape((SimParams.NOC_H,SimParams.NOC_W))            
                clusters_node_2darr = self._blockshaped(all_node_ids_2darr, c_rows, c_cols)
                                
                #pprint.pprint(clusters_node_2darr)
                #sys.exit()
                
                cluster_manager_ids_list = []
                # put all nodes into appropriate clusters            
                for cid, each_cluster_nids in enumerate(clusters_node_2darr):
                    flattened_each_cluster_nids = each_cluster_nids.flatten()
                    
                    # find cluster manager node
                    if(SimParams.CCP_LM_LOCATION_MIDDLE == True):
                        middle_node_id = flattened_each_cluster_nids[int(len(flattened_each_cluster_nids)/2)]
                        cluster_manager_ids_list.append(middle_node_id)
                    else:
                        middle_node_id = flattened_each_cluster_nids[0] # actually corner node
                        cluster_manager_ids_list.append(middle_node_id)                    
                    
                    for each_nid in flattened_each_cluster_nids:                    
                        each_node = self.RMInstance.node_network.get_Nodes()[each_nid]                    
                        each_node.ccpprops.set_cluster_id(cid)
                        
                        # also assign the cluster manager
                        each_node.ccpprops.set_cluster_manager_node_id(middle_node_id)  
                        
                
                # set cluster manager list
                for each_node in self.RMInstance.node_network.get_Nodes():
                    each_node.ccpprops.set_list_cluster_manager_ids(cluster_manager_ids_list)
                
                
                                      
            else:
                sys.exit("Error!! constructClusters:: incorrect sizes")
            
        
    
    def _verifyClusterParams(self):
        cluster_size = SimParams.CCP_CLUSTER_SIZE[0] * SimParams.CCP_CLUSTER_SIZE[1]
        noc_size = SimParams.NOC_H * SimParams.NOC_W
        
        if(noc_size % cluster_size == 0) and (noc_size >= cluster_size):
            return True
        else:
            return False
        
        
    """
    Return an array of shape (n, nrows, ncols) where
    n * nrows * ncols = arr.size

    If arr is a 2D array, the returned array should look like n subblocks with
    each subblock preserving the "physical" layout of arr.
    """
    def _blockshaped(self, arr, nrows, ncols):    
        h, w = arr.shape
        return (arr.reshape(h//nrows, nrows, -1, ncols)
               .swapaxes(1,2)
               .reshape(-1, nrows, ncols))



#############################################################################################
## Cluster protocol node specific class - this class is linked to each node
#############################################################################################
    
class CastilhosClusterProtocolProps:
    
    def __init__(self, env, node_instance):
        self.label = "CastilhosClusterProtocolProps"
        self.env = env
        self.node_instance = node_instance
        self.RMInstance = None
        
        # basic properties
        self.cluster_id = None
        self.cluster_manager_node_id = None
        self.list_cluster_manager_ids = []  # only the CM has this populated
        self.reserved_slave_node_ids = []   # only the CM has this populated
        self.cluster_monitoring_info = {}   # only the CM has this populated
        self.list_loan_delivery = {} # only the CM has this populated
        self.loan_req_count = self.node_instance.get_id() * 1000 # sort of like a unique id for each loan request made
        
        # constants
        self.SLAVE_NOT_FOUND = -1
        
    
    def set_cluster_id(self, cid):
        self.cluster_id = cid
    def set_cluster_manager_node_id(self, cmnid):
        self.cluster_manager_node_id = cmnid
    def set_RMInstance(self, rmi):
        self.RMInstance = rmi
    def set_list_cluster_manager_ids(self, lcmids):
        self.list_cluster_manager_ids = lcmids
        
    
    def get_cluster_id(self):
        return self.cluster_id
    def get_cluster_manager_node_id(self):
        return self.cluster_manager_node_id
    def get_cluster_monitoring_info(self):
        return self.cluster_monitoring_info
    def get_list_cluster_manager_ids(self):
        return self.list_cluster_manager_ids
    
    
    
    ########################################################
    ## Utilities
    ########################################################
    def getClusterbyNodeID(self, node_id):
        for each_node in self.RMInstance.node_network.get_Nodes():
            if each_node.get_id() == node_id:
                return each_node.ccpprops.get_cluster_id()
            
    
    def getClusterManagerByClusterID(self, cluster_id):
        for each_cmid in self.list_cluster_manager_ids:
            cm =  self.RMInstance.node_network.get_Nodes()[each_cmid]
            if cm.ccpprops.get_cluster_id() == cluster_id:
                return each_cmid
    
    
    
    ########################################################
    ## Within Cluster : Slave <-> Master communication
    ########################################################
    # once a task is complete, send notification to cluster manager
    def updateCM_taskComplete(self, finished_task):
        
        if(SimParams.CCP_ENABLE == True):        
            #Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'updateCM_taskComplete::, : finished_task='+str(finished_task.get_id()) + ", nid="+str(self.node_instance.get_id()), DebugCat.DEBUG_CAT_CCPROTOCOL)
             
            payload_metadata = {
                                'finished_task' : finished_task,
                                'node_id' : self.node_instance.get_id(),
                                'cluster_id' : self.get_cluster_id(),
                                'tq_size' : self.node_instance.getTaskQ_level(),
                                'mapped_tasks' : copy.copy(self.node_instance.get_SystemSlack_MappedTasks())
                                
                                # what we really need is the : 
                                # pri, wccc, rt, exect, wf_level_props                                
                                }
                        
            self._sendMsgFlow(
                              finished_task = finished_task, 
                              src_node_id = self.node_instance.get_id(), 
                              dst_node_id = self.get_cluster_manager_node_id(), 
                              payload = SimParams.CCP_SLAVE_MSG_FLOWPAYLOADSIZE,            
                              payload_metadata = payload_metadata,
                              type = FlowType.FLOWTYPE_CCP_SN_CM_UPDATE_TASKCOMPLETE
                              )
            
            
    
    # once a cluster manager received notification, update the monitoring table
    def updateSlaveMonitorInfo_taskCompleteMsgFlowReceived(self, flow):
        
        if(SimParams.CCP_ENABLE == True):
            #Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'updateSlaveMonitorInfo_taskCompleteMsgFlowReceived::, : nid='+ \
            #             str(self.node_instance.get_id()) + ", slave_nid="+str(flow.get_payload_metadata()['node_id']), DebugCat.DEBUG_CAT_CCPROTOCOL)
        
            payload_metadata = flow.get_payload_metadata()            
            slave_node_id = payload_metadata['node_id']
            finished_task = payload_metadata['finished_task']
            slave_node_tq_size =  payload_metadata['tq_size']
            slave_node_cluster_id = payload_metadata['cluster_id']
            slave_node_mapped_tasks = payload_metadata['mapped_tasks']
                        
            # check if this is the correct CM before updating monitoring dict
            if(self.get_cluster_manager_node_id() == self.node_instance.get_id() and
               self.get_cluster_id() == slave_node_cluster_id):
            
                # new entry
                if(slave_node_id not in self.cluster_monitoring_info):
                    self.cluster_monitoring_info[slave_node_id] = {
                                                                   "TQdepth" : slave_node_tq_size,
                                                                   "MPTasks" : slave_node_mapped_tasks 
                                                                   }
                else:
                    self.cluster_monitoring_info[slave_node_id]["TQdepth"] = slave_node_tq_size
                    self.cluster_monitoring_info[slave_node_id]["MPTasks"] = slave_node_mapped_tasks
                    
            else:
                sys.exit("updateSlaveMonitorInfo_taskCompleteMsgFlowReceived:: Error ! This is not a cluster manager")
               
    
    ########################################################
    ## Between Cluster : CM <-> CM
    ########################################################
    
    # CM --> other CMs
    def loanRequest_sendMsg(self, late_task, slave_node_id, current_blocking, current_util,  update_flw_table = True):        
        
        if(SimParams.CCP_ENABLE == True):        
            Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'loanRequest_sendMsg::, : late_task='+str(late_task.get_id()) + \
                         ", cm_id="+str(self.node_instance.get_id()) + \
                          ", loan_req_count="+str(self.loan_req_count), DebugCat.DEBUG_CAT_CCPROTOCOL)
             
            payload_metadata = {
                                'loan_req_count' : self.loan_req_count,
                                'late_task' : late_task,
                                'slave_node_id' : slave_node_id,
                                'cluster_id' : self.get_cluster_id(),
                                'cluster_manager_id' : self.node_instance.get_id(),
                                'current_blocking' : current_blocking,
                                'current_util' :  current_util,
                                
                                # what we really need is the : 
                                # pri, wccc, rt, exect, wf_level_props                                
                                }
            
            for each_neighbour_cmid in self.list_cluster_manager_ids:
                if(each_neighbour_cmid != self.node_instance.get_id()):                      
                    self._sendMsgFlow(
                                      finished_task = None, 
                                      src_node_id = self.node_instance.get_id(), 
                                      dst_node_id = each_neighbour_cmid, 
                                      payload = SimParams.CCP_BASIC_MSG_FLOWPAYLOADSIZE,            
                                      payload_metadata = payload_metadata,
                                      type = FlowType.FLOWTYPE_CCP_LOANREQUEST,
                                      update_flw_table = False
                                      )
            
            self.list_loan_delivery[self.loan_req_count] = {}
            
            if(update_flw_table==True):
                self.RMInstance.flow_table.updateTable(fire=True)
            
            
            
            self.loan_req_count += 1
            
        
    def loanRequest_receivedMsg(self, flow):
        if(SimParams.CCP_ENABLE == True):
            src_id = flow.get_source()
            old_node_id = flow.get_payload_metadata()['slave_node_id']
            late_task = flow.get_payload_metadata()['late_task']
            loan_req_count = flow.get_payload_metadata()['loan_req_count']
            old_node_util = flow.get_payload_metadata()['current_util']
            
            Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'loanRequest_receivedMsg::, :'  + \
                         ", cm_id="+str(self.node_instance.get_id()) + ", src_id="+str(src_id) + \
                          ", loan_req_count="+str(loan_req_count), DebugCat.DEBUG_CAT_CCPROTOCOL)
            
            # redirect message to remapping handler
            selected_node_id = self.node_instance.taskremapping_decent_scheme_instance.taskReMappingDecentSchImpl_CCP_LoanReq_v2(self.node_instance.get_id(),                                                                                                                                 
                                                                                                                                flow,
                                                                                                                               self.reserved_slave_node_ids,
                                                                                                                               old_node_util )
            
            if(selected_node_id != None):
                Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'loanRequest_receivedMsg::, :'  + \
                         ", cm_id="+str(self.node_instance.get_id()) + ", src_id="+str(src_id) + \
                          ", loan_req_count="+str(loan_req_count) + ":: +++ SLAVE FOUND !!", DebugCat.DEBUG_CAT_CCPROTOCOL)   

                # reserve the selected slave
                self.reserved_slave_node_ids.append(selected_node_id)
                self.loanDelivery_sendMsg(selected_node_id, flow.get_payload_metadata()['cluster_manager_id'], old_node_id, late_task, loan_req_count)            
            else:
                Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'loanRequest_receivedMsg::, :'  + \
                         ", cm_id="+str(self.node_instance.get_id()) + ", src_id="+str(src_id) + \
                          ", loan_req_count="+str(loan_req_count) + ":: ---- NO SUITABLE SLAVE FOUND !!", DebugCat.DEBUG_CAT_CCPROTOCOL) 
                 
                self.loanDelivery_sendMsg(self.SLAVE_NOT_FOUND, flow.get_payload_metadata()['cluster_manager_id'], old_node_id, late_task, loan_req_count)

       
    
    # other CMs --> CM
    def loanDelivery_sendMsg(self, selected_node_id, dst_cm_id, old_node_id,late_task, loan_req_count):
        #print "loanDelivery_sendMsg: enter"
        if(SimParams.CCP_ENABLE == True):
            Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'loanDelivery_sendMsg::, :'  + \
                         ", cm_id="+str(self.node_instance.get_id()) + ", dst_cm_id=" + str(dst_cm_id) + \
                          ", loan_req_count="+str(loan_req_count), DebugCat.DEBUG_CAT_CCPROTOCOL)             
            payload_metadata = {
                                'loan_req_count' : loan_req_count,
                                'late_task' : late_task,
                                'old_node_id' : old_node_id,
                                'selected_node_id' : selected_node_id,                                
                                'reply_from_cluster_id' : self.get_cluster_id(),
                                'reply_from_cluster_manager_id' : self.node_instance.get_id(),                       
                                }
            
            self.env.process(self._sendMsgAfterDelay(
                              finished_task = None, 
                              src_node_id = self.node_instance.get_id(), 
                              dst_node_id = dst_cm_id, 
                              payload = SimParams.CCP_BASIC_MSG_FLOWPAYLOADSIZE,            
                              payload_metadata = payload_metadata,                              
                              type = FlowType.FLOWTYPE_CCP_LOANDELIVERY
                              ))
                                         
            
        
    
    def loanDelivery_receivedMsg(self, flow):
        if(SimParams.CCP_ENABLE == True):
            src_id = flow.get_source()
            remote_cluster_manager_id = flow.get_payload_metadata()['reply_from_cluster_manager_id']
            remote_slave_id = flow.get_payload_metadata()['selected_node_id']
            old_node_id = flow.get_payload_metadata()['old_node_id']
            late_task = flow.get_payload_metadata()['late_task']
            loan_req_count = flow.get_payload_metadata()['loan_req_count']
            
            Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'loanDelivery_receivedMsg::, :'  + \
                         ", cm_id="+str(self.node_instance.get_id()) + ", src_id="+str(src_id) + \
                          ", loan_req_count="+str(loan_req_count), DebugCat.DEBUG_CAT_CCPROTOCOL)
            
            if(remote_cluster_manager_id not in self.list_loan_delivery[loan_req_count]):                
                self.list_loan_delivery[loan_req_count][remote_cluster_manager_id] = remote_slave_id
            
            # start checking loan del requests only when all replies have been received
            if(len(self.list_loan_delivery[loan_req_count].keys()) == (len(self.list_cluster_manager_ids) -1)):                
                # check if all replies have been received            
                selected_cluster_manager_id = self.node_instance.taskremapping_decent_scheme_instance.taskReMappingDecentSchImpl_CCP_LoanReply(self.list_loan_delivery[loan_req_count], old_node_id, late_task)
                
                # rejected cluster managers
                #rej_cm_list = [(nid, self.list_loan_delivery[nid]) for nid in self.list_loan_delivery.keys() if nid != selected_cluster_manager_id]
                rej_cm_list = [(cmid, self.list_loan_delivery[loan_req_count][cmid]) for cmid, slaveid in self.list_loan_delivery[loan_req_count].iteritems() if slaveid != self.SLAVE_NOT_FOUND]
                
                # notify all other cluster managers to release their resource
                self.loanRelease_sendMsg(rej_cm_list, loan_req_count)
                
                
    # send loan release : CM --> other CMs
    def loanRelease_sendMsg(self, rej_cm_list, loan_req_count):
        if(SimParams.CCP_ENABLE == True):
            Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'loanRelease_sendMsg::, :'  + \
                         ", cm_id="+str(self.node_instance.get_id()) + \
                         ", loan_req_count="+str(loan_req_count), DebugCat.DEBUG_CAT_CCPROTOCOL)
        
        #pprint.pprint(rej_cm_list)
        for each_item in rej_cm_list:            
            payload_metadata = {
                                'loan_req_count' : loan_req_count,
                                'slave_node_id' : each_item[1],
                                'slave_selected' : True,                                                                
                                'cluster_id' : self.get_cluster_id(),
                                'cluster_manager_id' : self.node_instance.get_id(),                       
                                }
                
            self._sendMsgFlow(
                              finished_task = None, 
                              src_node_id = self.node_instance.get_id(), 
                              dst_node_id = each_item[0], # manager
                              payload = SimParams.CCP_BASIC_MSG_FLOWPAYLOADSIZE,            
                              payload_metadata = payload_metadata,                              
                              type = FlowType.FLOWTYPE_CCP_LOANRELEASE,
                              update_flw_table = False
                              )
        
        self.RMInstance.flow_table.updateTable(fire=True)
        
        
        
    def loanRelease_receiveMsg(self, flow):
        if(SimParams.CCP_ENABLE == True):
            src_id = flow.get_source()
            loan_req_count = flow.get_payload_metadata()['loan_req_count']
            Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'loanRelease_receiveMsg::, :'  + \
                         ", cm_id="+str(self.node_instance.get_id()) + \
                         ", src_id="+str(src_id) + \
                         ", loan_req_count=" + str(loan_req_count), DebugCat.DEBUG_CAT_CCPROTOCOL)
            
            release_slave_id = flow.get_payload_metadata()['slave_node_id']
            
            if release_slave_id in self.reserved_slave_node_ids:
                self.reserved_slave_node_ids.remove(release_slave_id)
                
            ## debug
            if len(self.reserved_slave_node_ids) == 0:
                Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'loanRelease_receiveMsg::, :'  + \
                         ", cm_id="+str(self.node_instance.get_id()) + \
                         ":: slave reserve list is now empty !!", DebugCat.DEBUG_CAT_CCPROTOCOL)
        
    
    ########################################################
    ## cluster specific functions
    ########################################################
    def getClusterNodes(self, cluster_id):
        cluster_nodes_list = [] 
        for each_node in self.RMInstance.node_network.get_Nodes():
            if each_node.ccpprops.get_cluster_id() == cluster_id:
                cluster_nodes_list.append(each_node)
        
        return cluster_nodes_list
    
                
    
  
    ########################################################
    ## helper function
    ########################################################
    def _sendMsgAfterDelay(self,
                           finished_task = None, 
                           src_node_id = None, 
                           dst_node_id = None, 
                           payload = None,            
                           payload_metadata = None,
                           type = None,
                           update_flw_table = True):
        
        yield self.env.timeout(SimParams.CCP_LOAN_DELIVERY_MSG_SEND_OFFSET * self.node_instance.get_id())  
        
        if(finished_task != None):
            finished_task_id = finished_task.get_id()
        else:
            finished_task_id = None 
        
        release_time = self.env.now
        nextid = self.RMInstance.flow_table.nextid        
        route = self.RMInstance.interconnect.getRouteXY(dst_node_id, src_node_id)
        priority = SimParams.CCP_FLOWBASEPRIORITY + nextid        
        basic_latency = self.RMInstance.interconnect.getRouteCostXY(dst_node_id, 
                                                                        src_node_id,
                                                                        payload)            
        endTime_wrt_BL = release_time + basic_latency        
        newflow = NoCFlow(nextid,
                           finished_task,
                           finished_task_id,
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
                           type=type,                           
                           payload_metadata=payload_metadata)
        
        
        self.node_instance.lock_RM_FLWtbl()        
        # add to the flow table
        self.RMInstance.flow_table.addFlow(newflow, release_time, basic_latency)
        self.node_instance.release_RM_FLWtbl()
        
        if(update_flw_table == True):
            # update the table        
            self.RMInstance.flow_table.updateTable(fire=True)
        
        #return (newflow, release_time, basic_latency)  
    
        
        
        
    
    def _sendMsgFlow(self,
                     finished_task = None, 
                     src_node_id = None, 
                     dst_node_id = None, 
                     payload = None,            
                     payload_metadata = None,
                     type = None,
                     update_flw_table = True
                     ):        
        
#         curframe = inspect.currentframe()
#         calframe = inspect.getouterframes(curframe, 2)
#         print 'caller name:', calframe[1][3]
        
        if(finished_task != None):
            finished_task_id = finished_task.get_id()
        else:
            finished_task_id = None 
        
        release_time = self.env.now
        nextid = self.RMInstance.flow_table.nextid        
        route = self.RMInstance.interconnect.getRouteXY(dst_node_id, src_node_id)
        priority = SimParams.CCP_FLOWBASEPRIORITY + nextid        
        basic_latency = self.RMInstance.interconnect.getRouteCostXY(dst_node_id, 
                                                                        src_node_id,
                                                                        payload)            
        endTime_wrt_BL = release_time + basic_latency        
        newflow = NoCFlow(nextid,
                           finished_task,
                           finished_task_id,
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
                           type=type,                           
                           payload_metadata=payload_metadata)
        
        
        self.node_instance.lock_RM_FLWtbl()        
        # add to the flow table
        self.RMInstance.flow_table.addFlow(newflow, release_time, basic_latency)
        self.node_instance.release_RM_FLWtbl()
        
        if(update_flw_table == True):
            # update the table        
            self.RMInstance.flow_table.updateTable(fire=True)
        
        return (newflow, release_time, basic_latency)  
    
    
  
    
    
#############################################################################################
## PSAlgorithmProps : node types
#############################################################################################

class CCPNodeType:
    
    NONE                = 0    
    SLAVE_NODE          = 1
    CLUSTER_MANAGER     = 2
    