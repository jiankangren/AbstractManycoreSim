import pprint
import sys, os
import random
import time
import math
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from collections import OrderedDict
from scipy.stats import rv_discrete
from scipy.stats import exponweib
import scipy.stats as ss
import itertools

## local imports
from Task import Task
from SimParams import SimParams
from MPEG2FrameTask import MPEG2FrameTask
from AdaptiveGoPGenerator import AdaptiveGoPGenerator

# pregen data files
from libApplicationModel.DataPreloader import DataPreloader 
import libApplicationModel.HEVCWorkloadParams as HEVCWLP
from util_scripts.generate_hevc_frame_culevel import getCTUsForVideo, varyProbabilities_NormalDist



class HEVCFrameTask(MPEG2FrameTask):
    
    def __init__(self, env, id, 
                 frame_h= SimParams.FRAME_DEFAULT_H, \
                 frame_w = SimParams.FRAME_DEFAULT_W, \
                 frame_rate = SimParams.FRAME_RATE, \
                 frame_type = "I", \
                 task_granularity = "frame", \
                 frame_ix_in_gop = 0, \
                 unique_gop_id = 0, \
                 gop_id = 0, \
                 gop_struct = SimParams.GOP_STRUCTURE, \
                 video_stream_id = None, \
                 wf_id = None, \
                 priority = None,                  
                 
                 # additional for hevc
                 video_genre = None,
                 gop_decode_frame_order = None, # (fix-order, ftype-order)
                 gop_decode_order_ix = None, # the frame_ix according to decode order
                 
                 num_ctu_per_slice = None,
                 num_slices_per_frame=None,
                 num_tiles_per_frame=None,
                 interleaved_slice_types=None,
                 adaptiveGoP_Obj = None,
                 load_data_from_file = False,
                 hevc_cc = None,
                 construct_partitions = True,    
                 tile_parent_frame_task_id = None,
                 precalc_fr_sizes=None,
                 enable_workload_validation = False
                 ):
        
        
        MPEG2FrameTask.__init__(self, env, id, 
                                frame_h, frame_w, frame_rate, frame_type, frame_ix_in_gop, 
                                unique_gop_id, gop_id, gop_struct, 
                                video_stream_id, wf_id, 
                                priority,
                                calc_deps=False,
                                calc_cc=False,
                                calc_pri=False)
        
        self.type = "HEVCFrame-"+self.frame_type
        self.task_granularity = task_granularity # frame || tile || slice || block         
        
        # decoding order
        self.gop_frame_decoding_order = gop_decode_frame_order
        self.gop_decode_order_ix = gop_decode_order_ix
        
        ##  block level specs
        # we assume that all blocks in a slice are the same type
        self.block_level_info = {} # a structure containing number of blocks per different block type          
                
        self.video_genre = video_genre
        
        # frame level priority (Ip>Pp>Bp)
        self.frame_priority = self.calc_FramePriorityInsideGOP(self.frame_ix_in_gop, adaptiveGoP_Obj, gopseq=self.gop_structure)
       
        ## deadline calculation
        dl = (1.0/self.frame_rate)
        self.set_deadline(dl)   # this will be adjusted later    
        self.set_timeLeftTillDeadline(dl)    
        
        self.end_to_end_deadline = (float(len(self.gop_structure))/float(self.frame_rate))
        
        # total memory required per uncompressed frame
        max_mem = ((self.frame_h * self.frame_w) * 24)/8  # 24 bit, rgb, assume I_size = P_size = B_size  (in bytes)                                                                  )
        self.set_maxMemConsumption(max_mem)
                
        self.absDeadline = None
        self.completedTaskSize = max_mem
        
        # worst case execution times of different types of frames - stored for later use
        self.wccIFrame = None
        self.wccPFrame = None
        self.wccBFrame = None
        
        self.tile_observed_wccc = None
        
        # avg case execution times of different types of frames - stored for later use
        self.avgccIFrame = None
        self.avgccPFrame = None
        self.avgccBFrame = None
        
        # verification
        self.verify_num_ctus_generated = 0  
        
        # analytical wcet/wcrt
        self.analytical_wcet = None
        self.analytical_wcrt_with_deps = None
        
        # task size
        self.mpeg_tasksize = self.calc_encoded_mpegframe_size()
        #print self.mpeg_tasksize
        
        # HEVC interleaved slice types
        self.interleaved_slice_types=interleaved_slice_types
        
        # HEVC - number of ctu blocks per slice
        self.num_ctu_per_slice = num_ctu_per_slice
        
        # HEVC frames can be split into tiles
        self.number_of_tiles = num_tiles_per_frame
        self.tile_parent_frame_task_id = tile_parent_frame_task_id
        self.hevc_tile_id = None
        
        # Heirarchical B groups
        self.bpyramid_ix  = None
        self.bpyramid_primary_task = None
        
        # HEVC slices
        self.num_slices_per_frame = num_slices_per_frame
        
        ## dependency related info ##
        # populated later
        self.frame_dependencies = None
        self.set_dependencies(None) # dependent tasks
        self.which_frames_needs_me = None
        self.which_tasks_needs_me = None
        self.my_closest_children = None
        self.my_closest_parent = None
        self.non_dep_frames  = None
        self.possible_interfering_frame = None 
        
        # items in this dict will get removed as the deps come in
        self.outstanding_deps_parent_tids = {} 
        
        # how much decoded data do I need from my parent tasks
        # this gets populated when calculating the PU level deps,        
        self.expected_data_from_parents = {}       
        self.expected_data_from_parents_slicelevel = {}
        
        # how much decoded data do I need to send to my child tasks
        self.expected_data_to_children = {}
        self.expected_data_to_children_slicelevel = {}
        
        ## tracking for workload validation purposes (these are CU level stats)
        self.enable_workload_validation = enable_workload_validation
        if enable_workload_validation == True:
            self.trackvalidate_prop_cu_sizes = {64:0, 32:0, 16:0, 8:0, 4:0}
            self.trackvalidate_prop_cu_types = {"ICU":0, "PCU":0, "BCU":0, "SkipCU":0}
            self.trackvalidate_cu_dectime = {"ICU_cc":[], "PCU_cc":[], "BCU_cc":[], "SkipCU_cc":[]}
            self.trackvalidate_reffrdata = {} # k=parent_id_type, v=amount of data
        
        # related to dependencies        
        # HEVC adaptive gop obj
        self.adaptiveGoP_Obj = adaptiveGoP_Obj
        if (self.adaptiveGoP_Obj !=None):
            self.populate_FrameDependencies(self.adaptiveGoP_Obj, frame_ix_in_gop)
        
        # HEVC slice/block/tile partitions
        self.frame_block_partitions=None 
        self.frame_tile_partitions=None
        
        if (load_data_from_file == True):
            loaded_data_obj =   self.load_frame_data(wf_id, 
                                                     video_stream_id, 
                                                     unique_gop_id, 
                                                     frame_ix_in_gop, 
                                                     SimParams.HEVC_FRAME_GENRAND_SEED)
            self.frame_block_partitions = loaded_data_obj['frame_block_partitions'] 
            self.frame_tile_partitions = loaded_data_obj['frame_tile_partitions']
            cc = loaded_data_obj['cc']
            self.expected_data_from_parents = loaded_data_obj['expected_data_from_parents']    
            assert (cc > 0), ": cc calculation incorrect"
            
        else:
            if construct_partitions == True:                                        
                (self.frame_block_partitions, 
                 self.frame_tile_partitions, cc) = self.construct_slices_and_tiles()
                assert (cc > 0), ": cc calculation incorrect"
            else:
                self.frame_block_partitions = None 
                self.frame_tile_partitions = None
                   
        ## task level rts specs - need to calculate         
        if hevc_cc == None:
            self.set_computationCost(cc)
            self.set_remainingComputationCost(cc)
            self.set_timeLeftTillCompletion(cc)
        
        ## related to dep based scheduling ##
        if construct_partitions == True:
            self.current_processing_unit = {'slice_id':0 , 'ctu_id':0, 'rem_cc': self.frame_block_partitions[0]['ctus'][0]["cc"]} # slice, ctu, rem_cc
            #pass
        else:
            self.current_processing_unit = {'Notimplemented' : 0}
        
        
        ## stuff required for the memory reduction hack
        self.hack_abstract__tile_level_block_partitions = {}
        self.hack_abstract__num_ctus_in_tile = {}
        
        
    
    def __repr__(self):
        debug = "<Task "         
        debug += " type=" + self.type
        debug += " id=" + str(self.id) 
        debug += " cc=" + str(self.computationCost)
        debug += " wcc=" +  str(self.worstCaseComputationCost)
        #debug += " mmc=" + str(self.maxMemConsumption)
        debug += " sdt=" + str(self.get_scheduledDispatchTime())
        debug += " rt=" + str(self.releaseTime)
        #debug += " d=" + str(self.deadline)
        #debug += " p=" + str(self.period)
        debug += " pri=" + str(self.priority)
        debug += " ugid=" + str(self.unique_gop_id)
        debug += " ntiles=" + str(self.getNumSubTasksTiles())
        #debug += " stat=" +  str(self.status)
        #debug += " tltc=" +  str(self.timeLeftTillCompletion)
        #debug += " tltd=" +  str(self.timeLeftTillDeadline)
        #debug += " st=" +  str(self.taskStartTime)
        debug += " tct=" +  str(self.taskCompleteTime)
        #debug += " mdf=" +  str(self.missedDeadlineFlag)
        debug += " dt=" +  str(self.dispatchTime)        
        
        # frame specific
        #debug += " pgid=" +  str(self.parent_gop_id)
        #debug += " frtyp=" +  str(self.frame_type)
        debug += " fr_gop_ix=" +  str(self.frame_ix_in_gop )
        #debug += " frpr=" +  str(self.frame_priority)
        debug += " dep=" +  str(self.dependencies)
        #debug += " fr_dep=" +  str(self.frame_dependencies)
        #debug += " wh_fnm=" +  str(self.which_frames_needs_me)
        debug += " wh_tnm=" +  str(self.which_tasks_needs_me)
        
        
        # stream specific
        debug += " wfid=" + str(self.wf_id)
        debug += " vid=" + str(self.video_stream_id)        
        debug += " />"
    
        return debug
    
    
    def _debugLongXML(self):
        debug = "<Task "         
        debug += " type='" + self.type+ "'"
        debug += " id='" + str(self.id)+ "'" 
        debug += " cc='" + str(self.computationCost)+ "'"
        debug += " mmc='" + str(self.maxMemConsumption)+ "'"
        debug += " rt='" + str(self.releaseTime)+ "'"
        debug += " d='" + str(self.deadline)+ "'"
        debug += " p='" + str(self.period)+ "'"
        debug += " pri='" + str(self.priority)+ "'"
        debug += " st='" +  str(self.taskStartTime)+ "'"
        debug += " tct='" +  str(self.taskCompleteTime)+ "'"
        debug += " sdt='" +  str(self.scheduledDispatchTime)+ "'"
        debug += " wcc='" +  str(self.worstCaseComputationCost)+ "'"
        
        # frame specific
        debug += " pgid='" +  str(self.parent_gop_id)+ "'"
        debug += " ugid='" +  str(self.unique_gop_id)+ "'"        
        debug += " fr_gop_ix='" +  str(self.frame_ix_in_gop )+ "'"
        debug += " frpr='" +  str(self.frame_priority)+ "'"
        debug += " fps='" +  str(self.frame_rate)+ "'"
        debug += " dep='" +  str(self.dependencies)+ "'"
        debug += " fr_dep='" +  str(self.frame_dependencies)+ "'"
        debug += " wh_fnm='" +  str(self.which_frames_needs_me)+ "'"
        debug += " wh_tnm='" +  str(self.which_tasks_needs_me)+ "'"
        debug += " data_frm_prn='" +  str(self.expected_data_from_parents)+ "'"
        debug += " data_to_ch='" +  str(self.expected_data_to_children)+ "'"
        
        # stream specific
        debug += " wfid='" + str(self.wf_id)+ "'"
        debug += " vid='" + str(self.video_stream_id)+ "'"
        debug += " res='" + str(self.frame_h)+"x"+str(self.frame_w)+ "'"
                
        debug += " />"
    
        return debug
    
    
    def _debugShortLabel(self):
        debug = "<Task "
        debug += " id=" + str(self.id)
        debug += " frtyp=" +  str(self.frame_type)        
        debug += " dep=" +  str(self.dependencies).replace(","," ")
        #debug += " fr_dep=" +  str(self.frame_dependencies).replace(","," ")
        #debug += " wh_fnm=" +  str(self.which_frames_needs_me).replace(","," ")
        debug += " wh_tnm=" +  str(self.which_tasks_needs_me).replace(","," ")
        debug += " ctu=" +  (self.getCurrentlyProcessingUnitRef_Label())
        return debug
    
    # minimal version of to-string (for schedulability debug)
    def getSchedulability_toString(self):
        debug = ""
        debug += " id='" + str(self.id) + "'"
        debug += " gix='" + str(self.frame_ix_in_gop)+ "'"
        debug += " wfid='" + str(self.wf_id)+ "'"
        debug += " vid='" + str(self.video_stream_id)+ "'"
        debug += " pc='" + str(self.get_processingCore())+ "'"
        debug += " cc='" + str(self.computationCost)      + "'"  
        debug += " d='" + str(self.deadline)+ "'"
        debug += " p='" + str(self.period)+ "'"
        debug += " pri='" + str(self.priority)+ "'"
        debug += " dt='" + str(self.dispatchTime)  + "'"      
        
        return debug
    
    
    def getTaskWFSTRMId(self):
        name = "t_" + str(self.wf_id) + "_" + str(self.video_stream_id) + "_" + str(self.frame_ix_in_gop)
        return name
    
    
    
    # getters
    def get_expected_data_from_parents(self):
        return self.expected_data_from_parents        
    def get_expected_data_to_children(self):
        return self.expected_data_to_children
    
    def get_frame_tile_partitions(self, tid=None):
        if tid == None:
            return self.frame_tile_partitions
        else:
            if tid<len(self.frame_tile_partitions):
                return self.frame_tile_partitions[tid]
            else:
                sys.exit("Error: get_frame_tile_partitions:: invalid tile id")
                
    
    def get_gop_frame_dec_order_fix(self):
        return self.gop_frame_decoding_order[0]
    def get_gop_frame_dec_order_ftype(self):
        return self.gop_frame_decoding_order[1]
    
    def get_frame_block_partitions(self):
        return self.frame_block_partitions
    def get_adaptiveGoP_Obj(self):
        return self.adaptiveGoP_Obj
    
    def get_video_genre(self):
        return self.video_genre
    
    def get_hevc_tile_id(self):
        return self.hevc_tile_id
    
    def get_bpyramid_ix(self):
        return self.bpyramid_ix
    
    def get_bpyramid_primary_task(self):
        return self.bpyramid_primary_task
    
    
    # setters
    def set_expected_data_from_parents(self, d):
        self.expected_data_from_parents = d        
    def set_expected_data_to_children(self, d):
        self.expected_data_to_children = d
    
    def update_expected_data_to_children(self, k,v):
        self.expected_data_to_children[k]=v
        
    def update_expected_data_from_parent(self, k,v):
        self.expected_data_from_parents[k]=v
    
    def set_frame_block_partitions(self, fbp):
        self.frame_block_partitions = fbp
    def set_frame_tile_partitions(self, ftp):
        self.frame_tile_partitions = ftp

    def set_hevc_tile_id(self, tid):
        self.hevc_tile_id = tid
    
    
    def set_bpyramid_ix(self, pix):
        self.bpyramid_ix = pix
        
    def set_bpyramid_primary_task(self, v):
        self.bpyramid_primary_task = v
    
    # assume constant GOP structure 
    # IBBPBBPBBPBB (display order)   
    @staticmethod 
    def calc_FramePriorityInsideGOP(ix, adaptiveGoP_Obj, gopseq="IPBBPBBPBBBB"):        
        # priorites are set according to topological order
        if adaptiveGoP_Obj == None:
            return None
        else:
            gop_len = len(gopseq)
            decoding_order_ix = adaptiveGoP_Obj.getDecodingOrder()[0]
            priority_order = [-1]*len(gopseq)
            for each_frame_ix, eachframe_type in enumerate(gopseq):
                dec_ix = decoding_order_ix.index(each_frame_ix)
                priority_order[each_frame_ix] = (gop_len-dec_ix)
            
            return priority_order[ix]
    
    # each frame in the GOP has dependencies
    # I -> none
    # P -> I or P    (1 ref frame)
    # B -> I/P/B frames (always at least 2 ref frames)
    # nx_DG (networkX dependency graph)     
    def calc_FrameDependencies(self, gop_ix, task_id):
        dependencies = {
               'dep_gop_frames_ixs'                 : None,
               'dep_task_ids'                       : None,
               'which_task_needs_current_task'      : None,
               'which_frame_needs_current_frame'    : None,
               'my_closest_children'                : None,
               'my_closest_parent'                  : None,
               'non_dep_frames'                     : None,
               'possible_interfering_frames'        : None,               
               }        
        return dependencies
    
    def populate_FrameDependencies(self, AGOP_obj, gop_ix):
        ':type AGOP_obj: AdaptiveGoPGenerator'        
        self.frame_dependencies = AGOP_obj.get_gop_level_dep()[gop_ix]
        self.set_dependencies(AGOP_obj.get_task_level_dep()[gop_ix]) # dependent tasks        
        self.which_frames_needs_me = AGOP_obj.get_which_frame_needs_current_frame()[gop_ix]
        self.which_tasks_needs_me = AGOP_obj.get_which_task_needs_current_task()[gop_ix]
        self.my_closest_children = AGOP_obj.get_my_closest_children()[gop_ix]
        self.my_closest_parent = AGOP_obj.get_my_closest_parent()[gop_ix]
        self.non_dep_frames  = None
        self.possible_interfering_frame = AGOP_obj.get_possible_interfering_frames()[gop_ix] 
    
        for each_p_tid in AGOP_obj.get_task_level_dep()[gop_ix]:            
            self.outstanding_deps_parent_tids[each_p_tid] = None
            
    def calc_encoded_mpegframe_size(self, param_precalc_value=None):
        size=0.0        
        if (SimParams.HEVC_GOPGEN_USEPROBABILISTIC_MODEL==True and self.video_genre!= None):            
            if param_precalc_value != None:
                size = np.random.choice(param_precalc_value[self.frame_type])
                return size
            else:
                PRE_SAMPLE_RANGE = 100            
                fr_k = self.frame_type + "-Fr"
                fr_minmax_k = self.frame_type + "-Fr-minmax"            
                frsize_minmax = HEVCWLP.HEVCWLPARAMS_IPB_FR_SIZE_PARAMS[self.video_genre][fr_minmax_k]
                frsize_range = np.linspace(frsize_minmax[0], frsize_minmax[1], PRE_SAMPLE_RANGE)               
                frsize_expweib_params = HEVCWLP.HEVCWLPARAMS_IPB_FR_SIZE_PARAMS[self.video_genre][fr_k]
                
                pdf_y = exponweib.pdf(frsize_range, 
                                      frsize_expweib_params[0], frsize_expweib_params[1],
                                      scale = frsize_expweib_params[3],
                                      loc = frsize_expweib_params[2])*1.0        
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
                                
                # calculate normalisation
                norm_probabilties = np.array(probabilities)/np.sum(probabilities)                               
                distrib = rv_discrete(values=(np.arange(len(frsize_range)), norm_probabilties))
                
                
                # checking
                if np.isnan(norm_probabilties).any():
                    print  norm_probabilties
                    print probabilities
                    sys.exit("calc_encoded_mpegframe_size:: contains NaN")
                            
                compression_ratio_index = distrib.rvs(size=1)[0]                                
                compression_ratio = frsize_range[compression_ratio_index]     
                
                assert (compression_ratio > 0), "calc_encoded_mpegframe_size :: compression ratio is zero"
                assert (compression_ratio < 1), "calc_encoded_mpegframe_size :: compression ratio is larger than 1"
                           
                size = float(self.frame_w * self.frame_h * 3) * compression_ratio # in bytes
        
        else:
            if self.frame_type == "I": size = float(self.frame_w * self.frame_h * 3) * SimParams.HEVC_COMPRESSION_RATIO_IFRAME
            elif self.frame_type == "P": size = float(self.frame_w * self.frame_h * 3) * SimParams.HEVC_COMPRESSION_RATIO_PFRAME
            elif self.frame_type == "B": size = float(self.frame_w * self.frame_h * 3) * SimParams.HEVC_COMPRESSION_RATIO_BFRAME        
                    
        return size
    
    @staticmethod
    def getPrecalc_ProbabilisticFramesize(fr_h, fr_w, vid_genre, sample_size=1000):
        fr_types = ["I", "P", "B"]
        result = {}
        for each_frtype in fr_types:
            PRE_SAMPLE_RANGE = sample_size           
            fr_k = each_frtype + "-Fr"
            fr_minmax_k = each_frtype + "-Fr-minmax"            
            frsize_minmax = HEVCWLP.HEVCWLPARAMS_IPB_FR_SIZE_PARAMS[vid_genre][fr_minmax_k]
            frsize_range = np.linspace(frsize_minmax[0], frsize_minmax[1], PRE_SAMPLE_RANGE)
            frsize_expweib_params = HEVCWLP.HEVCWLPARAMS_IPB_FR_SIZE_PARAMS[vid_genre][fr_k]
            
            pdf_y = exponweib.pdf(frsize_range, 
                                  frsize_expweib_params[0], frsize_expweib_params[1],
                                  scale = frsize_expweib_params[3],
                                  loc = frsize_expweib_params[2])*1.0        
            probabilities = pdf_y
            
            # replace NaN with the closes non-NaN
            mask = np.isnan(probabilities)
            probabilities[mask] = np.interp(np.flatnonzero(mask), 
                                            np.flatnonzero(~mask), 
                                            probabilities[~mask])                
            norm_probabilties = np.array(probabilities)/np.sum(probabilities)                                
            distrib = rv_discrete(values=(frsize_range, norm_probabilties))
            
            if np.isnan(norm_probabilties).any():
                print  norm_probabilties
                print probabilities
                sys.exit("calc_encoded_mpegframe_size:: contains NaN")
                        
            compression_ratio_index = distrib.rvs(size=sample_size)
            compression_ratio = frsize_range[compression_ratio_index]                
            size_arr = float(fr_w * fr_h) * compression_ratio
            
            result[each_frtype] = size_arr
            
            
        return result
        
    
    
    def calc_WhichFramesToDrop(self, frame_nodecode_ix):
        sys.exit("Error: HEVCFrameTask::calc_WhichFramesToDrop:: not implemented yet !")
   
    def calc_ASAP_ReleaseTime(self, ftype, frame_nodecode_ix, time_now, gop_frames):
        sys.exit("Error: HEVCFrameTask::calc_ASAP_ReleaseTime:: not implemented yet !")
            
    # the cost of the computation depends on the number+type of different slices
    def calc_FrameComputationTime(self):        
        total_ct = 0.0
        # (TEMPSOLUTION) : comp.cost is calculated at a PU level     
        for each_slice_v in self.frame_block_partitions.values():
            total_ct += np.sum([each_ctu_v['cc'] for each_ctu_v in each_slice_v['ctus'].values()])                
        return total_ct
    
    
    def construct_slices_and_tiles(self):
        # construct the blocks and slice to tile mapping
        (block_partitions, temp_total_frame_slicelvl_cc) = self.construct_block_partitions(self.interleaved_slice_types)        
        tile_partitions = self.slice_to_tile_mapping(self.interleaved_slice_types)
        return (block_partitions, tile_partitions, temp_total_frame_slicelvl_cc)
    
    
    # this is used to split the slices into PUs
    def construct_block_partitions(self, interleaved_slice_types):                
        frame_res = self.frame_h*self.frame_w        
        block_partitions = OrderedDict()
            
        # keep track of the computation cost per ctu
        temp_total_frame_slicelvl_cc = 0.0
        
        if (SimParams.HEVC_GOPGEN_USEPROBABILISTIC_MODEL==True):
            pregen_cu_cc = self._getCUComputationCostPregen_ProbModel(1000, self.video_genre, interleaved_slice_types[0])
              
        # randomly allocate blocks to slices
        ctu_id = 0
        slice_id = 0
        for num_ctu, each_slice in zip(self.num_ctu_per_slice, self.interleaved_slice_types):
            block_partitions[slice_id] = OrderedDict()
            
            if (SimParams.HEVC_GOPGEN_USEPROBABILISTIC_MODEL==True):
                (ctus_dict, 
                 total_frame_slicevl_cc, 
                 new_ctu_id) = self._generate_PU_per_CTU_fromPreloadedData_ProbabilisticModel(self.video_genre, each_slice, slice_id, 
                                                                                              frame_res, num_ctu, ctu_id, pregen_cu_cc)
                #print "finished _generate_PU_per_CTU_fromPreloadedData_ProbabilisticModel: ", self.frame_ix_in_gop
            else:
                (ctus_dict, 
                 total_frame_slicevl_cc, 
                 new_ctu_id) = self._generate_PU_per_CTU_fromPreloadedData(each_slice, slice_id, frame_res, num_ctu, ctu_id)
             
            block_partitions[slice_id] = ctus_dict            
            
            temp_total_frame_slicelvl_cc += total_frame_slicevl_cc
            ctu_id = new_ctu_id                        
            slice_id +=1
        
        return (block_partitions, temp_total_frame_slicelvl_cc)
    
    
    # allocate slices to tiles - assume equal partitions (for now)
    def slice_to_tile_mapping(self, interleaved_slice_types):
        total_slices = len(interleaved_slice_types)       
        assert(total_slices >= self.number_of_tiles), ", too less slices"
        num_slices_per_tile = float(total_slices)/float(self.number_of_tiles)
        
        if (num_slices_per_tile %1) != 0: # not a fair proportion
            rounddown_slice_tile_allocation = int(num_slices_per_tile) 
            rounddown_total_slices = self.number_of_tiles*rounddown_slice_tile_allocation
            leftover_slices = int(total_slices - rounddown_total_slices)
            assert(leftover_slices>0)
            
            # assign the equal part
            num_equal_slices_per_tile = rounddown_slice_tile_allocation
            slice_tile_allocation = [ {'slice_types' : interleaved_slice_types[x:x+num_equal_slices_per_tile],
                                       'slice_ixs' : range(x,x+num_equal_slices_per_tile)}                                         
                                     for x in xrange(0, rounddown_total_slices, num_equal_slices_per_tile)]
            
            # assign the leftover slices            
            for each_leftover_slice in xrange(leftover_slices):
                rand_slice_ix = np.random.randint(0,self.number_of_tiles) 
                slice_tile_allocation[rand_slice_ix]['slice_types'].append(interleaved_slice_types[rounddown_total_slices+each_leftover_slice])
                slice_tile_allocation[rand_slice_ix]['slice_ixs'].append(rounddown_total_slices+each_leftover_slice)
            
            
        else:      # fair proportion 
            num_slices_per_tile = int(num_slices_per_tile)          
            slice_tile_allocation = [ {'slice_types' : interleaved_slice_types[x:x+num_slices_per_tile],
                                       'slice_ixs' : range(x,x+num_slices_per_tile)}
                                     for x in xrange(0, len(interleaved_slice_types), num_slices_per_tile)]
        return slice_tile_allocation

    
    
    
    # generate all the CTUs fro the given slice
    # pu and cu terminology interchangeable in this function
    def _generate_PU_per_CTU_fromPreloadedData_ProbabilisticModel(self, vid_genre, slice_type, slice_id, 
                                                                  frame_res, num_ctus, ctu_id, pregen_cu_cc):
        ctu_size = SimParams.HEVC_CTU_SIZE # we need to split this up into the quad tree structure        
        sum_pu_cc = 0.0
        mem_size = 0.0
        
        theoretical_max_num_ctus =  int(round(float((ctu_size)*num_ctus)/float(4*4)))
        
        if(slice_type == "Is"):     possible_cu_type = ["ICU"]
        elif(slice_type == "Ps"):   possible_cu_type = ["ICU", "PCU", "SkipCU"]
        else:                       possible_cu_type = ["ICU", "PCU", "BCU", "SkipCU"]
        
        if(slice_type == "Is") : slice_pred_type = "Intra"
        else: slice_pred_type = "Inter" 
        
        fr_type_str = slice_type.replace('s','') + "-fr"
        cu_type_list = ["ICU", "PCU", "BCU", "SkipCU"]
        cu_type_probabilities = HEVCWLP.HEVCWLPARAMS_CU_TYPE_PROBABILITIES[vid_genre][fr_type_str]
        varied_cu_type_probabilities = varyProbabilities_NormalDist(cu_type_probabilities)        
        #print varied_cu_type_probabilities
        
        count_ctu_id = ctu_id
        total_frame_slicelvl_cc = 0.0        
        result_ctus = {'sltype' :  slice_type, 'ctus' : OrderedDict()}
        
        # randomly select PU size, numctus, etc from loaded data
        #all_selected_pus = np.random.choice(DataPreloader.hevc_random_ctu[vid_genre][slice_type], size=num_ctus) # @UndefinedVariable
        
        #iter_all_available_pus = itertools.cycle(DataPreloader.hevc_random_ctu[vid_genre][slice_type])
        ctu_list = getCTUsForVideo(vid_genre, slice_pred_type, total_video_pixels=frame_res, force_ctu_size=True).values()
        np.random.shuffle(ctu_list)
        iter_all_available_pus = itertools.cycle(ctu_list)
        
        #pregen_cu_cc = pregen_cu_cc
        
        #pregen_cu_dep_indexes = self._getCULevelRefFrame_ProbModel(theoretical_max_num_ctus+100) 
               
        distrib = rv_discrete(values=(np.arange(len(cu_type_list)), varied_cu_type_probabilities))     
        tmp_cutypes_ixs = distrib.rvs(size=1000)
        np.random.shuffle(tmp_cutypes_ixs)       
        pregen_rand_cutypes_ixs = itertools.cycle(tmp_cutypes_ixs)        
        
        # if there are more than 2 ref frames - need to decide which to pick for B-frames        
        if slice_type == "Bs":
            if len(self.frame_dependencies) > 2:
