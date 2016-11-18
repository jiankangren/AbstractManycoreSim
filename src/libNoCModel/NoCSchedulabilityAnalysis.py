import pprint
import sys, os
import numpy as np
import time
#import networkx as nx
import simpy
import matplotlib.pyplot as plt
from datetime import timedelta, datetime

## local imports
from SimParams import SimParams
from libDebug.Debug import Debug, DebugCat
from libNoCModel.NoCFlow import FlowType


class NoCSchedulabilityAnalysis:
    
    def __init__(self, env, runtime_app_info, rm_instance):
        self.env = env
        self.label = "NoCSchedulabilityAnalysis"
        self.runtime_app_info = runtime_app_info
        
        self.RMInstance = rm_instance
        
        self.unschedulable_tasks = []
        self.unschedulable_flows = []
        self.unschedulable_streams = []
        
        self.track_admission_tests = []
        self.track_vsutil_vs_schedulability = []
    
    ## we can use this data later to save, display or analyse
    def recordSchedulabilityTest(self, stream_specs, test_time_taken, task_stats=True, flow_stats=True):
        test_stats = {                      
                      "new_stream_stats" : stream_specs,
                      
                      # task specific stats  
                      "current_alltasks_wcrt_distibution" : ([ (self._getMOGARelatedTaskName(x), x.get_analytical_wcet()) for x in self.runtime_app_info.getTasks()]) 
                      if task_stats==True else None,  
                      
                      #"current_alltasks_wcrt_withdeps_distibution" : ([(self._getMOGARelatedTaskName(x),x.get_analytical_wcrt_with_deps()) for x in self.runtime_app_info.getTasks()]) 
                      #if task_stats==True else None,                    
                      
                      "current_alltasks_wcet_min" : (min([x.get_analytical_wcet() for x in self.runtime_app_info.getTasks() if x.get_analytical_wcet() is not None])) 
                      if task_stats==True else None,
                      "current_alltasks_wcet_max" : (max([x.get_analytical_wcet() for x in self.runtime_app_info.getTasks() if x.get_analytical_wcet() is not None]))
                      if task_stats==True else None,
                      "current_alltasks_wcet_avg" : (np.mean([x.get_analytical_wcet() for x in self.runtime_app_info.getTasks() if x.get_analytical_wcet() is not None]))
                      if task_stats==True else None,
                      
                      # flow specific stats
                      "current_allflows_wcrt_distribution" : ([ (self._getMOGARelatedFlowName(x),  x.get_analytical_wcet()) for x in self.runtime_app_info.getFlows()])
                      if flow_stats==True else None,
                      "current_allflows_wcet_min" : (min([x.get_analytical_wcet() for x in self.runtime_app_info.getFlows() if x.get_analytical_wcet() is not None]))
                      if flow_stats==True else None,
                      "current_allflows_wcet_max" : (max([x.get_analytical_wcet() for x in self.runtime_app_info.getFlows() if x.get_analytical_wcet() is not None]))
                      if flow_stats==True else None,
                      "current_allflows_wcet_avg" : (np.mean([x.get_analytical_wcet() for x in self.runtime_app_info.getFlows() if x.get_analytical_wcet() is not None]))
                      if flow_stats==True else None,
                      
                      # stream specific stats
                      "current_stream_cp_wcet" : [(x.get_key(), x.get_criticalPathWCET()) for x in self.runtime_app_info.getStreams()],                      
                      
                      # time taken to perform schedulability test
                      "test_time_taken" : test_time_taken                                            
                      }
        
        self.track_admission_tests.append(test_stats)
    
    
    # called every time a video req is made, at the AC
    def recordUtilVsSchedStats(self):                
        entry = {
        
            # what are the streams present in the system now ?
            'vid_streams_wcrt_info' : [(x.get_key(), x.get_resolution(), x.get_criticalPathWCET(), SimParams.WFGEN_MAX_GOPS_PER_VID) 
                                       for x in self.runtime_app_info.getStreams()],
            
            # what is the utilisation of the tasks in the system ?
            'all_task_util' :  self.runtime_app_info.taskSetUtilisation()                   
        }
        
        self.track_vsutil_vs_schedulability.append(entry)
        
    
    
    
    # get response time of a newly arriving task
    def getResponseTime_newTask(self, new_task):
        
        application_tasks = self.runtime_app_info.getTasks()        
        new_task_wcet = new_task.getResponseTime(new_task.getInterferenceSet_withPrCnst(application_tasks))
        
        return new_task_wcet
    
    
    # check if system is schedulable
    def checkSchedulability(self, stream_specs):        
        
        result = False
        
        test_start_time = time.clock()
        
        # find the wcet for tasks and flows
        if(self.performAnalysis_ShiAndBurns() == True):
            # if the tasks and flows independently are schedulable, then check the critical paths 
            if(self.performAnalysis_criticalPath() == True):
                result = True
            else:
                result = False
        else:
            result = False
        
        test_time_taken = time.clock() - test_start_time        
        
        # calculate the task execution costs taking into account dependancies
        self.performAnalysis_WCRT_TasksWithDeps()
        
        # logout schedulability
        self.recordSchedulabilityTest(stream_specs, test_time_taken)
        
        return result
    
    
    # check if system is schedulable
    def checkSchedulability_directly_criticalPath(self, stream_specs):        
        
        result = False
        
        test_start_time = time.clock()
        
        # find the wcet for tasks and flows
        self.performAnalysis_ShiAndBurns_FullEval()
        # if the tasks and flows independently are schedulable, then check the critical paths 
        if(self.performAnalysis_criticalPath_evaluateAllStreams() == True):
            result = True
        else:
            result = False
    
        test_time_taken = time.clock() - test_start_time        
        
        # calculate the task execution costs taking into account dependancies
        self.performAnalysis_WCRT_TasksWithDeps()
        
        # logout schedulability
        self.recordSchedulabilityTest(stream_specs, test_time_taken)
        
        return result
    
    
    # check if system is schedulable
    # taking into account communication between nodes and mmc
    def checkSchedulability_directly_criticalPath_withMMCDataRDWR(self, stream_specs):        
        
        result = False        
        test_start_time = time.clock()
                
        # find the wcet for tasks and flows
        self.performAnalysis_ShiAndBurns_FullEval_withMMCDataRDWR()
        # if the tasks and flows independently are schedulable, then check the critical paths 
        if(self.performAnalysis_criticalPath_evaluateAllStreams_withMMCDataRDWR() == True):
            result = True
        else:
            result = False
    
        test_time_taken = time.clock() - test_start_time        
        
        # calculate the task execution costs taking into account dependancies
        self.performAnalysis_WCRT_TasksWithDeps()
        
        # logout schedulability
        self.recordSchedulabilityTest(stream_specs, test_time_taken)
        
        return result
    
    
    
    def checkSchedulability_onlyDIPrecheck(self, stream_specs):        
        
        result = False
        
        test_start_time = time.clock()
        
        ### first check using only DI flows ###
        # -------------------------------------
        # find the wcet for tasks and flows
        if(self.performAnalysis_ShiAndBurns_onlyDI() == True):
            # if the tasks and flows independently are schedulable, then check the critical paths 
            if(self.performAnalysis_criticalPath() == True):
                
                ### now check with both DI and II flows ###
                # -----------------------------------------
                # find the wcet for tasks and flows
                if(self.performAnalysis_ShiAndBurns() == True):
                    # if the tasks and flows independently are schedulable, then check the critical paths 
                    if(self.performAnalysis_criticalPath() == True):                        
                        result = True
                    else:
                        Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'outputReport::, : critical-path unschedulable', DebugCat.DEBUG_CAT_SCHEDANALYSIS)
                        result = False
                else:
                    Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'outputReport::, : tasks or flows unschedulable', DebugCat.DEBUG_CAT_SCHEDANALYSIS)
                    result = False
                # -----------------------------------------
                    
            else:
                Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'outputReport::, : *onlyDI* : critical-path unschedulable', DebugCat.DEBUG_CAT_SCHEDANALYSIS)                
                result = False
        else:            
            Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'outputReport::, : *onlyDI* : tasks or flows unschedulable', DebugCat.DEBUG_CAT_SCHEDANALYSIS)
            result = False
        
        test_time_taken = time.clock() - test_start_time
        
        # calculate the task execution costs taking into account dependancies
        self.performAnalysis_WCRT_TasksWithDeps()
        
        # record results of schedulability test        
        self.recordSchedulabilityTest(stream_specs, test_time_taken)
        
        return result
    
    
    def checkSchedulability_onlyDIPrecheck_OnlyCompCost(self, stream_specs):        
        
        result = False
        
        test_start_time = time.clock()
        
        ### first check using only DI flows ###
        # -------------------------------------
        # find the wcet for tasks
        if(self.performAnalysis_ShiAndBurns_onlyDI(check_tasks=True, check_flows=False) == True):
            # if the tasks and flows independently are schedulable, then check the critical paths 
            if(self.performAnalysis_criticalPath_tasksOnly() == True):                
                ### now check with both DI and II flows ###
                # -----------------------------------------
                # find the wcet for tasks
                if(self.performAnalysis_ShiAndBurns(check_tasks=True, check_flows=False) == True):
                    # if the tasks and flows independently are schedulable, then check the critical paths 
                    if(self.performAnalysis_criticalPath_tasksOnly() == True):                        
                        result = True
                    else:
                        Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'outputReport::, : critical-path unschedulable', DebugCat.DEBUG_CAT_SCHEDANALYSIS)
                        result = False
                else:
                    Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'outputReport::, : tasks or flows unschedulable', DebugCat.DEBUG_CAT_SCHEDANALYSIS)
                    result = False
                # -----------------------------------------                    
            else:
                Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'outputReport::, : *onlyDI* : critical-path unschedulable', DebugCat.DEBUG_CAT_SCHEDANALYSIS)                
                result = False
        else:            
            Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'outputReport::, : *onlyDI* : tasks or flows unschedulable', DebugCat.DEBUG_CAT_SCHEDANALYSIS)
            result = False
        
        test_time_taken = time.clock() - test_start_time        
        self.recordSchedulabilityTest(stream_specs, test_time_taken, task_stats=True,flow_stats=False)
        
        return result
    
    
    
    # Shi and Burns basic tests for tasks and flows, treating everything independently     
    # only considering direct interference flows, not indirect interference  
    def performAnalysis_ShiAndBurns_onlyDI(self, check_tasks=True, check_flows=True):
        
        # before performing analysis, reset lists
        self.unschedulable_flows = []
        self.unschedulable_tasks = []
        
        application_tasks = self.runtime_app_info.getTasks()
        application_flows = self.runtime_app_info.getFlows()
        
        if(check_tasks == True):
            # check tasks
            for t_ix, t in enumerate(application_tasks):                 
                t_wcet = t.getResponseTime(t.getInterferenceSet_withPrCnst(application_tasks))            
                self.runtime_app_info.setTask_analytical_wcet(t.get_id(), t_wcet)   # stored for later use
                
                percentage_of_t_wcet = float(t_wcet*(float(SimParams.WCRT_SCHEDULABILITY_TEST_PERCENTAGE)/100.0))            
                if percentage_of_t_wcet > t.get_end_to_end_deadline():
                    self.unschedulable_tasks.append(t)                
                    return False    # return immediately, to save time                
        
        
        if(check_flows == True):           
            # check flows
            for f_ix, f in enumerate(application_flows):
                
                # set release jitter again
                f_source_t = f.get_respectiveSrcTask()
                
                if(f_source_t != None):            
                    #rj = f_source_t.getResponseTime(f_source_t.getInterferenceSet_withPrCnst(self.runtime_app_info.getTasks()))                
                    rj = self.runtime_app_info.getTask_analytical_wcet(f_source_t.get_id())
                else:
                    rj = 0.0
                
                f.set_releaseJitter(rj)            
                f_wcet = f.getDirectInterferenceWorstCaseLatency(application_flows)            
                f_key = self._get_flow_key(f)
                self.runtime_app_info.setFlow_analytical_wcet(f_key, f_wcet)    # stored for later use                     
                
                percentage_of_f_wcet = float(f_wcet*(float(SimParams.WCRT_SCHEDULABILITY_TEST_PERCENTAGE)/100.0)) 
                if percentage_of_f_wcet > f.get_period():                  
                    self.unschedulable_flows.append(f)                
                    return False    # return immediately, to save time
            
        return True
    
              
    
    # Shi and Burns basic tests for tasks and flows, treating everything independently       
    def performAnalysis_ShiAndBurns(self, check_tasks=True, check_flows=True):

        # before performing analysis, reset lists
        self.unschedulable_flows = []
        self.unschedulable_tasks = []
        
        application_tasks = self.runtime_app_info.getTasks()
        application_flows = self.runtime_app_info.getFlows()
        
        if(check_tasks == True):
            # check tasks
            for t_ix, t in enumerate(application_tasks):                 
                t_wcet = t.getResponseTime(t.getInterferenceSet_withPrCnst(application_tasks))            
                self.runtime_app_info.setTask_analytical_wcet(t.get_id(), t_wcet)   # stored for later use            
                
                percentage_of_t_wcet = float(t_wcet*(float(SimParams.WCRT_SCHEDULABILITY_TEST_PERCENTAGE)/100.0))            
                if percentage_of_t_wcet > t.get_end_to_end_deadline():
                    self.unschedulable_tasks.append(t)
                    return False    # return immediately, to save time
        
        if(check_flows == True):
            
            # check flows
            for f_ix, f in enumerate(application_flows):
                
                # set release jitter again
                f_source_t = f.get_respectiveSrcTask()
                
                #rj = f_source_t.getResponseTime(f_source_t.getInterferenceSet_withPrCnst(self.runtime_app_info.getTasks()))            
                rj = self.runtime_app_info.getTask_analytical_wcet(f_source_t.get_id())
                
                f.set_releaseJitter(rj)
                timeout = datetime.utcnow() + timedelta(seconds = SimParams.WCRT_FLOW_CALC_TIMEOUT/float(len(application_flows)))            
                f_wcet = f.getWorstCaseLatency(application_flows, timeout)
                
                f_key = self._get_flow_key(f)
                self.runtime_app_info.setFlow_analytical_wcet(f_key, f_wcet)    # stored for later use                     
                
                percentage_of_f_wcet = float(f_wcet*(float(SimParams.WCRT_SCHEDULABILITY_TEST_PERCENTAGE)/100.0))
                if percentage_of_f_wcet > f.get_period():
                    self.unschedulable_flows.append(f)
                    return False    # return immediately, to save time                        
        
        return True

    
    
    # Shi and Burns basic tests for tasks and flows, treating everything independently       
    def performAnalysis_ShiAndBurns_FullEval(self, check_tasks=True, check_flows=True):
        # before performing analysis, reset lists
        self.unschedulable_flows = []
        self.unschedulable_tasks = []
        
        application_tasks = self.runtime_app_info.getTasks()
        application_flows = self.runtime_app_info.getFlows()
        
        if(check_tasks == True):
            # check tasks
            for t_ix, t in enumerate(application_tasks):                 
                t_wcet = t.getResponseTime(t.getInterferenceSet_withPrCnst(application_tasks))            
                self.runtime_app_info.setTask_analytical_wcet(t.get_id(), t_wcet)   # stored for later use            
                
                percentage_of_t_wcet = float(t_wcet*(float(SimParams.WCRT_SCHEDULABILITY_TEST_PERCENTAGE)/100.0))            
                if percentage_of_t_wcet > t.get_end_to_end_deadline():
                    self.unschedulable_tasks.append(t)                    
        
        if(check_flows == True):
            
            # check flows
            for f_ix, f in enumerate(application_flows):

