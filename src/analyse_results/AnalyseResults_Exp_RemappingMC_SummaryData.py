import sys, os, csv, pprint, math

from collections import OrderedDict
import numpy as np
import random
import shutil
import math
import matplotlib
matplotlib.use('Qt4Agg')
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

import seaborn.apionly as sns

plt.style.use('bmh_rosh')

NUM_WORKFLOWS = range(8, 19, 1)
#NUM_WORKFLOWS = [9]
#NUM_NODES = [2,4,8,16,32]
NUM_NODES = 9
NOC_XY = [(2,1), (2,2), (2,4), (2,8), (2,16)]


IBUFF_TASKS_LATENESS_RATIO_RANGE    = [0.3, 0.7]
TQ_TASKS_LATENESS_RATIO_RANGE       = [0.3, 0.7]        

SEED = 26358

# location for thesis draft
#EXP_DATA_DIR = "Z:/MCASim/experiment_data/remapping_psbased_montecarlo"
#EXP_DATA_DIR = "Z:/MCASim/experiment_data/remapping_ccpbased_montecarlo"

# location after BL fix
EXP_DATA_DIR = "Z:/Simulator_versions_perExperiment/ThesisTechCh6_PSRM/src/experiment_data/remapping_psbased_montecarlo/"




RANDOM_SEED_LIST = \
[33749, 70263, 80505, 26358, 
83660, 74076, 80521, 64217, 53864, 
22250, 69433, 26044, 22817, 
44117, 83200, 29917, 43894, 66093, 
99108, 81665, 77379, 44289, 21149,
5558, 42198, 69541, 18065, 57824]


#[44289, 99108, 88117, 29917, 83660, 42198, 73337, 94064]


NUM_ROWS = 5
NUM_COLS = 7

INTERESTED_SEEDS = len(RANDOM_SEED_LIST)
INTERESTED_SEEDS = 40
    
    
###################################################################################################
#    ResponseTime - Remapping off/on
###################################################################################################
def plot_resptime_variance():
        
    # get data
    fname = EXP_DATA_DIR + "/" + "summary_obuff.js"    
    json_data=open(fname)
    summary_obuff_data = json.load(json_data)
    json_data.close()
    
    result_diff_gb_allseeds = []
    for each_param_key, each_param_val in summary_obuff_data.iteritems():
        diff_g_b = []
        for each_seed_key, each_seed_val in each_param_val.iteritems():
            diff_g_b.append((each_seed_val['pos_variances_size']-each_seed_val['neg_variances_size']))
        
        result_diff_gb_allseeds.append({
                                        'param_key' : each_param_key,
                                        'diff_mean' : np.mean(diff_g_b),
                                        'diff_distibution' : diff_g_b
                                        })
    
    # sort according to mean
    sorted_result_diff_gb_allseeds = sorted(result_diff_gb_allseeds, key=itemgetter('diff_mean'), reverse=True)
        
    fig = plt.figure()   
    fig.canvas.set_window_title('plot_resptime_variance-line') 
    
    x_axis = [x['param_key'] for x in sorted_result_diff_gb_allseeds]
    y_data = [x['diff_mean'] for x in sorted_result_diff_gb_allseeds]
    
    plt.plot(range(0,len(x_axis)), y_data, marker='x') 
    #plt.yscale('log')
    plt.grid(True)        
    

def _set_bp(ax, bp, col):
    plt.setp(bp['boxes'], color=col, linewidth=1, alpha=0.7)    
    plt.setp(bp['caps'], color=col)
    plt.setp(bp['whiskers'], color=col)
    plt.setp(bp['fliers'], color=col)
    plt.setp(bp['medians'], color=col)
    


