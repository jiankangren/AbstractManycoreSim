import pprint
import sys
#import networkx as nx
import simpy
import matplotlib.pyplot as plt

## local imports
from SimParams import SimParams



# this class maintains a schedule for mapped video streams at runtime
# a node specific schedule is maintained
class RunTimeTaskSchedule:
    
    def __init__(self, env, RMinstance):
        self.env = env
        self.RMinstance = RMinstance
        
        self.schedule = {} # scheudle per node
        
    
    def addTaskToSchedule(self, task, node_id):
        #task_gopix = task.get_frameIXinGOP()        
        self.schedule[node_id].append(task)
    
    def getNodeEstRemainingExecutionTime(self, node_id):
        mapped_tasks = self.schedule[node_id]
        
    
    def getNodeTimeGapBeforeNextJobInvocation(self):
        return None
    
   
        