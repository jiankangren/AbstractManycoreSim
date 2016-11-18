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

from libResourceManager.AdmissionControllerOptions import AdmissionControllerOptions
from SimParams import SimParams


import Multicore_MPEG_Model as MMMSim


NUM_NODES = 9
EXP_DATA_DIR = "../experiment_data/mapping_and_pri_schemes"
NUM_WFS = 7

###################################################################################################
#    draw timeline
###################################################################################################
    
def plot_TaskExecTimeline(fname=None, m=None,p=None, wf=None, seed=None, all_seeds=False):                
    
    if (m==None) and (p==None) and (wf==None) and (seed==None):   
        sys.exit("plot_TaskExecTimeline:: error")    
    
    nodetaskexec_data = []
    
    colors = plt.get_cmap('jet')(np.linspace(0, 1.0, NUM_WFS))
    
    # get file data    
    if (all_seeds == False):
        if(fname == None):
            # get data        
            FNAME_PREFIX = "Exp_m"+str(m) + "_p"+str(p) + "_"    
            fname = EXP_DATA_DIR + "/seed_" + str(seed) + "/" + FNAME_PREFIX + 'wf'+str(wf)+'_cores'+str(NUM_NODES) + "_obuff.js"    
            json_data=open(fname)
            nodetaskexec_data = json.load(json_data)
        else:
            # fname supplied
            json_data=open(fname)
            nodetaskexec_data = json.load(json_data)
        
    
    # draw timeline
    plt.figure()
    plt.title('plot_TaskExecTimeline - ' + fname)
    plt.axes()
    
    # for each node draw the execution sequence    
    for each_node_key,each_node_val in nodetaskexec_data.iteritems():
        
        for ix,each_entry in enumerate(each_node_val):
            
            if(each_entry['e'] == "run"):            
                if(ix < len(each_node_val)):
                
                    line_x0 = each_node_val[ix]['t']
                    line_x1 = each_node_val[ix+1]['t']            
                    line_y0 = each_node_key
                    line_y1 = each_node_key
                    line_width = line_x1 -line_x0
                    
                    wf_id = each_node_val[ix]['wf_strm_ugid'][0]
                                        
                    #line = plt.Line2D((line_x0, line_x1), (line_y0, line_y1), lw=5, color="#33CCCC")                   
                    line = plt.Line2D((line_x0, line_x1), (line_y0, line_y1), lw=5, color=colors[wf_id])
                    plt.gca().add_line(line)
                    annotation = str(each_node_val[ix]['tid']) + "," + each_node_val[ix]['ft']
                    plt.text((line_x0+(line_width/2)), line_y0, annotation, fontsize=8, zorder=12)
                    
                    # is ix+1 the end ??
                    if(each_node_val[ix+1]['e'] == "end"):
                        end_line = plt.Line2D((line_x1, line_x1), (line_y0, line_y1), lw=5, color='red', marker="x", markersize=10, zorder=10)                    
                        plt.gca().add_line(end_line)
                    # if not , is the x+1 another task ??
                    elif(each_node_val[ix+1]['e'] == "run"):
                        if(each_node_val[ix+1]['tid'] != each_node_val[ix]['tid']):
                            interrupt_line = plt.Line2D((line_x1, line_x1), (line_y0, line_y1), lw=7, color='green', marker="^", markersize=10, zorder=10)                    
                            plt.gca().add_line(interrupt_line)
                        

    plt.axis('auto')
    plt.minorticks_on()    
    plt.grid(True, which='both')



###################################
#    HELPERS
###################################





###################################
#    MAIN
###################################

#plot_TaskExecTimeline(fname="../experiment_data/hrt_video/scenario_4/SCV4_NOCAC_IMPROVEDM_3_3_test__nodetaskexectime.js", m=-1,p=-1, wf=-1, seed=-1, all_seeds=False)
#plot_TaskExecTimeline(fname="../experiment_data/hrt_video/scenario_4/SCV4_NOAC_LUM_3_3_test__nodetaskexectime.js", m=-1,p=-1, wf=-1, seed=-1, all_seeds=False)

#plot_TaskExecTimeline(fname="../experiment_data/closedloop_vs_openloop/OL_2_2_test__nodetaskexectime.js", m=-1,p=-1, wf=-1, seed=-1, all_seeds=False)


plot_TaskExecTimeline(fname="../experiment_data/hevc_test/seed_1234/test__3_3_test__nodetaskexectime.js", m=-1,p=-1, wf=-1, seed=-1, all_seeds=False)

print "finished"

plt.show()

