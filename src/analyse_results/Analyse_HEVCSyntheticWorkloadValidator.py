import pprint
import sys, os
import random
import time
import math
import gc
import numpy as np
import matplotlib
matplotlib.use('Qt4Agg')
import matplotlib.pyplot as plt
plt.style.use('/home/rosh/Documents/EngD/Work/VidCodecWork/VideoProfilingData/analysis_tools/bmh_rosh.mplstyle')

import matplotlib.patches as patches
import matplotlib.patches as mpatches
from collections import OrderedDict
#from scipy.stats import rv_discrete

#from tabulate import tabulate

#import scipy.stats as ss
import itertools
import json
import csv
#from operator import itemgetter
#from collections import Counter, Sequence
#from collections import OrderedDict
import seaborn.apionly as sns
#from matplotlib.ticker import FuncFormatter
from matplotlib.ticker import ScalarFormatter

## local imports
sys.path.append('/home/rosh/Documents/EngD/Work/VidCodecWork/VideoProfilingData/analysis_tools/')
#from x265enc_analysis import _get_bframe_seq_sizes
#from x265dec_analysis import groupFramesToGoPs, _get_fr_from_gop


plt.style.use('/home/rosh/Documents/EngD/Work/VidCodecWork/VideoProfilingData/analysis_tools/bmh_rosh.mplstyle')

EXP_DATADIR = "../experiment_data/workload_validation/"
#RANDOM_SEEDS = [81665, 33749, 43894, 26358, 80505, 83660, 22817, 70263, 29917, 26044]

#RANDOM_SEEDS = [81665, 33749, 43894, 26358, 80505]



#RANDOM_SEEDS_0=[81665, 33749, 43894, 26358, 80505,
#83660, 22817, 70263, 29917, 26044,
#5558, 76891, 22250, 42198, 18065,
#74076, 98652, 21149, 50399, 64217]

RANDOM_SEEDS=[81665, 33749, 43894, 26358, 80505, 
74076, 18065, 42198, 22250, 76891  ]


REAL_VID_STREAM_ENCANALYSIS_DIR = "/home/rosh/Documents/EngD/Work/VidCodecWork/VideoProfilingData/encoder_analysis_dumps/"
REAL_VID_STREAM_DECANALYSIS_DIR = "/home/rosh/Documents/EngD/Work/VidCodecWork/VideoProfilingData/decoder_analysis_dumps/"


NUM_GOPS_PER_SEED = 20
GOP_LEN = 36
NBMAX = 4

RESOLUTION_PIX = 720*1280

