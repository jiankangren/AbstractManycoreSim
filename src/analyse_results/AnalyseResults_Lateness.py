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

#from AdmissionControllerOptions import AdmissionControllerOptions
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
#    Priority vs. BlockingTime vs. Lateness vs. InputBuffWaitTime
###################################################################################################
    
def plot_Pri_vs_BlockingTime_vs_Lateness_vs_InputBuffWaitTime(fname=None,m=None,p=None, wf=None, seed=None, all_seeds=False):                
    
    if (m==None) and (p==None) and (wf==None) and (seed==None):   
        sys.exit("plot_Pri_vs_BlockingTime_vs_Lateness_vs_InputBuffWaitTime:: error")    
    
    # plot single seed ?    
    if (all_seeds == False):    
        if(fname==None):
            FNAME_PREFIX = "Exp_m"+str(m) + "_p"+str(p) + "_"    
            fname = EXP_DATA_DIR + "/seed_" + str(seed) + "/" + FNAME_PREFIX + 'wf'+str(wf)+'_cores'+str(NUM_NODES) + "_obuff.js"    
            json_data=open(fname)
            file_data = json.load(json_data)
        else:
            json_data=open(fname)
            file_data = json.load(json_data)
    else:
        file_data = []
        for ix, each_seed in  enumerate(RANDOM_SEED_LIST):
            FNAME_PREFIX = "Exp_m"+str(m) + "_p"+str(p) + "_"    
            fname = EXP_DATA_DIR + "/seed_" + str(each_seed) + "/" + FNAME_PREFIX + 'wf'+str(wf)+'_cores'+str(NUM_NODES) + "_obuff.js"
            json_data=open(fname)
            temp_file_data = json.load(json_data)            
            file_data.extend(temp_file_data)
            
           
    sorted_file_data = sorted(file_data, key=itemgetter('pri')) 
    
    task_priorities = [x['pri'] for x in sorted_file_data] 
    task_blockingtime = [ ((x['et']-x['rt'])-x['cc']) for x in sorted_file_data]
    task_ibuff_watingtime = [ (x['rt']-x['dt']) for x in sorted_file_data]
    task_ids = [x['id'] for x in sorted_file_data]
    task_estlateness = [x['estL'] for x in sorted_file_data]
    
    f, axarr = plt.subplots(3, sharex=True)
    f.canvas.set_window_title('Pri_vs_BT_vs_estL_vs_ibwtime - ' + "m="+str(m)+"p="+str(p))
    
    axarr[0].set_title('IBuff Waiting Time')
    axarr[0].scatter(task_priorities, task_ibuff_watingtime, marker='.', color='g')    
    axarr[1].set_title('Task NodeTQ BlockingTime')
    axarr[1].scatter(task_priorities, task_blockingtime, marker='.', color='r')    
    axarr[2].set_title('Task lateness')
    axarr[2].scatter(task_priorities, task_estlateness, marker='.', color='b')

        
###################################################################################################
#    Lateness vs. video stream
###################################################################################################     
def plot_Vidstrm_vs_Lateness(m=None,p=None, wf=None, seed=None, all_seeds=False):
    if (m==None) and (p==None) and (wf==None) and (seed==None):       
        sys.exit("plot_Vidstrm_vs_Lateness:: error")        
        
    FNAME_PREFIX = "Exp_m"+str(m) + "_p"+str(p) + "_"    
    fname_wfressumm = EXP_DATA_DIR + "/seed_" + str(seed) + "/" + FNAME_PREFIX + 'wf'+str(wf)+'_cores'+str(NUM_NODES) + "_wfressumm.js"
    fname_gopsopbuffsumm = EXP_DATA_DIR + "/seed_" + str(seed) + "/" + FNAME_PREFIX + 'wf'+str(wf)+'_cores'+str(NUM_NODES) + "_gopsopbuffsumm.js"    
    
    print fname_wfressumm
    print fname_gopsopbuffsumm
    
    ######## data formatting ###########
    ## get data from both files and summarise data ##
    wfressumm_file_data = json.load(open(fname_wfressumm))
    gopsopbuffsumm_file_data = json.load(open(fname_gopsopbuffsumm))  
    
    
    # first build the resolution specific info
    vs_specific_data = _get_resfactor_specific_info(wfressumm_file_data)                
    
    # now update data struct with the gop specific lateness info
    for each_vs_resfactor_key, each_vs_resfactor_val in vs_specific_data.iteritems():
        for each_gop in each_vs_resfactor_val['gops_late_but_fully_complete']:
            if each_gop != -1:
                each_vs_resfactor_val['lateness'].append(gopsopbuffsumm_file_data[str(each_gop)]['gop_execution_lateness'])
            else:
                each_vs_resfactor_val['lateness'].append(0.0)
        
    # sort results
    boxplot_data = []
    boxplot_labels = []
    
    for each_key in sorted(vs_specific_data.keys()):
        boxplot_data.append(vs_specific_data[each_key]['lateness'])
        boxplot_labels.append(("("+str(vs_specific_data[each_key]['h'])+","+str(vs_specific_data[each_key]['w'])+")"))
        
    ######## plotting ###########
    fig = plt.figure()
    fig.canvas.set_window_title('vidstrm_vs_lateness - ' + "m="+str(m)+"p="+str(p))
    boxpos=np.arange(len(vs_specific_data.keys()))    
    bp=plt.boxplot(boxplot_data,0,'', whis=1, positions=boxpos, widths=0.8)
    
    xticks = [x for x in range(0,(len(boxplot_labels)))]    
    plt.xticks(xticks, boxplot_labels)
    
        

