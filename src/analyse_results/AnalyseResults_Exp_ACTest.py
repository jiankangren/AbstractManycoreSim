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

import matplotlib.cm as cm
from matplotlib.font_manager import FontProperties

from SimParams import SimParams


import Multicore_MPEG_Model as MMMSim


NUM_WORKFLOWS = range(8, 19, 1)
#NUM_WORKFLOWS = [9]
#NUM_NODES = [2,4,8,16,32]
NUM_NODES = 9
NOC_XY = [(2,1), (2,2), (2,4), (2,8), (2,16)]


RATIO_COMBINATIONS = [(0.5, 0.1), (0.1,0.5), (0.1, 1.0), (0.3, 0.3), (0.7, 0.3), (0.3, 1.0), (0.5, 0.5), (0.7, 0.5), (1.0,1.0)]


#IBUFF_TASKS_LATENESS_RATIO_RANGE    = [0.1, 0.3, 0.5, 0.7, 1.0]
#TQ_TASKS_LATENESS_RATIO_RANGE       = [0.1, 0.3, 0.5, 0.7, 1.0]

        
        

###################################################################################################
#    Video predictability statistics : schedulable, late, rejected
###################################################################################################

# Admission control tests :
# - None
# - heu based
# - sched based
def plot_ACTest_Results_VidStats():
    
    ##############################
    ####### gather results 
    ##############################
    exp_data = []    
    for each_wf_num in NUM_WORKFLOWS:
        
        none_entry = None
        heu_entry = None
        sched_entry = None
        hybv1_entry = None
        
        #exp_data[each_wf_num] = {}
        
        #### ac_test : none      
        FNAME_PREFIX = "ACTest_none_"
        vs_bs_fname = 'experiment_data/vs_ac_test/' +  FNAME_PREFIX + 'wf'+str(each_wf_num)+'_cores'+str(SimParams.NUM_NODES) + ".js"
        json_data=open(vs_bs_fname)
        file_data = json.load(json_data)        
        none_entry = _getEntry(file_data)          
        
        #### ac_test : heuristics only        
        FNAME_PREFIX = "ACTest_heu_"
        vs_bs_fname = 'experiment_data/vs_ac_test/' +  FNAME_PREFIX + 'wf'+str(each_wf_num)+'_cores'+str(SimParams.NUM_NODES) + ".js"
        json_data=open(vs_bs_fname)
        file_data = json.load(json_data)        
        heu_entry = _getEntry(file_data)          
        
        #### ac_test : schedulability test only        
        FNAME_PREFIX = "ACTest_sched_"
        vs_bs_fname = 'experiment_data/vs_ac_test/' +  FNAME_PREFIX + 'wf'+str(each_wf_num)+'_cores'+str(SimParams.NUM_NODES) + ".js"
        json_data=open(vs_bs_fname)
        file_data = json.load(json_data)        
        sched_entry = _getEntry(file_data)       


        
        temp = {
                "none" : none_entry,
                "heu" : heu_entry,
                "sched" : sched_entry,
                }  
        exp_data.append(temp)
        
    
    ##############################
    ####### plot results
    ##############################
    # labels are wf nums
    labels = [str(x) for x in NUM_WORKFLOWS] 
    
    results_category = [
                         "num_vids_accepted_success", 
                         "num_dropped_tasks", 
                         "num_vids_accepted_late", 
                         "num_vids_rejected"
                        ]
    
    
    #for ix, each_rc in enumerate(results_category):    
    # --------- number of success & failed ----------
    #### plot - num_vids_accepted_success
    
    fig = plt.figure(1)
    fig.canvas.set_window_title("num_vids_accepted_success AND late")
    ax = plt.subplot(111)
        
    # avg-lateness
    success_none = [x["none"]["num_vids_accepted_success"] for x in exp_data]
    late_none = [x["none"]["num_vids_accepted_late"] for x in exp_data]
    success_heu = [x["heu"]["num_vids_accepted_success"] for x in exp_data]
    late_heu = [x["heu"]["num_vids_accepted_late"] for x in exp_data]
    success_sched = [x["sched"]["num_vids_accepted_success"] for x in exp_data]
    late_sched = [x["sched"]["num_vids_accepted_late"] for x in exp_data]
#    success_hybv1 = [x["hybv1"]["num_vids_accepted_success"] for x in exp_data]
#        success_hybv2 = [x["hybv2"][each_rc] for x in exp_data]
    
    ind = np.arange(len(success_heu))
    width = 0.30
    pos_0 = ind
    pos_1 = ind+width
    pos_2 = ind+(2.0*width)
        
    rects0 = ax.bar(pos_0, success_none, width, color='r', alpha=1.0)
    rects_0_b = ax.bar(pos_0, late_none, width, color='r', alpha=0.6, bottom=success_none, hatch='\\')
    
    rects1 = ax.bar(pos_1, success_heu, width, color='g', alpha=1.0)
    rects_1_b = ax.bar(pos_1, late_heu, width, color='g', alpha=0.6, bottom=success_heu, hatch='\\')
    
    rects2 = ax.bar(pos_2, success_sched, width, color='b', alpha=1.0)
    rects_2_b = ax.bar(pos_2, late_sched, width, color='b', alpha=0.6, bottom=success_sched, hatch='\\')
    #rects3 = ax.bar(ind+(2.0*width), success_hybv1, width, color='b')
#        rects4 = ax.bar(ind+(3.0*width), success_hybv2, width, color='y')
    
    ax.set_ylabel("Number of video streams",fontsize=18)
    ax.set_xlabel('Workflows',fontsize=18)    
    plt.tick_params(axis='both', which='major', labelsize=17)
    ax.set_xticks(ind+(width*1.5))
    ax.set_xticklabels( labels )
    plt.grid(True, alpha=0.5)

    leg = ax.legend( (rects0[0], rects_0_b[0], rects1[0], rects_1_b[0], rects2[0], ), 
                     ('No AC (schedulable)', 'No AC (late)',
                      'Heuristics-based AC (schedulable)', 'Heuristics-based AC (late)', 
                      'Deterministic AC (schedulable)') )    
    leg.draggable()
    plt.setp(leg.get_texts(), fontsize='16')



# Admission control tests :
# - None
# - heu based
# - sched based
def plot_ACTest_Results_VidStats_HeuVar(wf_id = None, plot3D = True):
    
#    if(wf_id == None):
#        sys.exit("Error - no wf id specified")
    
    ##############################
    ####### gather results 
    ##############################
    NUM_WORKFLOWS = [8,16]
    all_wf_exp_data = {}
    
    for each_wf_id in NUM_WORKFLOWS:
        
        exp_data = OrderedDict()      # dict that will contain all the results for each param  
        
        #### ac_test : none      
        FNAME_PREFIX = "ACTest_none_"
        vs_bs_fname = 'experiment_data/vs_ac_test/' +  FNAME_PREFIX + 'wf'+str(each_wf_id)+'_cores'+str(SimParams.NUM_NODES) + ".js"
        json_data=open(vs_bs_fname)
        file_data = json.load(json_data)   
        exp_data['No-AC'] = _getEntry(file_data) 
        
        #### ac_test : schedulability test only        
        FNAME_PREFIX = "ACTest_sched_"
        vs_bs_fname = 'experiment_data/vs_ac_test/' +  FNAME_PREFIX + 'wf'+str(each_wf_id)+'_cores'+str(SimParams.NUM_NODES) + ".js"
        json_data=open(vs_bs_fname)
        file_data = json.load(json_data)        
        exp_data['Determ.'] = _getEntry(file_data) 
        
        #### ac_test : heuristics - KG deadline assignment 
