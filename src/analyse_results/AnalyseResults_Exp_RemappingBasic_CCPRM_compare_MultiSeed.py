import sys, os, csv, pprint, math

from collections import OrderedDict
import numpy as np
import random
import shutil
import math


## uncomment when running under CLI only version ##
#import matplotlib
#matplotlib.use('Agg')

import matplotlib
matplotlib.use('Qt4Agg')

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
#plt.style.use('ggplot')

import scipy.stats


from matplotlib import mlab
from itertools import cycle # for automatic markers
import json
from operator import itemgetter
from matplotlib.colors import colorConverter
#from aifc import data

import seaborn.apionly as sns

plt.style.use('bmh_rosh')

#from util_scripts.plot_workflows import wf_data

NUM_WORKFLOWS = range(8, 19, 1)
#NUM_WORKFLOWS = [9]
#NUM_NODES = [2,4,8,16,32]
NUM_NODES = 9
NOC_XY = [(2,1), (2,2), (2,4), (2,8), (2,16)]


IBUFF_TASKS_LATENESS_RATIO_RANGE    = [0.3, 0.7]
TQ_TASKS_LATENESS_RATIO_RANGE       = [0.3, 0.7]        

SEED = 26358

#EXP_DATA_DIR = "Z:/MCASim/experiment_data/remapping_psbased_mmcoff"
#EXP_DATA_DIR = "Z:/MCASim/experiment_data/remapping_psbased"
#EXP_DATA_DIR = "Z:/MCASim/experiment_data/remapping_randombased/neighbour"
#EXP_DATA_DIR = "Z:/MCASim/experiment_data/remapping_randombased"
EXP_DATA_DIR = "Z:/MCASim/experiment_data/remapping_ccpbased"
#EXP_DATA_DIR = "Z:/MCASim/experiment_data/remapping_ccpbased_single_cluster"
#EXP_DATA_DIR = "Z:/MCASim/experiment_data/remapping_central_dynamic"

#EXP_DATA_DIR = "../experiment_data/remapping_psbased"

#local
#PSRM_EXP_DATA_DIR = "Z:/MCASim/experiment_data/remapping_psbased"
#CCPRM_EXP_DATA_DIR = "Z:/MCASim/experiment_data/remapping_ccpbased"
#RANDNEIGHRM_EXP_DATA_DIR = "Z:/MCASim/experiment_data/remapping_randombased/neighbour"
#RAND_EXP_DATA_DIR = "Z:/MCASim/experiment_data/remapping_randombased"

# server
PSRM_EXP_DATA_DIR = "../experiment_data/remapping_psbased"
CCPRM_EXP_DATA_DIR = "../experiment_data/remapping_ccpbased"
RANDNEIGHRM_EXP_DATA_DIR = "../experiment_data/remapping_randombased/neighbour"
RAND_EXP_DATA_DIR = "../experiment_data/remapping_randombased"

# 30 seeds good for both ps AND ccp - 28/02/15
# RANDOM_SEED_LIST= [33749,
# 43894, 53784, 70263, 5558, 76891, 22250, 42198, 74076, 21149,
# 57824, 83200, 53864, 44289, 77379, 23327, 94064, 57177, 26828,
# 84400, 68553, 83694, 68385, 88649, 63193, 76160, 87209, 21576,
# 97669, 79913]



# 30 seeds good for both ps AND ccp - 26/02/15
# RANDOM_SEED_LIST=[33749, \
# 43894,26358,70263,5558,76891,42198,74076, \
# 98652,21149,83200,95928,44289,77379,88117, \
# 73337,94064,57177,84400,81474,68553,83694, \
# 79292,69923,68385,88649,76160,87209,21576, \
# 97669]


RANDOM_SEED_LIST=[81665, 33749, 43894, 53784, 26358, \
80505, 83660, 22817, 70263, 29917, \
26044, 6878, 66093, 69541, 5558, \
76891, 22250, 69433, 42198, 18065, \
74076, 98652, 21149, 50399, 64217, \
44117, 57824, 42267, 83200, 99108, \
95928, 53864, 44289, 77379, 80521, \
88117, 23327, 73337, 94064, 31982]



# # original list
# RANDOM_SEED_LIST=[81665, 33749, 43894, 53784, 26358, 80505, 83660, 22817, 70263, 29917, \
# 26044, 6878, 66093, 69541, 5558, \
# 76891, 22250, 69433, 42198, 18065, \
# 74076, 98652, 21149, 50399, 64217, \
# 44117, 57824, 42267, 83200, 99108, \
# 95928, 53864, 44289, 77379, 80521, \
# 88117, 23327, 73337, 94064, 31982, \
# 57177, 95537, 26828, 84400, 81474, \
# 98510, 34921, 25534, 53706, 61110, \
# 68553, 46319, 19346, 83694, 79292, \
# 29648, 94986, 28524, 69923, 68385]


# original list
# RANDOM_SEED_LIST=[81665, 33749, 43894, 53784, 26358, 80505, 83660, 22817, 70263, 29917, \
# 26044, 6878, 66093, 69541, 5558, \
# 76891, 22250, 69433, 42198, 18065, \
# 74076, 98652, 21149, 50399, 64217, \
# 44117, 57824, 42267, 83200, 99108, \
# 95928, 53864, 44289, 77379, 80521, \
# 88117, 23327, 73337, 94064, 31982, \
# 57177, 95537, 26828, 84400, 81474, \
# 98510, 34921, 25534, 53706, 61110, \
# 68553, 46319, 19346, 83694, 79292, \
# 29648, 94986, 28524, 69923, 68385, \
# 88649, 63193, 76160, 87209, 21576, \
# 97669, 97158, 79913, 18521, 84310]

# best seeds for ps remapping
# RANDOM_SEED_LIST = \
# [43894, 53784, 26358, 83660, 70263, 29917, \
# 26044, 6878, 66093, 69541, 5558, \
# 76891, 42198, 18065, \
# 74076, 98652, 21149, 64217, \
# 57824, 83200, \
# 95928, 44289, 77379, 80521, \
# 88117, 73337, 94064,  \
# 57177, 95537,    26828, 84400, 81474, \
# 61110, \
# 68553, 19346, 83694, 79292, \
# 94986,    28524, 69923, 68385, \
# 88649, 63193,    76160, 87209, 21576, \
# 97669, 97158,    79913, 18521]


# [43894, 26358, \
#  83660, 22817, 70263, 29917, 26044, \
#  5558,  76891, 22250, 42198, 18065, \
#  74076, 98652, 21149, 64217, \
#  57824, 83200, \
#  95928, 53864, 44289, 77379, 80521, \
#  88117, 23327, 73337, 94064, \
#  6878, 66093, 69541]



# [81665, 33749, 43894, 26358, 80505, \
#  83660, 22817, 70263, 29917, 26044, \
#  5558,  76891, 22250, 42198, 18065, \
#  74076, 98652, 21149, 50399, 64217, \
#  44117, 57824, 42267, 83200, 99108, \
#  95928, 53864, 44289, 77379, 80521, \
#  88117, 23327, 73337, 94064, 31982, \
#  6878, 66093, 69541]

# [
#                      # good ones
#                      26044,
#                      29917,
#                      83200,
#                      99108,
#                      73337,
#                      
#                      # bad ones
#                      43894,
#                      5558,
#                      74076,
#                      21149,
#                      77379,
#                      ]

# [81665, 33749, 43894, 26358, 80505, \
#  83660, 22817, 70263, 29917, 26044, \
#  5558,  76891, 42198, 18065, \
#  74076, 21149, 50399, 64217, \
#  44117, 42267, 83200, 99108, \
#  95928, 53864, 77379, 80521, \
#  88117, 23327, 73337, 94064, 31982, \
#  6878, 66093, 69541]

#[81665, 33749, 43894, 53784, 26358, \
#26044, 6878, 66093, 69541, 5558, \
#76891, 22250, 69433, 42198, 18065, \
#74076, 98652, 21149, 50399, 64217, \
#44117, 57824, 42267, 83200, 99108, \
#95928, 53864, 44289, 77379, 80521, \
#88117, 23327, 73337, 94064, 31982]

#[26044, 42198]

#[81665, 33749, 43894, 26358, 80505, \
# 83660, 22817, 70263, 29917, 26044, \
# 5558,  76891, 22250, 42198, 18065, \
# 74076, 98652, 21149, 50399, 64217, \
# 44117, 57824, 42267, 83200, 99108, \
# 95928, 53864, 44289, 77379, 80521, \
# 88117, 23327, 73337, 94064, 31982, \
# 6878, 66093, 69541]


#[44289, 99108, 88117, 29917, 83660, 42198, 73337, 94064]


NUM_ROWS = 7
NUM_COLS = 10

