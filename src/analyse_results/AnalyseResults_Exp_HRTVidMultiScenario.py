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

MAX_NUM_GOPS_IN_VS = SimParams.WFGEN_MAX_GOPS_PER_VID
NOC_H = 3
NOC_W = 3

FNAME_PREFIX_LIST = [                     
                     ("NOAC_LUM", "NOAC_LUM"), 
                     ("NOCAC_IMPROVEDM", "NOCAC_RMM"),
                     ("SCHEDONLYAC_LUM", "DETERM_LUM"),
                     ("SCHEDONLYAC_IMPROVEDM", "DETERM_RMM")
                     ]

SCENARIO_LIST = [
                 ("SCV1_", "scenario_1"),
                 ("SCV2_", "scenario_2"),
                 ("SCV3_", "scenario_3"),
                 ("SCV4_", "scenario_4")
                 ]


EXP_DATA_DIR = "../experiment_data/hrt_video/"

def plot_FlowsResponseTime(use_sched_test_results = False):
    
    all_scenario_all_actypes_distributions = OrderedDict()
    all_distributions = []
    for each_scenario in SCENARIO_LIST:
        #print each_scenario
        for each_fname_prefix in FNAME_PREFIX_LIST:
            if("SCH" in each_fname_prefix[0]) and (use_sched_test_results == True): # if it's a schedulability test, we have to get the analytical results
                # get data            
                fname_prefix = each_scenario[0] + each_fname_prefix[0] + "_"+str(NOC_H)+"_"+str(NOC_W)+"_"
                fname = EXP_DATA_DIR + each_scenario[1] + "/" +fname_prefix + "test__schedtestresults.js"    
                json_data=open(fname)
                flow_data = json.load(json_data)
                                
                sorted_flow_data_response_times = flow_data[-1]["current_allflows_wcrt_distribution"]
                
            else:
                # get data            
                fname_prefix = each_scenario[0] + each_fname_prefix[0] + "_"+str(NOC_H)+"_"+str(NOC_W)+"_"
                fname = EXP_DATA_DIR + each_scenario[1] + "/" +fname_prefix + "test__flwcompleted.js"    
                json_data=open(fname)
                flow_data = json.load(json_data)
                
                # sort them according to id
                sorted_flow_data = sorted(flow_data, key=itemgetter('id'))
                sorted_flow_data_response_times = [float(x['et']-x['st']) for x in sorted_flow_data if x['type'] == 1]

            all_distributions.append(np.array(sorted_flow_data_response_times))
            #print each_fname_prefix
            
            if (each_scenario not in all_scenario_all_actypes_distributions):
                all_scenario_all_actypes_distributions[each_scenario] = OrderedDict()
                all_scenario_all_actypes_distributions[each_scenario][each_fname_prefix[0]] = sorted_flow_data_response_times
            else:
                all_scenario_all_actypes_distributions[each_scenario][each_fname_prefix[0]] = sorted_flow_data_response_times
         
    # plot all ac types flow-response-times for all ac-types
    fig = plt.figure()
    fig.canvas.set_window_title('plot_FlowsResponseTime')
    ax = plt.subplot(111)
    
    dist_sizes = [len(x) for x in all_distributions]
    pprint.pprint(dist_sizes) 
    dist_means = [np.mean(x) for x in all_distributions]
    dist_max = [np.max(x) for x in all_distributions]
    
    pprint.pprint(dist_means)
        
    # plot a group of boxplots for each scenario
    width=0.3   
    ind = np.arange(len(all_distributions))
    ind_means = np.arange(len(dist_means))
    ind_max = np.arange(len(dist_max))
    pos_0 = ind
    ax.boxplot(all_distributions,0,'', whis=3, positions=pos_0, widths=0.3)
    ax.plot(ind_means, dist_means, marker='d', color='g', linewidth=0.3)
    ax.plot(ind_max, dist_max, marker='x', color='r', linewidth=0.3)
    
    #linestyle
    
    # put up vertical lines - seperating the different scenarios
    for ix, each_scenario in enumerate(SCENARIO_LIST):
        line_xcord = (((len(FNAME_PREFIX_LIST)-1)*(ix+1))+(ix)+0.4)
        plt.axvline(x=line_xcord, linewidth=2, color='k')
        
    labels = [x[1] for x in FNAME_PREFIX_LIST] *len(SCENARIO_LIST)
    xticks = range(0,(len(labels)))
    xticks = [x for x in xticks]    
    ax.set_xticks(xticks)
    ax.set_xticklabels(labels, rotation=75)
    plt.subplots_adjust(bottom=0.25)
        

