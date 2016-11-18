import pprint
import sys
import itertools
import simpy
import traceback
import numpy as np
import random
from operator import itemgetter
from collections import OrderedDict


## local imports
from libMappingAndScheduling.MappingPolicy import MappingPolicy
from libBuffer.Buffer import Buffer
from libProcessingElement.CPUNode_ClosedLoop_wIBuffering import CPUNode_ClosedLoop_wIBuffering
from libProcessingElement.Node import NodeStatus
from libApplicationModel.MPEG2FrameTask import MPEG2FrameTask
from libApplicationModel.Task import TaskStatus
from libNoCModel.NoCFlowTable import NoCFlowTable
from libNoCModel.NoCFlow import NoCFlow, FlowType
from SimParams import SimParams
from libDebug.Debug import Debug, DebugCat


class ScheduleAndMap_ClosedLoop_wIBuffering:
    
    def __init__(self, env, RM_instance):  
        
        self.env = env
        self.RM_instance = RM_instance
        self.label = "ScheduleAndMap_ClosedLoop_wIBuffering"        
        
        # query and update node TQ contents data structure
        self.rmlocal_nodeinfo_TQcontents = {
                                            'task_q_contents' : {},                                            
                                            'time_req_sent' : None,
                                            'time_allreplies_received' : None
                                            }
        self.rmlocal_nodeinfo_TQsize = {
                                        'task_q_size' : {},                                            
                                        'time_req_sent' : None,
                                        'time_allreplies_received' : None
                                        }
        
    
    
    # try to schedule the start of the GOP 
    # go through the input buffers and look for 
    # unscheduled I-frames
    def scheduleGOPStart(self):
        
        for i_buff_id in xrange(len(self.RM_instance.input_buffers)):
            # get unscheduled iframe from this input buffer
            unscheduled_iframe_task = self._getNextUnscheduledTaskID_In_InputBuff(i_buff_id, task_type="I")
            Ti = unscheduled_iframe_task
            
            if(Ti != None):            
            
#                ###### debug ####
#                if(Ti.get_id() == 0):
#                    print "48 here --- "
#                    print self.env.now                    
#                #################                
                
                # check if the i-frame has been mapped or not, if not mapped, then pick a node to map onto
                # find node that is currently free
                if(Ti.get_id() in self.RM_instance.task_mapping_table):
                    if(self.RM_instance.task_mapping_table[Ti.get_id()]['node_id'] != None):
                        selected_node_id = self.RM_instance.task_mapping_table[Ti.get_id()]['node_id']
                    else:
                        sys.exit('mapping-error - premapping, did not work ! - 1')
                        #selected_node_id = self._findFirstFreeFromNodeList_viaNodeInspection()
                else:
                    sys.exit('mapping-error - premapping, did not work ! - 2')
                    #selected_node_id = self._findFirstFreeFromNodeList_viaNodeInspection()
                
                if(selected_node_id != None):
                    
                    # if this node is free then lock it
                    if(self.RM_instance.node_network.nodeArray[selected_node_id].get_status() != NodeStatus.NODE_BUSY):
                        rel_time = self.env.now
                        tm_entry = {
                                    'node_id' : selected_node_id,
                                    'release_time' : rel_time,                            
                                    'wcc' : Ti.get_worstCaseComputationCost(),
                                    'status' : TaskStatus.TASK_NULL,
                                    'pri' : Ti.get_priority(),
                                    'deps_completed' : []
                                    }                                                        
                        self.RM_instance.task_mapping_table[Ti.get_id()] = tm_entry
                        
                        ## update input buffer task
                        self.RM_instance.input_buffers[i_buff_id].get_BufferItemsList()[Ti.get_id()].set_releaseTime(rel_time)
                        if(self.RM_instance.input_buffers[i_buff_id].get_BufferItemsList()[Ti.get_id()].get_initiallyScheduled() == False):
                            self.RM_instance.input_buffers[i_buff_id].get_BufferItemsList()[Ti.get_id()].set_initiallyScheduled(True)
                    else:
                        # selected node is busy, but does it have enough task-queue capacity ?
                        if(self._isNodeTQFull_viaNodeID(selected_node_id, safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL) == False):
                        #if(self._isNodeTQFull(selected_node_id, safe_level = SimParams.CPUNODE_TASKQ_SAFE_LEVEL) == False):
                            rel_time = self.env.now
                            tm_entry = {
                                        'node_id' : selected_node_id,
                                        'release_time' : rel_time,                            
                                        'wcc' : Ti.get_worstCaseComputationCost(),
                                        'status' : TaskStatus.TASK_NULL,
                                        'pri' : Ti.get_priority(),
                                        'deps_completed' : []
                                        }                                                        
                            self.RM_instance.task_mapping_table[Ti.get_id()] = tm_entry
                            
                            ## update input buffer task
                            self.RM_instance.input_buffers[i_buff_id].get_BufferItemsList()[Ti.get_id()].set_releaseTime(rel_time)
                            if(self.RM_instance.input_buffers[i_buff_id].get_BufferItemsList()[Ti.get_id()].get_initiallyScheduled() == False):
                                self.RM_instance.input_buffers[i_buff_id].get_BufferItemsList()[Ti.get_id()].set_initiallyScheduled(True)
                        else:
                         
                            #selected_node_id = self._findNodeWithLeastMappings_viaTMTblInspection()                    
                            tm_entry = {
                                        'node_id' : selected_node_id,
                                        'release_time' : None,                            
                                        'wcc' : Ti.get_worstCaseComputationCost(),
                                        'status' : TaskStatus.TASK_READY_WAITING,
                                        'pri' : Ti.get_priority(),
                                        'deps_completed' : []
                                        }                                                        
                            self.RM_instance.task_mapping_table[Ti.get_id()] = tm_entry
                        
                else:
                    sys.exit('mapping-error - premapping, did not work ! - 3')
                    