########################################
# GOP comparison (synthetic vs. real)
########################################    
def plot_GoP_comparison(realvid_encanalysisdump_fname, all_gop_data):
    
    f, axarr = plt.subplots(1,3, sharex=False, sharey=False)
    f.canvas.set_window_title('plot_GoP_comparison - Documentary')
    
    #cols = sns.diverging_palette(220, 20, n=2)
    cols = ['darkviolet', 'darkorange']
    
    ############ num P frames ##    
    synthetic_data_0 = all_gop_data['numP']
    realvid_data_0 = getdata_gop_ftype_count(realvid_encanalysisdump_fname)
        
    print len(synthetic_data_0), len(realvid_data_0)
    
    both_datasets = [realvid_data_0, synthetic_data_0]
    flat_both_datasets =  list(itertools.chain(*both_datasets))
    
    d = np.diff(np.unique(flat_both_datasets)).min()
    left_of_first_bin = np.min(flat_both_datasets) - float(d)/2
    right_of_last_bin = np.max(flat_both_datasets) + float(d)/2
    
    axarr[0].hist(both_datasets, np.arange(left_of_first_bin, right_of_last_bin + d, d), 
                             alpha=1.0, normed=True, color=cols)
    
    axarr[0].set_ylabel('Normalised frequency')
    axarr[0].set_xlabel('Number of\nP-frames in GoP')
    axarr[0].tick_params(axis='both', which='major')
    
    ############ contig B-frames ##
    synthetic_data_1 = all_gop_data['contig_bframes']
    realvid_data_1 = getdata_gop_contig_bframes(realvid_encanalysisdump_fname)
        
    print len(synthetic_data_1), len(realvid_data_1)
    
    both_datasets = [realvid_data_1, synthetic_data_1]
    flat_both_datasets =  list(itertools.chain(*both_datasets))
    
    d = np.diff(np.unique(flat_both_datasets)).min()
    left_of_first_bin = np.min(flat_both_datasets) - float(d)/2
    right_of_last_bin = np.max(flat_both_datasets) + float(d)/2
    
    axarr[1].hist(both_datasets, np.arange(left_of_first_bin, right_of_last_bin + d, d), 
                             alpha=1.0, normed=True, color=cols)
    
    axarr[1].set_ylabel('Normalised frequency')
    axarr[1].set_xlabel('Number of\ncontiguous B-frames')
    axarr[1].tick_params(axis='both', which='major')
    
    xt = np.arange(1,5) 
    xt_l = [str(x) for x in xt]   
    axarr[1].set_xticklabels(xt_l)
    axarr[1].set_xticks(xt)
    
    ############ B-fr ref dist ##
    synthetic_data_2 = all_gop_data['refdist']
    realvid_data_2 = getdata_gop_reffrdist_bfr(realvid_encanalysisdump_fname)
        
    print len(synthetic_data_2), len(realvid_data_2)
    
    both_datasets = [realvid_data_2, synthetic_data_2]
    flat_both_datasets =  list(itertools.chain(*both_datasets))
    
    d = np.diff(np.unique(flat_both_datasets)).min()
    left_of_first_bin = np.min(flat_both_datasets) - float(d)/2
    right_of_last_bin = np.max(flat_both_datasets) + float(d)/2
    
    axarr[2].hist(both_datasets, np.arange(left_of_first_bin, right_of_last_bin + d, d), 
                             alpha=1.0, normed=True, color=cols)
    
    
    axarr[2].set_ylabel('Normalised frequency')
    axarr[2].set_xlabel('Reference distance\nof B-frames')
    axarr[2].tick_params(axis='both', which='major')
    xt = np.arange(1,4) 
    xt_l = [str(x) for x in xt]   
    axarr[2].set_xticklabels(xt_l)
    axarr[2].set_xticks(xt)
    
    ## set legend ##    
    rect_lbl_list = ['Real', "Synthetic"]
    rec1 = patches.Rectangle( (0.72, 0.1), 0.2, 0.6, facecolor=cols[0], alpha=1.0)
    rec2 = patches.Rectangle( (0.72, 0.1), 0.2, 0.6, facecolor=cols[1], alpha=1.0)
    rects_list = [rec1, rec2]
    leg = plt.figlegend(rects_list, rect_lbl_list, loc = 'upper center', ncol=2, labelspacing=0. , fontsize=14)
    leg.get_frame().set_facecolor('#FFFFFF')
    leg.get_frame().set_linewidth(0.0)
    
    