def plot_TaskResponseTime(use_sched_test_results=False):
    
    all_scenario_all_actypes_distributions = OrderedDict()
    all_distributions = []
    for each_scenario in SCENARIO_LIST:
        #print each_scenario
        for each_fname_prefix in FNAME_PREFIX_LIST:
            if("SCH" in each_fname_prefix[0]) and (use_sched_test_results == True): # if it's a schedulability test, we have to get the analytical results
                # get data            
                fname_prefix = each_scenario[0] + each_fname_prefix[0] + "_"+str(NOC_H)+"_"+str(NOC_W)+"_"
                fname = EXP_DATA_DIR + each_scenario[1] + "/" +fname_prefix + "test__schedtestresults.js"    
                json_data=open(fname)
                flow_data = json.load(json_data)                                
                sorted_task_data_response_times = flow_data[-1]["current_alltasks_wcrt_withdeps_distibution"] # get the sched test as at the last VS admission
                
            else:
                # get data            
                fname_prefix = each_scenario[0] + each_fname_prefix[0] + "_"+str(NOC_H)+"_"+str(NOC_W)+"_"
                fname = EXP_DATA_DIR + each_scenario[1] + "/" +fname_prefix + "test__obuff.js"    
                json_data=open(fname)
                flow_data = json.load(json_data)
                
                # sort them according to id
                sorted_task_data = sorted(flow_data, key=itemgetter('id'))
                sorted_task_data_response_times = [float(x['et']-x['dt']) for x in sorted_task_data]

            all_distributions.append(np.array(sorted_task_data_response_times))
            #print each_fname_prefix
            
            if (each_scenario not in all_scenario_all_actypes_distributions):
                all_scenario_all_actypes_distributions[each_scenario] = OrderedDict()
                all_scenario_all_actypes_distributions[each_scenario][each_fname_prefix[0]] = sorted_task_data_response_times
            else:
                all_scenario_all_actypes_distributions[each_scenario][each_fname_prefix[0]] = sorted_task_data_response_times
         
    # plot all ac types flow-response-times for all ac-types
    fig = plt.figure()
    fig.canvas.set_window_title('plot_TaskResponseTime')
    ax = plt.subplot(111)
    
    dist_sizes = [len(x) for x in all_distributions]
    pprint.pprint(dist_sizes) 
    dist_means = [np.mean(x) for x in all_distributions]
    dist_max = [np.max(x) for x in all_distributions]
    
    pprint.pprint(dist_means)
        
    # plot a group of boxplots for each scenario
    width=0.3   
    ind = np.arange(len(all_distributions))
    ind_means = np.arange(len(dist_means))
    ind_max = np.arange(len(dist_max))
    pos_0 = ind
    ax.boxplot(all_distributions,0,'', whis=3, positions=pos_0, widths=0.3)
    ax.plot(ind_means, dist_means, marker='d', color='g', linewidth=0.3)
    ax.plot(ind_max, dist_max, marker='x', color='r', linewidth=0.3)
    plt.hold(True)
    
    # put up vertical lines - seperating the different scenarios
    for ix, each_scenario in enumerate(SCENARIO_LIST):
        line_xcord = (((len(FNAME_PREFIX_LIST)-1)*(ix+1))+(ix)+0.4)
        plt.axvline(x=line_xcord, linewidth=2, color='k')
        
    labels = [x[1] for x in FNAME_PREFIX_LIST] *len(SCENARIO_LIST)
    xticks = range(0,(len(labels)))
    xticks = [x for x in xticks]    
    ax.set_xticks(xticks)
    ax.set_xticklabels(labels, rotation=75)
    plt.subplots_adjust(bottom=0.25)
  
    


