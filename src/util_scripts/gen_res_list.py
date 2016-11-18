import sys, os, csv, pprint, math
import argparse

import numpy as np
import random
import shutil
import time
import json

## uncomment when running under CLI only version ##
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import scipy.stats
from matplotlib.colors import ListedColormap, NoNorm
from matplotlib import mlab
from itertools import cycle # for automatic markers

import matplotlib.cm as cm
from matplotlib.font_manager import FontProperties

RUN=False

MAX_WFS = 24

WF_NUM_5 = 5

MAX_WF_1_12 = int(float(MAX_WFS) * (1.0/12.0))
MAX_WF_1_8 = int(float(MAX_WFS) * (1.0/8.0))
MAX_WF_1_6 = int(float(MAX_WFS) * (1.0/6.0))
MAX_WF_1_5 = int(round(float(MAX_WFS) * (1.0/5.0)))
MAX_WF_1_4 = int(float(MAX_WFS) * (1.0/4.0))
MAX_WF_1_3 = int(float(MAX_WFS) * (1.0/3.0))
MAX_WF_1_2 = int(float(MAX_WFS) * (1.0/2.0))


DVB_RESOLUTIONS = [(3840,2160),(2560,1440), 
                   (1920,1080),(1280,720),
                   (854,480),(640,360),
                   (512,288),
                  ]


# TEST_WORKLOAD_CONFIGS = {                        
#                        # low resolution
#                        'WL1' : [(512,288)]*MAX_WF_1_2 + [(512,288)]*MAX_WF_1_2 + [(640,360)]*MAX_WF_1_2,
#                        
#                        # med resolution
#                        'WL2' : [(640,360)]*MAX_WF_1_12 + [(854,480)]*MAX_WF_1_12 + [(1280,720)]*MAX_WF_1_6 + [(1920,1080)]*MAX_WF_1_6 + \
#                                 [(3840,2160)] * MAX_WF_1_8 + [(2560,1440)] * MAX_WF_1_8, 
#                                     
#                        #'WL2' : [(640,360)]*MAX_WF_1_6 + [(854,480)]*MAX_WF_1_6 + [(1280,720)]*MAX_WF_1_2 + [(1920,1080)]*MAX_WF_1_2,
#                                               
#                        # high resolution, mixed
#                        'WL3' :  [(1920,1080)]*MAX_WF_1_8 + [(2560,1440)]*MAX_WF_1_4 + [(3840,2160)]*MAX_WF_1_6,
#                        
#                        # random workloads - not useful                          
#                        'WL4' : None,               
#                        
#                        'TEST_WL' : [(3840,2160),(2560,1440), 
#                                        (1920,1080),(1280,720),
#                                        (854,480),(640,360),
#                                        (512,288),
#                                        ]                                                                                 
#                        }



TEST_WORKLOAD_CONFIGS = {                        
                       # resolutions, mixed
                       'WL1' : [(512,288)]*MAX_WF_1_12 + [(640,360)]*MAX_WF_1_12 + [(854,480)]*MAX_WF_1_12 + 
                                [(1280,720)]*MAX_WF_1_12 + [(1920,1080)]*MAX_WF_1_8 + \
                                [(3840,2160)] * MAX_WF_1_8 + [(2560,1440)] * MAX_WF_1_8, 
                       
                       # resolutions, mixed
                       'WL2' : [(512,288)]*MAX_WF_1_8 + [(640,360)]*MAX_WF_1_8 + [(854,480)]*MAX_WF_1_8 + 
                                [(1280,720)]*MAX_WF_1_8 + [(1920,1080)]*MAX_WF_1_6 + \
                                [(3840,2160)] * MAX_WF_1_6 + [(2560,1440)] * MAX_WF_1_6, 
                                              
                       # resolutions, mixed
                       'WL3' :  [(512,288)]*MAX_WF_1_6 + [(640,360)]*MAX_WF_1_6 + [(854,480)]*MAX_WF_1_6 + 
                                [(1280,720)]*MAX_WF_1_6 + [(1920,1080)]*MAX_WF_1_4 + \
                                [(3840,2160)] * MAX_WF_1_4 + [(2560,1440)] * MAX_WF_1_4, 
                       
                       
                       # high resolution, mixed
                       'WL4' :  [(512,288)]*MAX_WF_1_4 + [(640,360)]*MAX_WF_1_4 + [(854,480)]*MAX_WF_1_4 + 
                                [(1280,720)]*MAX_WF_1_4 + [(1920,1080)]*MAX_WF_1_4 + \
                                [(3840,2160)] * MAX_WF_1_4 + [(2560,1440)] * MAX_WF_1_4,
                                
                       
                       # random workloads - not useful                          
                       'WL5' : None,       
                       
                       # high resolution, mixed
                       #'WL5' : [(640,360)]*MAX_WF_1_6 + [(854,480)]*MAX_WF_1_6 + [(1280,720)]*MAX_WF_1_2 + [(1920,1080)]*MAX_WF_1_2,    
                       
                       'TEST_WL' : [(3840,2160),(2560,1440), 
                                       (1920,1080),(1280,720),
                                       (854,480),(640,360),
                                       (512,288),
                                       ]                                                                                 
                       }


def get_res_list(config):
    wfs_list = []
    if config == 'WL5':         
        for i in xrange(MAX_WFS):
            wf = random.choice(DVB_RESOLUTIONS)
            wfs_list.append(wf)
    else:
        fixed_wfs = TEST_WORKLOAD_CONFIGS[config]
        np.random.shuffle(fixed_wfs) # shuffle in place
        wfs_list = fixed_wfs
    
    return wfs_list


def calc_total_workload_level(res_list):
    total_wl_level = []
    for each_res in res_list:
        vid_cc = each_res[0]*each_res[1]
        total_wl_level.append(vid_cc)
    
    return (total_wl_level, np.sum(total_wl_level))



######################
# MAIN
######################

if RUN == True:
    all_workload_levels = []
    sorted_config_keys = ['WL1','WL2', 'WL3', 'WL4', 'TEST_WL']
    
    for ix,each_config_k in enumerate(sorted_config_keys):
        res_list = get_res_list(each_config_k)
        print each_config_k, "::"
        print "res_list: ", res_list    
        workload = calc_total_workload_level(res_list)[1]
        print "workload: ", workload
        print "len(res_list) :", len(res_list)
        all_workload_levels.append(workload)
        
        percentage_increase=0.0
        if len(all_workload_levels)>1:
            diff = float(all_workload_levels[ix]) - float(all_workload_levels[0])
            percentage_increase = (diff/float(all_workload_levels[0]))*100
            
        print "percentage_increase :: ", percentage_increase
        print "----------------------------"





    
        
    
    