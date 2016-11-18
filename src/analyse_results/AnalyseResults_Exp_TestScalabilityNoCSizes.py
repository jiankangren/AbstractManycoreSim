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

NOC_SIZE = [(3,3),(4,4)]

NOC_H = 3
NOC_W = 3

EXP_DATA_DIR = "../experiment_data/hrt_video"

FNAME_PREFIX_LIST = [
                     
                     
                     ]

def plot_FlowsResponseTime():
    
    nn_all_distributions = []
    nonnn_all_distributions = []
    for each_noc_size in NOC_SIZE:
        noc_h = each_noc_size[0]
        noc_w = each_noc_size[1]        
      
        # get non-nn data
        FNAME_PREFIX = "Mapping_10_4_0_"+str(noc_h)+"_"+str(noc_w)+"_"
        fname = EXP_DATA_DIR + "/" + FNAME_PREFIX + "test__flwcompleted.js"    
        json_data=open(fname)
        nonnn_data = json.load(json_data)
        
        # get nn data
        FNAME_PREFIX = "Mapping_0_0_831_"+str(noc_h)+"_"+str(noc_w)+"_"
        fname = EXP_DATA_DIR + "/" + FNAME_PREFIX + "test__flwcompleted.js"    
        json_data=open(fname)
        nn_data = json.load(json_data)
        
        # sort them according to id
        sorted_nonnn_data = sorted(nonnn_data, key=itemgetter('id'))
        sorted_nn_data = sorted(nn_data, key=itemgetter('id')) 
        
        if(len(sorted_nonnn_data) != len(sorted_nn_data)):
            sys.exit("invalid sizes")
        
        nonnn_data_flwresptime_distribution = [x['et']-x['st'] for x in sorted_nonnn_data if x['type'] == 1]        
        nn_data_flwresptime_distribution = [x['et']-x['st'] for x in sorted_nn_data if x['type'] == 1]        
            
        nonnn_all_distributions.append(nonnn_data_flwresptime_distribution)
        nn_all_distributions.append(nn_data_flwresptime_distribution)
    
    
    nonnn_dist_means = [np.mean(x) for x in nonnn_all_distributions]
    nn_dist_means = [np.mean(x) for x in nn_all_distributions]
    
    fig = plt.figure()
    fig.canvas.set_window_title('plot_FlowsResponseTime')
    ax = plt.subplot(111)
    
    
    width = 0.8
    nonnn_boxpos=np.arange(len(nonnn_all_distributions)) 
    nn_boxpos=nonnn_boxpos+width
    
    boxpos_means=np.arange(len(nonnn_dist_means)) 
    
    bp0=ax.boxplot(nonnn_all_distributions,0,'', whis=1, positions=nonnn_boxpos, widths=0.3)
    bp1=ax.boxplot(nn_all_distributions,0,'', whis=1, positions=nn_boxpos, widths=0.3)
         
    labels = [str(x[0]*x[1]) for x in NOC_SIZE]
    xticks = range(0,(len(labels)))
    xticks = [x for x in xticks]    
    ax.set_xticks(xticks)
    ax.set_xticklabels(labels)
        

