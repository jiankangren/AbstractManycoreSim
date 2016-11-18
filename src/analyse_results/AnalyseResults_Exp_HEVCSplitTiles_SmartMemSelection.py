import sys, os, csv, pprint, math

#sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

## uncomment when running under CLI only version ##
#import matplotlib
#matplotlib.use('Agg')

#sys.path.append("/shared/storage/cs/staffstore/hrm506/simpy-3.0.5/")
#sys.path.append("/shared/storage/cs/staffstore/hrm506/networkx-1.10/networkx-1.10")

from collections import OrderedDict
import numpy as np
import traceback
from collections import Iterable
import re
import pylab
import random
import shutil
import math
import matplotlib
import matplotlib.pyplot as plt
plt.style.use('ggplot')
from mpl_toolkits.mplot3d import Axes3D
import scipy.stats
import scipy.optimize as scipy_optimize
import itertools
from matplotlib.colors import ListedColormap, NoNorm, rgb2hex
from matplotlib import mlab
from itertools import cycle # for automatic markers
import json
from operator import itemgetter
from scipy import stats
from collections import Counter

import multiprocessing

import seaborn as sns
matplotlib.rc("lines", markeredgewidth=0.5)

#from scipy.stats import gaussian_kde


import matplotlib.ticker
import matplotlib.cm as cm
import matplotlib.patches as patches
from matplotlib.font_manager import FontProperties
from SimParams import SimParams


SHOW_PLOTS = True
USE_MULTIPROCESSING = False

NOC_H = 8
NOC_W = 8

MAX_SEEDS = 30

RANDOM_SEEDS_BATCH0=[12345, 33749, 43894, 26358, 80505]
RANDOM_SEEDS_BATCH1=[83660, 22817, 70263, 29917, 26044]
RANDOM_SEEDS_BATCH2=[5558, 76891, 22250, 42198, 18065]
RANDOM_SEEDS_BATCH3=[74076, 98652, 21149, 50399, 64217]
RANDOM_SEEDS_BATCH4=[44117, 57824, 42267, 83200, 99108]
RANDOM_SEEDS_BATCH5=[95928, 53864, 44289, 77379, 80521]
RANDOM_SEEDS_BATCH6=[87288, 21349, 68546, 74944, 94329]
RANDOM_SEEDS_BATCH7=[90611, 69799, 85870, 26771, 75638]

RANDOM_SEEDS = RANDOM_SEEDS_BATCH0 + \
               RANDOM_SEEDS_BATCH1 + \
               RANDOM_SEEDS_BATCH2
               
#FAILED_SEEDS = []
#RANDOM_SEEDS =[s for s in RANDOM_SEEDS if s not in FAILED_SEEDS][:MAX_SEEDS]

#RANDOM_SEEDS_MISC=[33749, 43894, 26358, 80505]


print len(set(RANDOM_SEEDS))

#sys.exit()

EXP_DATADIR = "../experiment_data/hevc_tile_mapping_wMemPSel/"
#EXP_DATADIR = "Z:/MCASim/experiment_data/\hevc_tile_mapping_wMemPSel/"

DATA_TEMP_SAVE_LOC = "../experiment_data/hevc_tile_mapping_wMemPSel/"

# CL(905) vs. CL-IPB(911)
global_types_of_tests = [
                    
                     # 914 (CL-BG)
                    {'mp':0, 'pr':0, 'cmb':914 , 'mmp':0, 'lbl': "CL-BG_MMPDist"},
                    #{'mp':0, 'pr':0, 'cmb':914 , 'mmp':1, 'lbl': "CL-BG_MMPLU"},
                    #{'mp':0, 'pr':0, 'cmb':914 , 'mmp':3, 'lbl': "CL-BG_MMPLUDist"},
                    #{'mp':0, 'pr':0, 'cmb':914 , 'mmp':4, 'lbl': "CL-BG_MMPRand"},

                    # 911 (CL-IPB)
                    {'mp':0, 'pr':0, 'cmb':911 , 'mmp':0, 'lbl': "CL-IPB_MMPDist"},
                    #{'mp':0, 'pr':0, 'cmb':911 , 'mmp':1, 'lbl': "CL-IPB_MMPLU"},
                    #{'mp':0, 'pr':0, 'cmb':911 , 'mmp':3, 'lbl': "CL-IPB_MMPLUDist"},
                    #{'mp':0, 'pr':0, 'cmb':911 , 'mmp':4, 'lbl': "CL-IPB_MMPRand"},
                    
                    # 903 (PP)
                    #{'mp':0, 'pr':0, 'cmb':912 , 'mmp':0, 'lbl': "PP"},
                    #{'mp':0, 'pr':0, 'cmb':912 , 'mmp':1, 'lbl': "PP_MMPLU"},
                    #{'mp':0, 'pr':0, 'cmb':912 , 'mmp':3, 'lbl': "PP_MMPLUDist"},
                    #{'mp':0, 'pr':0, 'cmb':912 , 'mmp':4, 'lbl': "PP_MMPRand"},
                    
                    # 903 (LU)
                    {'mp':0, 'pr':0, 'cmb':903 , 'mmp':0, 'lbl': "LU_MMPDist"},
                    #{'mp':0, 'pr':0, 'cmb':903 , 'mmp':1, 'lbl': "LU_MMPLU"},
                    #{'mp':0, 'pr':0, 'cmb':903 , 'mmp':3, 'lbl': "LU_MMPLUDist"},
                    #{'mp':0, 'pr':0, 'cmb':903 , 'mmp':4, 'lbl': "LU_MMPRand"},
                  
#                     
#                     {'mp':0, 'pr':0, 'cmb':910 , 'lbl': "CL-FFI"},
#                     {'mp':0, 'pr':0, 'cmb':906 , 'lbl': "CL-FO"},
#                     {'mp':0, 'pr':0, 'cmb':907 , 'lbl': "CL-NoCCR"},
#                     
#                     {'mp':0, 'pr':0, 'cmb':903 , 'lbl': "LU"},
#                     {'mp':0, 'pr':0, 'cmb':908 , 'lbl': "LU-FFI"},
#                                         
                      ]


global_mp_order = [d['lbl'] for d in global_types_of_tests]

global_admission_rate_eq_zero = {}

DVB_RESOLUTIONS = [(3840,2160),(2560,1440), 
                   (1920,1080),(1280,720),
                   (854,480),(640,360),
                   (426,240),
                      ]

#global_workload_configs = ["WL1", "WL2", "WL3"]
global_workload_configs = ["WL1"]

colors_for_cluster_mp = [                    
                        '#fef0d9',
                        '#fdcc8a',
                        '#fc8d59',
                        '#d7301f'
                         ]

colors_for_lu_mp = [
                    '#deebf7',
                    #'#9ecae1',
                    '#3182bd'                   
                    ]

colors_for_cluster_mp.reverse()
colors_for_lu_mp.reverse()

temp_global_colors = [matplotlib.colors.rgb2hex(c) for c in sns.color_palette("muted", 4)]

pprint.pprint(temp_global_colors)
#sys.exit()

num_mmcs_types = 1
global_colors = [temp_global_colors[0]]*num_mmcs_types + [temp_global_colors[1]]*num_mmcs_types + \
                [temp_global_colors[2]]*num_mmcs_types + [temp_global_colors[3]]*num_mmcs_types

print global_colors
#sys.exit()



print global_colors


#global_colors_hex = [rgb2hex(c) for c in global_colors]


def _save_data(fname, data):
    final_fname = DATA_TEMP_SAVE_LOC + fname    
    logfile=open(final_fname, 'w')
    json_data = json.dumps(data)
    logfile.write(json_data)
    logfile.close()

def _load_data(fname):     
    final_fname = DATA_TEMP_SAVE_LOC + fname
    json_data=open(final_fname)
    data = json.load(json_data)      
    return data
    



def _gen_exp_key (mp, pr, cmb, mmp):
    exp_key = "ac"+str(SimParams.AC_TEST_OPTION) + \
                        "mp"+str(mp)+ \
                        "pr"+str(pr)+ \
                        "cmb"+str(cmb)+ \
                        "mmp"+str(mmp)
    return exp_key

def _get_final_fname(fname, exp_key, wl_cfg, seed):
    subdir1 = EXP_DATADIR + wl_cfg + "/" + exp_key + "/"            
    subdir2 = subdir1 + "seed_"+str(seed)+"/"    
    fname_prefix = "HEVCTileSplitTest__"  + exp_key + "_" + str(NOC_H)+"_"+str(NOC_W)+"_"
    finalfname_completedtasks = subdir2 + fname_prefix + fname
    return finalfname_completedtasks


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


def boxplot_colorize(bp, param_col, fc='#B8DCE6'):    
    i=0
    ## change outline color, fill color and linewidth of the boxes
    for box in bp['boxes']:
        # change outline color
        box.set( color='#000000', linewidth=1)
        # change fill color
        box.set( facecolor =  param_col)
        i+=1
    
    ## change color and linewidth of the whiskers
    for whisker in bp['whiskers']:
        whisker.set(color='#000000', linewidth=1, linestyle='-')
    
    ## change color and linewidth of the caps
    for cap in bp['caps']:
        cap.set(color='#000000', linewidth=1)
    
    ## change color and linewidth of the medians
    for median in bp['medians']:
        median.set(color='#000000', linewidth=1)
    
    ## change the style of fliers and their fill
    for flier in bp['fliers']:
        flier.set(marker='x', color='red', alpha=0.5)