########################################
# CU comparison (synthetic vs. real)
########################################
def plot_CU_comparison(realvid_encanalysisdump_fname, realvid_decanalysisdump_fname, all_fr_data):
    
    print "======================================"
    print "plot_CU_comparison"
    print "======================================"
    
    cols = ['red', 'blue', 'green', '#A2769C'] # darker
    
    
    ############ CU-sizes ##
    print "Cu-sizes: "
    f, axarr = plt.subplots(2,2, sharex=False, sharey=False)
    f.canvas.set_window_title('plot_CU_comparison - Doc. - CU sizes')
    cols = sns.color_palette("colorblind", 11)[6:]
    
    synthetic_data_0 = all_fr_data['trackvalidate_prop_cu_sizes']    
    realvid_data_0 = getdata_cu_cusizes(realvid_encanalysisdump_fname)
    
    ftypes = synthetic_data_0.keys()
    
    track_mean_error = {}
    
    
    j = 0
    for each_ftype in ftypes:
        track_all_data = []
        lbls = [str(k) for k in synthetic_data_0[each_ftype].keys()]
        sizes = [k for k in synthetic_data_0[each_ftype].keys()]
        # synthetic
        i=0                
        data = [synthetic_data_0[each_ftype][k] for k in sizes]  
        np_data = np.array([float(d) for d in data])/np.sum(data)
        wedges, plt_labels, junk = axarr[i][j].pie(data, labels=lbls, autopct='%1.1f%%', colors=cols)
        track_all_data.append(np.array(np_data))        
        axarr[i][j].set_title("Synthetic - " + each_ftype)
        
        # real
        i+=1
        data = [realvid_data_0[each_ftype][k] for k in sizes]
        np_data = np.array([float(d) for d in data])/np.sum(data)                        
        wedges, plt_labels, junk = axarr[i][j].pie(data, labels=lbls, autopct='%1.1f%%', colors=cols)
        track_all_data.append(np.array(np_data))
        axarr[i][j].set_title("Real - " + each_ftype)
        
        j +=1
        
        all_err = np.abs(track_all_data[0]-track_all_data[1])
        print each_ftype, all_err, np.mean(all_err)
        track_mean_error['CU_size_'+each_ftype] = np.mean(all_err)
        
    
    
    ############ CU-types ##
    print "Cu-types: "    
    f, axarr = plt.subplots(2,2, sharex=False, sharey=False)
    f.canvas.set_window_title('plot_CU_comparison - Doc. - CU type')
    cols = sns.color_palette("colorblind", 11)[6:]
    
    synthetic_data_0 = all_fr_data['trackvalidate_prop_cu_types']    
    realvid_data_0 = getdata_cu_cutypes(realvid_decanalysisdump_fname)
    
    ftypes = synthetic_data_0.keys()
    
    j = 0
    for each_ftype in ["P", "B"]:
        track_all_data = []
        lbls = [str(k) for k in realvid_data_0[each_ftype+"-SLICE"].keys()]
        types = [k for k in realvid_data_0[each_ftype+"-SLICE"].keys()]
        
        # synthetic
        i=0                
        data = [synthetic_data_0[each_ftype][k.replace("_", "")] for k in types]        
        np_data = np.array([float(d) for d in data])/np.sum(data)
        track_all_data.append(np.array(np_data))
        wedges, plt_labels, junk = axarr[i][j].pie(data, labels=lbls, autopct='%1.1f%%', colors=cols)        
        axarr[i][j].set_title("Synthetic - " + each_ftype)
        
        # real
        i+=1
        data = [realvid_data_0[each_ftype+"-SLICE"][k] for k in types]    
        np_data = np.array([float(d) for d in data])/np.sum(data)    
        track_all_data.append(np.array(np_data))
        wedges, plt_labels, junk = axarr[i][j].pie(data, labels=lbls, autopct='%1.1f%%', colors=cols)
        axarr[i][j].set_title("Real - " + each_ftype)
        
        j +=1
        
        all_err = np.abs(track_all_data[0]-track_all_data[1])
        print each_ftype, all_err, np.mean(all_err)
        track_mean_error['CU_type_'+each_ftype] = np.mean(all_err)
        
        
    
            
    ############ CU-decoding time ##    
    f, axarr = plt.subplots(2,4, sharex=True, sharey=False)
    f.canvas.set_window_title('plot_CU_comparison - Doc. - CU dec. time')    
    cols = ['r', 'g', 'b', 'k']
    
    synthetic_data_0 = all_fr_data['trackvalidate_cu_dectime']    
    realvid_data_0 = _get_cucc_data(realvid_decanalysisdump_fname)
    
    j = 0
    for each_cutype in ["ICU_cc", "PCU_cc", "BCU_cc", "SkipCU_cc"]:        
        # synthetic
        i=0                
        data = synthetic_data_0[each_cutype]
        axarr[0][j].hist(data, bins=100, histtype='step', fill=False, alpha=1.0, linewidth=1.5, normed=True, color=cols[j])
        axarr[0][j].set_title("Synthetic - " + each_cutype)
        
        # real
        i+=1
        data = realvid_data_0[each_cutype]
        axarr[1][j].hist(data, bins=100, histtype='step', fill=False, alpha=1.0, linewidth=1.5, normed=True, color=cols[j])
        axarr[1][j].set_title("Real - " + each_cutype)
        
        j +=1
        
        