def plot_task_responsetime():
    
    nonnn_all_nocsizes_distributions = []
    nn_all_nocsizes_distributions = []
    nonn_max_responsetime_allnocs = []
    nonn_max_responsetime_allnocs = []
    
    all_rt_variances = []
    for each_noc_size in NOC_SIZE:
        noc_h = each_noc_size[0]
        noc_w = each_noc_size[1]        
        
        # get non-nn scheme data    
        FNAME_PREFIX = "NOAC_LUM_"+str(SimParams.NOC_H)+"_"+str(SimParams.NOC_W)+"_"
        fname = EXP_DATA_DIR + "/" + FNAME_PREFIX + "test__obuff.js"    
        json_data=open(fname)
        nonnn_data = json.load(json_data)
        
        # get nn scheme data
        FNAME_PREFIX = "Mapping_0_0_831_"+str(noc_h)+"_"+str(noc_w)+"_"
        fname = EXP_DATA_DIR + "/" + FNAME_PREFIX + "test__obuff.js"    
        json_data=open(fname)
        nn_data = json.load(json_data)        
        
        # sort them according to id
        sorted_nonnn_data = sorted(nonnn_data, key=itemgetter('id'))
        sorted_nn_data = sorted(nn_data, key=itemgetter('id')) 
        
        if(len(sorted_nonnn_data) != len(sorted_nn_data)):
            sys.exit("invalid sizes")
        
        nonnn_data_resp_time_distribution = [each_task['et']-each_task['dt'] for each_task in sorted_nonnn_data]
        nn_data_resp_time_distribution = [each_task['et']-each_task['dt'] for each_task in sorted_nn_data]
        
        nonnn_all_nocsizes_distributions.append(nonnn_data_resp_time_distribution)
        nn_all_nocsizes_distributions.append(nn_data_resp_time_distribution)
                       
        rt_variance_positive= [float(rt_nn-rt_nonnn) for rt_nonnn, rt_nn in zip(nonnn_data_resp_time_distribution, nn_data_resp_time_distribution) 
                               if float(rt_nn-rt_nonnn)>0.0]  # means nn resptime is longer - bad
        rt_variance_negative= [float(rt_nn-rt_nonnn) for rt_nonnn, rt_nn in zip(nonnn_data_resp_time_distribution, nn_data_resp_time_distribution) 
                               if (float(rt_nn-rt_nonnn))<0.0]  # means nn resptime is shorter - good
        rt_variance= [float(rt_nn-rt_nonnn) for rt_nonnn, rt_nn in zip(nonnn_data_resp_time_distribution, nn_data_resp_time_distribution)] 
        
        print "---"
        print each_noc_size
        print "rt_variance_positive =" + str(len(rt_variance_positive))
        print "rt_variance_negative =" + str(len(rt_variance_negative))
        print "---"
        all_rt_variances.append(rt_variance)
        
    ## plot means
    fig = plt.figure()
    fig.canvas.set_window_title('plot_task_responsetime - means')
    ax = plt.subplot(111)  
    width=0.3
    nonnn_means = [np.mean(x) for x in nonnn_all_nocsizes_distributions]
    nn_means = [np.mean(x) for x in nn_all_nocsizes_distributions]
    variance_means =  [np.mean(x) for x in all_rt_variances]
    ind = np.arange(len(nonnn_means))
    pos_0 = ind
    pos_1 = ind+width        
    rects_ol = ax.bar(pos_0, variance_means, width, color='r')
    #rects_cl = ax.bar(pos_1, cl_means, width, color='b')
    
    ## plot max
    fig = plt.figure()
    fig.canvas.set_window_title('plot_task_responsetime - max')
    ax = plt.subplot(111)  
    width=0.3
    nonnn_max = [np.max(x) for x in nonnn_all_nocsizes_distributions]
    nn_max = [np.max(x) for x in nn_all_nocsizes_distributions]    
    ind = np.arange(len(nonnn_max))
    pos_0 = ind
    pos_1 = ind+width        
    rects_ol = ax.bar(pos_0, nonnn_max, width, color='r')
    rects_cl = ax.bar(pos_1, nn_max, width, color='b')
        
    fig = plt.figure()
    fig.canvas.set_window_title('plot_task_responsetime-distributions')
    ax = plt.subplot(111)    
    ind = np.arange(len(all_rt_variances))
    width=0.3    
    pos_0 = ind 
    pos_1 = ind+width       
    print len(all_rt_variances)
    print pos_0
    box_rt_variance = ax.boxplot(nonnn_all_nocsizes_distributions,0,'', whis=1, positions=pos_0, widths=width)
    box_rt_variance = ax.boxplot(nn_all_nocsizes_distributions,0,'', whis=1, positions=pos_1, widths=width)
    


