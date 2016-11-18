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


from SimParams import SimParams



NUM_WORKFLOWS = range(8, 19, 1)
#NUM_WORKFLOWS = [9]
#NUM_NODES = [2,4,8,16,32]
NUM_NODES = 9
NOC_XY = [(2,1), (2,2), (2,4), (2,8), (2,16)]


IBUFF_TASKS_LATENESS_RATIO_RANGE    = [0.3, 0.7]
TQ_TASKS_LATENESS_RATIO_RANGE       = [0.3, 0.7]        

SEED = 26358

EXP_DATA_DIR = "../experiment_data/hrt_video/scenario_4"

RANDOM_SEED_LIST = \
[81665, 33749, 43894, 26358, 80505, \
 83660, 22817, 70263, 29917, 26044, \
 5558,  76891, 22250, 42198, 18065, \
 74076, 98652, 21149, 50399, 64217, \
 44117, 57824, 42267, 83200, 99108, \
 95928, 53864, 44289, 77379, 80521, \
 88117, 23327, 73337, 94064, 31982, \
 6878, 66093, 69541]

def _get_payload_from_flowbl(flw_bl, bytes_sf=1.0):
    p = SimParams.NOC_PERIOD
    payload = (16.0*(flw_bl - (70.0*p*p)))/p
    return float(payload)/float(bytes_sf)  


###################################################################################################
#    Computation cost vs. Communication cost
###################################################################################################
    
