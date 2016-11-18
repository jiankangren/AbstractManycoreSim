import pprint
import sys
import math, random
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import scipy.stats
from matplotlib.colors import ListedColormap, NoNorm
from matplotlib import mlab
from itertools import cycle # for automatic markers

import matplotlib.cm as cm
from matplotlib.font_manager import FontProperties

import json


# group a gop sequence in to heirarchical B-fr groups
def getGroupedGop(gop_seq):
    individual_group = []
    all_groupings = []
    for ix, each_fr in enumerate(gop_seq):
        fr_lbl = each_fr + str(ix)
        if (each_fr == "I"): # start of first group
            individual_group.append(fr_lbl)
        
        ### P
        elif (each_fr == "P") and len(individual_group)==0: # other groups             
            individual_group.append(fr_lbl)
        
        elif (each_fr == "P") and len(individual_group)>1 and ix==(len(gop_seq)-1): # last P
            all_groupings.append(individual_group)
            all_groupings.append([fr_lbl])
        
        elif (each_fr == "P") and len(individual_group)==1 and ix==(len(gop_seq)-1): # last P and prev group was just P
            all_groupings.append(individual_group)
            all_groupings.append([fr_lbl])
        
        elif (each_fr == "P") and len(individual_group)>0: # other groups
            if ("P" in individual_group[-1]) and gop_seq[ix+1] != "B":
            #if (False):
                individual_group.append(fr_lbl)
            else:
                all_groupings.append(individual_group)
                individual_group = [] # reset
                individual_group.append(fr_lbl)
            
        
        ### B
        elif (each_fr == "B") and len(individual_group)>0 and ix==(len(gop_seq)-1): # last fr is a B
            individual_group.append(fr_lbl)
            all_groupings.append(individual_group)
            
        elif (each_fr == "B") and len(individual_group)>0: # other groups
            individual_group.append(fr_lbl)
            #print fr_lbl, individual_group
            
    
    assert(np.sum([len(f) for f in all_groupings]) == len(gop_seq)), "Error:: group_gop ! %s, %s" % (gop_seq, pprint.pformat(all_groupings, indent=4))
    
    # convert to dict (frlbl -> group_ix)
    fr_groupings_dict = {}
    for g, group in enumerate(all_groupings):
        for f, frames in enumerate(group):
            fr_groupings_dict[frames] = (g, group[0]) # set group ix and primary task of group
    
    
    return all_groupings, fr_groupings_dict
        
        
        
         


#############################
# MAIN
#############################
num    =  "012345678901234"
#GoP_seq = "IBBBBPBBPPBBPBBB"
#GoP_seq = "IBPPBBBBPBPBBBBP"
GoP_seq = "IBBBBPBBPPBBPPPPPPPBBPB"

print num
print GoP_seq

pprint.pprint( getGroupedGop(GoP_seq)[0] )