#INTERESTED_SEEDS = len(RANDOM_SEED_LIST)
INTERESTED_SEEDS = 30
    
    
###################################################################################################
#    ResponseTime - Remapping off/on
###################################################################################################
def plot_resptime_variance_multiseed(xaxis_key='dt'):
    
    all_exp_data = OrderedDict()
    for each_seed in RANDOM_SEED_LIST[:INTERESTED_SEEDS]:
        
        MULTISEED_EXP_DATA_DIR = EXP_DATA_DIR + "/seed_" + str(each_seed)
        
        # get remapping-off data
        FNAME_PREFIX = "RMOFF_"    
        fname = MULTISEED_EXP_DATA_DIR + "/" + FNAME_PREFIX + "test__obuff.js"    
        json_data=open(fname)
        remapping_off_data = json.load(json_data)
        
        # get remapping-off data
        FNAME_PREFIX = "RMON_"    
        fname = MULTISEED_EXP_DATA_DIR + "/" + FNAME_PREFIX + "test__obuff.js"    
        json_data=open(fname)
        remapping_on_data = json.load(json_data)
        
        # sort them according to id
        sorted_remapping_off_data = sorted(remapping_off_data, key=itemgetter(xaxis_key)) 
        sorted_remapping_on_data = sorted(remapping_on_data, key=itemgetter(xaxis_key))
        
        # get response_time variance for each task
        all_variances = []
        negative_variances  = []
        positive_variances  = []
        rmoff_all_responsetimes = []
        rmon_all_responsetimes = []
        tids = []
        result_col = []
        markers=[]
        max_xaxis = 0
        
        for ix,each_task in enumerate(sorted_remapping_off_data):
            rm_off_resptime = sorted_remapping_off_data[ix]['et']  - sorted_remapping_off_data[ix]['dt']
            rm_on_resptime = sorted_remapping_on_data[ix]['et']  - sorted_remapping_on_data[ix]['dt']
            
            rmoff_all_responsetimes.append(rm_off_resptime)
            rmon_all_responsetimes.append(rm_on_resptime)
            
            variance = rm_off_resptime - rm_on_resptime
            
            if(variance>0): # good
                result_col.append('g')
                positive_variances.append(variance)
                markers.append('x')
            elif(variance<0): # bad
                result_col.append('r')
                negative_variances.append(variance)
                markers.append('x')
            else:
                #result_col.append('b')
                #markers.append('')
                a=1
                
            if(variance>0 or variance <0):
                tids.append(sorted_remapping_off_data[ix][xaxis_key])            
                all_variances.append(variance)
                if(len(tids)>0):   
                    if(max(tids) > max_xaxis):  
                        max_xaxis = max(tids)   
        
        all_exp_data[each_seed] = {
                                   'RM_OFF_all_resptimes' :  rmoff_all_responsetimes,
                                   'RM_ON_all_resptimes' :  rmon_all_responsetimes,
                                   'negative_variances' : negative_variances,
                                   'positive_variances' : positive_variances,
                                   'all_variances' : all_variances,
                                   'tids' : tids,
                                   'result_col' : result_col,
                                   'markers' : markers
                                   }        
        
    # plot resp-time distributions (boxplots)
#    fig = plt.figure()
#    fig.canvas.set_window_title('plot_resptime_variance_multiseed-boxplots')        
#    i=1
#    for k,each_exp_result in all_exp_data.iteritems():
#        ax=plt.subplot(NUM_ROWS,NUM_COLS,i)
#        ax.boxplot([each_exp_result['RM_OFF_all_resptimes'], each_exp_result['RM_ON_all_resptimes']],
#                   0,'', whis=1, positions=np.arange(2), widths=0.8)
#        ax.set_title('seed_'+str(k))
#        ax.grid(True, alpha=0.5)
#        ax.set_xticklabels(['OFF', 'ON'])
#        i+=1
                    
        
    # plot resp-time distributions (scatter)
    #fig = plt.figure()
    
    fig, axes2d = plt.subplots(nrows=NUM_ROWS, ncols=NUM_COLS,
                           sharex=True)    
    fig.canvas.set_window_title('plot_resptime_variance_multiseed-scatter') 
    fig.text(0.03, 0.55, r"Remapping response time variance : $(RMOFF_{respTime}-RMON_{respTime})$", ha='center', va='center', rotation='vertical', fontsize=16)       
    fig.text(0.5, 0.06, r"Task dispatch time", ha='center', va='center', rotation='horizontal', fontsize=16)
    i=1
    summary = {
               'diff(g-b)' : [],
               }
    print "%10s %10s %10s %10s" % ("seed", "num_bad", "num_good", "diff(g-b)")
    
    for ax, k in zip(axes2d.flat, all_exp_data.keys()):
        #ax.subplot(NUM_ROWS,NUM_COLS,i)
        ax.scatter(all_exp_data[k]['tids'], all_exp_data[k]['all_variances'], marker='x', color=all_exp_data[k]['result_col'])
        ax.set_title('seed_'+str(k))
        ax.grid(True, alpha=0.5)
        ax.set_xlim([0,max_xaxis])
        
        print "%10s %10s %10s %10s" % (
                                       k, str(len(all_exp_data[k]['negative_variances'])), 
                                       str(len(all_exp_data[k]['positive_variances'])),
                                       str(len(all_exp_data[k]['positive_variances'])-len(all_exp_data[k]['negative_variances']))
                                       )
        
        summary['diff(g-b)'].append(len(all_exp_data[k]['positive_variances'])-len(all_exp_data[k]['negative_variances']))
        i+=1
        
    print "========================================================================"
    print "%10s | %10s" % ("diff(g-b)", "mean.diff(g-b)")
    print "%10s | %10s" % (np.sum(summary['diff(g-b)']), 
                           np.mean(summary['diff(g-b)'])
                           )
     
            

def _set_bp(ax, bp, col):
    plt.setp(bp['boxes'], color=col, linewidth=1, alpha=0.7)    
    plt.setp(bp['caps'], color=col)
    plt.setp(bp['whiskers'], color=col)
    plt.setp(bp['fliers'], color=col)
    plt.setp(bp['medians'], color=col)
    


def plot_GoP_lateness_vs_pri_multiseed():
    all_exp_data = OrderedDict()
    
    for each_seed in RANDOM_SEED_LIST[:INTERESTED_SEEDS]:
        
        MULTISEED_EXP_DATA_DIR = EXP_DATA_DIR + "/seed_" + str(each_seed)
        try:            
            # get remapping-off data
            FNAME_PREFIX = "RMOFF_"    
            fname = MULTISEED_EXP_DATA_DIR + "/" + FNAME_PREFIX + "test__gopsopbuffsumm.js"    
            print fname
            json_data=open(fname)
            remapping_off_data = json.load(json_data)
            
            # get remapping-off data
            FNAME_PREFIX = "RMON_"    
            fname = MULTISEED_EXP_DATA_DIR + "/" + FNAME_PREFIX + "test__gopsopbuffsumm.js"   
            print fname
            json_data=open(fname)
            remapping_on_data = json.load(json_data)
        except:
            print "------"
            print "file not found !"
            print fname
            print "------"
            continue

        ### lateness ###
        for each_gop_k, each_gop_v in  remapping_off_data.iteritems():
            try:
                rm_off_gop = each_gop_v
                rm_on_gop = remapping_on_data[each_gop_k]
            
                rm_off_gop_pri = rm_off_gop['gop_mean_pri']   
                rm_on_gop_pri = rm_on_gop['gop_mean_pri']
                
                if(rm_off_gop_pri != rm_on_gop_pri):
                    print "gop pri don't match !! " + str(each_gop_k)
                else:
                    rm_off_gopl = rm_off_gop['gop_execution_lateness']
                    rm_on_gopl = rm_on_gop['gop_execution_lateness']
                    
                    if(rm_off_gopl != rm_on_gopl):                    
                        gopl_reduction_percentage = (float((rm_off_gopl - rm_on_gopl))/rm_off_gopl) * 100.0 
                    
                        if rm_off_gop_pri not in all_exp_data:
                            all_exp_data[rm_off_gop_pri] = [gopl_reduction_percentage]
                        else:
                            all_exp_data[rm_off_gop_pri].append(gopl_reduction_percentage)
                    
            except:
                print "------"
                print "gop error !"
                print each_gop_k
                print "------"
                continue

    sorted_all_exp_data = OrderedDict(sorted(all_exp_data.items()))
    
    ### plot ###
    f2 = plt.figure()
    f2.canvas.set_window_title('Improvement distribution - pri sorted')
    
    hist_data = sorted_all_exp_data.values()
    hist_data_sums = [np.sum(x) for x in hist_data]
    hist_data_means = [np.mean(x) for x in hist_data]
    pos = range(len(sorted_all_exp_data.keys()))
    print sorted_all_exp_data.keys()
    print len(sorted_all_exp_data.keys())
    
    #ax = plt.boxplot(hist_data ,0,'', whis=1.5, positions=pos, widths=0.8)       
    plt.plot(pos, hist_data_means, 
             marker='x', linestyle='', color='b')
    
    f3 = plt.figure()
    plt.hist(hist_data_sums, bins=100)
    
    f4 = plt.figure()
    plt.hist(hist_data_means, bins=100)


