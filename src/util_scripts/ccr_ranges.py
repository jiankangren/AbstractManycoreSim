import sys, os, csv, pprint, math

#sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from collections import OrderedDict
from collections import Counter
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
import multiprocessing

import matplotlib.cm as cm
from matplotlib.font_manager import FontProperties
from SimParams import SimParams

from libApplicationModel.MPEG2FrameTask import MPEG2FrameTask
from libNoCModel.NoCFlow import NoCFlow



RANDOM_SEED_LIST = \
 [81665, 33749, 43894, 26358, 80505, \
  83660, 22817, 70263, 29917, 26044, \
  5558,  76891, 22250, 42198, 18065, \
  74076, 98652, 21149, 50399, 64217, \
  44117, 57824, 42267, 83200, 99108, \
  95928, 53864, 44289, 77379, 80521, \
  88117, 23327, 73337, 94064, 31982, \
  6878, 66093, 69541]

 
#frame_h = 480
#frame_w = 576

res_list = [(230,180), (528,576), (240,180), (240,180), (576, 720), (320,240), (320,240)]
#res_list = [(720,576), (544,576), (528,576), (480,576), (426,240), (320,240), (240,180)]
#res_list = [(576, 720)]

full_res_list = [(720,576), (544,576), (528,576), (480,576), (426,240), (320,240), (240,180)]



noc_period_max =  0.00001       # high period -> low noc freq -> increase CCR
noc_period_min =  0.0000000001 # low period -> high noc freq -> decrease CCR
cpu_exec_rat_min = 0.01
cpu_exec_rat_max = 2.0


def _write_formatted_file(fname, data, format):        
    if(format == "pretty"):
        logfile=open(fname, 'w')
        pprint.pprint(data, logfile, width=128)
        
    elif(format == "json"):
        logfile=open(fname, 'w')
        json_data = json.dumps(data)
        logfile.write(json_data)
        
    else:
        logfile=open(fname, 'w')
        pprint.pprint(data, logfile, width=128)

def _report_ccr(result_data):
    print "%15s | %15s | %15s | %15s | %15s | %15s" % ("cpu_exec_ratio", "noc_period", "mean_compcost", "noc_flw_cc", "ccr", "ccs")
    print "--------------------------------------------------------------------------------------------------------" 
    for each_entry in result_data:
        print "%15s | %15s | %15s | %15s | %15s | %15s" % (
                                        round(each_entry['cpu_exec_speed_ratio'],12),
                                        round(each_entry['noc_period'],12),                        
                                        round(each_entry['mean_computation_cost'],12),
                                        round(each_entry['noc_flow_cc'],12),                        
                                        round(each_entry['ccr'],12),
                                        round(each_entry['ccs'],12),           
                                        )    

    


def _gen_ccr(result_ccr_list, ccs_range, ccr_range, param_res_list):

    
        #cpu_exec_speed_ratio = random.choice(np.arange(cpu_exec_rat_min,cpu_exec_rat_max,(cpu_exec_rat_max-cpu_exec_rat_min)/10000))
        #noc_period = random.choice(np.arange(noc_period_min,noc_period_max,(noc_period_max-noc_period_min)/10000))
