import sys, os, csv, pprint, math

#sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from collections import OrderedDict
import numpy as np
import traceback
import re
import pylab
import random
import shutil
import math
import matplotlib
matplotlib.use('Qt4Agg')
import matplotlib.pyplot as plt
import itertools
import json


import matplotlib.patches as patches



import seaborn.apionly as sns

plt.style.use('bmh_rosh')


#MAX_NUM_GOPS_IN_VS = SimParams.WFGEN_MAX_GOPS_PER_VID

NOC_H = 8
NOC_W = 8

MAX_CC_LEVEL = 4000000


BATCH0A_RANDOM_SEED_ARRAY=[81665, 33749, 43894]
BATCH0B_RANDOM_SEED_ARRAY=[53784, 26358]

BATCH1A_RANDOM_SEED_ARRAY=[80505, 83660, 22817]
BATCH1B_RANDOM_SEED_ARRAY=[70263, 29917]

BATCH2A_RANDOM_SEED_ARRAY=[26044, 6878, 66093]
BATCH2B_RANDOM_SEED_ARRAY=[69541, 5558]

BATCH3A_RANDOM_SEED_ARRAY=[76891, 22250, 69433]
BATCH3B_RANDOM_SEED_ARRAY=[42198, 18065]

BATCH4A_RANDOM_SEED_ARRAY=[74076, 98652, 21149]
BATCH4B_RANDOM_SEED_ARRAY=[50399, 64217]

BATCH5A_RANDOM_SEED_ARRAY=[44117, 57824, 42267]
BATCH5B_RANDOM_SEED_ARRAY=[83200, 99108]

BATCH6A_RANDOM_SEED_ARRAY=[95928, 53864, 44289]
BATCH6B_RANDOM_SEED_ARRAY=[77379, 80521]



RANDOM_SEEDS =  BATCH0A_RANDOM_SEED_ARRAY + BATCH0B_RANDOM_SEED_ARRAY +\
                BATCH1A_RANDOM_SEED_ARRAY + BATCH1B_RANDOM_SEED_ARRAY +\
                BATCH2A_RANDOM_SEED_ARRAY + BATCH2B_RANDOM_SEED_ARRAY +\
                BATCH3A_RANDOM_SEED_ARRAY + BATCH3B_RANDOM_SEED_ARRAY +\
                BATCH4A_RANDOM_SEED_ARRAY + BATCH4B_RANDOM_SEED_ARRAY +\
                BATCH5A_RANDOM_SEED_ARRAY + BATCH5B_RANDOM_SEED_ARRAY +\
                BATCH6A_RANDOM_SEED_ARRAY + BATCH6B_RANDOM_SEED_ARRAY

#RANDOM_SEEDS =  BATCH6A_RANDOM_SEED_ARRAY + BATCH6B_RANDOM_SEED_ARRAY
                
                


DEL_SEED_LIST = [83200, 33749, 22250, 53784, 44117]
#DEL_SEED_LIST = []

RANDOM_SEEDS = list(set(RANDOM_SEEDS) - set(DEL_SEED_LIST))

print len(set(RANDOM_SEEDS))

# local path
EXP_DATADIR = "Z:/MCASim/experiment_data/hevc_tile_mapping_wMemPSel_HighCCR/"


# server path
#EXP_DATADIR = "../experiment_data/hevc_tile_mapping_wMemPSel_HighCCR/"

global_types_of_tests = [
                    # CL mapper 
                    {'mp':0, 'pr':0, 'cmb':905 , 'mmp':0, 'lbl': "CL+MMCP-Dist"},                    
                    {'mp':0, 'pr':0, 'cmb':905 , 'mmp':1, 'lbl': "CL+MMCP-LU"},
                    {'mp':0, 'pr':0, 'cmb':905 , 'mmp':3, 'lbl': "CL+MMCP-LUDist"},                    
                    {'mp':0, 'pr':0, 'cmb':905 , 'mmp':36, 'lbl': "CL+MMCP-LBP"},
                    {'mp':0, 'pr':0, 'cmb':905 , 'mmp':37, 'lbl': "CL+MMCP-Rand"},
                    {'mp':0, 'pr':0, 'cmb':905 , 'mmp':31, 'lbl': "CL+MMCP-Fair"},
                    {'mp':0, 'pr':0, 'cmb':905 , 'mmp':38, 'lbl': "CL+MMCP-InvPar"},
                                        
                    # CL-BG mapper
                    {'mp':0, 'pr':0, 'cmb':914 , 'mmp':0, 'lbl': "CL-BG+MMCP-Dist"},
                    {'mp':0, 'pr':0, 'cmb':914 , 'mmp':1, 'lbl': "CL-BG+MMCP-LU"},
                    {'mp':0, 'pr':0, 'cmb':914 , 'mmp':3, 'lbl': "CL-BG+MMCP-LUDist"},                    
                    {'mp':0, 'pr':0, 'cmb':914 , 'mmp':36, 'lbl': "CL-BG+MMCP-LBP"},
                    {'mp':0, 'pr':0, 'cmb':914 , 'mmp':37, 'lbl': "CL-BG+MMCP-Rand"},
                    {'mp':0, 'pr':0, 'cmb':914 , 'mmp':31, 'lbl': "CL-BG+MMCP-Fair"},
                    {'mp':0, 'pr':0, 'cmb':914 , 'mmp':38, 'lbl': "CL-BG+MMCP-InvPar"},
                                        
                    # PP mapper
                    {'mp':0, 'pr':0, 'cmb':912 , 'mmp':0, 'lbl': "PP+MMCP-Dist"},
                    {'mp':0, 'pr':0, 'cmb':912 , 'mmp':1, 'lbl': "PP+MMCP-LU"},
                    {'mp':0, 'pr':0, 'cmb':912 , 'mmp':3, 'lbl': "PP+MMCP-LUDist"},                    
                    {'mp':0, 'pr':0, 'cmb':912 , 'mmp':36, 'lbl': "PP+MMCP-LBP"},
                    {'mp':0, 'pr':0, 'cmb':912 , 'mmp':37, 'lbl': "PP+MMCP-Rand"},
                    {'mp':0, 'pr':0, 'cmb':912 , 'mmp':31, 'lbl': "PP+MMCP-Fair"},
                    {'mp':0, 'pr':0, 'cmb':912 , 'mmp':38, 'lbl': "PP+MMCP-InvPar"},
                    
                    # LU mappers
                    {'mp':0, 'pr':0, 'cmb':903 , 'mmp':0, 'lbl': "LU+MMCP-Dist"},
                    {'mp':0, 'pr':0, 'cmb':903 , 'mmp':1, 'lbl': "LU+MMCP-LU"},
                    {'mp':0, 'pr':0, 'cmb':903 , 'mmp':3, 'lbl': "LU+MMCP-LUDist"},
                    {'mp':0, 'pr':0, 'cmb':903 , 'mmp':36, 'lbl': "LU+MMCP-LBP"},
                    {'mp':0, 'pr':0, 'cmb':903 , 'mmp':37, 'lbl': "LU+MMCP-Rand"},
                    {'mp':0, 'pr':0, 'cmb':903 , 'mmp':31, 'lbl': "LU+MMCP-Fair"},
                    {'mp':0, 'pr':0, 'cmb':903 , 'mmp':38, 'lbl': "LU+MMCP-InvPar"},
                    
                      ]