#        FNAME_PREFIX = "ACTest_heukgES_"
#        vs_bs_fname = 'experiment_data/vs_ac_test/' +  FNAME_PREFIX + 'wf'+str(each_wf_id)+'_cores'+str(SimParams.NUM_NODES) + ".js"
#        json_data=open(vs_bs_fname)
#        file_data = json.load(json_data)        
#        exp_data['Heu\n(D-ES)'] = _getEntry(file_data) 
#        
        FNAME_PREFIX = "ACTest_heukgEQF_"
        vs_bs_fname = 'experiment_data/vs_ac_test/' +  FNAME_PREFIX + 'wf'+str(each_wf_id)+'_cores'+str(SimParams.NUM_NODES) + ".js"
        json_data=open(vs_bs_fname)
        file_data = json.load(json_data)        
        exp_data['Heu\n(D-EQF)'] = _getEntry(file_data)
              
        #### ac_test : heuristics threshold based    
#        for each_ibuff_ratio in IBUFF_TASKS_LATENESS_RATIO_RANGE:
#            for each_tq_ratio in TQ_TASKS_LATENESS_RATIO_RANGE:

        for each_ratio_combo in RATIO_COMBINATIONS:
            
            each_ibuff_ratio = each_ratio_combo[0]
            each_tq_ratio = each_ratio_combo[1]

            FNAME_PREFIX = "ACTest_heuth_" + "iblr" + str(each_ibuff_ratio) + "_tqlr" + str(each_tq_ratio) + "_"
            
            vs_bs_fname = 'experiment_data/vs_ac_test/' +  FNAME_PREFIX + 'wf'+str(each_wf_id)+'_cores'+str(SimParams.NUM_NODES) + ".js"
            json_data=open(vs_bs_fname)
            file_data = json.load(json_data)
            
            key = "Heu:" + "IBLR_\\alpha" + str(each_ibuff_ratio) + ", TQL_\\alpha" + str(each_tq_ratio)                
            key_2 =  "Heu" + "\n" + "(" + str(each_ibuff_ratio) + "," + str(each_tq_ratio) + ")"
            
            exp_data[key_2] = _getEntry(file_data)
        
        
        all_wf_exp_data[each_wf_id] = exp_data
        
    
    labels = [('%s'%x) for x in exp_data.keys()] 
    ##############################
    ####### plot results
    ##############################
    
    if(wf_id != None):
        ################# single workflow plot ##################
        # labels are wf nums
        
        
        results_cats = [
                         "num_vids_accepted_success", 
                         "num_dropped_tasks", 
                         "num_vids_accepted_late", 
                         "num_vids_rejected"
                        ]
                    
        # --------- number of success & failed ----------
        fig = plt.figure(1)
        fig.canvas.set_window_title("Predictability results for num_wf=" + str(wf_id))
        ax = plt.subplot(111)
            
        # data for different results categories
        streams_schedulable = [x["num_vids_accepted_success"] for x in exp_data.values()]
        streams_late = [x["num_vids_accepted_late"] for x in exp_data.values()]
        streams_rejected = [x["num_vids_rejected"] for x in exp_data.values()]
        dropped_gops = [float(x["num_dropped_tasks"]/12.0) for x in exp_data.values()]
            
        ind = np.arange(len(streams_schedulable))
        width = 0.25
        positions = [ind, ind+width, ind+(2.0*width), ind+(3.0*width)]
            
        rects0 = ax.bar(positions[0], streams_schedulable, width, color='g', alpha=1.0)                
        rects1 = ax.bar(positions[1], streams_late, width, color='b', alpha=1.0)                
        rects2 = ax.bar(positions[2], streams_rejected, width, color='r', alpha=1.0)
        rects3 = ax.bar(positions[3], dropped_gops, width, color='y', alpha=1.0)        
        
        ax.set_ylabel("Number of video streams",fontsize=18)
        ax.set_xlabel('AC-test type',fontsize=18)    
        plt.tick_params(axis='both', which='major', labelsize=12)
        ax.set_xticks(ind+(width*1.5))
        ax.set_xticklabels( labels , rotation=90)
        plt.grid(True, alpha=0.5)
        
        leg = ax.legend( (rects0[0], rects1[0], rects2[0],rects3[0] ), 
                         ('Admitted and schedulable',
                          'Admitted but late/dropped', 
                          'Dropped gops',
                          'Rejected') )    
        leg.draggable()
        plt.setp(leg.get_texts(), fontsize='16')
    
    else:
        ################# 3D plot ##################
        if(plot3D == True):
        
            fig = plt.figure(1)
            fig.canvas.set_window_title("Predictability results")
            ax = fig.add_subplot(111, projection='3d')
            
            # labels are wf nums
            labels = [(r'$%s$'%x) for x in all_wf_exp_data[8].keys()]
            #labels = [(r'$%s$'%x) for x in len(all_wf_exp_data[8].keys())]
            
            
            results_cats = [
                             "num_vids_accepted_success", 
                             "num_dropped_tasks", 
                             "num_vids_accepted_late", 
                             "num_vids_rejected"
                            ]
            
            for each_wf_id in [10, 12, 14, 16, 18]:
                each_wf_data = all_wf_exp_data[each_wf_id]
                each_wf_key = each_wf_id
                
                # --------- number of success & failed ----------           
                    
                # data for different results categories
                streams_schedulable = [x["num_vids_accepted_success"] for x in each_wf_data.values()]
                streams_late = [x["num_vids_accepted_late"] for x in each_wf_data.values()]
                streams_rejected = [x["num_vids_rejected"] for x in each_wf_data.values()]
                    
                ind = np.arange(len(streams_schedulable))
                width = 0.30
                positions = [ind, ind+width, ind+(2.0*width)]
                    
                rects0 = ax.bar(positions[0], streams_schedulable, width=width, color='g', alpha=0.6, zs=each_wf_key, zdir='y')                
                rects1 = ax.bar(positions[1], streams_late, width=width, color='b', alpha=0.6, zs=each_wf_key, zdir='y')                
                rects2 = ax.bar(positions[2], streams_rejected, width=width, color='r', alpha=0.6, zs=each_wf_key, zdir='y')        
                
            ax.set_zlabel("Number of video streams",fontsize=14)
            ax.set_ylabel("Number of workflows",fontsize=14)
            #ax.set_xlabel('AC-test type',fontsize=18)    
            plt.tick_params(axis='both', which='major', labelsize=10)
            ax.set_xticks(ind+(width*1.5))
            ax.set_xticklabels( labels , rotation=90)

        else:
            
            ################# multiple workflow plot : bar plots ##################
            
            WF_RANGE = [8, 16]
            
            # points scheme
            POINTS_SUCCESS  = 1.0
            POINTS_REJECT   = 0.0
            POINTS_LATE     = -1.0
            POINTS_DROPPED  = -2.0
            
            
            #fig = plt.figure(1)
            #fig.canvas.set_window_title("Predictability results")
            #fig = plt.subplot()            
            f, axarr = plt.subplots(len(WF_RANGE), sharex=True)
            f.canvas.set_window_title("Predictability results")
            
           
            # labels are wf nums
            #real_labels = [(r'$%s$'%x) for x in all_wf_exp_data[8].keys()]
            #pprint.pprint(real_labels)
            #labels = [("Heu_"+chr(65+x)) for x in range(0,len(all_wf_exp_data[8].keys())-2)]
            #labels.insert(0,"No-AC")
            #labels.insert(1,"Determ.")
            #pprint.pprint(labels)
            
            i=0
            t=[]
            for each_wf_id in WF_RANGE:
                
                each_wf_data = all_wf_exp_data[each_wf_id]
                each_wf_key = each_wf_id
                
                # --------- number of success & failed ----------           
                    
                # data for different results categories
                streams_schedulable = [x["num_vids_accepted_success"] for x in each_wf_data.values()]
                streams_late = [x["num_vids_accepted_late"] for x in each_wf_data.values()]                
                streams_rejected = [x["num_vids_rejected"] for x in each_wf_data.values()]
                dropped_gops = [float(x["num_dropped_tasks"]/12.0) for x in each_wf_data.values()]
                    
                ind = np.arange(len(streams_schedulable))
                width = 0.20
                positions = [ind, ind+width, ind+(2.0*width), ind+(3.0*width)]
                
                p = axarr[i].axvspan(0.0, (width*8.0)+(width*0.5), facecolor='0.5', alpha=0.3)
