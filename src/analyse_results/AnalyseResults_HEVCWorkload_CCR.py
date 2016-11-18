import sys, os, csv, pprint, math

#sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from collections import OrderedDict
import numpy as np
import traceback
import re
#import pylab
import matplotlib
matplotlib.use('Qt4Agg')
import matplotlib.pyplot as plt
#plt.style.use('bmh_rosh')


#import seaborn as sns
import seaborn.apionly as sns
import scipy.stats
import json
from matplotlib import colors
import matplotlib.cm as cm

import seaborn.apionly as sns
#sns.set_color_codes()


plt.style.use('bmh_rosh')
#from SimParams import SimParams


from util_scripts.resolution_combos import generate_resolution_combos
from libNoCModel.NoCFlow import NoCFlow

#EXP_DATADIR = "../experiment_data/workload_validation_fast/"
EXP_DATADIR = "Z:/MCASim/experiment_data/workload_validation_fast_cucc_scale_06/"
#EXP_DATADIR = "Z:/MCASim/experiment_data/workload_validation_fast_cucc_scale_06_01/"

RANDOM_SEEDS = [81665, 33749, 43894, 26358, 80505, 83660, 22817, 70263, 29917, 26044]
#RANDOM_SEEDS = [81665, 33749, 43894, 26358, 80505]


NOC_W = 8
NOC_H = 8
NOC_PERIOD = 0.00000001
NOC_ARBITRATION_COST = 7.0 * NOC_PERIOD

NUM_GOPS = 8
GOP_LEN = 31
NBMAX = 4
MOV_TYPE = "ANIM"
#MOV_TYPE = "DOC"



VID_RESOLUTION_LIST = [(3840,2160),(2560,1440), 
                       (1920,1080),(1280,720),
                       (854,480),(640,360),
                       (512,288),
                      ]

# VID_RESOLUTION_LIST = [(1280,720),                       
#                       ]

VID_RESOLUTION_LIST.reverse()


MOV_LIST = [ 'ACTION', 'DOC', 'SPORT', 'SPEECH', 'ANIM' ]
GOP_LEN_LIST = [16, 31]


