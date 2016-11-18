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






def plot_RMTaskRelease(report_summary = False, pfname = None):
    
    if(pfname == None):    
        fname =  "../test__RMTaskReleaseInfo.js"
    else:
        fname = pfname
        
    json_data=open(fname)
    file_data = json.load(json_data)
    
    fig = plt.figure()
    #fig, ax = plt.subplots(1, len(file_data)) 
    fig.canvas.set_window_title('RMTaskRelease')
    
    axis_list = []
    max_ax1_ylim = 0.0
    max_ax2_ylim = 0.0    
    summary_all_levels = []
    summary_all_cumlateness = []
    
    time_data = [round(float(x['time']), 4) for x in file_data]    
    
    timeline = list(np.round(np.arange(0.0, time_data[-1]+0.001, 0.001),3))
    
    which_node_data = [0] * len(timeline)
    
    for each_data_point in file_data:
        ix = timeline.index(round(float(each_data_point['time']), 3))
        
        which_node_data[ix] = int(each_data_point['node']) + 1
        
    plt.scatter(timeline, which_node_data)
    
    plt.ylabel("CPU-ID")
    plt.xlabel("Time (s)")
    plt.yticks(range(0, NUM_NODES+1, 1))
    plt.minorticks_on()    
    
    plt.tick_params(axis='both', which='both', labelsize=14)    
    plt.grid(True, which="both", axis="both", alpha=0.5)
        
    # report #
    if(report_summary == True):
        print "--------"
        print "REPORT : Total number of allocations"
        all_count = []
        for each_node_ix in xrange(1,NUM_NODES+1):
            count = len([x for x in which_node_data if x==each_node_ix])            
            print "CPU-" + str(each_node_ix) + " : " + str(count)
            all_count.append(count)
            
        print "sum : " + str(np.sum(all_count))
        print "mean : " + str(np.mean(all_count))
        print "--------"
            
        


  
        
def _set_bp(ax, bp, col):
    plt.setp(bp['boxes'], color=col, linewidth=1, alpha=0.7)    
    plt.setp(bp['caps'], color=col)
    plt.setp(bp['whiskers'], color=col)
    plt.setp(bp['fliers'], color=col)
    plt.setp(bp['medians'], color=col)
    






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




###################################
#    MAIN
###################################


plot_RMTaskRelease(report_summary=True, pfname = "../experiment_data/mapping_and_pri_schemes/seed_99108/Exp_m6_p0_wf8_cores9_rmtaskrel.js")

print "finished"

plt.show()

