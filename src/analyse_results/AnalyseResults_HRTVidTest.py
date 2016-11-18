import sys, os, csv, pprint, math

from collections import OrderedDict
import numpy as np
import random
import shutil
import math
import matplotlib
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import scipy.stats
import itertools
from matplotlib.colors import ListedColormap, NoNorm
from matplotlib import mlab
from itertools import cycle # for automatic markers
import json
from operator import itemgetter

import matplotlib.cm as cm
from matplotlib.font_manager import FontProperties
from SimParams import SimParams


import Multicore_MPEG_Model as MMMSim


NUM_WORKFLOWS = range(8, 19, 1)
#NUM_WORKFLOWS = [9]
#NUM_NODES = [2,4,8,16,32]
NUM_NODES = 9
NOC_XY = [(2,1), (2,2), (2,4), (2,8), (2,16)]


IBUFF_TASKS_LATENESS_RATIO_RANGE    = [0.3, 0.7]
TQ_TASKS_LATENESS_RATIO_RANGE       = [0.3, 0.7]        




def plot_Summary(results):
    
    fig = plt.figure()
    fig.canvas.set_window_title('summary')
    
    ax1 = plt.subplot(1,1,1)
    
    # plot ibuff usage - lateness
    ax1.plot(results['timeline'], results['ibuff_usage']['sum_cumlateness'], color='b', ls='--')
    plt.hold(True)
    ax2 = ax1.twinx()
    ax2.plot(results['timeline'], results['cpu_idleness']['vertical_sum_idletimes'], color='r')
    #plt.hold(True)

    ax1.set_ylabel('ibuff_sum_cumlateness', color='b')
    ax2.set_ylabel('core_sum_idletimes', color='r')
    
    plt.grid(b=True, alpha=0.5, linestyle='-')





def plot_InputBuff_Usage(fname =  "../test__ibuff.js"):
    
    json_data=open(fname)
    file_data = json.load(json_data)
    
    fig = plt.figure()
    #fig, ax = plt.subplots(1, len(file_data)) 
    fig.canvas.set_window_title('ibuff_usage')
    
    axis_list = []
    max_ax1_ylim = 0.0
    max_ax2_ylim = 0.0    
    summary_all_levels = []
    summary_all_cumlateness = []
    
    # get data for each ibuff    
    for i, each_ibuff in enumerate(file_data):
        
        data_level = [x['level'] for x in each_ibuff]
        data_cumlateness = [x['cum_lateness'] for x in each_ibuff]
        data_time = [x['time'] for x in each_ibuff]
        
        summary_all_levels.append(data_level)
        summary_all_cumlateness.append(data_cumlateness)
                
        ax1 = plt.subplot(len(file_data),1,i+1)
        ax2 = ax1.twinx()       
        axis_list.append([ax1,ax2])
        
        ax1.plot(data_time, data_level, lw=2, color='b')
        ax2.plot(data_time, data_cumlateness, lw=2, color='r')
        
        ax1.set_ylabel('level', color='b')
        ax2.set_ylabel('cum_lateness', color='r')        
        ax1.tick_params(axis='both', which='major', labelsize=8)    
        ax2.tick_params(axis='both', which='major', labelsize=8)
        ax1.grid(b=True, alpha=0.5, linestyle='-')
        ax2.grid(b=True, alpha=0.5, linestyle='-')
                    
        ax1.set_title("Ibuff-"+str(i))
        if(max(data_level) > max_ax1_ylim): max_ax1_ylim = max(data_level)
        if(max(data_cumlateness) > max_ax2_ylim): max_ax2_ylim = max(data_cumlateness)
        
    for each_ax in axis_list:
        each_ax[0].set_ylim((0.0,max_ax1_ylim))
        each_ax[1].set_ylim((0.0,max_ax2_ylim))    
    
    ## create summary of info - to return     
    mean_levels = np.mean(np.array(summary_all_levels), axis=0)
    mean_cumlateness = np.mean(np.array(summary_all_cumlateness), axis=0)     
    sum_levels = np.sum(np.array(summary_all_levels), axis=0)
    sum_cumlateness = np.sum(np.array(summary_all_cumlateness), axis=0)    
    
    
    results_summary = {
                       'data_time' : data_time, 
                       'mean_levels' : mean_levels, 
                       'mean_cumlateness' : mean_cumlateness, 
                       'sum_levels' : sum_levels, 
                       'sum_cumlateness' : sum_cumlateness
                       }    

    return results_summary