#                 ## debug ##                
#                 if(f.get_respectiveSrcTask().get_unique_gop_id() == 15):
#                     print f
#                 ## debug ##
                
                # set release jitter again
                f_source_t = f.get_respectiveSrcTask()
                
                #rj = f_source_t.getResponseTime(f_source_t.getInterferenceSet_withPrCnst(self.runtime_app_info.getTasks()))            
                rj = self.runtime_app_info.getTask_analytical_wcet(f_source_t.get_id())
                
                f.set_releaseJitter(rj)
                timeout = datetime.utcnow() + timedelta(seconds = SimParams.WCRT_FLOW_CALC_TIMEOUT/float(len(application_flows)))            
                f_wcet = f.getWorstCaseLatency(application_flows, timeout)
                
#                 ## debug ##
#                 if(f_wcet == None):
#                     print f
#                     print "num_flows = " + str(len(application_flows))                    
#                     sys.exit("Error - calculating f_wcet - None")                
#                 
#                 if(f.get_id() == 180):
#                     print f
#                     print f_wcet
#                     print "num_flows = " + str(len(application_flows))                    
#                     sys.exit("Error - calculating f_wcet - None")                
#                 ## debug ##
                
                f_key = self._get_flow_key(f)
                self.runtime_app_info.setFlow_analytical_wcet(f_key, f_wcet)    # stored for later use                     
                
                percentage_of_f_wcet = float(f_wcet*(float(SimParams.WCRT_SCHEDULABILITY_TEST_PERCENTAGE)/100.0))
                if percentage_of_f_wcet > f.get_period():
                    self.unschedulable_flows.append(f)
    
    
    
    # Shi and Burns basic tests for tasks and flows, treating everything independently       
    def performAnalysis_ShiAndBurns_FullEval_withMMCDataRDWR(self, check_tasks=True, check_flows=True):
        # before performing analysis, reset lists
        self.unschedulable_flows = []
        self.unschedulable_tasks = []
        
        application_tasks = self.runtime_app_info.getTasks()
        application_flows = self.runtime_app_info.getFlows()
        
        #print len(application_tasks)
        #print len(application_flows)
        