def plot_MappingExecOverhead(load_data=False):
    data_fname = "plot_MappingExecOverhead.json"
    ### get data ####
    alldata_perworkload_perexp_perseed = OrderedDict()        
    
    if load_data==True:        
        alldata_perworkload_perexp_perseed = _load_data(data_fname)         
    else:    
        for each_wrkld_cfg in global_workload_configs:        
            alldata_perworkload_perexp_perseed[each_wrkld_cfg] = OrderedDict()
            for each_mapping_type in global_types_of_tests:               
                # which exp condition ?
                exp_key = _gen_exp_key(each_mapping_type['mp'],
                                       each_mapping_type['pr'],
                                       each_mapping_type['cmb'],
                                       each_mapping_type['mmp'])
                exp_lbl = each_mapping_type['lbl']            
                alldata_perworkload_perexp_perseed[each_wrkld_cfg][exp_lbl] = None                        
                each_seed_data = []            
                for each_seed in RANDOM_SEEDS:                
                    # get filename
                    finalfname = _get_final_fname("_mapperexecoverhead.js", exp_key, each_wrkld_cfg, each_seed)                
                    try:        
                        print "getting : ", finalfname
                        ## get file data                        
                        json_data=open(finalfname)
                        file_data = json.load(json_data)                    
                        mapping_ovrhd =  [d[1] for d in file_data] #0: time, 1: clock, 2: timeit                     
                        # save                    
                        each_seed_data.extend(mapping_ovrhd)      
                                                        
                    except Exception, e:                    
                        tb = traceback.format_exc()
                        print tb                    
                        sys.exit(e)            
                alldata_perworkload_perexp_perseed[each_wrkld_cfg][exp_lbl] = each_seed_data
    
    if (load_data==False):
        _save_data(data_fname, alldata_perworkload_perexp_perseed)
        
    
    if SHOW_PLOTS==False:
        return
       
    ### plot data ####
    fig = plt.figure(figsize=(7*1.2, 3*1.2)) # w, h
    fig.canvas.set_window_title('plot_MappingExecOverhead')
    ax = plt.subplot(111)
    print "-- plot_MappingExecOverhead --"
    
    #global_colors = plt.get_cmap('rainbow')(np.linspace(0, 1.0, len(global_types_of_tests)))
            
    rects_list = []
    rect_lbl_list = []
    i=0
    
    temp_k = alldata_perworkload_perexp_perseed.keys()[0]
    num_items = len(alldata_perworkload_perexp_perseed.keys())    
    num_exp = len(alldata_perworkload_perexp_perseed[temp_k].keys())
    
    width=0.13
    ind = np.arange(num_items)
    
    for num, each_exp in enumerate(global_mp_order):            
            #ydata = [conf_data[each_exp] for k,conf_data  in alldata_perworkload_perexp_perseed.iteritems()]
            ydata = [alldata_perworkload_perexp_perseed[wl_k][each_exp] for wl_k  in global_workload_configs]
    
    
    # find global min/max values
    tmp_all_vals = [] 
    for num, each_exp in enumerate(global_mp_order):            
        #ydata = [conf_data[each_exp] for k,conf_data  in alldata_perworkload_perexp_perseed.iteritems()]
        ydata = [alldata_perworkload_perexp_perseed[wl_k][each_exp] for wl_k  in global_workload_configs]
            
        #tmp_all_vals.extend(ydata[0])
        tmp_all_vals.extend(list(itertools.chain(*ydata)))
    
    alldata_norm_min = np.min(tmp_all_vals)  
    alldata_norm_max = np.max(tmp_all_vals)
    
    for num, each_exp in enumerate(global_mp_order):            
        #ydata = [conf_data[each_exp] for k,conf_data  in alldata_perworkload_perexp_perseed.iteritems()]
        ydata = [alldata_perworkload_perexp_perseed[wl_k][each_exp] for wl_k  in global_workload_configs] 
        
        norm_ydata = _normalise_list(ydata, norm_min=alldata_norm_min, norm_max=alldata_norm_max)
        
        #print ydata
        xdata = ind+(width*num)
        print "all config data (mean) for exp : ", each_exp, [np.mean(yd) for yd in norm_ydata], ", list_sizes:", [len(yd) for yd in norm_ydata]
        print "all config data (cumsum) for exp : ", each_exp, [np.sum(yd) for yd in norm_ydata], ", list_sizes:", [len(yd) for yd in norm_ydata]
        
        bps = plt.boxplot(norm_ydata,0, 'x', positions=xdata, widths=width, patch_artist=True)
        
#         for scatter_y, scatter_x in zip(ydata, xdata):
#             plt.scatter([scatter_x]*len(scatter_y), scatter_y, marker='x', color='r', zorder=100)
            
        boxplot_colorize(bps, param_col = global_colors[i])
        
        plt.hold(True)
        
        rect_lbl_list.append(each_exp)        
        rec = patches.Rectangle(
                          (0.72, 0.1), 0.2, 0.6,
                          facecolor=global_colors[i]
                          ),
        rects_list.append(rec)        
        i+=1
        print "---"
        
    plt.grid(axis='y',b=True, which='major', color='k', linestyle='--', alpha=0.2)
    plt.grid(axis='y',b=True, which='minor', color='k', linestyle='--', alpha=0.2)
    #plt.minorticks_on()    
    
    box = ax.get_position()
    ax.set_position([box.x0-0.01, box.y0 + box.height * 0.06,
                 box.width*1.12, box.height * 0.8])
    
    leg = ax.legend(rects_list, rect_lbl_list,ncol=2, prop={'size':13}, loc='upper center', bbox_to_anchor=(0.5, 1.295),
      fancybox=True, shadow=True)
    
    #leg = plt.legend(rects_list, rect_lbl_list,ncol=2, prop={'size':14})
    leg.draggable(True)
    ax.tick_params(axis = 'y', which = 'major')        
    ax.set_ylabel('Normalised mapping\nexecution overhead', fontsize=14, multialignment='center')
    ax.set_xlabel('Workload configurations', fontsize=14)        
    ax.xaxis.major.formatter._useMathText = True
    ax.set_xlim(-0.13, 2+(width*6))
    #ax.set_ylim(-1.47, 41.4)
    ax.set_xticks(ind+( ((width*(float(num_exp)/(width*9.23))/2.0)) ) )
    ax.set_xticklabels(alldata_perworkload_perexp_perseed.keys())
    plt.yscale("symlog", linthreshy=0.01)
    
    

def _get_payload_from_flowbl(flw_bl):
    p = SimParams.NOC_PERIOD
    payload = (16.0*(flw_bl - (70.0*p*p)))/p
    return payload  


def plot_CommsOverhead(load_data=False):
    data_fname_normal = "plot_CommsOverhead_normal.json"
    data_fname_flwsavings = "plot_CommsOverhead_flwsavings.json"
    
    ### get data ####
    alldata_perworkload_perexp_perseed = OrderedDict()
    alldata_perworkload_perexp_perseed_flow_savings = OrderedDict()
    
    if load_data==True:        
        alldata_perworkload_perexp_perseed = _load_data(data_fname_normal)
        alldata_perworkload_perexp_perseed_flow_savings = _load_data(data_fname_flwsavings) 
    else:    
        for each_wrkld_cfg in global_workload_configs:        
            alldata_perworkload_perexp_perseed[each_wrkld_cfg] = OrderedDict()     
            alldata_perworkload_perexp_perseed_flow_savings[each_wrkld_cfg] = OrderedDict()
            for each_mapping_type in global_types_of_tests:               
                # which exp condition ?
                exp_key = _gen_exp_key(each_mapping_type['mp'],
                                       each_mapping_type['pr'],
                                       each_mapping_type['cmb'],
                                       each_mapping_type['mmp'])
                exp_lbl = each_mapping_type['lbl']            
                alldata_perworkload_perexp_perseed[each_wrkld_cfg][exp_lbl] = None
                alldata_perworkload_perexp_perseed_flow_savings[each_wrkld_cfg][exp_lbl] = None            
                each_seed_data = []
                each_seed_flw_savings_data = []
                for each_seed in RANDOM_SEEDS:                
                    # get filename
                    finalfname = _get_final_fname("_flwcompletedshort.js", exp_key, each_wrkld_cfg, each_seed)                
                    try:        
                        print "getting : ", finalfname
                        ## get file data                        
                        json_data=open(finalfname)
                        file_data = json.load(json_data)
                        
                        flows_bl = [f[0] for f in file_data['flows_completed'] if f[2] in [1,15]]  
                        flows_payload = [_get_payload_from_flowbl(bl) for bl in flows_bl]
                        flows_not_sent_proportion =  file_data['flows_not_sent_proportion']               
                        
                        flows_bl_sum = np.sum(flows_payload)
                        
                        # save
                        #each_seed_data.append(gop_lateness_dist_mean)
                        each_seed_data.extend([flows_bl_sum])      
                        each_seed_flw_savings_data.extend([flows_not_sent_proportion])              
                                                        
                    except Exception, e:                    
                        tb = traceback.format_exc()
                        print tb                    
                        sys.exit(e)            
                
                alldata_perworkload_perexp_perseed[each_wrkld_cfg][exp_lbl] = each_seed_data
                alldata_perworkload_perexp_perseed_flow_savings[each_wrkld_cfg][exp_lbl] = each_seed_flw_savings_data
    
    # save data
    if load_data==False:
        _save_data(data_fname_normal, alldata_perworkload_perexp_perseed)
        _save_data(data_fname_flwsavings, alldata_perworkload_perexp_perseed_flow_savings)
    
    if SHOW_PLOTS==False:
        return
            
    ### plot data ####
    fig = plt.figure(figsize=(7*1.2, 3*1.2)) # w, h
    fig.canvas.set_window_title('plot_CommsOverhead')
    ax = plt.subplot(111)
    print "-- plot_CommsOverhead --"
    
    #global_colors = plt.get_cmap('rainbow')(np.linspace(0, 1.0, len(global_types_of_tests)))
            
    rects_list = []
    rect_lbl_list = []
    i=0
    
    temp_k = alldata_perworkload_perexp_perseed.keys()[0]
    num_items = len(global_workload_configs)    
    num_exp = len(alldata_perworkload_perexp_perseed[temp_k].keys())
    
    width=0.13
    ind = np.arange(num_items)
    
    for num, each_exp in enumerate(global_mp_order):            
        #ydata = [conf_data[each_exp] for k,conf_data  in alldata_perworkload_perexp_perseed.iteritems()]
        ydata = [alldata_perworkload_perexp_perseed[wl_k][each_exp] for wl_k  in global_workload_configs]
        flw_savings_mean = [alldata_perworkload_perexp_perseed_flow_savings[wl_k][each_exp] for wl_k  in global_workload_configs]
             
        #print ydata
        xdata = ind+(width*num)
        print "all config data (mean) for exp : ", each_exp, [np.mean(yd) for yd in ydata], ", list_sizes:", [len(yd) for yd in ydata]
        print "all config data (cumsum) for exp : ", each_exp, [np.sum(yd) for yd in ydata], ", list_sizes:", [len(yd) for yd in ydata]
        
        print "flwsavings: all config data (mean) for exp : " , each_exp, np.mean(flw_savings_mean)
        pos = xdata
        val = [np.mean(yd) for yd in ydata]
        
        # convert to Giga
        ydata_GB = [np.array(yd)/1.0e9 for yd in ydata]       
        
        bps = plt.boxplot(ydata_GB,0, '', whis=np.inf, positions=xdata, widths=width, patch_artist=True)
        #plt.barh(pos, val , color=global_colors[i])
        