GLOBAL_MP_ORDER = [
                   
                    # CL mapper 
                    "CL+MMCP-Dist",                    
                    "CL+MMCP-LU",
                    "CL+MMCP-LUDist",                    
                    "CL+MMCP-LBP",
                    "CL+MMCP-Rand",
                    "CL+MMCP-Fair",
                    "CL+MMCP-InvPar",
                                        
                    # CL-BG mapper
                    "CL-BG+MMCP-Dist",
                    "CL-BG+MMCP-LU",
                    "CL-BG+MMCP-LUDist",                    
                    "CL-BG+MMCP-LBP",
                    "CL-BG+MMCP-Rand",
                    "CL-BG+MMCP-Fair",
                    "CL-BG+MMCP-InvPar",
                                        
                    # PP mapper
                    "PP+MMCP-Dist",
                    "PP+MMCP-LU",
                    "PP+MMCP-LUDist",                    
                    "PP+MMCP-LBP",
                    "PP+MMCP-Rand",
                    "PP+MMCP-Fair",
                    "PP+MMCP-InvPar",
                    
                    # LU mappers
                    "LU+MMCP-Dist",
                    "LU+MMCP-LU",
                    "LU+MMCP-LUDist",
                    "LU+MMCP-LBP",
                    "LU+MMCP-Rand",
                    "LU+MMCP-Fair",
                    "LU+MMCP-InvPar",
                   ]

NUM_MMCP_TYPES = 7
MMCP_TYPES_LBL = ["MMCP-Dist", "MMCP-LU", "MMCP-LUDist", "MMCP-LBP", "MMCP-Rand", "MMCP-Fair", "MMCP-InvPar"]

GLOBAL_COLS = sns.color_palette("YlOrRd", 4)[:4] +\
               sns.color_palette("Purples", 2)[:2] +\
               ["lightskyblue"] + \
               sns.color_palette("Greens", 2)
 
temp_blues = sns.color_palette("RdYlBu", 7)[5:]
temp_blues.reverse()
 
GLOBAL_COLS = [sns.color_palette("RdYlBu", 7)[0]]*NUM_MMCP_TYPES +\
              [temp_blues[0]]*NUM_MMCP_TYPES +\
                 ["lightpink"]*NUM_MMCP_TYPES + \
               [sns.color_palette("Greens", 2)[0]]*NUM_MMCP_TYPES

global_admission_rate_eq_zero = {}

DVB_RESOLUTIONS = [(3840,2160),(2560,1440), 
                   (1920,1080),(1280,720),
                   (854,480),(640,360),
                   (426,240),
                      ]

#global_workload_configs = ["WL1", "WL2", "WL3", "WL4"]
global_workload_configs = ["WL2"]
#global_workload_configs = ["Test"]


def _gen_exp_key (mp, pr, cmb, mmp):
    exp_key = "ac"+str(0) + \
                        "mp"+str(mp)+ \
                        "pr"+str(pr)+ \
                        "cmb"+str(cmb)+\
                        "mmp"+str(mmp)
    return exp_key

def _get_final_fname(fname, exp_key, wl_cfg, seed):
    subdir1 = EXP_DATADIR + "/" + wl_cfg + "/"  + exp_key + "/"          
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
        box.set( color='#000000', linewidth=2)
        # change fill color
        box.set( facecolor =  param_col)
        i+=1
    
    ## change color and linewidth of the whiskers
    for whisker in bp['whiskers']:
        whisker.set(color='#000000', linewidth=2, linestyle='-')
    
    ## change color and linewidth of the caps
    for cap in bp['caps']:
        cap.set(color='#000000', linewidth=2)
    
    ## change color and linewidth of the medians
    for median in bp['medians']:
        median.set(color='#000000', linewidth=2)
    
    ## change the style of fliers and their fill
    for flier in bp['fliers']:
        flier.set(marker='x', color='r', alpha=0.5)


def boxplot_colorize_combinedplots(bp, param_col, fc='#B8DCE6'):
    
    i=0
    ## change outline color, fill color and linewidth of the boxes
    for box in bp['boxes']:
        # change outline color
        box.set( color='#000000', linewidth=1.0)
        # change fill color
        box.set( facecolor =  param_col[i])
        i+=1
    
    ## change color and linewidth of the whiskers
    for whisker in bp['whiskers']:
        whisker.set(color='#000000', linewidth=1.0, linestyle='-')
    
    ## change color and linewidth of the caps
    for cap in bp['caps']:
        cap.set(color='#000000', linewidth=1.0)
    
    ## change color and linewidth of the medians
    for median in bp['medians']:
        median.set(color='#000000', linewidth=1.0)
    
    ## change the style of fliers and their fill
    for flier in bp['fliers']:
        flier.set(marker='x', color='k', alpha=0.5)




def plot_MappingExecOverhead(load_data=False, show_plot=True):
    data_fname = EXP_DATADIR + "data_MappingExecOverhead.js"
    
    mp_order = []
    
    ### get data ####
    alldata_perworkload_perexp_perseed = OrderedDict()        
    
    if load_data == False:
    
        for each_wrkld_cfg in global_workload_configs:        
            alldata_perworkload_perexp_perseed[each_wrkld_cfg] = OrderedDict()
            for each_mapping_type in global_types_of_tests:               
                # which exp condition ?
                exp_key = _gen_exp_key(each_mapping_type['mp'],
                                       each_mapping_type['pr'],
                                       each_mapping_type['cmb'], 
                                       each_mapping_type['mmp'],
                                       )
                exp_lbl = each_mapping_type['lbl']  
                mp_order.append(exp_lbl)          
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
                
