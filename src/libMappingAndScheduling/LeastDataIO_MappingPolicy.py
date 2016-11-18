import pprint
import operator


## local imports
from MappingPolicy import MappingPolicy
from libProcessingElement.CPUNode_ClosedLoop_wIBuffering import CPUNode_ClosedLoop_wIBuffering



class LeastDataIO_MappingPolicy(MappingPolicy):
    
    def __init__(self, node_network, input_buffers):
        MappingPolicy.__init__(self, 'LeastDataIO_MappingPolicy', node_network, input_buffers)
        
    
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
                                
        available_cpu_nodes.sort(key=operator.methodcaller("get_memWrite"), reverse=False)
       
        selected_node =  available_cpu_nodes[0]
        
        return selected_node