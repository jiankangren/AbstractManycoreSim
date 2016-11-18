import pprint
import sys
import math
import itertools
import simpy
import random

## local imports
from libMappingAndScheduling.MappingPolicy import MappingPolicy
from libBuffer.Buffer import Buffer
from libProcessingElement.CPUNode_ClosedLoop_wIBuffering import CPUNode_ClosedLoop_wIBuffering
from libProcessingElement.Node import NodeStatus
from libApplicationModel.MPEG2FrameTask import MPEG2FrameTask
from libNoCModel.NoCFlowTable import NoCFlowTable
from libNoCModel.NoCFlow import NoCFlow, FlowType
from SimParams import SimParams
from libDebug.Debug import Debug, DebugCat


class ScheduleAndMap_TT:
    
    def __init__(self, env, RM_instance):  
        
        self.env = env
        self.RM_instance = RM_instance
        self.label = "ScheduleAndMap_TT"        
              
    ##########################################################################################################################   
    ## schedule and map tasks of MULTIPLE input buffers, interleave
    ## : for each input buff do the following :
    ## - (1) get next task to schedule --> Ti
    ## - (2) find max depandent task (e.g. for B2 is it P1) --> T_dep
    ## - (3) find earliest schedulable time for Ti (based on max dependant task) --> Te = (T_dep_releasetime + T_dep_wcc + tr_delay), assume tr_delay =0
    ## - (4) find list of nodes available on/before Te : Nx[]
    ## - (5) check if T_dep is scheduled on any of Nx[]
    ##    -- if true: find which Node (N) and schedule Ti on this node , flag__same_node_as_dep = TRUE
    ##    -- if false: find earlist available node in Nx[], flag__same_node_as_dep = FALSE
    ## - (6) if (flag__same_node_as_dep == FALSE), then extend the release time of Ti by tr_delay.
    ##########################################################################################################################
    def scheduleAndMapTasks_MultiStream(self):
        
        # task mapping table entry:
#        entry = {
#                 release_time :
#                 wcc : 
#                 node_id : 
#                }   

        tasks_added_to_taskmappingtbl = []
         
        how_many_scheduled_in_stream = [0] * len(self.RM_instance.input_buffers)
        how_many_scheduled_in_node  = [0] * SimParams.NUM_NODES
        
        synch_time_offset = 0
        applied_synch_offset = False
        
        max_num_of_unscheduled_tasks = self._getMaxNumOfTasksUnscheduled_In_AllInBuffs()[1]
        for t in xrange(max_num_of_unscheduled_tasks):
            
            for i_buff_id in xrange(len(self.RM_instance.input_buffers)): 
                
                ### (1) get next unscheduled task in the respective input buffer
                next_task_to_schedule__id = self._getNextUnscheduledTaskID_In_InputBuff(i_buff_id)
                
                if(next_task_to_schedule__id != None):
                    
                    Ti = self.RM_instance.input_buffers[i_buff_id].get_BufferItemsList()[next_task_to_schedule__id]  
                    
                    tasks_added_to_taskmappingtbl.append(Ti)                  
                    
                    ##################################################################################
                    ### special case - for synchronisation issues --- race conditions !!! :(
                    #if(Ti.get_frameIXinGOP() > 0):
                    #    synch_time_offset = 0.0000001
                    #else:
                    #    if(how_many_scheduled_in_stream[i_buff_id] == 0):                        
                    #        synch_time_offset = 0.0000001
                    #    else:
                    #        synch_time_offset = 0                    
                    how_many_scheduled_in_stream[i_buff_id] = how_many_scheduled_in_stream[i_buff_id] + 1
                    ##################################################################################
                    
                    ### (2) find this tasks dependancies - get maximum task-id
                    if (len(Ti.get_dependencies()) > 0):
                        Ti_dep_max = max(Ti.get_dependencies())
                    else:
                        Ti_dep_max = None
                    
                    ### (3) based on the dependancy, find the earliest release time
                    if(Ti_dep_max != None):
                        # search task_mapping table
                        if(Ti_dep_max in self.RM_instance.task_mapping_table):
                            Te = self.RM_instance.task_mapping_table[Ti_dep_max]['release_time'] + self.RM_instance.task_mapping_table[Ti_dep_max]['wcc'] + 0
                        else:
                            print(self.label + ' : scheduleAndMapTasks: Ti_dep_max doesnt exist in task_mapping_table, at : %f' % self.env.now)
                            sys.exit()
                            
                    else: # no dependancies ? then it must be an I-frame, hence check if the task_id-1's finish time
                        prev_task_id = Ti.get_id()-1
                        if(prev_task_id in self.RM_instance.task_mapping_table):
                            Te = self.RM_instance.task_mapping_table[prev_task_id]['release_time'] + self.RM_instance.task_mapping_table[prev_task_id]['wcc'] + 0
                        else: # this would be when task-id=0
                            Te = self.env.now                    
                    
                    Te = Te + synch_time_offset
                    
                    ### (4) find list of nodes available on/before Te
                    (success, list_of_nodes_free_onorbefore_Te) = self._findNodesFreeBeforeTime(Te)    
                    
