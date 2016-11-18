import pprint
import sys, os
import math, random
import numpy as np
import copy
import csv
import bisect
import json
import itertools
from operator import itemgetter
import networkx as nx

from collections import Counter, Sequence
from collections import OrderedDict

import matplotlib
import matplotlib.pyplot as plt
#plt.style.use('ggplot')

from scipy.stats import exponweib
from scipy.stats import rv_discrete

# local imports
import HEVCWorkloadParams
from AdaptiveGoPGenerator_v2 import AdaptiveGoPGenerator_v2


###################################
# Testbench class
###################################
class AdaptiveGoPGenTestBench():

    def __init__(self):
        i=1
    
    # create a bunch of random GoPs
    def performTests_v1(self):        
        # N is highly dependent on nBmax
        # (N-1) % (nBmax+1) == 0. else not valid        
        nBmax = np.random.choice(HEVCWorkloadParams.HEVCWLPARAMS_CONTIG_BFRAMES_PROBS.keys()); 
        N=26; # 
        numPframerefs = 1
        numBframerefs = (1,1) # per direction
        test_num_gops = 10
        
        correct_graphs = []
        correct_nx_graphs = []
        correct_nx_graph_with_weights = []
        incorrect_graphs = []
        gops_generated =0
        for i in range(test_num_gops):
            AGG = AdaptiveGoPGenerator_v2(nBmax, N, 
                                          numPframerefs, numBframerefs,
                                          movieType=HEVCWorkloadParams.HEVCWLPARAMS_TYPES_OF_VIDEOS[1]
                                          )
            
            AGG.verifyAndRecreateGoP()
            AGG.applyWeights(10, 20, 25, 30)
        
            if AGG not in correct_graphs:
                correct_graphs.append(AGG)                
                # add to networkx
                #DG = nx.DiGraph()
                #DG = AGG.createGraph(DG)
                correct_nx_graphs.append(AGG.networkxDG)
                correct_nx_graph_with_weights.append(AGG.networkxDG_weighted)
                print "-- AGG added"
        
        print "finished creating - now dumping pngs"
        
        for ix, each_dg in enumerate(correct_nx_graphs):
            AdaptiveGoPGenerator_v2.output_png(each_dg, "_"+str(ix)+"_", 
                                               dir = "C:/Users/Rosh/Documents/EngD/Work/VideoProfiling/test_gops/", 
                                               format="png")
        
        for ix, each_dg in enumerate(correct_nx_graph_with_weights):
            AdaptiveGoPGenerator_v2.output_png(each_dg, "_"+str(ix)+"_", 
                                               dir = "C:/Users/Rosh/Documents/EngD/Work/VideoProfiling/test_gops_with_weights/", 
                                               format="png")
     
    
    # test task graph splitting and applying weights    
    def performTests_v2a(self):
        nBmax = np.random.choice(HEVCWorkloadParams.HEVCWLPARAMS_CONTIG_BFRAMES_PROBS.keys()); 
        N=21; # 
        numPframerefs = 1
        numBframerefs = (1,1) # per direction
        test_num_gops = 10        
        num_tiles = 2
        correct_graphs = []
        
        correct_nx_graphs = []
        correct_nx_graph_with_weights = []      
        correct_nx_split_graph = []
          
        for i in range(test_num_gops):
            AGG = AdaptiveGoPGenerator_v2(nBmax, N, 
                                          numPframerefs, numBframerefs,
                                          movieType=HEVCWorkloadParams.HEVCWLPARAMS_TYPES_OF_VIDEOS[1]
                                          )
            
            AGG.verifyAndRecreateGoP()
            correct_nx_graphs.append(AGG.networkxDG)
            
            if AGG not in correct_graphs:
                correct_graphs.append(AGG)
                AGG.splitDAG2TilesUnweighted(num_tiles, use_tex_labeling=True)
                correct_nx_split_graph.append(AGG.networkxDG_split)                
                print "-- AGG added"
        
        print "finished creating - now dumping pngs"
        for ix, each_dg in enumerate(correct_nx_graphs):
            AdaptiveGoPGenerator_v2.output_png(each_dg, "_"+str(ix)+"_", 
                                               dir = "C:/Users/Rosh/Documents/EngD/Work/VideoProfiling/test_gops/", 
                                               format="png")
        
        
        for ix, each_dg in enumerate(correct_nx_split_graph):
            AdaptiveGoPGenerator_v2.output_png(each_dg, "_"+str(ix)+"_", 
                                               dir = "C:/Users/Rosh/Documents/EngD/Work/VideoProfiling/test_gops_split/", 
                                               format="png")
    
    
    
    
    # test task graph splitting and applying weights    
    def performTests_v2b(self):
        nBmax = np.random.choice(HEVCWorkloadParams.HEVCWLPARAMS_CONTIG_BFRAMES_PROBS.keys()); 
        N=11; # 
        numPframerefs = 1
        numBframerefs = (1,1) # per direction
        test_num_gops = 10        
        num_tiles = 2
        correct_graphs = []
        
        correct_nx_graph_with_weights = []      
        correct_nx_split_graph = []
          
        for i in range(test_num_gops):
            AGG = AdaptiveGoPGenerator_v2(nBmax, N, 
                                          numPframerefs, numBframerefs,
                                          movieType=HEVCWorkloadParams.HEVCWLPARAMS_TYPES_OF_VIDEOS[1]
                                          )
            
            AGG.verifyAndRecreateGoP()
            AGG.applyWeights(10, 20, 25, 30)           
            
            if AGG not in correct_graphs:
                correct_graphs.append(AGG)                
                correct_nx_graph_with_weights.append(AGG.networkxDG_weighted)
                AGG.splitDAG2Tiles(num_tiles)
                correct_nx_split_graph.append(AGG.networkxDG_weighted_split)                
                print "-- AGG added"
        
        print "finished creating - now dumping pngs"        
        for ix, each_dg in enumerate(correct_nx_graph_with_weights):
            AdaptiveGoPGenerator_v2.output_png(each_dg, "_"+str(ix)+"_", 
                                               dir = "C:/Users/Rosh/Documents/EngD/Work/VideoProfiling/test_gops_with_weights/", 
                                               format="png")
        
        for ix, each_dg in enumerate(correct_nx_split_graph):
            AdaptiveGoPGenerator_v2.output_png(each_dg, "_"+str(ix)+"_", 
                                               dir = "C:/Users/Rosh/Documents/EngD/Work/VideoProfiling/test_gops_split/", 
                                               format="png")
        
    
    # test merge nodes in split graph    
    def performTests_v3(self):        
        
        nBmax = np.random.choice(HEVCWorkloadParams.HEVCWLPARAMS_CONTIG_BFRAMES_PROBS.keys()); 
        N=11; # 
        numPframerefs = 1
        numBframerefs = (1,1) # per direction
        test_num_gops = 10        
        num_tiles = 2
        correct_graphs = []
        
        correct_nx_graph_with_weights = []      
        correct_nx_split_graph = []
        correct_nx_merged_graph = []
          
        for i in range(test_num_gops):
            AGG = AdaptiveGoPGenerator_v2(nBmax, N, 
                                          numPframerefs, numBframerefs,
                                          movieType=HEVCWorkloadParams.HEVCWLPARAMS_TYPES_OF_VIDEOS[1]
                                          )
            
            AGG.verifyAndRecreateGoP()
            AGG.applyWeights(10, 20, 25, 30)           
            
            if AGG not in correct_graphs:
                correct_graphs.append(AGG)                
                correct_nx_graph_with_weights.append(AGG.networkxDG_weighted)
                AGG.splitDAG2Tiles(num_tiles)
                correct_nx_split_graph.append(AGG.networkxDG_weighted_split)                
                print "-- AGG added"
        
        
        
        #### special merge test ####
        dg_id = 8
        nodes = ["P2_0", "P2_1"]
        new_node = "P2_0;P2_1"
        G = correct_nx_split_graph[dg_id].copy()
        attr_dict = {
                     'weight' : (nx.get_node_attributes(G, 'weight')['P2_0'] + 
                                 nx.get_node_attributes(G, 'weight')['P2_1'])
                     }
        G, mtt = AGG.merge_nodes(G, 
                        nodes, new_node, attr_dict)
        
        
        ############################
        
        
        print "finished creating - now dumping pngs"       
        # output graphs with weights 
        for ix, each_dg in enumerate(correct_nx_graph_with_weights):
            AdaptiveGoPGenerator_v2.output_png(each_dg, "_"+str(ix)+"_", 
                                               dir = "C:/Users/Rosh/Documents/EngD/Work/VideoProfiling/test_gops_with_weights/", 
                                               format="png")
        
        # output graphs with weights - after splitting
        for ix, each_dg in enumerate(correct_nx_split_graph):
            AdaptiveGoPGenerator_v2.output_png(each_dg, "_"+str(ix)+"_", 
                                               dir = "C:/Users/Rosh/Documents/EngD/Work/VideoProfiling/test_gops_split/", 
                                               format="png")
        
            
        # output graphs with weights - after splitting - after merging
        AdaptiveGoPGenerator_v2.output_png(G, "_"+str(8)+"_", 
                                               dir = "C:/Users/Rosh/Documents/EngD/Work/VideoProfiling/test_gop_merged/", 
                                               format="png")
            

np.random.seed(1234)
random.seed(1234)    
AGG_TB = AdaptiveGoPGenTestBench()

AGG_TB.performTests_v2a()
#AGG_TB.performTests_v2b()
#AGG_TB.performTests_v3()
