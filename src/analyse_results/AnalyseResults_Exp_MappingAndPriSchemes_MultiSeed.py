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

from libMappingAndScheduling.SemiDynamic.TaskMappingSchemes import TaskMappingSchemes
from libMappingAndScheduling.SemiDynamic.TaskSemiDynamicPrioritySchemes import TaskSemiDynamicPrioritySchemes
from libMappingAndScheduling.SemiDynamic.TaskMappingAndPriAssCombinedSchemes import TaskMappingAndPriAssCombinedSchemes


import Multicore_MPEG_Model as MMMSim





RANDOM_SEED_LIST = \
[81665, 33749, 43894, 26358, 80505, \
 83660, 22817, 70263, 29917, 26044, \
 5558,  76891, 22250, 42198, 18065, \
 74076, 98652, 21149, 50399, 64217, \
 44117, 57824, 42267, 83200, 99108, \
 95928, 53864, 44289, 77379, 80521, \
 88117, 23327, 73337, 94064, 31982, \
 6878, 66093, 69541]
#[81665]
#[98652, 
#64217,
#29917,
#73337,
#99108,
#43894,
#22817,
#22250,
#77379,
#88117,
#44117,
#33749,
#94064,
#50399,
#57824,
#44289,
#31982,
#81665,
#6878,
#76891,
#5558,
#70263,
#95928,
#42198]
#[66093, 70263, 26358]

#[81665, 33749, 43894, 26358, 80505, \
# 83660, 22817, 70263, 29917, 26044, \
# 5558,  76891, 22250, 42198, 18065, \
# 74076, 98652, 21149, 50399, 64217, \
# 44117, 57824, 42267, 83200, 99108, \
# 95928, 53864, 44289, 77379, 80521, \
# 88117, 23327, 73337, 94064, 31982, \
# 6878, 66093, 69541]


NUM_WORKFLOWS = [8, 12]
#NUM_WORKFLOWS = [9]
#NUM_NODES = [2,4,8,16,32]
NUM_NODES = 9
NOC_XY = [(2,1), (2,2), (2,4), (2,8), (2,16)]




SCHEME_COMBINATIONS = [(0.5, 0.1)] # (mapping, priority)
        
EXP_DATA_FOLDER = '../experiment_data/mapping_and_pri_schemes/'


###################################################################################################
#    Video predictability statistics : schedulable, late, rejected
###################################################################################################

# Admission control tests :
# - None
# - heu based
# - sched based
def plot_MandPSchemeTest_Results_VidStats_MultiSeed(wf_id = None):

    
    ##############################
    ####### gather results 
    ##############################    
    all_wf_exp_data = {}
    multi_seed_data = {}
    
    
    for each_wf_id in NUM_WORKFLOWS:
        all_wf_exp_data[each_wf_id] = {}
        
        for each_seed in RANDOM_SEED_LIST:        
        
            exp_data = OrderedDict()      # dict that will contain all the results for each param  
                  
            #### ac_test : heuristics threshold based
            for each_scheme_combo in SCHEME_COMBINATIONS:
                
                each_mapping_scheme = each_scheme_combo[0]
                each_pri_scheme = each_scheme_combo[1]
    
                FNAME_PREFIX = "Exp_m"+str(each_mapping_scheme) + "_p"+str(each_pri_scheme) + "_"                                
                vs_bs_fname = EXP_DATA_FOLDER + "seed_" + str(each_seed) + "/" + FNAME_PREFIX + 'wf'+str(each_wf_id)+'_cores'+str(SimParams.NUM_NODES) + "_vsbs.js"
                
                json_data=open(vs_bs_fname)
                file_data = json.load(json_data)                
                key_2 =  "(" + str(each_mapping_scheme) + "," + str(each_pri_scheme) + ")"                
                exp_data[key_2] = _getEntry(file_data)  
            
            all_wf_exp_data[each_wf_id]['seed_'+str(each_seed)] = exp_data 
       
    
    labels = [('%s'%x) for x in exp_data.keys()] 
    
    #sys.exit("done")
    
    
    ##############################
    ####### plot results
    ##############################    
  
    ################# multiple workflow plot : bar plots ##################
    
    # points scheme
