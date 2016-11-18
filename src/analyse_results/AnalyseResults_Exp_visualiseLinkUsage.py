import sys, os, csv, pprint, math

from collections import OrderedDict
import numpy as np
import traceback
import random
import shutil
import math
import matplotlib
from matplotlib import text
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.lines as mlines
import scipy.stats
import itertools
from matplotlib.colors import ListedColormap, NoNorm
from matplotlib import mlab
from itertools import cycle # for automatic markers
import json
from operator import itemgetter

import matplotlib.cm as cm
from matplotlib.font_manager import FontProperties
from SimParams import SimParams




NOC_H=8
NOC_W=8
TEXT_MAX_LEN = 50

P_MIN = 0.1
P_MAX = 0.9
P_DELTA = 0.6
ARROW_HEAD_SIZE = 0.05

OFFSET = 0.1
MMC_ARR_OFFSET = 0.2

LINK_ARROW_COORDS = {
                     
                     "NORTH" : (P_MIN, P_MIN, 0,P_DELTA),
                     "SOUTH" : (P_MAX,P_MAX, 0,-1.0*P_DELTA),
                     "EAST" : (P_MIN,P_MAX, P_DELTA,0),
                     "WEST" : (P_MAX,P_MIN, -1.0*P_DELTA,0),
                     
                     "LOCAL_I" : (P_MAX-OFFSET ,P_MIN+(OFFSET/2),    -1.0*P_DELTA,P_DELTA),
                     "LOCAL_O" : (P_MIN+OFFSET, P_MAX-(OFFSET/2),  P_DELTA,-1.0*P_DELTA),
                     
                     
                     # mmc arrows
                     "EAST_MMC_I" : (P_MIN,P_MAX+MMC_ARR_OFFSET, P_DELTA,0),
                     "EAST_MMC_O" :  (P_MAX,P_MIN-MMC_ARR_OFFSET, -1.0*P_DELTA,0),
                     
                     "WEST_MMC_O" : (P_MIN,P_MAX+MMC_ARR_OFFSET, P_DELTA,0),
                     "WEST_MMC_I" :  (P_MAX,P_MIN-MMC_ARR_OFFSET, -1.0*P_DELTA,0),
                     
                     "NORTH_MMC_I" : (P_MIN-MMC_ARR_OFFSET, P_MIN, 0,P_DELTA),
                     "NORTH_MMC_O" : (P_MAX+MMC_ARR_OFFSET,P_MAX, 0,-1.0*P_DELTA),
                     
                     "SOUTH_MMC_O" : (P_MIN-MMC_ARR_OFFSET, P_MIN, 0,P_DELTA),
                     "SOUTH_MMC_I" : (P_MAX+MMC_ARR_OFFSET,P_MAX, 0,-1.0*P_DELTA),
                     
                     }


def _get_node_text_str(current_text, new_str):
    split_current_text = current_text.split("\n")
    if len(split_current_text[-1]) > TEXT_MAX_LEN:
        current_text += "\n" + ", " + new_str        
    else:
        current_text += ", " + new_str
    return current_text

def _get_2d_node_coords(node_id):
    i = int(node_id/NOC_H)
    j = (node_id%NOC_H)
    return i,j


def _normalise_val(x, x_max, x_min):
    norm_val = float(x-x_min)/float(x_max-x_min)
    return norm_val


