import sys, os, csv, pprint, math

from collections import OrderedDict
import numpy as np
import traceback
import random
import shutil
import math
import matplotlib
matplotlib.use('Qt4Agg')
import matplotlib.pyplot as plt
#plt.style.use('bmh_rosh')


import scipy.stats
import itertools
from matplotlib.colors import ListedColormap, NoNorm
from matplotlib import mlab
from itertools import cycle # for automatic markers
import json
from operator import itemgetter

import matplotlib.cm as cm
from matplotlib.font_manager import FontProperties
#from SimParams import SimParams


plt.style.use('bmh_rosh')


NOC_H = 3
NOC_W = 3

#AC_TYPE = 14 # correct one used for thesis draft
AC_TYPE = 14 # ac used for BL correction


global_types_of_tests = [
                      
                      ## Deterministic - AC ##

                    #{'ac':11, 'mp':0, 'pr':4, 'cmb':840 }, # determ, lumm
                    {'ac':AC_TYPE, 'mp':0, 'pr':4, 'cmb':841 , 'lbl': "IPC"}, # determ, improved
                    {'ac':AC_TYPE, 'mp':0, 'pr':4, 'cmb':842 , 'lbl': "LWCRS"}, # determ, improved
                    {'ac':AC_TYPE, 'mp':0, 'pr':4, 'cmb':833 , 'lbl': "PP"}, # determ, improved
                                        
                    {'ac':AC_TYPE, 'mp':0, 'pr':4, 'cmb':834 , 'lbl': "BN"}, # determ, improved
                    {'ac':AC_TYPE, 'mp':12, 'pr':4, 'cmb':0 , 'lbl': "LM"}, # determ, improved                    
                    {'ac':AC_TYPE, 'mp':10, 'pr':4, 'cmb':0 , 'lbl': "LU"}, # determ, improved
                    
                      
                      ]


#EXP_DATA_DIR = "../experiment_data/hrt_video/multiseed_random_res/"
#EXP_DATA_DIR = "Z:/MCASim/experiment_data/hrt_video/noc_scale_noschedtest/"
#EXP_DATA_DIR = "Z:/MCASim/experiment_data/hrt_video/noc_scale_noschedtest_06052015/"
#EXP_DATA_DIR = "Z:/MCASim/experiment_data/hrt_video/noc_scale_noschedtest_070515/"

# correct one as at time of writing thesis - first draft
#EXP_DATA_DIR = "Z:/MCASim/experiment_data/hrt_video/noc_scale/"

# after BL correction
EXP_DATA_DIR = "Z:/Simulator_versions_perExperiment/ThesisTechCh5_NoC_CCR/src/experiment_data/hrt_video/noc_scale/"


RANDOM_SEED_LIST = \
[81665, 33749, 43894, 26358, 80505, \
 83660, 22817, 70263, 29917, 26044, \
 5558,  76891, 22250, 42198, 18065, \
 74076, 98652, 21149, 50399, 64217, \
 57824, 42267, 83200, 99108, \
 95928, 53864, 44289, 77379, 80521, \
 88117, 23327, 73337, 94064, 31982, \
 6878, 66093, 69541]


BATCH_1_RANDOM_SEED_LIST=[81665, 33749, 43894, 26358, 80505, \
83660, 22817, 70263, 29917, 26044, 76891]

BATCH_2_RANDOM_SEED_LIST=[50399, 64217, 44117, 57824, 42267, 83200, 99108, \
                          95928, 53864, 44289]

BATCH_3_RANDOM_SEED_LIST=[77379, 80521, 88117, 23327, 73337, 94064, 31982, 22250]

RANDOM_SEED_LIST = BATCH_1_RANDOM_SEED_LIST + BATCH_2_RANDOM_SEED_LIST + BATCH_3_RANDOM_SEED_LIST


# test seeds
RANDOM_SEED_LIST = [81665, 33749, 43894, 26358, 80505, # batch 1
                    83660, 22817, 70263, 29917, 26044, # batch 2
                    50399, 64217, 44117, 57824, 42267, # batch 3
                    99108, 95928, 53864, 44289, 76891, # batch 4
                    77379, 80521, 88117, 23327, 73337, # batch 5
                    94064, 31982, 22250, 83200, # batch 6
                    66093 # batch 7
                    
                    # more ..
                    #6878 66093 69541 18065 74076 #batch 7
                    #98652 21149 42198 5558 # batch8 - not run yet
                                                            
                    ]


#[81665, 33749]

# [81665, 33749, 43894, 26358, 80505, \
#  83660, 22817, 70263, 29917, 26044, \
#  5558,  76891, 22250, 42198, 18065, \
#  74076, 98652, 21149, 50399, 64217, \
#  44117, 57824, 42267, 83200, 99108, \
#  95928, 53864, 44289, 77379, 80521, \
#  88117, 23327, 73337, 94064, 31982, \
#  6878, 66093, 69541]

