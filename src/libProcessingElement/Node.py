import pprint

import simpy



## local imports




class Node:
    
    def __init__(self, env, type, id):
        self.env = env
        self.type = type
        self.id = id
        self.processInstance = None
        self.status = NodeStatus.NODE_IDLE
        self.outputBuffInstance = None
        self.task_mapping_table = {}    # slave task mapping table
        self.resource_manager_instance = None
        
        self.node_network = None    # need to have access to other nodes ? (not sure about this..)
        self.onchip_network = None  # need to have access to the NoC
        
        self.link_relationship_tbl = {}
        
    
    def __repr__(self):
        debug = "<Node "         
        debug += " type=" + self.type
        debug += " id=" + str(self.id)       
        debug += " />"   
        
        return debug
    
    ## setters ##
    def set_processInstance(self, p):
        self.processInstance = p    
    def set_outputBuffInstance(self,buff):
        self.outputBuffInstance  = buff   
    def set_node_network(self, nn):
        self.node_network = nn
    def set_onchip_network(self, noc):
        self.onchip_network = noc
    def set_resourceManagerInstance(self, rm):#
        self.resource_manager_instance = rm
    def set_status(self, status):
        self.status = status
    
    def set_link_relationship(self, link, k): 
        # possible keys :
        # {NORTH_I, NORTH_O}, {SOUTH_I, SOUTH_O}, {WEST_I, WEST_O}, {EAST_I,EAST_O}, {LOCAL_I,LOCAL_O}
        if k not in self.link_relationship_tbl:
            self.link_relationship_tbl[k] = link
        else:
            pass
        
    
    ## getters ##
    def get_id(self):
        return self.id    
    def get_status(self):
        return self.status    
    def get_type(self):
        return self.type
    
    ## manage task mappign table ##
    def updateMappingTable(self, new_table):
        self.task_mapping_table = new_table
    def getTaskMappedNode(self, task_id):
        mapped_node = None
        try:
            mapped_node = self.resource_manager_instance.task_mapping_table[task_id]['node_id']           
        except KeyError:
            mapped_node = None
            #self.resource_manager_instance.showTaskMappingTable()
        
        return mapped_node
    
    def get_resourceManagerInstance(self, rm):#
        return self.resource_manager_instance
    
class NodeStatus:
    NODE_IDLE           = 1     # i.e sleeping
    NODE_BUSYWAITING    = 2     # i.e waiting for someone else/resource
    NODE_BUSY           = 3     # i.e busy computing
    NODE_ACTIVE         = 4     # i.e. ready and just about to process another task
    NODE_BUSY_DATAIO    = 5     # i.e. busy writing result to memory
    NODE_JUSTWOKEUP     = 6
    
    
        
    
    
        
    
        