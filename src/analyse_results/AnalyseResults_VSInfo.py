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
from libNoCModel.NoCFlow import FlowType




NOC_X = 4
NOC_Y = 4
NUM_NODES = NOC_X*NOC_Y

    

def plot_VS_info(fname):
        
    # get data
    fname = fname    
    json_data=open(fname)
    file_data = json.load(json_data)
       
    average_dispatch_rate_dist = []
    wf_level_info = {}
    res_freq = {}
    overall_inter_arrival_time_dist = []
    overall_initial_vid_gap_dist = []
    
    total_workload = 0
    for wf_id, each_wf in file_data.iteritems():
        wf_level_info[wf_id] = {}
        wf_level_info[wf_id]['vs_count'] = len(each_wf)
        wf_level_info[wf_id]['avg_disp_rate_dist'] = []
        wf_level_info[wf_id]['inter_arrival_time_dist'] = []
        wf_level_info[wf_id]['res_dist'] = []
                
        start_time = 0.0
        end_time = 0.0
        
        sorted_vs_keys = sorted(each_wf.keys())
        
        for vs_id in sorted_vs_keys: 
            #pprint.pprint(each_wf[vs_id])
            
            #print vs_id
            wf_level_info[wf_id]['avg_disp_rate_dist'].append(each_wf[vs_id]["avg_dis_rate"])
            wf_level_info[wf_id]['res_dist'].append((each_wf[vs_id]["res_h"], each_wf[vs_id]["res_w"]))
            total_workload += (each_wf[vs_id]["res_h"] * each_wf[vs_id]["res_w"])
            
            res_key = "%d x %d" % (each_wf[vs_id]["res_h"], each_wf[vs_id]["res_w"])
            if res_key in res_freq:
                res_freq[res_key]+=1
            else:
                res_freq[res_key]=0
            
            if(int(vs_id) == 0):
                try:
                    overall_initial_vid_gap_dist.append(each_wf[vs_id]['starttime'])
                except:
                    overall_initial_vid_gap_dist.append(each_wf[vs_id]['st'])
            else:
                try:                            
                    inter_arrival_time = each_wf[vs_id]['starttime'] - end_time
                except:
                    inter_arrival_time = each_wf[vs_id]['st'] - end_time
                wf_level_info[wf_id]['inter_arrival_time_dist'].append(inter_arrival_time)
                overall_inter_arrival_time_dist.append(inter_arrival_time)
            try:                
                start_time = each_wf[vs_id]['starttime']
                end_time = each_wf[vs_id]['endtime']
            except:
                start_time = each_wf[vs_id]['st']
                end_time = each_wf[vs_id]['et']
                
        wf_level_info[wf_id]['mean__avg_disp_rate_dist'] = np.mean(wf_level_info[wf_id]['avg_disp_rate_dist'])
        wf_level_info[wf_id]['mean__inter_arrival_time_dist'] = np.mean(wf_level_info[wf_id]['inter_arrival_time_dist'])
        
    print "-----------------------"
    print fname
    pprint.pprint(res_freq)
    #print "overall_inter_arrival_time_dist (mean) : " + str(np.mean(overall_inter_arrival_time_dist))
#    print "overall_inter_arrival_time_dist (max) : " + str(np.max(overall_inter_arrival_time_dist))
    
    print "sum_workload : " + str(total_workload)
    print "overall_initial_vid_gap_dist (mean) : " + str(np.mean(overall_initial_vid_gap_dist))
    print "overall_initial_vid_gap_dist (max) : " + str(np.max(overall_initial_vid_gap_dist))
    print "overall_vid_nums_per_wf (sum) : " + str(np.sum([x['vs_count'] for x in wf_level_info.values()]))
    print "-----------------------"
    
    
    final_data_struct = {
                         'mean__avg_disp_rate_dist' : np.mean([x['mean__avg_disp_rate_dist'] for x in wf_level_info.values()]),                         
                         'mean__inter_arrival_time_dist' : np.mean([x['mean__inter_arrival_time_dist'] for x in wf_level_info.values()]),
                    
                         'sum_workload' : total_workload,
                         
                         'overall_initial_vid_gap_dist_mean' :  np.mean(overall_initial_vid_gap_dist),
                         'overall_initial_vid_gap_dist_max' : np.max(overall_initial_vid_gap_dist),
                         'overall_vid_nums_per_wf_sum' : np.sum([x['vs_count'] for x in wf_level_info.values()]),
                         
                         # resulution freqs
                         'res_freq' : res_freq,             
                  }
    
    return final_data_struct
            
            