#    POINTS_SUCCESS  = 1.0
#    POINTS_REJECT   = 0.0
#    POINTS_LATE     = -1.0
#    POINTS_DROPPED  = -2.0
    
    num_subplots = len(NUM_WORKFLOWS) if len(NUM_WORKFLOWS)>1 else 2

    f, axarr = plt.subplots(num_subplots, sharex=True)
    
    #pprint.pprint(len(axarr))
    #sys.exit()
    
    f.canvas.set_window_title("Predictability results")
    
    i=0
    t=[]
    for each_wf_id in NUM_WORKFLOWS:
        
        each_wf_data = all_wf_exp_data[each_wf_id]
        each_wf_key = each_wf_id
        
        # --------- number of success & failed ----------          
            
        # data for different results categories
        streams_schedulable = _get_multi_seed_data_vidstats('num_vids_accepted_success', each_wf_data, mean=True)
        streams_late = _get_multi_seed_data_vidstats('num_vids_accepted_late', each_wf_data, mean=True)
        streams_rejected = _get_multi_seed_data_vidstats('num_vids_rejected', each_wf_data, mean=True)
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
        
        rects0 = axarr[i].bar(positions[0], streams_schedulable, width=width, color='g', alpha=0.9)                
        rects1 = axarr[i].bar(positions[1], streams_late, width=width, color='b', alpha=0.9)                
        rects2 = axarr[i].bar(positions[2], streams_rejected, width=width, color='#FF4747', alpha=0.9)  
        
        _autolabel(rects0, axarr[i])
        _autolabel(rects1, axarr[i], extra_text=dropped_gops)
        _autolabel(rects2, axarr[i])
         
        axarr[i].grid(True, alpha=0.5)
        t.append(axarr[i].set_title('Number of workflows = '+ str(each_wf_key), fontsize=20))
        
        axarr[i-1].tick_params(axis='both', which='major', labelsize=8)
        
        i+= 1
   
        
    axarr[i-1].set_xticks(ind+(width*2.0))
    axarr[i-1].set_xticklabels( labels , rotation=0)
    #t[0].set_y(1.09)  
            

def _get_multi_seed_data_vidstats(data_filter, all_data, mean=False):    
    each_seed_data = []   
    
    for each_seed in all_data.items():        
        data = [x[data_filter] for x in each_seed[1].values()]        
        each_seed_data.append(data)
    
    reshaped_each_seed_data = np.transpose(each_seed_data)
    
    #pprint.pprint(reshaped_each_seed_data)
    
    if(mean==True):
        #pprint.pprint(reshaped_each_seed_data)
        
        mean_reshaped_each_seed_data = [np.round(np.mean(x)) for x in reshaped_each_seed_data]
        #pprint.pprint(mean_reshaped_each_seed_data)
        #sys.exit()
        return mean_reshaped_each_seed_data
    else:
        return reshaped_each_seed_data


        
