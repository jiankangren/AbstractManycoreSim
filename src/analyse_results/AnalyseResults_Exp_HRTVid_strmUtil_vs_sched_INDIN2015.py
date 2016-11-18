import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

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


NOC_H = 3
NOC_W = 3

MAX_CC_LEVEL = 4000000

RANDOM_SEEDS = [80505, 1234, 81665, 33749, 43894, 26358, 70505, \
83660, 22817, 70263, 29917, 26044, \
76891, 50399, 64217, \
44117, 57824, 42267, 83200, 99108, \
95928, 53864, 44289, 77379, 80521, \
88117, 23327, 73337, 94064, 31982, 22250, \
6878, 66093, 69541, 18065, 74076, 98652, 21149, 42198, 5558]


# for testing
#RANDOM_SEEDS = [81665, 33749, 43894, 26358, 80505, \
#83660, 22817, 70263, 29917, 26044, \
#76891]

RANDOM_SEEDS=\
[

# batch 1
81665, 33749, 43894, 26358, 80505, 83660, 22817, 70263, 29917, 26044, 76891,

# batch 2
50399, 64217, 44117, 57824, 42267, 83200, 99108, 95928, 53864, 44289,

# batch 3     
77379, 80521, 88117, 23327, 73337, 94064, 31982, 22250,

#batch 4
#6878, 66093, 69541, 18065, 74076, 98652, 21149, 42198, 5558, 70505, 1234
6878
]



# correct locations used for thesis draft
#FNAME_DATA_OUT_ADMINRATES = "../experiment_data/hrt_video/HRTVIDShort_data_260716/data_HRTVIDSHORT_Load_vs_VSInfo.js"
#FNAME_DATA_OUT_UTIL = "../experiment_data/hrt_video/HRTVIDShort_data_260716/data_HRTVIDSHORT_Load_vs_OverallSysUtil.js"

# location after bl correction

FNAME_DATA_OUT_ADMINRATES = "../experiment_data/hrt_video/HRTVIDShort_data_BLTest/data_HRTVIDSHORT_Load_vs_VSInfo.js"
FNAME_DATA_OUT_UTIL = "../experiment_data/hrt_video/HRTVIDShort_data_BLTest/data_HRTVIDSHORT_Load_vs_OverallSysUtil.js"




#GLOBAL_COLS = sns.color_palette("Reds", 3)[0:2] # proposed (always 1 more)
#GLOBAL_COLS.extend(sns.color_palette("Blues", 3)[0:2]) # baselines PP, BN (always 1 more)
#GLOBAL_COLS.extend(sns.color_palette("Greens", 3)[0:2]) # baselines LU, LM (always 1 more)


#GLOBAL_COLS = sns.color_palette("Paired", 6)
#GLOBAL_COLS.reverse()


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
               
               
               }

GLOBAL_LINESTYLES = {
                     "IPC" :'-', 
                     "LWCRS":'-',
                     "PP":'--',
                     "BN":'-',
                     "LU": '--',
                     "LM": '-',                      
                     } 

GLOBAL_LINEWIDTH = 2.5

print len(GLOBAL_COLS)

NOC_H = 3
NOC_W = 3

print len(RANDOM_SEEDS)
#sys.exit()

#RANDOM_SEEDS = [81665, 76891]

# correct locations used for thesis draft
#EXP_DATADIR = "../experiment_data/hrt_video/util_vs_sched/"
#EXP_DATADIR = "Z:/MCASim/experiment_data/hrt_video/util_vs_sched/seed_70505/"
#EXP_DATADIR = "Z:/MCASim/experiment_data/hrt_video/util_vs_sched_230415/" # for thesis draft


# location after bl correction
#EXP_DATADIR = "Z:/Simulator_versions_perExperiment/ThesisTechCh5_INDIN/src/experiment_data/hrt_video/util_vs_sched/"
EXP_DATADIR = "../experiment_data/hrt_video/util_vs_sched/"

global_types_of_tests = [
                      
                      ## Deterministic - AC ##

                    #{'ac':11, 'mp':0, 'pr':4, 'cmb':840 }, # determ, lumm
                    
                    {'ac':11, 'mp':0, 'pr':4, 'cmb':841 , 'lbl': "IPC"}, # determ, improved
                    {'ac':11, 'mp':0, 'pr':4, 'cmb':842 , 'lbl': "LWCRS"}, # determ, improved                    
                    {'ac':11, 'mp':0, 'pr':4, 'cmb':833 , 'lbl': "PP"}, # determ, improved
                    {'ac':11, 'mp':0, 'pr':4, 'cmb':834 , 'lbl': "BN"}, # determ, improved
                    ##{'ac':11, 'mp':0, 'pr':4, 'cmb':832 , 'lbl': "BN"}, # determ, improved - not used
                    {'ac':11, 'mp':10, 'pr':4, 'cmb':0 , 'lbl': "LU"}, # determ, improved
                    {'ac':11, 'mp':12, 'pr':4, 'cmb':0 , 'lbl': "LM"}, # determ, improved
                      
                      ]

