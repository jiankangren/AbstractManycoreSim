import sys, os, csv, pprint, math

from collections import OrderedDict
import numpy as np
import random
import shutil
import math
import matplotlib as mpl
from matplotlib import cm

## uncomment when running under CLI only version ##
#import matplotlib
#matplotlib.use('Agg')

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
#from util_scripts.plot_workflows import wf_data

NUM_WORKFLOWS = range(8, 19, 1)
#NUM_WORKFLOWS = [9]
#NUM_NODES = [2,4,8,16,32]
NUM_NODES = 9
NOC_XY = [(2,1), (2,2), (2,4), (2,8), (2,16)]


IBUFF_TASKS_LATENESS_RATIO_RANGE    = [0.3, 0.7]
TQ_TASKS_LATENESS_RATIO_RANGE       = [0.3, 0.7]        

SEED = 26358

#EXP_DATA_DIR = "Z:/MCASim/experiment_data/remapping_psbased_mmcoff"
#EXP_DATA_DIR = "Z:/MCASim/experiment_data/remapping_psbased"
#EXP_DATA_DIR = "Z:/MCASim/experiment_data/remapping_randombased/neighbour"
#EXP_DATA_DIR = "Z:/MCASim/experiment_data/remapping_randombased"
EXP_DATA_DIR = "Z:/MCASim/experiment_data/remapping_ccpbased"
#EXP_DATA_DIR = "Z:/MCASim/experiment_data/remapping_ccpbased_single_cluster"
#EXP_DATA_DIR = "Z:/MCASim/experiment_data/remapping_central_dynamic"

#EXP_DATA_DIR = "../experiment_data/remapping_psbased"

#local
#PSRM_EXP_DATA_DIR = "Z:/MCASim/experiment_data/remapping_psbased"
#CCPRM_EXP_DATA_DIR = "Z:/MCASim/experiment_data/remapping_ccpbased"
#RANDNEIGHRM_EXP_DATA_DIR = "Z:/MCASim/experiment_data/remapping_randombased/neighbour"
#RAND_EXP_DATA_DIR = "Z:/MCASim/experiment_data/remapping_randombased"

# server
PSRM_EXP_DATA_DIR = "../experiment_data/remapping_psbased"
CCPRM_EXP_DATA_DIR = "../experiment_data/remapping_ccpbased"
RANDNEIGHRM_EXP_DATA_DIR = "../experiment_data/remapping_randombased/neighbour"
RAND_EXP_DATA_DIR = "../experiment_data/remapping_randombased"

# 30 seeds good for both ps AND ccp - 28/02/15
# RANDOM_SEED_LIST= [33749,
# 43894, 53784, 70263, 5558, 76891, 22250, 42198, 74076, 21149,
# 57824, 83200, 53864, 44289, 77379, 23327, 94064, 57177, 26828,
# 84400, 68553, 83694, 68385, 88649, 63193, 76160, 87209, 21576,
# 97669, 79913]



# 30 seeds good for both ps AND ccp - 26/02/15
# RANDOM_SEED_LIST=[33749, \
# 43894,26358,70263,5558,76891,42198,74076, \
# 98652,21149,83200,95928,44289,77379,88117, \
# 73337,94064,57177,84400,81474,68553,83694, \
# 79292,69923,68385,88649,76160,87209,21576, \
# 97669]


RANDOM_SEED_LIST=[81665, 33749, 43894, 53784, 26358, \
80505, 83660, 22817, 70263, 29917, \
26044, 6878, 66093, 69541, 5558, \
76891, 22250, 69433, 42198, 18065, \
74076, 98652, 21149, 50399, 64217, \
44117, 57824, 42267, 83200, 99108, \
95928, 53864, 44289, 77379, 80521, \
88117, 23327, 73337, 94064, 31982]



#[44289, 99108, 88117, 29917, 83660, 42198, 73337, 94064]


NUM_ROWS = 7
NUM_COLS = 10