def plot_NodeTQ_Usage(filter, report_summary=False, pfname= None):
    
    if pfname == None:    
        fname =  "../test__nodetqs.js"
    else:
        fname =  pfname
        
    json_data=open(fname)
    file_data = json.load(json_data)
    
    fig = plt.figure()
    fig.canvas.set_window_title('nodeTQ_usage__'+filter)
    
    axis_list = []
    max_ax1_ylim = 0.0
    max_ax2_ylim = 0.0    
    summary_all_len = []
    summary_all_cumlateness = []
    summary_all_tqremexec = []
    
    entry = {
             "tq_len": [],
             "cum_lateness": [],
             "tq_remcc": []
             }
    
    #nstq_data = [entry] * NUM_NODES
    nstq_data = []
    
    # get all data points for each node
    for each_node_ix in xrange(NUM_NODES):
       
        
        entry = {
             "tq_len": [x['record'][each_node_ix]['tq_len'] for x in file_data],
             "cum_lateness": [x['record'][each_node_ix]['cum_lateness'] for x in file_data],
             "tq_remcc": [x['record'][each_node_ix]['tq_remcc'] for x in file_data]
             }                 
        nstq_data.append(entry)
        data_time = [x['time'] for x in file_data]
        
        ax1 = plt.subplot(NUM_NODES,1,each_node_ix+1) 
        ax1.plot(data_time, nstq_data[each_node_ix][filter], lw=1, color='b')
    
        ax1.set_ylabel(filter, color='b')                
        ax1.tick_params(axis='both', which='major', labelsize=8)
        ax1.set_title("CPU-"+str(each_node_ix))
        ax1.grid(b=True, alpha=0.5, linestyle='-')
        
        if(max(nstq_data[each_node_ix][filter]) > max_ax1_ylim): max_ax1_ylim = max(nstq_data[each_node_ix][filter])
        
        axis_list.append([ax1])
     
    for each_ax in axis_list:
        each_ax[0].set_ylim((0.0,max_ax1_ylim))
    
    ## report ##
    if(report_summary==True):
        print "-------------"
        print "REPORT :: " + filter + ", (totals)"
        cumsum=0
        for each_node_ix in xrange(NUM_NODES):
            sum = np.sum(nstq_data[each_node_ix][filter])
            print "CPU-"+ str(each_node_ix) + ": " + str(sum)  
            cumsum+=sum
        
        print "cumsum: " + str(cumsum)
        print "-------------"
            
    
    
    
def plot_Pri_vs_Lateness():   
    fname =  "../test__obuff.js"
    json_data=open(fname)
    file_data = json.load(json_data)
    
    fig = plt.figure()
    fig.canvas.set_window_title('pri_vs_lateness')
    
    sorted_file_data = sorted(file_data, key=itemgetter('priority')) 
    
    task_priorities = [x['priority'] for x in sorted_file_data] 
    task_ids = [x['id'] for x in sorted_file_data]
    task_estlateness = [x['est_lateness'] for x in sorted_file_data]

    plt.plot(task_priorities, task_estlateness)

        
        

    
    

###################################################################################################
#    Utilisation comparisons, visualisations
###################################################################################################

