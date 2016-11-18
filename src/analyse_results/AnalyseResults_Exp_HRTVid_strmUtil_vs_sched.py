import sys

#sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from pprint import pprint
from collections import OrderedDict
import numpy as np
import traceback
import re
#import pylab
import matplotlib
matplotlib.use('Qt4Agg')
import matplotlib.pyplot as plt
#plt.style.use('bmh_rosh')

#import seaborn as sns
import seaborn.apionly as sns
import scipy.stats
import json
from matplotlib import colors
import matplotlib.cm as cm

plt.style.use('bmh_rosh')
#from SimParams import SimParams


from util_scripts.resolution_combos import generate_resolution_combos

# before bl-fix
#FNAME_DATA_OUT_ADMINRATES = "../experiment_data/hrt_video/HRTVIDLong_data_090616/data_Load_vs_VSInfo.js"
#FNAME_DATA_OUT_PEUTIL = "../experiment_data/hrt_video/HRTVIDLong_data_090616/data_Load_vs_OverallSysUtil.js"
#FNAME_DATA_OUT_NOCUTIL = "../experiment_data/hrt_video/HRTVIDLong_data_090616/data_Load_vs_OverallNoCUtil.js"
#FNAME_DATA_OUT_ADMINLOAD = "../experiment_data/hrt_video/HRTVIDLong_data_090616/data_Load_vs_AdmittedLoad.js"

# after bl-fix
FNAME_DATA_OUT_ADMINRATES = "../experiment_data/hrt_video/HRTVIDLong_data_BLTest/data_Load_vs_VSInfo.js"
FNAME_DATA_OUT_PEUTIL = "../experiment_data/hrt_video/HRTVIDLong_data_BLTest/data_Load_vs_OverallSysUtil.js"
FNAME_DATA_OUT_NOCUTIL = "../experiment_data/hrt_video/HRTVIDLong_data_BLTest/data_Load_vs_OverallNoCUtil.js"
FNAME_DATA_OUT_ADMINLOAD = "../experiment_data/hrt_video/HRTVIDLong_data_BLTest/data_Load_vs_AdmittedLoad.js"


MAX_TASK_PRIORITY = 100000000

NOC_H = 3
NOC_W = 3

MAX_CC_LEVEL = 4000000
#MAX_CC_LEVEL = 1434664

RANDOM_SEEDS = [80505, 1234, 81665, 33749, 43894, 26358, 70505, \
83660, 22817, 70263, 29917, 26044, \
76891, 50399, 64217, \
44117, 57824, 42267, 83200, 99108, \
95928, 53864, 44289, 77379, 80521, \
88117, 23327, 73337, 94064, 31982, 22250, \
6878, 66093, 69541, 18065, 74076, 98652, 21149, 42198, 5558]

#RANDOM_SEEDS = [1234]
RANDOM_SEEDS = RANDOM_SEEDS[:30]

print len(RANDOM_SEEDS)
#sys.exit()

#RANDOM_SEEDS = [81665, 76891]

#EXP_DATADIR = "../experiment_data/hrt_video/util_vs_sched/"
#EXP_DATADIR = "Z:/MCASim/experiment_data/hrt_video/util_vs_sched/seed_70505/"
#EXP_DATADIR = "Z:/MCASim/experiment_data/hrt_video/util_vs_sched/" # version for long hrtvid paper
EXP_DATADIR = "Z:/Simulator_versions_perExperiment/ThesisTechCh5_GASim/src/experiment_data/hrt_video/util_vs_sched/" # after bl fix

global_types_of_tests = [
                      
                    ## Deterministic - AC ##

                    #{'ac':11, 'mp':0, 'pr':4, 'cmb':840 }, # determ, lumm
                    
                    {'ac':11, 'mp':0, 'pr':4, 'cmb':841 , 'lbl': "IPC"}, # determ, improved
                    {'ac':11, 'mp':0, 'pr':4, 'cmb':842 , 'lbl': "LWCRS"}, # determ, improved                    
                    {'ac':11, 'mp':0, 'pr':4, 'cmb':833 , 'lbl': "PP"}, # determ, improved
                    {'ac':11, 'mp':0, 'pr':4, 'cmb':834 , 'lbl': "BN"}, # determ, improved
                    ##{'ac':11, 'mp':0, 'pr':4, 'cmb':832 , 'lbl': "BN"}, # determ, improved - not in use
                    {'ac':11, 'mp':10, 'pr':4, 'cmb':0 , 'lbl': "LU"}, # determ, improved
                    {'ac':11, 'mp':12, 'pr':4, 'cmb':0 , 'lbl': "LM"}, # determ, improved
                    {'ac':11, 'mp':13, 'pr':4, 'cmb':0 , 'lbl': "GA-MP"}, # determ, improved  
                      ]


GLOBAL_COLS = {
               
               #'r', '#fb9a99', # reds
               #'b', '#80b1d3', # blues
               #'g', '#a6d854',  # greens
               
               "IPC":'r', 
               "LWCRS":'#fb9a99',
               "PP":'#08306b',
               "BN":'#2171b5',
               "LU": '#6baed6',
               "LM": '#c6dbef',  
               "GA-MP": '#31a354'
               }


GLOBAL_HATCHES = ['/',
                  "\\", 
                  '//',
                  'x', 
                  "." , 
                  'o', 
                  'O']
                  
                  


global_admission_rate_eq_zero = {}


def _get_wfs_for_cc(cc):
    if cc == 541584:
        num_wfs = 5 
    elif cc == 831168:
        num_wfs = 4 
    elif cc == 853464:
        num_wfs = 6 
    elif cc == 1099776:
        num_wfs = 4
    elif cc == 1124208:
        num_wfs = 5
    elif cc == 1433664:
        num_wfs = 7
    elif cc == 1772928:
        num_wfs = 7
    elif cc == 1898496:
        num_wfs = 6
    elif cc == 1912248:
        num_wfs = 7
    elif cc == 2254104:
        num_wfs = 8
    else:
        sys.exit("_get_wfs_for_cc:: Error")
    
    return num_wfs


def _get_ga_totalevals(cc):
    
    if cc == 541584:
        gensize = 50 
        popsize = 100
    elif cc == 831168:
        gensize = 60
        popsize = 100
    elif cc == 853464:
        gensize = 60
        popsize = 120
    elif cc == 1099776:
        gensize = 60
        popsize = 150
    elif cc == 1124208:
        gensize = 100
        popsize = 150
    elif cc == 1433664:
        gensize = 100
        popsize = 200
    elif cc == 1772928:
        gensize = 120
        popsize = 200
    elif cc == 1898496:
        gensize = 150
        popsize = 250
    elif cc == 1912248:
        gensize = 150
        popsize = 250
    elif cc == 2254104:
        gensize = 200
        popsize = 250
    else:
        sys.exit("_get_ga_totalevals:: Error")
    
    return (gensize, popsize, (gensize*popsize))




    


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
        
