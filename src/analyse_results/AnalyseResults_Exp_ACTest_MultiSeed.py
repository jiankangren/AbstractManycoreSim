import sys, os, csv, pprint, math

from collections import OrderedDict
import numpy as np
import random
import shutil
import math
import matplotlib
matplotlib.use('Qt4Agg')
import matplotlib.pyplot as plt
plt.style.use('bmh_rosh')
#from mpl_toolkits.mplot3d import Axes3D

import itertools
from itertools import cycle # for automatic markers
import json

#from matplotlib.font_manager import FontProperties

#from AdmissionControllerOptions import AdmissionControllerOptions
#from SimParams import SimParams


#import Multicore_MPEG_Model as MMMSim


EXP_NUM_NODES =9

RANDOM_SEED_LIST = \
[81665, 33749, 43894, 26358, 80505, \
 83660, 22817, 70263, 29917, 26044, \
 5558,  76891, 22250, 42198, 18065, \
 74076, 98652, 21149, 50399, 64217, \
 44117, 57824, 42267, 83200, 99108, \
 95928, 53864, 44289, 77379, 80521, \
 88117, 23327, 73337, 94064, 31982, \
 6878, 66093, 69541]



NUM_WORKFLOWS = [8,16]
#NUM_WORKFLOWS = [9]
#NUM_NODES = [2,4,8,16,32]
NUM_NODES = 9
NOC_XY = [(2,1), (2,2), (2,4), (2,8), (2,16)]




RATIO_COMBINATIONS = [(0.5, 0.1), (0.1,0.5), (0.1, 1.0), (0.3, 0.3), (0.3, 0.7), (0.3, 1.0), (0.5, 0.5), (0.7, 0.7), (1.0,1.0)]
        
#EXP_DATA_FOLDER = '../experiment_data/vs_ac_test/'
EXP_DATA_FOLDER = '../experiment_data/vs_ac_test/vs_ac_test_130814_orig/'
#EXP_DATA_FOLDER = '../experiment_data/vs_ac_test/vs_ac_test/'


## with bl correction
#RANDOM_SEED_LIST = \
#[80505, 33749, 29917, 26358, 22817]

EXP_DATA_FOLDER = 'Z:/Simulator_versions_perExperiment/ThesisTechCh4/src/experiment_data/vs_ac_test/'




###################################################################################################
#    Video predictability statistics : schedulable, late, rejected
###################################################################################################

# Admission control tests :
# - None
# - heu based
# - sched based
def plot_ACTest_Results_VidStats_HeuVar(wf_id = None, plot3D = True):

    
    ##############################
    ####### gather results 
    ##############################    
    all_wf_exp_data = {}
    multi_seed_data = {}
    
    #F_PREFIX = "_vsbs.js"
    F_PREFIX = ".js"
    
    for each_wf_id in NUM_WORKFLOWS:
        all_wf_exp_data[each_wf_id] = {}
        
        for each_seed in RANDOM_SEED_LIST:        
        
            exp_data = OrderedDict()      # dict that will contain all the results for each param  
            
            #### ac_test : none      
            FNAME_PREFIX = "ACTest_none_"
            vs_bs_fname = EXP_DATA_FOLDER + "seed_" + str(each_seed) + "/" + FNAME_PREFIX + 'wf'+str(each_wf_id)+'_cores'+str(EXP_NUM_NODES) + F_PREFIX
            print vs_bs_fname
            json_data=open(vs_bs_fname)
            file_data = json.load(json_data)   
            exp_data['No-AC'] = _getEntry(file_data) 
            
            #### ac_test : schedulability test only        
            FNAME_PREFIX = "ACTest_sched_"
            vs_bs_fname = EXP_DATA_FOLDER + "seed_" + str(each_seed) + "/" + FNAME_PREFIX + 'wf'+str(each_wf_id)+'_cores'+str(EXP_NUM_NODES) + F_PREFIX
            print vs_bs_fname
            json_data=open(vs_bs_fname)
            file_data = json.load(json_data)        
            exp_data['D-AC'] = _getEntry(file_data) 
            
