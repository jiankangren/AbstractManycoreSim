import pprint
import pickle

import math, random
import os, sys
import gc

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import scipy.stats
from matplotlib.colors import ListedColormap, NoNorm
from matplotlib import mlab
from itertools import cycle # for automatic markers

import matplotlib.cm as cm
from matplotlib.font_manager import FontProperties

## local imports
from MPEG2GOPTask import MPEG2GOPTask
from MPEG2FrameTask import MPEG2FrameTask
from MPEG2FrameTask_InterRelatedGOP import MPEG2FrameTask_InterRelatedGOP
from SimParams import SimParams
from libApplicationModel.MPEG2FrameTask import MPEG2FrameTask
from libApplicationModel.HEVCFrameTask import HEVCFrameTask
from AdaptiveGoPGenerator import AdaptiveGoPGenerator
from AdaptiveGoPGenerator_v2 import AdaptiveGoPGenerator_v2
from libApplicationModel.DataPreloader import DataPreloader
import HEVCWorkloadParams


class TaskSet:
    def __init__(self, env):
        self.taskList = []
        self.taskList_orig = []
        self.env = env
        
        # for debug #
        self.fig_counter = 100
    
    ## generates a MPEG GOP task set
    def generateMPEG2GOPTaskSet(self, num_gops):
        
        for tid in xrange(num_gops):
            gop_task = MPEG2GOPTask(env= self.env, id = tid)
            self.taskList.append(gop_task)
        
        print '%f'%self.env.now + "," + 'TaskSet::' + "," + 'generateMPEG2GOPTaskSet::,' + " - " + str(len(self.taskList)) + " tasks generated"
        
        # archive to refer to later
        self.taskList_orig = list(self.taskList)
        
    
    ## generates a MPEG-Frame task set
    ## we also provide the taskset dispatch times
    def generateMPEG2FrameTaskSet(self, num_gops, task_start_id, gop_start_id, unique_gop_start_id, \
                                  gop_structure = SimParams.GOP_STRUCTURE,                                  
                                  taskset_dispatch_start_time = 0.0,
                                  video_stream_id = None,
                                  wf_id = None,                                  
                                  frame_h=SimParams.FRAME_DEFAULT_H,
                                  frame_w=SimParams.FRAME_DEFAULT_W,
                                  frame_rate=SimParams.FRAME_RATE,
                                  priority_range = None):        
        
        # check pri range
        if (priority_range == None):
            sys.exit('Error: generateMPEG2FrameTaskSet:: error in pri range')
        
        taskset_dispatch_rates = []
        gop_dispatch_times_list = []
        
        gop_dispatch_time = taskset_dispatch_start_time
        for each_gop_id in xrange(0,num_gops):            
            gop_instance = []   # reset
            frame_id = 0     # reset
            for each_frame in gop_structure:
                frame_task = MPEG2FrameTask(env = self.env, \
                                            id = (((each_gop_id) * SimParams.GOP_LENGTH) + frame_id) + task_start_id, \
                                            frame_type = str(each_frame), \
                                            frame_ix_in_gop = frame_id, \
                                            unique_gop_id = (each_gop_id + unique_gop_start_id), \
                                            gop_id = (each_gop_id+gop_start_id), \
                                            video_stream_id = video_stream_id, \
                                            wf_id = wf_id, \
                                            frame_h=frame_h, \
                                            frame_w=frame_w, \
                                            frame_rate=frame_rate, \
                                            priority = priority_range[frame_id])
                
                frame_task.set_scheduledDispatchTime(gop_dispatch_time)
                gop_dispatch_times_list.append(gop_dispatch_time)
                
                # is this the first or last gop in the video stream ?
                if(each_gop_id == 0): # first
                    frame_task.set_isHeadVideoGop(True)
                elif(each_gop_id == (num_gops-1)): # last
                    frame_task.set_isTailVideoGop(True)
                
                gop_instance.append(frame_task)
            
                self.taskList.append(frame_task)
                frame_id = frame_id + 1
            
            for frame in gop_instance:
                frame.adjust_deadline(gop_instance)
                
            # adjust scheduled dispatch time for next gop
            gop_e2ed =  float(len(gop_instance))/float(gop_instance[0].get_framerate())
            dr = random.uniform(SimParams.TASKDISPATCH_RATE_MIN*gop_e2ed, SimParams.TASKDISPATCH_RATE_MAX*gop_e2ed)
            gop_dispatch_time += dr
            taskset_dispatch_rates.append(dr)
                
        #print '%f'%self.env.now + "," + "TaskSet::,generateMPEG2FrameTaskSet, - " + str(len(self.taskList)) + " tasks generated, num_gops=" + str(num_gops)
        
        # archive to refer to later
        self.taskList_orig = list(self.taskList)
        
        avg_dispatch_rate =  float(sum(taskset_dispatch_rates))/float(len(taskset_dispatch_rates))
        min_dispatch_rate = min(taskset_dispatch_rates)
        
        final_gop_dispatch_time = gop_dispatch_times_list[-1]        
        return (final_gop_dispatch_time, avg_dispatch_rate, min_dispatch_rate)
        
    
    ## generates a MPEG-Frame- interrelated GOP task set
    ## we also provide the taskset dispatch times
    ## execution cost of one gop is similar to the next (probabilistically)
    def generateMPEG2FrameInterRelatedGOPTaskSet(self, num_gops, task_start_id, gop_start_id, unique_gop_start_id, \
                                  gop_structure = SimParams.GOP_STRUCTURE,                                  
                                  taskset_dispatch_start_time = 0.0,
                                  video_stream_id = None,
                                  wf_id = None,                                  
                                  frame_h=SimParams.FRAME_DEFAULT_H,
                                  frame_w=SimParams.FRAME_DEFAULT_W,
                                  frame_rate=SimParams.FRAME_RATE,
                                  priority_range = None):        
        
        
        # check pri range
        if (priority_range == None):
            sys.exit('Error: generateMPEG2FrameTaskSet:: error in pri range')
        
        taskset_dispatch_rates = []
        gop_dispatch_times_list = []
        all_gop_instances = []
        
        gop_dispatch_time = taskset_dispatch_start_time
        for each_gop_id in xrange(0,num_gops):            
             
            # get any deviation data for this gop
            gop_cc_dev = self._gop_cc_deviation()
            
            gop_instance = []   # reset
            temp_gop_frame_dict = {}
            frame_id = 0     # reset
            for each_frame in gop_structure:
                frame_task = MPEG2FrameTask_InterRelatedGOP(env = self.env, \
                                            id = (((each_gop_id) * SimParams.GOP_LENGTH) + frame_id) + task_start_id, \
                                            frame_type = str(each_frame), \
                                            frame_ix_in_gop = frame_id, \
                                            unique_gop_id = (each_gop_id + unique_gop_start_id), \
                                            gop_id = (each_gop_id+gop_start_id), \
                                            video_stream_id = video_stream_id, \
                                            wf_id = wf_id, \
                                            frame_h=frame_h, \
                                            frame_w=frame_w, \
                                            frame_rate=frame_rate, \
                                            priority = priority_range[frame_id], \
                                            previous_gop_tasks = all_gop_instances[each_gop_id-1] if len(all_gop_instances)>0 else None, \
                                            gop_cc_deviation = gop_cc_dev)
                
                frame_task.set_scheduledDispatchTime(gop_dispatch_time)
                gop_dispatch_times_list.append(gop_dispatch_time)
                
                # is this the first or last gop in the video stream ?
                if(each_gop_id == 0): # first
                    frame_task.set_isHeadVideoGop(True)
                elif(each_gop_id == (num_gops-1)): # last
                    frame_task.set_isTailVideoGop(True)
                
                gop_instance.append(frame_task)
                temp_gop_frame_dict[frame_id] = frame_task
            
                self.taskList.append(frame_task)
                frame_id = frame_id + 1
            
            for frame in gop_instance:
                frame.adjust_deadline(gop_instance)
                
            # adjust scheduled dispatch time for next gop
            gop_e2ed =  float(len(gop_instance))/float(gop_instance[0].get_framerate())
            dr = random.uniform(SimParams.TASKDISPATCH_RATE_MIN*gop_e2ed, SimParams.TASKDISPATCH_RATE_MAX*gop_e2ed)      
            gop_dispatch_time += dr
            taskset_dispatch_rates.append(dr)
            
            
            all_gop_instances.append(temp_gop_frame_dict)
                
        #print '%f'%self.env.now + "," + "TaskSet::,generateMPEG2FrameTaskSet, - " + str(len(self.taskList)) + " tasks generated, num_gops=" + str(num_gops)
        
        # archive to refer to later
        self.taskList_orig = list(self.taskList)
        
        avg_dispatch_rate =  float(sum(taskset_dispatch_rates))/float(len(taskset_dispatch_rates))
        min_dispatch_rate = min(taskset_dispatch_rates)
        
        final_gop_dispatch_time = gop_dispatch_times_list[-1]
        
        return (final_gop_dispatch_time, avg_dispatch_rate, min_dispatch_rate)
    
    
    
    
    ## generates a HEVC-Frame 
    ## we also provide the taskset dispatch times
    ## execution cost of one gop is similar to the next (probabilistically)
    def generateHEVCFrameTaskSet(self, num_gops, task_start_id, gop_start_id, unique_gop_start_id, \
                                  gop_structure = None,                                  
                                  taskset_dispatch_start_time = 0.0,
                                  video_stream_id = None, wf_id = None,                                                                    
                                  frame_h=SimParams.FRAME_DEFAULT_H, frame_w=SimParams.FRAME_DEFAULT_W,
                                  frame_rate = SimParams.FRAME_RATE,
                                  priority_range = None,                                                                    
                                  ):        
                
        # check pri range
        if (priority_range is None): sys.exit('Error: generateHEVCFrameTaskSet:: error in pri range')
        
        taskset_dispatch_rates = []
        gop_dispatch_times_list = []
                
        strm_resolution = frame_h*frame_w
        print "strm_resolution: ", strm_resolution, frame_h, frame_w
        
        (n_frame_slices, n_frame_tile_rows, n_frame_tile_cols) = self._get_slices_tile_rowscols(strm_resolution)
        
        ctu_size = (SimParams.HEVC_CTU_SIZE)
        n_frame_tiles = n_frame_tile_rows*n_frame_tile_cols
        total_num_ctus = int(float(strm_resolution)/float(ctu_size))
        n_ctus_per_slice = self._get_num_ctus_per_slice(n_frame_slices, total_num_ctus)
        
           
        #frame_slice_info = self.calc_hevc_slices(n_frame_slices)
        frame_slice_info = self.calc_hevc_slices_constantslicetype(n_frame_slices)
        
        #print "n_ctus_per_slice:: ", n_ctus_per_slice     
        #print "frame_slice_info::", frame_slice_info
        #print "n_frame_slices::", n_frame_slices
        #sys.exit()
        
        
        # only when using probabilistic gop model