def plot_Load_vs_VSInfo(normal_plot = True, bin_plot = False, bar_plot=False, load_data_from_file=False):    
    global global_admission_rate_eq_zero
    #reject_cc_list = [1433664,1800504,2254104]
    reject_cc_list = []
    
    ## get data from experiment files
    if(load_data_from_file==False):
    
        # get res_combos 
        rand_seed = 1234    
        res_arr = [(720,576), (544,576), (528,576), (480,576), (426,240), (320,240), (240,180), (230,180)]
        max_num_wfs = 10
        #res_combos = generate_resolution_combos(max_num_wfs-1,res_arr,rand_seed, sampled=True)
        
        res_combos = generate_resolution_combos(max_num_wfs-1,res_arr,rand_seed, 
                                        sampled=True, 
                                        reduced_samples=10, 
                                        total_samples=20000,
                                        lower_limit=80000)
        
        # remove specific wf
        res_combos, target_ix = _remove_custom_wf(res_combos, 1800504, 9)
        # add custom wf
        res_combos.insert(target_ix, _get_custom_wf_cc1772928_wfs7())
        
        all_exp_results_listbased = OrderedDict()    
        colors = ['b', 'r', 'b', 'r']
        markers = ['x', 'x', 'o', 'o']
        
        for each_test_type in global_types_of_tests:
            exp_key =  "AC"+ str(each_test_type['ac']) + "_" + \
                                 "MP"+ str(each_test_type['mp']) + "_" + \
                                 "PR"+ str(each_test_type['pr']) + "_" + \
                                 "CMB"+ str(each_test_type['cmb'])
            exp_key = each_test_type['lbl']        
            all_exp_results_listbased[exp_key] = []
            
            #print "exp_key = " + exp_key
            count_temp = 0
            for each_res_combo in res_combos:
                cc = each_res_combo['cc']                    
                if cc > MAX_CC_LEVEL:
                    continue
                
                if cc in reject_cc_list:
                    continue
                
                #print cc      
                cc_uid = each_res_combo['cc_uid']   
                all_admission_ratio = []              
                for each_seed in RANDOM_SEEDS:
                    print "Get VSInfo : exp_key = " + str(exp_key) + ", cc = " + str(cc) + ", seed = " + str(each_seed) 
                    try:            
                                                
                        subdir = "seed_" + str(each_seed) + "/" +"ac"+str(each_test_type['ac'])+"mp"+str(each_test_type['mp'])+"pr"+str(each_test_type['pr'])+"cmb"+str(each_test_type['cmb'])+"/"
                        # get data for no-ac, LUM
                        prefix = "HRTVid_" + \
                                     "AC" + str(each_test_type['ac']) + "_" + \
                                     "MP" + str(each_test_type['mp']) + "_" + \
                                     "PR" + str(each_test_type['pr']) + "_" + \
                                     "CMB" + str(each_test_type['cmb']) + "_" + \
                                     "cc" + str(cc) + "-" + str(cc_uid) + "_"                             
                                     
                        fname_prefix = EXP_DATADIR+subdir+prefix+str(NOC_H)+"_"+str(NOC_W)+"_"
                        
                        ## get video accept/reject/late list
                        fname = fname_prefix+"test__vsbs.js"    
                        print fname
                        json_data=open(fname)
                        file_data = json.load(json_data)
                        
                        num_vidstrm_accepted_but_late = file_data["num_vids_accepted_late"] 
                        num_vidstrm_dropped_tasks = file_data["num_dropped_tasks"] 
                        num_vidstrm_rejected = file_data["num_vids_rejected"]
                        num_vidstrm_accepted_success = file_data["num_vids_accepted_success"]
                        
                        total_num_streams = num_vidstrm_accepted_but_late + num_vidstrm_rejected + num_vidstrm_accepted_success
                        
                        # check late streams
                        if(num_vidstrm_accepted_but_late != 0):
                            print "--"
                            print num_vidstrm_accepted_but_late
                            print total_num_streams
                            print fname
                            print "--"
                            count_temp +=1
                            #sys.exit("error")
                        
                        if(num_vidstrm_accepted_success==0 and num_vidstrm_accepted_but_late==1):
                            num_vidstrm_accepted_success = 1
                            admitted_ratio = float(float(num_vidstrm_accepted_success) / float(total_num_streams))
                        else:                    
                            admitted_ratio = float(float(num_vidstrm_accepted_success) / float(total_num_streams))
                            
                        if(admitted_ratio == 0):
                            dkey =   str(each_test_type['ac']) + "_" + \
                                     str(each_test_type['mp']) + "_" + \
                                     str(each_test_type['pr']) + "_" + \
                                     str(each_test_type['cmb']) + "_" + \
                                     str(each_seed) + "_" + \
                                     str(cc) + "_" + \
                                     str(cc_uid)
                                                           
                            global_admission_rate_eq_zero[dkey] = {
                                                           "AC" : each_test_type['ac'],
                                                           "MP" : each_test_type['mp'],
                                                           "PR" : each_test_type['pr'],
                                                           "CMB" : each_test_type['cmb'],
                                                           'seed' : each_seed,
                                                           'fname' : fname,
                                                           'total_num_streams' : total_num_streams,
                                                           'cc' : str(cc),
                                                           'ccuid' : str(cc_uid),
                                                           'res_list' : each_res_combo['res_list']
                                                          }
                        
                        # record metric
                        all_admission_ratio.append(admitted_ratio)                    
                        
                    except Exception, e:
                        print "exception"
                        print e
                        tb = traceback.format_exc()
                        print tb  
                        sys.exit()                  
                
                entry = {
                          'cc' : cc,
                          'res_list': each_res_combo['res_list'],
                          'avg_cc': each_res_combo['avg_cc'],
                          #'utilisation_taskset' : utilisation_of_all_tasks,
                          #'num_vidstrm_accepted_but_late' : num_vidstrm_accepted_but_late,
                          #'num_vidstrm_dropped_tasks' : num_vidstrm_dropped_tasks,
                          #'num_vidstrm_rejected' : num_vidstrm_rejected,
                          #'num_vidstrm_accepted_success' : num_vidstrm_accepted_success,
                          #'num_total_streams' : total_num_streams,
                          'admitted_ratio_allseeds' : all_admission_ratio,
                          'mean_admitted_ratio_allseeds' : np.mean(all_admission_ratio)
                         }
                                        
                all_exp_results_listbased[exp_key].append(entry)            
                        
                print count_temp
                #pprint.pprint(global_admission_rate_eq_zero)
        
        # save results
        _write_formatted_file(FNAME_DATA_OUT_ADMINRATES, all_exp_results_listbased, "json")
    
    
    
    
    ## get data from dump file
    else:
        fname = FNAME_DATA_OUT_ADMINRATES   
        json_data=open(fname)
        file_data = json.load(json_data)
        all_exp_results_listbased = file_data

    
    # for small number of samples
    if (bar_plot == True):
        #######################################
        ### step plot with equal width bins ###
            
        ## now we plot
        fig = plt.figure(figsize=(8*1.2, 6*1.2))
        fig.canvas.set_window_title('plot_Util_vs_VSInfo')
        ax = plt.subplot(111)        
        legend_bars = []    
        
        scatter_colors = plt.get_cmap('Blues')(np.linspace(0, 1.0, len(global_types_of_tests)))
        scatter_markers = ["1", "2", "3", "4", "8", "D", "o", "x", "s", "*", "+"]        
        positions = OrderedDict()        
        exp_metric = 'mean_admitted_ratio_allseeds'
        
        key_order = ["IPC", "LWCRS", "PP", "BN", "LU","LM", "GA-MP"] 
        
        width = 0.10
        
        rects_list = []
        rect_lbl_list = []
        i=0
        for k in key_order:
            each_exp = all_exp_results_listbased[k]
            label = k 
            
            # sorted_results        
            sorted_results = sorted(each_exp, key=lambda k: k['cc'])
            
            sorted_cc_list = [x['cc'] for x in  sorted_results]
            all_admitted_ratio = [x[exp_metric]*float(100.0) for x in  sorted_results]
            
            ind = np.arange(len(sorted_cc_list))
            x_data = sorted_cc_list
            y_data = all_admitted_ratio            
            
            x = sorted_cc_list            
            y = [ np.mean(q) for q in y_data]
            
            rect = plt.bar(ind+(width*i), y, width, color=GLOBAL_COLS[k])
            plt.hold(True)
            rects_list.append(rect)
            rect_lbl_list.append(k)
            
            i+=1
            
        plt.grid(b=True, which='major', color='k', linestyle='-', alpha=0.5)
        plt.grid(b=True, which='minor', color='k', linestyle='--', alpha=0.2)
        plt.minorticks_on()
        #plt.yscale('log')
        #plt.xscale('log')
        leg = plt.legend(rects_list, rect_lbl_list,ncol=3)
        leg.draggable(True)
        ax.tick_params(axis = 'both', which = 'both')
        ax.set_ylabel('Mean admission rate (%)', fontsize=20)        
        ax.set_xlabel('Workload', fontsize=20)        
        ax.xaxis.major.formatter._useMathText = True
        plt.ticklabel_format(style='sci', axis='x', scilimits=(0,0), labelsize=20)
        plt.tick_params(axis='both', which='major', labelsize=16)
        plt.tick_params(axis='both', which='minor', labelsize=16)
        plt.rc('font', **{'size':'16'})
        ax.set_xticks(ind+((width*7)/2) )
        ax.set_xticklabels( [r"$%.1f\times10^4$"% (round(float(x)/10000.0,1)) + "\n" + "(%d VSs)"%_get_wfs_for_cc(x) for x in sorted_cc_list] )
        plt.rcParams['mathtext.default'] = 'regular'
    
    
    return all_exp_results_listbased
    
    
