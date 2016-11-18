import pprint

## local imports
from SimParams import SimParams


class MappingPolicy:
    
    
    
    def __init__(self, type, node_network, input_buffers):
        
        self.type = type
        ## all mapping policies will have access to the node network and the input buffer
        self.node_network = node_network
        self.input_buffers = input_buffers
        
    
    # which task do we need to map ?
    def getNextTaskToMap(self):
        return self.input_buffers[0].get_Item()
        
    
    # how many free taskQ slots are available in the system ? 
    def getNumOfFreeTaskQSlots(self):
        total_free_slots = 0        
        for each_node in self.node_network.get_Nodes():
            total_free_slots += SimParams.CPUNODE_TASKQ_SIZE - len(each_node.taskQueue)
        
        return total_free_slots