#         global_noc_period_list.append(noc_period)
#         while(noc_period in global_noc_period_list):     
#             global_noc_period_list.append(noc_period)       
#             noc_period = random.choice(np.arange(noc_period_min,noc_period_max,(noc_period_max-noc_period_min)/1000000))
            
        
        
        cpu_exec_speed_ratio = 0.8
        noc_period = random.uniform(noc_period_min, noc_period_max)
        
        list_mean_computation_cost = []
        list_sum_computation_cost_all_tasks = []
        list_mean_computation_cost_all_tasks = []
        list_noc_flow_cc_all_edges = []
        list_noc_flow_cc = []
        list_ccr = []
        list_ccs = []
        
        for each_res in param_res_list:
            
            frame_h = each_res[0]
            frame_w = each_res[1]
            
            # computation cost                        
            (iframe_cc, pframe_cc, bframe_cc) = MPEG2FrameTask.getStaticComputationCost(frame_h, frame_w, cpu_exec_speed_ratio)
            
            mean_computation_cost = float(iframe_cc + pframe_cc + bframe_cc)/3.0
            sum_computation_cost_all_tasks = (iframe_cc*1.0) + (pframe_cc*3.0) + (bframe_cc*8.0)
            mean_computation_cost_all_tasks = (sum_computation_cost_all_tasks)/12.0                
            
            # communication cost
            noc_w = np.sqrt(len(param_res_list)-3)            
            max_hop_count = (noc_w) + (noc_w)         
            payload = ((frame_h * frame_w) * 16)/8 
            arb_cost = noc_period *7
            noc_flow_cc = NoCFlow.getCommunicationCost(payload, max_hop_count, noc_period, arb_cost)
            num_edges = 19
            noc_flow_cc_all_edges = (noc_flow_cc * num_edges)
            
            # CCR : communication to computation
            #ccr = noc_flow_cc/mean_computation_cost    
            ccr = (noc_flow_cc_all_edges/sum_computation_cost_all_tasks)
            
            # CCS : communication + computation (summation)
            #ccs = noc_flow_cc + mean_computation_cost
            ccs = (noc_flow_cc_all_edges + sum_computation_cost_all_tasks)
            
            list_mean_computation_cost.append(mean_computation_cost)
            list_noc_flow_cc.append(noc_flow_cc)
            list_sum_computation_cost_all_tasks.append(sum_computation_cost_all_tasks)
            list_mean_computation_cost_all_tasks.append(mean_computation_cost_all_tasks)
            list_noc_flow_cc_all_edges.append(noc_flow_cc_all_edges)
            list_ccr.append(ccr)
            list_ccs.append(ccs)
            
            
        if (
            ((np.mean(list_ccs) >= float(ccs_range[0]) ) and (np.mean(list_ccs) <= float(ccs_range[1])))
         and 
         (round(np.mean(list_ccr),3) not in result_ccr_list)
         and
         (round(np.mean(list_ccr),3) in ccr_range)
         ):            
            entry = {
                        'cpu_exec_speed_ratio' : cpu_exec_speed_ratio,
                        'noc_period' : noc_period,                        
                        'mean_computation_cost' : np.mean(list_mean_computation_cost),
                        'noc_flow_cc' : np.mean(list_noc_flow_cc),                        
                        'ccr' : np.mean(list_ccr),
                        'ccs' : np.mean(list_ccs),                        
                     }
            
            return entry
        else:
            return None
            
            
        


def get_ccr_range_variablewfs(ccs_range, ccr_range, wf_nums, seed_range):
    final_result_dict = OrderedDict()
    
    for each_seed in seed_range:
        print "seed: " , each_seed
        final_result_dict[each_seed] = OrderedDict()
        for each_wf_num in wf_nums:   
            print "each_wf_num: ", each_wf_num
                 
            random.seed(each_seed) # randomise
            param_res_list = []
            # populate resolution list
            for wfn in xrange(each_wf_num):
                temp_res = random.choice(full_res_list)                       
                param_res_list.append(temp_res)
            
            # search for ccr
            result_data = OrderedDict()
            n = 0
            count = 0    
            result_ccr_list = []
    
            while(n<len(ccr_range)):
                entry = _gen_ccr(result_ccr_list, ccs_range, ccr_range, param_res_list)

                if(entry != None):
                    rounded_ccr = round(entry['ccr'], 3)
                    result_data[rounded_ccr] = entry
                    result_ccr_list.append(rounded_ccr)
                    n+=1
                    print n,  entry['ccr']
                 
                count+=1
            if(each_wf_num not in final_result_dict[each_seed]):                    
                final_result_dict[each_seed][each_wf_num] = {
                                     'ccr_list' : result_data,
                                     'res_list' : param_res_list
                                     }
                pprint.pprint(final_result_dict[each_seed][each_wf_num])
                print "---"
    
    
    ## write data file output   
    if(len(seed_range)==1):  
        fname = 'ccr_list_allwfs_output_' + str(ccr_range[0]) + "_" + str(ccr_range[-1]) +  "_s" + str(seed_range[0]) +  ".js"     
        _write_formatted_file(fname, final_result_dict, "json")
    else:
        fname = 'ccr_list_allwfs_output_' + str(ccr_range[0]) + "_" + str(ccr_range[-1]) +  ".js"     
        _write_formatted_file(fname, final_result_dict, "json")
        
                    