#                     if exp_lbl == "PP":
#                         print  each_seed, np.max(mapping_ovrhd)
                         
                
                alldata_perworkload_perexp_perseed[each_wrkld_cfg][exp_lbl] = each_seed_data
    
        # dump results
        _write_formatted_file(data_fname, alldata_perworkload_perexp_perseed, "json")
    
    else:
        json_data=open(data_fname)
        alldata_perworkload_perexp_perseed = json.load(json_data)
    
            
    ### plot data ####
    if show_plot == True:
        fig = plt.figure(figsize=(8*1.2, 6*1.2))
        fig.canvas.set_window_title('plot_MappingExecOverhead')
        ax = plt.subplot(111)
        print "-- plot_MappingExecOverhead --"
        
        scatter_colors = plt.get_cmap('rainbow')(np.linspace(0, 1.0, len(global_types_of_tests)))
                
        rects_list = []
        rect_lbl_list = []
        i=0
        
        temp_k = alldata_perworkload_perexp_perseed.keys()[0]
        num_items = len(alldata_perworkload_perexp_perseed.keys())    
        num_exp = len(alldata_perworkload_perexp_perseed[temp_k].keys())
        
        width=0.1
        ind = np.arange(num_items)
        
        
        # find global min/max values
        tmp_all_vals = [] 
        
        for num, each_exp in enumerate(alldata_perworkload_perexp_perseed[temp_k].keys()):       
            ydata = [conf_data[each_exp] for k,conf_data  in alldata_perworkload_perexp_perseed.iteritems()]    
            tmp_all_vals.extend(ydata[0])
        
        alldata_norm_min = np.min(tmp_all_vals)  
        alldata_norm_max = np.max(tmp_all_vals)
        
        for num, each_exp in enumerate(alldata_perworkload_perexp_perseed[temp_k].keys()):    
            ydata = [conf_data[each_exp] for k,conf_data  in alldata_perworkload_perexp_perseed.iteritems()]   
            
            #ydata = [alldata_perworkload_perexp_perseed[temp_k][mp_order[num]]]
            
            print len(ydata)
            
            norm_ydata = _normalise_list(ydata, norm_min=alldata_norm_min, norm_max=alldata_norm_max)
            #norm_ydata = ydata
            
            #print ydata
            xdata = ind+(width*num)
            
            print len(xdata)
            
            print "all config data (mean) for exp : ", each_exp, [np.mean(yd) for yd in norm_ydata], ", list_sizes:", [len(yd) for yd in norm_ydata]
            print "all config data (cumsum) for exp : ", each_exp, [np.sum(yd) for yd in norm_ydata], ", list_sizes:", [len(yd) for yd in norm_ydata]
            
            bps = plt.boxplot(norm_ydata,0, 'x', positions=xdata, widths=width, patch_artist=True)
            
    #         for scatter_y, scatter_x in zip(ydata, xdata):
    #             plt.scatter([scatter_x]*len(scatter_y), scatter_y, marker='x', color='r', zorder=100)
                
            boxplot_colorize(bps, param_col = scatter_colors[i])
            
            plt.hold(True)
            
            rect_lbl_list.append(each_exp)        
            rec = patches.Rectangle(
                              (0.72, 0.1), 0.2, 0.6,
                              facecolor=scatter_colors[i]
                              ),
            rects_list.append(rec)        
            i+=1
            print "---"
            
        plt.grid(b=True, which='major', color='k', linestyle='-', alpha=0.5)
        plt.grid(b=True, which='minor', color='k', linestyle='--', alpha=0.2)
        plt.minorticks_on()
        
        leg = plt.legend(rects_list, rect_lbl_list,ncol=3)
        leg.draggable(True)
        ax.tick_params(axis = 'both', which = 'both')
        ax.set_ylabel('Normalised mapping overhead', fontsize=20)        
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
        plt.yscale("symlog", linthreshy=0.0005)
    
    return



def plot_CommsOverhead(load_data = False, show_plot=True):
    data_fname = EXP_DATADIR + "data_CommsOverhead.js"
    
    ### get data ####
    alldata_perworkload_perexp_perseed = OrderedDict()
    alldata_perworkload_perexp_perseed_flow_savings = OrderedDict()
    
    if load_data == False:
        
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
                        
                        flows_bl = [f[0] for f in file_data['flows_completed']]    
                        flows_not_sent_proportion =  file_data['flows_not_sent_proportion']               
                        flows_bl_sum = np.sum(flows_bl)
                        
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
                
        # dump results
        _write_formatted_file(data_fname, alldata_perworkload_perexp_perseed, "json")
    
    else:
        json_data=open(data_fname)
        alldata_perworkload_perexp_perseed = json.load(json_data)
        
            
    ### plot data ####
    if show_plot == True:
        fig = plt.figure(figsize=(8*1.2, 6*1.2))
        fig.canvas.set_window_title('plot_CommsOverhead')
        ax = plt.subplot(111)
        print "-- plot_CommsOverhead --"
        
        scatter_colors = plt.get_cmap('rainbow')(np.linspace(0, 1.0, len(global_types_of_tests)))
                
        rects_list = []
        rect_lbl_list = []
        i=0
        
        temp_k = alldata_perworkload_perexp_perseed.keys()[0]
        num_items = len(alldata_perworkload_perexp_perseed.keys())    
        num_exp = len(alldata_perworkload_perexp_perseed[temp_k].keys())
        
        width=0.1
        ind = np.arange(num_items)
        
        for num, each_exp in enumerate(alldata_perworkload_perexp_perseed[temp_k].keys()):
            ydata = [conf_data[each_exp] for k,conf_data  in alldata_perworkload_perexp_perseed.iteritems()]   
            
            flw_savings_mean = [conf_data[each_exp] for k,conf_data  in alldata_perworkload_perexp_perseed_flow_savings.iteritems()] 
                 
            #print ydata
            xdata = ind+(width*num)
            print "all config data (mean) for exp : ", each_exp, [np.mean(yd) for yd in ydata], ", list_sizes:", [len(yd) for yd in ydata]
            print "all config data (cumsum) for exp : ", each_exp, [np.sum(yd) for yd in ydata], ", list_sizes:", [len(yd) for yd in ydata]
            
            print "flwsavings: all config data (mean) for exp : " , each_exp, np.mean(flw_savings_mean)
            
            bps = plt.boxplot(ydata,0, 'x', positions=xdata, widths=width, patch_artist=True)
            
    #         for scatter_y, scatter_x in zip(ydata, xdata):
    #             plt.scatter([scatter_x]*len(scatter_y), scatter_y, marker='x', color='r', zorder=100)
                
            boxplot_colorize(bps, param_col = scatter_colors[i])
            
            plt.hold(True)
            
            rect_lbl_list.append(each_exp)        
            rec = patches.Rectangle(
                              (0.72, 0.1), 0.2, 0.6,
                              facecolor=scatter_colors[i]
                              ),
            rects_list.append(rec)        
            i+=1
            print "---"
            
        plt.grid(b=True, which='major', color='k', linestyle='-', alpha=0.5)
        plt.grid(b=True, which='minor', color='k', linestyle='--', alpha=0.2)
        plt.minorticks_on()
        
        leg = plt.legend(rects_list, rect_lbl_list,ncol=3)
        leg.draggable(True)
        ax.tick_params(axis = 'both', which = 'both')
        ax.set_ylabel('Communication overhead', fontsize=20)        
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

    return
    
    
