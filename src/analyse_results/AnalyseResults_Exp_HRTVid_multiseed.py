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
from SimParams import SimParams

MAX_NUM_GOPS_IN_VS = SimParams.WFGEN_MAX_GOPS_PER_VID
NOC_H = 3
NOC_W = 3

global_types_of_tests = [
                      
                      ## Deterministic - AC ##

                    #{'ac':11, 'mp':0, 'pr':4, 'cmb':840 }, # determ, lumm
                    #{'ac':12, 'mp':13, 'pr':4, 'cmb':0 , 'lbl': "GA"}, # determ, improved
                    {'ac':12, 'mp':0, 'pr':4, 'cmb':841 , 'lbl': "IPC"}, # determ, improved
                    {'ac':12, 'mp':0, 'pr':4, 'cmb':842 , 'lbl': "LWCRS"}, # determ, improved
                    {'ac':12, 'mp':0, 'pr':4, 'cmb':833 , 'lbl': "PP"}, # determ, improved
                    
                    #{'ac':12, 'mp':0, 'pr':4, 'cmb':834 , 'lbl': "BN-V2"}, # determ, improved
                    {'ac':12, 'mp':0, 'pr':4, 'cmb':834 , 'lbl': "BN"}, # determ, improved
                    {'ac':12, 'mp':10, 'pr':4, 'cmb':0 , 'lbl': "LU"}, # determ, improved
                    {'ac':12, 'mp':12, 'pr':4, 'cmb':0 , 'lbl': "LM"}, # determ, improved                    
                    
                    
                      
                      ]

EXP_DATA_DIR = "../experiment_data/hrt_video/multiseed_random_res/"
#EXP_DATA_DIR = "Z:/MCASim/experiment_data/hrt_video/multiseed_random_res/"



RANDOM_SEED_LIST=[81665, 33749, 43894, 53784, 26358, \
                  80505, 83660, 22817, 70263, 29917, \
26044, 6878, 66093, 69541, 5558, \
76891, 22250, 69433, 42198, 18065, \
74076, 98652, 21149, 50399, 64217, \
44117, 57824, 42267, 83200, 99108, \
95928, 53864, 44289, 77379, 80521, \
88117, 23327, 73337, 94064, 31982]

RANDOM_SEED_LIST = [1234]


def plot_GoPResponseTime(use_sched_test_results=False):
    
    all_mptype_distributions = OrderedDict()
    
    for each_mp_type in global_types_of_tests:
        #print each_scenario
        all_seed_data = []
        for seed in RANDOM_SEED_LIST:
            # get data            
            final_fname_prefix = "HRTVid_" + \
                         "AC"+ str(each_mp_type['ac']) + "_" + \
                         "MP"+ str(each_mp_type['mp']) + "_" + \
                         "PR"+ str(each_mp_type['pr']) + "_" + \
                         "CMB"+ str(each_mp_type['cmb']) + "_"
            
            FNAME_PREFIX = final_fname_prefix+str(SimParams.NOC_H)+"_"+str(SimParams.NOC_W)+"_"
            subdir = "seed_"+str(seed)+"/"
            fname = EXP_DATA_DIR+subdir+FNAME_PREFIX + "test__schedtestresults.js"   
            print fname 
            json_data=open(fname)
            gop_data = json.load(json_data)                                
            sorted_gop_data_response_times = [x[1] for x in gop_data[-1]["current_stream_cp_wcet"]] # get the sched test as at the last VS admission
                      
            all_seed_data.append(sorted_gop_data_response_times)
        
        all_mptype_distributions[each_mp_type['lbl']] = all_seed_data
         
    # plot all ac types flow-response-times for all ac-types
    fig = plt.figure()
    fig.canvas.set_window_title('plot_GoPResponseTime')
    ax = plt.subplot(111)
    
    dist_sizes = [len(x) for x in all_mptype_distributions.values()]
    pprint.pprint(dist_sizes) 
    dist_means = [np.mean(x) for x in all_mptype_distributions.values()]
    dist_max = [np.max(x) for x in all_mptype_distributions.values()]
    
    pprint.pprint(dist_means)
        
    # plot a group of boxplots for each scenario
    width=0.3   
    ind = np.arange(len(all_mptype_distributions))
    ind_means = np.arange(len(dist_means))
    ind_max = np.arange(len(dist_max))
    pos_0 = ind
    #ax.boxplot(all_mptype_distributions.values(),0,'', whis=3, positions=pos_0, widths=0.3)
    ax.boxplot(all_mptype_distributions.values(),0,positions=pos_0, widths=0.3)
    ax.plot(ind_means, dist_means, marker='d', color='g', linewidth=0.3, label='Mean')
    #ax.plot(ind_max, dist_max, marker='x', color='r', linewidth=0.3)
    plt.hold(True)
    
    plt.grid(True)    
    labels = [ str(x) for x in all_mptype_distributions.keys()] 
    xticks = range(0,(len(labels)))
    xticks = [x for x in xticks]    
    ax.set_xticks(xticks)
    ax.set_xticklabels(labels)
    l = plt.legend()
    l.draggable(True)
    
    #plt.title("", fontsize=20)    
    ax.set_ylabel('Analytical worst-case \njob response time', fontsize=16, multialignment='center')
    ax.set_xlabel('Task mapping types', fontsize=16)
    plt.tick_params(axis='both', which='major', labelsize=14)
    plt.tick_params(axis='both', which='minor', labelsize=14)
    
    
    


       

###################################
#    HELPERS
###################################

            



###################################
#    MAIN
###################################

#plot_FlowsResponseTime(use_sched_test_results=True)
#plot_TaskResponseTime(use_sched_test_results=True)
plot_GoPResponseTime(use_sched_test_results=True)
#plot_task_executioncosts()
#plot_GoP_Lateness()
print "finished"

plt.show()

