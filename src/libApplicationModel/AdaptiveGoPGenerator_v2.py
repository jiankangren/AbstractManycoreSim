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
import operator
import time, timeit

from collections import Counter, Sequence
from collections import OrderedDict

import matplotlib
import matplotlib.pyplot as plt
#plt.style.use('ggplot')

from scipy.stats import exponweib
from scipy.stats import rv_discrete

# local imports
import HEVCWorkloadParams



class AdaptiveGoPGenerator_v2():

    def __init__(self, nBmax, N, numPFrameRefs, numBFrameRefs, 
                 movieType = HEVCWorkloadParams.HEVCWLPARAMS_TYPES_OF_VIDEOS[0], 
                 pregen_hevc_CTUs = None):
        self.nBmax = nBmax  # maximum number of consecutive B-frames
        self.N = N  # GoP length    
        print self.N  
        self.numPFrameRefs = numPFrameRefs # maximum number of P-frame references
        self.numBFrameRefs = numBFrameRefs # maximum number of B-frame references
        self.movieType = movieType
        
        self.nP_expweib_params = HEVCWorkloadParams.HEVCWLPARAMS_GOP_PB_NUM_PARAMS[movieType] # a,c,scale,loc
        
        ### calculate ###
        self.nPmax = (N-1)
        
        if (N-1)%(nBmax + 1) != 0:
            sys.exit("Error: generateGOPSequence: Error :: (N-1)%(nBmax + 1) != 0")
        else:        
            self.nPmin = int(float(N-1)/float(nBmax + 1)) # +1 because of P-frame
        
        # find nP,nB
        np_range = np.arange(self.nPmin, self.nPmax+1)
        #print np_range
        self.nP = self._get_nP_using_fitted_distrib(np_range)        
        self.nB = (N-1) - self.nP
        
        print "P,B :", self.nP, self.nB 
        
        self.nBPyramMax = int(float(self.nB)/float(self.nBmax))
        self.nBPyramSizes = np.arange(1, self.nBmax+1)
        
        # we populate these later        
        self.gopSeq = None
        self.generalisedBfrlocs = None
        self.numTemporalLevels = None
        self.framesTemporalGroupings = None
        self.frameLevelRefs = None
        
        # network x structure
        ':type networkxDG: DiGraph'
        ':type networkxDG_weighted: DiGraph'
        self.networkxDG = None
        self.networkxDG_weighted = None
        self.networkxDG_weighted_split = None
        self.networkxDG_split = None # unweighted
        
        # related to dependencies
        self.gop_level_dep = {}
        self.task_level_dep = {}        
        self.which_task_needs_current_task = {}
        self.my_closest_children = {}
        self.my_closest_parent = {}
        self.which_frame_needs_current_frame = {}
        self.non_dep_frames = {}        
        self.possible_interfering_frames = {}        
        
    
    # getters/setters
    def get_nBmax(self):
        return self.nBmax
    def get_N(self):
        return self.N
    def get_numPFrameRefs(self):          
        return self.numPFrameRefs
    def get_numBFrameRefs(self):
        return self.numBFrameRefs
    def get_gopSeq(self):
        return self.gopSeq    
    def get_numTemporalLevels(self):    
        return self.numTemporalLevels
    def get_framesTemporalGroupings(self):
        return self.framesTemporalGroupings
    def get_frameLevelRefs(self):
        return self.frameLevelRefs
    def get_networkxDG(self):        
        return self.networkxDG
    def get_networkxDG_weighted(self):        
        return self.networkxDG_weighted
    def get_networkxDG_weighted_split(self):        
        return self.networkxDG_weighted_split    
    def get_gop_level_dep(self):        
        return self.gop_level_dep
    def get_task_level_dep(self):
        return self.task_level_dep
    def get_which_task_needs_current_task(self):        
        return self.which_task_needs_current_task
    def get_my_closest_children(self):
        return self.my_closest_children
    def get_my_closest_parent(self):
        return self.my_closest_parent
    def get_which_frame_needs_current_frame(self):
        return self.which_frame_needs_current_frame
    def get_non_dep_frames(self):
        return self.non_dep_frames
    def get_possible_interfering_frames(self):        
        return self.possible_interfering_frames
    
    
    
    
    
    def printGraph(self):
        print "Edges of graph:"
        pprint.pprint(self.networkxDG.edges())
    
    
    # create the gop 
    def createGoP(self):
        self.gopSeq, self.generalisedBfrlocs = self.generateGOPSequence(self.N)
        
        #print self.gopSeq, len(self.gopSeq) 
        #print self.generalisedBfrlocs
        self.frameLevelRefs = self.constructFrameReferences(self.gopSeq, self.generalisedBfrlocs,
                                                             self.numPFrameRefs, 
                                                             self.numBFrameRefs[0], self.numBFrameRefs[1])
     
        #pprint.pprint(self.frameLevelRefs)
        
    
    # this iterates until a gop struct with valid deps have been found 
    # issue is with getting cyclic dependencies
    def verifyAndRecreateGoP(self):
        valid=False
        # iterate till a valid gop is found
        while(valid==False):
            self.createGoP()
            self.createNetworkXDG()
            
            check_cycles = False
            check_numNodesWithoutRefs = False
            check_ZeroPreds = False
            
            if (len(list(nx.simple_cycles(self.networkxDG))) == 0):
                check_cycles = True
            else:
                print "check_cycles: fail!"
                pprint.pprint(list(nx.simple_cycles(self.networkxDG)))
                sys.exit()
            
            if (self.numNodesWithoutRefs()==0):
                check_numNodesWithoutRefs = True
            else:
                print "check_numNodesWithoutRefs: fail!"
                print self.numNodesWithoutRefs()
                sys.exit()
            
            if self.checkZeroPredecessors(self.networkxDG)==0:
                check_ZeroPreds = True
            else:
                print "check_ZeroPreds: fail!"
                print self.checkZeroPredecessors(self.networkxDG)
                sys.exit()            
            
            # check and set
            if ((check_cycles == True) and (check_numNodesWithoutRefs == True) and (check_ZeroPreds == True)):
                valid=True
            else:
                valid=False
            
                
        
    def initialiseInternalStructures(self, gop_task_ids):
        #print gop_task_ids
        self.calc_GopDependencies(gop_task_ids)
    
    
    def constructFrameReferences(self, gopSeq, genBfrPos, maxPframeRefs, maxBframeRefs_forwdir, maxBframeRefs_backdir):
        
        assert (gopSeq[0]=="I")
        
        # P-frame references
        # references == parent dependencies        
        parent_frame_refs = OrderedDict() 
        print gopSeq
        print genBfrPos       
        
        for frix, fr in enumerate(gopSeq):
                
                selected_fwd_ref_frames = None
                selected_bwd_ref_frames = None
                
                ########## I-FRAMES ############
                if fr == 'I':
                    # no dependencies for I-frames
                    selected_ref_frames = {'gop_ix' : frix,
                                           'fwd_pred' : selected_fwd_ref_frames,
                                           'bwd_pred' : selected_bwd_ref_frames
                                           }
                                            
                    
                ########## P-FRAMES ############
                elif fr == 'P':
                    # for P-frames we get refer to the previous I or P frame
                    selected_fwd_ref_frames = []
                    for j in range(self.numBFrameRefs[0]): # for multiple refs
                        possible_ref_frixs = [i for i, f in enumerate(gopSeq)
                                              if f != "B" and i < frix
                                              ]                    
                        selected_fwd_ref_frix = np.max(possible_ref_frixs)                    
                        selected_fwd_ref_frames.append({
                                                          'frix': selected_fwd_ref_frix,
                                                          'fr' : gopSeq[selected_fwd_ref_frix],
                                                          'pyramid_id' : None                                                              
                                                          })
                                                       
                    
                    selected_ref_frames = {'gop_ix' : frix,
                                           'fwd_pred' : selected_fwd_ref_frames,
                                           'bwd_pred' : None
                                           }
                    
                
                ########## B-FRAMES ############
                elif fr == 'B':
                    
                    selected_fwd_ref_frames = []
                    selected_bwd_ref_frames = []
                    
                    # get the frames in the heirarchical group
                    IorP_frix_behind = np.max([i for i, f in enumerate(gopSeq) if f in ["I", "P"] and i<frix])
                    IorP_frix_front = np.min([i for i, f in enumerate(gopSeq) if f in ["I", "P"] and i>frix])
                    fr_ixs_in_pyram = np.arange(IorP_frix_behind, IorP_frix_front+1)
                    fr_in_pyram = [gopSeq[i] for i in fr_ixs_in_pyram]
                    
                    #print frix, fr, fr_ixs_in_pyram, fr_in_pyram, IorP_frix_behind, IorP_frix_front
                    
                    #### for fwd references ###
                    for j in range(self.numBFrameRefs[0]): # for multiple refs
                        possible_fwd_ref_dist = [np.abs(frix-i) for i, f in enumerate(gopSeq)
                                                   if ((i in self.generalisedBfrlocs) or (f in ["I", "P"]))
                                                   and (i<frix)
                                                   and np.abs(frix-i)<self.nBmax
                                                   and i in fr_ixs_in_pyram                                               
                                                  ]
                        
                        # if available refs equal to max refs, then take all available refs
                        if self.numBFrameRefs[0]<= len(possible_fwd_ref_dist):
                            selected_fwd_ref_frames = [{
                                                          'frix': frix-rd,
                                                          'fr' : gopSeq[frix-rd],
                                                          'pyramid_id' : None                                                              
                                                          } for rd in possible_fwd_ref_dist]
                            break;
                        else:
                            #print "possible_fwd_ref_dist : ", possible_fwd_ref_dist
                            assert len(possible_fwd_ref_dist) > 0
    #                         selected_ref_dist_fwd = self.getBfrRefDist_FromProbDist(None, None, self.movieType, 
    #                                                                                 fixed_rfdists = possible_fwd_ref_dist)
                            selected_ref_dist_fwd = self.getBfrRefDist_FromProbDist_fwdbwdrf1(None, None, self.movieType, 
                                                                                    fixed_rfdists = possible_fwd_ref_dist)
                            selected_fwd_ref_frix = frix-selected_ref_dist_fwd
                            selected_fwd_ref_frames.append({
                                                              'frix': selected_fwd_ref_frix,
                                                              'fr' : gopSeq[selected_fwd_ref_frix],
                                                              'pyramid_id' : None                                                              
                                                              })                                                       
                        
                    ### for bwd references ###
                    for j in range(self.numBFrameRefs[1]): # for multiple refs
                        possible_bwd_ref_dist = [np.abs(frix-i) for i, f in enumerate(gopSeq)
                                                   if ((i in self.generalisedBfrlocs) or (f in ["I", "P"]))
                                                   and (i>frix)
                                                   and np.abs(frix-i)<self.nBmax  
                                                   and i in fr_ixs_in_pyram                                             
                                                  ]
                        
                        if self.numBFrameRefs[1]<= len(possible_bwd_ref_dist):
                            selected_bwd_ref_frames = [{
                                                          'frix': frix+rd,
                                                          'fr' : gopSeq[frix+rd],
                                                          'pyramid_id' : None                                                              
                                                          } for rd in possible_bwd_ref_dist]
                            break;
                        else:
                            #print "possible_bwd_ref_dist : ", possible_bwd_ref_dist
                            assert len(possible_bwd_ref_dist) > 0
    #                         selected_ref_dist_bwd = self.getBfrRefDist_FromProbDist(None, None, self.movieType, 
    #                                                                                 fixed_rfdists = possible_bwd_ref_dist)
                            selected_ref_dist_bwd = self.getBfrRefDist_FromProbDist_fwdbwdrf1(None, None, self.movieType, 
                                                                                    fixed_rfdists = possible_bwd_ref_dist)
                            selected_bwd_ref_frix = frix+selected_ref_dist_bwd
                            selected_bwd_ref_frames.append({
                                                              'frix': selected_bwd_ref_frix,
                                                              'fr' : gopSeq[selected_bwd_ref_frix],
                                                              'pyramid_id' : None                                                              
                                                              })
                    
                    #print possible_fwd_ref_dist, selected_ref_dist_fwd,  possible_bwd_ref_dist, selected_ref_dist_bwd
                    
                    ## save both dir refs
                    selected_ref_frames = {'gop_ix' : frix,
                                           'fwd_pred' : selected_fwd_ref_frames,
                                           'bwd_pred' : selected_bwd_ref_frames
                                           } 
                    
                    #pprint.pprint(selected_ref_frames)
                       
                parent_frame_refs[fr + str(frix)] = selected_ref_frames        
        return parent_frame_refs
    
    
    # use polynomial prob dist to get ref distance
    def getBfrRefDist_FromProbDist(self, min_ref_dist, max_ref_dist, mov_type, fixed_rfdists = None):        
        if fixed_rfdists == None:
            possible_ref_fr_dist = np.arange(min_ref_dist,max_ref_dist+1)
        else:
            possible_ref_fr_dist = fixed_rfdists
        
        
        rfdist_probabilities = [HEVCWorkloadParams.HEVCWLPARAMS_REFDIST_PARAMS(x, mov_type) for x in possible_ref_fr_dist]        
        distrib = rv_discrete(values=(possible_ref_fr_dist, rfdist_probabilities))
        refdist = distrib.rvs(size=1)[0]
        
        return refdist
        
        
    # use polynomial prob dist to get ref distance
    def getBfrRefDist_FromProbDist_fwdbwdrf1(self, min_ref_dist, max_ref_dist, mov_type, fixed_rfdists = None):        
        if fixed_rfdists == None:
            possible_ref_fr_dist = np.arange(min_ref_dist,max_ref_dist+1)
        else:
            possible_ref_fr_dist = fixed_rfdists
        
        
        #print mov_type, possible_ref_fr_dist
        #print HEVCWorkloadParams.HEVCWLPARAMS_REFDIST__FWD1_BWD1_RATIOS.keys()
        rfdist_probabilities = [HEVCWorkloadParams.HEVCWLPARAMS_REFDIST__FWD1_BWD1_RATIOS[mov_type][int(p-1)] for p in possible_ref_fr_dist]
        distrib = rv_discrete(values=(possible_ref_fr_dist, rfdist_probabilities))
        refdist = distrib.rvs(size=1)[0]
        
        #print "possible_ref_fr_dist :", possible_ref_fr_dist, refdist
        
        return refdist
        
        
    
    # 1-D list
    def getPFrameIxs(self, gopSeq):
        result = []
        for each_fr_ix, each_fr in enumerate(gopSeq):
            if (each_fr == "P"):
                result.append(each_fr_ix)
        return result
    
    # 2-D list
    def getBFrameIxs(self, gopSeq):
        result = []
        subBfrIxs = []
        for each_fr_ix, each_fr in enumerate(gopSeq):
            if(each_fr=='B'):
                subBfrIxs.append(each_fr_ix)
            else:
                if len(subBfrIxs) >0:
                    result.append(subBfrIxs)
                    subBfrIxs = []
        
        # save lastly gathered bframes
        if len(subBfrIxs)>0:
            result.append(subBfrIxs)
        
        return result
                
        
    # nBMax = distance between consecutive P-frames
    # N = (GopSize)
    def generateGOPSequence(self, N, ClosedGop=True):        
        p_pos = np.arange(1,self.nP+1)
        