#         gopprobmodel_fixed_GoPSize_N =  np.random.choice(HEVCWorkloadParams.HEVCWLPARAMS_POSSIBLE_GOP_SIZES(
#                                                                         HEVCWorkloadParams.HEVCWLPARAMS_GOPLEN_MIN_MAX[0],
#                                                                         HEVCWorkloadParams.HEVCWLPARAMS_GOPLEN_MIN_MAX[1],
#                                                                         )) 
        gopprobmodel_fixed_GoPSize_N =  np.random.choice([16,31])        
        gopprobmodel_fixed_nBMax = np.random.choice(HEVCWorkloadParams.HEVCWLPARAMS_CONTIG_BFRAMES_PROBS.keys())  
        gopprobmodel_fixed_movietype = np.random.choice(HEVCWorkloadParams.HEVCWLPARAMS_TYPES_OF_VIDEOS) 
        
        ## testing ##
        #gopprobmodel_fixed_GoPSize_N = 16
        #gopprobmodel_fixed_movietype = HEVCWorkloadParams.HEVCWLPARAMS_TYPES_OF_VIDEOS[wf_id]
        ###
        
        
        
        
        #gopprobmodel_fixed_movietype = 'ANIM'
        #gopprobmodel_fixed_movietype = HEVCWorkloadParams.HEVCWLPARAMS_TYPES_OF_VIDEOS[2]        
        #gopprobmodel_fixed_movietype = HEVCWorkloadParams.HEVCWLPARAMS_TYPES_OF_VIDEOS[0] # @UndefinedVariable        