#         print "+++++++++++++"
#         print "all flows"
#         for each_f in application_flows:
#             print each_f.getFlowHashCode() + ", src_c=" + str(each_f.get_source()) + ", dst_c=" + str(each_f.get_destination())  + "+".join([r.__repr__() for r in each_f.get_route()]) + ", " + str(each_f.get_priority())  + ", " + \
#                         str(each_f.get_payload_metadata()['wf_id']) + ", " + str(each_f.get_payload_metadata()['vid_strm_id']) + ", " + str(each_f.get_payload_metadata()['gop_ix'])
#         print "+++++++++++++"
        
#         print "*********************"
#         print "all tasks"
#         for each_t in application_tasks:
#             print each_t.getTaskWFSTRMId() + ", core=" + str(each_t.get_processingCore()) + ", pr=" + str(each_t.get_priority())                        
#         print "*********************"
        
        
        
        if(check_tasks == True):
            # check tasks
            for t_ix, t in enumerate(application_tasks):
                if(t.get_frameIXinGOP() not in [-1,-2]):                 
                    t_wcet = t.getResponseTime(t.getInterferenceSet(application_tasks))
                    t_wcet_withdeps = t.getResponseTime(t.getInterferenceSet_withPrCnst(application_tasks))
                    
                    #print "t_wcet_withdeps: " + str(t_wcet_withdeps)
                    
                    # we use the modified task wcrt analysis
                    self.runtime_app_info.setTask_analytical_wcet(t.get_id(), t_wcet_withdeps)   # stored for later use                    
                     
                    percentage_of_t_wcet = float(t_wcet*(float(SimParams.WCRT_SCHEDULABILITY_TEST_PERCENTAGE)/100.0))            
                    if percentage_of_t_wcet > t.get_end_to_end_deadline():
                        self.unschedulable_tasks.append(t)
                else:
                    
                    self.runtime_app_info.setTask_analytical_wcet(t.get_id(), 0.0)                    
                    
