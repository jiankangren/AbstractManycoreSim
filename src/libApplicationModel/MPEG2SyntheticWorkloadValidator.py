import pprint
import argparse
import sys, os
import random
import time
import math
import gc
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
#plt.style.use('ggplot')

from collections import OrderedDict
from scipy.stats import rv_discrete
from scipy.stats import exponweib
import scipy.stats as ss
import itertools
import json
import csv
from operator import itemgetter
import networkx as nx
import operator
from collections import Counter, Sequence
from collections import OrderedDict
from scipy.stats import exponweib
from scipy.stats import rv_discrete
import multiprocessing

import simpy

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

## local imports
from SimParams import SimParams

from libApplicationModel.MPEG2FrameTask import MPEG2FrameTask
from libNoCModel.NoCFlow import NoCFlow



EXP_DATADIR = "../experiment_data/workload_validation_mpeg2/"

RANDOM_SEEDS = [81665, 33749, 43894, 26358, 80505, 83660, 22817, 70263, 29917, 26044]

NOC_W = 8
NOC_H = 8
NOC_PERIOD = 0.00000001
NOC_ARBITRATION_COST = 7.0 * NOC_PERIOD

# testbench class for hevc frame
class MPEG2SyntheticWorkloadValidator():
    
    def __init__(self, seed, num_gops, vid_res):
        
        self.env = simpy.Environment()
        
        self.seed = seed
        self.num_gops = num_gops
        self.vid_res = vid_res        
        self.generated_gops_list = []
    
    
    def _write_formatted_file(self, fname, data, format):        
        if(format == "pretty"):
            logfile=open(fname, 'w')
            pprint(data, logfile, width=128)
            
        elif(format == "json"):
            logfile=open(fname, 'w')
            json_data = json.dumps(data)
            logfile.write(json_data)
            
        else:
            logfile=open(fname, 'w')
            pprint(data, logfile, width=128)
    
    def generateMultipleGoPs(self):          
        print "generateMultipleGoPs:: SEED === " + str(self.seed)        
        random.seed(self.seed)
        np.random.seed(self.seed)
        
        task_start_id = 0
        for gid in xrange(self.num_gops):
            GoP_obj = MPEGGoP_TB(self.env, 
                                 task_start_id, gid, self.vid_res,
                                 )
            
            GoP_obj.generateMPEGGoP()
            self.generated_gops_list.append(GoP_obj)
            print "finished : ", gid
            
            task_start_id += 12 # 12 frames
    
    
    
    
    
    def dump_video_workload_stats(self, vidworkload_data_fname):
                
        vid_wkl_stats = {
                
                # gop-level stats
                'gop_info': [],
                
                # worst-case TG stats
                'max_num_nodes' : None,
                'max_num_edges' : None,
                
                'fr_cc_I' : [],
                'fr_cc_P' : [],
                'fr_cc_B' : [],
                
                'wc_comp_cost_I' : None, 
                'wc_comp_cost_P' : None,
                'wc_comp_cost_B' : None,
                
                'max_ccr' : None # based on wccc
                                
        } 
        
        
        # frame-level, data
        all_gop_stats = []
        for gix, each_gop in enumerate(self.generated_gops_list):    
            gop_stats = {
                # high level stats
                'gop_ix' : gix,
                'gop_sequence' : each_gop.gop_seq,
                'numP' : each_gop.num_P,
                'numB' : each_gop.num_B,                
                'num_edges' : each_gop.num_edges,
                'num_nodes' : each_gop.num_nodes,
                'real_ccr' : None                                
            }
            
            all_ref_data_payloads = []
            all_fr_ccs = []
            for each_frame in each_gop.mpeg_frames:
                ftype = each_frame.get_frameType()
                
                # computation costs
                if ftype == "I":
                    vid_wkl_stats['fr_cc_I'].append(each_frame.get_computationCost())                    
                elif ftype == "P":
                    vid_wkl_stats['fr_cc_P'].append(each_frame.get_computationCost())
                    all_ref_data_payloads.append(each_frame.get_completedTaskSize()) # fwd
                elif ftype == "B":
                    vid_wkl_stats['fr_cc_B'].append(each_frame.get_computationCost())
                    all_ref_data_payloads.append(each_frame.get_completedTaskSize()) # fwd
                    all_ref_data_payloads.append(each_frame.get_completedTaskSize()) # bwd
                else:
                    sys.exit("frsize- unknown ftype = " + str(ftype))
                
                all_fr_ccs.append(each_frame.get_computationCost())
                
            
            # add gop stats to video stats
            vid_wkl_stats['gop_info'].append(gop_stats)
            
            # calculate gop ccr
            gop_stats['real_ccr'] = self._get_ccr(all_ref_data_payloads, all_fr_ccs, each_gop.num_nodes, each_gop.num_edges)            
        
        # calculate worst-case stats (video-level)
        vid_wkl_stats['max_num_nodes'] = np.max([ g['num_nodes'] for g in  vid_wkl_stats['gop_info'] ])
        vid_wkl_stats['max_num_edges'] = np.max([ g['num_edges'] for g in  vid_wkl_stats['gop_info'] ])
        vid_wkl_stats['wc_comp_cost_I'] = np.max(vid_wkl_stats['fr_cc_I'])
        vid_wkl_stats['wc_comp_cost_P'] = np.max(vid_wkl_stats['fr_cc_P'])
        vid_wkl_stats['wc_comp_cost_B'] = np.max(vid_wkl_stats['fr_cc_B'])
        
        vid_wkl_stats['max_ccr'] = self._get_max_ccr(self.generated_gops_list[0].vid_res, 
                                                     vid_wkl_stats['wc_comp_cost_I'],
                                                     vid_wkl_stats['wc_comp_cost_P'],
                                                     vid_wkl_stats['wc_comp_cost_B'])
        
        # write out (frame data)
        logfile=open(vidworkload_data_fname, 'w')
        json_data = json.dumps(vid_wkl_stats)
        logfile.write(json_data)
        
    
    
    
    def _get_ccr(self, payloads, fr_ccs, num_nodes, num_edges ):
        # checks
        assert(len(payloads) == num_edges)
        assert(len(fr_ccs) == num_nodes)
                
        total_nodes_cost = np.sum(fr_ccs)
        total_edges_cost = 0
        
        nhops= (NOC_H-1) + (NOC_W-1) 
        for each_flw_payload in payloads:
            total_edges_cost += NoCFlow.getCommunicationCost(each_flw_payload, nhops, NOC_PERIOD, NOC_ARBITRATION_COST)
                                                                         
            
        ratio_ccr = float(total_edges_cost)/float(total_nodes_cost)  
        
        return ratio_ccr
    
    
    def _get_max_ccr(self, vid_res, I_wcc, P_wcc, B_wcc):        
        # assuming fixed gop seq - "IPBBPBBPBBBB"
        total_nodes_cost = I_wcc + (P_wcc * 3.0) + (B_wcc * 8.0) 
        each_edge_payload = (vid_res[0] * vid_res[1] * 2)
        nhops= (NOC_H-1) + (NOC_W-1) 
        total_edges_cost =  NoCFlow.getCommunicationCost(each_edge_payload, nhops, NOC_PERIOD, NOC_ARBITRATION_COST) * 19.0
            
        max_ratio_ccr = float(total_edges_cost)/float(total_nodes_cost)  
        
        return max_ratio_ccr
    
            
            
    

