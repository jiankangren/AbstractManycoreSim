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

import simpy

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

## local imports
from SimParams import SimParams
from AdaptiveGoPGenerator import AdaptiveGoPGenerator
from AdaptiveGoPGenerator_v2 import AdaptiveGoPGenerator_v2

# pregen data files
from libApplicationModel.DataPreloader import DataPreloader 
import libApplicationModel.HEVCWorkloadParams as HEVCWLP
from libApplicationModel.HEVCFrameTask import HEVCFrameTask

EXP_DATADIR = "../experiment_data/workload_validation/"
RANDOM_SEEDS = [81665, 33749, 43894, 26358, 80505, 83660, 22817, 70263, 29917, 26044]

# testbench class for hevc frame
class HEVCSyntheticWorkloadValidator():
    
    def __init__(self, seed, num_gops, vid_res, movie_type):
        
        self.env = simpy.Environment()
        
        self.seed = seed
        self.num_gops = num_gops
        self.vid_res = vid_res
        self.movie_type = movie_type
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
    
    def generateMultipleGoPs(self, nBmax, N):          
        print "generateMultipleGoPs:: SEED === " + str(self.seed)        
        random.seed(self.seed)
        np.random.seed(self.seed)
        
        task_start_id = 0
        for gid in xrange(self.num_gops):
            GoP_obj = HEVCGoP_TB(self.env, nBmax, N,
                                 task_start_id, gid, self.vid_res,  
                                 self.movie_type,
                                 )
            
            GoP_obj.generateHEVCGoP()
            self.generated_gops_list.append(GoP_obj)
            print "finished : ", gid
            
            task_start_id += N
    
    
    def dump_statistics(self, gop_fname, fr_fname):
        
        gop_data_fname = gop_fname
        frame_data_fname = fr_fname
        
        gop_data = {
                'contig_bframes' : [],
                'numP' : [],
                'numB' : [],
                'refdist' : []
        }
        
        # get gop data
        for each_gop in self.generated_gops_list:
            gop_data['contig_bframes'].extend(each_gop.num_contiguous_b_frames)
            gop_data['numP'].append(each_gop.num_P)
            gop_data['numB'].append(each_gop.num_B)
            gop_data['refdist'].extend(each_gop.ref_fr_dist)        
        
        # get frame level data
        frame_data = {
                      'trackvalidate_prop_cu_sizes' : {
                                                       "intra" : {64:0, 32:0, 16:0, 8:0, 4:0}, 
                                                       "inter" : {64:0, 32:0, 16:0, 8:0, 4:0}
                                                      },
                                                       
                      'trackvalidate_prop_cu_types' : {
                                                       "I" : {"ICU":0, "PCU":0, "BCU":0, "SkipCU":0},
                                                       "P" : {"ICU":0, "PCU":0, "BCU":0, "SkipCU":0},
                                                       "B" : {"ICU":0, "PCU":0, "BCU":0, "SkipCU":0},
                                                       },
                      
                      'trackvalidate_cu_dectime' : {"ICU_cc":[], "PCU_cc":[], "BCU_cc":[], "SkipCU_cc":[]},
                      'trackvalidate_reffrdata' : {
                                                   "P<-I" : [],
                                                   "P<-P" : [],
                                                   "B<-I" : [],
                                                   "B<-P" : [],
                                                   "B<-B" : []                                                   
                                                   },
                      
                      'trackvalidate_frdectime' : {
                                                   "I" : [], "P" : [], "B" : []
                                                   },
                                             
                      'trackvalidate_frencsize' : {
                                                   "I" : [], "P" : [], "B" : []
                                                   }
                      
                      }
        
        
        # frame-level, data
        for each_gop in self.generated_gops_list:
            for each_frame in each_gop.hevc_frames:
                ftype = each_frame.get_frameType()
                # trackvalidate_prop_cu_sizes
                if ftype in ["I"]:
                    for k,v in each_frame.trackvalidate_prop_cu_sizes.iteritems():
                        frame_data['trackvalidate_prop_cu_sizes']['intra'][k]+=v
                elif ftype in ["P", "B"]:
                    for k,v in each_frame.trackvalidate_prop_cu_sizes.iteritems():
                        frame_data['trackvalidate_prop_cu_sizes']['inter'][k]+=v
                else:
                    sys.exit("unknown ftype = " + str(ftype))
                
                # trackvalidate_prop_cu_types
                #pprint.pprint(each_frame.trackvalidate_prop_cu_types)                
                for k,v in each_frame.trackvalidate_prop_cu_types.iteritems():
                    frame_data['trackvalidate_prop_cu_types'][ftype][k]+=v
                
                # trackvalidate_cu_dectime
                for k,v in each_frame.trackvalidate_cu_dectime.iteritems():
                    frame_data['trackvalidate_cu_dectime'][k].extend(v)
                
                # trackvalidate_reffrdata
                for each_parent_node, payload in each_frame.trackvalidate_reffrdata.iteritems():
                    parent_ftype = each_parent_node[0]
                    refdata_dir_k = "%s<-%s" % (ftype, parent_ftype)
                    frame_data['trackvalidate_reffrdata'][refdata_dir_k].append(payload)
                    
                # frame size (encoded) and decoding time
                if ftype == "I":
                    frame_data['trackvalidate_frencsize']["I"].append(each_frame.get_mpeg_tasksize())
                    frame_data['trackvalidate_frdectime']["I"].append(each_frame.get_computationCost())
                elif ftype == "P":
                    frame_data['trackvalidate_frencsize']["P"].append(each_frame.get_mpeg_tasksize())
                    frame_data['trackvalidate_frdectime']["P"].append(each_frame.get_computationCost())
                elif ftype == "B":
                    frame_data['trackvalidate_frencsize']["B"].append(each_frame.get_mpeg_tasksize())
                    frame_data['trackvalidate_frdectime']["B"].append(each_frame.get_computationCost())
                else:
                    sys.exit("frsize- unknown ftype = " + str(ftype))
                
                # debug     
                #if ftype == "B":            
                #    print ftype, each_frame.get_frameIXinGOP(),  each_frame.trackvalidate_reffrdata
                
        # write out (gop data)
        logfile=open(gop_data_fname, 'w')
        json_data = json.dumps(gop_data)
        logfile.write(json_data)
        
        # write out (frame data)
        logfile=open(frame_data_fname, 'w')
        json_data = json.dumps(frame_data)
        logfile.write(json_data)
        
        

