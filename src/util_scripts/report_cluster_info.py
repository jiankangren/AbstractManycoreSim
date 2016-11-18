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


def _swap_res_lbls(res_list = SORTED_RESOLUTIONS):
    result=[]
    for r in res_list:
        x1,x2 = r.split("x")
        result.append("%sx%s"%(x2,x1))
    return result
    


def _get_data(fname):
    json_data=open(fname)
    file_data = json.load(json_data)     
    return file_data        
    

def get_cluster_size_per_gop(jdata_gops, jdata_obuff):
    all_data_pes = {}
    
    # put tasks into resolutions
    for each_gid, g_data in jdata_gops.iteritems():
        strm_res = g_data["strm_res"]
        if strm_res not in all_data_pes:
            all_data_pes[strm_res] = {}
            all_data_pes[strm_res][int(each_gid)] = set()
        else:
            all_data_pes[strm_res][int(each_gid)] = set()
            
    # put task pe sets into gops    
    for each_t in jdata_obuff:
        t_gid = each_t["ugid"]
        t_pe = each_t["pe"]
        for each_strm_res_k, each_strm_res_gops in all_data_pes.iteritems():
            for each_gid_k, g_val in each_strm_res_gops.iteritems():
                if each_gid_k == t_gid:                    
                    all_data_pes[each_strm_res_k][each_gid_k].update(set([t_pe]))
    
    #pprint.pprint(all_data)
    return all_data_pes


def get_pri_vs_mmcs(jdata_obuff, jdata_mmcsel):
    task_dict = {}
    # construct task-level dict
    for each_t in jdata_obuff:
        t_pri = each_t["pri"]
        t_id = each_t["id"]
        t_gid = each_t["ugid"]
        task_dict[t_id] = {
                           'mmc_id' : None,
                           'pri' : t_pri,
                           'gid' : t_gid                                  
                           }     
    # populate mmc id
    for each_tid, each_mmcid in  jdata_mmcsel.iteritems():
        task_dict[each_tid]['mmc_id'] = each_mmcid
        
    
    return task_dict


        

def plot_cluster_size(cluster_data, lbl):
    all_data_tuples = []    
    for each_strm_res_k, each_strm_res_gops in cluster_data.iteritems():
        res_pixels_hw = [int(p) for p in each_strm_res_k.split("x")]
        res_pixels = res_pixels_hw[0]*res_pixels_hw[1]
        for each_gid_k, g_val in each_strm_res_gops.iteritems():
            all_data_tuples.append((res_pixels, len(g_val)))
    
    f = plt.figure()    
    plt.scatter(*zip(*all_data_tuples))
    plt.title(lbl)
    

def plot_gid_vs_mmcid(task_data, lbl):
    all_data_tuples = []
    
    mmc_count = {}
    for each_tid, each_t_data in task_data.iteritems():
        all_data_tuples.append((each_t_data['gid'], int(str(each_t_data['mmc_id']).replace("MMC",""))  ))
        
        if each_t_data['mmc_id'] not in mmc_count:
            mmc_count[each_t_data['mmc_id']] = 1
        else:
            mmc_count[each_t_data['mmc_id']] += 1
        
    
    pprint.pprint(mmc_count)
    
    f = plt.figure()    
    plt.scatter(*zip(*all_data_tuples), marker='x')
    plt.title(lbl)
    plt.minorticks_on()
    plt.grid(True, which='both')
    
    



#############################
# MAIN
#############################
lbl = "ac0mp0pr0cmb914mmp1"

#gop_fname = "Z:/MCASim/experiment_data/hevc_tile_mapping_wMemPSel_HighCCR/WL2/ac0mp0pr0cmb914mmp38/seed_26044/HEVCTileSplitTest__%s_8_8__gopsopbuffsumm.js" % ( lbl)
#obuff_fname = "Z:/MCASim/experiment_data/hevc_tile_mapping_wMemPSel_HighCCR/WL2/ac0mp0pr0cmb914mmp38/seed_26044/HEVCTileSplitTest__%s_8_8__obuff.js"  % ( lbl)
#smartmmcid_fname = "Z:/MCASim/experiment_data/hevc_tile_mapping_wMemPSel_HighCCR/WL2/ac0mp0pr0cmb914mmp38/seed_26044/HEVCTileSplitTest__%s_8_8__smartmmcid.js"  % ( lbl)


gop_fname = "C:/Users/Rosh/Documents/EngD/Work/AbstractSimulator/Multicore_Abstract_Sim/src/experiment_data/hevc_tile_mapping_wMemPSel_HighCCR/WL2/ac0mp0pr0cmb914mmp1/seed_80505/HEVCTileSplitTest__%s_8_8__gopsopbuffsumm.js" % ( lbl)
obuff_fname = "C:/Users/Rosh/Documents/EngD/Work/AbstractSimulator/Multicore_Abstract_Sim/src/experiment_data/hevc_tile_mapping_wMemPSel_HighCCR/WL2/ac0mp0pr0cmb914mmp1/seed_80505/HEVCTileSplitTest__%s_8_8__obuff.js"  % ( lbl)
smartmmcid_fname = "C:/Users/Rosh/Documents/EngD/Work/AbstractSimulator/Multicore_Abstract_Sim/src/experiment_data/hevc_tile_mapping_wMemPSel_HighCCR/WL2/ac0mp0pr0cmb914mmp1/seed_80505/HEVCTileSplitTest__%s_8_8__smartmmcid.js"  % ( lbl)


# gop_fname = "C:/Users/Rosh/Documents/EngD/Work/AbstractSimulator/Multicore_Abstract_Sim/src/experiment_data/hevc_tile_mapping_wMemPSel/WL1/ac0mp0pr0cmb914mmp0/seed_1234/HEVCTileSplitTest__ac0mp0pr0cmb914mmp0_8_8__gopsopbuffsumm.js"
# obuff_fname = "C:/Users/Rosh/Documents/EngD/Work/AbstractSimulator/Multicore_Abstract_Sim/src/experiment_data/hevc_tile_mapping_wMemPSel/WL1/ac0mp0pr0cmb914mmp0/seed_1234/HEVCTileSplitTest__ac0mp0pr0cmb914mmp0_8_8__obuff.js"

#gop_jdata =  _get_data(gop_fname)
obuff_jdata =  _get_data(obuff_fname)
smartmmc_jdata = _get_data(smartmmcid_fname)


#cluster_data_pes  = get_cluster_size_per_gop(gop_jdata, obuff_jdata)
cluster_data_mmcs = get_pri_vs_mmcs(obuff_jdata, smartmmc_jdata)


#plot_cluster_size(cluster_data_pes, lbl)

plot_gid_vs_mmcid(cluster_data_mmcs, lbl)

plt.show()