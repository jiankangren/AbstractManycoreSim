import pprint
from collections import OrderedDict


import simpy

# local imports
from libApplicationModel.MPEG2FrameTask import MPEG2FrameTask

class Buffer():
    
    def __init__(self, env, btype, size, safe_level=None):
        self.env = env
        self.btype = type
        self.size = size
        self.safe_level = safe_level
        self.list_of_objects = OrderedDict()   # can be tasks completed or not yet run (FIFO)
        
        self.simpy_container_instance = simpy.Container(self.env, capacity=self.size, init=0)

    ## simpy related    
    def get_simpyContainerInstance(self):
        return self.simpy_container_instance
    
    def simpyContainer_put(self,n):
        yield self.simpy_container_instance.put(n)
    
    def simpyContainer_get(self,n):
        yield self.simpy_container_instance.get(n)
    
    def add_Item(self, item, key):
        if(self.isFull() == False):
            self.list_of_objects[key] = item      
    
    def append_Item(self, item, key):
        if(self.isFull() == False):
            if key not in self.list_of_objects:
                self.list_of_objects[key] = [item]
            else:
                self.list_of_objects[key].append(item)               
                            
       
    def remove_Item_byKey(self, key):
        del self.list_of_objects[key]        
    
    def get_Item(self):
        if(len(self.list_of_objects.items()) != 0 and (self.isEmpty()==False)):     
            tup =  self.list_of_objects.items()[0]  # return first item
            return tup[1]
        else:
            return None
        
    def get_BuffContents(self):
        new_list = [x[1] for x in self.list_of_objects.items()]
        return new_list 
    
    def get_level(self):
        return  self.simpy_container_instance.level
    
    def get_BufferItemsList(self):
        return self.list_of_objects
       
    def status_getCurrentItems(self):
        #return (self.simpy_container_instance.level, self.list_of_objects)
        #return self.simpy_container_instance.level
        return (len(self.list_of_objects.items()), self.simpy_container_instance.level)
    
    def isFull(self):
        return (self.simpy_container_instance.level == self.simpy_container_instance.capacity)
        #print "self.simpy_container_instance.level = " + str(self.simpy_container_instance.level)
        
#         if (self.simpy_container_instance.level == self.simpy_container_instance.capacity):
#             return True
#         else:    
#             return False
        
        #if ((len(self.list_of_objects.items())) == self.size):
        #    return True
        #else:    
        #    return False
    
    def isEmpty(self):
        return (self.simpy_container_instance.level == 0)
                
        #if ((len(self.list_of_objects.items())) == 0):
        #    return True
        #else:
        #    return False
        
    
    ##################################
    # specialist helper functions
    ##################################
    
    # the total lateness of the tasks in the input buffers    
    def get_cumulativeTaskLateness(self):
        cum_lateness = 0.0
        
        for each_item in self.list_of_objects.items():
            
            each_task = each_item[1]
            
            # calculate lateness
            current_time = self.env.now
            dispatched_time = each_task.get_dispatchTime()                
            end_to_end_deadline = each_task.get_end_to_end_deadline()
            
            estimated_lateness = float(float((current_time - dispatched_time)) - float(end_to_end_deadline))
            
            if(estimated_lateness > 0.0):
                cum_lateness += estimated_lateness
        
        
        return cum_lateness
                
            
    ##################################
    # useful for tracking
    ##################################
    # return taskqueue task information    
    def get_BuffTaskInfo(self):
        # ibuff task info:            
        #  - task ugid
        #  - task rem cc (avg, wcc)
        #  - task pri
        #  - task dt, rt
        buff_task_info = []
        for each_item in self.list_of_objects.items():
            each_task = each_item[1]
            buff_task_info.append( 
                [
                 each_task.get_id(),
                 each_task.get_priority(),
                 each_task.get_unique_gop_id(),
                 [each_task.get_avgCaseRemainingComputationCost(), each_task.get_worstCaseRemainingComputationCost()],
                 [each_task.get_dispatchTime(), each_task.get_releaseTime(), each_task.get_taskStartTime()]
                ])
            
        return buff_task_info
    

class BufferType():
    BUFFER_TYPE_INPUT = 1
    BUFFER_TYPE_OUTPUT = 2
    
               
        
    