def plot_NodeIdlePeriods():
    
    ### get data ####
    alldata_perworkload_perexp_perseed = OrderedDict()
    
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
                    
                    # save
                    #each_seed_data.append(gop_lateness_dist_mean)
                    each_seed_data.extend(node_idle_periods)
                    
                                                    
                except Exception, e:                    
                    tb = traceback.format_exc()
                    print tb                    
                    sys.exit(e)
            
            
            alldata_perworkload_perexp_perseed[each_wrkld_cfg][exp_lbl] = each_seed_data 
    
    
    ### plot data ####
    fig = plt.figure(figsize=(8*1.2, 6*1.2))
    fig.canvas.set_window_title('plot_NodeIdlePeriods')
    ax = plt.subplot(111)     
    print "-- plot_NodeIdlePeriods --"
    
    scatter_colors = plt.get_cmap('rainbow')(np.linspace(0, 1.0, len(global_types_of_tests)))
    #scatter_colors = ['r', 'g', 'b']        
    rects_list = []
    rect_lbl_list = []
    i=0
    
    temp_k = alldata_perworkload_perexp_perseed.keys()[0]
    num_items = len(alldata_perworkload_perexp_perseed.keys())    
    num_exp = len(alldata_perworkload_perexp_perseed[temp_k].keys())
    
    width=0.1
    ind = np.arange(num_items)
    
    for num, each_exp in enumerate(alldata_perworkload_perexp_perseed[temp_k].keys()):
        ydata = [conf_data[each_exp] for k,conf_data  in alldata_perworkload_perexp_perseed.iteritems()]        
        #print ydata
        xdata = ind+(width*num)
        print "all config data (mean) for exp : ", each_exp, [np.mean(yd) for yd in ydata], ", list_sizes:", [len(yd) for yd in ydata]
        print "all config data (cumsum) for exp : ", each_exp, [np.sum(yd) for yd in ydata], ", list_sizes:", [len(yd) for yd in ydata]
        print "all config data (var) for exp : ", each_exp, [np.var(yd) for yd in ydata], ", list_sizes:", [len(yd) for yd in ydata]
        print "all config data (std) for exp : ", each_exp, [np.std(yd) for yd in ydata], ", list_sizes:", [len(yd) for yd in ydata]
        #print "all config data (mode) for exp : ", each_exp, [stats.mode(yd) for yd in ydata], ", list_sizes:", [len(yd) for yd in ydata]
        
        #bps = plt.boxplot(ydata,0, 'x', positions=xdata, widths=width, patch_artist=True)
        plt.hist(ydata, bins=5, histtype='step', color=scatter_colors[i], label=each_exp, lw=5)
        #plt.yscale('log')
        #for scatter_y, scatter_x in zip(ydata, xdata):
        #    plt.scatter([scatter_x]*len(scatter_y), scatter_y, marker='x', color='r', zorder=100)
            
        #boxplot_colorize(bps, param_col = scatter_colors[i])
        
        plt.hold(True)
        
        rect_lbl_list.append(each_exp)        
        rec = patches.Rectangle(
                          (0.72, 0.1), 0.2, 0.6,
                          facecolor=scatter_colors[i]
                          ),
        rects_list.append(rec)        
        i+=1
        
        print "---"
        
    plt.grid(b=True, which='major', color='k', linestyle='--', alpha=0.3)
    #plt.grid(b=True, which='minor', color='k', linestyle='--', alpha=0.2)
    plt.minorticks_on()
    box = ax.get_position()
    ax.set_position([box.x0-0.01, box.y0 + box.height * 0.06, box.width*1.12, box.height * 0.8])        
    leg = ax.legend(rects_list, rect_lbl_list,ncol=3, prop={'size':13}, loc='upper center', bbox_to_anchor=(0.5, 1.295),
          fancybox=True, shadow=True)
    
    leg.draggable(True)
    ax.tick_params(axis = 'both', which = 'both')
    ax.set_ylabel('Node Idle Periods', fontsize=20)        
    ax.set_xlabel('Workload configurations', fontsize=20)        
    #ax.xaxis.major.formatter._useMathText = True
    #plt.ticklabel_format(style='sci', axis='x', scilimits=(0,0), labelsize=20)
    #plt.tick_params(axis='both', which='major', labelsize=16)
    #plt.tick_params(axis='both', which='minor', labelsize=16)
    #plt.rc('font', **{'size':'16'})
    #ax.set_xticks(ind+0.5)
    #ax.set_xticks(ind+((width*num_exp)/2) )
    #ax.set_xticklabels(alldata_perworkload_perexp_perseed.keys())
    #ax.set_xticklabels( [r"$%.1f\times10^4$"% (round(float(x)/10000.0,1)) + "\n" + "(%d VSs)"%_get_wfs_for_cc(x) for x in sorted_cc_list] )
    #plt.rcParams['mathtext.default'] = 'regular'
    ax.set_xlim(-0.13, 2+(width*6))
    ax.set_ylim(-1.47, 41.4)
    ax.set_xticks(ind+( ((width*(float(num_exp)/(width*9.23))/2.0)) ) )
  
    return


 

def plot_GoPLateness(load_data=False, show_plot=True):    
    data_fname = EXP_DATADIR + "data_GoPLateness.js"
    
    ### get data ####
    alldata_perworkload_perexp_perseed = OrderedDict()
    
    if load_data == False:
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
                        
                        # save
                        #each_seed_data.append(gop_lateness_dist_mean)
                        each_seed_data.extend(gop_lateness_dist)
                                                        
                    except Exception, e:                    
                        tb = traceback.format_exc()
                        print tb                    
                        #sys.exit(e)
                
                
                alldata_perworkload_perexp_perseed[each_wrkld_cfg][exp_lbl] = each_seed_data 
    
        # dump results
        _write_formatted_file(data_fname, alldata_perworkload_perexp_perseed, "json")
    
    else:
        json_data=open(data_fname)
        alldata_perworkload_perexp_perseed = json.load(json_data)
    
    
    if show_plot == True:
        ### plot data ####
        fig = plt.figure(figsize=(8*1.2, 6*1.2))
        fig.canvas.set_window_title('plot_GoPLateness')
        ax = plt.subplot(111)     
        
        scatter_colors = GLOBAL_COLS
                
        rects_list = []
        rect_lbl_list = []
        i=0
        
        temp_k = alldata_perworkload_perexp_perseed.keys()[0]
        num_items = len(alldata_perworkload_perexp_perseed.keys())
        num_configs = len(alldata_perworkload_perexp_perseed.keys())
        num_exp = len(alldata_perworkload_perexp_perseed[temp_k].keys())
        
        width=0.5
        ind = np.arange(num_items)
        
        #for each_exp in GLOBAL_MP_ORDER:
        ydata = [alldata_perworkload_perexp_perseed[temp_k][each_exp] for each_exp in GLOBAL_MP_ORDER]  
        
              
        #print ydata
        xdata = np.arange(1, len(GLOBAL_MP_ORDER)+1)
        #print "all config data (mean) for exp : ", each_exp, [np.mean(yd) for yd in ydata], ", list_sizes:", [len(yd) for yd in ydata]
        #print "all config data (cumsum) for exp : ", each_exp, [np.sum(yd) for yd in ydata], ", list_sizes:", [len(yd) for yd in ydata]
        
        bps = plt.boxplot(ydata,0, 'x', positions=xdata, widths=width, patch_artist=True)
        
        # plot actual data
        #for scatter_y, scatter_x in zip(ydata, xdata):
        #    plt.scatter([scatter_x]*len(scatter_y), scatter_y, marker='x', color='r', zorder=100)
            
        boxplot_colorize_combinedplots(bps, param_col = GLOBAL_COLS)
        
        plt.hold(True)
            
        #plt.grid(b=True, which='major', color='k', linestyle='-', alpha=0.5)
        #plt.grid(b=True, which='minor', color='k', linestyle='--', alpha=0.2)
        plt.minorticks_on()    
        #leg = plt.legend(rects_list, rect_lbl_list,ncol=3)
        #leg.draggable(True)
        ax.tick_params(axis = 'both', which = 'both')
        ax.set_ylabel('GoP Lateness', fontsize=20)        
        ax.set_xlabel('Workload configurations', fontsize=20)        
        ax.xaxis.major.formatter._useMathText = True
        #plt.ticklabel_format(style='sci', axis='x', scilimits=(0,0), labelsize=20)
        #plt.tick_params(axis='both', which='major', labelsize=16)
        #plt.tick_params(axis='both', which='minor', labelsize=16)
        #plt.rc('font', **{'size':'16'})
        #ax.set_xticks(ind+0.5)
        ax.set_xticks(xdata)
        ax.set_xticklabels(GLOBAL_MP_ORDER, rotation=90)
        #ax.set_xticklabels( [r"$%.1f\times10^4$"% (round(float(x)/10000.0,1)) + "\n" + "(%d VSs)"%_get_wfs_for_cc(x) for x in sorted_cc_list] )
        #plt.rcParams['mathtext.default'] = 'regular'
        
    
    return
    