def plot_GoP_lateness_multiseed():
    
    all_exp_data = OrderedDict()
    
    for each_seed in RANDOM_SEED_LIST[:INTERESTED_SEEDS]:
        
        MULTISEED_EXP_DATA_DIR = EXP_DATA_DIR + "/seed_" + str(each_seed)
        try:            
            # get remapping-off data
            FNAME_PREFIX = "RMOFF_"    
            fname = MULTISEED_EXP_DATA_DIR + "/" + FNAME_PREFIX + "test__gopsopbuffsumm.js"    
            print fname
            json_data=open(fname)
            remapping_off_data = json.load(json_data)
            
            # get remapping-off data
            FNAME_PREFIX = "RMON_"    
            fname = MULTISEED_EXP_DATA_DIR + "/" + FNAME_PREFIX + "test__gopsopbuffsumm.js"   
            print fname
            json_data=open(fname)
            remapping_on_data = json.load(json_data)
        except:
            print "------"
            print "file not found !"
            print fname
            print "------"
            continue
        
        
        ### lateness ###
        gop_lateness_distribution_rmoff = []
        gop_lateness_distribution_rmon = []        
        # gop lateness distribution - rm-off
        for each_ugid_key, each_ugid_val in remapping_off_data.iteritems():
            if(each_ugid_val['gop_execution_lateness'] > 0):
                gop_lateness_distribution_rmoff.append(each_ugid_val['gop_execution_lateness'])        
        if(len(gop_lateness_distribution_rmoff)==0):
            gop_lateness_distribution_rmoff = [0]           
        
        # gop lateness distribution - rm-on
        for each_ugid_key, each_ugid_val in remapping_on_data.iteritems():
            if(each_ugid_val['gop_execution_lateness'] > 0):
                gop_lateness_distribution_rmon.append(each_ugid_val['gop_execution_lateness'])        
        if(len(gop_lateness_distribution_rmon)==0):
            gop_lateness_distribution_rmon = [0]
                
        ### response-time ###        
        gop_rt_distribution_rmoff = []
        gop_rt_distribution_rmon = []
        # gop-rt : rm-off
        for each_ugid_key, each_ugid_val in remapping_off_data.iteritems():
            gop_rt_distribution_rmoff.append(each_ugid_val['tt_wrt_dt'])
        
        # gop-rt : rm-on  
        for each_ugid_key, each_ugid_val in remapping_on_data.iteritems():
            gop_rt_distribution_rmon.append(each_ugid_val['tt_wrt_dt'])
      
        all_distributions = [gop_lateness_distribution_rmoff, gop_lateness_distribution_rmon]
        all_distributions_rt = [gop_rt_distribution_rmoff, gop_rt_distribution_rmon]
        
        all_exp_data[each_seed] = {
                                   'gop_lateness_distribution_rmoff' : gop_lateness_distribution_rmoff,
                                   'gop_lateness_distribution_rmon' : gop_lateness_distribution_rmon, 
                                   'gop_rt_distribution_rmoff' : gop_rt_distribution_rmoff,
                                   'gop_rt_distribution_rmon' : gop_rt_distribution_rmon,
                                   'all_distributions' : all_distributions,
                                   'all_distributions_rt' : all_distributions_rt
                                   }
        
    i=1    
    summary = {               
               'seed' : [],
               'size_gopl_dist_rmoff' :  [], 
               'size_gopl_dist_rmon' :  [],
               'mean_gopl_rmoff' :  [],
               'mean_gopl_rmon' :  [],
               'max_gopl_rmon' : [],
               'max_gopl_rmoff' :  [],                                
               'size_gopl_variance' : [],
               'improvement_sum_gopl' : [],
               'improvement_mean_gopl' : [],
               'improvement_max_gopl' : [],
               'improvement_mean_gop_rt' : [],
               'improvement_max_gop_rt' : [],
               }
    
    fig, axes2d = plt.subplots(nrows=NUM_ROWS, ncols=NUM_COLS,
                           sharex=True)    
    fig.canvas.set_window_title('plot_GoP_lateness_multiseed') 
    fig.text(0.03, 0.55, "Job Lateness", ha='center', va='center', rotation='vertical', fontsize=16)       
    #fig.text(0.5, 0.06, r"", ha='center', va='center', rotation='horizontal', fontsize=16)
    
    x_labels = ["RMOFF", "RMON"]
    print "%10s, %10s, %10s, %20s, %20s, %20s, %20s, %10s, %28s, %28s, %28s, %28s" % \
    ("seed", "rmoff-size", "rmon-size", "rmoff_gopl_mean", "rmon_gopl_mean", "size_var", 
     "% improvement_sum_gopl", "% improvement_mean_gopl", "% improvement_max_gopl",
     "% improvement_mean_gop_rt", "% improvement_max_gop_rt", "wilcoxon-p-val",
     
     )
    
    for ax, k in zip(axes2d.flat, all_exp_data.keys()): 
        # calculate means, max, variances, etc
        sum_gopl = [np.sum(x) for x in all_exp_data[k]['all_distributions']]
        means_gopl =  [np.mean(x) for x in all_exp_data[k]['all_distributions']]      
        max_lateness_gopl = [np.max(x) for x in all_exp_data[k]['all_distributions']]
        means_gop_rt = [np.mean(x) for x in all_exp_data[k]['all_distributions_rt']]
        max_gop_rt = [np.max(x) for x in all_exp_data[k]['all_distributions_rt']]
        
        
        summary['seed'].append(k)
        summary['size_gopl_dist_rmoff'].append(len(all_exp_data[k]['gop_lateness_distribution_rmoff']))
        summary['size_gopl_dist_rmon'].append(len(all_exp_data[k]['gop_lateness_distribution_rmon']))
        summary['mean_gopl_rmoff'].append(means_gopl[0])
        summary['mean_gopl_rmon'].append(means_gopl[1])
        summary['max_gopl_rmon'].append(max_lateness_gopl[0])
        summary['max_gopl_rmoff'].append(max_lateness_gopl[1])                                
        summary['size_gopl_variance'].append(len(all_exp_data[k]['gop_lateness_distribution_rmoff']) - len(all_exp_data[k]['gop_lateness_distribution_rmon']))
        summary['improvement_sum_gopl'].append(np.round(1.0*(float(100.0*((sum_gopl[0]-sum_gopl[1])/sum_gopl[0]))),3))
        summary['improvement_mean_gopl'].append(np.round(1.0*(float(100.0*((means_gopl[0]-means_gopl[1])/means_gopl[0]))),3))
        summary['improvement_max_gopl'].append(np.round(1.0*(float(100.0*((max_lateness_gopl[0]-max_lateness_gopl[1])/max_lateness_gopl[0]))),3))
        summary['improvement_mean_gop_rt'].append(np.round(1.0*(float(100.0*((means_gop_rt[0]-means_gop_rt[1])/means_gop_rt[0]))),3))
        summary['improvement_max_gop_rt'].append(np.round(1.0*(float(100.0*((max_gop_rt[0]-max_gop_rt[1])/max_gop_rt[0]))),3))
               
        
        # draw boxplots
        boxpos = np.arange(len(all_exp_data[k]['all_distributions']))
        ax.boxplot(all_exp_data[k]['all_distributions'],0,'', whis=1, positions=boxpos, widths=0.8)
                 
        ax.plot(boxpos, means_gopl, marker='d', markersize=10, linestyle='--', color='g', linewidth=0.5, label="Mean job lateness")
        ax.plot(boxpos, max_lateness_gopl, marker='o', markersize=10, linestyle='--', color='r', linewidth=0.5, label="Maximum job lateness")
        ax.set_title('seed_'+str(k))
        ax.grid(True, alpha=0.5)
        ax.set_xticklabels(x_labels)
        
        (T, p) = scipy.stats.wilcoxon(all_exp_data[k]['all_distributions_rt'][0], all_exp_data[k]['all_distributions_rt'][1])
        
        # reporting results 
        print "%10s, %10s, %10s, %20s, %20s, %20s, %20s, %10s, %28s, %28s, %28s, %28s" % \
                                 (  summary['seed'][-1],
                                    summary['size_gopl_dist_rmoff'][-1],
                                    summary['size_gopl_dist_rmon'][-1],
                                    summary['mean_gopl_rmoff'][-1],
                                    summary['mean_gopl_rmon'][-1],                                                                 
                                    summary['size_gopl_variance'][-1],
                                    summary['improvement_sum_gopl'][-1],
                                    summary['improvement_mean_gopl'][-1],
                                    summary['improvement_max_gopl'][-1],
                                    summary['improvement_mean_gop_rt'][-1],
                                    summary['improvement_max_gop_rt'][-1],
                                    p
                                  )
       
        i+=1
    
    
        
    print "========================================================================"
    print "overall_mean_improvement_sum_gopl = " + str(np.mean(summary['improvement_sum_gopl']))
    print "overall_mean_improvement_mean_gopl = " + str(np.mean(summary['improvement_mean_gopl']))
    print "overall_mean_improvement_max_gopl = " + str(np.mean(summary['improvement_max_gopl']))
    print "overall_mean_improvement_mean_gop_rt = " + str(np.mean(summary['improvement_mean_gop_rt']))
    print "overall_mean_improvement_max_gop_rt = " + str(np.mean(summary['improvement_max_gop_rt']))
    
    
    
    ## distribution of improvements
    f2 = plt.figure()
    f2.canvas.set_window_title('Improvement distribution')
    pos = [0,1,2,3, 4]
    dist_improvements = [
                         summary['improvement_sum_gopl'],
                         summary['improvement_mean_gopl'], 
                         summary['improvement_max_gopl'], 
                         summary['improvement_mean_gop_rt'], 
                         summary['improvement_max_gop_rt']
                         ]
         
    ax = plt.boxplot(dist_improvements ,0,'', whis=1.5, positions=pos, widths=0.8)       
    plt.plot(pos, [np.mean(x) for x in dist_improvements], marker='d', markersize=10, linestyle='', color='g', linewidth=0.5, label="Mean")
    
    #ax.set_yscale('log')
    plt.grid(True)
    plt.xticks(pos, ['improvement_sum_gopl', 'improvement_mean_gopl', 'improvement_max_gopl', 'improvement_mean_gop_rt', 'improvement_max_gop_rt' ], fontsize=16)
    plt.ylabel('% Improvement', fontsize=16)
    plt.legend(numpoints=1)
    
    
    print "------------"
    print "statistical significance :: Wilcoxon signed-rank test"
    data_exp_condition_1_rmoff = [np.sum(each_seed_v['all_distributions'][0]) 
                                  for each_seed_k, each_seed_v in all_exp_data.iteritems()] 
    
    data_exp_condition_2_rmon = [np.sum(each_seed_v['all_distributions'][1]) 
                                  for each_seed_k, each_seed_v in all_exp_data.iteritems()]
    
    (T, p) = scipy.stats.wilcoxon(data_exp_condition_2_rmon, data_exp_condition_1_rmoff)
    print "p = " + str(p)
    print "T = " + str(T)
    
    print "statistical significance :: mann-whitneyU test"
    (U,p) = scipy.stats.mannwhitneyu(data_exp_condition_1_rmoff, data_exp_condition_2_rmon)
    print "p = " + str(p)
    print "U = " + str(U)
    
    print "confidence interval:"
    (m, neg, pos) = _mean_confidence_interval(summary['improvement_sum_gopl'])
    print m, neg, pos
    
    print "------------"
    


   