def plot_WindowedIdleness(fname =  "../test__utilisation.js"):
    
    NUM_WF = 12
    NUM_CORES = 9
    
    ##############################
    ####### gather results 
    ##############################   
   
    all_exp_data = {}    
  
    exp_data = {}
    
    ## No AC ##
    # get data        
    
    json_data=open(fname)
    file_data = json.load(json_data)
    exp_data['No-AC'] = file_data
            
    all_exp_data['exp_data'] = exp_data
                
              
    #####################################
    ####### format data, get what we need
    #####################################
        
    allwfs_idletime_allperms = OrderedDict()
    node_specific_idletimes = OrderedDict()
    node_specific_idletimes_with_totalsimtime = OrderedDict()
    
        
    node_specific_idletimes[NUM_WF] = []
    node_specific_idletimes_with_totalsimtime[NUM_WF] = []
    
    timeline = []
    
    vertical_sum_idletimes = []
    vertical_mean_idletimes = []
    
    allwfs_idletime_allperms[NUM_WF] = []
    for each_exp_key, each_exp_data in all_exp_data['exp_data'].iteritems():
        mean_idletimes = [] 
        sum_idletimes = []
        mean_busytimes = []
        sum_busytimes = [] 
        std_idletime = []          
        for each_data_point in each_exp_data['node_idle_time']:
            total_idle = 0
            total_busy = 0
            for idle_time in each_data_point['nsit']:                    
                total_idle +=  idle_time
                total_busy += float(1.0-idle_time)
                 
            mean_idletimes.append(float(total_idle/len(each_data_point['nsit'])))
            mean_busytimes.append(float(total_busy/len(each_data_point['nsit'])))
            sum_idletimes.append(total_idle)
            sum_busytimes.append(total_busy)
            std_idletime.append(np.std(each_data_point['nsit']))
            
            timeline.append(each_data_point['time'])
            
            vertical_sum_idletimes.append(np.sum(each_data_point['nsit']))
            vertical_mean_idletimes.append(np.mean(each_data_point['nsit']))
            
            
        mean_throughput = [] 
        sum_throughput = []
        for each_data_point in each_exp_data['node_throughput']:
            total_t = 0                
            for idle_time in each_data_point['csp_tc']:                    
                total_t +=  idle_time
                 
            mean_throughput.append(float(total_t/len(each_data_point['csp_tc'])))
            sum_throughput.append(total_t)
        
        allwfs_idletime_allperms[NUM_WF].append(mean_idletimes)            
        
        total_sim_time = float(len(each_exp_data['node_idle_time']) * SimParams.SIM_MONITOR_SAMPLE_RATE * 1.0)
       
        node_specific_idletimes[NUM_WF].append(each_exp_data['node_idle_time'][-1])
        
        temp_entry = {
                      'total_idletime' : each_exp_data['node_idle_time'][-1],
                      'total_simtime' : total_sim_time
                      }
        
        node_specific_idletimes_with_totalsimtime[NUM_WF].append(temp_entry)
        
    
    ##############################
    ####### plot idleness per cpu
    ##############################    
    labels = [("%s"%x) for x in all_exp_data['exp_data'].keys()]

    fig = plt.figure()
    lines = ["-","--","-.",":"]
    linecycler = cycle(lines)
    
    #fig, ax = plt.subplots(NUM_CORES, NUM_CORES)
    
    track_ns_idleness = []
    
    for each_node in xrange(NUM_CORES):
        
        running_nsit = []        
        
        ax = plt.subplot(NUM_CORES,1,each_node)
        for each_sample in all_exp_data['exp_data']['No-AC']['node_idle_time']:
            data = each_sample['nsit'][each_node]
            running_nsit.append(data)            
        
      
        x = np.array(running_nsit, dtype=np.float)
        grad = np.gradient(x)        
        #ax.plot(grad, lw=1, color='r')
        ax.plot(timeline, x, lw=1, color='b')
        ax.set_ylim((0.0,0.5))
        ax.set_title("CPU-"+str(each_node))
        
        track_ns_idleness.append(x)
    
    # average of gradients
    fig = plt.figure()
    mean_grads = np.array(np.mean(track_ns_idleness,axis=0))
    np.seterr(divide='ignore', invalid='ignore')
    for each_node in xrange(NUM_CORES):
        
        ax = plt.subplot(NUM_CORES,1,each_node)
        
        running_nsit = np.array(track_ns_idleness[each_node])        
        ratio =  np.divide(running_nsit, mean_grads)
         
        ax.plot(timeline, ratio, lw=1, color='g')
        ax.set_ylim((0.0,9))
        ax.set_title("CPU-"+str(each_node))    
    
    #################################
    ####### plot lines all wfs in one
    #################################  
    plt.figure()
    summation = {}
    
    total_sim_time = {}
    ind = np.arange(len([each_exp['total_idletime'] for each_exp in node_specific_idletimes_with_totalsimtime[NUM_WF] if 'it_c' in each_exp['total_idletime']]))
    width = 0.25
    positions = [ind, ind+width]
    
    lcols = itertools.cycle(('blanchedalmond', 'blueviolet'))
    i=0
    
    pprint.pprint(each_exp['total_idletime']['it_c'])
    pprint.pprint(np.mean(each_exp['total_idletime']['it_c']))
    pprint.pprint(each_exp['total_simtime'])
    summation[NUM_WF] = [ float(float(np.mean(each_exp['total_idletime']['it_c']))/each_exp['total_simtime'])*100.0 for each_exp in node_specific_idletimes_with_totalsimtime[NUM_WF] if 'it_c' in each_exp['total_idletime']]
    #total_sim_time[wf_id] = 0
    
    #plt.bar(positions[0:len(summation[wf_id])], summation[wf_id], width=width, label='wf' + str(wf_id))
    #plt.hold(True)
    plt.bar(positions[i], summation[NUM_WF], width=width, color=lcols.next(), alpha=0.9)                
    
    
    plt.hold(True)
    p = plt.axvspan(0.0, (width*5.0)+(width*1.75), facecolor='0.5', alpha=0.3)
    
    xticks = ind+(width*1.0)
    xticks = [x for x in xticks]
    plt.tick_params(axis='both', which='major', labelsize=20)
    plt.xticks(xticks, labels)    
    
    plt.grid(True)
    #leg = plt.legend()
    #leg.draggable()
    
    results_summary = {
                       'timeline' : timeline, 
                       'vertical_sum_idletimes' : vertical_sum_idletimes, 
                       'vertical_mean_idletimes' : vertical_mean_idletimes                       
                       }    

    return results_summary



            