def plot_LinkUsage(fname, lbl):
    
    json_data=open(fname)
    link_data = json.load(json_data)
    
    f, axarr = plt.subplots(NOC_H, NOC_W, sharex=True, sharey=True)
    f.canvas.set_window_title('plot_LinkUsage -' + lbl)    
    
    node_xy_mapping = {}
    for ix_y in xrange(0, NOC_W):
        for ix_x in xrange(0, NOC_H):
            temp_node_ix = (ix_x*NOC_W) + ix_y            
            node_xy_mapping[temp_node_ix] = (ix_x,ix_y)
            axarr[ix_x, ix_y].set_axis_bgcolor('lightgray')            
            axarr[ix_x, ix_y].set_xlim([-0.2,1.2])
            axarr[ix_x, ix_x].set_ylim([-0.2,1.2])
            
            axarr[ix_x,ix_y].set_xticklabels([])  
            axarr[ix_x,ix_y].set_yticklabels([])
            axarr[ix_x,ix_y].set_title(temp_node_ix)
            #axarr[ix_x,ix_y].set(adjustable='box-forced', aspect='equal')
            
            #axarr[ax_i,ax_j].set_ylim(ymax = 1.1, ymin = -0.1)
            #axarr[ax_i,ax_j].set_xlim(xmax = 1.1, xmin = -0.1)
            
            axarr[ix_x,ix_y].tick_params(
                                            axis='both',          # changes apply to the x-axis
                                            which='both',      # both major and minor ticks are affected
                                            bottom='off',      # ticks along the bottom edge are off
                                            top='off',         # ticks along the top edge are off
                                            left='off',
                                            right='off',
                                            labelbottom='off')
            
    
    # calculate normalised link usage values
    all_totalf = [v["total_flows"] for v in link_data.values()]
    
    all_payload_means = [v["payload_max_min_sum_mean"][3] for v in link_data.values()]
    all_payload_sums = [v["payload_max_min_sum_mean"][2] for v in link_data.values()]
    all_intfs_means = [v["intfs_max_min_sum_mean"][3] for v in link_data.values()]
    all_intfs_sums = [v["intfs_max_min_sum_mean"][2] for v in link_data.values()]
    all_lvar_means = [v["l_var_max_min_sum_mean"][3] for v in link_data.values()]
    all_lvar_sums = [v["l_var_max_min_sum_mean"][2] for v in link_data.values()]
    
    max_totalf = np.max(all_totalf)
    min_totalf = np.min(all_totalf)
    
    max_payload_mean =  np.max(all_payload_means)
    min_payload_mean =  np.min(all_payload_means)
    max_payload_sum = np.max(all_payload_sums)
    min_payload_sum = np.min(all_payload_sums)
    
    max_intfs_mean =  np.max(all_intfs_means)
    min_intfs_mean =  np.min(all_intfs_means)
    max_intfs_sum = np.max(all_intfs_sums)
    min_intfs_sum = np.min(all_intfs_sums)
    
    max_lvar_mean =  np.max(all_lvar_means)
    min_lvar_mean =  np.min(all_lvar_means)
    max_lvar_sum = np.max(all_lvar_sums)
    min_lvar_sum = np.min(all_lvar_sums)
    
    
    print "---------------------"
    print "all_totalf_sum:", np.sum(all_totalf)
    print "max_totalf , min_totalf :", max_totalf , min_totalf
    
    print "max_payload_mean , min_payload_mean :", max_payload_mean , min_payload_mean
    print "max_payload_sum, min_payload_sum :", max_payload_sum, min_payload_sum 
    
    print "max_intfs_mean, min_intfs_mean :", max_intfs_mean, min_intfs_mean
    print "max_intfs_sum, min_intfs_sum :", max_intfs_sum, min_intfs_sum
    
    print "max_lvar_mean, min_lvar_mean :", max_lvar_mean, min_lvar_mean
    print "max_lvar_sum, min_lvar_sum :", max_lvar_sum, min_lvar_sum 
    print "---------------------"
    
    
    # plot link arrows for each link 
    for each_link_id, each_link_data in link_data.iteritems():
        
        src_nid = each_link_data['src_dst_nid_tup'][0]
        dst_nid = each_link_data['src_dst_nid_tup'][1]
        data_dir = each_link_data["data_dir"]
        
        if "MMC" in str(src_nid):
            src_nid = int(src_nid[3:])
        else:        
            if "L" in str(src_nid): 
                src_nid = int(src_nid[1:])
            else:
                src_nid = int(src_nid)
            
        
        (ax_i, ax_j) =  node_xy_mapping[src_nid]
        
        
        v = each_link_data["intfs_max_min_sum_mean"][3]
        v_max = max_intfs_mean
        v_min = min_intfs_mean       
        
        # metric
        norm_link_val = _normalise_val(v, 
                                       #0.0314419106187, 0.000555769404332)
                                       v_max, v_min)
         
#         norm_link_val = _normalise_val(each_link_data["total_flows"], 
#                                        #0.0314419106187, 0.000555769404332)
#                                        max_totalf, min_totalf)
                                       
        
        arr_col =  cm.hot(norm_link_val)
        
        if ("MMC" in data_dir):
            edge_col = "green"
        else:
            edge_col = arr_col
        
        
        axarr[ax_i,ax_j].arrow(LINK_ARROW_COORDS[data_dir][0], 
                               LINK_ARROW_COORDS[data_dir][1], 
                               LINK_ARROW_COORDS[data_dir][2], 
                               LINK_ARROW_COORDS[data_dir][3], 
                               head_width=0.05, head_length=ARROW_HEAD_SIZE, fc=arr_col, ec=arr_col, lw=4.0)
        
      
    #f.tight_layout()
    
    
    cax = f.add_axes([0.9, 0.1, 0.03, 0.8])
    matplotlib.colorbar.ColorbarBase(cax, cmap=matplotlib.cm.hot,
                                norm=matplotlib.colors.Normalize(vmin=v_min, vmax=v_max),
                                orientation='vertical')
    
###################################
#    HELPERS
###################################
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


###################################
#    MAIN
###################################

#plot_LinkUsage("C:/Users/Rosh/Documents/EngD/Work/AbstractSimulator/Multicore_Abstract_Sim/src/experiment_data/hevc_tile_mapping_wMemPSel_HighCCR/WL2/ac0mp0pr0cmb914mmp0/seed_80505/HEVCTileSplitTest__ac0mp0pr0cmb914mmp0_8_8__linkusagereport.js", lbl="mmp0")

plot_LinkUsage("Z:/MCASim/experiment_data/hevc_tile_mapping_wMemPSel_HighCCR/WL2/ac0mp0pr0cmb914mmp31/seed_81665/HEVCTileSplitTest__ac0mp0pr0cmb914mmp31_8_8__linkusagereport.js", lbl="mmp31")

plot_LinkUsage("Z:/MCASim/experiment_data/hevc_tile_mapping_wMemPSel_HighCCR/WL2/ac0mp0pr0cmb914mmp37/seed_81665/HEVCTileSplitTest__ac0mp0pr0cmb914mmp37_8_8__linkusagereport.js", lbl="mmp37")



print "finished"

plt.show()

