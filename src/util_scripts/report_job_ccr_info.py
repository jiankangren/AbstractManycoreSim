import pprint
import sys
import math, random
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import scipy.stats
from matplotlib.colors import ListedColormap, NoNorm
from matplotlib import mlab
from itertools import cycle # for automatic markers

import matplotlib.cm as cm
from matplotlib.font_manager import FontProperties

import json

SORTED_RESOLUTIONS = ["2160x3840",
                      "1440x2560", 
                      "1080x1920",
                        "720x1280",
                        "480x854",
                        "360x640",
                        "288x512"]


def _get_data(fname):
    json_data=open(fname)
    file_data = json.load(json_data)     
    return file_data        
    

def show_ccr_per_resolution(jdata):
    print "show_ccr_per_resolution :: Enter"
    res_ccr_data = {}
    for each_res, ccr_samples in jdata.iteritems():        
        res_ccr_data[each_res] = [r["ccr"] for r in ccr_samples]
    
    # show stats
    for k in SORTED_RESOLUTIONS:
        if k in res_ccr_data:
            print "%s \t %f \t %f" % (k, np.min(res_ccr_data[k]), np.max(res_ccr_data[k])) 
                        

def show_maxploadratio_per_resolution(jdata):
    print "show_maxploadratio_per_resolution :: Enter"
    res_maxploadratio_data = {}
    for each_res, ccr_samples in jdata.iteritems():        
        res_maxploadratio_data[each_res] = [r["max_wccc"]/r["max_bl"] for r in ccr_samples]
    
    # show stats
    for k in SORTED_RESOLUTIONS:        
        print "%s \t %f \t %f" % (k, np.min(res_maxploadratio_data[k]), np.max(res_maxploadratio_data[k])) 


def show_maxpload_per_resolution(jdata):
    print "show_maxploadratio_per_resolution :: Enter"
    res_maxploadratio_data = {}
    for each_res, ccr_samples in jdata.iteritems():        
        res_maxploadratio_data[each_res] = [r["max_wccc"] for r in ccr_samples]
    
    # show stats
    for k in SORTED_RESOLUTIONS:        
        print "%s \t %f \t %f" % (k, np.min(res_maxploadratio_data[k]), np.max(res_maxploadratio_data[k]))



#############################
# MAIN
#############################
#fname = "Z:/MCASim/experiment_data/hevc_tile_mapping_varCCR/WL2/ac0mp0pr0cmb914mmp0ccrs01/seed_80505/HEVCTileSplitTest__ac0mp0pr0cmb914mmp0ccrs01_6_6__jobccrinfo.js"

fname = "../experiment_data/hevc_tile_mapping_wMemPSel/WL1/ac0mp0pr0cmb911mmp37/seed_80505/HEVCTileSplitTest__ac0mp0pr0cmb911mmp37_8_8__jobccrinfo.js"

jdata =  _get_data(fname)
show_ccr_per_resolution(jdata)
#print "---"
#show_maxploadratio_per_resolution(jdata)
#print "---"
#show_maxpload_per_resolution(jdata)