global_admission_rate_eq_zero = {}

MP_ORDER = ["IPC", "LWCRS", "PP", "BN", "LU", "LM"]
#MP_ORDER = ["IPC", "LWCRS"]

def plot_Load_vs_VSInfo(normal_plot = True, bin_plot = False, load_data_from_file=False):    
    global global_admission_rate_eq_zero
    
    
    ## get data from experiment files
    if(load_data_from_file==False):
    
        # get res_combos 
        rand_seed = 1234    
        res_arr = [(720,576), (544,576), (528,576), (480,576), (426,240), (320,240), (240,180), (230,180)]
        max_num_wfs = 10
        res_combos = generate_resolution_combos(max_num_wfs-1,res_arr,rand_seed, sampled=True)
        
        #print len(res_combos)
        
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
            for rix, each_res_combo in enumerate(res_combos):
                
                print "rix =", rix
                
                cc = each_res_combo['cc']                    
                if cc > MAX_CC_LEVEL:
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
                        #fname = fname_prefix+"test__vsbs.js"
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
        
        
        
        
    
    
    if (bin_plot == True):
        #######################################
        ### step plot with equal width bins ###
            
        ## now we plot
        fig = plt.figure(figsize=(7*1.2, 5*1.2))
        fig.canvas.set_window_title('plot_Util_vs_VSInfo')
        ax = plt.subplot(111)
        i = 0
        legend_bars = []    
        scatter_colors = plt.get_cmap('jet')(np.linspace(0, 1.0, len(global_types_of_tests))) # used for INDIN
        #scatter_colors = ["#FF0000", "#00FF00" , "#0000FF", "#FFA200", "#FF00F7", "#00FBFF"]
        #scatter_colors = GLOBAL_COLS
        scatter_markers = ["1", "2", "3", "4", "8", "D", "o", "x", "s", "*", "+"]        
        positions = OrderedDict()
        binwidth = 50000
        #crop_min = 500000
        crop_min = 0
        crop_max = 2230000
        exp_metric = 'mean_admitted_ratio_allseeds'
        
        #for k, each_exp in all_exp_results_listbased.iteritems():
        for k in MP_ORDER:
            each_exp = all_exp_results_listbased[k]
            label = k 
            
            # sorted_results        
            sorted_results = sorted(each_exp, key=lambda k: k['cc'])
            
            sorted_cc_list = [x['cc'] for x in  sorted_results]
            all_admitted_ratio = [x[exp_metric]*float(100.0) for x in  sorted_results]
            
            
            print sorted_cc_list
            print len(set(sorted_cc_list))
            
            x_data = sorted_cc_list
            y_data = all_admitted_ratio
            
            bins = np.arange(np.min(sorted_cc_list), np.max(sorted_cc_list) + binwidth, binwidth) # create equal width bins
            
            if(positions == {}):
                for ix, each_bin in enumerate(bins):
                    if(ix<(len(bins)-1)):
                        temp_pos = [jx for jx, v in enumerate(x_data) if (v < bins[ix+1] and v > bins[ix])]
                        if temp_pos != []:
                            positions[each_bin] = temp_pos
                        
            y_chunks = []
            for b, each_pos in positions.iteritems():
                y_chunks.append([v for ix, v in enumerate(y_data) if ix in each_pos])
            
            x = positions.keys()            
            y = [ np.mean(q) for q in y_chunks]
            
            plt.step(x,y, color=GLOBAL_COLS[k], label=k, linestyle=GLOBAL_LINESTYLES[k], linewidth=GLOBAL_LINEWIDTH)
            plt.hold(True)
            
            
            x_data_ix_gt_q = [ix for (ix,val) in enumerate(x) if val>crop_min][0]
            x_data_ix_lt_q = [ix for (ix,val) in enumerate(x) if val<crop_max][-1]
            
            # cropped_data
            x_data_cropped = x[x_data_ix_gt_q:x_data_ix_lt_q]
            y_data_cropped = y[x_data_ix_gt_q:x_data_ix_lt_q]
            y_data_cropped = [q if ~np.isnan(q) else 0.0 for q in y_data_cropped]

            i+=1
            
        #plt.grid(b=True, which='major', color='k', linestyle='-', alpha=0.5)
        #plt.grid(b=True, which='minor', color='k', linestyle='--', alpha=0.5)
        #plt.grid(b=True, which='both')
        plt.minorticks_on()
        #plt.yscale('log')
        #plt.xscale('log')
        leg = plt.legend(fontsize=14)
        leg.draggable(True)
        ax.tick_params(axis = 'both', which = 'both', labelsize=14)
        ax.set_ylabel('Mean admission rate (%)')        
        ax.set_xlabel('Workload bins (bin_width=%d)' % binwidth)
        ax.xaxis.major.formatter._useMathText = True
        plt.ticklabel_format(style='sci', axis='x', scilimits=(0,0), labelsize=20)
        plt.tick_params(axis='both', which='major', labelsize=14)
        plt.tick_params(axis='both', which='minor', labelsize=14)
        plt.rc('font', **{'size':'16'})
        plt.subplots_adjust(left=0.09, right=0.98, top=0.98, bottom=0.09)
    
    
    

