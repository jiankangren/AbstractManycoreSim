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
from scipy.stats import gaussian_kde

import matplotlib.patches as patches



import seaborn.apionly as sns

plt.style.use('bmh_rosh')


#MAX_NUM_GOPS_IN_VS = SimParams.WFGEN_MAX_GOPS_PER_VID

NOC_H = 8
NOC_W = 8

MAX_CC_LEVEL = 4000000


RANDOM_SEEDS_BATCH0=[81665, 33749, 43894, 53784, 26358]
RANDOM_SEEDS_BATCH1=[80505, 83660, 22817, 70263, 29917]
RANDOM_SEEDS_BATCH2=[26044, 6878, 66093, 69541, 5558]
RANDOM_SEEDS_BATCH3A=[76891, 22250, 69433]
RANDOM_SEEDS_BATCH3B=[42198, 18065]
RANDOM_SEEDS_BATCH4=[74076, 98652, 21149, 50399, 64217]
RANDOM_SEEDS_BATCH5=[44117, 57824, 42267, 83200, 99108]
RANDOM_SEEDS_BATCH6=[95928, 53864, 44289, 77379, 80521]


RANDOM_SEEDS = RANDOM_SEEDS_BATCH0 +\
                RANDOM_SEEDS_BATCH1 +\
                RANDOM_SEEDS_BATCH2 +\
                RANDOM_SEEDS_BATCH3A +\
                RANDOM_SEEDS_BATCH3B +\
                RANDOM_SEEDS_BATCH4 +\
                RANDOM_SEEDS_BATCH5 +\
                RANDOM_SEEDS_BATCH6

DEL_SEED_LIST = [83200, 33749, 22250, 53784, 44117] 

RANDOM_SEEDS = list(set(RANDOM_SEEDS) - set(DEL_SEED_LIST))

print len(set(RANDOM_SEEDS))

# local path
EXP_DATADIR = "Z:/MCASim/experiment_data/hevc_tiles_mapping_test/"
#EXP_DATADIR = "Z:/MCASim/experiment_data/hevc_mapping_highccr_test/"

# server path
#EXP_DATADIR = "../experiment_data/hevc_tiles_mapping_test/"
#EXP_DATADIR = "../experiment_data/hevc_mapping_highccr_test/"

global_types_of_tests = [
                    #{'mp':0, 'pr':0, 'cmb':920 , 'mmp':0, 'lbl': "LU_feedbk"},
                    #{'mp':0, 'pr':0, 'cmb':921 , 'mmp':0, 'lbl': "MWCRS_feedbk"},     
                    #{'mp':0, 'pr':0, 'cmb':922 , 'mmp':0, 'lbl': "Cluster-feedbk"}, 
                    {'mp':0, 'pr':0, 'cmb':903 , 'mmp':0, 'lbl': "LU"},
                    {'mp':0, 'pr':0, 'cmb':908 , 'mmp':0, 'lbl': "LU-FFI"},
                    #{'mp':0, 'pr':0, 'cmb':909 , 'mmp':0, 'lbl': "LU-GroupedTiles"},
                    #{'mp':0, 'pr':0, 'cmb':901 , 'mmp':0, 'lbl': "MWCRS"},     
                    #{'mp':0, 'pr':0, 'cmb':902 , 'mmp':0, 'lbl': "Cluster"},         
                    {'mp':0, 'pr':0, 'cmb':905 , 'mmp':0, 'lbl': "CL"},
                    {'mp':0, 'pr':0, 'cmb':910 , 'mmp':0, 'lbl': "CL-FFI"},
                    {'mp':0, 'pr':0, 'cmb':911 , 'mmp':0, 'lbl': "CL-IPB"},
                    #{'mp':0, 'pr':0, 'cmb':906 , 'mmp':0, 'lbl': "Cluster_v2-fakecp"},
                    {'mp':0, 'pr':0, 'cmb':907 , 'mmp':0, 'lbl': "CL-NoCCR"},
                    
                    {'mp':0, 'pr':0, 'cmb':914 , 'mmp':0, 'lbl': "CL-BG"},
                    {'mp':0, 'pr':0, 'cmb':915 , 'mmp':0, 'lbl': "CL-BG-FFI"},
                    
                    {'mp':0, 'pr':0, 'cmb':912 , 'mmp':0, 'lbl': "PP"},
                    
                      ]