#                 b_rf_ixs = [i for i, f in enumerate(self.frame_dependencies) if self.gop_structure[f] == "B"]                
#                 for i in xrange(1000):                    
#                         b_fr_ix = np.random.choice([i for i, f in enumerate(self.frame_dependencies) if self.gop_structure[f] == "B"])
#                         p_fr_ix = np.random.choice([i for i, f in enumerate(self.frame_dependencies) if self.gop_structure[f] == "P"])
#                      
#                         #print b_fr_ix, p_fr_ix
#                         ref_fwdbwd_pairs.append([p_fr_ix, b_fr_ix])
#                     
#                 pregen_rand_rfixs = itertools.cycle(ref_fwdbwd_pairs)
#                  
#             else:
#                 pregen_rand_rfixs = itertools.cycle([[0,1]])
                 
                ref_fwdbwd_pairs = []
                for i in xrange(1000):
                    fwd_rnd_rfix = np.random.choice(range(len(self.frame_dependencies)))
                    bwd_rnd_rfix = np.random.choice([x for x in range(len(self.frame_dependencies)) if x != fwd_rnd_rfix])
                    ref_fwdbwd_pairs.append([fwd_rnd_rfix, bwd_rnd_rfix])                        
                pregen_rand_rfixs = itertools.cycle(ref_fwdbwd_pairs)
            else:
                pregen_rand_rfixs = itertools.cycle([[0,1]])