def plot_SeedCCDistributions():

    all_exp_data = OrderedDict()

    
    for each_seed in RANDOM_SEED_LIST[:INTERESTED_SEEDS]:
        
        MULTISEED_EXP_DATA_DIR = EXP_DATA_DIR + "/seed_" + str(each_seed)
        
        # get remapping-off data
        FNAME_PREFIX = "RMOFF_"    
        fname = MULTISEED_EXP_DATA_DIR + "/" + FNAME_PREFIX + "test__obuff.js"    
        json_data=open(fname)
        remapping_off_data = json.load(json_data)
        
        # get response_time variance for each task
        rmoff_all_cc = []
        
        for ix,each_task in enumerate(remapping_off_data):
            rm_off_cc = remapping_off_data[ix]['cc']            
            rmoff_all_cc.append(rm_off_cc)
          
        all_exp_data[each_seed] = {
                                   'RM_OFF_all_cc' :  rmoff_all_cc                                   
                                   }        
        
        
    # plot resp-time distributions (scatter)
    #fig = plt.figure()
    
    fig = plt.figure()  
    fig.canvas.set_window_title('plot_SeedCCDistributions-boxplots') 
    
    x_labels  = all_exp_data.keys()
    cc_distributions = [x['RM_OFF_all_cc'] for x in all_exp_data.values()]
    cc_means = [np.mean(x['RM_OFF_all_cc']) for x in all_exp_data.values()]
    cc_maxes = [max(x['RM_OFF_all_cc']) for x in all_exp_data.values()]
    
        
    boxpos = np.arange(len(cc_distributions))
    plt.boxplot(cc_distributions,0,'', whis=1, positions=boxpos, widths=0.8)
    plt.plot(boxpos, cc_means, marker='d', markersize=10, linestyle='--', color='g', linewidth=0.5, label="Mean cc")
    plt.plot(boxpos, cc_maxes, marker='o', markersize=10, linestyle='--', color='r', linewidth=0.5, label="Maximum cc")    
    plt.hold(True)
    
    for x,d in zip(boxpos, cc_distributions):
        plt.scatter(np.ones(len(d))*x, d, marker='x', alpha=0.2)
        plt.hold(True)
    
    plt.grid(True, alpha=0.5)
    plt.xticks(boxpos, x_labels)
            

def plot_num_vids_fully_scheduled(data_filename = None, base_dir="Z:/MCASim/experiment_data/"):
    
    print "plot_num_vids_fully_scheduled"
            
    LIST_EXP_DATA_DIRS = [ 
                            ## no remapping
                            #[base_dir + "remapping_psbased", 'NO_REMAPPING', None, "No\nremapping"],
                            
                            ## PSRM
                            #["Z:/MCASim/experiment_data/remapping_psbased_mmcoff", 'PSRM_MMCOFF', None],
                            #["Z:/MCASim/experiment_data/remapping_psbased_mmcoff_v2", 'PSRM', "plot_flows_completed_datafile.js"],                            
                            [base_dir + "remapping_psbased", 'PSRM_EXP', None, "PSRM"],                            
                                                        
                            ## CCPRM - improved
                            [base_dir + "remapping_ccpbased", 'CCPRM_IMP', None, 'CCPRM$_{\\rmV2}$\n(2x5 cluster)'],                                                        
                            [base_dir + "remapping_ccpbased_single_cluster", 'CCPRM_SINGLECLUSTER_IMP', None, 'Centralised\nmanagement'],
                            
                            ## CCPRM - original
                            #[base_dir + "remapping_ccpbased_orig", 'CCPRM_ORIG', None],                                                        
                            #[base_dir + "remapping_ccpbased_single_cluster_orig", 'CCPRM_SINGLECLUSTER_ORIG', None],
                                                        
                            ## random
                            [base_dir + "remapping_randombased", 'RANDOMANY', None, "Random\nremapping"],
                            
                            ## fully dynamic
                            #["Z:/MCASim/experiment_data/remapping_central_dynamic", 'FULLYDYNAMIC', None],
                            
                        ]
    all_exp_data = OrderedDict()
    
    if(data_filename == None):    
        
        for each_exp_dir in LIST_EXP_DATA_DIRS:        
            EXP_DATA_DIR = each_exp_dir[0]
            EXP_LABEL = each_exp_dir[1]
            DATAFILENAME = each_exp_dir[2]            
            
            if (DATAFILENAME == None):
                
                
                if EXP_LABEL != "NO_REMAPPING":
            
                    print "------------------------------------------"
                    print EXP_LABEL
                    print "------------------------------------------"                    
                    all_seed_data = []
                    for each_seed in RANDOM_SEED_LIST[:INTERESTED_SEEDS]:                        
                        try:            
                            # get psbased_remapping data communication costs            
                            MULTISEED_EXP_DATA_DIR = EXP_DATA_DIR + "/seed_" + str(each_seed)
                            FNAME_PREFIX = "RMON_"    
                            fname = MULTISEED_EXP_DATA_DIR + "/" + FNAME_PREFIX + "test__wfressumm.js"
                            print fname
                            json_data=open(fname)
                            wfsumm_file_data = json.load(json_data)
                            json_data.close()
                            data = _get_num_vids_fully_scheduled(wfsumm_file_data)
                            #data = _get_num_gops_late(wfsumm_file_data)
                            all_seed_data.append(data)        
                                   
                        except Exception as e:
                            print "------"
                            print "file not found !"
                            print fname
                            print e
                            print "------"
                            continue
                        
                    print all_seed_data            
                    all_exp_data[EXP_LABEL] = {
                                               'total_true_mean' : np.mean(all_seed_data),
                                               'total_true_dist' : all_seed_data,
                                               'total_true_variance' : np.var(all_seed_data),
                                               'total_true_cumsum' : np.sum(all_seed_data),
                                               }
                else:
                    
                    print "------------------------------------------"
                    print EXP_LABEL
                    print "------------------------------------------"                    
                    all_seed_data = []
                    for each_seed in RANDOM_SEED_LIST[:INTERESTED_SEEDS]:                        
                        try:            
                            # get psbased_remapping data communication costs            
                            MULTISEED_EXP_DATA_DIR = EXP_DATA_DIR + "/seed_" + str(each_seed)
                            FNAME_PREFIX = "RMOFF_"    
                            fname = MULTISEED_EXP_DATA_DIR + "/" + FNAME_PREFIX + "test__wfressumm.js"
                            print fname
                            json_data=open(fname)
                            wfsumm_file_data = json.load(json_data)
                            json_data.close()
                            data = _get_num_vids_fully_scheduled(wfsumm_file_data)
                            #data = _get_num_gops_late(wfsumm_file_data)
                            all_seed_data.append(data)        
                                   
                        except Exception as e:
                            print "------"
                            print "file not found !"
                            print fname
                            print e
                            print "------"
                            continue
                        
                    print all_seed_data            
                    all_exp_data[EXP_LABEL] = {
                                               'total_true_mean' : np.mean(all_seed_data),
                                               'total_true_variance' : np.var(all_seed_data),
                                               'total_true_cumsum' : np.sum(all_seed_data),
                                               'total_true_dist' : all_seed_data
                                               }
                    
            else:
                print "------------------------------------------"
                print EXP_LABEL  + " :: loading from local file"
                print "------------------------------------------"
                json_data=open(DATAFILENAME)
                all_exp_data[EXP_LABEL] = json.load(json_data)[EXP_LABEL]
                
    else:
        print "plot_num_vids_fully_scheduled :: loading data from file"
        json_data=open(data_filename)
        all_exp_data = json.load(json_data)
        
    
    # plot data
    bar_plot_data = [v['total_true_cumsum'] for k,v in all_exp_data.iteritems()]
    bar_plot_data_variance = [v['total_true_variance'] for k,v in all_exp_data.iteritems()]
    box_plot_data = [v['total_true_dist'] for k,v in all_exp_data.iteritems()]
    
    #norm_box_plot_data =_normalise_2d_list(box_plot_data)
    
    #pprint.pprint(norm_box_plot_data)
    
    exp_labels = [x[3] for x in LIST_EXP_DATA_DIRS]
    ind = np.arange(len(exp_labels))
    width = 0.6
    
    f1, ax1 = plt.subplots()
    f1.canvas.set_window_title('Total schedulable video streams - barplots')
    pos = np.arange(len(exp_labels))
    ax1.bar(ind, bar_plot_data, width, align='center')
    plt.xticks(ind, exp_labels, fontsize=18)
    plt.ylabel('Total schedulable video streams\n(mean of all exp. runs)', fontsize=18, multialignment='center')    
    ax1.tick_params(axis='both', labelsize=18)
    #ax1.set_yscale('log')
    plt.grid(True)
    
