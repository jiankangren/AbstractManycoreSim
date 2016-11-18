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


EXP_DATADIR = "Z:/MCASim/experiment_data/workload_validation_mpeg2/"


RANDOM_SEEDS = [81665, 33749, 43894, 26358, 80505, 83660, 22817, 70263, 29917, 26044]



NOC_W = 8
NOC_H = 8
NOC_PERIOD = 0.00000001
NOC_ARBITRATION_COST = 7.0 * NOC_PERIOD

NUM_GOPS = 8
GOP_LEN = 26
NBMAX = 4



VID_RESOLUTION_LIST = [(720,576), (544,576), (528,576), (480,576), (426,240), (320,240), (240,180)]
VID_RESOLUTION_LIST.reverse()


def plot_Resolution_vs_CCR():
    
    all_wc_ccr_per_vid = {} # keys are resolutions
    
    res_str_to_pixels_mapping = {}
    
    # get data per video res    
    for rix, each_vid_res in enumerate(VID_RESOLUTION_LIST):
        
        res_key_int =  each_vid_res[0] * each_vid_res[1] # num pixels
        res_key_str = str(each_vid_res[0]) + "x" + str(each_vid_res[1])
        
        res_str_to_pixels_mapping[res_key_str] = (res_key_int, rix+1)
                
        # data structs
        all_wc_ccr_per_vid[res_key_str] = []
         
        Icc_list = []
        Pcc_list = []
        Bcc_list = []
        
        # get data per seed 
        for each_seed in RANDOM_SEEDS:
            
            res_str = str(each_vid_res[0]) + "x" + str(each_vid_res[1])            
            fname_prefix = "__s%d_G%d" % (each_seed, NUM_GOPS)    
            fname = EXP_DATADIR + "vidworkload_data_res" + res_str + "_" + fname_prefix + ".js"
                
                
            json_data=open(fname)
            file_data = json.load(json_data)
   
            # record real-CCRs per gop
            real_ccrs = [g['real_ccr'] for g in file_data['gop_info']]
            max_ccrs = file_data['max_ccr']
            
            Icc_list.append(np.max(file_data['fr_cc_I']))
            Pcc_list.append(np.max(file_data['fr_cc_P']))
            Bcc_list.append(np.max(file_data['fr_cc_B']))
            
            all_wc_ccr_per_vid[res_key_str].append(max_ccrs)
        
        
        Iwcc =  np.max(Icc_list)
        Pwcc =  np.max(Pcc_list)
        Bwcc =  np.max(Bcc_list)
        max_flw_payload = res_key_int * 3
        
        #sys.exit()
        print each_vid_res
       
       
    ## now we plot
    fig = plt.figure(figsize=(11,4))
    fig.canvas.set_window_title('Scatter - resolution vs. ccr (per gop)')    
        
    
    print VID_RESOLUTION_LIST
    xaxis_ticks_str = [str(s[0]) + "x" + str(s[1]) for s in VID_RESOLUTION_LIST]
    
    plt.xticks(range(1, len(xaxis_ticks_str)+1), xaxis_ticks_str)
    plt.xlim([0.5, len(xaxis_ticks_str)+0.5])
    # worst-case CCR #
    
    y_data =  []
    x_data = []
    i=0
    for each_res_k, each_res_ccr_data in all_wc_ccr_per_vid.iteritems():
        x_data.extend([res_str_to_pixels_mapping[each_res_k][1]]*len(each_res_ccr_data))                
        y_data.extend(each_res_ccr_data)
        
        bp_data = each_res_ccr_data
        
        #plt.scatter(x_data, y_data)
        plt.boxplot(bp_data, positions=[i])
        plt.hold(True)
        
        i+=1
    
   
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
            fname_prefix = "__s%d_G%d" % (each_seed, NUM_GOPS)    
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
    
    data = [vid_res[0]*vid_res[1]*2 for vid_res in VID_RESOLUTION_LIST]
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
    max_bl = NoCFlow.getCommunicationCost(max_payload*0.5, nhops, NOC_PERIOD, NOC_ARBITRATION_COST)
    
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
            plt.setp(box, color='k', linewidth=1.25)
            plt.setp(box, facecolor=c_boxface, alpha=0.5)
            plt.setp(medians,linewidth=1.25, color=c_boxline)        
    for caps in bp['caps']:            
        plt.setp(caps, linewidth=1.25, color=c_cap)    
    for whiskers in bp['whiskers']:            
        plt.setp(whiskers, linewidth=1.25, color=c_wh)    
    for fliers in bp['fliers']:            
        plt.setp(fliers, linewidth=1.25, color=c_fly)

###################################
#    MAIN
###################################



#plot_Resolution_vs_CCR()

plot_Resolution_vs_CompCost()

#plot_CC_Dist_single_res()

print "finished"

plt.show()



