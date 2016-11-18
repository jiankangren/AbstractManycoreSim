import pprint
import sys
import math, random
import numpy as np
import copy
import csv
from collections import OrderedDict

## local imports
from SimParams import SimParams
from libApplicationModel.MPEG2FrameTask import MPEG2FrameTask



class AziziMOGATestbenchGenerator:
    def __init__(self, workflows, MMC_enable=True):
        self.workflows = copy.copy(workflows)
        self.organised_tasks = {}
        self.all_tasks = []
        self.sorted_all_tasks = []
        self.task_noninterferers = {}
        self.MMC_enable = MMC_enable
        self.task_pri_float_to_int_mappings = {}
        self.flw_pri_offset = None
    
    def get_organised_tasks(self):
        return self.organised_tasks 
    def set_flow_pri_offset(self, fpo):
        self.flw_pri_offset = fpo
    
    # this turns the workflow
    def constructWfLevelTasks(self):        
        for each_wf_id, each_wf_data in self.workflows.iteritems():
            if(each_wf_id not in self.organised_tasks):                    
                    self.organised_tasks[each_wf_id]={}
                    
            for each_task in each_wf_data:                
                # wf/vid level properties
                wf_id = each_task.get_wfid()
                vid_id = each_task.get_video_stream_id()
                gop_fix = each_task.get_frameIXinGOP()
                wf_gopid = each_task.get_parentGopId()
                
                if(wf_gopid == 0): # only enter if first gop of the video stream                   
                    if(vid_id not in self.organised_tasks[wf_id]):
                        self.organised_tasks[wf_id][vid_id]={}
                        self.organised_tasks[wf_id][vid_id][gop_fix] = each_task
                    else:                    
                        self.organised_tasks[wf_id][vid_id][gop_fix] = each_task
        
        # populate all tasks
        self.all_tasks = self._getAllTasksFromOrganisedWFlist()
        
        # sorted all tasks
        self.sorted_all_tasks = sorted(self.all_tasks, key=lambda x: x.get_scheduledDispatchTime(), reverse=False)
        
        # convert the task priorities from float to int
        #self._convertTaskPrioritiesToIntegers()
        
        # populate the non interferers
        self.populateNonInterferers()
        
        #pprint.pprint(self.sorted_all_tasks)
        #sys.exit()
        
        return self.organised_tasks
        
        
    def populateNonInterferers(self):
        
        for each_wf_id, each_wf_data in self.organised_tasks.iteritems():  
            for each_vid_id, each_vid_data in each_wf_data.iteritems():
                for each_task_gop_ix, each_task in each_vid_data.iteritems():
                    
                    nonint_subset = self._getNonInterferenceSet_DueToPrCnst(each_task, self.all_tasks)                    
                    self.task_noninterferers[each_task.get_id()] = nonint_subset
                    
        
    def outputTestBench(self, org_tasks, fname):
        print "outputTestBench :: Enter"
        testbench_text = ""
        gop_tasks = []
        flow_id_counter = 0
        total_task_count = 0
        
        #print self.sorted_all_tasks
        #sys.exit()
        
        for each_task in self.sorted_all_tasks:
            total_task_count +=1            
            
            #print each_task
            
            ## get flow entries for gop tasks
            if len(each_task.get_children_frames()) > 0:
                # get flows per task
                flows_per_task,temp_flw_id_counter  = self._getFlowsEntryPerTask(each_task, org_tasks, flow_id_counter)
                flow_id_counter = temp_flw_id_counter
                temp_entries = self._getTBEntry_string(flows_per_task)
                
                testbench_text += temp_entries
                
            gop_tasks.append(each_task)           
            
            ## messy mmc flow entry capture, because we did it badly in the runtimemanager class
            ## generate read/write mmc flows for each gop-task
            if(len(gop_tasks) > 0):
                if(len(gop_tasks) == len(gop_tasks[0].get_gopstructure())):
                    (mmc_flow_entries, temp_flw_id_counter, temp_task_count) = self._getMMCRelatedFlowsEntiesPerGoP(gop_tasks, flow_id_counter)
                    flow_id_counter = temp_flw_id_counter
                    #total_task_count += temp_task_count
                    mmc_flow_entries_text = self._getTBEntry_string(mmc_flow_entries)
                    
                    #mmc_flow_entries_text = "NULL \n"
                    #print "---"
                    #pprint.pprint(gop_tasks)
                    #print "---"
                    
                    testbench_text += mmc_flow_entries_text
                    gop_tasks = []
                    #gop_tasks.append(each_task)
                    
        
        
        #sys.exit()
                
        # open file and output testbench
        f = open(fname,'w')
        f.write(testbench_text)
        f.close()
        
        ## report
        #print "Total flows: " + str(flow_id_counter)
        #print "Total tasks (without MMC): " + str(total_task_count) 
        
        
        
        return testbench_text
            
    
    

    
    
    ###############################
    #    Helper functions
    ###############################
    def _getAllTasksFromOrganisedWFlist(self):
        all_tasks = []
        for each_wf_id, each_wf_data in self.organised_tasks.iteritems():  
            for each_vid_id, each_vid_data in each_wf_data.iteritems():
                for each_task_gop_ix, each_task in each_vid_data.iteritems():
                    all_tasks.append(each_task)
        
        return all_tasks
    
    
    def _getNonInterferenceSet_DueToPrCnst(self, target_task, allTasks):    
        nonint_subset = []    
        for each_task in allTasks:
            if(target_task.get_wfid() == each_task.get_wfid() and
               target_task.get_video_stream_id() == each_task.get_video_stream_id()): # if from same video stream
                    if(each_task.get_frameIXinGOP() not in target_task.get_possible_interfering_frame()):  # at a gop level, due to parallelism/precedence, some frames may not interfere
                        nonint_subset.append(each_task)
                    
        return nonint_subset
    
    # conditions for a flow originating from Task Ti:
    # - Ti has children : {Ti_child} 
    # - child is on a different node than Ti's processing node
    def _getFlowsEntryPerTask(self, source_task, organised_tasks, flw_id_counter):
        all_flows_per_task = []    
        Ti = source_task
        wf_id = Ti.get_wfid()
        strm_id = Ti.get_video_stream_id()
        source_task_non_interferers = self.task_noninterferers[source_task.get_id()] # non interferers        
        child_frame_ixs = Ti.get_children_frames()  #ids
        
        Ti_child_tasks = []
        # get children tasks
        for each_child_gopix in child_frame_ixs:
            Ti_c = organised_tasks[wf_id][strm_id][each_child_gopix]
            Ti_child_tasks.append(Ti_c)    
        
        # populate
        for each_Ti_c in Ti_child_tasks:   
            tb_entry = OrderedDict()
            
            dst_task = each_Ti_c
            dst_task_non_interferers = self.task_noninterferers[dst_task.get_id()] # non interferers             
            
            # general info
            tb_entry['flw_id_counter'] = flw_id_counter
            tb_entry['src_t_label'] = self._getTaskName(source_task)            
            tb_entry['dst_t_label'] = self._getTaskName(dst_task)
            tb_entry['unique_gop_id'] = source_task.get_unique_gop_id()
            
            # information about the source_task
            tb_entry['src_t_wccc'] = source_task.get_worstCaseComputationCost()
            tb_entry['src_t_period'] = source_task.get_period()
            tb_entry['src_t_pri'] = self._getTaskPriority_LowResFirst_Integer(source_task)
            tb_entry['src_t_nonints'] = ",".join([self._getTaskName(t) for t in source_task_non_interferers])
            
            # information about the dst_task
            tb_entry['dst_t_wccc'] = dst_task.get_worstCaseComputationCost()
            tb_entry['dst_t_period'] = dst_task.get_period()
            tb_entry['dst_t_pri'] = self._getTaskPriority_LowResFirst_Integer(dst_task)            
            tb_entry['dst_t_nonints'] = ",".join([self._getTaskName(t) for t in dst_task_non_interferers])
                        
            # information about the message flow
            tb_entry['bits'] = 0
            tb_entry['flits'] = 0            
            tb_entry['payload'] = int(source_task.get_completedTaskSize())
            tb_entry['period'] = source_task.get_period()
            tb_entry['flow_pri'] = self._getFlowPriority_LowResFirst(tb_entry['src_t_pri'], flw_id_counter, len(Ti_child_tasks))            
            
            
            #print "--"
            #print tb_entry['src_t_label'], tb_entry['dst_t_label']
            #print "tb_entry['src_t_pri']" , tb_entry['src_t_pri']            
            #print flw_id_counter
            #print "tb_entry['flow_pri']" , tb_entry['flow_pri'] 
            #print "--"
            
            all_flows_per_task.append(tb_entry)            
            flw_id_counter +=1
        
        return (all_flows_per_task, flw_id_counter)
    
    
    
    def _getMMCRelatedFlowsEntiesPerGoP(self, gop_tasks, flw_id_counter):
        
        #print "_getMMCRelatedFlowsEntiesPerGoP: enter"
        
        all_flw_entries = []
        task_count = 0
        
        # MMC - RD (loading a task data)
        for each_gop_task in gop_tasks:
            
            #print each_gop_task
            
            tb_entry = OrderedDict()
            dst_task_non_interferers = self.task_noninterferers[each_gop_task.get_id()] # non interferers 
            
            # general info
            tb_entry['flw_id_counter'] = flw_id_counter
            tb_entry['src_t_label'] = "MMC"            
            tb_entry['dst_t_label'] = self._getTaskName(each_gop_task)
            tb_entry['unique_gop_id'] = each_gop_task.get_unique_gop_id()
            
            # information about the source_task (MMC)
            tb_entry['src_t_wccc'] = 0.0            
            tb_entry['src_t_period'] = each_gop_task.get_period()
            tb_entry['src_t_pri'] = 0
            tb_entry['src_t_nonints'] = "NONE"
            
            # information about the dst_task (Ti)
            tb_entry['dst_t_wccc'] = each_gop_task.get_worstCaseComputationCost()
            tb_entry['dst_t_period'] = each_gop_task.get_period()
            tb_entry['dst_t_pri'] = self._getTaskPriority_LowResFirst_Integer(each_gop_task)            
            tb_entry['dst_t_nonints'] = ",".join([self._getTaskName(t) for t in dst_task_non_interferers])
            
            # information about the message flow  
            tb_entry['bits'] = 0
            tb_entry['flits'] = 0                      
            tb_entry['payload'] = int(each_gop_task.get_mpeg_tasksize())
            tb_entry['period'] = each_gop_task.get_period()            
            #tb_entry['flow_pri'] = SimParams.MMC_DATAREAD_FLOW_PRIORITY + float(flw_id_counter)
            tb_entry['flow_pri'] = SimParams.MMC_DATAREAD_FLOW_PRIORITY # we add the flwidcounter in the javaapp
            
            all_flw_entries.append(tb_entry)            
            flw_id_counter +=1
        
        
        
        # MMC - WR (writing back to MMC)
        for each_gop_task in gop_tasks:
            tb_entry = OrderedDict()
            src_task_non_interferers = self.task_noninterferers[each_gop_task.get_id()] # non interferers
            each_gop_task_pri = self._getTaskPriority_LowResFirst_Integer(each_gop_task)
                        
            # general info
            tb_entry['flw_id_counter'] = flw_id_counter
            tb_entry['src_t_label'] = self._getTaskName(each_gop_task)            
            tb_entry['dst_t_label'] = "MMC"
            tb_entry['unique_gop_id'] = each_gop_task.get_unique_gop_id()
            
            # information about the source_task (Ti)
            tb_entry['src_t_wccc'] = each_gop_task.get_worstCaseComputationCost()                        
            tb_entry['src_t_period'] = each_gop_task.get_period()
            tb_entry['src_t_pri'] = each_gop_task_pri
            tb_entry['src_t_nonints'] = ",".join([self._getTaskName(t) for t in src_task_non_interferers])
            
            # information about the dst_task (Ti)
            tb_entry['dst_t_wccc'] = 0.0
            tb_entry['dst_t_period'] = each_gop_task.get_period()
            tb_entry['dst_t_pri'] = 0            
            tb_entry['dst_t_nonints'] = "NONE"
           
            # information about the message flow    
            tb_entry['bits'] = 0
            tb_entry['flits'] = 0
            tb_entry['payload'] = int(each_gop_task.get_completedTaskSize())
            tb_entry['period'] = each_gop_task.get_period()
            #tb_entry['flow_pri'] = float(each_gop_task_pri) + ( float(self.flw_pri_offset) + 100.0) + float(flw_id_counter)
            tb_entry['flow_pri'] = float(each_gop_task_pri) + ( float(self.flw_pri_offset) + 100.0) # we add the flwidcounter in the javaapp
           
            all_flw_entries.append(tb_entry)            
            flw_id_counter +=1
            task_count +=1
        
        return (all_flw_entries, flw_id_counter, task_count)
    
    
    def _getTBEntry_string(self, flows):
        entries = ""    
        for each_flow in flows:
            entries += " ".join(str(v) for v in each_flow.values()) + "\n"
            
        return entries
    
    
    def _getTaskName(self, Ti):
        tname = "t_" + str(Ti.get_wfid()) + "_" + str(Ti.get_video_stream_id()) + "_" + str(Ti.get_frameIXinGOP())
        return tname
    
    def _getTaskPriority_LowResFirst(self, Ti):        
        OFFSET = 10                 
        Ti_scheduled_dispatch_time = Ti.get_scheduledDispatchTime()
        Ti_gop_ix = Ti.get_frameIXinGOP()
        target_vid_resolution = Ti.get_frame_h() * Ti.get_frame_w() 
        
        # stratergy : pri = (MAX_TASK_PRI - (w*h) + frame_ix_pri + (arr_time * offset))        
        priority = SimParams.MAX_TASK_PRIORITY - ((target_vid_resolution - MPEG2FrameTask.calc_FramePriorityInsideGOP(Ti_gop_ix)) +
                                                                (Ti_scheduled_dispatch_time * OFFSET))
        return priority
    
    
    def _getTaskPriority_LowResFirst_Integer(self, Ti):
        orig_pri = self._getTaskPriority_LowResFirst(Ti)
        #integer_pri = self.task_pri_float_to_int_mappings[orig_pri]
        return orig_pri

    
    
    
    def _getFlowPriority_LowResFirst(self, src_t_pri, flw_id, num_flows_from_same_src_t):
        #priority = src_t_pri + 100 + flw_id + num_flows_from_same_src_t
        
        #priority = src_t_pri + ( float(self.flw_pri_offset) + 100.0) + float(flw_id)
        priority = src_t_pri + ( float(self.flw_pri_offset) + 100.0) # we add the flwidcounter in the javaapp
        
        #print priority
        
        return priority
    
    
    # conversion of task priorities from float to int (to suit aziz codebase)
    def _convertTaskPrioritiesToIntegers(self):
        
        float_pri_dict = {}
        
        # store original priorities
        for each_task in self.sorted_all_tasks:
            orig_pri = self._getTaskPriority_LowResFirst(each_task) 
            if  orig_pri not in float_pri_dict:
                float_pri_dict[orig_pri] = None;
        
        # sorted priorities
        sorted_orig_pri_list = sorted(float_pri_dict.keys(), reverse=True)
        
        # not map integer priorities
        i = len(sorted_orig_pri_list) + 1
        for each_pri in sorted_orig_pri_list:
            float_pri_dict[each_pri] = i
            i=i-1
            
        self.task_pri_float_to_int_mappings = float_pri_dict
        
            
            
    
    
    
    