from pprint import pprint
import simpy
import csv
import sys
import math
import os
import json
from collections import OrderedDict

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import scipy.stats
from matplotlib.colors import ListedColormap, NoNorm
from matplotlib import mlab
from itertools import cycle # for automatic markers

import matplotlib.cm as cm
from matplotlib.font_manager import FontProperties

# local imports
from libMappingAndScheduling.Decentralised.PSAlgorithmViewer import PSAlgorithmViewer
from SimParams import SimParams
from libProcessingElement.Node import NodeStatus
from libApplicationModel.Task import TaskModel



class SimDataMonitor:
    def __init__(self, env, node_network, interconnect, input_buffers, output_buffer, 
                 task_dispatcher, workflows, resource_manager):
        self.env = env
        self.node_network = node_network
        self.interconnect = interconnect
        self.input_buffers = input_buffers
        self.output_buffer = output_buffer
        self.task_dispatcher = task_dispatcher
        self.workflows = workflows
        self.resource_manager = resource_manager
        self.label = "SimDataMonitor"
        self.fig_counter = 0
        
        self.ObjInputBuffTasks = []
        # objects to keep track of sim actors
        for each_ibuff_id in xrange(SimParams.NUM_INPUTBUFFERS):
            self.ObjInputBuffTasks.append([])
            
        self.ObjOutputBuffTasks = []
        self.ObjNodesTasks = []
        self.TaskDispatcherBlocked = [] # boolean at every tick
        self.SystemInstantaneousUtilisation = {
                                               'node_throughput'       : [],
                                               'interconnect'       : [],
                                               'node_idle_time'    : [], 
                                               'node_idle_periods' : None                                              
                                               }
        
        # info about simulation end
        self.last_scheduled_dispatchtime = None
        self.first_scheduled_dispatchtime = None
        self.simulation_end_time = None
        
        
        
        # Start the run process everytime an instance is created.        
        self.process_instance = self.env.process(self.run())
        
    
    
    
    ########################################################################
    ## Used to track platform level characteristics every sampling interval
    ########################################################################   
    def run(self):        
        
        # temp counter storage
        prev_completed_tasks = [0 for x in range(SimParams.NUM_NODES)]
        prev_completed_flows = [0 for x in range(len(self.interconnect.getLinks()))]
        prev_nodeidletime = [0 for x in range(SimParams.NUM_NODES)]
        prev_total_link_idletime = 0.0
        
        
        #print(self.label + ' : run starting at %d' % self.env.now)        
        while True:
        
            #############################
            ## tracking INPUT BUFFER
            #############################
            
            if(SimParams.TRACK_INPUTBUFF == True):
                for each_ibuff_id in xrange(SimParams.NUM_INPUTBUFFERS):
                    
                    item = {
                            'time' : self.env.now,
                            'len' : self.input_buffers[each_ibuff_id].status_getCurrentItems()[0],
                            'level' : self.input_buffers[each_ibuff_id].status_getCurrentItems()[1],
                            'cum_lateness' : self.input_buffers[each_ibuff_id].get_cumulativeTaskLateness()
                            }                
                    self.ObjInputBuffTasks[each_ibuff_id].append(item)
            
            #############################
            ## tracking OUTPUT BUFFER
            #############################
            if(SimParams.TRACK_OUTPUTBUFF == True):
                item = {
                        'time' : self.env.now,
                        'record' : self.output_buffer.status_getCurrentItems()
                        }            
                self.ObjOutputBuffTasks.append(item)
            
            #############################
            ## tracking NODE TASK QUEUS
            #############################
            if(SimParams.TRACK_NODESTASKQ == True):
                nodes = []
                for each_node in self.node_network.get_Nodes():
                    node = {
                            'tq_len'   : each_node.get_NumTasksInTQ(),   # num of tasks in task queue
                            'tq_remcc' : each_node.get_TotalRemainingTaskExecutionTime(),    # remaining computation cost in task queue
                            'cum_lateness' : each_node.get_cumulativeTaskLateness() # cumulative task lateness
                            }
                    nodes.append(node)
                
                item = {
                        'time' : self.env.now,
                        'record' : nodes
                        }
                self.ObjNodesTasks.append(item)
            
            #################################################
            ## tracking THROUGHPUT - Nodes
            #################################################
            if(SimParams.TRACK_NODE_THROUGHPUT == True):
                num_idle_cores = []
                num_busy_cores = []
                core_specific_tc = []
                tq = 0
                tc = 0
                for ix,each_node in enumerate(self.node_network.get_Nodes()):
                    
                    prev = prev_completed_tasks[ix]
                    now = len(self.node_network.nodeArray[ix].completedTasks)                    
                    delta = now-prev     # difference               
                    prev_completed_tasks[ix] = now  # update
                    core_specific_tc.append(delta)
                    
                    tc += delta
                
                entry = {
                         'time' : self.env.now,
                         "csp_tc" : core_specific_tc,
                         "sum_tc" :   tc
                         }                
                self.SystemInstantaneousUtilisation['node_throughput'].append(entry)
            
            
            #################################################
            ## tracking IDLETIME - Nodes
            #################################################
            if(SimParams.TRACK_NODE_IDLETIME == True):
                node_idletime = []
                idle_time_counter = []
                #idle_time_periods = {}               
                for ix,each_node in enumerate(self.node_network.get_Nodes()):
                    
                    prev = prev_nodeidletime[ix]
                    now = self.node_network.nodeArray[ix].track_idle_time                    
                    delta = now-prev     # difference               
                    prev_nodeidletime[ix] = now  # update
                    node_idletime.append(delta)
                    idle_time_counter.append(now)
                    #self.node_network.nodeArray[ix].track_idle_time = 0.0 # reset node's idletime tracker
                    #idle_time_periods[ix] = self.node_network.nodeArray[ix].track_idle_periods
                
                entry = {
                         'time' : self.env.now,
                         "nsit" : node_idletime,    # delta value (all nodes)
                         "it_c" : idle_time_counter # exact counter value (all nodes)                       
                         }                
                self.SystemInstantaneousUtilisation['node_idle_time'].append(entry)
            
                
            ######################################################
            ## tracking NOCLINKUTIL - NoC Links
            ######################################################
            if(SimParams.TRACK_NOCLINKUTIL == True):
                link_specific_fc =  []
                
                total_link_idle_time = 0.0
                 
                for ix,each_link in enumerate(self.interconnect.getLinks()):
                    # completed flows
                    prev = prev_completed_flows[ix]
                    now = len(each_link.completed_flows)    
                    delta = now-prev     # difference  
                    prev_completed_flows[ix] = now  # update   
                    link_specific_fc.append(delta)
                    
                    # idle time
                    total_link_idle_time += each_link.getAccumulatedIdleTime()                    
                
                prev = prev_total_link_idletime
                now = total_link_idle_time
                delta = now-prev
                prev_total_link_idletime = total_link_idle_time
                      
                    
                entry = {
                         'time' : self.env.now,
                         "lsp_fc" : link_specific_fc,
                         "sampled_link_idletime" : delta,
                         "total_link_idletime" :  total_link_idle_time                        
                         }                
                self.SystemInstantaneousUtilisation['interconnect'].append(entry)
          
          
            # go to sleep according to sample rate
            yield self.env.timeout(SimParams.SIM_MONITOR_SAMPLE_RATE)
            