def get_ccr_range(enable_print = True):
 
    result_data = []
    
    frame_h = res_list[0][0]
    frame_w = res_list[0][1]
    
    for cpu_exec_speed_ratio in [0.1]:
    #for cpu_exec_speed_ratio in np.arange(cpu_exec_rat_min,cpu_exec_rat_max,(cpu_exec_rat_max-cpu_exec_rat_min)/2):    
        for noc_period in np.arange(noc_period_min,noc_period_max,(noc_period_max-noc_period_min)/10):
            
            # computation cost
            (iframe_cc, pframe_cc, bframe_cc) = MPEG2FrameTask.getStaticComputationCost(frame_h, frame_w, cpu_exec_speed_ratio)             
            mean_computation_cost = float(iframe_cc + pframe_cc + bframe_cc)/3.0
             
            # communication cost
            max_hop_count = (SimParams.NOC_W-1) + (SimParams.NOC_H-1)         
            payload = ((frame_h * frame_w) * 16)/8 
            arb_cost = noc_period *7
            noc_flow_cc = NoCFlow.getCommunicationCost(payload, max_hop_count, noc_period, arb_cost)
                         
            # CCR : communication to computation ratio
            ccr = noc_flow_cc/mean_computation_cost
             
            # CCS : communication + computation (summation)
            ccs = noc_flow_cc + mean_computation_cost
             
            entry = {
                        'cpu_exec_speed_ratio' : cpu_exec_speed_ratio,
                        'noc_period' : noc_period,
                         
                        'mean_computation_cost' : mean_computation_cost,
                        'noc_flow_cc' : noc_flow_cc,
                         
                        'ccr' : ccr,
                        'ccs' : ccs,                        
                     }
             
            result_data.append(entry)
     
    # print table of results                        
    if(enable_print == True):         
        _report_ccr(result_data)
            
    return result_data
 
    
            