GLOBAL_COLS = {               
               #'r', '#fb9a99', # reds
               #'b', '#80b1d3', # blues
               #'g', '#a6d854',  # greens
               
               "IPC":'r', 
               "LWCRS":'#fb9a99',
               "PP":'#08306b',
               "BN":'#2171b5',
               "LU": '#6baed6',
               "LM": '#c6dbef',
               }

MP_ORDER = ["IPC", "LWCRS", "PP", "BN", "LU", "LM"]

def plot_GoPResponseTime(use_sched_test_results=False, load_from_file=False):
    
    all_exp_results = OrderedDict()
    #out_fname = os.path.splitext("path_to_file")[0] + "_plot_GoPResponseTime.js"
    out_fname = EXP_DATA_DIR + "_plot_GoPResponseTime.js"
    
    if (load_from_file == False):
        
        try :
            ## FOR EACH_SEED
            for each_seed in RANDOM_SEED_LIST:
                print each_seed
                # get the ccr values from file
                fname = '../util_scripts/ccr_list_allwfs_output_0.001_2.0_s'+ str(each_seed) + '.js'    
                json_data=open(fname)
                file_data = json.load(json_data) 
                seed_specific_data = file_data[str(each_seed)]        
                subdir1 = "seed_"+str(each_seed)+"/"
                
                # sort
                sorted_wf_sizes = sorted(seed_specific_data.keys())
                sorted_seed_specific_data = OrderedDict()
                for each_k in sorted_wf_sizes:
                    sorted_seed_specific_data[each_k] = seed_specific_data[each_k]
                
                
                ## FOR EACH_NOCSIZE
                offset = 0
                for each_wf_k, each_wf_v in sorted_seed_specific_data.iteritems():
                    noc_h = int(np.sqrt(int(each_wf_k)-offset))  
                    #if noc_h not in [9]:
                    #    continue          
                    subdir2 = subdir1 + "noc_h" + str(noc_h) + "/"
                    wf_nums = int(each_wf_k)        
                    sorted_ccr_entries = sorted(each_wf_v["ccr_list"].values(), reverse=True)
                    #print noc_h
                    if(noc_h not in all_exp_results):
                        all_exp_results[noc_h] = OrderedDict()
                                
                    ## FOR EACH_CCR
                    # get ccr specific results
                    for each_ccr_entry in sorted_ccr_entries:
                        ccr = round(each_ccr_entry['ccr'], 4)                
                        subdir3 = subdir2 + "ccr_" + str(ccr) + "/"
                        #rounded_ccr = round(ccr, 3)
                        rounded_ccr = _get_closest_ccr_from_ccr_list(ccr)
                        #print rounded_ccr
                        if(rounded_ccr not in all_exp_results[noc_h]):
                            all_exp_results[noc_h][rounded_ccr] = OrderedDict()
                        
                        ## FOR EACH_MPTYPE
                        for each_mp_type in global_types_of_tests:  
                            #print each_mp_type
                            mp_type_lbl = each_mp_type['lbl']
                            
                            # get data            
                            final_fname_prefix = "HRTVid_" + \
                                         "AC"+ str(each_mp_type['ac']) + "_" + \
                                         "MP"+ str(each_mp_type['mp']) + "_" + \
                                         "PR"+ str(each_mp_type['pr']) + "_" + \
                                         "CMB"+ str(each_mp_type['cmb']) + "_"
                            
                            FNAME_PREFIX = final_fname_prefix+str(noc_h)+"_"+str(noc_h)+"_"                        
                            fname = EXP_DATA_DIR+subdir3+FNAME_PREFIX + "test__gopsopbuffsumm.js" 
                            print fname   
                            json_data=open(fname)
                            gop_data = json.load(json_data)                                
                            gop_rt = [x['tt_wrt_dt'] for x in gop_data.values()]
                            gop_lateness = [x['gop_execution_lateness'] for x in gop_data.values()]                    
                                                
                            if(mp_type_lbl not in all_exp_results[noc_h][rounded_ccr]):
                                all_exp_results[noc_h][rounded_ccr][mp_type_lbl] = gop_lateness
                            else:
                                all_exp_results[noc_h][rounded_ccr][mp_type_lbl].extend(gop_lateness)
        
        except:
            pprint.pprint(sys.exc_info())
            print traceback.format_exc()
            sys.exit()
                   
        _write_formatted_file(out_fname, all_exp_results, "json")
        
    else:         
        json_data=open(out_fname)
        all_exp_results = json.load(json_data)      
        
    
    
    mapping_heuristic_sort_order = ['IPC', 'LWCRS', 'PP', 'BN', 'LU', 'LM']
    
    ### plot results
    num_noc_sizes = len(all_exp_results.keys())
    num_ccr_vals = len( all_exp_results[all_exp_results.keys()[0]].keys() )
    num_mappers = len( global_types_of_tests )
    