########################################
# Frame comparison (synthetic vs. real)
########################################
def plot_Frame_comparison(realvid_encanalysisdump_fname, realvid_decanalysisdump_fname, all_fr_data):    
    print "plot_Frame_comparison - decoding time"
    
    plt_dect = True
    plt_refdata = True
    plt_encsize = False
    
    ############ Fr decoding time ##
    xfmt = ScalarFormatter(useMathText=True)
    xfmt.set_powerlimits((-3,-1))
    if plt_dect == True:
        f, axarr = plt.subplots(1,2, sharex=False, sharey=False)
        f.canvas.set_window_title('plot_Frame_comparison - Documentary - decoding time')
        
        cols = ['red', 'green', 'blue']   
        ftypes = ["I", "P", "B"]
            
        synthetic_data_0 = all_fr_data['trackvalidate_frdectime']    
        realvid_data_0 = getdata_fr_dect(realvid_decanalysisdump_fname)
        
        bin_n = 50
        
        for ix1, each_frtype in enumerate(ftypes):
            synth_data = synthetic_data_0[each_frtype]
            realvid_data = realvid_data_0[each_frtype] 
             
            print len(synth_data), len(realvid_data)
                   
            #z_ord=100*(ix+1)
            #axarr[0].hist(realvid_data, bins=bin_n, histtype='step', fill=False, linewidth=3.0, color=cols[ix1], normed=True, alpha=0.3)
            #z_ord+=1
            axarr[0].hist(synth_data, bins=bin_n, histtype='step', fill=False, linewidth=1.5, color=cols[ix1],  normed=True, alpha=1.0) 
            
        red_patch = mpatches.Patch(color='red', label='I-frame')
        green_patch = mpatches.Patch(color='green', label='P-frame')
        blue_patch = mpatches.Patch(color='blue', label='B-frame')   
        leg_lbls = ["I-frame", "P-frame", "B-frame"]     
        l = axarr[0].legend(handles=[red_patch, green_patch, blue_patch], fontsize=14, frameon=True, fancybox=True)
        l.draggable()

        axarr[0].set_ylabel('Normalised frequency')
        axarr[0].set_xlabel('Frame decoding time (s)')                
        axarr[0].xaxis.set_major_formatter(FixedOrderFormatter(-2))
        axarr[0].tick_params(axis='both', which='major')
        #axarr[0].xaxis.get_offset_text().set_size(16)      
        
    
    ############ Ref fr data distibution ##
    if plt_refdata == True:
        print "plot_Frame_comparison - reference data"
        
        #f2, axarr2 = plt.subplots(1,1)
        #f2.canvas.set_window_title('plot_Frame_comparison - Documentary - reference data')
        
        #cols = sns.color_palette("colorblind", 3)
        cols = ['darkviolet', 'darkorange']
        
        synthetic_data_0 =  all_fr_data['trackvalidate_reffrdata']
        realvid_data_0 = getdata_fr_refdata(realvid_decanalysisdump_fname)
        
        rf_types = ["P<-I", "P<-P", "B<-I", "B<-P", "B<-B"]
        width=0.3
        gap = 0.05
        ind = np.arange(len(rf_types))
        
        for ix2, dataset in enumerate([realvid_data_0, synthetic_data_0]):
            ydata = [dataset[t] for t in rf_types]
            xdata = ind+((width+gap)*ix2)
            bps = axarr[1].boxplot(ydata,0,  positions=xdata, widths=width, patch_artist=True, sym='', whis=[5, 95])
            boxplot_colorize(bps, param_col = cols[ix2])
        
        axarr[1].set_xticklabels(rf_types)
        axarr[1].set_xticks(ind+(width/2.0)+(gap/2.0))
        axarr[1].set_ylabel('Frame reference data (KB)')
        axarr[1].set_xlabel('Reference data direction')
        axarr[1].tick_params(axis='both', which='major')
            
        ## set legend ##    
#         rect_lbl_list = ['Real', "Synthetic"]
#         rec1 = patches.Rectangle( (0.72, 0.1), 0.2, 0.6, facecolor=cols[0], alpha=1.0)
#         rec2 = patches.Rectangle( (0.72, 0.1), 0.2, 0.6, facecolor=cols[1], alpha=1.0)
#         rects_list = [rec1, rec2]
#         leg = plt.figlegend( rects_list, rect_lbl_list, loc = 'upper center', ncol=5, labelspacing=0. , fontsize=11, )
#         leg.draggable()

        real_patch = mpatches.Patch(color=cols[0], label='Real')
        synth_patch = mpatches.Patch(color=cols[1], label='Synthetic')        
        leg_lbls = ['Real', "Synthetic"]     
        l = axarr[1].legend(handles=[real_patch, synth_patch], fontsize=14, frameon=True, fancybox=True)
        l.draggable()
        axarr[1].tick_params(axis='both', which='major')
        
        axarr[1].xaxis.grid(False)
        axarr[1].yaxis.grid(True)
    
    ############ Encoded fr size distibution ##
    if plt_encsize ==True:
        print "plot_Frame_comparison - encoded fr size dist"
         
        #f3, axarr3 = plt.subplots(1,3)
        #f3.canvas.set_window_title('plot_Frame_comparison - Documentary - encoded fr size')     
        cols = ['red', 'green', 'blue', '#A2769C']
         
        synthetic_data_0 =  all_fr_data['trackvalidate_frencsize']
        realvid_data_0 = getdata_fr_encsize(realvid_encanalysisdump_fname)
         
        stypes = ["I", "P", "B"]
    
        for ix, each_s in enumerate(stypes):
            axarr[2].hist(realvid_data_0[each_s], bins=50, histtype='step', fill=False, linewidth=3.0, color=cols[ix], normed=True, alpha=0.3)
            #z_ord+=1
            axarr[2].hist(synthetic_data_0[each_s], bins=50, histtype='step', fill=False, linewidth=2.0, color=cols[ix],  normed=True, alpha=1.0)
                 
    
    
    plt.tight_layout()
     
    