#         for scatter_y, scatter_x in zip(ydata, xdata):
#             plt.scatter([scatter_x]*len(scatter_y), scatter_y, marker='x', color='r', zorder=100)
            
        boxplot_colorize(bps, param_col = global_colors[i])
        
        plt.hold(True)
        
        rect_lbl_list.append(each_exp)        
        rec = patches.Rectangle(
                          (0.72, 0.1), 0.2, 0.6,
                          facecolor=global_colors[i]
                          ),
        rects_list.append(rec)        
        i+=1
        print "---"
        
    plt.grid(axis='y',b=True, which='major', color='k', linestyle='--', alpha=0.3)
    plt.grid(axis='y',b=True, which='minor', color='k', linestyle='-', alpha=0.2)
    #plt.minorticks_on()
    
    box = ax.get_position()
    ax.set_position([box.x0-0.01, box.y0 + box.height * 0.06,
             box.width*1.12, box.height * 0.8])    
    leg = ax.legend(rects_list, rect_lbl_list,ncol=2, prop={'size':13}, loc='upper center', bbox_to_anchor=(0.5, 1.295),
                    fancybox=True, shadow=True)
    ax.tick_params(axis = 'y', which = 'major')
    ax.set_ylabel('Cumulative data communication\noverhead (volume in GB)', fontsize=14, multialignment='center')        
    ax.set_xlabel('Workload configurations', fontsize=14)        
    ax.xaxis.major.formatter._useMathText = True
    #plt.ticklabel_format(style='sci', axis='x', scilimits=(0,0), labelsize=20)
    #plt.tick_params(axis='both', which='major', labelsize=16)
    #plt.tick_params(axis='both', which='minor', labelsize=16)
    #plt.rc('font', **{'size':'16'})
    #ax.set_xticks(ind+0.5)
    ax.set_xticks(ind+( ((width*(float(num_exp)/(width*9.23))/2.0)) ) )
    ax.set_xticklabels(alldata_perworkload_perexp_perseed.keys())
    ax.set_xlim(-0.13, 2+(width*6))

    
    
    
    
    
    
    


def plot_CommsLatencies(load_data, 
                            #traffic_types=[1,15]): # data
                            traffic_types
                            ): # mem
    
    type_lbl = "_".join([str(xx) for xx in traffic_types])
    data_fname_normal = "plot_CommsLatencies_" + type_lbl + ".json"
    
    ### get data ####
    alldata_perworkload_perexp_perseed = OrderedDict()
    alldata_perworkload_perexp_perseed_flow_savings = OrderedDict()
    
    if load_data==True:        
        alldata_perworkload_perexp_perseed = _load_data(data_fname_normal)        
    else:    
        for each_wrkld_cfg in global_workload_configs:        
            alldata_perworkload_perexp_perseed[each_wrkld_cfg] = OrderedDict()     
            
            for each_mapping_type in global_types_of_tests:               
                # which exp condition ?
                exp_key = _gen_exp_key(each_mapping_type['mp'],
                                       each_mapping_type['pr'],
                                       each_mapping_type['cmb'],
                                       each_mapping_type['mmp'])
                exp_lbl = each_mapping_type['lbl']            
                alldata_perworkload_perexp_perseed[each_wrkld_cfg][exp_lbl] = None                            
                each_seed_data = []
                each_seed_flw_savings_data = []
                for each_seed in RANDOM_SEEDS:                
                    # get filename
                    finalfname = _get_final_fname("_flwcompletedshort.js", exp_key, each_wrkld_cfg, each_seed)                
                    try:        
                        print "getting : ", finalfname
                        ## get file data                        
                        json_data=open(finalfname)
                        file_data = json.load(json_data)
                        
                        flows_actuallatency = [f[1] for f in file_data['flows_completed'] if f[2] in traffic_types]  
                        flows_bl_sum = np.sum(flows_actuallatency)
                        flows_actuallatency_mean = np.mean(flows_actuallatency)
                        flows_actuallatency_max = np.max(flows_actuallatency)
                        
                        # save                        
                        #each_seed_data.extend([flows_bl_sum])      
                        each_seed_data.extend(flows_actuallatency)
                        #each_seed_data.append(flows_actuallatency_mean)
                        #each_seed_data.append(flows_actuallatency_max)
                                                        
                    except Exception, e:                    
                        tb = traceback.format_exc()
                        print tb                    
                        sys.exit(e)            
                
                alldata_perworkload_perexp_perseed[each_wrkld_cfg][exp_lbl] = each_seed_data
                
    # save data
    if load_data==False:
        _save_data(data_fname_normal, alldata_perworkload_perexp_perseed)
    
    if SHOW_PLOTS==False:
        return
      
    ### plot data ####
    fig = plt.figure(figsize=(7*1.2, 3*1.2)) # w, h
    fig.canvas.set_window_title(data_fname_normal)
    ax = plt.subplot(111)
    print "-- plot_CommsLatencies --"
   
    # find global min, max
    g_min = sys.maxint
    g_max = 0
    for num, each_exp in enumerate(global_mp_order):
        ydata = [alldata_perworkload_perexp_perseed[wl_k][each_exp] for wl_k  in global_workload_configs]        
        tmp_min = np.min(ydata)
        tmp_max = np.max(ydata)
        
        if (tmp_min<g_min): g_min = tmp_min
        if (tmp_max>g_max): g_max = tmp_max
    
    
    rects_list = []
    rect_lbl_list = []
    i=0
    
    temp_k = alldata_perworkload_perexp_perseed.keys()[0]
    num_items = len(global_workload_configs)    
    num_exp = len(alldata_perworkload_perexp_perseed[temp_k].keys())
    
    width=0.13
    ind = np.arange(num_items)
    
    for num, each_exp in enumerate(global_mp_order):            
        #ydata = [conf_data[each_exp] for k,conf_data  in alldata_perworkload_perexp_perseed.iteritems()]
        ydata = [alldata_perworkload_perexp_perseed[wl_k][each_exp] for wl_k  in global_workload_configs]
             
        #print ydata
        xdata = ind+(width*num)
        print "all config data (mean) for exp : ", each_exp, [np.mean(yd) for yd in ydata], ", list_sizes:", [len(yd) for yd in ydata]
        print "all config data (cumsum) for exp : ", each_exp, [np.sum(yd) for yd in ydata], ", list_sizes:", [len(yd) for yd in ydata]
        
        pos = xdata
        val = [np.mean(yd) for yd in ydata]
        
        #norm_ydata = [_normalise_list(yd, norm_min=g_min, norm_max=g_max) for yd in ydata]
        
        #bps = plt.boxplot(norm_ydata,0, 'x', positions=xdata, widths=width, patch_artist=True)
        bps = plt.boxplot(ydata,0, 'x', positions=xdata, widths=width, patch_artist=True)
        #plt.barh(pos, val , color=global_colors[i])
        
#         for scatter_y, scatter_x in zip(ydata, xdata):
#             plt.scatter([scatter_x]*len(scatter_y), scatter_y, marker='x', color='r', zorder=100)
            
        boxplot_colorize(bps, param_col = global_colors[i])
        
        plt.hold(True)
        
        rect_lbl_list.append(each_exp)        
        rec = patches.Rectangle(
                          (0.72, 0.1), 0.2, 0.6,
                          facecolor=global_colors[i]
                          ),
        rects_list.append(rec)        
        i+=1
        print "---"
        
    plt.grid(axis='y',b=True, which='major', color='k', linestyle='--', alpha=0.3)
    plt.grid(axis='y',b=True, which='minor', color='k', linestyle='-', alpha=0.2)
    #plt.minorticks_on()
    
    box = ax.get_position()
    ax.set_position([box.x0-0.01, box.y0 + box.height * 0.06, box.width*1.12, box.height * 0.8])    
    leg = ax.legend(rects_list, rect_lbl_list,ncol=2, prop={'size':13}, loc='upper center', bbox_to_anchor=(0.5, 1.295),
                    fancybox=True, shadow=True)
    ax.tick_params(axis = 'y', which = 'major')
    ax.set_ylabel('Normalised mean memory\ncommunication latencies', fontsize=14, multialignment='center')        
    ax.set_xlabel('Workload configurations', fontsize=14)        
    ax.xaxis.major.formatter._useMathText = True
    
    ax.set_xticks(ind+( ((width*(float(num_exp)/(width*9.23))/2.0)) ) )
    ax.set_xticklabels(alldata_perworkload_perexp_perseed.keys())
    #ax.set_xlim(-0.13, 2+(width*6))
    #ax.set_ylim(0, 1.0)
    plt.yscale('symlog')