def plot_GoP_lateness_summary():
    
    # get data
    fname = EXP_DATA_DIR + "/" + "summary_gopsumm.js"    
    json_data=open(fname)
    summary_gopsumm_data = json.load(json_data)
    json_data.close()
    
    result_improvementmean_allseeds = []
    for each_param_key, each_param_val in summary_gopsumm_data.iteritems():
        improvement_mean = []
        for each_seed_key, each_seed_val in each_param_val.iteritems():
            improvement_mean.append(each_seed_val['improvement_mean_lateness'])
        
        result_improvementmean_allseeds.append({
                                        'param_key' : each_param_key,
                                        'mean_improvement_mean' : np.mean(improvement_mean),
                                        'improvement_mean' : improvement_mean
                                        })
    
    # sort according to mean
    sorted_result_improvementmean_allseeds = sorted(result_improvementmean_allseeds, key=itemgetter('mean_improvement_mean'), reverse=True)
    
    ## print keys onto log
    f = open("mc_summary_keys.csv", 'a')
    for ix, each_item in enumerate(sorted_result_improvementmean_allseeds):
        f.write("%d,%s \n"%(ix,each_item['param_key']))
    f.close()
    
    fig = plt.figure()   
    fig.canvas.set_window_title('plot_GoP_lateness_summary-line') 
    
    x_axis = [x['param_key'] for x in sorted_result_improvementmean_allseeds]
    y_data = [x['mean_improvement_mean'] for x in sorted_result_improvementmean_allseeds]
    
    plt.plot(range(0,len(x_axis)), y_data, marker='x') 
    #plt.yscale('log')
    plt.grid(True)
    

def plot_overall_mean_GOPL_mean_improvement():    
    # get data
    fname = EXP_DATA_DIR + "/" + "mcparam_final_results.js"    
    json_data=open(fname)
    file_data = json.load(json_data)
    json_data.close()
    
    x_data = [x['param'] for x in file_data]
    #y_data = sorted([100.0*float(x['overall_mean_GOPL_cum_improvement']) for x in file_data])
    y_data = [100.0*float(x['overall_mean_GOPL_cum_improvement']) for x in file_data]
    
    fig = plt.figure()   
    fig.canvas.set_window_title('overall_mean_GOPL_cum_improvement-line')
    
    plt.plot(range(0,len(x_data)), y_data, marker='x', linestyle='') 
    plt.grid(True)
    
      
def plot_overall_mean_GOPL_mean_improvement_boxplots():
    
    # get data
    fname = EXP_DATA_DIR + "/" + "mcparam_final_results.js"    
    json_data=open(fname)
    file_data = json.load(json_data)
    json_data.close()
    
    x_data = [x['param'] for x in file_data]    
    y_data = []
    
    gopl_data_dict = {}
    
    # add ids to the params
    i = 1
    for ix, each_p in enumerate(file_data):
        
#         if(np.median(each_p['all_GOPL_mean_dist_values']) > 0):            
#             param_id = ix
#             y_data.append(each_p['all_GOPL_mean_dist_values'])
        
        param_id = ix
        y_data.append(each_p['all_GOPL_mean_dist_values'])
        
        print i, param_id, each_p['param'], each_p['overall_mean_GOPL_cum_improvement'], np.median(each_p['all_GOPL_mean_dist_values'])
        i+= 1

    fig = plt.figure()   
    fig.canvas.set_window_title('plot_all_GOPL_mean_dist_values_boxplot') 
   
    plt.boxplot(y_data)    
    plt.grid(True)    
    plt.tick_params(axis='x', labelsize=8)





def plot_combined():
    
    # get data
    fname = EXP_DATA_DIR + "/" + "mcparam_final_results.js"    
    json_data=open(fname)
    file_data = json.load(json_data)
    json_data.close()
    
    x_data = [x['param'] for x in file_data]    
    x_data_vals_only =  [x['param'].replace("perm_", "") for x in file_data]
    y_data_1 = []
    y_data_2 = []
    
    gopl_data_dict = {}
    
    # add ids to the params
    i = 1
    for ix, each_p in enumerate(file_data):
        
