import pprint
import sys
import math, random
import numpy as np
import copy
from datetime import datetime
import csv
import bisect
import json
import itertools
import networkx as nx
import matplotlib.pyplot as plt
from collections import Counter, Sequence
from collections import OrderedDict
import pickle
import os
from scipy.stats import rv_discrete

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# local imports
from SimParams import SimParams
import libApplicationModel.HEVCWorkloadParams as HEVCWLP

USE_PROBABILISTIC_HEVCWL_MODEL = True



def generate_PU_per_CTU(slice_type, frame_res):
        ctu_size = SimParams.HEVC_CTU_SIZE # we need to split this up into the quad tree structure
                
        if(slice_type == "Is"):
            block_sizes_list = SimParams.HEVC_PU_BLOCK_SIZES_INTRA 
            block_size_weights = SimParams.HEVC_PU_BLOCK_SIZES_PROBABILITY[frame_res]['intra']
            pu_type = ["Ipu"]
        else:
            block_sizes_list = SimParams.HEVC_PU_BLOCK_SIZES_INTER
            block_size_weights = SimParams.HEVC_PU_BLOCK_SIZES_PROBABILITY[frame_res]['inter']
            pu_type = ["Ppu", "Bpu"]
        
        result_pus = []
        cum_pix = 0 # cumulative pixels count
        while(cum_pix<ctu_size):            
            selected_pu_size = _weightedChoice(block_size_weights, block_sizes_list)            
            selected_pu_pix = selected_pu_size[0]*selected_pu_size[1]
            
            if ((cum_pix+selected_pu_pix)<=ctu_size):
                #rand_pu_type = random.choice(pu_type)
                result_pus.append(selected_pu_size)
                          
                cum_pix+=selected_pu_pix
        
        return result_pus


def generate_PU_per_CTU_ProbabilisticModel(slice_type, movtype):
        
        print slice_type
        
        ctu_size = SimParams.HEVC_CTU_SIZE # we need to split this up into the quad tree structure
        block_sizes_list = SimParams.HEVC_PU_BLOCK_SIZES_ALL    
        if(slice_type == "Is"):             
            block_size_weights = HEVCWLP.HEVCWLPARAMS_CU_SIZE_PROBABILITIES[movtype]['Intra']            
        else:            
            block_size_weights = HEVCWLP.HEVCWLPARAMS_CU_SIZE_PROBABILITIES[movtype]['Inter']            
        
        result_pus = []
        cum_pix = 0 # cumulative pixels count
        while(cum_pix<ctu_size):
            distrib = rv_discrete(values=(block_sizes_list, block_size_weights))
            all_possible_cu_sizes = distrib.rvs(size=100)
            
            tmp_selected_pu_size = np.random.choice(all_possible_cu_sizes) 
            selected_pu_size = (tmp_selected_pu_size,tmp_selected_pu_size)           
            selected_pu_pix = tmp_selected_pu_size*tmp_selected_pu_size
            
            if ((cum_pix+selected_pu_pix)<=ctu_size):                
                result_pus.append(selected_pu_size)                          
                cum_pix+=selected_pu_pix
        
        return result_pus


def generate_PU_per_CTU_ProbabilisticModel_v2(slice_type, movtype, current_pus_set_list, all_combos_len_intra, all_combos_len_inter):
        
        print slice_type
        
        ctu_size = SimParams.HEVC_CTU_SIZE # we need to split this up into the quad tree structure
        block_sizes_list = SimParams.HEVC_PU_BLOCK_SIZES_ALL    
        if(slice_type == "Is"):             
            block_size_weights = HEVCWLP.HEVCWLPARAMS_CU_SIZE_PROBABILITIES[movtype]['Intra']   
            all_combos_len = all_combos_len_intra         
        else:            
            block_size_weights = HEVCWLP.HEVCWLPARAMS_CU_SIZE_PROBABILITIES[movtype]['Inter']
            all_combos_len = all_combos_len_inter            
        
        cum_pix = 0 # cumulative pixels count        
        i=0
        
        print "trying ",
        while(cum_pix != ctu_size):
            rand_size = np.random.choice(all_combos_len)
            all_possible_cu_sizes = np.random.choice(block_sizes_list, p=block_size_weights, size=rand_size)
            
            sorted_all_possible_cu_sizes = sorted(all_possible_cu_sizes)
            
            if sorted_all_possible_cu_sizes not in current_pus_set_list:            
                cum_pix = np.sum([p*p for p in all_possible_cu_sizes])
            else:
                cum_pix = 0
                
            i+=1
            
            if (i%10000) == 0:
                #print "trying %d" % (i)
                np.random.seed()
            
            
            if (i%100000) == 0:
                print str(i) + ", ",
            
           
        result_pus = [(p,p) for p in all_possible_cu_sizes]
        print ""
        print "pu_list len : ", len(result_pus)
        
        return result_pus