def plot_NodeIdlePeriods(load_data=False, bar_plot=False, hist_plot=False):
    data_fname = "plot_NodeIdlePeriods.json"
    
    ### get data ####
    alldata_perworkload_perexp_perseed = OrderedDict()
    
    if load_data==True:        
        alldata_perworkload_perexp_perseed = _load_data(data_fname)
    else:    
        for each_wrkld_cfg in global_workload_configs:        
            alldata_perworkload_perexp_perseed[each_wrkld_cfg] = OrderedDict()        
            for each_mapping_type in global_types_of_tests:               
                # which exp condition ?
                exp_key = _gen_exp_key(each_mapping_type['mp'],
                                       each_mapping_type['pr'],
                                       each_mapping_type['cmb'],
                                       each_mapping_type['mmp'])
                exp_lbl = each_mapping_type['lbl']            
                alldata_perworkload_perexp_perseed[each_wrkld_cfg][exp_lbl] = None            
                each_seed_data = []
                for each_seed in RANDOM_SEEDS:                
                    # get filename
                    finalfname = _get_final_fname("_util.js", exp_key, each_wrkld_cfg, each_seed)                
                    try:        
                        print "getting : ", finalfname
                        ## get file data                        
                        json_data=open(finalfname)
                        file_data = json.load(json_data)                    
                        node_idle_periods = itertools.chain.from_iterable(file_data['node_idle_periods'].values())                    
                        #mean_node_idle_periods = np.mean(list(node_idle_periods))
                        
                        # save                        
                        each_seed_data.extend(node_idle_periods)              
                        #each_seed_data.append(mean_node_idle_periods)                        
                                          
                    except Exception, e:                    
                        tb = traceback.format_exc()
                        print tb                    
                        sys.exit(e)
                alldata_perworkload_perexp_perseed[each_wrkld_cfg][exp_lbl] =  {
                                                                                'mean' : np.mean(each_seed_data),
                                                                                'sum' : np.sum(each_seed_data),
                                                                                'mode' : Counter(each_seed_data).most_common(1),
                                                                                'std' : np.std(each_seed_data),
                                                                                'var' : np.var(each_seed_data),
                                                                                'len' : len(each_seed_data)
                                                                                }
        
    # save data    
    if load_data==False:
        _save_data(data_fname, alldata_perworkload_perexp_perseed)
    
    if SHOW_PLOTS==False:
        return
    
    print "-- plot_NodeIdlePeriods --"
#     if hist_plot == True:
#         ### plot data ####
#         #fig = plt.figure(figsize=(8*1.2, 6*1.2))
#         f, axarr = plt.subplots(1, len(global_workload_configs), sharex=True, sharey=True)
#         f.canvas.set_window_title('plot_NodeIdlePeriods')
#                 
#         rects_list = []
#         rect_lbl_list = []
#         i=0
#         
#         temp_k = alldata_perworkload_perexp_perseed.keys()[0]
#         num_items = len(alldata_perworkload_perexp_perseed.keys())    
#         num_exp = len(alldata_perworkload_perexp_perseed[temp_k].keys())
#         
#         width=0.1
#         ind = np.arange(num_items)        
#         xs = np.linspace(0.0,0.55,200)
#         
#         for num, each_exp in enumerate(global_mp_order): 
#             all_ydata = [alldata_perworkload_perexp_perseed[wl_k][each_exp] for wl_k  in global_workload_configs]      
#             
#             #print "all config data (mean) for exp : ", each_exp, [np.mean(yd) for yd in all_ydata], ", list_sizes:", [len(yd) for yd in all_ydata]
#             #print "all config data (cumsum) for exp : ", each_exp, [np.sum(yd) for yd in all_ydata], ", list_sizes:", [len(yd) for yd in all_ydata]
#             #print "all config data (var) for exp : ", each_exp, [np.var(yd) for yd in all_ydata], ", list_sizes:", [len(yd) for yd in all_ydata]
#             #print "all config data (std) for exp : ", each_exp, [np.std(yd) for yd in all_ydata], ", list_sizes:", [len(yd) for yd in all_ydata]
#             #print "all config data (mode) for exp : ", each_exp, [Counter(yd).most_common(1) for yd in all_ydata], ", list_sizes:", [len(yd) for yd in all_ydata]
#             
#             print "all config data (mean) for exp : ", each_exp, [yd['mean'] for yd in all_ydata], ", list_sizes:", [yd['len'] for yd in all_ydata]
#             print "all config data (sum) for exp : ", each_exp, [yd['sum'] for yd in all_ydata], ", list_sizes:", [yd['len'] for yd in all_ydata]
#             print "all config data (var) for exp : ", each_exp, [yd['var'] for yd in all_ydata], ", list_sizes:", [yd['len'] for yd in all_ydata]
#             print "all config data (std) for exp : ", each_exp, [yd['std'] for yd in all_ydata], ", list_sizes:", [yd['len'] for yd in all_ydata]
#             print "all config data (mode) for exp : ", each_exp, [yd['mode'] for yd in all_ydata], ", list_sizes:", [yd['len'] for yd in all_ydata]
#                         
#             if isinstance(axarr, Iterable)==False: axarr = [axarr] 
#             
#             for each_axarr, ydata in zip(axarr, all_ydata):
#                 
#                 ## filter-out data ##
#                 #cutdown_ydata = [d for d in ydata if d>0.001]            
#                 #ydata = cutdown_ydata
#                 
#                 #ydata.append(0.6)         
#                 #density = scipy.stats.gaussian_kde(ydata)            
#                 #density.covariance_factor = lambda : .25
#                 #density._compute_covariance()
#                 #each_axarr.plot(xs,density(xs), c=global_colors[i], lw=2)
#                 weights = np.ones_like(ydata)/float(len(ydata))
#                 each_axarr.hist(ydata, bins=5, histtype='step', color=global_colors[i], label=each_exp, lw=2, weights=weights)
#                 
#             rect_lbl_list.append(each_exp)        
#             rec = patches.Rectangle(
#                               (0.72, 0.1), 0.2, 0.6,
#                               facecolor=global_colors[i]
#                               ),
#             rects_list.append(rec)        
#             i+=1
#             print "---"
#         
#         for each_axarr in axarr:    
#             each_axarr.grid(b=True, which='major', color='k', linestyle='-', alpha=0.5)
#             each_axarr.grid(b=True, which='minor', color='k', linestyle='--', alpha=0.2)
#             each_axarr.minorticks_on()
#             leg = plt.legend(rects_list, rect_lbl_list,ncol=2)
#             leg.draggable(True)
#             each_axarr.tick_params(axis = 'both', which = 'both')
#             each_axarr.set_ylabel('Node Idle Periods', fontsize=20)        
#             each_axarr.set_xlabel('Workload configurations', fontsize=20)        
#             each_axarr.set_yscale('log')
    
    if bar_plot==True:
        ### plot data ####
        fig = plt.figure(figsize=(7*1.2, 3*1.2)) # w, h
        ax = plt.subplot(111)
        fig.canvas.set_window_title('plot_NodeIdlePeriods')
                
        rects_list = []
        rect_lbl_list = []
        i=0
        
        temp_k = alldata_perworkload_perexp_perseed.keys()[0]
        num_items = len(alldata_perworkload_perexp_perseed.keys())    
        num_exp = len(alldata_perworkload_perexp_perseed[temp_k].keys())
        
        width=0.1
        ind = np.arange(num_items)
        
        for num, each_exp in enumerate(global_mp_order): 
            all_ydata = [alldata_perworkload_perexp_perseed[wl_k][each_exp] for wl_k  in global_workload_configs]      
            