#                for x in xrange(0,len(labels)):
#                    l = plt.axvline(x=(width*3.5)*x)
                
                rects0 = axarr[i].bar(positions[0], streams_schedulable, width=width, color='g', alpha=0.9)                
                rects1 = axarr[i].bar(positions[1], streams_late, width=width, color='b', alpha=0.9)                
                rects2 = axarr[i].bar(positions[2], streams_rejected, width=width, color='#FF4747', alpha=0.9)  
                #rects3 = axarr[i].bar(positions[3], dropped_gops, width=width, color='y', alpha=0.9)
                
                _autolabel(rects0, axarr[i])
                _autolabel(rects1, axarr[i], extra_text=dropped_gops)
                _autolabel(rects2, axarr[i])
                #_autolabel(rects3, axarr[i])
                
                #l = plt.axvline(x=1)
                
                 
                axarr[i].grid(True, alpha=0.5)
                t.append(axarr[i].set_title('Number of workflows = '+ str(each_wf_key), fontsize=20))
                
                axarr[i-1].tick_params(axis='both', which='major', labelsize=20)
                
                i+= 1
            
           
            #ax.set_xlabel("Number of workflows",fontsize=14)
            # Set common y-label           
            #f.text(0.06, 0.5, 'Number of video streams', ha='center', va='center', rotation='vertical', fontsize=18)

            #axarr[i-1].set_xlabel('AC-test type',fontsize=18)    
                
            axarr[i-1].set_xticks(ind+(width*2.0))
            axarr[i-1].set_xticklabels( labels , rotation=0)
            t[0].set_y(1.09)  
            #plt.subplots_adjust(top=0.86) 
            
        
def _autolabel(rects, ax, extra_text=None):
    j=0
    for rect in rects:
        height = rect.get_height()   
        
        #y_cord = (height *1.05) if height>0 else (height *1.05)
        
        if(height>80):
            y_cord = (height *1.00)
        elif(height>0):
            y_cord = (height *1.05)
        elif(height == 0):
            y_cord = (height +2.0)
        else:
            y_cord = (height *1.05)
            
             
        if(extra_text != None):
            if(extra_text[j]>0):
                ax.text( rect.get_x()+rect.get_width()/2., y_cord, '%d(%d)*'%( int(height), int(extra_text[j])  ),
                        ha='center', va='bottom', fontsize=18)
            else:
                ax.text( rect.get_x()+rect.get_width()/2., y_cord, '%d'%( int(height)  ),
                        ha='center', va='bottom', fontsize=18)
        else:
            ax.text( rect.get_x()+rect.get_width()/2., y_cord, '%d'%( int(height)  ),
                        ha='center', va='bottom', fontsize=18)
        
        j+=1 
            
#autolabel(rects1)
            



###################################################################################################
#    Utilisation comparisons, visualisations
###################################################################################################
   
def plot_InstUtilisation(summaryHist=False, fillPlots=False):        
        
    ##############################
    ####### gather results 
    ##############################   
        
    folder = 'experiment_data/vs_ac_test/'
    
    actest_none_all_data = []
    actest_heu_all_data = []
    actest_sched_all_data = []
    actest_hybv1_all_data = []
    
    actest_none_sumnodes = []
    actest_none_sumnodes = [[] for i in NUM_WORKFLOWS] # init
    actest_heu_sumnodes = []
    actest_heu_sumnodes = [[] for i in NUM_WORKFLOWS] # init
    actest_sched_sumnodes = []
    actest_sched_sumnodes = [[] for i in NUM_WORKFLOWS] # init
    
    for each_wf_num in NUM_WORKFLOWS:
        
        ## none ##
        # get data        
        fname =  folder + "ACTest_none_" +'wf'+str(each_wf_num)+'_cores'+str(SimParams.NUM_NODES) + "__utilisation.js"
        json_data=open(fname)
        actest_none_all_data.append(json.load(json_data))                
        
        ## heuristics ##
        # get data        
        fname =  folder + "ACTest_heu_" +'wf'+str(each_wf_num)+'_cores'+str(SimParams.NUM_NODES) + "__utilisation.js"
        json_data=open(fname)
        actest_heu_all_data.append(json.load(json_data))        
                
        ## sched-test ##
        # get data
        data = []
        fname =  folder + "ACTest_sched_" +'wf'+str(each_wf_num)+'_cores'+str(SimParams.NUM_NODES) + "__utilisation.js"      
        json_data=open(fname)            
        actest_sched_all_data.append(json.load(json_data))   
        