def plot_Load_vs_OverallSysUtil(normal_plot = True, bin_plot = False, bar_plot=False, load_data_from_file=False):
    
    ## get data from experiment files
    if(load_data_from_file==False):
    
        # get res_combos 
        rand_seed = 1234    
        res_arr = [(720,576), (544,576), (528,576), (480,576), (426,240), (320,240), (240,180), (230,180)]
        max_num_wfs = 10
        #res_combos = generate_resolution_combos(max_num_wfs-1,res_arr,rand_seed,sampled=True)
        res_combos = generate_resolution_combos(max_num_wfs-1,res_arr,rand_seed, 
                                        sampled=True, 
                                        reduced_samples=10, 
                                        total_samples=20000,
                                        lower_limit=80000)
        # remove specific wf
        res_combos, target_ix = _remove_custom_wf(res_combos, 1800504, 9)
        # add custom wf
        res_combos.insert(target_ix, _get_custom_wf_cc1772928_wfs7())
        
        all_exp_results_listbased = OrderedDict()        
        colors = ['b', 'r', 'b', 'r']
        markers = ['x', 'x', 'o', 'o']
        
        for each_test_type in global_types_of_tests:
            
            exp_key =  "AC"+ str(each_test_type['ac']) + "_" + \
                             "MP"+ str(each_test_type['mp']) + "_" + \
                             "PR"+ str(each_test_type['pr']) + "_" + \
                             "CMB"+ str(each_test_type['cmb'])
                   
            exp_key = each_test_type['lbl']            
            all_exp_results_listbased[exp_key] = []
            
            for each_res_combo in res_combos:        
                cc = each_res_combo['cc']
                if cc > MAX_CC_LEVEL:
                    continue
                cc_uid = each_res_combo['cc_uid']
                all_util_ratio = []              
                
                for each_seed in RANDOM_SEEDS:
                    print "Get Util : exp_key = " + str(exp_key) + ", cc = " + str(cc) + ", seed = " + str(each_seed)                    
                    try:
                        subdir = "seed_" + str(each_seed) + "/" +"ac"+str(each_test_type['ac'])+"mp"+str(each_test_type['mp'])+"pr"+str(each_test_type['pr'])+"cmb"+str(each_test_type['cmb'])+"/"
                        # get data for no-ac, LUM
                        prefix = "HRTVid_" + \
                                     "AC" + str(each_test_type['ac']) + "_" + \
                                     "MP" + str(each_test_type['mp']) + "_" + \
                                     "PR" + str(each_test_type['pr']) + "_" + \
                                     "CMB" + str(each_test_type['cmb']) + "_" + \
                                     "cc" + str(cc) + "-" + str(cc_uid) + "_"
                                     
                                     
                        fname_prefix = EXP_DATADIR+subdir+prefix+str(NOC_H)+"_"+str(NOC_W)+"_"
                        
                        ## get utilisation value
                        fname = fname_prefix+"test__utilshort.js"    
                        json_data=open(fname)
                        file_data = json.load(json_data)
                        
                        if (_is_zero_admin_rate(
                                                each_test_type['ac'],
                                                each_test_type['mp'], 
                                                each_test_type['pr'], 
                                                each_test_type['cmb'], 
                                                cc, 
                                                cc_uid) == True):
                            #simulation_time = file_data['node_idle_time'][-1]['time']
                            simulation_time = file_data['node_idle_time']['time']
                            all_nodes_idle_times = []
                            overall_system_busy_percentage = 0.0
                        else:
                            # idle time counter
                            #all_nodes_idle_times = file_data['node_idle_time'][-1]['it_c']
                            #simulation_time = file_data['node_idle_time'][-1]['time']
                            all_nodes_idle_times = file_data['node_idle_time']['it_c']
                            simulation_time = file_data['node_idle_time']['time']
                            overall_system_busy_percentage = (1.0-float(float(np.mean(all_nodes_idle_times))/float(simulation_time)))*100.0
                        
                        
                        all_util_ratio.append(overall_system_busy_percentage)
                        
                    except Exception, e:
                        #print e
                        tb = traceback.format_exc()
                        print tb
                    
                    
                entry = {
                          'cc' : cc,
                          'res_list': each_res_combo['res_list'],                          
                          #'all_nodes_idle_times' : all_nodes_idle_times,
                          #'simulation_time' : simulation_time,
                          #'overall_system_busy_percentage' : overall_system_busy_percentage,
                          'all_util_ratio_all_seeds' : all_util_ratio,
                          'mean_all_util_ratio_allseeds' : np.mean(all_util_ratio)                          
                         }
                                        
                all_exp_results_listbased[exp_key].append(entry)
            
        
        # save results
        _write_formatted_file(FNAME_DATA_OUT_PEUTIL, all_exp_results_listbased, "json")
    
    ## get data from dump file
    else:
        fname = FNAME_DATA_OUT_PEUTIL 
        json_data=open(fname)
        file_data = json.load(json_data)
        all_exp_results_listbased = file_data
    
    # for small number of samples
    if (bar_plot == True):
        #######################################
        ### step plot with equal width bins ###
            
        ## now we plot
        fig = plt.figure(figsize=(8*1.2, 6*1.2))
        fig.canvas.set_window_title('plot_Load_vs_OverallSysUtil')
        ax = plt.subplot(111)        
        legend_bars = []    
        
        scatter_colors = plt.get_cmap('Blues')(np.linspace(0, 1.0, len(global_types_of_tests)))

        #scatter_colors = ["#FF0000", "#00FF00" , "#0000FF", "#FFA200", "#FF00F7", "#00FBFF"]
        scatter_markers = ["1", "2", "3", "4", "8", "D", "o", "x", "s", "*", "+"]        
        positions = OrderedDict()        
        exp_metric = 'mean_all_util_ratio_allseeds'
        
        key_order = ["IPC", "LWCRS", "PP", "BN", "LU","LM", "GA-MP"] 
        
        width = 0.10
        
        #for k, each_exp in all_exp_results_listbased.iteritems():
        rects_list = []
        rect_lbl_list = []
        i=0
        for k in key_order:
            each_exp = all_exp_results_listbased[k]
            label = k 
            
            # sorted_results        
            sorted_results = sorted(each_exp, key=lambda k: k['cc'])
            
            sorted_cc_list = [x['cc'] for x in  sorted_results]
            all_util = [x[exp_metric] for x in  sorted_results]
            
            ind = np.arange(len(sorted_cc_list))
            x_data = sorted_cc_list
            y_data = all_util            
            
            x = sorted_cc_list            
            y = [ np.mean(q) for q in y_data]
            
            #rect = plt.bar(ind+(width*i), y, width, color=scatter_colors[i])
            rect = plt.bar(ind+(width*i), y, width, color=GLOBAL_COLS[k])
            plt.hold(True)
            rects_list.append(rect)
            rect_lbl_list.append(k)
            
            i+=1
            
        plt.grid(b=True, which='major', color='k', linestyle='-', alpha=0.5)
        plt.grid(b=True, which='minor', color='k', linestyle='--', alpha=0.2)
        plt.minorticks_on()
        #plt.yscale('log')
        #plt.xscale('log')
        leg = plt.legend(rects_list, rect_lbl_list,ncol=3)
        leg.draggable(True)
        ax.tick_params(axis = 'both', which = 'both')
        ax.set_ylabel('Mean PE busy time (%)', fontsize=20)        
        ax.set_xlabel('Workload', fontsize=20)        
        ax.xaxis.major.formatter._useMathText = True
        plt.ticklabel_format(style='sci', axis='x', scilimits=(0,0), labelsize=20)
        plt.tick_params(axis='both', which='major', labelsize=16)
        plt.tick_params(axis='both', which='minor', labelsize=16)
        plt.rc('font', **{'size':'16'})
        ax.set_xticks(ind+((width*7)/2) )
        ax.set_xticklabels( [r"$%.1f\times10^4$"% (round(float(x)/10000.0,1)) + "\n" + "(%d VSs)"%_get_wfs_for_cc(x) for x in sorted_cc_list] )
        plt.rcParams['mathtext.default'] = 'regular'
    
    
    return all_exp_results_listbased