#     print num_mappers
#     print num_noc_sizes
#     print num_ccr_vals    
#     print all_exp_results[all_exp_results.keys()[0]].keys()
    
    mapping_type_colors = plt.get_cmap('jet')(np.linspace(0, 1.0, 6))
    
    f, axarr = plt.subplots(num_ccr_vals, num_noc_sizes, sharex=True, sharey=True)
    f.canvas.set_window_title('plot_GoPResponseTime')    
    ix_i = 0
    ix_j = 0
    for each_noc_h_k  in sorted(all_exp_results.keys()):
        each_noc_h_v = all_exp_results[each_noc_h_k]
        ix_i = 0
        
        for each_ccr_k in sorted(each_noc_h_v.keys(), reverse=True):
            each_ccr_v = each_noc_h_v[each_ccr_k]
            print each_noc_h_k, each_ccr_k
            
            # sort according to the mapping list
            sorted_each_ccr_v = OrderedDict()
            for k in mapping_heuristic_sort_order:
                sorted_each_ccr_v[k] = each_ccr_v[k]
            
            boxplot_data = [gop_data for map_lbl, gop_data in sorted_each_ccr_v.iteritems()]
            norm_boxplot_data = _long_normalise_boxplot_data(boxplot_data)
            
            boxplot_labels = [map_lbl for map_lbl, gop_data in sorted_each_ccr_v.iteritems()]
            boxplot_means = [np.mean(gop_data) for gop_data in norm_boxplot_data]
            #boxplot_max = [np.max(gop_data) for map_lbl, gop_data in each_ccr_v.iteritems()]
            
            # plot a group of boxplots for each scenario
            width=0.7 
            ind = np.arange(num_mappers)
            pos_0 = ind
            
            
            bp=axarr[ix_i, ix_j].boxplot(norm_boxplot_data,0,'',positions=pos_0, widths=width, patch_artist=True)
            boxplot_colorize(bp)
            axarr[ix_i, ix_j].plot(ind, boxplot_means, marker='o', color='r', linewidth=1)
            
            #axarr[ix_i].boxplot(norm_boxplot_data,0,positions=pos_0, widths=width)
            #axarr[ix_i].plot(ind, boxplot_means, marker='d', color='g', linewidth=0.3)
            #axarr[ix_i, ix_j].plot(ind, boxplot_max, marker='x', color='r', linewidth=0.3)
            
            labels = boxplot_labels
            xticks = range(0,(len(labels)))
            xticks = [x for x in xticks]    
            axarr[ix_i, ix_j].set_xticks(xticks)
            axarr[ix_i, ix_j].set_xticklabels(labels, rotation='vertical')
            #axarr[ix_i, ix_j].set_title(str(each_noc_h_k)+"x"+str(each_noc_h_k)+","+str(each_ccr_k))
            axarr[ix_i, ix_j].grid(True)
            
            if(ix_i == len(all_exp_results.keys())):
                axarr[ix_i, ix_j].set_xlabel("\nNoC_size="+str(each_noc_h_k)+"x"+str(each_noc_h_k), fontsize=18)
                
            if(ix_j == 0):
                axarr[ix_i, ix_j].set_ylabel("CCR="+str(each_ccr_k)+"\n\nGoP Lateness",multialignment='center', fontsize=18)
             
            
#             axarr[ix_i].set_xticks(xticks)
#             axarr[ix_i].set_xticklabels(labels)
#             axarr[ix_i].set_title(str(each_noc_h_k)+"x"+str(each_noc_h_k)+","+str(each_ccr_k))
#             axarr[ix_i].grid(True)
#             
            ix_i += 1
        ix_j += 1    
            
    plt.tick_params(axis='both', which='major', labelsize=16)
    plt.tick_params(axis='both', which='minor', labelsize=16)
    plt.rc('font', **{'size':'16'})
    
    