# testbench class for hevc gop
class HEVCGoP_TB():
    def __init__(self, env, nBmax, N,
                 task_start_id,gid, vid_res,  
                 movieType = 'DOC',
                 ):
        
        # gop-level stats
        self.env = env
        self.movieType = movieType
        self.N = N
        self.nBmax = nBmax
        self.task_start_id = task_start_id
        self.gop_id = gid
        self.vid_res = vid_res        
        
        # to calculate
        self.num_contiguous_b_frames = [] # different numbers of contiguous frames
        self.num_P = None
        self.num_B = None
        self.ref_fr_dist = [] # different numbers of ref dist
        
        # frames in gop
        self.gop_seq = None        
        self.hevc_frames = []
    
    
    
    def calculateStats(self):
        # contig b-frames
        self.num_contiguous_b_frames = []
        splited_gop = self.gop_seq[1:].split("P")
        for each_sp_gop in splited_gop:
            if len(each_sp_gop) > 0:
                self.num_contiguous_b_frames.append(len(each_sp_gop))
        
        # P/B counts
        self.num_P = self.gop_seq.count("P")
        self.num_B = self.gop_seq.count("B")
        
        
        
        
        
    
    def generateHEVCGoP(self):        
        
        gop_size_N = self.N 
        nBmax = self.nBmax
        movie_type = self.movieType        
        task_start_id = self.task_start_id
        gop_id = self.gop_id
        unique_gop_start_id = gop_id                                                                                                              
        frame_h =  self.vid_res[0]       
        frame_w = self.vid_res[1]
        
        priority_range = range(1,100) # dummy
        strm_resolution = frame_h*frame_w 
