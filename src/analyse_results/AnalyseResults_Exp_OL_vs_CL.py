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


#NOC_SIZE = [(2,2), (3,3), (4,4), (5,5), (6,6), (7,7), (8,8), (9,9), (10,10)]
#NOC_SIZE = [(5,5)]
NOC_SIZE = [(2,2), (3,3), (4,4), (5,5), (6,6), (7,7)]

EXP_DATA_DIR = "../experiment_data/closedloop_vs_openloop"

def plot_CL_signallingFlows():
    
    all_distributions = []
    for each_noc_size in NOC_SIZE:
        noc_h = each_noc_size[0]
        noc_w = each_noc_size[1]        
      
        # get cl data
        FNAME_PREFIX = "CLwoIB_"+str(noc_h)+"_"+str(noc_w)+"_"
        fname = EXP_DATA_DIR + "/" + FNAME_PREFIX + "test__flwcompleted.js"    
        json_data=open(fname)
        cl_data = json.load(json_data)
        
        cl_data_flwresptime_distribution = [x['et']-x['st'] for x in cl_data if x['type'] != 1]        
        all_distributions.append(cl_data_flwresptime_distribution)
    
    dist_means = [np.mean(x) for x in all_distributions]
    
    fig = plt.figure()
    fig.canvas.set_window_title('plot_CL_signallingFlows')
    ax = plt.subplot(111)
       
    boxpos=np.arange(len(all_distributions)) 
    boxpos_means=np.arange(len(all_distributions)) 
    bp=ax.boxplot(all_distributions,0,'', whis=1, positions=boxpos, widths=0.8)
    ax.plot(boxpos, dist_means, marker='d', color='g')    
    labels = [str(x[0]*x[1]) for x in NOC_SIZE]
    xticks = range(0,(len(labels)))
    xticks = [x for x in xticks]    
    ax.set_xticks(xticks)
    ax.set_xticklabels(labels)
    plt.grid(True)
        

def plot_task_responsetime():
    
    ol_all_nocsizes_distributions = []
    cl_all_nocsizes_distributions = []
    all_rt_variances = []
    for each_noc_size in NOC_SIZE:
        noc_h = each_noc_size[0]
        noc_w = each_noc_size[1]        
        
        print noc_h
        print noc_w
        
        # get ol data    
        FNAME_PREFIX = "OL_"+str(noc_h)+"_"+str(noc_w)+"_"
        fname = EXP_DATA_DIR + "/" + FNAME_PREFIX + "test__obuff.js"    
        json_data=open(fname)
        ol_data = json.load(json_data)
        
        # get cl data
        FNAME_PREFIX = "CLwoIB_"+str(noc_h)+"_"+str(noc_w)+"_"
        fname = EXP_DATA_DIR + "/" + FNAME_PREFIX + "test__obuff.js"    
        json_data=open(fname)
        cl_data = json.load(json_data)   
        
        # sort them according to id
        sorted_ol_data = sorted(ol_data, key=itemgetter('id'))
        sorted_cl_data = sorted(cl_data, key=itemgetter('id')) 
        
        print len(sorted_ol_data) == len(sorted_cl_data)
                     
        ol_data_resp_time_distribution = [each_task['et']-each_task['dt'] for each_task in sorted_ol_data]
        cl_data_resp_time_distribution = [each_task['et']-each_task['dt'] for each_task in sorted_cl_data]
        
        ol_all_nocsizes_distributions.append(ol_data_resp_time_distribution)
        cl_all_nocsizes_distributions.append(cl_data_resp_time_distribution)
                       
        rt_variance_positive= [rt_cl-rt_ol for rt_ol, rt_cl in zip(ol_data_resp_time_distribution, cl_data_resp_time_distribution) if (rt_cl-rt_ol)>0.0]
        rt_variance_negative= [rt_cl-rt_ol for rt_ol, rt_cl in zip(ol_data_resp_time_distribution, cl_data_resp_time_distribution) if (rt_cl-rt_ol)<0.0]
        rt_variance= [rt_cl-rt_ol for rt_ol, rt_cl in zip(ol_data_resp_time_distribution, cl_data_resp_time_distribution)]        
        