#                    selected_node_id = self._findNodeWithLeastMappings_viaTMTblInspection()
#                    
#                    tm_entry = {
#                                'node_id' : selected_node_id,
#                                'release_time' : None,                            
#                                'wcc' : Ti.get_worstCaseComputationCost(),
#                                'status' : TaskStatus.TASK_READY_WAITING,
#                                'deps_completed' : []
#                                }                                                        
#                    self.RM_instance.task_mapping_table[Ti.get_id()] = tm_entry
                    
                    
    
    # map all unmapped tasks in the input buffers
    def mapNewGoPTasks(self):
        for i_buff_id in xrange(len(self.RM_instance.input_buffers)):            
            wf_id = i_buff_id            
            for (each_task_id, each_task) in self.RM_instance.input_buffers[i_buff_id].get_BufferItemsList().items():
                Ti = each_task
                stream_id = Ti.get_video_stream_id()
                gop_fr_ix = Ti.get_frameIXinGOP()
                
                
                ## SEMI_DYNAMIC_APPROACH : ## 
                # in this mode, we assume all the tasks of a video stream
                # is premapped upon admission of the video stream
                if(SimParams.MAPPING_PREMAPPING_ENABLED == True):                                    
                    self.mapNewGoPTasks_SemiDynamicMapping_withoutMSSignalling(each_task_id, 
                                                                               i_buff_id, 
                                                                               wf_id, stream_id, gop_fr_ix, Ti)
                
                ## FULLY_DYNAMIC_APPROACH : ##
                # in this mode, we assume all the jobs of a video stream are assigned mapping,
                # when they are dispatched by the task dispatcher, not beforehand.
                else:
                    if(SimParams.MS_SIGNALLING_TYPE_RM2N_REQ_TQINFO_JOBSTART_ENABLE == True):
                        self.mapNewGoPTasks_FullyDynamicMapping_withMSSignalling(each_task_id, Ti)
                    else:
                        self.mapNewGoPTasks_FullyDynamicMapping_withoutMSSignalling(each_task_id, Ti)
                        
                                                
    
    # semi-dynamic mapping WITH MS-signalling
    def mapNewGoPTasks_SemiDynamicMapping_withMSSignalling(self):
        sys.exit('mapNewGoPTasks_SemiDynamicMapping_withMSSignalling : error - not implemented yet!')
        
    # semi-dynamic mapping WITHOUT MS-signalling
    def mapNewGoPTasks_SemiDynamicMapping_withoutMSSignalling(self, each_task_id, i_buff_id, wf_id, stream_id, gop_fr_ix, Ti, 
                                                              task_status = TaskStatus.TASK_NULL,
                                                              task_release_time = None):
        # is task already mapped ?                
        if Ti.get_id() not in self.RM_instance.task_mapping_table:            
            try:
                selected_node_id = self.RM_instance.vidstream_frames_mapping_table[wf_id][stream_id]['frames_mapping'][gop_fr_ix] 
                #print selected_node_id               
                tm_entry = {
                                'node_id' : selected_node_id,
                                'release_time' : task_release_time,                            
                                'wcc' : Ti.get_worstCaseComputationCost(),
                                'status' : task_status,
                                'pri' : Ti.get_priority(),
                                'deps_completed' : []
                                }                                                        
                self.RM_instance.task_mapping_table[Ti.get_id()] = tm_entry    
                
                self.volatileTaskMappingTable_addEntry(tm_entry, Ti) # add to volatile table, used for openloop mapping   
                            
            except Exception, e:
                traceback.print_exc()
                print self.env.now
                pprint.pprint(self.RM_instance.vidstream_frames_mapping_table)
                print "ti_id =" + str(Ti.get_id())
                print Ti.get_parentGopId()
                print (wf_id, stream_id)
                pprint.pprint(self.RM_instance.input_buffers[i_buff_id].get_BufferItemsList().items())
                sys.exit('mapNewGoPTasks:: mapNewGoPTasks_SemiDynamicMapping_withoutMSSignalling: error !!')
    
        
        
        
        
        
    
    # fully-dynamic mapping WITH MS-signalling
    def mapNewGoPTasks_FullyDynamicMapping_withMSSignalling(self, each_task_id, Ti):
        i=1
        
        
    # fully-dynamic mapping WITHOUT MS-signalling
    def mapNewGoPTasks_FullyDynamicMapping_withoutMSSignalling(self, each_task_id, Ti,
                                                               task_status = TaskStatus.TASK_NULL,
                                                               task_release_time = None):
        if each_task_id not in self.RM_instance.task_mapping_table:
            selected_node_id = self._findNodeWithLeastMappings_viaTMTblInspection()
            #selected_node_id = self._findNodeWithLeastMappings_viaTMTblInspection_and_NodeInspection()
            selected_node_id = self._findNodeWithLeastMappings_viaAuxTMTbl()                        
            self.RM_instance.node_to_task_mapped_count[selected_node_id] = self.RM_instance.node_to_task_mapped_count[selected_node_id] +1
            
            tm_entry = {
                        'node_id' : selected_node_id,
                        'release_time' : task_release_time,                            
                        'wcc' : Ti.get_worstCaseComputationCost(),
                        'status' : task_status,
                        'pri' : Ti.get_priority(),
                        'deps_completed' : []
                        }                                                        
            self.RM_instance.task_mapping_table[Ti.get_id()] = tm_entry
    
    
    
    def mapNewGoPTasks_FullyDynamicMapping_withoutMSSignalling_v2(self, wf_id, stream_id, gop_fr_ix, Ti, 
                                                              task_status = TaskStatus.TASK_NULL,
                                                              task_release_time = None):
        # is task already mapped ?                
        if Ti.get_id() not in self.RM_instance.task_mapping_table:            
            try:
                selected_node_id = self.RM_instance.vidstream_frames_mapping_table[wf_id][stream_id]['frames_mapping'][gop_fr_ix]                
                tm_entry = {
                                'node_id' : selected_node_id,
                                'release_time' : task_release_time,                            
                                'wcc' : Ti.get_worstCaseComputationCost(),
                                'status' : task_status,
                                'pri' : Ti.get_priority(),
                                'deps_completed' : []
                                }                                                        
                self.RM_instance.task_mapping_table[Ti.get_id()] = tm_entry                
            except:
                print self.env.now
                pprint.pprint(self.RM_instance.vidstream_frames_mapping_table)
                print "ti_id =" + str(Ti.get_id())
                print Ti.get_parentGopId()
                print (wf_id, stream_id)                
                sys.exit('mapNewGoPTasks:: mapNewGoPTasks_FullyDynamicMapping_withoutMSSignalling_v2: error !!')
    
    
    
    
    ## when task is finished this is called to say to schedule it's dependant tasks ##
    def releaseChildTasks(self, finished_task, node_id):
        Debug.PPrint("%.15f"%self.env.now + "," + self.label + "," +'releaseChildTasks::, : Enter - finished_task='+str(finished_task.get_id()) + ", nodeid="+str(node_id), DebugCat.DEBUG_CAT_MAPPERINFO)
                
        total_released_tasks = []
        tasks_released_on_current_node = []
        total_tasks_released_on_specific_node = {}
            
        ### try to release all dependant tasks of the finished task ###        
        # get child tasks 
        child_tasks_ids = finished_task.get_children()
        
        if(len(child_tasks_ids) > 0):            
        
            # for each child check if it is mapped and dependancies are complete
            for each_child_task_id in child_tasks_ids:
                
                # find child from input buffers
                (child_task, childtask_ibuff_id) = self._findTaskFromInputBuffers(each_child_task_id)
                
                if(each_child_task_id in self.RM_instance.task_mapping_table):
                    finished_task_nodeid = self.RM_instance.task_mapping_table[finished_task.get_id()]['node_id']
                    child_task_nodeid = self.RM_instance.task_mapping_table[each_child_task_id]['node_id']
                    if(finished_task_nodeid == child_task_nodeid): 
                        # they are mapped on the same node, so add to deps completed
                        if(finished_task.get_id() not in self.RM_instance.task_mapping_table[each_child_task_id]['deps_completed']):
                            self.RM_instance.task_mapping_table[each_child_task_id]['deps_completed'].append(finished_task.get_id())
                        
                        # check if all dependancies are present
                        if(self._areAllDependanciesMet(child_task) == True):
                            
                            # first check if the selected node is free to use
                            selected_node = self.RM_instance.node_network.get_Node(child_task_nodeid)
                            if(self._IsNodeTQFull(selected_node, safe_level=SimParams.CPUNODE_TASKQ_SAFE_LEVEL)== False) and \
                                (selected_node.get_id() not in total_tasks_released_on_specific_node):                                
                                # the child task is now ready to be released
                                # set release time in input buffers and task mapping table
                                rel_time = self.env.now + SimParams.SYNCH_TIME_OFFSET
                                self.RM_instance.task_mapping_table[each_child_task_id]['release_time'] = rel_time
                                self.RM_instance.input_buffers[childtask_ibuff_id].get_BufferItemsList()[each_child_task_id].set_releaseTime(rel_time)
                                if(self.RM_instance.input_buffers[childtask_ibuff_id].get_BufferItemsList()[each_child_task_id].get_initiallyScheduled() == False):
                                    self.RM_instance.input_buffers[childtask_ibuff_id].get_BufferItemsList()[each_child_task_id].set_initiallyScheduled(True)
                                
                                # set the task status on the tm table
                                self.setTaskStatus_inRM_TMTbl(each_child_task_id, TaskStatus.TASK_MARKED_FOR_RELEASE)
                                    
                                total_released_tasks.append(each_child_task_id)
                                tasks_released_on_current_node.append(each_child_task_id)
                                total_tasks_released_on_specific_node[selected_node.get_id()] = [each_child_task_id]                                
                            else:
                                # node is busy, so just wait till it is free
                                self.RM_instance.task_mapping_table[each_child_task_id]['status'] = TaskStatus.TASK_READY_WAITING                                
                    else:
                        i=1 # do nothing, the necessary flows will need to be released                        
                else:
                    sys.exit('Error! - finished '+str(finished_task.get_id()) + ', Child task not mapped = '+str(each_child_task_id))
    
        ### so no tasks were released on this node, either because the node is busy or no children for the finished task
        if(len(tasks_released_on_current_node) == 0):
            ## so now check if there are any other tasks waiting to be released on the current node                
            # find all tasks already mapped on the same node, AND different gop AND task status is null or waiting
            tasksids_already_mapped_on_node = []
            for (task_id,val) in self.RM_instance.task_mapping_table.iteritems():
                if((val['node_id'] == node_id) and \
                #(finished_task.get_unique_gop_id() != finished_task.get_unique_gop_id()) and \
                (val['status'] in [TaskStatus.TASK_NULL, TaskStatus.TASK_READY_WAITING])):
                    tasksids_already_mapped_on_node.append(task_id)   
            
            tasks_already_mapped_on_node = []
            if(len(tasksids_already_mapped_on_node) > 0):
                # get actual tasks from the input buffer
                tasks_already_mapped_on_node = self._findTaskFromInputBuffers(None, tasksids_already_mapped_on_node)
                tasks_already_mapped_on_node.sort(key=lambda x: (x[0].get_dispatchTime(), x[0].get_id()), reverse=False)
                
                # release the first task in the above list if the node_id is free
                task = tasks_already_mapped_on_node[0][0]
                task_ibuff_id = tasks_already_mapped_on_node[0][1]
                
                # check if the dependancies are all met
                if(self._areAllDependanciesMet(task) == True):                    
                   
                    # first check if the selected node is free to use
                    child_task_nodeid = self.RM_instance.task_mapping_table[task.get_id()]['node_id']
                    selected_node = self.RM_instance.node_network.get_Node(child_task_nodeid)
                    if(self._IsNodeTQFull(selected_node, safe_level=SimParams.CPUNODE_TASKQ_SAFE_LEVEL)== False) and \
                        (selected_node.get_id() not in total_tasks_released_on_specific_node):
                        
                        # the child task is now ready to be released
                        # set release time in input buffers and task mapping table
                        rel_time = self.env.now + SimParams.SYNCH_TIME_OFFSET
                        self.RM_instance.task_mapping_table[task.get_id()]['release_time'] = rel_time
                        self.RM_instance.input_buffers[task_ibuff_id].get_BufferItemsList()[task.get_id()].set_releaseTime(rel_time)
                        if(self.RM_instance.input_buffers[task_ibuff_id].get_BufferItemsList()[task.get_id()].get_initiallyScheduled() == False):
                            self.RM_instance.input_buffers[task_ibuff_id].get_BufferItemsList()[task.get_id()].set_initiallyScheduled(True)
                        
                        # set the task status on the tm table
                        self.setTaskStatus_inRM_TMTbl(task.get_id(), TaskStatus.TASK_MARKED_FOR_RELEASE)
                        
                        total_released_tasks.append(task.get_id())
                        tasks_released_on_current_node.append(task.get_id())
                        total_tasks_released_on_specific_node[selected_node.get_id()] = [task.get_id()]
                    else:
                        # node is busy, so just wait till it is free
                        self.RM_instance.task_mapping_table[task.get_id()]['status'] = TaskStatus.TASK_READY_WAITING                    
        
        return total_released_tasks
            
                
    ## when task is finished this is called to say to schedule it's dependant tasks ##
    ## RWTPr_FCFS : Ready Waiting Priority Tasks based Highest Pri first    
    def releaseChildTasks_RWTPr_PriSorted(self, finished_task, node_id):
        Debug.PPrint("%.15f"%self.env.now + "," + self.label + "," +'releaseChildTasks_RWTPr_PriSorted::, : Enter - finished_task='+str(finished_task.get_id()) + ", nodeid="+str(node_id), DebugCat.DEBUG_CAT_MAPPERINFO)
                
        total_released_tasks = []
        tasks_released_on_current_node = []
        total_tasks_released_on_specific_node = {}
        
        ### how much node capacity do we have ? ###
        node_available_cap = self._nodeTQ_AvailableCapacity(node_id)
                
        ### try to release any ready-waiting tasks ###
        if(node_available_cap>0):
            ready_waiting_tasklist_prisorted = self._getTasksReadyAndWaiting_PriSorted(node_id, limit_num=node_available_cap)            
            if(len(ready_waiting_tasklist_prisorted)>0):
                for each_task in ready_waiting_tasklist_prisorted:                    
                    result = self._markTaskForRelease(each_task, each_task.get_dispatched_ibuffid(), node_id,
                                                        total_tasks_released_on_specific_node,
                                                        total_released_tasks,                            
                                                        tasks_released_on_current_node
                                                        )
                    if(result==True):
                        total_released_tasks.append(each_task.get_id())                        
                        if(node_id not in total_tasks_released_on_specific_node):
                            total_tasks_released_on_specific_node[node_id] = [each_task.get_id()]
                        else:
                            total_tasks_released_on_specific_node[node_id].append(each_task.get_id())
                        
                        
        ### try to release all dependant tasks of the finished task ###        
        # get child tasks 
        child_tasks_ids = finished_task.get_children()        
        if(len(child_tasks_ids) > 0):            
        
            # for each child check if it is mapped and dependancies are complete
            for each_child_task_id in child_tasks_ids:
                
                # find child from input buffers
                (child_task, childtask_ibuff_id) = self._findTaskFromInputBuffers(each_child_task_id)                
                if(each_child_task_id in self.RM_instance.task_mapping_table):
                    finished_task_nodeid = self.RM_instance.task_mapping_table[finished_task.get_id()]['node_id']
                    child_task_nodeid = self.RM_instance.task_mapping_table[each_child_task_id]['node_id']
                    if(finished_task_nodeid == child_task_nodeid): 
                        # they are mapped on the same node, so add to deps completed
                        if(finished_task.get_id() not in self.RM_instance.task_mapping_table[each_child_task_id]['deps_completed']):
                            self.RM_instance.task_mapping_table[each_child_task_id]['deps_completed'].append(finished_task.get_id())                        
                        
                        result = self._markTaskForRelease(child_task, child_task.get_dispatched_ibuffid(), child_task_nodeid,
                                                          total_tasks_released_on_specific_node,
                                                          total_released_tasks,                            
                                                          tasks_released_on_current_node)
                        if(result==True):
                            total_released_tasks.append(child_task.get_id())                        
                            if(child_task_nodeid not in total_tasks_released_on_specific_node):
                                total_tasks_released_on_specific_node[child_task_nodeid] = [child_task.get_id()]
                            else:
                                total_tasks_released_on_specific_node[child_task_nodeid].append(child_task.get_id())
                                                          
                    else:
                        i=1 # do nothing, the necessary flows will need to be released                        
                else:
                    sys.exit('Error! - finished '+str(finished_task.get_id()) + ', Child task not mapped = '+str(each_child_task_id))
        
        return total_released_tasks
                


           
    ## this gets called when a flow has completed ##
    def DataFlowComplete(self, flow):
        
        Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'DataFlowComplete::, : Enter - flowid='+str(flow.get_id()), DebugCat.DEBUG_CAT_MAPPERINFO)
        
        total_released_tasks = []
        total_tasks_released_on_specific_node = {}
        
        # mark flow as complete
        #self.RM_instance.flow_table.set_endTime(self.env.now, flow_id=flow_id)
        #self.RM_instance.flow_table.set_active(False, flow_id=flow_id)   
        
        # mark dependancies
        # this completed flow may serve two dependancies - need to take this into account
        src_task_id =  flow.get_respectiveSrcTaskId()
        dst_task_ids = []    # could be alot of dst tasks, mapped on the same dst core
        dst_task_ids =  flow.get_respectiveDstTaskId()
        
        for dst_task_id in dst_task_ids:
        
            if(src_task_id not in self.RM_instance.task_mapping_table[dst_task_id]['deps_completed']):
                self.RM_instance.task_mapping_table[dst_task_id]['deps_completed'].append(src_task_id) 
            
            ## debug ##
