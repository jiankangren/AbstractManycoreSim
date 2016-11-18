import pprint
import sys
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


class AdaptiveGoPGenerator():

    def __init__(self, M, N, numPFrameRefs, numBFrameRefs, 
                 pregen_hevc_CTUs = None):
        self.M = M  # distance between successive P-frames
        self.N = N  # distance between successive I-frames (or in our case GopSize-1)      
        self.numPFrameRefs = numPFrameRefs 
        self.numBFrameRefs = numBFrameRefs 
        
        # we populate these later
        self.gopSeq = None
        self.numTemporalLevels = None
        self.framesTemporalGroupings = None
        self.frameLevelRefs = None
        
        # network x structure
        ':type networkxDG: DiGraph'
        self.networkxDG = None
        
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
    def get_M(self):
        return self.M
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
        self.gopSeq = self.generateGOPSequence(self.M, self.N)
        #print self.gopSeq
        self.numTemporalLevels = self.getNumTemporalLayers(self.M)
        self.framesTemporalGroupings = self.groupFramesIntoTemporalLayers(self.gopSeq, self.numTemporalLevels)
        self.frameLevelRefs = self.constructFrameReferences(self.gopSeq, self.numTemporalLevels, 
                                                            self.numPFrameRefs, 
                                                            self.numBFrameRefs[0], self.numBFrameRefs[1])
    
    
        
    
    # this iterates until a gop struct with valid deps have been found 
    # issue is with getting cyclic dependencies
    def verifyAndRecreateGoP(self):
        valid=False
        # iterate till a valid gop is found
        while(valid==False):
            self.createGoP()
            self.createNetworkXDG()
            
            # check and set
            if (len(list(nx.simple_cycles(self.networkxDG))) == 0) and \
                (self.numNodesWithoutRefs()==0) and \
                (self.checkZeroPredecessors(self.networkxDG)==0):                    
                    valid=True
            else:
                valid=False
                
        
    def initialiseInternalStructures(self, gop_task_ids):
        #print gop_task_ids
        self.calc_GopDependencies(gop_task_ids)
    
    
    def constructFrameReferences(self, gopSeq, numTemporalLevels, maxPframeRefs, maxBframeRefs_forwdir, maxBframeRefs_backdir):
        
        # get frame based temporal level groupings
        frame_templevel_groupings = self.groupFramesIntoTemporalLayers(gopSeq, numTemporalLevels)
        all_pyramid_ids = self._get_pyramid_ids(frame_templevel_groupings)
        num_pyramids = len(all_pyramid_ids)
        
        # P-frame references
        # references == parent dependencies
        all_dep_list = []
        parent_frame_refs = OrderedDict()
        for each_level_ix, each_level_frames in  frame_templevel_groupings.iteritems():
            for each_frame in each_level_frames:
                fr = each_frame['fr']
                frix = each_frame['frix']
                pyramidix = each_frame['pyramid_id']
                
                ########## I-FRAMES ############
                if fr == 'I':
                    # no dependencies for I-frames
                    selected_ref_frames = {'gop_ix' : frix,
                                           'fwd_pred' : None,
                                           'bwd_pred' : None
                                           }
                                            
                    
                ########## P-FRAMES ############
                elif fr == 'P':
                    # get all frames in temporal layer and with lower ixs
                    all_possible_ref_frames = [f for f in each_level_frames if frix > f['frix']]
                    
                    if maxPframeRefs>1:
                        num_ref_frames = np.random.randint(1, maxPframeRefs)
                    elif maxPframeRefs == 1:
                        num_ref_frames = 1
                    else:
                        sys.exit("Error: maxPframeRefs  invalid : " + maxPframeRefs)
                        
                    #num_ref_frames = 2
                    if num_ref_frames <= len(all_possible_ref_frames):                    
                        selected_ref_frames = random.sample(all_possible_ref_frames, num_ref_frames)
                    else:
                        selected_ref_frames = all_possible_ref_frames
                        
                    # update dep list
                    all_dep_list.extend(self._get_dep_list(fr+str(frix), selected_ref_frames))
                    
                    
                    selected_ref_frames = {'gop_ix' : frix,
                                           'fwd_pred' : selected_ref_frames,
                                           'bwd_pred' : None
                                           }
                    
                
                ########## B-FRAMES ############
                elif fr == 'B':                    
                    # 1) B-frames must have dependencies from forward or backward frames
                    # 2) Cannot have circular dependencies
                    # 3) refs should be from own pyramid (assumption)
                   
                    if(maxBframeRefs_forwdir>1): num_ref_fwd_dir = np.random.randint(1, maxBframeRefs_forwdir)
                    else: num_ref_fwd_dir = 1                    
                    if(maxBframeRefs_backdir>1): num_ref_bwd_dir = np.random.randint(1, maxBframeRefs_backdir)
                    else: num_ref_bwd_dir =1
                    
                    selected_fwd_ref_frames = None
                    selected_bwd_ref_frames = None
                    possible_fwd_refs = []
                    possible_bwd_refs = []
                    
                    #print pyramidix + [pyramidix[0]-1]
                    
                    # get all possible fwd, bwd ref frames
                    all_possible_fwd_ref_frames = self._getFramesFromLowerOrEqualTemporalLayers_SpecificPyramid(frame_templevel_groupings, 
                                                                                                       frix, 
                                                                                                       each_level_ix, 
                                                                                                       pyramidix + [pyramidix[0]-1])
                    
                    all_possible_bwd_ref_frames = self._getFramesFromEqualTemporalLayers_SpecificPyramid(frame_templevel_groupings, 
                                                                                                       frix, 
                                                                                                       each_level_ix, 
                                                                                                       pyramidix+ [pyramidix[0]+1])
                    
                    if((len(all_possible_fwd_ref_frames)==0) and (len(all_possible_bwd_ref_frames)==0)) : 
                        sys.exit("Error: AdaptiveGoPGenerator::constructFrameReferences::error 1")
                    
                    #assert len(all_possible_fwd_ref_frames) != 0      
                    if len(all_possible_fwd_ref_frames) >0:
                        possible_fwd_refs = self._bframe_get_fwdref_frames(frame_templevel_groupings,  each_level_ix, pyramidix,
                                                                      all_possible_fwd_ref_frames, frix, fr, all_dep_list)                        
                    #assert len(all_possible_bwd_ref_frames) != 0
                    if len(all_possible_bwd_ref_frames) >0:                
                        possible_bwd_refs= self._bframe_get_bwdref_frames(frame_templevel_groupings,  each_level_ix, pyramidix,
                                                                          all_possible_bwd_ref_frames, frix, fr, all_dep_list)
                    
                    # do we have enough fwd refs to select from ?
                    if (len(possible_fwd_refs) < num_ref_fwd_dir):      # no we dont 
                        num_ref_fwd_dir = len(possible_fwd_refs)
                        num_ref_bwd_dir +=1  # increase bwd refs                                  
                    
                    # do we have enough bwd refs to select from ?
                    if (len(possible_bwd_refs) < num_ref_bwd_dir):      # no we dont
                        num_ref_bwd_dir = len(possible_bwd_refs)
                        num_ref_fwd_dir += 1 # increase fwd refs   
                                        
                    ####### select forward refs ###
                    if (len(possible_fwd_refs) > 0) and (len(possible_fwd_refs) >= num_ref_fwd_dir):
                        selected_fwd_ref_frames = random.sample(possible_fwd_refs, num_ref_fwd_dir)
                        all_dep_list.extend(self._get_dep_list(fr+str(frix), selected_fwd_ref_frames))
                    
                    ####### select backward refs ###
                    if (len(possible_bwd_refs) > 0) and (len(possible_bwd_refs) >= num_ref_bwd_dir):
                        selected_bwd_ref_frames = random.sample(possible_bwd_refs, num_ref_bwd_dir)
                        all_dep_list.extend(self._get_dep_list(fr+str(frix), selected_bwd_ref_frames))                        
                        
                    # verify the b refs                    
                    if((selected_fwd_ref_frames==None) and (selected_bwd_ref_frames==None)) : sys.exit("Error: AdaptiveGoPGenerator::constructFrameReferences::error 2")                   
                    
                    selected_ref_frames = {'gop_ix' : frix,
                                           'fwd_pred' : selected_fwd_ref_frames,
                                           'bwd_pred' : selected_bwd_ref_frames
                                           }    
                parent_frame_refs[fr + str(frix)] = selected_ref_frames
                
        return parent_frame_refs
    
    
    def getNumTemporalLayers(self, M):
        numBFrBetweenPFr = M-1    
        m = (np.log((numBFrBetweenPFr + 1)/2.0) / np.log(2)) + 2
        return int(m)
    
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
                
    def groupFramesIntoTemporalLayers(self, gopSeq, numTemporalLayers):
        frames_per_tlevel = OrderedDict()        
        # initialise layers
        for each_l_ix in xrange(numTemporalLayers):
            frames_per_tlevel[each_l_ix] = []
        
        # first layer is I/P frames
        pframecount =0
        for each_fr_ix, each_fr in enumerate(gopSeq):
            if (each_fr == "I"): 
                frames_per_tlevel[0].append({
                                              'frix': each_fr_ix,
                                              'fr' : each_fr,
                                              'pyramid_id' : [0]                                                              
                                              })
                
            elif (each_fr == "P"):
                # assign pyramid ids for p frames, last p is treated differently
                if(pframecount+1 == gopSeq.count('P')):     # last pframe
                    max_num_b_frames = gopSeq.count('P')    # assuming structure is always pyramid form 
                                                            # and has P-frames included.           
                    pyramid_ids = [max_num_b_frames-1]
                else:
                    pyramid_ids = [pframecount, pframecount+1]
                     
                frames_per_tlevel[0].append({
                                              'frix': each_fr_ix,
                                              'fr' : each_fr,
                                              'pyramid_id' : pyramid_ids                                                           
                                              })
                pframecount+=1
                
        
        # all other layers are B-frames
        # construct multiple B-frame pyramids between P-frames
        numBPyramidLevels =  numTemporalLayers-1    
        bframe_ixs_2d_list = self.getBFrameIxs(gopSeq)
        
        # put all gop b-frames into level groups    
        for each_b_chunck_ix, each_b_chunk in enumerate(bframe_ixs_2d_list):
            for each_b_frame_local_ix, each_b_frame_global_ix in enumerate(each_b_chunk):
                level_id = self.getPyramidBFrameLevelID(numBPyramidLevels, each_b_frame_local_ix)
                frames_per_tlevel[level_id].append({
                                                    'frix': each_b_frame_global_ix,
                                                    'fr' : "B",
                                                    'pyramid_id' : [each_b_chunck_ix]
                                                    })
                
                
        return frames_per_tlevel
            
                
    
    def getPyramidBFrameLevelID(self, tot_levels, B_ix):
        
        LVL_SPECIFIC_BFRAMES = {
                                  1: { # max levels = 1
                                      1: [0] # b-frame ix for level 1
                                      },
        
                                  2: { # max levels = 2
                                      1: [0],
                                      2: [1,2],
                                     },
        
                                  3: { # max levels = 3
                                      1: [0],
                                      2: [1,4],
                                      3: [2,3,5,6],                                  
                                      },
         
                                  4:  { # max levels = 4
                                       1: [0],
                                       2: [1,8],
                                       3: [2,5,9,12],
                                       4: [3,4,6,7,10,11,13,14],
                                       }                              
                                  }
        
        target_pyramid_profile = LVL_SPECIFIC_BFRAMES[tot_levels]
        for each_lvl_ix, each_lvl_bframeixs in target_pyramid_profile.iteritems():
            if B_ix in each_lvl_bframeixs:
                return each_lvl_ix        
        return None
        
        
    # M = distance between consecutive P-frames
    # N = (GopSize -1)
    def generateGOPSequence(self, M, N, ClosedGop=True):
        GOPSize = N+1    
        numIFrames = 1
        numBandPFrames = (GOPSize-numIFrames)
        
        if (M!=0):
            if (numBandPFrames % M ) != 0:
                sys.exit("Error: generateGOPSequence: Error :: (numBandPFrames % M ) != 0")
            
        if(M==0): # no B-frames
            numPFrames = 0
            numBFrames = numBandPFrames
            numBFramesBetweenPFrames = numBFrames
            
        else:    
            numPFrames = int(numBandPFrames/M)            
            numBFramesBetweenPFrames = (M-1)
            numBFrames = (numBFramesBetweenPFrames*numPFrames)        
        
        gop_seq = "I" # we assume always start with a I-frame (HEVC-IDR)
        count_nPfr = 0
        count_nBfr_between = 0
        count_sumBfr = 0
        
        for ix in xrange(1,GOPSize):
            if (ix==1): 
                if (numPFrames>0):
                    gop_seq += "P"
                    count_nPfr += 1
                else:
                    gop_seq += "B"
                    count_sumBfr += 1
            else:
                if (count_nBfr_between < numBFramesBetweenPFrames):
                    gop_seq += "B"
                    count_sumBfr += 1
                    count_nBfr_between += 1
                else:
                    gop_seq += "P"
                    count_nPfr +=1
                    count_nBfr_between =0
                    
        return gop_seq
    
    
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
        # first char is the type
        ftype = nxDGLabel[0]
        fix = int(nxDGLabel[1:])
        
        result = {
                  'ftype': ftype,
                  'fix': fix,                  
                  }
        
        return result
        
        
    
    
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
            
            
        
    
    
    ########################################
    # Functions related to networkX
    ########################################
    def createGraph(self, DG):    
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
                
        return DG
    

    def createNetworkXDG(self):
        DG = nx.DiGraph()
        DG = self.createGraph(DG)
        self.networkxDG=DG

    def checkZeroPredecessors(self, DG):
        nodes_list = nx.nodes(DG)    
        num_nodes_with_zero_preds = []
        for each_node in nodes_list:        
            if (len(DG.predecessors(each_node)) == 0) and ("I" not in each_node):
                num_nodes_with_zero_preds.append(each_node)
                
        return len(num_nodes_with_zero_preds)
    
    
    
    
    ########################################
    # HELPERS 
    ########################################
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





###################################
# Testbench class
###################################
class AdaptiveGoPGenerator_TestBench():

    def __init__(self):
        i=1
    
    def performTests_v1(self):
#         print "M=4, N=8 : ",generateGOPSequence(M=4, N=8)
#         print "M=8, N=24 : ",generateGOPSequence(M=8, N=24)
#         print "M=0, N=8 : ",generateGOPSequence(M=0, N=15)         
#         print "---"
        
        M=8; N=24
        numPframerefs = 2
        numBframerefs = (1,1) # per direction
        AGG = AdaptiveGoPGenerator(M, N, numPframerefs, numBframerefs)
        AGG.createGoP()
        
        print AGG.gopSeq, len(AGG.gopSeq)
        print AGG.numTemporalLevels
        
        print(json.dumps(AGG.frameLevelRefs, indent=4))

#AGG_TB = AdaptiveGopGenerator_TestBench()
#AGG_TB.performTests_v1()