# testbench class for hevc gop
class MPEGGoP_TB():
    def __init__(self, env, task_start_id,gid, vid_res,
                 ):
        
        # gop-level stats
        self.env = env
        self.task_start_id = task_start_id
        self.gop_id = gid
        self.vid_res = vid_res        
        
        # to calculate        
        self.num_P = None
        self.num_B = None        
        
        # frames in gop
        self.gop_seq = None        
        self.mpeg_frames = []
        self.num_edges = None
        self.num_nodes = None
    
    
    
    def calculateStats(self):
        # P/B counts
        self.num_P = self.gop_seq.count("P")
        self.num_B = self.gop_seq.count("B")
         
        
        
        
        
    
    def generateMPEGGoP(self):        
                
        task_start_id = self.task_start_id
        gop_id = self.gop_id
        unique_gop_start_id = gop_id                                                                                                              
        frame_h =  self.vid_res[0]       
        frame_w = self.vid_res[1]
        
        priority_range = range(1,100) # dummy
        strm_resolution = frame_h*frame_w 
                    
        gop_instance_frames = []   # reset            
        unique_gop_id = gop_id
     
        self.gop_seq = SimParams.GOP_STRUCTURE 
        
        # get num edges + nodes
        self.num_edges = (8*2)+(3*1)
        self.num_nodes = 12
        
        
        # construct task ids
        gop_task_ids = range(task_start_id, task_start_id+len(self.gop_seq))                      
        
        
        for fix, each_frame in enumerate(SimParams.GOP_STRUCTURE):
            frame_task = MPEG2FrameTask(env = self.env, \
                                        id = gop_task_ids[fix], \
                                        frame_type = str(each_frame), \
                                        frame_ix_in_gop = fix, \
                                        unique_gop_id = unique_gop_id, \
                                        gop_id = gop_id, \
                                        video_stream_id = 0, \
                                        wf_id = 0, \
                                        frame_h=frame_h, \
                                        frame_w=frame_w, \
                                        frame_rate=SimParams.FRAME_RATE, \
                                        priority = priority_range[fix])
            
            gop_instance_frames.append(frame_task)
        
        
        
        # save the generated frames
        self.mpeg_frames = gop_instance_frames
        
        # calculate some gop level stats
        self.calculateStats()




