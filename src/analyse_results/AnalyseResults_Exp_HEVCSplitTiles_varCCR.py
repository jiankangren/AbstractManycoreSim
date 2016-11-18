#sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

## uncomment when running under CLI only version ##
#import matplotlib
#matplotlib.use('Agg')

#sys.path.append("/shared/storage/cs/staffstore/hrm506/simpy-3.0.5/")
#sys.path.append("/shared/storage/cs/staffstore/hrm506/networkx-1.10/networkx-1.10")

import sys, os, csv, pprint, math

#sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

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

import seaborn.apionly as sns
#sns.set_color_codes()


plt.style.use('bmh_rosh')

import json

#from scipy.stats import gaussian_kde



from SimParams import SimParams


SHOW_PLOTS = True
USE_MULTIPROCESSING = False

NOC_H = 6
NOC_W = 6

MAX_SEEDS = 30

               
FAILED_SEEDS = []
#RANDOM_SEEDS =[s for s in RANDOM_SEEDS if s not in FAILED_SEEDS][:MAX_SEEDS]

#RANDOM_SEEDS_MISC=[33749, 43894, 26358, 80505]
RANDOM_SEEDS_MISC=[80505]

RANDOM_SEEDS = RANDOM_SEEDS_MISC
print len(set(RANDOM_SEEDS))

#sys.exit()

EXP_DATADIR = "Z:/MCASim/experiment_data/hevc_tile_mapping_varCCR/"

DATA_TEMP_SAVE_LOC = "../experiment_data/hevc_tile_mapping_varCCR/"


CMB_ID = 903
MMP_ID = 0 

#global_mp_order = [d['lbl'] for d in global_types_of_tests]

VARIABLE_CC_SCALE_FACTORS = [0.75, 0.5, 0.25, 0.1, 0.01]

WORKLOAD_KEY = "WL2"

def _save_data(fname, data):
    final_fname = DATA_TEMP_SAVE_LOC + fname    
    logfile=open(final_fname, 'w')
    json_data = json.dumps(data)
    logfile.write(json_data)
    logfile.close()

def _load_data(fname):     
    final_fname = DATA_TEMP_SAVE_LOC + fname
    json_data=open(final_fname)
    data = json.load(json_data)      
    return data
    



def _gen_exp_key (cmb, mmp, ccs_val):
    exp_key = "ac"+str(SimParams.AC_TEST_OPTION) + \
            "mp"+str(0)+ \
            "pr"+str(0)+ \
            "cmb"+str(cmb) + \
            "mmp"+str(mmp) +\
            "ccrs"+str(str(ccs_val).replace(".",""))
              
    return exp_key

def _get_final_fname(fname, exp_key, wl_cfg, seed):
    subdir1 = EXP_DATADIR + wl_cfg + "/" + exp_key + "/"            
    subdir2 = subdir1 + "seed_"+str(seed)+"/"    
    fname_prefix = "HEVCTileSplitTest__"  + exp_key + "_" + str(NOC_H)+"_"+str(NOC_W)+"_"
    finalfname_completedtasks = subdir2 + fname_prefix + fname
    return finalfname_completedtasks


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
        box.set( color='#000000', linewidth=1)
        # change fill color
        box.set( facecolor =  param_col)
        i+=1
    
    ## change color and linewidth of the whiskers
    for whisker in bp['whiskers']:
        whisker.set(color='#000000', linewidth=1, linestyle='-')
    
    ## change color and linewidth of the caps
    for cap in bp['caps']:
        cap.set(color='#000000', linewidth=1)
    
    ## change color and linewidth of the medians
    for median in bp['medians']:
        median.set(color='#000000', linewidth=1)
    
    ## change the style of fliers and their fill
    for flier in bp['fliers']:
        flier.set(marker='x', color='red', alpha=0.5)