def plot_Load_vs_OverallSysUtil(normal_plot = True, bin_plot = False, load_data_from_file=False):
    
    ## get data from experiment files
    if(load_data_from_file==False):
    
        # get res_combos 
        rand_seed = 1234    
        res_arr = [(720,576), (544,576), (528,576), (480,576), (426,240), (320,240), (240,180), (230,180)]
        max_num_wfs = 10
        res_combos = generate_resolution_combos(max_num_wfs-1,res_arr,rand_seed,sampled=True)
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
        _write_formatted_file(FNAME_DATA_OUT_UTIL, all_exp_results_listbased, "json")
    
    ## get data from dump file
    else:
        fname = FNAME_DATA_OUT_UTIL  
        json_data=open(fname)
        file_data = json.load(json_data)
        all_exp_results_listbased = file_data
    
    
    
    if(bin_plot == True):
        ####################
        ### bin plot     ###
        
        ## now we plot
        fig = plt.figure(figsize=(7*1.2, 5*1.2))
        #fig.canvas.set_window_title('plot_Load_vs_OverallSysUtil')
        ax = plt.subplot(111)
        i = 0
        legend_bars = []    
        positions = OrderedDict()
        scatter_colors = plt.get_cmap('jet')(np.linspace(0, 1.0, len(global_types_of_tests)))
        scatter_markers = ["1", "2", "3", "4", "8", "D", "o", "x", "s", "*", "+"]
        exp_metric = 'mean_all_util_ratio_allseeds'
        
        for k in MP_ORDER:
            each_exp = all_exp_results_listbased[k]
            label = k 
            
            # sorted_results            
            sorted_results = sorted(each_exp, key=lambda k: k['cc'])
            
            sorted_cc_list = [x['cc'] for x in  sorted_results]
            sorted_overall_system_busy_percentage =  [x[exp_metric] for x in  sorted_results]
                    
            x_data = sorted_cc_list
            y_data = sorted_overall_system_busy_percentage
            
            binwidth = 50000
            bins = np.arange(np.min(sorted_cc_list), np.max(sorted_cc_list) + binwidth, binwidth)
            
            if(positions == {}):
                for ix, each_bin in enumerate(bins):
                    if(ix<(len(bins)-1)):
                        temp_pos = [jx for jx, v in enumerate(x_data) if v < bins[ix+1] and v > bins[ix]]
                        if temp_pos != []:
                            positions[each_bin] = temp_pos
                        
            y_chunks = []
            for b, each_pos in positions.iteritems():
                y_chunks.append([v for ix, v in enumerate(y_data) if ix in each_pos])
            
            x = positions.keys()            
            y = [ np.mean(q) for q in y_chunks]
            
            plt.step(x,y, color=GLOBAL_COLS[k], label=k, linestyle=GLOBAL_LINESTYLES[k], linewidth=GLOBAL_LINEWIDTH)
            plt.hold(True)
            
            crop_min = 500000
            crop_max = 2230000
            x_data_ix_gt_q = [ix for (ix,val) in enumerate(x) if val>crop_min][0]
            x_data_ix_lt_q = [ix for (ix,val) in enumerate(x) if val<crop_max][-1]
            
            # cropped_data
            x_data_cropped = x[x_data_ix_gt_q:x_data_ix_lt_q]
            y_data_cropped = y[x_data_ix_gt_q:x_data_ix_lt_q]
            y_data_cropped = [q if ~np.isnan(q) else 0.0 for q in y_data_cropped]

            i+=1
            
        #plt.grid(b=True, which='major', color='k', linestyle='-', alpha=0.5)
        #plt.grid(b=True, which='minor', color='k', linestyle='--', alpha=0.5)
        plt.minorticks_on()
        #plt.yscale('log')
        #plt.xscale('log')
        leg = plt.legend(fontsize=14)
        leg.draggable(True)
        ax.tick_params(axis = 'both', which = 'both', labelsize=14)        
        ax.set_ylabel('Mean PE busy time (%)')
        ax.set_xlabel('Workload bins (bin_width=%d)' % binwidth)
        ax.xaxis.major.formatter._useMathText = True
        plt.ticklabel_format(style='sci', axis='x', scilimits=(0,0))
        plt.tick_params(axis='both', which='major', labelsize=14)
        plt.tick_params(axis='both', which='minor', labelsize=14)
        plt.rc('font', **{'size':'16'})
        plt.subplots_adjust(left=0.09, right=0.98, top=0.98, bottom=0.09)



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
        
        
       

###################################
#    HELPERS
###################################

            



###################################
#    MAIN
###################################

#plot_Util_vs_Schedulability()


plot_Load_vs_VSInfo(normal_plot=False, bin_plot=True, load_data_from_file=True)
plot_Load_vs_OverallSysUtil(normal_plot=False, bin_plot=True, load_data_from_file=True)



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