def plot_Load_vs_OverallNoCUtil(normal_plot = True, bin_plot = False, bar_plot=False, load_data_from_file=False):
    
    ## get data from experiment files
    if(load_data_from_file==False):
    
        # get res_combos 
        rand_seed = 1234    
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
        
        all_exp_results_listbased = OrderedDict()        
        colors = ['b', 'r', 'b', 'r']
        markers = ['x', 'x', 'o', 'o']
        
        for each_test_type in global_types_of_tests:
            
            exp_key =  "AC"+ str(each_test_type['ac']) + "_" + \
                             "MP"+ str(each_test_type['mp']) + "_" + \
                             "PR"+ str(each_test_type['pr']) + "_" + \
                             "CMB"+ str(each_test_type['cmb'])
                   
            exp_key = each_test_type['lbl']            
            all_exp_results_listbased[exp_key] = []
            
            for each_res_combo in res_combos:        
                cc = each_res_combo['cc']
                if cc > MAX_CC_LEVEL:
                    continue
                cc_uid = each_res_combo['cc_uid']
                all_util_ratio = []              
                
                for each_seed in RANDOM_SEEDS:
                    print "Get Util : exp_key = " + str(exp_key) + ", cc = " + str(cc) + ", seed = " + str(each_seed)                    
                    try:
                        subdir = "seed_" + str(each_seed) + "/" +"ac"+str(each_test_type['ac'])+"mp"+str(each_test_type['mp'])+"pr"+str(each_test_type['pr'])+"cmb"+str(each_test_type['cmb'])+"/"
                        # get data for no-ac, LUM
                        prefix = "HRTVid_" + \
                                     "AC" + str(each_test_type['ac']) + "_" + \
                                     "MP" + str(each_test_type['mp']) + "_" + \
                                     "PR" + str(each_test_type['pr']) + "_" + \
                                     "CMB" + str(each_test_type['cmb']) + "_" + \
                                     "cc" + str(cc) + "-" + str(cc_uid) + "_"
                                     
                                     
                        fname_prefix = EXP_DATADIR+subdir+prefix+str(NOC_H)+"_"+str(NOC_W)+"_"
                        
                        ## get utilisation value
                        fname = fname_prefix+"test__utilshort.js"    
                        json_data=open(fname)
                        file_data = json.load(json_data)
                        
                        if (_is_zero_admin_rate(
                                                each_test_type['ac'],
                                                each_test_type['mp'], 
                                                each_test_type['pr'], 
                                                each_test_type['cmb'], 
                                                cc, 
                                                cc_uid) == True):
                            
                            simulation_time = file_data['interconnect']['time']
                            all_nodes_idle_times = []
                            overall_noc_busy_percentage = 0.0
                        else:
                            # idle time counter                            
                            all_links_idle_times = file_data['interconnect']['total_link_idletime']
                            num_noc_links = int(len(file_data['interconnect']['lsp_fc']))
                            mean_link_idle_time = float(float(all_links_idle_times)/float(num_noc_links))
                            simulation_time = file_data['interconnect']['time']
                            overall_noc_busy_percentage = (1.0- (mean_link_idle_time/float(simulation_time)))*100.0
                        
                        
                        all_util_ratio.append(overall_noc_busy_percentage)
                        
                    except Exception, e:
                        #print e
                        tb = traceback.format_exc()
                        print tb
                    
                    
                entry = {
                          'cc' : cc,
                          'res_list': each_res_combo['res_list'],                          
                          #'all_nodes_idle_times' : all_nodes_idle_times,
                          #'simulation_time' : simulation_time,
                          #'overall_system_busy_percentage' : overall_system_busy_percentage,
                          'all_util_ratio_all_seeds' : all_util_ratio,
                          'mean_all_util_ratio_allseeds' : np.mean(all_util_ratio)                          
                         }
                                        
                all_exp_results_listbased[exp_key].append(entry)
            
        
        # save results
        _write_formatted_file(FNAME_DATA_OUT_NOCUTIL, all_exp_results_listbased, "json")
    
    ## get data from dump file
    else:
        fname = FNAME_DATA_OUT_NOCUTIL 
        json_data=open(fname)
        file_data = json.load(json_data)
        all_exp_results_listbased = file_data
    
    # for small number of samples
    if (bar_plot == True):
            
        ## now we plot
        fig = plt.figure(figsize=(8*1.2, 6*1.2))
        fig.canvas.set_window_title('data_Load_vs_OverallNoCUtil')
        ax = plt.subplot(111)        
        scatter_colors = plt.get_cmap('Blues')(np.linspace(0, 1.0, len(global_types_of_tests)))
                
        exp_metric = 'mean_all_util_ratio_allseeds'        
        key_order = ["IPC", "LWCRS", "PP", "BN", "LU","LM", "GA-MP"] 
        
        width = 0.10
        rects_list = []
        rect_lbl_list = []
        i=0
        for k in key_order:
            each_exp = all_exp_results_listbased[k]
            label = k 
            
            # sorted_results        
            sorted_results = sorted(each_exp, key=lambda k: k['cc'])
            
            sorted_cc_list = [x['cc'] for x in  sorted_results]
            all_util = [x[exp_metric] for x in  sorted_results]
            
            ind = np.arange(len(sorted_cc_list))
            x_data = sorted_cc_list
            y_data = all_util            
            
            x = sorted_cc_list            
            y = [ np.mean(q) for q in y_data]
            
            #rect = plt.bar(ind+(width*i), y, width, color=scatter_colors[i])
            rect = plt.bar(ind+(width*i), y, width, color=GLOBAL_COLS[k])
            plt.hold(True)
            rects_list.append(rect)
            rect_lbl_list.append(k)
            
            i+=1
            
        plt.grid(b=True, which='major', color='k', linestyle='-', alpha=0.5)
        plt.grid(b=True, which='minor', color='k', linestyle='--', alpha=0.2)
        plt.minorticks_on()
        leg = plt.legend(rects_list, rect_lbl_list,ncol=3)
        leg.draggable(True)
        ax.tick_params(axis = 'both', which = 'both')
        ax.set_ylabel('Mean NoC busy time (%)', fontsize=20)        
        ax.set_xlabel('Workload', fontsize=20)        
        ax.xaxis.major.formatter._useMathText = True
        plt.ticklabel_format(style='sci', axis='x', scilimits=(0,0), labelsize=20)
        plt.tick_params(axis='both', which='major', labelsize=16)
        plt.tick_params(axis='both', which='minor', labelsize=16)
        plt.rc('font', **{'size':'16'})
        ax.set_xticks(ind+((width*7)/2) )
        ax.set_xticklabels( [r"$%.1f\times10^4$"% (round(float(x)/10000.0,1)) + "\n" + "(%d VSs)"%_get_wfs_for_cc(x) for x in sorted_cc_list] )
        plt.rcParams['mathtext.default'] = 'regular'
    
    
    return all_exp_results_listbased






