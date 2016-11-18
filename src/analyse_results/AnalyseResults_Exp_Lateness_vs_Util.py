import sys, os, csv, pprint, math

import numpy as np
import random
import shutil
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import scipy.stats
from matplotlib.colors import ListedColormap, NoNorm
from matplotlib import mlab
from itertools import cycle # for automatic markers

import matplotlib.cm as cm
from matplotlib.font_manager import FontProperties

#from AdmissionControllerOptions import AdmissionControllerOptions
from SimParams import SimParams


import Multicore_MPEG_Model as MMMSim


NUM_WORKFLOWS = range(2, 17, 2)
#NUM_WORKFLOWS = [9]
NUM_NODES = [2,4,8,16,32]
NOC_XY = [(2,1), (2,2), (2,4), (2,8), (2,16)]


# lateness vs. number of cores
def plot_LatenessComparisons_varyingCores():
    
    
    folder = 'experiment_data/lateness/'
    
    FbFalse_all_data = []
    FbFalse_all_summary = []
    
    for i in xrange(5):
        
        print "i = " + str(NUM_NODES[i])
        
        
        ## get data ##
        fname = 'experiment_data/lateness/FbFalse_wf'+str(16)+'_cores'+str(NUM_NODES[i])+"__data.txt"
        file = open(fname, 'r')        
        data = file.readlines()
        data = [float(x.strip()) for x in data]        
        FbFalse_all_data.append(data)
        
        ## get summary ##        
        summary = []
        fname = 'experiment_data/lateness/FbFalse_wf'+str(16)+'_cores'+str(NUM_NODES[i])+"__summary.txt"
        file = open(fname, 'r')        
        summary = file.readline()
        summary = summary.strip()
        summary = summary.split(',')
        
        entry = {
                 'num_workflow' : NUM_NODES[i],
                 'total_blocks_dispatched' : int(summary[0]),
                 'gops_successfully_completed' : int(summary[1]),
                 'gops_late_but_fully_complete' : int(summary[2]),
                 'avg_gop_lateness' : float(summary[3]),
                 'max_gop_lateness' : float(summary[4]),
                 'min_gop_lateness' : float(summary[5]),
                 'sum_gop_lateness' : float(summary[6])                 
                 }
        
        FbFalse_all_summary.append(entry)
                
    
    ###############################
    # lateness vs cores 
    ###############################
    
    fig = plt.figure(1)
    fig.canvas.set_window_title('lateness vs cores')
    ax = plt.subplot(111)
    
    #boxpos_FbFalse=range(1,len(FbFalse_all_data)*1,1)    
    
    labels = [str(x) for x in NUM_NODES]
    
    # plot box plots
    bp=plt.boxplot(FbFalse_all_data, whis=1)
    plt.setp(bp['boxes'], color='blue', linewidth=1)
    plt.setp(bp['caps'], color='blue')
    plt.setp(bp['whiskers'], color='blue')
    plt.setp(bp['fliers'], color='blue')
    plt.setp(bp['medians'], color='blue')
    
    ## figure specs
    plt.xlabel('Number of cores',fontsize=18)
    plt.ylabel('GOP Lateness',fontsize=18)    
    ax.set_xticklabels(labels)    
    ax.set_xticks(range(1,len(labels)+1),labels)
    ax.yaxis.grid(True)
    plt.tick_params(axis='both', which='major', labelsize=16)
    
    
    ###############################
    # Total lateness vs cores.
    ###############################
    
    fig = plt.figure(2)
    fig.canvas.set_window_title('Total lateness vs. cores')
    ax = plt.subplot(111)
        
    # avg-lateness
    fb_false_sum_lateness = [x['sum_gop_lateness'] for x in FbFalse_all_summary]
    
    ind = np.arange(len(fb_false_sum_lateness))
    width = 0.35
    
    rects1 = ax.bar(ind, fb_false_sum_lateness, width, color='b')    
    
    ax.set_ylabel('GOP Lateness',fontsize=18)
    ax.set_xlabel('Number of cores',fontsize=18)    
    plt.tick_params(axis='both', which='major', labelsize=16)    
    ax.set_xticks(ind+width)
    ax.set_xticklabels( labels )
    
    plt.grid(True)
    