#         
        
        # we need to decide if Skip will have bwd refs or not, this boolean array will be used
        # x% of the time skip will have bwd refs pregenerated for speed
        rand_skip_bwd_select = []
        if slice_type == "Bs":
            for i in xrange(1000):
                if np.random.rand() < 0.5: rand_skip_bwd_select.append(True)
                else: rand_skip_bwd_select.append(False)            
            pregen_rand_skip_bwd_select = itertools.cycle(rand_skip_bwd_select)
        
        #pregen_cu_cc_Icu = np.random.choice(pregen_cu_cc["ICU"], size=theoretical_max_num_ctus+100)  # @UndefinedVariable
        #pregen_cu_cc_Pcu = np.random.choice(pregen_cu_cc["PCU"], size=theoretical_max_num_ctus+100) # @UndefinedVariable
        #pregen_cu_cc_Bcu = np.random.choice(pregen_cu_cc["BCU"], size=theoretical_max_num_ctus+100) # @UndefinedVariable
        #pregen_cu_cc_Skipcu = np.random.choice(pregen_cu_cc["SkipCU"], size=theoretical_max_num_ctus+100) # @UndefinedVariable
                
        ##### testing ####
#         pregen_cu_cc = {
#                         "ICU" : [0.001] * (theoretical_max_num_ctus+100),
#                         "PCU" : [0.001] * (theoretical_max_num_ctus+100),
#                         "BCU" : [0.001] * (theoretical_max_num_ctus+100),
#                         "SkipCU" : [0.001] * (theoretical_max_num_ctus+100),
#                         }
#         pregen_cu_dep_indexes = [0] * (theoretical_max_num_ctus+100)            
#         pregen_rand_cutypes_ixs = [0]*(theoretical_max_num_ctus+100)
#         
        ######################
        
        #pprint.pprint(pregen_cu_cc)
        tmp_all_rand_pu_types = []
        tmp_all_rand_pu_sizes = []        
        
        
        # all ctus in the slice
        count_cu = 0
        #for each_pu_sizes in all_selected_pus :
        for i_ctu in xrange(num_ctus): 
            #self._verify_pu_sizes(ctu_size, selected_pu_sizes)            
            each_pu_sizes = iter_all_available_pus.next()
            #each_pu_sizes = np.random.choice(ctu_list)
            
            #selected_pu_sizes = each_pu_sizes['pu_list']            
            #assert (np.sum([p[0]*p[1] for p in selected_pu_sizes]) == SimParams.HEVC_CTU_SIZE)
            
            selected_pu_sizes = each_pu_sizes
            assert (np.sum([p*p for p in selected_pu_sizes]) == SimParams.HEVC_CTU_SIZE)
            
            cum_pix = 0 # cumulative pixels count
            for each_pu_ix, each_pu in enumerate(selected_pu_sizes):
                #selected_pu_size =   each_pu                          
                selected_pu_size =   [each_pu, each_pu]
                selected_pu_pix = selected_pu_size[0]*selected_pu_size[1]   
                decoded_pu_size = (selected_pu_pix) * 3 # 3 bytes a pixel
                tmp_cutype_ix = pregen_rand_cutypes_ixs.next()          
                rand_pu_type = cu_type_list[tmp_cutype_ix]
                
                tmp_all_rand_pu_types.append(tmp_cutype_ix)
                tmp_all_rand_pu_sizes.append(selected_pu_size[0])
                                
                assert(rand_pu_type in possible_cu_type), \
                "_generate_PU_per_CTU_fromPreloadedData_ProbabilisticModel :: invalid CU type selected: <%s>, <%s>, <%s>"% \
                (slice_type, rand_pu_type, possible_cu_type.__repr__())
                
                # for optimisation reasons we are expanding something
                # that could be put into a function (nb: python function overhead is large)
                
                # for optimisation reasons (nb: python function overhead is large)
                if (rand_pu_type=="ICU"):
                    dep = {'fwd': [], 'bwd':[]}                  
                    rand_pu_wcc =   pregen_cu_cc["ICU"].next()
                              
                elif (rand_pu_type=="PCU"):
                    if slice_type == "Bs":
                        f_b = pregen_rand_rfixs.next()
                        dep = {'fwd': [self.frame_dependencies[f_b[0]], self.dependencies[f_b[0]]], 'bwd': [] }
                    else:
                        dep = {'fwd': [self.frame_dependencies[0], self.dependencies[0]], 'bwd': [] }
                    
                    rand_pu_wcc =   pregen_cu_cc["PCU"].next()
                    
                elif (rand_pu_type=="BCU"):            