#        ## hybrid_v1 ##
#        data = []
#        fname =  folder + "ACTest_hybv1_" +'wf'+str(each_wf_num)+'_cores'+str(SimParams.NUM_NODES) + "__utilisation.js"
#        json_data=open(fname)            
#        actest_hybv1_all_data.append(json.load(json_data))
#        
        
    ##############################
    ####### format data
    ##############################
    
    ## for none ##
    allwfs_node_usage_none = []
    for wf_id in xrange(len(NUM_WORKFLOWS)):
        node_usage_none = [[] for i in range(NUM_NODES)] # init        
        
        for each_data_point in actest_none_all_data[wf_id]['node_network']:
            temp_sum = 0
            for each_node_id in xrange(NUM_NODES):
                node_usage_none[each_node_id].append(each_data_point['csp_tc'][each_node_id])
                temp_sum +=  each_data_point['csp_tc'][each_node_id]
            
            actest_none_sumnodes[wf_id].append(temp_sum)
            
        allwfs_node_usage_none.append(node_usage_none)
    
    ## for heuristic based ##
    allwfs_node_usage_heu = []
    for wf_id in xrange(len(NUM_WORKFLOWS)):
        node_usage_heu = [[] for i in range(NUM_NODES)] # init
        
        for each_data_point in actest_heu_all_data[wf_id]['node_network']:
            temp_sum = 0
            for each_node_id in xrange(NUM_NODES):
                node_usage_heu[each_node_id].append(each_data_point['csp_tc'][each_node_id])
                temp_sum +=  each_data_point['csp_tc'][each_node_id]
            
            actest_heu_sumnodes[wf_id].append(temp_sum)
        
        allwfs_node_usage_heu.append(node_usage_heu)
                    
    
    ## for shed based ##
    allwfs_node_usage_sched = []
    for wf_id in xrange(len(NUM_WORKFLOWS)):
        node_usage_sched = [[] for i in range(NUM_NODES)] # init
        
        for each_data_point in actest_sched_all_data[wf_id]['node_network']:
            temp_sum = 0
            for each_node_id in xrange(NUM_NODES):
                node_usage_sched[each_node_id].append(each_data_point['csp_tc'][each_node_id])
                temp_sum +=  each_data_point['csp_tc'][each_node_id]
            
            actest_sched_sumnodes[wf_id].append(temp_sum)
    
        allwfs_node_usage_sched.append(node_usage_sched)
    
    
#    ## for hybv1 based ##
#    allwfs_node_usage_hybv1 = []
#    for wf_id in xrange(len(NUM_WORKFLOWS)):
#        node_usage_hybv1 = [[] for i in range(NUM_NODES)] # init
#        
#        for each_data_point in actest_hybv1_all_data[wf_id]:
#            for each_node_id in xrange(NUM_NODES):
#                node_usage_hybv1[each_node_id].append(each_data_point['csp_tc'][each_node_id])
#    
#        allwfs_node_usage_hybv1.append(node_usage_hybv1)
    
    #####################################
    ####### plot util as function of time 
    #####################################
    if(fillPlots==True):
        
        plt.plot(actest_none_sumnodes[0], color='k', linewidth=0.1)
        plt.fill_between(range(0,len(actest_none_sumnodes[0])), min(actest_none_sumnodes[0]), actest_none_sumnodes[0], facecolor='r', alpha=0.5)
        plt.hold(True)
        plt.plot(actest_heu_sumnodes[0], color='k', linewidth=0.1)
        plt.fill_between(range(0,len(actest_heu_sumnodes[0])), min(actest_heu_sumnodes[0]), actest_heu_sumnodes[0], facecolor='g', alpha=0.5)
        plt.hold(True)
        plt.plot(actest_sched_sumnodes[0], color='k', linewidth=0.1)
        plt.fill_between(range(0,len(actest_sched_sumnodes[0])), min(actest_sched_sumnodes[0]), actest_sched_sumnodes[0], facecolor='b', alpha=0.5)
    
    if(summaryHist==True):
    
        ##############################
        ####### plot histogram 
        ##############################
        
        wf_labels = range(8,19,1)
        REDUCED_NUM_WORKFLOWS = range(0,16,2)
        fig = plt.figure()
        #fig.canvas.set_window_title("NumWorkflows = " + str(REDUCED_NUM_WORKFLOWS[wf_id]))
        i=1
        for wf_id in xrange(0,len(wf_labels),2):
            
            print wf_id
            print  wf_labels[wf_id]
            
            
            ax = plt.subplot(2,3,i)
            
            boxpos_nu_none=range(1,(len(allwfs_node_usage_none[wf_id])*3),3)
            boxpos_nu_hue=range(2,(len(allwfs_node_usage_heu[wf_id])*3)+2,3)
            boxpos_nu_sched=range(3,(len(allwfs_node_usage_sched[wf_id])*3)+3,3)        
            
            labels = [str(x) for x in range(NUM_NODES)]    
            
            # plot box plots
            bp=ax.boxplot(allwfs_node_usage_none[wf_id],0,'', whis=1, positions=boxpos_nu_none, patch_artist=True)
            _set_bp(ax, bp, 'red')            
            bp=ax.boxplot(allwfs_node_usage_heu[wf_id],0,'', whis=1, positions=boxpos_nu_hue, patch_artist=True)
            _set_bp(ax, bp, 'green')            
            bp=ax.boxplot(allwfs_node_usage_sched[wf_id],0,'', whis=1, positions=boxpos_nu_sched, patch_artist=True)
            _set_bp(ax, bp, 'blue')
            
    #        bp=plt.boxplot(allwfs_node_usage_hybv1[wf_id],0,'', whis=1, positions=boxpos_nu_hybv1)
    #        plt.setp(bp['boxes'], color='green', linewidth=1)
    #        plt.setp(bp['caps'], color='green')
    #        plt.setp(bp['whiskers'], color='green')
    #        plt.setp(bp['fliers'], color='green')
    #        plt.setp(bp['medians'], color='green')
            
            ## figure specs
            plt.xlabel('Nodes',fontsize=18)
            plt.ylabel('Tasks completed',fontsize=18)
            plt.title('Workflows='+str(wf_labels[wf_id]), fontsize=18, fontweight="bold")
            #plt.setxticks(range(1,len(dyn_results['labels'])+1), dyn_results['labels'])
            ax.set_xticklabels(labels)
            
            xticks = range(1,(len(labels)*3),3)
            xticks = [x+0.5 for x in xticks]
            
            ax.set_xticks(xticks)
            plt.xlim(0,(len(labels)*3)+1)
            #plt.ylim(-0.35,-0.25)
            ax.yaxis.grid(True)
            ax.xaxis.grid(True)
            ax.tick_params(axis='both', which='major', labelsize=16)
            
            hR, = ax.plot([1,1],'r-')
            hB, = ax.plot([1,1],'b-')        
            hG, = ax.plot([1,1],'g-')
            #leg = ax.legend((hR, hG, hB),('None', 'Heu', 'Sched'))
            #leg.draggable()        
            hR.set_visible(False)
            hG.set_visible(False)
            hB.set_visible(False)
            
            # plot means
            ax.hold(True)
            means_none = [np.mean(x) for x in allwfs_node_usage_none[wf_id]]
            ax.plot(boxpos_nu_none, means_none, marker='*', linestyle='-', color='r', linewidth=3)
            ax.hold(True)
            means_heu = [np.mean(x) for x in allwfs_node_usage_heu[wf_id]]
            ax.plot(boxpos_nu_hue, means_heu, marker='*', linestyle='-', color='g', linewidth=3)
            ax.hold(True)
            means_sched = [np.mean(x) for x in allwfs_node_usage_sched[wf_id]]
            ax.plot(boxpos_nu_sched, means_sched, marker='*', linestyle='-', color='b', linewidth=3)
    #        plt.hold(True)
    #        means_hybv1 = [np.mean(x) for x in allwfs_node_usage_hybv1[wf_id]]
    #        plt.plot(boxpos_nu_hybv1, means_hybv1, marker='*', linestyle='-', color='g', linewidth=3)
            
            i+=1
            
            
            
            
