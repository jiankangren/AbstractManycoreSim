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
from util_scripts.count_finished_log_files import fname


EXP_DATA_DIR = "Z:/MCASim/experiment_data/hrt_video/noc_scale/"


NOC_H=4
NOC_W=4
TEXT_MAX_LEN = 50



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
  
#     text(0.5, 0.5,'matplotlib',
#      horizontalalignment='center',
#      verticalalignment='center',
#      transform = ax.transAxes)
#     




def plot_TileAllocation(fname):
    
    fname_prefix_rmtable = fname+"__rmtaskmappingtable.js"
    fname_prefix_gopsumm = fname+"__gopsopbuffsumm.js"
    
    json_data=open(fname_prefix_rmtable)
    tm_data = json.load(json_data)
    
    json_data=open(fname_prefix_gopsumm)
    gop_data = json.load(json_data)
    
    
    f, axarr = plt.subplots(NOC_H, NOC_W, sharex=True, sharey=True)
    f.canvas.set_window_title('plot_TileAllocation')    
    
    node_specific_text = {}
    unique_gops = []
    node_specific_scatter = {}
    
    # construct strings for nodes
    for each_task_id, each_task_info in tm_data.iteritems():
        orig_tid = each_task_id.split("_")[0]
        task_text = orig_tid + "_" + each_task_info['strm_key'].split('_')[-1]
        node_id = each_task_info['node_id']
        
        # populate nodes text
        if node_id not in node_specific_text:
            node_specific_text[node_id] = task_text
        else:
            node_specific_text[node_id] = _get_node_text_str(node_specific_text[node_id], task_text)
                
        # populate unique gops
        if each_task_info['strm_key'] not in unique_gops: unique_gops.append(each_task_info['strm_key'])
        
    # plot text on nodes
    for each_node_id, each_node_text in  node_specific_text.iteritems():
        i,j = _get_2d_node_coords(each_node_id)
        
#         axarr[i,j].text(0.5, 0.5, each_node_text,
#           horizontalalignment='center',
#           verticalalignment='center',
#           size=9
#           )
        
        axarr[i,j].set_xticklabels([])  
        axarr[i,j].set_yticklabels([])
        axarr[i,j].set_ylim(ymax = 1.1, ymin = -0.1)
        axarr[i,j].set_xlim(xmax = 1.1, xmin = -0.1)
        #axarr[i,j].set_title("PE_"+str(each_node_id))
        
        axarr[i,j].tick_params(
            axis='both',          # changes apply to the x-axis
            which='both',      # both major and minor ticks are affected
            bottom='off',      # ticks along the bottom edge are off
            top='off',         # ticks along the top edge are off
            left='off',
            right='off',
            labelbottom='off') 
      
        
            
    mapping_type_colors = plt.get_cmap('rainbow')(np.linspace(0, 1.0, len(unique_gops)))  
    
#     mapping_type_colors = [
#                            
#                            # diverging
#                            # '#f1a340',
#                            # '#f7f7f7',
#                            # '#998ec3'
#                            
#                            # sequential
#                            '#fee8c8',
#                            '#fdbb84',
#                            '#e34a33',
#                                                       
#                            ]
    
    #markers_list = mlines.Line2D.filled_markers
    #markers_list = markers_list + ('.',) 
    markers_list = 'o', 'd', 's'
    
    
    print "num unique gops : ", len(unique_gops)
     
    # plot scatter on nodes
    print len(markers_list)    
    scref_list = []
    label_list = []
    ugid_list = []
    node_specific_task_count = {}
    node_specific_task_type = {}
    
    for each_task_id, each_task_info in tm_data.iteritems():
        gop_key = each_task_info['strm_key']
        node_id = each_task_info['node_id']
        
        col_ix = unique_gops.index(gop_key)
        i,j = _get_2d_node_coords(node_id)
        sc_ref = axarr[i,j].scatter(np.random.rand(), np.random.rand(), s=20*4**2, 
                                    c=mapping_type_colors[col_ix], lw = 0.3,
                                    marker=markers_list[col_ix])
        
        ugid = each_task_info['strm_key'].split('_')[2]
        if ugid not in ugid_list:
            scref_list.append(sc_ref)        
            vid_res = gop_data[ugid]['strm_res']
            label_list.append(vid_res)
            ugid_list.append(ugid)
        
        
        if node_id not in node_specific_task_count: 
            node_specific_task_count[node_id] = 0
            node_specific_task_type[node_id] = each_task_info['wcc']
        else:
            node_specific_task_count[node_id] += 1
            node_specific_task_type[node_id] += each_task_info['wcc']
    
    pprint.pprint(node_specific_task_count)
    print "---"
    pprint.pprint(node_specific_task_type)
    
    
    leg = f.legend( scref_list, label_list, loc = (0.5, 0), ncol=5, scatterpoints=1, )
    leg.draggable()
    leg.legendHandles[0]._sizes = [150]
    leg.legendHandles[1]._sizes = [150]
    leg.legendHandles[2]._sizes = [150]
    
    f.subplots_adjust(wspace=0.025, hspace=0.05)
    
    
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


#plot_TileAllocation("Z:/MCASim/experiment_data/hevc_tiles_mapping_test/WL1/ac0mp0pr0cmb903mmp0/seed_80505/HEVCTileSplitTest__ac0mp0pr0cmb903mmp0_8_8")

plot_TileAllocation("../experiment_data/\hevc_tiles_mapping_test/WL1/ac0mp0pr0cmb903mmp0/seed_6868/HEVCTileSplitTest__ac0mp0pr0cmb903mmp0_4_4")


print "finished"

plt.show()