#         print "finished - tasks"
#         print ""
#         print ""
        ## set release jitter for flows
        for f_ix, f in enumerate(application_flows):
            # set release jitter again
            f_source_t = f.get_respectiveSrcTask()                
            if(f_source_t != None):                
                #rj = f_source_t.getResponseTime(f_source_t.getInterferenceSet_withPrCnst(self.runtime_app_info.getTasks()))            
                rj = self.runtime_app_info.getTask_analytical_wcet(f_source_t.get_id())     # we use the modified task wcrt analysis               
                f.set_releaseJitter(rj)                    
            else:
                rj=0.0
                f.set_releaseJitter(rj)
                
            # if this is a MMC flow
            if (f.get_type()==FlowType.FLOWTYPE_MMCTONODE_DATATRANSFER_RD):
                f.set_releaseJitter(0.0)
                f.set_payload_metadata('r_jitter',0.0)
            elif(f.get_type()==FlowType.FLOWTYPE_MMCTONODE_DATATRANSFER_WR):
                rj = self.runtime_app_info.getTask_analytical_wcet(f.get_payload_metadata()['src_task'].get_id())                
                f.set_releaseJitter(rj)
                f.set_payload_metadata('r_jitter',rj)
        
        
        
        
        #print "----------------"
        #print "calculating flow wcrt"
        
        ## calculate flows w.c response time
        if(check_flows == True):            
            # check flows
            for f_ix, f in enumerate(application_flows):

#                 ## debug ##                
#                 if(f.get_respectiveSrcTask().get_unique_gop_id() == 15):
#                     print f
#                 ## debug ##
                    
                                        
                timeout = datetime.utcnow() + timedelta(seconds = SimParams.WCRT_FLOW_CALC_TIMEOUT/float(len(application_flows)))            
                f_wcet = f.getWorstCaseLatency(application_flows, timeout, recur_depth=0)
                #print "f_wcet : " + str(f_ix) + " / " + str(len(application_flows)) + ": " + str(f_wcet)
                #sys.exit("done 1 flow")
#                 ## debug ##
#                 if(f_wcet == None):
#                     print f
#                     print "num_flows = " + str(len(application_flows))                    
#                     sys.exit("Error - calculating f_wcet - None")                
#                 
#                 if(f.get_id() == 180):
#                     print f
#                     print f_wcet
#                     print "num_flows = " + str(len(application_flows))                    
#                     sys.exit("Error - calculating f_wcet - None")                
#                 ## debug ##
                
                f_key = self._get_flow_key(f)
                self.runtime_app_info.setFlow_analytical_wcet(f_key, f_wcet)    # stored for later use                     
                
                percentage_of_f_wcet = float(f_wcet*(float(SimParams.WCRT_SCHEDULABILITY_TEST_PERCENTAGE)/100.0))
                if percentage_of_f_wcet > f.get_period():
                    self.unschedulable_flows.append(f)
                    
                
                ## debug ##    
