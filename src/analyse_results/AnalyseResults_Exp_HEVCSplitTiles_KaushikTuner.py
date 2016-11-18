import sys, os, csv, pprint, math

#sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

## uncomment when running under CLI only version ##
#import matplotlib
#matplotlib.use('Agg')

#sys.path.append("/shared/storage/cs/staffstore/hrm506/simpy-3.0.5/")
#sys.path.append("/shared/storage/cs/staffstore/hrm506/networkx-1.10/networkx-1.10")

from collections import OrderedDict
import numpy as np
import traceback
from collections import Iterable
import re
import pylab
import random
import shutil
import math
import matplotlib
import matplotlib.pyplot as plt
plt.style.use('ggplot')
from mpl_toolkits.mplot3d import Axes3D
import scipy.stats
import scipy.optimize as scipy_optimize
import itertools
from matplotlib.colors import ListedColormap, NoNorm, rgb2hex
from matplotlib import mlab
from itertools import cycle # for automatic markers
import json
from operator import itemgetter
from scipy import stats
from collections import Counter

import multiprocessing

#from scipy.stats import gaussian_kde


import matplotlib.ticker
import matplotlib.cm as cm
import matplotlib.patches as patches
from matplotlib.font_manager import FontProperties
from SimParams import SimParams


SHOW_PLOTS = True
USE_MULTIPROCESSING = False

NOC_H = 8
NOC_W = 8

MAX_SEEDS = 30

               
FAILED_SEEDS = []
#RANDOM_SEEDS =[s for s in RANDOM_SEEDS if s not in FAILED_SEEDS][:MAX_SEEDS]

RANDOM_SEEDS_MISC=[33749, 43894, 26358, 80505]

RANDOM_SEEDS = RANDOM_SEEDS_MISC
print len(set(RANDOM_SEEDS))

#sys.exit()

EXP_DATADIR = "Z:/MCASim/experiment_data/hevc_tile_mapping_kaushikTuner/"

DATA_TEMP_SAVE_LOC = "../experiment_data/hevc_tile_mapping_kaushikTuner/"


CMB_ID = 912
MMP_ID = 0 

#global_mp_order = [d['lbl'] for d in global_types_of_tests]


KAUSHIK_COMMS_SCALE_FACTOR = [6, 9, 12, 15, 20, 25, 30, 35, 40, 45, 50]


WORKLOAD_KEY = "WL2"



def _save_data(fname, data):
    final_fname = DATA_TEMP_SAVE_LOC + fname    
    logfile=open(final_fname, 'w')
    json_data = json.dumps(data)
    logfile.write(json_data)
    logfile.close()

def _load_data(fname):     
    final_fname = DATA_TEMP_SAVE_LOC + fname
    json_data=open(final_fname)
    data = json.load(json_data)      
    return data
    



def _gen_exp_key (cmb, mmp, ksf):
    exp_key = "cmb"+str(cmb)+ \
              "mmp"+str(mmp)+ \
              "ksf"+str(ksf)
              
    return exp_key

def _get_final_fname(fname, exp_key, wl_cfg, seed):
    subdir1 = EXP_DATADIR + wl_cfg + "/" + exp_key + "/"            
    subdir2 = subdir1 + "seed_"+str(seed)+"/"    
    fname_prefix = "HEVCTileSplitTest__"  + exp_key + "_" + str(NOC_H)+"_"+str(NOC_W)+"_"
    finalfname_completedtasks = subdir2 + fname_prefix + fname
    return finalfname_completedtasks


def _normalise_list(lst, norm_min=None, norm_max=None):    
    if norm_max == None:
        norm_max = np.max(lst)    
    if norm_min == None:
        norm_min = np.min(lst)    
    new_list = []
    for each_l in lst:   
        x = each_l     
        norm_val = (x-norm_min)/(norm_max-norm_min)
        new_list.append(norm_val)
    return new_list


def boxplot_colorize(bp, param_col, fc='#B8DCE6'):    
    i=0
    ## change outline color, fill color and linewidth of the boxes
    for box in bp['boxes']:
        # change outline color
        box.set( color='#000000', linewidth=1)
        # change fill color
        box.set( facecolor =  param_col)
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
        flier.set(marker='x', color='red', alpha=0.5)