# feedback on/off lateness comparison
def plot_LatenessComparisons_boxplot():
    
    
    folder = 'experiment_data/lateness/'
    
    FbFalse_all_data = []
    FbTrue_all_data = []
    
    for each_wf_num in NUM_WORKFLOWS:
        
        ## FB_disabled ##
        # get data
        data = []
        fname =  folder + "FbFalse_wf" +str(each_wf_num)+'_cores'+str(SimParams.NUM_NODES)+"__data.txt"
        file = open(fname, 'r')
        
        data = file.readlines()
        data = [float(x.strip()) for x in data]
        
        FbFalse_all_data.append(data)
        
        
        ## FB_enabled ##
        # get data
        data = []
        fname =  folder + "FbTrue_wf" +str(each_wf_num)+'_cores'+str(SimParams.NUM_NODES)+"__data.txt"
        file = open(fname, 'r')
        
        data = file.readlines()
        data = [float(x.strip()) for x in data]
        
        FbTrue_all_data.append(data)
    
    #pprint.pprint(FbTrue_all_data)
    
    fig = plt.figure()
    fig.canvas.set_window_title('Feedback Enabled/Disabled - Lateness comparison - boxplots')
    ax = plt.subplot(111)
    
    boxpos_FbFalse=range(1,len(FbFalse_all_data)*2,2)
    boxpos_FbTrue=range(2,(len(FbTrue_all_data)*2)+2,2)
    
    labels = [str(x) for x in NUM_WORKFLOWS]    
    
    # plot box plots
    bp=plt.boxplot(FbFalse_all_data, whis=1, positions=boxpos_FbFalse)
    plt.setp(bp['boxes'], color='blue', linewidth=1)
    plt.setp(bp['caps'], color='blue')
    plt.setp(bp['whiskers'], color='blue')
    plt.setp(bp['fliers'], color='blue')
    plt.setp(bp['medians'], color='blue')
    
    bp=plt.boxplot(FbTrue_all_data, whis=1, positions=boxpos_FbTrue)
    plt.setp(bp['boxes'], color='red', linewidth=1)
    plt.setp(bp['caps'], color='red')
    plt.setp(bp['whiskers'], color='red')
    plt.setp(bp['fliers'], color='red')
    plt.setp(bp['medians'], color='red')
    
    ## figure specs
    plt.xlabel('Workflows',fontsize=18)
    plt.ylabel('GOP Lateness',fontsize=18)
    #plt.setxticks(range(1,len(dyn_results['labels'])+1), dyn_results['labels'])
    ax.set_xticklabels(labels)
    
    xticks = range(1,(len(labels)*2),2)
    xticks = [x+0.5 for x in xticks]
    
    ax.set_xticks(xticks)
    plt.xlim(0,(len(labels)*2)+1)
    #plt.ylim(-0.35,-0.25)
    ax.yaxis.grid(True)
    plt.tick_params(axis='both', which='major', labelsize=16)
    
    #ax.set_yscale('log')
    
    hB, = plt.plot([1,1],'b-')
    hR, = plt.plot([1,1],'r-')
    leg = plt.legend((hB, hR),('Feedback-DISABLED', 'Feedback-ENABLED'))
    leg.draggable()
    hB.set_visible(False)
    hR.set_visible(False)
    
    return (FbFalse_all_data, FbTrue_all_data)
    
        

