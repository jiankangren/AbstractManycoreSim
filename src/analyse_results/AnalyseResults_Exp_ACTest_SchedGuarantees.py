import sys, os, csv, pprint, math

import numpy as np
import random
import shutil
import math
import matplotlib
matplotlib.use('Qt4Agg')
import matplotlib.pyplot as plt
plt.style.use('bmh_rosh')
import scipy.stats
from itertools import cycle # for automatic markers
import json


#from AdmissionControllerOptions import AdmissionControllerOptions
#from SimParams import SimParams


#import Multicore_MPEG_Model as MMMSim


NUM_WORKFLOWS = range(8, 19, 1)
#NUM_WORKFLOWS = [9]
#NUM_NODES = [2,4,8,16,32]
NUM_NODES = 9
NOC_XY = [(2,1), (2,2), (2,4), (2,8), (2,16)]


###################################################################################################
#    Comparison of different Schedulability guarantees
###################################################################################################  


def plot_SchedulabilityPercentage_vs_DeadlineMiss():
    
    EXP_RESULTS_FOLDER = '../experiment_data/sched_percentage_compare/archive/archive_060614/'
    
    listdir = os.listdir(EXP_RESULTS_FOLDER)
    
    all_runs_num_vids_acc_late = []
    all_runs_num_vids_success = []
    all_runs_num_vids_rejected = []    
    total_vids = []
    
    all_gop_lateness_avg = []
    all_gop_lateness_max = []
    all_gop_lateness_all = {}
    
    sample_size = 0
    
    for each_dir in listdir:
        if('seed_' in each_dir):            
            seed_folder = EXP_RESULTS_FOLDER + each_dir            
            
            print seed_folder            
            
            ##############################
            ####### gather results 
            ##############################
          
            percentage_list = range(0, 80, 5)
            
            NUM_WORKFLOWS = 11
            NUM_NODES = 9
            
            exp_data = []   
            temp_all_gop_lateness_max = []
            temp_all_gop_lateness_avg = []
            
            
            for each_sched_percentage in percentage_list:
                
                FNAME_PREFIX = "ACTest_sched_p" + str(each_sched_percentage) + "_"
                EXP_OUTPUT_FOLDER = "sched_percentage_compare/"         
                
                ## vid-stats
                #### ac_test : schedulability test only 
                vs_bs_fname = seed_folder + '/' + FNAME_PREFIX + 'wf'+str(NUM_WORKFLOWS)+'_cores'+str(NUM_NODES) + ".js"
                json_data=open(vs_bs_fname)
                file_data = json.load(json_data)        
                
                exp_data.append(file_data)
                
                ## gop lateness
                data = []
                fname =  seed_folder + '/' + FNAME_PREFIX + 'wf'+str(NUM_WORKFLOWS)+'_cores'+str(NUM_NODES) + "_gopsopbuffsumm.js"      
                json_data=json.load(open(fname))
                
                
                temp_all_gop_lateness_max.append(max([x['gop_execution_lateness'] for x in json_data.values()]))
                temp_all_gop_lateness_avg.append(np.mean([x['gop_execution_lateness'] for x in json_data.values()]))
                
                
                # record all latenesses across all seeds
                if each_sched_percentage not in all_gop_lateness_all:
                    all_gop_lateness_all[each_sched_percentage]= []
                    all_gop_lateness_all[each_sched_percentage].extend([x['gop_execution_lateness'] for x in json_data.values() 
                                                                        if x['gop_execution_lateness']>0])
                else:
                    all_gop_lateness_all[each_sched_percentage].extend([x['gop_execution_lateness'] for x in json_data.values() 
                                                                        if x['gop_execution_lateness']>0])
                
               
                
                #actest_sched_all_data.append(json.load(json_data))  
            
            all_gop_lateness_max.append(temp_all_gop_lateness_max)
            all_gop_lateness_avg.append(temp_all_gop_lateness_avg)
            
            
            #pprint.pprint(all_gop_lateness_max)
            #sys.exit()    
                
            
            ##############################
            ####### plot results 
            ##############################
            num_vids_accepted_late = []
            num_vids_success = []
            num_vids_rejected = []
            num_total_vids = []
            
            for each_record in exp_data:
            
                num_vids_accepted_late.append(int(each_record['num_vids_accepted_late']))      
                num_vids_success.append(int(each_record['num_vids_accepted_success']))
                num_vids_rejected.append(int(each_record['num_vids_rejected']))
                
                num_total_vids = int(each_record['num_vids_accepted_late']) + \
                                int(each_record['num_vids_accepted_success']) + \
                                int(each_record['num_vids_rejected'])
            
            all_runs_num_vids_acc_late.append(num_vids_accepted_late)
            all_runs_num_vids_success.append(num_vids_success)
            all_runs_num_vids_rejected.append(num_vids_rejected)
            total_vids.append(num_total_vids)
        
            sample_size += 1
    
    #########################################
    ## box plots -- lateness
    #########################################
    
    ## ------
    plt.figure("all_gop_lateness_max")  
    ax = plt.subplot(111)
    bp_labels = [str(x) + "%" for x in percentage_list]
    
    all_gop_lateness_max = np.array(all_gop_lateness_max)
    bp=plt.boxplot(all_gop_lateness_max,0,'', whis=1)    
    ax.set_xticklabels(bp_labels)    
    xticks = range(1,(len(bp_labels)+1))
    xticks = [x for x in xticks]    
    ax.set_xticks(xticks)
    ax.grid(True)
    plt.xlabel('Schedulability guarantee (%)',fontsize=18)
    plt.ylabel('Maximum GOP lateness',fontsize=18)
    
    ## ------
    plt.figure("all_gop_lateness_avg")    
    ax = plt.subplot(111)
    all_gop_lateness_avg = np.array(all_gop_lateness_avg)
    bp=plt.boxplot(all_gop_lateness_avg,0,'', whis=1)  
    ax.set_xticklabels(bp_labels)    
    xticks = range(1,(len(bp_labels)+1))
    xticks = [x for x in xticks]    
    ax.set_xticks(xticks)
    ax.grid(True)
    plt.xlabel('Schedulability guarantee (%)',fontsize=18)
    plt.ylabel('Maximum GOP lateness',fontsize=18)
    
    
    
    ## ------
    plt.figure("all_gop_lateness_all")    
    ax = plt.subplot(111)    
    xticks = np.arange((len(bp_labels)))    
    
    bpdata = [ all_gop_lateness_all[p] for p in percentage_list ]   
    
    boxpos=np.arange(len(bpdata))   
    max_bpdata = [ np.max(all_gop_lateness_all[p]) if (len(all_gop_lateness_all[p])>0) else np.nan for p in percentage_list]
    
    bp=ax.boxplot(bpdata,notch=0,sym='', whis=1, widths=0.8, patch_artist=True, positions=xticks) 
     
    # stylise boxplots
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
    
    # draw max job lateness
    plt.hold(True)
    ax2 = ax.twinx()
    p_maxes = ax2.plot(xticks, max_bpdata, marker='o', markersize=10, linestyle='--', color='r', linewidth=1.0, label="Maximum job lateness (s)")
    ax2.set_ylabel("Maximum job lateness (s)")
    ax2.tick_params(axis='y', labelsize=12, color='r', labelcolor='r')
     
    ax.set_xticks(xticks)
    ax.set_xticklabels(bp_labels)
    
    ax.grid(True)
    ax.set_xlabel(r"Scaled down WCRT: $\{r_i,R_i\}\times\beta$")
    ax.set_ylabel('Job lateness(s)')
   
    
    
    
    
    
    #########################################
    ## line plots -- success/late/rejected ##
    #########################################
    
    plt.figure("adminrate")
    
    # plot success
    all_runs_num_vids_success = np.array(all_runs_num_vids_success)
    mean_of_num_vids_success = all_runs_num_vids_success.mean(axis=0)
    sem = scipy.stats.sem(all_runs_num_vids_success, axis=0)
    
    plt.plot(percentage_list, mean_of_num_vids_success, marker='x', color='g', label='Admitted and fully schedulable')
    plt.hold(True)
    #plt.errorbar(percentage_list, mean_of_num_vids_success, sem, ecolor = 'black', fmt = None, marker='o')
    
    # plot late             
    all_runs_num_vids_acc_late = np.array(all_runs_num_vids_acc_late)
    mean_of_num_vids_acc_late = all_runs_num_vids_acc_late.mean(axis=0)
    sem = scipy.stats.sem(all_runs_num_vids_acc_late, axis=0)
    
    plt.plot(percentage_list, mean_of_num_vids_acc_late, marker='o', color='b', label='Admitted but late')
    plt.hold(True)
    #plt.errorbar(percentage_list, mean_of_num_vids_acc_late, sem, ecolor = 'black', fmt = None, marker='o')
        
    # plot rejected
    all_runs_num_vids_rejected = np.array(all_runs_num_vids_rejected)
    mean_of_num_vids_rejected = all_runs_num_vids_rejected.mean(axis=0)
    sem = scipy.stats.sem(all_runs_num_vids_rejected, axis=0)
    
    plt.plot(percentage_list, mean_of_num_vids_rejected, marker='d', color='r', label='Rejected')
    #plt.hold(True)
    #plt.errorbar(percentage_list, mean_of_num_vids_rejected, sem, ecolor = 'black', fmt = None, marker='o')
    
    plt.xlabel(r"Scaled down WCRT: $\{r_i,R_i\}\times\beta$")
    plt.ylabel('Number of video streams')
    
    hSucc, = plt.plot([1,1],'g-')
    hLate, = plt.plot([1,1],'b-')
    hRej, = plt.plot([1,1],'r-')
    #leg = plt.legend((hSucc, hLate, hRej),('Admitted and fully schedulable', 'Admitted but late', 'Rejected'))
    leg = plt.legend(ncol=1, fontsize=12)
    leg.draggable()
    hSucc.set_visible(False)    
    hLate.set_visible(False)    
    hRej.set_visible(False)
    
#    # total
#    total_vids = np.array(total_vids)
#    mean_of_total_vids = total_vids.mean(axis=0)
#    sem = scipy.stats.sem(total_vids, axis=0)
#    
#    pprint.pprint(mean_of_total_vids)
#    
#    plt.plot(percentage_list, mean_of_total_vids, marker='o', color='k')
#    plt.hold(True)
#    plt.errorbar(percentage_list, mean_of_total_vids, sem, ecolor = 'black', fmt = None, marker='o')
    
    plt.xticks(percentage_list, bp_labels)
    plt.grid(True)
        
    
    
        
    
    
        
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
    



#plot_ACTest_Results_VidStats()
#plot_InstUtilisation(summaryHist=True)
#plot_GOPLateness()
plot_SchedulabilityPercentage_vs_DeadlineMiss()
print "finished"

plt.show()