#                    if(Ti.get_id() == 1656):
#                        print "here 1 - "
#                        pprint.pprint((success, list_of_nodes_free_onorbefore_Te))                                    
                    
                    if(success == True):    # good - we have some choices !
                        if(Ti_dep_max != None):         # if not an i-frame             
                            
                            ### (5) find if Ti_dep is scheduled on any of those nodes in this list, if true schedule on same node - to minimise travel cost
                            Ti_dep_max_mapped_node_id = self.RM_instance.task_mapping_table[Ti_dep_max]['node_id']
                            if(Ti_dep_max_mapped_node_id in list_of_nodes_free_onorbefore_Te):
                                                        
                                tm_entry = {
                                            'node_id' : Ti_dep_max_mapped_node_id,
                                            'release_time' : Te,
                                            'wcc' : Ti.get_worstCaseComputationCost()
                                            }                                                        
                                self.RM_instance.task_mapping_table[Ti.get_id()] = tm_entry                                
                            else: # Ti_dep not in node list, so get the next soonest available node
                                (next_free_node, next_free_time) = self._findFirstFreeFromNodeList(node_list=list_of_nodes_free_onorbefore_Te)
                                tm_entry = {
                                            'node_id' : next_free_node,
                                            'release_time' : Te,
                                            'wcc' : Ti.get_worstCaseComputationCost()
                                            }                                                        
                                self.RM_instance.task_mapping_table[Ti.get_id()] = tm_entry
                        
                        else: # if an i-frame, schedule on any available node
                            (next_free_node, next_free_time) = self._findFirstFreeFromNodeList(node_list=list_of_nodes_free_onorbefore_Te)
                            tm_entry = {
                                        'node_id' : next_free_node,
                                        'release_time' : Te,
                                        #'release_time' : next_free_time,
                                        'wcc' : Ti.get_worstCaseComputationCost()
                                        }                                                        
                            self.RM_instance.task_mapping_table[Ti.get_id()] = tm_entry                            
                            
                    else:
                        # we have no choices, this means none of the nodes are free before Te. Hence :
                        # - see if his dependant task is mapped on to the table, if true, map to same node (reduce comms)
                        # - if no deps or no deps in table, then first-free-node
                        
                        if(Ti_dep_max != None):                            
                            if(Ti_dep_max in self.RM_instance.task_mapping_table):
                                Ti_dep_max_mapped_node_id = self.RM_instance.task_mapping_table[Ti_dep_max]['node_id']
                                tm_entry = {
                                            'node_id' : Ti_dep_max_mapped_node_id,
                                            'release_time' : Te,
                                            'wcc' : Ti.get_worstCaseComputationCost()
                                            }
                                self.RM_instance.task_mapping_table[Ti.get_id()] = tm_entry
                                
                                # CHECK: same node mapping, but lets find if there are other tasks after his dep task mapped to this node 
                                next_avail_timeslot = self._findNodeNextAvailableTimeSlot(Ti_dep_max_mapped_node_id, Ti.get_id())                        
                                if(next_avail_timeslot > self.RM_instance.task_mapping_table[Ti.get_id()]['release_time']):
                                    self.RM_instance.task_mapping_table[Ti.get_id()]['release_time'] = next_avail_timeslot + synch_time_offset
                                                                 
                            else: # Ti_dep_max not mapped, so get the next soonest available node  
                                #### does this section get executed ???? ####                                                          
                                (next_free_node, next_free_time) = self._findFirstFreeFromNodeList()
                                next_free_time = next_free_time + synch_time_offset                    
                                tm_entry = {
                                            'node_id' : next_free_node,
                                            'release_time' : next_free_time,
                                            'wcc' : Ti.get_worstCaseComputationCost()
                                            }                                                        
                                self.RM_instance.task_mapping_table[Ti.get_id()] = tm_entry
                        else:                            
                            
                            #print "here -0"
                            (next_free_node, next_free_time) = self._findFirstFreeFromNodeList()
                            