#     f2, ax2 = plt.subplots()
#     f2.canvas.set_window_title('Total schedulable video streams - boxplots')
#     pos = np.arange(len(exp_labels))
#     ax2.boxplot(box_plot_data ,0,'', whis=1.5, positions=ind, widths=0.8)
#     plt.hold(True)
#     ax2.plot(ind, [np.mean(x) for x in box_plot_data], marker='d', markersize=10, linestyle='', color='g', linewidth=0.5, label="Mean") 
#     plt.grid(True)
#     plt.xticks(pos, exp_labels, fontsize=16)
#     plt.ylabel('Total schedulable video streams', fontsize=16)
    
    
    print "======================================================="
    print "results"
    print "======================================================="
    print exp_labels
    print "total_true_cumsum : ", [ int(float(v['total_true_cumsum'])) for k,v in all_exp_data.iteritems()]
    print "total_true_mean : ", [v['total_true_mean'] for k,v in all_exp_data.iteritems()]
    print "======================================================="
    
    
    return all_exp_data


def plot_systemidletime_histogram(data_filename = None, base_dir="Z:/MCASim/experiment_data/"):
    
    print "plot_systemidletime_histogram"
            
    LIST_EXP_DATA_DIRS = [ 
                            ## no remapping
                            #[base_dir + "remapping_psbased", 'NO_REMAPPING', None, "No\nremapping"],
                            
                            ## PSRM
                            #["Z:/MCASim/experiment_data/remapping_psbased_mmcoff", 'PSRM_MMCOFF', None],
                            #["Z:/MCASim/experiment_data/remapping_psbased_mmcoff_v2", 'PSRM', "plot_flows_completed_datafile.js"],                            
                            [base_dir + "remapping_psbased", 'PSRM_EXP', None, "PSRM"],                            
                                                        
                            ## CCPRM - improved
                            [base_dir + "remapping_ccpbased", 'CCPRM_IMP', None, 'CCPRM$_{\\rmV2}$\n(2x5 cluster)'],                                                        
                            [base_dir + "remapping_ccpbased_single_cluster", 'CCPRM_SINGLECLUSTER_IMP', None, 'Centralised\nmanagement'],
                            
                            ## CCPRM - original
                            #[base_dir + "remapping_ccpbased_orig", 'CCPRM_ORIG', None],                                                        
                            #[base_dir + "remapping_ccpbased_single_cluster_orig", 'CCPRM_SINGLECLUSTER_ORIG', None],
                                                        
                            ## random
                            [base_dir + "remapping_randombased", 'RANDOMANY', None, "Random\nremapping"],
                            
                            ## fully dynamic
                            #["Z:/MCASim/experiment_data/remapping_central_dynamic", 'FULLYDYNAMIC', None],
                            
                        ]
    all_exp_data = OrderedDict()
    
    if(data_filename == None):    
        
        for each_exp_dir in LIST_EXP_DATA_DIRS:        
            EXP_DATA_DIR = each_exp_dir[0]
            EXP_LABEL = each_exp_dir[1]
            DATAFILENAME = each_exp_dir[2]            
            
            if (DATAFILENAME == None):
                
                    print "------------------------------------------"
                    print EXP_LABEL
                    print "------------------------------------------"                    
                    all_seed_data = []
                    for each_seed in RANDOM_SEED_LIST[:INTERESTED_SEEDS]:                        
                        try:            
                            # get psbased_remapping data communication costs            
                            MULTISEED_EXP_DATA_DIR = EXP_DATA_DIR + "/seed_" + str(each_seed)
                            FNAME_PREFIX = "RMON_"    
                            fname = MULTISEED_EXP_DATA_DIR + "/" + FNAME_PREFIX + "test__utilshort.js"
                            print fname
                            json_data=open(fname)
                            sysutil_file_data = json.load(json_data)
                            json_data.close()
                            data = np.array(_get_cpu_busytime_allnodes(sysutil_file_data))
                            #data = _get_num_gops_late(wfsumm_file_data)
                            all_seed_data.append(data)        
                                   
                        except Exception as e:
                            print "------"
                            print "file not found !"
                            print fname
                            print e
                            print "------"
                            continue
                    
                    #print all_seed_data
                    #sys.exit()
                     
                    #print all_seed_data            
                    all_exp_data[EXP_LABEL] = {
                                               #'total_true_mean' : np.mean(all_seed_data),
                                               'all_nodes_idle_dist_means' : np.mean(all_seed_data, axis=0)
                                               }
                
                    
            else:
                print "------------------------------------------"
                print EXP_LABEL  + " :: loading from local file"
                print "------------------------------------------"
                json_data=open(DATAFILENAME)
                all_exp_data[EXP_LABEL] = json.load(json_data)[EXP_LABEL]
                
    else:
        print "plot_num_vids_fully_scheduled :: loading data from file"
        json_data=open(data_filename)
        all_exp_data = json.load(json_data)
    
    # find max
    ultimate_max = np.amax([x['all_nodes_idle_dist_means'] for x in all_exp_data.values()])
    ultimate_min = np.amin([x['all_nodes_idle_dist_means'] for x in all_exp_data.values()])   
    
    # plot data
    
    exp_labels = [x[3] for x in LIST_EXP_DATA_DIRS]
    ind = np.arange(len(exp_labels))
    width = 0.6
    
    colors = ['r', 'g', 'b', 'y']
    f1, ax = plt.subplots(2,2)
    f1.canvas.set_window_title('plot_systemidletime_histogram')
    
    ax = ax.ravel()
    track_rounded_hist_data = []
    i=0
    for each_k, each_v in all_exp_data.iteritems():
        hist_data = each_v['all_nodes_idle_dist_means']
        
        #print hist_data
        
        hist_data_norm = _normalise_list(hist_data, norm_min=ultimate_min, norm_max=ultimate_max)        
        hist_data_norm_rounded = np.array([round(x,10) for x in hist_data_norm])        
        reshaped_hist_data = hist_data_norm_rounded.reshape((10, 10))        
        track_rounded_hist_data.append(hist_data_norm_rounded)
        
        print "---"
        print "Exp: " + each_k
        print reshaped_hist_data        
        print "Variance :: " + str(np.round(np.var(hist_data), 4))
        print "Mean :: " + str(np.round(np.mean(hist_data_norm_rounded), 4))
        print "---"
                
        #n, bins, patches = ax[i].hist(hist_data_rounded, 20, ec=colors[i], fc='none', lw=1.5, histtype='step', label=each_k, alpha=0.5, range=(ultimate_min-0.1, ultimate_max+0.1))
        x = ax[i].pcolor(np.flipud(reshaped_hist_data), cmap='hot', edgecolors='g', linewidths=1)
        #n, bins, patches = ax[0].hist(hist_data_rounded, 20, ec=colors[i],  lw=1.5, histtype='step', label=each_k, alpha=0.3)
        
        # add a 'best fit' line
        #(mu, sigma) = scipy.stats.norm.fit(hist_data_rounded)
        #y = mlab.normpdf( bins, mu, sigma)
        #l = ax[0].plot(bins, y, linestyle='--', c=colors[i], linewidth=2)       
        
        ax[i].set_title(exp_labels[i], fontsize=20)        
        ax[i].set_axis_off()
        i+=1
    
    plt.legend()
    plt.grid(True)
    
    f1.subplots_adjust(right=0.8)
    cbar_ax = f1.add_axes([0.85, 0.15, 0.05, 0.7])
    cbar = f1.colorbar(x, cax=cbar_ax, ticks=[0,1])
    cbar_ax.set_xticklabels(['Idle', 'Busy'])
        
    #plt.xticks(ind+(width/2), exp_labels, fontsize=20)
    #plt.ylabel('Total schedulable video streams\n(mean of all exp. runs)', fontsize=20, multialignment='center')    
    #ax.tick_params(axis='both', labelsize=20)    
    #plt.grid(True)
    
    patterns = ('-', '+', 'x', '\\', '*', 'o', 'O', '.')
    f2, ax2 = plt.subplots()
    f2.canvas.set_window_title('plot_systemidletime_histogram - v2')
    common_params = dict(bins=50, 
                     range=(0.0, 1.0), 
                     normed=True,
                     alpha=0.5)
    
    colors = [colorConverter.to_rgba(c) for c in ['r', 'g', 'b', 'y']]
    
    n, bins, patches = ax2.hist(track_rounded_hist_data,label=exp_labels ,color=colors, **common_params)
    # add a 'best fit' line
    colors = ['r', 'g', 'b', 'y']
    i=0
    for data in track_rounded_hist_data:
        bincenters = 0.5*(bins[1:]+bins[:-1])
        (mu, sigma) = scipy.stats.norm.fit(data)
        y = mlab.normpdf(bincenters, mu, sigma)        
        #pprint.pprint(y)        
        l = ax2.plot(bincenters, y, linestyle='--',  linewidth=3, c=colors[i])
        i+=1
               
    plt.legend()
    plt.setp(plt.gca().get_legend().get_texts(), fontsize='18')
    plt.grid(True)
    plt.ylabel('Frequency', fontsize=20, multialignment='center')    
    plt.xlabel('Normalised PE busy time', fontsize=20, multialignment='center')
    ax2.tick_params(axis='both', labelsize=20)
    