#     big_ax = f.add_subplot(111,frameon=False)
#     big_ax.set_axis_bgcolor('none')
#     big_ax.tick_params(labelcolor='none', top='off', bottom='off', left='off', right='off')
#     big_ax.set_ylabel('-- CCR -->', fontsize=20)        
#     big_ax.set_xlabel('NoC_size', fontsize=20)
#     big_ax.xaxis.labelpad = 20
#     big_ax.yaxis.labelpad = 20
#     big_ax.patch.set_visible(False)
#     
    
    
    
    
def plot_AnalyticalGOPWCRT(use_sched_test_results=False, load_from_file=False):
    
    all_exp_results = OrderedDict()
    out_fname = os.path.splitext("path_to_file")[0] + "_plot_AnalyticalGOPWCRT.js"
    
    if (load_from_file == False):
        
        try :
            ## FOR EACH_SEED
            for each_seed in RANDOM_SEED_LIST:
                print each_seed
                # get the ccr values from file
                fname = '../util_scripts/ccr_list_allwfs_output_0.001_2.0_s'+ str(each_seed) + '.js'    
                json_data=open(fname)
                file_data = json.load(json_data) 
                seed_specific_data = file_data[str(each_seed)]        
                subdir1 = "seed_"+str(each_seed)+"/"
                
                # sort
                sorted_wf_sizes = sorted(seed_specific_data.keys())
                sorted_seed_specific_data = OrderedDict()
                for each_k in sorted_wf_sizes:
                    sorted_seed_specific_data[each_k] = seed_specific_data[each_k]
                
                
                ## FOR EACH_NOCSIZE
                offset = 0
                for each_wf_k, each_wf_v in sorted_seed_specific_data.iteritems():                
                    noc_h = int(np.sqrt(int(each_wf_k)-offset))  
                    #if noc_h not in [9]:
                    #    continue          
                    subdir2 = subdir1 + "noc_h" + str(noc_h) + "/"
                    wf_nums = int(each_wf_k)        
                    sorted_ccr_entries = sorted(each_wf_v["ccr_list"].values(), reverse=True)
                    #print noc_h
                    if(noc_h not in all_exp_results):
                        all_exp_results[noc_h] = OrderedDict()
                                
                    ## FOR EACH_CCR
                    # get ccr specific results
                    for each_ccr_entry in sorted_ccr_entries:
                        ccr = round(each_ccr_entry['ccr'], 4)                
                        subdir3 = subdir2 + "ccr_" + str(ccr) + "/"
                        #rounded_ccr = round(ccr, 3)
                        rounded_ccr = _get_closest_ccr_from_ccr_list(ccr)
                        #print rounded_ccr
                        if(rounded_ccr not in all_exp_results[noc_h]):
                            all_exp_results[noc_h][rounded_ccr] = OrderedDict()
                        
                        ## FOR EACH_MPTYPE
                        for each_mp_type in global_types_of_tests:  
                            #print each_mp_type
                            mp_type_lbl = each_mp_type['lbl']
                            
                            # get data            
                            final_fname_prefix = "HRTVid_" + \
                                         "AC"+ str(each_mp_type['ac']) + "_" + \
                                         "MP"+ str(each_mp_type['mp']) + "_" + \
                                         "PR"+ str(each_mp_type['pr']) + "_" + \
                                         "CMB"+ str(each_mp_type['cmb']) + "_"
                            
                            FNAME_PREFIX = final_fname_prefix+str(noc_h)+"_"+str(noc_h)+"_"                        
                            fname = EXP_DATA_DIR+subdir3+FNAME_PREFIX + "test__schedtestresults.js" 
                            print fname   
                            json_data=open(fname)
                            data = json.load(json_data)
                            strm_wcrt = [x[1] for x in data[-1]["current_stream_cp_wcet"]]                                
                            
                            if(mp_type_lbl not in all_exp_results[noc_h][rounded_ccr]):
                                all_exp_results[noc_h][rounded_ccr][mp_type_lbl] = strm_wcrt
                            else:
                                all_exp_results[noc_h][rounded_ccr][mp_type_lbl].extend(strm_wcrt)
        
        except:
            pprint.pprint(sys.exc_info())
            print traceback.format_exc()
            
       
        _write_formatted_file(out_fname, all_exp_results, "json")
        
    else:         
        json_data=open(out_fname)
        all_exp_results = json.load(json_data)      
        
    
    
        
    
    ### plot results
    mapping_heuristic_sort_order = ['IPC', 'LWCRS', 'PP', 'BN', 'LU', 'LM']
    num_noc_sizes = len(all_exp_results.keys())
    num_ccr_vals = len( all_exp_results[all_exp_results.keys()[0]].keys() )
    num_mappers = len( global_types_of_tests )
    