def plot_LatenessComparisons_summary():
        
    folder = 'experiment_data/lateness/'
    
    FbFalse_all_data = []
    FbTrue_all_data = []
    
    for each_wf_num in NUM_WORKFLOWS:
        
        ## FB_disabled ##
        # get data
        data = []
        fname =  folder + "FbFalse_wf" +str(each_wf_num)+'_cores'+str(SimParams.NUM_NODES)+"__summary.txt"
        file = open(fname, 'r')
        
        data = file.readline()
        data = data.strip()
        data = data.split(',')
        
        entry = {
                 'num_workflow' : each_wf_num,
                 'total_blocks_dispatched' : int(data[0]),
                 'gops_successfully_completed' : int(data[1]),
                 'gops_late_but_fully_complete' : int(data[2]),
                 'avg_gop_lateness' : float(data[3]),
                 'max_gop_lateness' : float(data[4]),
                 'min_gop_lateness' : float(data[5]),
                 'sum_gop_lateness' : float(data[6])                 
                 }
        
        FbFalse_all_data.append(entry)
        
        
        ## FB_enabled ##
        # get data
        data = []
        fname =  folder + "FbTrue_wf" +str(each_wf_num)+'_cores'+str(SimParams.NUM_NODES)+"__summary.txt"
        file = open(fname, 'r')
        
        data = file.readline()
        data = data.strip()
        data = data.split(',')
        
        entry = {
                 'num_workflow' : each_wf_num,
                 'total_blocks_dispatched' : int(data[0]),
                 'gops_successfully_completed' : int(data[1]),
                 'gops_late_but_fully_complete' : int(data[2]),
                 'avg_gop_lateness' : float(data[3]),
                 'max_gop_lateness' : float(data[4]),
                 'min_gop_lateness' : float(data[5]),
                 'sum_gop_lateness' : float(data[6])                 
                 }
        
        FbTrue_all_data.append(entry)
        
        
    # now we plot
    labels = [str(x) for x in NUM_WORKFLOWS]  
    
    ###############################
    # AVG - lateness
    ###############################
    
    fig = plt.figure(1)
    fig.canvas.set_window_title('Avgerage lateness')
    ax = plt.subplot(111)
        
    # avg-lateness
    fb_false_avg_lateness = [x['avg_gop_lateness'] for x in FbFalse_all_data]
    fb_true_avg_lateness = [x['avg_gop_lateness'] for x in FbTrue_all_data]
    
    ind = np.arange(len(fb_false_avg_lateness))
    width = 0.35
    
    rects1 = ax.bar(ind, fb_false_avg_lateness, width, color='r')
    rects2 = ax.bar(ind+width, fb_true_avg_lateness, width, color='y')
    
    ax.set_ylabel('GOP Lateness',fontsize=18)
    ax.set_xlabel('Workflows',fontsize=18)
    ax.set_title('Average lateness',fontsize=18)
    plt.tick_params(axis='both', which='major', labelsize=16)    
    ax.set_xticks(ind+width)
    ax.set_xticklabels( labels )

    leg = ax.legend( (rects1[0], rects2[0]), ('Feedback-Disabled', 'Feedback-Enabled') )    
    
    #leg = plt.legend((hB, hR),('Feedback-DISABLED', 'Feedback-ENABLED'))
    leg.draggable()
    #hB.set_visible(False)
    #hR.set_visible(False)
    
    ###############################
    # MAX - lateness
    ###############################
    
    fig = plt.figure(2)
    fig.canvas.set_window_title('Maximum lateness')
    ax = plt.subplot(111)
        
    # avg-lateness
    fb_false_avg_lateness = [x['max_gop_lateness'] for x in FbFalse_all_data]
    fb_true_avg_lateness = [x['max_gop_lateness'] for x in FbTrue_all_data]
    
    ind = np.arange(len(fb_false_avg_lateness))
    width = 0.35
    
    rects1 = ax.bar(ind, fb_false_avg_lateness, width, color='r')
    rects2 = ax.bar(ind+width, fb_true_avg_lateness, width, color='y')
    
    ax.set_ylabel('GOP Lateness',fontsize=18)
    ax.set_xlabel('Workflows',fontsize=18)
    ax.set_title('Maximum lateness',fontsize=18)
    plt.tick_params(axis='both', which='major', labelsize=16)    
    ax.set_xticks(ind+width)
    ax.set_xticklabels( labels )

    leg = ax.legend( (rects1[0], rects2[0]), ('Feedback-Disabled', 'Feedback-Enabled') )

    
    
    #leg = plt.legend((hB, hR),('Feedback-DISABLED', 'Feedback-ENABLED'))
    leg.draggable()
    #hB.set_visible(False)
    #hR.set_visible(False)


    ###############################
    # Total - lateness
    ###############################
    
    fig = plt.figure(3)
    fig.canvas.set_window_title('Total lateness')
    ax = plt.subplot(111)
        
    # avg-lateness
    fb_false_avg_lateness = [x['sum_gop_lateness'] for x in FbFalse_all_data]
    fb_true_avg_lateness = [x['sum_gop_lateness'] for x in FbTrue_all_data]
    
    ind = np.arange(len(fb_false_avg_lateness))
    width = 0.35
    
    rects1 = ax.bar(ind, fb_false_avg_lateness, width, color='r')
    rects2 = ax.bar(ind+width, fb_true_avg_lateness, width, color='y')
    
    ax.set_ylabel('GOP Lateness',fontsize=18)
    ax.set_xlabel('Workflows',fontsize=18)
    ax.set_title('Total lateness',fontsize=18)
    plt.tick_params(axis='both', which='major', labelsize=16)    
    ax.set_xticks(ind+width)
    ax.set_xticklabels( labels )


    leg = ax.legend( (rects1[0], rects2[0]), ('Feedback-Disabled', 'Feedback-Enabled') )

    
    
    #leg = plt.legend((hB, hR),('Feedback-DISABLED', 'Feedback-ENABLED'))
    leg.draggable()
    #hB.set_visible(False)
    #hR.set_visible(False)