GLOBAL_MP_ORDER = ["CL", "CL-IPB", "CL-NoCCR", "CL-FFI", "CL-BG", "CL-BG-FFI", "PP" , "LU", "LU-FFI"]


#GLOBAL_COLS = []
# GLOBAL_COLS = sns.color_palette("YlOrRd", 4)[:4] +\
#               sns.color_palette("Purples", 2)[:2] +\
#               ["lightskyblue"] + \
#               sns.color_palette("Greens", 2)

temp_blues = sns.color_palette("RdYlBu", 7)[5:]
temp_blues.reverse()

GLOBAL_COLS = sns.color_palette("RdYlBu", 7)[:4] + temp_blues +\
                ["lightpink"] + \
              sns.color_palette("Greens", 2)

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
            print each_exp
            ydata = [conf_data[each_exp] for k,conf_data  in alldata_perworkload_perexp_perseed.iteritems()]   
            
            #ydata = [alldata_perworkload_perexp_perseed[temp_k][mp_order[num]]]
            
            print len(ydata)
            
            print np.max(ydata),np.mean(ydata)
            
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



def plot_NodeBusyTimeAllPEDists(load_data=False, show_plot=False):
    data_fname = EXP_DATADIR + "data_NodeBusyTimeDistAllPEs.js"
        
    ### get data ####
    alldata_perworkload_perexp_perseed = OrderedDict()
    
    if load_data == False:
    
        for each_wrkld_cfg in global_workload_configs:        
            alldata_perworkload_perexp_perseed[each_wrkld_cfg] = OrderedDict()        
            for each_mapping_type in global_types_of_tests:               
                # which exp condition ?
                exp_key = _gen_exp_key(each_mapping_type['mp'],
                                       each_mapping_type['pr'],
                                       each_mapping_type['cmb'],0)
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
                        #all_nodes_idle_times = file_data['node_idle_time'][-1]["it_c"] 
                        simulation_time = file_data['node_idle_time'][-1]['time']                        
                        allnodes_busy_percentage = [
                                                    (1.0 - p_itc/float(simulation_time))*100.0
                                                    for p_itc in file_data['node_idle_time'][-1]["it_c"]
                                                    ]
                         
                        # save                        
                        each_seed_data.append(allnodes_busy_percentage)              
                                                
                                          
                    except Exception, e:                    
                        tb = traceback.format_exc()
                        print tb                    
                        sys.exit(e)
                alldata_perworkload_perexp_perseed[each_wrkld_cfg][exp_lbl] =  each_seed_data
        
        # dump results
        _write_formatted_file(data_fname, alldata_perworkload_perexp_perseed, "json")
        
        
    else:
        json_data=open(data_fname)
        alldata_perworkload_perexp_perseed = json.load(json_data)
        
        
    
    ## plot the results ##
    if show_plot == True:
        ### plot data ####
        fig = plt.figure(figsize=(4.5, 3.5)) # w, h
        ax = plt.subplot(111)
        fig.canvas.set_window_title('plot_NodeBusyTimeAllPEDists')
                
        rects_list = []
        rect_lbl_list = []
        i=0
        
        temp_k = alldata_perworkload_perexp_perseed.keys()[0]
        num_items = len(alldata_perworkload_perexp_perseed.keys())    
        num_exp = len(alldata_perworkload_perexp_perseed[temp_k].keys())
        
        width=0.8
        ind = np.arange(1, num_exp+1)
        
        wl_k = global_workload_configs[0]
        
        all_ydata = OrderedDict()
        for each_exp in GLOBAL_MP_ORDER:
            all_pe_data = []
            for six, each_seed in enumerate(RANDOM_SEEDS):
                data = np.array(sorted(alldata_perworkload_perexp_perseed[wl_k][each_exp][six]))
                if all_pe_data == []:
                    all_pe_data = np.array(data)
                else:
                    all_pe_data += np.array(data)
            
            all_ydata[each_exp] = (all_pe_data/float(len(RANDOM_SEEDS)))
        
        
        #mean_ydata = [float(alldata_perworkload_perexp_perseed[wl_k][each_exp]['len']*1000.0) for each_exp in GLOBAL_MP_ORDER] 
        #ydata = [ list(itertools.chain.from_iterable(alldata_perworkload_perexp_perseed[wl_k][each_exp])) for each_exp in GLOBAL_MP_ORDER]
        ydata = [all_ydata[each_exp] for each_exp in GLOBAL_MP_ORDER]
        
        print GLOBAL_MP_ORDER
        print [np.std(y) for y in ydata]
        
        #ydata_len = [ len(list(itertools.chain.from_iterable(alldata_perworkload_perexp_perseed[wl_k][each_exp]))) for each_exp in GLOBAL_MP_ORDER]        
        #print ydata_len
        
        #ydata_max = np.max([np.max(itertools.chain.from_iterable(alldata_perworkload_perexp_perseed[wl_k][each_exp])) for each_exp in GLOBAL_MP_ORDER])
        #ydata_min = np.max([np.min(itertools.chain.from_iterable(alldata_perworkload_perexp_perseed[wl_k][each_exp])) for each_exp in GLOBAL_MP_ORDER])
         
        #print GLOBAL_MP_ORDER
        #print "all config data (mean) for exp : ", ydata
           
        #ax.bar(ind, mean_ydata, width=width, color=GLOBAL_COLS)
        bps = ax.boxplot(ydata, positions=ind, patch_artist=True)
        boxplot_colorize_combinedplots(bps, GLOBAL_COLS)
           
        ax.xaxis.grid(False)
        ax.yaxis.grid(True)
        #ax.set_ylim([2.0, 3.0])
        ax.tick_params(axis = 'both', which = 'both')
        ax.set_ylabel('Mean PE busy time % in the NoC', fontsize=12)
        
        ax.set_xticks(ind)
        x_lbl_text = [m.replace("FFI", "F") for m in GLOBAL_MP_ORDER]
        x_lbl_text = [m.replace("IPB", "IPC") for m in x_lbl_text]
        ax.set_xticklabels(x_lbl_text, rotation=35, ha='right', fontsize=12)
        
        plt.subplots_adjust(left=0.13, right=0.995, top=0.96, bottom=0.185, hspace=0.14, wspace=0.25)
        
        
        
        