#        for ol,cl in zip(sorted_ol_data, sorted_cl_data):
#            rt_v = (cl['et']-cl['dt']) - (ol['et']-ol['dt'])
#            if(rt_v<0):
#                print "---"
#                print cl['id']
#                print ol['id']
#                
#                print ".."
#                print "%.15f" % cl['dt']
#                print "%.15f" % cl['et']
#                print ".."
#                print "%.15f" % ol['dt']
#                print "%.15f" % ol['et']
#                print ".."
#                print rt_v
#                print cl['type']
#                print "---"
#                sys.exit()
        
        
        #pprint.pprint(rt_variance)
        
        print "---"
        print each_noc_size
        print "rt_variance_positive =" + str(len(rt_variance_positive))
        print "rt_variance_negative =" + str(len(rt_variance_negative))
        print "---"
        all_rt_variances.append(rt_variance)
    
        #sys.exit()
        
    # mean variance  - bar plots 
    fig = plt.figure()
    fig.canvas.set_window_title('plot_task_responsetime - mean variance')
    ax = plt.subplot(111)
    width=0.3    
    variance_means =  [np.mean(x) for x in all_rt_variances]
    ind = np.arange(len(variance_means))
    pos_0 = ind
    pos_1 = ind+width        
    rects_ol = ax.bar(pos_0, variance_means, width, color='r')
    #rects_cl = ax.bar(pos_1, cl_means, width, color='b')
    labels = [str(x[0]*x[1]) for x in NOC_SIZE]
    xticks = range(0,(len(labels)))
    xticks = [x for x in xticks]    
    ax.set_xticks(xticks)
    ax.set_xticklabels(labels)
    plt.grid(True)
    
    # max variance  - bar plots 
    fig = plt.figure()
    fig.canvas.set_window_title('plot_task_responsetime - max variance')
    ax = plt.subplot(111)
    width=0.3
    variance_max =  [np.max(x) for x in all_rt_variances]
    ind = np.arange(len(variance_max))
    pos_0 = ind
    pos_1 = ind+width        
    rects_ol = ax.bar(pos_0, variance_max, width, color='r')
    #rects_cl = ax.bar(pos_1, cl_means, width, color='b')
    labels = [str(x[0]*x[1]) for x in NOC_SIZE]
    xticks = range(0,(len(labels)))
    xticks = [x for x in xticks]    
    ax.set_xticks(xticks)
    ax.set_xticklabels(labels)
    plt.grid(True)    
        
    # max rt  - bar plots 
    fig = plt.figure()
    fig.canvas.set_window_title('plot_task_responsetime - max resptime')
    ax = plt.subplot(111)
    width=0.3
    ol_rt_max =  [np.max(x) for x in ol_all_nocsizes_distributions]
    cl_rt_max =  [np.max(x) for x in cl_all_nocsizes_distributions]
    ind = np.arange(len(ol_rt_max))
    pos_0 = ind
    pos_1 = ind+width        
    rects_ol = ax.bar(pos_0, ol_rt_max, width, color='r', label='ol_rt_max')
    rects_cl = ax.bar(pos_1, cl_rt_max, width, color='b', label='cl_rt_max')    
    labels = [str(x[0]*x[1]) for x in NOC_SIZE]
    xticks = range(0,(len(labels)))
    xticks = [x for x in xticks]    
    ax.set_xticks(xticks)
    ax.set_xticklabels(labels)
    plt.grid(True)
    leg = plt.legend()
    leg.draggable()
    
        
    # cumulative resp time  - bar plots 
    fig = plt.figure()
    fig.canvas.set_window_title('plot_task_responsetime - cumulative resptime')
    ax = plt.subplot(111)
    width=0.3
    ol_rt_cumsum =  [np.sum(x) for x in ol_all_nocsizes_distributions]
    cl_rt_cumsum =  [np.sum(x) for x in cl_all_nocsizes_distributions]
    
    cumsum_variance = [np.sum(cl) - np.sum(ol) for ol, cl in zip(ol_all_nocsizes_distributions, cl_all_nocsizes_distributions)]
        
    ind = np.arange(len(ol_rt_max))
    pos_0 = ind
    pos_1 = ind+width        
    #rects_ol = ax.bar(pos_0, ol_rt_cumsum, width, color='r', label='ol_rt_cumsum')
    #rects_cl = ax.bar(pos_1, cl_rt_cumsum, width, color='b', label='cl_rt_cumsum')    
    rects_var = ax.bar(pos_0, cumsum_variance, width, color='b', label='cumsum_variance')
    
    labels = [str(x[0]*x[1]) for x in NOC_SIZE]
    xticks = range(0,(len(labels)))
    xticks = [x for x in xticks]    
    ax.set_xticks(xticks)
    ax.set_xticklabels(labels)
    plt.grid(True)
    leg = plt.legend()
    leg.draggable()
        
    
    # response time distribution, box plots
    fig = plt.figure()
    fig.canvas.set_window_title('plot_task_responsetime distributions')
    ax = plt.subplot(111)    
    ind = np.arange(len(all_rt_variances))
    width=0.3    
    pos_0 = ind
    pos_1 = ind+width        
    print len(all_rt_variances)
    print pos_0
    box_rt_variance = ax.boxplot(ol_all_nocsizes_distributions,0,'', whis=1, positions=pos_0, widths=0.3)
    box_rt_variance = ax.boxplot(cl_all_nocsizes_distributions,0,'', whis=1, positions=pos_1, widths=0.3)
    #lines = ax.plot(pos_0, variance_means, color='g', marker='d', markersize=10, linestyle='--')
    labels = [str(x[0]*x[1]) for x in NOC_SIZE]
    xticks = range(0,(len(labels)))
    xticks = [x for x in xticks]    
    ax.set_xticks(xticks)
    ax.set_xticklabels(labels)
    plt.grid(True)

    
    # response time variance distributions, box plots
    fig = plt.figure()
    fig.canvas.set_window_title('plot_task_responsetime-variance distribution')
    ax = plt.subplot(111)    
    ind = np.arange(len(all_rt_variances))
    width=0.3    
    pos_0 = ind
    pos_1 = ind+width        
    print len(all_rt_variances)
    print pos_0
    box_rt_variance = ax.boxplot(all_rt_variances,0,'', whis=1, positions=pos_0, widths=0.3)    
    #lines = ax.plot(pos_0, variance_means, color='g', marker='d', markersize=10, linestyle='--')
        
