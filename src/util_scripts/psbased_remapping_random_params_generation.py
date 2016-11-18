import random
import numpy as np
import pprint
import sys


def generate_random_params(max_rumtime_mins = 2880, param_seed = 1234):

    random.seed(param_seed)
    np.random.seed(param_seed)
    
    # duration
    TIME_TAKEN_FOR_ONE_SIMULATION = 35 # minutes    
        
    # params we are concerened about
    #TQN                         = [round(float(x),3) for x in np.linspace(0.048, 0.96, 10)]
    TQN                         = [0.10, 0.22, 0.46, 0.94]
    #TDECAY                     = [round(float(x),3)  for x in np.arange(0.006, 1.0, 0.001)]    
    TDECAY                      = [round(float(x),3)  for x in np.arange(2.0, 4.5, 0.5)]
    
    #TQN_TDECAY_RATIO            = [round(float(x),3)  for x in np.arange(1.0, 10.0, 0.1)]    
    TQN_TDECAY_RATIO            = [round(float(x),3)  for x in np.arange(3.0, 4.5, 0.5)]
    #THRESHOLDQN                 = [round(float(x),1) for x in np.arange(1,26,2)]
    THRESHOLDQN                 = [9.0, 10.0, 15.0, 20.0, 26.0]
    THRESHOLDHOPCOUNT           = [2,3]
    THRESHOLDQN_RAT_DECREASE    = [round(float(x),3) for x in np.linspace(0.01, 0.30, 4)]
    THRESHOLDQN_RAT_INCREASE    = [round(float(x),3) for x in np.linspace(0.01, 0.30, 4)]
    KHOPDECAY                   = [round(float(x),3) for x in np.linspace(0.05, 0.20, 4)]
    KTIMEDECAY                  = [round(float(x),3) for x in np.linspace(0.05, 0.30, 4)]    
    INITHD                      = [int(x) for x in np.arange(1,25,1)]
    HQN                         = [int(x) for x in np.linspace(5, 25, 4)]    
    #REMAP_PERIOD                = [round(float(x),3)  for x in np.linspace(0.46, 4.6, 10)]
    REMAP_PERIOD                = [2.38, 3.80, 4.6, 6.9]
    LATENESS_RATIO              = [round(float(x),3)  for x in np.arange(0.1,1.0, 0.1)]
        
    list_of_patterns = {}
    total_cum_time = 0    
#     total_permutations = len(TQN) * len(TQN_TDECAY_RATIO) * len(THRESHOLDQN) *  len(THRESHOLDHOPCOUNT) * \
#                         len(THRESHOLDQN_RAT_DECREASE) * len(THRESHOLDQN_RAT_INCREASE)* \
#                         len(REMAP_PERIOD) 
     
    total_permutations = len(TQN) * len(TQN_TDECAY_RATIO) * len(THRESHOLDQN_RAT_DECREASE) * \
                         len(THRESHOLDQN_RAT_INCREASE) * len(KHOPDECAY) * \
                         len(KTIMEDECAY) * len(THRESHOLDHOPCOUNT) * len(REMAP_PERIOD) * len(HQN)
                         
    
#     print len(TQN) 
#     print len(TQN_TDECAY_RATIO)
#     print len(THRESHOLDQN)
#    print len(THRESHOLDQN_RAT_DECREASE)
#    print len(THRESHOLDQN_RAT_INCREASE)
#     print len(REMAP_PERIOD) 
    

    #print total_permutations
    
    #sys.exit()
        
    while ((total_cum_time < max_rumtime_mins) and (len(list_of_patterns) < total_permutations)):
        
        rand_TQN                        =  random.choice(TQN)
        if (rand_TQN == 0.000):
            continue                
        rand_TDECAY                     =  round(float(rand_TQN/random.choice(TQN_TDECAY_RATIO)),4)        
        if (rand_TDECAY==0.0000): # we do not want zero tdecays
            continue
                                    
        #rand_THRESHOLDQN                =  random.choice(THRESHOLDQN)
        rand_THRESHOLDHOPCOUNT          = random.choice(THRESHOLDHOPCOUNT)
        rand_KHOPDECAY                  =  random.choice(KHOPDECAY)
        rand_KTIMEDECAY                 =  random.choice(KTIMEDECAY)
        #rand_INITHD                     =  random.choice(INITHD)
        rand_HQN                        =  random.choice(HQN)
        rand_REMAP_PERIOD               =  random.choice(REMAP_PERIOD)
        #rand_LATENESS_RATIO             =  random.choice(LATENESS_RATIO)
        rand_THRESHOLDQN_RAT_DECREASE   =  random.choice(THRESHOLDQN_RAT_DECREASE)
        rand_THRESHOLDQN_RAT_INCREASE   =  random.choice(THRESHOLDQN_RAT_INCREASE)
        