def plot_Load_vs_AdmittedLoad(normal_plot = True, bin_plot = False, bar_plot=False, load_data_from_file=False):    
    global global_admission_rate_eq_zero    
    reject_cc_list = []
    
    ## get data from experiment files
    if(load_data_from_file==False):
    
        # get res_combos 
        rand_seed = 1234    
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
        
        all_exp_results_listbased = OrderedDict()    
        colors = ['b', 'r', 'b', 'r']
        markers = ['x', 'x', 'o', 'o']
        
        for each_test_type in global_types_of_tests:
            exp_key =  "AC"+ str(each_test_type['ac']) + "_" + \
                                 "MP"+ str(each_test_type['mp']) + "_" + \
                                 "PR"+ str(each_test_type['pr']) + "_" + \
                                 "CMB"+ str(each_test_type['cmb'])
            exp_key = each_test_type['lbl']        
            all_exp_results_listbased[exp_key] = []
            
            #print "exp_key = " + exp_key
            count_temp = 0
            for each_res_combo in res_combos:
                cc = each_res_combo['cc']                    
                if cc > MAX_CC_LEVEL:
                    continue
                
                if cc in reject_cc_list:
                    continue
                
                #print cc      
                cc_uid = each_res_combo['cc_uid']   
                all_total_admitted_load = []              
                for each_seed in RANDOM_SEEDS:
                    print "Get VSInfo : exp_key = " + str(exp_key) + ", cc = " + str(cc) + ", seed = " + str(each_seed) 
                    try:            
                                                
                        subdir = "seed_" + str(each_seed) + "/" +"ac"+str(each_test_type['ac'])+"mp"+str(each_test_type['mp'])+"pr"+str(each_test_type['pr'])+"cmb"+str(each_test_type['cmb'])+"/"
                        # get data for no-ac, LUM
                        prefix = "HRTVid_" + \
                                     "AC" + str(each_test_type['ac']) + "_" + \
                                     "MP" + str(each_test_type['mp']) + "_" + \
                                     "PR" + str(each_test_type['pr']) + "_" + \
                                     "CMB" + str(each_test_type['cmb']) + "_" + \
                                     "cc" + str(cc) + "-" + str(cc_uid) + "_"                             
                                     
                        fname_prefix = EXP_DATADIR+subdir+prefix+str(NOC_H)+"_"+str(NOC_W)+"_"
                        
                        ## get video accept/reject/late list
                        fname = fname_prefix+"test__gopsopbuffsummshort.js"    
                        json_data=open(fname)
                        file_data = json.load(json_data)
                        
                        # this is the estimated load for all gops that were admitted.
                        # we estimate using the priority value
                        total_admitted_load_approx = np.sum([
                                                      ((float(MAX_TASK_PRIORITY) - float(g['gop_mean_pri'])) + (float(g['dispatch_time'])*10.0))
                                                      for ugid,g in file_data.iteritems()
                                                      ])
                        
                        # record metric
                        all_total_admitted_load.append(total_admitted_load_approx)                    
                        
                    except Exception, e:
                        print "exception"
                        print e
                        tb = traceback.format_exc()
                        print tb                    
                
                entry = {
                          'cc' : cc,
                          'res_list': each_res_combo['res_list'],
                          'avg_cc': each_res_combo['avg_cc'],                          
                          'admitted_load_allseeds' : all_total_admitted_load,
                          'mean_admitted_load_allseeds' : np.mean(all_total_admitted_load)
                         }
                                        
                all_exp_results_listbased[exp_key].append(entry)            
                        
                print count_temp
                
        # save results
        _write_formatted_file(FNAME_DATA_OUT_ADMINLOAD, all_exp_results_listbased, "json")
    
    
    ## get data from dump file
    else:
        fname = FNAME_DATA_OUT_ADMINLOAD   
        json_data=open(fname)
        file_data = json.load(json_data)
        all_exp_results_listbased = file_data

    
    # for small number of samples
    if (bar_plot == True):
        #######################################
        ### step plot with equal width bins ###
            
        ## now we plot
        fig = plt.figure(figsize=(8*1.2, 6*1.2))
        fig.canvas.set_window_title('data_Load_vs_AdmittedLoad')
        ax = plt.subplot(111)        
        
        scatter_colors = plt.get_cmap('Blues')(np.linspace(0, 1.0, len(global_types_of_tests)))            
        exp_metric = 'mean_admitted_load_allseeds'        
        key_order = ["IPC", "LWCRS", "PP", "BN", "LU","LM", "GA-MP"] 
        
        width = 0.10
        
        rects_list = []
        rect_lbl_list = []
        i=0
        for k in key_order:
            each_exp = all_exp_results_listbased[k]
            
            # sorted_results        
            sorted_results = sorted(each_exp, key=lambda k: k['cc'])
            
            sorted_cc_list = [x['cc'] for x in  sorted_results]
            all_admitted_load = [x[exp_metric] for x in  sorted_results]
            
            ind = np.arange(len(sorted_cc_list))
            x_data = sorted_cc_list
            y_data = all_admitted_load            
            
            x = sorted_cc_list            
            y = [ np.mean(q) for q in y_data]
            
            #rect = plt.bar(ind+(width*i), y, width, color=scatter_colors[i])
            rect = plt.bar(ind+(width*i), y, width, color=GLOBAL_COLS[k])
            plt.hold(True)
            rects_list.append(rect)
            rect_lbl_list.append(k)
            
            i+=1
            
        plt.grid(b=True, which='major', color='k', linestyle='-', alpha=0.5)
        plt.grid(b=True, which='minor', color='k', linestyle='--', alpha=0.2)
        plt.minorticks_on()        
        leg = plt.legend(rects_list, rect_lbl_list,ncol=3)
        leg.draggable(True)
        ax.tick_params(axis = 'both', which = 'both')
        ax.set_ylabel('Mean admitted load', fontsize=20)        
        ax.set_xlabel('Workload', fontsize=20)        
        ax.xaxis.major.formatter._useMathText = True
        plt.ticklabel_format(style='sci', axis='x', scilimits=(0,0), labelsize=20)
        plt.tick_params(axis='both', which='major', labelsize=16)
        plt.tick_params(axis='both', which='minor', labelsize=16)
        plt.rc('font', **{'size':'16'})
        ax.set_xticks(ind+((width*7)/2) )
        ax.set_xticklabels( [r"$%.1f\times10^4$"% (round(float(x)/10000.0,1)) + "\n" + "(%d VSs)"%_get_wfs_for_cc(x) for x in sorted_cc_list] )
        plt.rcParams['mathtext.default'] = 'regular'
    
    
    return all_exp_results_listbased








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
            