#             print "all config data (mean) for exp : ", each_exp, [np.mean(yd) for yd in all_ydata], ", list_sizes:", [len(yd) for yd in all_ydata]
#             print "all config data (cumsum) for exp : ", each_exp, [np.sum(yd) for yd in all_ydata], ", list_sizes:", [len(yd) for yd in all_ydata]
#             print "all config data (var) for exp : ", each_exp, [np.var(yd) for yd in all_ydata], ", list_sizes:", [len(yd) for yd in all_ydata]
#             print "all config data (std) for exp : ", each_exp, [np.std(yd) for yd in all_ydata], ", list_sizes:", [len(yd) for yd in all_ydata]
#             print "all config data (mode) for exp : ", each_exp, [Counter(yd).most_common(1) for yd in all_ydata], ", list_sizes:", [len(yd) for yd in all_ydata]
             
            print "all config data (mean) for exp : ", each_exp, [yd['mean'] for yd in all_ydata], ", list_sizes:", [yd['len'] for yd in all_ydata]
            print "all config data (sum) for exp : ", each_exp, [yd['sum'] for yd in all_ydata], ", list_sizes:", [yd['len'] for yd in all_ydata]
            print "all config data (var) for exp : ", each_exp, [yd['var'] for yd in all_ydata], ", list_sizes:", [yd['len'] for yd in all_ydata]
            print "all config data (std) for exp : ", each_exp, [yd['std'] for yd in all_ydata], ", list_sizes:", [yd['len'] for yd in all_ydata]
            print "all config data (mode) for exp : ", each_exp, [yd['mode'] for yd in all_ydata], ", list_sizes:", [yd['len'] for yd in all_ydata]
            
            
            mean_ydata = [float(yd['mean']*1000.0) for yd in all_ydata] # in milisecs   
            ax.barh(ind + (width*num), mean_ydata, width, color=global_colors[i])
                
            rect_lbl_list.append(each_exp)        
            rec = patches.Rectangle(
                              (0.72, 0.1), 0.2, 0.6,
                              facecolor=global_colors[i]
                              ),
            rects_list.append(rec)        
            i+=1
            print "---"
           
        ax.grid(axis='x', b=True, which='major', color='k', linestyle='--', alpha=0.3)
        #ax.grid(b=True, which='minor', color='k', linestyle='--', alpha=0.2)
        ax.minorticks_on()        
        ax.tick_params(axis = 'both', which = 'both')
        ax.set_ylabel('Workload configurations', fontsize=14)        
        ax.set_xlabel('Mean PE idle period (ms)', fontsize=14)        
        ax.set(yticks=ind+( ((width*(float(num_exp)/(width*9.23))/2.0)) ), 
               yticklabels=global_workload_configs, 
               ylim=[9*width - 1, float(num_items)*(width/0.11)])
        
        #ax.set_xlim(-0.13, 2+(width*6))
        #ax.set_ylim(-1.47, 41.4)
        #ax.set_xticks(ind+( ((width*(float(num_exp)/(width*9.23))/2.0)) ) )
    
        box = ax.get_position()
        ax.set_position([box.x0-0.025, box.y0 + box.height * 0.06, box.width*1.11, box.height * 0.8])        
        leg = ax.legend(rects_list, rect_lbl_list,ncol=2, prop={'size':13}, loc='upper center', bbox_to_anchor=(0.5, 1.295),
              fancybox=True, shadow=True)
        leg.draggable(True)
    
        #ax.set_xticks(ind+( ((width*(float(num_exp)/(width*9.23))/2.0)) ) )
        #ax.set_xticklabels(alldata_perworkload_perexp_perseed.keys())
        
        
        
        
        
        
        

def plot_NodeUtilisation(load_data=False, bar_plot=False, hist_plot=False):
    data_fname = "plot_NodeUtilisation.json"
    
    ### get data ####
    alldata_perworkload_perexp_perseed = OrderedDict()
    
    if load_data==True:        
        alldata_perworkload_perexp_perseed = _load_data(data_fname)
    else:    
        for each_wrkld_cfg in global_workload_configs:        
            alldata_perworkload_perexp_perseed[each_wrkld_cfg] = OrderedDict()        
            for each_mapping_type in global_types_of_tests:               
                # which exp condition ?
                exp_key = _gen_exp_key(each_mapping_type['mp'],
                                       each_mapping_type['pr'],
                                       each_mapping_type['cmb'],
                                       each_mapping_type['mmp'])
                exp_lbl = each_mapping_type['lbl']            
                alldata_perworkload_perexp_perseed[each_wrkld_cfg][exp_lbl] = None            
                each_seed_data = []
                for each_seed in RANDOM_SEEDS:                
                    # get filename
                    finalfname = _get_final_fname("_util.js", exp_key, each_wrkld_cfg, each_seed)                
                    try:        
                        print "getting : ", finalfname
                        ## get file data                        
                        json_data=open(finalfname)
                        file_data = json.load(json_data)                    
                        all_nodes_idle_times = file_data['node_idle_time'][-1]["it_c"] 
                        simulation_time = file_data['node_idle_time'][-1]['time']                        
                        overall_system_busy_percentage = (1.0-float(float(np.mean(all_nodes_idle_times))/float(simulation_time)))*100.0
                        
                        # save
                        each_seed_data.append(overall_system_busy_percentage)
                                                        
                    except Exception, e:                    
                        tb = traceback.format_exc()
                        print tb                    
                        sys.exit(e)
                alldata_perworkload_perexp_perseed[each_wrkld_cfg][exp_lbl] = each_seed_data
        
    # save data    
    if load_data==False:
        _save_data(data_fname, alldata_perworkload_perexp_perseed)
    
    
    if SHOW_PLOTS==False:
        return
    
    
    if bar_plot==True:
        print "-- plot_NodeUtilisation --"
        ### plot data ####
        fig = plt.figure(figsize=(8*1.2, 6*1.2))
        ax = plt.subplot(111)
        fig.canvas.set_window_title('plot_NodeUtilisation')
                
        rects_list = []
        rect_lbl_list = []
        i=0
        
        temp_k = alldata_perworkload_perexp_perseed.keys()[0]
        num_items = len(alldata_perworkload_perexp_perseed.keys())    
        num_exp = len(alldata_perworkload_perexp_perseed[temp_k].keys())
        
        width=0.1
        ind = np.arange(num_items)
        
        for num, each_exp in enumerate(global_mp_order): 
            all_ydata = [alldata_perworkload_perexp_perseed[wl_k][each_exp] for wl_k  in global_workload_configs]      
            
            print "all config data (mean) for exp : ", each_exp, [np.mean(yd) for yd in all_ydata], ", list_sizes:", [len(yd) for yd in all_ydata]
            print "all config data (cumsum) for exp : ", each_exp, [np.sum(yd) for yd in all_ydata], ", list_sizes:", [len(yd) for yd in all_ydata]
            print "all config data (var) for exp : ", each_exp, [np.var(yd) for yd in all_ydata], ", list_sizes:", [len(yd) for yd in all_ydata]
            print "all config data (std) for exp : ", each_exp, [np.std(yd) for yd in all_ydata], ", list_sizes:", [len(yd) for yd in all_ydata]
            print "all config data (mode) for exp : ", each_exp, [Counter(yd).most_common(1) for yd in all_ydata], ", list_sizes:", [len(yd) for yd in all_ydata]
                
            mean_ydata = [np.mean(yd) for yd in all_ydata]            
            ax.barh(ind + (width*num), mean_ydata, width, color=global_colors[i])
                
            rect_lbl_list.append(each_exp)        
            rec = patches.Rectangle(
                              (0.72, 0.1), 0.2, 0.6,
                              facecolor=global_colors[i]
                              ),
            rects_list.append(rec)        
            i+=1
            print "---"
           
        ax.grid(b=True, which='major', color='k', linestyle='-', alpha=0.5)
        ax.grid(b=True, which='minor', color='k', linestyle='--', alpha=0.2)
        ax.minorticks_on()
        leg = plt.legend(rects_list, rect_lbl_list,ncol=2)
        leg.draggable(True)
        ax.tick_params(axis = 'both', which = 'both')
        ax.set_ylabel('Mean node busy time', fontsize=20)        
        ax.set_xlabel('Workload configurations', fontsize=20)        
        ax.set(yticks=ind + width, yticklabels=global_workload_configs, ylim=[2*width - 1, num_items])




def plot_CumulativeIdleTime(load_data=False, bar_plot=False, hist_plot=False):
    data_fname = "plot_CumulativeIdleTime.json"
    
    ### get data ####
    alldata_perworkload_perexp_perseed = OrderedDict()
    
    if load_data==True:        
        alldata_perworkload_perexp_perseed = _load_data(data_fname)
    else:    
        for each_wrkld_cfg in global_workload_configs:        
            alldata_perworkload_perexp_perseed[each_wrkld_cfg] = OrderedDict()        
            for each_mapping_type in global_types_of_tests:               
                # which exp condition ?
                exp_key = _gen_exp_key(each_mapping_type['mp'],
                                       each_mapping_type['pr'],
                                       each_mapping_type['cmb'],
                                       each_mapping_type['mmp'])
                exp_lbl = each_mapping_type['lbl']            
                alldata_perworkload_perexp_perseed[each_wrkld_cfg][exp_lbl] = None            
                each_seed_data = []
                for each_seed in RANDOM_SEEDS:                
                    # get filename
                    finalfname = _get_final_fname("_util.js", exp_key, each_wrkld_cfg, each_seed)                
                    try:        
                        print "getting : ", finalfname
                        ## get file data                        
                        json_data=open(finalfname)
                        file_data = json.load(json_data)                    
                        all_nodes_idle_times = file_data['node_idle_time'][-1]["it_c"] 
                        #simulation_time = file_data['node_idle_time'][-1]['time']                        
                        #overall_system_busy_percentage = (1.0-float(float(np.mean(all_nodes_idle_times))/float(simulation_time)))*100.0
                        cumulative_idle_time = np.sum(all_nodes_idle_times)
                                                
                        # save
                        each_seed_data.append(cumulative_idle_time)
                                                        
                    except Exception, e:                    
                        tb = traceback.format_exc()
                        print tb                    
                        sys.exit(e)
                alldata_perworkload_perexp_perseed[each_wrkld_cfg][exp_lbl] = each_seed_data
        
    # save data    
    if load_data==False:
        _save_data(data_fname, alldata_perworkload_perexp_perseed)
    
    
    if SHOW_PLOTS==False:
        return
    
    if bar_plot==True:
        print "-- plot_CumulativeIdleTime --"
        ### plot data ####
        fig = plt.figure(figsize=(8*1.2, 6*1.2))
        ax = plt.subplot(111)
        fig.canvas.set_window_title('plot_CumulativeIdleTime')
                
        rects_list = []
        rect_lbl_list = []
        i=0
        
        temp_k = alldata_perworkload_perexp_perseed.keys()[0]
        num_items = len(alldata_perworkload_perexp_perseed.keys())    
        num_exp = len(alldata_perworkload_perexp_perseed[temp_k].keys())
        
        width=0.1
        ind = np.arange(num_items)
        
        for num, each_exp in enumerate(global_mp_order): 
            all_ydata = [alldata_perworkload_perexp_perseed[wl_k][each_exp] for wl_k  in global_workload_configs]      
            
            print "all config data (mean) for exp : ", each_exp, [np.mean(yd) for yd in all_ydata], ", list_sizes:", [len(yd) for yd in all_ydata]
            print "all config data (cumsum) for exp : ", each_exp, [np.sum(yd) for yd in all_ydata], ", list_sizes:", [len(yd) for yd in all_ydata]
            print "all config data (var) for exp : ", each_exp, [np.var(yd) for yd in all_ydata], ", list_sizes:", [len(yd) for yd in all_ydata]
            print "all config data (std) for exp : ", each_exp, [np.std(yd) for yd in all_ydata], ", list_sizes:", [len(yd) for yd in all_ydata]
            print "all config data (mode) for exp : ", each_exp, [Counter(yd).most_common(1) for yd in all_ydata], ", list_sizes:", [len(yd) for yd in all_ydata]
                
            mean_ydata = [np.mean(yd) for yd in all_ydata]            
            ax.barh(ind + (width*num), mean_ydata, width, color=global_colors[i])
                
            rect_lbl_list.append(each_exp)        
            rec = patches.Rectangle(
                              (0.72, 0.1), 0.2, 0.6,
                              facecolor=global_colors[i]
                              ),
            rects_list.append(rec)        
            i+=1
            print "---"
           
        ax.grid(b=True, which='major', color='k', linestyle='-', alpha=0.5)
        ax.grid(b=True, which='minor', color='k', linestyle='--', alpha=0.2)
        ax.minorticks_on()
        leg = plt.legend(rects_list, rect_lbl_list,ncol=2)
        leg.draggable(True)
        ax.tick_params(axis = 'both', which = 'both')
        ax.set_ylabel('Mean Cumulative Node Idle Time', fontsize=20)        
        ax.set_xlabel('Workload configurations', fontsize=20)        
        ax.set(yticks=ind + width, yticklabels=global_workload_configs, ylim=[2*width - 1, num_items])