def plot_qnstatus(fname, key='ntype'):
    
    print "plot_qnstatus"
    
    NUM_NODES =16
    # get data
    fname = fname    
    json_data=open(fname)
    psalgo_qnstatus = json.load(json_data)      
    
    node_level_attribute1 = [[] for x in xrange(NUM_NODES)]
    node_level_attribute2 = [[] for x in xrange(NUM_NODES)]
    node_level_attribute3 = [[] for x in xrange(NUM_NODES)]
    node_level_attribute4 = [[] for x in xrange(NUM_NODES)]
    
    all_cumslack = []
    for each_entry in psalgo_qnstatus:        
        for each_node in each_entry:
            print each_node['nid']
            node_level_attribute1[each_node['nid']].append(each_node[key])
            node_level_attribute2[each_node['nid']].append(each_node['plevel'])
            node_level_attribute3[each_node['nid']].append(each_node['qncount'])
            node_level_attribute4[each_node['nid']].append(each_node['ntype']*50)
    
    fig = plt.figure()
    fig.canvas.set_window_title('plot_qnstatus - ' + fname)
    
    for each_node_ix in xrange(NUM_NODES):
        ax1 = plt.subplot(NUM_NODES,1,each_node_ix+1) 
        #ax1.plot(node_level_attribute1[each_node_ix])
        ax1.plot(node_level_attribute2[each_node_ix], color='r')
        #ax1.plot(node_level_attribute3[each_node_ix], color='g')
        #ax1.plot(node_level_attribute4[each_node_ix], color='k')
        
        ax1.set_title("CPU-"+str(each_node_ix))        
   


def analysis_good_bad_plot_boxplot(good_data, bad_data):
    
    num_data_categories = 14
    Nrows = math.ceil(num_data_categories / 2.)
    
    titles = [
                'mean__avg_disp_rate_dist',
                'mean__inter_arrival_time_dist',
                'sum_workload',
                'overall_initial_vid_gap_dist_mean',
                'overall_initial_vid_gap_dist_max',
                'overall_vid_nums_per_wf_sum',
                  
                'res_freq_240 x 180',
                'res_freq_320 x 240',
                'res_freq_426 x 240',
                'res_freq_480 x 576',
                'res_freq_528 x 576',
                'res_freq_544 x 576',
                'res_freq_720 x 576',
              ]
    
    good_data_dist = [
                      [x['mean__avg_disp_rate_dist'] for x in good_data],
                      [x['mean__inter_arrival_time_dist'] for x in good_data],
                      [x['sum_workload'] for x in good_data],
                      [x['overall_initial_vid_gap_dist_mean'] for x in good_data],
                      [x['overall_initial_vid_gap_dist_max'] for x in good_data],
                      [x['overall_vid_nums_per_wf_sum'] for x in good_data],
                      
                      [x['res_freq']['240 x 180'] for x in good_data],
                      [x['res_freq']['320 x 240'] for x in good_data],
                      [x['res_freq']['426 x 240'] for x in good_data],
                      [x['res_freq']['480 x 576'] for x in good_data],
                      [x['res_freq']['528 x 576'] for x in good_data],
                      [x['res_freq']['544 x 576'] for x in good_data],
                      [x['res_freq']['720 x 576'] for x in good_data],
                      ]
    
    bad_data_dist = [
                      [x['mean__avg_disp_rate_dist'] for x in bad_data],
                      [x['mean__inter_arrival_time_dist'] for x in bad_data],
                      [x['sum_workload'] for x in good_data],
                      [x['overall_initial_vid_gap_dist_mean'] for x in bad_data],
                      [x['overall_initial_vid_gap_dist_max'] for x in bad_data],
                      [x['overall_vid_nums_per_wf_sum'] for x in bad_data],
                      
                      [x['res_freq']['240 x 180'] for x in bad_data],
                      [x['res_freq']['320 x 240'] for x in bad_data],
                      [x['res_freq']['426 x 240'] for x in bad_data],
                      [x['res_freq']['480 x 576'] for x in bad_data],
                      [x['res_freq']['528 x 576'] for x in bad_data],
                      [x['res_freq']['544 x 576'] for x in bad_data],
                      [x['res_freq']['720 x 576'] for x in bad_data],
                      ]
    f = plt.figure()
    i = 0
    for g_data, b_data in zip(good_data_dist, bad_data_dist):
        plt.subplot(1, num_data_categories, i+1)
        plt.boxplot([g_data, b_data])
        plt.title(titles[i], rotation=25)
        plt.grid(True)
        
        i +=1


def res_freq_analysis(data):
    
    total_freqs = OrderedDict()        
    total_freqs['240 x 180'] = np.sum([x['res_freq']['240 x 180'] for x in data])
    total_freqs['320 x 240'] = np.sum([x['res_freq']['320 x 240'] for x in data])
    total_freqs['426 x 240'] = np.sum([x['res_freq']['426 x 240'] for x in data])
    total_freqs['480 x 576'] = np.sum([x['res_freq']['480 x 576'] for x in data])
    total_freqs['528 x 576'] = np.sum([x['res_freq']['528 x 576'] for x in data])
    total_freqs['544 x 576'] = np.sum([x['res_freq']['544 x 576'] for x in data])
    total_freqs['720 x 576'] = np.sum([x['res_freq']['720 x 576'] for x in data])
    
    pprint.pprint(total_freqs)
    