def _is_zero_admin_rate(ac,mp, pr, cmb, cc, ccuid):
    
    dkey =   str(ac) + "_" + \
             str(mp) + "_" + \
             str(pr) + "_" + \
             str(cmb) + "_" + \
             str(cc) + "_" + \
             str(ccuid)
    
    if dkey in global_admission_rate_eq_zero:
        return True
    else:
        return False


def plot_Util_vs_Schedulability():
    
    # get res_combos 
    rand_seed = 1234
    res_arr = [(720,576), (544,576), (528,576), (480,576), (426,240), (320,240), (240,180)]
    max_num_wfs = 7
    res_combos = generate_resolution_combos(max_num_wfs-1,res_arr,rand_seed)
    all_exp_results_listbased = {}    
    colors = ['b', 'r']    
   
    
    for each_test_type in global_types_of_tests:
        
        exp_key =  "AC"+ str(each_test_type['ac']) + "_" + \
                         "MP"+ str(each_test_type['mp']) + "_" + \
                         "PR"+ str(each_test_type['pr']) + "_" + \
                         "CMB"+ str(each_test_type['cmb'])
        
       
        all_exp_results_listbased[exp_key] = []
        
        utilisation_list = []
        schedulablability_actual = []
        schedulablability_analytical = []
        
        for each_res_combo in res_combos:        
            
            try:            
                cc = each_res_combo['cc']                
                subdir = "ac"+str(each_test_type['ac'])+"mp"+str(each_test_type['mp'])+"pr"+str(each_test_type['pr'])+"cmb"+str(each_test_type['cmb'])+"/"
                # get data for no-ac, LUM
                prefix = "HRTVid_" + \
                             "AC"+ str(each_test_type['ac']) + "_" + \
                             "MP"+ str(each_test_type['mp']) + "_" + \
                             "PR"+ str(each_test_type['pr']) + "_" + \
                             "CMB"+ str(each_test_type['cmb']) + "_" +\
                             "cc"+ str(cc) + "_"
                             
                fname_prefix = EXP_DATADIR+subdir+prefix+str(NOC_H)+"_"+str(NOC_W)+"_"
                #print fname_prefix           
                
                # ACTUAL : how many gops were schedulable ?
                fname = fname_prefix+"test__gopsopbuffsumm.js"    
                json_data=open(fname)
                file_data = json.load(json_data)
                
                total_num_gops = len(file_data)
                count_late_gops = 0 
                for k, each_gop in file_data.iteritems():
                    if(each_gop['gop_execution_lateness'] > 0):
                        count_late_gops+=1
                
                actual_schedulable_gop_percentage = 1.0- float(float(count_late_gops)/float(total_num_gops))
                schedulablability_actual.append(actual_schedulable_gop_percentage)
                            
                # ANALYTICAL : how many gops were analytically deemed schedulable ?
                fname = fname_prefix+"test__utilvsschedresults.js"    
                json_data=open(fname)
                file_data = json.load(json_data)
                
                # we only look at the last entry, because that has all the vids that entered
                #pprint.pprint(file_data)
                utilisation_of_all_tasks = file_data[-1]['all_task_util'][1]            
                utilisation_list.append(utilisation_of_all_tasks)
                
                num_gops_late = 0
                total_num_gops = 0
                for each_vid in file_data[-1]['vid_streams_wcrt_info']:
                    strm_key    = each_vid[0]
                    strm_res    = each_vid[1]
                    strm_wcet   = each_vid[2]
                    strm_num_gops   = each_vid[3]
                    
                    if(strm_wcet > 0.48):
                        num_gops_late += strm_num_gops                
                    
                    total_num_gops += strm_num_gops
                
                analytically_schedulable_gop_percentage = 1.0 - float(float(num_gops_late)/float(total_num_gops))
                schedulablability_analytical.append(analytically_schedulable_gop_percentage)
                
                entry = {
                         'cc' : cc,
                         'res_list': each_res_combo['res_list'],
                         'avg_cc': each_res_combo['avg_cc'],
                         'utilisation_taskset' : utilisation_of_all_tasks,
                         'actual_schedulable_gop_percentage' : actual_schedulable_gop_percentage,
                         'analytically_schedulable_gop_percentage' : analytically_schedulable_gop_percentage
                         }
                
                
                all_exp_results_listbased[exp_key].append(entry)
                
            except Exception, e:
                print e
       
    ## now we plot
    fig = plt.figure()
    fig.canvas.set_window_title('plot_Util_vs_Schedulability')
    ax = plt.subplot(111)
    i = 0
    for k, each_exp in all_exp_results_listbased.iteritems():
        label = k 
        
        # sorted_results
        sorted_results = sorted(each_exp, key=lambda k: k['utilisation_taskset']) 
        #sorted_results = sorted(each_exp, key=lambda k: k['cc']) 
        
        sorted_cc_list = [x['cc'] for x in  sorted_results]
        sorted_util_list = [x['utilisation_taskset'] for x in  sorted_results]
        sorted_avgcc_list = [x['avg_cc'] for x in  sorted_results]
        sorted_shed_actual =  [x['actual_schedulable_gop_percentage'] for x in  sorted_results]
        sorted_shed_analytical =  [x['analytically_schedulable_gop_percentage'] for x in  sorted_results]
        
        x_data = sorted_cc_list
        y_data = sorted_shed_analytical
        
        plt.scatter(x_data, y_data, color=colors[i], marker='x', alpha=0.5)   
        plt.hold(True)        
        
        # regression
        slope, intercept, r_value, p_value, std_err = scipy.stats.linregress(x_data,y_data)
        line = slope*np.array(x_data)+intercept
        plt.plot(x_data,line, marker='', linestyle='--', linewidth=2,color=colors[i])        
        
        #p, residuals, rank, singular_values, rcond = np.polyfit(x_data, y_data, 5, full=True)
        #fit_fn = np.poly1d(p)
        #xtick = np.linspace(0, np.max(x_data), num=len(x_data))
        #plt.plot(xtick,fit_fn(x_data),color=colors[i], marker='', linestyle='--', linewidth=2, label='Polynomial Regression fit')
        #plt.scatter(sorted_util_list, sorted_shed_analytical, color='r', marker='x')
        #plt.plot(sorted_util_list, yEXP, color='r', linestyle='--')
        #plt.plot(sorted_util_list, sorted_shed_analytical, color='r', marker='x', linestyle='')
        
        i+=1
    plt.grid(True)
        
            
