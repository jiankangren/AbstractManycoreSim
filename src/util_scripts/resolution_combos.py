import sys, os, csv, pprint, math
# 
# from collections import OrderedDict
# from collections import Counter
import numpy as np
import random
# import shutil
# import math
# import matplotlib
# import matplotlib.pyplot as plt
# from mpl_toolkits.mplot3d import Axes3D
# import scipy.stats
# import itertools
# from matplotlib.colors import ListedColormap, NoNorm
# from matplotlib import mlab
# from itertools import cycle # for automatic markers
# import json
# from operator import itemgetter
# 
# import matplotlib.cm as cm
# from matplotlib.font_manager import FontProperties


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
        

def get_sampled_subset(orig_list, num_samples):
    sample_points = np.linspace(1,len(orig_list),num_samples+1)    
    rounded_integer_sample_ixs = [int(round(x)) for x in sample_points]
    print rounded_integer_sample_ixs
    
    sampled_list = [val for ix, val in enumerate(orig_list) if ix in rounded_integer_sample_ixs]
    return sampled_list
    


def generate_resolution_combos(num_wfs, res_arr, rand_seed, sampled=False, reduced_samples=500, total_samples=2000, lower_limit=0):
    
    random.seed(rand_seed)
    np.random.seed(rand_seed)
    
    n = total_samples
    samples = reduced_samples
    
    list_of_combos = []
    existing_cc = []
    existing_reslist_strs = []
    
    i=0
    while(i<n):
        entry = {
                 "cc" : 0,
                 "cc_uid": 0,
                 "avg_cc": 0.0,
                 "res_list" : [],
                 'res_list_len' : 0,
                 }
        cc = 0
        avg_cc = 0.0
        # sum up all the resolutions in this combo
        for j in xrange(random.randrange(num_wfs)+1):
            res = random.choice(res_arr)
            entry['res_list'].append(res)
            cc += res[0] *  res[1] 
        
        # make sure above the lower limit threshold
        if cc >= lower_limit:               
            entry['cc'] = cc
            entry['res_list_len'] = len(entry['res_list'])
            entry['avg_cc'] = float(float(cc)/float(len(entry['res_list'])))
    #         if(entry['cc'] not in existing_cc):
    #             list_of_combos.append(entry)
    #             existing_cc.append(entry['cc'])
            
            if(_reslist_to_string(entry['res_list']) not in existing_reslist_strs):
                list_of_combos.append(entry)
                existing_cc.append(entry['cc'])
                existing_reslist_strs.append(_reslist_to_string(entry['res_list']))
            
            # cc uid (unique id offset for the cc)
            entry['cc_uid'] = len([x for x in existing_cc if x==entry['cc']])
            i+=1
        
    # sort
    if (sampled==False):               
        sorted_list_of_combos = sorted(list_of_combos, key=lambda k: k['cc'])
    else:
        sampled_list_of_combos = get_sampled_subset(list_of_combos, samples) 
        sorted_list_of_combos = sorted(sampled_list_of_combos, key=lambda k: k['cc'])
       
    return sorted_list_of_combos



## testing ##

# res_arr = [(720,576), (544,576), (528,576), (480,576), (426,240), (320,240), (240,180), (230,180)]
# result = generate_resolution_combos(9, res_arr, 1234, sampled=True)
#     
# pprint.pprint( [x["cc"] for x in result])
# print len(result)
#     
#    
# #pprint.pprint(result)
#     
#           
# pprint.pprint(Counter([x['cc_uid'] for x in result]))
#     
#     
#     
#           
# fig, ax1 = plt.subplots()
#         
# ax1.plot(range(len(result)), [x['cc'] for x in result], marker='x', color='r')
# ax2 = ax1.twinx()
# plt.plot(range(len(result)), [len(x['res_list']) for x in result], marker='o', linestyle='--')
#         
# plt.show()





    
    