#         if(np.median(each_p['all_GOPL_mean_dist_values']) > 0):            
#             param_id = ix
#             y_data.append(each_p['all_GOPL_mean_dist_values'])
        
        param_id = ix
        y_data_1.append(each_p['all_GOPL_mean_dist_values'])
        y_data_2.append(100.0*float(each_p['overall_mean_GOPL_cum_improvement']))
        
        print i, param_id, each_p['param'], each_p['overall_mean_GOPL_cum_improvement'], np.median(each_p['all_GOPL_mean_dist_values'])
        i+= 1

    fig, ax1 = plt.subplots()
    fig.canvas.set_window_title('combined') 
   
    bps = ax1.boxplot(y_data_1, patch_artist=True, sym='x')
    _stylize_boxplots(bps)   
    
    tex_params = "$T_{QN}$, " + \
                "$T_{DECAY}$, " + \
                "$HC$, " + \
                "$T_{RM}$, " + \
                "$H_{QN}$, " + \
                r"$Q_{TH}^{\alpha}$, " + \
                r"$Q_{TH}^{\beta}$, " + \
                "$K_{HDECAY}$, " + \
                "$K_{TDECAY}$"
    
    ax1.set_xlabel('Parameter combination\n'+tex_params, fontsize=13)
    ax1.set_ylabel('Distribution of mean job lateness improvement (per seed)', fontsize=13)
    ax1.tick_params(axis='x', labelsize=9)
    ax1.tick_params(axis='y', labelsize=9)
    ax1.set_xlim([-0.5, len(x_data_vals_only)+1.5])
    
    ax1.set_xticks(range(1,len(x_data_vals_only)+1))
    ax1.set_xticklabels(x_data_vals_only, rotation=90)
    
    
    
    ax2 = ax1.twinx()
    ax2.plot(range(1,len(y_data_2)+1), y_data_2, marker='d', linestyle='-', color='r') 
    ax2.set_ylabel('Cumulative job lateness improvement (mean of all seeds)', color='r', fontsize=13)
    ax2.tick_params(axis='y', colors='r', labelsize=9)
    
    ax2.format_coord = make_format(ax2, ax1)
    
    ax1.axhline(y=0.0, color='y')
    
    #plt.grid(True)    
    

    








###################################
#    HELPERS
###################################
def _stylize_boxplots(bp, c_boxface='#348ABD', c_boxline='k', 
                            c_cap='k', c_wh='k', c_fly='k'):
    # stylise boxplots
    for box, medians in zip(bp['boxes'], bp['medians']):            
            plt.setp(box, color='k', linewidth=1.25)
            plt.setp(box, facecolor=c_boxface)
            plt.setp(medians,linewidth=1.25, color='#99d8c9')        
    for caps in bp['caps']:            
        plt.setp(caps, linewidth=1.25, color=c_cap)    
    for whiskers in bp['whiskers']:            
        plt.setp(whiskers, linewidth=1.25, color=c_wh)    
    for fliers in bp['fliers']:            
        plt.setp(fliers, linewidth=1.25, color=c_fly)
        
def _movingaverage (values, window):
    weights = np.repeat(1.0, window)/window
    sma = np.convolve(values, weights, 'same')
    return sma

def make_format(current, other):
    # current and other are axes
    def format_coord(x, y):
        # x, y are data coordinates
        # convert to display coords
        display_coord = current.transData.transform((x,y))
        inv = other.transData.inverted()
        # convert back to data coords with respect to ax
        ax_coord = inv.transform(display_coord)
        coords = [ax_coord, (x, y)]
        return ('Left: {:<40}    Right: {:<}'
                .format(*['({:.3f}, {:.3f})'.format(x, y) for x,y in coords]))
    return format_coord




###################################
#    MAIN
###################################

#plot_overall_mean_GOPL_mean_improvement()
#plot_overall_mean_GOPL_mean_improvement_boxplots()
#plot_GoP_lateness_summary()

plot_combined()

print "finished"

plt.show()

