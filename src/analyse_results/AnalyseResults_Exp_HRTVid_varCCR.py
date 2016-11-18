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

#from util_scripts.ccr_ranges import get_properties_fixed_ccs_fixed_ccr_range

MAX_NUM_GOPS_IN_VS = SimParams.WFGEN_MAX_GOPS_PER_VID
NOC_H = 3
NOC_W = 3

EXP_DATA_DIR = "../experiment_data/hrt_video/util_vs_sched_variable_ccr/"

global_types_of_tests = [
                      
                    ## Deterministic - AC ##

                    #{'ac':12, 'mp':0, 'pr':4, 'cmb':840 }, # determ, lumm
                    
                    {'ac':12, 'mp':0, 'pr':4, 'cmb':841 , 'lbl': "IPC"}, # determ, improved
                    {'ac':12, 'mp':0, 'pr':4, 'cmb':842 , 'lbl': "LWCRS"}, # determ, improved                    
                    {'ac':12, 'mp':0, 'pr':4, 'cmb':833 , 'lbl': "PP"}, # determ, improved
                    
                               
                    {'ac':12, 'mp':10, 'pr':4, 'cmb':0 , 'lbl': "LU"}, # determ, improved
                    {'ac':12, 'mp':12, 'pr':4, 'cmb':0 , 'lbl': "LM"}, # determ, improved
                    
                    {'ac':12, 'mp':0, 'pr':4, 'cmb':834 , 'lbl': "BN"}, # determ, improved
                    #{'ac':12, 'mp':0, 'pr':4, 'cmb':834 , 'lbl': "BN-v2"}, # determ, improved
                    
                      ]


RANDOM_SEED_LIST = \
 [81665, 33749, 43894, 26358, 80505, \
  83660, 22817, 70263, 29917, 26044, \
  5558,  76891, 22250, 42198, 18065, \
  74076, 98652, 21149, 50399, 64217, \
  44117, 57824, 42267, 83200, 99108, \
  95928, 53864, 44289, 77379, 80521, \
  88117, 23327, 73337, 94064, 31982, \
  6878, 66093, 69541]

# [21149,
# 22250,
# 23327,
# 26044,
# 26358,
# 29917,
# 42267,
# 43894,
# 64217,
# 73337,
# 77379,
# 80505,
# 83660,
# 88117,
# 94064,
# 98652]