#         print N
#         print self.nBmax
#         print self.nP, self.nB
#         print self.nBPyramSizes
#         print p_pos
        
        # intialise list
        contig_B_frames = {}
        for i in p_pos:
            contig_B_frames[i]=0
        
        print self.nBmax, self.movieType
        # find groups of contiguous B-frames 
#         while(np.sum(contig_B_frames.values()) < self.nB):
#             pos = np.random.choice(p_pos)
#             numBframes = np.random.choice(self.nBPyramSizes, 
#                                           p=HEVCWorkloadParams.HEVCWLPARAMS_CONTIG_BFRAMES_PROBS[self.nBmax][self.movieType])
#             
#             if (((contig_B_frames[pos]) + numBframes) <= self.nBmax):
#                 if (np.sum(contig_B_frames.values())+numBframes) <= self.nB:
#                     contig_B_frames[pos] += numBframes                    
#                 else:
#                     pass
#             else:
#                 pass        
#             
        
        pos_counts = [0]*len(p_pos)
        pos_prob = [1.0/len(p_pos)] * len(p_pos)
        check_count = 0
        while(np.sum(contig_B_frames.values()) < self.nB):
            
            distrib = rv_discrete(values=(p_pos, pos_prob))
            pos = distrib.rvs(size=1)[0]
            pos_ix = np.where(p_pos==pos)[0][0]
                        
            numBframes = np.random.choice(self.nBPyramSizes, 
                                          p=HEVCWorkloadParams.HEVCWLPARAMS_CONTIG_BFRAMES_PROBS[self.nBmax][self.movieType])
            
            if (((contig_B_frames[pos]) + numBframes) <= self.nBmax):
                if (np.sum(contig_B_frames.values())+numBframes) <= self.nB:
                    contig_B_frames[pos] += numBframes
                    
                    pos_counts[pos_ix] +=1
                                        
                else:
                    check_count+=1
                    pass
            else:
                check_count+=1
                pass        
         
        #print "contig_B_frames : ", contig_B_frames.values()
        #print "pos_counts : ", pos_counts
        
        # construct the gop sequence (one long string)
        # e.g : IBBBPBBB...        
        # at the same time identify which B-frames are "referencable" B-frames        
        gop_seq = "I"        
        for i in p_pos:
            num_contig_b_frames = contig_B_frames[i]
            
            # TODO: currently, the code below only works for nBmax = 4, extend to other values
            b_frs = ""
            if num_contig_b_frames == 1:
                b_frs = "b"
            elif num_contig_b_frames == 2:
                b_frs = "bb"
            elif num_contig_b_frames == 3:
                b_frs = "bbb"
            elif num_contig_b_frames == 4:
                b_frs = "bbBb"
            else:
                pass 
                        
            #tmp_frs =  "B"*contig_B_frames[i] + "P"
            tmp_frs =  b_frs + "P"
            gop_seq+= tmp_frs
        
        # find which B-frames are not referenceable
        general_Bfr_pos = [ix for ix,fr in enumerate(gop_seq) if fr == "B"]
        gop_seq = gop_seq.replace("b", "B")
                    
        return gop_seq, general_Bfr_pos
    
    
    def numNodesWithoutRefs(self):        
        result = []        
        for each_node_k, each_node_v in self.frameLevelRefs.iteritems():
            
            fwd_pred_ref_frames = each_node_v['fwd_pred']
            bwd_pred_ref_frames = each_node_v['bwd_pred']
            
            fwd_flag = False
            bwd_flag = False
            
            if "I" not in each_node_k:
                if (fwd_pred_ref_frames == None) and (bwd_pred_ref_frames == None):
                    result.append(each_node_k)
        #print len(result), result
        
        return len(result)
    
    @staticmethod
    def nxLabel2Frame(nxDGLabel):        
        if len(nxDGLabel) < 2: 
            print "AdaptiveGopGen_v2:: nxLabel2Frame: error ", nxDGLabel        
        # first char is the type
        ftype = nxDGLabel[0]
        fix = int(nxDGLabel[1:])        
        result = { 'ftype': ftype, 'fix': fix}        
        return result
        
        
    
    
    ########################################
    # Task graph manipulation
    ########################################    
    def applyWeights(self, max_comm_cost, max_wccc_I, max_wccc_P, max_wccc_B):
        # create empty graph
        DG = nx.DiGraph()
        
        # create nodes with weights
        for each_node in self.networkxDG.nodes():
            if "I" in each_node:
                w = max_wccc_I
            elif "P" in each_node:
                w = max_wccc_P
            elif "B" in each_node:
                w = max_wccc_B
            else:
                pass
                
            DG.add_node(each_node, weight=w)
            
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
        
        
        # create edges with weights
        # for each node we get the parents (i.e. incoming flows)
        for each_c_node in self.networkxDG.nodes():
            all_p_nodes = self.networkxDG.predecessors(each_c_node)
            if len(all_p_nodes) > 0:
                # get flw weights
                p_weights = self._get_flw_weights(all_p_nodes, max_comm_cost)                
                for each_p_node in all_p_nodes:
                    #DG.add_edge(each_p_node, each_c_node, weight=p_weights[each_p_node],label=str(p_weights[each_p_node]))
                    DG.add_edge(each_p_node, each_c_node, weight=max_comm_cost,label=str(p_weights[each_p_node])) # max edge weight (worst-case)
            else:
                pass
        
        
        self.networkxDG_weighted = DG
        
        #pprint.pprint(self.networkxDG_weighted.nodes(data=True))
        
    
    def _get_flw_weights(self, all_p_nodes, max_comm_cost):
        if len(all_p_nodes) == 0: sys.exit("_get_flw_weights:: Error - 0")
        
        result = {} # parent: weight        
        num_I = len([n for n in all_p_nodes if "I" in n])
        num_P = len([n for n in all_p_nodes if "P" in n])
        num_B = len([n for n in all_p_nodes if "B" in n])
        
        mask = [num_I, num_P, num_B]
        
        if mask.count(0) == 3:
            sys.exit("_get_flw_weights:: Error - 1")
        
        # only one type of parent
        elif mask.count(0) == 2:
            [vI, vP, vB] = [0,0,0]
            n = len(all_p_nodes)
            vI = float(max_comm_cost)/float(n) if num_I>0 else 0
            vP = float(max_comm_cost)/float(n) if num_P>0 else 0
            vB = float(max_comm_cost)/float(n) if num_B>0 else 0
        
        # more than one type of parent
        elif mask.count(0) == 1:
            [vI, vP, vB] = [0,0,0]
            
            if mask[0] == 0:    # nI=0
                vP = (float(max_comm_cost) * 0.66)/float(num_P)
                vB = (float(max_comm_cost) * 0.33)/float(num_B)                
            elif mask[1] == 0:  # nP=0
                vI = (float(max_comm_cost) * 0.8)/float(num_I)
                vB = (float(max_comm_cost) * 0.2)/float(num_B)
            elif mask[2] == 0:  # nB=0
                vI = (float(max_comm_cost) * 0.66)/float(num_I)
                vP = (float(max_comm_cost) * 0.33)/float(num_P)
            else:
                sys.exit("_get_flw_weights:: Error - 2")
            
        # all types of parent
        elif mask.count(0) == 0:
            [vI, vP, vB] = [0,0,0]
            vI = (float(max_comm_cost) * 0.5714)/float(num_I)
            vP = (float(max_comm_cost) * 0.2857)/float(num_P)
            vB = (float(max_comm_cost) * 0.14285)/float(num_B)
        
        # assign weights to parents
        for p in all_p_nodes:
            if "I" in p: result[p] = vI
            elif "P" in p: result[p] = vP
            elif "B" in p: result[p] = vB
            else:
                sys.exit("_get_flw_weights:: Error - 3")
        
        return result  
        
        
        
    def splitDAG2Tiles(self, num_tiles):
        # create empty graph
        DG = nx.DiGraph()
        
        # create sub task nodes
        for each_node, data in self.networkxDG_weighted.nodes(data=True):
            if 'weight' in data:
                w = data['weight']
            else:
                w = 0.0
                
            for t in range(num_tiles):
                node_label = each_node + "_" + str(t)
                DG.add_node(node_label, weight=float(w)/float(num_tiles)) # equally divide weights
        
                # colorize nodes
                ftype = self.nxLabel2Frame(each_node)['ftype']
                DG.node[node_label]['fillcolor']=self._get_fr_node_col(ftype)
                DG.node[node_label]['style']='filled'
                DG.node[node_label]['fontsize']='30'
                DG.node[node_label]['arrowsize']="10.0"
                if 'weight' in DG.node[node_label]:
                    DG.node[node_label]['node_size']=(DG.node[node_label]['weight']*2)+300 # default 300                
        
        # graph-level properties
        DG.graph['graph']={'rankdir':'LR'}
                        
        # create subtask graph edges
        for each_edge in self.networkxDG_weighted.edges(data=True):
            p = each_edge[0]
            c = each_edge[1]
            w = each_edge[2]['weight']
             
            for each_pp_id in range(num_tiles):
                for each_cc_id in range(num_tiles):
                    pp_lbl = p + "_" + str(each_pp_id)
                    cc_lbl = c + "_" + str(each_cc_id)
                    ww = float(w)/float(num_tiles**2)
                    DG.add_edge(pp_lbl, cc_lbl, weight=ww, label=str(ww))
        
        self.networkxDG_weighted_split = DG
        
        
    def splitDAG2TilesUnweighted(self, num_tiles, use_tex_labeling=False):
        # create empty graph
        DG = nx.DiGraph()
        
        # create sub task nodes
        for each_node, data in self.networkxDG.nodes(data=True):                
            for t in range(num_tiles):
                node_label = each_node + "_" + str(t)
                
                if use_tex_labeling == True:
                    lbl = self._get_tex_node_lbl(node_label)
                else:
                    pass
                
                DG.add_node(node_label) 
        
                # colorize nodes
                ftype = self.nxLabel2Frame(each_node)['ftype']
                DG.node[node_label]['fillcolor']=self._get_fr_node_col(ftype)
                DG.node[node_label]['style']='filled'
                DG.node[node_label]['fontsize']='30'
                DG.node[node_label]['arrowsize']="10.0"
                #DG.node[node_label]['label']=lbl
                               
        # graph-level properties
        DG.graph['graph']={'rankdir':'LR'}
                        
        # create subtask graph edges
        for each_edge in self.networkxDG.edges(data=True):
            p = each_edge[0]
            c = each_edge[1] 
            for each_pp_id in range(num_tiles):
                for each_cc_id in range(num_tiles):
                    pp_lbl = p + "_" + str(each_pp_id)
                    cc_lbl = c + "_" + str(each_cc_id)                    
                    DG.add_edge(pp_lbl, cc_lbl)
        
        self.networkxDG_split = DG
        
        
        
        
    
    @staticmethod
    def merge_nodes(G,nodes, new_node, attr_dict=None, **attr):
        """
        Merges the selected `nodes` of the graph G into one `new_node`,
        meaning that all the edges that pointed to or from one of these
        `nodes` will point to or from the `new_node`.
        attr_dict and **attr are defined as in `G.add_node`.
        
        Adapted from : https://gist.github.com/Zulko/7629206
        """   
        
        merge_start_timer_pytime = time.time()
        merge_start_timer_pyclock = time.clock()
        merge_start_timer_pytimeit = timeit.default_timer()
        
        G.add_node(new_node, attr_dict, **attr) # Add the 'merged' node        
        
        track_data = {}        
        for n1,n2,data in G.edges(data=True):
            # For all edges related to one of the nodes to merge,
            # make an edge going to or coming from the 'new node'.
            if n1 in nodes:
                G.add_edge(new_node,n2,data) # outgoing                
                #k = "%s->%s" % (new_node, n2)
                k = (new_node, n2)
                if k not in track_data: 
                    track_data[k] = data['weight']
                    G[new_node][n2]['weight'] =  data['weight']
                    G[new_node][n2]['label'] =  data['weight']
                else: 
                    track_data[k] += data['weight']   
                    G[new_node][n2]['weight'] +=  data['weight']
                    G[new_node][n2]['label'] =  G[new_node][n2]['weight']       
                                
            elif n2 in nodes:
                G.add_edge(n1,new_node,data) # incoming
                #k = "%s->%s" % (n1, new_node)
                k = (n1, new_node)
                if k not in track_data: 
                    track_data[k] = data['weight']
                    G[n1][new_node]['weight'] =  data['weight']
                    G[n1][new_node]['label'] =  data['weight']
                else: 
                    track_data[k] += data['weight']
                    G[n1][new_node]['weight'] +=  data['weight']
                    G[n1][new_node]['label'] =  G[n1][new_node]['weight']
            
            else:
                pass
        
        for n in nodes: # remove the merged nodes
            G.remove_node(n)
            
        copy_G = G.copy()
        
        merge_stop_timer_pytime = time.time()
        merge_stop_timer_pyclock = time.clock()
        merge_stop_timer_pytimeit = timeit.default_timer()
        
        merge_time_taken = [merge_stop_timer_pytime-merge_start_timer_pytime,
                            merge_stop_timer_pyclock-merge_start_timer_pyclock,
                            merge_stop_timer_pytimeit-merge_start_timer_pytimeit]
        
        return copy_G, merge_time_taken
    
  
    
    
    
    def get_edges_max_weight(self, G):   
        #print "get_edges_max_weight:: Enter"
        all_edges_dict = nx.get_edge_attributes(G, 'weight')
        max_w =  np.max(all_edges_dict.values())
        k = [k for k,v in all_edges_dict.iteritems() if v == max_w]
        # output keys + vals
        result = {}
        for each_k in k:
            result[each_k] = max_w
        return result    
        
    def get_nodes_max_weight(self, G):
        all_nodes_dict = nx.get_node_attributes(G, 'weight')
        
        max_w =  np.max(all_nodes_dict.values())
        k = [k for k,v in all_nodes_dict.iteritems() if v == max_w]
        # output keys + vals
        result = {}
        for each_k in k:
            result[each_k] = max_w
        return result
    
    def get_nodes_sorted_weight(self, G, rev=False):
        all_nodes_dict = nx.get_node_attributes(G, 'weight')
        sorted_all_nodes_tuples = sorted(all_nodes_dict.items(), key=operator.itemgetter(1), reverse=rev)         
        return  sorted_all_nodes_tuples
    
    def get_edges_sorted_weight(self, G, rev=False):
        all_edges_dict = nx.get_edge_attributes(G, 'weight')
        sorted_all_edges_tuples = sorted(all_edges_dict.items(), key=operator.itemgetter(1), reverse=rev)         
        return  sorted_all_edges_tuples
        
    def get_node_weight(self, G, node):
        node_w = nx.get_node_attributes(G, 'weight')[node]
        return node_w    
    def get_edge_weight(self, G, edge):
        edge_w = nx.get_edge_attributes(G, 'weight')[edge]
        return edge_w
    
    
    
    
    
    ########################################
    # These functions will be useful to get
    # dependency related info
    ########################################
    
    def calc_GopDependencies(self, gop_task_ids):
        
        ## memory related 
        self.gop_level_dep[-2] = [] #mmc_rd
        self.gop_level_dep[-1] = [] #mmc_wr
        self.task_level_dep[-2] = []
        self.task_level_dep[-1] = []
        self.which_task_needs_current_task[-2] = []
        self.which_task_needs_current_task[-1] = []
        self.my_closest_children[-2]=[]
        self.my_closest_children[-1]=[]
        
        self.my_closest_parent[-2]=None
        self.my_closest_parent[-1]=None
        
        self.which_frame_needs_current_frame[-2]=[]
        self.which_frame_needs_current_frame[-1]=[]
        
        self.possible_interfering_frames[-2]=[]
        self.possible_interfering_frames[-1]=[]
                
        for each_frame  in self.networkxDG.nodes():
            parents = self.networkxDG.predecessors(each_frame)
            children = self.networkxDG.successors(each_frame)
            
            frame_type = self.nxLabel2Frame(each_frame)['ftype']
            frame_ix = self.nxLabel2Frame(each_frame)['fix']
            parents_frix = [self.nxLabel2Frame(f)['fix'] for f in parents]
            children_frix = [self.nxLabel2Frame(f)['fix'] for f in children]
            
            parents_taskix = [gop_task_ids[ix] for ix in parents_frix]
            children_taskix = [gop_task_ids[ix] for ix in children_frix]
            
            if(each_frame != "I0"):
                parents_distance_from_I0 = [nx.shortest_path_length(self.networkxDG, source="I0", target=p) for p in parents]            
                temp_closest_parent_ix = [ix for ix,v in enumerate(parents_distance_from_I0) if v == np.min(parents_distance_from_I0)][0]
                closest_parent = parents[temp_closest_parent_ix]
            else:
                closest_parent=None
            
            # populate dependencies structures from stuff obtained above           
            self.gop_level_dep[frame_ix] = parents_frix
            self.task_level_dep[frame_ix] = parents_taskix   
            self.which_task_needs_current_task[frame_ix] = children_taskix
            self.my_closest_children[frame_ix] = None # not needed for now
            self.my_closest_parent[frame_ix] = closest_parent            
            self.which_frame_needs_current_frame[frame_ix] = children_frix
            self.non_dep_frames = {}        
            self.possible_interfering_frames[frame_ix] = [self.nxLabel2Frame(n)['fix'] for n in self.find_inteferers(each_frame)]
        
        
        
    
    # 1) exclude all nodes from [I0->parent], endpoints inclusive    
    # 2) exclude all nodes from [children->leafnodes], endpoints inclusive
    def find_inteferers(self, target_frame):
        set_all_nodes = set(self.networkxDG.nodes())
        
        parents = self.networkxDG.predecessors(target_frame)
        children = self.networkxDG.successors(target_frame)
        
        # all nodes from I0-> parent
        set_all_nodes_fromI0_toparent = set([])
        for each_parent in parents:
            for path in nx.all_simple_paths(self.networkxDG, source="I0", target=each_parent):                
                set_all_nodes_fromI0_toparent = set_all_nodes_fromI0_toparent.union(path)
                
        # exclude the above
        stage1_excluded_set = set_all_nodes.difference(set_all_nodes_fromI0_toparent)        
        
        # all nodes from children -> leaf nodes
        leaf_nodes = self.get_leaf_nodes()
        set_all_nodes_fromChildren_toLeafnodes = set([])
        for each_child in children:
            for each_lfn in leaf_nodes:
                for path in nx.all_simple_paths(self.networkxDG, source=each_child, target=each_lfn):                    
                    set_all_nodes_fromChildren_toLeafnodes = set_all_nodes_fromChildren_toLeafnodes.union(path)
        
        stage2_exluded_set = stage1_excluded_set.difference(set_all_nodes_fromChildren_toLeafnodes)        
        return list(stage2_exluded_set)
        
        
    # nodes withou children    
    def get_leaf_nodes(self):
        leaf_nodes = [n for n in self.networkxDG.nodes()
                       if len(self.networkxDG.successors(n)) == 0]                                            
        return leaf_nodes
    
    
    # get the possible decoding order of the gop
    # take into account the dependencies
    def getDecodingOrder(self):
        if (self.networkxDG == None): sys.exit("Error: getDecodingOrder::Error - nx obj is null")

        try:
            topo_sorted_nodes = nx.topological_sort(self.networkxDG)                
        except:
            sys.exit("Error: getDecodingOrder::Error - could not get the topological sort order")
        
        # get the node gop_ix
        dep_sorted_ixs = []
        dep_sorted_ftype = []
        for each_nx_node in topo_sorted_nodes:
            fix = self.nxLabel2Frame(each_nx_node)['fix']
            ftype = self.nxLabel2Frame(each_nx_node)['ftype']
            dep_sorted_ixs.append(fix)
            dep_sorted_ftype.append(ftype)
        
        return dep_sorted_ixs, dep_sorted_ftype       
    
    
    # in the order of fanout (most number of outgoing edges)
    def getFanOutOrder_Decreasing(self):        
        decoding_order_frix = self.getDecodingOrder()[0]        
        nodes = []        
        for each_node in self.networkxDG.nodes():
            num_out_edges = len(self.networkxDG.out_edges(nbunch=[each_node]))
            nodes.append(each_node,num_out_edges)
        
        # sort 
        sorted_nodes = sorted(nodes, key=itemgetter(1), reverse=True)
        node_ixs  = [self.nxLabel2Frame(n)['fix'] for n in sorted_nodes]
        
        return node_ixs
    
    def getTotalEdges(self):
        return self.networkxDG.number_of_edges()
    def getTotalNodes(self):
        return self.networkxDG.number_of_nodes()
    
    def getEdges(self):
        return self.networkxDG.edges()
    def getNodes(self):
        return self.networkxDG.nodes()
    
    
    # O(n*m) :: n=num leaves, m=num simple paths per leaf node
    def getCriticalPath_v1(self):
        leaf_nodes = [n for n in self.networkxDG.nodes() if len(self.networkxDG.out_edges(nbunch=[n])) == 0]
        longest_path = []
        for each_leaf_node in leaf_nodes:   # lf
            # get simple paths
            simple_paths = nx.all_simple_paths(self.networkxDG, "I0", each_leaf_node)
            
            for each_sp in simple_paths: # lf_sp
                if len(each_sp) > len(longest_path):
                    longest_path = each_sp   
                    
        longest_path_fix =  [self.nxLabel2Frame(n)['fix'] for n in longest_path]            
             
        return longest_path_fix
    
    
    def getCriticalPath_v2(self):
        longest_path = self.get_longest_path(self.networkxDG)        
        longest_path_fix =  [self.nxLabel2Frame(n)['fix'] for n in longest_path]         
        return longest_path_fix
    
                   
    # http://stackoverflow.com/questions/17985202/networkx-efficiently-find-absolute-longest-path-in-digraph
    def get_longest_path(self,G):
        dist = {} # stores [node, distance] pair
        for node in nx.topological_sort(G):
            # pairs of dist,node for all incoming edges
            pairs = [(dist[v][0]+1,v) for v in G.pred[node]] 
            if pairs:
                dist[node] = max(pairs)
            else:
                dist[node] = (0, node)
        node,(length,_)  = max(dist.items(), key=lambda x:x[1])
        path = []
        while length > 0:
            path.append(node)
            length,node = dist[node]
        return list(reversed(path))
    
    
    
    # fake-cp : using fanout as a metric
    def getPseudoCriticalPath_v1(self):
        # get the number of outgoing-edges per node        
        node_num_edges = []
        all_out_edges = []        
        for each_node in self.networkxDG.nodes():
            num_outedges = len(self.networkxDG.out_edges(nbunch=[each_node]))            
            node_num_edges.append((each_node, num_outedges))                        
            all_out_edges.append(num_outedges)            
        
        # avg edges per node 
        avg_edges_per_node = np.mean(all_out_edges)        
        # get all nodes higher than the avg        
        pseudo_cp_fix = [self.nxLabel2Frame(each_node_num_edges[0])['fix'] for each_node_num_edges in node_num_edges 
                        if (each_node_num_edges[1]>=avg_edges_per_node)]        
        if 0 not in pseudo_cp_fix: pseudo_cp_fix.append(0)               
        return pseudo_cp_fix     
         
    
    # fake-cp : using I + P + Generalised-B frames as inside the critical path (order does not matter)
    def getPseudoCriticalPath_v2(self, include_gen_b = False):
        cp_nodes_fix = []
        for each_node in self.networkxDG.nodes():
            if self.nxLabel2Frame(each_node)['ftype'] in ["I", "P"]:
                cp_nodes_fix.append(self.nxLabel2Frame(each_node)['fix'])
            elif self.nxLabel2Frame(each_node)['ftype'] == "B":
                if include_gen_b == True:    # check if we can include generalised B-frames            
                    if len(self.networkxDG.out_edges(nbunch=[each_node]))>0: # generalised B
                        cp_nodes_fix.append(self.nxLabel2Frame(each_node)['fix'])
                    else:
                        pass
                else:
                    pass
            else:
                pass
        return cp_nodes_fix
            
    
    
    # groups the nodes according to the max-distance from the root-node
    def getParallelSets(self):
        root_node_dist_groupings = {}
        for each_node in self.networkxDG.nodes():
            # get simple paths
            max_simple_path_len = np.max([len(p) for p in  nx.all_simple_paths(self.networkxDG, "I0", each_node)])
            
            if max_simple_path_len not in root_node_dist_groupings:
                root_node_dist_groupings[max_simple_path_len] = [each_node]
            else:
                root_node_dist_groupings[max_simple_path_len].append(each_node)
        
        return root_node_dist_groupings
            
            
    
    # group a gop sequence in to heirarchical B-fr groups
    def getGroupedGop(self, gop_seq):
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
        
    
    ########################################
    # Functions related to networkX
    ########################################
    def createGraph(self, DG):    
        ':type DG: DiGraph'
        for each_node_k, each_node_v in self.frameLevelRefs.iteritems():
            fwd_pred_ref_frames = each_node_v['fwd_pred']
            bwd_pred_ref_frames = each_node_v['bwd_pred']
                    
            if(fwd_pred_ref_frames != None):        
                for each_frame in fwd_pred_ref_frames:
                    ref_node_label = each_frame['fr'] + str(each_frame['frix'])
                    DG.add_edge(ref_node_label, each_node_k)                
                    
            if (bwd_pred_ref_frames != None):        
                for each_frame in bwd_pred_ref_frames:                    
                    ref_node_label = each_frame['fr'] + str(each_frame['frix'])
                    DG.add_edge(ref_node_label, each_node_k)
           
        # colorize
        for each_node_k, each_node_v in self.frameLevelRefs.iteritems():
            ftype = self.nxLabel2Frame(each_node_k)['ftype']
            DG.node[each_node_k]['fillcolor']=self._get_fr_node_col(ftype)
            DG.node[each_node_k]['style']='filled'
            DG.node[each_node_k]['fontsize']='30'
            DG.node[each_node_k]['arrowsize']="10.0"
            if 'weight' in DG.node[each_node_k]:
                DG.node[each_node_k]['node_size']=DG.node[each_node_k]['weight']+300 # default 300
            
            # graph-level properties
            DG.graph['graph']={'rankdir':'LR'}
               
        return DG

    
    def _get_tex_node_lbl(self, node_lbl):
        if ("_" not in node_lbl):
            ftype = node_lbl[0]
            ix = node_lbl[1:]
            result = "%s<SUB>%s</SUB>" %(ftype,ix)
        else:
            ftype = node_lbl[0]
            ix = node_lbl[1:].split("_")[0]
            tile_ix  = node_lbl[1:].split("_")[1]            
            result = "<%s<SUB>%s</SUB><SUP>%s</SUP>>" %(ftype,ix,tile_ix)
            
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
    

    def createNetworkXDG(self):
        DG = nx.DiGraph()
        DG = self.createGraph(DG)
        self.networkxDG=DG
        #self.printGraph()

    def checkZeroPredecessors(self, DG):
        nodes_list = nx.nodes(DG)    
        num_nodes_with_zero_preds = []
        
        for each_node in nodes_list:        
            if (len(DG.predecessors(each_node)) == 0) and ("I" not in each_node):
                num_nodes_with_zero_preds.append(each_node)
        
        return len(num_nodes_with_zero_preds)
    
    
    
    # write dot file to use with graphviz
    # run "dot -Tpng test.dot >test.png"
    @staticmethod
    def output_png(DG, lbl, dir = "/home/rosh/Documents/EngD/Papers/Paper_HEVC/generated_tgs/", format="png"):    
        dot_fname = dir+'tg_test_'+lbl+'.dot'
        png_fname =  dir+'tg_test_'+lbl+'.' + format 
        
        nx.write_dot(DG,dot_fname)
        
        cmd = "dot -T" + format +" "+ dot_fname + " >" + png_fname    
        print cmd
        os.system(cmd)
    
    
    
    ########################################
    # HELPERS 
    ########################################
    def _get_nP_using_fitted_distrib(self, np_range):        
        orig_np_range = np.arange(7,35)        
        pdf_y = exponweib.pdf(orig_np_range, self.nP_expweib_params[0], 
                               self.nP_expweib_params[1],
                               scale = self.nP_expweib_params[2],
                               loc = self.nP_expweib_params[3]
                               #loc=0
                               )
        
        probabilities = pdf_y
        
        # replace NaN with the closest non-NaN
        mask = np.isnan(probabilities)
        probabilities[mask] = np.interp(np.flatnonzero(mask), 
                                        np.flatnonzero(~mask), 
                                        probabilities[~mask])   
                        
        # replace 'inf' with the closest non-inf
        mask = np.isinf(probabilities)
        probabilities[mask] = np.interp(np.flatnonzero(mask), 
                                        np.flatnonzero(~mask), 
                                        probabilities[~mask])
        
        
        norm_probabilties = np.array(probabilities)/np.sum(probabilities)
        x_axis_vals = np.linspace(np.min(np_range), np.max(np_range), len(norm_probabilties))
                