def plot_InstUtilisation_VH(summaryHist=False, fillPlots=False):        
    
    NUM_WORKFLOWS = [6]
    WF_RANGE = [6]
    
    ##############################
    ####### gather results 
    ##############################   
    
    folder = 'experiment_data/vs_ac_test/'
    all_exp_data = OrderedDict()    
    
    for each_wf_num in NUM_WORKFLOWS:
        
        exp_data = OrderedDict()
        
        ## No AC ##
        # get data        
        fname =  "test__utilisation.js"
        json_data=open(fname)
        file_data = json.load(json_data)
        exp_data['No-AC'] = file_data
                
        all_exp_data[each_wf_num] = exp_data
                
              
    #####################################
    ####### format data, get what we need
    #####################################
        
    allwfs_idletime_allperms = OrderedDict()
    node_specific_idletimes = OrderedDict()
    node_specific_idletimes_with_totalsimtime = OrderedDict()
    mean_idletime = []
    for wf_id in NUM_WORKFLOWS:
        
        node_specific_idletimes[wf_id] = []
        node_specific_idletimes_with_totalsimtime[wf_id] = []
        
        allwfs_idletime_allperms[wf_id] = []
        for each_exp_key, each_exp_data in all_exp_data[wf_id].iteritems():
            mean_idletimes = [] 
            sum_idletimes = []
            mean_busytimes = []
            sum_busytimes = [] 
            std_idletime = []          
            for each_data_point in each_exp_data['node_idle_time']:
                total_idle = 0
                total_busy = 0
                for idle_time in each_data_point['nsit']:                    
                    total_idle +=  idle_time
                    total_busy += float(1.0-idle_time)
                     
                mean_idletimes.append(float(total_idle/len(each_data_point['nsit'])))
                mean_busytimes.append(float(total_busy/len(each_data_point['nsit'])))
                sum_idletimes.append(total_idle)
                sum_busytimes.append(total_busy)
                std_idletime.append(np.std(each_data_point['nsit']))
                       
            mean_throughput = [] 
            sum_throughput = []
            for each_data_point in each_exp_data['node_throughput']:
                total_t = 0                
                for idle_time in each_data_point['csp_tc']:                    
                    total_t +=  idle_time
                     
                mean_throughput.append(float(total_t/len(each_data_point['csp_tc'])))
                sum_throughput.append(total_t)
            
            allwfs_idletime_allperms[wf_id].append(mean_idletimes)            
            
            total_sim_time = float(len(each_exp_data['node_idle_time']) * SimParams.SIM_MONITOR_SAMPLE_RATE * 1.0)
           
            node_specific_idletimes[wf_id].append(each_exp_data['node_idle_time'][-1])
            
            temp_entry = {
                          'total_idletime' : each_exp_data['node_idle_time'][-1],
                          'total_simtime' : total_sim_time
                          }
            
            node_specific_idletimes_with_totalsimtime[wf_id].append(temp_entry)
        
    
    ##############################
    ####### plot boxplots 
    ##############################    
    labels = [("%s"%x) for x in all_exp_data[6].keys()]
