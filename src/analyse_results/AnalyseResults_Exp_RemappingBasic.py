import sys, os, csv, pprint, math
import traceback

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



NUM_NODES = 9
IBUFF_TASKS_LATENESS_RATIO_RANGE    = [0.3, 0.7]
TQ_TASKS_LATENESS_RATIO_RANGE       = [0.3, 0.7]        

SEED = 26358

#EXP_DATA_DIR = "../experiment_data/remapping_ccpbased"
#EXP_DATA_DIR = "../experiment_data/remapping_randombased"
#EXP_DATA_DIR = "../experiment_data/remapping_psbased"
#EXP_DATA_DIR = "../experiment_data/remapping_psbased_montecarlo"
EXP_DATA_DIR = "../experiment_data/remapping_central_dynamic"

RANDOM_SEED_LIST = \
[81665, 33749, 43894, 26358, 80505, \
 83660, 22817, 70263, 29917, 26044, \
 5558,  76891, 22250, 42198, 18065, \
 74076, 98652, 21149, 50399, 64217, \
 44117, 57824, 42267, 83200, 99108, \
 95928, 53864, 44289, 77379, 80521, \
 88117, 23327, 73337, 94064, 31982, \
 6878, 66093, 69541]


###################################################################################################
#    Id vs. BlockingTime vs. Lateness vs. InputBuffWaitTime
###################################################################################################
    
def plot_Id_vs_BlockingTime_vs_Lateness_vs_InputBuffWaitTime():                
    
    mcols = itertools.cycle(['r', 'g', 'b', 'c', 'm', 'y', 'k'])
    
    # get remapping-off data
    FNAME_PREFIX = "RMOFF_"    
    fname = EXP_DATA_DIR + "/" + FNAME_PREFIX + "test__obuff.js"    
    json_data=open(fname)
    remapping_off_data = json.load(json_data)
    
    # get remapping-off data
    FNAME_PREFIX = "RMON_"    
    fname = EXP_DATA_DIR + "/" + FNAME_PREFIX + "test__obuff.js"    
    json_data=open(fname)
    remapping_on_data = json.load(json_data)
                   
    # sort them according to id
    sorted_remapping_off_data = sorted(remapping_off_data, key=itemgetter('id')) 
    sorted_remapping_on_data = sorted(remapping_on_data, key=itemgetter('id'))
    
    # get the necessary data
    remapping_off_data_dict = _get_blt_lt_ibwt(sorted_remapping_off_data)
    remapping_on_data_dict = _get_blt_lt_ibwt(sorted_remapping_on_data)
    
    f, axarr = plt.subplots(len(remapping_off_data_dict.keys())-1, 2, sharex=True)
    f.canvas.set_window_title('plot_Id_vs_BlockingTime_vs_Lateness_vs_InputBuffWaitTime')
    
    i=0
    for k,v in remapping_off_data_dict.iteritems():
        if(k!= 'task_ids'):
            
            c = mcols.next()
            # plot remapping-off
            axarr[i,0].set_title(k)
            axarr[i,0].scatter(remapping_off_data_dict['task_ids'], remapping_off_data_dict[k], marker='.', color=c)
            axarr[i,0].xaxis.grid()
            axarr[i,0].yaxis.grid()
            
            # plot remapping-on
            axarr[i,1].set_title(k)
            axarr[i,1].scatter(remapping_on_data_dict['task_ids'], remapping_on_data_dict[k], marker='.', color=c)
            axarr[i,1].xaxis.grid()
            axarr[i,1].yaxis.grid()
    
            i+=1