#                            if(Ti.get_id() == 1656):
#                                print "here -2"
#                                pprint.pprint((next_free_node, next_free_time))                            
                            
                            if(synch_time_offset > 0):
                                applied_synch_offset = True
                            else:
                                applied_synch_offset = False
                            
                            next_free_time = next_free_time + synch_time_offset                    
                            tm_entry = {
                                        'node_id' : next_free_node,
                                        'release_time' : next_free_time,
                                        'wcc' : Ti.get_worstCaseComputationCost()
                                        }                                                        
                            self.RM_instance.task_mapping_table[Ti.get_id()] = tm_entry
                            
                            
                    ## stupid synch offset calculation - hack to get rid of race conditions ??
                    #pprint.pprint(self.task_mapping_table)
                    #print self.task_mapping_table[Ti.get_id()]['node_id']
                    how_many_scheduled_in_node[self.RM_instance.task_mapping_table[Ti.get_id()]['node_id']] = how_many_scheduled_in_node[self.RM_instance.task_mapping_table[Ti.get_id()]['node_id']] + 1
                    
                    if(how_many_scheduled_in_node[self.RM_instance.task_mapping_table[Ti.get_id()]['node_id']] > 0):
                        synch_time_offset = 0.0000001
                    else:
                        synch_time_offset = 0                    
                    
                    ### (6) if Ti_max_dep is in another node, then extend the release time (add the tr_delay) 
                    final_release_time = 0
                    
                    # find out if same node as dep or diff node
                    if(Ti_dep_max != None):
                        if(Ti_dep_max in self.RM_instance.task_mapping_table):
                            if(self.RM_instance.task_mapping_table[Ti.get_id()]['node_id'] == self.RM_instance.task_mapping_table[Ti_dep_max]['node_id']):
                                flag__same_node_as_dep = True
                            else:
                                flag__same_node_as_dep = False
                        else:
                            flag__same_node_as_dep = True   # not sure about this one...??
                    else:
                        flag__same_node_as_dep = True                    
                       
                    if(flag__same_node_as_dep == False):    ## NOT same node mapping
                        num_flits = math.ceil(self.RM_instance.input_buffers[i_buff_id].get_BufferItemsList()[Ti_dep_max].get_completedTaskSize()/SimParams.NOC_FLIT_BYTES)        
                        num_hops = 1        
                        cost = ((num_hops * SimParams.NOC_ARBITRATION_COST) + num_flits) * SimParams.NOC_PERIOD
                        #cost += (SimParams.NOC_PERIOD * 100)
                        orig_rel_time = self.RM_instance.task_mapping_table[Ti.get_id()]['release_time']
                        new_rel_time = orig_rel_time + cost
                        # update mapping table
                        self.RM_instance.task_mapping_table[Ti.get_id()]['release_time'] = new_rel_time
                        final_release_time = new_rel_time                    
                    else:                        
                        ## Same node mapping, but lets check if there are other tasks before him
                        next_avail_timeslot = self._findNodeNextAvailableTimeSlot(self.RM_instance.task_mapping_table[Ti.get_id()]['node_id'], Ti.get_id())
                        
                        if(next_avail_timeslot > self.RM_instance.task_mapping_table[Ti.get_id()]['release_time']):                            
                            self.RM_instance.task_mapping_table[Ti.get_id()]['release_time'] = next_avail_timeslot + synch_time_offset
                            final_release_time = self.RM_instance.task_mapping_table[Ti.get_id()]['release_time']
                        else:
                            #if(applied_synch_offset==True):     
                            ### not sure about this point !!! ### :(
                              
                            self.RM_instance.task_mapping_table[Ti.get_id()]['release_time'] += synch_time_offset
                            final_release_time = self.RM_instance.task_mapping_table[Ti.get_id()]['release_time']
                            
