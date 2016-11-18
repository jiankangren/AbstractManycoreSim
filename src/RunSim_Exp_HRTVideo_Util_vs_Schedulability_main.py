import sys, os, csv, pprint, math
import argparse
import subprocess
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

from libProcessingElement.LocalScheduler import LocalRRScheduler,    \
                        LocalEDFScheduler, \
                        LocalMPEG2FrameEDFScheduler, \
                        LocalMPEG2FrameListScheduler, \
                        LocalMPEG2FramePriorityScheduler, \
                        LocalMPEG2FramePriorityScheduler_WithDepCheck 

from libResourceManager.RMTypes import RMTypes
from libProcessingElement.CPUTypes import CPUTypes
from libResourceManager.Mapper.MapperTypes import MapperTypes
from libTaskDispatcher.TDTypes import TDTypes

from libResourceManager.AdmissionControllerOptions import AdmissionControllerOptions
from libMappingAndScheduling.SemiDynamic.TaskMappingSchemes import TaskMappingSchemes
from libMappingAndScheduling.SemiDynamic.TaskSemiDynamicPrioritySchemes import TaskSemiDynamicPrioritySchemes
from libMappingAndScheduling.SemiDynamic.TaskMappingAndPriAssCombinedSchemes import TaskMappingAndPriAssCombinedSchemes 

from util_scripts.resolution_combos import generate_resolution_combos, _reslist_to_string

from SimParams import SimParams

import Multicore_MPEG_Model as MMMSim


GET_RESARR_FROM_FILE = True

NUM_WORKFLOWS = range(8, 17, 2)
#NUM_WORKFLOWS = [12]
NUM_NODES = [2,4,8,16,32]
NOC_XY = [(2,1), (2,2), (2,4), (2,8), (2,16)]

def _makeDir(directory):
    try:
        os.stat(directory)
    except:
        os.makedirs(directory)

def _check_file_exists(fname):
    return os.path.exists(fname)


def _get_res_array_from_file(fname, cc, wfgenseed):
    key = str(cc)+"_"+str(wfgenseed)    
    json_data=open(fname)
    file_data = json.load(json_data)
    
    res_array = file_data[key]['res_array']
    
    return res_array
    

def _get_custom_wf_cc1772928_wfs7():
    entry = {
                 "cc" : 1772928,
                 "cc_uid": 0,
                 "avg_cc": 253275.428571,
                 "res_list" : [[720, 576], [240,180], [480,576], [720,576], [528,576], [480,576], [240,180]],
                 'res_list_len' : 7,
                 }    
    return entry

def _remove_custom_wf(res_combos_list, cc, res_list_len):
    
    target_ix = None
    for ix, each_entry in enumerate(res_combos_list):
        #print each_entry['cc'], each_entry['res_list_len']
        if (each_entry['cc'] == cc) and (each_entry['res_list_len'] == res_list_len):
            target_ix= ix
            break;
    
    del res_combos_list[target_ix]
        
    return res_combos_list, target_ix

############################################################################
############################################################################
##                MAIN SCRIPT SECTION
############################################################################
############################################################################

sys.setrecursionlimit(1500)

# collect command line params
parser = argparse.ArgumentParser(__file__, description="Run specified experiment on abstract simulator")

parser = argparse.ArgumentParser(__file__, description="Run specified experiment on abstract simulator")
parser.add_argument("--ac_type", help="admission control type", type=int, default=-1)
parser.add_argument("--mp_type", help="mapping type", type=int, default=-1)
parser.add_argument("--pr_type", help="pri assignment type", type=int, default=-1)
parser.add_argument("--cmbmppri_type", help="combined mapping and pri-assignment type", type=int, default=-1)
parser.add_argument("--forced_seed", help="forced seed", type=int, default=-1)


args = parser.parse_args()

####################################
## check which experiment to run ##
####################################
#runSim_Simple()

rand_seed = 1234
#reject_cc_list = [1433664,1800504,2254104]
reject_cc_list = [1800504]

# get list of random seeds :
#res_arr = [(720,576), (544,576), (528,576), (480,576), (426,240), (320,240), (240,180), (230,180)]
#max_num_wfs = 10
#res_combos = generate_resolution_combos(max_num_wfs-1,res_arr,rand_seed, sampled=True)

res_arr = [(720,576), (544,576), (528,576), (480,576), (426,240), (320,240), (240,180), (230,180)]

max_num_wfs = 10
res_combos = generate_resolution_combos(max_num_wfs-1,res_arr,rand_seed, 
                                        sampled=True, 
                                        reduced_samples=10, 
                                        total_samples=20000,
                                        lower_limit=80000)


# remove specific wf
res_combos, target_ix = _remove_custom_wf(res_combos, 1800504, 9)

# add custom wf
res_combos.insert(target_ix, _get_custom_wf_cc1772928_wfs7())


for each_rescombo in res_combos:
    
    if (GET_RESARR_FROM_FILE == True):
        res_array = _get_res_array_from_file('MOGATestbenches/track_cc_res_array.js',each_rescombo['cc'],  args.forced_seed)
    else:
        res_array = each_rescombo['res_list']
        
    num_wfs = len(each_rescombo['res_list'])
    cc = each_rescombo['cc']
    cc_uid = each_rescombo['cc_uid']
    
    if cc in reject_cc_list:
        continue
    
    res_array_string = _reslist_to_string(res_array)
    
#     res_array = [(426, 240), (720, 576), (480, 576), (528, 576), (720, 576), (480, 576)]
#     num_wfs = 6
#     cc = 1788768
    
    pprint.pprint(res_array)
    print num_wfs

    cmd = 'python -u RunSim_Exp_HRTVideo_Util_vs_Schedulability.py ' + \
            " --num_wfs=" + str(num_wfs) + \
            " --ac_type=" + str(args.ac_type) + \
            " --mp_type=" + str(args.mp_type) + \
            " --pr_type=" + str(args.pr_type) + \
            " --cmbmppri_type=" + str(args.cmbmppri_type) + \
            " --cc_uid=" + str(cc) + "-" + str(cc_uid) + \
            " --res_list=" + res_array_string + \
            " --forced_seed=" + str(args.forced_seed)
                        
    print cmd        
    subprocess.call(cmd , shell=True)
    # wait a bit
    time.sleep(3)
    
    
    
    
    
    
    
    
    
    
    
    