def _autolabel(rects, ax, extra_text=None, fsize=8):
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
#    System Utilisation comparisons, visualisations
###################################################################################################
 
            
def plot_MandPSchemeTest_Results_InstSysUtilisation_MultiSeed():        
    ##############################
    ####### gather results 
    ##############################    
    all_wf_exp_data = {}
    multi_seed_data = {}
    
    
    for each_wf_id in NUM_WORKFLOWS:
        all_wf_exp_data[each_wf_id] = {}
        
        for each_seed in RANDOM_SEED_LIST:        
        
            exp_data = OrderedDict()      # dict that will contain all the results for each param  
                  
            #### ac_test : heuristics threshold based
            for each_scheme_combo in SCHEME_COMBINATIONS:
                
                each_mapping_scheme = each_scheme_combo[0]
                each_pri_scheme = each_scheme_combo[1]
    
                FNAME_PREFIX = "Exp_m"+str(each_mapping_scheme) + "_p"+str(each_pri_scheme) + "_"                                
                vs_bs_fname = EXP_DATA_FOLDER + "seed_" + str(each_seed) + "/" + FNAME_PREFIX + 'wf'+str(each_wf_id)+'_cores'+str(SimParams.NUM_NODES) + "_util.js"
                
                json_data=open(vs_bs_fname)
                file_data = json.load(json_data)                
                key_2 =  "(" + str(each_mapping_scheme) + "," + str(each_pri_scheme) + ")"                
                exp_data[key_2] = file_data  
            
            all_wf_exp_data[each_wf_id]['seed_'+str(each_seed)] = exp_data       
    
    labels = [('%s'%x) for x in exp_data.keys()] 
    
   
    #####################################
    ####### format data, get what we need
    #####################################
    node_specific_idletimes_with_totalsimtime = OrderedDict()
        
    for wf_id in NUM_WORKFLOWS:
        node_specific_idletimes_with_totalsimtime[wf_id] = OrderedDict()        
        for each_exp_seed_key, each_exp_seed_data in all_wf_exp_data[wf_id].iteritems():
                            
            for each_exp_key, each_exp_data in each_exp_seed_data.iteritems():

                #total_sim_time = float(len(each_exp_data['node_idle_time']) * 0.2 * 1.0)
                total_sim_time = float(each_exp_data['node_idle_time'][-1]['time'])                               
                temp_entry = {
                              'total_idletime' : each_exp_data['node_idle_time'][-1],
                              'total_idletime_allseeds' : None,                          
                              'total_simtime' : total_sim_time                          
                              }
                
                idle_time_percentage = np.mean(each_exp_data['node_idle_time'][-1]['it_c'])/total_sim_time
                                
                if(each_exp_key not in node_specific_idletimes_with_totalsimtime[wf_id]):
                    node_specific_idletimes_with_totalsimtime[wf_id][each_exp_key] = [idle_time_percentage]
                else:
                    node_specific_idletimes_with_totalsimtime[wf_id][each_exp_key].extend([idle_time_percentage])
    
    
    #################################
    ####### plot lines all wfs in one
    #################################  
    labels = [("%s"%x) for x in node_specific_idletimes_with_totalsimtime[8].keys()]    
    fig = plt.figure()
    fig.canvas.set_window_title("Sys Utilisation results")
    ax = plt.gca()
    summation = {}
    bp_data = {}    
    total_sim_time = {}    
    ind = np.arange(len(node_specific_idletimes_with_totalsimtime[8].keys()))
    
    width = 0.25
    positions = [ind, ind+width]
    
    lcols = itertools.cycle(('blanchedalmond', 'blueviolet'))
    i=0
    for wf_id in NUM_WORKFLOWS:        
        summation[wf_id] = [100.0-float(np.mean(x)*100.0) for x in node_specific_idletimes_with_totalsimtime[wf_id].values()]  
        bp_data[wf_id] = [np.subtract(100.0,np.multiply(x,100.0)) for x in node_specific_idletimes_with_totalsimtime[wf_id].values()]
                                
        plt.bar(positions[i], summation[wf_id], width=width, color=lcols.next(), alpha=0.9)                
        
        if (wf_id == 8): c='#FF9933' 
        else:  c='#6600CC'        
        plt.hold(True)
        
        i+=1
    plt.hold(True)
    
    xticks = ind+(width*1.0)
    xticks = [x for x in xticks]
    plt.tick_params(axis='both', which='major', labelsize=8)
    plt.xticks(xticks, labels)
    plt.grid(True)        
        
        
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
    
    #pprint.pprint(reshaped_each_seed_data)
    
    if(mean==True):
        #pprint.pprint(reshaped_each_seed_data)
        
        mean_reshaped_each_seed_data = [np.mean(x) for x in reshaped_each_seed_data]
        #pprint.pprint(mean_reshaped_each_seed_data)
        #sys.exit()
        return mean_reshaped_each_seed_data
    else:
        return reshaped_each_seed_data


###################################################################################################
#    Link Utilisation comparisons, visualisations
###################################################################################################