def plot_CommsOverhead_and_GoPLateness_Combined(load_data=False, show_plots=False):
    data_fname_comms = "plot_comms.json"
    data_fname_gopl = "plot_gopl.json"
    
    ### get data ####
    alldata_perseed_commsoverhead = OrderedDict()
    alldata_perseed_goplateness = OrderedDict()
    
    if load_data==True:        
        alldata_perseed_commsoverhead = _load_data(data_fname_comms)
        alldata_perseed_goplateness = _load_data(data_fname_gopl) 
    else:    
            for each_ksf in KAUSHIK_COMMS_SCALE_FACTOR:
                                        
                alldata_perseed_commsoverhead[each_ksf] = None
                alldata_perseed_goplateness[each_ksf] = None
                           
                # which exp condition ?
                exp_key = _gen_exp_key(
                                       CMB_ID,
                                       MMP_ID,
                                       each_ksf
                                        )
                exp_lbl = each_ksf            
                            
                each_seed_data_comms = []
                each_seed_data_goplateness = []
                for each_seed in RANDOM_SEEDS:                
                    # get filename
                    finalfname_comms = _get_final_fname("_flwcompletedshort.js", exp_key, WORKLOAD_KEY, each_seed)
                    finalfname_gopsummary = _get_final_fname("_gopsopbuffsumm.js", exp_key, WORKLOAD_KEY, each_seed)                
                    try:        
                        print "getting : ", finalfname_comms
                        ## get file data                        
                        json_data=open(finalfname_comms)
                        file_data = json.load(json_data)
                        
                        flows_bl = [f[0] for f in file_data['flows_completed'] if f[2] in [1,15]]  
                        flows_payload = [_get_payload_from_flowbl(bl) for bl in flows_bl]                                
                        flows_bl_sum = np.sum(flows_payload)
                        
                        # save                                
                        each_seed_data_comms.append(flows_bl_sum)  
                        
                        
                        print "getting : ", finalfname_gopsummary
                        ## get file data
                        json_data=open(finalfname_gopsummary)
                        file_data = json.load(json_data)
                                                        
                        gop_lateness_dist = [g['gop_execution_lateness'] for gid, g in file_data.iteritems()]
                        
                        # save                                
                        each_seed_data_goplateness.extend(gop_lateness_dist)
                                                        
                    except Exception, e:                    
                        tb = traceback.format_exc()
                        print tb                    
                        sys.exit(e)            
                
                alldata_perseed_commsoverhead[each_ksf] = each_seed_data_comms
                alldata_perseed_goplateness[each_ksf] = each_seed_data_goplateness
    
    # save data
    if load_data==False:
        _save_data(data_fname_comms, alldata_perseed_commsoverhead)
        _save_data(data_fname_gopl, alldata_perseed_goplateness)
    
    if show_plots==False:
        return
            
    ### plot data ####
    fig, ax1 = plt.subplots()
    fig.canvas.set_window_title('plot_GopL_CommsOvh_Combined')    
                    
    ydata_comms = [np.mean(alldata_perseed_commsoverhead[str(k)]) for k  in KAUSHIK_COMMS_SCALE_FACTOR]
    ydata_gopl = [alldata_perseed_goplateness[str(k)] for k  in KAUSHIK_COMMS_SCALE_FACTOR]
    xdata = np.arange(len(KAUSHIK_COMMS_SCALE_FACTOR))
    
    ax1.boxplot(ydata_gopl, positions=xdata)
    ax1.set_ylabel('GoPLateness')
    
    ax2 = ax1.twinx()    
    
    ax2.plot(xdata, ydata_comms, 'r-', linewidth=2)
    ax2.set_ylabel('CommOverhead', color='r')
    
    print "---"
        
    plt.grid(axis='y',b=True, which='major', color='k', linestyle='--', alpha=0.3)
    plt.grid(axis='y',b=True, which='minor', color='k', linestyle='-', alpha=0.2)
    plt.minorticks_on()
    
    
    ax1.tick_params(axis = 'y', which = 'both')            
    ax2.tick_params(axis = 'y', which = 'both')
    
    #plt.ticklabel_format(style='sci', axis='x', scilimits=(0,0), labelsize=20)
    #plt.tick_params(axis='both', which='major', labelsize=16)
    #plt.tick_params(axis='both', which='minor', labelsize=16)
    #plt.rc('font', **{'size':'16'})
    #ax.set_xticks(ind+0.5)
    
    ax1.set_xticks(xdata)
    ax1.set_xticklabels(KAUSHIK_COMMS_SCALE_FACTOR, rotation=40)
    


def _get_payload_from_flowbl(flw_bl):
    p = SimParams.NOC_PERIOD
    payload = (16.0*(flw_bl - (70.0*p*p)))/p
    return payload  






   
    

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
            

        
            
def func_fit_data(x, a, b, c):
    return a * np.exp(-b * x) + c        
        





       

###################################
#    HELPERS
###################################

          



###################################
#    MAIN
###################################
if __name__ == "__main__":
    
    plot_CommsOverhead_and_GoPLateness_Combined(load_data=True, show_plots=True)

    plt.show()






class LogFormatterTeXExponent(pylab.LogFormatter, object):
    """Extends pylab.LogFormatter to use 
    tex notation for tick labels."""
    
    def __init__(self, *args, **kwargs):
        super(LogFormatterTeXExponent, 
              self).__init__(*args, **kwargs)
        
    def __call__(self, *args, **kwargs):
        """Wrap call to parent class with 
        change to tex notation."""
        label = super(LogFormatterTeXExponent, 
                      self).__call__(*args, **kwargs)
        label = re.sub(r'e(\S)0?(\d+)', 
                       r'\\times 10^{\1\2}', 
                       str(label))
        label = "$" + label + "$"
        return label