#################################################
# Helpers - get data from real vid streams
#################################################

def getdata_gop_ftype_count(fname, ftype_count='P_slice_count'):
    f = open(fname)
    jdata = json.load(f)    
    p_fr_count = np.array(jdata[ftype_count])
    return p_fr_count

def getdata_gop_contig_bframes(fname):
    f = open(fname)
    jdata = json.load(f)    
    gop_seqs = jdata['gop_sequences']
    #result = np.array(x265enc_analysis._get_bframe_seq_sizes(gop_seqs))
    result = np.array(_get_bframe_seq_sizes(gop_seqs))
    return result

def getdata_gop_reffrdist_bfr(fname):
    f = open(fname)
    jdata = json.load(f)
    ref_distances = jdata['ref_fr_distances']['RD_B_fr']        
    result = np.array(ref_distances)
    return result

def getdata_fr_dect(fname):
    f = open(fname)
    jdata = json.load(f)
    result = {"I":[], "P":[], "B":[]}
    
    #pprint.pprint(len(jdata))
    #pprint.pprint(jdata.keys())
    
    for each_fr in jdata:
        #print each_fr.keys()
        if "I-" in each_fr['slice_t']:
            result["I"].append(each_fr['fr_dec_t'])
        elif "P-" in each_fr['slice_t']:
            result["P"].append(each_fr['fr_dec_t'])
        elif "B-" in each_fr['slice_t']:
            result["B"].append(each_fr['fr_dec_t'])
    return result
            

def getdata_fr_refdata(fname):
    f = open(fname)
    jdata = json.load(f)    
    frames_as_gops = groupFramesToGoPs(jdata)    
    result = {"P<-I" : [], "P<-P" : [], "B<-I" : [],"B<-P" : [],"B<-B" : []}
    
    #gather data
    for each_gop in frames_as_gops:
        for each_fr in each_gop:                         
            for each_rf_poc, fr_data_vol in each_fr['ref_fr_data'].iteritems():                  
                rf_frame = _get_fr_from_gop(each_gop, int(each_rf_poc))                        
                rf_frame_type = rf_frame['slice_t'] 
                                
                if "P-" in each_fr['slice_t']:
                    if "I-" in rf_frame_type:
                        result["P<-I"].append(int(float(fr_data_vol)/1024.0))
                    elif "P-" in rf_frame_type:
                        result["P<-P"].append(int(float(fr_data_vol)/1024.0))                        
                    else:
                        sys.exit("Error - P")
                
                if "B-" in each_fr['slice_t']:
                    if "I-" in rf_frame_type:
                        result["B<-I"].append(int(float(fr_data_vol)/1024.0))
                    elif "P-" in rf_frame_type:
                        result["B<-P"].append(int(float(fr_data_vol)/1024.0))                        
                    elif "B-" in rf_frame_type:
                        result["B<-B"].append(int(float(fr_data_vol)/1024.0))
                    else:
                        sys.exit("Error - B")            
    return result
             



def getdata_fr_encsize(fname):    
    f = open(fname)
    jdata = json.load(f)    
    slice_level_data = jdata    
    result = {"I" : [], "P" : [], "B" : []}
    
    for each_slice_type in ["I", "P", "B"]:
        each_stype_encsize_k = each_slice_type + "_slice_size"     
        data_orig = np.array(slice_level_data[each_stype_encsize_k])    
        fr_size_as_ratio_of_totalsize = [(float(d)/float(RESOLUTION_PIX*24)) for d in data_orig]
        result[each_slice_type] = fr_size_as_ratio_of_totalsize
    
    return result
        
    
    