#     f = plt.figure()
#     plt.hist(total_freqs.values(), 7, normed=True)
#     plt.grid(True)


def analysis_good_bad_data():
    
    all_bad_data = []
    all_good_data = []
    
    print "====================================================================================="
    print "============================= ---- bad ----"
    print "====================================================================================="
    # bad    
    data = plot_VS_info("Z:/MCASim/experiment_data/remapping_psbased/seed_74076/RMOFF_test__wfressumm.js")
    all_bad_data.append(data)    
    data = plot_VS_info("Z:/MCASim/experiment_data/remapping_psbased/seed_76891/RMOFF_test__wfressumm.js")
    all_bad_data.append(data)
    data = plot_VS_info("Z:/MCASim/experiment_data/remapping_psbased/seed_98652/RMOFF_test__wfressumm.js")
    all_bad_data.append(data)
    data = plot_VS_info("Z:/MCASim/experiment_data/remapping_psbased/seed_81474/RMOFF_test__wfressumm.js")
    all_bad_data.append(data)
    data = plot_VS_info("Z:/MCASim/experiment_data/remapping_psbased/seed_26358/RMOFF_test__wfressumm.js")
    all_bad_data.append(data)
    data = plot_VS_info("Z:/MCASim/experiment_data/remapping_psbased/seed_83660/RMOFF_test__wfressumm.js")
    all_bad_data.append(data)
    data = plot_VS_info("Z:/MCASim/experiment_data/remapping_psbased/seed_68385/RMOFF_test__wfressumm.js")
    all_bad_data.append(data)
    data = plot_VS_info("Z:/MCASim/experiment_data/remapping_psbased/seed_64217/RMOFF_test__wfressumm.js")
    all_bad_data.append(data)
    data = plot_VS_info("Z:/MCASim/experiment_data/remapping_psbased/seed_99108/RMOFF_test__wfressumm.js")
    all_bad_data.append(data)
    data = plot_VS_info("Z:/MCASim/experiment_data/remapping_psbased/seed_34921/RMOFF_test__wfressumm.js")
    all_bad_data.append(data)

    
    print "====================================================================================="
    print "============================= ---- good ----"
    print "====================================================================================="
    
    # good    
    data = plot_VS_info("Z:/MCASim/experiment_data/remapping_psbased/seed_31982/RMOFF_test__wfressumm.js")
    all_good_data.append(data)
    data = plot_VS_info("Z:/MCASim/experiment_data/remapping_psbased/seed_53864/RMOFF_test__wfressumm.js")
    all_good_data.append(data)
    data = plot_VS_info("Z:/MCASim/experiment_data/remapping_psbased/seed_66093/RMOFF_test__wfressumm.js")
    all_good_data.append(data)
    data = plot_VS_info("Z:/MCASim/experiment_data/remapping_psbased/seed_73337/RMOFF_test__wfressumm.js")
    all_good_data.append(data)
    data = plot_VS_info("Z:/MCASim/experiment_data/remapping_psbased/seed_53706/RMOFF_test__wfressumm.js")
    all_good_data.append(data)
    data = plot_VS_info("Z:/MCASim/experiment_data/remapping_psbased/seed_29648/RMOFF_test__wfressumm.js")
    all_good_data.append(data)
    data = plot_VS_info("Z:/MCASim/experiment_data/remapping_psbased/seed_57177/RMOFF_test__wfressumm.js")
    all_good_data.append(data)
    data = plot_VS_info("Z:/MCASim/experiment_data/remapping_psbased/seed_29917/RMOFF_test__wfressumm.js")
    all_good_data.append(data)
    data = plot_VS_info("Z:/MCASim/experiment_data/remapping_psbased/seed_83694/RMOFF_test__wfressumm.js")
    all_good_data.append(data)
    data = plot_VS_info("Z:/MCASim/experiment_data/remapping_psbased/seed_88117/RMOFF_test__wfressumm.js")
    all_good_data.append(data)

    
    analysis_good_bad_plot_boxplot(all_good_data, all_bad_data)
    res_freq_analysis(all_good_data)

#plot_qnstatus("../experiment_data/remapping_psbased/temp/remapping_psbased__2236_061114/seed_99108/RMON_test__psalgonodeprops.js")


analysis_good_bad_data()



#plot_VS_info(fname="../experiment_data/closedloop_vs_openloop/CLwoIB_7_7_test__wfressumm.js")
#plot_VS_info(fname="../experiment_data/closedloop_vs_openloop/CLwoIB_6_6_test__wfressumm.js")


#plot_VS_info("../experiment_data/remapping_psbased/seed_42198/RMON_test__psalgonodeprops.js", key='thrqn')

print "finished"
plt.show()
