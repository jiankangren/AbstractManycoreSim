import sys, os, csv, pprint, math
import argparse
import socket
import random
import shutil
import time
import subprocess
import itertools
import multiprocessing
import json
from util_scripts.psbased_remapping_random_params_generation import generate_random_params
from analyse_results.AnalyseResults_Exp_RemappingBasic import generate_exp_results_summary

# name the report filenames
tm_fname                = "test__timeline.png"
vs_bs_fname             = "test__vsbs.js"
util_fname              = "test__util.js"
wf_res_fname            = "test__wfressumm.js"
gops_opbuff_fname       = "test__gopsopbuffsumm.js"
gops_opbuff_short_fname = "test__gopsopbuffsummshort.js"
rmtbl_dt_fname          = "test__rmtbldt.js"
ibuff_fname             = "test__ibuff.js"
obuff_fname             = "test__obuff.js"
obuff_short_fname       = "test__obuffshort.js"
nodetqs_fname           = "test__nodetqs.js"
rmtaskrelease_fname     = "test__rmtaskrel.js"
mappingandpriass_fname  = "test__mappingandpriass.js"
flowscompleted_fname    = "test__flwcompleted.js"
nodetaskexectime_fname  = "test__nodetaskexectime.js" 
psalgo_nodeprops        = "test__psalgonodeprops.js"
flowsadded_fname        = "test__flwsadded.js"
trminfo_fname           = "test__taskremappinginfo.js"
nodecumslack_fname      = "test__nodecumslack.js"
node_importedtasks      = "test__nodeimportedtasks.js"

RANDOM_SEEDS_LIST= \
[81665, 33749, 43894, 53784, 26358, \
80505, 83660, 22817, 70263, 29917, \
26044, 6878, 66093, 69541, 5558, \
76891, 22250, 69433, 42198, 18065, \
74076, 98652, 21149, 50399, 64217, \
44117, 57824, 42267, 83200, 99108, \
95928, 53864, 44289, 77379, 80521, \
88117, 23327, 73337, 94064, 31982]


# remapping on full fact params test
def runSim_RemappingMCParamsTestMain(param_gen_seed=1234):
         
    ##########################
    # PSBased remapping - OFF
    ##########################
    rmoff_jobs = []
    for each_seed in RANDOM_SEEDS_LIST:
        p = multiprocessing.Process(target=rmoff_jobs_process, args=(each_seed, ))
        rmoff_jobs.append(p)
    
    # start the processes
    for p in rmoff_jobs:
        p.start()
        
    # exit the completed processes
    for p in rmoff_jobs:
        p.join()
    
    ##########################
    # PSBased remapping - ON
    ##########################    
    
    # get randomly generated params
    runtime_mins = 5760
    pregenerated_random_params = generate_random_params(max_rumtime_mins=runtime_mins , param_seed=param_gen_seed)
    
    # get domain name
    domain_name = socket.getfqdn()
    
    for each_seed in RANDOM_SEEDS_LIST:
        
        # setup some processes
        rmon_jobs = []
        for each_entry_key, each_entry_value  in pregenerated_random_params.iteritems():
            p = multiprocessing.Process(target=rmon_jobs_process, args=(each_entry_value, each_seed, ))
            rmon_jobs.append(p)
            
        # start the processes
        for p in rmon_jobs:
            p.start()
        
        # exit the completed processes
        for p in rmon_jobs:
            p.join()


def rmoff_jobs_process(seed):
    stdout_fname = "logs/rmoff_jobs_process_s" + str(seed) + ".out"
    sys.stdout = open(stdout_fname, "w")
    print "_rmoff_jobs_process:: SEED === " + str(seed)
    subprocess.call(
                    'python -u RunSim_Exp_PSBasedRemapping_MCTest.py ' + \
                    " --exp_type=RMOFF" + \
                    " --forced_seed=" + str(seed) ,shell=True, stdout=sys.stdout)