def plot_NodeBusyTime(load_data=False, show_plot=False):
    data_fname = EXP_DATADIR + "data_NodeBusyTime.js"
        
    ### get data ####
    alldata_perworkload_perexp_perseed = OrderedDict()
    
    if load_data == False:
    
        for each_wrkld_cfg in global_workload_configs:        
            alldata_perworkload_perexp_perseed[each_wrkld_cfg] = OrderedDict()        
            for each_mapping_type in global_types_of_tests:               
                # which exp condition ?
                exp_key = _gen_exp_key(each_mapping_type['mp'],
                                       each_mapping_type['pr'],
                                       each_mapping_type['cmb'],0)
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
                alldata_perworkload_perexp_perseed[each_wrkld_cfg][exp_lbl] =  each_seed_data
        
        # dump results
        _write_formatted_file(data_fname, alldata_perworkload_perexp_perseed, "json")
    
    
    else:
        json_data=open(data_fname)
        alldata_perworkload_perexp_perseed = json.load(json_data)


    ## plot the results ##
    if show_plot == True:
        ### plot data ####
        fig = plt.figure(figsize=(4.5, 4.5)) # w, h
        ax = plt.subplot(111)
        fig.canvas.set_window_title('plot_NodeBusyTime')
                
        rects_list = []
        rect_lbl_list = []
        i=0
        
        temp_k = alldata_perworkload_perexp_perseed.keys()[0]
        num_items = len(alldata_perworkload_perexp_perseed.keys())    
        num_exp = len(alldata_perworkload_perexp_perseed[temp_k].keys())
        
        width=0.8
        ind = np.arange(1, num_exp+1)
        
        wl_k = global_workload_configs[0]
        
        #mean_ydata = [float(alldata_perworkload_perexp_perseed[wl_k][each_exp]['len']*1000.0) for each_exp in GLOBAL_MP_ORDER] 
        ydata = [ alldata_perworkload_perexp_perseed[wl_k][each_exp] for each_exp in GLOBAL_MP_ORDER]
        
        print GLOBAL_MP_ORDER
        print "all config data (mean) for exp : ", ydata
           
        #ax.bar(ind, mean_ydata, width=width, color=GLOBAL_COLS)
        ax.boxplot(ydata, positions=ind)
           
        ax.xaxis.grid(False)
        ax.yaxis.grid(True)
        #ax.set_ylim([2.0, 3.0])
        ax.tick_params(axis = 'both', which = 'both')
        ax.set_ylabel('PE busy time %', fontsize=14)
        
        ax.set_xticks(ind+(width/2.0))
        ax.set_xticklabels(GLOBAL_MP_ORDER, rotation=35, ha='right')
        
        plt.subplots_adjust(left=0.14, right=0.995, top=0.98, bottom=0.14, hspace=0.14, wspace=0.25)
        
        