#         n_frame_tile_rows = random.choice(range(2,SimParams.HEVC_PICTURE_SPECIFIC_LIMITS[strm_resolution]['max_tiles_rows'],1))
#         n_frame_tile_cols = random.choice(range(2,SimParams.HEVC_PICTURE_SPECIFIC_LIMITS[strm_resolution]['max_tiles_cols'],1))
#         n_frame_slices = n_frame_tile_rows*n_frame_tile_cols
        n_frame_slices = 1
        
        ctu_size = (SimParams.HEVC_CTU_SIZE)
        #n_frame_tiles = n_frame_tile_rows*n_frame_tile_cols
        n_frame_tiles = 1
        total_num_ctus = int(float(strm_resolution)/float(ctu_size))
        
        #n_ctus_per_slice = self._get_num_ctus_per_slice(n_frame_slices, total_num_ctus)
        n_ctus_per_slice = [total_num_ctus]
       
        #frame_slice_info = self.calc_hevc_slices_constantslicetype(n_frame_slices)
        frame_slice_info = tmp_fr_slice_info = {
                   "I" : {'interleaved_slice_types' : ['Is']},
                   "P" : {'interleaved_slice_types' : ['Ps']},
                   "B" : {'interleaved_slice_types' : ['Bs']},
                   }
        
        
        # only when using probabilistic gop model
        gopprobmodel_fixed_GoPSize_N =  gop_size_N
        gopprobmodel_fixed_nBMax = nBmax
        gopprobmodel_fixed_movietype = movie_type # @UndefinedVariable
                    
        gop_instance_frames = []   # reset            
        unique_gop_id = gop_id
        
        pfr_num_refs = 1
        bfr_num_refs = [1,2]
        
        
        # generate a gop structure            
        AGG = AdaptiveGoPGenerator_v2(gopprobmodel_fixed_nBMax, gopprobmodel_fixed_GoPSize_N, 
                                    SimParams.HEVC_ADAPTIVEGOPGEN_PARAM_PFRAME_REFS,
                                    SimParams.HEVC_ADAPTIVEGOPGEN_PARAM_BFRAME_REFS,
                                    movieType=gopprobmodel_fixed_movietype
                                  )
    
        
        AGG.verifyAndRecreateGoP() # this will create a valid gop  (brute-force checking)
        
        # calculate reference distance of nodes
        ref_distance_list = []
        for each_node in AGG.get_networkxDG().nodes():    
            if "B" in each_node:       
                for each_parent in AGG.get_networkxDG().predecessors(each_node):
                    ref_dist = np.abs(AdaptiveGoPGenerator_v2.nxLabel2Frame(each_node)['fix'] - AdaptiveGoPGenerator_v2.nxLabel2Frame(each_parent)['fix'])
                    ref_distance_list.append(ref_dist)
                    
                    if ref_dist > 3: # checking
                        print each_node, each_parent, AGG.get_gopSeq()
                        sys.exit()
            else:
                pass
                
        self.ref_fr_dist = ref_distance_list      
        
        
        gop_sequence = AGG.get_gopSeq()
        self.gop_seq = gop_sequence
        gop_frame_dec_order = AGG.getDecodingOrder()
        print gop_sequence, len(gop_sequence), n_frame_tiles 
        
        # construct task ids
        gop_task_ids = range(task_start_id, task_start_id+len(gop_sequence))  
        
        #print gop_task_ids
        AGG.initialiseInternalStructures(gop_task_ids)                      
            
        for frame_id, each_frame in enumerate(gop_sequence):
            frame_task = HEVCFrameTask(env = self.env,
                                        #id = (((each_gop_id) * len(gop_sequence) + frame_id) + task_start_id), \
                                        id = gop_task_ids[frame_id],
                                        frame_type = str(each_frame),
                                        frame_ix_in_gop = frame_id,
                                        unique_gop_id = unique_gop_id,
                                        gop_id = gop_id,
                                        gop_struct = gop_sequence,
                                        video_stream_id = 0,
                                        wf_id = 0,
                                        frame_h=frame_h,
                                        frame_w=frame_w,
                                        video_genre = gopprobmodel_fixed_movietype,
                                        priority = priority_range[frame_id],
                                        num_slices_per_frame = n_frame_slices,
                                        num_tiles_per_frame =  n_frame_tiles,
                                        interleaved_slice_types = frame_slice_info[str(each_frame)]['interleaved_slice_types'],
                                        num_ctu_per_slice=n_ctus_per_slice,
                                        adaptiveGoP_Obj=AGG,     
                                        load_data_from_file = SimParams.HEVC_LOAD_FRAME_DATAFILE,
                                        gop_decode_frame_order = gop_frame_dec_order,
                                        gop_decode_order_ix = gop_frame_dec_order[0].index(frame_id),   
                                        enable_workload_validation = True                                                                                                                            
                                        )
            
            gop_instance_frames.append(frame_task)
            
            assert(n_frame_tiles == frame_task.getNumSubTasksTiles()), \
             ", generateHEVCFrameTaskSet:: error in tile generation : %d, %d" % (n_frame_tiles, frame_task.getNumSubTasksTiles())

            # calculate the data dependency
            #task_level_decoded_data_output = self.hevcframelevel_calc_expected_data_to_children(gop_instance_frames, task_level_decoded_data_output)
            
            task_start_id =  gop_task_ids[-1]+1           
        
        # populate the data deps for each task in task list
        #self.populate_expected_data_to_children(task_level_decoded_data_output)
        
        # see if we can flush the frame block-level info
        self.hevc_flush_frame_block_level_data()
        
        # save the generated frames
        self.hevc_frames = gop_instance_frames
        
        # calculate some gop level stats
        self.calculateStats()

            
    # for each task, we delete the frame block level info.
    def hevc_flush_frame_block_level_data(self):
        if SimParams.HEVC_MODEL_FLUSH_FRAMEBLOCK_INFO == True:
            for each_task in self.hevc_frames:
                #print "BEFORE : hevc_flush_frame_block_level_data : blk_len, tid: ", len(each_task.frame_block_partitions.keys()), each_task.get_id()
                each_task.hack_abstract__frame_block_partitions()
                #print "AFTER : hevc_flush_frame_block_level_data : blk_len, tid: ", len(each_task.frame_block_partitions.keys()), each_task.get_id()
                
        else:
            pass
        
        collected = gc.collect()
        print "Garbage collector: collected %d objects." % (collected)
    