#    for x,d in zip(pos_0, all_rt_variances):
#        plt.scatter(np.ones(len(d))*x, d, marker='x', alpha=0.2)
#        plt.hold(True)    
    
    labels = [str(x[0]*x[1]) for x in NOC_SIZE]
    xticks = range(0,(len(labels)))
    xticks = [x for x in xticks]    
    ax.set_xticks(xticks)
    ax.set_xticklabels(labels)
    plt.grid(True)

    
    

def plot_task_executioncosts():
    ol_all_nocsizes_distributions = []
    cl_all_nocsizes_distributions = []
    all_rt_variances = []
    for each_noc_size in NOC_SIZE:
        noc_h = each_noc_size[0]
        noc_w = each_noc_size[1]        
        
        # get ol data    
        FNAME_PREFIX = "OL_"+str(noc_h)+"_"+str(noc_w)+"_"
        fname = EXP_DATA_DIR + "/" + FNAME_PREFIX + "test__obuff.js"    
        json_data=open(fname)
        ol_data = json.load(json_data)
        
        # get cl data
        FNAME_PREFIX = "CLwoIB_"+str(noc_h)+"_"+str(noc_w)+"_"
        fname = EXP_DATA_DIR + "/" + FNAME_PREFIX + "test__obuff.js"    
        json_data=open(fname)
        cl_data = json.load(json_data)        
        
        ol_data_cc_distribution = [each_task['cc'] for each_task in ol_data]
        cl_data_cc_distribution = [each_task['cc'] for each_task in cl_data]
        
        ol_all_nocsizes_distributions.append(ol_data_cc_distribution)
        cl_all_nocsizes_distributions.append(cl_data_cc_distribution)
    
    fig = plt.figure()
    fig.canvas.set_window_title('plot_task_executioncosts')
    ax = plt.subplot(111)    
    
    width=0.3
    ol_means = [np.mean(x) for x in ol_all_nocsizes_distributions]
    cl_means = [np.mean(x) for x in cl_all_nocsizes_distributions]    
    ind = np.arange(len(ol_means))
    pos_0 = ind
    pos_1 = ind+width        
    rects_ol = ax.boxplot(ol_all_nocsizes_distributions,0,'', whis=1, positions=pos_0, widths=0.3)
    rects_cl = ax.boxplot(cl_all_nocsizes_distributions,0,'', whis=1, positions=pos_1, widths=0.3)
    ax.plot(pos_0, ol_means)
    ax.plot(pos_1, cl_means)
    