def plot_InstUtilisation_VH(summaryHist=False, fillPlots=False):        
    
    NUM_WORKFLOWS = [8,16]
    WF_RANGE = [8, 16]
    
    ##############################
    ####### gather results 
    ##############################   
    
    folder = 'experiment_data/vs_ac_test/'
    all_exp_data = OrderedDict()    
    
    for each_wf_num in NUM_WORKFLOWS:
        
        exp_data = OrderedDict()
        
        ## No AC ##
        # get data        
        fname =  folder + "ACTest_none_" +'wf'+str(each_wf_num)+'_cores'+str(SimParams.NUM_NODES) + "__utilisation.js"
        json_data=open(fname)
        file_data = json.load(json_data)
        exp_data['No-AC'] = file_data
        
        ## deterministic-test ##
        # get data
        data = []
        fname =  folder + "ACTest_sched_" +'wf'+str(each_wf_num)+'_cores'+str(SimParams.NUM_NODES) + "__utilisation.js"     
        json_data=open(fname)            
        file_data = json.load(json_data)
        exp_data['Determ.'] = file_data         
        
        #### ac_test : heuristics - KG deadline assignment 
#        FNAME_PREFIX = "ACTest_heukgES_"
#        fname =  folder + FNAME_PREFIX +'wf'+str(each_wf_num)+'_cores'+str(SimParams.NUM_NODES) + "__utilisation.js"      
#        json_data=open(fname)
#        file_data = json.load(json_data)
#        exp_data['Heu_ES'] = file_data                 
              
        FNAME_PREFIX = "ACTest_heukgEQF_"
        fname =  folder + FNAME_PREFIX +'wf'+str(each_wf_num)+'_cores'+str(SimParams.NUM_NODES) + "__utilisation.js"      
        json_data=open(fname)
        file_data = json.load(json_data)
        exp_data['Heu\n(D-EQF)'] = file_data                 
                     
       
        ## variable heuristics ##
        for each_ratio_combo in RATIO_COMBINATIONS:
            
            each_ibuff_ratio = each_ratio_combo[0]
            each_tq_ratio = each_ratio_combo[1]
                
            FNAME_PREFIX = "ACTest_heuth_" + "iblr" + str(each_ibuff_ratio) + "_tqlr" + str(each_tq_ratio) + "_"
            
            fname =  folder + FNAME_PREFIX +'wf'+str(each_wf_num)+'_cores'+str(SimParams.NUM_NODES) + "__utilisation.js"      
            json_data=open(fname)
            heuth_entry = json.load(json_data)               
            key = "Heu:" + "IBLR_\\alpha" + str(each_ibuff_ratio) + ", TQL_\\alpha" + str(each_tq_ratio)
            key_2 = "Heu\n" "(" + str(each_ibuff_ratio) + "," + str(each_tq_ratio) + ")"
            exp_data[key_2] = heuth_entry
                
        all_exp_data[each_wf_num] = exp_data
                
              
    #####################################
    ####### format data, get what we need
    #####################################
        
    allwfs_idletime_allperms = OrderedDict()
    node_specific_idletimes = OrderedDict()
    node_specific_idletimes_with_totalsimtime = OrderedDict()
    mean_idletime = []
    for wf_id in NUM_WORKFLOWS:
        
        node_specific_idletimes[wf_id] = []
        node_specific_idletimes_with_totalsimtime[wf_id] = []
        
        allwfs_idletime_allperms[wf_id] = []
        for each_exp_key, each_exp_data in all_exp_data[wf_id].iteritems():
            mean_idletimes = [] 
            sum_idletimes = []
            mean_busytimes = []
            sum_busytimes = [] 
            std_idletime = []          
            for each_data_point in each_exp_data['node_idle_time']:
                total_idle = 0
                total_busy = 0
                for idle_time in each_data_point['nsit']:                    
                    total_idle +=  idle_time
                    total_busy += float(1.0-idle_time)
                     
                mean_idletimes.append(float(total_idle/len(each_data_point['nsit'])))
                mean_busytimes.append(float(total_busy/len(each_data_point['nsit'])))
                sum_idletimes.append(total_idle)
                sum_busytimes.append(total_busy)
                std_idletime.append(np.std(each_data_point['nsit']))
                       
            mean_throughput = [] 
            sum_throughput = []
            for each_data_point in each_exp_data['node_throughput']:
                total_t = 0                
                for idle_time in each_data_point['csp_tc']:                    
                    total_t +=  idle_time
                     
                mean_throughput.append(float(total_t/len(each_data_point['csp_tc'])))
                sum_throughput.append(total_t)
            
            allwfs_idletime_allperms[wf_id].append(mean_idletimes)            
            
            total_sim_time = float(len(each_exp_data['node_idle_time']) * SimParams.SIM_MONITOR_SAMPLE_RATE * 1.0)
           
            node_specific_idletimes[wf_id].append(each_exp_data['node_idle_time'][-1])
            
            temp_entry = {
                          'total_idletime' : each_exp_data['node_idle_time'][-1],
                          'total_simtime' : 37.0
                          
                          }
            
            node_specific_idletimes_with_totalsimtime[wf_id].append(temp_entry)
        
    #####################################
    ####### fill plots 
    #####################################
    
#    plt.figure()
#    max_orig_datalen = 0
#    max_ma_datalen = 0
#    markers = itertools.cycle((',', '+', '.', 'o', '*')) 
#    lcols = itertools.cycle(('r', 'g', 'b', 'y', 'k', 'aqua', 'darksalmon', 'beige', 'chocolate', 'darkorange', 'cadetblue', 'cornsilk'))
#    #labels = [("Heu_"+chr(65+x)) for x in range(0,len(all_exp_data[8].keys())-2)]
#    #labels.insert(0,"None")
#    #labels.insert(1,"Deterministic")
#    
#    labels = [("%s"%x) for x in all_exp_data[8].keys()]
#    
#    colors = matplotlib.colors.cnames.keys()[0:len(labels)]
#    
#    window_size = 10
#    wf_id = 14
#    
#    x = np.arange(0,len(all_exp_data[wf_id].values()), SimParams.SIM_MONITOR_SAMPLE_RATE) 
#    
#    for each_exp_data, lbl, c in zip(all_exp_data[wf_id].values(), labels, colors):
#        
#        data = [np.sum(each_data_point['nsit']) for each_data_point in each_exp_data['node_idle_time']]
#        data_moving_avg = _movingaverage(data, window_size)
#        
#       
#        plt.plot(data, label=lbl, marker=markers.next(), lw=1.0, color=c)
#        plt.hold(True)
#        plt.fill_between(range(0,len(data)), min(data), data, alpha=0.3, lw=1.0, color=c)
#        plt.hold(True)
#        
#        if(len(data)>max_orig_datalen):
#            max_orig_datalen = len(data)
#        if(len(data_moving_avg)>max_ma_datalen):
#            max_ma_datalen = len(data_moving_avg)
#    
#    #x_tick_labels = [str(x) for x in np.arange(0,max_len, float(SimParams.SIM_MONITOR_SAMPLE_RATE*window_size))]
#    
#    
#    total_orig_sim_time = SimParams.SIM_MONITOR_SAMPLE_RATE*max_orig_datalen
#    
#    xticks = np.arange(0,max_ma_datalen)    
#    xticks = [x for x in xticks]
#    xticks = xticks[0::10]
#    
#    xlabel = [ str(x*10) for x in
#    np.arange(0,max_ma_datalen*SimParams.SIM_MONITOR_SAMPLE_RATE, SimParams.SIM_MONITOR_SAMPLE_RATE)]
#    
#    plt.tick_params(axis='both', which='major', labelsize=20)
#    plt.xticks(xticks, xlabel)
#    plt.grid(True)
#    leg = plt.legend()
#    #leg.draggable()
        
    
    ##############################
    ####### plot boxplots 
    ##############################    
    labels = [("%s"%x) for x in all_exp_data[8].keys()]