def plot_MandPSchemeTest_Results_InstLinkUtilisation_MultiSeed():
    ##############################
    ####### gather results 
    ##############################    
    all_wf_exp_data = {}
    multi_seed_data = {}    
    
    for each_wf_id in NUM_WORKFLOWS:
        all_wf_exp_data[each_wf_id] = {}
        
        for each_seed in RANDOM_SEED_LIST:        
        
            exp_data = OrderedDict()      # dict that will contain all the results for each param  
                  
            #### ac_test : heuristics threshold based
            for each_scheme_combo in SCHEME_COMBINATIONS:
                
                each_mapping_scheme = each_scheme_combo[0]
                each_pri_scheme = each_scheme_combo[1]
    
                FNAME_PREFIX = "Exp_m"+str(each_mapping_scheme) + "_p"+str(each_pri_scheme) + "_"                                
                vs_bs_fname = EXP_DATA_FOLDER + "seed_" + str(each_seed) + "/" + FNAME_PREFIX + 'wf'+str(each_wf_id)+'_cores'+str(SimParams.NUM_NODES) + "_util.js"
                
                json_data=open(vs_bs_fname)
                file_data = json.load(json_data)                
                key_2 =  "(" + str(each_mapping_scheme) + "," + str(each_pri_scheme) + ")"                
                exp_data[key_2] = file_data  
            
            all_wf_exp_data[each_wf_id]['seed_'+str(each_seed)] = exp_data       
    
    labels = [('%s'%x) for x in exp_data.keys()] 
    
   
    #####################################
    ####### format data, get what we need
    #####################################
    total_linkidletime_with_totalsimtime = OrderedDict()
        
    for wf_id in NUM_WORKFLOWS:
        total_linkidletime_with_totalsimtime[wf_id] = OrderedDict()        
        for each_exp_seed_key, each_exp_seed_data in all_wf_exp_data[wf_id].iteritems():
                            
            for each_exp_key, each_exp_data in each_exp_seed_data.iteritems():

                #total_sim_time = float(len(each_exp_data['node_idle_time']) * 0.2 * 1.0)
                total_sim_time = float(each_exp_data['interconnect'][-1]['time']) 
                total_number_of_links = float(len(each_exp_data['interconnect'][-1]['lsp_fc']))
                total_idletime_alllinks = float(each_exp_data['interconnect'][-1]['total_link_idletime']/total_number_of_links)            
                                              
                temp_entry = {
                              'total_idletime' : total_idletime_alllinks,
                              'total_idletime_allseeds' : None,                          
                              'total_simtime' : total_sim_time                          
                              }
                
                idle_time_percentage = total_idletime_alllinks/total_sim_time
                                
                if(each_exp_key not in total_linkidletime_with_totalsimtime[wf_id]):
                    total_linkidletime_with_totalsimtime[wf_id][each_exp_key] = [idle_time_percentage]
                else:
                    total_linkidletime_with_totalsimtime[wf_id][each_exp_key].extend([idle_time_percentage])
    
    
    #################################
    ####### plot lines all wfs in one
    #################################  
    labels = [("%s"%x) for x in total_linkidletime_with_totalsimtime[8].keys()]    
    fig = plt.figure()
    fig.canvas.set_window_title("Link Utilisation results")
    ax = plt.gca()
    summation = {}
    bp_data = {}    
    total_sim_time = {}    
    ind = np.arange(len(total_linkidletime_with_totalsimtime[8].keys()))
    
    width = 0.25
    positions = [ind, ind+width]
    
    lcols = itertools.cycle(('blanchedalmond', 'blueviolet'))
    i=0
    for wf_id in NUM_WORKFLOWS:        
        summation[wf_id] = [100.0-float(np.mean(x)*100.0) for x in total_linkidletime_with_totalsimtime[wf_id].values()]  
        bp_data[wf_id] = [np.subtract(100.0,np.multiply(x,100.0)) for x in total_linkidletime_with_totalsimtime[wf_id].values()]
                                
        plt.bar(positions[i], summation[wf_id], width=width, color=lcols.next(), alpha=0.9)                
        
#        if (wf_id == 8): c='#FF9933' 
#        else:  c='#6600CC'        
        plt.hold(True)
        
        i+=1
    plt.hold(True)
    
    xticks = ind+(width*1.0)
    xticks = [x for x in xticks]
    plt.tick_params(axis='both', which='major', labelsize=8)
    plt.xticks(xticks, labels)
    plt.grid(True)        











###################################################################################################
#    GOP lateness - different AC tests
###################################################################################################   