#         print np_range
#         print norm_probabilties
#         print probabilities
#         f = plt.figure()
#         plt.plot(x_axis_vals, norm_probabilties, marker='*')
#         plt.show()
          
        #values = np_range        
        #distrib = rv_discrete(values=(values, norm_probabilties))
        #nP = distrib.rvs(size=1)[0]
        nP = np.random.choice(x_axis_vals, p=norm_probabilties)       
        
        nP_int = int(np.round(nP))
        
        return nP_int
        
    
    def _weightedChoice(self, weights, objects):
            #http://stackoverflow.com/questions/10803135/weighted-choice-short-and-simple
            """Return a random item from objects, with the weighting defined by weights 
            (which must sum to 1)."""
            cs = np.cumsum(weights) #An array of the weights, cumulatively summed.
            idx = np.sum(cs < np.random.rand()) #Find the index of the first weight over a random value.
            return objects[idx]
    
    
    def _bframe_get_fwdref_frames(self, frame_templevel_groupings,  each_level_ix, pyramidix,
                                  all_possible_ref_frames, frix, fr, all_dep_list):
        possible_fwd_refs = []
        selection_weights = []
        local_deps = []
        for each_ref_frame in all_possible_ref_frames:
            if (each_ref_frame['frix']<frix):
                # check for circular deps
                temp_lbl = each_ref_frame['fr']+str(each_ref_frame['frix']) + "<-" +  fr+str(frix)                        
                if temp_lbl not in all_dep_list:                        
                    possible_fwd_refs.append(each_ref_frame)                
        
        return possible_fwd_refs
    
    
    def _bframe_get_bwdref_frames(self, frame_templevel_groupings,  each_level_ix, pyramidix,
                                  all_possible_ref_frames, frix, fr, all_dep_list):
        possible_bwd_refs = []
        selection_weights = []
        #print frix
        for each_ref_frame in all_possible_ref_frames:
            if (each_ref_frame['frix']>frix):
                # check for circular deps
                temp_lbl = each_ref_frame['fr']+str(each_ref_frame['frix']) + "<-" +  fr+str(frix)
                if temp_lbl not in all_dep_list:                        
                    possible_bwd_refs.append(each_ref_frame)
        
        return possible_bwd_refs
    
    
    
    def _get_dep_list(self, current_frame_label, selected_ref_frames):
        result = []
        for each_selected_ref_frame in selected_ref_frames:
            ref_fr_label = each_selected_ref_frame['fr']+str(each_selected_ref_frame['frix'])
            entry = current_frame_label + "<-" + ref_fr_label
            result.append(entry)
        return result
            
    
    def _get_pyramid_ids(self, frame_level_groupings):
        unique_pyramid_ids =[]        
        for each_level_ix, each_level_frames in  frame_level_groupings.iteritems():
            for each_frame in each_level_frames:
                if (each_frame['fr'] == 'B'):
                    if(each_frame['pyramid_id'][0] not in unique_pyramid_ids):
                        unique_pyramid_ids.append(each_frame['pyramid_id'][0])
                    
        return unique_pyramid_ids
                
    
    
    def _getFramesFromLowerOrEqualTemporalLayers(self, frame_level_groupings, current_frix, current_templayer_ix):
        
        # all frames in temporal levels lower than equal to the ones specified    
        temp_frames_1  = [frs for tlix, frs in frame_level_groupings.iteritems() if tlix <= current_templayer_ix]
        
        # all frames larger in frix
        temp_frames_2 = [f for f in temp_frames_1 if current_frix > f['frix']]
        
        return temp_frames_2
        
    
    
    
    def _getFramesFromLowerOrEqualTemporalLayers_SpecificPyramid(self, frame_level_groupings, current_frix, 
                                                                 current_templayer_ix, specific_pyramid_id_list):
            
        # all frames in temporal levels lower than equal to the ones specified    
        temp_frames_1  = [frs for tlix, frs in frame_level_groupings.iteritems() if tlix <= current_templayer_ix]    
        temp_frames_1 = list(itertools.chain(*temp_frames_1))
        
        # all frames in specified pyramid - does not consider frame ix
        temp_frames_2 = [f for f in temp_frames_1 
                         #if (set(specific_pyramid_id_list).issubset(set(f['pyramid_id'])) == True) and
                         if (set(f['pyramid_id']).issubset(set(specific_pyramid_id_list)) == True) and
                         (f['frix'] != current_frix)
                         ]
        
        return temp_frames_2
        
    
    def _getFramesFromHigherOrEqualTemporalLayers_SpecificPyramid(self, frame_level_groupings, current_frix, 
                                                                 current_templayer_ix, specific_pyramid_id_list):
            
        # all frames in temporal levels higher than equal to the ones specified    
        temp_frames_1  = [frs for tlix, frs in frame_level_groupings.iteritems() if tlix >= current_templayer_ix]    
        temp_frames_1 = list(itertools.chain(*temp_frames_1))
        
        # all frames in specified pyramid - does not consider frame ix
        temp_frames_2 = [f for f in temp_frames_1 
                         #if (set(specific_pyramid_id_list).issubset(set(f['pyramid_id'])) == True) and
                         if (set(f['pyramid_id']).issubset(set(specific_pyramid_id_list)) == True) and
                         (f['frix'] != current_frix)
                         ]
        
        return temp_frames_2
    
    
    def _getFramesFromEqualTemporalLayers_SpecificPyramid(self, frame_level_groupings, current_frix, 
                                                                 current_templayer_ix, specific_pyramid_id_list):
            
        # all frames in temporal levels lower than equal to the ones specified    
        temp_frames_1  = [frs for tlix, frs in frame_level_groupings.iteritems() if tlix == current_templayer_ix]    
        temp_frames_1 = list(itertools.chain(*temp_frames_1))
        
        # all frames in specified pyramid - does not consider frame ix
        temp_frames_2 = [f for f in temp_frames_1 
                         #if (set(specific_pyramid_id_list).issubset(set(f['pyramid_id'])) == True) and
                         if (set(f['pyramid_id']).issubset(set(specific_pyramid_id_list)) == True) and
                         (f['frix'] != current_frix)
                         ]
        
        return temp_frames_2
    
    
    
#     def weighted_sample(self, population, weights, k):
#         return random.sample(WeightedPopulation(population, weights), k)
# 
# 
# 
# class WeightedPopulation(Sequence):
#     def __init__(self, population, weights):
#         #print len(population), len(weights)
#         assert len(population) == len(weights) > 0 , "%d, %d" %(len(population), len(weights))
#         self.population = population
#         self.cumweights = []
#         cumsum = 0 # compute cumulative weight
#         for w in weights:
#             cumsum += w   
#             self.cumweights.append(cumsum)  
#     def __len__(self):
#         return self.cumweights[-1]
#     def __getitem__(self, i):
#         if not 0 <= i < len(self):
#             raise IndexError(i)
#         return self.population[bisect.bisect(self.cumweights, i)]











