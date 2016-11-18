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



class HEVCDAGSplitter():
    
    def __init__(self, DAGnx):
        ':type self.DAGnx: DiGraph'        
        self.DAGnx = DAGnx
        
        # splitted task graph with weights
        self.DAGnx_splitted = None
    
    
    @staticmethod
    def nxLabel2Frame(nxDGLabel):        
        if len(nxDGLabel) < 2: 
            print "AdaptiveGopGen_v2:: nxLabel2Frame: error ", nxDGLabel        
        # first char is the type
        ftype = nxDGLabel[0]
        fix = int(nxDGLabel[1:])        
        result = { 'ftype': ftype, 'fix': fix}        
        return result
    
    def _get_fr_node_col(self, fr_type):
        if fr_type == "I":
            col = "#FFB2B2"
        elif fr_type == "P":
            col = "#B2FFB2"
        elif fr_type == "B":
            col = "#B2B2FF"
        elif fr_type == "b":
            col = "#B2B2FF"
            
        return col
    
    def splitDAG2Tiles(self, num_tiles):
        # create empty graph
        DG = nx.DiGraph()
        
        # create sub task nodes
        for each_node in self.DAGnx.nodes():
            if 'weight' in each_node:
                w = each_node['weight']
            else:
                w = 0.0
            for t in range(num_tiles):
                node_label = each_node + "_" + str(t)
                DG.add_node(node_label, weight=float(w)/float(num_tiles))
        
        # colorize nodes
        ftype = self.nxLabel2Frame(each_node)['ftype']
        DG.node[each_node]['fillcolor']=self._get_fr_node_col(ftype)
        DG.node[each_node]['style']='filled'
        DG.node[each_node]['fontsize']='30'
        DG.node[each_node]['arrowsize']="10.0"
        if 'weight' in DG.node[each_node]:
            DG.node[each_node]['node_size']=(DG.node[each_node]['weight']*2)+300 # default 300                
        
        # graph-level properties
        DG.graph['graph']={'rankdir':'LR'}
        
                
        # create subtask graph edges
        for each_edge in self.DAGnx.edges():
            p = each_edge[0]
            c = each_edge[1]
            w = each_edge[2]['weight']
             
            for each_pp_id in range(num_tiles):
                for each_cc_id in range(num_tiles):
                    pp_lbl = p + "_" + str(each_pp_id)
                    cc_lbl = c + "_" + str(each_cc_id)
                    ww = float(w)/float(num_tiles**2)
                    DG.add_edge(pp_lbl, cc_lbl, weight=ww)
        
        self.DAGnx_splitted = DG
        
    
    
    