#             #### ac_test : schedulability test (tasks only)    
#             FNAME_PREFIX = "ACTest_schedtasksonly_"
#             vs_bs_fname = EXP_DATA_FOLDER + "seed_" + str(each_seed) + "/" + FNAME_PREFIX + 'wf'+str(each_wf_id)+'_cores'+str(EXP_NUM_NODES) + F_PREFIX
#             json_data=open(vs_bs_fname)
#             file_data = json.load(json_data)        
#             exp_data['Deterministic.\n(comp.)'] = _getEntry(file_data) 
             
            #### ac_test : heuristics - KG deadline assignment 
            FNAME_PREFIX = "ACTest_heukgEQF_"
            vs_bs_fname = EXP_DATA_FOLDER + "seed_" + str(each_seed) + "/" + FNAME_PREFIX + 'wf'+str(each_wf_id)+'_cores'+str(EXP_NUM_NODES) + F_PREFIX
            print vs_bs_fname
            json_data=open(vs_bs_fname)
            file_data = json.load(json_data)        
            exp_data['DEQF-AC'] = _getEntry(file_data)
                  
            #### ac_test : heuristics threshold based
            for each_ratio_combo in RATIO_COMBINATIONS:
                
                each_ibuff_ratio = each_ratio_combo[0]
                each_tq_ratio = each_ratio_combo[1]
    
                FNAME_PREFIX = "ACTest_heuth_" + "iblr" + str(each_ibuff_ratio) + "_tqlr" + str(each_tq_ratio) + "_"
                
                vs_bs_fname = EXP_DATA_FOLDER + "seed_" + str(each_seed) + "/" + FNAME_PREFIX + 'wf'+str(each_wf_id)+'_cores'+str(EXP_NUM_NODES) + F_PREFIX
                print vs_bs_fname
                json_data=open(vs_bs_fname)
                file_data = json.load(json_data)
                
                key = "Heu:" + "IBLR_\\alpha" + str(each_ibuff_ratio) + ", TQL_\\alpha" + str(each_tq_ratio)                
                key_2 =  "Heu-AC" + "\n" + "(" + str(each_ibuff_ratio) + "," + str(each_tq_ratio) + ")"
                
                exp_data[key_2] = _getEntry(file_data)        
        
            
            all_wf_exp_data[each_wf_id]['seed_'+str(each_seed)] = exp_data 
       
    
    labels = [('%s'%x) for x in exp_data.keys()] 
    
    #### dump the summary results ####
    _write_formatted_file(EXP_DATA_FOLDER+"data_ACTest_Results_VidStats_HeuVar.js", all_wf_exp_data, format='json')
    
    
    
    ##############################
    ####### plot results
    ##############################    
  
    ################# multiple workflow plot : bar plots ##################
    
    # points scheme
    POINTS_SUCCESS  = 1.0
    POINTS_REJECT   = 0.0
    POINTS_LATE     = -1.0
    POINTS_DROPPED  = -2.0

    f, axarr = plt.subplots(len(NUM_WORKFLOWS), sharex=True)
    f.canvas.set_window_title("Predictability results")
    
    i=0
    t=[]
    for each_wf_id in NUM_WORKFLOWS:
        
        each_wf_data = all_wf_exp_data[each_wf_id]
        each_wf_key = each_wf_id
        
        # --------- number of success & failed ----------          
            
        # data for different results categories
        streams_schedulable = _get_multi_seed_data_vidstats('num_vids_accepted_success', each_wf_data, mean=True)
        streams_schedulable_yerr = _get_multi_seed_data_vidstats_yerr('num_vids_accepted_success', each_wf_data, mean=True)
        
        streams_late = _get_multi_seed_data_vidstats('num_vids_accepted_late', each_wf_data, mean=True)
        streams_late_yerr = _get_multi_seed_data_vidstats_yerr('num_vids_accepted_late', each_wf_data, mean=True)
        
        streams_rejected = _get_multi_seed_data_vidstats('num_vids_rejected', each_wf_data, mean=True)
        streams_rejected_yerr = _get_multi_seed_data_vidstats_yerr('num_vids_rejected', each_wf_data, mean=True)
        
        print "dropped"
        dropped_gops = _get_multi_seed_data_vidstats('num_dropped_tasks', each_wf_data, mean=True)        
        print "dropped-end"
        pprint.pprint(dropped_gops)
        
        dropped_gops = [float(x/12.0) for x in dropped_gops]
        
        #streams_schedulable = [x["num_vids_accepted_success"] for x in each_wf_data.values()]
        #streams_late = [x["num_vids_accepted_late"] for x in each_wf_data.values()]                
        #streams_rejected = [x["num_vids_rejected"] for x in each_wf_data.values()]
        #dropped_gops = [float(x["num_dropped_tasks"]/12.0) for x in each_wf_data.values()]
            
        ind = np.arange(len(streams_schedulable))
        width = 0.20
        positions = [ind, ind+width, ind+(2.0*width), ind+(3.0*width)]
        
        
