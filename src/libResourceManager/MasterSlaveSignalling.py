import pprint
import sys
#import networkx as nx
import simpy


## local imports
## local imports
from libMappingAndScheduling.MappingPolicy import MappingPolicy
from libBuffer.Buffer import Buffer
#from libProcessingElement.CPUNode import CPUNode
from libProcessingElement.Node import NodeStatus
from libApplicationModel.MPEG2FrameTask import MPEG2FrameTask
from libApplicationModel.Task import TaskStatus
from libNoCModel.NoCFlowTable import NoCFlowTable
from libNoCModel.NoCFlow import NoCFlow, FlowType
from SimParams import SimParams
from libDebug.Debug import Debug, DebugCat



class MasterSlaveSignalling:
    
    def __init__(self, env, RMinstance):
        self.env = env
        self.RMinstance = RMinstance
        self.master_node_id = 0
    
    
    # make requests to all nodes (broadcast)
    def requestToNodes(self, request):
        
        new_flows_added = []        
        for each_node in self.RMInstance.node_network.get_Nodes():
            if(each_node.get_id() == self.master_node_id):
                i=1
            else:
                metadata = {
                            'type' : request['type'],                            
                            }
                (newmsflow, bl) = self._constructFlow(self.master_node_id, each_node.get_id(), metadata)
                self.RMInstance.flow_table.addFlow(newmsflow, self.env.now, bl)        
                new_flows_added.append(newmsflow.get_id())
                                
        if(len(new_flows_added) > 0):
            self.RMInstance.flow_table.updateTable(fire=True)   # one update for many additions           
                
    
    def replyFromNode(self, flw, node_id):
        i=1
        
    
    def _constructFlow(self, src_nodeid, dst_nodeid, metadata, pri, payload_size):         
        
        # construct new flow
        nextid = self.RMinstance.flow_table.nextid                    
        route = self.RMinstance.interconnect.getRouteXY(src_nodeid, dst_nodeid)
        priority = nextid        
        basicLatency = self.RMinstance.interconnect.getRouteCostXY(src_nodeid, 
                                                                   dst_nodeid,
                                                                   payload_size)
        relase_time = self.env.now
        payload = payload_size
        endTime_wrt_BL = relase_time + basicLatency
        payload_metadata  = metadata     
        
        newflow = NoCFlow(nextid,
                          None, None, None, None,
                          src_nodeid, dst_nodeid, route,
                          priority, 
                          None, 
                          basicLatency, payload, endTime_wrt_BL, 
                          type=FlowType.FLOWTYPE_MASTERSLAVESIGNALLING,
                          payload_metadata=payload_metadata)        
        
        return (newflow, basicLatency)
        
        
        
        
    
#############################################################################################
## MSSignalling : signalling types
#############################################################################################
class MSSignallingType:   
    # request/reply when stream starts (tq content query)
    TYPE_RM2N_REQ_TQINFO_STRMSTART = 1    
    TYPE_N2RM_REP_TQINFO_STRMSTART = 2    
    
    # request/reply when job starts (tq content query)
    TYPE_RM2N_REQ_TQINFO_JOBSTART = 3    
    TYPE_N2RM_REP_TQINFO_JOBSTART = 4
    
    # request/reply when task is going to be released to nodes
    TYPE_RM2N_REQ_TQSIZE_TASKRELEASE = 5    
    TYPE_N2RM_REP_TQSIZE_TASKRELEASE = 6
    
    # interrupts
    TYPE_RM2N_INTERRUPT_TASKRELEASE = 7
    TYPE_N2RM_INTERRUPT_TASKCOMPLETE = 8
    TYPE_N2RM_INTERRUPT_FLOWCOMPLETE = 9
    