def plot_GoPResponseTime(use_ccr_file_input=True):
    
    all_test_types_allccrs_gopL = OrderedDict()
        
    # obtain ccr values
    #ccr_range = [round(x,4) for x in np.linspace(0.001, 2.0, 100)]    
    #ccr_entries = get_properties_fixed_ccs_fixed_ccr_range(ccs_range, ccr_range, enable_print = False)    
    #sorted_ccr_entries = sorted(ccr_entries, key=lambda k: k['ccr'])
    
    fname = '../util_scripts/ccr_list_output.js'    
    json_data=open(fname)
    ccr_data = json.load(json_data)
    sorted_ccr_entries = sorted(ccr_data, key=lambda k: k['ccr'])
    ccr_range = [x['ccr'] for x in sorted_ccr_entries]
    #ccr_range = [round(x['ccr'], 6) for x in sorted_ccr_entries]
    ccs_range = [round(x['ccs'], 4) for x in sorted_ccr_entries]
    
    for each_seed in RANDOM_SEED_LIST:
        
        print each_seed
        
        for each_test_type in global_types_of_tests: 
            exp_key = each_test_type['lbl']
            all_test_types_allccrs_gopL[exp_key] = OrderedDict()
            
            print exp_key
            
            for each_ccr_entry in ccr_range:
                
                #print each_ccr_entry
                
                if(each_ccr_entry not in all_test_types_allccrs_gopL[exp_key]):
                    all_test_types_allccrs_gopL[exp_key][each_ccr_entry] = []
                
                subdir = "seed_" + str(each_seed)  + "/"              
                subdir = subdir+"ccr_" + str(round(each_ccr_entry, 4)) + "/"
                
                # get data for no-ac, LUM
                prefix = "HRTVid_" + \
                             "AC" + str(each_test_type['ac']) + "_" + \
                             "MP" + str(each_test_type['mp']) + "_" + \
                             "PR" + str(each_test_type['pr']) + "_" + \
                             "CMB" + str(each_test_type['cmb']) + "_"                                                      
                             
                fname_prefix = EXP_DATA_DIR+subdir+prefix+str(SimParams.NOC_H)+"_"+str(SimParams.NOC_W)+"_"
                
                ## get utilisation value
                fname = fname_prefix+"test__gopsopbuffsumm.js"    
                json_data=open(fname)
                gop_data = json.load(json_data)
                
                # save data
                gop_lateness_allgops =  [x['gop_execution_lateness'] for x in gop_data.values()]
                all_test_types_allccrs_gopL[exp_key][each_ccr_entry].extend(gop_lateness_allgops)
                
                
    ## now we plot
    fig = plt.figure()
    fig.canvas.set_window_title('plot_GoPResponseTime')
    ax = plt.subplot(111)
    
    #f, (ax1, ax2) = plt.subplots(2, 1, sharex=True)    
    i = 0
    legend_bars = []    
    cols = plt.get_cmap('jet')(np.linspace(0, 1.0, len(all_test_types_allccrs_gopL)))
    markers = ["1", "2", "3", "4", "8", "D", "o", "x", "s", "*", "+"]    
    norm_min = 0.0
    norm_max = 0.0
    for expkey, each_exp in all_test_types_allccrs_gopL.iteritems():
        print expkey
        
        #ccr_list = [x['ccr'] for x in each_exp]  
        ccr_list = each_exp.keys()
        mean_gopL = [np.mean(v) for k,v in each_exp.iteritems()]
        max_gopL = [np.max(v) for k,v in each_exp.iteritems()]
        
        min_mean_gopL = np.min(mean_gopL)
        max_mean_gopL = np.max(mean_gopL)
        
        if(min_mean_gopL < norm_min):
            norm_min = min_mean_gopL
        if(max_mean_gopL > norm_max):
            norm_max = max_mean_gopL     
           
        ax.plot(ccr_list, mean_gopL, marker='x', color=cols[i], linewidth=0.3, label=expkey)
        
        i+=1            
    labels = [str(x) for x in ccr_list]
    print labels
    plt.grid(True)
    
    l  = plt.legend()
    l.draggable()
    
    ## NORMALISED
    i = 0
    fig2 = plt.figure()
    fig2.canvas.set_window_title('plot_GoPResponseTime-normalised')
    ax2 = plt.subplot(111)
    for expkey, each_exp in all_test_types_allccrs_gopL.iteritems():
        print expkey
        
        #ccr_list = [x['ccr'] for x in each_exp]  
        ccr_list = each_exp.keys()
        mean_gopL = [np.mean(v) for k,v in each_exp.iteritems()]
        max_gopL = [np.max(v) for k,v in each_exp.iteritems()]
        
        normalised_result  = [(x-norm_min)/(norm_max-norm_min) for x in mean_gopL]
           
        ax2.plot(ccr_list, normalised_result, marker='x', color=cols[i], linewidth=1.0, label=expkey)
        
        i+=1   
    ax2.set_ylabel('Normalised job lateness', fontsize=20)
    ax2.set_xlabel(r'$CCR_W$', fontsize=20)        
    plt.tick_params(axis='both', which='major', labelsize=16)
    plt.tick_params(axis='both', which='minor', labelsize=16)         
    labels = [str(x) for x in ccr_list]
    print labels
    plt.grid(True)    
    l  = plt.legend()
    l.draggable()
    
    
    
    
    
    
    

    ## plot boxplots
#     fig = plt.figure()
#     fig.canvas.set_window_title('plot_GoPResponseTime')
#     ax = plt.subplot(111)
#     
#     ccr_list = all_test_types_allccrs_gopL['IPC'].keys()
#     ipc_data = [v for k,v in all_test_types_allccrs_gopL['IPC'].iteritems()]
#     lwcrs_data = [v for k,v in all_test_types_allccrs_gopL['LWCRS'].iteritems()]
#     
#     width = 0.3
#     ind = np.arange(len(ipc_data))
#     pos_0 = ind
#     pos_1 = ind+width
#     
#     bp1 = ax.boxplot(ipc_data,0,'', whis=1, positions=pos_0, widths=0.3)
#     bp2 = ax.boxplot(lwcrs_data,0,'', whis=1, positions=pos_1, widths=0.3)
#     plt.setp(bp1['boxes'], color='b')   
#     plt.setp(bp2['boxes'], color='r')
#     plt.xticks(np.arange(len(ccr_list)), [str(np.round(x,1)) for x in ccr_list], fontsize=8)
    
        
        
        
    
    




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
plot_GoPResponseTime()
#plot_task_executioncosts()
#plot_GoP_Lateness()
print "finished"

plt.show()

