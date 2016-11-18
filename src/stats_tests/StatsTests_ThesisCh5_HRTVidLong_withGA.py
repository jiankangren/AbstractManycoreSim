import sys, os, csv, pprint, math

from collections import OrderedDict
import numpy as np
import random
import shutil
import math
import scipy.stats
import itertools
from itertools import cycle # for automatic markers
import json
from operator import itemgetter



FNAME_DATA_OUT_ADMINRATES = "../experiment_data/hrt_video/HRTVIDLong_data_090616/data_Load_vs_VSInfo.js"
FNAME_DATA_OUT_PEUTIL = "../experiment_data/hrt_video/HRTVIDLong_data_090616/data_Load_vs_OverallSysUtil.js"
FNAME_DATA_OUT_NOCUTIL = "../experiment_data/hrt_video/HRTVIDLong_data_090616/data_Load_vs_OverallNoCUtil.js"
FNAME_DATA_OUT_ADMINLOAD = "../experiment_data/hrt_video/HRTVIDLong_data_090616/data_Load_vs_AdmittedLoad.js"


###################################################################################################
#    data collection
###################################################################################################
# we only check the 
def report_adminrate_significance(mp_type1, mp_type2):
    vs_bs_fname = FNAME_DATA_OUT_ADMINRATES 
    json_data=open(vs_bs_fname)
    file_data = json.load(json_data)
    
    # mptype-1
    mp1_admin_rates_per_cc = OrderedDict()
    for each_cc_vals in file_data[mp_type1]:
        mp1_admin_rates_per_cc[each_cc_vals["cc"]] = each_cc_vals["admitted_ratio_allseeds"]
    
    # mptype-2
    mp2_admin_rates_per_cc = OrderedDict()
    for each_cc_vals in file_data[mp_type2]:
        mp2_admin_rates_per_cc[each_cc_vals["cc"]] = each_cc_vals["admitted_ratio_allseeds"]
    
    
    all_cx_vals = mp1_admin_rates_per_cc.keys()
    
    print "CC, Mann-whitney-pval, Wilcoxon-SignedRank-pval"
    for each_cc in all_cx_vals:
        dist1 = mp1_admin_rates_per_cc[each_cc]
        dist2 = mp2_admin_rates_per_cc[each_cc]
        
        if set(dist1) == set(dist2):
            mw_p = "identical dists"
            wsr_p = "identical dists"
        else:
        
            # get mann-whitney stat
            mw_p =  report_mannwhitneyU_test(dist1, dist2)[1]
            
            # get wilcoxon-signed-rank stat
            wsr_p = report_wilcoxonsignedrank_test(dist1, dist2)[1]
            
        #print each_cc, len(dist1), len(dist2), mw_p, wsr_p
        print each_cc, mw_p, wsr_p
    
    
###################################################################################################
#    stats tests
###################################################################################################
def report_mannwhitneyU_test(dist1, dist2):    
    statistic, pvalue = scipy.stats.mannwhitneyu(dist1, dist2)    
    return (statistic, pvalue)


def report_wilcoxonsignedrank_test(dist1, dist2):    
    statistic, pvalue = scipy.stats.wilcoxon(dist1, dist2)    
    return (statistic, pvalue)



###################################
#    HELPERS
###################################





###################################
#    MAIN
###################################

report_adminrate_significance("IPC", "GA-MP")


print "finished"