def plot_Resolution_vs_CCR():
    
    all_realccr_per_gop = {} # keys are resolutions
    all_wc_ccr_per_vid = {} # keys are resolutions
    
    res_str_to_pixels_mapping = {}
    
    # get data per video res    
    for rix, each_vid_res in enumerate(VID_RESOLUTION_LIST):
        
        res_key_int =  each_vid_res[0] * each_vid_res[1] # num pixels
        res_key_str = str(each_vid_res[0]) + "x" + str(each_vid_res[1])
        
        res_str_to_pixels_mapping[res_key_str] = (res_key_int, rix+1)
                
        # data structs
        all_realccr_per_gop[res_key_str] = []
         
        Icc_list = []
        Pcc_list = []
        Bcc_list = []
        
        # get data per seed 
        for each_seed in RANDOM_SEEDS:
            
            res_str = str(each_vid_res[0]) + "x" + str(each_vid_res[1])
            fname_prefix = "__s%d_G%d_N%d_B%d_%s" % (each_seed, NUM_GOPS, GOP_LEN, NBMAX, MOV_TYPE)    
            fname = EXP_DATADIR + "vidworkload_data_res" + res_str + "_" + fname_prefix + ".js"
                
            json_data=open(fname)
            file_data = json.load(json_data)
   
            # record real-CCRs per gop
            real_ccrs = [g['real_ccr'] for g in file_data['gop_info']]
            all_realccr_per_gop[res_key_str].extend(real_ccrs)
            
            Icc_list.append(np.max(file_data['fr_cc_I']))
            Pcc_list.append(np.max(file_data['fr_cc_P']))
            Bcc_list.append(np.max(file_data['fr_cc_B']))
            
        Iwcc =  np.max(Icc_list)
        Pwcc =  np.max(Pcc_list)
        Bwcc =  np.max(Bcc_list)
        max_flw_payload = res_key_int * 3
        
        #sys.exit()
        print each_vid_res
        
        vid_min_ccr, vid_max_ccr = _get_minmax_ccr(Iwcc, Pwcc, Bwcc, GOP_LEN, max_flw_payload)
        vid_avg_ccr = np.mean([vid_min_ccr, vid_max_ccr])
        all_wc_ccr_per_vid[res_key_str] = [vid_min_ccr, vid_max_ccr, vid_avg_ccr]
    
        #print Iwcc, Pwcc, Bwcc , max_flw_payload
        #print vid_min_ccr, vid_max_ccr
        #sys.exit()    
       
       
    ## now we plot
    fig = plt.figure(figsize=(11,4))
    fig.canvas.set_window_title('Scatter - resolution vs. ccr (per gop)')    
        
    
    print VID_RESOLUTION_LIST
    xaxis_ticks_str = [str(s[0]) + "x" + str(s[1]) for s in VID_RESOLUTION_LIST]
    
    plt.xticks(range(1, len(xaxis_ticks_str)+1), xaxis_ticks_str)
    plt.xlim([0.5, len(xaxis_ticks_str)+0.5])
    # worst-case CCR #
    
    y_data_min_max =  []
    x_data_min_max = []
    y_data_avg = []
    x_data_avg = []
    for each_res_k, each_res_ccr_data in all_wc_ccr_per_vid.iteritems():
        x_data_min_max.extend( [res_str_to_pixels_mapping[each_res_k][1]] * 2)
        x_data_avg.extend([res_str_to_pixels_mapping[each_res_k][1]] * 1)        
        y_data_min_max.extend([each_res_ccr_data[0], each_res_ccr_data[1]])
        y_data_avg.extend([each_res_ccr_data[2]])
    
    plt.plot(x_data_min_max, y_data_min_max, marker='o', alpha=0.8, color='r', linestyle='', label='$CCR(J_i)$ (calculated lower/upper bound)')
    #plt.plot(x_data_avg, y_data_avg, marker='^', alpha=0.8, color='y', linestyle='', label='CCR (avg. of lower/upper bound)', zorder=10, markersize=10)
    
    plt.hold(True)
    
    
    # real-CCR #
    y_data =  []
    x_data = []
    for each_res_k, each_res_ccr_data in all_realccr_per_gop.iteritems():
        x_data.extend( [res_str_to_pixels_mapping[each_res_k][1]] * len(each_res_ccr_data))
        #x_data.extend([each_res_k] * len(each_res_ccr_data))
        y_data.extend(each_res_ccr_data)
    #plt.scatter(x_data, y_data, marker='x', alpha=0.8, color='b')
    plt.plot(x_data, y_data, marker='x', alpha=0.8, color='b', linestyle='', label='$aCCR(J_i)$ (synthetic workload)')
    
    plt.xlabel("Video stream resolution")
    plt.ylabel("Job CCR")
    
    leg = plt.legend(numpoints=1)
    leg.draggable()
    
    plt.grid(True)
        



def plot_Resolution_vs_CompCost():
    
    I_cc_dist = {}
    P_cc_dist = {}
    B_cc_dist = {}
    res_str_to_pixels_mapping = {}
    res_list_order = []
    for rix, each_vid_res in enumerate(VID_RESOLUTION_LIST):
        
        res_key_int =  each_vid_res[0] * each_vid_res[1] # num pixels
        res_key_str = str(each_vid_res[0]) + "x" + str(each_vid_res[1])
        res_list_order.append(res_key_str)
        res_str_to_pixels_mapping[res_key_str] = (res_key_int, rix+1)
        
        I_cc_dist[res_key_str] = []
        P_cc_dist[res_key_str] = []
        B_cc_dist[res_key_str] = []
              
        for each_seed in RANDOM_SEEDS:
            res_str = str(each_vid_res[0]) + "x" + str(each_vid_res[1])
            fname_prefix = "__s%d_G%d_N%d_B%d_%s" % (each_seed, NUM_GOPS, GOP_LEN, NBMAX, MOV_TYPE)    
            fname = EXP_DATADIR + "vidworkload_data_res" + res_str + "_" + fname_prefix + ".js"
                
            json_data=open(fname)
            file_data = json.load(json_data)
            
            I_cc_dist[res_key_str].extend(file_data['fr_cc_I'])
            P_cc_dist[res_key_str].extend(file_data['fr_cc_P'])
            B_cc_dist[res_key_str].extend(file_data['fr_cc_B'])
            
    ## plotting - comp cost ##
    
    fig1 = plt.figure(figsize=(11,4))
    fig1.canvas.set_window_title('boxplot - resolution vs. comp.cost')
    
    xaxis_ticks_str = [str(s[0]) + "x" + str(s[1]) for s in VID_RESOLUTION_LIST]
    plt.xticks(range(1, len(xaxis_ticks_str)+1), xaxis_ticks_str)
    plt.xlim([0.5, len(xaxis_ticks_str)+0.5])
    
    
    bp_data = [I_cc_dist[s] for s in res_list_order]
    
    plt.boxplot(bp_data, positions=range(1, len(xaxis_ticks_str)+1))   
    
    plt.xlabel("Video stream resolution")
    plt.ylabel("I-frame computation cost (s)")
    
    
    ## plotting - max.payload ##
    fig2 = plt.figure(figsize=(11,4))
    fig2.canvas.set_window_title('boxplot - plot_Resolution_vs_CompCost')
    
    data = [vid_res[0]*vid_res[1]*3 for vid_res in VID_RESOLUTION_LIST] # 3 bytes per pixel
    xaxis_ticks_str = [str(s[0]) + "x" + str(s[1]) for s in VID_RESOLUTION_LIST]
    plt.xticks(range(1, len(xaxis_ticks_str)+1), xaxis_ticks_str)
    plt.xlim([0.5, len(xaxis_ticks_str)+0.5])
    
    
    plt.plot(range(1, len(xaxis_ticks_str)+1), data, marker='d')
    
    plt.xlabel("Video stream resolution")
    plt.ylabel("Max. Reference frame payload")
    