#    f_0, axarr_0 = plt.subplots(len(WF_RANGE), sharex=True)
#    f_0.canvas.set_window_title("Utilisation boxplots")
#    
    f_1, axarr_1 = plt.subplots(len(WF_RANGE), sharex=True)
    f_1.canvas.set_window_title("Utilisation nodespecific")
#    
#    
#    # labels
#    #real_labels = [(r'$%s$'%x) for x in allwfs_goplateness_allperms[8].keys()]
#    #pprint.pprint(real_labels)
#    labels = [("Heu_"+chr(65+x)) for x in range(0,len(all_exp_data[8].keys())-2)]
#    labels.insert(0,"None")
#    labels.insert(1,"Deterministic")
#    pprint.pprint(labels)
#    
#    i=0
#    for wf_id in WF_RANGE:
#        
#        each_wf_data = allwfs_idletime_allperms[wf_id]
#        each_wf_key = wf_id
#        
#        boxpos=range(1,len(allwfs_idletime_allperms[wf_id]),1) 
#        boxpos_means=range(0,len(allwfs_idletime_allperms[wf_id]),1)
#        
#        # plot box plots
#        bp=axarr_0[i].boxplot(allwfs_idletime_allperms[wf_id],0,'', whis=1, positions=boxpos, widths=0.8)
#        means =  [np.mean(x) for x in allwfs_idletime_allperms[wf_id]]      
#        axarr_0[i].plot(boxpos_means, means, marker='x', markersize=5, linestyle='', color='g', linewidth=1.0)
#    
#        ## figure specs
#        axarr_0[i].yaxis.grid(True)
#        axarr_0[i].xaxis.grid(True)
#        
#        axarr_0[i].set_title('Workflows = '+ str(wf_id))
#        
#        i+= 1               
#
#    #axarr[i-1].set_xlabel('AC-test type',fontsize=18)    
#    xticks = range(1,(len(labels)*1),1)
#    xticks = [x for x in xticks]
#    plt.tick_params(axis='both', which='major', labelsize=12)
#    axarr_0[i-1].set_xticks(xticks)
#    axarr_0[i-1].set_xticklabels(labels)

    #################################
    ####### plot bars different wfs
    ################################# 
    i=0   
    
    
    node_data = 0
    bar_width = 0.3
    
    node_data_mean = 0.0
    for wf_id in WF_RANGE:
        positions = np.arange(len(node_specific_idletimes[wf_id]))        
        mean_ns_idletimes = [np.mean(each_exp['it_c'])  for each_exp in node_specific_idletimes[wf_id] if 'it_c' in each_exp]        
        axarr_1[i].bar(positions, mean_ns_idletimes, width=bar_width)                   
        
        i+=1
        
    xticks = range(0,len(labels))
    xticks = [x for x in xticks]
    plt.tick_params(axis='both', which='major', labelsize=10)
    axarr_1[i-1].set_xticks(xticks)
    axarr_1[i-1].set_xticklabels(labels)
    
    #################################
    ####### plot lines all wfs in one
    #################################  
    plt.figure()
    summation = {}
    
    total_sim_time = {}
    ind = np.arange(len([each_exp['total_idletime'] for each_exp in node_specific_idletimes_with_totalsimtime[8] if 'it_c' in each_exp['total_idletime']]))
    width = 0.25
    positions = [ind, ind+width]
    
    lcols = itertools.cycle(('blanchedalmond', 'blueviolet'))
    i=0
    for wf_id in WF_RANGE:
        summation[wf_id] = [ 100.0-float(float(np.mean(each_exp['total_idletime']['it_c']))/each_exp['total_simtime'])*100.0 for each_exp in node_specific_idletimes_with_totalsimtime[wf_id] if 'it_c' in each_exp['total_idletime']]
        #total_sim_time[wf_id] = 0
        
        #plt.bar(positions[0:len(summation[wf_id])], summation[wf_id], width=width, label='wf' + str(wf_id))
        #plt.hold(True)
        plt.bar(positions[i], summation[wf_id], width=width, color=lcols.next(), alpha=0.9)                
        
        i+=1
    plt.hold(True)
    p = plt.axvspan(0.0, (width*5.0)+(width*1.75), facecolor='0.5', alpha=0.3)
    
    xticks = ind+(width*1.0)
    xticks = [x for x in xticks]
    plt.tick_params(axis='both', which='major', labelsize=20)
    plt.xticks(xticks, labels)    
    
    plt.grid(True)
    #leg = plt.legend()
    #leg.draggable()
        
        
        
        
def _set_bp(ax, bp, col):
    plt.setp(bp['boxes'], color=col, linewidth=1, alpha=0.7)    
    plt.setp(bp['caps'], color=col)
    plt.setp(bp['whiskers'], color=col)
    plt.setp(bp['fliers'], color=col)
    plt.setp(bp['medians'], color=col)
    


###################################################################################################
#    GOP lateness - different AC tests
###################################################################################################   