##########################################
## Getter/setters
##########################################



          
##########################################
## Plotting functions 
##########################################           
    def plot_InputBuffer(self):
        
        time = []
        data = []
        data_2 = []
        
        #pprint(self.ObjInputBuffTasks)
        lines = ["-*","-x","-o","-+"]
        linecycler = cycle(lines)
        
        self.fig_counter += 1
        fig = plt.figure(self.fig_counter)
        fig.canvas.set_window_title('InputBuffers')
        
        ibuff_id = 0
        for each_ibuff in self.ObjInputBuffTasks:
            time = []
            data = []
            data_2 = []
            
            for each_item in each_ibuff:
            
                time.append(each_item['time_now'])
                data.append(each_item['record'])
                data_2.append(each_item['record_2'])
                
            lbl = "IBuff-"+str(ibuff_id)
            
            plt.plot(time, data, next(linecycler), label =lbl, linewidth=2.0 )
            plt.hold(True)
            ibuff_id +=1
                
        plt.grid(True)
        leg = plt.legend()
        leg.draggable()
        
        
    def plot_OutputBuffer(self):
        
        time = []
        data = []
        
        for each_item in self.ObjOutputBuffTasks:
            time.append(each_item['time_now'])
            data.append(each_item['record'])
       
        self.fig_counter += 1
        fig = plt.figure(self.fig_counter)
        fig.canvas.set_window_title('OutputBuffer')
        plt.plot(time, data)
        plt.grid(True)    
        
    def plot_TasksMissedDeadline_perCore(self):
        
        labels = []
        core_specific_misseddeadlines = []
        percentage = 0.0
        
        print "plot_TasksMissedDeadline_perCore"
        print "---------------------------------"
        
        for each_node in self.node_network.get_Nodes():
            if((len(each_node.completedTasks) >0)):
                percentage = float(float(len(each_node.tasks_that_missed_deadline)/float(len(each_node.completedTasks))) * 100.00)
                core_specific_misseddeadlines.append(percentage)
                labels.append(each_node.label)
                
                # print out value
                print each_node.label + " = " + str(percentage) + "(" + str(len(each_node.tasks_that_missed_deadline)) + "/" + str(len(each_node.completedTasks)) + ")"
            else:
                print "Error ! - no completed tasks !!"
                return   
            
        if(len(core_specific_misseddeadlines) > 0):        
            self.fig_counter += 1
            fig = plt.figure(self.fig_counter)
            fig.canvas.set_window_title('TasksMissedDeadline_perCore')
            
            xlocations = np.array(range(len(core_specific_misseddeadlines)))+0.5
            width = 0.5
            plt.bar(xlocations, core_specific_misseddeadlines, width=width)       
            plt.xticks(xlocations+ width/2, labels)
            plt.xlim(0, xlocations[-1]+width*2)
            plt.grid(True)
        
            
    ## analyse the tasks in the output buff 
    ## in terms of their missed deadlines
    def plot_TasksMissedDeadline_perTask(self):
        
        labels = []
        task_specific_misseddeadline = []
        
        for each_task in self.output_buffer.get_BuffContents():
            if(each_task.get_missedDeadlineFlag() == True):
                missed_alpha = each_task.get_taskCompleteTime() - (each_task.get_releaseTime() + each_task.get_deadline())                
                task_specific_misseddeadline.append(missed_alpha)                
                labels.append(str(each_task.get_id()))
        
        print " "
        print "plot_TasksMissedDeadline_perTask"
        print "---------------------------------"
        if(len(task_specific_misseddeadline) > 0):
            
            print "Worst-case GOP deadline miss delay : " + str(max(task_specific_misseddeadline))
            print "Average GOP deadline miss delay : " + str(sum(task_specific_misseddeadline)/float(len(task_specific_misseddeadline)))
            
                
            if(len(task_specific_misseddeadline) > 0):        
                self.fig_counter += 1
                fig = plt.figure(self.fig_counter)
                fig.canvas.set_window_title('TasksMissedDeadline_perTask')
                
                xlocations = np.array(range(len(task_specific_misseddeadline)))+0.5
                width = 0.5
                plt.bar(xlocations, task_specific_misseddeadline, width=width)       
                plt.xticks(xlocations+ width/2, labels)
                plt.tick_params(axis='x', which='major', labelsize=10)
                plt.xlim(0, xlocations[-1]+width*2)
                
                # plot mean (horizontal-line)
                plt.hold(True)
                plt.axhline(y=sum(task_specific_misseddeadline)/float(len(task_specific_misseddeadline)), color='r')       
                
                plt.grid(True)
        else:
            print "None of the tasks missed their deadline"
    
    
    def plot_NodeTaskQs(self):
        
        time = []
        data = []
        lines = ["-","--","-.",":"]
        linecycler = cycle(lines)
    
        self.fig_counter += 1
        fig = plt.figure(self.fig_counter)
        fig.canvas.set_window_title('NodeTaskQueues')
        
        for each_node_id in xrange(SimParams.NUM_NODES):        
            
            time = []
            data = []
            for each_item in self.ObjNodesTasks:
                time.append(each_item['time_now'])
                data.append(each_item['record'][each_node_id]['tasks_in_q'])                
                lbl = each_item['record'][each_node_id]['type']+"-"+str(each_item['record'][each_node_id]['id'])
            
           
            plt.plot(time, data, next(linecycler), label =lbl, linewidth=2.5 )
            plt.hold(True)
            
        plt.grid(True)
        leg = plt.legend()
        leg.draggable()
        
    def show_CPU_utilisation(self):
        ## numeric stats ##        
        # completed tasks (total)
        print " "
        print "CPU Utilisation"
        print "---------------"
        total_system_utilisation = 0.0
        for each_node in self.node_network.get_Nodes():
            print each_node.label + " : " +  str(each_node.get_TotalCompletedTasks()) + \
                    ", total_cc = " + str(each_node.get_TotalTaskExecutionTime()) + \
                    ", total_sim_runtime = " + str(SimParams.SIM_RUNTIME) + \
                    ", utilisation (based on total_cc) = " + str((each_node.get_TotalTaskExecutionTime() / SimParams.SIM_RUNTIME) * 100) + "%"
        
            total_system_utilisation = total_system_utilisation + ((each_node.get_TotalTaskExecutionTime() / SimParams.SIM_RUNTIME) * 100)
        
        print " "
        print "Total System Utilisation = %f" % (total_system_utilisation/float(SimParams.NUM_NODES))
    
    
    
    
    
    #######################################################
    # REPORT OUT RUNTIME STATISTICS
    #######################################################
    
    def report_RMTaskMappingTable(self, dump_to_file=None):
        print "SimDataMonitor :: dumping report_RMTaskMappingTable"
        if(dump_to_file != None):
            tm_tbl = self.resource_manager.task_mapping_table
            fname = dump_to_file                        
            self._write_formatted_file(fname, tm_tbl, "json")
        else:
            sys.exit("Error: report_RMTaskMappingTable : fname null")
            
    def report_RMVolatileTaskMappingTable(self, dump_to_file=None):
        print "SimDataMonitor :: dumping report_RMVolatileTaskMappingTable"
        if(dump_to_file != None):
            tm_tbl = self.resource_manager.volatile_task_mapping_table
            fname = dump_to_file                        
            self._write_formatted_file(fname, tm_tbl, "json")
        else:
            sys.exit("Error: report_RMTaskMappingTable : fname null")
    
    def report_HEVC_NumCTU(self,dump_to_file=None):        
        print "SimDataMonitor :: dumping report_HEVC_NumCTU"
        
        # calculate total ctus completed
        completed_ctus = {}
        all_tasks_completed_ctus = {}
        for each_node in self.node_network.get_Nodes():
            completed_ctus[each_node.get_id()] = np.sum([len(v) for k,v in each_node.track_completed_ctus.iteritems()])
            all_tasks_completed_ctus.update(each_node.track_completed_ctus)
        
        # calculate total ctus generated in workload
        total_gen_ctus = 0
        for each_wf_id, each_wf_tasks in self.workflows.workflows.iteritems():
            for each_task in each_wf_tasks:
                total_gen_ctus += each_task.calc_num_CTU_via_block_partitions()
        
        # calculate ctus released to PE task queues by the RM
        num_ctus_released = np.sum(self.resource_manager.track_hevc_ctus_released.values())
        num_tiles_released = len(self.resource_manager.track_hevc_ctus_released.values())
        num_tiles_generated = self.resource_manager.total_number_of_tiles_generated
        
        # output the variance - generated vs. completed ctus
        tasks_with_ctus_missing = {}
        for each_task_id, num_ctus_per_task_released in self.resource_manager.track_hevc_ctus_released.iteritems():
            if num_ctus_per_task_released != len(all_tasks_completed_ctus[each_task_id]):
                tasks_with_ctus_missing[each_task_id] = {
                                                         'released' : int(num_ctus_per_task_released),
                                                         'completed' : len(all_tasks_completed_ctus[each_task_id]),
                                                         }
            
        print "-------"
        print "Total CTUs completed =", np.sum(completed_ctus.values())
        print "Total CTUs generated =", total_gen_ctus
        print "Total CTUs released to PEs =", num_ctus_released
        print "Total Tiles (released to PEs vs. generated)  =", num_tiles_released, num_tiles_generated
        print "-------"
        
        # write output
        if dump_to_file != None:
            if len(tasks_with_ctus_missing.keys()) >0:
                self._write_formatted_file(dump_to_file, tasks_with_ctus_missing, "json")
            
    
    def report_VerifyFlows_HEVCFrameLvl(self, dump_to_file=None):
        print "SimDataMonitor :: dumping report_VerifyFlows_HEVCFrameLvl"
        ## calc number of flows in workflows (original data)
        num_flows_theoretical = 0
        total_num_tasks = 0
        for each_wf_id, each_wf_tasks in self.workflows.workflows.iteritems():
            for each_task in each_wf_tasks:
                num_flows_theoretical += len(each_task.get_expected_data_to_children().keys())
                total_num_tasks+=1
                
        # add mmc->task, task->mmc (2 flows per task)
        num_flows_theoretical += total_num_tasks*2
        
        ## get total completed flows
        total_completed_flows_simulated = len(self.resource_manager.flow_table.track_flows_completed)
        
        total_flows_too_short = self.resource_manager.flow_table.track_num_flows_too_short
        
        # flows that were not sent due to same node mapping
        total_flows_not_sent = 0
        for each_node in self.node_network.get_Nodes():
            total_flows_not_sent+= len(each_node.track_flows_sent_to_own_depbuff)
                
        print "-----"
        print "num_flows_theoretical : ", num_flows_theoretical
        print "(1) - total_completed_flows_simulated : ", total_completed_flows_simulated
        print "(2) - total_flows_not_sent : ", total_flows_not_sent
        print "(1) + (2) = ", total_completed_flows_simulated+total_flows_not_sent
        
        print "proportion of total_flows_too_short : ", float(total_flows_too_short)/float(total_completed_flows_simulated+total_flows_not_sent) * 100
        print "-----"
        
        
    def report_VerifyFlows_HEVCTileLvl(self, dump_to_file=None):
        print "SimDataMonitor :: dumping report_VerifyFlows_HEVCTileLvl"
        
        (num_flows_theoretical, total_completed_flows_simulated,
                total_flows_not_sent, total_flows_too_short) = self._get_calc_theoretical_hevc_tile_flows()
                
        print "-----"
        print "num_flows_theoretical : ", num_flows_theoretical
        print "(1) - total_completed_flows_simulated : ", total_completed_flows_simulated
        print "(2) - total_flows_not_sent : ", total_flows_not_sent
        print "(1) + (2) = ", total_completed_flows_simulated+total_flows_not_sent
        print "proportion of total_flows_too_short : ", float(total_flows_too_short)/float(total_completed_flows_simulated+total_flows_not_sent) * 100
        print "-----"    
        
        
                
    def _get_calc_theoretical_hevc_tile_flows(self):
        ## calc number of flows in workflows (original data)
        num_flows_theoretical = 0
        total_num_tasks = 0
        for each_wf_id, each_wf_tasks in self.workflows.workflows.iteritems():
            for each_task in each_wf_tasks:
                n_tiles = each_task.getNumSubTasksTiles()
                num_children = len(each_task.get_expected_data_to_children().keys())                
                num_flows_after_tile_splitting = n_tiles * (num_children*n_tiles)
                num_flows_theoretical += num_flows_after_tile_splitting
                total_num_tasks+=n_tiles
                
        # add mmc->task, task->mmc (2 flows per task)
        num_flows_theoretical += total_num_tasks*2
        
        ## get total completed flows
        total_completed_flows_simulated = len(self.resource_manager.flow_table.track_flows_completed)
        total_flows_too_short = self.resource_manager.flow_table.track_num_flows_too_short
        
        # flows that were not sent due to same node mapping
        total_flows_not_sent = 0
        for each_node in self.node_network.get_Nodes():
            total_flows_not_sent+= len(each_node.track_flows_sent_to_own_depbuff)
        
        
        return (num_flows_theoretical, total_completed_flows_simulated,
                total_flows_not_sent, total_flows_too_short)
        
    
    
        
        
                    
    def report_InstUtilisation(self, dump_to_file= None):              
        if(dump_to_file != None):            
            print "SimDataMonitor :: dumping sysutil"
            
            # get node specific idle periods
            node_idle_periods = {}
            for each_node in self.node_network.get_Nodes():
                node_idle_periods[each_node.get_id()] = each_node.track_idle_periods
            
            
            self.SystemInstantaneousUtilisation['node_idle_periods'] = node_idle_periods
            
            # write full python object to file, as json     
            fname = dump_to_file                        
            self._write_formatted_file(fname, self.SystemInstantaneousUtilisation, "json")
        else:
            sys.exit("Error: report_InstUtilisation : fname null")
            
    
    
    
            
    def report_InstUtilisationShort(self, dump_to_file= None):              
        if(dump_to_file != None):
            
            print "SimDataMonitor :: dumping sysutil-short"
            # write full python object to file, as json     
            fname = dump_to_file
            
            short_result = {}
            for each_k, each_v in self.SystemInstantaneousUtilisation.iteritems():
                if(len(each_v)>0):
                    last_item = each_v[-1]
                    short_result[each_k] = last_item
            
            self._write_formatted_file(fname, short_result, "json")
        else:
            sys.exit("Error: report_InstUtilisationShort : fname null")
    
    
    def report_InputBuffer(self, dump_to_file=None):      
        if(dump_to_file != None):
            
            print "SimDataMonitor :: dumping inputbuffer"
            # write full python object to file, as json     
            fname = dump_to_file
                        
            self._write_formatted_file(fname, self.ObjInputBuffTasks, "json")
        else:
            sys.exit("Error: report_InputBuffer : fname null")
        
    
    def report_NodeTQs(self, dump_to_file=None):        
        if(dump_to_file != None):
            
            print "SimDataMonitor :: dumping nodeTQs"
            # write full python object to file, as json     
            fname = dump_to_file
                        
            self._write_formatted_file(fname, self.ObjNodesTasks, "json")
        else:
            sys.exit("Error: report_NodeTQs : fname null")
            
    
    def report_OutputBufferContents(self, dump_to_file=None):        
        if(dump_to_file != None):            
            print "SimDataMonitor :: dumping outputbuffer contents"
            # write full python object to file, as json     
            fname = dump_to_file            
            all_tasks_in_obuff = []
            for each_task in self.output_buffer.get_BuffContents():                
                entry = {
                         'id' : each_task.get_id(),
                         'type' : each_task.get_frameType(),                         
                         'pri' : each_task.get_priority(),
                         'estL' : each_task.get_estimatedLateness(),
                         'ugid' : each_task.get_unique_gop_id(),
                         'dt' : each_task.get_dispatchTime(),   # dispatched by TD
                         'st' : each_task.get_taskStartTime(),  # time task execution was started
                         'rt' : each_task.get_releaseTime(),     # time task was released to processing node by RM
                         'dct' : each_task.get_deps_allcomplete_time(),     # time task received all its completed deps
                         'et' : each_task.get_taskCompleteTime(),     # time task ended
                         'cc' : each_task.get_computationCost(),     # time computation cost (actual)
                         'pe' : each_task.get_processingCore()
                         }            
                all_tasks_in_obuff.append(entry)                        
            self._write_formatted_file(fname, all_tasks_in_obuff, "json")
        else:
            sys.exit("Error: report_OutputBufferContents : fname null")
    
    
    def report_OutputBufferContents_short(self, dump_to_file=None):        
        if(dump_to_file != None):            
            print "SimDataMonitor :: dumping report_OutputBufferContents_short"
            # write full python object to file, as json     
            fname = dump_to_file            
            all_tasks_in_obuff = []
            for each_task in self.output_buffer.get_BuffContents():                
                entry = {
                         't_props' : [each_task.get_id(), each_task.get_unique_gop_id(), each_task.get_frameType(), each_task.get_priority()],
                         'respT' : float(each_task.get_taskCompleteTime() - each_task.get_dispatchTime()),
                         'estL' : each_task.get_estimatedLateness(),
                         'cc' : each_task.get_computationCost(),     # time computation cost (actual)                         
                         }            
                all_tasks_in_obuff.append(entry)                        
            self._write_formatted_file(fname, all_tasks_in_obuff, "json")
        else:
            sys.exit("Error: report_OutputBufferContents_short : fname null")
    
    
    def report_RMTaskReleaseInfo(self, dump_to_file=None):        
        if(dump_to_file != None):            
            print "SimDataMonitor :: dumping RMTaskReleaseInfo"
            # write full python object to file, as json    
            fname = dump_to_file                        
            self._write_formatted_file(fname, self.resource_manager.track_taskrelease, "json")
        else:
            sys.exit("Error: report_RMTaskReleaseInfo : fname null")
    
    
    def report_MappingAndPriAssInfo(self, dump_to_file=None):        
        if(dump_to_file != None):            
            print "SimDataMonitor :: dumping MappingAndPriAssInfo"
            # write full python object to file, as json    
            fname = dump_to_file                        
            self._write_formatted_file(fname, self.resource_manager.track_mappingandpriass, "json")
        else:
            sys.exit("Error: report_MappingAndPriAssInfo : fname null")
    
    def report_FlowsCompleted(self, dump_to_file=None):        
        if(dump_to_file != None):            
            print "SimDataMonitor :: dumping FlowsCompleted"
            # write full python object to file, as json    
            fname = dump_to_file                        
            self._write_formatted_file(fname, self.resource_manager.flow_table.track_flows_completed, "json")
        else:
            sys.exit("Error: report_FlowsCompleted : fname null")
    
    # same as the above, but using lists instead of dict to save text space
    def report_FlowsCompleted_short(self, dump_to_file=None):
        if(dump_to_file != None):            
            print "SimDataMonitor :: dumping report_FlowsCompleted_short"
            # write full python object to file, as json    
            fname = dump_to_file            
            
            # theoretical - only for TILES
            if (SimParams.TASK_MODEL == TaskModel.TASK_MODEL_HEVC_TILE_LEVEL):
                (num_flows_theoretical, 
                 total_completed_flows_simulated,
                 total_flows_not_sent, 
                 total_flows_too_short) = self._get_calc_theoretical_hevc_tile_flows()
                 
                flows_not_sent_proportion = float(total_flows_not_sent)/float(num_flows_theoretical)
            else:
                #sys.exit("Error - report_FlowsCompleted_short : not tile task model")
                flows_not_sent_proportion = None
            
            
            data = {
                    'flows_completed' : [(f['bl'], f['l_var'], f['tp'], f['pl'], f['intfs'], f['r_len']) 
                                         for f in self.resource_manager.flow_table.track_flows_completed],
                    'flows_not_sent_proportion' : flows_not_sent_proportion
                    }
            
                                              
            self._write_formatted_file(fname, data, "json")
        else:
            sys.exit("Error: report_FlowsCompleted_short : fname null")
    
    
    def report_FlowsAdded(self, dump_to_file=None):        
        if(dump_to_file != None):            
            print "SimDataMonitor :: dumping report_FlowsAdded"
            # write full python object to file, as json    
            fname = dump_to_file                        
            self._write_formatted_file(fname, self.resource_manager.flow_table.track_flows_added, "json")
        else:
            sys.exit("Error: report_FlowsAdded : fname null")
            
    def report_NodeTaskExecTimeline(self, dump_to_file=None):        
        if(dump_to_file != None):            
            print "SimDataMonitor :: dumping NodeTaskExecTimeline"
            
            node_data = {}
            for each_node in self.node_network.get_Nodes():
                node_data[each_node.get_id()] = each_node.task_execution_timeline            
            
            # write full python object to file, as json    
            fname = dump_to_file                        
            self._write_formatted_file(fname, node_data, "json")
        else:
            sys.exit("Error: report_NodeTaskExecTimeline : fname null")
    
    
    def report_PSAlgoNodePSProps(self, dump_to_file=None):        
        if(dump_to_file != None):                        
            print "SimDataMonitor :: dumping PSAlgoNodePSProps"
            # write full python object to file, as json    
            fname = dump_to_file                        
            self._write_formatted_file(fname, self.resource_manager.PSAlgo.track_nodepsprops, "json")
        else:
            sys.exit("Error: report_PSAlgoNodePSProps : fname null")
            
    
    def report_PSRemappDebugInfo_1(self, dump_to_file=None):        
        if(dump_to_file != None):                        
            print "SimDataMonitor :: dumping report_PSRemappDebugInfo_1"
            # write full python object to file, as json    
            fname = dump_to_file 
            node_data = OrderedDict()
            for each_node in self.node_network.get_Nodes():
                node_data[each_node.get_id()] = each_node.taskremapping_decent_scheme_instance.track_nodetqinfo_at_remapping_instant
            
                                   
            self._write_formatted_file(fname, node_data, "json")
        else:
            sys.exit("Error: report_PSAlgoNodePSProps : fname null")
            
    
    
    def report_TaskRemappingInfo(self, dump_to_file=None):        
        if(dump_to_file != None):
            print "SimDataMonitor :: dumping report_TaskRemappingInfo"
            node_rmdata = {}
            for each_node in self.node_network.get_Nodes():
                node_rmdata[each_node.get_id()] = each_node.taskremapping_decent_scheme_instance.track_remaped_numtasks
            
            # write full python object to file, as json    
            fname = dump_to_file                        
            self._write_formatted_file(fname, node_rmdata, "json")
        else:
            sys.exit("Error: report_TaskRemappingInfo : fname null")
    
    
    def report_NodeCumSlack(self, dump_to_file=None):        
        if(dump_to_file != None):
            print "SimDataMonitor :: dumping report_NodeCumSlack"
            node_cumslack = {}
            for each_node in self.node_network.get_Nodes():
                node_cumslack[each_node.get_id()] = {
                                                     'cum_slack' : each_node.track_total_system_slack['current_cum_slack'],  
                                                     'norm_cum_slack' : each_node.track_total_system_slack['current_normalised_cum_slack'],
                                                     'decay_cycle_info' : each_node.psalgoprops.track_cycledecay
                                                     }
            # write full python object to file, as json    
            fname = dump_to_file                        
            self._write_formatted_file(fname, node_cumslack, "json")
        else:
            sys.exit("Error: report_NodeCumSlack : fname null")
        
    def report_NodeTQLatenessProperties(self, dump_to_file=None):        
        if(dump_to_file != None):
            print "SimDataMonitor :: dumping report_NodeCumSlack"
            node_cumslack = {}
            for each_node in self.node_network.get_Nodes():
                node_cumslack[each_node.get_id()] = {
                                                     'cum_slack' : each_node.track_total_system_slack['current_cum_slack'],  
                                                     'norm_cum_slack' : each_node.track_total_system_slack['current_normalised_cum_slack'],
                                                     'decay_cycle_info' : each_node.psalgoprops.track_cycledecay
                                                     }
            # write full python object to file, as json    
            fname = dump_to_file                        
            self._write_formatted_file(fname, node_cumslack, "json")
        else:
            sys.exit("Error: report_NodeTQLatenessProperties : fname null")
    
    
    def report_NodeImportedTasks(self, dump_to_file=None):        
        if(dump_to_file != None):
            print "SimDataMonitor :: dumping report_NodeImportedTasks"
            node_imp_tasks = {}
            for each_node in self.node_network.get_Nodes():
                node_imp_tasks[each_node.get_id()] = each_node.track_imported_tasks                                                     
            
            # write full python object to file, as json    
            fname = dump_to_file                        
            self._write_formatted_file(fname, node_imp_tasks, "json")
        else:
            sys.exit("Error: report_NodeImportedTasks : fname null")
            
    def report_NodeTasksCompleted(self, dump_to_file=None):
        if(dump_to_file != None):
            print "SimDataMonitor :: dumping report_NodeTasksCompleted"
            node_tasks_completed = {}
            for each_node in self.node_network.get_Nodes():
                node_tasks_completed[each_node.get_id()] = [[t.get_id(), t.get_unique_gop_id(), t.calc_FrameComputationTime()]
                                                            for t in each_node.completedTasks]
                                                            
            # write full python object to file, as json    
            fname = dump_to_file                        
            self._write_formatted_file(fname, node_tasks_completed, "json")
        else:
            sys.exit("Error: report_NodeTasksCompleted : fname null")
    
    
    def report_WCRT_TasksAndFlows_viaSchedAnalysis(self, dump_to_file=None):        
        if(dump_to_file != None):            
            print "SimDataMonitor :: dumping report_WCRT_TasksAndFlows_viaSchedAnalysis"
            # write full python object to file, as json    
            fname = dump_to_file                        
            self._write_formatted_file(fname, self.resource_manager.NoCSchedulabilityAnalyser.track_admission_tests, "json")
        else:
            sys.exit("Error: report_WCRT_TasksAndFlows_viaSchedAnalysis : fname null")
    
    
    def report_WCRT_TasksAndFlows_viaSchedAnalysis_short(self, dump_to_file=None):        
        if(dump_to_file != None):            
            print "SimDataMonitor :: dumping report_WCRT_TasksAndFlows_viaSchedAnalysis_short"
            # write full python object to file, as json    
            fname = dump_to_file
            if(len(self.resource_manager.NoCSchedulabilityAnalyser.track_admission_tests)>0):                        
                self._write_formatted_file(fname, self.resource_manager.NoCSchedulabilityAnalyser.track_admission_tests[-1], "json")
            else:
                self._write_formatted_file(fname, self.resource_manager.NoCSchedulabilityAnalyser.track_admission_tests, "json")
        else:
            sys.exit("Error: report_WCRT_TasksAndFlows_viaSchedAnalysis_short : fname null")
    
    
    def report_StreamUtil_vs_sched(self, dump_to_file=None):
        if(dump_to_file != None):
            print "SimDataMonitor :: dumping report_StreamUtil_vs_sched"
            sched_test_info = self.resource_manager.NoCSchedulabilityAnalyser.track_vsutil_vs_schedulability
            fname = dump_to_file       
            self._write_formatted_file(fname, sched_test_info, "json")
        else:
            sys.exit("Error: report_StreamUtil_vs_sched : fname null")
    
    
    def report_StreamUtil_vs_sched_short(self, dump_to_file=None):
        if(dump_to_file != None):
            print "SimDataMonitor :: dumping report_StreamUtil_vs_sched_short"
            if(len(self.resource_manager.NoCSchedulabilityAnalyser.track_vsutil_vs_schedulability)>0):
                sched_test_info = self.resource_manager.NoCSchedulabilityAnalyser.track_vsutil_vs_schedulability[-1]
            else:
                sched_test_info = self.resource_manager.NoCSchedulabilityAnalyser.track_vsutil_vs_schedulability
            fname = dump_to_file       
            self._write_formatted_file(fname, sched_test_info, "json")
        
        else:
            sys.exit("Error: report_StreamUtil_vs_sched_short : fname null")
    
    
    # profiling results of the task mappers
    def report_MappingExecOverhead(self, dump_to_file=None):
        if(dump_to_file != None):
            print "SimDataMonitor :: dumping report_MappingExecOverhead"
            fname = dump_to_file       
            self._write_formatted_file(fname, self.resource_manager.taskTileMapperAndPriAssignerCombo.track_execution_overhead, "json")        
        else:
            sys.exit("Error: report_MappingExecOverhead : fname null")
        
        
    # MMC port used for tasks
    def report_PremappedMMCPortID(self, dump_to_file=None):
        if(dump_to_file != None):
            print "SimDataMonitor :: dumping report_PremappedMMCPortID"
            fname = dump_to_file       
            self._write_formatted_file(fname, self.resource_manager.mmc.mmc_task_to_mmcnode_mapping, "json")        
        else:
            sys.exit("Error: report_PremappedMMCPortID : fname null")
    
    
    # MMC port used for tasks
    def report_JobCCRInfo(self, dump_to_file=None):
        if(dump_to_file != None):
            print "SimDataMonitor :: dumping report_JobCCRInfo"
            fname = dump_to_file       
            self._write_formatted_file(fname, self.resource_manager.taskTileMapperAndPriAssignerCombo.track_ccr_level, "json")        
        else:
            sys.exit("Error: report_JobCCRInfo : fname null")
    
    
    # get the link specific information
    def report_LinkUsageInfo(self, dump_to_file=None):
        if(dump_to_file != None):
            print "SimDataMonitor :: dumping report_LinkUsageInfo"
            link_report = self._build_link_info()
            fname = dump_to_file                   
            self._write_formatted_file(fname, link_report, "json")        
        else:
            sys.exit("Error: report_JobCCRInfo : fname null")
    
    
    ## for kaushik-pp-tile mapper debugging
    def report_PPTileMapperOptStage_Info(self, dump_to_file=None):
        if(dump_to_file != None):
            print "SimDataMonitor :: dumping report_MappingExecOverhead"
            fname = dump_to_file       
            self._write_formatted_file(fname, self.resource_manager.taskTileMapperAndPriAssignerCombo.pp_mapping_info, "json")        
        else:
            sys.exit("Error: report_PPTileMapperOptStage_Info : fname null")
    
    
    
    
    def plot_showall(self):
        plt.show()
        
                        
                    
