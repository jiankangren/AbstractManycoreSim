import pprint
import sys
#import networkx as nx
import simpy
import matplotlib.pyplot as plt
import numpy as np

## local imports
from SimParams import SimParams
from libNoCModel.NoCFlow import NoCFlow


class RuntimeApplicationInfo:
    
    def __init__(self, env, RMinstance):
        self.env = env
        self.RMinstance = RMinstance
        self.stream_info = {}
        self.tasks = {} # list of tasks the system is dealing with
        self.flows = {} # list of flows the system is dealing with          
        self.task_to_node_mapping = {}  # which tasks are mapped to which node
        
        
    
    ## getters/setters
    
    # these should actually be called (WCRT) not WCET
    def setTask_analytical_wcet(self, task_key, awcet):
        self.tasks[task_key].set_analytical_wcet(awcet)
    def setFlow_analytical_wcet(self, flow_key, awcet):
        self.flows[flow_key].set_analytical_wcet(awcet)    
    
    def setTask_analytical_wcet_with_dep(self, task_key, awcet_with_dep):
        self.tasks[task_key].set_analytical_wcrt_with_deps(awcet_with_dep)
    def setFlow_analytical_wcet_with_dep(self, flow_key, awcet):
        self.flows[flow_key].set_analytical_wcet(awcet)    
    
    
    def setStream_critical_path_wcet(self, strm_key, awcet):
        self.stream_info[strm_key].set_criticalPathWCET(awcet)
    
    
    def getTasks(self):
        return self.tasks.values()            
    def getFlows(self):
        return self.flows.values()
    def getStreams(self):
        return self.stream_info.values()
    
    def getTask(self, gop_ix, wf_id, strm_id):
        
        # normal gop tasks         
        for each_t in self.tasks.values():
            if (each_t.get_wfid()== wf_id) and (each_t.get_video_stream_id() == strm_id):
                if(each_t.get_frameIXinGOP() == gop_ix):
                    return each_t
                
        return None
    
    def getStreamSpecificTasks(self,wf_id, strm_id):
        all_tasks = []
        for each_t in self.tasks.values():
            if (each_t.get_wfid()== wf_id) and (each_t.get_video_stream_id() == strm_id):
                all_tasks.append(each_t)
                
        # sort tasks into gop_ix order
        sorted_tasks = sorted(all_tasks, key=lambda x: x.get_frameIXinGOP(), reverse=False)
        
        return sorted_tasks
                
        
    
    def getTask_analytical_wcet(self, task_key):
        return self.tasks[task_key].get_analytical_wcet()
    def getFlow_analytical_wcet(self, flow_key):
        return self.flows[flow_key].get_analytical_wcet()
    def getStream_critical_path_wcet(self, strm_key):
        return self.stream_info[strm_key].get_criticalPathWCET()
        
    
    ## task management
    def addTask(self, task):
        #print "addTask: enter"
        if task.get_id() not in self.tasks:
            self.tasks[task.get_id()] = task
            
            # record the task to node mapping
            node_id = task.get_processingCore()
            if node_id in self.task_to_node_mapping:                
                self.task_to_node_mapping[node_id].append(task)
            else:
                self.task_to_node_mapping[node_id] = [task]
            
            self.RMinstance.node_network.get_Nodes()[node_id].update_SystemSlack_addTask(task)
                        
    def removeTask(self, task):
        if task.get_id() in self.tasks:
            del self.tasks[task.get_id()]
            
            # update the task to node mapping
            node_id = task.get_processingCore()
            for ix, each_task in enumerate(self.task_to_node_mapping[node_id]):
                # get index of this task; try to match the task
                if (each_task.get_id() == task.get_id() and
                    each_task.get_priority() == task.get_priority() and
                    each_task.get_frameIXinGOP() == task.get_frameIXinGOP() and
                    each_task.get_frameType() == task.get_frameType() and
                    each_task.get_wfid() == task.get_wfid() and
                    each_task.get_video_stream_id() == task.get_video_stream_id()):
                    
                    t_ix = ix
                    break
            
            del self.task_to_node_mapping[node_id][t_ix]
            
            self.RMinstance.node_network.get_Nodes()[node_id].update_SystemSlack_removeTask(task)
            
    
    def updateTaskProcessingCore(self,gop_ix, wf_id, strm_id, new_node_id):
        old_mapped_processingcore_id = None
        updated_task = None
        
        for each_t in self.tasks.values():
            if ((each_t.get_wfid()== wf_id) and 
                (each_t.get_video_stream_id() == strm_id) and
                (each_t.get_frameIXinGOP() == gop_ix)):                    
                    updated_task = each_t
                    
                    # update task properties
                    old_mapped_processingcore_id = each_t.get_processingCore()                    
                    each_t.set_processingCore(new_node_id)                    
                    break
        
        if(old_mapped_processingcore_id != None) and (updated_task != None):
            return (updated_task, old_mapped_processingcore_id)
        else:
            # this means the stream was removed at this point, but still the last invocation
            # of the task was present in the nodes task queue
            print "RuntimeApplicationInfo::updateTaskProcessingCore: stream already removed, so no remapping performed !!"
            return (None, None)
                    
    # update local task to node mapping properties            
    def updateTaskToNodeMappingTbl(self, task, old_node_id, new_node_id):                
        
        if(task != None) and (old_node_id != None):
        
            # find and delete task from old node           
            for ix, each_task in enumerate(self.task_to_node_mapping[old_node_id]):
                    # get index of this task; try to match the task
                    if (each_task.get_id() == task.get_id() and
                        each_task.get_priority() == task.get_priority() and
                        each_task.get_frameIXinGOP() == task.get_frameIXinGOP() and
                        each_task.get_frameType() == task.get_frameType() and
                        each_task.get_wfid() == task.get_wfid() and
                        each_task.get_video_stream_id() == task.get_video_stream_id()):
                        
                        t_ix = ix
                        del self.task_to_node_mapping[old_node_id][t_ix]
                                                        
            # add task to the new node in the table
            self.task_to_node_mapping[new_node_id].append(task)
            return True
        else:
            return False
            
            
    ## flow management
    def addFlow(self, flow):
        
        #key = str(flow.get_respectiveSrcTaskId()) + "_" + str(flow.get_respectiveDstTaskId())        
        key = self.RMinstance.NoCSchedulabilityAnalyser._get_flow_key(flow)
        
        if key not in self.flows:
            self.flows[key] = flow
                        
    def removeFlow(self, flow):
        
        #key = str(flow.get_respectiveSrcTaskId()) + "_" + str(flow.get_respectiveDstTaskId())
        key = self.RMinstance.NoCSchedulabilityAnalyser._get_flow_key(flow)
                
        if key in self.flows:
            del self.flows[key]
    
    
    
    def getRouteLoad(self, src_node_id, dst_node_id, link_to_flow_mapping):
        # get links for this route
        target_route = self.RMinstance.interconnect.getRouteXY(src_node_id, dst_node_id)        
        target_route = [r.get_id() for r in target_route]
        
        number_of_flows_using_links_in_targetroute = []
        # how many flows are using this route ?        
        for each_link_k, each_flow_per_link in link_to_flow_mapping.iteritems():
            if each_link_k in target_route:
                number_of_flows_using_links_in_targetroute.extend(each_flow_per_link)
       
        return len(number_of_flows_using_links_in_targetroute)
        
        
        
           
            
    def getLinkToFlowMapping(self, all_flows=None):        
        if(all_flows==None):
            all_flows=self.flows.values()
                
        link_to_flow_mapping = {}
        for each_flow in all_flows:
            noc_links =  each_flow.get_route()
            for each_link in noc_links:
                if each_link.get_id() not in link_to_flow_mapping:
                    link_to_flow_mapping[each_link.get_id()] = [each_flow]
                else:
                    link_to_flow_mapping[each_link.get_id()].append(each_flow)
                    
        return link_to_flow_mapping
    
    
    def getNodeToTaskMapping(self, node_id=None):
        
        # build temp node to task mapping
        node_tasks_mapping = {}
        for each_node in self.RMinstance.node_network.get_Nodes():
            node_tasks_mapping[each_node.get_id()] = []
        
        # which tasks are in which node ?
        for each_task in self.tasks.values():
            if(each_task.get_processingCore() not in node_tasks_mapping):
                node_tasks_mapping[each_task.get_processingCore()] = [each_task]
            else:
                node_tasks_mapping[each_task.get_processingCore()].append(each_task)
        
        if(node_id == None):
            return node_tasks_mapping
        else:
            return node_tasks_mapping[node_id]
    
    
    def getNodeLowestMappedTasks(self):
        node_to_task_mapping = self.getNodeToTaskMapping()        
        min_tasks = min([len(x) for x in node_to_task_mapping.values()])
        selected_node_id = [k for k,v in node_to_task_mapping.iteritems() if len(v) == min_tasks][0]
        
        return selected_node_id
    
    
    def getNodeToTaskMapping_forSpecificVideoID(self, wf_id, strm_id):
        
        # build temp node to task mapping
        node_tasks_mapping = {}
        for each_node in self.RMinstance.node_network.get_Nodes():
            node_tasks_mapping[each_node.get_id()] = []
        
        # which tasks are in which node ?
        for each_task in self.tasks.values():
            if(each_task.get_wfid() == wf_id and each_task.get_video_stream_id() == strm_id):
                if(each_task.get_processingCore() not in node_tasks_mapping):
                    node_tasks_mapping[each_task.get_processingCore()] = [each_task]
                else:
                    node_tasks_mapping[each_task.get_processingCore()].append(each_task)
        
        return node_tasks_mapping
    
    def getFlows_RelatedtoSpecificVideoID(self, wf_id, strm_id):
        
        stream_specific_flw_list = []
        
        for f in self.getFlows():
            src_task = f.get_respectiveSrcTask()
            if(src_task.get_wfid() == wf_id and src_task.get_video_stream_id() == strm_id):
                stream_specific_flw_list.append(f)
        
        return stream_specific_flw_list
        
      
    
    
    # each node is connected to two or more links
    # each of these links have flows
    # congestion rating = sum of number of flows 
    #                     associated to the links connected to the given node
    def getNodeCongestionRating(self, node_id, task_pri=None, nextid=None):
        
        # what are the links connected to the node ?
        node_connected_linkids = [l.get_id() for l in self.RMinstance.interconnect.getLinksConnectedToNode(node_id)]
        
        # link to flow mapping
        link_to_flow_mapping = self.getLinkToFlowMapping()

        node_congestion = 0 # number of flows that will block a given task
        
        for each_link_id in node_connected_linkids:
            if(each_link_id in link_to_flow_mapping):
                for each_flow in link_to_flow_mapping[each_link_id]:
                    if(task_pri != None):
                        flow_pri = NoCFlow.getPriorityFromTask(task_pri, self.RMinstance, nextid)
                        if(flow_pri < each_flow.get_priority()):
                            node_congestion += 1
                    else:   # if supplied task priority is None then this flow will by default be counted as congestion
                        node_congestion += 1
        
        return node_congestion
                        
    
    # get utilisation for a nodes/specific node
    def getNodeEstimatedUtilisation(self, node_id=None):
        
        node_tasks_mapping = {}
        
        # which tasks are in which node ?
        for each_task in self.tasks.values():
            if(each_task.get_processingCore() not in node_tasks_mapping):
                node_tasks_mapping[each_task.get_processingCore()] = [each_task]
            else:
                node_tasks_mapping[each_task.get_processingCore()].append(each_task)
        
        # fill in nodes with no tasks mapped
        for each_node in self.RMinstance.node_network.get_Nodes():
            if each_node.get_id() not in node_tasks_mapping:
                node_tasks_mapping[each_node.get_id()] = []
                
        # calculated the utilisation per node
        node_util = {}        
        for each_node_key,each_node_val in node_tasks_mapping.iteritems():
            
            if(len(each_node_val) > 0):
                total_util = 0.0
                for each_task in each_node_val:
                    task_util = float(each_task.get_worstCaseComputationCost()/each_task.get_period())                
                    total_util += task_util # summation of all the task utils
                    
                node_util[each_node_key] = total_util
            else:
                node_util[each_node_key] = 0.0
                
        
        if(node_id == None):
            return node_util
        else:
            return node_util[node_id]
                
    
    
    def taskSetUtilisation(self):
        all_tasks_in_system = []
        for each_task in self.tasks.values():
            u = each_task.get_computationCost()/each_task.get_period()
            all_tasks_in_system.append(u)
        
        total_task_utilisation = np.sum(all_tasks_in_system)
        
        all_stream_task_util = {}        
        for strm_k, each_stream in self.stream_info.iteritems():
            stream_task_util = []
            stream_period = None 
            all_tasks_cc = []                       
            for each_task in self.tasks.values():
                if(each_task.get_wfid() == each_stream.get_wfid() and each_task.get_video_stream_id() == each_stream.get_stream_id()):
                    if(stream_period==None): 
                        stream_period=each_task.get_period()
                    
                    all_tasks_cc.append(each_task.get_computationCost())
            
            u = np.sum(all_tasks_cc)/stream_period
            all_stream_task_util[strm_k] = u
        
        