#        bp0 = axarr[i].boxplot(streams_schedulable, positions=positions[0], widths=width)
#        bp1 = axarr[i].boxplot(streams_late, positions=positions[1], widths=width)
#        bp2 = axarr[i].boxplot(streams_rejected, positions=positions[2], widths=width)   
#        _set_bp(axarr[i],bp0, 'g' )
#        _set_bp(axarr[i],bp1, 'b' )
#        _set_bp(axarr[i],bp2, 'r' )
        
        #p = axarr[i].axvspan(0.0, (width*8.0)+(width*0.5), facecolor='0.5', alpha=0.3)
        
        rects0 = axarr[i].bar(positions[0], streams_schedulable, width=width, color='g', 
                              alpha=0.9, label="Admitted and fully schedulable", yerr=None)                
        rects1 = axarr[i].bar(positions[1], streams_late, width=width, color='b', 
                              alpha=0.9, label="Admitted but late", yerr=None)                
        rects2 = axarr[i].bar(positions[2], streams_rejected, width=width, color='#FF4747', 
                              alpha=0.9, label="Rejected", yerr=None)  
        
        _autolabel(rects0, axarr[i])
        _autolabel(rects1, axarr[i], extra_text=dropped_gops)
        _autolabel(rects2, axarr[i])
         
        axarr[i].grid(True, alpha=0.5)
        t.append(axarr[i].set_title('Number of workflows = '+ str(each_wf_key), fontsize=14))
        
        axarr[i-1].tick_params(axis='both', which='major', labelsize=12)
        
        
        
        
        i+= 1
   
    axarr[i-1].set_xlabel("Admission control test type", fontsize=14)
    f.text(0.015, 0.5, 'Number of video streams', va='center', rotation='vertical', fontsize=14)
    
    leg = plt.legend(ncol=3, loc = 'upper center', fontsize=12, 
                     bbox_to_anchor = (0,0.02,1,1), bbox_transform = plt.gcf().transFigure
            )
    leg.get_frame().set_facecolor('#FFFFFF')
    leg.get_frame().set_linewidth(0.0)
    leg.draggable(True)
    axarr[i-1].set_xticks(ind+(width*1.5))
    axarr[i-1].set_xticklabels( labels , rotation=0)
    #t[0].set_y(1.09)  
    plt.axis('tight')

def _get_multi_seed_data_vidstats(data_filter, all_data, mean=False):    
    each_seed_data = []   
    
    for each_seed in all_data.items():
        data = [x[data_filter] for x in each_seed[1].values()]       
        each_seed_data.append(data)
    
    reshaped_each_seed_data = np.transpose(each_seed_data)
    
    pprint.pprint(reshaped_each_seed_data)
    
    if(mean==True):
        #pprint.pprint(reshaped_each_seed_data)
        
        mean_reshaped_each_seed_data = [math.ceil(np.mean(x)) for x in reshaped_each_seed_data]
        #pprint.pprint(mean_reshaped_each_seed_data)
        #sys.exit()
        return mean_reshaped_each_seed_data
    else:
        return reshaped_each_seed_data


def _get_multi_seed_data_vidstats_yerr(data_filter, all_data, mean=False):    
    each_seed_data = []   
    
    for each_seed in all_data.items():
        data = [x[data_filter] for x in each_seed[1].values()]       
        each_seed_data.append(data)
    
    reshaped_each_seed_data = np.transpose(each_seed_data)
    
    pprint.pprint(reshaped_each_seed_data)
    
    if(mean==True):
        #pprint.pprint(reshaped_each_seed_data)
        
        mean_reshaped_each_seed_data = [[np.min(x),np.max(x)] for x in reshaped_each_seed_data]
        #pprint.pprint(mean_reshaped_each_seed_data)
        #sys.exit()
        return np.transpose(mean_reshaped_each_seed_data)
    else:
        return reshaped_each_seed_data






        