def plot_GoPLateness(plt_boxplot=True, plt_beanplot=False, load_data=False):
    
    data_fname = "plot_GoPLateness_data.json"
    
    ### get data ####
    alldata_perworkload_perexp_perseed = OrderedDict()
    
    if load_data==True:        
        alldata_perworkload_perexp_perseed = _load_data(data_fname)
    else:    
        for each_wrkld_cfg in global_workload_configs:        
            alldata_perworkload_perexp_perseed[each_wrkld_cfg] = OrderedDict()        
            for each_mapping_type in global_types_of_tests:               
                # which exp condition ?
                exp_key = _gen_exp_key(each_mapping_type['mp'],
                                       each_mapping_type['pr'],
                                       each_mapping_type['cmb'],
                                       each_mapping_type['mmp'])
                exp_lbl = each_mapping_type['lbl']
                
                alldata_perworkload_perexp_perseed[each_wrkld_cfg][exp_lbl] = None
                
                each_seed_data = []
                for each_seed in RANDOM_SEEDS:
                    
                    # get filename
                    finalfname_gopsummary = _get_final_fname("_gopsopbuffsumm.js", exp_key, each_wrkld_cfg, each_seed)
                    
                    try:        
                        print "getting : ", finalfname_gopsummary
                        ## get file data                        
                        json_data=open(finalfname_gopsummary)
                        file_data = json.load(json_data)                    
                        gop_lateness_dist = [g['gop_execution_lateness'] for gid, g in file_data.iteritems()]
                        #gop_lateness_dist = [g['gop_execution_lateness'] for gid, g in file_data.iteritems() if g['gop_execution_lateness'] > 0]
                        gop_lateness_dist_mean = np.mean(gop_lateness_dist)
                        gop_lateness_dist_sum = np.sum(gop_lateness_dist)
                        
                        # save
                        #each_seed_data.append(gop_lateness_dist_mean)
                        #each_seed_data.extend([gop_lateness_dist_sum])
                        each_seed_data.extend(gop_lateness_dist)
                        
                                                        
                    except Exception, e:                    
                        tb = traceback.format_exc()
                        print tb                    
                        sys.exit(e)
                
                
                alldata_perworkload_perexp_perseed[each_wrkld_cfg][exp_lbl] = each_seed_data 
    
    # save data    
    if load_data==False:
        _save_data(data_fname, alldata_perworkload_perexp_perseed)
    
    if SHOW_PLOTS==False:
        return
    
    print "-- plot_GoPLateness --"
    if plt_boxplot == True:
        ### plot data ####
        fig = plt.figure(figsize=(7*1.2, 3*1.2)) # w, h
        fig.canvas.set_window_title('plot_GoPLateness-box')
        ax = plt.subplot(111)     
                
        rects_list = []
        rect_lbl_list = []
        i=0
        
        temp_k = alldata_perworkload_perexp_perseed.keys()[0]
        num_items = len(global_workload_configs)
        num_configs = len(alldata_perworkload_perexp_perseed.keys())
        num_exp = len(alldata_perworkload_perexp_perseed[temp_k].keys())
        
        width=0.13
        ind = np.arange(num_items)
        
        for num, each_exp in enumerate(global_mp_order):            
            #ydata = [conf_data[each_exp] for k,conf_data  in alldata_perworkload_perexp_perseed.iteritems()]
            ydata = [alldata_perworkload_perexp_perseed[wl_k][each_exp] for wl_k  in global_workload_configs]
            #print ydata
            xdata = ind+(width*num)
            print "all config data (mean) for exp : ", each_exp, [np.mean(yd) for yd in ydata], ", list_sizes:", [len(yd) for yd in ydata]
            print "all config data (cumsum) for exp : ", each_exp, [np.sum(yd) for yd in ydata], ", list_sizes:", [len(yd) for yd in ydata]
            print "all config data (max) for exp : ", each_exp, [np.max(yd) for yd in ydata], ", list_sizes:", [len(yd) for yd in ydata]
            
            ydata_onlylategops = []
            for each_y in ydata:
                temp_y = [y for y in each_y if y>0] 
                ydata_onlylategops.append(temp_y)
            
            print len(ydata)
            print len(xdata)
            print len(ind)
            
            #bps = plt.boxplot(ydata,0, '', whis=np.inf, positions=xdata, widths=width, patch_artist=True)
            bps = plt.boxplot(ydata,0, 'x', positions=xdata, widths=width, patch_artist=True)
            
            #for scatter_y, scatter_x in zip(ydata, xdata):
            #    plt.scatter([scatter_x]*len(scatter_y), scatter_y, marker='x', color='r', zorder=100)
                
            boxplot_colorize(bps, param_col = global_colors[i])
            
            plt.hold(True)
            
            rect_lbl_list.append(each_exp)        
            rec = patches.Rectangle(
                              (0.72, 0.1), 0.2, 0.6,
                              facecolor=global_colors[i]
                              ),
            rects_list.append(rec)        
            i+=1
            
        plt.grid(axis='y',b=True, which='major', color='k', linestyle='--', alpha=0.2)
        plt.grid(axis='y',b=True, which='minor', color='k', linestyle='--', alpha=0.2)
        #plt.minorticks_on()    
        
        box = ax.get_position()
        ax.set_position([box.x0-0.01, box.y0 + box.height * 0.06,
                 box.width*1.12, box.height * 0.8])
        
        leg = ax.legend(rects_list, rect_lbl_list,ncol=2, prop={'size':13}, loc='upper center', bbox_to_anchor=(0.5, 1.295),
          fancybox=True, shadow=True)
        
        #leg = plt.legend(rects_list, rect_lbl_list,ncol=2, prop={'size':14})
        leg.draggable(True)
        ax.tick_params(axis = 'y', which = 'major')        
        ax.set_ylabel('Job lateness (s)\n(logarithmic scale)', fontsize=14, multialignment='center')
        ax.set_xlabel('Workload configurations', fontsize=14)        
        ax.xaxis.major.formatter._useMathText = True
        #ax.set_xlim(-0.13, 2+(width*6))
        #ax.set_ylim(-1.47, 41.4)
        #plt.ticklabel_format(style='sci', axis='x', scilimits=(0,0), labelsize=20)
        #plt.tick_params(axis='both', which='major', labelsize=16)
        #plt.tick_params(axis='both', which='minor', labelsize=16)
        #plt.rc('font', **{'size':'16'})
        #ax.set_xticks(ind+0.5)
        ax.set_xticks(ind+( ((width*(float(num_exp)/(width*9.23))/2.0)) ) )
        ax.set_xticklabels(alldata_perworkload_perexp_perseed.keys())
        #ax.set_xticklabels( [r"$%.1f\times10^4$"% (round(float(x)/10000.0,1)) + "\n" + "(%d VSs)"%_get_wfs_for_cc(x) for x in sorted_cc_list] )
        #plt.rcParams['mathtext.default'] = 'regular'
        plt.yscale('symlog')
        
    if plt_beanplot == True:
        ### plot data ####
        fig = plt.figure(figsize=(8*1.2, 6*1.2))
        fig.canvas.set_window_title('plot_GoPLateness-bean')
        ax = plt.subplot(111)     
        
        #global_colors = plt.get_cmap('rainbow')(np.linspace(0, 1.0, len(global_types_of_tests)))      
        #global_colors_hex = [rgb2hex(c) for c in global_colors]
                
        rects_list = []
        rect_lbl_list = []
        i=0
        
        temp_k = alldata_perworkload_perexp_perseed.keys()[0]
        num_items = len(alldata_perworkload_perexp_perseed.keys())
        num_configs = len(alldata_perworkload_perexp_perseed.keys())
        num_exp = len(alldata_perworkload_perexp_perseed[temp_k].keys())
        
        width=0.1
        ind = np.arange(num_items)
        
        for num, each_exp in enumerate(global_mp_order):            
            #ydata = [conf_data[each_exp] for k,conf_data  in alldata_perworkload_perexp_perseed.iteritems()]
            ydata = [alldata_perworkload_perexp_perseed[wl_k][each_exp] for wl_k  in global_workload_configs]
                    
            #print ydata
            xdata = ind+(width*num)
            print "all config data (mean) for exp : ", each_exp, [np.mean(yd) for yd in ydata], ", list_sizes:", [len(yd) for yd in ydata]
            print "all config data (cumsum) for exp : ", each_exp, [np.sum(yd) for yd in ydata], ", list_sizes:", [len(yd) for yd in ydata]
                        
            dist = [np.max(pp)-np.min(pp) for pp in xdata]
            w = [min(0.15*max(dd,1.0),0.5) for dd in dist]
            
            k = [scipy.stats.gaussian_kde(kk) for kk in ydata] #calculates the kernel density            
            m = [mm.dataset.min() for mm in k] #lower bound of violin
            M = [MM.dataset.max() for MM in k] #upper bound of violin
            x = [ np.arange(mm,MM,(MM-mm)/100.) for mm, MM in zip(m, M)] # support for violin 
            v = [kk.evaluate(xx) for kk,xx in zip(k,x)] #violin profile (density curve)
            v = [vv/vv.max()*ww for vv,ww in zip(v,w)] #scaling the violin to the available space 
            
            for each_v, each_x, each_p in zip(v,x,xdata):
                ax.fill_betweenx(each_x,each_p,each_v+each_p,facecolor=global_colors[i],alpha=0.3)
                ax.fill_betweenx(each_x,each_p,-each_v+each_p,facecolor=global_colors[i],alpha=0.3)
            
            #bps = plt.boxplot(ydata,0, '', whis=np.inf, positions=xdata, widths=width, patch_artist=True)
            bps = plt.boxplot(ydata,1, 'x', positions=xdata, vert=1,widths=width, patch_artist=True)
            
            #for scatter_y, scatter_x in zip(ydata, xdata):
            #    plt.scatter([scatter_x]*len(scatter_y), scatter_y, marker='x', color='r', zorder=100)
                
            boxplot_colorize(bps, param_col = global_colors[i])
            
            plt.hold(True)
            
            rect_lbl_list.append(each_exp)        
            rec = patches.Rectangle(
                              (0.72, 0.1), 0.2, 0.6,
                              facecolor=global_colors[i]
                              ),
            rects_list.append(rec)        
            i+=1
        
        plt.grid(b=True, which='major', color='k', linestyle='--', alpha=0.2)
        plt.grid(b=True, which='minor', color='k', linestyle='--', alpha=0.2)
        #plt.yscale('log')
        #plt.minorticks_on()    
        leg = plt.legend(rects_list, rect_lbl_list,ncol=2)
        leg.draggable(True)
        ax.tick_params(axis = 'both', which = 'both')
        ax.set_ylabel('GoP Lateness', fontsize=20)        
        ax.set_xlabel('Workload configurations', fontsize=20)        
        ax.xaxis.major.formatter._useMathText = True
        #plt.ticklabel_format(style='sci', axis='x', scilimits=(0,0), labelsize=20)
        #plt.tick_params(axis='both', which='major', labelsize=16)
        #plt.tick_params(axis='both', which='minor', labelsize=16)
        #plt.rc('font', **{'size':'16'})
        #ax.set_xticks(ind+0.5)
        ax.set_xticks(ind+((width*num_exp)/2) )
        ax.set_xticklabels(alldata_perworkload_perexp_perseed.keys())
        #ax.set_xticklabels( [r"$%.1f\times10^4$"% (round(float(x)/10000.0,1)) + "\n" + "(%d VSs)"%_get_wfs_for_cc(x) for x in sorted_cc_list] )
        #plt.rcParams['mathtext.default'] = 'regular'
        
    print "----"
           
        