#     print num_mappers
#     print num_noc_sizes
#     print num_ccr_vals    
#     print all_exp_results[all_exp_results.keys()[0]].keys()

    # find global min,max
    (overall_min, overall_max) = _get_global_minmax(all_exp_results)
         
    f, axarr = plt.subplots(num_ccr_vals, num_noc_sizes, sharex=True, sharey=False)
    f.canvas.set_window_title('plot_AnalyticalGOPWCRT')    
    ix_i = 0
    ix_j = 0
    pprint.pprint(len(axarr))
    #sys.exit()
    for each_noc_h_k  in sorted(all_exp_results.keys()):
        each_noc_h_v = all_exp_results[each_noc_h_k]
        ix_i = 0
        for each_ccr_k  in sorted(each_noc_h_v.keys(), reverse=True):
            
            each_ccr_v = each_noc_h_v[each_ccr_k]
            
            # sort according to the mapping list
            sorted_each_ccr_v = OrderedDict()
            for k in mapping_heuristic_sort_order:
                sorted_each_ccr_v[k] = each_ccr_v[k]
            
            print each_noc_h_k, each_ccr_k
            
            boxplot_data = [gop_data for map_lbl, gop_data in sorted_each_ccr_v.iteritems()]
            norm_boxplot_data = _long_normalise_boxplot_data(boxplot_data, 
                                                             min_of_data=overall_min,
                                                             max_of_data=overall_max)
            
            norm_boxplot_data = boxplot_data
            
            boxplot_labels = [map_lbl for map_lbl, gop_data in sorted_each_ccr_v.iteritems()]
            boxplot_means = [np.mean(gop_data) for gop_data in norm_boxplot_data]
            #boxplot_max = [np.max(gop_data) for map_lbl, gop_data in each_ccr_v.iteritems()]
            
            # plot a group of boxplots for each scenario
            width=0.7
            ind = np.arange(num_mappers)
            pos_0 = ind
            
            bp=axarr[ix_i, ix_j].boxplot(norm_boxplot_data,0,'x',positions=pos_0, widths=width, patch_artist=True)
            boxplot_colorize(bp)
            axarr[ix_i, ix_j].plot(ind, boxplot_means, marker='o', color='darkorange', linewidth=1)
                        
            #bp = axarr[ix_i].boxplot(norm_boxplot_data,0,positions=pos_0, widths=width)            
            #axarr[ix_i].plot(ind, boxplot_means, marker='d', color='g', linewidth=0.3)
            #axarr[ix_i, ix_j].plot(ind, boxplot_max, marker='x', color='r', linewidth=0.3)
            
            labels = boxplot_labels
            xticks = range(0,(len(labels)))
            xticks = [x for x in xticks]    
            axarr[ix_i, ix_j].set_xticks(xticks)
            #axarr[ix_i, ix_j].set_xticklabels(labels, rotation='vertical')
            axarr[ix_i, ix_j].set_xticklabels(labels, rotation=35)
            #axarr[ix_i, ix_j].set_title(str(each_noc_h_k)+"x"+str(each_noc_h_k)+","+str(each_ccr_k))
            axarr[ix_i, ix_j].grid(True)
            
            if(ix_i == len(all_exp_results.keys())):
                axarr[ix_i, ix_j].set_xlabel("\nNoC_size="+str(each_noc_h_k)+"x"+str(each_noc_h_k))
                
            if(ix_j == 0):
                axarr[ix_i, ix_j].set_ylabel("$CCR_{WL}="+str(each_ccr_k)+"$\n\n$WCRT(J_i^{CP})$",multialignment='center')

            axarr[ix_i, ix_j].tick_params(axis='both', which='both', labelsize=14)
            
            # hide the yaxis ticks
            if(ix_j!=0):
                axarr[ix_i, ix_j].get_yaxis().set_ticklabels([])
            
            # set the axis limits - normalised
#             if(float(each_ccr_k) == 0.001): axarr[ix_i, ix_j].set_ylim([-0.01,0.1])
#             elif(float(each_ccr_k) == 0.501): axarr[ix_i, ix_j].set_ylim([0,0.25])
#             elif(float(each_ccr_k) == 1.0): axarr[ix_i, ix_j].set_ylim([0,0.6])
#             elif(float(each_ccr_k) == 1.5): axarr[ix_i, ix_j].set_ylim([0,0.81])
#             elif(float(each_ccr_k) == 2.0): axarr[ix_i, ix_j].set_ylim([0,1.1])
            
            # set the axis limits - raw
            if(float(each_ccr_k) == 0.001): axarr[ix_i, ix_j].set_ylim([-0.01,3.0])
            elif(float(each_ccr_k) == 0.501): axarr[ix_i, ix_j].set_ylim([0,8.0])
            elif(float(each_ccr_k) == 1.0): axarr[ix_i, ix_j].set_ylim([0,16.0])
            elif(float(each_ccr_k) == 1.5): axarr[ix_i, ix_j].set_ylim([0,25.0])
            elif(float(each_ccr_k) == 2.0): axarr[ix_i, ix_j].set_ylim([0,35.0])
            
#             

#             axarr[ix_i].set_xticks(xticks)
#             axarr[ix_i].set_xticklabels(labels)
#             axarr[ix_i].set_title(str(each_noc_h_k)+"x"+str(each_noc_h_k)+","+str(each_ccr_k))
#             axarr[ix_i].grid(True)
                        
            ix_i += 1
        ix_j += 1    
            
        
    plt.rc('font', **{'size':'16'})
    #plt.rcParams['mathtext.default'] = 'regular'
       










   