def func_fit_data(x, a, b, c):
    return a * np.exp(-b * x) + c        
        




def plot_combined_adminrate_and_util(data_adminrate, data_util, data_noc_util, data_adminload):
    
    ## now we plot    
    f, (ax1, ax2, ax3) = plt.subplots(3, sharex=True)
    #f, (ax1, ax2, ax3, ax4) = plt.subplots(4, sharex=True)
    
    scatter_colors = plt.get_cmap('Blues')(np.linspace(0, 1.0, len(global_types_of_tests)))    
            
    key_order = ["IPC", "LWCRS", "PP", "BN", "LU","LM", "GA-MP"] 
    #key_order = ["IPC", "LWCRS", "PP", "BN", "LU","LM"]
    
    width = 0.10
    
    rects_list_adminrate = []
    rect_lbl_list_adminrate = []
    rects_list_util = []
    rect_lbl_list_util = []
    
    i=0
    for k in key_order:
        each_exp_adminrate = data_adminrate[k]
        each_exp_util = data_util[k]
        each_exp_noc_util = data_noc_util[k]
        each_exp_adminload = data_adminload[k]
        
        # sorted_results        
        sorted_results_adminrate = sorted(each_exp_adminrate, key=lambda k: k['cc'])
        sorted_results_util = sorted(each_exp_util, key=lambda k: k['cc'])
        sorted_results_noc_util = sorted(each_exp_noc_util, key=lambda k: k['cc'])
        sorted_results_adminload = sorted(each_exp_adminload, key=lambda k: k['cc'])
        
        cc_list = [x['cc'] for x in  sorted_results_adminrate]
        
        ## plot adminrate        
        exp_metric = 'mean_admitted_ratio_allseeds'
        ind = np.arange(len([x['cc'] for x in  sorted_results_adminrate]))        
        y_data = [x[exp_metric]*100.0 for x in sorted_results_adminrate]
        y = [ np.mean(q) for q in y_data]        
        #rect = ax1.bar(ind+(width*i), y, width, color=GLOBAL_COLS[k], hatch=GLOBAL_HATCHES[i], edgecolor='dimgrey') 
        rect = ax1.bar(ind+(width*i), y, width, color=GLOBAL_COLS[k])
        
        
#         if (k == "GA-MP"):
#             # get genpop for each workload
#             cc_list = [x['cc'] for x in  sorted_results_adminrate]
#             genpop_list = [_get_ga_totalevals(cc) for cc in cc_list]        
#             _gen_pop_autolabel(rect, ax1, genpop_list)
               
        rects_list_adminrate.append(rect)
        rect_lbl_list_adminrate.append(k)
        
        ## plot util
        exp_metric = 'mean_all_util_ratio_allseeds'
        ind = np.arange(len([x['cc'] for x in  sorted_results_util]))        
        y_data = [x[exp_metric] for x in  sorted_results_util]
        y = [ np.mean(q) for q in y_data]        
        rect = ax2.bar(ind+(width*i), y, width, color=GLOBAL_COLS[k])        
        #rects_list_util.append(rect)
        #rect_lbl_list_util.append(k)    
        
#         if (k == "GA-MP"):
#             # get genpop for each workload
#             cc_list = [x['cc'] for x in  sorted_results_adminrate]
#             genpop_list = [_get_ga_totalevals(cc) for cc in cc_list]        
#             _gen_pop_autolabel(rect, ax2, genpop_list)
        
        ## plot noc util
        exp_metric = 'mean_all_util_ratio_allseeds'
        ind = np.arange(len([x['cc'] for x in  sorted_results_noc_util]))        
        y_data = [x[exp_metric] for x in  sorted_results_noc_util]
        y = [ np.mean(q) for q in y_data]        
        rect = ax3.bar(ind+(width*i), y, width, color=GLOBAL_COLS[k])        
        rects_list_util.append(rect)
        rect_lbl_list_util.append(k)
        
        
#         ## plot admitted load
#         exp_metric = 'mean_admitted_load_allseeds'
#         ind = np.arange(len([x['cc'] for x in  sorted_results_adminload]))                
#         y_data = [x[exp_metric] for x in  sorted_results_adminload]
#         y = [ np.mean(q) for q in y_data]        
#         rect = ax4.bar(ind+(width*i), y, width, color=scatter_colors[i])        
#         rects_list_util.append(rect)
#         rect_lbl_list_util.append(k)
#         
        i+=1
    
    
    sorted_cc_list = [x['cc'] for x in  sorted_results_adminrate]
    
    #ax1.grid(b=True, which='major', color='k', linestyle='-', alpha=0.5)
    #ax1.grid(b=True, which='minor', color='k', linestyle='--', alpha=0.2)
    #ax1.grid(b=True, which='major')
    ax1.xaxis.grid(False)
    ax1.yaxis.grid(True, which='major')
    ax1.minorticks_on()    
    
    #ax2.grid(b=True, which='major', color='k', linestyle='-', alpha=0.5)
    #ax2.grid(b=True, which='minor', color='k', linestyle='--', alpha=0.2)
    #ax2.grid(b=True, which='major')
    ax2.xaxis.grid(False)
    ax2.yaxis.grid(True, which='major')
    ax2.minorticks_on() 
    
    #ax3.grid(b=True, which='major', color='k', linestyle='-', alpha=0.5)
    #ax3.grid(b=True, which='minor', color='k', linestyle='--', alpha=0.2)
    #ax3.grid(b=True, which='major')
    ax3.xaxis.grid(False)
    ax3.yaxis.grid(True, which='major')
    ax3.minorticks_on() 
    