#         precalc_fr_sizes = HEVCFrameTask.getPrecalc_ProbabilisticFramesize(frame_h, frame_w, 
#                                                                            gopprobmodel_fixed_movietype)
        
        print "gopprobmodel_fixed_movietype :: ", gopprobmodel_fixed_movietype
        
        task_level_decoded_data_output = {}        
        gop_dispatch_time = taskset_dispatch_start_time
        for each_gop_id in xrange(0,num_gops):            
            gop_instance = []   # reset
            
            unique_gop_id = (each_gop_id + unique_gop_start_id)
            
            # generate a gop structure
            if SimParams.HEVC_GOPGEN_USEPROBABILISTIC_MODEL==True:
                AGG = AdaptiveGoPGenerator_v2(gopprobmodel_fixed_nBMax, gopprobmodel_fixed_GoPSize_N, 
                                            SimParams.HEVC_ADAPTIVEGOPGEN_PARAM_PFRAME_REFS,
                                            SimParams.HEVC_ADAPTIVEGOPGEN_PARAM_BFRAME_REFS,
                                            movieType=gopprobmodel_fixed_movietype
                                          )
            else:
                # randomly select gop params
                randGoP_M = random.choice([2,4,8,16])
                if(randGoP_M<16):
                    randGoP_N = randGoP_M*random.choice([2,3])
                else:
                    randGoP_N = randGoP_M*2
                AGG = AdaptiveGoPGenerator(randGoP_M, randGoP_N,
                                           SimParams.HEVC_ADAPTIVEGOPGEN_PARAM_PFRAME_REFS,
                                           SimParams.HEVC_ADAPTIVEGOPGEN_PARAM_BFRAME_REFS,                                       
                                           )
            
            AGG.verifyAndRecreateGoP() # this will create a valid gop  (brute-force checking)
            
            gop_sequence = AGG.get_gopSeq()
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
                                            gop_id = (each_gop_id+gop_start_id),
                                            gop_struct = gop_sequence,
                                            video_stream_id = video_stream_id,
                                            wf_id = wf_id,
                                            frame_h=frame_h,
                                            frame_w=frame_w,
                                            frame_rate=frame_rate,
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
                                            )
                
                if (SimParams.HEVC_DUMP_FRAME_DATAFILE == True):
                    self.dump_frame_data(frame_task)
                
                frame_task.set_scheduledDispatchTime(gop_dispatch_time)
                gop_dispatch_times_list.append(gop_dispatch_time)
                
                # is this the first or last gop in the video stream ?
                if(each_gop_id == 0): # first
                    frame_task.set_isHeadVideoGop(True)
                elif(each_gop_id == (num_gops-1)): # last
                    frame_task.set_isTailVideoGop(True)
                
                gop_instance.append(frame_task)                
                self.taskList.append(frame_task)
                
                assert(n_frame_tiles == frame_task.getNumSubTasksTiles()), \
                 ", generateHEVCFrameTaskSet:: error in tile generation : %d, %d" % (n_frame_tiles, frame_task.getNumSubTasksTiles())

            # calculate the data dependency
            task_level_decoded_data_output = self.hevcframelevel_calc_expected_data_to_children(gop_instance, task_level_decoded_data_output)
            
            task_start_id =  gop_task_ids[-1]+1
            
            # adjust scheduled dispatch time for next gop
            gop_e2ed =  float(len(gop_instance))/float(gop_instance[0].get_framerate())
            dr = random.uniform(SimParams.TASKDISPATCH_RATE_MIN*gop_e2ed, SimParams.TASKDISPATCH_RATE_MAX*gop_e2ed)
            gop_dispatch_time += dr
            taskset_dispatch_rates.append(dr)
            
                
        print '%f'%self.env.now + "," + "TaskSet::,generateHEVCFrameTaskSet, - " + str(len(self.taskList)) + " tasks generated, num_gops=" + str(num_gops)
        
        # populate the data deps for each task in task list
        self.populate_expected_data_to_children(task_level_decoded_data_output)
        
        # archive to refer to later
        #self.taskList_orig = list(self.taskList)
        
        avg_dispatch_rate =  float(sum(taskset_dispatch_rates))/float(len(taskset_dispatch_rates))
        min_dispatch_rate = min(taskset_dispatch_rates)        
        final_gop_dispatch_time = gop_dispatch_times_list[-1]
        
        # see if we can flush the frame block-level info
        self.hevc_flush_frame_block_level_data()
        
        return (final_gop_dispatch_time, avg_dispatch_rate, min_dispatch_rate)
    
    
    
    def _get_slices_tile_rowscols(self, strm_resolution):        
        max_tiles_r = SimParams.HEVC_PICTURE_SPECIFIC_LIMITS[strm_resolution]['max_tiles_rows']
        max_tiles_c = SimParams.HEVC_PICTURE_SPECIFIC_LIMITS[strm_resolution]['max_tiles_cols']        
        
        # we assume tiles are always not equal
        n_frame_tile_rows = np.random.choice(max_tiles_r)                               
        n_frame_tile_cols = np.random.choice(max_tiles_c)
        n_frame_slices = n_frame_tile_rows*n_frame_tile_cols 
        
        return  (n_frame_slices, n_frame_tile_rows, n_frame_tile_cols)
    
    
    # we roughly give the same number of ctus per slice
    def _get_num_ctus_per_slice(self, total_num_slices, total_num_ctus):
        float_fair_num_ctus_per_slice = (float(total_num_ctus)/float(total_num_slices))        
        assert float_fair_num_ctus_per_slice > 1.0, "_get_num_ctus_per_slice:: Error - 1"
        
        if(float_fair_num_ctus_per_slice % 1 != 0):        # not a fair partition
            rounddown_fair_num_ctus_per_slice = int(float_fair_num_ctus_per_slice)        
            leftover_ctus = int(total_num_ctus - (rounddown_fair_num_ctus_per_slice*total_num_slices))        
            assert (leftover_ctus > 0), "_get_num_ctus_per_slice:: Error - 2"            
            ctus_per_slice = [rounddown_fair_num_ctus_per_slice]*total_num_slices
            # now decide where the other leftover ctus can be placed
            for each_leftover_ctu in xrange(leftover_ctus):
                rand_slice_ix = np.random.randint(0,total_num_slices) 
                ctus_per_slice[rand_slice_ix]+=1        
                
        else: # num ctus can be equal partitioned into slices 
            rounddown_fair_num_ctus_per_slice = int(float_fair_num_ctus_per_slice)
            ctus_per_slice = [rounddown_fair_num_ctus_per_slice]*total_num_slices
        
        assert (np.sum(ctus_per_slice) == total_num_ctus), "_get_num_ctus_per_slice:: Error - 3"
        return ctus_per_slice
    
    
    
    
    def hevcframelevel_calc_expected_data_to_children(self, gop_frame_tasks, task_level_decoded_data_output):
        # for each task in gop
        for each_task in gop_frame_tasks:
            each_task_id = each_task.get_id()
            # for each parent of the task
            each_task_expected_data_from_parents = each_task.get_expected_data_from_parents()
            
            for each_parent_task_id, each_parent_decoded_data in each_task_expected_data_from_parents.iteritems():
                #print each_parent_task_id
                if each_parent_task_id not in task_level_decoded_data_output:
                    task_level_decoded_data_output[each_parent_task_id] = {}
                    task_level_decoded_data_output[each_parent_task_id][each_task_id] = each_parent_decoded_data
                else:
                    if (each_task_id not in task_level_decoded_data_output[each_parent_task_id]):
                        task_level_decoded_data_output[each_parent_task_id][each_task_id] = each_parent_decoded_data
                    else:
                        task_level_decoded_data_output[each_parent_task_id][each_task_id] += each_parent_decoded_data
        
        return task_level_decoded_data_output
           
    
    def populate_expected_data_to_children(self, task_level_decoded_data_output):
        assert(len(task_level_decoded_data_output.keys())>0)
        
        # update the task_list structure
        for each_task in self.taskList:
            if each_task.get_id() in task_level_decoded_data_output:
                d = task_level_decoded_data_output[each_task.get_id()]
                each_task.set_expected_data_to_children(d)
            
    # for each task, we delete the frame block level info.
    def hevc_flush_frame_block_level_data(self):
        if SimParams.HEVC_MODEL_FLUSH_FRAMEBLOCK_INFO == True:
            for each_task in self.taskList:
                #print "BEFORE : hevc_flush_frame_block_level_data : blk_len, tid: ", len(each_task.frame_block_partitions.keys()), each_task.get_id()
                each_task.hack_abstract__frame_block_partitions()
                #print "AFTER : hevc_flush_frame_block_level_data : blk_len, tid: ", len(each_task.frame_block_partitions.keys()), each_task.get_id()
                
        else:
            pass
        
        collected = gc.collect()
        print "Garbage collector: collected %d objects." % (collected)
    
    
    
    
    def calc_hevc_slices_constantslicetype(self, num_slices_per_frame):
        results = {}
        for frame_type in ["I", "P", "B"]:
            results[frame_type]={}
            if frame_type == "I":                
                results[frame_type]['interleaved_slice_types'] = ['Is']*num_slices_per_frame
            elif frame_type == "P":
                results[frame_type]['interleaved_slice_types'] = ['Ps']*num_slices_per_frame
            elif frame_type == "B":
                results[frame_type]['interleaved_slice_types'] = ['Bs']*num_slices_per_frame
            else:
                pass
                
        return results
        
    
    # this is used to split the frame into slices
    def calc_hevc_slices(self, num_slices_per_frame):
        print "num_slices_per_frame: ", num_slices_per_frame        
        results = {}
        for frame_type in ["I", "P", "B"]:        
            # get the number of slices for each type
            if frame_type == "I":   
                # only i slices
                num_islices = num_slices_per_frame
                num_pslices = 0
                num_bslices = 0                
            elif frame_type == "P":
                # only i and p slices (precedence to p slices)
                min_p_slices = int(SimParams.HEVC_SLICE_TYPES_MIN_PROPORTIONS["P"]["Ps"]*float(num_slices_per_frame))  
                
                if min_p_slices < (num_slices_per_frame-1):                              
                    num_pslices = np.random.randint(min_p_slices, (num_slices_per_frame-1))
                    num_islices = num_slices_per_frame - num_pslices
                    num_bslices = 0                
                else:
                    num_pslices = num_slices_per_frame-1
                    num_islices = 1
                    num_bslices = 0                    
                    
            elif frame_type == "B":
                # I/P/B slices (precedence to b slices)
                min_b_slices = int(SimParams.HEVC_SLICE_TYPES_MIN_PROPORTIONS["B"]["Bs"]*float(num_slices_per_frame))
                if min_b_slices < (num_slices_per_frame-2):
                    num_bslices = np.random.randint(min_b_slices, num_slices_per_frame-2)                
                    num_pslices = np.random.randint(1, (num_slices_per_frame-num_bslices)-1)
                    num_islices = num_slices_per_frame - (num_pslices+num_bslices)
                else:
                    num_bslices = num_slices_per_frame-2
                    num_pslices = num_slices_per_frame-num_bslices
                    num_islices = 0                
                            
            # validate
            assert ((num_islices+num_pslices+num_bslices) == num_slices_per_frame), \
                    "slice categorisation invalid : %d, %d, %d, %d" % (num_islices,num_pslices,num_bslices, num_slices_per_frame)
            
            # combine them to make a single list (interleaved)
            islices_list = ['Is']*num_islices
            pslices_list = ['Ps']*num_pslices
            bslices_list = ['Bs']*num_bslices         
             
            interleaved_slice_types = [c.pop(0) for c in random.sample(
                                                  [islices_list]*len(islices_list) + 
                                                  [pslices_list]*len(pslices_list) + 
                                                  [bslices_list]*len(bslices_list),
                                                  len(islices_list)+len(pslices_list)+len(bslices_list))]       
            results[frame_type] = {
                                   'num_islices' : num_islices, 
                                   'num_pslices' : num_pslices, 
                                   'num_bslices' : num_bslices, 
                                   'interleaved_slice_types' : interleaved_slice_types
                                   }        
        return results
    
    
    
    def _gop_cc_deviation(self):
        result = {
        'decision' : MPEG2FrameTask_InterRelatedGOP.deviateFromPreviousGOP(),
        'dev_rat' :  MPEG2FrameTask_InterRelatedGOP.gopCCDeviationRatio()
        }
        return result
    
    ## get max_min of Frame_specific tasks : i.e (max,min) of I/P/B frames
    def get_maxmin_MPEG2Frame(self, all_tasks):
        i_frames_cc = []
        p_frames_cc = []
        b_frames_cc = []        
        
        for each_task in all_tasks:
            if(each_task.get_frameType() == "I"):
                i_frames_cc.append(each_task.get_computationCost())
            if(each_task.get_frameType() == "P"):
                p_frames_cc.append(each_task.get_computationCost())
            if(each_task.get_frameType() == "B"):
                b_frames_cc.append(each_task.get_computationCost())
                
        iframe_wcc = all_tasks[0].gen_Iframe_wcc()
        pframe_wcc = all_tasks[0].gen_Pframe_wcc()
        bframe_wcc = all_tasks[0].gen_Bframe_wcc()
        
        ## sanity check !!!
        if (type(all_tasks[0]) == MPEG2FrameTask):
            if(max(i_frames_cc) > iframe_wcc):
                sys.exit("Error: TaskSet:: get_maxmin_MPEG2Frame - bad  iframe_wcc")
            if(max(p_frames_cc) > pframe_wcc):
                sys.exit("Error: TaskSet:: get_maxmin_MPEG2Frame - bad  pframe_wcc")
            if(max(b_frames_cc) > bframe_wcc):
                sys.exit("Error: TaskSet:: get_maxmin_MPEG2Frame - bad  bframe_wcc")
        
        # check length of lists before calcs
        dummy_cc = 0.00000000000000001
        if len(i_frames_cc)>0:
            i_frame_result = ( max(i_frames_cc), float(sum(i_frames_cc)/float(len(i_frames_cc))), min(i_frames_cc) )
        else:
            sys.exit("get_maxmin_MPEG2Frame:: Error , No iframes")
        
        if len(p_frames_cc)>0:
            p_frame_result = ( max(p_frames_cc), float(sum(p_frames_cc)/float(len(p_frames_cc))), min(p_frames_cc) )
        else:
            p_frame_result = ( dummy_cc, dummy_cc, dummy_cc )
            
        if len(b_frames_cc)>0:
            b_frame_result = ( max(b_frames_cc), float(sum(b_frames_cc)/float(len(b_frames_cc))), min(b_frames_cc) )
        else:
            b_frame_result = ( dummy_cc, dummy_cc, dummy_cc )
        
                
        result = {
                  "I" : i_frame_result,
                  "P" : p_frame_result,
                  "B" : b_frame_result
                  }

