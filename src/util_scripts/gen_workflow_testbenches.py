# system imports
import simpy
import os, sys
import numpy as np
import pprint
from time import gmtime, strftime
import time, random
import json

# local imports
from SimParams import SimParams
from libApplicationModel.Workflow import Workflow
from libApplicationModel.WorkflowGenerator import WorkflowGenerator
from libApplicationModel.AziziMOGATestbenchGenerator import AziziMOGATestbenchGenerator
from util_scripts.resolution_combos import generate_resolution_combos, _reslist_to_string

NOC_H = 3
NOC_W = 3


RANDOM_SEEDS = [80505, 1234, 81665, 33749, 43894, 26358, 70505, \
83660, 22817, 70263, 29917, 26044, \
76891, 50399, 64217, \
44117, 57824, 42267, 83200, 99108, \
95928, 53864, 44289, 77379, 80521, \
88117, 23327, 73337, 94064, 31982, 22250, \
6878, 66093, 69541, 18065, 74076, 98652, 21149, 42198, 5558]

def _reslist_to_string(res_list):
    str_res_list = ""
    for each_r in res_list:
        res_h = each_r[0]
        res_w = each_r[1]
        if str_res_list != "" :   
            str_res_list = str_res_list + "," + str(res_h) + "x" + str(res_w)
        else:
            str_res_list = str(res_h) + "x" + str(res_w)
    return str_res_list


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



def _get_custom_wf_cc1772928_wfs7():
    entry = {
                 "cc" : 1772928,
                 "cc_uid": 0,
                 "avg_cc": 253275.428571,
                 "res_list" : [[720, 576], [240,180], [480,576], [720,576], [528,576], [480,576], [240,180]],
                 'res_list_len' : 7,
                 }    
    return entry

def _remove_custom_wf(res_combos_list, cc, res_list_len):
    
    target_ix = None
    for ix, each_entry in enumerate(res_combos_list):
        #print each_entry['cc'], each_entry['res_list_len']
        if (each_entry['cc'] == cc) and (each_entry['res_list_len'] == res_list_len):
            target_ix= ix
            break;
    
    del res_combos_list[target_ix]
        
    return res_combos_list, target_ix




def get_multiple_workflows(num_wfs, res_list, seed):
    print "get_multiple_workflows:Enter"
    
    #new_res_list = list(res_list)
    
    random.seed(seed)
    np.random.seed(seed)
    #np.random.shuffle(new_res_list) # shuffle in place
    np.random.shuffle(res_list) # shuffle in place
    # create environment
    env = simpy.Environment()
    
    SimParams.NOC_W = NOC_W
    SimParams.NOC_H = NOC_H    
    SimParams.NUM_WORKFLOWS                       = num_wfs    
    SimParams.NUM_NODES = (SimParams.NOC_W * SimParams.NOC_H)
    SimParams.NUM_INPUTBUFFERS                    = SimParams.NUM_WORKFLOWS
    #SimParams.DVB_RESOLUTIONS                     = res_list
    SimParams.DVB_RESOLUTIONS_FIXED               = res_list
    SimParams.DVB_RESOLUTIONS_SELECTED_RANDOM     = False    
    SimParams.CPU_EXEC_SPEED_RATIO = 0.8
    SimParams.NOC_PERIOD = 0.0000001
    SimParams.WFGEN_MIN_GOPS_PER_VID = 5 
    SimParams.WFGEN_MAX_GOPS_PER_VID = 5 
        
    random.seed(seed)
    np.random.seed(seed)
    Workflows = WorkflowGenerator(env, SimParams.NUM_WORKFLOWS, 
                      SimParams.WFGEN_MIN_VIDS_PER_WF, SimParams.WFGEN_MAX_VIDS_PER_WF,
                      SimParams.WFGEN_MIN_GOPS_PER_VID, SimParams.WFGEN_MAX_GOPS_PER_VID,
                      SimParams.WFGEN_MIN_INTER_VIDEO_GAP, SimParams.WFGEN_MAX_INTER_VIDEO_GAP,
                      None,
                      None )
        
    Workflows.generate_workflows()
    
    return Workflows






#################
# MAIN
#################

track_cc_res_array = {}
rand_seed_gen_res_combos = 1234

# get list of random seeds :
res_arr = [(720,576), (544,576), (528,576), (480,576), (426,240), (320,240), (240,180), (230,180)]
max_num_wfs = 10
res_combos = generate_resolution_combos(max_num_wfs-1,res_arr,rand_seed_gen_res_combos, 
                                        sampled=True, 
                                        reduced_samples=10, 
                                        total_samples=20000,
                                        lower_limit=80000)


# remove specific wf
res_combos, target_ix = _remove_custom_wf(res_combos, 1800504, 9)

# add custom wf
res_combos.insert(target_ix, _get_custom_wf_cc1772928_wfs7())

pprint.pprint([ (x['cc'], x['res_list_len']) for x in res_combos])
#sys.exit()
list_of_testbench_fnames = []
seed = 1234

for each_random_seed in RANDOM_SEEDS[:30]:
    
    wf_gen_seed = each_random_seed
    for each_rescombo in res_combos:
            
        res_array = each_rescombo['res_list']        
        num_wfs = len(each_rescombo['res_list'])
        cc = each_rescombo['cc']
        cc_uid = each_rescombo['cc_uid']    
        
        #print "here -1"
        #print res_array
        print "-------------------------------------------------------"
        print cc
        print wf_gen_seed
        pprint.pprint(res_array)
        #strres_array = _reslist_to_string(res_array)
        print _reslist_to_string(res_array)
        
        #--- debug --
        #if (cc == 541584) and (wf_gen_seed==1234):
        #    sys.exit()
        #else:
        #    continue
        #--- debug --
        
        # record res_array        
        track_cc_res_array[str(cc)+"_"+str(wf_gen_seed)] = {
                                                            'res_array' : list(res_array),                                                            
                                                            }
        
        # get workflow
        Workflows = get_multiple_workflows(num_wfs, res_array, wf_gen_seed)
    
        # convert to azizi testbench
        AzizMOGATB = AziziMOGATestbenchGenerator(Workflows.workflows)
        AzizMOGATB.set_flow_pri_offset(max(Workflows.get_used_pri_values()))
        organised_wfs = AzizMOGATB.constructWfLevelTasks()    
        
        testbench_dir = "../MOGATestBenches/"
        testbench_fname = "HdVidTestbench_" + str(NOC_W) + "x" + str(NOC_H) + \
                            "_s" + str(wf_gen_seed)  + \
                            "_wfs" + str(num_wfs) + \
                            "_cc" + str(cc) + \
                            ".txt" 
        list_of_testbench_fnames.append(
                                        {
                                         'testbench_fname' : testbench_fname,
                                         's' : wf_gen_seed,
                                         'cc' : cc,
                                         'cc_uid' : cc_uid,
                                         'res_array' :  res_array,
                                         'num_wfs' : num_wfs
                                         }                                    
                                        )    
        if cc == 1772928:
            tb_text = AzizMOGATB.outputTestBench(organised_wfs, testbench_dir+testbench_fname)


# output the list of 
summary_file_fname = "workflow_testbench_generation_summary.js"
_write_formatted_file(testbench_dir+summary_file_fname, list_of_testbench_fnames, "json")

# -- output res_array -- this is because we made an error (reshuffle overwrites the original array)
track_cc_res_array_fname = "track_cc_res_array.js"
_write_formatted_file(testbench_dir+track_cc_res_array_fname, track_cc_res_array, "json")


    
print "--------"
#pprint.pprint(list_of_testbench_fnames)

    