#                    if(Ti.get_id() == 0):
#                        print "----"
#                        print Ti
#                        print Te
#                        pprint.pprint(self.task_mapping_table)
#                        print "----"                
                        
                    ## update input buffer task
                    self.RM_instance.input_buffers[i_buff_id].get_BufferItemsList()[next_task_to_schedule__id].set_releaseTime(final_release_time)
                    if(self.RM_instance.input_buffers[i_buff_id].get_BufferItemsList()[next_task_to_schedule__id].get_initiallyScheduled() == False):
                        self.RM_instance.input_buffers[i_buff_id].get_BufferItemsList()[next_task_to_schedule__id].set_initiallyScheduled(True)
                        
                    
        ## populate the flow table with the newly added tasks ##
        self.addTo_RM_FlowTable(tasks_added_to_taskmappingtbl)
                    


    def addTo_RM_FlowTable(self, task_list, releaseTime):        
        
        for each_task in task_list:
            
            task_mapped_nodeid = self.RM_instance.task_mapping_table[each_task.get_id()]['node_id']            
            child_tasks = each_task.get_children()
            
            
            # find unique flows
            # e.g. if task has two children both mapped on same node, then we only have 1 flow
            dst_node_list = []            
            for each_child in child_tasks:
                child_task_nodeid = self.RM_instance.task_mapping_table[each_child]['node_id']
                
                if(child_task_nodeid not in dst_node_list):
                    dst_node_list.append(child_task_nodeid)
                    
                    # new flow
                    if(child_task_nodeid != task_mapped_nodeid):
                        nextid = self.RM_instance.flow_table.nextid                    
                        route = self.RM_instance.interconnect.getRouteXY(task_mapped_nodeid, child_task_nodeid)
                        priority = random.randint(0,SimParams.NOC_FLOW_PRIORITY_LEVELS)
                        basicLatency = self.RM_instance.interconnect.getRouteCostXY(task_mapped_nodeid, 
                                                                                    child_task_nodeid,
                                                                                    each_task.get_completedTaskSize())
                        payload = each_task.get_completedTaskSize()