#                     random_ixs = np.random.randint(len(self.frame_dependencies), size=2)
#                     dep = {'fwd': [self.frame_dependencies[random_ixs[0]], self.dependencies[random_ixs[0]]],
#                            'bwd': [self.frame_dependencies[random_ixs[1]], self.dependencies[random_ixs[1]]]
#                           }
                    f_b = pregen_rand_rfixs.next()
                    dep = {'fwd': [self.frame_dependencies[f_b[0]], self.dependencies[f_b[0]]],
                           'bwd': [self.frame_dependencies[f_b[1]], self.dependencies[f_b[1]]]
                          }
                    rand_pu_wcc =   pregen_cu_cc["BCU"].next()
                    
                elif (rand_pu_type=="SkipCU") and (slice_type=="Ps"):
                    dep = {'fwd': [self.frame_dependencies[0], self.dependencies[0]], 'bwd': [] }
                    rand_pu_wcc =   pregen_cu_cc["SkipCU"].next()
                    
                elif (rand_pu_type=="SkipCU") and (slice_type=="Bs"):
                    #random_ixs = np.random.randint(len(self.frame_dependencies), size=2)
                    f_b = pregen_rand_rfixs.next()
                    if pregen_rand_skip_bwd_select.next() == True:                        
                        dep = {'fwd': [self.frame_dependencies[f_b[0]], self.dependencies[f_b[0]]],
                               'bwd': []
                              }
                    else: # has both bwd and fwd                                                                        
                        dep = {'fwd': [self.frame_dependencies[f_b[0]], self.dependencies[f_b[0]]],
                               'bwd': [self.frame_dependencies[f_b[1]], self.dependencies[f_b[1]]]
                              }
                        
                    rand_pu_wcc =   pregen_cu_cc["SkipCU"].next()
                
                #cc = rand_pu_wcc * SimParams.CPU_EXEC_SPEED_RATIO
                
                #pprint.pprint(HEVCWLP.HEVCWLPARAMS_SCALE_FACTOR) 
                
                cc = rand_pu_wcc * np.random.uniform(HEVCWLP.HEVCWLPARAMS_SCALE_FACTOR[rand_pu_type][0],
                                                     HEVCWLP.HEVCWLPARAMS_SCALE_FACTOR[rand_pu_type][1])
                assert(cc != 0) , "PU size is zero"
                sum_pu_cc += cc          
                cum_pix += selected_pu_pix

                # here we fill the dependency info - from parents
                self._populate_expected_data_from_parents(slice_id, dep, decoded_pu_size)
                
                count_cu+=1
                
                #############################################################                
                # update tracking info - only for validation #                
                if self.enable_workload_validation == True:
                    self.trackvalidate_prop_cu_sizes[selected_pu_size[0]]+=1
                    self.trackvalidate_prop_cu_types[rand_pu_type]+=1
                    self.trackvalidate_cu_dectime[rand_pu_type+"_cc"].append(cc)
                                    
                    if dep['fwd'] != []:
                        gop_ix = dep['fwd'][0] # 0 is gop level ix
                        k = self.gop_structure[gop_ix] + str(gop_ix)
                        if k not in self.trackvalidate_reffrdata:                        
                            self.trackvalidate_reffrdata[k] = decoded_pu_size
                        else:
                            self.trackvalidate_reffrdata[k] += decoded_pu_size
                    if dep['bwd'] != []:
                        gop_ix = dep['bwd'][0]
                        k = self.gop_structure[gop_ix] + str(gop_ix)
                        if k not in self.trackvalidate_reffrdata:                        
                            self.trackvalidate_reffrdata[k] = decoded_pu_size
                        else:
                            self.trackvalidate_reffrdata[k] += decoded_pu_size                    
                #############################################################
                
            assert (cum_pix==SimParams.HEVC_CTU_SIZE)                                
            result_ctus['ctus'][count_ctu_id] = {
                                      #-- most important property --
                                      "cc" : sum_pu_cc,
                                      #-- other (optional) properties --                                      
                                      #"slice_type" : slice_type,                                                                                                
                                      #"pu_list" : result_pus,                                      
                                      #'status' : HEVCProcessingStatus.HEVC_TPROCSTAT_CTU_LEVEL_INIT,
                                      #'deps' : pu_deps_lbl,    
                                      }                    
            total_frame_slicelvl_cc+= result_ctus['ctus'][count_ctu_id]["cc"]
            count_ctu_id+=1   
            sum_pu_cc = 0.0         
            mem_size += (sys.getsizeof(result_ctus) / 1000.0) # mem prof.            
            self.verify_num_ctus_generated +=1
        
        
        #print "np.random.rand() : ", np.random.rand()        
        #print total_frame_slicelvl_cc
                