def plot_CompCost_vs_CommCost(fname=None, m=None,p=None, wf=None, seed=None, all_seeds=False):                
    
    if (m==None) and (p==None) and (wf==None) and (seed==None):   
        sys.exit("plot_CompCost_vs_CommCost:: error")    
    
    flwscompleted_file_data = []
    obuff_file_data = []
    
    # plot single seed ?    
    if (all_seeds == False):
        if(fname == None):
            # get execution costs        
            FNAME_PREFIX = "Exp_m"+str(m) + "_p"+str(p) + "_"    
            fname = EXP_DATA_DIR + "/seed_" + str(seed) + "/" + FNAME_PREFIX + 'wf'+str(wf)+'_cores'+str(NUM_NODES) + "_obuff.js"    
            json_data=open(fname)
            obuff_file_data = json.load(json_data)
            
            # get communication costs        
            FNAME_PREFIX = "Exp_m"+str(m) + "_p"+str(p) + "_"    
            fname = EXP_DATA_DIR + "/seed_" + str(seed) + "/" + FNAME_PREFIX + 'wf'+str(wf)+'_cores'+str(NUM_NODES) + "_flwcompleted.js"    
            json_data=open(fname)
            flwscompleted_file_data = json.load(json_data)
        else:
            # fname supplied
            json_data=open(fname[0])
            obuff_file_data = json.load(json_data)
            json_data=open(fname[1])
            flwscompleted_file_data = json.load(json_data)
        
    else:
        file_data = []
        for ix, each_seed in  enumerate(RANDOM_SEED_LIST):
                        
            # get execution costs        
            FNAME_PREFIX = "Exp_m"+str(m) + "_p"+str(p) + "_"    
            fname = EXP_DATA_DIR + "/seed_" + str(each_seed) + "/" + FNAME_PREFIX + 'wf'+str(wf)+'_cores'+str(NUM_NODES) + "_obuff.js"    
            json_data=open(fname)            
            temp_file_data = json.load(json_data)            
            obuff_file_data.extend(temp_file_data)
            
            # get communication costs        
            FNAME_PREFIX = "Exp_m"+str(m) + "_p"+str(p) + "_"    
            fname = EXP_DATA_DIR + "/seed_" + str(each_seed) + "/" + FNAME_PREFIX + 'wf'+str(wf)+'_cores'+str(NUM_NODES) + "_flwcompleted.js"    
            json_data=open(fname)            
            temp_file_data = json.load(json_data)
            flwscompleted_file_data.extend(temp_file_data)
            
    
    # plot box plots    
    f, axarr = plt.subplots(1, sharex=True)
    f.canvas.set_window_title('plot_CompCost_vs_CommCost - ')
    
    all_distributions = []
    iframe_execution_distribution = [t['cc'] for t in obuff_file_data if t['type'] == "I"]
    pframe_execution_distribution = [t['cc'] for t in obuff_file_data if t['type'] == "P"]
    bframe_execution_distribution = [t['cc'] for t in obuff_file_data if t['type'] == "B"]
    
    
    iframe_resptime_distribution = [t['et']-t['dt'] for t in obuff_file_data if t['type'] == "I"]
    pframe_resptime_distribution = [t['et']-t['dct'] for t in obuff_file_data if t['type'] == "P"]
    bframe_resptime_distribution = [t['et']-t['dct'] for t in obuff_file_data if t['type'] == "B"]
    
    #flow_commcost_distribution = [f['bl'] for f in flwscompleted_file_data  if f['tp'] in [1,15]]
    data_flow_commcost_distribution = [f[0] for f in flwscompleted_file_data['flows_completed'] if f[2] in [1,15]]
    #flow_totaltime_distribution = [f['et']-f['st'] for f in flwscompleted_file_data if f['type'] in [1,15]]
    #flow_totaltime_distribution = [f['l_var']+f['bl'] for f in flwscompleted_file_data if f['tp'] in [1,15]]
    data_flow_totaltime_distribution = [f[0]+f[1] for f in flwscompleted_file_data['flows_completed'] if f[2] in [1,15]]
    
    all_mem_flow_commcost_distribution = [f[0] for f in flwscompleted_file_data['flows_completed'] if f[2] not in [1,15]]    
    all_mem_flow_totaltime_distribution = [f[0]+f[1] for f in flwscompleted_file_data['flows_completed'] if f[2] not in [1,15]]
    
    memrd_flow_commcost_distribution = [f[0] for f in flwscompleted_file_data['flows_completed'] if f[2] in [8]]
    memrd_flow_totaltime_distribution = [f[0]+f[1] for f in flwscompleted_file_data['flows_completed'] if f[2] in [8]]
    
    memwr_flow_commcost_distribution = [f[0] for f in flwscompleted_file_data['flows_completed'] if f[2] in [9]]
    memwr_flow_totaltime_distribution = [f[0]+f[1] for f in flwscompleted_file_data['flows_completed'] if f[2] in [9]]
    
    #pprint.pprint(flow_totaltime_distribution)
    
    #communication_data_payload = [_get_payload_from_flowbl(bl,bytes_sf=10e7) for bl in data_flow_commcost_distribution]    
    #communication_mem_payload = [_get_payload_from_flowbl(bl,bytes_sf=10e7) for bl in all_mem_flow_commcost_distribution]
    
    #print "np.sum(communication_data_payload) : " , np.sum(communication_data_payload)
    #print "np.sum(communication_mem_payload) : ", np.sum(communication_mem_payload) 
    
    all_types_data = [iframe_execution_distribution,
                      pframe_execution_distribution,
                      bframe_execution_distribution,
                      
                      iframe_resptime_distribution,
                      pframe_resptime_distribution,
                      bframe_resptime_distribution,
                      
                      data_flow_commcost_distribution,
                      data_flow_totaltime_distribution,
                      
                      # data traffic (all)
                      #communication_data_payload,
                      #communication_mem_payload,
                      
                      # mem traffic (all)
                      #all_mem_flow_commcost_distribution,
                      #all_mem_flow_totaltime_distribution,
                      
                      # mem traffic (rd)
                      memrd_flow_commcost_distribution,
                      memrd_flow_totaltime_distribution,
                      
                      # mem traffic (wr)
                      memwr_flow_commcost_distribution,
                      memwr_flow_totaltime_distribution
                      
                 ]
    
    pprint.pprint([len(x) for x in all_types_data])
    
    boxpos=np.arange(len(all_types_data)) 
    axarr.boxplot(all_types_data, 0, 'x', whis=1, positions=boxpos, widths=0.8)
    
    x_labels = [
                  "i_cc",
                  "p_cc",
                  "b_cc",
                  
                  "i_tt",
                  "p_tt",
                  "b_tt",
                  
                  # data flow timings
                  "df_bl",
                  "df_r",
                  
                  # data traffic (all)
                  #communication_data_payload,
                  #communication_mem_payload,
                  
                  # mem traffic (all)
                  #all_mem_flow_commcost_distribution,
                  #all_mem_flow_totaltime_distribution,
                  
                  # mem traffic (rd)
                  "mrd_cc",
                  "mrd_r",
                  
                  # mem traffic (wr)
                  "mwr_cc",
                  "mwr_r",
                
                ]
                
    axarr.set_xticks(boxpos)
    axarr.set_xticklabels(x_labels)
    axarr.grid(True)            


        

    



        
        
        
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
if __name__ == '__main__':

    plot_CompCost_vs_CommCost(fname=["Z:/MCASim/experiment_data/hevc_mapping_highccr_test/WL2/ac0mp0pr0cmb914mmp0/seed_26358/HEVCTileSplitTest__ac0mp0pr0cmb914mmp0_8_8__obuff.js", 
                                     "Z:/MCASim/experiment_data/hevc_mapping_highccr_test/WL2/ac0mp0pr0cmb914mmp0/seed_26358/HEVCTileSplitTest__ac0mp0pr0cmb914mmp0_8_8__flwcompletedshort.js"], 
                              m=-1,p=-1, wf=-1, seed=-1, all_seeds=False)
    
    
