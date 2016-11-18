import pprint


## local imports
from libProcessingElement.Node import Node

class NodeNetwork:
    def __init__(self):
        self.nodeArray = []
        
    def addNode(self, Node):
        self.nodeArray.append(Node)
        
    def set_outputBuffInstance(self, out_buff_inst):
    
        for each_node in self.nodeArray:
            each_node.set_outputBuffInstance(out_buff_inst)
    
    def set_nodeNetworkAccess(self, noc):
        for each_node in self.nodeArray:
            each_node.set_node_network(self)    
            each_node.set_onchip_network(noc)
            
    def set_resourceManagerInstance(self, rm):
        for each_node in self.nodeArray:
            each_node.set_resourceManagerInstance(rm)
            each_node.ccpprops.set_RMInstance(rm)    
            
        
    def get_Node(self, id):
        for each_node in self.nodeArray:
            if(each_node.get_id()==id):
                return each_node   
            
    def get_Nodes(self):
        return self.nodeArray 