#            if(dst_task_id == 6):
#                print " yes 6!!!"       
#                pprint.pprint(self.RM_instance.task_mapping_table[dst_task_id])     
            ###
            
            
            # find if the dst_task_id is now ready to be released due to this flow completion
            # this task should still be in the buffer
            which_ibuff = None
            potential_task = None
            (potential_task, which_ibuff) = self._findTaskFromInputBuffers(dst_task_id)
                
            # check if the dependancies are all met
            if(self._areAllDependanciesMet(potential_task) == True):
                
                # first check if the selected node is free to use
                potential_task_nodeid = self.RM_instance.task_mapping_table[potential_task.get_id()]['node_id']
                selected_node = self.RM_instance.node_network.get_Node(potential_task_nodeid)
                if(self._IsNodeTQFull(selected_node, safe_level=SimParams.CPUNODE_TASKQ_SAFE_LEVEL)== False) and \
                    (selected_node.get_id() not in total_tasks_released_on_specific_node):
                    
                    # the potiential task is now ready to be released
                    # set release time in input buffers and task mapping table
                    rel_time = self.env.now + SimParams.SYNCH_TIME_OFFSET
                    self.RM_instance.task_mapping_table[dst_task_id]['release_time'] = rel_time
                    self.RM_instance.input_buffers[which_ibuff].get_BufferItemsList()[potential_task.get_id()].set_releaseTime(rel_time)
                    if(self.RM_instance.input_buffers[which_ibuff].get_BufferItemsList()[potential_task.get_id()].get_initiallyScheduled() == False):
                        self.RM_instance.input_buffers[which_ibuff].get_BufferItemsList()[potential_task.get_id()].set_initiallyScheduled(True)
                    
                    # set the task status on the tm table
                    self.setTaskStatus_inRM_TMTbl(potential_task.get_id(), TaskStatus.TASK_MARKED_FOR_RELEASE)
                    
                    total_released_tasks.append(dst_task_id)
                    total_tasks_released_on_specific_node[selected_node.get_id()] = [dst_task_id]
                    
                else:
                    # node is busy, so just wait till it is free
                    self.RM_instance.task_mapping_table[dst_task_id]['status'] = TaskStatus.TASK_READY_WAITING 
                            
        return total_released_tasks                

      
    ## add all mapped tasks to the flow table, the respective flows ##
    def addTo_RM_FlowTable(self, finished_taskList, releaseTime, debug_which_cpu):        
        
        debug_ftl = [x.get_id() for x in finished_taskList]
        
        Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'addTo_RM_FlowTable::, : Enter - fin_tsk_lst='+str(debug_ftl) + ", which_cpu="+str(debug_which_cpu), DebugCat.DEBUG_CAT_MAPPERINFO)
        
        num_flows_added = []
        
        for each_task in finished_taskList:
            
            task_mapped_nodeid = self.RM_instance.task_mapping_table[each_task.get_id()]['node_id']            
            child_tasks_ids = each_task.get_children()  #ids
            child_tasks_ixs = each_task.get_children_frames() #ixs
            child_tasks_id_ix_rel = self._get_tid_tix_dict(child_tasks_ids, child_tasks_ixs)
            
