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

import seaborn as sns
matplotlib.rc("lines", markeredgewidth=0.5)

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




def plot_GoPLateness_Multiple(fname_list, lbl_list):
    
    all_data = []
    
    for each_fname, each_lbl in zip(fname_list, lbl_list):
        json_data=open(each_fname)
        file_data = json.load(json_data)                    
        gop_lateness_dist = [g['gop_execution_lateness'] for gid, g in file_data.iteritems()]
        #gop_lateness_dist = [g['gop_execution_lateness'] for gid, g in file_data.iteritems() if g['gop_execution_lateness'] > 0]
        gop_lateness_dist_mean = np.mean(gop_lateness_dist)
        gop_lateness_dist_sum = np.sum(gop_lateness_dist)
    
        all_data.append(gop_lateness_dist)
    
    print "-- plot_GoPLateness_Multiple --"    
    print "mean gop lateness list : ", np.mean(all_data, axis=1)
    
    fig = plt.figure()
    fig.canvas.set_window_title('plot_GoPLateness_Multiple-boxplot')
    ax = plt.subplot(111)
    pos=np.arange(len(lbl_list))
    width=0.13
    bps = plt.boxplot(all_data,0, 'x', positions=pos, widths=width, patch_artist=True)
    
    
            
    plt.grid(axis='y',b=True, which='major', color='k', linestyle='--', alpha=0.2)
    plt.grid(axis='y',b=True, which='minor', color='k', linestyle='--', alpha=0.2)
    
    ax.tick_params(axis = 'y', which = 'major')        
    ax.set_ylabel('Job lateness (s)\n(logarithmic scale)', fontsize=14, multialignment='center')
    ax.set_xlabel('experiment list', fontsize=14)        
    ax.xaxis.major.formatter._useMathText = True    
    ax.set_xticks(pos)
    ax.set_xticklabels(lbl_list)    
    #plt.yscale('symlog')
   
    print "----"
           
       

###################################
#    HELPERS
###################################

          



###################################
#    MAIN
###################################
if __name__ == "__main__":
    
    fname_list = [
                  "../experiment_data/hevc_tile_mapping_wMemPSel/WL1/ac0mp0pr0cmb914mmp37_variable_fps/seed_80505/HEVCTileSplitTest__ac0mp0pr0cmb914mmp37_8_8__gopsopbuffsumm.js",
                  "../experiment_data/hevc_tile_mapping_wMemPSel/WL1/ac0mp0pr0cmb914mmp37/seed_80505/HEVCTileSplitTest__ac0mp0pr0cmb914mmp37_8_8__gopsopbuffsumm.js",
                  ]
    
    lbl_list = [
                "variable fps", "normal"
                ]
    
    plot_GoPLateness_Multiple(fname_list, lbl_list)
       
    
    plt.show()