def plot_AnalyticalGOPWCRT_TEST(use_sched_test_results=False, load_from_file=False):
    
    all_exp_results = OrderedDict()
    out_fname = os.path.splitext("path_to_file")[0] + "_plot_AnalyticalGOPWCRT_TEST.js"
    
    if (load_from_file == False):
        
        try :
            ## FOR EACH_SEED
            for each_seed in RANDOM_SEED_LIST:
                print each_seed
                # get the ccr values from file
                #fname = '../util_scripts/ccr_list_allwfs_output_0.001_2.0_s'+ str(each_seed) + '.js'
                fname =  '../util_scripts/ccr_list_with_bl_corrrection/ccr_list_allwfs_output_0.001_2.0_s'+ str(each_seed) + '.js'
                   
                json_data=open(fname)
                file_data = json.load(json_data) 
                seed_specific_data = file_data[str(each_seed)]        
                subdir1 = "seed_"+str(each_seed)+"/"
                
                # sort
                sorted_wf_sizes = sorted(seed_specific_data.keys())
                sorted_seed_specific_data = OrderedDict()
                for each_k in sorted_wf_sizes:
                    sorted_seed_specific_data[each_k] = seed_specific_data[each_k]
                
                
                print sorted_seed_specific_data.keys()
                
                ## FOR EACH_NOCSIZE
                offset = 0
                #for each_wf_k, each_wf_v in sorted_seed_specific_data.iteritems():
                noc_sizes = ['9','25', '49', '81']
                for each_wf_k in noc_sizes:  
                                       
                    each_wf_v = sorted_seed_specific_data[each_wf_k]
                    noc_h = int(np.sqrt(int(each_wf_k)-offset))  
                    #if noc_h not in [9]:
                    #    continue          
                    subdir2 = subdir1 + "noc_h" + str(noc_h) + "/"
                    wf_nums = int(each_wf_k)        
                    sorted_ccr_entries = sorted(each_wf_v["ccr_list"].values(), reverse=True)
                    
                    print "--->"
                    print sorted_ccr_entries
                    
                    #print noc_h
                    if(noc_h not in all_exp_results):
                        all_exp_results[noc_h] = OrderedDict()
                                
                    ## FOR EACH_CCR
                    # get ccr specific results
                    for each_ccr_entry in sorted_ccr_entries:
                        ccr = round(each_ccr_entry['ccr'], 4)      
                        
                        print "CCr:" + str(ccr)
                        
                        #if (ccr > 1.5) or (ccr < 1.1): continue
                        #if (ccr > 1.5) or (ccr < 1.1): continue
                                  
                        subdir3 = subdir2 + "ccr_" + str(ccr) + "/"
                        #rounded_ccr = round(ccr, 3)
                        rounded_ccr = _get_closest_ccr_from_ccr_list(ccr)
                        #print rounded_ccr
                        if(rounded_ccr not in all_exp_results[noc_h]):
                            all_exp_results[noc_h][rounded_ccr] = OrderedDict()
                        
                        ## FOR EACH_MPTYPE
                        for each_mp_type in global_types_of_tests:  
                            #print each_mp_type
                            mp_type_lbl = each_mp_type['lbl']
                            
                            # get data            
                            final_fname_prefix = "HRTVid_" + \
                                         "AC"+ str(each_mp_type['ac']) + "_" + \
                                         "MP"+ str(each_mp_type['mp']) + "_" + \
                                         "PR"+ str(each_mp_type['pr']) + "_" + \
                                         "CMB"+ str(each_mp_type['cmb']) + "_"
                            
                            FNAME_PREFIX = final_fname_prefix+str(noc_h)+"_"+str(noc_h)+"_"                        
                            fname = EXP_DATA_DIR+subdir3+FNAME_PREFIX + "test__schedtestresults.js" 
                            print fname   
                            json_data=open(fname)
                            data = json.load(json_data)
                            strm_wcrt = [x[1] for x in data[-1]["current_stream_cp_wcet"]]                                
                            
                            if(mp_type_lbl not in all_exp_results[noc_h][rounded_ccr]):
                                all_exp_results[noc_h][rounded_ccr][mp_type_lbl] = strm_wcrt
                            else:
                                all_exp_results[noc_h][rounded_ccr][mp_type_lbl].extend(strm_wcrt)
        
        except:
            pprint.pprint(sys.exc_info())
            print traceback.format_exc()
            sys.exit()
       
        _write_formatted_file(out_fname, all_exp_results, "json")
        
    else:         
        json_data=open(out_fname)
        all_exp_results = json.load(json_data)      
        
    
    
    ### plot results
    mapping_heuristic_sort_order = ['IPC', 'LWCRS', 'PP', 'BN', 'LU', 'LM']
    
    #mapping_heuristic_sort_order = ['IPC', 'LWCRS', 'PP', 'BN']
    
    num_noc_sizes = len(all_exp_results.keys())
    num_ccr_vals = len( all_exp_results[all_exp_results.keys()[0]].keys() )
    num_mappers = len( global_types_of_tests )

    print "------+++="    
    print num_mappers
    print num_noc_sizes
    print num_ccr_vals    
    print all_exp_results[all_exp_results.keys()[0]].keys()
    print "------+++="

    # find global min,max
    (overall_min, overall_max) = _get_global_minmax(all_exp_results)
         
    f, axarr = plt.subplots(num_ccr_vals, num_noc_sizes, sharex=True, sharey=False)
    f.canvas.set_window_title('plot_AnalyticalGOPWCRT')    
    ix_i = 0
    ix_j = 0
    pprint.pprint(len(axarr))
    #sys.exit()
    for each_noc_h_k  in sorted(all_exp_results.keys()):
        each_noc_h_v = all_exp_results[each_noc_h_k]
        ix_i = 0
        for each_ccr_k  in sorted(each_noc_h_v.keys(), reverse=True):
            
            each_ccr_v = each_noc_h_v[each_ccr_k]
            
            # sort according to the mapping list
            sorted_each_ccr_v = OrderedDict()
            for k in mapping_heuristic_sort_order:
                sorted_each_ccr_v[k] = each_ccr_v[k]
            
            print each_noc_h_k, each_ccr_k
            
            boxplot_data = [gop_data for map_lbl, gop_data in sorted_each_ccr_v.iteritems()]
            norm_boxplot_data = _long_normalise_boxplot_data(boxplot_data, 
                                                             min_of_data=overall_min,
                                                             max_of_data=overall_max)
            
            norm_boxplot_data = boxplot_data
            
            boxplot_labels = [map_lbl for map_lbl, gop_data in sorted_each_ccr_v.iteritems()]
            boxplot_means = [np.mean(gop_data) for gop_data in norm_boxplot_data]
            #boxplot_max = [np.max(gop_data) for map_lbl, gop_data in each_ccr_v.iteritems()]
            
            # plot a group of boxplots for each scenario
            width=0.7
            ind = np.arange(num_mappers)
            pos_0 = ind
            
            #print "------0"
            #print len(axarr[0])
            
            bp=axarr[ix_i, ix_j].boxplot(norm_boxplot_data,0,'x',positions=pos_0, widths=width, patch_artist=True)
            boxplot_colorize(bp)
            axarr[ix_i, ix_j].plot(ind, boxplot_means, marker='o', color='darkorange', linewidth=1)
                        
            #bp = axarr[ix_i].boxplot(norm_boxplot_data,0,positions=pos_0, widths=width)            
            #axarr[ix_i].plot(ind, boxplot_means, marker='d', color='g', linewidth=0.3)
            #axarr[ix_i, ix_j].plot(ind, boxplot_max, marker='x', color='r', linewidth=0.3)
            
            labels = boxplot_labels
            xticks = range(0,(len(labels)))
            xticks = [x for x in xticks]    
            axarr[ ix_i, ix_j].set_xticks(xticks)
            #axarr[ix_i, ix_j].set_xticklabels(labels, rotation='vertical')
            axarr[ix_i, ix_j].set_xticklabels(labels, rotation=35)
            #axarr[ix_i, ix_j].set_title(str(each_noc_h_k)+"x"+str(each_noc_h_k)+","+str(each_ccr_k))
            axarr[ix_i, ix_j].grid(True)
            
            if(ix_i == len(all_exp_results.keys())):
                axarr[ix_i, ix_j].set_xlabel("\nNoC_size="+str(each_noc_h_k)+"x"+str(each_noc_h_k))
                
            if(ix_j == 0):
                axarr[ix_i, ix_j].set_ylabel("$CCR_{WL}="+str(each_ccr_k)+"$\n\n$WCRT(J_i^{CP})$",multialignment='center')

            axarr[ ix_i, ix_j].tick_params(axis='both', which='both', labelsize=14)
            
            # hide the yaxis ticks
            if(ix_j!=0):
                axarr[ ix_i, ix_j].get_yaxis().set_ticklabels([])
            
            # set the axis limits - normalised