#         f = plt.figure()
#         data = [v['cc'] for k,v in result_ctus['ctus'].iteritems()]
#         mu_data = np.mean(data)        
#         plt.plot(data)
#         plt.hold(True)
#         plt.axhline(y=mu_data, color='r')
#         plt.show()
        
        return (result_ctus, total_frame_slicelvl_cc, count_ctu_id)
    
    
    
    def _getCUComputationCostPregen_ProbModel(self, size_per_cutype, vid_genre, slice_type):
        plot_hist = False       
        
        possible_cu_type = ["ICU", "PCU", "BCU", "SkipCU"]
        PRE_SAMPLE_RANGE = 1000
        POST_SAMPLE_RANGE = size_per_cutype
        
        ipb_cu_cc_params = HEVCWLP.HEVCWLPARAMS_IPB_CU_DECT_PARAMS[vid_genre]                
        result_cu_cc = {
                        'ICU': [],
                        'PCU': [],
                        'BCU': [],
                        'SkipCU': [],
                        }
        
        for each_cu in possible_cu_type:            
            if (each_cu in ["ICU", "PCU", "BCU"]): # for I/P/B CU
                minmax_lbl = each_cu+"-minmax"
                cc_range = np.linspace(ipb_cu_cc_params[minmax_lbl][0], 
                                       ipb_cu_cc_params[minmax_lbl][1], 
                                       PRE_SAMPLE_RANGE)
                
                pdf_y = exponweib.pdf(cc_range, 
                                      ipb_cu_cc_params[each_cu][0], 
                                      ipb_cu_cc_params[each_cu][1],
                                      scale = ipb_cu_cc_params[each_cu][2],
                                      loc = ipb_cu_cc_params[each_cu][3])
                
                norm_pdf_y = np.array(pdf_y)/np.sum(pdf_y)     # normalised           
                distrib = rv_discrete(values=(np.arange(len(cc_range)), norm_pdf_y))
                tmp_indeces = distrib.rvs(size=POST_SAMPLE_RANGE)
                result_cu_cc[each_cu] = np.take(cc_range, tmp_indeces)
                
            else:   # for Skip CU
                minmax_lbl = each_cu+"-minmax"
                cc_minmax = HEVCWLP.HEVCWLPARAMS_SKIP_CU_DECT_PARAMS(0, vid_genre, return_minmax=True)[1]
                
#                 if slice_type == "P": 
#                     cc_minmax[1] = cc_minmax[1]*0.80 
                
                cc_range = np.linspace(cc_minmax[0], cc_minmax[1], PRE_SAMPLE_RANGE)
                skip_cu_cc_probs = [HEVCWLP.HEVCWLPARAMS_SKIP_CU_DECT_PARAMS(x, vid_genre)
                                    for x in cc_range]
                
                norm_skip_cu_cc_probs = np.array(skip_cu_cc_probs)/np.sum(skip_cu_cc_probs)
                
                distrib = rv_discrete(values=(np.arange(len(cc_range)), norm_skip_cu_cc_probs))
                tmp_indeces = distrib.rvs(size=POST_SAMPLE_RANGE)
                result_cu_cc[each_cu] = np.take(cc_range, tmp_indeces)
        
        # temporary plot distribution - testing
        if plot_hist == True:
            f, axarr = plt.subplots(4, sharex=True)
            axarr[0].hist(result_cu_cc['ICU'], bins=30)
            axarr[0].ticklabel_format(style='sci', axis='both', scilimits=(0,0))
            axarr[1].hist(result_cu_cc['PCU'], bins=30)
            axarr[1].ticklabel_format(style='sci', axis='both', scilimits=(0,0))
            axarr[2].hist(result_cu_cc['BCU'], bins=30)
            axarr[2].ticklabel_format(style='sci', axis='both', scilimits=(0,0))
            axarr[3].hist(result_cu_cc['SkipCU'], bins=30)
            axarr[3].ticklabel_format(style='sci', axis='both', scilimits=(0,0))
            plt.show()
        
        
        np.random.shuffle(result_cu_cc["ICU"])
        np.random.shuffle(result_cu_cc["PCU"])
        np.random.shuffle(result_cu_cc["BCU"])
        np.random.shuffle(result_cu_cc["SkipCU"])
        
        # convert to iterators
        result_cu_cc['ICU'] = itertools.cycle(result_cu_cc['ICU'])
        result_cu_cc['PCU'] = itertools.cycle(result_cu_cc['PCU'])
        result_cu_cc['BCU'] = itertools.cycle(result_cu_cc['BCU'])
        result_cu_cc['SkipCU'] = itertools.cycle(result_cu_cc['SkipCU'])
        
        return result_cu_cc
        
        
    
    def _getCULevelRefFrame_ProbModel(self, max_num_cus):
        fr_type = self.frame_type
        fr_lbl_k = fr_type + str(self.frame_ix_in_gop)
        fwd_fr_refs = self.adaptiveGoP_Obj.get_frameLevelRefs()[fr_lbl_k]['fwd_pred']
        bwd_fr_refs = self.adaptiveGoP_Obj.get_frameLevelRefs()[fr_lbl_k]['bwd_pred']
        
        if fwd_fr_refs==None:
            fwd_fr_refs=[]
        if bwd_fr_refs==None:
            bwd_fr_refs=[]
        
        prob_order = {"I":0, "P":1, "B":2}
        
        assert (len(fwd_fr_refs) + len(bwd_fr_refs)) == len(self.frame_dependencies), "_getCULevelRefFrame:: major Error ! frame refs"
        
        # get probabilities
        fwd_fr_probs = []
        bwd_fr_probs = []
        for rf_fr in fwd_fr_refs:
            tmp_ix =  prob_order[rf_fr['fr']]
            p = HEVCWLP.HEVCWLPARAMS_REFFR_SELECTION_PROBABILITIES[fr_type][tmp_ix]
            fwd_fr_probs.append(p)      
        
        for rf_fr in bwd_fr_refs:
            tmp_ix =  prob_order[rf_fr['fr']]
            p = HEVCWLP.HEVCWLPARAMS_REFFR_SELECTION_PROBABILITIES[fr_type][tmp_ix]
            bwd_fr_probs.append(p)
        
        # normalise probabilities
        if len(fwd_fr_probs)>0:
            fwd_fr_probs = np.array(fwd_fr_probs)
            norm_fwd_fr_probs = fwd_fr_probs/np.sum(fwd_fr_probs)
        if len(bwd_fr_probs)>0:
            bwd_fr_probs = np.array(bwd_fr_probs)
            norm_bwd_fr_probs = bwd_fr_probs/np.sum(bwd_fr_probs)
        
        # select which ref frame for both (fwd , bwd) - for multiple CUs
        result_self_frdep_ix_fwd = []
        result_self_frdep_ix_bwd = []        
        for i in range(max_num_cus):        
            if len(fwd_fr_refs)>0:
                distrib_fwd = rv_discrete(values=(np.arange(len(fwd_fr_refs)), norm_fwd_fr_probs))
                tmp_fwd_rf_ix = distrib_fwd.rvs(size=1)[0]
                fwd_rf_rf_ix = fwd_fr_refs[tmp_fwd_rf_ix]['frix']
                self_frdep_ix_fwd = self.frame_dependencies.index(fwd_rf_rf_ix)                
                result_self_frdep_ix_fwd.append(self_frdep_ix_fwd)
                
            if len(bwd_fr_refs)>0:
                distrib_bwd = rv_discrete(values=(np.arange(len(bwd_fr_refs)), norm_bwd_fr_probs))
                tmp_bwd_rf_ix = distrib_bwd.rvs(size=1)[0]
                bwd_rf_rf_ix = bwd_fr_refs[tmp_bwd_rf_ix]['frix']
                self_frdep_ix_bwd = self.frame_dependencies.index(bwd_rf_rf_ix)
                result_self_frdep_ix_bwd.append(self_frdep_ix_bwd)
                    
        final_result = {
                        'result_self_frdep_ix_fwd' : result_self_frdep_ix_fwd,
                        'result_self_frdep_ix_bwd' : result_self_frdep_ix_bwd                        
                        }
        return final_result
                