def plot_NodeIdlePeriods(load_data=False, show_plot=False):
    data_fname = EXP_DATADIR + "data_NodeIdlePeriods.js"
    
    ### get data ####
    alldata_perworkload_perexp_perseed = OrderedDict()
    
    if load_data == False:
    
        for each_wrkld_cfg in global_workload_configs:        
            alldata_perworkload_perexp_perseed[each_wrkld_cfg] = OrderedDict()        
            for each_mapping_type in global_types_of_tests:               
                # which exp condition ?
                exp_key = _gen_exp_key(each_mapping_type['mp'],
                                       each_mapping_type['pr'],
                                       each_mapping_type['cmb'],0)
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
                                                                                #'mode' : Counter(each_seed_data).most_common(1),
                                                                                'std' : np.std(each_seed_data),
                                                                                'var' : np.var(each_seed_data),
                                                                                'len' : len(each_seed_data)                                                                                
                                                                                }
        
        # dump results
        _write_formatted_file(data_fname, alldata_perworkload_perexp_perseed, "json")
    
    
    else:
        json_data=open(data_fname)
        alldata_perworkload_perexp_perseed = json.load(json_data)
    
        
    
    if show_plot==True:
        ### plot data ####
        fig = plt.figure(figsize=(4.5, 4.5)) # w, h
        ax = plt.subplot(111)
        fig.canvas.set_window_title('plot_NodeIdlePeriods')
                
        rects_list = []
        rect_lbl_list = []
        i=0
        
        temp_k = alldata_perworkload_perexp_perseed.keys()[0]
        num_items = len(alldata_perworkload_perexp_perseed.keys())    
        num_exp = len(alldata_perworkload_perexp_perseed[temp_k].keys())
        
        width=0.8
        ind = np.arange(1, num_exp+1)
        
        wl_k = global_workload_configs[0]
        
        #mean_ydata = [float(alldata_perworkload_perexp_perseed[wl_k][each_exp]['len']*1000.0) for each_exp in GLOBAL_MP_ORDER] 
        mean_ydata = [float(alldata_perworkload_perexp_perseed[wl_k][each_exp]['mean']) for each_exp in GLOBAL_MP_ORDER]
        sum_ydata = [float(alldata_perworkload_perexp_perseed[wl_k][each_exp]['sum']) for each_exp in GLOBAL_MP_ORDER]
        
        
        print GLOBAL_MP_ORDER
        print "all config data (mean) for exp : ", mean_ydata
        print "all config data (sum) for exp : ", sum_ydata
           
        ax.bar(ind, mean_ydata, width=width, color=GLOBAL_COLS)
        
           
        ax.xaxis.grid(False)
        ax.yaxis.grid(True)
        #ax.set_ylim([2.0, 3.0])
        ax.tick_params(axis = 'both', which = 'both')
        ax.set_ylabel('Mean PE idle period (ms)', fontsize=14)
        
        ax.set_xticks(ind+(width/2.0))
        ax.set_xticklabels(GLOBAL_MP_ORDER, rotation=35, ha='right')
        
        plt.subplots_adjust(left=0.14, right=0.995, top=0.98, bottom=0.14, hspace=0.14, wspace=0.25)
        
        

 

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
        
        width=0.1
        ind = np.arange(num_items)
        
        for num, each_exp in enumerate(alldata_perworkload_perexp_perseed[temp_k].keys()):
            ydata = [conf_data[each_exp] for k,conf_data  in alldata_perworkload_perexp_perseed.iteritems()]        
            #print ydata
            xdata = ind+(width*num)
            print "all config data (mean) for exp : ", each_exp, [np.mean(yd) for yd in ydata], ", list_sizes:", [len(yd) for yd in ydata]
            print "all config data (cumsum) for exp : ", each_exp, [np.sum(yd) for yd in ydata], ", list_sizes:", [len(yd) for yd in ydata]
            
            bps = plt.boxplot(ydata,0, 'x', positions=xdata, widths=width, patch_artist=True)
            
            # plot actual data
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
            
        #plt.grid(b=True, which='major', color='k', linestyle='-', alpha=0.5)
        #plt.grid(b=True, which='minor', color='k', linestyle='--', alpha=0.2)
        plt.minorticks_on()    
        leg = plt.legend(rects_list, rect_lbl_list,ncol=3)
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
        ax.set_xticks(xdata)
        ax.set_xticklabels(alldata_perworkload_perexp_perseed.keys())
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
    f, axarr = plt.subplots(2, 3, sharex=True, sharey=False, figsize=(16,10))
    f.canvas.set_window_title('plot_combined_primary')    
    
    wf_key = global_workload_configs[0]
    xdata = np.arange(1, len(GLOBAL_MP_ORDER)+1)
    width = 0.5
    xticklbls = [ k.replace("FFI", "F").strip() for k in GLOBAL_MP_ORDER]
    xticklbls = [ k.replace("IPB", "IPC").strip() for k in xticklbls]
    
    
    # gop lateness
    ydata = [all_exp_goplateness[wf_key][k] for k in GLOBAL_MP_ORDER]
    bps = axarr[0,0].boxplot(ydata, 0, 'x', positions=xdata, widths=width, patch_artist=True)
    boxplot_colorize_combinedplots(bps, param_col = GLOBAL_COLS)
    axarr[0,0].set_ylabel("Job lateness (s)", fontsize=16)
    axarr[0,0].tick_params(axis='both', which='both', labelsize=16)
    #axarr[0,0].set_ylim([-1.11, 3.3]) # for normal ccr
    axarr[0,0].set_ylim([-1.11, 3.0]) # for normal ccr
    print "all_exp_goplateness -- plotted"
    
    # Comms cost
    ydata = [all_exp_commscost[wf_key][k] for k in GLOBAL_MP_ORDER]
    bps = axarr[0,1].boxplot(ydata, 0, 'x', positions=xdata, widths=width, patch_artist=True)
    boxplot_colorize_combinedplots(bps, param_col = GLOBAL_COLS)
    axarr[0,1].set_ylabel("Cumulative comm. basic latency (s)", fontsize=16)
    axarr[0,1].tick_params(axis='both', which='both', labelsize=16)
    axarr[0,1].set_ylim([20, 36])
    print "all_exp_commscost -- plotted"
    
    # mapping overhead
    ydata = [all_exp_mappingoverhead[wf_key][k] for k in GLOBAL_MP_ORDER]
    norm_ydata = _normalise_list(ydata, norm_min=np.amin(ydata), norm_max=np.amax(ydata))
    bps = axarr[0,2].boxplot(norm_ydata, 0, 'x', positions=xdata, widths=width, patch_artist=True)
    axarr[0,2].set_yscale("symlog", linthreshy=0.0005)
    boxplot_colorize_combinedplots(bps, param_col = GLOBAL_COLS)
    axarr[0,2].set_ylabel("Normalised mapping exec. overhead", fontsize=16)
    axarr[0,2].tick_params(axis='both', which='both', labelsize=16)
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
    
    axarr[1,0].tick_params(axis='both', which='both', labelsize=16)
    axarr[1,0].set_xticks(xdata) 
    axarr[1,0].set_xticklabels(xticklbls,  rotation=90)
    axarr[1,0].set_yscale("symlog", linthreshy=0.001)
    axarr[1,0].set_ylabel("Data flow response time (s)", fontsize=16)
    axarr[1,0].tick_params(axis='both', which='both', labelsize=16)
    #axarr[1,0].set_ylim([-0.0001, 0.9]) # for normal ccr
    axarr[1,0].set_ylim([-0.0001, 1.7]) # for highccr ccr
        
    
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
    
    axarr[1,1].tick_params(axis='both', which='both', labelsize=16)
    axarr[1,1].set_xticks(xdata) 
    axarr[1,1].set_xticklabels(xticklbls,  rotation=90)
    axarr[1,1].set_yscale("symlog", linthreshy=0.001)
    axarr[1,1].set_ylabel("Memory flow response time (s)", fontsize=16)
    axarr[1,1].tick_params(axis='both', which='both', labelsize=16)
    axarr[1,1].set_ylim([-0.0001, 6.6])
    
    
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
    
    axarr[1,2].tick_params(axis='both', which='both', labelsize=16)
    axarr[1,2].set_xticks(xdata) 
    axarr[1,2].set_xticklabels(xticklbls,  rotation=90)
    axarr[1,2].set_yscale("symlog", linthreshy=0.001)
    axarr[1,2].set_ylabel("Task turn-around time (s)", fontsize=16)
    axarr[1,2].tick_params(axis='both', which='both', labelsize=16)
    #axarr[1,2].set_ylim([-0.0001, 4.5]) # for normal ccr
    axarr[1,2].set_ylim([-0.0001, 0.2]) # for high ccr
    
    p1 = plt.Line2D((0,1),(0,0), ls='', marker='o', c='k', fillstyle='none', lw=0.8, ms=15, mew=1.5)
    p2 = plt.Line2D((0,1),(0,0), ls='', marker='v', c='k', fillstyle='none', lw=0.8, ms=15, mew=1.5)
    p3 = plt.Line2D((0,1),(0,0), ls='', marker='^', c='k', fillstyle='none', lw=0.8, ms=15, mew=1.5)
    l = f.legend((p1, p2, p3), ("Mean", "Min", "Max"), loc='top center', ncol=3, numpoints=1,labelspacing=1)
    l.draggable()
    l.get_frame().set_facecolor('#FFFFFF')
    l.get_frame().set_linewidth(0.0)
    
    
    for i in [0,1]:
        for j in [0,1,2]:
            axarr[i,j].xaxis.grid(False)
            axarr[i,j].yaxis.grid(True, which='major')
            axarr[i,j].axvline(x= 4.5, linewidth=1.0, color='k', linestyle='-', alpha=0.5)
            axarr[i,j].axvline(x= 6.5, linewidth=1.0, color='k', linestyle='-', alpha=0.5)
            axarr[i,j].axvline(x= 7.5, linewidth=1.0, color='k', linestyle='-', alpha=0.5)
    
    