def _autolabel(rects, ax, extra_text=None, extra_text_maxlate=None, fsize=12):
    j=0
    for rect in rects:
        height = rect.get_height()   
        
        #y_cord = (height *1.05) if height>0 else (height *1.05)
        
        if(height>80):  y_cord = (height *1.00)
        elif(height>0): y_cord = (height *1.05)
        elif(height == 0): y_cord = (height +2.0)
        else: y_cord = (height *1.05)            
             
        if(extra_text != None):
            if(int(round(extra_text[j]))>0):
                ax.text( rect.get_x()+rect.get_width()/2., y_cord, '%d(%d)*'%( int(height), int(round(extra_text[j]))  ),
                        ha='center', va='bottom', fontsize=fsize)
            else:
                ax.text( rect.get_x()+rect.get_width()/2., y_cord, '%d'%( int(height)  ),
                        ha='center', va='bottom', fontsize=fsize)
        else:
            ax.text( rect.get_x()+rect.get_width()/2., y_cord, '%d'%( int(round(height))  ),
                        ha='center', va='bottom', fontsize=fsize)
        
        j+=1 


###################################################################################################
#    Utilisation comparisons, visualisations
###################################################################################################
 
            
def plot_InstUtilisation_VH(summaryHist=False, fillPlots=False):        
    
    
    ##############################
    ####### gather results 
    ##############################   
    
    #F_PREFIX = "_util.js"
    F_PREFIX = "__utilisation.js"
    
    all_exp_data = {}
    multi_seed_data = {}
    
    for each_wf_id in NUM_WORKFLOWS:
        all_exp_data[each_wf_id] = {}
        print "--"
        
        for each_seed in RANDOM_SEED_LIST:        
            
            print each_seed
            
            exp_data = OrderedDict()      # dict that will contain all the results for each param  
            
            #### ac_test : none      
            FNAME_PREFIX = "ACTest_none_"
            vs_bs_fname = EXP_DATA_FOLDER + "seed_" + str(each_seed) + "/" + FNAME_PREFIX + 'wf'+str(each_wf_id)+'_cores'+str(EXP_NUM_NODES) + F_PREFIX
            json_data=open(vs_bs_fname)
            file_data = json.load(json_data)   
            exp_data['No-AC'] = file_data
            
            #### ac_test : schedulability test only        
            FNAME_PREFIX = "ACTest_sched_"
            vs_bs_fname = EXP_DATA_FOLDER + "seed_" + str(each_seed) + "/" + FNAME_PREFIX + 'wf'+str(each_wf_id)+'_cores'+str(EXP_NUM_NODES) + F_PREFIX
            json_data=open(vs_bs_fname)
            file_data = json.load(json_data)        
            exp_data['D-AC'] = file_data
            
#             #### ac_test : schedulability test only  (tasks)      
#             FNAME_PREFIX = "ACTest_schedtasksonly_"
#             vs_bs_fname = EXP_DATA_FOLDER + "seed_" + str(each_seed) + "/" + FNAME_PREFIX + 'wf'+str(each_wf_id)+'_cores'+str(EXP_NUM_NODES) + F_PREFIX
#             json_data=open(vs_bs_fname)
#             file_data = json.load(json_data)        
#             exp_data['Deterministic.\n(comp.)'] = file_data
           
            #### ac_test : heuristics - KG deadline assignment 
            FNAME_PREFIX = "ACTest_heukgEQF_"
            vs_bs_fname = EXP_DATA_FOLDER + "seed_" + str(each_seed) + "/" + FNAME_PREFIX + 'wf'+str(each_wf_id)+'_cores'+str(EXP_NUM_NODES) + F_PREFIX
            json_data=open(vs_bs_fname)
            file_data = json.load(json_data)        
            exp_data['DEQF-AC'] = file_data
                  
            #### ac_test : heuristics threshold based
            for each_ratio_combo in RATIO_COMBINATIONS:
                
                each_ibuff_ratio = each_ratio_combo[0]
                each_tq_ratio = each_ratio_combo[1]
    
                FNAME_PREFIX = "ACTest_heuth_" + "iblr" + str(each_ibuff_ratio) + "_tqlr" + str(each_tq_ratio) + "_"
                
                vs_bs_fname = EXP_DATA_FOLDER + "seed_" + str(each_seed) + "/" + FNAME_PREFIX + 'wf'+str(each_wf_id)+'_cores'+str(EXP_NUM_NODES) + F_PREFIX
                json_data=open(vs_bs_fname)
                file_data = json.load(json_data)
                
                key = "Heu:" + "IBLR_\\alpha" + str(each_ibuff_ratio) + ", TQL_\\alpha" + str(each_tq_ratio)                
                key_2 =  "Heu-AC" + "\n" + "(" + str(each_ibuff_ratio) + "," + str(each_tq_ratio) + ")"
                
                exp_data[key_2] = file_data  
            
            all_exp_data[each_wf_id]['seed_'+str(each_seed)] = exp_data 
       
    
   
    #####################################
    ####### format data, get what we need
    #####################################
        
        
    node_specific_idletimes_with_totalsimtime = OrderedDict()
        
    for wf_id in NUM_WORKFLOWS:
        node_specific_idletimes_with_totalsimtime[wf_id] = OrderedDict()        
        for each_exp_seed_key, each_exp_seed_data in all_exp_data[wf_id].iteritems():
                            
            for each_exp_key, each_exp_data in each_exp_seed_data.iteritems():
                
