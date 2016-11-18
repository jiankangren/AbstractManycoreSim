import pprint
import sys
import itertools
import simpy
import random
from operator import itemgetter





        
class TaskSemiDynamicPrioritySchemes:
    
    TASKSEMIDYNAMICPRIORITYSCHEMES_NONE                                 = 0     # this will result in using fixed pri's at design-time
    TASKSEMIDYNAMICPRIORITYSCHEMES_LOWEST_TQ_PRI                        = 1
    TASKSEMIDYNAMICPRIORITYSCHEMES_GLOBALLY_LOWEST_TQ_PRI               = 2
    TASKSEMIDYNAMICPRIORITYSCHEMES_HIGHRES_FIRST                        = 3
    TASKSEMIDYNAMICPRIORITYSCHEMES_LOWRES_FIRST                         = 4
    TASKSEMIDYNAMICPRIORITYSCHEMES_FCFS                                 = 5 # first come first served