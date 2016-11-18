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
import scipy.stats as stats

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# local imports
from SimParams import SimParams
import libApplicationModel.HEVCWorkloadParams as HEVCWLP


MAX_CTU_PIX = (64*64)
MAX_CTU_SIZE = 64
RESOLUTION = (720*1280)
NUM_CTUS = float(RESOLUTION)/float(MAX_CTU_PIX)
 
BLOCK_SIZES = [64,32,16,8,4]
BLK_PIXELS = [64*64, 32*32, 16*16, 8*8, 4*4]

BLK_PIX_MAPPING = {64*64:64, 32*32:32, 16*16:16, 8*8:8, 4*4:4}


# exhaustive method
def find_all_permutations(total = 64*64):
                   
    all_permutations_intra = []
    all_permutations_inter = []
    
    px_list = [64*64, 32*32, 16*16, 8*8, 4*4]
    
    total_i = int(float(total)/float(px_list[0]))
    total_j = int(float(total)/float(px_list[1]))
    total_k = int(float(total)/float(px_list[2]))
    total_m = int(float(total)/float(px_list[3]))
    
    ## for intra ##    
    for i in xrange(total_i):
        for j in xrange(total_j):
            for k in xrange(total_k):
                for m in xrange(total_m):                    
                    current_sum = (px_list[0]*i) + \
                                    (px_list[1]*j) + \
                                    (px_list[2]*k) + \
                                    (px_list[3]*m)
                    
                    perm = [px_list[0]/32]*i + [px_list[1]/16]*j + [px_list[2]/8]*k + [px_list[3]/4]*m
                    
                    if current_sum == total:                        
                        all_permutations_intra.append(perm)
                        print "found perm (intra): ", len(all_permutations_intra), \
                                                    float(i)/float(total_i), \
                                                    float(j)/float(total_j), \
                                                    float(k)/float(total_k), \
                                                    float(m)/float(total_m)
                                                        
    ## for inter ##
    px_list = [64*64, 32*32, 16*16, 8*8]
    for i in xrange(total_i):
        for j in xrange(total_j):
            for k in xrange(total_k):                    
                    current_sum = (px_list[0]*i) + \
                                    (px_list[1]*j) + \
                                    (px_list[2]*k)
                    
                    perm = [px_list[0]/32]*i + [px_list[1]/16]*j + [px_list[2]/8]*k
                    
                    if current_sum == total:                        
                        all_permutations_inter.append(perm)
                        print "found perm (inter): ", len(all_permutations_inter), \
                                                    float(i)/float(total_i), \
                                                    float(j)/float(total_j), \
                                                    float(k)/float(total_k)
                                                    
                        
    return (all_permutations_intra, all_permutations_inter)


def genCUList_Probabilistic(block_size_weights, total_pixels, stype):
    #print "genCUList_Probabilistic : ", stype
    cumsum_cus = 0    
    sum_weights = np.sum(block_size_weights)
    if sum_weights != 1.0: # normalise such that sum is 1.0
        for ix, w in enumerate(block_size_weights):
            block_size_weights[ix] = float(block_size_weights[ix])/sum_weights
    else:
        pass # all normalised
    
    # if we want to pregen #
    pregen_varied_block_size_weights = varyProbabilities_NormalDist(block_size_weights, sigma=0.05)
    pregen_current_cu = np.random.choice(BLK_PIXELS, p=pregen_varied_block_size_weights, size=10000)
    random.shuffle(pregen_current_cu)
    pregen_current_cu = itertools.cycle(pregen_current_cu)
        
    i = 0
    all_possible_cu_pixels = []
    all_possible_cu_blks_dict = {}
    all_possible_cu_blks_list = []
    while(cumsum_cus < total_pixels):        
        #varied_block_size_weights = varyProbabilities_NormalDist(block_size_weights, sigma=0.05)
        #current_cu = np.random.choice(BLK_PIXELS, p=varied_block_size_weights, size=1)
        varied_block_size_weights = pregen_varied_block_size_weights
        current_cu = pregen_current_cu.next()
        
        if cumsum_cus + current_cu <= total_pixels:
            cumsum_cus += current_cu
            all_possible_cu_pixels.append(current_cu)            
            
            blk_size = BLK_PIX_MAPPING[int(current_cu)]
            all_possible_cu_blks_list.append(blk_size)
            if blk_size in all_possible_cu_blks_dict:
                all_possible_cu_blks_dict[blk_size] += 1
            else:
                all_possible_cu_blks_dict[blk_size] = 1
            
        else:
            pass

        i+=1
        
        if (i % 1000000) == 0: # reset random block size generation
            print  "WARNING..Looping :", i, cumsum_cus, total_pixels, varied_block_size_weights
            pregen_varied_block_size_weights = varyProbabilities_NormalDist(block_size_weights, sigma=0.05)
            pregen_current_cu = np.random.choice(BLK_PIXELS, p=pregen_varied_block_size_weights, size=10000)
            random.shuffle(pregen_current_cu)
            pregen_current_cu = itertools.cycle(pregen_current_cu)            
            varied_block_size_weights = pregen_varied_block_size_weights
            i = 0
        else:
            pass
            
            
        
     
    #total_pixels = int(NUM_CTUS)*(MAX_CTU_PIX)
    assert(total_pixels == np.sum(all_possible_cu_pixels))
    
    return all_possible_cu_blks_dict, all_possible_cu_blks_list