def plot_GOPLateness():
        
        
    ##############################
    ####### gather results 
    ##############################   
        
    folder = 'experiment_data/vs_ac_test/'
    
    actest_heu_all_data = []
    actest_sched_all_data = []
    actest_hybv1_all_data = []
    
    for each_wf_num in NUM_WORKFLOWS:
        
        ## heuristics ##
        # get data        
        fname =  folder + "ACTest_heu_" +'wf'+str(each_wf_num)+'_cores'+str(SimParams.NUM_NODES) + "_gopsopbuffsumm.js"
        json_data=open(fname)
        actest_heu_all_data.append(json.load(json_data))        
        
        
        ## sched-test ##
        # get data
        data = []
        fname =  folder + "ACTest_sched_" +'wf'+str(each_wf_num)+'_cores'+str(SimParams.NUM_NODES) + "_gopsopbuffsumm.js"      
        json_data=open(fname)            
        actest_sched_all_data.append(json.load(json_data))   
        
        ## hybrid_v1 ##
        data = []
        fname =  folder + "ACTest_hybv1_" +'wf'+str(each_wf_num)+'_cores'+str(SimParams.NUM_NODES) + "_gopsopbuffsumm.js"
        json_data=open(fname)            
        actest_hybv1_all_data.append(json.load(json_data))
        
        
    ##############################
    ####### format data
    ##############################
    
    
    ## for heuristic based ##
    allwfs_goplateness_heu = []
    for wf_id in xrange(len(NUM_WORKFLOWS)):
        gop_lateness_heu = [[] for i in range(NUM_NODES)] # init        
        for each_ugid_key, each_ugid_val in actest_heu_all_data[wf_id].iteritems():            
                gop_lateness_heu.append(each_ugid_val['gop_execution_lateness'])
        
        allwfs_goplateness_heu.append(gop_lateness_heu)
    
    
    ## for hybv1 based ##
    allwfs_goplateness_hybv1 = []
    for wf_id in xrange(len(NUM_WORKFLOWS)):
        gop_lateness_hybv1 = [[] for i in range(NUM_NODES)] # init        
        for each_ugid_key, each_ugid_val in actest_hybv1_all_data[wf_id].iteritems():            
                gop_lateness_hybv1.append(each_ugid_val['gop_execution_lateness'])
        
        allwfs_goplateness_hybv1.append(gop_lateness_hybv1)
    
    
    
    ##############################
    ####### plot histogram 
    ##############################    

    fig = plt.figure()
    fig.canvas.set_window_title("Gop Lateness per wf")
    ax = plt.subplot(111)
    
    boxpos_gl_hue=range(1,len(allwfs_goplateness_heu)*2,2)
    boxpos_gl_hybv1=range(2,(len(allwfs_goplateness_hybv1)*2)+2,2)
    
    labels = [str(x) for x in NUM_WORKFLOWS]    
    
    # plot box plots
    bp=plt.boxplot(allwfs_goplateness_heu,0,'', whis=1, positions=boxpos_gl_hue)
    plt.setp(bp['boxes'], color='blue', linewidth=1)
    plt.setp(bp['caps'], color='blue')
    plt.setp(bp['whiskers'], color='blue')
    plt.setp(bp['fliers'], color='blue')
    plt.setp(bp['medians'], color='blue')
    
    bp=plt.boxplot(allwfs_goplateness_hybv1,0,'', whis=1, positions=boxpos_gl_hybv1)
    plt.setp(bp['boxes'], color='green', linewidth=1)
    plt.setp(bp['caps'], color='green')
    plt.setp(bp['whiskers'], color='green')
    plt.setp(bp['fliers'], color='green')
    plt.setp(bp['medians'], color='green')
    
    ## figure specs
    plt.xlabel('workflows',fontsize=18)
    plt.ylabel('gop lateness',fontsize=18)
    #plt.setxticks(range(1,len(dyn_results['labels'])+1), dyn_results['labels'])
    ax.set_xticklabels(labels)
    
    xticks = range(1,(len(labels)*2),2)
    xticks = [x+0.5 for x in xticks]
    
    ax.set_xticks(xticks)
    plt.xlim(0,(len(labels)*2)+1)
    #plt.ylim(-0.35,-0.25)
    ax.yaxis.grid(True)
    ax.xaxis.grid(True)
    plt.tick_params(axis='both', which='major', labelsize=16)
    
    hB, = plt.plot([1,1],'b-')    
    hG, = plt.plot([1,1],'g-')
    leg = plt.legend((hB, hG),('Heu', 'hybv1'))
    leg.draggable()
    hB.set_visible(False)    
    hG.set_visible(False)
    
    # plot means
#    plt.hold(True)
#    means_heu = [np.mean(x) for x in allwfs_goplateness_heu]
#    plt.plot(boxpos_gl_hue, means_heu, marker='*', linestyle='-', color='b', linewidth=3)
#    plt.hold(True)    
#    means_hybv1 = [np.mean(x) for x in allwfs_goplateness_hybv1]
#    plt.plot(boxpos_gl_hybv1, means_hybv1, marker='*', linestyle='-', color='g', linewidth=3)



# variable heuristics
def plot_GOPLateness_VH():
        
    
    NUM_WORKFLOWS = [8,16] 
    
    ##############################
    ####### gather results 
    ##############################   
    
    folder = 'experiment_data/vs_ac_test/'
    all_exp_data = OrderedDict()
    
    
    for each_wf_num in NUM_WORKFLOWS:
        
        exp_data = OrderedDict()
        
        ## No AC ##
        # get data        
        fname =  folder + "ACTest_none_" +'wf'+str(each_wf_num)+'_cores'+str(SimParams.NUM_NODES) + "_gopsopbuffsumm.js"
        json_data=open(fname)
        file_data = json.load(json_data)
        exp_data['No-AC'] = file_data
        
        ## deterministic-test ##
        # get data
        data = []
        fname =  folder + "ACTest_sched_" +'wf'+str(each_wf_num)+'_cores'+str(SimParams.NUM_NODES) + "_gopsopbuffsumm.js"      
        json_data=open(fname)            
        file_data = json.load(json_data)
        exp_data['Determ.'] = file_data   
        
        #### ac_test : heuristics - KG deadline assignment 