#             if(float(each_ccr_k) == 0.001): axarr[ix_i, ix_j].set_ylim([-0.01,0.1])
#             elif(float(each_ccr_k) == 0.501): axarr[ix_i, ix_j].set_ylim([0,0.25])
#             elif(float(each_ccr_k) == 1.0): axarr[ix_i, ix_j].set_ylim([0,0.6])
#             elif(float(each_ccr_k) == 1.5): axarr[ix_i, ix_j].set_ylim([0,0.81])
#             elif(float(each_ccr_k) == 2.0): axarr[ix_i, ix_j].set_ylim([0,1.1])
            
            # set the axis limits - raw
            if(float(each_ccr_k) == 0.001): axarr[ix_i, ix_j].set_ylim([-0.01,3.0])
            elif(float(each_ccr_k) == 0.501): axarr[ix_i, ix_j].set_ylim([0,8.0])
            elif(float(each_ccr_k) == 1.0): axarr[ix_i, ix_j].set_ylim([0,16.0])
            elif(float(each_ccr_k) == 1.5): axarr[ix_i, ix_j].set_ylim([0,25.0])
            elif(float(each_ccr_k) == 2.0): axarr[ix_i, ix_j].set_ylim([0,35.0])
             
#             

#             axarr[ix_i].set_xticks(xticks)
#             axarr[ix_i].set_xticklabels(labels)
#             axarr[ix_i].set_title(str(each_noc_h_k)+"x"+str(each_noc_h_k)+","+str(each_ccr_k))
#             axarr[ix_i].grid(True)
                        
            ix_i += 1
        ix_j += 1    
            
        
    plt.rc('font', **{'size':'16'})
    #plt.rcParams['mathtext.default'] = 'regular'















###################################
#    HELPERS
###################################