#     plot_CompCost_vs_CommCost(fname=["../experiment_data/hevc_tile_mapping_wMemPSel/WL1/ac0mp0pr0cmb903mmp1/seed_80505/HEVCTileSplitTest__ac0mp0pr0cmb903mmp1_8_8__obuff.js", 
#                                      "../experiment_data/hevc_tile_mapping_wMemPSel/WL1/ac0mp0pr0cmb903mmp1/seed_80505/HEVCTileSplitTest__ac0mp0pr0cmb903mmp1_8_8__flwcompletedshort.js"], 
#                                         m=-1,p=-1, wf=-1, seed=-1, all_seeds=False)
    
    
    # plot_CompCost_vs_CommCost(fname=["C:/Users/Rosh/Documents/EngD/Work/AbstractSimulator/Multicore_Abstract_Sim/src/experiment_data/hevc_tile_mapping_wMemPSel/WL1/ac0mp0pr0cmb911mmp0/seed_1234/HEVCTileSplitTest__ac0mp0pr0cmb911mmp0_6_6__obuff.js", 
    #                                  "C:/Users/Rosh/Documents/EngD/Work/AbstractSimulator/Multicore_Abstract_Sim/src/experiment_data/hevc_tile_mapping_wMemPSel/WL1/ac0mp0pr0cmb911mmp0/seed_1234/HEVCTileSplitTest__ac0mp0pr0cmb911mmp0_6_6__flwcompletedshort.js"], 
    #                           m=-1,p=-1, wf=-1, seed=-1, all_seeds=False)
    
    
    # plot_CompCost_vs_CommCost(fname=["Z:/MCASim/experiment_data/hevc_tiles_mapping/WL2/ac0mp0pr0cmb905/seed_80505/HEVCTileSplitTest__ac0mp0pr0cmb905_6_6__obuff.js", 
    #                                  "Z:/MCASim/experiment_data/hevc_tiles_mapping/WL2/ac0mp0pr0cmb905/seed_80505/HEVCTileSplitTest__ac0mp0pr0cmb905_6_6__flwcompletedshort.js"], 
    #                           m=-1,p=-1, wf=-1, seed=-1, all_seeds=False)
    
    # plot_CompCost_vs_CommCost(fname=["../experiment_data/hevc_tilesplit_test/ac0mp0pr0cmb905/seed_1234/HEVCTileSplitTest__ac0mp0pr0cmb905_6_6__obuff.js", 
    #                                  "../experiment_data/hevc_tilesplit_test/ac0mp0pr0cmb905/seed_1234/HEVCTileSplitTest__ac0mp0pr0cmb905_6_6__flwcompleted.js"], 
    #                           m=-1,p=-1, wf=-1, seed=-1, all_seeds=False)
    
    
    
    #plot_Pri_vs_BlockingTime_vs_Lateness_vs_InputBuffWaitTime(p=4,m=8,wf=12,seed=-1, all_seeds=True)
    
    print "finished"
    
    plt.show()