#INTERESTED_SEEDS = len(RANDOM_SEED_LIST)
INTERESTED_SEEDS = 30
    
  
            

def _set_bp(ax, bp, col):
    plt.setp(bp['boxes'], color=col, linewidth=1, alpha=0.7)    
    plt.setp(bp['caps'], color=col)
    plt.setp(bp['whiskers'], color=col)
    plt.setp(bp['fliers'], color=col)
    plt.setp(bp['medians'], color=col)
    

    


def plot_flows_completed(data_filename = None, base_dir="Z:/MCASim/experiment_data/"):
            
    LIST_EXP_DATA_DIRS = [ 
                            ## PSRM
                            #["Z:/MCASim/experiment_data/remapping_psbased_mmcoff", 'PSRM_MMCOFF', None],
                            #["Z:/MCASim/experiment_data/remapping_psbased_mmcoff_v2", 'PSRM', "plot_flows_completed_datafile.js"],                            
                            [base_dir + "remapping_psbased", 'PSRM_EXP', None],                            
                               
                            ## fully dynamic
                            [base_dir + "remapping_central_dynamic", 'FULLYDYNAMIC', None],
                            
                        ]
    
    NOC_SIZE = [7,10,12,20]
    
    all_exp_data = OrderedDict()
    
    
    if(data_filename == None):    
        
        for each_exp_dir in LIST_EXP_DATA_DIRS:        
            EXP_DATA_DIR = each_exp_dir[0]
            EXP_LABEL = each_exp_dir[1]
            DATAFILENAME = each_exp_dir[2]
            
            if (DATAFILENAME == None):
            
                print "------------------------------------------"
                print EXP_LABEL
                print "------------------------------------------"
                
                all_noc_data = []
                for each_nocsize in NOC_SIZE:                        
                    try:            
                        # get psbased_remapping data communication costs            
                        MULTISEED_EXP_DATA_DIR = EXP_DATA_DIR + "/noc_" + str(each_nocsize) + "x" + str(each_nocsize)
                        FNAME_PREFIX = "RMON_"    
                        fname = MULTISEED_EXP_DATA_DIR + "/" + FNAME_PREFIX + "test__flwcompleted.js"
                        print fname
                        json_data=open(fname)
                        flwscompleted_file_data = json.load(json_data)
                        json_data.close()
                        data = _get_comms_overhead(flwscompleted_file_data)
                        #data_2 = _get_datatraffic_interference(flwscompleted_file_data)
                        all_noc_data.append(data[0])
        
                               
                    except Exception as e:
                        print "------"
                        print "file not found !"
                        print fname
                        print e
                        print "------"
                        continue
                    
                print all_noc_data            
                all_exp_data[EXP_LABEL] = {                                           
                                           'flws_completed_dist' : all_noc_data
                                           }
            else:
                print "------------------------------------------"
                print EXP_LABEL  + " :: loading from local file"
                print "------------------------------------------"
                json_data=open(DATAFILENAME)
                all_exp_data[EXP_LABEL] = json.load(json_data)[EXP_LABEL]
                
    else:
        print "plot_flows_completed :: loading data from file"
        json_data=open(data_filename)
        all_exp_data = json.load(json_data)
        
    
    # plot data
    f1, ax1 = plt.subplots()
    f1.canvas.set_window_title('Communication overhead - barplots')
    #color=iter(cm.get_cmap(name='rainbow')(np.linspace(0,1,len(all_exp_data.keys()))))    
    colors = ['r','g','b','k']
    
    i=0
    for each_noc_k, each_noc_v in all_exp_data.iteritems():
        #c=next(color)
        x_pos = np.arange(len(each_noc_v['flws_completed_dist']))
        ax1.plot(x_pos, each_noc_v['flws_completed_dist'], c=colors[i], marker='x')
        plt.hold(True)     
        i+=1
        
    ax1.tick_params(axis='both', labelsize=20)
    plt.ylabel('Communication overhead\nCumulative basic latency (s)\n(mean of all exp. runs)', fontsize=20, multialignment='center')
    plt.grid(True)
     

    
    
    
    
    
    return all_exp_data