def get_properties_fixed_ccs_fixed_ccr_range(ccs_range, ccr_range, enable_print = True):
    
    random.seed(1234)    
    result_data = []
    n = 0
    count = 0    
    result_ccr_list = []
    
    while(n < len(ccr_range)):
        
        #cpu_exec_speed_ratio = random.choice(np.arange(cpu_exec_rat_min,cpu_exec_rat_max,(cpu_exec_rat_max-cpu_exec_rat_min)/10000))        
        #noc_period = random.choice(np.arange(noc_period_min,noc_period_max,(noc_period_max-noc_period_min)/10000))
        
        cpu_exec_speed_ratio = 0.8
        noc_period = random.uniform(noc_period_min, noc_period_max)
        
        list_mean_computation_cost = []
        list_sum_computation_cost_all_tasks = []
        list_mean_computation_cost_all_tasks = []
        list_noc_flow_cc_all_edges = []
        list_noc_flow_cc = []
        list_ccr = []
        list_ccs = []
        
        for each_res in res_list:
            
            frame_h = each_res[0]
            frame_w = each_res[1]
            
            # computation cost
            (iframe_cc, pframe_cc, bframe_cc) = MPEG2FrameTask.getStaticComputationCost(frame_h, frame_w, cpu_exec_speed_ratio)    
            mean_computation_cost = float(iframe_cc + pframe_cc + bframe_cc)/3.0
            sum_computation_cost_all_tasks = (iframe_cc*1.0) + (pframe_cc*3.0) + (bframe_cc*8.0)
            mean_computation_cost_all_tasks = (iframe_cc) + (pframe_cc) + (bframe_cc)
                
            
            # communication cost
            max_hop_count = (SimParams.NOC_W-1) + (SimParams.NOC_H-1)         
            payload = ((frame_h * frame_w) * 16)/8 
            arb_cost = noc_period *7
            noc_flow_cc = NoCFlow.getCommunicationCost(payload, max_hop_count, noc_period, arb_cost)
            num_edges = 19
            noc_flow_cc_all_edges = (noc_flow_cc * num_edges)
            
            # CCR : communication to computation
            #ccr = noc_flow_cc/mean_computation_cost    
            ccr = (noc_flow_cc_all_edges/sum_computation_cost_all_tasks)
            
            # CCS : communication + computation (summation)
            #ccs = noc_flow_cc + mean_computation_cost
            ccs = (noc_flow_cc_all_edges + sum_computation_cost_all_tasks)
            
            list_mean_computation_cost.append(mean_computation_cost)
            list_noc_flow_cc.append(noc_flow_cc)
            list_sum_computation_cost_all_tasks.append(sum_computation_cost_all_tasks)
            list_mean_computation_cost_all_tasks.append(mean_computation_cost_all_tasks)
            list_noc_flow_cc_all_edges.append(noc_flow_cc_all_edges)
            list_ccr.append(ccr)
            list_ccs.append(ccs)
            
            
        if (
            ((np.mean(list_ccs) >= float(ccs_range[0]) ) and (np.mean(list_ccs) <= float(ccs_range[1])))
         and 
         (round(np.mean(list_ccr),3) not in result_ccr_list)
         and
         (round(np.mean(list_ccr),3) in ccr_range)
         ):            
            entry = {
                        'cpu_exec_speed_ratio' : cpu_exec_speed_ratio,
                        'noc_period' : noc_period,                        
                        'mean_computation_cost' : np.mean(list_mean_computation_cost),
                        'noc_flow_cc' : np.mean(list_noc_flow_cc),                        
                        'ccr' : np.mean(list_ccr),
                        'ccs' : np.mean(list_ccs),                        
                     }
            
            result_data.append(entry)
            result_ccr_list.append(round(np.mean(list_ccr), 3))
            n+=1
            print n,  np.mean(list_ccr)   
                 
        count+=1        
            
    # print table of results                        
    if(enable_print == True):        
        # sort
        new_result_data = sorted(result_data, key=lambda k: k['ccr'])
        _report_ccr(new_result_data)   
        
        ## write data file output     
        fname = 'ccr_list_output_' + str(ccr_range[0]) + "_" + str(ccr_range[-1]) + ".js"     
        _write_formatted_file(fname, new_result_data, "json")
        
        
    return result_data
            


def get_specific_ccr(cpu_exec_speed_ratio, noc_period):
    
    list_ipb_frame_cost = []
    list_mean_computation_cost = []
    list_sum_computation_cost_all_tasks = []
    list_mean_computation_cost_all_tasks = []
    list_noc_flow_cc_all_edges = []
    list_noc_flow_cc = []
    list_ccr = []
    list_ccs = []
     
    
    for each_res in res_list:    
        frame_h = each_res[0]
        frame_w = each_res[1]
                
        # computation cost
        (iframe_cc, pframe_cc, bframe_cc) = MPEG2FrameTask.getStaticComputationCost(frame_h, frame_w, cpu_exec_speed_ratio)    
        mean_computation_cost = float(iframe_cc + pframe_cc + bframe_cc)/3.0
        sum_computation_cost_all_tasks = (iframe_cc*1.0) + (pframe_cc*3.0) + (bframe_cc*8.0)
        mean_computation_cost_all_tasks = (iframe_cc) + (pframe_cc) + (bframe_cc)
        
        # communication cost
        max_hop_count = (SimParams.NOC_W-1) + (SimParams.NOC_H-1)         
        payload = ((frame_h * frame_w) * 16)/8 
        arb_cost = noc_period *7
        noc_flow_cc = NoCFlow.getCommunicationCost(payload, max_hop_count, noc_period, arb_cost)
        num_edges = 19
        noc_flow_cc_all_edges = (noc_flow_cc * num_edges)
        
        # CCR : communication to computation
        #ccr = noc_flow_cc/mean_computation_cost    
        ccr = (noc_flow_cc_all_edges/sum_computation_cost_all_tasks)
        
        # CCS : communication + computation (summation)
        #ccs = noc_flow_cc + mean_computation_cost
        ccs = (noc_flow_cc_all_edges + sum_computation_cost_all_tasks)
        
        list_mean_computation_cost.append(mean_computation_cost)
        list_noc_flow_cc.append(noc_flow_cc)
        list_sum_computation_cost_all_tasks.append(sum_computation_cost_all_tasks)
        list_mean_computation_cost_all_tasks.append(mean_computation_cost_all_tasks)
        list_noc_flow_cc_all_edges.append(noc_flow_cc_all_edges)
        list_ccr.append(ccr)
        list_ccs.append(ccs)
        list_ipb_frame_cost.append((iframe_cc, pframe_cc, bframe_cc))
        