#     # data-flw response time
#     ydata = [all_exp_dataflwresptime[wf_key][k] for k in GLOBAL_MP_ORDER]    
#     print [len(y) for y in ydata]
#     bps = axarr[1,0].boxplot(ydata, 0, 'x', positions=xdata, widths=width, patch_artist=True)
#     boxplot_colorize_combinedplots(bps, param_col = GLOBAL_COLS)
#     axarr[1,0].set_xticks(xdata)
#     axarr[1,0].set_xticklabels(xticklbls,  rotation=90)
#     axarr[1,0].set_yscale("symlog", linthreshy=0.001)
#     axarr[1,0].set_ylabel("Data flow response time (s)", fontsize=16)
#     axarr[1,0].tick_params(axis='both', which='both', labelsize=16)
#     axarr[1,0].set_ylim([-0.0001, 0.9])
#     print "all_exp_dataflwresptime -- plotted"
#       
#     # mem-flw response time
#     ydata = [all_exp_memflwresptime[wf_key][k] for k in GLOBAL_MP_ORDER]
#     print [len(y) for y in ydata]
#     bps = axarr[1,1].boxplot(ydata, 0, 'x', positions=xdata, widths=width, patch_artist=True)
#     boxplot_colorize_combinedplots(bps, param_col = GLOBAL_COLS)
#     axarr[1,1].set_xticks(xdata)
#     axarr[1,1].set_xticklabels(xticklbls, rotation=90)
#     axarr[1,1].set_yscale("symlog", linthreshy=0.001)
#     axarr[1,1].set_ylabel("Memory flow response time (s)", fontsize=16)
#     axarr[1,1].tick_params(axis='both', which='both', labelsize=16)
#     axarr[1,1].set_ylim([-0.0001, 6.6])
#     print "all_exp_memflwresptime -- plotted"
#       
#     # task turnaround time
#     ydata = [all_exp_taskturnaroundtime[wf_key][k] for k in GLOBAL_MP_ORDER]
#     print [len(y) for y in ydata]
#     bps = axarr[1,2].boxplot(ydata, 0, 'x', positions=xdata, widths=width, patch_artist=True)
#     boxplot_colorize_combinedplots(bps, param_col = GLOBAL_COLS)
#     axarr[1,2].set_xticks(xdata)
#     axarr[1,2].set_xticklabels(xticklbls, rotation=90)
#     axarr[1,2].set_yscale("symlog", linthreshy=0.01)
#     axarr[1,2].set_ylabel("Task turn-around time (s)", fontsize=16)
#     axarr[1,2].tick_params(axis='both', which='both', labelsize=16)
#     axarr[1,2].set_ylim([-0.0001, 4.5])
#     print "all_exp_taskturnaroundtime -- plotted"
     
    plt.subplots_adjust(left=0.06, right=0.995, top=0.98, bottom=0.13, hspace=0.14, wspace=0.25)
    

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
plot_NodeIdlePeriods(load_data=True, show_plot=True)
#plot_NodeBusyTime(load_data=False, show_plot=False)
#plot_NodeBusyTimeAllPEDists(load_data=True, show_plot=True)
#plot_FlowResponseTime(filter_flw_type=[1,15], title_prefix='Data', load_data=False, show_plot=False)
#plot_FlowResponseTime(filter_flw_type=[8,9], title_prefix='Memory', load_data=False, show_plot=False)
#plot_TaskResponseTime(load_data=False, show_plot=False)
#plot_CommsOverhead(load_data=False, show_plot=False)

#plot_MappingExecOverhead(load_data=True, show_plot=True)

#plot_CommsInfo(load_data=False, show_plot=True)

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