def plot_CC_Dist_single_res():
    
    I_cc_dist = {}
    P_cc_dist = {}
    B_cc_dist = {}
    res_str_to_pixels_mapping = {}
    res_list_order = []
    res_key = None
    for rix, each_vid_res in enumerate(VID_RESOLUTION_LIST):
        
        res_key_int =  each_vid_res[0] * each_vid_res[1] # num pixels
        res_key_str = str(each_vid_res[0]) + "x" + str(each_vid_res[1])
        res_list_order.append(res_key_str)
        res_str_to_pixels_mapping[res_key_str] = (res_key_int, rix+1)
        
        res_key = res_key_str
        
        I_cc_dist[res_key_str] = []
        P_cc_dist[res_key_str] = []
        B_cc_dist[res_key_str] = []
              
        for each_seed in RANDOM_SEEDS:
            res_str = str(each_vid_res[0]) + "x" + str(each_vid_res[1])
            fname_prefix = "__s%d_G%d_N%d_B%d_%s" % (each_seed, NUM_GOPS, GOP_LEN, NBMAX, MOV_TYPE)    
            fname = EXP_DATADIR + "vidworkload_data_res" + res_str + "_" + fname_prefix + ".js"
                
            json_data=open(fname)
            file_data = json.load(json_data)
            
            I_cc_dist[res_key_str].extend(file_data['fr_cc_I'])
            P_cc_dist[res_key_str].extend(file_data['fr_cc_P'])
            B_cc_dist[res_key_str].extend(file_data['fr_cc_B'])
            
    ## plotting - comp cost ##
    
    fig1 = plt.figure(figsize=(11,4))
    fig1.canvas.set_window_title('boxplot - resolution vs. comp.cost')
    
    bp_data_I = I_cc_dist[res_key]
    bp_data_P = P_cc_dist[res_key]
    bp_data_B = B_cc_dist[res_key]
    
    #plt.boxplot(bp_data, positions=range(1, len(xaxis_ticks_str)+1))
    plt.hist(bp_data_I, color='r', histtype='step', normed=1)
    plt.hold(True)   
    plt.hist(bp_data_P, color='g', histtype='step', normed=1)
    plt.hold(True)   
    plt.hist(bp_data_B, color='b', histtype='step', normed=1)
    plt.hold(True)   
    
    plt.xlabel("comp_cost (s)")
    plt.ylabel("freq")
    
    