###################################################################################################
#    Lateness vs. GoP dispatch time vs. Priorities
###################################################################################################    
def plot_Vidstrm_vs_DispatchTime(m=None,p=None, wf=None, seed=None):
    if (m!=None) and (p!=None) and (wf!=None) and (seed!=None):
        FNAME_PREFIX = "Exp_m"+str(m) + "_p"+str(p) + "_"    
        fname_wfressumm = EXP_DATA_DIR + "/seed_" + str(seed) + "/" + FNAME_PREFIX + 'wf'+str(wf)+'_cores'+str(NUM_NODES) + "_wfressumm.js"
        fname_gopsopbuffsumm = EXP_DATA_DIR + "/seed_" + str(seed) + "/" + FNAME_PREFIX + 'wf'+str(wf)+'_cores'+str(NUM_NODES) + "_gopsopbuffsumm.js"
        
    else:
        sys.exit("plot_Vidstrm_vs_DispatchTime:: error")        
    
    print fname_wfressumm
    print fname_gopsopbuffsumm
    
    ######## data formatting ###########
    ## get data from both files and summarise data ##
    wfressumm_file_data = json.load(open(fname_wfressumm))
    gopsopbuffsumm_file_data = json.load(open(fname_gopsopbuffsumm))    
    
    gop_list = [v for v in gopsopbuffsumm_file_data.values()]
    sorted_gops = sorted(gop_list, key=lambda k: k['dispatch_time']) 
    
    x_data = []
    y_data = []
    pri_data = []
    
    for k,gop in enumerate(sorted_gops):
        x_data.append(gop['dispatch_time'])
        y_data.append(gop['gop_execution_lateness'])
        pri_data.append(gop['task_priorities'])
    
    lab = [str(x) for x in x_data]
    ######## plotting ###########
    f, axarr = plt.subplots(2, sharex=True)
    f.canvas.set_window_title('pri_vs_lateness_vs_dispatchtime - ' + "m="+str(m)+"p="+str(p))
    
    # priorities
    boxpos = np.arange(len(x_data))
    boxplot_data = pri_data
    bp=axarr[0].boxplot(boxplot_data,0,'', whis=1, positions=boxpos, widths=0.8)
    
    # lateness        
    bp=axarr[1].plot(y_data)    
    xticks = [x for x in range(0,(len(lab)))]    
    #plt.xticks(xticks, lab, rotation=90, fontsize=8)
    
    axarr[1].set_xticks(xticks)
    axarr[1].set_xticklabels( lab , rotation=90,fontsize=8)

    
    



        
        
        
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

#plot_Pri_vs_BlockingTime_vs_Lateness_vs_InputBuffWaitTime(fname=None,p=4,m=2,wf=8,seed=-1, all_seeds=True)
#plot_Pri_vs_BlockingTime_vs_Lateness_vs_InputBuffWaitTime(fname=None,p=4,m=8,wf=8,seed=-1, all_seeds=True)
#plot_Pri_vs_BlockingTime_vs_Lateness_vs_InputBuffWaitTime(fname=None,p=4,m=5,wf=8,seed=-1, all_seeds=True)
plot_Pri_vs_BlockingTime_vs_Lateness_vs_InputBuffWaitTime(fname="../test__obuff.js",p=4,m=5,wf=8,seed=-1, all_seeds=False)
#plot_Pri_vs_BlockingTime_vs_Lateness_vs_InputBuffWaitTime(p=4,m=8,wf=12,seed=-1, all_seeds=True)

#plot_Vidstrm_vs_Lateness(p=4,m=2,wf=8, seed=74076)
#plot_Vidstrm_vs_Lateness(p=4,m=2,wf=12, seed=74076)

#plot_Vidstrm_vs_DispatchTime(p=4,m=2,wf=8, seed=26358)
#plot_Vidstrm_vs_DispatchTime(p=4,m=2,wf=12, seed=26358)




print "finished"

plt.show()