def rmon_jobs_process(each_entry_value, seed):
    
    fname_param = each_entry_value['fname_param_prefix']
    
    stdout_fname = "logs/rmon_jobs_process_s" + str(seed) + \
                    "_" + fname_param + ".out"                    
    sys.stdout = open(stdout_fname, "w")
    
    print "_rmon_jobs_process:: SEED === " + str(seed)
    each_param_entry = each_entry_value["params"]        
    cmd = 'python -u RunSim_Exp_PSBasedRemapping_MCTest.py ' + \
                        " --exp_type=RMON" + \
                        " --forced_seed=" + str(seed) + \
                        " --tqn=" + str(each_param_entry["rand_TQN"]) + \
                        " --hqn=" + str(each_param_entry["rand_HQN"]) + \
                        " --tdecay=" + str(each_param_entry["rand_TDECAY"]) + \
                        " --thresholdqn=" + str(each_param_entry["rand_THRESHOLDQN"])  + \
                        " --thresholdhc=" + str(each_param_entry["rand_THRESHOLDHOPCOUNT"])  + \
                        " --thresholdqn_r_i=" + str(each_param_entry["rand_THRESHOLDQN_RAT_INCREASE"])  + \
                        " --thresholdqn_r_d=" + str(each_param_entry["rand_THRESHOLDQN_RAT_DECREASE"])  + \
                        " --khopdec=" + str(each_param_entry["rand_KHOPDECAY"])  + \
                        " --ktimedec=" + str(each_param_entry["rand_KTIMEDECAY"]) + \
                        " --remap_p=" + str(each_param_entry["rand_REMAP_PERIOD"]) + \
                        " --fname_param=" + fname_param
                        
    print cmd
    try:
        subprocess.call(cmd , shell=True, stdout=sys.stdout)
    except Exception as e: # catch exceptions to avoid exiting the thread prematurely 
        print cmd + ' - failed!'
        pprint.pprint(e)  
        
    EXP_DATA_DIR = "experiment_data/remapping_psbased_montecarlo/"
    exp_dir = EXP_DATA_DIR + "seed_" + str(seed) + "/"
    exp_params = each_entry_value["fname_param_prefix"]
    
    # perform analysis, and output summary
    print "---- performing analysis ----"
    results_summary = generate_exp_results_summary(exp_dir, exp_params)
    
    if("GOP_Error" not in results_summary["result_gopl"]):        
        fname_results_summary = exp_dir + "RMON_" + exp_params + "_resultssummary.js"        
        _write_formatted_file(fname_results_summary, results_summary, "json")
        
        # compress data files       
        print "---- compressing data files ----"
        fname_prefix = exp_dir + "RMON_" + exp_params        
        output_zipfile_fname = exp_dir + "RMON_" + exp_params + "_originaldata.zip"
        
        target_file_list = [
                        fname_prefix+"_"+wf_res_fname, 
                        fname_prefix+"_"+gops_opbuff_short_fname,
                        fname_prefix+"_"+obuff_short_fname,
                        fname_prefix+"_"+trminfo_fname,                    
                        ]
        
        _compress_files(target_file_list, output_zipfile_fname)
    else:
        xx=1 # do nothing
        print "rmon_jobs_process :: Nothing to do, exiting.."



##########################
# Helper functions
########################## 
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
            
def _makeDir(directory):
    try:
        os.stat(directory)
    except:
        os.makedirs(directory)

def _check_file_exists(fname):
    return os.path.exists(fname)

def _remove_file(fname):
    try:
        os.remove(fname)
    except:
        print "_remove_file: Error : failed to remove file : " + fname

def _compress_files(target_file_list, output_zipfile):
    target_files = ' '.join(target_file_list)
    cmd = "zip -m " + output_zipfile + " " + target_files
    print cmd
    try:        
        subprocess.call(cmd ,shell=True)
    except Exception, e:
        print "_compress_files: Error : failed to compress files : " + target_files
        print str(e)
    
    return None




    


############################################################################
############################################################################
##                MAIN SCRIPT SECTION
############################################################################
############################################################################
sys.setrecursionlimit(1500)

# collect command line params
parser = argparse.ArgumentParser(__file__, description="MC test main")
parser.add_argument("--forced_seed", help="experiment - seed", type=int, default=-1)
parser.add_argument("--param_gen_seed", help="parameter generator - seed", type=int, default=-1)

args = parser.parse_args()

####################################
## check which experiment to run ##
####################################
runSim_RemappingMCParamsTestMain()