def plot_InstUtilisation(wf):
        
    folder = 'experiment_data/lateness/'
    
    FbFalse_all_data = []
    FbTrue_all_data = []
    
    for each_wf_num in NUM_WORKFLOWS:
        
        ## FB_disabled ##
        # get data
        data = []
        fname =  folder + "FbFalse_wf" +str(each_wf_num)+'_cores'+str(SimParams.NUM_NODES)+"__utilisation.txt"
        file = open(fname, 'r')
        
        data = file.readlines()
        data = [(float(x.strip())*100.0) for x in data]        
        FbFalse_all_data.append(data)
        
        ## FB_enabled ##
        # get data
        data = []
        fname =  folder + "FbTrue_wf" +str(each_wf_num)+'_cores'+str(SimParams.NUM_NODES)+"__utilisation.txt"
        file = open(fname, 'r')
        
        data = file.readlines()
        data = [(float(x.strip())*100.0) for x in data]            
        FbTrue_all_data.append(data)
        
        
    if wf != None:
        # now we plot
        labels = [str(x) for x in NUM_WORKFLOWS]  
        
        fig = plt.figure(1)
        fig.canvas.set_window_title('Inst. Utilisation')
        ax = plt.subplot(111)
        
        fbk = {'lw':0.5, 'edgecolor':'k', 'alpha':0.5}
        
        x = np.arange(0.0, float(len(FbTrue_all_data[wf]))*SimParams.SIM_MONITOR_SAMPLE_RATE, SimParams.SIM_MONITOR_SAMPLE_RATE)
        
        #print len(x)
        #print len(FbTrue_all_data[wf])    
        
        d = len(FbTrue_all_data[wf])
        
        #ax.fill_between(x[0:d], 0, FbTrue_all_data[wf],facecolor = 'r',label='enabled', **fbk)
        ax.scatter(x, FbTrue_all_data[wf], c='r')
        
        plt.hold(True)
        
        x = np.arange(0.0, float(len(FbFalse_all_data[wf]))*SimParams.SIM_MONITOR_SAMPLE_RATE, SimParams.SIM_MONITOR_SAMPLE_RATE)    
        
        #print len(x)
        #print len(FbFalse_all_data[wf])
        #ax.fill_between(x, 0, FbFalse_all_data[wf],facecolor = 'b',label='disabled', **fbk)
        ax.scatter(x, FbFalse_all_data[wf], c='b')
        
        
        ax.set_ylabel('System utilisation %',fontsize=18)
        ax.set_xlabel('Simulation time',fontsize=18)
        plt.tick_params(axis='both', which='major', labelsize=16)
        
        #plt.xlim(3.598,3.759)
        #plt.ylim(0.0,1.0)
        hB, = plt.plot([1,1],'b-',linewidth=2.5)
        hR, = plt.plot([1,1],'r-',linewidth=2.5)
        leg = plt.legend((hB, hR),('Feedback-DISABLED', 'Feedback-ENABLED'))
        leg.draggable()
        hB.set_visible(False)
        hR.set_visible(False)
        
        #ax.set_yscale('log')

        ### diff plot ###
        fig = plt.figure(2)
        fig.canvas.set_window_title('Inst. Utilisation - diff')
        ax = plt.subplot(111)
        
        if(len(FbFalse_all_data[wf]) < len(FbTrue_all_data[wf])):
            size = len(FbFalse_all_data[wf])
        else:
            size = len(FbTrue_all_data[wf])
        
        diff = [] 
        for i in xrange(size):
            diff.append(FbTrue_all_data[wf][i] - FbFalse_all_data[wf][i])
            
        x = np.arange(0.0, float(len(diff))*SimParams.SIM_MONITOR_SAMPLE_RATE, SimParams.SIM_MONITOR_SAMPLE_RATE) 
        
        plt.plot(x, diff, 'k')
        plt.grid(True)
        
        
    else:
        
        NUM_CORES = 9
        
        # adjust data to account for lack of data in certain percentages
        bin_ranges = [(float(x)/float(NUM_CORES-1))*100.0 for x in range(NUM_CORES+1)]
        
        nrows = len(NUM_WORKFLOWS)
        
        ind = range(10)
        labels = [("%.2f%%"%x) for x in bin_ranges]  
        #width = 0.35
        
        #fig = plt.figure(1)
        f, axarr = plt.subplots(nrows, sharex=True)
        
        #axarr[0].set_xticks(ind+width)
        axarr[0].set_xticklabels([""]*10)
        
        
        
        for wf_id in xrange(len(NUM_WORKFLOWS)):
            
            if(len(FbFalse_all_data[wf_id]) < len(FbTrue_all_data[wf_id])):
                size = len(FbFalse_all_data[wf_id])            
            else:
                size = len(FbTrue_all_data[wf_id])
            
            diff = [] 
            for i in xrange(size):
                diff.append(FbTrue_all_data[wf_id][i] - FbFalse_all_data[wf_id][i])
           
            #x = np.arange(0.0, float(len(diff))*SimParams.SIM_MONITOR_SAMPLE_RATE, SimParams.SIM_MONITOR_SAMPLE_RATE) 
            #x = np.arange(0.0, float(size)*SimParams.SIM_MONITOR_SAMPLE_RATE, SimParams.SIM_MONITOR_SAMPLE_RATE)
                                    
            #plt.plot(x, np.cumsum(diff), 'k')
            #plt.plot(x, np.cumsum(FbTrue_all_data[wf_id][0:size]), 'r')
            #plt.subplot(nrows,1, wf_id+1)
            #plt.hist([FbFalse_all_data[wf_id][0:size],FbTrue_all_data[wf_id]], bins=bin_ranges, histtype='bar')
            #plt.hold(True)
            counts, bins, patches = axarr[wf_id].hist([FbFalse_all_data[wf_id][0:size],FbTrue_all_data[wf_id]], bins=bin_ranges, histtype='bar')
            axarr[wf_id].grid(True)
            axarr[wf_id].tick_params(axis='y', labelsize=10)
            axarr[wf_id].tick_params(axis='x', labelsize=14)
        
        bin_centers = 0.5 * np.diff(bins) + bins[:-1]
        for i, x in zip(ind, bin_centers):           
            axarr[wf_id].annotate(labels[i], xy=(x, 0), xycoords=('data', 'axes fraction'),size=14,
                        xytext=(0, -5), textcoords='offset points', va='top', ha='center')
            
        