def plot_FlowResponseTime(load_data=False, filter_flw_type=[1,15], title_prefix='', show_plot = True): # data=[1,15], mem=[8,9]
    data_fname = EXP_DATADIR + "data_FlowResponseTime_" + title_prefix + ".js"
    
    ### get data ####
    alldata_perworkload_perexp_perseed = OrderedDict()
    
    if load_data == False:
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
                    finalfname_gopsummary = _get_final_fname("_flwcompletedshort.js", exp_key, each_wrkld_cfg, each_seed)
                    
                    try:        
                        print "getting : ", finalfname_gopsummary
                        ## get file data                        
                        json_data=open(finalfname_gopsummary)
                        file_data = json.load(json_data)
                        
                        flw_resptime = [f[0]+f[1] for f in file_data["flows_completed"] if f[2] in filter_flw_type]
                        
                        flw_resptime_mean = np.mean(flw_resptime)
                        flw_resptime_min = np.min(flw_resptime)
                        flw_resptime_max = np.max(flw_resptime)
                        
                        # save                    
                        each_seed_data.append(
                                              [flw_resptime_mean, flw_resptime_min, flw_resptime_max]
                                              )
                                              
                        
                                                        
                    except Exception, e:                    
                        tb = traceback.format_exc()
                        print tb                    
                        sys.exit(e)
                
                
                alldata_perworkload_perexp_perseed[each_wrkld_cfg][exp_lbl] = each_seed_data 
        
        
            # dump results
            _write_formatted_file(data_fname, alldata_perworkload_perexp_perseed, "json")
        
    else:
        json_data=open(data_fname)
        alldata_perworkload_perexp_perseed = json.load(json_data)
    
    ### plot data ####
    if show_plot == True:
        fig = plt.figure(figsize=(8*1.2, 6*1.2))
        fig.canvas.set_window_title('plot_FlwResponseTime - ' + title_prefix)
        ax = plt.subplot(111)     
        
        scatter_colors = GLOBAL_COLS      
        
                
        rects_list = []
        rect_lbl_list = []
        i=0
        
        temp_k = alldata_perworkload_perexp_perseed.keys()[0]
        num_items = len(alldata_perworkload_perexp_perseed.keys())
        num_configs = len(alldata_perworkload_perexp_perseed.keys())
        num_exp = len(alldata_perworkload_perexp_perseed[temp_k].keys())
        
        width=0.1
        ind = np.arange(num_items)
        
        for num, each_exp in enumerate(alldata_perworkload_perexp_perseed[temp_k].keys()):
            ydata = [conf_data[each_exp] for k,conf_data  in alldata_perworkload_perexp_perseed.iteritems()]        
            #print ydata
            xdata = ind+(width*num)
            print "all config data (mean) for exp : ", each_exp, [np.mean(yd) for yd in ydata], ", list_sizes:", [len(yd) for yd in ydata]
            print "all config data (cumsum) for exp : ", each_exp, [np.sum(yd) for yd in ydata], ", list_sizes:", [len(yd) for yd in ydata]
            
            bps = plt.boxplot(ydata,0, 'x', positions=xdata, widths=width, patch_artist=True)
            
            #for scatter_y, scatter_x in zip(ydata, xdata):
            #    plt.scatter([scatter_x]*len(scatter_y), scatter_y, marker='x', color='r', zorder=100)
                
            boxplot_colorize(bps, param_col = scatter_colors[i])
            
            plt.hold(True)
            
            rect_lbl_list.append(each_exp)        
            rec = patches.Rectangle(
                              (0.72, 0.1), 0.2, 0.6,
                              facecolor=scatter_colors[i]
                              ),
            rects_list.append(rec)        
            i+=1
            
        plt.grid(b=True, which='major', color='k', linestyle='-', alpha=0.5)
        plt.grid(b=True, which='minor', color='k', linestyle='--', alpha=0.2)
        plt.minorticks_on()    
        leg = plt.legend(rects_list, rect_lbl_list,ncol=3)
        leg.draggable(True)
        ax.tick_params(axis = 'both', which = 'both')
        ax.set_ylabel('FlwResponseTime', fontsize=20)        
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
        plt.yscale("symlog", linthreshy=0.01)
    
    return
    
    
    
    