#            ## DEBUG ##
#            if(each_task.get_id() == 721):
#                pprint.pprint(child_tasks_ids)#
#                #pprint.pprint(self.RM_instance.task_mapping_table)
#                                
#            ###########                
            
            # find unique flows
            # e.g. if task has two children both mapped on same node, then we only have 1 flow
            dst_node_list = []
            temp_destinations_dict = {}            
            for each_child_id in child_tasks_ids:
                child_task_nodeid = self.RM_instance.task_mapping_table[each_child_id]['node_id']
                
                if(child_task_nodeid not in temp_destinations_dict):
                    temp_destinations_dict[child_task_nodeid] = [each_child_id]
                else:
                    temp_destinations_dict[child_task_nodeid].append(each_child_id) 
                
                if(child_task_nodeid not in dst_node_list):
                    dst_node_list.append(child_task_nodeid)                    
                    
#                    ## DEBUG ##
#                    if(each_task.get_id() == 721):
#                        print "each_child_id = " + str(each_child_id)
#                        print "child_task_nodeid = " + str(child_task_nodeid)
#                        pprint.pprint(temp_destinations_dict)
#                        print "dst_node_list = " + str(dst_node_list)
#                    ###########
                    
                    # new flow
                    if(child_task_nodeid != task_mapped_nodeid):
                        nextid = self.RM_instance.flow_table.nextid                    
                        route = self.RM_instance.interconnect.getRouteXY(task_mapped_nodeid, child_task_nodeid)
                        #priority = random.randint(0,SimParams.NOC_FLOW_PRIORITY_LEVELS)
                        #priority = each_task.get_priority()
                        priority = each_task.get_priority() + (self.RM_instance.flow_priority_offset+100) + nextid
                        basicLatency = self.RM_instance.interconnect.getRouteCostXY(task_mapped_nodeid, 
                                                                                    child_task_nodeid,
                                                                                    each_task.get_completedTaskSize())
                        payload = each_task.get_completedTaskSize()
                        endTime_wrt_BL = releaseTime + basicLatency
                        
                        newflow = NoCFlow(nextid,
                                       each_task,
                                       each_task.get_id(),
                                       temp_destinations_dict[child_task_nodeid],
                                       self._get_tixs_from_tids(temp_destinations_dict[child_task_nodeid], child_tasks_id_ix_rel),
                                       task_mapped_nodeid, 
                                       child_task_nodeid, 
                                       route,
                                       priority, 
                                       None, 
                                       basicLatency, 
                                       payload,
                                       endTime_wrt_BL,
                                       type=FlowType.FLOWTYPE_DATA)
                        