def plot_InstUtilisation_3D(wf):
        
    folder = 'experiment_data/lateness/'
    
    x, y = np.random.rand(2, 20) * 4
    pprint.pprint(x)
    pprint.pprint(y)
    sys.exit()
    
    FbFalse_all_data = []
    FbTrue_all_data = []
    
    for each_wf_num in NUM_WORKFLOWS:
        
        ## FB_disabled ##
        # get data
        data = []
        fname =  folder + "FbFalse_wf" +str(each_wf_num)+'_cores'+str(SimParams.NUM_NODES)+"__utilisation.txt"
        file = open(fname, 'r')
        
        data = file.readlines()
        data = [(float(x.strip())*100.0) for x in data]        
        FbFalse_all_data.append(data)
        
        ## FB_enabled ##
        # get data
        data = []
        fname =  folder + "FbTrue_wf" +str(each_wf_num)+'_cores'+str(SimParams.NUM_NODES)+"__utilisation.txt"
        file = open(fname, 'r')
        
        data = file.readlines()
        data = [(float(x.strip())*100.0) for x in data]            
        FbTrue_all_data.append(data)
                
    NUM_CORES = 9
    
    # adjust data to account for lack of data in certain percentages
    bin_ranges = [(float(x)/float(NUM_CORES-1))*100.0 for x in range(NUM_CORES+1)]
    
    nrows = len(NUM_WORKFLOWS)
    
    ind = range(10)
    labels = [("%.2f%%"%x) for x in bin_ranges]  
    #width = 0.35
    
    #fig = plt.figure(1)
    f, axarr = plt.subplots(nrows, sharex=True)
    
    #axarr[0].set_xticks(ind+width)
    axarr[0].set_xticklabels([""]*10)
        
    hist, xedges, yedges = np.histogram2d(x, y, bins=4)
    
    
    for wf_id in xrange(len(NUM_WORKFLOWS)):
        
        if(len(FbFalse_all_data[wf_id]) < len(FbTrue_all_data[wf_id])):
            size = len(FbFalse_all_data[wf_id])            
        else:
            size = len(FbTrue_all_data[wf_id])
        
        diff = [] 
        for i in xrange(size):
            diff.append(FbTrue_all_data[wf_id][i] - FbFalse_all_data[wf_id][i])
       
        #x = np.arange(0.0, float(len(diff))*SimParams.SIM_MONITOR_SAMPLE_RATE, SimParams.SIM_MONITOR_SAMPLE_RATE) 
        #x = np.arange(0.0, float(size)*SimParams.SIM_MONITOR_SAMPLE_RATE, SimParams.SIM_MONITOR_SAMPLE_RATE)
                                
        #plt.plot(x, np.cumsum(diff), 'k')
        #plt.plot(x, np.cumsum(FbTrue_all_data[wf_id][0:size]), 'r')
        #plt.subplot(nrows,1, wf_id+1)
        #plt.hist([FbFalse_all_data[wf_id][0:size],FbTrue_all_data[wf_id]], bins=bin_ranges, histtype='bar')
        #plt.hold(True)
        counts, bins, patches = axarr[wf_id].hist([FbFalse_all_data[wf_id][0:size],FbTrue_all_data[wf_id]], bins=bin_ranges, histtype='bar')
        axarr[wf_id].grid(True)
        axarr[wf_id].tick_params(axis='y', labelsize=10)
        axarr[wf_id].tick_params(axis='x', labelsize=14)
    
    bin_centers = 0.5 * np.diff(bins) + bins[:-1]
    for i, x in zip(ind, bin_centers):           
        axarr[wf_id].annotate(labels[i], xy=(x, 0), xycoords=('data', 'axes fraction'),size=14,
                    xytext=(0, -5), textcoords='offset points', va='top', ha='center')


    