def plot_GoP_responsetime():
    
    gop_lateness_distribution_rmoff = []
    gop_lateness_distribution_rmon = []
    gop_rt_distribution_rmoff = []
    gop_rt_distribution_rmon = []
    
    all_gopL_distributions = []
    
    ol_all_nocsizes_distributions = []
    cl_all_nocsizes_distributions = []
    
    for each_noc_size in NOC_SIZE:
        noc_h = each_noc_size[0]
        noc_w = each_noc_size[1]        
        
        print noc_h
        print noc_w
        
        # get ol data    
        FNAME_PREFIX = "OL_"+str(noc_h)+"_"+str(noc_w)+"_"
        fname = EXP_DATA_DIR + "/" + FNAME_PREFIX + "test__gopsopbuffsumm.js"    
        json_data=open(fname)
        ol_data = json.load(json_data)
        
        # get cl data
        FNAME_PREFIX = "CLwoIB_"+str(noc_h)+"_"+str(noc_w)+"_"
        fname = EXP_DATA_DIR + "/" + FNAME_PREFIX + "test__gopsopbuffsumm.js"    
        json_data=open(fname)
        cl_data = json.load(json_data)   
        
        # sort them according to id
        sorted_ol_data = sorted(ol_data.values(), key=itemgetter('gop_unique_id'))
        sorted_cl_data = sorted(cl_data.values(), key=itemgetter('gop_unique_id')) 
        
        variance = [cl['tt_wrt_dt'] - ol['tt_wrt_dt'] for ol, cl in zip(sorted_ol_data, sorted_cl_data)]
        
#        for ol, cl in zip(sorted_ol_data, sorted_cl_data):
#            print "==="
#            print cl['gop_unique_id']
#            print ol['gop_unique_id']
#            print cl['tt_wrt_dt'] - ol['tt_wrt_dt']  
#            print "==="
#        
        
        pprint.pprint(variance)
        
        #sys.exit() 
        print len(sorted_ol_data) == len(sorted_cl_data)
                     
        ol_data_resp_time_distribution = [g['tt_wrt_dt'] for g in sorted_ol_data]
        cl_data_resp_time_distribution = [g['tt_wrt_dt'] for g in sorted_cl_data]
        
        ol_all_nocsizes_distributions.append(ol_data_resp_time_distribution)
        cl_all_nocsizes_distributions.append(cl_data_resp_time_distribution)
    
        print "----------------"
        
    # cumulative resp time  - bar plots 
    fig = plt.figure()
    fig.canvas.set_window_title('plot_GoP_responsetime - cumulative resptime')
    ax = plt.subplot(111)
    width=0.3
    ol_goprt_cumsum =  [np.sum(x) for x in ol_all_nocsizes_distributions]
    cl_goprt_cumsum =  [np.sum(x) for x in cl_all_nocsizes_distributions]
    
    cumsum_variance = [np.sum(cl) - np.sum(ol) for ol, cl in zip(ol_all_nocsizes_distributions, cl_all_nocsizes_distributions)]
        
    ind = np.arange(len(ol_goprt_cumsum))
    pos_0 = ind
    pos_1 = ind+width
    rects_var = ax.bar(pos_0, cumsum_variance, width, color='b', label='gop_cumsum_variance')
    
    labels = [str(x[0]*x[1]) for x in NOC_SIZE]
    xticks = range(0,(len(labels)))
    xticks = [x for x in xticks]    
    ax.set_xticks(xticks)
    ax.set_xticklabels(labels)
    plt.grid(True)
    leg = plt.legend()
    leg.draggable()
    
    
    


      

###################################
#    HELPERS
###################################

            



###################################
#    MAIN
###################################


#plot_CL_signallingFlows()
plot_task_responsetime()
#plot_GoP_responsetime()
#plot_task_executioncosts()

print "finished"

plt.show()