def boxplot_colorize(bp, fc='#B8DCE6',
                     mapping_type_colors = GLOBAL_COLS 
                     #mapping_type_colors = plt.get_cmap('Blues')(np.linspace(0, 1.0, 7))
                     ):
    
    i=0
    ## change outline color, fill color and linewidth of the boxes
    for box in bp['boxes']:
        c = GLOBAL_COLS[MP_ORDER[i]]
        # change outline color
        box.set( color='#000000', linewidth=1)        
        # change fill color
        #box.set( facecolor =  mapping_type_colors[i])
        box.set( facecolor =  c)
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
        flier.set(marker='x', color='k', alpha=0.7)
        
        
        
    
def _get_closest_ccr_from_ccr_list(param_ccr):
    ccr_list = [round(x,3) for x in np.linspace(0.001, 2.0, 5)]
    closest_ccr = min(ccr_list, key=lambda x:abs(x-param_ccr))
     
    return closest_ccr

def _write_formatted_file(fname, data, format):        
    if(format == "pretty"):
        logfile=open(fname, 'w')
        pprint.pprint(data, logfile, width=128)
        
    elif(format == "json"):
        logfile=open(fname, 'w')
        json_data = json.dumps(data)
        logfile.write(json_data)
        
    else:
        logfile=open(fname, 'w')
        pprint.pprint(data, logfile, width=128)



def _long_normalise_boxplot_data(bp_data, min_of_data=None, max_of_data=None):
    if (min_of_data==None)and(max_of_data==None):
        norm_min = bp_data[0][0]
        norm_max = bp_data[0][0]
        for i in bp_data:
            for j in i:
                if j < norm_min: norm_min = j            
                if j > norm_max: norm_max = j
    else:
        norm_min=min_of_data
        norm_max=max_of_data
    
    norm_bp_data = []
    for i in bp_data:
        new_bp_data_col = []
        for j in i:
            new_val = (j-norm_min)/(norm_max-norm_min)
            new_bp_data_col.append(new_val)
        
        norm_bp_data.append(new_bp_data_col)
    
    return norm_bp_data
            


def _get_global_minmax(all_exp_data):
    global_min = 1000
    global_max = 0.0
    for each_noc_h_k, each_noc_h_v  in all_exp_data.iteritems():
        for each_ccr_k,each_ccr_v  in each_noc_h_v.iteritems():
            
            boxplot_data = [gop_data for map_lbl, gop_data in each_ccr_v.iteritems()]
            temp_min = np.amin(boxplot_data)
            temp_max = np.amax(boxplot_data)
            
            if temp_min < global_min: global_min = temp_min            
            if temp_max > global_max: global_max = temp_max
            
    return (global_min, global_max)
            
    
    


def _normalise_boxplot_data(bp_data):
    
    lens = [len(x) for x in bp_data]    
    if(_all_same(lens) == False):
        bp_data = _square_an_array(bp_data)
        print "error!!"
        print lens
    
    norm_min = np.amin(bp_data, axis=None)
    norm_max = np.amax(bp_data)
     
    arr_bp_data = np.array(bp_data)
    bp_data_normalised = (arr_bp_data-norm_min)/(norm_max-norm_min)
    
    #pprint.pprint(arr_bp_data[0])
    #pprint.pprint(bp_data_normalised[0])
    
    #sys.exit()
    
    print "----"
    
    return bp_data_normalised
    

def _square_an_array(lst):
    
    lst_lens = [len(x) for x in lst]
    max_len = np.max(lst_lens)
    
    for ix, each_row in enumerate(lst):
        each_row_len = len(each_row)
        if (len(each_row) < max_len):
            padding = [0.0]*(max_len-each_row_len)
            lst[ix].extend(padding)
    
    return lst
    
def _all_same(items):
    return all(x == items[0] for x in items)


def getWFCCinfo():
    
    noc_size = 3
    
    num_wfs = (noc_size*noc_size)+0
    
    ## FOR EACH_SEED
    for each_seed in RANDOM_SEED_LIST:
        #print each_seed
        # get the ccr values from file
        fname = 'Z:/MCASim/util_scripts/ccr_list_allwfs_output_0.001_2.0_s'+ str(each_seed) + '.js'    
        json_data=open(fname)
        file_data = json.load(json_data) 
        seed_specific_data = file_data[str(each_seed)]
        
        print get_cc_for_rescombo(seed_specific_data[str(num_wfs)]["res_list"]), len(seed_specific_data[str(num_wfs)]["res_list"])
        
        
def get_cc_for_rescombo(res_combo_list):
    cc = 0
    for each_res in res_combo_list:
        cc += each_res[0] * each_res[1]
    return cc

###################################
#    MAIN
###################################

#plot_AnalyticalGOPWCRT(load_from_file=True)
plot_AnalyticalGOPWCRT_TEST(load_from_file=False)
#plot_GoPResponseTime(use_sched_test_results=True, load_from_file=False)

#getWFCCinfo()


print "finished"

plt.show()