# variable heuristics
def plot_MandPSchemeTest_Results_GOPLateness_MultiSeed():
        
    ##############################
    ####### gather results 
    ##############################    
    all_wf_exp_data = {}
    multi_seed_data = {}
    
    
    for each_wf_id in NUM_WORKFLOWS:
        all_wf_exp_data[each_wf_id] = {}
        
        for each_seed in RANDOM_SEED_LIST:        
        
            exp_data = OrderedDict()      # dict that will contain all the results for each param  
                  
            #### ac_test : heuristics threshold based
            for each_scheme_combo in SCHEME_COMBINATIONS:
                
                each_mapping_scheme = each_scheme_combo[0]
                each_pri_scheme = each_scheme_combo[1]
    
                FNAME_PREFIX = "Exp_m"+str(each_mapping_scheme) + "_p"+str(each_pri_scheme) + "_"                                
                goplatenessdata_fname = EXP_DATA_FOLDER + "seed_" + str(each_seed) + "/" + FNAME_PREFIX + 'wf'+str(each_wf_id)+'_cores'+str(SimParams.NUM_NODES) + "_gopsopbuffsumm.js"
                
                json_data=open(goplatenessdata_fname)
                file_data = json.load(json_data) 
                key_2 =  "(" + str(each_mapping_scheme) + "," + str(each_pri_scheme) + ")"                
                exp_data[key_2] = file_data
            
            all_wf_exp_data[each_wf_id]['seed_'+str(each_seed)] = exp_data 
       
    
    labels = [('%s'%x) for x in exp_data.keys()]
       
    #####################################
    ####### format data, get what we need
    #####################################
        
    allwfs_goplateness_allperms = OrderedDict()
    for wf_id in NUM_WORKFLOWS:
        
        # concatenate results for all seeds
        allwfs_goplateness_allperms[wf_id] = []
        temp_gop_lateness_data = OrderedDict()
        for each_exp_seed_key, each_exp_seed_data in all_wf_exp_data[wf_id].iteritems():
            
            print each_exp_seed_key
            
            for each_exp_key, each_exp_val in each_exp_seed_data.iteritems():                
                gop_latenesses = [np.round(x['gop_execution_lateness'],2) for x in each_exp_val.values() if (x['gop_execution_lateness'] > 0)]
                
                if(each_exp_key not in temp_gop_lateness_data):
                    temp_gop_lateness_data[each_exp_key] = gop_latenesses
                else:
                    temp_gop_lateness_data[each_exp_key].extend(gop_latenesses)            
                    
        allwfs_goplateness_allperms[wf_id].append(temp_gop_lateness_data)
        
            
    ##############################
    ####### plot boxplots 
    ##############################    
    
    num_subplots = (len(NUM_WORKFLOWS) if len(NUM_WORKFLOWS)>1 else 2)
    f, axarr = plt.subplots(num_subplots, sharex=True)
    f.canvas.set_window_title("Gop Lateness per M-P-Scheme")
    
    # labels
    labels = [("%s" %x) for x in allwfs_goplateness_allperms[8][0].keys()]
    
    i=0
    for wf_id in NUM_WORKFLOWS:
                
        each_wf_data = allwfs_goplateness_allperms[wf_id]
        each_wf_key = wf_id
        
        boxpos=np.arange(len(allwfs_goplateness_allperms[wf_id][0].keys())) 
        boxpos_means=np.arange(len(allwfs_goplateness_allperms[wf_id][0].keys()))
       
        # make sure boxplots have equal sample size
        boxplot_data_orig = [x for x in allwfs_goplateness_allperms[wf_id][0].values()]
        boxplot_data = []
        boxplot_data_maxlengths = max([len(x) for x in allwfs_goplateness_allperms[wf_id][0].values()])
        for each_bp_data in allwfs_goplateness_allperms[wf_id][0].values():
            #new_data = each_bp_data + [0.0]*(len(RANDOM_SEED_LIST) - len(each_bp_data))
            new_data = each_bp_data + [0.0]*(boxplot_data_maxlengths - len(each_bp_data))
            boxplot_data.append(new_data)
       
        # plot box plots                
        bp=axarr[i].boxplot(boxplot_data,0,'', whis=1, positions=boxpos, widths=0.8)
        
        #if(wf_id==8):
        #    pprint.pprint([len(x) for x in allwfs_goplateness_allperms[wf_id][0].values()])
        
        #pprint.pprint([x.get_data()[1][1] for x in bp['whiskers']])        
        max_y_cord = max([x.get_data()[1][1] for x in bp['whiskers']])
        #print max_y_cord 
        
        plt.setp(bp['boxes'], color='b', linewidth=1.25)        
        plt.setp(bp['caps'], color='b', linewidth=1.25)
        plt.setp(bp['whiskers'], color='b', linewidth=1.25)
        plt.setp(bp['fliers'], color='b', linewidth=1.25)
        plt.setp(bp['medians'], color='b', linewidth=1.25)
        
        means =  [np.mean(x) if len(x)>0 else 0 for x in allwfs_goplateness_allperms[wf_id][0].values()]      
        max_lateness = [max(x) if len(x)>0 else 0 for x in allwfs_goplateness_allperms[wf_id][0].values()] 
        sum_lateness = [sum(x) if len(x)>0 else 0 for x in allwfs_goplateness_allperms[wf_id][0].values()]
        
        width = 0.30
            
        axarr[i].plot(boxpos_means, means, marker='d', markersize=10, linestyle='', color='g', linewidth=1.0, label="Mean job lateness")
        #axarr[i].plot(boxpos_means, max_lateness, marker='o', markersize=10, linestyle='--', color='r', linewidth=0.5, label="Maximum job lateness")        
        
        plt.hold(True)
        ax2 = axarr[i].twinx()
        ax2.plot(boxpos_means, max_lateness, marker='o', markersize=10, linestyle='--', color='r', linewidth=1.0, label="Maximum job lateness")       
        #ax2.set_ylabel('core_sum_idletimes', color='r')
        
        for ix,each_max_val in enumerate(max_lateness):
            if(each_max_val <0): gap=-1.10
            else:
                if(each_max_val > 2.0): gap=0.85
                else: gap=1.10
        
        ## figure specs        
        axarr[i].yaxis.grid(True, which='both')
        axarr[i].xaxis.grid(True)
        axarr[i].set_title('Workflows = '+ str(wf_id), fontsize=20)
        axarr[i].set_ylim([0.0, max_y_cord])        
        ax2.tick_params(axis='y', labelsize=20, color='r', labelcolor='r')
        axarr[i].tick_params(axis='x', which='both', labelsize=8, labelcolor='k')
        axarr[i].tick_params(axis='y', which='both', labelsize=8, labelcolor='b')
        
        i+= 1       
    
    xticks = [x for x in range(0,(len(labels)))]    
    axarr[i-1].set_xticks(xticks)
    axarr[i-1].set_xticklabels(labels)
    
    

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