def plot_CCR_boxplots_various_range_of_workloads():
    
    all_realccr_per_gop = {} # keys are resolutions
    all_wc_ccr_per_vid = {} # keys are resolutions
    
    res_str_to_pixels_mapping = {}
    res_list = []
    all_vid_info = OrderedDict()
    x_ticks_labels = []
    # get data per video res
    for each_vid_res in VID_RESOLUTION_LIST:  
        res_key_int =  each_vid_res[0] * each_vid_res[1] # num pixels
        res_key_str = str(each_vid_res[0]) + "x" + str(each_vid_res[1])
        res_list.append(res_key_str)
        all_vid_info[res_key_str] = OrderedDict()
              
        for each_gop_len in GOP_LEN_LIST:
            for each_mov_type in MOV_LIST:
                vid_key = "%s_N%d" % (each_mov_type, each_gop_len)
                
                
                for each_seed in RANDOM_SEEDS:
        
                    res_str_to_pixels_mapping[res_key_str] = res_key_int
                    
                    fname_prefix = "__s%d_G%d_N%d_B%d_%s" % (each_seed, NUM_GOPS, each_gop_len, NBMAX, each_mov_type)
                    fname = EXP_DATADIR + "vidworkload_data_res" + res_key_str + "_" + fname_prefix + ".js"
                    print fname
                    
                    json_data=open(fname)
                    file_data = json.load(json_data)
                    
                    # specific data from file - cc's and realccrs
                    real_ccrs = [g['real_ccr'] for g in file_data['gop_info']]
                    
                    ref_data_payloads = file_data['fr_ref_data_payloads']
                    
                    runtime_ccrs = [
                                    _get_runtime_ccr(file_data['wc_comp_cost_I'], 
                                                     file_data['wc_comp_cost_P'], 
                                                     file_data['wc_comp_cost_B'], 
                                                     each_vid_res[0] * each_vid_res[1] * 3, 
                                                     g['num_edges'], 
                                                     g['gop_sequence']
                                                     )
                                    for g in file_data['gop_info']
                                    ]
                    
                    
                    if vid_key not in all_vid_info[res_key_str]:
                        all_vid_info[res_key_str][vid_key] = {
                                                 'real_ccr': real_ccrs,
                                                 'runtime_ccr': runtime_ccrs,
                                                 'Icc':  file_data['fr_cc_I'],
                                                 'Pcc':  file_data['fr_cc_P'],
                                                 'Bcc':  file_data['fr_cc_B'],  
                                                 'num_edges':  [g['num_edges'] for g in file_data["gop_info"]],
                                                 'numB':  [g['numB'] for g in file_data["gop_info"]],
                                                 'numP':  [g['numP'] for g in file_data["gop_info"]],
                                                 'lb_ccr': None,
                                                 'ub_ccr': None,
                                                 'avg_ccr' : None,
                                                 'fr_ref_data_payloads': ref_data_payloads
                                                 }
                    else:                        
                        all_vid_info[res_key_str][vid_key]['real_ccr'].extend(real_ccrs)
                        all_vid_info[res_key_str][vid_key]['runtime_ccr'].extend(runtime_ccrs)
                        all_vid_info[res_key_str][vid_key]['Icc'].extend(file_data['fr_cc_I'])
                        all_vid_info[res_key_str][vid_key]['Pcc'].extend(file_data['fr_cc_P'])
                        all_vid_info[res_key_str][vid_key]['Bcc'].extend(file_data['fr_cc_B'])
                        
                        all_vid_info[res_key_str][vid_key]['num_edges'].extend([g['num_edges'] for g in file_data["gop_info"]])
                        all_vid_info[res_key_str][vid_key]['numB'].extend([g['numB'] for g in file_data["gop_info"]])
                        all_vid_info[res_key_str][vid_key]['numP'].extend([g['numP'] for g in file_data["gop_info"]])
                        
                        all_vid_info[res_key_str][vid_key]['fr_ref_data_payloads'].extend(ref_data_payloads)
                        
                        
                        
                        
                # calculate and populate min/max ccrs
                #res_key_str = str(each_vid_res[0]) + "x" + str(each_vid_res[1])
                #vid_key = "%s_G%d_N%d_B%d_%s" % (res_key_str, NUM_GOPS, each_gop_len, NBMAX, each_mov_type)
                
                Iwcc = np.max(all_vid_info[res_key_str][vid_key]['Icc'])
                Pwcc = np.max(all_vid_info[res_key_str][vid_key]['Pcc'])
                Bwcc = np.max(all_vid_info[res_key_str][vid_key]['Bcc'])
                
                Ibcc = np.min(all_vid_info[res_key_str][vid_key]['Icc'])
                Pbcc = np.min(all_vid_info[res_key_str][vid_key]['Pcc'])
                Bbcc = np.min(all_vid_info[res_key_str][vid_key]['Bcc'])
                
                max_flw_payload = each_vid_res[0] * each_vid_res[1] * 3
                vid_min_ccr, vid_max_ccr = _get_minmax_ccr(Iwcc, Pwcc, Bwcc,
                                                           Ibcc,Pbcc, Bbcc,
                                                           each_gop_len, max_flw_payload)
                vid_avg_ccr = np.mean([vid_min_ccr, vid_max_ccr])
                
                all_vid_info[res_key_str][vid_key]['lb_ccr'] = vid_min_ccr
                all_vid_info[res_key_str][vid_key]['ub_ccr'] = vid_max_ccr
                all_vid_info[res_key_str][vid_key]['avg_ccr'] = vid_avg_ccr
                