def groupCUsIntoCTUs(cu_dict, cu_list, slice_type, param_num_ctus=int(NUM_CTUS)):
    #print "groupCUsIntoCTUs : Enter"
    cu_dict_copy = copy.copy(cu_dict)
    
    # only the non-max CUs need to be sorted
    num_ctus = param_num_ctus
    #non_max_num_ctus = num_ctus - cu_dict_copy[MAX_CTU_SIZE]
    non_max_num_ctus = num_ctus
    
    all_ctu_sums = {n:0 for n in range(non_max_num_ctus)}
    all_ctu_content = {n:[] for n in range(non_max_num_ctus)}
    
    sorted_blks = sorted(cu_list, reverse=True)
    
    # put sorted CUs into bins
    ctu_id = 0
    for each_blk in sorted_blks:
        if all_ctu_sums[ctu_id] + (each_blk*each_blk) <=  MAX_CTU_PIX:
            all_ctu_content[ctu_id].append(each_blk)
            all_ctu_sums[ctu_id] += (each_blk*each_blk)
            cu_dict_copy[each_blk] -= 1
        else:
            ctu_id += 1 # new bin
            all_ctu_content[ctu_id].append(each_blk)
            all_ctu_sums[ctu_id] += (each_blk*each_blk)
            
            cu_dict_copy[each_blk] -= 1
    
    # swap items around
    SWAP_32_16_COUNT = HEVCWLP.HEVCWLPARAMS_CTU_SWAP_32_16_COUNT
    SWAP_32_8_COUNT = HEVCWLP.HEVCWLPARAMS_CTU_SWAP_32_8_COUNT
    SWAP_32_4_COUNT = HEVCWLP.HEVCWLPARAMS_CTU_SWAP_32_4_COUNT
    SWAP_16_8_COUNT = HEVCWLP.HEVCWLPARAMS_CTU_SWAP_16_8_COUNT
    SWAP_8_4_COUNT = HEVCWLP.HEVCWLPARAMS_CTU_SWAP_8_4_COUNT    
    
    all_ctu_content = _swap_CUs(all_ctu_content, slice_type, SWAP_32_16_COUNT, SWAP_32_4_COUNT, 
                                SWAP_32_8_COUNT, SWAP_16_8_COUNT, SWAP_8_4_COUNT )
    
    
    # checks
    assert([_get_cu_sum(x) for x in all_ctu_content.values()].count(MAX_CTU_PIX) >= param_num_ctus-1), [_get_cu_sum(x) for x in all_ctu_content.values()]    
    #assert(all(_get_cu_sum(i) == MAX_CTU_PIX for i in all_ctu_content.values())), [_get_cu_sum(x) for x in all_ctu_content.values()]
    assert(all(i == 0 for i in cu_dict_copy.values()))
    assert(all(i != [] for i in all_ctu_content.values()))
        
    return all_ctu_content

def _get_cu_sum(cus):
    return np.sum([c*c for c in cus])


    
        
