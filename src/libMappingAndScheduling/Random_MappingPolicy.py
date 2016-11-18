import pprint
import random

## local imports
from MappingPolicy import MappingPolicy
from libProcessingElement.CPUNode_ClosedLoop_wIBuffering import CPUNode_ClosedLoop_wIBuffering


class Random_MappingPolicy(MappingPolicy):
    def __init__(self, node_network, input_buffers):
        MappingPolicy.__init__(self, 'Random_MappingPolicy', node_network, input_buffers)
        
    

    
    # for the given task, we have to find a suitable node to map on to
    def getTasktoNodeMapping(self, Task):
        
        # Note : need to construct a list of nodes with non-full
        # task-qs
        
        available_cpu_nodes = []        
        
        for each_node in self.node_network.get_Nodes():            
            
            ## for CPU Nodes
            if(isinstance(each_node,CPUNode_ClosedLoop_wIBuffering)):
                if(each_node.isTaskQFull() == False):
                    available_cpu_nodes.append(each_node)                    
                                
        # select random node from availabe list
        if(len(available_cpu_nodes)>0):
            selected_node = random.choice(available_cpu_nodes)
        else:
            selected_node = None   
                
        return selected_node
        





class Random_Basic_MappingPolicy(MappingPolicy):
    def __init__(self, node_network, input_buffers):
        MappingPolicy.__init__(self, 'Random_Basic_MappingPolicy', node_network, input_buffers)
        
    
    # for the given task, we have to find a suitable node to map on to
    # doesn't check if the node is busy
    def getTasktoNodeMapping(self, Task):
        
        # Note : need to construct a list of nodes with non-full
        # task-qs
        
        available_cpu_nodes = []        
        
        available_cpu_nodes = self.node_network.get_Nodes()
        
        '''
        for each_node in self.node_network.get_Nodes():            
            
            ## for CPU Nodes
            if(isinstance(each_node,CPUNode)):
                if(each_node.isTaskQFull() == False):
                    available_cpu_nodes.append(each_node)       
        '''             
                                
        # select random node from availabe list
        if(len(available_cpu_nodes)>0):
            selected_node = random.choice(available_cpu_nodes)
            
            # check if the node is busy - if true return None
            if(selected_node.isTaskQFull() == True):
                selected_node = None
            
        else:
            selected_node = None
                
        return selected_node
        
        

