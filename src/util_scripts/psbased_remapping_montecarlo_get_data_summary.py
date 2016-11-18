import os, sys, json, pprint
import numpy as np
from operator import itemgetter
from psbased_remapping_random_params_generation import generate_random_params

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


RANDOM_SEED_LIST = \
[81665, 33749, 43894, 53784, 26358, \
80505, 83660, 22817, 70263, 29917, \
26044, 6878, 66093, 69541, 5558, \
76891, 22250, 69433, 42198, 18065, \
74076, 98652, 21149, 50399, 64217, \
44117, 57824, 42267, 83200, 99108, \
95928, 53864, 44289, 77379, 80521, \
88117, 23327, 73337, 94064, 31982]



def _check_file_exists(fname):
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


def construct_summary_data(get_obuff_data = True, get_gopsumm_data= True):

    # get_params
    rand_params_dict = generate_random_params(5760)
    
    # go through all the seeds and determine which are complete
    complete_seed_list = []
    for each_seed in RANDOM_SEED_LIST:
        DATA_FOLDER = "../experiment_data/remapping_psbased_montecarlo/"+"seed_"+str(each_seed)+"/"
        FNAME_PREFIX = DATA_FOLDER+"RMON_"
        
        # which seeds have completed all the monte_carlo params ?
        count = 0
        for k, rand_params in rand_params_dict.iteritems():    
        
            fname = FNAME_PREFIX + str(rand_params["rand_TQN"]) + \
                    "_" + str(rand_params["rand_TDECAY"]) + \
                    "_" + str(rand_params["rand_THRESHOLDQN"]) + \
                    "_" + str(rand_params["rand_KHOPDECAY"]) + \
                    "_" + str(rand_params["rand_KTIMEDECAY"]) + \
                    "_" + str(rand_params["rand_HQN"]) + \
                    "_" + str(rand_params["rand_INITHD"]) + \
                    "_" + str(rand_params["rand_REMAP_PERIOD"]) + \
                    "_" + str(rand_params["rand_LATENESS_RATIO"]) + "_test__obuff.js"            
    
        
            if(_check_file_exists(fname)==True):
                count += 1
        if(count == len(rand_params_dict)):
            complete_seed_list.append(each_seed)
        
        
    # report
    print "count_finished_Seeds : " + str(len(complete_seed_list))
    #sys.exit()
    
    obuf_all_exp_data = {}
    gopsumm_all_exp_data = {}
    processed_params_perms = 0
    track_obuff_errors = []
    track_gopsumm_errors = []
    for k, rand_params in rand_params_dict.iteritems():
        
        if(k not in obuf_all_exp_data):
            obuf_all_exp_data[k] = {}
        if(k not in gopsumm_all_exp_data):
            gopsumm_all_exp_data[k] = {}
        
        processed_seeds = 0
        for each_seed in complete_seed_list:  
    
            DATA_FOLDER = "../experiment_data/remapping_psbased_montecarlo/"+"seed_"+str(each_seed)+"/"
            FNAME_PREFIX = DATA_FOLDER+"RMON_"
            rmon_fname = FNAME_PREFIX + str(rand_params["rand_TQN"]) + \
                    "_" + str(rand_params["rand_TDECAY"]) + \
                    "_" + str(rand_params["rand_THRESHOLDQN"]) + \
                    "_" + str(rand_params["rand_KHOPDECAY"]) + \
                    "_" + str(rand_params["rand_KTIMEDECAY"]) + \
                    "_" + str(rand_params["rand_HQN"]) + \
                    "_" + str(rand_params["rand_INITHD"]) + \
                    "_" + str(rand_params["rand_REMAP_PERIOD"]) + \
                    "_" + str(rand_params["rand_LATENESS_RATIO"])  
            
            print "---------------------------------------------"
            print "current param_permutation : " + k
            print "current seed: " + str(each_seed)
            print "remaining_seeds= " + str(processed_seeds) + "/" + str(len(complete_seed_list))
            print "remaining_params= " + str(processed_params_perms) + "/" + str(len(rand_params_dict.keys()))
            print "---------------------------------------------"
            
            ########################################
            ########## get obuf data ###############
            
            if(get_obuff_data == True):
            
                # get remapping-off data
                FNAME_PREFIX = "RMOFF_"    
                fname = DATA_FOLDER + "/" + "RMOFF_" + "test__obuff.js"    
                json_data=open(fname)
                remapping_off_data = json.load(json_data)
                json_data.close()
                
                # get remapping-off data
                FNAME_PREFIX = "RMON_"    
                fname = rmon_fname 
                json_data=open(fname+ "_test__obuff.js" )
                remapping_on_data = json.load(json_data)
                json_data.close()
                
                # sort them according to id
                sorted_remapping_off_data = sorted(remapping_off_data, key=itemgetter('dt')) 
                sorted_remapping_on_data = sorted(remapping_on_data, key=itemgetter('dt'))
                
                # get response_time variance for each task
                all_variances = []
                negative_variances  = []
                positive_variances  = []
                equal_variances = []
                rmoff_all_responsetimes = []
                rmon_all_responsetimes = []
                
                        
                for ix,each_task in enumerate(sorted_remapping_off_data):
                    error = False
                    try:
                        rm_off_resptime = sorted_remapping_off_data[ix]['et']  - sorted_remapping_off_data[ix]['dt']
                        rm_on_resptime = sorted_remapping_on_data[ix]['et']  - sorted_remapping_on_data[ix]['dt']
                        
                        rmoff_all_responsetimes.append(rm_off_resptime)
                        rmon_all_responsetimes.append(rm_on_resptime)
                        
                        variance = rm_off_resptime - rm_on_resptime
                        
                        # track variances
                        if(variance>0): # good                
                            positive_variances.append(variance)                
                        elif(variance<0): # bad                
                            negative_variances.append(variance)                
                        else:
                            equal_variances.append(variance)
                            
                        all_variances.append(variance)
                    except:
                        error = True
                        print "WARNING :: error getting data - obuff"
                        print ix
                        pprint.pprint(each_task)
                        print each_seed
                        
                        track_obuff_errors.append({
                                             'param_fname' : rmon_fname,                                              
                                             'each_seed' : each_seed,
                                             'ix' : ix,
                                             'each_task' : each_task
                                             })                        
                        break
                        
                        
                
                if(error != True):
                    obuf_all_exp_data[k][each_seed] = {                                   
                                               'mean_max_min_RMOFF_resptimes' :  [np.mean(rmoff_all_responsetimes), np.max(rmoff_all_responsetimes), np.min(rmoff_all_responsetimes)],
                                               'mean_max_min_RMON_resptimes' :  [np.mean(rmon_all_responsetimes), np.max(rmon_all_responsetimes), np.min(rmon_all_responsetimes)],
                                               'neg_variances_size' : len(negative_variances),                                   
                                               'pos_variances_size' : len(positive_variances),
                                               'sum_pos_var' : np.sum(positive_variances),
                                               'sum_neg_var' : np.sum(negative_variances),
                                               'equal_variances_num' : len(equal_variances),                                   
                                               'sum_all_variances' : np.sum(all_variances),
                                               'mean_variances' : np.mean(all_variances),
                                               }
            
            
            ########################################
            ########## get gopsum data #############
                        
            if(get_gopsumm_data == True):
            
                # get remapping-off data
                FNAME_PREFIX = "RMOFF_"    
                fname = DATA_FOLDER + "/" + "RMOFF_" + "test__gopsopbuffsumm.js"    
                json_data=open(fname)
                remapping_off_data = json.load(json_data)
                json_data.close()
                
                # get remapping-off data
                FNAME_PREFIX = "RMON_"    
                fname = rmon_fname 
                json_data=open(fname+ "_test__gopsopbuffsumm.js" )
                remapping_on_data = json.load(json_data)
                json_data.close()
                        
            
                gop_lateness_distribution_rmoff = []
                gop_lateness_distribution_rmon = []
                
                # gop lateness distribution - rm-off
                for each_ugid_key, each_ugid_val in remapping_off_data.iteritems():
                    if(each_ugid_val['gop_execution_lateness'] > 0):
                        gop_lateness_distribution_rmoff.append(each_ugid_val['gop_execution_lateness'])        
                if(len(gop_lateness_distribution_rmoff)==0):
                    gop_lateness_distribution_rmoff = [0]           
                
                # gop lateness distribution - rm-on
                for each_ugid_key, each_ugid_val in remapping_on_data.iteritems():
                    if(each_ugid_val['gop_execution_lateness'] > 0):
                        gop_lateness_distribution_rmon.append(each_ugid_val['gop_execution_lateness'])        
                if(len(gop_lateness_distribution_rmon)==0):
                    gop_lateness_distribution_rmon = [0]
                
                #print "RMON gop-lateness-dist-size = " + str(len(gop_lateness_distribution_rmon))
                #print "RMOFF gop-lateness-dist-size = " + str(len(gop_lateness_distribution_rmoff))
                
                try:
                
                    rmoff_ssize_mean_max_min_median_lateness = {
                                                                'ssize': len(gop_lateness_distribution_rmoff),
                                                                 'mean': np.mean(gop_lateness_distribution_rmoff),
                                                                 'max': np.max(gop_lateness_distribution_rmoff),
                                                                 'min' : np.min(gop_lateness_distribution_rmoff),
                                                                 'median' : np.median(gop_lateness_distribution_rmoff)
                                                                 }
                    rmon_ssize_mean_max_min_median_lateness = {
                                                               'ssize': len(gop_lateness_distribution_rmon),
                                                               'mean': np.mean(gop_lateness_distribution_rmon),
                                                               'max': np.max(gop_lateness_distribution_rmon),
                                                               'min': np.min(gop_lateness_distribution_rmon),
                                                               'median': np.median(gop_lateness_distribution_rmon)
                                                               }
    
                    meanlateness_variance = float(rmon_ssize_mean_max_min_median_lateness['mean'] - rmoff_ssize_mean_max_min_median_lateness['mean'])
                    maxlateness_variance = float(rmon_ssize_mean_max_min_median_lateness['max'] - rmoff_ssize_mean_max_min_median_lateness['max'])
                    meanlateness_improvement = np.round(-1.0*(float(100.0*(meanlateness_variance/rmoff_ssize_mean_max_min_median_lateness['mean']))),3)
                    maxlateness_improvement = np.round(-1.0*(float(100.0*(maxlateness_variance/rmoff_ssize_mean_max_min_median_lateness['max']))),3)
                    
                    gopsumm_all_exp_data[k][each_seed] = {
                           'rmoff_ssize_mean_max_min_median_lateness' : rmoff_ssize_mean_max_min_median_lateness,                        
                           'rmon_ssize_mean_max_min_median_lateness' : rmon_ssize_mean_max_min_median_lateness,                        
                            'improvement_mean_lateness' : meanlateness_improvement,
                            'improvement_max_lateness' : maxlateness_improvement
                           }
                    
                except Exception, e:
                    track_gopsumm_errors.append({
                                                 'param_fname' : rmon_fname,                                              
                                                 'each_seed' : each_seed,                                                
                                                 })
                    print "WARNING :: error getting data - gopsumm"                        
                    print str(e)
                    print each_seed
                    print rmon_fname
                     
            
            processed_seeds += 1
        processed_params_perms += 1
        
        
    
    # write out data summary
    if(get_obuff_data==True):
        fname_summary_output =    "../experiment_data/remapping_psbased_montecarlo/" + "summary_obuff.js"
        fname_error_output =    "../experiment_data/remapping_psbased_montecarlo/" + "error_obuff.js"
        _write_formatted_file(fname_summary_output, obuf_all_exp_data, "json")
        _write_formatted_file(fname_error_output, track_obuff_errors, "json")
    
    if(get_gopsumm_data==True):
        fname_summary_output =    "../experiment_data/remapping_psbased_montecarlo/" + "summary_gopsumm.js"
        fname_error_output =    "../experiment_data/remapping_psbased_montecarlo/" + "error_gopsumm.js"
        _write_formatted_file(fname_summary_output, gopsumm_all_exp_data, "json")
        _write_formatted_file(fname_error_output, track_gopsumm_errors, "json")

    

###################
## MAIN
###################
construct_summary_data(get_obuff_data = True, get_gopsumm_data= True)
    