def _swap_CUs(all_ctu_content, slice_type, SWAP_32_16_COUNT, SWAP_32_8_COUNT, SWAP_32_4_COUNT, SWAP_16_8_COUNT, SWAP_8_4_COUNT):
    # randomly move contents in CTUs around
    
    ## swap 32,16 ##
    for i in xrange(SWAP_32_16_COUNT):     
        ctus_with_32 = [k for k,v in all_ctu_content.iteritems() if v.count(32)>0]
        ctus_with_16 = [k for k,v in all_ctu_content.iteritems() if v.count(16)>3]
        if ctus_with_32 == [] or ctus_with_16 ==[]: 
            break;
        else:
            ctu_with_32 = np.random.choice(ctus_with_32)
            ctu_with_16 = np.random.choice(ctus_with_16)        
            all_ctu_content[ctu_with_32].remove(32)
            all_ctu_content[ctu_with_16].append(32)
            for j in xrange(4):
                all_ctu_content[ctu_with_16].remove(16)
                all_ctu_content[ctu_with_32].append(16)        
    
    ## swap 32,8 ##
    for i in xrange(SWAP_32_8_COUNT):  
        ctus_with_32 = [k for k,v in all_ctu_content.iteritems() if v.count(32)>0]
        ctus_with_8 = [k for k,v in all_ctu_content.iteritems() if v.count(8)>15]
        if ctus_with_32 == [] or ctus_with_8 ==[]: 
            break;
        else:        
            ctu_with_32 = np.random.choice(ctus_with_32)
            ctu_with_8 = np.random.choice(ctus_with_8)    
            all_ctu_content[ctu_with_32].remove(32)
            all_ctu_content[ctu_with_8].append(32)
            for j in xrange(16):
                all_ctu_content[ctu_with_8].remove(8)
                all_ctu_content[ctu_with_32].append(8)
            
    ## swap 32,4 ##
    if slice_type == "Intra":
        for i in xrange(SWAP_32_4_COUNT):
            ctus_with_32 = [k for k,v in all_ctu_content.iteritems() if v.count(32)>0]
            ctus_with_4 = [k for k,v in all_ctu_content.iteritems() if v.count(4)>63]        
            if ctus_with_32 == [] or ctus_with_4 ==[]: 
                break;
            else:             
                ctu_with_32 = np.random.choice(ctus_with_32)
                ctu_with_4 = np.random.choice(ctus_with_4)                   
                all_ctu_content[ctu_with_32].remove(32)
                all_ctu_content[ctu_with_4].append(32)
                for j in xrange(64):
                    all_ctu_content[ctu_with_4].remove(4)
                    all_ctu_content[ctu_with_32].append(4)
        
    ## swap 16,8 ##
    for i in xrange(SWAP_16_8_COUNT):     
        ctus_with_16 = [k for k,v in all_ctu_content.iteritems() if v.count(16)>0]
        ctus_with_8 = [k for k,v in all_ctu_content.iteritems() if v.count(8)>3]        
        if ctus_with_16 == [] or ctus_with_8 ==[]: 
            break;
        else:
            ctu_with_16 = np.random.choice(ctus_with_16)
            ctu_with_8 = np.random.choice(ctus_with_8)        
            all_ctu_content[ctu_with_16].remove(16)
            all_ctu_content[ctu_with_8].append(16)
            for j in xrange(4):
                all_ctu_content[ctu_with_8].remove(8)
                all_ctu_content[ctu_with_16].append(8)        
            
    
    ## swap 8,4 ##
    if slice_type == "Intra":
        for i in xrange(SWAP_8_4_COUNT):
            ctus_with_8 = [k for k,v in all_ctu_content.iteritems() if v.count(8)>0]
            ctus_with_4 = [k for k,v in all_ctu_content.iteritems() if v.count(4)>3]            
            if ctus_with_8 == [] or ctus_with_4 ==[]: 
                break;
            else:             
                ctu_with_8 = np.random.choice(ctus_with_8)
                ctu_with_4 = np.random.choice(ctus_with_4)                
                all_ctu_content[ctu_with_8].remove(8)
                all_ctu_content[ctu_with_4].append(8)
                for j in xrange(4):
                    all_ctu_content[ctu_with_4].remove(4)
                    all_ctu_content[ctu_with_8].append(4)                
            
        
    return all_ctu_content


# MAIN function to be called by outside code
def getCTUsForVideo(mov_type, slice_type, total_video_pixels=RESOLUTION, force_ctu_size=False):
    #print "getCTUsForVideo : Enter"    
    #total_pixels = int(NUM_CTUS)*(MAX_CTU_PIX)
    
    total_pixels = total_video_pixels
    
    result_dict, result_list = genCUList_Probabilistic(list(HEVCWLP.HEVCWLPARAMS_CU_SIZE_PROBABILITIES[mov_type][slice_type]), 
                                                       total_pixels, 
                                                       slice_type)    
    
    all_ctu_content = groupCUsIntoCTUs(result_dict, result_list, 
                                       slice_type, 
                                       param_num_ctus= int(np.ceil(float(total_video_pixels)/float(MAX_CTU_PIX)))) # returns dict    
    
    
    # make sure all CTUs we are returning are of the size MAX_CTU
    if force_ctu_size==True:
        all_ctu_content = dict((k, v) for k, v in all_ctu_content.iteritems() if _get_cu_sum(v)==MAX_CTU_PIX)
    
    return all_ctu_content




# for a given probability list we vary each value according to normal dist
# where, mu = item in list, sigma = given 
def varyProbabilities_NormalDist(probs_list, sigma=0.05):    
    lower=0.0
    upper=1.0
    
    new_probs_list =  []
    for each_p in probs_list:
        if each_p > 0:
            mu = each_p        
            truncnorm_obj = stats.truncnorm((lower - mu) / sigma, (upper - mu) / sigma, loc=mu, scale=sigma)
            new_p = truncnorm_obj.rvs(1)[0]
            new_probs_list.append(new_p)
        else:
            new_probs_list.append(each_p) # if the value is zero, then we don't change it
    
    # we need to normalise the new probs to 1 before returning
    new_probs_list_nparr = np.array(new_probs_list)
    new_probs_list_nparr = new_probs_list_nparr/np.sum(new_probs_list_nparr)
      
    return new_probs_list_nparr
        




##############################
# Testing section
##############################

# 
# for i in xrange(10):
#     getCTUsForVideo('DOC', "Inter")

     
# f = plt.figure()  
# pprint.pprint(size_types)                  
# lbl_vals = [(k,v)  for k,v in size_types.iteritems()]
# lbls = [i[0]  for i in lbl_vals]
# data = [i[1]  for i in lbl_vals]
# wedges, plt_labels, junk = plt.pie(data, labels=lbls, autopct='%1.1f%%')
#  
# plt.show()