#     ax4.grid(b=True, which='major', color='k', linestyle='-', alpha=0.5)
#     ax4.grid(b=True, which='minor', color='k', linestyle='--', alpha=0.2)
#     ax4.minorticks_on()
       
       
    
    #leg = plt.legend(rects_list, rect_lbl_list,ncol=3)
    #leg.draggable(True)
    
    ax1.tick_params(axis = 'both', which = 'both')
    ax1.set_ylabel('Mean admission\nrate (%)')        
    #ax1.set_xlabel('Workload', fontsize=20)        
    ax1.xaxis.major.formatter._useMathText = True
    ax1.set_xticks(ind+((width*7)/2) )
    ax1.set_xticklabels( [r"$%.1f\times10^4$"% (round(float(x)/10000.0,1)) + "\n" + "(%d VSs)"%_get_wfs_for_cc(x) for x in sorted_cc_list] )
    
    ax2.tick_params(axis = 'both', which = 'both')
    ax2.set_ylabel('Mean PE\nbusy time (%)')        
    #ax2.set_xlabel('Workload', fontsize=20)        
    ax2.xaxis.major.formatter._useMathText = True
    ax2.set_xticks(ind+((width*7)/2) )
    ax2.set_xticklabels( [r"$%.1f\times10^4$"% (round(float(x)/10000.0,1)) + "\n" + "(%d VSs)"%_get_wfs_for_cc(x) for x in sorted_cc_list] )
    
    ax3.tick_params(axis = 'both', which = 'both')
    ax3.set_ylabel('Mean NoC\nbusy time (%)')        
    ax3.set_xlabel('Workload')        
    ax3.xaxis.major.formatter._useMathText = True
    ax3.set_xticks(ind+((width*7)/2) )
    ax3.set_xticklabels( [r"$%.1f\times10^4$"% (round(float(x)/10000.0,1)) + "\n" + "(%d VSs)"%_get_wfs_for_cc(x) for x in sorted_cc_list] )
    
#     ax4.tick_params(axis = 'both', which = 'both')
#     ax4.set_ylabel('Mean\nAdmitted Load', fontsize=20)        
#     ax4.set_xlabel('Workload', fontsize=20)        
#     ax4.xaxis.major.formatter._useMathText = True
#     ax4.set_xticks(ind+((width*7)/2) )
#     ax4.set_xticklabels( [r"$%.1f\times10^4$"% (round(float(x)/10000.0,1)) + "\n" + "(%d VSs)"%_get_wfs_for_cc(x) for x in sorted_cc_list] )

    
    extra_gap =  (width*1.5)
    vbar_p = (len(key_order) * (width)) + extra_gap
    for i in xrange(1,10):
        ax1.axvline(x= (vbar_p * i) + (extra_gap*(i-1))
                       , linewidth=0.5, color='k', linestyle='--', alpha=0.5)
        
        ax2.axvline(x= (vbar_p * i) + (extra_gap*(i-1))
                       , linewidth=0.5, color='k', linestyle='--', alpha=0.5)
        
        ax3.axvline(x= (vbar_p * i) + (extra_gap*(i-1))
                       , linewidth=0.5, color='k', linestyle='--', alpha=0.5)
    
    
    #ax1.ticklabel_format(style='sci', axis='x', scilimits=(0,0), labelsize=20)
    #ax2.ticklabel_format(style='sci', axis='x', scilimits=(0,0), labelsize=20)
    
    plt.tick_params(axis='both', which='both', labelsize=14)    
    plt.rc('font', **{'size':'16'})
    plt.rcParams['mathtext.default'] = 'regular'
   
    
    leg = f.legend( rects_list_util, rect_lbl_list_util, loc = 'upper center', ncol=4, fontsize=14,
                    bbox_to_anchor = (0,0.02,1,1), bbox_transform = plt.gcf().transFigure)
    
    leg.get_frame().set_facecolor('#FFFFFF')
    leg.get_frame().set_linewidth(0.0)
    
    
    leg.draggable(True)
    


       

###################################
#    HELPERS
###################################
def _normalise_list(lst, norm_min=None, norm_max=None):    
    if norm_max == None:
        norm_max = np.max(lst)    
    if norm_min == None:
        norm_min = np.min(lst)    
    new_list = []
    for each_l in lst:   
        x = each_l     
        norm_val = (x-norm_min)/(norm_max-norm_min)
        new_list.append(norm_val)
    return new_list


def _gen_pop_autolabel(rects, ax, gen_pop_list, fsize=8):
    j=0
    for rect, each_genpop in zip(rects, gen_pop_list):
        height = rect.get_height()
        y_cord = (height *1.01)
        ax.text( rect.get_x()+rect.get_width()/2., y_cord, "GA Evals. :\n" + r"$%d\times10^3$"%(float(each_genpop[2])/1000.0),
                        ha='center', va='bottom', fontsize=fsize)
        
        j+=1             



###################################
#    MAIN
###################################

#plot_Util_vs_Schedulability()

## run these to get proper results (used in paper)

 
data1 = plot_Load_vs_VSInfo(normal_plot=False, bin_plot=False, bar_plot=False, load_data_from_file=False)
data2 = plot_Load_vs_OverallSysUtil(normal_plot=False, bin_plot=False, bar_plot=False, load_data_from_file=False)
data3 = plot_Load_vs_OverallNoCUtil(normal_plot=False, bin_plot=False, bar_plot=False, load_data_from_file=False)
data4 = plot_Load_vs_AdmittedLoad(normal_plot=False, bin_plot=False, bar_plot=False, load_data_from_file=False)


plot_combined_adminrate_and_util(data1, data2, data3, data4)




print "finished"

plt.show()





# class LogFormatterTeXExponent(pylab.LogFormatter, object):
#     """Extends pylab.LogFormatter to use 
#     tex notation for tick labels."""
#     
#     def __init__(self, *args, **kwargs):
#         super(LogFormatterTeXExponent, 
#               self).__init__(*args, **kwargs)
#         
#     def __call__(self, *args, **kwargs):
#         """Wrap call to parent class with 
#         change to tex notation."""
#         label = super(LogFormatterTeXExponent, 
#                       self).__call__(*args, **kwargs)
#         label = re.sub(r'e(\S)0?(\d+)', 
#                        r'\\times 10^{\1\2}', 
#                        str(label))
#         label = "$" + label + "$"
#         return label