# statistical significance testing
# tabular format
def FB_stat_significance_tests(fb_true, fb_false):
    
    print "stat_significance_tests"
    print "========================"
    print "Generation , Mann-whitney U (p-val) , Wilcoxon signed-rank (p-val) , Effect size , median diff , ks_val , comment"    
    
    gen = 0
    for fb_true_each_wf, fb_false_each_wf in zip(fb_true, fb_false):
        # comparing averages #
        EffectSize =  abs(np.mean(fb_true_each_wf) - np.mean(fb_false_each_wf))
        
        # test for significance #
        if(np.median(fb_true_each_wf) != np.median(fb_false_each_wf)):
            median_diff = ', -- medians diff --'
        else:
            median_diff = ", -- medians same --"
        
        MannWhitneyU_pval =  scipy.stats.mannwhitneyu(np.array(fb_true_each_wf), np.array(fb_false_each_wf))[1]
        WilcoxonSignedRank_pval = scipy.stats.wilcoxon(np.array(fb_true_each_wf), np.array(fb_false_each_wf))[1]
        ks_2samp_pval = scipy.stats.ks_2samp(np.array(fb_true_each_wf), np.array(fb_false_each_wf))[1]
        
        comment = ',  -- distributions significantly differ' if (WilcoxonSignedRank_pval<0.05) else "" +  ', -- distributions are same'
        
        print str(gen) + ",\t %.10f" %  MannWhitneyU_pval + ",\t %.10f" % WilcoxonSignedRank_pval + ",\t %.10f" % EffectSize + ",\t" + (median_diff) + "\t, %.10f"%ks_2samp_pval +comment
        gen=gen+1
        
        



(FbFalse_all_data, FbTrue_all_data) = plot_LatenessComparisons_boxplot()
#plot_LatenessComparisons_summary()
#plot_InstUtilisation(None)
#plot_InstUtilisation_3D(None)

#plot_LatenessComparisons_varyingCores()

#FB_stat_significance_tests(FbTrue_all_data, FbFalse_all_data)
#plt.show()