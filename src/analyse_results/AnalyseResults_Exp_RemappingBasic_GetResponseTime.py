## temporary data extraction script for amit singh

import sys, os, csv, pprint, math
import shutil
import math
import json

    

def getExecutionCost_Jobs(fname_in):    
    try:            
        print fname_in
        json_data=open(fname_in)
        gop_data = json.load(json_data)
    except:
        print "------"
        print "file not found !"
        print fname_in
        print "------"
        sys.exit()
        
    # get sorted list of gop ids (keys)
    gop_id_keys = sorted([k for k in gop_data.keys()])
    
    # go through each gop and get response time
    gop_response_time = []
    for each_ugid_key in gop_id_keys:
        #if(gop_data[each_ugid_key]['gop_execution_lateness'] > 0): ## uncomment this if ONLY late jobs are needed
            gop_response_time.append(gop_data[each_ugid_key]['tt_wrt_dt'])
    
    return gop_response_time
    




###################################
#    HELPERS
###################################


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
            


###################################
#    MAIN
###################################

DATA_IN_FNAME = "Z:/MCASim/experiment_data/remapping_psbased/seed_42198/RMON_test__gopsopbuffsumm.js"
DATA_OUT_FNAME =  "gop_resptime_array_test_010616.js"

print "data input : " + DATA_IN_FNAME
result = getExecutionCost_Jobs(fname_in = DATA_IN_FNAME)
_write_formatted_file(DATA_OUT_FNAME, result, format="json")

print "data output : " + DATA_IN_FNAME


print "finished !"