#        FNAME_PREFIX = "ACTest_heukgES_"
#        fname =  folder + FNAME_PREFIX +'wf'+str(each_wf_num)+'_cores'+str(SimParams.NUM_NODES) + "_gopsopbuffsumm.js"      
#        json_data=open(fname)
#        file_data = json.load(json_data)               
#        exp_data['Heu_ES'] = file_data
        
        FNAME_PREFIX = "ACTest_heukgEQF_"
        fname =  folder + FNAME_PREFIX +'wf'+str(each_wf_num)+'_cores'+str(SimParams.NUM_NODES) + "_gopsopbuffsumm.js"      
        json_data=open(fname)
        file_data = json.load(json_data)               
        exp_data['Heu\n(D-EQF)'] = file_data
        
       
        ## variable heuristics ##
        for each_ratio_combo in RATIO_COMBINATIONS:
            
            each_ibuff_ratio = each_ratio_combo[0]
            each_tq_ratio = each_ratio_combo[1]
                
            FNAME_PREFIX = "ACTest_heuth_" + "iblr" + str(each_ibuff_ratio) + "_tqlr" + str(each_tq_ratio) + "_"
            
            fname =  folder + FNAME_PREFIX +'wf'+str(each_wf_num)+'_cores'+str(SimParams.NUM_NODES) + "_gopsopbuffsumm.js"      
            json_data=open(fname)
            heuth_entry = json.load(json_data)               
            key = "Heu:" + "IBLR_\\alpha" + str(each_ibuff_ratio) + ", TQL_\\alpha" + str(each_tq_ratio)
            key_2 =  'Heu\n' + "(" + str(each_ibuff_ratio) + "," + str(each_tq_ratio) + ")"
            
            exp_data[key_2] = heuth_entry
                
        all_exp_data[each_wf_num] = exp_data
                
       
       
    #####################################
    ####### format data, get what we need
    #####################################
        
    allwfs_goplateness_allperms = OrderedDict()
    for wf_id in NUM_WORKFLOWS:
        
        allwfs_goplateness_allperms[wf_id] = []
        for each_exp_key, each_exp_data in all_exp_data[wf_id].iteritems():
            
            temp_gop_lateness_data = []
            for each_ugid_key, each_ugid_val in each_exp_data.iteritems():
                if(each_ugid_val['gop_execution_lateness'] > 0):
                    temp_gop_lateness_data.append(each_ugid_val['gop_execution_lateness'])
                
            if(len(temp_gop_lateness_data)==0):
                temp_gop_lateness_data = [0]           
            
            allwfs_goplateness_allperms[wf_id].append(temp_gop_lateness_data)
                
    
    ##############################
    ####### plot boxplots 
    ##############################    
    WF_RANGE = [8, 16]
    
    f, axarr = plt.subplots(len(WF_RANGE), sharex=True)
    f.canvas.set_window_title("Gop Lateness per AC-test")
    
    # labels
    labels = [("%s" %x) for x in all_exp_data[8].keys()]
    #labels = [("Heu_"+chr(65+x)) for x in range(0,len(all_exp_data[8].keys())-2)]        
    #labels.insert(0,"No-AC")
    #labels.insert(1,"Determ.")
    #pprint.pprint(labels)
    
    i=0
    for wf_id in WF_RANGE:
                
        each_wf_data = allwfs_goplateness_allperms[wf_id]
        each_wf_key = wf_id
        
        boxpos=np.arange(len(allwfs_goplateness_allperms[wf_id])) 
        boxpos_means=np.arange(len(allwfs_goplateness_allperms[wf_id]))
       
        # plot box plots
        p = axarr[i].axvspan(-0.5, 1 + 0.5, facecolor='0.5', alpha=0.2)        
        bp=axarr[i].boxplot(allwfs_goplateness_allperms[wf_id],0,'', whis=1, positions=boxpos, widths=0.8)
        plt.setp(bp['boxes'], color='b', linewidth=1.25)        
        plt.setp(bp['caps'], color='b', linewidth=1.25)
        plt.setp(bp['whiskers'], color='b', linewidth=1.25)
        plt.setp(bp['fliers'], color='b', linewidth=1.25)
        plt.setp(bp['medians'], color='r', linewidth=1.25)
        
        means =  [np.mean(x) for x in allwfs_goplateness_allperms[wf_id]]      
        max_lateness = [max(x) for x in allwfs_goplateness_allperms[wf_id]] 
        sum_lateness = [sum(x) for x in allwfs_goplateness_allperms[wf_id]]
        
        width = 0.30
            
        axarr[i].plot(boxpos_means, means, marker='d', markersize=10, linestyle='', color='g', linewidth=0.5, label="Mean job lateness")
        axarr[i].plot(boxpos_means, max_lateness, marker='o', markersize=10, linestyle='--', color='r', linewidth=0.5, label="Maximum job lateness")
        #rects0 = axarr[i].bar(boxpos_means, max_lateness, color='b', width=width, alpha=1.0)
        #axarr[i].plot(boxpos_means, sum_lateness, marker='x', markersize=5, linestyle='', color='b', linewidth=1.0)
        
        for ix,each_max_val in enumerate(max_lateness):
            if(each_max_val <0): gap=-1.10
            else:
                if(each_max_val > 2.0): gap=0.85
                else: gap=1.10
            #axarr[i].text(boxpos_means[ix], gap*each_max_val, '%.3f'%float(each_max_val), ha='center', va='bottom', fontsize=16)
                
        axarr[i].tick_params(axis='both', which='major', labelsize=20)
        ## figure specs
        axarr[i].yaxis.grid(True)
        axarr[i].xaxis.grid(True)
        axarr[i].set_title('Workflows = '+ str(wf_id), fontsize=20)
        
        i+= 1
    
    xticks = range(0,(len(labels)))
    xticks = [x for x in xticks]
    
    axarr[i-1].set_xticks(xticks)
    axarr[i-1].set_xticklabels(labels)
    #leg = axarr[i-1].legend(bbox_to_anchor=(1.05, 0), loc='lower left', borderaxespad=0.)
    #leg.draggable()    

    ##############################
    ####### plot lines single plot
    ##############################    
    WF_RANGE = [8, 16]
    
    f = plt.figure()
    f.canvas.set_window_title("Gop Lateness per AC-test for all wfs")
    
    # labels
    labels = [(r"%s" %x) for x in all_exp_data[8].keys()]
    
    i=0
    for wf_id in WF_RANGE:
                
        each_wf_data = allwfs_goplateness_allperms[wf_id]
        each_wf_key = wf_id
        
        pos=np.arange(len(allwfs_goplateness_allperms[wf_id])) 
        pos_means=np.arange(len(allwfs_goplateness_allperms[wf_id]))
       
        # plot box plots
        p = plt.axvspan(0, 1 + 0.5, facecolor='0.5', alpha=0.1)        
        
        means =  [np.mean(x) for x in allwfs_goplateness_allperms[wf_id]]      
        max_lateness = [max(x) for x in allwfs_goplateness_allperms[wf_id]] 
        sum_lateness = [sum(x) for x in allwfs_goplateness_allperms[wf_id]]
            
        #plt.plot(pos_means+(width*0.5), means, marker='d', markersize=6, linestyle='-', color='y', linewidth=1.0)
        ax = plt.plot(pos_means, max_lateness, linewidth=2,marker='*', markersize=8 )
 
#        for ix,each_max_val in enumerate(max_lateness):
#            if(each_max_val <0): gap=-1.10
#            else: gap=1.10
#            plt.text(boxpos_means[ix]+(width*0.5), gap*each_max_val, '%.3f'%float(each_max_val), ha='center', va='bottom', fontsize=16)
                
        plt.tick_params(axis='both', which='major', labelsize=12)
        ## figure specs
        plt.grid(True)
        plt.hold(True)
        
        i+= 1
    
    xticks = range(0,(len(labels)))
    xticks = [x for x in xticks]
    
    plt.xticks(xticks, labels)
    



def plot_priority_vs_lateness():
    
    
    NUM_WORKFLOWS = range(8,19,2) 
    IBUFF_TASKS_LATENESS_RATIO_RANGE = [0.5, 0.6, 0.7, 0.8]
    TQ_TASKS_LATENESS_RATIO_RANGE = [0.5, 0.6, 0.7, 0.8]







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

#plot_ACTest_Results_VidStats_HeuVar(wf_id=None, plot3D=False)
#plot_ACTest_Results_VidStats()
#plot_InstUtilisation(summaryHist=True)
#plot_GOPLateness()
plot_GOPLateness_VH()
#plot_InstUtilisation_VH(summaryHist=True)
print "finished"

plt.show()