#     f2, ax2 = plt.subplots()
#     f2.canvas.set_window_title('Total schedulable video streams - boxplots')
#     pos = np.arange(len(exp_labels))
#     ax2.boxplot(box_plot_data ,0,'', whis=1.5, positions=ind, widths=0.8)
#     plt.hold(True)
#     ax2.plot(ind, [np.mean(x) for x in box_plot_data], marker='d', markersize=10, linestyle='', color='g', linewidth=0.5, label="Mean") 
#     plt.grid(True)
#     plt.xticks(pos, exp_labels, fontsize=16)
#     plt.ylabel('Total schedulable video streams', fontsize=16)
    
    print "======================================================="
    print "results"
    print "======================================================="
    print exp_labels
    print "high : med : low : "    
    for data in track_rounded_hist_data:
        print _get_workload_distr(data)        
     
    print "======================================================="
    
    
    return all_exp_data


def _get_workload_distr(data):
    
    # high utilised : 100-65%
    # med utilised :   70-50%
    # low utilised :   49-0%
    
    tot_num_nodes = len(data)
    
    high_wl = round((float(len([each_data_point for each_data_point in data
                   if each_data_point >= 0.65 and each_data_point <= 1.0]))/float(tot_num_nodes)) * 100.0)
    
    med_wl = round((float(len([each_data_point for each_data_point in data
                   if each_data_point >= 0.5 and each_data_point < 0.65]))/float(tot_num_nodes)) * 100.0)
    
    low_wl = round((float(len([each_data_point for each_data_point in data
                   if each_data_point >= 0.0 and each_data_point < 0.5]))/float(tot_num_nodes)) * 100.0)
    
    result = [high_wl, med_wl, low_wl]
    
    return result
    
    

def plot_flows_completed(data_filename = None, base_dir="Z:/MCASim/experiment_data/", show_plot=False):
            
    LIST_EXP_DATA_DIRS = [ 
                            ## PSRM
                            #["Z:/MCASim/experiment_data/remapping_psbased_mmcoff", 'PSRM_MMCOFF', None],
                            #["Z:/MCASim/experiment_data/remapping_psbased_mmcoff_v2", 'PSRM', "plot_flows_completed_datafile.js"],                            
                            #[base_dir + "remapping_psbased", 'PSRM', "plot_flows_completed_datafile.js", "PSRM"],                            
                                                        
                            ## CCPRM - original
                            [base_dir + "remapping_ccpbased_orig_060415/remapping_ccpbased_orig", 'CCPRM_ORIG', None, 'CCPRM$_{\\rmV1}$'],                                                        
                            #[base_dir + "remapping_ccpbased_single_cluster_orig", 'CCPRM_SINGLECLUSTER_ORIG', None],
                            
                            ## CCPRM - improved
                            [base_dir + "remapping_ccpbased", 'CCPRM_IMP', None, 'CCPRM$_{\\rmV2}$'],                                                        
                            #[base_dir + "remapping_ccpbased_single_cluster", 'CCPRM_SINGLECLUSTER_IMP', "plot_flows_completed_datafile.js", 'Centralised\nmanagement'],
                            
                            ## random
                            #[base_dir + "remapping_randombased", 'RANDOMANY', "plot_flows_completed_datafile.js", "Random\nremapping"],
                            
                            ## fully dynamic
                            #["Z:/MCASim/experiment_data/remapping_central_dynamic", 'FULLYDYNAMIC', None],
                            
                        ]
    all_exp_data = OrderedDict()
    
    if(data_filename == None):    
        
        for each_exp_dir in LIST_EXP_DATA_DIRS:        
            EXP_DATA_DIR = each_exp_dir[0]
            EXP_LABEL = each_exp_dir[1]
            DATAFILENAME = each_exp_dir[2]
            
            if (DATAFILENAME == None):
            
                print "------------------------------------------"
                print EXP_LABEL
                print "------------------------------------------"
                
                all_seed_data = []
                for each_seed in RANDOM_SEED_LIST[:INTERESTED_SEEDS]:                        
                    try:            
                        # get psbased_remapping data communication costs            
                        MULTISEED_EXP_DATA_DIR = EXP_DATA_DIR + "/seed_" + str(each_seed)
                        FNAME_PREFIX = "RMON_"    
                        fname = MULTISEED_EXP_DATA_DIR + "/" + FNAME_PREFIX + "test__flwcompleted.js"
                        print fname
                        json_data=open(fname)
                        flwscompleted_file_data = json.load(json_data)
                        json_data.close()
                        data = _get_comms_overhead(flwscompleted_file_data)
                        all_seed_data.append(data)
        
                               
                    except Exception as e:
                        print "------"
                        print "file not found !"
                        print fname
                        print e
                        print "------"
                        continue
                    
                print all_seed_data            
                all_exp_data[EXP_LABEL] = {
                                           'flws_completed_mean' : np.mean(all_seed_data),
                                           'flws_completed_dist' : all_seed_data
                                           }
            else:
                print "------------------------------------------"
                print EXP_LABEL  + " :: loading from local file"
                print "------------------------------------------"
                json_data=open(DATAFILENAME)
                all_exp_data[EXP_LABEL] = json.load(json_data)[EXP_LABEL]
                
    else:
        print "plot_flows_completed :: loading data from file"
        json_data=open(data_filename)
        all_exp_data = json.load(json_data)
        
    if show_plot == True:
        #order_of_remappers = ['PSRM' , 'CCPRM_IMP', 'CCPRM_SINGLECLUSTER_IMP', 'RANDOMANY']
        order_of_remappers = ['CCPRM_ORIG','CCPRM_IMP']
        
        # plot data
        #bar_plot_data = [v['flws_completed_mean'] for k,v in all_exp_data.iteritems()]
        #box_plot_data = [v['flws_completed_dist'] for k,v in all_exp_data.iteritems()]
        
        bar_plot_data = [all_exp_data[k]['flws_completed_mean'] for k in order_of_remappers]
        box_plot_data = [all_exp_data[k]['flws_completed_dist'] for k in order_of_remappers]
           
        
        #norm_box_plot_data =_normalise_2d_list(box_plot_data)
        #norm_bar_plot_data =_normalise_list(bar_plot_data)
        
        #pprint.pprint(norm_box_plot_data)
        
        #exp_labels = all_exp_data.keys()
        exp_labels =  [x[3] for x in LIST_EXP_DATA_DIRS]
        ind = np.arange(len(exp_labels))
        width = 0.5
        
        # bar plot
        f1, ax1 = plt.subplots(figsize=(4.1, 4.8))    
        f1.canvas.set_window_title('Communication overhead - barplots')
        pos = np.arange(len(exp_labels))
        ax1.bar(ind, bar_plot_data, width)
        plt.xticks(ind+(width/2.0), exp_labels, fontsize=14)
        ax1.tick_params(axis='both', labelsize=14)
        plt.ylabel('Communication overhead\nMean of cumulative basic latencies (s)\n', fontsize=14, multialignment='center')
        plt.ticklabel_format(style='sci', axis='y', scilimits=(0,0))
        ax1.yaxis.grid(True)
        ax1.xaxis.grid(False)
        ax1.set_ylim([1.0e-4, 1.20e-4])
        ax1.set_xlim([ (0+(width/2.0)-0.5), (1+(width/2.0)+0.5)])
        plt.tight_layout()
        plt.subplots_adjust(left=0.30, right=0.98, top=0.96, bottom=0.07)
        
        
        
        
        # box plot    
#         f2,(ax2a,ax2b) = plt.subplots(2,1,sharex=True)    
#         f2.canvas.set_window_title('Communication overhead - boxplots')
#         
#         gs = gridspec.GridSpec(2, 1,height_ratios=[4,1])
#         ax2a = plt.subplot(gs[0])
#         ax2b = plt.subplot(gs[1])
#         
#         pos = np.arange(len(exp_labels))
#         ax2a.boxplot(box_plot_data ,0,'', whis=1.5, positions=ind, widths=0.8)
#         ax2b.boxplot(box_plot_data ,0,'', whis=1.5, positions=ind, widths=0.8)
#         ax2a.plot(ind, [np.mean(x) for x in box_plot_data], marker='d', markersize=10, linestyle='', color='g', linewidth=0.5, label="Mean")
#         ax2b.plot(ind, [np.mean(x) for x in box_plot_data], marker='d', markersize=10, linestyle='', color='g', linewidth=0.5, label="Mean")
#         ax2b.ticklabel_format(style='sci', axis='y', scilimits=(0,0), labelsize=14)
#         ax2a.ticklabel_format(style='sci', axis='y', scilimits=(0,0), labelsize=14)
#         plt.rc('font', size=14)
#         
#         ax2a.set_ylim(7.28e-5, 0.000132957 ) # most of the data
#         l=plt.legend(numpoints=1)
#         l.draggable()
#         
#         ax2b.set_ylim(7.662e-14 , 9.67e-14) # outliers only
#         
#         ax2a.spines['bottom'].set_visible(False)
#         ax2b.spines['top'].set_visible(False)
#         ax2a.xaxis.tick_top()
#         ax2a.tick_params(labeltop='off') # don't put tick labels at the top
#         ax2b.xaxis.tick_bottom()
#         ax2a.tick_params(axis='both', labelsize=14)
#         ax2b.tick_params(axis='both', labelsize=14)
#         
#         d = .015
#         kwargs = dict(transform=ax2a.transAxes, color='k', clip_on=False)
#         ax2a.plot((-d,+d),(-d,+d), **kwargs)      # top-left diagonal
#         ax2a.plot((1-d,1+d),(-d,+d), **kwargs)    # top-right diagonal
#         
#         kwargs.update(transform=ax2b.transAxes)  # switch to the bottom axes
#         ax2b.plot((-d,+d),(1-d,1+d), **kwargs)   # bottom-left diagonal
#         ax2b.plot((1-d,1+d),(1-d,1+d), **kwargs) # bottom-right diagonal
#         
#         ax2b.grid(True)
#         ax2a.grid(True)
#         
#         plt.xticks(pos, exp_labels, fontsize=14)
#         #l=plt.legend()
#         #l.draggable()
#         #plt.ylabel('Communication overhead\n(cumulative basic latency)', fontsize=20, multialignment='center')
#         f2.text(0.009, 0.5, 'Communication overhead\ncumulative basic latency (s)', va='center', rotation='vertical', fontsize=20, multialignment='center')
#         
    return all_exp_data