#                        ## DEBUG ##
#                        if(each_task.get_id() == 721):
#                            print newflow
#                        ###########
                        
                        # add to the flow table
                        self.RM_instance.flow_table.addFlow(newflow, releaseTime, basicLatency)                        
                        num_flows_added.append(newflow.get_id())
                        
        # update the table
        if(len(num_flows_added) > 0):
            self.RM_instance.flow_table.updateTable(fire=True)   # one update for many additions
    


                                                
    ########################################
    ## Helper functions
    ########################################  
    
    def _get_tid_tix_dict(self, tids, tixs):        
        if(len(tids) != len(tixs)):
            sys.exit("_get_tid_tix_dict::Error !")
        
        result = OrderedDict()
        for i, tid_v in enumerate(tids):
            result[tid_v] = tixs[i]
        
        return result
    
    
    def _get_tixs_from_tids(self, tids, search_dict): 
        if(len(search_dict.keys())==0) or (len(tids)==0):
            sys.exit("_get_tixs_from_tids::Error !")        
               
        result = []
        for each_tid in tids:
            result.append(search_dict[each_tid])
        return result
            
            
    
    def _IsNodeTQFull(self, selected_node, safe_level = SimParams.CPUNODE_TASKQ_SIZE):        
        if (selected_node.getTaskQ_level() < safe_level):
            return False
        else:
            return True
      
    
    def _isNodeTQFull_viaNodeID(self, node_id, safe_level = SimParams.CPUNODE_TASKQ_SIZE):
        
        for each_node in self.RM_instance.node_network.get_Nodes():
            if (each_node.get_id() == node_id):
                if(each_node.getTaskQ_level() < safe_level):
                    return False
                else:
                    return True
        
    def _nodeTQ_AvailableCapacity(self, node_id):
        for each_node in self.RM_instance.node_network.get_Nodes():
            if(each_node.get_id() == node_id):
                return each_node.getTaskQ_availableCapacity()
        
        
    
    # what is the link utilisation - for all the links in a route
    def _cumulativeLinkUtilPerRoute(self, src_node_id, dst_node_id):
        
        # find route
        route = self.RM_instance.interconnect.getRouteXY(src_node_id, dst_node_id)
        
        cumLinkUtil = 0.0
        for each_link in route:
            cumLinkUtil += each_link.getUtilisation()
        
        return cumLinkUtil
    
    # what is the utilisation for different routes (for different src, dst nodes)
    def _mappingVsLinkUtilStats(self, src_node_id, node_list):
        
        results = {}        
        for each_node_id in node_list:
            if(each_node_id != src_node_id):
                util = self._cumulativeLinkUtilPerRoute(src_node_id, each_node_id)
                entry = {
                         "src_node_id" : src_node_id,
                         "dst_node_id" : each_node_id,
                         "cumLinkUtil" : util
                         }                
                results[each_node_id] = entry
            
        return results
    
    
    #TODO:: a better mapping scheme which uses link util + node util
    def _whichNode_ToMapTo(self, src_node_id):
        
        # which nodes are least used in the 
        
        
        # get link util stats
        linkUtilStats = self._mappingVsLinkUtilStats()
        
 
    # find task from input buffers, given task_id
    def _findTaskFromInputBuffers(self, task_id, task_id_list = None):
        
        if(task_id_list == None and task_id != None):
            for each_ibuff_id in xrange(len(self.RM_instance.input_buffers)):
                for (each_task_id, each_task) in self.RM_instance.input_buffers[each_ibuff_id].get_BufferItemsList().items():
                    if(each_task_id == task_id):
                        return (each_task, each_ibuff_id)
                    
            
            pprint.pprint(task_id_list)
            pprint.pprint(task_id)
            pprint.pprint(self.RM_instance.input_buffers)
            sys.exit("_findTaskFromInputBuffers :: no task found.")            
            
        else:            
            if(len(task_id_list) > 0): # we need to find more than one task
                result_tasks = []
                for each_ibuff_id in xrange(len(self.RM_instance.input_buffers)):
                    for (each_task_id, each_task) in self.RM_instance.input_buffers[each_ibuff_id].get_BufferItemsList().items():
                        if(each_task_id in task_id_list):
                            result_tasks.append((each_task, each_ibuff_id))
                        
                return result_tasks
            else:
                sys.exit('_findTaskFromInputBuffers:: invalid function call')
    
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
            
    
    def _getNextUnscheduledTaskID_In_InputBuff(self, ib_id, task_type = "IPB"):        
        result =  [x for x in self.RM_instance.input_buffers[ib_id].get_BufferItemsList().values() if ((x.get_initiallyScheduled() == False) and (x.get_frameType() in task_type))]        
        if(len(result) > 0):
            return result[0]
        else:
            return None        
    
    def _getAllUnscheduledTaskID_In_InputBuff(self, ib_id): 
        #print self.RM_instance.input_buffers[ib_id].get_BufferItemsList().values()       
        result =  [x for x in self.RM_instance.input_buffers[ib_id].get_BufferItemsList().values() if ((x.get_initiallyScheduled() == False))]
        #print result        
        if(len(result) > 0):
            return result
        else:
            return None
    
    
    # find first free node by inspecting the nodes
    def _findFirstFreeFromNodeList_viaNodeInspection(self, node_list=None):       
        
        available_node = None        
        for each_node in self.RM_instance.node_network.get_Nodes():            
            if(each_node.get_status() == NodeStatus.NODE_IDLE) and \
             (each_node.getTaskQ_level() < SimParams.CPUNODE_TASKQ_SIZE):
                
                # we found a match, now check task mapping table
                # check the task mapping table to be sure
                flag = True
                for (task_id,val) in self.RM_instance.task_mapping_table.iteritems():                
                    if(val['node_id'] == each_node.get_id()):
                        if(("%.15f"%val['release_time']) == ("%.15f"%self.env.now)):
                            flag = False
                            break
                
                if(flag == True):
                    available_node = each_node.get_id()
                    break 
            
        return available_node
    
    
    def _findFirstFreeFromNodeList_viaTQ_and_TMTbl_Inspection(self):
        
        # find nodes that have enough TQ capacity
        nodes_tq_nonfull = []
        for each_node in self.RM_instance.node_network.get_Nodes(): 
            if(each_node.getTaskQ_level() < SimParams.CPUNODE_TASKQ_SIZE):
                nodes_tq_nonfull.append(each_node)
        
        if(len(nodes_tq_nonfull)>0):
            # now find out how many tasks are waiting on that node - according to the task-mapping table
            nodes_available_in_tmtbl = {}
            for (task_id,val) in self.RM_instance.task_mapping_table.iteritems():
                if(val['node_id'] in nodes_tq_nonfull):
                    if(val['status'] == TaskStatus.TASK_COMPLETED):
                        if(val['node_id'] not in nodes_available_in_tmtbl):
                            nodes_available_in_tmtbl[val['node_id']] = [task_id]
                        else:
                            nodes_available_in_tmtbl[val['node_id']].append(task_id)
            
            if(len(nodes_available_in_tmtbl)>0):            
                selected_node = min(nodes_available_in_tmtbl, key = lambda x: len(nodes_available_in_tmtbl.get(x)))
                return selected_node
            else:
                # if there are no nodes available in tm table, then choose randomly
                selected_node = random.choice(nodes_tq_nonfull)
                return selected_node         
        else:
            # if there are no nodes with task queues non-full, then map to any random node
            selected_node = random.choice(self.RM_instance.node_network.get_Nodes())
            return selected_node
            
        
        
    
    def _findNodeWithLeastMappings_viaTMTblInspection(self, node_list=None):
        nodes = []  
        
        # basically build a reverse - mapping_table                
        for each_node_id in xrange(SimParams.NUM_NODES):                                    
            count = 0                       
            for (task_id,val) in self.RM_instance.task_mapping_table.iteritems():                
                if(val['node_id'] == each_node_id):
                    count += 1            
            nodes.append((each_node_id, count))
        
        nodes.sort(key=lambda x: (x[1]), reverse=False)
        
        return nodes[0][0]
    
    def _findNodeWithLeastMappings_viaAuxTMTbl(self, node_list=None):
        
        min_val = min(self.RM_instance.node_to_task_mapped_count.itervalues())      
        sorted_nodeids = [k for k, v in self.RM_instance.node_to_task_mapped_count.iteritems() if v == min_val]
        
        return sorted_nodeids[0]
        
    
    # combination of taskmapping and node-tq  
    def _findNodeWithLeastMappings_viaTMTblInspection_and_NodeInspection(self, node_list=None):
        tmtbl_inspection_nodes = {}
        tq_inspection_nodes = {}
        
        # get count from task-mapping table                
        for each_node_id in xrange(SimParams.NUM_NODES):                                    
            count = 0                       
            for (task_id,val) in self.RM_instance.task_mapping_table.iteritems():                
                if(val['node_id'] == each_node_id):
                    count += 1            
            tmtbl_inspection_nodes[each_node_id] = count
        
        # get count from task-queue
        for each_node in self.RM_instance.node_network.get_Nodes():
            if(each_node.getTaskQ_level() < SimParams.CPUNODE_TASKQ_SAFE_LEVEL):            
                each_node_id = each_node.get_id()
                count = each_node.getTaskQ_level()
                tq_inspection_nodes[each_node_id] = count
    
        # combine the results from both the tmtbl and node_tqs            
        combined_results_nodes = []
        for each_node_id in tq_inspection_nodes.keys():
            entry = {   "node_id" : each_node_id,
                        "tmtbl_count" : tmtbl_inspection_nodes[each_node_id] if each_node_id in tmtbl_inspection_nodes else 10000,
                        "tq_count" : tq_inspection_nodes[each_node_id]
                        }
            combined_results_nodes.append(entry)
            
        # first sort by tq, then sort by tmtbl
        sorted_combined_results_nodes = sorted(combined_results_nodes, key=itemgetter('tq_count', 'tmtbl_count'), reverse=False)
            
        if(len(sorted_combined_results_nodes) > 0):
            return sorted_combined_results_nodes[0]['node_id']
        else:
            sys.exit("_findNodeWithLeastMappings_viaTMTblInspection_and_NodeInspection :: error")
    
    # find first free node by inspectiing the task mapping table
    def _findFirstFreeFromNodeList_viaTMTblInspection(self, node_list=None):
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
        
    def _tasksMappedOnNodeId(self, node_id, task_status=TaskStatus.TASK_NULL):
        taskid_list = []
        for (task_id,val) in self.RM_instance.task_mapping_table.iteritems():
            if(val['node_id'] == node_id) and (val['status'] == task_status):                
                taskid_list.append(task_id)
        
        task_list = []
        for each_taskid in taskid_list:
            (task,ibuffid) = self._findTaskFromInputBuffers(each_taskid)            
            task_list.append(task)
                    
        return task_list
    
    def _getTasksReadyAndWaiting_PriSorted(self, node_id, limit_num=-1):
        readywaiting_tasklist = self._tasksMappedOnNodeId(node_id, task_status=TaskStatus.TASK_READY_WAITING)        
        
        if(len(readywaiting_tasklist) > 0):
            sorted_readywaiting_tasklist = sorted(readywaiting_tasklist, key=lambda x: x.get_priority(), reverse=True) # highest pri first
            
            if(limit_num == -1):    # return all
                return sorted_readywaiting_tasklist
            else:                  
                if(len(sorted_readywaiting_tasklist) > limit_num):
                    return sorted_readywaiting_tasklist[:limit_num]
                else:
                    return sorted_readywaiting_tasklist
        else:
            empty_list = []
            return empty_list        
    
    
    def _getTasksReadyAndWaiting_FCFS(self, node_id, limit_num=-1):
        readywaiting_tasklist = self._tasksMappedOnNodeId(node_id, task_status=TaskStatus.TASK_READY_WAITING)        
        
        if(len(readywaiting_tasklist) > 0):
            sorted_readywaiting_tasklist = sorted(readywaiting_tasklist, key=lambda x: x.get_dispatchTime(), reverse=False) # lowest dispatch time first
            
            if(limit_num == -1):    # return all
                return sorted_readywaiting_tasklist
            else:                  
                if(len(sorted_readywaiting_tasklist) > limit_num):
                    return sorted_readywaiting_tasklist[:limit_num]
                else:
                    return sorted_readywaiting_tasklist
        else:
            empty_list = []
            return empty_list 
        
    
    def _NodeFree_viaRMTMTBL_inspection(self, node_id, time_now):
        for (task_id,val) in self.RM_instance.task_mapping_table.iteritems():
            if(val['release_time'] != None):
                #if(val['node_id'] == node_id) and (round(val['release_time'],9) == round(time_now,9)):
                if(val['node_id'] == node_id) and (("%.9f"%val['release_time']) == ("%.9f"%time_now)):
                    return False
        return True
    
    def _IsNodeAvailableForTaskRelease(self, selected_node, safe_level = SimParams.CPUNODE_TASKQ_SIZE):
         
        if(self._NodeFree_viaRMTMTBL_inspection(selected_node.get_id(), self.env.now + SimParams.SYNCH_TIME_OFFSET) == True) and \
        (selected_node.getTaskQ_level() < safe_level):
            return True
        else:
            return False
         
    
    def _tasksInGop(self, task_list, gop_id):
        result = []
        for each_t in task_list:
            if(each_t.get_unique_gop_id() == gop_id):
                result.append(each_t)
        return result
                
    def _tasksNotInGop(self, task_list, gop_id):
        result = []
        for each_t in task_list:
            if(each_t.get_unique_gop_id() != gop_id):
                result.append(each_t)
        return result
    
    def _areAllDependanciesMet(self, task):
        A = self.RM_instance.task_mapping_table[task.get_id()]['deps_completed']
        B =  task.get_dependencies()
        if (set(A) == set(B)):
            return True
        else:
            return False
        
    # set the tasks status in RM's Task mapping table
    def setTaskStatus_inRM_TMTbl(self, task_id, task_status):
        if(task_id in self.RM_instance.task_mapping_table):
            self.RM_instance.task_mapping_table[task_id]['status'] = task_status
  
    
    def _markTaskForRelease(self, task, task_ibuffid, mapped_node_id,
                            total_tasks_released_on_specific_node,
                            total_released_tasks,                            
                            tasks_released_on_current_node
                            ):
        
        # total tasks going to be released on this node id ?        
        if(mapped_node_id in total_tasks_released_on_specific_node):
            num_tasks_goingtobe_released_on_nodeid = len(total_tasks_released_on_specific_node[mapped_node_id])
        else:
            num_tasks_goingtobe_released_on_nodeid = 0
        
        # check if all dependancies are present
        if(self._areAllDependanciesMet(task) == True):    

            # first check if the selected node is free to use
        
            selected_node = self.RM_instance.node_network.get_Node(mapped_node_id)
            if(self._IsNodeTQFull(selected_node, safe_level=SimParams.CPUNODE_TASKQ_SAFE_LEVEL)== False) and \
                (num_tasks_goingtobe_released_on_nodeid < self._nodeTQ_AvailableCapacity(mapped_node_id)):
                #(selected_node.get_id() not in total_tasks_released_on_specific_node) and \                                
        
                # the child task is now ready to be released
                # set release time in input buffers and task mapping table
                rel_time = self.env.now + SimParams.SYNCH_TIME_OFFSET
                self.RM_instance.task_mapping_table[task.get_id()]['release_time'] = rel_time
                self.RM_instance.input_buffers[task_ibuffid].get_BufferItemsList()[task.get_id()].set_releaseTime(rel_time)
                if(self.RM_instance.input_buffers[task_ibuffid].get_BufferItemsList()[task.get_id()].get_initiallyScheduled() == False):
                    self.RM_instance.input_buffers[task_ibuffid].get_BufferItemsList()[task.get_id()].set_initiallyScheduled(True)
                
                # set the task status on the tm table
                self.setTaskStatus_inRM_TMTbl(task.get_id(), TaskStatus.TASK_MARKED_FOR_RELEASE)
                
                return True
                               
            else:
                # node is full, so just wait till it is free
                self.RM_instance.task_mapping_table[task.get_id()]['status'] = TaskStatus.TASK_READY_WAITING  
                return False
        else:
            return False
                

    
       
        
        
    #######################################
    ## Cleanup functions for: 
    ## - task mapping table
    ## - flow table
    #######################################
    def taskMappingTable_Remove(self, finished_task):
        output_buffer = self.RM_instance.output_buffer
        
        # what type of frame is this ? last order one ? (speeding up)
        if(finished_task.get_frameIXinGOP() in [8, 9, 10, 11]):
        
            # if all frames in a gop has been completed 
            # then remove all respective tasks from task-mapping-table
            unique_gop_id = finished_task.get_unique_gop_id()
            
            #frames_completed = []
            frames_completed = [t for t in output_buffer.get_BufferItemsList().values() if t.get_unique_gop_id() == unique_gop_id]
            