def multiprocessing_job_instance(each_res):
    
    for each_seed in RANDOM_SEEDS:
        print "==============================================="
        print "seed: ", each_seed
        print "res: ", each_res
        print "==============================================="
        
        random.seed(each_seed)
        np.random.seed(each_seed)
        
        # dump fnames
        res_str = str(each_res[0]) + "x" + str(each_res[1])
        fname_prefix = "__s%d_G%d" % (each_seed, args.num_gops)    
        vidworkload_data_fname = EXP_DATADIR + "vidworkload_data_res" + res_str + "_" + fname_prefix + ".js"
                
        MSWV = MPEG2SyntheticWorkloadValidator(seed=each_seed, num_gops=args.num_gops, vid_res=each_res)
        MSWV.generateMultipleGoPs()
        MSWV.dump_video_workload_stats(vidworkload_data_fname)
        
        print ""
        print "-- FINISHED --"
        print "==============================================="




#################################################
# MAIN - start the generation and validation
#################################################
parser = argparse.ArgumentParser(__file__, description="Generate MPEG GoP/frame workloads")
parser.add_argument("--seed", "-w", help="seed", type=int, default=1234)
parser.add_argument("--num_gops", help="num of gops", type=int, default=8)


args = parser.parse_args()

jobs = []

#######################
# temp fixed settings #
# args.seed = 1234
# args.num_gops = 3
# vid_resolution_list = [(1280,720)



vid_resolution_list = [(1280,720), (720,576), (544,576), (528,576), (480,576), (426,240), (320,240), (240,180)]


#######################



# print "args.seed :" + str(args.seed)
# print "args.num_gops :" + str(args.num_gops)
# print "vid_res :" + str(vid_resolution_list) 

# create and dump
jobs = []
for each_res in vid_resolution_list:        
    # create a thread
    p = multiprocessing.Process(target=multiprocessing_job_instance, args=(each_res, ))
    jobs.append(p)


# start the processes
for p in jobs:
    p.start()

# exit the completed processes
for p in jobs:
    p.join()

