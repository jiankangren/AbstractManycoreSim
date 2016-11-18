import pprint
import sys
import simpy

## local imports
from libMappingAndScheduling.MappingPolicy import MappingPolicy
from Buffer import Buffer
from libProcessingElement.CPUNode import CPUNode
from libProcessingElement.Node import NodeStatus
from SimParams import SimParams



class RunTimeTaskManager:
    
    def __init__(self, env, polling_delay, mapping_policy, node_network, input_buffer, output_buffer):        
        self.env = env        
        self.polling_delay = polling_delay        
        self.mapping_policy = mapping_policy
        self.label = "ResourceManager::"+self.mapping_policy.type
        self.status = RMStatus.RM_SLEEPING 
        
        # runtime taskmanager needs to have a view of the system resources      
        self.node_network = node_network
        self.input_buffer = input_buffer
        self.output_buffer = output_buffer
        
        # also need to keep track of the task-to-node mapping
        # all the nodes will also have this table
        self.task_mapping_table = {}
        
        # Start the run process everytime an instance is created.        
        self.processInstance = env.process(self.run())
        
        
    def run(self):
        
        print(self.label + ' : run starting at %f' % self.env.now)
        list_of_nodes_to_interrupt = []
        
        while True:
            self.status = RMStatus.RM_ACTIVE
            #print(self.label + ' : waking up and doing work at:  %f' % self.env.now)
            
            ## perform task mapping ##
            # the RM will map a block of N tasks at once (specified in SimParams)
            if(self.mapping_policy.getNumOfFreeTaskQSlots() >= SimParams.RESOURCEMANAGER_ALLOC_NUM_TASKS):
                for i in xrange(0,SimParams.RESOURCEMANAGER_ALLOC_NUM_TASKS):
                    
                    # get next task and which node to map to 
                    next_task_to_map = self.mapping_policy.getNextTaskToMap()
                    
                    if(next_task_to_map != None):
                        
                        node_to_map = self.mapping_policy.getTasktoNodeMapping(next_task_to_map)
                        
                        if(node_to_map != None):
                        
                            # if cpu node add to it's taskq
                            if(isinstance(node_to_map, CPUNode) == True):
                                node_to_map.add_Task(next_task_to_map)
                                # we then set the release time
                                next_task_to_map.set_releaseTime(self.env.now) # assume releast time = time that the task entered the queue of the core
                                next_task_to_map.set_absDeadline(self.env.now)  # set abs deadline
                                
                                # update mapping table
                                self.updateMappingTables(next_task_to_map.get_id(), node_to_map.get_id())
                                
                                print(self.label + ' : (mapping_table_size=%d) mapped task-%d to node-%d at:  %f' % (len(self.task_mapping_table), next_task_to_map.get_id(),node_to_map.get_id(), self.env.now))
                                
                            else:
                                print(self.label + ' : Not a CPU node!!! at:  %f' % self.env.now)
                                sys.exit()
                                
                          
                            # remove task from input buffer
                            self.input_buffer.remove_Item_byKey(next_task_to_map.get_id())
                            
                            # decrement simpy container counter                    
                            self.InputBuffer_get(1)
                            
                            # add node to the list of nodes to wake up
                            list_of_nodes_to_interrupt = self.WakeSleepingNodesAddNode(list_of_nodes_to_interrupt, node_to_map)
                            
                        else:
                            print(self.label + ' : All nodes are BUSY! at:  %f' % self.env.now)
                            #i=1
                    else:
                        #print(self.label + ' : InputBuffer is NULL at:  %f' % self.env.now)
                        i=1            
                
                
                self.WakeSleepingNodes(list_of_nodes=list_of_nodes_to_interrupt)
                list_of_nodes_to_interrupt = []
                
            ## go back to sleep - can be interrupted
            try:
                self.status = RMStatus.RM_SLEEPING
                yield self.env.timeout(self.polling_delay)
            except simpy.Interrupt: # if sleeping - now gets woken up
                self.status = RMStatus.NODE_JUSTWOKEUP
                print(self.label + ' : I got interrupted, was sleeping, at : %f' % self.env.now)
                            
            
    
    # updates local table AND the slave tables
    def updateMappingTables(self, task_id, node_id):
        # local table
        entry = {
                 'node_id' : node_id,
                 'release_time' : None
                 }
        self.task_mapping_table[task_id] = entry
        
        # slave tables
        for each_node in self.node_network.get_Nodes():
            each_node.updateMappingTable(self.task_mapping_table)
        
    
    
    def InputBuffer_get(self,n):
        self.input_buffer.simpy_container_instance.get(n)
    
    
    ## getters
    def get_processInstance(self):
        return self.processInstance
    
    ## wake invactive nodes ##    
    
    
    ## if node is not in this list, then add to list
    def WakeSleepingNodesAddNode(self, list, node):
        for each_item in list:
            if(each_item.get_id() == node.get_id()):
                return list
        
        list.append(node)
        return list
    
    
    def WakeSleepingNodes(self, list_of_nodes=None):
        if (list_of_nodes == None): # empty list so we wake up all nodes
            for each_node in self.node_network.get_Nodes():
                if(each_node.get_status() == NodeStatus.NODE_IDLE):
                    #print(self.label + "::WakeSleepingNodes: node="+str(each_node.get_id()))
                    # interrupt the sleeping node
                    each_node.processInstance.interrupt()
        else:
            for each_node in list_of_nodes:
                if(each_node.get_status() == NodeStatus.NODE_IDLE):
                    #print(self.label + "::WakeSleepingNodes: node="+str(each_node.get_id()))
                    # interrupt the sleeping node
                    each_node.processInstance.interrupt()
                
    def WakeSingleSleepingNode(self, node):        
        if(node.get_status() == NodeStatus.NODE_IDLE):
            #print(self.label + "::WakeSingleSleepingNode: node="+str(node.get_id()))
            # interrupt the sleeping node
            node.processInstance.interrupt()
            
    
    ### For Debug ###    
    def showTaskMappingTable(self):
        print "RunTimeTaskManager::showTaskMappingTable"
        print "----------------------------------------"
        pprint.pprint(self.task_mapping_table)
        print "----------------------------------------"
            
        
class RMStatus:
    RM_SLEEPING       = 1     # i.e sleeping
    RM_BUSYWAITING    = 2     # i.e waiting for someone else/resource
    RM_BUSY           = 3     # i.e busy computing
    RM_ACTIVE         = 4     # i.e. ready and doing work    
    NODE_JUSTWOKEUP   = 5
    