#                mean_idletimes = [] 
#                sum_idletimes = []
#                mean_busytimes = []
#                sum_busytimes = [] 
#                std_idletime = []          
#                for each_data_point in each_exp_data['node_idle_time']:
#                    total_idle = 0
#                    total_busy = 0
#                    for idle_time in each_data_point['nsit']:                    
#                        total_idle +=  idle_time
#                        total_busy += float(1.0-idle_time)
#                         
#                    mean_idletimes.append(float(total_idle/len(each_data_point['nsit'])))
#                    mean_busytimes.append(float(total_busy/len(each_data_point['nsit'])))
#                    sum_idletimes.append(total_idle)
#                    sum_busytimes.append(total_busy)
#                    std_idletime.append(np.std(each_data_point['nsit']))
                           
#                for each_data_point in each_exp_data['node_throughput']:
#                    total_t = 0                
#                    for idle_time in each_data_point['csp_tc']:                    
#                        total_t +=  idle_time
                 
                total_sim_time = float(len(each_exp_data['node_idle_time']) * 0.5 * 1.0)                               
                temp_entry = {
                              'total_idletime' : each_exp_data['node_idle_time'][-1],
                              'total_idletime_allseeds' : None,                          
                              'total_simtime' : total_sim_time    #37.0#                      
                              }
                
                #pprint.pprint(each_exp_data['node_idle_time'][-1]['it_c'])
                #print total_sim_time
                #sys.exit()
                
                idle_time_percentage = np.mean(each_exp_data['node_idle_time'][-1]['it_c'])/total_sim_time
                                
                if(each_exp_key not in node_specific_idletimes_with_totalsimtime[wf_id]):
                    node_specific_idletimes_with_totalsimtime[wf_id][each_exp_key] = [idle_time_percentage]
                else:
                    node_specific_idletimes_with_totalsimtime[wf_id][each_exp_key].extend([idle_time_percentage])
    
    
    #pprint.pprint(node_specific_idletimes_with_totalsimtime)
    #sys.exit()
    
    
    #### dump the summary results ####
    _write_formatted_file(EXP_DATA_FOLDER+"data_InstUtilisation_VH.js", node_specific_idletimes_with_totalsimtime, format='json')
    
    
    
    #################################
    ####### plot lines all wfs in one
    #################################  
    labels = [("%s"%x) for x in node_specific_idletimes_with_totalsimtime[8].keys()]   
    
    summation = {}
    bp_data = {}
    
    total_sim_time = {}
    #ind = np.arange(len([each_exp['total_idletime'] for each_exp in node_specific_idletimes_with_totalsimtime[8] if 'it_c' in each_exp['total_idletime']]))
    
    ind = np.arange(len(node_specific_idletimes_with_totalsimtime[8].keys()))
    
    width = 0.25
    positions = [ind, ind+width]
    
    #temp_cols = ['blanchedalmond', 'blueviolet']
    temp_cols = ['#aab7b7', '#34495e']
    
    #lcols = itertools.cycle(('blanchedalmond', 'blueviolet'))
    lcols = itertools.cycle(('#aab7b7', '#34495e'))
    
    f = plt.figure()
    
    i=0
    for wf_id in NUM_WORKFLOWS:        
        summation[wf_id] = [100.0-float(np.mean(x)*100.0) for x in node_specific_idletimes_with_totalsimtime[wf_id].values()]  
        bp_data[wf_id] = [np.subtract(100.0,np.multiply(x,100.0)) for x in node_specific_idletimes_with_totalsimtime[wf_id].values()]
                                
        plt.bar(positions[i], summation[wf_id], width=width, color=lcols.next(), alpha=0.9)                
        
        #bp0 = ax.boxplot(bp_data[wf_id], positions=positions[i], widths=width)