#################################################
# MAIN - start the generation and validation
#################################################
parser = argparse.ArgumentParser(__file__, description="Generate HEVC GoP/frame workloads")
parser.add_argument("--seed", "-w", help="seed", type=int, default=123)
parser.add_argument("--num_gops", help="num of gops", type=int, default=3)
parser.add_argument("--gop_len", help="gop length", type=int, default=36)
parser.add_argument("--nbmax", help="max contig. B fr", type=int, default=4)

args = parser.parse_args()

fname_prefix = "__s%d_G%d_N%d_B%d" %(args.seed, args.num_gops, args.gop_len, args.nbmax)

gop_data_fname = EXP_DATADIR + "gop_data_seed" + fname_prefix + "_.js"
frame_data_fname = EXP_DATADIR + "frame_data_seed" + fname_prefix + "_.js"

#DataPreloader.preload_data_files(fname="../hevc_pregen_data_files/pregen_pus/hevc_probmodel_generate_PU_per_CTU_200ctus.p")
DataPreloader.preload_data_files(fname="../hevc_pregen_data_files/pregen_pus/hevc_probmodel_generate_PU_per_CTU_10ctus.p")

jobs = []
        
#p = multiprocessing.Process(target=plot_GoPLateness)
#jobs.append(p)

HSWV = HEVCSyntheticWorkloadValidator(seed=args.seed, num_gops=args.num_gops, vid_res=[720, 1280], movie_type='DOC')
HSWV.generateMultipleGoPs(args.nbmax, args.gop_len)
HSWV.dump_statistics(gop_data_fname, frame_data_fname)