def generate_PU_per_CTU_ProbabilisticModel_v3(slice_type, movtype, current_pus_set_list, all_combos_len,
                                              cu_probs):
    
    print slice_type
    
    ctu_size = SimParams.HEVC_CTU_SIZE # we need to split this up into the quad tree structure
    block_sizes_list = SimParams.HEVC_PU_BLOCK_SIZES_ALL    
    
    cum_pix = 0 # cumulative pixels count        
    i=0
    
    print "trying ",
    while(cum_pix != ctu_size):
        rand_size = np.random.choice(all_combos_len)
        all_possible_cu_sizes = np.random.choice(block_sizes_list, p=cu_probs, size=rand_size)
        
        sorted_all_possible_cu_sizes = sorted(all_possible_cu_sizes)
        
        if sorted_all_possible_cu_sizes not in current_pus_set_list:            
            cum_pix = np.sum([p*p for p in all_possible_cu_sizes])
        else:
            cum_pix = 0
        i+=1
        
        if (i%10000) == 0:
            #print "trying %d" % (i)
            np.random.seed()
        if (i%100000) == 0:
            print str(i) + ", ",
        
    result_pus = [(p,p) for p in all_possible_cu_sizes]
    print ""
    print "pu_list len : ", len(result_pus)
    
    return result_pus
    

def _get_cusize_probabilities(slice_type, movtype):
    if(slice_type == "Is"):             
        block_size_weights = HEVCWLP.HEVCWLPARAMS_CU_SIZE_PROBABILITIES[movtype]['Intra']            
    else:            
        block_size_weights = HEVCWLP.HEVCWLPARAMS_CU_SIZE_PROBABILITIES[movtype]['Inter']
    
    return block_size_weights
    


def _get_new_adjusted_weights(original_cu_weights, prev_cu_list):    
    if prev_cu_list == []:
        return original_cu_weights
    
    new_weights = []
    cu_sizes = [64, 32, 16, 8, 4]
    plist = [p[0] for p in prev_cu_list]
    probs = [float(plist.count(c))/float(len(plist)) for c in cu_sizes]
    
    print "current probs : ", probs
    
    for ix, c in enumerate(cu_sizes):
        current_p = probs[ix]
        delta = original_cu_weights[ix] - current_p
        new_p = original_cu_weights[ix] + delta
        new_weights.append(new_p)
    
    return new_weights    
        



def _weightedChoice(weights, objects):
            #http://stackoverflow.com/questions/10803135/weighted-choice-short-and-simple
            """Return a random item from objects, with the weighting defined by weights 
            (which must sum to 1)."""
            cs = np.cumsum(weights) #An array of the weights, cumulatively summed.
              
            idx = np.sum(cs < np.random.rand()) #Find the index of the first weight over a random value.
            return objects[idx]


def get_unique_combinations(current_pus_list):
    # find unique combinations
    unique_lists = {}
    
    for l in current_pus_list:                    
        k = "-".join([str(i) for i in l])
        if k not in unique_lists:
            unique_lists[k] = 1
        else:
            unique_lists[k] += 1
    
    print "-------"
    pprint.pprint(unique_lists)
    print "unique lists : ",  len(unique_lists.keys())



# exhaustive method
def find_all_permutations(total = 64*64):
                   
    all_permutations_intra = []
    all_permutations_inter = []
    
    ## for intra ##
    px_list = [32*32, 16*16, 8*8, 4*4]
    for i in xrange(int(float(total)/float(px_list[0]))):
        for j in xrange(int(float(total)/float(px_list[1]))):
            for k in xrange(int(float(total)/float(px_list[2]))):
                for m in xrange(int(float(total)/float(px_list[3]))):
                    
                    current_sum = (px_list[0]*i) + \
                                    (px_list[1]*j) + \
                                    (px_list[2]*k) + \
                                    (px_list[3]*m)
                    
                    perm = [px_list[0]/32]*i + [px_list[1]/16]*j + [px_list[2]/8]*k + [px_list[3]/4]*m
                    
                    if current_sum == total:                        
                        all_permutations_intra.append(perm)

    ## for inter ##
    px_list = [32*32, 16*16, 8*8]
    for i in xrange(int(float(total)/float(px_list[0]))):
        for j in xrange(int(float(total)/float(px_list[1]))):
            for k in xrange(int(float(total)/float(px_list[2]))):
                    
                    current_sum = (px_list[0]*i) + \
                                    (px_list[1]*j) + \
                                    (px_list[2]*k)
                    
                    perm = [px_list[0]/32]*i + [px_list[1]/16]*j + [px_list[2]/8]*k
                    
                    if current_sum == total:                        
                        all_permutations_inter.append(perm)
                        
    
    return (all_permutations_intra, all_permutations_inter)

    


#####################
# MAIN
#####################

