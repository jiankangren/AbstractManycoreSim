import os, sys, json, pprint
import numpy as np
from operator import itemgetter
from ccpbased_remapping_random_params_generation import generate_random_params


# 
# RANDOM_SEED_LIST = \
# [81665, 33749, 43894, 26358, 80505, \
#  83660, 22817, 70263, 29917, 26044, \
#  5558,  76891, 22250, 42198, 18065, \
#  74076, 98652, 21149, 50399, 64217, \
#  44117, 57824, 42267, 83200, 99108, \
#  95928, 53864, 44289, 77379, 80521, \
#  88117, 23327, 73337, 94064, 31982, \
#  6878, 66093, 69541]

# RANDOM_SEED_LIST = \
# [81665, 33749, 43894, 53784, 26358, \
# 26044, 6878, 66093, 69541, 5558, \
# 76891, 22250, 69433, 42198, 18065, \
# 74076, 98652, 21149, 50399, 64217, \
# 44117, 57824, 42267, 83200, 99108, \
# 95928, 53864, 44289, 77379, 80521, \
# 88117, 23327, 73337, 94064, 31982]

# RANDOM_SEEDS_LIST = [
#                      # good ones
#                      43894,
#                      70263,
#                      42198,
#                      94064,
#                      68553,
#                      
#                      # bad ones
#                      95537,
#                      18065,
#                      64217,
#                       6878,
#                      94986,
#                      
#                      # close to mean
#                      77379,
#                      98652,
#                      84400,
#                      68385,
#                      66093,
#                      69923,
#                      73337,
#                      88117,
#                      79292,
#                      53784                     
#                      ]

RANDOM_SEEDS_LIST = [81665, 33749, 43894, 53784, 26358, \
80505, 83660, 22817, 70263, 29917, \
26044, 6878, 66093, 69541, 5558, \
76891, 22250, 69433, 42198, 18065, \
74076, 98652, 21149, 50399, 64217, \
44117, 57824, 42267, 83200, 99108, \
95928, 53864, 44289, 77379, 80521, \
88117, 23327, 73337, 94064, 31982]


#MAX_SEEDS = len(RANDOM_SEEDS_LIST)
MAX_SEEDS = 30

def _check_file_exists(fname):
    #print "- checking ::  " + fname
    return os.path.exists(fname)

def _write_formatted_file(fname, data, format):        
    if(format == "pretty"):
        logfile=open(fname, 'w')
        pprint.pprint(data, logfile, width=128)
        
    elif(format == "json"):
        logfile=open(fname, 'w')
        json_data = json.dumps(data)
        logfile.write(json_data)
        
    else:
        logfile=open(fname, 'w')
        pprint.pprint(data, logfile, width=128)


def _get_fname_prefix(rand_params, fname_prefix):
    fname_param_prefix = fname_prefix + rand_params['fname_param_prefix'] + \
                             "_resultssummary.js"    
    return fname_param_prefix

def _get_key_from_fnameprefix(rand_params):    
    key = rand_params['fname_param_prefix']                            
    return key
    