#                 x_ticks_labels.append(
#                                "%s_N%d_%s" % (res_key_str, each_gop_len, each_mov_type)
#                                )
                
    ## now we plot
    fig, axes = plt.subplots(ncols=len(res_list), sharey=True)
    fig.subplots_adjust(wspace=0)    
    
    
    #plt.xticks(ind, x_ticks_labels)
    i=0
    for ax, res in zip(axes,  res_list):
        
        all_k = [k for k in all_vid_info[res].keys() if "N16" not in k]        
        #all_k = [k for k in all_vid_info[res].keys()]
        bp_data = [all_vid_info[res][k]['Bcc'] for k in all_k if "N16" not in k]
        #bp_data = [all_vid_info[res][k]['runtime_ccr'] for k in all_k]
        data_lb_ccr  = [all_vid_info[res][k]['lb_ccr'] for k in all_k]
        data_ub_ccr  = [all_vid_info[res][k]['ub_ccr'] for k in all_k]
        data_avgb_ccr = [ (all_vid_info[res][k]['ub_ccr']+all_vid_info[res][k]['lb_ccr'])/2.0 for k in all_k]
        
        ind = range(1, len(bp_data)+1)
        
        bps = ax.boxplot(bp_data, positions = ind, sym='x', showmeans=False, patch_artist=True)
        _stylize_boxplots(bps)
        #ax.set(xticklabels=all_k, xlabel=res)
        ax.set_xticks(ind)
        ax.set_xticklabels(all_k, fontsize=10, rotation=40, ha='right')
        ax.set_xlabel(res)
        #ax.tick_params(axis='both', which='major', labelsize=9)
        ax.margins(0.05) # Optional
        
        # plot min/max ccr
#         ax.hold(True)
#         ax.plot(ind, data_lb_ccr, color='g', marker='d', linewidth=0.5, markersize=6)
#         ax.hold(True)
#         ax.plot(ind, data_ub_ccr, color='g', marker='d', linewidth=0.5, markersize=6, label="$CCR(J_i)$ (calculated lower/upper bound)")
        #ax.hold(True)
        #ax.plot(ind, data_avgb_ccr, color='g', marker='d', linewidth=0.5, markersize=5)
        
        ax.grid(True, axis='y')
        ax.grid(False, axis='x')
        
        if i!=0:
            ax.yaxis.tick_left()                        
            ax.yaxis.set_ticks_position('none')
        else:
            ax.yaxis.set_ticks_position('left')
        
        # top axis ticks
        #ax2 = ax.twin()
        #ax2.set_xticks(ind)
        
        
    #plt.xlabel("Synthetic video profile")
        i+=1
    
    
    #axes[0].set_ylabel("Job CCR")
    axes[0].set_ylabel("Number of edges in a GoP")
    
    
        
    #plt.xticks(ind, x_ticks_labels, rotation=40, ha='right', fontsize=9)
    #p1 = plt.Line2D((0,1),(0,0), linestyle='-', color='y', marker='d')
    #l = fig.legend(p1, "$CCR(J_i)$ (calculated lower/upper bound)", loc='top center', ncol=1, numpoints=2,labelspacing=1)
    #l = plt.legend()
    #l.draggable()
    #l.get_frame().set_facecolor('#FFFFFF')
    #l.get_frame().set_linewidth(0.0)
    
    
    
#     v_l_locs = range(1,len(x_ticks_labels)+1, 10)[1:]    
#     for i in v_l_locs:
#         plt.axvline(x=i, linewidth=0.5, color='k', alpha=0.6)
#         plt.hold(True)
















       