# get all possible combinations
print "getting all combos length"
(combos_intra, combos_inter) = find_all_permutations()
len_combos_intra = list(set([len(r) for r in combos_intra]))
len_combos_inter = list(set([len(r) for r in combos_inter]))

print len(len_combos_intra)
print len(len_combos_inter)

print "getting all combos length -- finished"

# we have to generate
ALL_POSSIBLE_RESOLUTIONS = [(7680*4320), (3840*2160), 
                           (2048*1080), (2560*1440), (1920*1080), 
                           (1280*720), (720*576), (854*480), 
                           (640*480), (544*576), 
                           (528*576), (480*576),  (640*360),
                           (426*240), (320*240), 
                           (240*180)]



SLICE_TYPES = ["Is", "Ps", "Bs"]
NUM_CTU = 10

NUM_CTU_INTRA = 15
NUM_CTU_INTER = 7

final_random_ctu_list = {}


if USE_PROBABILISTIC_HEVCWL_MODEL==True:
    #### --- using probability models from trace data ------
    
    #for each_mov_type in HEVCWLP.HEVCWLPARAMS_TYPES_OF_VIDEOS:
    for each_mov_type in ['DOC']:
            final_random_ctu_list[each_mov_type] = {}
            for each_slice_type in SLICE_TYPES:
                final_random_ctu_list[each_mov_type][each_slice_type] = []
                current_pus_list = []
                pus_list = []
                
                if each_slice_type in ["Is"]: num_ctu = NUM_CTU_INTRA
                else: num_ctu = NUM_CTU_INTER
                
                for each_ctu in xrange(num_ctu):
                    #pus_list = generate_PU_per_CTU_ProbabilisticModel(each_slice_type, each_mov_type)
                    pus_list = generate_PU_per_CTU_ProbabilisticModel_v2(each_slice_type, 
                                                                         each_mov_type, 
                                                                         current_pus_list,
                                                                         len_combos_intra,
                                                                         len_combos_inter)
                     
                    #original_cu_weights = _get_cusize_probabilities(each_slice_type, each_mov_type)
                    #adjusted_cu_weights = _get_new_adjusted_weights(original_cu_weights, pus_list)
                    
                    #print "original_cu_weights : ", original_cu_weights
                    #print "adjusted_cu_weights : ", adjusted_cu_weights
                    
#                     pus_list = generate_PU_per_CTU_ProbabilisticModel_v3(each_slice_type, 
#                                                               each_mov_type, 
#                                                               current_pus_list,
#                                                               length_all_possible_combos,
#                                                               adjusted_cu_weights
#                                                               )
                    
                    
                    current_pus_list.append(sorted([p[0] for p in pus_list]))
                    
                    final_random_ctu_list[each_mov_type][each_slice_type].append({
                                                                             'pu_list': pus_list,
                                                                             }) 
                                                                         
                    print "-- done : ", each_mov_type, each_slice_type, each_ctu
                
                
                #get_unique_combinations(current_pus_list)
                
#                 # plot
#                 size_types = {4:0, 8:0, 16:0, 32:0, 64:0}
#                 for p in final_random_ctu_list[each_mov_type][each_slice_type]:
#                     each_pulist = p['pu_list']
#                     for each_pu in each_pulist:
#                         size_types[each_pu[0]]+=1
#                     
#                 f = plt.figure()  
#                 pprint.pprint(size_types)                  
#                 lbl_vals = [(k,v)  for k,v in size_types.iteritems()]
#                 lbls = [i[0]  for i in lbl_vals]
#                 data = [i[1]  for i in lbl_vals]
#                 wedges, plt_labels, junk = plt.pie(data, labels=lbls, autopct='%1.1f%%')
#                 
#                 plt.show()
            

else:    
    #### --- arbitrary probabilities ------    
    for each_res in ALL_POSSIBLE_RESOLUTIONS:
        final_random_ctu_list[each_res] = {}
        for each_slice_type in SLICE_TYPES:
            final_random_ctu_list[each_res][each_slice_type] = []
            for each_ctu in xrange(NUM_CTU):
                pus_list = generate_PU_per_CTU(each_slice_type, each_res)
                
                #pprint.pprint(pus_list)
                #sys.exit()
                final_random_ctu_list[each_res][each_slice_type].append({
                                                                         'pu_list': pus_list,
                                                                         }) 
                                                                     
                print "-- done : ", each_res, each_slice_type, each_ctu

    

print "------------------------------------"
print "--pickle dump"
#pickle.dump(final_random_ctu_list, open( "../hevc_pregen_data_files/pregen_pus/hevc_generate_PU_per_CTU_%dctus.p" %NUM_CTU, "wb" ))
pickle.dump(final_random_ctu_list, open( "../hevc_pregen_data_files/pregen_pus/hevc_probmodel_generate_PU_per_CTU_%dctus.p" %NUM_CTU, "wb" ))
            
            




