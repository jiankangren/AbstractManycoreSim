import sys, os, csv, pprint, math

from collections import OrderedDict
import numpy as np
import random
import shutil
import math
import matplotlib.gridspec as gridspec
import matplotlib.patches as patches

## uncomment when running under CLI only version ##
#import matplotlib
#matplotlib.use('Agg')

import matplotlib.pyplot as plt
plt.style.use('ggplot')
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

from matplotlib.colors import colorConverter
#from aifc import data

NOC_SIZE = [8,8]

EXP_DIR = "" 

def _set_bp(ax, bp, col):
    plt.setp(bp['boxes'], color=col, linewidth=1, alpha=0.7)    
    plt.setp(bp['caps'], color=col)
    plt.setp(bp['whiskers'], color=col)
    plt.setp(bp['fliers'], color=col)
    plt.setp(bp['medians'], color=col)
    



def plot_taskalloc_pcolor(obuff_tasks_fname, lbl=""):    
    print "plot_taskalloc_pcolor"            
    print obuff_tasks_fname
    
    # create empty dict
    all_data_cc = dict((i,[]) for i in range(NOC_SIZE[0]*NOC_SIZE[1])) # comp cost
    all_data_numt = dict((i,0) for i in range(NOC_SIZE[0]*NOC_SIZE[1])) # num tasks
        
    json_data=open(obuff_tasks_fname)
    obuff_file_data = json.load(json_data)
    
    for t in obuff_file_data:
        all_data_cc[t['pe']].append(t['cc'])
        all_data_numt[t['pe']] += 1
    
    sorted_all_data_cc = np.array([np.sum(all_data_cc[k]) for k in sorted(all_data_cc.keys())])            
    sorted_all_data_numt = np.array([all_data_numt[k] for k in sorted(all_data_numt.keys())])
        
    reshaped_all_data_cc = sorted_all_data_cc.reshape((NOC_SIZE[0], NOC_SIZE[1])) 
    reshaped_all_data_numt = sorted_all_data_numt.reshape((NOC_SIZE[0], NOC_SIZE[1]))
        
    f1, ax = plt.subplots(1,2)
    f1.canvas.set_window_title('plot_taskalloc_pcolor -'+lbl)
        
    pc1 = ax[0].pcolor(np.flipud(reshaped_all_data_cc), cmap='hot', edgecolors='g', linewidths=1)
    ax[0].set_title('reshaped_all_data_cc')
    ax[0].set_axis_off()
    ax[0].grid(True)    
    plt.colorbar(pc1, ax=ax[0])
        
    pc2 = ax[1].pcolor(np.flipud(reshaped_all_data_numt), cmap='hot', edgecolors='g', linewidths=1)
    ax[1].set_title('reshaped_all_data_numt')
    ax[1].set_axis_off()
    ax[1].grid(True)
    plt.colorbar(pc2, ax=ax[1])

    # report stats
    print  "sorted_all_data_cc: mean =", np.mean(sorted_all_data_cc)
    print  "sorted_all_data_cc: std =", np.std(sorted_all_data_cc)    
    print "-----------" 
    print  "sorted_all_data_numt: mean =", np.mean(sorted_all_data_numt)
    print  "sorted_all_data_numt: std =", np.std(sorted_all_data_numt)
    
    



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




###################################
#    HELPERS
###################################
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

plot_taskalloc_pcolor(
        obuff_tasks_fname="Z:/MCASim/experiment_data/hevc_tile_mapping_wMemPSel_HighCCR/WL2/ac0mp0pr0cmb914mmp4/seed_33749/HEVCTileSplitTest__ac0mp0pr0cmb914mmp4_8_8__obuff.js",
        lbl="mmp4") 
                                 
plot_taskalloc_pcolor(
        obuff_tasks_fname="Z:/MCASim/experiment_data/hevc_tile_mapping_wMemPSel_HighCCR/WL2/ac0mp0pr0cmb914mmp30/seed_33749/HEVCTileSplitTest__ac0mp0pr0cmb914mmp30_8_8__obuff.js",
        lbl="mmp30") 



print "finished"

plt.show()