def plot_ugid_vs_goprt_variance():                
    
    mcols = itertools.cycle(['r', 'g', 'b', 'c', 'm', 'y', 'k'])
    
    # get remapping-off data
    FNAME_PREFIX = "RMOFF_"    
    fname = EXP_DATA_DIR + "/" + FNAME_PREFIX + "test__gopsopbuffsumm.js"    
    json_data=open(fname)
    remapping_off_data = json.load(json_data)
    
    # get remapping-off data
    FNAME_PREFIX = "RMON_"    
    fname = EXP_DATA_DIR + "/" + FNAME_PREFIX + "test__gopsopbuffsumm.js"    
    json_data=open(fname)
    remapping_on_data = json.load(json_data)
                   
    # sort them according to id
    sorted_remapping_off_data = sorted(remapping_off_data.values(), key=itemgetter('gop_unique_id')) 
    sorted_remapping_on_data = sorted(remapping_on_data.values(), key=itemgetter('gop_unique_id'))
   
    # calc variance
    goprt_variance_list = []
    pos_var = []
    neg_var = []
    result_col = []
    ugid = []
    variance = []
    for each_gop_rmoff, each_gop_rmon in zip(sorted_remapping_off_data, sorted_remapping_on_data):        
        
        if(each_gop_rmoff['gop_unique_id'] != each_gop_rmon['gop_unique_id']): 
            sys.exit("error! : plot_ugid_vs_goprt_variance")
                
        rt_variance = each_gop_rmoff['tt_wrt_dt'] - each_gop_rmon['tt_wrt_dt']        
        goprt_variance_list.append([each_gop_rmoff['gop_unique_id'], rt_variance])
        
        if(rt_variance>0): # good
            result_col.append('g')
            variance.append(rt_variance)
            ugid.append(each_gop_rmoff['gop_unique_id'])
        elif(rt_variance<0): # bad
            result_col.append('r')
            variance.append(rt_variance)
            ugid.append(each_gop_rmoff['gop_unique_id'])
        else:
            #result_col.append('k')            
            a=1
    
    pprint.pprint(goprt_variance_list)
    
    f = plt.figure('plot_ugid_vs_goprt_variance')    
    plt.scatter(ugid, variance, marker='x', color=result_col)
    plt.grid(True)
      


def _get_blt_lt_ibwt(sorted_file_data):    
    result = {
                'task_pri' : [x['pri'] for x in sorted_file_data], 
                'task_blockingtime' : [ ((x['et']-x['rt'])-x['cc']) for x in sorted_file_data],
                'task_ibuff_watingtime' : [ (x['rt']-x['dt']) for x in sorted_file_data],
                'task_ids' : [x['id'] for x in sorted_file_data],
                'task_estlateness' : [x['estL'] for x in sorted_file_data],    
              }
    return result
    
    
###################################################################################################
#    ResponseTime - Remapping off/on
###################################################################################################
def plot_resptime_variance(exp_dir = None, exp_params = None, xaxis_key='dt', plot=True):
    
    all_variances = []
    negative_variances  = []
    positive_variances  = []
    rmoff_all_responsetimes = []
    rmon_all_responsetimes = []
    tids = []
    result_col = []
    
    neg_affected_tasks = []
    
    try:
        # get remapping-off data
        if(exp_params != None):
            FNAME_PREFIX = "RMOFF_"
            fname = exp_dir + FNAME_PREFIX + "test__obuffshort.js" 
        else:
            FNAME_PREFIX = "RMOFF_"    
            fname = EXP_DATA_DIR + "/" + FNAME_PREFIX + "test__obuffshort.js"            
        json_data=open(fname)
        remapping_off_data = json.load(json_data)
        
        # get remapping-on data
        if(exp_params != None):
            FNAME_PREFIX = "RMON_"
            fname = exp_dir + FNAME_PREFIX + exp_params + "test__obuffshort.js" 
        else:
            FNAME_PREFIX = "RMON_"    
            fname = EXP_DATA_DIR + "/" + FNAME_PREFIX + "test__obuffshort.js"    
        json_data=open(fname)
        remapping_on_data = json.load(json_data)
        
        # sort them according to id
        sorted_remapping_off_data = sorted(remapping_off_data, key=itemgetter(xaxis_key)) 
        sorted_remapping_on_data = sorted(remapping_on_data, key=itemgetter(xaxis_key))
        
        # get response_time variance for each task
        for ix,each_task in enumerate(sorted_remapping_off_data):
            rm_off_resptime = sorted_remapping_off_data[ix]['et']  - sorted_remapping_off_data[ix]['dt']
            rm_on_resptime = sorted_remapping_on_data[ix]['et']  - sorted_remapping_on_data[ix]['dt']
            
            rmoff_all_responsetimes.append(rm_off_resptime)
            rmon_all_responsetimes.append(rm_on_resptime)
            
            variance = rm_off_resptime - rm_on_resptime
            if(variance>0): # good
                result_col.append('g')
                positive_variances.append(variance)
            elif(variance<0): # bad
                result_col.append('r')
                negative_variances.append(variance)
                
                neg_affected_tasks.append(
                                          sorted_remapping_off_data[ix]
                                          )
            else:
                #result_col.append('b')
                a=1
                    
            if(variance >0 or variance<0):    
                tids.append(sorted_remapping_off_data[ix][xaxis_key])
                all_variances.append(variance)
        
        
        new_neg_affected_tasks = sorted([t['pri']
                                  for t in neg_affected_tasks])
        
        _write_formatted_file("neg_affected_files.js", new_neg_affected_tasks, "json")
        
                
    except Exception, err:
        print "plot_resptime_variance:: Error !!"
        print traceback.format_exc()
        
    
    if(plot==True):
        f, axarr = plt.subplots(2,1)
        f.canvas.set_window_title('plot_resptime_variance')
        
        axarr[0].scatter(tids, all_variances, marker='x', color=result_col)
        plt.grid(True)
        axarr[1].boxplot([rmoff_all_responsetimes, rmon_all_responsetimes],0,'', whis=1, positions=np.arange(2), widths=0.8)
        plt.grid(True)
        
        print np.sum(all_variances)
        print "num of negatively (bad) affected tasks = " + str(len(negative_variances))  
        print "num of positively (good) affected tasks = " + str(len(positive_variances))        
    
    if(len(all_variances)>0):       
        
        results = OrderedDict()        
        results['RT_num_neg_affected_tasks'] = len(negative_variances),
        results['RT_num_pos_affected_tasks'] = len(positive_variances),
        results['RT_mean_neg_affected_tasks'] = np.mean(negative_variances),
        results['RT_mean_pos_affected_tasks'] = np.mean(positive_variances),
        results['RT_rmoff_mean'] = np.mean(rmoff_all_responsetimes),
        results['RT_rmon_mean'] = np.mean(rmon_all_responsetimes),
        results['RT_rmoff_max'] = np.max(rmoff_all_responsetimes),
        results['RT_rmon_max'] = np.max(rmon_all_responsetimes),
        
    else:
        results = {
                  'RT_num_neg_affected_tasks' : None,
                  'RT_num_pos_affected_tasks' : None,
                  'RT_mean_neg_affected_tasks' : None,
                  'RT_mean_pos_affected_tasks' : None,
                  'RT_rmoff_mean' : None,
                  'RT_rmon_mean' : None,
                  'RT_rmoff_max' : None,
                  'RT_rmon_max' : None,
                  }
    
    return results
        
        