def _get_all_scheme_combos(x, y):
    combinations = []
    for each_x in x:
        for each_y in y:
            pair = (each_x, each_y)
            combinations.append(pair)
    
    # extra combo
    combinations.append((800,800)) #TaskMappingAndPriAssCombinedSchemes.TASKMAPPINGANDPRIASSCOMBINED_IMPACTSCORING_V1
    #combinations.append((9,4))
    combinations.append((801,801)) #TaskMappingAndPriAssCombinedSchemes.TASKMAPPINGANDPRIASSCOMBINED_IMPACTSCORING_V2
    combinations.append((802,802)) #TaskMappingAndPriAssCombinedSchemes.TASKMAPPINGANDPRIASSCOMBINED_IMPACTSCORING_V2
    combinations.append((810,810)) #TaskMappingAndPriAssCombinedSchemes.TASKMAPPINGANDPRIASSCOMBINED_IMPACTSCORING_V2    
    combinations.append((820,820)) #TaskMappingAndPriAssCombinedSchemes.TASKMAPPINGANDPRIASSCOMBINED_IMPACTSCORING_V2
    
    
    return combinations
 
def _get_scheme_alpha_labels(mapping_schemes, pri_ass_schemes):    
    
    mapping_text_dict = {
        0 : "MP:None",    
        1 : "MP:Random",
        2 : "MP:ShortesTQ",
        3 : "MP:HighestThroughput",
        4 : "MP:LowestThroughput",  
        5 : "MP:LowestRemCC",
        6 : "MP:HighestRemCC",
    }
    pri_ass_text_dict = {
        0 : "PR:None",
        1 : "PR:LowestTQPri",
        2 : "PR:GlobalLowestTQPri",
        3 : "PR:HighestResFirst",
        4 : "PR:LowestResFirst"
    }
    
    
    all_labels = []
    
    for each_mp_sch in mapping_schemes:
        for each_pri_ass_sch in pri_ass_schemes:
            
            label = "(" + str(each_mp_sch) + "," + str(each_pri_ass_sch) + ") - " +  \
                    mapping_text_dict[each_mp_sch] + " , " + pri_ass_text_dict[each_pri_ass_sch]
            
            all_labels.append(label)
            
    return all_labels
            
    
 
 
 
###################################
#    MAIN
###################################           


SCHEME_COMBINATIONS = _get_all_scheme_combos([2,5,8,9],[0,1,2,4])

#plot_MandPSchemeTest_Results_VidStats_MultiSeed(wf_id=None)
plot_MandPSchemeTest_Results_GOPLateness_MultiSeed()
#plot_MandPSchemeTest_Results_InstSysUtilisation_MultiSeed()
#plot_MandPSchemeTest_Results_InstLinkUtilisation_MultiSeed()


pprint.pprint(_get_scheme_alpha_labels([1,2,3,4,5,6],[0,1,2,3]))


print "finished"

plt.show()