def _normalise_2d_list(list_2d):
    # normalise all-data 
    norm_max = np.max([item for sublist in list_2d for item in sublist])
    norm_min = np.min([item for sublist in list_2d for item in sublist])
    
    new_2d_list = []
    for each_l in list_2d:
        temp_list = []
        for x in each_l:
            norm_val = (x-norm_min)/(norm_max-norm_min)
            temp_list.append(norm_val)
        
        new_2d_list.append(temp_list)
    
    return new_2d_list 
        
        
def _normalise_list(lst):
    norm_max = np.max(lst)
    norm_min = np.min(lst)
    
    new_list = []
    for each_l in lst:   
        x = each_l     
        norm_val = (x-norm_min)/(norm_max-norm_min)
        new_list.append(norm_val)
       
    
    return new_list 







###################################
#    HELPERS
###################################
# any flow_type other than [0,1,6,7] is considered overhead
def _get_comms_overhead(flwscompleted_file_data):
    intfs_count = 0.0
    count = 0.0
    DATA_FLOWS = [0,1,8,9]
    all_control_flow_durations = []
    all_control_flow_durations = [f['bl'] for f in flwscompleted_file_data if(f['type'] not in DATA_FLOWS)]
    
#     for each_flw_completed in flwscompleted_file_data:
#         if(each_flw_completed['type'] not in DATA_FLOWS):
#             flow_rt = each_flw_completed['et'] - each_flw_completed['st']
#             flow_bl = each_flw_completed['bl']
#             all_control_flow_durations.append(flow_bl)
    
    
    return [np.mean(all_control_flow_durations), len(all_control_flow_durations)]

def _get_datatraffic_interference(flwscompleted_file_data):
    intfs_count = 0.0
    count = 0.0
    DATA_FLOWS = [0,1,8,9]
    all_data_traffic_intrs = []
    all_data_traffic_intrs = [f['intfs'] for f in flwscompleted_file_data if(f['type'] in DATA_FLOWS)]
    

    return [all_data_traffic_intrs, np.sum(all_data_traffic_intrs)]



def _get_num_vids_fully_scheduled(wf_data):
    total_true = []
    for each_wf_id, each_wf in wf_data.iteritems():
        for each_vidstrm_id, each_vidstrm in each_wf.iteritems():
            result = each_vidstrm['result']
            if result == True:
                total_true.append([each_wf_id, each_vidstrm_id])
    
    return len(total_true)
            

        
def _getEntry(file_data):
    
    entry =  {
            "num_vids_accepted_success": file_data['num_vids_accepted_success'], 
            "num_dropped_tasks": file_data['num_dropped_tasks'], 
            "num_vids_accepted_late": file_data['num_vids_accepted_late'], 
            "num_vids_rejected": file_data['num_vids_rejected']
        }    
    return entry

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
            


def _mean_confidence_interval(data, confidence=0.95):
    a = 1.0*np.array(data)
    n = len(a)
    m, se = np.mean(a), scipy.stats.sem(a)
    h = se * scipy.stats.t._ppf((1+confidence)/2., n-1)
    return m, m-h, m+h


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
#    MAIN
###################################

#plot_resptime_variance_multiseed(xaxis_key='dt')
print "========================================================================"
#plot_GoP_lateness_multiseed()
#plot_GoP_lateness_vs_pri_multiseed()



result = plot_flows_completed(base_dir="Z:/MCASim/experiment_data/remapping_nocsize/")
_write_formatted_file('plot_flows_completed_datafile.js', result, 'json')


#result = plot_num_vids_fully_scheduled()
#_write_formatted_file('plot_num_vids_fully_scheduled.js', result, 'json')


print "========================================================================"
#plot_SeedCCDistributions()

#plot_flows_completed()

print len(RANDOM_SEED_LIST[:INTERESTED_SEEDS])

print "finished"

plt.show()