def _normalise_2d_list(list_2d):
    # normalise all-data 
    norm_max = np.max([item for sublist in list_2d for item in sublist])
    norm_min = np.min([item for sublist in list_2d for item in sublist])
    
    new_2d_list = []
    for each_l in list_2d:
        temp_list = []
        for x in each_l:
            norm_val = (x-norm_min)/(norm_max-norm_min)
            temp_list.append(norm_val)
        
        new_2d_list.append(temp_list)
    
    return new_2d_list 
        
        
def _normalise_list(lst, norm_min=None, norm_max=None):
    
    if norm_max == None:
        norm_max = np.max(lst)
    
    if norm_min == None:
        norm_min = np.min(lst)
    
    new_list = []
    for each_l in lst:   
        x = each_l     
        norm_val = (x-norm_min)/(norm_max-norm_min)
        new_list.append(norm_val)
       
    
    return new_list 







def plot_cumsum_improvement_distributions_all_techniques(data_filename = None, base_dir="Z:/MCASim/experiment_data/", show_plot=False):
    
    LIST_EXP_DATA_DIRS = [ 
                            
                            ## PSRM
                            #["Z:/MCASim/experiment_data/remapping_psbased_mmcoff", 'PSRM_MMCOFF', None],
                            #["Z:/MCASim/experiment_data/remapping_psbased_mmcoff_v2", 'PSRM', "plot_cumsum_improvement_distributions_all_techniques_datafile.js"],
                            #[base_dir + "remapping_psbased", 'PSRM_MEM_OFF', None, "PSRM_MEM_OFF"],                            
                            #[base_dir + "remapping_psbased_mmcon_060415/remapping_psbased_mmcon", 'PSRM_MEM_ON', None, "PSRM_MEM_ON"],
                            
                            ## CCPRM - original
                            [base_dir + "remapping_ccpbased_orig_060415/remapping_ccpbased_orig", 'CCPRM_ORIG', None, 'CCPRM$_{\\rmV1}$'],                            
                            #[base_dir + "remapping_ccpbased_single_cluster_orig", 'CCPRM_SINGLECLUSTER_ORIG', None],
                                                        
                            ## CCPRM - improved
                            [base_dir + "remapping_ccpbased", 'CCPRM_IMP', None, 'CCPRM$_{\\rmV2}$'],                            
                            #[base_dir + "remapping_ccpbased_single_cluster", 'CCPRM_SINGLECLUSTER_IMP', "plot_cumsum_improvement_distributions_all_techniques_datafile.js", 'Centralised\nmanagement'],
                                                        
                            ## random
                            #[base_dir + "remapping_randombased", 'RANDOMANY', "plot_cumsum_improvement_distributions_all_techniques_datafile.js", "Random\nremapping"]
                            #["Z:/MCASim/experiment_data/remapping_central_dynamic", 'FULLYDYNAMIC', None],
                        ]
    
    all_algorithm_data = OrderedDict()
    
    if(data_filename == None):    
        for each_exp_dir in LIST_EXP_DATA_DIRS:
            
            EXP_DATA_DIR = each_exp_dir[0]
            EXP_LABEL = each_exp_dir[1]            
            DATAFILENAME = each_exp_dir[2]
            EXP_LABEL_2 = each_exp_dir[3]
            
            if (DATAFILENAME == None):
            
                print "------------------------------------------------"
                print EXP_LABEL
                print "------------------------------------------------"
                    
                all_exp_data = {}
                for each_seed in RANDOM_SEED_LIST[:INTERESTED_SEEDS]:
                    
                    MULTISEED_EXP_DATA_DIR = EXP_DATA_DIR + "/seed_" + str(each_seed)
                    try:            
                        # get remapping-off data
                        FNAME_PREFIX = "RMOFF_"    
                        fname = MULTISEED_EXP_DATA_DIR + "/" + FNAME_PREFIX + "test__gopsopbuffsumm.js"    
                        print fname
                        json_data=open(fname)
                        remapping_off_data = json.load(json_data)                
                        
                        # get remapping-off data
                        FNAME_PREFIX = "RMON_"    
                        fname = MULTISEED_EXP_DATA_DIR + "/" + FNAME_PREFIX + "test__gopsopbuffsumm.js"   
                        print fname
                        json_data=open(fname)
                        remapping_on_data = json.load(json_data)
                    except:
                        print "------"
                        print "file not found !"
                        print fname
                        print "------"
                        continue
                    
                    
                    ### lateness ###
                    gop_lateness_distribution_rmoff = []
                    gop_lateness_distribution_rmon = []        
                    # gop lateness distribution - rm-off
                    for each_ugid_key, each_ugid_val in remapping_off_data.iteritems():
                        if(each_ugid_val['gop_execution_lateness'] > 0):
                            gop_lateness_distribution_rmoff.append(each_ugid_val['gop_execution_lateness'])        
                    if(len(gop_lateness_distribution_rmoff)==0):
                        gop_lateness_distribution_rmoff = [0]           
                    
                    # gop lateness distribution - rm-on
                    for each_ugid_key, each_ugid_val in remapping_on_data.iteritems():
                        if(each_ugid_val['gop_execution_lateness'] > 0):
                            gop_lateness_distribution_rmon.append(each_ugid_val['gop_execution_lateness'])        
                    if(len(gop_lateness_distribution_rmon)==0):
                        gop_lateness_distribution_rmon = [0]
                            
                    ### response-time ###
                    all_distributions = [gop_lateness_distribution_rmoff, gop_lateness_distribution_rmon]
                    
                    all_exp_data[each_seed] = { 'all_distributions' : all_distributions }
                    
                 
                summary = OrderedDict()                       
                summary['seed'] = []
                summary['size_gopl_dist_rmoff'] =  [] 
                summary['size_gopl_dist_rmon'] =  []
                summary['mean_gopl_rmoff'] =  []
                summary['mean_gopl_rmon'] =  []
                summary['max_gopl_rmon'] = []
                summary['max_gopl_rmoff'] =  []                                
                summary['size_gopl_variance'] = []
                summary['improvement_sum_gopl'] = []
                summary['improvement_mean_gopl'] = []
                summary['improvement_max_gopl'] = []
                summary['improvement_mean_gop_rt'] = []
                summary['improvement_max_gop_rt'] = []
        
                for k, each_seed_v in all_exp_data.iteritems():
                    # calculate means, max, variances, etc
                    sum_gopl = [np.sum(x) for x in all_exp_data[k]['all_distributions']]
                    means_gopl =  [np.mean(x) for x in all_exp_data[k]['all_distributions']]      
                    max_lateness_gopl = [np.max(x) for x in all_exp_data[k]['all_distributions']]
                    size_gopl_dist_rm_off = len(all_exp_data[k]['all_distributions'][0])
                    size_gopl_dist_rm_on = len(all_exp_data[k]['all_distributions'][1])
                    size_gopl_variance = (size_gopl_dist_rm_off - size_gopl_dist_rm_on)
                    
                    summary['seed'].append(k)
                    summary['size_gopl_dist_rmoff'].append(size_gopl_dist_rm_off)
                    summary['size_gopl_dist_rmon'].append(size_gopl_dist_rm_on)
                    summary['mean_gopl_rmoff'].append(means_gopl[0])
                    summary['mean_gopl_rmon'].append(means_gopl[1])
                    summary['max_gopl_rmon'].append(max_lateness_gopl[0])
                    summary['max_gopl_rmoff'].append(max_lateness_gopl[1])                                
                    summary['size_gopl_variance'].append(size_gopl_variance)
                    summary['improvement_sum_gopl'].append(np.round(1.0*(float(100.0*((sum_gopl[0]-sum_gopl[1])/sum_gopl[0]))),3))
                    summary['improvement_mean_gopl'].append(np.round(1.0*(float(100.0*((means_gopl[0]-means_gopl[1])/means_gopl[0]))),3))
                    summary['improvement_max_gopl'].append(np.round(1.0*(float(100.0*((max_lateness_gopl[0]-max_lateness_gopl[1])/max_lateness_gopl[0]))),3))
                    
                all_algorithm_data[EXP_LABEL] = summary
                
                print "------------"
                print "statistical significance :: Wilcoxon signed-rank test"
                data_exp_condition_1_rmoff = [np.sum(each_seed_v['all_distributions'][0]) 
                                              for each_seed_k, each_seed_v in all_exp_data.iteritems()] 
                
                data_exp_condition_2_rmon = [np.sum(each_seed_v['all_distributions'][1]) 
                                              for each_seed_k, each_seed_v in all_exp_data.iteritems()]
                
                (T, p) = scipy.stats.wilcoxon(data_exp_condition_2_rmon, data_exp_condition_1_rmoff)
                print "p = " + str(p)
                print "T = " + str(T)
                
                print "statistical significance :: mann-whitneyU test"
                (U,p) = scipy.stats.mannwhitneyu(data_exp_condition_1_rmoff, data_exp_condition_2_rmon)
                print "p = " + str(p)
                print "U = " + str(U)
                
                print "confidence interval:"
                (m, neg, pos) = _mean_confidence_interval(summary['improvement_sum_gopl'])
                print m, neg, pos
                
                print "------------"
            
                
            else:
                print "------------------------------------------"
                print EXP_LABEL  + " :: loading from local file"
                print "------------------------------------------"
                json_data=open(DATAFILENAME)
                all_algorithm_data[EXP_LABEL] = json.load(json_data)[EXP_LABEL]
        
    else:
        print "plot_cumsum_improvement_distributions_all_techniques :: loading data from file"
        json_data=open(data_filename)
        all_algorithm_data = json.load(json_data)
        
    if show_plot == True:
        # plot distribution of gop_lateness reduction for every technique
        #order_of_remappers = ['PSRM_EXP' , 'CCPRM_IMP', 'CCPRM_SINGLECLUSTER_IMP', 'RANDOMANY']
        #order_of_remappers = ['PSRM_MEM_OFF' , 'PSRM_MEM_ON']
        order_of_remappers = ['CCPRM_ORIG','CCPRM_IMP']
        
        remapper_labels = {
                           'PSRM_MEM_OFF': "PSRM\n(Mem. disabled)",
                           'PSRM_MEM_ON' : "PSRM\n(Mem. enabled)",
                           'CCPRM_ORIG' : "CCPRM"
                                                      
                           }
        
        #all_data = [each_exp_v['improvement_sum_gopl'] for each_exp_k, each_exp_v in  all_algorithm_data.iteritems()]
        #all_data_means = [np.mean(each_exp_v['improvement_sum_gopl']) for each_exp_k, each_exp_v in  all_algorithm_data.iteritems()]
        
        all_data = [all_algorithm_data[k]['improvement_sum_gopl'] for k in order_of_remappers]
        all_data_means = [np.mean(all_algorithm_data[k]['improvement_sum_gopl']) for k in order_of_remappers]
        
        print all_data_means
        all_bp_labels =  [x[3] for x in LIST_EXP_DATA_DIRS]
           
        f , ax= plt.subplots(figsize=(4.1, 4.8))
        f.canvas.set_window_title('GOPL_SUM Improvement distribution - all_techniques')
        pos = np.arange(len(all_bp_labels))
        #lbls = [remapper_labels[x] for x in order_of_remappers]
        bp = ax.boxplot(all_data ,0,'', whis=1.5, positions=pos, widths=0.5, patch_artist=True)
        
        _stylize_boxplots(bp)
        
        #blue = sns.color_palette()[0]
        
        
        ax.plot(pos, all_data_means, label='Mean', marker='d', linestyle='', color='r')
        ax.tick_params(axis='both', labelsize=14)
        plt.grid(True)
        plt.xticks(pos, all_bp_labels, fontsize=14)
        plt.ylabel('% Job lateness improvement', fontsize=14)
        l = plt.legend(numpoints=1)
        l.draggable()
        plt.tight_layout()
        plt.subplots_adjust(left=0.16, right=0.99, top=0.97, bottom=0.07)
    
    return all_algorithm_data