#         if (wf_id == 8): c='#FF9933' 
#         else:  c='#6600CC'
        #_set_bp(ax,bp0, c , lw=2)
        
        plt.hold(True)
        
        i+=1
    plt.hold(True)
    #p = plt.axvspan(0.0, (width*5.0)+(width*1.75), facecolor='0.5', alpha=0.3)
    
    xticks = ind+(width*1.0)
    xticks = [x for x in xticks]
    #plt.tick_params(axis='both', which='major', labelsize=12)
    plt.xticks(xticks, labels)    
    
    
    r1 = matplotlib.patches.Rectangle((0, 0), 1, 1, fc=temp_cols[0])
    r2 = matplotlib.patches.Rectangle((0, 0), 1, 1, fc=temp_cols[1])
    
    leg = plt.legend([r1,r2], ["Num. of workflows = 8", "Num. of workflows = 16"], ncol=2, loc = 'upper center', fontsize=12,)
    #leg.get_frame().set_facecolor('#FFFFFF')
    leg.draggable(True)
    plt.xlabel("Admission control test type")
    plt.ylabel("Mean PE busy time %")
    
    
    plt.grid(True)
    plt.axis('tight')
        
        
        
def _set_bp(ax, bp, col, lw=1):
    plt.setp(bp['boxes'], color=col, linewidth=lw, alpha=0.7)    
    plt.setp(bp['caps'], color=col)
    plt.setp(bp['whiskers'], color=col)
    plt.setp(bp['fliers'], color=col)
    plt.setp(bp['medians'], color=col)
    
def _get_multi_seed_data_utilisation(data_filter, all_data, mean=False):    
    each_seed_data = []   
    
    for each_seed in all_data.items():        
        data = [x[data_filter] for x in each_seed[1].values()]        
        each_seed_data.append(data)
    
    reshaped_each_seed_data = np.transpose(each_seed_data)
    
    pprint.pprint(reshaped_each_seed_data)
    
    if(mean==True):
        #pprint.pprint(reshaped_each_seed_data)
        
        mean_reshaped_each_seed_data = [np.mean(x) for x in reshaped_each_seed_data]
        #pprint.pprint(mean_reshaped_each_seed_data)
        #sys.exit()
        return mean_reshaped_each_seed_data
    else:
        return reshaped_each_seed_data

###################################################################################################
#    GOP lateness - different AC tests
###################################################################################################   

# variable heuristics
def plot_GOPLateness_VH():
        
    ##############################
    ####### gather results 
    ##############################    
    all_exp_data = {}
    multi_seed_data = {}
        
    for each_wf_id in NUM_WORKFLOWS:
        all_exp_data[each_wf_id] = {}
        
        print each_wf_id
        
        for each_seed in RANDOM_SEED_LIST:        
            
            exp_data = OrderedDict()      # dict that will contain all the results for each param  
            
            #### ac_test : none      
            FNAME_PREFIX = "ACTest_none_"
            goplatenessdata_fname = EXP_DATA_FOLDER + "seed_" + str(each_seed) + "/" + FNAME_PREFIX + 'wf'+str(each_wf_id)+'_cores'+str(EXP_NUM_NODES) + "_gopsopbuffsumm.js"
            json_data=open(goplatenessdata_fname)
            file_data = json.load(json_data)   
            exp_data['No-AC'] = file_data            
            
            #### ac_test : schedulability test only        
            FNAME_PREFIX = "ACTest_sched_"
            goplatenessdata_fname = EXP_DATA_FOLDER + "seed_" + str(each_seed) + "/" + FNAME_PREFIX + 'wf'+str(each_wf_id)+'_cores'+str(EXP_NUM_NODES) + "_gopsopbuffsumm.js"
            json_data=open(goplatenessdata_fname)
            file_data = json.load(json_data)        
            exp_data['D-AC'] = file_data
            