def plot_TaskResponseTime(load_data=False, show_plot=True): # data=[1,15], mem=[8,9]
    data_fname = EXP_DATADIR + "data_TaskResponseTime.js"
    
    ### get data ####
    alldata_perworkload_perexp_perseed = OrderedDict()
    
    if load_data == False:
    
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
                    finalfname_gopsummary = _get_final_fname("_obuff.js", exp_key, each_wrkld_cfg, each_seed)
                    
                    try:        
                        print "getting : ", finalfname_gopsummary
                        ## get file data                        
                        json_data=open(finalfname_gopsummary)
                        file_data = json.load(json_data)
                        
                        task_resptime = [t['et']-t['dct'] if t['dct']!= None else t['et']-t['rt'] for t in file_data]
                        
                        task_resptime_mean = np.mean(task_resptime)
                        task_resptime_min = np.min(task_resptime)
                        task_resptime_max = np.max(task_resptime)
                        
                        # save                    
                        each_seed_data.append(
                                              [task_resptime_mean, task_resptime_min, task_resptime_max]
                                              )
                        
                                                        
                    except Exception, e:                    
                        tb = traceback.format_exc()
                        print tb                    
                        sys.exit(e)
                
                
                alldata_perworkload_perexp_perseed[each_wrkld_cfg][exp_lbl] = each_seed_data 
                
        # dump results
        _write_formatted_file(data_fname, alldata_perworkload_perexp_perseed, "json")
        
    else:
        json_data=open(data_fname)
        alldata_perworkload_perexp_perseed = json.load(json_data)
        
    
    ### plot data ####
    if show_plot == True:
        fig = plt.figure(figsize=(8*1.2, 6*1.2))
        fig.canvas.set_window_title('plot_TaskResponseTime')
        ax = plt.subplot(111)     
        
        scatter_colors = GLOBAL_COLS      
                
        rects_list = []
        rect_lbl_list = []
        i=0
        
        temp_k = alldata_perworkload_perexp_perseed.keys()[0]
        num_items = len(alldata_perworkload_perexp_perseed.keys())
        num_configs = len(alldata_perworkload_perexp_perseed.keys())
        num_exp = len(alldata_perworkload_perexp_perseed[temp_k].keys())
        
        width=0.1
        ind = np.arange(num_items)
        
        for num, each_exp in enumerate(alldata_perworkload_perexp_perseed[temp_k].keys()):
            ydata = [conf_data[each_exp] for k,conf_data  in alldata_perworkload_perexp_perseed.iteritems()]        
            #print ydata
            xdata = ind+(width*num)
            print "all config data (mean) for exp : ", each_exp, [np.mean(yd) for yd in ydata], ", list_sizes:", [len(yd) for yd in ydata]
            print "all config data (cumsum) for exp : ", each_exp, [np.sum(yd) for yd in ydata], ", list_sizes:", [len(yd) for yd in ydata]
            
            bps = plt.boxplot(ydata,0, 'x', positions=xdata, widths=width, patch_artist=True)
            
            for scatter_y, scatter_x in zip(ydata, xdata):
                plt.scatter([scatter_x]*len(scatter_y), scatter_y, marker='x', color='r', zorder=100)
                
            boxplot_colorize(bps, param_col = scatter_colors[i])
            
            plt.hold(True)
            
            rect_lbl_list.append(each_exp)        
            rec = patches.Rectangle(
                              (0.72, 0.1), 0.2, 0.6,
                              facecolor=scatter_colors[i]
                              ),
            rects_list.append(rec)        
            i+=1
            
        plt.grid(b=True, which='major', color='k', linestyle='-', alpha=0.5)
        plt.grid(b=True, which='minor', color='k', linestyle='--', alpha=0.2)
        plt.minorticks_on()    
        leg = plt.legend(rects_list, rect_lbl_list,ncol=3)
        leg.draggable(True)
        ax.tick_params(axis = 'both', which = 'both')
        ax.set_ylabel('TaskResponseTime', fontsize=20)        
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
        
    return


def plot_CommsInfo(load_data = False, show_plot=True):
    data_fname = EXP_DATADIR + "data_CommsInfo.js"
    
    ### get data ####
    alldata_perworkload_perexp_perseed = OrderedDict()
    alldata_perworkload_perexp_perseed_flow_savings = OrderedDict()
    
    if load_data == False:
        
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
                each_seed_data = {
                                  # payloads
                                  'flows_payload_sums' : [],
                                  'flows_payload_means' : [],
                                  'flows_payload_mins' : [],
                                  'flows_payload_maxes' : [],
                                  
                                  # num flows
                                  'flows_count' : [],
                                  
                                  # route_lengths
                                  'flows_rlen_means' : [],
                                  'flows_rlen_mins' : [],
                                  'flows_rlen_max' : [],                                  
                                  }
                
                for each_seed in RANDOM_SEEDS:                
                    # get filename
                    finalfname = _get_final_fname("_flwcompletedshort.js", exp_key, each_wrkld_cfg, each_seed)                
                    try:        
                        print "getting : ", finalfname
                        ## get file data                        
                        json_data=open(finalfname)
                        file_data = json.load(json_data)
                        
                        flows_payloads = [f[3] for f in file_data['flows_completed']]    
                        flows_route_lengths = [f[5] for f in file_data['flows_completed']]
                        flows_num = len(file_data['flows_completed'])
                        
                        # save
                        each_seed_data['flows_payload_sums'].append(np.sum(flows_payloads))
                        each_seed_data['flows_payload_means'].append(np.mean(flows_payloads))                        
                        each_seed_data['flows_payload_mins'].append(np.min(flows_payloads))
                        each_seed_data['flows_payload_maxes'].append(np.max(flows_payloads))
                        
                        each_seed_data['flows_count'].append(flows_num)
                        
                        each_seed_data['flows_rlen_means'].append(np.mean(flows_route_lengths))
                        each_seed_data['flows_rlen_mins'].append(np.min(flows_route_lengths))
                        each_seed_data['flows_rlen_max'].append(np.max(flows_route_lengths))
                                 
                                                        
                    except Exception, e:                    
                        tb = traceback.format_exc()
                        print tb                    
                        sys.exit(e)
                
                alldata_perworkload_perexp_perseed[each_wrkld_cfg][exp_lbl] = each_seed_data
                
                
        # dump results
        _write_formatted_file(data_fname, alldata_perworkload_perexp_perseed, "json")
    
    else:
        json_data=open(data_fname)
        alldata_perworkload_perexp_perseed = json.load(json_data)
        
            
    ### plot data ####
    if show_plot == True:
        print "-- plot_CommsOverhead --"
        temp_k = alldata_perworkload_perexp_perseed.keys()[0]        
        
        print "EXP_NAME, \t  sum_pl,  mean_rlen,  mean_flwcount,  sum_flwcount"
        print "---------------------------------------------------------------------------------------"
        wl_k = global_workload_configs[0]
        for num, each_exp in enumerate(GLOBAL_MP_ORDER): 
            all_ydata = alldata_perworkload_perexp_perseed[wl_k][each_exp]
                        
        
            print "%s \t  %d \t %.2f \t %.2f \t %.2f" % \
            (each_exp,\
             (np.sum(all_ydata['flows_payload_sums'])/float(1024*1024*1024)),\
            np.mean(all_ydata['flows_rlen_means']),\
            np.mean(all_ydata['flows_count'])/10000.0,\
            np.sum(all_ydata['flows_count'])/100000.0)
            
            
            
            
            

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
        
    
    pprint.pprint(alldata_perworkload_perexp_perseed)
    
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
        
        scatter_colors = GLOBAL_COLS      
        
        #pprint.pprint(scatter_colors)
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
            
            rects = plt.bar(xdata, ydata, width, color=scatter_colors[i])
            
            plt.hold(True)
            rects_list.append(rects[0])
            rect_lbl_list.append(each_exp)
            
            i+=1
            
        
        plt.grid(b=True, which='major', color='k', linestyle='-', alpha=0.5)
        plt.grid(b=True, which='minor', color='k', linestyle='--', alpha=0.2)
        plt.minorticks_on()        
        leg = plt.legend(rects_list, rect_lbl_list,ncol=3)
        leg.draggable(True)
        ax.tick_params(axis = 'both', which = 'both')
        ax.set_ylabel('Mean Workload var.', fontsize=20)        
        ax.set_xlabel('Workload configurations', fontsize=20)        
        ax.xaxis.major.formatter._useMathText = True
        #ax.set_xticks(ind+((1.0)/num_exp))
        ax.set_xticks(ind+((width*num_exp)/2) )
        ax.set_xticklabels(alldata_perworkload_perexp_perseed.keys())
        
    
    return