###################################
#    HELPERS
###################################
def _stylize_boxplots(bp, c_boxface='#348ABD', c_boxline='k', 
                            c_cap='k', c_wh='k', c_fly='k'):
    # stylise boxplots
    for box, medians in zip(bp['boxes'], bp['medians']):            
            plt.setp(box, color='k', linewidth=1.25)
            plt.setp(box, facecolor=c_boxface)
            plt.setp(medians,linewidth=1.25, color=c_boxline)        
    for caps in bp['caps']:            
        plt.setp(caps, linewidth=1.25, color=c_cap)    
    for whiskers in bp['whiskers']:            
        plt.setp(whiskers, linewidth=1.25, color=c_wh)    
    for fliers in bp['fliers']:            
        plt.setp(fliers, linewidth=1.25, color=c_fly)
    

def _get_cpu_busytime_allnodes(sysutil_data):    
    all_nodes_idle_times = sysutil_data["node_idle_time"]['it_c']
    total_time = sysutil_data["node_idle_time"]["time"]
    
    all_nodes_busy_times = [(total_time - x) for x in all_nodes_idle_times]
        
    norm_all_nodes_idle_times = _normalise_list(all_nodes_idle_times)
    norm_all_nodes_busy_times = _normalise_list(all_nodes_busy_times)
    
    #rounded_norm_all_nodes_busy_times = [round(x,2) for x in norm_all_nodes_busy_times]
    
    return all_nodes_busy_times
    
    


# any flow_type other than [0,1,6,7] is considered overhead
def _get_comms_overhead(flwscompleted_file_data):
    intfs_count = 0.0
    count = 0.0
    DATA_FLOWS = [0,1,8,9]
    all_control_flow_durations = []
    all_control_flow_durations = [f['bl'] for f in flwscompleted_file_data if(f['type'] not in DATA_FLOWS)]
    
#     for each_flw_completed in flwscompleted_file_data:
#         if(each_flw_completed['type'] not in DATA_FLOWS):
#             flow_rt = each_flw_completed['et'] - each_flw_completed['st']
#             flow_bl = each_flw_completed['bl']
#             all_control_flow_durations.append(flow_bl)

    return np.sum(all_control_flow_durations)


def _get_num_vids_fully_scheduled(wf_data):
    total_true = []
    for each_wf_id, each_wf in wf_data.iteritems():
        for each_vidstrm_id, each_vidstrm in each_wf.iteritems():
            result = each_vidstrm['result']
            if result == True:
                total_true.append([each_wf_id, each_vidstrm_id])
    
    return len(total_true)
            
def _get_num_gops_late(wf_data):
    num_gops_late = []
    for each_wf_id, each_wf in wf_data.iteritems():
        for each_vidstrm_id, each_vidstrm in each_wf.iteritems():
            if "gops_late_but_fully_complete" in each_vidstrm:            
                result = len(each_vidstrm["gops_late_but_fully_complete"])
                num_gops_late.append(result)            
    
    return np.sum(num_gops_late)
    
                    
        
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


def _get_resfactor_specific_info(data_wfressumm):
    vs_specific_data = {}
    
    for each_wf_id, each_wf in data_wfressumm.iteritems():
        for each_vs_id, each_vs in each_wf.iteritems():
            res_factor = each_vs["res_w"] * each_vs["res_h"]
            print "wf=" + str(each_wf_id) + ",vs=" + str(each_vs_id) + ", res="+str(res_factor)
            
            try:
                if(each_vs['result'] == False):
                    if res_factor not in vs_specific_data:
                        vs_specific_data[res_factor] = {
                                                        'h' : each_vs["res_h"],
                                                        'w' : each_vs["res_w"],
                                                        'gops_late_but_fully_complete' : each_vs["gops_late_but_fully_complete"],                                                        
                                                        'res' : res_factor,
                                                        'lateness' : []                                                                                                      
                                                        }
                    else:                    
                        vs_specific_data[res_factor]['gops_late_but_fully_complete'].extend(each_vs["gops_late_but_fully_complete"])
                else:
                    if res_factor not in vs_specific_data:
                        vs_specific_data[res_factor] = {
                                                        'h' : each_vs["res_h"],
                                                        'w' : each_vs["res_w"],
                                                        'gops_late_but_fully_complete' : [-1],
                                                        'res' : res_factor,
                                                        'lateness' : [0.0]                                             
                                                        }                    
                    
            except:
                pprint.pprint(each_vs)               
                sys.exit("error")
    
    
    return vs_specific_data
            


def _mean_confidence_interval(data, confidence=0.95):
    a = 1.0*np.array(data)
    n = len(a)
    m, se = np.mean(a), scipy.stats.sem(a)
    h = se * scipy.stats.t._ppf((1+confidence)/2., n-1)
    return m, m-h, m+h


def _write_formatted_file(fname, data, format):        
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
            


###################################
#    MAIN
###################################

#plot_resptime_variance_multiseed(xaxis_key='dt')
print "========================================================================"
#plot_GoP_lateness_multiseed()
#plot_GoP_lateness_vs_pri_multiseed()


result = plot_cumsum_improvement_distributions_all_techniques(data_filename='plot_cumsum_improvement_distributions_all_techniques_datafile_ccprmcompare.js',
                                                              show_plot=True)
#_write_formatted_file('plot_cumsum_improvement_distributions_all_techniques_datafile_ccprmcompare.js', result, 'json')


result = plot_flows_completed(data_filename = 'plot_flows_completed_datafile_ccprmcompare.js',
                              show_plot=True)
#_write_formatted_file('plot_flows_completed_datafile_ccprmcompare.js', result, 'json')


#result = plot_num_vids_fully_scheduled()
#_write_formatted_file('plot_num_vids_fully_scheduled.js', result, 'json')

#result = plot_systemidletime_histogram()


print "========================================================================"
#plot_SeedCCDistributions()

#plot_flows_completed()

print len(RANDOM_SEED_LIST[:INTERESTED_SEEDS])

print "finished"

plt.show()