#         print "-------- utilisation analysis : START ------------"
#         pprint.pprint(all_stream_task_util)
#         print "total_task_utilisation : " + str(total_task_utilisation)
#         print "-------- utilisation analysis : END ------------"
    
        
        return (all_stream_task_util, total_task_utilisation)
        
        
                
    ## stream management
    def addStream(self, strm_key, entry):        
        #print "addStream:: " + strm_key
        if strm_key not in self.stream_info:
            self.stream_info[strm_key] = entry
    
    def removeStream(self, strm_key):
        if strm_key in self.stream_info:
            del self.stream_info[strm_key] 
        

class VideoStreamInfo():
    
    def __init__(self,  id,
                        wf_id,
                        gop_structure, 
                        resolution,
                        arrival_rate_ub,
                        frame_rate,
                        start_time):
        
        self.id = id
        self.wf_id = wf_id
        self.gop_structure = gop_structure 
        self.resolution = resolution
        self.arrival_rate_ub = arrival_rate_ub
        self.frame_rate = frame_rate
        self.start_time = start_time
        self.taskids = [] # periodic tasks within the stream
        self.critical_path_wcet = None
        
    
    # minimal version of to-string (for schedulability debug)
    def getSchedulability_toString(self):
        debug = ""
        debug += " wfid='" + str(self.wf_id)+ "'"
        debug += " vid='" + str(self.id) + "'"
        debug += " res='" + str(self.resolution)+ "'"
        debug += " ar_ub='" + str(self.arrival_rate_ub)+ "'"
        debug += " st='" + str(self.start_time)+ "'"        
        
        return debug
        
    
    def get_key(self):
        return str(self.wf_id) + "_" + str(self.id)
       
    def get_wfid(self):
        return self.wf_id
    def get_stream_id(self):
        return self.id
    def get_gopStructure(self):
        return self.gop_structure    
    def get_resolution(self):
        return self.resolution
    def get_arrivalRateUB(self):
        return self.arrival_rate_ub
    def get_frame_rate(self):
        return self.frame_rate
    def get_startTime(self):
        return self.start_time
    def get_end2end_deadline(self):
        e2ed = (float(len(self.gop_structure))/float(self.frame_rate))
        return e2ed
    def get_criticalPathWCET(self):
        return self.critical_path_wcet
    
    def set_streamTasks(self, taskids):
        self.taskids = taskids
    def set_criticalPathWCET(self, cpc):
        self.critical_path_wcet = cpc
    
    