def _set_bp(ax, bp, col):
    plt.setp(bp['boxes'], color=col, linewidth=1, alpha=0.7)    
    plt.setp(bp['caps'], color=col)
    plt.setp(bp['whiskers'], color=col)
    plt.setp(bp['fliers'], color=col)
    plt.setp(bp['medians'], color=col)
    


def plot_GoP_lateness(exp_dir=None, exp_params=None, plot=True):
    
    gop_lateness_distribution_rmoff = []
    gop_lateness_distribution_rmon = []
    gop_rt_distribution_rmoff = []
    gop_rt_distribution_rmon = []
    
    all_gopL_distributions = []
    
    try:
        # ---- get data - RMOFF ----
        if(exp_params != None):
            FNAME_PREFIX = "RMOFF_"
            fname = exp_dir + FNAME_PREFIX + "test__gopsopbuffsummshort.js" 
        else:
            FNAME_PREFIX = "RMOFF_"    
            fname = EXP_DATA_DIR + "/" + FNAME_PREFIX + "test__gopsopbuffsummshort.js"    
        json_data=open(fname)
        remapping_off_data = json.load(json_data)
        
        # ---- get data - RMON ----
        if(exp_params != None):
            FNAME_PREFIX = "RMON_"
            fname = exp_dir + FNAME_PREFIX + exp_params + "_test__gopsopbuffsummshort.js" 
        else:
            FNAME_PREFIX = "RMON_"    
            fname = EXP_DATA_DIR + "/" + FNAME_PREFIX + "test__gopsopbuffsummshort.js"    
        json_data=open(fname)
        remapping_on_data = json.load(json_data)        
        
        # ---- gop lateness distribution - RMOFF ----
        for each_ugid_key, each_ugid_val in remapping_off_data.iteritems():
            if(each_ugid_val['gop_execution_lateness'] > 0):
                gop_lateness_distribution_rmoff.append(each_ugid_val['gop_execution_lateness'])        
        if(len(gop_lateness_distribution_rmoff)==0):
            gop_lateness_distribution_rmoff = [0]           
        
        # ---- gop lateness distribution - RMON ----
        for each_ugid_key, each_ugid_val in remapping_on_data.iteritems():
            if(each_ugid_val['gop_execution_lateness'] > 0):
                gop_lateness_distribution_rmon.append(each_ugid_val['gop_execution_lateness'])        
        if(len(gop_lateness_distribution_rmon)==0):
            gop_lateness_distribution_rmon = [0]
                
        # ---- gop response-time - RMOFF ----
        for each_ugid_key, each_ugid_val in remapping_off_data.iteritems():
            gop_rt_distribution_rmoff.append(each_ugid_val['tt_wrt_dt'])
        
        # ---- gop response-time - RMON ----
        for each_ugid_key, each_ugid_val in remapping_on_data.iteritems():
            gop_rt_distribution_rmon.append(each_ugid_val['tt_wrt_dt'])
                        
        all_gopL_distributions = [gop_lateness_distribution_rmoff, gop_lateness_distribution_rmon]
        
    except Exception, err:
        print "plot_GoP_lateness:: Error !!"
        print "--- traceback.format_exc() : Start ------"
        print traceback.format_exc()
        print "--- traceback.format_exc() : End ------"
    
    
    if(plot==True):
        # draw boxplots
        f, axarr = plt.subplots(1,1)
        f.canvas.set_window_title('plot_GoP_lateness')
        boxpos = np.arange(len(all_gopL_distributions))
        axarr.boxplot(all_gopL_distributions,0,'', whis=1, positions=boxpos, widths=0.8)
        means =  [np.mean(x) for x in all_gopL_distributions]      
        max_lateness = [max(x) for x in all_gopL_distributions]         
        axarr.plot(boxpos, means, marker='d', markersize=10, linestyle='--', color='g', linewidth=0.5, label="Mean job lateness")
        axarr.plot(boxpos, max_lateness, marker='o', markersize=10, linestyle='--', color='r', linewidth=0.5, label="Maximum job lateness")
        #axarr.set_yscale('log')
        axarr.grid(True)
        
        print "RMON gop-lateness-dist-size = " + str(len(gop_lateness_distribution_rmon))
        print "RMOFF gop-lateness-dist-size = " + str(len(gop_lateness_distribution_rmoff))
        print "RMON gop-lateness-dist-mean = " + str(np.mean(gop_lateness_distribution_rmon))
        print "RMOFF gop-lateness-dist-mean = " + str(np.mean(gop_lateness_distribution_rmoff))
        print "RMON gop-lateness-dist-cumulative = " + str(np.sum(gop_lateness_distribution_rmon))
        print "RMOFF gop-lateness-dist-cumulative = " + str(np.sum(gop_lateness_distribution_rmoff))
        
    if(len(all_gopL_distributions) >0):
        result = OrderedDict()
        
        result['GOPL_RMOFF_size'] = len(gop_lateness_distribution_rmoff),
        result['GOPL_RMON_size'] = len(gop_lateness_distribution_rmon)
                  
        result['GOP_RT_RMOFF_mean'] = np.mean(gop_rt_distribution_rmoff),
        result['GOP_RT_RMON_mean'] = np.mean(gop_rt_distribution_rmon),
                  
        result['GOP_RT_RMOFF_max'] = np.max(gop_rt_distribution_rmoff),
        result['GOP_RT_RMON_max'] = np.max(gop_rt_distribution_rmon),  
                  
        result['GOP_RT_RMOFF_sum'] = np.sum(gop_rt_distribution_rmoff),
        result['GOP_RT_RMON_sum'] = np.sum(gop_rt_distribution_rmon),  
        
        result['GOP_RT_sum_improvement'] = (np.sum(gop_rt_distribution_rmoff) - np.sum(gop_rt_distribution_rmon))/np.sum(gop_rt_distribution_rmoff),
                  
        result['GOPL_cum_improvement'] = ((np.sum(all_gopL_distributions[0]) - np.sum(all_gopL_distributions[1]))/np.sum(all_gopL_distributions[0])),
        result['GOPL_mean_improvement'] = ((np.mean(all_gopL_distributions[0]) - np.mean(all_gopL_distributions[1]))/np.mean(all_gopL_distributions[0])),
        result['GOPL_max_improvement'] = ((np.max(all_gopL_distributions[0]) - np.max(all_gopL_distributions[1]))/np.max(all_gopL_distributions[0])),
        
    else:
        result = {
                  'GOP_Error' : None,                  
                }
    
    return result
    
    

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
            


def generate_exp_results_summary(exp_dir, exp_params, plot=False):
    #plot_ugid_vs_goprt_variance()
    #result_rt_variance = plot_resptime_variance(exp_dir = exp_dir, exp_params=exp_params, xaxis_key='id', plot=plot)
    result_rt_variance = []
    result_gopl = plot_GoP_lateness(exp_dir = exp_dir, exp_params=exp_params, plot=plot)
    #pprint.pprint(result_gopl.items())
    final_result = OrderedDict()    
    final_result["result_rt_variance"] = result_rt_variance
    final_result["result_gopl"] = result_gopl
    
    
    
    return final_result


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


results = generate_exp_results_summary(None, None, plot=True)
pprint.pprint(results)
print "GOPL_cum_improvement :: ",
print results["result_gopl"]['GOPL_cum_improvement']

plt.show()