###################################
#    HELPERS
###################################

def _get_runtime_ccr(Iwcc, Pwcc, Bwcc, max_payload, num_edges, gop_seq):
    
    total_node_cost = 0.0
    for ft_type in gop_seq:
        
        if ft_type == "I": total_node_cost+= Iwcc
        elif ft_type == "P": total_node_cost+= Pwcc
        elif ft_type == "B": total_node_cost+= Bwcc
        else:
            sys.exit("Error - _get_runtime_ccr")
    
    nhops = (NOC_H-1) + (NOC_W-1)
    max_bl = NoCFlow.getCommunicationCost(max_payload, nhops, NOC_PERIOD, NOC_ARBITRATION_COST)
    
    total_edges_cost = max_bl * float(num_edges)
    
    runtime_ccr = float(total_edges_cost)/float(total_node_cost)
    return runtime_ccr
    

def _get_minmax_ccr(Iwcc, Pwcc, Bwcc, Ibcc, Pbcc, Bbcc,
                    gop_len, max_payload):
    
    nPmax = gop_len -1
    nPmin = int(float(gop_len-1)/float(NBMAX + 1))
    
    nBmax = (gop_len - 1) - nPmin
    nBmin = 0
    nhops = (NOC_H-1) + (NOC_W-1)
    #nhops = (NOC_H) + (NOC_W)
    max_bl = NoCFlow.getCommunicationCost(max_payload*0.45, nhops, NOC_PERIOD, NOC_ARBITRATION_COST)
    
#     print "Iwcc, %.9f" % Iwcc
#     print "Pwcc, %.9f" % Pwcc
#     print "Bwcc, %.9f" % Bwcc
        
    print "max_bl: ", max_bl   
    
    ## calculate upper-bound CCR ##
    
    # how many num P's and B's do we consider ?    
    nP =  nPmin
    nB =  nBmax
    
    # upper ccr occurs when there are as many as possible edges, when there are max amount of B-frames
    # B frames can have max 3 incoming edges
    # P frames can have only 1 incoming edge
    # and have to take best-case ccs
    
    num_edges = (nP * 1) + (nB * 3)    
    print "w.c. num_edges:", num_edges
    wc_comm_cost = num_edges * max_bl
    
    bc_comp_cost = Ibcc + (nP * Pbcc) + (nB * Bbcc)    
    ub_ccr =  float(wc_comm_cost)/float(bc_comp_cost)
    
    
    ## calculate best-case CCR ##
    # how many num P's and B's do we consider ?    
    nP =  nPmax
    nB =  nBmin
    
    # bc ccr occurs when there are as less as possible edges, when there are min amount of B-frames
    # B frames can have max 3 incoming edges
    # P frames can have only 1 incoming edge
    
    num_edges = (nP * 1) + (nB * 2)
    print "b.c. num_edges:", num_edges
    bl = max_bl
    #print bl
    bc_comm_cost = float(num_edges) * bl
    
    wc_comp_cost = Iwcc + (nP * Pwcc) + (nB * Bwcc)    
    
    
    #print bc_comm_cost, bc_comp_cost
    
    lb_ccr =  float(bc_comm_cost)/float(wc_comp_cost)
    
    
    return (lb_ccr, ub_ccr)
            
def _stylize_boxplots(bp, c_boxface='#348ABD', c_boxline='k', 
                            c_cap='k', c_wh='k', c_fly='k'):
    # stylise boxplots
    for box, medians in zip(bp['boxes'], bp['medians']):            
            plt.setp(box, color='k', linewidth=1.00)
            plt.setp(box, facecolor=c_boxface, alpha=0.5)
            plt.setp(medians,linewidth=1.00, color=c_boxline)        
    for caps in bp['caps']:            
        plt.setp(caps, linewidth=1.00, color=c_cap)    
    for whiskers in bp['whiskers']:            
        plt.setp(whiskers, linewidth=1.00, color=c_wh, linestyle='-')    
    for fliers in bp['fliers']:            
        plt.setp(fliers, linewidth=1.00, color=c_fly)

###################################
#    MAIN
###################################



#plot_Resolution_vs_CCR()

#plot_Resolution_vs_CompCost()

plot_CCR_boxplots_various_range_of_workloads()


#plot_CC_Dist_single_res()

print "finished"

plt.show()