def plot_GoPResponseTime(use_sched_test_results=False):
    
    all_scenario_all_actypes_distributions = OrderedDict()
    all_distributions = []
    for each_scenario in SCENARIO_LIST:
        #print each_scenario
        for each_fname_prefix in FNAME_PREFIX_LIST:
            if("SCH" in each_fname_prefix[0]) and (use_sched_test_results == True): # if it's a schedulability test, we have to get the analytical results
                # get data            
                fname_prefix = each_scenario[0] + each_fname_prefix[0] + "_"+str(NOC_H)+"_"+str(NOC_W)+"_"
                fname = EXP_DATA_DIR + each_scenario[1] + "/" +fname_prefix + "test__schedtestresults.js"    
                json_data=open(fname)
                gop_data = json.load(json_data)                                
                sorted_gop_data_response_times = [x[1] for x in gop_data[-1]["current_stream_cp_wcet"]] # get the sched test as at the last VS admission
                
            else:
                # get data            
                fname_prefix = each_scenario[0] + each_fname_prefix[0] + "_"+str(NOC_H)+"_"+str(NOC_W)+"_"
                fname = EXP_DATA_DIR + each_scenario[1] + "/" +fname_prefix + "test__gopsopbuffsumm.js"    
                json_data=open(fname)
                gop_data = json.load(json_data)
                
                # sort them according to id
                sorted_gop_data = sorted(gop_data.values(), key=itemgetter('gop_unique_id'))
                sorted_gop_data_response_times = [float(x['end_time']-x['start_time']) for x in sorted_gop_data]
                
            if(len(sorted_gop_data_response_times)>0 and (None not in sorted_gop_data_response_times)):                
                all_distributions.append(sorted_gop_data_response_times)
            else:                
                print each_fname_prefix
                print each_scenario
                sys.exit("Error!!")
            #print each_fname_prefix
            
            if (each_scenario not in all_scenario_all_actypes_distributions):
                all_scenario_all_actypes_distributions[each_scenario] = OrderedDict()
                all_scenario_all_actypes_distributions[each_scenario][each_fname_prefix[0]] = sorted_gop_data_response_times
            else:
                all_scenario_all_actypes_distributions[each_scenario][each_fname_prefix[0]] = sorted_gop_data_response_times
         
    # plot all ac types flow-response-times for all ac-types
    fig = plt.figure()
    fig.canvas.set_window_title('plot_GoPResponseTime')
    ax = plt.subplot(111)
    
    dist_sizes = [len(x) for x in all_distributions]
    pprint.pprint(dist_sizes) 
    dist_means = [np.mean(x) for x in all_distributions]
    dist_max = [np.max(x) for x in all_distributions]
    
    pprint.pprint(dist_means)
        
    # plot a group of boxplots for each scenario
    width=0.3   
    ind = np.arange(len(all_distributions))
    ind_means = np.arange(len(dist_means))
    ind_max = np.arange(len(dist_max))
    pos_0 = ind
    ax.boxplot(all_distributions,0,'', whis=3, positions=pos_0, widths=0.3)
    ax.plot(ind_means, dist_means, marker='d', color='g', linewidth=0.3)
    ax.plot(ind_max, dist_max, marker='x', color='r', linewidth=0.3)
    plt.hold(True)
    
    # put up vertical lines - seperating the different scenarios
    for ix, each_scenario in enumerate(SCENARIO_LIST):
        line_xcord = (((len(FNAME_PREFIX_LIST)-1)*(ix+1))+(ix)+0.4)
        plt.axvline(x=line_xcord, linewidth=2, color='k')
        
    labels = [x[1] for x in FNAME_PREFIX_LIST] *len(SCENARIO_LIST)
    xticks = range(0,(len(labels)))
    xticks = [x for x in xticks]    
    ax.set_xticks(xticks)
    ax.set_xticklabels(labels, rotation=75)
    plt.subplots_adjust(bottom=0.25)