def plot_GoP_Lateness():
    
    nonnn_all_nocsizes_distributions = []
    nn_all_nocsizes_distributions = []
    nonn_max_goplateness_allnocs = []
    nonn_max_goplateness_allnocs = []
    
    all_gl_variances = []
    for each_noc_size in NOC_SIZE:
        noc_h = each_noc_size[0]
        noc_w = each_noc_size[1]        
        
        # get non-nn scheme data    
        FNAME_PREFIX = "Mapping_10_4_0_"+str(noc_h)+"_"+str(noc_w)+"_"
        fname = EXP_DATA_DIR + "/" + FNAME_PREFIX + "test__gopsopbuffsumm.js"    
        json_data=open(fname)
        nonnn_data = json.load(json_data)
        
        # get nn scheme data
        FNAME_PREFIX = "Mapping_0_0_831_"+str(noc_h)+"_"+str(noc_w)+"_"
        fname = EXP_DATA_DIR + "/" + FNAME_PREFIX + "test__gopsopbuffsumm.js"    
        json_data=open(fname)
        nn_data = json.load(json_data)   
        
        # sort them according to id
        sorted_nonnn_data = sorted(nonnn_data, key=itemgetter('id'))
        sorted_nn_data = sorted(nn_data, key=itemgetter('id')) 
        
        if(len(sorted_nonnn_data) != len(sorted_nn_data)):
            sys.exit("invalid sizes")             
        
        nonnn_data_goplateness_distribution = [each_task['gop_execution_lateness'] for each_task in sorted_nonnn_data]
        nn_data_goplateness_distribution = [each_task['gop_execution_lateness'] for each_task in sorted_nn_data]
        
        nonnn_all_nocsizes_distributions.append(nonnn_data_goplateness_distribution)
        nn_all_nocsizes_distributions.append(nn_data_goplateness_distribution)
                       
        gl_variance_positive= [float(rt_nn-rt_nonnn) for rt_nonnn, rt_nn in zip(nonnn_data_goplateness_distribution, nn_data_goplateness_distribution) 
                               if float(rt_nn-rt_nonnn)>0.0]  # means nn resptime is longer - bad
        gl_variance_negative= [float(rt_nn-rt_nonnn) for rt_nonnn, rt_nn in zip(nonnn_data_goplateness_distribution, nn_data_goplateness_distribution) 
                               if (float(rt_nn-rt_nonnn))<0.0]  # means nn resptime is shorter - good
        gl_variance= [float(rt_nn-rt_nonnn) for rt_nonnn, rt_nn in zip(nonnn_data_goplateness_distribution, nn_data_goplateness_distribution)] 
        
        print "---"
        print each_noc_size
        print "rt_variance_positive =" + str(len(gl_variance_positive))
        print "rt_variance_negative =" + str(len(gl_variance_negative))
        print "---"
        all_gl_variances.append(gl_variance)
        
        
    fig = plt.figure()
    fig.canvas.set_window_title('plot_GoP_Lateness - varmeans')
    ax = plt.subplot(111)    
    
    width=0.3
    nonnn_means = [np.mean(x) for x in nonnn_all_nocsizes_distributions]
    nn_means = [np.mean(x) for x in nn_all_nocsizes_distributions]
    variance_means =  [np.mean(x) for x in all_gl_variances]
    ind = np.arange(len(nonnn_means))
    pos_0 = ind
    pos_1 = ind+width        
    rects_ol = ax.bar(pos_0, nonnn_means, width, color='r')
    rects_cl = ax.bar(pos_1, nn_means, width, color='b')
        
    fig = plt.figure()
    fig.canvas.set_window_title('plot_GoP_Lateness-variance')
    ax = plt.subplot(111)    
    ind = np.arange(len(all_gl_variances))
    width=0.8    
    pos_0 = ind        
    print len(all_gl_variances)
    print pos_0
    box_rt_variance = ax.boxplot(nonnn_all_nocsizes_distributions,0,'', whis=1, positions=pos_0, widths=0.3)
    box_rt_variance = ax.boxplot(nn_all_nocsizes_distributions,0,'', whis=1, positions=pos_1, widths=0.3)
    
    
def plot_task_executioncosts():
    ol_all_nocsizes_distributions = []
    cl_all_nocsizes_distributions = []
    all_rt_variances = []
    for each_noc_size in NOC_SIZE:
        noc_h = each_noc_size[0]
        noc_w = each_noc_size[1]        
        
        # get ol data    
        FNAME_PREFIX = "Mapping_12_4_0_"+str(noc_h)+"_"+str(noc_w)+"_"
        fname = EXP_DATA_DIR + "/" + FNAME_PREFIX + "test__obuff.js"    
        json_data=open(fname)
        ol_data = json.load(json_data)
        
        # get cl data
        FNAME_PREFIX = "Mapping_0_0_830_"+str(noc_h)+"_"+str(noc_w)+"_"
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
    
    
       

###################################
#    HELPERS
###################################

            



###################################
#    MAIN
###################################

#plot_FlowsResponseTime()
plot_task_responsetime()
#plot_task_executioncosts()
#plot_GoP_Lateness()
print "finished"

plt.show()