#        result = {
#                  "I" : ( iframe_wcc, float(sum(i_frames_cc)/float(len(i_frames_cc))), min(i_frames_cc) ),
#                  "P" : ( pframe_wcc, float(sum(p_frames_cc)/float(len(p_frames_cc))), min(p_frames_cc) ),
#                  "B" : ( bframe_wcc, float(sum(b_frames_cc)/float(len(b_frames_cc))), min(b_frames_cc) )
#                  }
        
        return result
    
    
    # set worst-case, avg-case task costs
    def set_worstCaseComputationTime_alltasks(self):
        
        max_avg_min = self.get_maxmin_MPEG2Frame(self.taskList) 
        
        # worst-case
        max_i = max_avg_min["I"][0]
        max_p = max_avg_min["P"][0]
        max_b = max_avg_min["B"][0]
        
        assert((max_i != None) and (max_p != None) and (max_b != None)), "Error: set_worstCaseComputationTime_alltasks"
        assert((max_i > 0.0) and (max_p > 0.0) and (max_b > 0.0)), "Error: set_worstCaseComputationTime_alltasks"
        
        # avg-case
        avg_i = max_avg_min["I"][1]
        avg_p = max_avg_min["P"][1]
        avg_b = max_avg_min["B"][1]
        
        assert((avg_i != None) and (avg_p != None) and (avg_b != None)), "Error: set_worstCaseComputationTime_alltasks"
        assert((avg_i > 0.0) and (avg_p > 0.0) and (avg_b > 0.0)), "Error: set_worstCaseComputationTime_alltasks"
        
        
        for each_task in self.taskList:
            if(each_task.get_frameType() == "I"):
                #worst
                each_task.set_worstCaseComputationCost(max_i)
                each_task.set_worstCaseRemainingComputationCost(max_i)  
                # avg
                each_task.set_avgCaseComputationCost(avg_i)
                each_task.set_avgCaseRemainingComputationCost(avg_i)
                
            if(each_task.get_frameType() == "P"):
                #worst
                each_task.set_worstCaseComputationCost(max_p) 
                each_task.set_worstCaseRemainingComputationCost(max_p)
                # avg
                each_task.set_avgCaseComputationCost(avg_p)
                each_task.set_avgCaseRemainingComputationCost(avg_p)
                
            if(each_task.get_frameType() == "B"):
                #worst
                each_task.set_worstCaseComputationCost(max_b)
                each_task.set_worstCaseRemainingComputationCost(max_b)
                # avg
                each_task.set_avgCaseComputationCost(avg_b)
                each_task.set_avgCaseRemainingComputationCost(avg_b)
                
            # worst case-execution times for different frame types
            each_task.set_wccIFrame(max_i)
            each_task.set_wccPFrame(max_p)
            each_task.set_wccBFrame(max_b)
        
            # avg case-execution times for different frame types
            each_task.set_avgccIFrame(avg_i)
            each_task.set_avgccPFrame(avg_p)
            each_task.set_avgccBFrame(avg_b)
        
    
    ## getters ##
    def get_taskList(self):
        return self.taskList
    
    def get_Task(self):
        return self.taskList.pop(0)    # return first item
        
    
    def isEmpty(self):
        if(len(self.taskList)> 0):
            return False
        else:
            return True
    
    ######################
    ## data dumping   ####
    ######################
    def dump_frame_data(self, frame_task):
        file_info = {
                        'wf_id' : frame_task.get_wfid(),
                        'strm_id' : frame_task.get_video_stream_id(),
                        'ugid' : frame_task.get_unique_gop_id(),
                        'frame_ix' : frame_task.get_frameIXinGOP(),
                        'rand_seed' : SimParams.HEVC_FRAME_GENRAND_SEED                     
                     }
        data_obj = {
                    'frame_block_partitions' : frame_task.get_frame_block_partitions(), 
                    'frame_tile_partitions' : frame_task.get_frame_tile_partitions(),
                    'expected_data_from_parents' : frame_task.get_expected_data_from_parents(),
                    'expected_data_to_children' : frame_task.get_expected_data_to_children(),
                    'cc' : frame_task.get_computationCost(),
                    }
                    
        DataPreloader.dump_frame_data_file(data_obj, file_info)
        
    
    ######################
    ## debug specific ####
    ######################
    def printTaskSet(self):
        for each_task in self.taskList :
            print each_task
            print ""
    
    def dumpTaskSetToFile(self, fname='taskset.xml'):
        file = open(fname, "w")
        
        file.write("<TaskSet>")
        
        for each_task in self.taskList :
            file.write( each_task._debugLongXML() )
            file.write("\n")
        
        file.write("</TaskSet>")
        file.close()

          
        
    def plot_TaskComputationCostHistogram(self):
        hist_data = [t.get_computationCost() for t in self.taskList_orig]        
        
        self.fig_counter += 1
        fig = plt.figure(self.fig_counter)
        fig.canvas.set_window_title('TaskComputationCostHistogram')
        plt.hist(hist_data, alpha=0.5, color='g', bins=int(len(self.taskList_orig)))
        plt.grid(True)
        
    
        
        
        
        
        