import pprint
import operator

## local imports
from MappingPolicy import MappingPolicy
from libProcessingElement.CPUNode_ClosedLoop_wIBuffering import CPUNode_ClosedLoop_wIBuffering



class FirstFree_MappingPolicy(MappingPolicy):

    def __init__(self, node_network, input_buffers):
        MappingPolicy.__init__(self, 'FirstFree_MappingPolicy', node_network, input_buffers)
        
    

    
    # for the given task, we have to find a suitable node to map on to
    def getTasktoNodeMapping(self, Task):
        
        # Note : need to construct a list of nodes with non-full
        # task-qs
        
        available_cpu_nodes = []       
        selected_node = None 
        
        for each_node in self.node_network.get_Nodes():            
            
            ## for CPU Nodes
            if(isinstance(each_node,CPUNode_ClosedLoop_wIBuffering)):
                if(each_node.isTaskQFull() == False):
                    available_cpu_nodes.append(each_node)                    
                                
        # select random node from availabe list
        for each_node in available_cpu_nodes:
            if(each_node.isTaskQFull() == False):
                selected_node = each_node
                break
        
                
        #available_cpu_nodes.sort(key=operator.methodcaller("get_NumTasksInQ"), reverse=True)        
        #selected_node =  available_cpu_nodes[0]
        
        return selected_node
    
    