#         result_ixs = {'fwd': [], 'bwd':[]}
#         
#         ## target : I-frame ##
#         if fr_type == "I":
#             result_ixs = {'fwd': [], 'bwd':[]}        
#         
#         ## target : P-frame ##
#         elif fr_type == "P":            
#             if len(self.frame_dependencies) == 0:
#                 sys.exit("_getCULevelRefFrame:: Error - P fr but no refs - something wrong")
#             elif len(self.frame_dependencies) == 1: # no choice
#                 result_ixs = {'fwd': [self.frame_dependencies[0], self.dependencies[0]], 'bwd':[]}
#             elif len(self.frame_dependencies) > 1: # we have choices
#                 result_ixs = {'fwd': [self.frame_dependencies[self_frdep_ix_fwd], self.dependencies[self_frdep_ix_fwd]], 'bwd':[]}                
#             else:
#                 pass
#             
#         ## target : B-frame ##
#         elif fr_type == "B":
#             if len(self.frame_dependencies) == 0:
#                 sys.exit("_getCULevelRefFrame:: Error - B fr but no refs - something wrong")
#             elif len(self.frame_dependencies) == 1: # no choice
#                 sys.exit("_getCULevelRefFrame:: Error - B fr but only 1 refs - something wrong")            
#             elif len(self.frame_dependencies) == 2: # we have choices
#                 result_ixs = {'fwd': [self.frame_dependencies[0], self.dependencies[0]], 
#                               'bwd': [self.frame_dependencies[1], self.dependencies[1]]
#                               }    
#             elif len(self.frame_dependencies) > 2: # we have choices
#                 result_ixs = {'fwd': [self.frame_dependencies[self_frdep_ix_fwd], self.dependencies[self_frdep_ix_fwd]], 
#                               'bwd': [self.frame_dependencies[self_frdep_ix_bwd], self.dependencies[self_frdep_ix_bwd]]
#                               }                
#             else:
#                 pass            
#             
#         else:
#             pass
#         
#         
#         return result_ixs
        
    
    
    # generate all the CTUs fro the given slice
    def _generate_PU_per_CTU_fromPreloadedData(self, slice_type, slice_id, frame_res, num_ctus, ctu_id):
        ctu_size = SimParams.HEVC_CTU_SIZE # we need to split this up into the quad tree structure        
        sum_pu_cc = 0.0
        mem_size = 0.0
        
        if(slice_type == "Is"):     pu_type = ["Ipu"]
        elif(slice_type == "Ps"):   pu_type = ["Ipu", "Ppu", "Ppu", "Ppu"]
        else:                       pu_type = ["Ipu", "Ppu", "Bpu", "Bpu"]
            
        count_ctu_id = ctu_id
        total_frame_slicelvl_cc = 0.0        
        result_ctus = {'sltype' :  slice_type, 'ctus' : OrderedDict()}
        
        # randomly select PU size, numctus, etc from loaded data
        all_random_ixs = np.random.randint(0,len(DataPreloader.hevc_random_ctu[frame_res][slice_type]), size=num_ctus)
        range_num_ctus = range(num_ctus)        
        all_selected_pus = [DataPreloader.hevc_random_ctu[frame_res][slice_type][ix]['pu_list'] for ix in all_random_ixs]
        
        # all ctus in the slice
        for each_ctu, ix, selected_pu_sizes in zip(range_num_ctus,all_random_ixs, all_selected_pus) :
            #self._verify_pu_sizes(ctu_size, selected_pu_sizes)
            
            # horrible but faster
            if len(pu_type)>1:
                temp_rand_pu_ixs = np.random.randint(len(pu_type),size=len(selected_pu_sizes))
            else:
                temp_rand_pu_ixs = [0]* len(selected_pu_sizes)
            
            assert (np.sum([p[0]*p[1] for p in selected_pu_sizes]) == SimParams.HEVC_CTU_SIZE)
            
            cum_pix = 0 # cumulative pixels count
            for each_pu_ix, each_pu in enumerate(selected_pu_sizes):
                selected_pu_size =   each_pu          
                selected_pu_pix = selected_pu_size[0]*selected_pu_size[1]   
                decoded_pu_size = (selected_pu_pix) * 3 # 3 bytes a pixel          
                rand_pu_type = pu_type[temp_rand_pu_ixs[each_pu_ix]]                                
                
                # for optimisation reasons (nb: python function overhead is large)
                if (rand_pu_type=="Ipu"):
                    dep = {'fwd': [], 'bwd':[]}                            
                elif (rand_pu_type=="Ppu"):
                    dep = {'fwd': [self.frame_dependencies[0], self.dependencies[0]], 'bwd': [] }
                elif (rand_pu_type=="Bpu"):            
                    random_ixs = np.random.randint(len(self.frame_dependencies), size=2)
                    dep = {'fwd': [self.frame_dependencies[random_ixs[0]], self.dependencies[random_ixs[0]]],
                           'bwd': [self.frame_dependencies[random_ixs[1]], self.dependencies[random_ixs[1]]]
                          }
                    
                rand_pu_wcc = np.random.uniform(low=SimParams.HEVC_FIXED_BLOCK_WCCC[rand_pu_type][0], 
                                                high=SimParams.HEVC_FIXED_BLOCK_WCCC[rand_pu_type][1])
                
                cc = rand_pu_wcc * SimParams.CPU_EXEC_SPEED_RATIO
                assert(cc != 0) , "PU size is zero"
                sum_pu_cc += cc          
                cum_pix += selected_pu_pix

                # here we fill the dependency info - from parents
                self._populate_expected_data_from_parents(slice_id, dep, decoded_pu_size)
            
            assert (cum_pix==SimParams.HEVC_CTU_SIZE)    
                            
            result_ctus['ctus'][count_ctu_id] = {
                                      #-- most important property --
                                      "cc" : sum_pu_cc,
                                      #-- other (optional) properties --                                      
                                      #"slice_type" : slice_type,                                                                                                
                                      #"pu_list" : result_pus,                                      
                                      #'status' : HEVCProcessingStatus.HEVC_TPROCSTAT_CTU_LEVEL_INIT,
                                      #'deps' : pu_deps_lbl,    
                                      }                    
            total_frame_slicelvl_cc+= result_ctus['ctus'][count_ctu_id]["cc"]
            count_ctu_id+=1
            sum_pu_cc=0.0            
            mem_size += (sys.getsizeof(result_ctus) / 1000.0) # mem prof.            
            self.verify_num_ctus_generated +=1
         
        return (result_ctus, total_frame_slicelvl_cc, count_ctu_id)
    
    
    
    def _populate_expected_data_from_parents(self, slice_id, dep, decoded_pu_size):
        # populate expected_data_from_parents                       
        if (dep['fwd'] != []):
            fwddep_task_id = dep['fwd'][1]            
            if fwddep_task_id not in self.expected_data_from_parents:
                self.expected_data_from_parents[fwddep_task_id] = decoded_pu_size
            else:                            
                self.expected_data_from_parents[fwddep_task_id] += decoded_pu_size
            
        if (dep['bwd'] != []):  
            bwddep_task_id = dep['bwd'][1]
            if bwddep_task_id not in self.expected_data_from_parents:
                self.expected_data_from_parents[bwddep_task_id] = decoded_pu_size
            else:                
                self.expected_data_from_parents[bwddep_task_id] += decoded_pu_size
            
            
    
    def calc_deps_as_ratio_of_frame_num_pixs(self):        
        assert (self.verify_num_ctus_generated == np.sum(self.num_ctu_per_slice))        
        total_pix_data = (self.frame_h * self.frame_w) *3
        total_ctu_pix_data = np.sum(self.num_ctu_per_slice)*SimParams.HEVC_CTU_SIZE*3                
        data_per_parent = {}
        for each_parent_tid, data_size in self.expected_data_from_parents.iteritems():
            data_per_parent[each_parent_tid] = (float(data_size)/float(total_ctu_pix_data)) * 100
        
        data_per_parent['NONE'] = 100 - np.sum(data_per_parent.values())        
        return data_per_parent
    
    def _verify_pu_sizes(self, sum_ctu, pu_sizes):
        temp1 = np.sum([p[0]*p[1] for p in pu_sizes])
        if (temp1 != sum_ctu): sys.exit("Error _verify_pu_sizes")
    
    def _get_PU_level_deps(self, pu_type):        
        if (pu_type=="Ipu"):
            dep = {'fwd': [], 'bwd':[]}
        elif (pu_type=="Ppu"):
            dep = {'fwd': [self.frame_dependencies[0], self.dependencies[0]], 'bwd': []}        
        elif (pu_type=="Bpu"):            
            random_ixs = np.random.randint(len(self.frame_dependencies), size=2)
            dep = {'fwd': [self.frame_dependencies[random_ixs[0]], self.dependencies[random_ixs[0]]],
                   'bwd': [self.frame_dependencies[random_ixs[1]], self.dependencies[random_ixs[1]]]
                  }        
        return dep
  
    
    def calc_num_CTU_theoretical(self):        
        max_num_CTU_frame  = int(float(self.frame_h*self.frame_w)/float(SimParams.HEVC_CTU_SIZE))
        max_num_CTU_tile = int(float(max_num_CTU_frame)/float(self.number_of_tiles))
        
        return (max_num_CTU_frame, max_num_CTU_tile)
    
    def calc_num_CTU_via_block_partitions(self):        
        num_ctus_count = np.sum([
                          len(v['ctus'].keys()) for k,v in self.frame_block_partitions.iteritems()                          
                          ])        
        return num_ctus_count
    
    
    ######################
    ## helper functions ##
    ######################        
    # not used
    def _generate_Iframe_ComputationTime(self):return 0.0
    def _generate_PFrame_ComputationTime(self):return 0.0
    def _generate_BFrame_ComputationTime(self):return 0.0
        
    @staticmethod
    def getStaticComputationCost(frame_h, frame_w, cpu_exec_speed_ratio):        
        sys.exit("Error: HEVCFrameTask::getStaticComputationCost:: not implemented yet !")
        
    ##########################################
    ## generate the worst-case execution times
    ## for I/P/B frames
    ##########################################    
    def gen_Iframe_wcc(self):    
        ct=0.0; bl_8x8 = (8*8)
        num_8x8_blks = ((self.frame_h*self.frame_w)/(bl_8x8))
        ct = (num_8x8_blks * SimParams.HEVC_FIXED_BLOCK_WCCC['Ipu'][1]) * SimParams.CPU_EXEC_SPEED_RATIO        
        return ct 
    
    def gen_Pframe_wcc(self):        
        ct=0.0; bl_8x8 = (8*8)
        num_8x8_blks = ((self.frame_h*self.frame_w)/(bl_8x8))
        ct = (num_8x8_blks * SimParams.HEVC_FIXED_BLOCK_WCCC['Ppu'][1]) * SimParams.CPU_EXEC_SPEED_RATIO        
        return ct
    
    def gen_Bframe_wcc(self):
        ct=0.0; bl_8x8 = (8*8)
        num_8x8_blks = ((self.frame_h*self.frame_w)/(bl_8x8))
        ct = (num_8x8_blks * SimParams.HEVC_FIXED_BLOCK_WCCC['Bpu'][1]) * SimParams.CPU_EXEC_SPEED_RATIO            
        return ct
        
        
    ###############################################
    ## functions to assist schedulability analysis
    ###############################################
    # assume gop structure is the IPBBPBBPBBBB format
    def getCriticalPaths(self):
        sys.exit("Error: HEVCFrameTask::getCriticalPaths:: not implemented yet !")
    
    # assume gop structure is the IPBBPBBPBBBB format
    # we take into account the edges from node-->MMC(dst_task_ix = -1)
    # we take into account the edge from MMC (src_task_ix=-2)-->I_frame_task
    def getCriticalPaths_withMMCDataRDWR(self):
        sys.exit("Error: HEVCFrameTask::getCriticalPaths_withMMCDataRDWR:: not implemented yet !")
        
    def getEstimatedRelativeDeadline_EQF(self, dispatch_time=None):
        if (dispatch_time==None): ai = self.get_dispatchTime()
        else: ai = dispatch_time
            
        ci = self.get_worstCaseComputationCost()
        De2e = self.get_end_to_end_deadline()
        
        # sum of all frames in gop
        sum_gop_ci = 0.0
        for each_frame_type in self.get_gop_frame_dec_order_ftype():
            if(each_frame_type == "I"):
                sum_gop_ci += self.get_wccIFrame()
            elif(each_frame_type == "P"):
                sum_gop_ci += self.get_wccPFrame()
            elif(each_frame_type == "B"):
                sum_gop_ci += self.get_wccBFrame()
            
        # sum of all frames in gop - starting from current frame
        sum_gop_ci_m = 0.0
        for each_frame_type in self.get_gop_frame_dec_order_ftype()[self.gop_decode_order_ix:]:
            if(each_frame_type == "I"):
                sum_gop_ci_m += self.get_wccIFrame()
            elif(each_frame_type == "P"):
                sum_gop_ci_m += self.get_wccPFrame()
            elif(each_frame_type == "B"):
                sum_gop_ci_m += self.get_wccBFrame()
                
        di =  ai +  ci + ((De2e - ai - sum_gop_ci) * ( ci/(sum_gop_ci_m)) )
        
        assert ((di - ai) > 0)        
        return (di - ai)
    
    # total deadline is divided equally amongst subtasks
    def getEstimatedRelativeDeadline_Div_x(self):        
        De2e = self.get_end_to_end_deadline()        
        n = float(len(self.gop_structure))
        x=1.0
        di = (De2e / (n*x))        
        return di
    
    
    ###############################################
    ## related with dependency based scheduling
    ## CTU-level deps
    ###############################################    
    def setCurrentlyProcessingUnitRef(self, unit_dict):
        self.current_processing_unit = unit_dict
    
    # called when the task is completed
    def nullifyCurrentlyProcessingUnitRef(self):
        self.current_processing_unit = {'slice_id'  : None, 
                                        'ctu_id'    : None,
                                        'rem_cc'    : None,
                                        }
        
    def getCurrentlyProcessingUnitRef(self):
        return self.current_processing_unit
        
    def getCurrentlyProcessingUnitRef_Label(self):        
        max_slice_id = np.max(self.frame_block_partitions.keys())
        str = "{%d/%d, %d, %.15f}" % (self.current_processing_unit['slice_id'], max_slice_id, 
                              self.current_processing_unit['ctu_id'],
                              self.current_processing_unit['rem_cc'],
                              )
        return str
    
    def getNextProcessingUnitRef(self):        
        current_slice_id = self.current_processing_unit['slice_id']
        current_ctu_id = self.current_processing_unit['ctu_id']
        max_slice_id = np.max(self.frame_block_partitions.keys())
        max_ctuid_in_current_slice = np.max(self.frame_block_partitions[current_slice_id]['ctus'].keys())