def getdata_cu_cutypes(fname):
    f = open(fname)
    jdata = json.load(f)
       
    slicelevel_cutype_bytes = OrderedDict()    
    slice_types = ['P-SLICE', 'B-SLICE']
    cu_types = ['I_CU', 'P_CU', 'B_CU', 'Skip_CU']
    # get data per slice, per cu
    for each_stype in slice_types:
        slicelevel_cutype_bytes[each_stype] = OrderedDict()                
        for each_cu_type in cu_types:            
            val =  np.mean([fr['cu_bytes'][each_cu_type] for fr in jdata if fr['slice_t'] == each_stype])/1024.0            
            slicelevel_cutype_bytes[each_stype][each_cu_type] = val
    
    return slicelevel_cutype_bytes


def getdata_cu_cusizes(fname):
    f = open(fname)
    jdata = json.load(f)       
    slice_types = ['I_slice_blocksize_dist', 'P_slice_blocksize_dist', 'B_slice_blocksize_dist', 'b_slice_blocksize_dist']    
    result = {
              'intra': {4:[], 8:[], 16:[],32:[],64:[]},
              'inter': {4:[], 8:[], 16:[],32:[],64:[]}              
              }
    
    for each_stype in slice_types:
        if each_stype in ['I_slice_blocksize_dist']: #intra
            for each_size, data in jdata[each_stype].iteritems():
                size_k = int(each_size.split("x")[0])
                result['intra'][size_k].extend(data)
                
        elif each_stype in ['P_slice_blocksize_dist', 'B_slice_blocksize_dist', 'b_slice_blocksize_dist']: # inter
            for each_size, data in jdata[each_stype].iteritems():
                size_k = int(each_size.split("x")[0])
                result['inter'][size_k].extend(data)
    
    # get the mean of all the data
    for each_ft in result.keys():
        for each_s, data in result[each_ft].iteritems():
            result[each_ft][each_s] = np.mean(data)
    
    return result


def _get_cucc_data(fname):
    f = open(fname)
    cu_data = json.load(f)
        
    I_cu_cc_hist =  [fr['cu_dec_t']['I_CU'][0] for fr in cu_data if fr['cu_dec_t']['I_CU'][0] !=-1]    
    P_cu_cc_hist =  [fr['cu_dec_t']['P_CU'][0] for fr in cu_data if fr['cu_dec_t']['P_CU'][0] !=-1]
    B_cu_cc_hist =  [fr['cu_dec_t']['B_CU'][0] for fr in cu_data if fr['cu_dec_t']['B_CU'][0] !=-1]
    Skip_cu_cc_hist =  [fr['cu_dec_t']['Skip_CU'][0] for fr in cu_data if fr['cu_dec_t']['Skip_CU'][0] !=-1]        
    
    flat_I_cu_cc_hist = I_cu_cc_hist
    flat_P_cu_cc_hist = P_cu_cc_hist
    flat_B_cu_cc_hist = B_cu_cc_hist
    flat_Skip_cu_cc_hist = Skip_cu_cc_hist
    
#     cu_types_list = [
#                      # sqroot defined num bins
# #                       ["I_cu_cc", flat_I_cu_cc_hist, int(np.sqrt(len(flat_I_cu_cc_hist))) ],
# #                       ["P_cu_cc", flat_P_cu_cc_hist, int(np.sqrt(len(flat_P_cu_cc_hist))) ],
# #                       ["B_cu_cc", flat_B_cu_cc_hist, int(np.sqrt(len(flat_B_cu_cc_hist))) ],
# #                       ["Skip_cu_cc", flat_Skip_cu_cc_hist, int(np.sqrt(len(flat_Skip_cu_cc_hist))) ],
#                                           
#                      # uniform bins
#                     ["I_cu_cc", flat_I_cu_cc_hist, 3000 ],
#                     ["P_cu_cc", flat_P_cu_cc_hist, 3000 ],
#                     ["B_cu_cc", flat_B_cu_cc_hist, 3000 ],
#                     ["Skip_cu_cc", flat_Skip_cu_cc_hist, 2000 ],
#                                                                
#                      ]
#     
    result = {
              "ICU_cc" : flat_I_cu_cc_hist,
              "PCU_cc" : flat_P_cu_cc_hist,
              "BCU_cc" : flat_B_cu_cc_hist,
              "SkipCU_cc" : flat_Skip_cu_cc_hist,              
              }
    
    return result