def construct_summary_data():

    # get_params
    rand_params_dict1 = generate_random_params(max_rumtime_mins = 5760, param_seed=1234)
    
    #rand_params_dict1 = _remove_records(rand_params_dict1)
    
    print len(rand_params_dict1)
    
    #rand_params_dict2 = generate_random_params(param_seed=6862)
    #print len(rand_params_dict2)
    #rand_params_dict2.update(rand_params_dict1)
    #print len(rand_params_dict2)
    
    # go through all the param list and determine which params have completed all seeds
    
    track_param_specific_data = {}
    track_errors = {}
    processed_params_perms = 0
    for k, rand_params in rand_params_dict1.iteritems():
        
        track_param_specific_data[k] = {
                                        'arr_GOP_RT_mean_improvement_dist' : [],
                                        'arr_GOP_RT_sum_improvement_dist' : [],
                                        'arr_GOPL_mean_improvement_dist' : [],
                                        'arr_GOPL_max_improvement_dist' : [],
                                        'arr_GOPL_cum_improvement_dist' : [],
                                        '_has_data' : False,
                                        'overall_mean_GOP_RT_sum_improvement' : 0.0,
                                        'overall_mean_GOPL_cum_improvement' : 0.0, 
                                        'overall_mean_GOPL_mean_improvement' : 0.0, 
                                        'overall_mean_GOPL_max_improvement' : 0.0,                                        
                                        }
        processed_seeds = 0
        for each_seed in RANDOM_SEEDS_LIST[:MAX_SEEDS]:
            DATA_FOLDER = "Z:/MCASim/experiment_data/remapping_ccpbased_montecarlo/"+"seed_"+str(each_seed)+"/"
            FNAME_PREFIX = DATA_FOLDER+"RMON_"                    
            fname = _get_fname_prefix(rand_params, FNAME_PREFIX)
                        
            print "---------------------------------------------"
            #print "current param_permutation : " + fname.replace("_resultssummary.js","")  
            #print "fname : " + fname          
            print "remaining_seeds= " + str(processed_seeds) + "/" + str(MAX_SEEDS)
            print "remaining_params= " + str(processed_params_perms) + "/" + str(len(rand_params_dict1.keys()))
            print "---------------------------------------------"
            
            if(_check_file_exists(fname)==True):                
                try:
                    # load results file 
                    json_data=open(fname)
                    file_data = json.load(json_data)
                    json_data.close()
                
                    GOP_RT_RMOFF_mean = file_data['result_gopl']['GOP_RT_RMOFF_mean'][0]
                    GOP_RT_RMON_mean = file_data['result_gopl']['GOP_RT_RMON_mean'][0]
                    GOP_RT_mean_improvement = (GOP_RT_RMOFF_mean - GOP_RT_RMON_mean)/GOP_RT_RMOFF_mean
                    
                    GOP_RT_sum_improvement =  file_data['result_gopl']['GOP_RT_sum_improvement'][0]
                    GOPL_mean_improvement = file_data['result_gopl']['GOPL_mean_improvement'][0]
                    GOPL_max_improvement = file_data['result_gopl']['GOPL_max_improvement'][0]
                    GOPL_cum_improvement = file_data['result_gopl']['GOPL_cum_improvement'][0]                    
                    
                    track_param_specific_data[k]['arr_GOP_RT_mean_improvement_dist'].append(GOP_RT_mean_improvement)
                    track_param_specific_data[k]['arr_GOP_RT_sum_improvement_dist'].append(GOP_RT_sum_improvement)
                    track_param_specific_data[k]['arr_GOPL_mean_improvement_dist'].append(GOPL_mean_improvement)
                    track_param_specific_data[k]['arr_GOPL_max_improvement_dist'].append(GOPL_max_improvement)
                    track_param_specific_data[k]['arr_GOPL_cum_improvement_dist'].append(GOPL_cum_improvement)
                    
                    track_param_specific_data[k]['_has_data'] = True
                except Exception, e:
                    track_errors[fname] = str(e)
                                                           
                    print "WARNING :: error getting data"                        
                    print fname 
            else:
                print "file does not exist : " + fname
            
            processed_seeds+=1
            
                    
        ## find overall result of this permutation ##
        track_param_specific_data[k]['overall_mean_GOP_RT_mean_improvement'] = np.mean(track_param_specific_data[k]['arr_GOP_RT_mean_improvement_dist'])
        track_param_specific_data[k]['overall_mean_GOP_RT_sum_improvement'] = np.mean(track_param_specific_data[k]['arr_GOP_RT_sum_improvement_dist'])
        track_param_specific_data[k]['overall_mean_GOPL_mean_improvement'] = np.mean(track_param_specific_data[k]['arr_GOPL_mean_improvement_dist'])
        track_param_specific_data[k]['overall_mean_GOPL_max_improvement'] = np.mean(track_param_specific_data[k]['arr_GOPL_max_improvement_dist'])
        track_param_specific_data[k]['overall_mean_GOPL_cum_improvement'] = np.mean(track_param_specific_data[k]['arr_GOPL_cum_improvement_dist'])
        track_param_specific_data[k]['arr_GOPL_cum_improvement_dist'] = track_param_specific_data[k]['arr_GOPL_cum_improvement_dist']
        
        processed_params_perms+=1        
        
    print "Finished gathering data ..."
    print "Finding best param ..."    
    
    temp_unsorted_results = []
    for k, each_param in track_param_specific_data.iteritems():
        if(len(each_param['arr_GOPL_cum_improvement_dist'])>=10):
            record = {  
                      'param' : k,
                      'all_GOPL_mean_dist_values' : each_param['arr_GOPL_cum_improvement_dist'],
                      'overall_mean_GOP_RT_mean_improvement' : each_param['overall_mean_GOP_RT_mean_improvement'],
                      'overall_mean_GOP_RT_sum_improvement' : each_param['overall_mean_GOP_RT_sum_improvement'],
                      'overall_mean_GOPL_mean_improvement' : each_param['overall_mean_GOPL_mean_improvement'],
                      'overall_mean_GOPL_max_improvement' :  each_param['overall_mean_GOPL_max_improvement'],
                      'overall_mean_GOPL_cum_improvement' :  each_param['overall_mean_GOPL_cum_improvement'],
                      'no_seeds_completed' : len(each_param['arr_GOP_RT_sum_improvement_dist'])
                      }
            
            temp_unsorted_results.append(record)
    
    final_sorted_results = sorted(temp_unsorted_results, key=lambda k: k['overall_mean_GOPL_cum_improvement'], reverse=True)
                
    # write out data summary
    print "Writing out final results ..."    
        
    fname_summary_output =    "Z:/MCASim/experiment_data/remapping_ccpbased_montecarlo/" + "mcparam_final_results.js"
    fname_error_output =    "Z:/MCASim/experiment_data/remapping_ccpbased_montecarlo/" + "mcparam_error_.js"
    _write_formatted_file(fname_summary_output, final_sorted_results, "json")
    _write_formatted_file(fname_error_output, track_errors, "json")
        

def _remove_records(params_list):    
    new_param_list = {}
    for k, rand_params in params_list.iteritems():
        if rand_params['params']["rand_THRESHOLDHOPCOUNT"] != 4:
            new_param_list[k] = rand_params
    
    return new_param_list
    

###################
## MAIN
###################
construct_summary_data()
    