## debug##               
#         pprint.pprint({                      
#                       's_id': current_slice_id,  'ctu_id': current_ctu_id, 'max_s': max_slice_id, 'max_c': max_ctuid_in_current_slice,                                            
#                       })
## debug##

        # -- last ctu in slice
        if (current_ctu_id >= max_ctuid_in_current_slice):
            # -- last slice
            if (current_slice_id >= max_slice_id):
                return None
            else: # roll over to next slice
                current_slice_id +=1 
                next_slice_first_ctu_id = np.min(self.frame_block_partitions[current_slice_id]['ctus'].keys())
                current_ctu_id = next_slice_first_ctu_id                
        
        # -- more ctus to process in slice
        else:
            current_ctu_id +=1
            current_slice_id = current_slice_id          
        
        cc = self.frame_block_partitions[current_slice_id]['ctus'][current_ctu_id]["cc"]
        assert(cc != 0), "Error : getNextProcessingUnitRef: - CTU size is zero"
        
        # assign
        result = {'slice_id':current_slice_id, 
                  'ctu_id':current_ctu_id,
                  'rem_cc': cc
                  }
        
        return result
        
    
    def getRemainingCTU_ComputationCost(self):
        return self.current_processing_unit['rem_cc']
    def setRemainingCTU_ComputationCost(self, ctu_cc):
        self.current_processing_unit['rem_cc'] = ctu_cc
    
    def getCTU_ComputationCost(self, slice_id, ctu_id):
        ctu_cc = self.frame_block_partitions[slice_id]['ctus'][ctu_id]["cc"]
        return ctu_cc
    
    # called when an interrupt occurs
    def updateRemainingCTU_ComputationCost(self, time_elapsed):
        self.current_processing_unit['rem_cc'] =   self.current_processing_unit['rem_cc']-time_elapsed
        return self.current_processing_unit['rem_cc']
        
    
    # have all the CTU deps been fullfiled ? 
    def isCTUDepsComplete(self, slice_id, ctu_id):            
        # get target ctu
        target_ctu_dep_ids = self.frame_block_partitions[slice_id]['ctus'][ctu_id]['deps']        
        if len(target_ctu_dep_ids) == 0:
            return True
        else:
            return False
       
    
    
    # each frame task has a dep (tagged with size in bytes) from a parent
    # we reduce this required dep size
    # if required dep size is zero from all parents, then task is ready to run
    def clearFrameDeps_bySize(self, parent_task_id, dep_size_bytes):
        sys.exit("Error: clearFrameDeps_bySize:: not implemented yet")        
    def clearFrameDeps(self, parent_task_id):
        del self.outstanding_deps_parent_tids[parent_task_id]
    
    ###############################################
    ## related with Task splitting
    ###############################################
    def setTileParentFrameId(self, pid):
        self.tile_parent_frame_task_id = pid
    def getTileParentFrameId(self):
        return self.tile_parent_frame_task_id
    
    # tile based splits
    def getNumSubTasksTiles(self):
        return len(self.frame_tile_partitions)    
    
    def setTileInitialProcessingUnitRef(self, tile_block_partitions):
        min_slice_id = np.min(tile_block_partitions.keys())
        min_ctu_id = np.min(tile_block_partitions[min_slice_id]['ctus'].keys())        
        self.current_processing_unit = {'slice_id':min_slice_id , 'ctu_id':min_ctu_id, 'rem_cc': tile_block_partitions[min_slice_id]['ctus'][min_ctu_id]["cc"]} # slice, ctu, rem_cc
    
    # execution costs per tile
    def getTileLevel_ExecutionCost(self):        
        tile_level_cc = {}        
        for each_tile_ix, each_tile in enumerate(self.frame_tile_partitions):
            slice_ixs = each_tile['slice_ixs']            
            # whats the cc for each slice
            tile_sum_cc = 0.0
            for each_slice_ix in slice_ixs:
                tile_sum_cc += np.sum([ctu_dict['cc'] for ctu_dict in self.frame_block_partitions[each_slice_ix]['ctus'].values()])
            tile_level_cc[each_tile_ix] = tile_sum_cc        
        return tile_level_cc
    
    
    # (1) tile WCET  - as a proportion of the tile pixels
    def getTileWCCC_viaFiarProportions(self, tile_h, tile_w, frame_h, frame_w, frame_wccc):
        if len(self.frame_tile_partitions) == 1:
            return frame_wccc
        else:        
            tile_dim_proportion = float(tile_w*tile_h)/float(frame_w*frame_h)
            tile_wcc = float(frame_wccc) * float(tile_dim_proportion)            
            assert (tile_wcc > 0) and (tile_wcc < frame_wccc), "getTileWCCC_viaFiarProportions:: Error: %f, %f, %d" %(tile_wcc, frame_wccc, self.number_of_tiles)        
            return tile_wcc
    
    # (2) tile WCET  - using worst-case values of PU cc
    def getTileWCCC_viaWCPUCC(self, tile_h, tile_w, frame_h, frame_w):        
        if len(self.frame_tile_partitions) == 1:
            return frame_wccc
        else:            
            wc_pu_cc = np.max(SimParams.HEVC_FIXED_BLOCK_WCCC.values()) * SimParams.CPU_EXEC_SPEED_RATIO
            tile_wcc = (float(tile_w*tile_h) / float(8*8)) * wc_pu_cc         
            return tile_wcc
    
    # (3) tile WCET - from 
    def setTileWCCC_viaDistribution(self, tile_wccc):
        self.tile_observed_wccc(tile_wccc)
    def getTileWCCC_viaDistribution(self):
        return self.tile_observed_wccc
    
    # relative deadline of the tile as a proportion of the relative deadline of the frame task
    def getTileEstimatedRelativeDeadline_viaFairProportions(self, tile_h, tile_w, frame_h, frame_w, frame_relD):
        if len(self.frame_tile_partitions) == 1:
            return frame_relD
        else:
            tile_dim_proportion = float(tile_w*tile_h)/float(frame_w*frame_h)
            tile_relD = frame_relD * float(tile_dim_proportion)
            assert (tile_relD > 0) and (tile_relD < frame_relD), "getTileEstimatedRelativeDeadline_viaFairProportions:: Error: %f, %f" %(tile_relD, frame_relD)
            return tile_relD
    
    
    # block partitions - gives us the CTU level info for each tile 
    def getTileLevel_block_partitions(self):
        if (SimParams.HEVC_MODEL_FLUSH_FRAMEBLOCK_INFO == False):        
            tile_level_block_partitions = {}
            for each_tile_ix, each_tile in enumerate(self.frame_tile_partitions):
                tile_level_block_partitions[each_tile_ix] = {}
                slice_ixs = each_tile['slice_ixs']
                new_sl_id = 0
                for each_slice_ix in slice_ixs:
                    tile_level_block_partitions[each_tile_ix][new_sl_id] = self.frame_block_partitions[each_slice_ix]
                    new_sl_id+=1
            return tile_level_block_partitions
        else:
            return self.hack_abstract__getTileLevel_block_partitions()
        
    
    
    def getNumCTUinTile(self, tile_ix):
        if (SimParams.HEVC_MODEL_FLUSH_FRAMEBLOCK_INFO == False):
            tile_level_block_partitions = self.getTileLevel_block_partitions()            
            num_ctus_in_tile = np.sum([len(s['ctus'].keys()) 
                                     for s_ix, s in tile_level_block_partitions[tile_ix].iteritems()])            
            return num_ctus_in_tile 
        else:
            return self.hack_abstract__num_ctus_in_tile[tile_ix]
        
    
    # not sure if this is important - so very lame solution
    # num_ctus : number of ctus in the tile
    def getTileDimensions(self, num_ctus):
        if ((num_ctus % 6) == 0): 
            numctu_h = 6 
            numctu_w = (num_ctus/6)
        elif ((num_ctus % 4) == 0): 
            numctu_h = 4 
            numctu_w = num_ctus/4
        elif((num_ctus % 2) == 0): 
            numctu_h = 2
            numctu_w = num_ctus/2
        else: 
            numctu_h=1
            numctu_w = num_ctus   
        
        assert (((numctu_w*SimParams.HEVC_CTU_WIDTH)*(numctu_h*SimParams.HEVC_CTU_WIDTH)) == (num_ctus*SimParams.HEVC_CTU_SIZE)), \
        "%d, %d" % (numctu_w*SimParams.HEVC_CTU_WIDTH, numctu_h*SimParams.HEVC_CTU_WIDTH)
             
        return (numctu_w*SimParams.HEVC_CTU_WIDTH, numctu_h*SimParams.HEVC_CTU_WIDTH) 
    
    
    
                
    # find the dependencies per tile