def plot_TaskResponseTime(load_data=False, plt_boxplot=False):
    
    data_fname = "plot_TaskResponseTime.json"
    
    ### get data ####
    alldata_perworkload_perexp_perseed = OrderedDict()
    
    if load_data==True:        
        alldata_perworkload_perexp_perseed = _load_data(data_fname)
    else:    
        for each_wrkld_cfg in global_workload_configs:        
            alldata_perworkload_perexp_perseed[each_wrkld_cfg] = OrderedDict()        
            for each_mapping_type in global_types_of_tests:               
                # which exp condition ?
                exp_key = _gen_exp_key(each_mapping_type['mp'],
                                       each_mapping_type['pr'],
                                       each_mapping_type['cmb'],
                                       each_mapping_type['mmp'])
                exp_lbl = each_mapping_type['lbl']
                
                alldata_perworkload_perexp_perseed[each_wrkld_cfg][exp_lbl] = None
                
                each_seed_data = []
                for each_seed in RANDOM_SEEDS:
                    
                    # get filename
                    finalfname_obuff = _get_final_fname("_obuff.js", exp_key, each_wrkld_cfg, each_seed)
                    
                    try:        
                        print "getting : ", finalfname_obuff
                        ## get file data                        
                        json_data=open(finalfname_obuff)
                        file_data = json.load(json_data)
                        task_responsetime = [t["et"] - t["dt"] for t in file_data]
                        task_responsetime_mean = np.mean([t["et"] - t["dt"] for t in file_data])
                        task_responsetime_max = np.max([t["et"] - t["dt"] for t in file_data])
                        
                        # save                        
                        each_seed_data.extend(task_responsetime)
                        
                        
                                                        
                    except Exception, e:                    
                        tb = traceback.format_exc()
                        print tb                    
                        sys.exit(e)
                
                
                alldata_perworkload_perexp_perseed[each_wrkld_cfg][exp_lbl] = each_seed_data 
    
    # save data    
    if load_data==False:
        _save_data(data_fname, alldata_perworkload_perexp_perseed)
    
    if SHOW_PLOTS==False:
        return
    
    print "-- plot_TaskResponseTime --"
    if plt_boxplot == True:
        ### plot data ####
        fig = plt.figure(figsize=(7*1.2, 3*1.2)) # w, h
        fig.canvas.set_window_title('plot_GoPLateness-box')
        ax = plt.subplot(111)     
                
        rects_list = []
        rect_lbl_list = []
        i=0
        
        temp_k = alldata_perworkload_perexp_perseed.keys()[0]
        num_items = len(global_workload_configs)
        num_configs = len(alldata_perworkload_perexp_perseed.keys())
        num_exp = len(alldata_perworkload_perexp_perseed[temp_k].keys())
        
        width=0.13
        ind = np.arange(num_items)
        
        for num, each_exp in enumerate(global_mp_order):            
            #ydata = [conf_data[each_exp] for k,conf_data  in alldata_perworkload_perexp_perseed.iteritems()]
            ydata = [alldata_perworkload_perexp_perseed[wl_k][each_exp] for wl_k  in global_workload_configs]
            #print ydata
            xdata = ind+(width*num)
            print "all config data (mean) for exp : ", each_exp, [np.mean(yd) for yd in ydata], ", list_sizes:", [len(yd) for yd in ydata]
            print "all config data (cumsum) for exp : ", each_exp, [np.sum(yd) for yd in ydata], ", list_sizes:", [len(yd) for yd in ydata]
            print "all config data (max) for exp : ", each_exp, [np.max(yd) for yd in ydata], ", list_sizes:", [len(yd) for yd in ydata]
            
            ydata_onlylategops = []
            for each_y in ydata:
                temp_y = [y for y in each_y if y>0] 
                ydata_onlylategops.append(temp_y)
            
            #bps = plt.boxplot(ydata,0, '', whis=np.inf, positions=xdata, widths=width, patch_artist=True)
            bps = plt.boxplot(ydata,0, 'x', positions=xdata, widths=width, patch_artist=True)
            
            #for scatter_y, scatter_x in zip(ydata, xdata):
            #    plt.scatter([scatter_x]*len(scatter_y), scatter_y, marker='x', color='r', zorder=100)
                
            boxplot_colorize(bps, param_col = global_colors[i])
            
            plt.hold(True)
            
            rect_lbl_list.append(each_exp)        
            rec = patches.Rectangle(
                              (0.72, 0.1), 0.2, 0.6,
                              facecolor=global_colors[i]
                              ),
            rects_list.append(rec)        
            i+=1
            
        plt.grid(axis='y',b=True, which='major', color='k', linestyle='--', alpha=0.2)
        plt.grid(axis='y',b=True, which='minor', color='k', linestyle='--', alpha=0.2)
        #plt.minorticks_on()    
        
        box = ax.get_position()
        ax.set_position([box.x0-0.01, box.y0 + box.height * 0.06,
                 box.width*1.12, box.height * 0.8])
        
        leg = ax.legend(rects_list, rect_lbl_list,ncol=2, prop={'size':13}, loc='upper center', bbox_to_anchor=(0.5, 1.295),
          fancybox=True, shadow=True)
        
        #leg = plt.legend(rects_list, rect_lbl_list,ncol=2, prop={'size':14})
        leg.draggable(True)
        ax.tick_params(axis = 'y', which = 'major')        
        ax.set_ylabel('Task response time (s)', fontsize=14, multialignment='center')
        ax.set_xlabel('Workload configurations', fontsize=14)        
        ax.xaxis.major.formatter._useMathText = True
        #ax.set_xlim(-0.13, 2+(width*6))
        #ax.set_ylim(-1.47, 41.4)
        #plt.ticklabel_format(style='sci', axis='x', scilimits=(0,0), labelsize=20)
        #plt.tick_params(axis='both', which='major', labelsize=16)
        #plt.tick_params(axis='both', which='minor', labelsize=16)
        #plt.rc('font', **{'size':'16'})
        #ax.set_xticks(ind+0.5)
        ax.set_xticks(ind+( ((width*(float(num_exp)/(width*9.23))/2.0)) ) )
        ax.set_xticklabels(alldata_perworkload_perexp_perseed.keys())
        #ax.set_xticklabels( [r"$%.1f\times10^4$"% (round(float(x)/10000.0,1)) + "\n" + "(%d VSs)"%_get_wfs_for_cc(x) for x in sorted_cc_list] )
        #plt.rcParams['mathtext.default'] = 'regular'
        plt.yscale('symlog')
        
    print "----"

