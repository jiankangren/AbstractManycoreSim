import sys, os, csv, pprint, math

#sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

## uncomment when running under CLI only version ##
#import matplotlib
#matplotlib.use('Agg')

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


from analyse_results.AnalyseResults_Exp_HEVCSplitTiles_workloadDist_vs_Lateness_varWorkload import _gen_exp_key
from analyse_results.AnalyseResults_Exp_HEVCSplitTiles_workloadDist_vs_Lateness_varWorkload import _get_final_fname
from analyse_results.AnalyseResults_Exp_HEVCSplitTiles_workloadDist_vs_Lateness_varWorkload import global_types_of_tests
from analyse_results.AnalyseResults_Exp_HEVCSplitTiles_workloadDist_vs_Lateness_varWorkload import global_workload_configs
from analyse_results.AnalyseResults_Exp_HEVCSplitTiles_workloadDist_vs_Lateness_varWorkload import _write_formatted_file

NOC_H = 6
NOC_W = 6

RANDOM_SEEDS_BATCH0=[81665, 33749, 43894, 26358, 80505]
RANDOM_SEEDS_BATCH1=[83660, 22817, 70263, 29917, 26044]
RANDOM_SEEDS_BATCH2=[5558, 76891, 42198, 18065, 22250]
RANDOM_SEEDS_BATCH3=[74076, 98652, 21149, 50399, 64217]
RANDOM_SEEDS_BATCH4=[44117, 57824, 42267, 83200, 99108]
RANDOM_SEEDS_BATCH5=[95928, 53864, 44289, 77379, 80521]
RANDOM_SEEDS_BATCH6=[87288, 21349, 68546, 74944, 94329]
RANDOM_SEEDS_BATCH7=[90611, 69799, 85870, 26771, 75638]

#RANDOM_SEEDS = [81665, 33749, 43894, 26358, 80505]

RANDOM_SEEDS = RANDOM_SEEDS_BATCH0 + \
               RANDOM_SEEDS_BATCH1 + \
               RANDOM_SEEDS_BATCH2 + \
               RANDOM_SEEDS_BATCH3 + \
               RANDOM_SEEDS_BATCH4 + \
               RANDOM_SEEDS_BATCH5 + \
               RANDOM_SEEDS_BATCH6 + \
               RANDOM_SEEDS_BATCH7


#RANDOM_SEEDS = RANDOM_SEEDS_BATCH0
print len(set(RANDOM_SEEDS))


#EXP_DATADIR = "../experiment_data/hevc_tilesplit_test/"
#EXP_DATADIR = "../experiment_data/hevc_tiles_mapping/"
EXP_DATADIR = "Z:/MCASim/experiment_data/hevc_tiles_mapping/"
#EXP_DATADIR = "Z:/MCASim/experiment_data/hevc_tiles_mapping_priassfcfs/"




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
#    HELPERS
###################################

          



###################################
#    MAIN
###################################

failed_seeds = []

for each_wrkld_cfg in global_workload_configs:
    for each_mapping_type in global_types_of_tests:               
        # which exp condition ?
        exp_key = _gen_exp_key(each_mapping_type['mp'],
                               each_mapping_type['pr'],
                               each_mapping_type['cmb'])
        exp_lbl = each_mapping_type['lbl']
        
        each_seed_data = []
        for each_seed in RANDOM_SEEDS:
            
            if each_seed not in failed_seeds:
                # get filename
                finalfname_gopsummary = _get_final_fname("_gopsopbuffsumm.js", exp_key, each_wrkld_cfg, each_seed)
                
                try:        
                    print "getting : ", finalfname_gopsummary
                    ## get file data                        
                    json_data=open(finalfname_gopsummary)
                    file_data = json.load(json_data)                    
                                                    
                except Exception, e:                    
                    #tb = traceback.format_exc()
                    #print tb
                    print "--> failed seed : " , each_seed
                    if each_seed not in failed_seeds: 
                        failed_seeds.append(each_seed)

print "finished !"
print " "
print "========================================"
print "failed seeds : ", failed_seeds