#             #### ac_test : schedulability test only (tasks)       
#             FNAME_PREFIX = "ACTest_schedtasksonly_"
#             goplatenessdata_fname = EXP_DATA_FOLDER + "seed_" + str(each_seed) + "/" + FNAME_PREFIX + 'wf'+str(each_wf_id)+'_cores'+str(EXP_NUM_NODES) + "_gopsopbuffsumm.js"
#             json_data=open(goplatenessdata_fname)
#             file_data = json.load(json_data)        
#             exp_data['Deterministic.\n(comp.)'] = file_data
             
            #### ac_test : heuristics - KG deadline assignment 
            FNAME_PREFIX = "ACTest_heukgEQF_"
            goplatenessdata_fname = EXP_DATA_FOLDER + "seed_" + str(each_seed) + "/" + FNAME_PREFIX + 'wf'+str(each_wf_id)+'_cores'+str(EXP_NUM_NODES) + "_gopsopbuffsumm.js"
            json_data=open(goplatenessdata_fname)
            file_data = json.load(json_data)        
            exp_data['DEQF-AC'] = file_data
                  
            #### ac_test : heuristics threshold based
            for each_ratio_combo in RATIO_COMBINATIONS:
                
                each_ibuff_ratio = each_ratio_combo[0]
                each_tq_ratio = each_ratio_combo[1]
    
                FNAME_PREFIX = "ACTest_heuth_" + "iblr" + str(each_ibuff_ratio) + "_tqlr" + str(each_tq_ratio) + "_"
                
                goplatenessdata_fname = EXP_DATA_FOLDER + "seed_" + str(each_seed) + "/" + FNAME_PREFIX + 'wf'+str(each_wf_id)+'_cores'+str(EXP_NUM_NODES) + "_gopsopbuffsumm.js"
                json_data=open(goplatenessdata_fname)
                file_data = json.load(json_data)
                
                key = "Heu:" + "IBLR_\\alpha" + str(each_ibuff_ratio) + ", TQL_\\alpha" + str(each_tq_ratio)                
                key_2 =  "Heu-AC" + "\n" + "(" + str(each_ibuff_ratio) + "," + str(each_tq_ratio) + ")"                
                exp_data[key_2] = file_data               
            
            all_exp_data[each_wf_id]['seed_'+str(each_seed)] = exp_data     
    
    #####################################
    ####### format data, get what we need
    #####################################
        
    allwfs_goplateness_allperms = OrderedDict()
    for wf_id in NUM_WORKFLOWS:
        
        # concatenate results for all seeds
        allwfs_goplateness_allperms[wf_id] = []
        temp_gop_lateness_data = OrderedDict()
        for each_exp_seed_key, each_exp_seed_data in all_exp_data[wf_id].iteritems():
            
            print each_exp_seed_key
            
            for each_exp_key, each_exp_val in each_exp_seed_data.iteritems():
                
                #print each_ugid_key                    
                gop_latenesses = [np.round(x['gop_execution_lateness'],2) for x in each_exp_val.values() if (x['gop_execution_lateness'] > 0)]
                #pprint.pprint(gop_latenesses)

                if(each_exp_key not in temp_gop_lateness_data):
                    temp_gop_lateness_data[each_exp_key] = gop_latenesses
                else:
                    temp_gop_lateness_data[each_exp_key].extend(gop_latenesses)
            
                    
        allwfs_goplateness_allperms[wf_id].append(temp_gop_lateness_data)
    
    
    #### dump the summary results ####
    _write_formatted_file(EXP_DATA_FOLDER+"data_GOPLateness_VH.js", allwfs_goplateness_allperms, format='json')
    
    
            
    ##############################
    ####### plot boxplots 
    ##############################    
    WF_RANGE = [8, 16]
    
    f, axarr = plt.subplots(len(WF_RANGE), sharex=True)
    f.canvas.set_window_title("Gop Lateness per AC-test")
    
    # labels
    labels = [("%s" %x) for x in allwfs_goplateness_allperms[8][0].keys()]
    
    i=0
    for wf_id in WF_RANGE:
                
        each_wf_data = allwfs_goplateness_allperms[wf_id]
        each_wf_key = wf_id
        
        boxpos=np.arange(len(allwfs_goplateness_allperms[wf_id][0].keys())) 
        boxpos_means=np.arange(len(allwfs_goplateness_allperms[wf_id][0].keys()))
       
        # make sure boxplots have equal sample size
        #boxplot_data_orig = [x for x in allwfs_goplateness_allperms[wf_id][0].values()]
        boxplot_data = []
        #boxplot_data_maxlengths = max([len(x) for x in allwfs_goplateness_allperms[wf_id][0].values()])
        for each_bp_data in allwfs_goplateness_allperms[wf_id][0].values():
            new_data = each_bp_data + [0.0]*(len(RANDOM_SEED_LIST) - len(each_bp_data))
            boxplot_data.append(new_data)
       
        # plot box plots                
        #p = axarr[i].axvspan(-0.5, 1 + 0.5, facecolor='0.5', alpha=0.2)        
        bp=axarr[i].boxplot(boxplot_data,notch=0,sym='', whis=1, positions=boxpos, widths=0.8, patch_artist=True)
        
        max_of_all = [np.max(x) for x in boxplot_data]
               
        max_y_cord = max([x.get_data()[1][1] for x in bp['whiskers']])
        for box, medians in zip(bp['boxes'], bp['medians']):            
            plt.setp(box, color='k', linewidth=1.25)
            plt.setp(box, facecolor='#348ABD')
            plt.setp(medians,linewidth=1.25, color='k')
        
        for caps in bp['caps']:            
            plt.setp(caps, linewidth=1.25, color='k')
        
        for whiskers in bp['whiskers']:            
            plt.setp(whiskers, linewidth=1.25, color='k')
        
        for fliers in bp['fliers']:            
            plt.setp(fliers, linewidth=1.25, color='k')
            
        
        means =  [np.mean(x) if len(x)>0 else 0 for x in allwfs_goplateness_allperms[wf_id][0].values()]      
        max_lateness = [max(x) if len(x)>0 else 0 for x in allwfs_goplateness_allperms[wf_id][0].values()] 
        
        plt.hold(True)
        ax2 = axarr[i].twinx()
        #p_maxes = ax2.plot(boxpos_means, max_lateness, marker='o', markersize=10, linestyle='--', color='r', linewidth=1.0, label="Maximum job lateness")
        p_means = axarr[i].plot(boxpos_means, means, marker='d', markersize=10, linestyle='', color='g', linewidth=1.0, label="Mean job lateness")        
        p_maxes = ax2.plot(boxpos_means, max_of_all, marker='o', markersize=10, linestyle='--', color='r', linewidth=1.0, label="Maximum job lateness")       
        
        for ix,each_max_val in enumerate(max_lateness):
            if(each_max_val <0): gap=-1.10
            else:
                if(each_max_val > 2.0): gap=0.85
                else: gap=1.10
        
        ## figure specs        
        axarr[i].yaxis.grid(True, which='both')
        axarr[i].xaxis.grid(True)
        axarr[i].set_title('Number of workflows = '+ str(wf_id))
        #axarr[i].set_ylim([0.0, max_y_cord])        
        ax2.tick_params(axis='y', labelsize=12, color='r', labelcolor='r')
        axarr[i].tick_params(axis='x', which='both', labelsize=12)
        axarr[i].tick_params(axis='y', which='both', labelsize=12)
        
        #axarr[i].set_yscale("log")

        i+= 1       
    
    
    meanL = plt.Line2D((0,1),(0,0), color='g', marker='d', linestyle='')
    maxL = plt.Line2D((0,1),(0,0), color='r', marker='o', linestyle='--')
    
    
    leg = plt.legend([meanL, maxL], ["Mean job lateness", "Maximum job lateness"], 
                     ncol=2, loc = 'upper center', fontsize=12, bbox_to_anchor = (0,0.02,1,1),
                     bbox_transform = plt.gcf().transFigure)
    leg.get_frame().set_facecolor('#FFFFFF')
    leg.get_frame().set_linewidth(0.0)
    leg.draggable(True)
    axarr[i-1].set_xlabel("Admission control test type")
    f.text(0.02, 0.5, 'Job lateness (s)', va='center', rotation='vertical', fontsize=14)
    f.text(0.98, 0.5, 'Maximum job lateness (s)', va='center', rotation='vertical', fontsize=14)
    
    xticks = [x for x in range(0,(len(labels)))]    
    axarr[i-1].set_xticks(xticks)
    axarr[i-1].set_xticklabels(labels)
    plt.axis('tight')










###################################
#    HELPERS
###################################
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

def _get_all_ratio_combos(ibl_list, tql_list):
    combinations = []
    for each_ibl in ibl_list:
        for each_tql in tql_list:
            pair = (each_ibl, each_tql)
            combinations.append(pair)
    
    return combinations
            


#RATIO_COMBINATIONS = _get_all_ratio_combos([0.7],[0.5])

#RATIO_COMBINATIONS = _get_all_ratio_combos([0.1,0.3,0.5,0.7,0.9,1.0],[0.1,0.3,0.5,0.7,0.9,1.0])


#plot_ACTest_Results_VidStats_HeuVar(wf_id=None, plot3D=False)
#plot_GOPLateness_VH()
plot_InstUtilisation_VH(summaryHist=False)
print "finished"

plt.show()

