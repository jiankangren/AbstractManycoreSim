import random
import numpy as np
import pprint
import sys

def generate_random_params(max_rumtime_mins = 2880, param_seed = 1234):

    random.seed(param_seed)
    np.random.seed(param_seed)
    
    # duration
    TIME_TAKEN_FOR_ONE_SIMULATION = 40 # minutes    
        
    # params we are concerened about
    #CLUSTER_SIZE                = ["2-2"]
    CLUSTER_SIZE                = ["5-5", "2-5"]
    REMAP_PERIOD                = [0.96, 2.4, 4.8, 7.2]
    LATENESS_RATIO              = [0.1, 0.2, 0.4, 0.6, 0.8, 1.0]
    LOAN_AMOUNT                 = [1,2,5,8,10]
        
    list_of_patterns = {}
    total_cum_time = 0    
    total_permutations = len(CLUSTER_SIZE) * \
                        len(REMAP_PERIOD) * \
                        len(LOAN_AMOUNT)
    
    #print total_permutations
    #sys.exit()
    
    while ((total_cum_time < max_rumtime_mins) and (len(list_of_patterns) < total_permutations)):
        
        rand_CLUSTER_SIZE                        =  random.choice(CLUSTER_SIZE)
        rand_REMAP_PERIOD                        =  random.choice(REMAP_PERIOD)
        rand_LATENESS_RATIO                      =  random.choice(LATENESS_RATIO)
        rand_LOAN_AMOUNT                         =  random.choice(LOAN_AMOUNT)
        
        perm_key = "perm_" + \
                    str(rand_CLUSTER_SIZE) + "_" + \
                    str(rand_REMAP_PERIOD) + "_" + \
                    str(rand_LOAN_AMOUNT) + "_"
                    
        fname_param_prefix = str(rand_CLUSTER_SIZE) + \
                            "_" + str(rand_REMAP_PERIOD) + \
                            "_" + str(rand_LOAN_AMOUNT)                 
        
        if (perm_key not in list_of_patterns):
            list_of_patterns[perm_key] = {
                                            "params" : {
                                              "rand_CLUSTER_SIZE" : rand_CLUSTER_SIZE,
                                              "rand_REMAP_PERIOD" : rand_REMAP_PERIOD,
                                              "rand_LOAN_AMOUNT" : rand_LOAN_AMOUNT,
                                              "rand_LATENESS_RATIO" : -1.0,
                                              },
                                          
                                            "fname_param_prefix" : fname_param_prefix
                                          }        
            total_cum_time += TIME_TAKEN_FOR_ONE_SIMULATION        
        else:
            #ignore
            i=1
    
    return list_of_patterns

#print "finished!"
#random_params = generate_random_params(max_rumtime_mins=5760)
#print pprint.pprint(random_params)
#print len(random_params)

    
    

    
    