##########################################
## Report output
##########################################                   
     
    def report_CompletedTaskAnalysis(self):   
        print " "
        print "Completed task analysis"
        print "======================="
        for each_node in self.node_network.get_Nodes():
            print each_node.label            
            print "--------------"
            for each_completed_task in each_node.completedTasks:
                print "Ti="+ str(each_completed_task.get_id()) + \
                    ", (=" + str(each_completed_task.get_type())+")" + \
                    ", stT=" + str(each_completed_task.get_taskStartTime()) + \
                    ", cmpT=" + str(each_completed_task.get_taskCompleteTime()) + \
                    ", relT=" + str(each_completed_task.get_releaseTime()) + \
                    ", cc=" + str(each_completed_task.get_computationCost()) + \
                    ", deadln=" + str(each_completed_task.get_deadline()) + \
                    ", missedDeadlineFlag=" + str(each_completed_task.get_missedDeadlineFlag())
            
            print " "
        
        
    def report_RM_FlowTable(self):        
        
        # output rm-dropped tasks table
        logfile=open('rm_tbl_flowtable.js', 'w')
        pprint(self.resource_manager.flow_table.flowEntries, logfile, width=128)
    
    
    def report_VideoStream_BasicStats(self, wf_results_summary, fname):
        print "SimDataMonitor :: dumping report_VideoStream_BasicStats"
        # original workflow data (at task generation)
        original_workflow = self.workflows.workflows_summary
        
        # track completeness/lateness
        vids_rejected = []
        vids_accepted_success = []
        vids_accepted_late = []        
        
        for each_wf_key, each_wf_val in wf_results_summary.iteritems():
            
                       
            for each_vid_key, each_vid_val in enumerate(each_wf_val): 
                
                if(wf_results_summary[each_wf_key][each_vid_val]['result'] == True):
                    vids_accepted_success.append(each_vid_val)
                else:
                    if(len(wf_results_summary[each_wf_key][each_vid_val]['gops_in_outbuff']) > 0):
                        vids_accepted_late.append(each_vid_val)
                    else:
                        vids_rejected.append(each_vid_val)
        
        
        # construct report
        video_stream_highlevel_stats = {
                                        "num_vids_rejected" : len(vids_rejected),
                                        "num_vids_accepted_success" : len(vids_accepted_success),
                                        "num_vids_accepted_late" : len(vids_accepted_late),
                                        "num_dropped_tasks" : self.resource_manager.totalDroppedTasks(),
                                        "sim_end_time" : self.simulation_end_time,
                                        "last_scheduled_dispatchtime" : self.last_scheduled_dispatchtime,
                                        "first_scheduled_dispatchtime" : self.first_scheduled_dispatchtime
                                        }
        
        
        logfile=open(fname, 'w')
        json_data = json.dumps(video_stream_highlevel_stats, indent=4)
        logfile.write(json_data)
          
               
        
        
        
    
    def report_DecodedWorkflows_Summary(self, timeline_fname = 'showTaskTimeLine.png', 
                                        wf_res_summary_fname = 'workflow_results_summary.js',
                                        gops_opbuff_summary_fname = 'gops_in_outputbuff_summary.js',
                                        gops_opbuff_summary_short_fname = None,
                                        rmtbl_dt_summary_fname = 'rm_tbl_droppedtasks.js',
                                        output_format="pretty", 
                                        task_model_type=TaskModel.TASK_MODEL_MHEG2_FRAME_LEVEL
                                        ):
        print " "
        print "show_DecodedWorkflows_Summary"
        print "================================"
        
        # construct GOP range
        frame_groups = {}
        for each_task in self.output_buffer.get_BuffContents():
            if each_task.get_unique_gop_id() not in frame_groups:                
                frame_groups[each_task.get_unique_gop_id()] = [each_task]            
            else:
                frame_groups[each_task.get_unique_gop_id()].append(each_task)
                
        
        ## print out results of each GOP ##
        gops_successfully_completed = []    # i.e : not late, and all frames decoded
        gops_late_but_fully_complete = []
        gops_ids_late_but_fully_complete = []
        gops_incomplete = 0
        total_gop_lateness = []
        
        gops_in_outputbuff_summary = {}
        
        for each_gop_id in frame_groups.keys():
            
            gops_in_outputbuff_summary[frame_groups[each_gop_id][0].get_unique_gop_id()] = {}            
            #print frame_groups[each_gop_id][0]
            
            for each_t in frame_groups[each_gop_id]:
                if(each_t.get_frameType() == "I"):
                    i_frame = each_t
                    break
            
            if (task_model_type == TaskModel.TASK_MODEL_HEVC_TILE_LEVEL):
                potential_num_tiles_per_frame = i_frame.getNumSubTasksTiles()
            else:
                potential_num_tiles_per_frame = 1
            
            
            vid_res = self.workflows.workflows_summary[i_frame.get_wfid()][i_frame.get_video_stream_id()]['resolution']
            
            gop_startend_dict = {
                             'gop_unique_id' : i_frame.get_unique_gop_id(),
                             'nframes' : 0,
                             'gop_struct' : i_frame.get_gopstructure(),
                             'tpri' : [],
                             'start_time' : i_frame.get_releaseTime(),
                             'stid' : i_frame.get_id(),
                             'stgid' : i_frame.get_frameIXinGOP(),
                             'end_time' : i_frame.get_taskCompleteTime(),
                             'mmcwr_et' : i_frame.get_taskMMCWRCompleteTime(),
                             'etid' : 0,
                             'etgid' : 0,
                             'dispatch_time' : i_frame.get_dispatchTime(), # assume all tasks have equal dispatch time
                             'tt_wrt_dt' : 0,
                             'tt_wrt_rt' : 0,
                             'e2ed' : 0,
                             'gop_execution_lateness' : 0,
                             'gop_mean_pri': 0.0,
                             'strm_res' : "%dx%d" % (vid_res[0], vid_res[1])                                                                                        
                             }
            task_priorities = []
            for each_task in frame_groups[each_gop_id]:
                
                # set start-time
                if(each_task.get_releaseTime() <  gop_startend_dict['start_time']):
                    gop_startend_dict['start_time'] = each_task.get_releaseTime()
                    gop_startend_dict['stid'] = each_task.get_id()                    
                    gop_startend_dict['stgid'] = each_task.get_frameIXinGOP()                    
                    
                # set end-time
                if(each_task.get_taskCompleteTime() >=  gop_startend_dict['end_time']):
                    gop_startend_dict['end_time'] = each_task.get_taskCompleteTime()
                    gop_startend_dict['etid'] = each_task.get_id()
                    gop_startend_dict['etgid'] = each_task.get_frameIXinGOP()
                
                # mmc-write, end time
                if(SimParams.MMC_ENABLE_DATATRANSMISSION_MODELLING == True):
                    if(each_task.get_taskMMCWRCompleteTime() >=  gop_startend_dict['mmcwr_et']):
                        gop_startend_dict['mmcwr_et'] = each_task.get_taskMMCWRCompleteTime()
                        gop_startend_dict['etid'] = each_task.get_id()
                        gop_startend_dict['etgid'] = each_task.get_frameIXinGOP()
                        
                task_priorities.append(each_task.get_priority())
                gop_len = len(gop_startend_dict['gop_struct'])
                gop_startend_dict['nframes'] += 1
                gop_startend_dict['e2ed'] = float(gop_len)/float(each_task.frame_rate) 
                
                #gop_startend_dict['task_priorities'].append(each_task.get_priority())
                    
            ##---------------------------------------------------------------------------------------
            ## perform sanity check on frame_ids : is last_frame_id = 11, is start_frame_id = 0 ##
            theoretical_nframes_in_gop = len(gop_startend_dict['gop_struct'])*potential_num_tiles_per_frame
            if(gop_startend_dict['nframes'] != theoretical_nframes_in_gop):
                pprint(gop_startend_dict)
                sys.exit("Error - num frames in gop incorrect %d, %d, %d"%(theoretical_nframes_in_gop, gop_startend_dict['nframes'], potential_num_tiles_per_frame))
            elif(gop_startend_dict['nframes'] == len(gop_startend_dict['gop_struct'])):
                if SimParams.TASK_MODEL not in [TaskModel.TASK_MODEL_HEVC_FRAME_LEVEL,TaskModel.TASK_MODEL_HEVC_TILE_LEVEL] :
                    if((gop_startend_dict['etgid'] not in [2,3,5,6,8,9,10,11]) or 
                       (gop_startend_dict['stgid'] != 0)):
                        pprint(gop_startend_dict)
                        sys.exit("Incorrect gop start/end")
            ##---------------------------------------------------------------------------------------
            
            if(SimParams.MMC_ENABLE_DATATRANSMISSION_MODELLING == True):
                full_gop_decode_duration = float(gop_startend_dict['mmcwr_et'] - gop_startend_dict['dispatch_time'])
                gop_startend_dict['gop_mean_pri'] = np.mean(task_priorities)
                gop_startend_dict['tt_wrt_dt'] = full_gop_decode_duration
                gop_startend_dict['tt_wrt_rt'] = gop_startend_dict['mmcwr_et'] - gop_startend_dict['start_time']
                gop_startend_dict['gop_execution_lateness'] = gop_startend_dict['mmcwr_et'] - (each_task.get_dispatchTime() + gop_startend_dict['e2ed'])         
            else:
                full_gop_decode_duration = float(gop_startend_dict['end_time'] - gop_startend_dict['dispatch_time'])
                gop_startend_dict['gop_mean_pri'] = np.mean(task_priorities)
                gop_startend_dict['tt_wrt_dt'] = full_gop_decode_duration
                gop_startend_dict['tt_wrt_rt'] = gop_startend_dict['end_time'] - gop_startend_dict['start_time']
                gop_startend_dict['gop_execution_lateness'] = gop_startend_dict['end_time'] - (each_task.get_dispatchTime() + gop_startend_dict['e2ed'])          
               
               
            if((gop_startend_dict['gop_execution_lateness'] <= 0) and
               (full_gop_decode_duration <= gop_startend_dict['e2ed'])):
                gops_successfully_completed.append(gop_startend_dict['gop_unique_id'])
            
            total_gop_lateness.append(gop_startend_dict['gop_execution_lateness'])
                                
            if(len(frame_groups[each_gop_id]) == theoretical_nframes_in_gop) and (gop_startend_dict['gop_execution_lateness'] > 0):            
                gops_late_but_fully_complete.append(gop_startend_dict['gop_execution_lateness'])
                gops_ids_late_but_fully_complete.append(gop_startend_dict['gop_unique_id'])        
                
            gops_in_outputbuff_summary[frame_groups[each_gop_id][0].get_unique_gop_id()] = gop_startend_dict  
        
        gops_incomplete = len(frame_groups) - len(gops_successfully_completed)
        
        # construct short-gop-summary
        gops_in_outputbuff_summary_short = {}
        for each_k, each_v in  gops_in_outputbuff_summary.iteritems():
            gops_in_outputbuff_summary_short[each_k] = {
                                                        'gop_unique_id' : each_v['gop_unique_id'],
                                                         'end_time' : each_v['end_time'] if SimParams.MMC_ENABLE_DATATRANSMISSION_MODELLING==False else each_v['mmcwr_et'],                                                                                   
                                                         'dispatch_time' : each_v['dispatch_time'],
                                                         'tt_wrt_dt' : each_v['tt_wrt_dt'],                                                                                                                  
                                                         'gop_execution_lateness' : each_v['gop_execution_lateness'],
                                                         'gop_mean_pri': each_v['gop_mean_pri']
                                                        }
            
        
        
        
        wf_results_summary = {}
        #wf_results_summary['gops_successfully_completed'] = gops_successfully_completed
        for each_wf_key, each_wf_val in self.workflows.workflows_summary.iteritems():
            wf_results_summary[each_wf_key] = {}            
            
            for each_vid_key, each_vid_val in each_wf_val.iteritems():  
                
                # check if all gops in video have been fully completed, withion the deadline
                orig_gop_set = set(each_vid_val['gops'])
                results_gop_set = set(gops_successfully_completed)
               
                if(orig_gop_set.issubset(results_gop_set) == True):
                    wf_results_summary[each_wf_key][each_vid_key] = {                                                                     
                                                                     # design_time_info
                                                                     'numgops' : each_vid_val['numgops'],
                                                                     'res_h' : each_vid_val['resolution'][0],
                                                                     'res_w' : each_vid_val['resolution'][1],
                                                                     'starttime' : each_vid_val['starttime'],
                                                                     'endtime' : each_vid_val['endtime'],
                                                                     'avg_dis_rate' : each_vid_val['avg_dispatch_rate'],
                                                                     
                                                                     # sim results
                                                                     'result': True                                                                     
                                                                     }
                else:
                    # find which gops of the unsuccessful vids were partially/delayed completed
                    g = []
                    late_gops =[]
                    for each_gop in each_vid_val['gops']:
                        if(each_gop in frame_groups):
                            g.append(each_gop)
                        if(each_gop in gops_ids_late_but_fully_complete):
                            late_gops.append(each_gop)
                    
                    wf_results_summary[each_wf_key][each_vid_key] = {                                                                     
                                                                     # design_time_info
                                                                     'numgops' : each_vid_val['numgops'],
                                                                     'res_h' : each_vid_val['resolution'][0],
                                                                     'res_w' : each_vid_val['resolution'][1],
                                                                     'st' : each_vid_val['starttime'],
                                                                     'et' : each_vid_val['endtime'],
                                                                     'avg_dis_rate' : each_vid_val['avg_dispatch_rate'],
                                                                     
                                                                     # sim_results
                                                                     'result': False,
                                                                     'gops_in_outbuff': g,
                                                                     'gops_late_but_fully_complete' : late_gops
                                                                     }
                    
        
        
        # save results summary
        if(wf_res_summary_fname != None):
            self._write_formatted_file(wf_res_summary_fname, wf_results_summary, output_format)        
        
        # save full gop specific results summary
        if(gops_opbuff_summary_short_fname != None):
            self._write_formatted_file(gops_opbuff_summary_short_fname, gops_in_outputbuff_summary_short, output_format)
        else:
            self._write_formatted_file(gops_opbuff_summary_fname, gops_in_outputbuff_summary, output_format)
        
        # output video stream timeline
        if(SimParams.TRACK_WFLEVEL_TASKTIMELINE_PNG_DUMP == True):
            self.workflows.showTaskTimeLine(len(self.workflows.workflows_summary), simon_wf_results_summary=wf_results_summary, fname=timeline_fname)
        
        # output rm-dropped tasks table        
        #self._write_formatted_file(rmtbl_dt_summary_fname, self.resource_manager.video_streams, output_format)
        
        # return all the gathered results back 
        return (wf_results_summary, gops_in_outputbuff_summary)
    
    
    def _write_formatted_file(self, fname, data, format):        
        if(format == "pretty"):
            logfile=open(fname, 'w')
            pprint(data, logfile, width=128)
            
        elif(format == "json"):
            logfile=open(fname, 'w')
            json_data = json.dumps(data)
            logfile.write(json_data)
            
        else:
            logfile=open(fname, 'w')
            pprint(data, logfile, width=128)
            
            
        
        
    
    def report_OutputBuffer_Contents_ByGOP(self, verbose=0, dump_to_file=None):
        print " "
        print "show_OutputBuffer_Contents_ByGOP"
        print "================================"        
        
        # construct GOP range
        frame_groups = {}
        for each_task in self.output_buffer.get_BuffContents():
            if each_task.get_unique_gop_id() not in frame_groups:                
                frame_groups[each_task.get_unique_gop_id()] = []        
        for each_task in self.output_buffer.get_BuffContents():
            frame_groups[each_task.get_unique_gop_id()].append(each_task)
        
        gop_end_to_end_deadline = (float(SimParams.GOP_LENGTH)/float(SimParams.FRAME_RATE))
        
        ## print out results of each GOP ##
        gops_successfully_completed = []    # i.e : not late, and all frames decoded
        gops_late_but_fully_complete = []
        total_gop_lateness = []
        for each_gop_id in frame_groups:
            
            gop_startend_dict = {
                             'total_frames_in_gop' : 0,
                             'start_time' : frame_groups[each_gop_id][0].get_releaseTime(),
                             'start_task_id' : 0,
                             'start_task_gopix' : 0,
                             'end_time' : frame_groups[each_gop_id][0].get_taskCompleteTime(),
                             'end_task_id' : 0,
                             'end_task_gopix' : 0,
                             'gop_struct' : frame_groups[each_gop_id][0].get_gopstructure(),
                             'dispatch_time' : frame_groups[each_gop_id][0].get_dispatchTime(),                             
                             }            
            
            print " "
            print "GOP_ID = " +  str(each_gop_id)
            print "-------------"
            
            for each_task in frame_groups[each_gop_id]:
                
                if(verbose == 1):
                    print "Ti="+ str(each_task.get_id()) + \
                        ", (=" + str(each_task.get_type())+")" + \
                        ", relT=" + str(each_task.get_releaseTime()) + \
                        ", stT=" + str(each_task.get_taskStartTime()) + \
                        ", cmpT=" + str(each_task.get_taskCompleteTime()) + \
                        ", cc=" + str(each_task.get_computationCost()) + \
                        ", wccc=" + str(each_task.get_worstCaseComputationCost())
                    
                if(each_task.get_releaseTime() <  gop_startend_dict['start_time']):
                    gop_startend_dict['start_time'] = each_task.get_releaseTime()
                    gop_startend_dict['start_task_id'] = each_task.get_id()                    
                    gop_startend_dict['start_task_gopix'] = each_task.get_frameIXinGOP()
            
                if(each_task.get_taskCompleteTime() >=  gop_startend_dict['end_time']):
                    gop_startend_dict['end_time'] = each_task.get_taskCompleteTime()
                    gop_startend_dict['end_task_id'] = each_task.get_id()
                    gop_startend_dict['end_task_gopix'] = each_task.get_frameIXinGOP()
                
                gop_startend_dict['total_frames_in_gop'] += 1
                    
            ##---------------------------------------------------------------------------------------
            ## perform sanity check on frame_ids : is last_frame_id = 11, is start_frame_id = 0 ##
            gop_len = len(gop_startend_dict['gop_struct'])
            if(gop_startend_dict['total_frames_in_gop'] > gop_len):
                pprint(gop_startend_dict)
                sys.exit("Error - too many frames in gop")
            elif(gop_startend_dict['total_frames_in_gop'] == gop_len):
                if SimParams.TASK_MODEL not in [TaskModel.TASK_MODEL_HEVC_FRAME_LEVEL,TaskModel.TASK_MODEL_HEVC_TILE_LEVEL]:
                    if((gop_startend_dict['end_task_gopix'] not in [8,9,10,11]) or 
                       (gop_startend_dict['start_task_gopix'] != 0)):
                        pprint(gop_startend_dict)
                        sys.exit("Incorrect gop start/end")
            ##---------------------------------------------------------------------------------------
            
            if(verbose != 0):            
                pprint(gop_startend_dict)
            
            
            print "Total frames processed = " + str(len(frame_groups[each_gop_id]))
            
            full_gop_decode_duration = float(gop_startend_dict['end_time'] - gop_startend_dict['dispatch_time'])
            
            print "Total_time (completed_time - dispatched_time)= " + str(full_gop_decode_duration)
            print "Total_time (completed_time - release_time)= " + str(gop_startend_dict['end_time'] - gop_startend_dict['start_time'])
            
            print "GOP_End-to-End deadline = %f" % (gop_end_to_end_deadline)
            gop_execution_lateness = gop_startend_dict['end_time'] - (each_task.get_dispatchTime() + float(gop_len)/float(each_task.get_framerate()))
            print "Lateness = %f" % (gop_execution_lateness)
        
            if((gop_execution_lateness < 0) and
               (full_gop_decode_duration < gop_end_to_end_deadline)):
                gops_successfully_completed.append(each_gop_id)
            
            total_gop_lateness.append(gop_execution_lateness)
                                
            if(len(frame_groups[each_gop_id]) == SimParams.GOP_LENGTH) and (gop_execution_lateness > 0):            
                gops_late_but_fully_complete.append(gop_execution_lateness)
                
        print " "
        print "Number of GOPs successfully decoded = " + str(len(gops_successfully_completed)) 
        print "Number of incomplete GOPs = " + str(len(frame_groups) - len(gops_successfully_completed))
        print "Number of gops (late but fully complete) = " + str(len(gops_late_but_fully_complete))
        avg_gop_lateness = float(sum(total_gop_lateness))/float(len(total_gop_lateness))
        max_gop_lateness = float(max(total_gop_lateness))
        min_gop_lateness = float(min(total_gop_lateness))
        sum_gop_lateness = float(sum(total_gop_lateness))
        
        print "Average_GOP_lateness (avg)= " + str(avg_gop_lateness)
        print "Maximum GOP lateness (max)= " + str(max_gop_lateness)
        print "Minimum GOP lateness (min)= " + str(min_gop_lateness)
        print "Total GOP lateness (sum) = " + str(sum_gop_lateness)
        print "Total Blocks Dispatched = " + str(self.task_dispatcher.total_blocks_dispatched)        
        
        print str(self.task_dispatcher.total_blocks_dispatched) + "," + \
                str(len(gops_successfully_completed)) + "," + \
                str(len(gops_late_but_fully_complete))
        
        ############################
        ### dump data to file(s) ###
        ############################        
        if(dump_to_file != None):
            lateness_stats =   str(self.task_dispatcher.total_blocks_dispatched) + "," + \
                str(len(gops_successfully_completed)) + "," + \
                str(len(gops_late_but_fully_complete)) + "," + \
                ("%f" % avg_gop_lateness) + "," + \
                ("%f" % max_gop_lateness) + "," + \
                ("%f" % min_gop_lateness) + "," + \
                ("%f" % sum_gop_lateness)                            
            
            # write entire gop_lateness values per gop     
            fname = dump_to_file+"__data.txt"
            with open(fname, 'w') as f:
                for lateness in total_gop_lateness:
                    f.write(("%f"%lateness) + '\n')
            
            # write summary to file 
            fname = dump_to_file+"__summary.txt"
            with open(fname, 'w') as f:               
                    f.write(lateness_stats)
            
                
    ####################################################################################
    # Helpers
    ####################################################################################
            
    def _build_link_info(self):
        link_report = {}
        for flw in self.resource_manager.flow_table.track_flows_completed:
            route_str = flw["r"]
            num_interferers = flw["intfs"]
            payload = flw["pl"]
            l_var = flw["l_var"]
            
            route_2dlist = self._get_route_node_tuples(route_str)
            
            for each_link in route_2dlist:
                src_nid = each_link[0]
                dst_nid = each_link[1]
                
                link_obj = self.resource_manager.interconnect._findLink(src_nid, dst_nid)
                link_id = link_obj.get_id()
                
                if link_id not in link_report:
                    link_report[link_id] = {                                            
                                            'data_dir' : link_obj.get_data_dir(),
                                            'src_dst_nid_tup' : link_obj.get_src_dst(),
                                                                                         
                                            'intfs_max_min_sum_mean' : [num_interferers,num_interferers,num_interferers,num_interferers],                                            
                                            #'intfs_list' : [num_interferers],
                                            
                                            'payload_max_min_sum_mean' : [payload,payload,payload,payload],
                                            #'payload_list': [payload],
                                            
                                            'total_flows' : 1,
                                            
                                            'l_var_max_min_sum_mean' : [l_var,l_var,l_var,l_var],
                                            #'l_var_list' : [l_var]                 
                                            }
                else:                    
                    link_report[link_id]['total_flows'] += 1
                    
                    # intfs
                    if num_interferers > link_report[link_id]['intfs_max_min_sum_mean'][0]: # max
                        link_report[link_id]['intfs_max_min_sum_mean'][0] = num_interferers
                    if num_interferers < link_report[link_id]['intfs_max_min_sum_mean'][1]: # min
                        link_report[link_id]['intfs_max_min_sum_mean'][1] = num_interferers
                    
                    link_report[link_id]['intfs_max_min_sum_mean'][2] += num_interferers # sum
                    link_report[link_id]['intfs_max_min_sum_mean'][3] = float(link_report[link_id]['intfs_max_min_sum_mean'][2])/float(link_report[link_id]['total_flows']) # mean
                    
                    # payload
                    if payload > link_report[link_id]['payload_max_min_sum_mean'][0]: # max
                        link_report[link_id]['payload_max_min_sum_mean'][0] = payload
                    if payload < link_report[link_id]['payload_max_min_sum_mean'][1]: # min
                        link_report[link_id]['payload_max_min_sum_mean'][1] = payload
                    
                    link_report[link_id]['payload_max_min_sum_mean'][2] += payload # sum
                    link_report[link_id]['payload_max_min_sum_mean'][3] = float(link_report[link_id]['payload_max_min_sum_mean'][2])/float(link_report[link_id]['total_flows']) # mean
     
                    # l_var
                    if l_var > link_report[link_id]['l_var_max_min_sum_mean'][0]: # max
                        link_report[link_id]['l_var_max_min_sum_mean'][0] = l_var
                    if l_var < link_report[link_id]['l_var_max_min_sum_mean'][1]: # min
                        link_report[link_id]['l_var_max_min_sum_mean'][1] = l_var
                    
                    link_report[link_id]['l_var_max_min_sum_mean'][2] += l_var # sum
                    link_report[link_id]['l_var_max_min_sum_mean'][3] = float(link_report[link_id]['l_var_max_min_sum_mean'][2])/float(link_report[link_id]['total_flows']) # mean
     
        
        ## populate links that have not been used