#                 print "flow= ;" + f.getFlowHashCode() + ";" + "+".join([r.__repr__() for r in f.get_route()]) + ";" + \
#                                 str(len(f.getDirectInterferenceSet_withPrCnst(application_flows))) + ";" + \
#                                 str(len(f.getIndirectInterferenceSet_withPrCnst(application_flows))) + ";" + \
#                                 str(f.getBasicLatency())  + ";" + str(f_wcet)
                        
                    
        #print "finished - flows"
        #print "----------------"
    
    
    
    # is critical path cost less than the end-to-end deadline
    # NB: need to obtain the wcet results of tasks and flows before calling this  
    def performAnalysis_criticalPath(self, peform_wcet_analysis=True):
        
        if(peform_wcet_analysis == False):
            self.performAnalysis_ShiAndBurns()        
        
        unschedulable_critical_paths = []
        
        # find the streams currently active
        for each_stream in self.runtime_app_info.getStreams():
            
            print "---"
            print "wfid:" + str(each_stream.get_wfid())
            print "strmid:" + str(each_stream.get_stream_id())
            print "---"
            
            # get all paths for this stream
            paths = self.runtime_app_info.getTask(0, each_stream.get_wfid(), each_stream.get_stream_id()).getCriticalPaths()            
            p_results = {}
            
            for p_ix, each_p in enumerate(paths):  # list of tasks
                total_path_cost = 0.0
                for ix, t_ix in enumerate(each_p):   # frame index in gop
                    
                    if(ix < len(each_p)-1):    # task has an outward flow
                        T_src = self.runtime_app_info.getTask(each_p[ix], each_stream.get_wfid(), each_stream.get_stream_id())
                        T_dst = self.runtime_app_info.getTask(each_p[ix+1], each_stream.get_wfid(), each_stream.get_stream_id())                    
                        T_src_wcet = T_src.get_analytical_wcet()                        
                        f = self._getFlow_t2t(T_src.get_id(), each_p[ix+1], self.runtime_app_info.getFlows(), srct_ix=each_p[ix], dstt_ix=each_p[ix+1])
                        if(f!=None):                            
                            #total_path_cost = total_path_cost + T_src_wcet + f.get_analytical_wcet()
                            total_path_cost = total_path_cost + f.get_analytical_wcet() # flow_wcrt already has the task_wcrt as jitter !!
                        else: # this is when the parent node_id == child node_id
                            total_path_cost = total_path_cost + T_src_wcet
                            
                    else:   # task does not have an outward flow
                        T_src = self.runtime_app_info.getTask(each_p[ix], each_stream.get_wfid(), each_stream.get_stream_id())
                        T_src_wcet = T_src.get_analytical_wcet()
                        total_path_cost = total_path_cost + T_src_wcet
                        
                p_results[p_ix] = {
                                   'path' : each_p,
                                   'total_path_cost' :  total_path_cost
                                   }           
                    
            # find longest path
            cp = max(data['total_path_cost'] for data in p_results.values())
            cp_key = [k for k in p_results if p_results[k]['total_path_cost'] == cp]
            cp_key = cp_key[0]
                        
            # save result
            stream_key = str(each_stream.get_wfid()) + "_" + str(each_stream.get_stream_id())  # hash
            self.runtime_app_info.setStream_critical_path_wcet(stream_key, cp)
            
            print "performAnalysis_criticalPath : cp : " + str(cp)
            print "performAnalysis_criticalPath : stream_key : " + str(stream_key)
            
            # if longest path is larger than end-2-end deadline, then job is not schedulable
            percentage_of_cp_wcc = float(cp*(float(SimParams.WCRT_SCHEDULABILITY_TEST_PERCENTAGE)/100.0))
            
            if(percentage_of_cp_wcc > each_stream.get_end2end_deadline()):
                unschedulable_critical_paths.append([each_stream, each_p, cp])                 
                return False           
                
        return True
    
    
    
    
    
    # is critical path cost less than the end-to-end deadline
    # NB: need to obtain the wcet results of tasks and flows before calling this  
    def performAnalysis_criticalPath_evaluateAllStreams(self, peform_wcet_analysis=True):
        
        if(peform_wcet_analysis == False):
            self.performAnalysis_ShiAndBurns()        
        
        unschedulable_critical_paths = []
        
        # find the streams currently active
        for each_stream in self.runtime_app_info.getStreams():
            
            # get all paths for this stream
            paths = self.runtime_app_info.getTask(0, each_stream.get_wfid(), each_stream.get_stream_id()).getCriticalPaths()            
            p_results = {}
            
            for p_ix, each_p in enumerate(paths):  # list of tasks
                total_path_cost = 0.0
                for ix, t_ix in enumerate(each_p):   # frame index in gop
                    
                    if(ix < len(each_p)-1):    # task has an outward flow
                        T_src = self.runtime_app_info.getTask(each_p[ix], each_stream.get_wfid(), each_stream.get_stream_id())
                        T_dst = self.runtime_app_info.getTask(each_p[ix+1], each_stream.get_wfid(), each_stream.get_stream_id())                    
                        T_src_wcet = T_src.get_analytical_wcet()                        
                        f = self._getFlow_t2t(T_src.get_id(), each_p[ix+1], self.runtime_app_info.getFlows(), srct_ix=each_p[ix], dstt_ix=each_p[ix+1])
                        if(f!=None):
                            #total_path_cost = total_path_cost + T_src_wcet + f.get_analytical_wcet()
                            total_path_cost = total_path_cost + f.get_analytical_wcet() # flow_wcrt already has the task_wcrt as jitter !!
                        else: # this is when the parent node_id == child node_id
                            total_path_cost = total_path_cost + T_src_wcet
                            
                    else:   # task does not have an outward flow
                        T_src = self.runtime_app_info.getTask(each_p[ix], each_stream.get_wfid(), each_stream.get_stream_id())
                        T_src_wcet = T_src.get_analytical_wcet()
                        total_path_cost = total_path_cost + T_src_wcet
                        
                p_results[p_ix] = {
                                   'path' : each_p,
                                   'total_path_cost' :  total_path_cost
                                   }           
                    
            # find longest path
            cp = max(data['total_path_cost'] for data in p_results.values())
            cp_key = [k for k in p_results if p_results[k]['total_path_cost'] == cp]
            cp_key = cp_key[0]
                        
            # save result
            stream_key = str(each_stream.get_wfid()) + "_" + str(each_stream.get_stream_id())  # hash
            self.runtime_app_info.setStream_critical_path_wcet(stream_key, cp)
            
            # if longest path is larger than end-2-end deadline, then job is not schedulable
            percentage_of_cp_wcc = float(cp*(float(SimParams.WCRT_SCHEDULABILITY_TEST_PERCENTAGE)/100.0))
            
            if(percentage_of_cp_wcc > each_stream.get_end2end_deadline()):
                unschedulable_critical_paths.append([each_stream, each_p, cp])                 
                
        if(len(unschedulable_critical_paths)>0):
            return False
        else:   
            return True
    
    
    
    
    
    # is critical path cost less than the end-to-end deadline
    # NB: need to obtain the wcet results of tasks and flows before calling this  
    # NB: we take into account MMC data read/write communication flows
    def performAnalysis_criticalPath_evaluateAllStreams_withMMCDataRDWR(self, peform_wcet_analysis=True):
        
        if(peform_wcet_analysis == False):
            self.performAnalysis_ShiAndBurns_FullEval_withMMCDataRDWR()        
        
        unschedulable_critical_paths = []
        
        # find the streams currently active
        for each_stream in self.runtime_app_info.getStreams():
            
            # get all paths for this stream
            paths = self.runtime_app_info.getTask(0, each_stream.get_wfid(), each_stream.get_stream_id()).getCriticalPaths_withMMCDataRDWR()            
            p_results = {}
            
            for p_ix, each_p in enumerate(paths):  # list of tasks
                total_path_cost = 0.0
                for ix, t_ix in enumerate(each_p):   # frame index in gop
                    
                    if(ix < len(each_p)-1):    # task has an outward flow
                        T_src = self.runtime_app_info.getTask(each_p[ix], each_stream.get_wfid(), each_stream.get_stream_id())
                        T_dst = self.runtime_app_info.getTask(each_p[ix+1], each_stream.get_wfid(), each_stream.get_stream_id())                    
                        T_src_wcet = T_src.get_analytical_wcet()                        
                        f = self._getFlow_t2t(T_src.get_id(), each_p[ix+1], self.runtime_app_info.getFlows(), srct_ix=each_p[ix], dstt_ix=each_p[ix+1],
                                              wf_id=each_stream.get_wfid(), strm_id=each_stream.get_stream_id())
                        if(f!=None):
                            #total_path_cost = total_path_cost + T_src_wcet + f.get_analytical_wcet()
                            total_path_cost = total_path_cost + f.get_analytical_wcet() # flow_wcrt already has the task_wcrt as jitter !!
                            #self._debug_report(each_p[ix], T_src_wcet, p_ix, -1,-1);
                            #self._debug_report(100, f.get_analytical_wcet(), p_ix, each_p[ix], each_p[ix+1]);
                        else: # this is when the parent node_id == child node_id
                            total_path_cost = total_path_cost + T_src_wcet
                            #self._debug_report(each_p[ix], T_src_wcet, p_ix, -1, -1);
                            
                    else:   # task does not have an outward flow
                        #pprint.pprint(self.runtime_app_info.tasks)
                        T_src = self.runtime_app_info.getTask(each_p[ix], each_stream.get_wfid(), each_stream.get_stream_id())
                        T_src_wcet = T_src.get_analytical_wcet()
                        total_path_cost = total_path_cost + T_src_wcet
                        #self._debug_report(each_p[ix], T_src_wcet, p_ix, -1, -1);
                        
                p_results[p_ix] = {
                                   'path' : each_p,
                                   'total_path_cost' :  total_path_cost
                                   }           
                    
            # find longest path
            cp = max(data['total_path_cost'] for data in p_results.values())
            all_cp_key = [k for k in p_results if p_results[k]['total_path_cost'] == cp]
            cp_key = all_cp_key[0]
                        
            # save result
            stream_key = str(each_stream.get_wfid()) + "_" + str(each_stream.get_stream_id())  # hash
            self.runtime_app_info.setStream_critical_path_wcet(stream_key, cp)
            
            # if longest path is larger than end-2-end deadline, then job is not schedulable
            percentage_of_cp_wcc = float(cp*(float(SimParams.WCRT_SCHEDULABILITY_TEST_PERCENTAGE)/100.0))
            
            if(percentage_of_cp_wcc > each_stream.get_end2end_deadline()):
                unschedulable_critical_paths.append([each_stream, each_p, cp])
                
            
            # report
            print "Stream : " + stream_key + ", WCRT = " + str(cp) + ", pix=" + ":".join([str(x) for x in all_cp_key])
            
                             
                
        if(len(unschedulable_critical_paths)>0):
            return False
        else:   
            return True
    
    
    def _debug_report(self, tix, val, pix, srcix, dstix):
        if (pix == 7):            
            if (tix != 100):
                print "tix=" + str(tix) + ", " + str(val)
            else:
                print "tix=" + str(tix) + ", " + str(val) + ", srcix=" + str(srcix) + ", dstix="+ str(dstix)
            
        
    
    
    # is critical path cost less than the end-to-end deadline
    # NB: need to obtain the wcet results of tasks and flows before calling this  
    def performAnalysis_criticalPath_tasksOnly(self, peform_wcet_analysis=True):
        
        if(peform_wcet_analysis == False):
            self.performAnalysis_ShiAndBurns()        
        
        unschedulable_critical_paths = []
        
        # find the streams currently active
        for each_stream in self.runtime_app_info.getStreams():
            
            # get critical paths for this stream
            paths = self.runtime_app_info.getTask(0, each_stream.get_wfid(), each_stream.get_stream_id()).getCriticalPaths()            
            p_results = {}
            
            for p_ix, each_p in enumerate(paths):  # list of tasks
                total_path_cost = 0.0
                for ix, t_ix in enumerate(each_p):   # frame index in gop
                    
                    T_src = self.runtime_app_info.getTask(each_p[ix], each_stream.get_wfid(), each_stream.get_stream_id())
                    T_src_wcet = T_src.get_analytical_wcet()                        
                    total_path_cost = total_path_cost + T_src_wcet
                        
                p_results[p_ix] = {
                                   'path' : each_p,
                                   'total_path_cost' :  total_path_cost
                                   }           
                    
            # find longest path
            cp = max(data['total_path_cost'] for data in p_results.values())
            cp_key = [k for k in p_results if p_results[k]['total_path_cost'] == cp]
            cp_key = cp_key[0]
            
            # save result
            stream_key = str(each_stream.get_wfid()) + "_" + str(each_stream.get_stream_id())  # hash
            self.runtime_app_info.setStream_critical_path_wcet(stream_key, cp)
            
            # if longest path is larger than end-2-end deadline, then job is not schedulable
            percentage_of_cp_wcc = float(cp*(float(SimParams.WCRT_SCHEDULABILITY_TEST_PERCENTAGE)/100.0))
            
            if(percentage_of_cp_wcc > each_stream.get_end2end_deadline()):
                unschedulable_critical_paths.append([each_stream, each_p, cp])                 
                return False           
                
        return True
    
    
    
    
    # is critical path cost less than the end-to-end deadline
    # NB: need to obtain the wcet results of tasks and flows before calling this  
    def performAnalysis_WCRT_TasksWithDeps(self, peform_wcet_analysis=True):
        
        if(peform_wcet_analysis == False):
            self.performAnalysis_ShiAndBurns()        
        
        # find the streams currently active
        for each_stream in self.runtime_app_info.getStreams():
            # get all tasks for specified stream
            all_tasks = self.runtime_app_info.getStreamSpecificTasks(each_stream.get_wfid(), each_stream.get_stream_id())
            wcrt_per_task = {}
            
            for ix,each_task in enumerate(all_tasks):
                
                # get parents of this task
                parents_ix = each_task.get_parents()
                if(len(parents_ix)>0):
                    
                    wcrt_based_on_parent = []                    
                    for each_parent_ix in parents_ix:
                        parent_task = self.runtime_app_info.getTask(each_parent_ix, each_stream.get_wfid(), each_stream.get_stream_id())
                        f = self._getFlow_t2t(parent_task.get_id(), each_task.get_frameIXinGOP(), self.runtime_app_info.getFlows())
                        
                        if(f!=None):                        
                            wcrt_per_parent = wcrt_per_task[each_parent_ix] + f.get_analytical_wcet() + each_task.get_analytical_wcet()
                            #wcrt_per_parent = f.get_analytical_wcet() + each_task.get_analytical_wcet()
                            # add to out list
                            wcrt_based_on_parent.append(wcrt_per_parent)
                        else:
                            #wcrt_per_parent = wcrt_per_task[each_parent_ix] + f.get_analytical_wcet() + each_task.get_analytical_wcet()
                            wcrt_per_parent = wcrt_per_task[each_parent_ix] + each_task.get_analytical_wcet()
                            # add to out list
                            wcrt_based_on_parent.append(wcrt_per_parent)                            
                        
                    # therefore the wcrt_with_dep for this task is the max (i.e. worst-case) of the above list of wcrt_based_on_parents 
                    task_wcrt_with_deps =  max(wcrt_based_on_parent)                  
                    wcrt_per_task[each_task.get_frameIXinGOP()]= task_wcrt_with_deps
                    self.runtime_app_info.setTask_analytical_wcet_with_dep(each_task.get_id(), task_wcrt_with_deps)   # stored for later use 
                    
                else:
                    # probably an i-frame        
                    task_wcrt_with_deps =  each_task.get_analytical_wcet()         
                    wcrt_per_task[each_task.get_frameIXinGOP()]= task_wcrt_with_deps
                    self.runtime_app_info.setTask_analytical_wcet_with_dep(each_task.get_id(), task_wcrt_with_deps)   # stored for later use 
                    
      
    
    
    
    def performAnalysis_Utilisation(self):
        
        application_tasks = self.runtime_app_info.getTasks()
        application_flows = self.runtime_app_info.getFlows()
        
        total_utilisation = {  "NodeUtil" : {},
                               "LinkUtil" : {},                                  
                            }        
        
        # initialise utilisation results to zero
        for each_node in self.RMInstance.node_network.get_Nodes():
            total_utilisation['NodeUtil'][each_node.get_id()] = 0.0                                              
            
        for each_link in self.RMInstance.interconnect.getLinks():
            total_utilisation['LinkUtil'][each_link.get_id()] = 0.0 
        
        # calculate utilisation for the nodes        
        for each_task in application_tasks:
            node_id = each_task.get_processingCore()
            
            if(node_id != None):
                task_util = each_task.getUtilization()
                
                # add to node util
                total_utilisation['NodeUtil'][node_id] += task_util
                
        # calculate utilisation for the links
        for each_flows in application_flows:
            links = each_flows.get_route()
            flow_util = each_flows.getUtilisation()
            for each_link in links:
                total_utilisation['LinkUtil'][each_link.get_id()] += flow_util                
                
        return total_utilisation
                                             
                
                
    def outputReport_Utilisation(self):
        
        output = "<systemUtil>"
        
        total_sys_util = self.performAnalysis_Utilisation()
        
        # node util
        output += "<nodes>"
        for each_node_id, each_node_util  in total_sys_util['NodeUtil'].iteritems():            
            output += "<node id='" + str(each_node_id) + "' total_util='" + str(each_node_util) + "'"
            output += " />"
        output += "</nodes>"
        
        # link util
        output += "<links>"
        for each_link_id, each_link_util  in total_sys_util['LinkUtil'].iteritems():            
            output += "<link id='" + str(each_link_id) + "' total_util='" + str(each_link_util) + "'"
            output += " />"
        output += "</links>"
        
        output += "</systemUtil>"
    
        return output
        
    @staticmethod
    def cleanOutputReports(dirPath):            
        fileList = os.listdir(dirPath)
        for fileName in fileList:
            os.remove(dirPath+"/"+fileName)
    
    
    
    ###################################
    # For debug/reporting purposes
    ###################################
   
    # output schedulability test to log file
    def outputReport_ShiAndBurns(self, fname):    
        
        Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'outputReport::, : Enter', DebugCat.DEBUG_CAT_SCHEDANALYSIS)
        
        # output the flows and tasks properties
        application_streams = self.runtime_app_info.getStreams()
        application_tasks = self.runtime_app_info.getTasks()
        application_flows = self.runtime_app_info.getFlows()
                
        file = open(fname, "w")        
        file.write("<SchedulabilityReport>")  
        
        ##############################
        ## basic STREAM info
        ##############################
        file.write("<AppStreams>")
        for s_ix, s in enumerate(application_streams):
            
            sched_report_entry = "<Stream"
            sched_report_entry += s.getSchedulability_toString()            
            sched_report_entry += " />"            
            file.write(sched_report_entry)
            
        file.write("</AppStreams>")    
        
        ##############################
        ## TASK schedulability results
        ##############################
        file.write("<AppTasks>")
        
        Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'outputReport::, : Task analysis', DebugCat.DEBUG_CAT_SCHEDANALYSIS)
                
        for t_ix, t in enumerate(application_tasks):
            t_prop = t.getSchedulability_toString()            
            t_wcet = t.getResponseTime(t.getInterferenceSet_withPrCnst(application_tasks))
            
            self.runtime_app_info.setTask_analytical_wcet(t.get_id(), t_wcet)
            
            if t_wcet > t.get_end_to_end_deadline():  sched_result = False
            else:  sched_result = True
            
            sched_report_entry = "<Task"
            sched_report_entry += t_prop
            sched_report_entry += " wcet='" + str(t_wcet) + "' sch_r='" + str(sched_result)+ "'"
            sched_report_entry += " />"            
            file.write(sched_report_entry)
        
        file.write("</AppTasks>")        
            
        ##############################
        ## FLOWS schedulability results
        ##############################   
        file.write("<AppFlows>")
        
        Debug.PPrint("%f"%self.env.now + "," + self.label + "," +'outputReport::, : Flow analysis', DebugCat.DEBUG_CAT_SCHEDANALYSIS)
                
        for f_ix, f in enumerate(application_flows):            
            
            # set release jitter 
            f_prop = f.getSchedulability_toString()            
            f_BL = f.getBasicLatency()
            f_nDISet = len(f.getDirectInterferenceSet(application_flows))
            f_nIISet = len(f.getIndirectInterferenceSet(application_flows))
            f_nDISet_wPC = len(f.getDirectInterferenceSet_withPrCnst(application_flows))
            f_nIISet_wPC = len(f.getIndirectInterferenceSet_withPrCnst(application_flows))
            timeout = datetime.utcnow() + timedelta(seconds = SimParams.WCRT_FLOW_CALC_TIMEOUT/float(len(application_flows)))
            f_wcet = f.getWorstCaseLatency(application_flows, timeout)
            
            f_key = self._get_flow_key(f)
            self.runtime_app_info.setFlow_analytical_wcet(f_key, f_wcet)                         
            
            if f_wcet > f.get_period():  sched_result = False
            else:  sched_result = True
            
            sched_report_entry = "<Flow"
            sched_report_entry += f_prop
            sched_report_entry += " bl='" + str(f_BL) + "' nDI='" + str(f_nDISet) + "' nII='" + str(f_nIISet) + "' nDI_wPC='" + str(f_nDISet_wPC) + "' nII_wPC='" + str(f_nIISet_wPC) + "' wcet='" + str(f_wcet)+ "'"
            sched_report_entry += " sch_r='" + str(sched_result)+ "'"
            sched_report_entry += " />"            
            file.write(sched_report_entry)
        
        file.write("</AppFlows>")
        
        ##############################
        ## critical path analysis
        ##############################         
        sched_report_entry = self.outputReport_criticalPathAnalysis()
        file.write(sched_report_entry)       
        
        ##############################
        ## system utilisation
        ##############################  
               
        sys_util_entry = self.outputReport_Utilisation()
        file.write(sys_util_entry)  
        
        file.write("</SchedulabilityReport>")
        
        
        
    def outputReport_criticalPathAnalysis(self):
        
        sched_report_entry = "<CriticalPathAnalysis>"
        
        # find the streams currently active
        for each_stream in self.runtime_app_info.getStreams():
            
            # get critical paths for this stream
            paths = self.runtime_app_info.getTask(0, each_stream.get_wfid(), each_stream.get_stream_id()).getCriticalPaths()
            
            p_results = {}
            
            for p_ix, each_p in enumerate(paths):  # list of tasks                
                #pprint.pprint(each_p)
                total_path_cost = 0.0
                for ix, t_ix in enumerate(each_p):   # frame index in gop
                    
                    if(ix < len(each_p)-1):    # task has an outward flow
                        T_src = self.runtime_app_info.getTask(each_p[ix], each_stream.get_wfid(), each_stream.get_stream_id())
                        T_dst = self.runtime_app_info.getTask(each_p[ix+1], each_stream.get_wfid(), each_stream.get_stream_id())                    
                        T_src_wcet = T_src.get_analytical_wcet()                        
                        f = self._getFlow_t2t(T_src.get_id(), each_p[ix+1], self.runtime_app_info.getFlows(), srct_ix=each_p[ix], dstt_ix=each_p[ix+1])
                        if(f!=None): 
                            total_path_cost = total_path_cost + T_src_wcet + f.get_analytical_wcet()
                        else:
                            total_path_cost = total_path_cost + T_src_wcet
                            
                    else:   # task does not have an outward flow
                        T_src = self.runtime_app_info.getTask(each_p[ix], each_stream.get_wfid(), each_stream.get_stream_id())
                        T_src_wcet = T_src.get_analytical_wcet()
                        total_path_cost = total_path_cost + T_src_wcet
                        
                p_results[p_ix] = {
                                   'path' : each_p,
                                   'total_path_cost' :  total_path_cost
                                   }            
                    
            # find longest path
            cp = max(data['total_path_cost'] for data in p_results.values())
            cp_key = [k for k in p_results if p_results[k]['total_path_cost'] == cp]
            cp_key = cp_key[0]
            
            sched_report_entry += "<CP wfid='" + str(each_stream.get_wfid()) + "' stid='" + str(each_stream.get_stream_id()) + "' cp='" + str(p_results[cp_key]['path']) + "' cp_cost='" + str(cp) + "' />"
        
        sched_report_entry += "</CriticalPathAnalysis>"
        
        return sched_report_entry
    
    def _getFlow_t2t(self, src_task_id, dst_task_ix, all_flows, srct_ix=None, dstt_ix=None, wf_id=None, strm_id=None):
        
        for each_f in all_flows:
            if(each_f.get_type() == FlowType.FLOWTYPE_DATA):
                if (each_f.get_respectiveSrcTaskId() == src_task_id) and (dst_task_ix in each_f.get_respectiveDstTaskId()) :
                    return each_f
            elif(each_f.get_type() in [FlowType.FLOWTYPE_MMCTONODE_DATATRANSFER_RD, FlowType.FLOWTYPE_MMCTONODE_DATATRANSFER_WR]) :
                each_f_srct_ix = each_f.get_payload_metadata()['src_t_ix']
                each_f_dstt_ix = each_f.get_payload_metadata()['dst_t_ix']
                each_f_wf_id = each_f.get_payload_metadata()['wf_id']
                each_f_vid_strm_id = each_f.get_payload_metadata()['vid_strm_id']
                if ((each_f_srct_ix == srct_ix) and 
                    (each_f_dstt_ix == dstt_ix) and
                    (wf_id == each_f_wf_id) and 
                    (strm_id == each_f_vid_strm_id)):
                    #print "found MMC flow"
                    return each_f
                
        
        return None
                 
            
    def _get_flow_key(self,f):
        if(f.get_type()== FlowType.FLOWTYPE_DATA):
            f_key = str(f.get_respectiveSrcTaskId()) + "_" + str(f.get_respectiveDstTaskId())
        elif(f.get_type()== FlowType.FLOWTYPE_PSALGOSIGNALLING):
            f_key = "PSALGO_" + str(f.get_id())
        elif(f.get_type()== FlowType.FLOWTYPE_REMAPPING_NOTIFY_DISPATCHER):
            f_key = "REMAP_NOTIFY_" + str(f.get_id())
        elif(f.get_type()== FlowType.FLOWTYPE_MMCTONODE_DATATRANSFER_RD):
            #f_key = "MMCTONODE_RD" + str(f.get_respectiveDstTaskId())
            f_key = "MMCTONODE_RD_" + str(f.get_payload_metadata()['wf_id']) + "_" + \
                                        str(f.get_payload_metadata()['vid_strm_id']) + "_" + \
                                        str(f.get_payload_metadata()['gop_ix'])
            
        elif(f.get_type()== FlowType.FLOWTYPE_MMCTONODE_DATATRANSFER_WR):
            #f_key = "MMCTONODE_WR" + str(f.get_respectiveSrcTaskId())
            f_key = "MMCTONODE_WR" + str(f.get_payload_metadata()['wf_id']) + "_" + \
                                        str(f.get_payload_metadata()['vid_strm_id']) + "_" + \
                                        str(f.get_payload_metadata()['gop_ix'])
        return f_key
                    
    ## moga related : azizi GA related helpers ##
    def _getMOGARelatedTaskName(self, task):        
        name = task.getTaskWFSTRMId() + ", " + \
                str(task.get_worstCaseComputationCost()) + ", " + \
                str(task.get_priority()) + ", " + \
                str(len(task.getInterferenceSet_withPrCnst(self.runtime_app_info.getTasks()))) + ", " + \
                ':'.join([t.getTaskWFSTRMId() for t in task.getInterferenceSet_withPrCnst(self.runtime_app_info.getTasks())]) 
        return name
    
    
    
    
    def _getMOGARelatedFlowName(self, flow):  
        
        flow_type = flow.get_type()
        src_task = flow.get_respectiveSrcTask()
        dst_task_ixs = flow.get_respectiveDstTaskIx()
        
        if (flow_type == FlowType.FLOWTYPE_DATA):             
            src_task_name = "t_" + str(src_task.get_wfid()) + "_" + str(src_task.get_video_stream_id()) + "_" + str(src_task.get_frameIXinGOP())
            dst_task_ixs = "tix_" +  ':'.join(str(x) for x in dst_task_ixs)            
            name = src_task_name + "-->" + dst_task_ixs
            
        elif (flow_type == FlowType.FLOWTYPE_MMCTONODE_DATATRANSFER_RD):
            wf_id = flow.get_payload_metadata()['wf_id']
            strm_id = flow.get_payload_metadata()['vid_strm_id']
            gop_ix = flow.get_payload_metadata()['gop_ix']
                        
            dst_task_name = "t_" + str(wf_id) + "_" + str(strm_id) + "_" + str(gop_ix)
            name = "MMC" + "-->" + dst_task_name
            
        elif (flow_type == FlowType.FLOWTYPE_MMCTONODE_DATATRANSFER_WR):
            wf_id = flow.get_payload_metadata()['wf_id']
            strm_id = flow.get_payload_metadata()['vid_strm_id']
            gop_ix = flow.get_payload_metadata()['gop_ix']
                        
            src_task_name = "t_" + str(wf_id) + "_" + str(strm_id) + "_" + str(gop_ix)            
            name = src_task_name + "-->" + "MMC"
                                    
        else:
            sys.exit("Error: _getMOGARelatedFlowName:: unknown type = " + str(flow_type))
        
        return name
        
        
        
        
        
    ## getters/setters    
    
    