def plot_combined_primary():
        
    # fnames
    data_commscost_fname = EXP_DATADIR + "data_CommsOverhead.js"
    data_goplateness_fname = EXP_DATADIR + "data_GoPLateness.js"
    data_mappingoverhead_fname = EXP_DATADIR + "data_MappingExecOverhead.js"
    data_memflwresptime_fname = EXP_DATADIR + "data_FlowResponseTime_" + "Memory" + ".js"
    data_dataflwresptime_fname = EXP_DATADIR + "data_FlowResponseTime_" + "Data" + ".js"
    data_taskturnaroundtime_fname = EXP_DATADIR + "data_TaskResponseTime.js"
    
    
    ###### get data ######    
    json_data=open(data_goplateness_fname)
    all_exp_goplateness = json.load(json_data)
    print "all_exp_goplateness -- loaded"
    
    json_data=open(data_commscost_fname)
    all_exp_commscost = json.load(json_data)
    print "all_exp_commscost -- loaded"
            
    json_data=open(data_mappingoverhead_fname)
    all_exp_mappingoverhead = json.load(json_data)
    print "all_exp_mappingoverhead -- loaded"
  
    json_data=open(data_dataflwresptime_fname)
    all_exp_dataflwresptime = json.load(json_data)    
    print "all_exp_dataflwresptime -- loaded"
    
    json_data=open(data_memflwresptime_fname)
    all_exp_memflwresptime = json.load(json_data)
    print "all_exp_memflwresptime -- loaded"
  
    json_data=open(data_taskturnaroundtime_fname)
    all_exp_taskturnaroundtime = json.load(json_data)
    print "all_exp_taskturnaroundtime -- loaded"
  
    ###### plot ######
    f, axarr = plt.subplots(2, 3, sharex=True, sharey=False, figsize=(20,10))
    f.canvas.set_window_title('plot_combined_primary')    
    
    wf_key = global_workload_configs[0]
    xdata = np.arange(1, len(GLOBAL_MP_ORDER)+1)
    width = 0.5
    xticklbls = [ k.replace("FFI", "F").strip() for k in GLOBAL_MP_ORDER]
    xticklbls = [k[k.index("+")+1:] for k in xticklbls]
    
    # gop lateness
    ydata = [all_exp_goplateness[wf_key][k] for k in GLOBAL_MP_ORDER]
    new_data = []
    for y1 in ydata:
        y2 = [y for y in y1 if y>0]
        new_data.append(y2)
    
    bps = axarr[0,0].boxplot(ydata, 0, 'x', positions=xdata, widths=width, patch_artist=True)
    boxplot_colorize_combinedplots(bps, param_col = GLOBAL_COLS)
    axarr[0,0].set_ylabel("Job lateness (s)", fontsize=14)
    axarr[0,0].tick_params(axis='both', which='both', labelsize=12)
    axarr[0,0].set_ylim([-1.11, 3.0]) # for normal ccr
    #axarr[0,0].set_ylim([-1.11, 3.0]) # for normal ccr
    
    print "cumulative job lateness:"
    print GLOBAL_MP_ORDER
    print [len(y) for y in new_data]
    print [np.mean(y) for y in ydata]
    print [np.max(y) for y in ydata]
    
    print "all_exp_goplateness -- plotted"
    
    # Comms cost
    ydata = [all_exp_commscost[wf_key][k] for k in GLOBAL_MP_ORDER]
    bps = axarr[0,1].boxplot(ydata, 0, 'x', positions=xdata, widths=width, patch_artist=True)
    boxplot_colorize_combinedplots(bps, param_col = GLOBAL_COLS)
    axarr[0,1].set_ylabel("Cumulative comm. basic latency (s)", fontsize=14)
    axarr[0,1].tick_params(axis='both', which='both', labelsize=12)
    axarr[0,1].set_ylim([20, 36])
    print "all_exp_commscost -- plotted"
    
    # mapping overhead
    ydata = [all_exp_mappingoverhead[wf_key][k] for k in GLOBAL_MP_ORDER]
    norm_ydata = _normalise_list(ydata, norm_min=np.amin(ydata), norm_max=np.amax(ydata))
    bps = axarr[0,2].boxplot(norm_ydata, 0, 'x', positions=xdata, widths=width, patch_artist=True)
    axarr[0,2].set_yscale("symlog", linthreshy=0.0005)
    boxplot_colorize_combinedplots(bps, param_col = GLOBAL_COLS)
    axarr[0,2].set_ylabel("Normalised mapping exec. overhead", fontsize=14)
    axarr[0,2].tick_params(axis='both', which='both', labelsize=12)
    axarr[0,2].set_ylim([-1.55e-5, 1.1])
    print "all_exp_mappingoverhead -- plotted"
     
     
    # data-flw response time
    all_means = OrderedDict()
    all_maxes = OrderedDict()
    all_mins = OrderedDict()    
    for each_mp in GLOBAL_MP_ORDER:
        all_means[each_mp] = []
        all_maxes[each_mp] = []
        all_mins[each_mp] = [] 
        for each_seed in all_exp_dataflwresptime[wf_key][each_mp]:
            all_means[each_mp].append(each_seed[0])            
            all_mins[each_mp].append(each_seed[1])
            all_maxes[each_mp].append(each_seed[2])
    
    for ix, each_mp in enumerate(GLOBAL_MP_ORDER):
        axarr[1,0].scatter([ix+1]*len(all_means[each_mp]), all_means[each_mp], marker='o', color=GLOBAL_COLS[ix], s=100, lw = 0.8, edgecolor='k')
        axarr[1,0].hold(True)
        axarr[1,0].scatter([ix+1]*len(all_mins[each_mp]), all_mins[each_mp], marker='v', color=GLOBAL_COLS[ix], s=100, lw = 0.8, edgecolor='k')
        axarr[1,0].hold(True)
        axarr[1,0].scatter([ix+1]*len(all_maxes[each_mp]), all_maxes[each_mp], marker='^', color=GLOBAL_COLS[ix], s=100, lw = 0.8, edgecolor='k')
        axarr[1,0].hold(True)


    axarr[1,0].set_xticks(xdata) 
    axarr[1,0].set_xticklabels(xticklbls,  rotation=55, ha='right', fontsize=13)
    axarr[1,0].set_yscale("symlog", linthreshy=0.001)
    axarr[1,0].set_ylabel("Data flow response time (s)", fontsize=14)
    axarr[1,0].tick_params(axis='y-axis', which='both', labelsize=12)
    axarr[1,0].set_ylim([-0.0001, 1.1]) # for normal ccr
    #axarr[1,0].set_ylim([-0.0001, 1.7]) # for highccr ccr
        
    
    # mem-flw response time
    all_means = OrderedDict()
    all_maxes = OrderedDict()
    all_mins = OrderedDict()    
    for each_mp in GLOBAL_MP_ORDER:
        all_means[each_mp] = []
        all_maxes[each_mp] = []
        all_mins[each_mp] = [] 
        for each_seed in all_exp_memflwresptime[wf_key][each_mp]:
            all_means[each_mp].append(each_seed[0])            
            all_mins[each_mp].append(each_seed[1])
            all_maxes[each_mp].append(each_seed[2])
    
    for ix, each_mp in enumerate(GLOBAL_MP_ORDER):
        axarr[1,1].scatter([ix+1]*len(all_means[each_mp]), all_means[each_mp], marker='o', color=GLOBAL_COLS[ix], s=100, lw = 0.8, edgecolor='k')
        axarr[1,1].hold(True)
        axarr[1,1].scatter([ix+1]*len(all_mins[each_mp]), all_mins[each_mp], marker='v', color=GLOBAL_COLS[ix], s=100, lw = 0.8, edgecolor='k')
        axarr[1,1].hold(True)
        axarr[1,1].scatter([ix+1]*len(all_maxes[each_mp]), all_maxes[each_mp], marker='^', color=GLOBAL_COLS[ix], s=100, lw = 0.8, edgecolor='k')
        axarr[1,1].hold(True)
    

    axarr[1,1].set_xticks(xdata) 
    axarr[1,1].set_xticklabels(xticklbls,  rotation=55, ha='right', fontsize=13)
    axarr[1,1].set_yscale("symlog", linthreshy=0.001)
    axarr[1,1].set_ylabel("Memory flow response time (s)", fontsize=14)
    axarr[1,1].tick_params(axis='y-axis', which='both', labelsize=12)
    axarr[1,1].set_ylim([-0.0001, 10])
    
    
    # task turnaround time
    all_means = OrderedDict()
    all_maxes = OrderedDict()
    all_mins = OrderedDict()    
    for each_mp in GLOBAL_MP_ORDER:
        all_means[each_mp] = []
        all_maxes[each_mp] = []
        all_mins[each_mp] = [] 
        for each_seed in all_exp_taskturnaroundtime[wf_key][each_mp]:
            all_means[each_mp].append(each_seed[0])            
            all_mins[each_mp].append(each_seed[1])
            all_maxes[each_mp].append(each_seed[2])
    
    for ix, each_mp in enumerate(GLOBAL_MP_ORDER):
        axarr[1,2].scatter([ix+1]*len(all_means[each_mp]), all_means[each_mp], marker='o', color=GLOBAL_COLS[ix], s=100, lw = 0.8, edgecolor='k')
        axarr[1,2].hold(True)
        axarr[1,2].scatter([ix+1]*len(all_mins[each_mp]), all_mins[each_mp], marker='v', color=GLOBAL_COLS[ix], s=100, lw = 0.8, edgecolor='k')
        axarr[1,2].hold(True)
        axarr[1,2].scatter([ix+1]*len(all_maxes[each_mp]), all_maxes[each_mp], marker='^', color=GLOBAL_COLS[ix], s=100, lw = 0.8, edgecolor='k')
        axarr[1,2].hold(True)
    
    
    axarr[1,2].set_xticks(xdata) 
    axarr[1,2].set_xticklabels(xticklbls,  rotation=55, ha='right', fontsize=13)
    axarr[1,2].set_yscale("symlog", linthreshy=0.001)
    axarr[1,2].set_ylabel("Task turn-around time (s)", fontsize=14)
    axarr[1,2].tick_params(axis='y-axis', which='both', labelsize=12)
    axarr[1,2].set_ylim([-0.0001, 0.1]) # for normal ccr
    #axarr[1,2].set_ylim([-0.0001, 0.2]) # for high ccr
    
    p1 = plt.Line2D((0,1),(0,0), ls='', marker='o', c='k', fillstyle='none', lw=0.8, ms=15, mew=1.5)
    p2 = plt.Line2D((0,1),(0,0), ls='', marker='v', c='k', fillstyle='none', lw=0.8, ms=15, mew=1.5)
    p3 = plt.Line2D((0,1),(0,0), ls='', marker='^', c='k', fillstyle='none', lw=0.8, ms=15, mew=1.5)
    l = f.legend((p1, p2, p3), ("Mean", "Min", "Max"), loc='top center', ncol=3, numpoints=1,labelspacing=1)
    l.draggable()
    l.get_frame().set_facecolor('#FFFFFF')
    l.get_frame().set_linewidth(0.0)
    
    rect_lists = []
    rect_list_txt = []
    for each_mp, each_mp_col in zip(GLOBAL_MP_ORDER[::NUM_MMCP_TYPES], GLOBAL_COLS[::NUM_MMCP_TYPES]):
        r = plt.Rectangle((0, 0), 1, 1, fc=each_mp_col)        
        rect_lists.append(r)
        rect_list_txt.append(each_mp[:each_mp.index("+")])
    
    l2 = f.legend(rect_lists, rect_list_txt, loc='top center', ncol=4, labelspacing=1)
    l2.draggable()
    l2.get_frame().set_facecolor('#FFFFFF')
    l2.get_frame().set_linewidth(0.0)
    
    
    
    
    for i in [0,1]:
        for j in [0,1,2]:
            axarr[i,j].xaxis.grid(False)
            axarr[i,j].yaxis.grid(True, which='major')
            axarr[i,j].axvline(x= 7.5, linewidth=1.0, color='k', linestyle='-', alpha=0.5)
            axarr[i,j].axvline(x= 14.5, linewidth=1.0, color='k', linestyle='-', alpha=0.5)
            axarr[i,j].axvline(x= 21.5, linewidth=1.0, color='k', linestyle='-', alpha=0.5)
    
    

     
    plt.subplots_adjust(left=0.04, right=0.998, top=0.95, bottom=0.10, hspace=0.14, wspace=0.145)
    

def plot_combined_secondary():
    pass
       




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
#    HELPERS
###################################

def movingaverage(interval, window_size):
    window = np.ones(int(window_size))/float(window_size)
    return np.convolve(interval, window, 'same')          

def moving_average(a, n=3) :
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n

###################################
#    MAIN
###################################

#plot_workloadDistribution()
#plot_GoPLateness(load_data=False, show_plot=False)
#plot_NodeIdlePeriods()
#plot_FlowResponseTime(filter_flw_type=[1,15], title_prefix='Data', load_data=False, show_plot=False)
#plot_FlowResponseTime(filter_flw_type=[8,9], title_prefix='Memory', load_data=False, show_plot=False)
#plot_TaskResponseTime(load_data=False, show_plot=False)
#plot_CommsOverhead(load_data=False, show_plot=False)

#plot_MappingExecOverhead(load_data=False, show_plot=False)

plot_CommsInfo(load_data=False, show_plot=True)

#plot_combined_primary()



print "finished"

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