#         print "len(link_report.keys()) :", len(link_report.keys())
#         print "self.resource_manager.interconnect.getLinks() :", len(self.resource_manager.interconnect.getLinks()) 
#         print "unique link ids: ", len(set([l.get_id() for l in self.resource_manager.interconnect.getLinks()]))
        all_noc_links = self.resource_manager.interconnect.getLinks() 
        for each_l in all_noc_links:
            link_id = each_l.get_id()
            if link_id not in link_report:
                link_report[link_id] = {                                            
                                            'data_dir' : each_l.get_data_dir(),
                                            'src_dst_nid_tup' : each_l.get_src_dst(),
                                                                                         
                                            'intfs_max_min_sum_mean' : [0,0,0,0.0],                                            
                                            
                                            'payload_max_min_sum_mean' : [0,0,0,0.0],
                                            
                                            'total_flows' : 0,
                                            
                                            'l_var_max_min_sum_mean' : [0,0,0,0.0],
                                            }
            else:
                pass # already populated in previous loop
                
        return link_report
        
        
                
                
                
                
            
    
    def _get_route_node_tuples(self, route_str):
        removed_sq_br = route_str.replace("[", "")
        removed_sq_br = removed_sq_br.replace("]", "")
        route_split =  removed_sq_br.split(",")
        route_2dlist = [v.strip().split("->") for v in route_split]
        return route_2dlist
        
        
        
        