#def plot_GoP_Lateness():
#    
#    nonnn_all_nocsizes_distributions = []
#    nn_all_nocsizes_distributions = []
#    nonn_max_goplateness_allnocs = []
#    nonn_max_goplateness_allnocs = []
#    
#    all_gl_variances = []
#    for each_noc_size in NOC_SIZE:
#        noc_h = each_noc_size[0]
#        noc_w = each_noc_size[1]        
#        
#        # get non-nn scheme data    
#        FNAME_PREFIX = "Mapping_10_4_0_"+str(noc_h)+"_"+str(noc_w)+"_"
#        fname = EXP_DATA_DIR + "/" + FNAME_PREFIX + "test__gopsopbuffsumm.js"    
#        json_data=open(fname)
#        nonnn_data = json.load(json_data)
#        
#        # get nn scheme data
#        FNAME_PREFIX = "Mapping_0_0_831_"+str(noc_h)+"_"+str(noc_w)+"_"
#        fname = EXP_DATA_DIR + "/" + FNAME_PREFIX + "test__gopsopbuffsumm.js"    
#        json_data=open(fname)
#        nn_data = json.load(json_data)   
#        
#        # sort them according to id
#        sorted_nonnn_data = sorted(nonnn_data, key=itemgetter('id'))
#        sorted_nn_data = sorted(nn_data, key=itemgetter('id')) 
#        
#        if(len(sorted_nonnn_data) != len(sorted_nn_data)):
#            sys.exit("invalid sizes")             
#        
#        nonnn_data_goplateness_distribution = [each_task['gop_execution_lateness'] for each_task in sorted_nonnn_data]
#        nn_data_goplateness_distribution = [each_task['gop_execution_lateness'] for each_task in sorted_nn_data]
#        
#        nonnn_all_nocsizes_distributions.append(nonnn_data_goplateness_distribution)
#        nn_all_nocsizes_distributions.append(nn_data_goplateness_distribution)
#                       
#        gl_variance_positive= [float(rt_nn-rt_nonnn) for rt_nonnn, rt_nn in zip(nonnn_data_goplateness_distribution, nn_data_goplateness_distribution) 
#                               if float(rt_nn-rt_nonnn)>0.0]  # means nn resptime is longer - bad
#        gl_variance_negative= [float(rt_nn-rt_nonnn) for rt_nonnn, rt_nn in zip(nonnn_data_goplateness_distribution, nn_data_goplateness_distribution) 
#                               if (float(rt_nn-rt_nonnn))<0.0]  # means nn resptime is shorter - good
#        gl_variance= [float(rt_nn-rt_nonnn) for rt_nonnn, rt_nn in zip(nonnn_data_goplateness_distribution, nn_data_goplateness_distribution)] 
#        
#        print "---"
#        print each_noc_size
#        print "rt_variance_positive =" + str(len(gl_variance_positive))
#        print "rt_variance_negative =" + str(len(gl_variance_negative))
#        print "---"
#        all_gl_variances.append(gl_variance)
#        
#        
#    fig = plt.figure()
#    fig.canvas.set_window_title('plot_GoP_Lateness - varmeans')
#    ax = plt.subplot(111)    
#    
#    width=0.3
#    nonnn_means = [np.mean(x) for x in nonnn_all_nocsizes_distributions]
#    nn_means = [np.mean(x) for x in nn_all_nocsizes_distributions]
#    variance_means =  [np.mean(x) for x in all_gl_variances]
#    ind = np.arange(len(nonnn_means))
#    pos_0 = ind
#    pos_1 = ind+width        
#    rects_ol = ax.bar(pos_0, nonnn_means, width, color='r')
#    rects_cl = ax.bar(pos_1, nn_means, width, color='b')
#        
#    fig = plt.figure()
#    fig.canvas.set_window_title('plot_GoP_Lateness-variance')
#    ax = plt.subplot(111)    
#    ind = np.arange(len(all_gl_variances))
#    width=0.8    
#    pos_0 = ind        
#    print len(all_gl_variances)
#    print pos_0
#    box_rt_variance = ax.boxplot(nonnn_all_nocsizes_distributions,0,'', whis=1, positions=pos_0, widths=0.3)
#    box_rt_variance = ax.boxplot(nn_all_nocsizes_distributions,0,'', whis=1, positions=pos_1, widths=0.3)
    
#    
#def plot_task_executioncosts():
#    ol_all_nocsizes_distributions = []
#    cl_all_nocsizes_distributions = []
#    all_rt_variances = []
#    for each_noc_size in NOC_SIZE:
#        noc_h = each_noc_size[0]
#        noc_w = each_noc_size[1]        
#        
#        # get ol data    
#        FNAME_PREFIX = "Mapping_12_4_0_"+str(noc_h)+"_"+str(noc_w)+"_"
#        fname = EXP_DATA_DIR + "/" + FNAME_PREFIX + "test__obuff.js"    
#        json_data=open(fname)
#        ol_data = json.load(json_data)
#        
#        # get cl data
#        FNAME_PREFIX = "Mapping_0_0_830_"+str(noc_h)+"_"+str(noc_w)+"_"
#        fname = EXP_DATA_DIR + "/" + FNAME_PREFIX + "test__obuff.js"    
#        json_data=open(fname)
#        cl_data = json.load(json_data)        
#        
#        ol_data_cc_distribution = [each_task['cc'] for each_task in ol_data]
#        cl_data_cc_distribution = [each_task['cc'] for each_task in cl_data]
#        
#        ol_all_nocsizes_distributions.append(ol_data_cc_distribution)
#        cl_all_nocsizes_distributions.append(cl_data_cc_distribution)
#    
#    fig = plt.figure()
#    fig.canvas.set_window_title('plot_task_executioncosts')
#    ax = plt.subplot(111)    
#    
#    width=0.3
#    ol_means = [np.mean(x) for x in ol_all_nocsizes_distributions]
#    cl_means = [np.mean(x) for x in cl_all_nocsizes_distributions]    
#    ind = np.arange(len(ol_means))
#    pos_0 = ind
#    pos_1 = ind+width        
#    rects_ol = ax.boxplot(ol_all_nocsizes_distributions,0,'', whis=1, positions=pos_0, widths=0.3)
#    rects_cl = ax.boxplot(cl_all_nocsizes_distributions,0,'', whis=1, positions=pos_1, widths=0.3)
#    ax.plot(pos_0, ol_means)
#    ax.plot(pos_1, cl_means)
    
    
       

###################################
#    HELPERS
###################################

            



###################################
#    MAIN
###################################

#plot_FlowsResponseTime(use_sched_test_results=True)
#plot_TaskResponseTime(use_sched_test_results=True)
plot_GoPResponseTime(use_sched_test_results=True)
#plot_task_executioncosts()
#plot_GoP_Lateness()
print "finished"

plt.show()