#                        releaseTime = self.RM_instance.task_mapping_table[each_task.get_id()]['release_time'] + \
#                                    self.RM_instance.task_mapping_table[each_task.get_id()]['wcc']
                        endTime_wrt_BL = releaseTime + basicLatency
                        
                        newflow = NoCFlow(nextid,
                                       each_task.get_id(),
                                       task_mapped_nodeid, 
                                       child_task_nodeid, 
                                       route,
                                       priority, 
                                       None, 
                                       basicLatency, 
                                       payload,
                                       releaseTime, 
                                       None,
                                       endTime_wrt_BL,
                                       None,
                                       type=FlowType)
                        
                        
                        
                        # add to the flow table
                        #self.RM_instance.flow_table.addFlow(newflow, releaseTime, basicLatency)
                        
                        
                        
                
            
            
    







                                                
    ########################################
    ## Helper functions
    ########################################  
    
    # go through all input buffs and find the max number of tasks unscheduled, and which input buff is this ?
    def _getMaxNumOfTasksUnscheduled_In_AllInBuffs(self):
        
        max_tasks_unsched = 0
        which_ibuff = 0
        for each_ibuff_id in xrange(len(self.RM_instance.input_buffers)):
            count = 0
            for (each_task_id, each_task) in self.RM_instance.input_buffers[each_ibuff_id].get_BufferItemsList().items():
                if(each_task.get_initiallyScheduled() == False):
                    count +=1
                
            if(count > max_tasks_unsched):
                max_tasks_unsched = count
                which_ibuff = each_ibuff_id
    
        return (which_ibuff , max_tasks_unsched)
            
    
    def _getNextUnscheduledTaskID_In_InputBuff(self, ib_id):
        
        result = None
        for (each_task_id, each_task) in self.RM_instance.input_buffers[ib_id].get_BufferItemsList().items():
            if(each_task.get_initiallyScheduled() == False):
                result = each_task.get_id()
                break
            
        return result
            
    
    def _findFirstFreeFromNodeList(self, node_list=None):
        node_to_task_freq = []
        node_to_task_list = []
        node_next_free = []        
        
        if node_list == None:
            node_list = range(SimParams.NUM_NODES)        
        
        # basically build a reverse - mapping_table                
        for each_node_id in node_list:                                    
            count = 0
            temp_list = []
            next_free_time = 0.0            
            for (task_id,val) in self.RM_instance.task_mapping_table.iteritems():                
                if(val['node_id'] == each_node_id):
                    count += 1
                    temp_list.append(task_id)                    
                    task_end_time = val['release_time'] + val['wcc']
                    
                    if(task_end_time > next_free_time):
                        next_free_time = task_end_time
            
            if(count > 0):
                node_next_free.append((each_node_id, next_free_time))
            else:
                node_next_free.append((each_node_id, self.env.now))
                
        # find soonest free node
        next_free_node = node_next_free[0][0]
        next_free_node_time = node_next_free[0][1]
        lowest_time = node_next_free[0][1]
      
        for each_node in node_next_free:
            if(each_node[1] < lowest_time):
                lowest_time = each_node[1]
                next_free_node = each_node[0]
                next_free_node_time = each_node[1]
                
        return (next_free_node, next_free_node_time)
            
            
    def _findNodeNextAvailableTimeSlot(self, node_id, current_task_id):
        
        node_avail_times = []
        
        # basically build a reverse - mapping_table        
        for (task_id,val) in self.RM_instance.task_mapping_table.iteritems():
            if(val['node_id'] == node_id):
                if(task_id != current_task_id): # if already mapped task isn't the current task..
                    node_avail_times.append(val['release_time'] + val['wcc'])
                
        if(len(node_avail_times) > 0):
            next_avail_timeslot = max(node_avail_times)
        else:
            next_avail_timeslot = self.env.now
        
        return next_avail_timeslot        
        
        
    def _findNodesFreeBeforeTime(self, target_time):
        node_to_task_freq = []
        node_to_task_list = []
        node_next_free = []
        
        nodes_free_before_target_time = []
        
        # basically build a reverse - mapping_table        
        for each_node_id in xrange(SimParams.NUM_NODES):
            count = 0
            temp_list = []
            next_free_time = 0.0            
            for (task_id,val) in self.RM_instance.task_mapping_table.iteritems():
                if(val['node_id'] == each_node_id):
                    count += 1
                    temp_list.append(task_id)
                    
                    task_end_time = val['release_time'] + val['wcc']
                    
                    if(task_end_time > next_free_time):
                        next_free_time = task_end_time
            
            node_to_task_freq.append(count)
            node_to_task_list.append(temp_list)
            node_next_free.append(next_free_time)
            
            if(count > 0):
                if(next_free_time <= target_time):
                    nodes_free_before_target_time.append(each_node_id)
            else:
                nodes_free_before_target_time.append(each_node_id)            
        
        ## check if any node is ready before target time, else send earliest node free ##
        if (len(nodes_free_before_target_time) > 0):
            return (True, nodes_free_before_target_time)
        else:
            #print "node_next_free"
            #pprint.pprint(node_next_free)
            #print node_next_free.index(min(node_next_free))
            return (False, node_next_free.index(min(node_next_free)))
        
        