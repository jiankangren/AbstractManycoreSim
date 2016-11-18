import sys, os, csv, pprint, math
import argparse

import random
import shutil
import time
import subprocess
import itertools
import json
from util_scripts.psbased_remapping_random_params_generation import generate_random_params
from analyse_results.AnalyseResults_Exp_RemappingBasic import generate_exp_results_summary

tm_fname                = "test__timeline.png"
vs_bs_fname             = "test__vsbs.js"
util_fname              = "test__util.js"
wf_res_fname            = "test__wfressumm.js"
gops_opbuff_fname       = "test__gopsopbuffsumm.js"    
rmtbl_dt_fname          = "test__rmtbldt.js"
ibuff_fname             = "test__ibuff.js"
obuff_fname             = "test__obuff.js"
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

# remapping on full fact params test
def runSim_RemappingMCParamsTestMain(seed=77379, param_gen_seed=1234):
         
    print "SEED === " + str(seed)    
    
    ##########################
    # PSBased remapping - OFF
    ##########################
    
    subprocess.call(
                        'python -u RunSim_Exp_PSBasedRemapping_MCTest.py ' + \
                        " --exp_type=RMOFF" + \
                        " --forced_seed=" + str(seed) ,shell=True)
    
    
    ##########################
    # PSBased remapping - ON
    ##########################    
    
    # get randomly generated params
    runtime_mins = 2880
    pregenerated_random_params = generate_random_params(max_rumtime_mins=runtime_mins , param_seed=param_gen_seed)
    
    for each_entry_key, each_entry_value  in pregenerated_random_params.iteritems():        
        each_param_entry = each_entry_value ["params"]        
        cmd = 'python -u RunSim_Exp_PSBasedRemapping_MCTest.py ' + \
                        " --exp_type=RMON" + \
                        " --forced_seed=" + str(seed) + \
                        " --tqn=" + str(each_param_entry["rand_TQN"]) + \
                        " --tdecay=" + str(each_param_entry["rand_TDECAY"]) + \
                        " --thresholdqn=" + str(each_param_entry["rand_THRESHOLDQN"])  + \
                        " --thresholdqn_r_i=" + str(each_param_entry["rand_THRESHOLDQN_RAT_INCREASE"])  + \
                        " --thresholdqn_r_d=" + str(each_param_entry["rand_THRESHOLDQN_RAT_DECREASE"])  + \
                        " --khopdec=" + str(each_param_entry["rand_KHOPDECAY"])  + \
                        " --ktimedec=" + str(each_param_entry["rand_KTIMEDECAY"])  + \
                        " --hqn=" + str(each_param_entry["rand_HQN"])  + \
                        " --inithd=" + str(each_param_entry["rand_INITHD"])  + \
                        " --remap_p=" + str(each_param_entry["rand_REMAP_PERIOD"]) + \
                        " --late_rat=" + str(each_param_entry["rand_LATENESS_RATIO"])
                        
        print cmd        
        subprocess.call(cmd , shell=True)
        
        EXP_DATA_DIR = "experiment_data/remapping_psbased_montecarlo/"
        exp_dir = EXP_DATA_DIR + "seed_" + str(seed) + "/"
        exp_params = each_entry_value["fname_param_prefix"]
        
        # perform analysis, and output summary
        print "---- performing analysis ----"
        results_summary = generate_exp_results_summary(exp_dir, exp_params)
        fname_results_summary = exp_dir + "RMON_" + exp_params + "_resultssummary.js"        
        _write_formatted_file(fname_results_summary, results_summary, "json")
        
        # compress data files       
        print "---- compressing data files ----"
        fname_prefix = exp_dir + "RMON_" + exp_params        
        output_zipfile_fname = exp_dir + "RMON_" + exp_params + "_originaldata.zip"
        
        target_file_list = [
                        fname_prefix+wf_res_fname, 
                        fname_prefix+gops_opbuff_fname,
                        fname_prefix+obuff_fname,
                        fname_prefix+trminfo_fname,
                        fname_prefix+nodecumslack_fname,
                        ]
        
        _compress_files(target_file_list, output_zipfile_fname)
        
        
        
       
        

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
runSim_RemappingMCParamsTestMain(seed=args.forced_seed, param_gen_seed = args.param_gen_seed)


