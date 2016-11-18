import sys, os, csv, pprint, math

from collections import OrderedDict
import numpy as np
import random
import shutil
import math
import matplotlib
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
import matplotlib.image as mpimg

from AdmissionControllerOptions import AdmissionControllerOptions
from SimParams import SimParams


import Multicore_MPEG_Model as MMMSim


NUM_WORKFLOWS = range(8, 19, 1)
#NUM_WORKFLOWS = [9]
#NUM_NODES = [2,4,8,16,32]
NUM_NODES = 9
NOC_XY = [(2,1), (2,2), (2,4), (2,8), (2,16)]


IBUFF_TASKS_LATENESS_RATIO_RANGE    = [0.3, 0.7]
TQ_TASKS_LATENESS_RATIO_RANGE       = [0.3, 0.7]        

SEED = 26358

EXP_DATA_DIR = "../experiment_data/mapping_and_pri_schemes"

RANDOM_SEED_LIST = \
[81665, 33749, 43894, 26358, 80505, \
 83660, 22817, 70263, 29917, 26044, \
 5558,  76891, 22250, 42198, 18065, \
 74076, 98652, 21149, 50399, 64217, \
 44117, 57824, 42267, 83200, 99108, \
 95928, 53864, 44289, 77379, 80521, \
 88117, 23327, 73337, 94064, 31982, \
 6878, 66093, 69541]




###################################################################################################
#    Mapping+Pri selection vs. System Load
###################################################################################################
    
def plot_Mapping_vs_SysLoad(m=None,p=None, wf=None, seed=None, all_seeds=False):                
    
    if (m==None) and (p==None) and (wf==None) and (seed==None):   
        sys.exit("plot_Mapping_vs_SysLoad:: error")    
    
    # plot single seed ?    
    if (all_seeds == False):    
        FNAME_PREFIX = "Exp_m"+str(m) + "_p"+str(p) + "_"    
        fname = EXP_DATA_DIR + "/seed_" + str(seed) + "/" + FNAME_PREFIX + 'wf'+str(wf)+'_cores'+str(NUM_NODES) + "_mappingandpriass.js"    
        json_data=open(fname)
        file_data = json.load(json_data)
    else:
        file_data = []
        for ix, each_seed in  enumerate(RANDOM_SEED_LIST):
            FNAME_PREFIX = "Exp_m"+str(m) + "_p"+str(p) + "_"    
            fname = EXP_DATA_DIR + "/seed_" + str(each_seed) + "/" + FNAME_PREFIX + 'wf'+str(wf)+'_cores'+str(NUM_NODES) + "_mappingandpriass.js"
            json_data=open(fname)
            temp_file_data = json.load(json_data)            
            file_data.extend(temp_file_data)
            
           
    sorted_file_data = sorted(file_data, key=itemgetter('time')) 
    
    timeline        =  [x['time'] for x in sorted_file_data]
    frame_mappings = [x['fr_mapp'].values() for x in sorted_file_data] 
    frame_priass = [x['fr_priass'].values() for x in sorted_file_data]
    ntq_info = [x['nTQInfo'] for x in sorted_file_data]
    strm_specs = [x['strm_specs'] for x in sorted_file_data]
    
    print len(timeline)
    
#    for x in strm_specs:
#        print "--"
#        print str(x['wf_id']) + "," + str(x['vid_strm_id'])
#        print "--"
#    
    #sys.exit()
    
    ## format mapping data
    expanded_timeline = []
    expanded_frame_mappings = []
    expanded_priass = []
    expanded_scatter_marker_size = []
    expanded_annotation = []
    
    for ix,each_item in enumerate(frame_mappings):
        expanded_timeline.extend([timeline[ix]]*len(each_item))
        expanded_frame_mappings.extend(each_item)
        expanded_priass.extend(frame_priass[ix])
        expanded_scatter_marker_size.extend([20*each_item.count(x) for x in each_item])
        
    ## format node load information
    node_specific_load_info = {}
    num_total_nodes = len(ntq_info[0])
    max_load = 0
    for each_node_id in xrange(num_total_nodes):    
        node_tqlen = [len(x[each_node_id]) for x in ntq_info]
        node_specific_load_info[each_node_id] = {
                                                 'tq_len' : node_tqlen 
                                                 }        
        if(max(node_tqlen) > max_load): max_load = max(node_tqlen)
    
    f, axarr = plt.subplots(2+num_total_nodes, sharex=True)    
    f.canvas.set_window_title('plot_Mapping_vs_SysLoad - ' + "m="+str(m)+"p="+str(p) + "seed="+str(seed))
    
    axarr_count=0
    #axarr[0].set_title('Mapping Selection')
    axarr[axarr_count].scatter(expanded_timeline, expanded_frame_mappings, s=expanded_scatter_marker_size, marker='.', color='g')
    axarr_count+=1
    #axarr[1].set_title('Mapping Selection')
    axarr[axarr_count].scatter(expanded_timeline, expanded_priass, marker='.', color='r')
    axarr_count+=1
    
    for each_node_id in xrange(num_total_nodes):    
        axarr[axarr_count].plot(timeline, node_specific_load_info[each_node_id]['tq_len'], color='b', marker='*')        
        axarr[axarr_count].set_ylim((0,max_load))        
        axarr[axarr_count].yaxis.set_tick_params(labelsize=9)
        axarr_count+=1
    