def plot_workloadDistribution(plt_pcolor = True, plt_bars = True):
    
    ### get data ####
    alldata_perworkload_perexp_perseed = OrderedDict()
    
    config_order = ["WL4"]
    exp_lbl_order = ["WCRS-based", "Random"]
    
    for each_wrkld_cfg in global_workload_configs:        
        alldata_perworkload_perexp_perseed[each_wrkld_cfg] = OrderedDict()        
        for each_mapping_type in global_types_of_tests:   
            
            # which exp condition ?
            exp_key = _gen_exp_key(each_mapping_type['mp'],
                                   each_mapping_type['pr'],
                                   each_mapping_type['cmb'],
                                   each_mapping_type['mmp'])
            exp_lbl = each_mapping_type['lbl']
            
            alldata_perworkload_perexp_perseed[each_wrkld_cfg][exp_lbl] = None
            
            each_seed_data = []
            for each_seed in RANDOM_SEEDS:
                
                # get filename
                finalfname_completedtasks = _get_final_fname("_taskscompleted.js", exp_key, each_wrkld_cfg, each_seed)
                
                try:        
                    print "getting : ", finalfname_completedtasks
                    ## get file data                        
                    json_data=open(finalfname_completedtasks)
                    file_data = json.load(json_data)
                    
                    all_nodes_tasks_sum_cc = []
                    for each_node_id, each_node_tasks in file_data.iteritems():
                        all_tasks_sum_cc = np.sum([float(t[1]) for t in each_node_tasks])
                        #all_tasks_mean_cc = np.mean([float(t[1]) for t in each_node_tasks])                        
                        all_nodes_tasks_sum_cc.append(all_tasks_sum_cc)
                    
                    # calculate
                    mean_sum_cc = np.mean(all_nodes_tasks_sum_cc) # mean of the sum_cc on each node
                    var_sum_cc = np.var(all_nodes_tasks_sum_cc) # variance of the sum_cc on each node
                    # coefficient of variance (normalised standard deviation)
                    coefvar_sum_cc = np.std(all_nodes_tasks_sum_cc)/np.mean(all_nodes_tasks_sum_cc) 
                    # save
                    each_seed_data.append(coefvar_sum_cc)                    
                                                    
                except Exception, e:                    
                    tb = traceback.format_exc()
                    print tb                    
                    sys.exit(e)
            
            alldata_perworkload_perexp_perseed[each_wrkld_cfg][exp_lbl] = np.mean(each_seed_data)    
        
    if SHOW_PLOTS==False:
        return
    
    ### plot data ####    
    if (plt_bars == True):
        
        best_colours = [
                        '#f0f9e8',
                        '#bae4bc',
                        '#7bccc4',
                        '#43a2ca',
                        '#0868ac'
                        ]        
        
        ## now we plot
        fig = plt.figure(figsize=(8*1.2, 6*1.2))
        fig.canvas.set_window_title('plot_workloadDistribution')
        ax = plt.subplot(111)      
        
        #global_colors = plt.get_cmap('Blues')(np.linspace(0, 1.0, len(global_types_of_tests)))      
        #global_colors_hex = [rgb2hex(c) for c in global_colors]
        
        #print global_colors_hex
        
        #pprint.pprint(global_colors)
        #sys.exit()
                
        rects_list = []
        rect_lbl_list = []
        i=0
        
        temp_k = alldata_perworkload_perexp_perseed.keys()[0]
        num_items = len(alldata_perworkload_perexp_perseed.keys())
        num_configs = len(alldata_perworkload_perexp_perseed.keys())
        num_exp = len(alldata_perworkload_perexp_perseed[temp_k].keys())
        
        width=0.1
        print width
        ind = np.arange(num_items)
        #ind = np.arange(num_exp)
        
        for num, each_exp in enumerate(alldata_perworkload_perexp_perseed[temp_k].keys()):
            ydata = [conf_data[each_exp] for k,conf_data  in alldata_perworkload_perexp_perseed.iteritems()]
            #xdata = ind+margin+(num*width)
            xdata = ind+(width*num)
            
            print xdata
            print "all config data for exp : ", each_exp, ydata
            
            rects = plt.bar(xdata, ydata, width, color=global_colors[i])
            
            plt.hold(True)
            rects_list.append(rects[0])
            rect_lbl_list.append(each_exp)
            
            i+=1
            
        
        plt.grid(b=True, which='major', color='k', linestyle='-', alpha=0.5)
        plt.grid(b=True, which='minor', color='k', linestyle='--', alpha=0.2)
        plt.minorticks_on()        
        leg = plt.legend(rects_list, rect_lbl_list,ncol=2)
        leg.draggable(True)
        ax.tick_params(axis = 'both', which = 'both')
        ax.set_ylabel('Mean Workload var.', fontsize=20)        
        ax.set_xlabel('Workload configurations', fontsize=20)        
        ax.xaxis.major.formatter._useMathText = True
        #ax.set_xticks(ind+((1.0)/num_exp))
        ax.set_xticks(ind+((width*num_exp)/2) )
        ax.set_xticklabels(alldata_perworkload_perexp_perseed.keys())
        
    
    




   
    

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
            

def _is_zero_admin_rate(ac,mp, pr, cmb, cc, ccuid):
    
    dkey =   str(ac) + "_" + \
             str(mp) + "_" + \
             str(pr) + "_" + \
             str(cmb) + "_" + \
             str(cc) + "_" + \
             str(ccuid)
    
    if dkey in global_admission_rate_eq_zero:
        return True
    else:
        return False


        
            
def func_fit_data(x, a, b, c):
    return a * np.exp(-b * x) + c        
        





       

###################################
#    HELPERS
###################################

          



###################################
#    MAIN
###################################
if __name__ == "__main__":
    load_data_flag = True
    
    if USE_MULTIPROCESSING==True:    
        # create jobs and dispatch #
        jobs = []
        
        p = multiprocessing.Process(target=plot_GoPLateness)
        jobs.append(p)
        p = multiprocessing.Process(target=plot_NodeIdlePeriods)
        jobs.append(p)
        p = multiprocessing.Process(target=plot_CommsOverhead)
        jobs.append(p)
        p = multiprocessing.Process(target=plot_CommsLatencies, args=(load_data_flag, [8,9], )) # mem
        jobs.append(p)
        p = multiprocessing.Process(target=plot_CommsLatencies, args=(load_data_flag, [1,15], )) # data
        jobs.append(p)
        p = multiprocessing.Process(target=plot_MappingExecOverhead)
        jobs.append(p)
                 
        p = multiprocessing.Process(target=plot_TaskResponseTime)
        jobs.append(p)
        
    #     p = multiprocessing.Process(target=plot_NodeUtilisation)
    #     jobs.append(p)
    #     p = multiprocessing.Process(target=plot_CumulativeIdleTime)
    #     jobs.append(p)
        
        for each_p in jobs:
            each_p.start() 
            
    else:
        plot_GoPLateness(plt_boxplot=True, plt_beanplot=False, load_data=load_data_flag)
        #plot_NodeIdlePeriods(load_data=load_data_flag, bar_plot=True, hist_plot=False)
        #plot_CommsOverhead(load_data=load_data_flag)
        #plot_CommsLatencies(load_data_flag, [8,9]) # mem
        #plot_CommsLatencies(load_data_flag, [1,15]) # data
        plot_MappingExecOverhead(load_data=load_data_flag)
        #plot_NodeUtilisation(load_data=load_data_flag, bar_plot=True)
        #plot_CumulativeIdleTime(load_data=load_data_flag, bar_plot=True)
        #plot_TaskResponseTime(load_data=load_data_flag,plt_boxplot=True)
        
    print "finished"
    
    if (SHOW_PLOTS==True):
        plt.show()






class LogFormatterTeXExponent(pylab.LogFormatter, object):
    """Extends pylab.LogFormatter to use 
    tex notation for tick labels."""
    
    def __init__(self, *args, **kwargs):
        super(LogFormatterTeXExponent, 
              self).__init__(*args, **kwargs)
        
    def __call__(self, *args, **kwargs):
        """Wrap call to parent class with 
        change to tex notation."""
        label = super(LogFormatterTeXExponent, 
                      self).__call__(*args, **kwargs)
        label = re.sub(r'e(\S)0?(\d+)', 
                       r'\\times 10^{\1\2}', 
                       str(label))
        label = "$" + label + "$"
        return label