#            for each_task in output_buffer.get_BuffContents():
#                if each_task.get_unique_gop_id() == unique_gop_id:             
#                    frames_completed.append(each_task.get_id()) 

            if(len(frames_completed) == len(finished_task.get_gopstructure())):
                # yes now remove task from task-mapping table                
                for each_task_id in frames_completed: 
                    if(each_task_id in self.RM_instance.task_mapping_table):
                        del self.RM_instance.task_mapping_table[each_task_id]
            
        else:
            return
        
    
    
    #############################################
    ## Volatile Task Mapping Table    
    #############################################
    
    #### IMPORTANT : if you add any entries here - you have to update the functions in tilemappingschemeImpl #####
    def volatileTaskMappingTable_addEntry(self, entry, new_task):        
        if SimParams.RESOURCEMANAGER_USE_VOLATILE_TMTBL == False:
            sys.exit("volatileTaskMappingTable_addEntry::Error - SimParams.RESOURCEMANAGER_USE_VOLATILE_TMTBL == False")
        
        newtask_node_id = entry['node_id']                
        # add new fields to entry
        entry['task_id'] = new_task.get_id()      
        entry['deadline'] = new_task.getEstimatedRelativeDeadline_Div_x()   # we can't use EQF, since hevc task sizes could be large
        entry['ftype'] = new_task.get_frameType()
        entry['strm_key'] = "%d_%d" % (new_task.get_wfid(), new_task.get_video_stream_id())
        
        vol_tm_tbl =  self.RM_instance.volatile_task_mapping_table['runtime_task_mapping']        
        if newtask_node_id not in vol_tm_tbl:
            vol_tm_tbl[newtask_node_id] = [entry]
        else:
            vol_tm_tbl[newtask_node_id].append(entry)
        
        # update node usage
        self.volatileTaskMappingTable_updateNodeUsage(newtask_node_id, new_task)
        
        # sort the table entries according to task priority
        for each_node_id, each_task_entry in vol_tm_tbl.iteritems():
            new_sorted_entry = sorted(each_task_entry, key=itemgetter('pri'), reverse=True)
            vol_tm_tbl[each_node_id] = new_sorted_entry
    
    def volatileTaskMappingTable_updateNodeUsage(self, nid, new_task):
        if SimParams.RESOURCEMANAGER_USE_VOLATILE_TMTBL == False:
            sys.exit("volatileTaskMappingTable_addEntry::Error - SimParams.RESOURCEMANAGER_USE_VOLATILE_TMTBL == False")
                
        vol_nu_tm_tbl =  self.RM_instance.volatile_task_mapping_table['node_usage_field']        
        if nid not in vol_nu_tm_tbl:
            vol_nu_tm_tbl[nid] = new_task.get_worstCaseComputationCost()
        else:
            vol_nu_tm_tbl[nid] += new_task.get_worstCaseComputationCost()
        
        
        
    
    # remove task from node entry, keep sort order
    def volatileTaskMappingTable_RemoveSpecificTask(self, rem_task_id, node_id):
        if SimParams.RESOURCEMANAGER_USE_VOLATILE_TMTBL == False:
            sys.exit("volatileTaskMappingTable_RemoveSpecificTask::Error - SimParams.RESOURCEMANAGER_USE_VOLATILE_TMTBL == False")
        
        vol_tm_tbl =  self.RM_instance.volatile_task_mapping_table['runtime_task_mapping']        
        rem_ix = None
        for ix, each_task_enry in enumerate(vol_tm_tbl[node_id]):            
            if each_task_enry['task_id'] == rem_task_id:
                rem_ix = ix
                break;
            
        if rem_ix != None:
            del vol_tm_tbl[node_id][rem_ix]
        else:
            sys.exit("volatileTaskMappingTable_RemoveSpecificTask:: Error task not found !")
                
    
    # -- version 1 -- 
    # - takes into account the WCET  of tasks  
    def volatileTaskMappingTable_RemoveExpiredTasks_v1(self):        
        if SimParams.RESOURCEMANAGER_USE_VOLATILE_TMTBL == False:
            sys.exit("volatileTaskMappingTable_RemoveExpiredTasks_v1::Error - SimParams.RESOURCEMANAGER_USE_VOLATILE_TMTBL == False")
         
        vol_tm_tbl =  self.RM_instance.volatile_task_mapping_table['runtime_task_mapping']        
        # we only need to clean the table, if the MS signalling is switched off
        if (SimParams.MS_SIGNALLING_NOTIFY_TASK_COMPLETE_ENABLE == False):
            if self.env.now != self.RM_instance.volatile_task_mapping_table_lastrefreshed:                            
                time_now = self.env.now
                for each_node_id, each_task_entry in vol_tm_tbl.iteritems(): # do for each node
                    if (len(each_task_entry)>0):
                        # check if each task has completed processing
                        rem_indexes = []
                        hp_task_rel_time = each_task_entry[0]['release_time'] # release time of highest pri task
                        for ix, each_task_dict in enumerate(each_task_entry): # sorted in pri desc order                    
                            start_time = hp_task_rel_time + np.sum([t['wcc'] for t in each_task_entry[:ix]]) # predicted start time
                            elapsed_time = (time_now - start_time) 
                            if (elapsed_time > each_task_dict['wcc']): # remove item
                                rem_indexes.append(ix)
                         
                        # remove potentially finished tasks, return new list
                        vol_tm_tbl[each_node_id] = self._removeListItems_byIndex(each_task_entry, rem_indexes)                
                self.RM_instance.volatile_task_mapping_table_lastrefreshed = self.env.now        
    
    
    
    
    # does not take into account task blocking
    def volatileTaskMappingTable_RemoveExpiredTasks_woBlocking_v1(self):
        if SimParams.RESOURCEMANAGER_USE_VOLATILE_TMTBL == False:
            sys.exit("volatileTaskMappingTable_RemoveExpiredTasks_woBlocking_v1::Error - SimParams.RESOURCEMANAGER_USE_VOLATILE_TMTBL == False")
        
        vol_tm_tbl =  self.RM_instance.volatile_task_mapping_table['runtime_task_mapping']        
        # we only need to clean the table, if the MS signalling is switched off
        if (SimParams.MS_SIGNALLING_NOTIFY_TASK_COMPLETE_ENABLE == False):
            if self.env.now != self.RM_instance.volatile_task_mapping_table_lastrefreshed:                            
                time_now = self.env.now
                for each_node_id, each_task_entry in vol_tm_tbl.iteritems(): # do for each node
                    if (len(each_task_entry)>0):
                        # check if each task has completed processing
                        rem_indexes = []
                        #hp_task_rel_time = each_task_entry[0]['release_time'] # release time of highest pri task
                        for ix, each_task_dict in enumerate(each_task_entry): # sorted in pri desc order                    
                            start_time = each_task_dict['release_time']
                            elapsed_time = (time_now - start_time) 
                            if (elapsed_time > each_task_dict['wcc']): # remove item
                                rem_indexes.append(ix)
                        
                        # remove potentially finished tasks, return new list
                        vol_tm_tbl[each_node_id] = self._removeListItems_byIndex(each_task_entry, rem_indexes)
                
                self.RM_instance.volatile_task_mapping_table_lastrefreshed = self.env.now
        
    
    
       
    def volatileTaskMappingTable_RemoveExpiredTasks_TileTasks_v1(self):        
        if SimParams.RESOURCEMANAGER_USE_VOLATILE_TMTBL == False:
            sys.exit("volatileTaskMappingTable_RemoveExpiredTasks_TileTasks_v1::Error - SimParams.RESOURCEMANAGER_USE_VOLATILE_TMTBL == False")
        
        # we only need to clean the table, if the MS signalling is switched off
        if (SimParams.MS_SIGNALLING_NOTIFY_TASK_COMPLETE_ENABLE == False):
            self.volatileTaskMappingTable_RemoveExpiredTasks_v1()
            #self.volatileTaskMappingTable_RemoveExpiredTasks_woBlocking_v1()
            
                    
    def _removeListItems_byIndex(self, lst, rem_ixs):
        new_list = [t for ix,t in enumerate(lst) if ix not in rem_ixs]
        return new_list
             
         
    
    
    
    ######################################################
    # Shared resources locking mechanisms
    #  - RM task mapping table
    #  - RM flow table
    ######################################################
    
    def lock_RM_TMtbl(self):
        while(self.RM_instance.mutex_tmtbl.level == 1):
            i=1 # busy wait                                                            
        self.RM_instance.mutex_tmtbl.put(1) # obtain lock
        
    def release_RM_TMtbl(self):
        self.RM_instance.mutex_tmtbl.get(1) # release lock
        
    def lock_RM_FLWtbl(self):
        while(self.RM_instance.flow_table.mutex.level == 1):
            i=1 # busy wait                                       
        self.RM_instance.flow_table.mutex.put(1)   # obtain lock   
    
    def release_RM_FLWtbl(self):
        self.RM_instance.flow_table.mutex.get(1) # release lock
        
        
        
    ######################################################
    # Deprecated function 
    ######################################################
    def scheduleAndMapTasks_MultiStream(self):
        sys.exit('scheduleAndMapTasks_MultiStream :: Error ! deprecated on 12/11/14')
    def mapChildTasks(self, finished_task):
        sys.exit('mapChildTasks :: Error ! deprecated on 12/11/14')
    def releaseChildTasks_v1(self, finished_task, node_id):
        sys.exit('releaseChildTasks_v1 :: Error ! deprecated on 12/11/14')
        
        
        
    