#    for ix,timestamp in enumerate(timeline):
#        for each_mapping in frame_mappings[ix]:
#            axarr[0].scatter(timestamp, each_mapping, marker='.', color='g')    
#            plt.hold(True)
            
#    axarr[1].set_title('Task NodeTQ BlockingTime')
#    axarr[1].scatter(task_priorities, task_blockingtime, marker='.', color='r')    
#    axarr[2].set_title('Task lateness')
#    axarr[2].scatter(task_priorities, task_estlateness, marker='.', color='b')
    
     
    #xticks = [x for x in range(0,(len(timeline)))]    
    #xticks_labels = [str(x) for x in range(0,(len(timeline)))]
    #plt.xticks(xticks, xticks_labels)
    
    f.subplots_adjust(hspace=0)
    
    

    
    



        
        
        
def _set_bp(ax, bp, col):
    plt.setp(bp['boxes'], color=col, linewidth=1, alpha=0.7)    
    plt.setp(bp['caps'], color=col)
    plt.setp(bp['whiskers'], color=col)
    plt.setp(bp['fliers'], color=col)
    plt.setp(bp['medians'], color=col)
    
    
###################################
#    Show images
###################################
def show_timeline_image(m=None,p=None, wf=None, seed=None):
    
    if (m==None) and (p==None) and (wf==None) and (seed==None):   
        sys.exit("plot_Mapping_vs_SysLoad:: error")    
     
    FNAME_PREFIX = "Exp_m"+str(m) + "_p"+str(p) + "_"    
    fname = EXP_DATA_DIR + "/seed_" + str(seed) + "/" + FNAME_PREFIX + 'wf'+str(wf)+'_cores'+str(NUM_NODES) + "_timeline.png"    
    
    f = plt.figure()
    ax = plt.subplot(1,1,1)
    
    img=mpimg.imread(fname)
    imgplot = plt.imshow(img)
    ax.xaxis.set_visible(False)
    ax.yaxis.set_visible(False)


###################################
#    HELPERS
###################################

        
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


def _get_resfactor_specific_info(data_wfressumm):
    vs_specific_data = {}
    
    for each_wf_id, each_wf in data_wfressumm.iteritems():
        for each_vs_id, each_vs in each_wf.iteritems():
            res_factor = each_vs["res_w"] * each_vs["res_h"]
            print "wf=" + str(each_wf_id) + ",vs=" + str(each_vs_id) + ", res="+str(res_factor)
            
            try:
                if(each_vs['result'] == False):
                    if res_factor not in vs_specific_data:
                        vs_specific_data[res_factor] = {
                                                        'h' : each_vs["res_h"],
                                                        'w' : each_vs["res_w"],
                                                        'gops_late_but_fully_complete' : each_vs["gops_late_but_fully_complete"],                                                        
                                                        'res' : res_factor,
                                                        'lateness' : []                                                                                                      
                                                        }
                    else:                    
                        vs_specific_data[res_factor]['gops_late_but_fully_complete'].extend(each_vs["gops_late_but_fully_complete"])
                else:
                    if res_factor not in vs_specific_data:
                        vs_specific_data[res_factor] = {
                                                        'h' : each_vs["res_h"],
                                                        'w' : each_vs["res_w"],
                                                        'gops_late_but_fully_complete' : [-1],
                                                        'res' : res_factor,
                                                        'lateness' : [0.0]                                             
                                                        }                    
                    
            except:
                pprint.pprint(each_vs)               
                sys.exit("error")
    
    
    return vs_specific_data
            



###################################
#    MAIN
###################################

plot_Mapping_vs_SysLoad(p=4,m=2,wf=8,seed=99108, all_seeds=False)

show_timeline_image(p=4,m=2,wf=8,seed=99108)


print "finished"

plt.show()

