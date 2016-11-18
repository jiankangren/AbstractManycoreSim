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


###################################################################################################
#    draw timeline
###################################################################################################
    
def plot_FlowExecTimeline(fname=None):                
    
    nodeflwexec_data = []
    
    # get file data    
    # fname supplied
    json_data=open(fname)
    file_data = json.load(json_data)
    
    # draw timeline
    plt.figure()
    plt.title('plot_FlowExecTimeline - ' + fname)
    ax = plt.axes()
        
    for each_flw in file_data:
        flw_start_time =  each_flw['st']
        flw_end_time = each_flw['et']
        
        
        line_x0 = each_flw['st']
        line_x1 = each_flw['et']       
        line_y0 = each_flw['src']
        line_y1 = each_flw['dst']
        line_width = line_x1 -line_x0
        
        if(each_flw['type']==0):
            color='#FF0000'
        elif(each_flw['type'] in [1,15]):
            color='#00CC00'
        elif(each_flw['type']==2):
            color='#0033CC'
        elif(each_flw['type']==3):
            color='#000000'
        elif(each_flw['type']==4):
            color='#FFFF00'
        elif(each_flw['type']==5):
            color='#FF66FF'
                    
        line = plt.Line2D((line_x0, line_x1), (line_y0, line_y1), lw=5, color=color)                   
        plt.gca().add_line(line)
        
        #annotation = str(each_flw['pri']) + "," + str(each_flw['src_tid']) + "->" + str(each_flw['dst_tid'])
        #plt.text((line_x0+(line_width/2)), line_y0, annotation, fontsize=6, zorder=12)
   

    plt.axis('auto')
    plt.minorticks_on()    
    plt.grid(True, which='both')



###################################
#    HELPERS
###################################


###################################
#    MAIN
###################################

#plot_FlowExecTimeline(fname="../experiment_data/closedloop_vs_openloop/CLwoIB_7_7_test__flwcompleted.js")
plot_FlowExecTimeline(fname="../experiment_data/hevc_test/seed_1234/test__3_3_test__flwcompleted.js")


#plot_FlowExecTimeline(fname="../experiment_data/closedloop_vs_openloop/CLwoIB_6_6_test__flwcompleted.js")
#plot_FlowExecTimeline(fname="../experiment_data/closedloop_vs_openloop/OL_6_6_test__flwcompleted.js")

print "finished"

plt.show()