#     gop_tile_partitions = { 
#         'orig_gop_struct' => original gop structure
#         'orig_task_ids' => original task ids
#         'new_tasks' => old_task_id : <new task ids (tile level)>
#                         e.g : 120 : [120_0, 120_1, 120_2]
#     
#     def getTileLevel_Dependencies_RandomPartitionData_FromParents(self, gop_tile_partitions):        
#         ### expected data from parents
#         new_struct_expected_data_from_parents = {}
#         for each_parent_task_id , data_size in self.get_expected_data_from_parents().iteritems():
#             new_tile_level_parent_ids = gop_tile_partitions['new_tasks'][each_parent_task_id]
#             # if there are more parents now, randomly split the incoming edges
#             if (len(new_tile_level_parent_ids)>1):
#                 temp_data_partitions = self.constrained_sum_sample_pos(len(new_tile_level_parent_ids), data_size)
#                 for each_new_parent_task_id, new_data_from_parent_bytes in zip(new_tile_level_parent_ids, temp_data_partitions):
#                     new_struct_expected_data_from_parents[each_new_parent_task_id] = new_data_from_parent_bytes
#             else:
#                 new_struct_expected_data_from_parents[each_parent_task_id] = data_size
#                 
#         return new_struct_expected_data_from_parents 
#         
#     def getTileLevel_Dependencies_RandomPartitionData_ToChildren(self, gop_tile_partitions):        
#         ### expected data to children
#         new_struct_expected_data_to_children = {}
#         for each_child_task_id, data_size in self.get_expected_data_to_children().iteritems():
#             new_tile_level_child_ids = gop_tile_partitions['new_tasks'][each_child_task_id]
#             # if there are more children now, randomly split the outgoing edges
#             if (len(new_tile_level_child_ids)>1):
#                 temp_data_partitions = self.constrained_sum_sample_pos(len(new_tile_level_child_ids), data_size)
#                 for each_new_child_task_id , new_data_to_children_bytes in zip(new_tile_level_child_ids, temp_data_partitions):
#                     new_struct_expected_data_to_children[each_new_child_task_id] = new_data_to_children_bytes
#             else:
#                 new_struct_expected_data_to_children[each_child_task_id] = data_size
#                 
#         return new_struct_expected_data_to_children
    
    
    def getTileLevel_MpegTaskSize(self, parent_mpged_task_size, tile_w, tile_h, frame_w, frame_h):
        if len(self.frame_tile_partitions) == 1:
            return float(parent_mpged_task_size)
        else:            
            return np.rint(float(parent_mpged_task_size) * float(tile_w*tile_h)/float(frame_w*frame_h))
        
    
    
    
    ## this is a hack to reduce the memory footprint of the HEVCFrame object ##
    # the block-level cc info is taking up alot of memory per object
    # we are going to replace all the ctus with a single ctu
    # so these functions need to be called AFTER the whole frame and GOP has been constructed
    
    def hack_abstract__frame_block_partitions(self):
        if SimParams.HEVC_MODEL_FLUSH_FRAMEBLOCK_INFO == False:
            sys.exit("Error : hack__abstract_frame_block_partitions - HEVC_MODEL_FLUSH_FRAMEBLOCK_INFO = True")
        
        # set the tile-level new single ctus
        self.hack_abstract__calculateTileLevel_block_partitions()
        
        # reset the frame block partitions
        sum_ctu_cc = self.calc_FrameComputationTime()        
        # template format of dict : self.frame_block_partitions[current_slice_id]['ctus'][current_ctu_id]["cc"]      
        self.frame_block_partitions = {}  
        self.frame_block_partitions = {
                                       0 : {
                                            'ctus' : { 0 : { 'cc' : sum_ctu_cc} },
                                            'sltype' :  None
                                            }                                       
                                       }
        
        # reset all methods and member to be compatible
        self.current_processing_unit = {'slice_id':0 , 'ctu_id':0, 'rem_cc': self.frame_block_partitions[0]['ctus'][0]["cc"]} # slice, ctu, rem_cc
        
        
    def hack_abstract__calculateTileLevel_block_partitions(self):   
        tile_level_block_partitions = {}        
        for each_tile_ix, each_tile in enumerate(self.frame_tile_partitions):
            tile_level_block_partitions[each_tile_ix] = {}
            slice_ixs = each_tile['slice_ixs']
            new_sl_id = 0
            for each_slice_ix in slice_ixs:
                tile_level_block_partitions[each_tile_ix][new_sl_id] = self.frame_block_partitions[each_slice_ix]
                new_sl_id+=1
                
            # calculate the total cc per tile 
            sum_tile_cc = 0.0            
            for each_slice_v in tile_level_block_partitions[each_tile_ix].values():
                sum_tile_cc += np.sum([each_ctu_v['cc'] for each_ctu_v in each_slice_v['ctus'].values()])
            
            # populate hack structure
            self.hack_abstract__tile_level_block_partitions[each_tile_ix] = {
                                                                               0 : {
                                                                                    'ctus' : { 0 : { 'cc' : sum_tile_cc} },
                                                                                    'sltype' :  None
                                                                                    }                                       
                                                                            }
            # calc number of ctus in tile
            num_ctus_in_tile = np.sum([len(s['ctus'].keys()) 
                                     for s_ix, s in tile_level_block_partitions[each_tile_ix].iteritems()])
            self.hack_abstract__num_ctus_in_tile[each_tile_ix] = num_ctus_in_tile
        
        
        # verify
        total_frame_cc = self.calc_FrameComputationTime()
        sum_alltiles_cc = 0.0
        num_tiles=0
        for each_tile in self.hack_abstract__tile_level_block_partitions.values():
            for each_slice_v in each_tile.values():
                sum_alltiles_cc += np.sum([each_ctu_v['cc'] for each_ctu_v in each_slice_v['ctus'].values()])
            num_tiles+=1                
        assert(total_frame_cc == sum_alltiles_cc), "%d, %d, %d, %d" % (total_frame_cc, sum_alltiles_cc, num_tiles, self.getNumSubTasksTiles())
        
        
            
            
    def hack_abstract__getTileLevel_block_partitions(self):
        return self.hack_abstract__tile_level_block_partitions
        
        
        
    
        
    
    
    
    
    
    ######################
    ## data loading   ####
    ######################
    def load_frame_data(self, wf_id, strm_id, ugid, frame_ix, rand_seed):
        file_info = {
                        'wf_id' : wf_id,
                        'strm_id' : strm_id,
                        'ugid' : ugid,
                        'frame_ix' : frame_ix, 
                        'rand_seed' : rand_seed,                     
                     }
                    
        data_obj = DataPreloader.load_frame_data_file(file_info)
        return data_obj
        
        
    
    ######################
    ## misc function  ####
    ######################
    @staticmethod        
    def constrained_sum_sample_pos(n, total):
        """Return a randomly chosen list of n positive integers summing to total.
        Each such list is equally likely to occur."""
        # source : http://stackoverflow.com/questions/3589214/generate-multiple-random-numbers-to-equal-a-value-in-python
        dividers = sorted(random.sample(xrange(1, total), n - 1))
        return [a - b for a, b in zip(dividers + [total], [0] + dividers)]    
        
    
    @staticmethod                           
    def _generate_list_of_random_nums(N, param_sum):
        result = [0]*N    
        ix = 0
        while(np.sum(result) < param_sum):
            if(np.random.rand()>0.5):
                result[ix]+=1            
                ix+=1            
            if ix==N:
                ix=0    
        final_sum = np.sum(result)
        assert(final_sum == param_sum), "calc_sum=%d" % final_sum
        
        # tricky when there are zeros
        # find list of ix where value is zero
        zero_ixs = [ix for ix, v in enumerate(result)]
        if(len(zero_ixs)>0):
            max_val_ix = [i for i, j in enumerate(result) if j == max(result)]
            for each_zero_ix in zero_ixs:
                result[each_zero_ix] +=1
                result[random.choice(max_val_ix)] -= 1
        return result
        
    def _weightedChoice(self, weights, objects):
        #http://stackoverflow.com/questions/10803135/weighted-choice-short-and-simple
        """Return a random item from objects, with the weighting defined by weights 
        (which must sum to 1)."""
        cs = np.cumsum(weights) #An array of the weights, cumulatively summed.
        idx = np.sum(cs < np.random.rand()) #Find the index of the first weight over a random value.
        return objects[idx] 
    
    
    
    

class HEVCProcessingStatus:
    
    HEVC_TPROCSTAT_CTU_LEVEL_INIT = 0
    HEVC_TPROCSTAT_CTU_LEVEL_WAITING_FOR_DEPS = 1
    HEVC_TPROCSTAT_CTU_LEVEL_PROCESSING = 2
    HEVC_TPROCSTAT_CTU_LEVEL_COMPLETED = 3
    
    
class modified_expweib_gen(ss.rv_continuous):
    #def _argcheck(self, skew):
    #    return np.isfinite(skew) #I guess we can confine it to finite value
    
    def _argcheck(self, *args):
        """Default check for correct values on args and keywords.

        Returns condition array of 1's where arguments are correct and
         0's where they are not.

        """
        cond = 1
        for arg in args:
            cond = 1 if np.isfinite(arg) else 0
        return cond
    
    
    
#     def _pdf(self, x, skew):
#         return 2 * ss.exponweib.pdf(x) * ss.norm.cdf(x * skew)  
    