#     print list_ccr
#     print list_ccs

    entry = {
               'cpu_exec_speed_ratio' : cpu_exec_speed_ratio,
               'noc_period' : noc_period,            
               'mean_computation_cost' : np.mean(list_mean_computation_cost),
               'noc_flow_cc' : np.mean(list_noc_flow_cc),            
               
               'sum_computation_cost_all_tasks' : list_sum_computation_cost_all_tasks,
               'mean_computation_cost_all_tasks' : list_mean_computation_cost_all_tasks,
               'noc_flow_cc_all_edges' : list_noc_flow_cc_all_edges,
               
               'list_ipb_frame_cost' : list_ipb_frame_cost,
               
               'list_ccr' : list_ccr,
               'list_ccs' : list_ccs,                        
               
               'mean_ccr' : np.mean(list_ccr),
               'mean_ccs' : np.mean(list_ccs),
               
               'ccr_v2' : np.sum(list_noc_flow_cc_all_edges)/np.sum(list_mean_computation_cost_all_tasks),
               'csr_v2' : np.sum(list_noc_flow_cc_all_edges) + np.sum(list_mean_computation_cost_all_tasks)
               
            }
    
    pprint.pprint(entry)


def get_ccr_range_variablewfs_multiprocessing():
    ccs_range = [0.0, 1000000]
    ccr_range = [round(x,3) for x in np.linspace(0.001, 2.0, 5)]
    offset = 0
    wf_nums = [(3*3)+offset, (5*5)+offset, (7*7)+offset, (9*9)+offset]
    jobs = []
    for each_seed in RANDOM_SEED_LIST:
        temp_seed_list = [each_seed]
        #get_ccr_range_variablewfs(ccs_range, ccr_range, wf_nums, enable_print=True, seed_range=temp_seed_list)
        
        p = multiprocessing.Process(target=get_ccr_range_variablewfs, args=(ccs_range, ccr_range, wf_nums, temp_seed_list, ))
        jobs.append(p)
        p.start()



###########
# Main
###########
    

#get_specific_ccr(0.8, 0.0000001)
 
#get_ccr_range()
#get_ccr_range_fixed_ccs([0.044, 0.046], 500, enable_print = True)
  
#ccs_range = [0.0676, 0.0684]
#ccr_range = [round(x,2) for x in np.arange(0.05, 2.01, 0.01)]

#ccs_range = [0.0, 1000000]
#ccr_range = [round(x,3) for x in np.linspace(0.001, 2.0, 5)]

#offset = 3
#wf_nums = [(3*3)+offset, (5*5)+offset, (7*7)+offset, (9*9)+offset]

#get_properties_fixed_ccs_fixed_ccr_range(ccs_range, ccr_range, enable_print = True)

#get_ccr_range_variablewfs(ccs_range, ccr_range, wf_nums, enable_print=True)
#get_ccr_range_variablewfs_multiprocessing()