#######################################################
# Helpers - concat all data from all seeds (synthetic)
#######################################################
def _get_fname(seed, num_gops, gop_len, nbmax):
    fname_prefix = "__s%d_G%d_N%d_B%d" %(seed, num_gops, gop_len, nbmax)
    gop_data_fname = EXP_DATADIR + "gop_data_seed" + fname_prefix + "_.js"
    frame_data_fname = EXP_DATADIR + "frame_data_seed" + fname_prefix + "_.js"    
    return (gop_data_fname, frame_data_fname)

def get_all_seed_gopdata(seeds, num_gops, gop_len, nbmax):
    all_gopdata = {
                    'contig_bframes' : [],
                    'numP' : [],
                    'numB' : [],
                    'refdist' : []
                   }
    
    for each_s in seeds:
        (gop_data_fname, fr_data_fname) = _get_fname(each_s, num_gops, gop_len, nbmax)
        f = open(gop_data_fname)
        jdata = json.load(f)
        p_fr_cnt = jdata['numP']
        b_fr_cnt = jdata['numB']
        contig_b_fr = jdata['contig_bframes']
        rf_fr_dist = jdata['refdist']
        
        all_gopdata['numP'].extend(p_fr_cnt)
        all_gopdata['numB'].extend(b_fr_cnt)
        all_gopdata['contig_bframes'].extend(contig_b_fr)
        all_gopdata['refdist'].extend(rf_fr_dist)
        
    return all_gopdata


def get_all_seed_frdata(seeds, num_gops, gop_len, nbmax):
    all_frame_data = {
                      'trackvalidate_prop_cu_sizes' : {
                                                       "intra" : {64:0, 32:0, 16:0, 8:0, 4:0}, 
                                                       "inter" : {64:0, 32:0, 16:0, 8:0, 4:0}
                                                      },
                                                       
                      'trackvalidate_prop_cu_types' : {
                                                       "I" : {"ICU":0, "PCU":0, "BCU":0, "SkipCU":0},
                                                       "P" : {"ICU":0, "PCU":0, "BCU":0, "SkipCU":0},
                                                       "B" : {"ICU":0, "PCU":0, "BCU":0, "SkipCU":0},
                                                       },
                      
                      'trackvalidate_cu_dectime' : {"ICU_cc":[], "PCU_cc":[], "BCU_cc":[], "SkipCU_cc":[]},
                      'trackvalidate_reffrdata' : {"P<-I" : [], "P<-P" : [], "B<-I" : [],"B<-P" : [],"B<-B" : []},                      
                      'trackvalidate_frdectime' : {"I" : [], "P" : [], "B" : []},                                             
                      'trackvalidate_frencsize' : {"I" : [], "P" : [], "B" : []}                      
                      }
    
    for each_s in seeds:
        (gop_data_fname, fr_data_fname) = _get_fname(each_s, num_gops, gop_len, nbmax)
        f = open(fr_data_fname)
        jdata = json.load(f)        
        
        # cu sizes
        for k in all_frame_data['trackvalidate_prop_cu_sizes']['intra'].keys():
            all_frame_data['trackvalidate_prop_cu_sizes']['intra'][k] += jdata['trackvalidate_prop_cu_sizes']['intra'][str(k)]
        for k in all_frame_data['trackvalidate_prop_cu_sizes']['inter'].keys():            
            all_frame_data['trackvalidate_prop_cu_sizes']['inter'][k] += jdata['trackvalidate_prop_cu_sizes']['inter'][str(k)]
        
        # cu types
        for frtype in all_frame_data['trackvalidate_prop_cu_types'].keys():
            for cutype in all_frame_data['trackvalidate_prop_cu_types'][frtype].keys():
                all_frame_data['trackvalidate_prop_cu_types'][frtype][cutype] += jdata['trackvalidate_prop_cu_types'][frtype][cutype]
        
        # cu dec time
        for frtype_cc in all_frame_data['trackvalidate_cu_dectime'].keys():
            all_frame_data['trackvalidate_cu_dectime'][frtype_cc].extend(jdata['trackvalidate_cu_dectime'][frtype_cc])
        
        # ref fr data
        for rffrdir in all_frame_data['trackvalidate_reffrdata'].keys():
            all_frame_data['trackvalidate_reffrdata'][rffrdir].extend([int(float(i)/float(1024)) for i in 
                                                                       jdata['trackvalidate_reffrdata'][rffrdir]])
        
        # fr dec time + fr enc size
        for frtype in all_frame_data['trackvalidate_frdectime'].keys():
            all_frame_data['trackvalidate_frdectime'][frtype].extend(jdata['trackvalidate_frdectime'][frtype])
            all_frame_data['trackvalidate_frencsize'][frtype].extend([float(x)/float(RESOLUTION_PIX*3)
                                                                     for x in jdata['trackvalidate_frencsize'][frtype]])
        
    return all_frame_data


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