#    f_0, axarr_0 = plt.subplots(len(WF_RANGE), sharex=True)
#    f_0.canvas.set_window_title("Utilisation boxplots")
#    
    f_1, axarr_1 = plt.subplots(len(WF_RANGE), sharex=True)
    f_1.canvas.set_window_title("Utilisation nodespecific")
    
    #################################
    ####### plot lines all wfs in one
    #################################  
    plt.figure()
    summation = {}
    
    total_sim_time = {}
    ind = np.arange(len([each_exp['total_idletime'] for each_exp in node_specific_idletimes_with_totalsimtime[6] if 'it_c' in each_exp['total_idletime']]))
    width = 0.25
    positions = [ind, ind+width]
    
    lcols = itertools.cycle(('blanchedalmond', 'blueviolet'))
    i=0
    for wf_id in WF_RANGE:
        pprint.pprint(each_exp['total_idletime']['it_c'])
        pprint.pprint(np.mean(each_exp['total_idletime']['it_c']))
        pprint.pprint(each_exp['total_simtime'])
        summation[wf_id] = [ float(float(np.mean(each_exp['total_idletime']['it_c']))/each_exp['total_simtime'])*100.0 for each_exp in node_specific_idletimes_with_totalsimtime[wf_id] if 'it_c' in each_exp['total_idletime']]
        #total_sim_time[wf_id] = 0
        
        #plt.bar(positions[0:len(summation[wf_id])], summation[wf_id], width=width, label='wf' + str(wf_id))
        #plt.hold(True)
        plt.bar(positions[i], summation[wf_id], width=width, color=lcols.next(), alpha=0.9)                
        
        i+=1
    plt.hold(True)
    p = plt.axvspan(0.0, (width*5.0)+(width*1.75), facecolor='0.5', alpha=0.3)
    
    xticks = ind+(width*1.0)
    xticks = [x for x in xticks]
    plt.tick_params(axis='both', which='major', labelsize=20)
    plt.xticks(xticks, labels)    
    
    plt.grid(True)
    #leg = plt.legend()
    #leg.draggable()
        
        
        
        
def _set_bp(ax, bp, col):
    plt.setp(bp['boxes'], color=col, linewidth=1, alpha=0.7)    
    plt.setp(bp['caps'], color=col)
    plt.setp(bp['whiskers'], color=col)
    plt.setp(bp['fliers'], color=col)
    plt.setp(bp['medians'], color=col)
    






###################################
#    HELPERS
###################################

        
def _getEntry(file_data):
    
    entry =  {
            "num_vids_accepted_success": file_data['num_vids_accepted_success'], 
            "num_dropped_tasks": file_data['num_dropped_tasks'], 
            "num_vids_accepted_late": file_data['num_vids_accepted_late'], 
            "num_vids_rejected": file_data['num_vids_rejected']
        }    
    return entry

def _getUtilData(fname):
    file = open(fname, 'r')        
    data = file.readlines()
    data = [(float(x.strip())) for x in data]        
    
    return data


def _movingaverage (values, window):
    weights = np.repeat(1.0, window)/window
    sma = np.convolve(values, weights, 'same')
    return sma




###################################
#    MAIN
###################################

prefix = "../experiment_data/hrt_video/OL_3_3_"


w_idleness_results = plot_WindowedIdleness(fname=prefix+"test__util.js")
#ibuff_usage_results = plot_InputBuff_Usage(fname=prefix+"test__ibuff.js")
ibuff_usage_results = None
summary_results = {
                   'timeline' : w_idleness_results['timeline'],
                   'cpu_idleness' : w_idleness_results,
                   'ibuff_usage' : ibuff_usage_results
                   } 


#plot_Summary(summary_results)

plot_NodeTQ_Usage('tq_len', report_summary=True, pfname = prefix+"test__nodetqs.js")
#plot_NodeTQ_Usage('cum_lateness', report_summary=True, pfname = prefix+"test__nodetqs.js")
#plot_NodeTQ_Usage('tq_remcc', report_summary=True, pfname = "../experiment_data/mapping_and_pri_schemes/seed_99108/Exp_m5_p0_wf8_cores9_nodetqs.js")

#plot_Pri_vs_Lateness()


print "finished"

plt.show()