#         perm_key = "perm_" + \
#                     str(rand_TQN) + "_" + \
#                     str(rand_TDECAY) + "_" + \
#                     str(rand_THRESHOLDQN) + "_" + \
#                     str(rand_THRESHOLDHOPCOUNT) + "_" + \
#                     str(rand_THRESHOLDQN_RAT_INCREASE) + "_" + \
#                     str(rand_THRESHOLDQN_RAT_DECREASE) + "_" + \
#                     str(rand_REMAP_PERIOD) + "_"
#                     
#         fname_param_prefix = str(rand_TQN) + \
#                             "_" + str(rand_TDECAY) + \
#                             "_" + str(rand_THRESHOLDQN) + \
#                             "_" + str(rand_THRESHOLDHOPCOUNT) + \
#                             "_" + str(rand_THRESHOLDQN_RAT_INCREASE) + \
#                             "_" + str(rand_THRESHOLDQN_RAT_DECREASE) + \
#                             "_" + str(rand_REMAP_PERIOD)                    

        perm_key = "perm_" + \
                            str(rand_TQN) + "_" +  \
                            str(rand_TDECAY) + "_" +  \
                            str(rand_THRESHOLDHOPCOUNT) + "_" +  \
                            str(rand_REMAP_PERIOD) + "_" +  \
                            str(rand_HQN) + "_" +  \
                            str(rand_THRESHOLDQN_RAT_INCREASE) + "_" +  \
                            str(rand_THRESHOLDQN_RAT_DECREASE) + "_" +  \
                            str(rand_KHOPDECAY) + "_" +  \
                            str(rand_KTIMEDECAY) + "_"
                    
        fname_param_prefix = "_" + str(rand_TQN) + \
                            "_" + str(rand_TDECAY) + \
                            "_" + str(rand_THRESHOLDHOPCOUNT) + \
                            "_" + str(rand_REMAP_PERIOD) + \
                            "_" + str(rand_HQN) + \
                            "_" + str(rand_THRESHOLDQN_RAT_INCREASE) + \
                            "_" + str(rand_THRESHOLDQN_RAT_DECREASE) + \
                            "_" + str(rand_KHOPDECAY) + \
                            "_" + str(rand_KTIMEDECAY)
                            
        
        if (perm_key not in list_of_patterns):
            list_of_patterns[perm_key] = {
                                            "params" : {
                                              "rand_TQN" : rand_TQN,
                                              "rand_HQN" : rand_HQN,
                                              "rand_TDECAY" : rand_TDECAY,
                                              "rand_THRESHOLDQN" : -1.0,
                                              "rand_THRESHOLDHOPCOUNT" : rand_THRESHOLDHOPCOUNT,                                              
                                              "rand_THRESHOLDQN_RAT_INCREASE" : rand_THRESHOLDQN_RAT_INCREASE,
                                              "rand_THRESHOLDQN_RAT_DECREASE" : rand_THRESHOLDQN_RAT_DECREASE,
                                              "rand_REMAP_PERIOD" : rand_REMAP_PERIOD,
                                              "rand_KHOPDECAY" : rand_KHOPDECAY,
                                              "rand_KTIMEDECAY" : rand_KTIMEDECAY,                                              
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

    
    

    
    