def boxplot_colorize(bp, param_col, fc='#B8DCE6'):    
    i=0
    ## change outline color, fill color and linewidth of the boxes
    for box in bp['boxes']:
        # change outline color
        box.set( color=param_col, linewidth=2)
        # change fill color
        box.set( facecolor =  '#ffffff')
        i+=1
    
    ## change color and linewidth of the whiskers
    for whisker in bp['whiskers']:
        whisker.set(color=param_col, linewidth=1, linestyle='-')
    
    ## change color and linewidth of the caps
    for cap in bp['caps']:
        cap.set(color=param_col, linewidth=1)
    
    ## change color and linewidth of the medians
    for median in bp['medians']:
        median.set(color=param_col, linewidth=1)
    
    ## change the style of fliers and their fill
    for flier in bp['fliers']:
        flier.set(marker='x', color=param_col, alpha=0.5)



def _get_bframe_seq_sizes(gop_seqs):    
    bfr_seqs = []
    for each_gop in gop_seqs:
        #rem Iframe
        splited_gop = each_gop[1:].split("P")
        for each_sp_gop in splited_gop:
            if len(each_sp_gop) > 0:
                bfr_seqs.append(len(each_sp_gop))
    return bfr_seqs

def groupFramesToGoPs(vid_frames):
    # create gops - put frames into groups
    gop_frame_groups = []
    temp_gop_frame_groups = []
    
    # group frames into gops
    for each_frame in vid_frames:        
        if each_frame['poc'] == 0: # key-frame detected            
            if len(temp_gop_frame_groups) > 0: # prev gop ended
                gop_frame_groups.append(temp_gop_frame_groups)
                temp_gop_frame_groups = [] # reset
                temp_gop_frame_groups.append(each_frame)
            else: # first gop
                temp_gop_frame_groups.append(each_frame)        
        else: # normal frame in gop
            temp_gop_frame_groups.append(each_frame)
    
    return gop_frame_groups

def _get_fr_from_gop(gop_frames, fr_poc):
    for each_fr in gop_frames:
        if each_fr['poc']==fr_poc:
            return each_fr
    return None






class FixedOrderFormatter(ScalarFormatter):
    """Formats axis ticks using scientific notation with a constant order of 
    magnitude"""
    def __init__(self, order_of_mag=0, useOffset=True, useMathText=False):
        self._order_of_mag = order_of_mag
        ScalarFormatter.__init__(self, useOffset=useOffset, 
                                 useMathText=useMathText)
    def _set_orderOfMagnitude(self, range):
        """Over-riding this to avoid having orderOfMagnitude reset elsewhere"""
        self.orderOfMagnitude = self._order_of_mag
        
#################################################
# MAIN - start the generation and validation
#################################################
print "hello"

fname_realvid_encanalysis_dump = REAL_VID_STREAM_ENCANALYSIS_DIR + "encanalsysis_dump_LionWildlifeDocumentary_720p_extracted.json"
fname_realvid_decanalysis_dump = REAL_VID_STREAM_DECANALYSIS_DIR + "decanalsysis_dump_LionWildlifeDocumentary_720p_extracted.json"

all_synth_gop_data = get_all_seed_gopdata(RANDOM_SEEDS, NUM_GOPS_PER_SEED, GOP_LEN, NBMAX)
all_synth_fr_data = get_all_seed_frdata(RANDOM_SEEDS, NUM_GOPS_PER_SEED, GOP_LEN, NBMAX)

# plot
#plot_GoP_comparison(fname_realvid_encanalysis_dump, all_synth_gop_data)

#plot_CU_comparison(fname_realvid_encanalysis_dump, fname_realvid_decanalysis_dump, all_synth_fr_data)


#plot_Frame_comparison(fname_realvid_encanalysis_dump, fname_realvid_decanalysis_dump, all_synth_fr_data)



plt.show()