def plot_CommsOverhead_and_GoPLateness_Combined(load_data=False, show_plots=False):
    data_fname_datacomms = "plot_data_comms.json"
    data_fname_memcomms = "plot_mem_comms.json"
    data_fname_taskreptime = "plot_task_resptime.json"
    data_fname_gopl = "plot_gopl.json"
        
    ### get data ####    
    alldata_perseed_datacomms = OrderedDict()
    alldata_perseed_memcomms = OrderedDict()
    alldata_perseed_taskreptime = OrderedDict()
    alldata_perseed_goplateness = OrderedDict()
    
    if load_data==True:        
        alldata_perseed_datacomms = _load_data(data_fname_datacomms)
        alldata_perseed_memcomms = _load_data(data_fname_memcomms)
        alldata_perseed_taskreptime = _load_data(data_fname_taskreptime)
        alldata_perseed_goplateness = _load_data(data_fname_gopl) 
    else:    
            for each_ccsf in VARIABLE_CC_SCALE_FACTORS:
                                        
                #alldata_perseed_datacomms[each_ccsf] = None
                #alldata_perseed_memcomms[each_ccsf] = None
                #alldata_perseed_taskreptime[each_ccsf] = None
                #alldata_perseed_goplateness[each_ccsf] = None
                           
                # which exp condition ?
                exp_key = _gen_exp_key(
                                       CMB_ID,
                                       MMP_ID,
                                       each_ccsf
                                        )
                exp_lbl = each_ccsf            
                            
                each_seed_data_datacomms = []
                each_seed_data_memcomms = []
                each_seed_taskresptime = []
                each_seed_data_goplateness = []
                
                for each_seed in RANDOM_SEEDS:                
                    # get filename
                    finalfname_comms = _get_final_fname("_flwcompletedshort.js", exp_key, WORKLOAD_KEY, each_seed)
                    finalfname_gopsummary = _get_final_fname("_gopsopbuffsumm.js", exp_key, WORKLOAD_KEY, each_seed) 
                    finalfname_obuff = _get_final_fname("_obuff.js", exp_key, WORKLOAD_KEY, each_seed)
                                   
                    try:        
                        ## get flow info data
                        print "getting : ", finalfname_comms                                                
                        json_data=open(finalfname_comms)
                        file_data = json.load(json_data)                        
                        flows_data_rt_dist = [f[0]+f[1] for f in file_data['flows_completed'] if f[2] in [1,15]]
                        flows_mem_rdwr_rt_dist = [f[0]+f[1] for f in file_data['flows_completed'] if f[2] in [8,9]]
                        
                        ## get task info data
                        print "getting : ", finalfname_obuff                                                
                        json_data=open(finalfname_obuff)
                        file_data = json.load(json_data)                        
                        pb_task_et_minus_dct_dist = [t['et']-t['dct'] for t in file_data if t['type'] in ["P", "B"]]
                        i_task_et_minus_dct_dist = [t['et']-t['dt'] for t in file_data if t['type'] in ["I"]]
                        task_et_minus_dct_dist = pb_task_et_minus_dct_dist + i_task_et_minus_dct_dist
                        
                        
                        ## get gop info data
                        print "getting : ", finalfname_gopsummary                                                
                        json_data=open(finalfname_gopsummary)
                        file_data = json.load(json_data)                        
                        gop_lateness_dist = [g['gop_execution_lateness'] for gid, g in file_data.iteritems()]
                                                
                        each_seed_data_datacomms.extend(flows_data_rt_dist)
                        each_seed_data_memcomms.extend(flows_mem_rdwr_rt_dist)
                        each_seed_taskresptime.extend(task_et_minus_dct_dist)
                        each_seed_data_goplateness.extend(gop_lateness_dist)                        
                                                        
                    except Exception, e:                    
                        tb = traceback.format_exc()
                        print tb                    
                        sys.exit(e)            
                
                alldata_perseed_datacomms[str(each_ccsf)] = each_seed_data_datacomms
                alldata_perseed_memcomms[str(each_ccsf)] = each_seed_data_memcomms
                alldata_perseed_taskreptime[str(each_ccsf)] = each_seed_taskresptime
                alldata_perseed_goplateness[str(each_ccsf)] = each_seed_data_goplateness
    
    # save data
    if load_data==False:
        _save_data(data_fname_datacomms, alldata_perseed_datacomms)
        _save_data(data_fname_memcomms, alldata_perseed_memcomms)
        _save_data(data_fname_taskreptime, alldata_perseed_taskreptime)
        _save_data(data_fname_gopl, alldata_perseed_goplateness)
    
    if show_plots==False:
        return
            
    ### plot data ####
    fig, ax = plt.subplots(2, 2)
    fig.canvas.set_window_title('plot_var_ccr')    
                    
    x_data = np.arange(len(VARIABLE_CC_SCALE_FACTORS))
    x_data_lbls = ["CC\nx"+str(x) for x in VARIABLE_CC_SCALE_FACTORS]
    
        
    ydata_data_flw_rt = [alldata_perseed_datacomms[str(k)] for k  in VARIABLE_CC_SCALE_FACTORS]
    ydata_mem_flw_rt = [alldata_perseed_memcomms[str(k)] for k  in VARIABLE_CC_SCALE_FACTORS]
    ydata_task_rt = [alldata_perseed_taskreptime[str(k)] for k  in VARIABLE_CC_SCALE_FACTORS]
    ydata_gopl = [alldata_perseed_goplateness[str(k)] for k  in VARIABLE_CC_SCALE_FACTORS]
    
    #print [np.mean(y) for y in ydata_data_flw_rt]
    #print [np.mean(y) for y in ydata_mem_flw_rt]
    #print [ (np.min(y), np.max(y)) for y in ydata_mem_flw_rt]
    
    
    
    #pprint.pprint(ydata_data_flw_rt)
    
    ax[0,0].boxplot(ydata_data_flw_rt, positions=x_data)
    ax[0,0].set_ylabel('Data flow\nresponse time (s)')
    ax[0,0].set_yscale('symlog', linthreshy=0.005)
    
    ax[0,1].boxplot(ydata_mem_flw_rt, positions=x_data)
    ax[0,1].set_ylabel('Memory flow\nresponse time (s)')
    ax[0,1].set_yscale('symlog', linthreshy=0.005)
    
    ax[1,0].boxplot(ydata_task_rt, positions=x_data)
    ax[1,0].set_ylabel('Task turn\naround time (s)')
    
    ax[1,1].boxplot(ydata_gopl, positions=x_data)
    ax[1,1].set_ylabel('Job lateness (s)')
        
    for i in xrange(2):
        for j in xrange(2):        
            ax[i,j].grid(True)
            ax[i,j].set_xticks(x_data)
            ax[i,j].set_xticklabels(x_data_lbls, rotation=0)
            ax[i,j].tick_params(axis = 'y', which = 'both')            
        
    
    ax[0,0].set_xticklabels([])
    ax[0,1].set_xticklabels([])
    
    print "---"
    
    plt.tight_layout()


def _get_payload_from_flowbl(flw_bl):
    p = SimParams.NOC_PERIOD
    payload = (16.0*(flw_bl - (70.0*p*p)))/p
    return payload  



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
            

        
            
def func_fit_data(x, a, b, c):
    return a * np.exp(-b * x) + c        
        





       

###################################
#    HELPERS
###################################

          



###################################
#    MAIN
###################################
if __name__ == "__main__":
    
    plot_CommsOverhead_and_GoPLateness_Combined(load_data=True, show_plots=True)

    plt.show()



