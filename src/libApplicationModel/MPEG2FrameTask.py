import pprint
import sys, os
import random
import time
import math
import numpy
from scipy.stats import rv_discrete
import scipy.stats as stats

## local imports
from Task import Task
from SimParams import SimParams


class MPEG2FrameTask(Task):
    
    
    # static array
    #PARALLEL_TASK_GOP_IX = [2,3,4,  5,6,7,  8,9,10,11]
    #PARALLEL_TASK_CORE_RESET = [1,4,7]
    
    
    def __init__(self, env, id, 
                 frame_h= SimParams.FRAME_DEFAULT_H, \
                 frame_w = SimParams.FRAME_DEFAULT_W, \
                 frame_rate = SimParams.FRAME_RATE, \
                 frame_type = "I", \
                 frame_ix_in_gop = 0, \
                 unique_gop_id = 0, \
                 gop_id = 0, \
                 gop_struct = SimParams.GOP_STRUCTURE, \
                 video_stream_id = None, \
                 wf_id = None, \
                 priority = None,
                 
                 ## optional params ##
                 calc_deps = True,
                 calc_cc = True,
                 calc_pri = True
                 ):
        
        ## pass params to parent class
        Task.__init__(self, env, "MPGFrame-"+frame_type, id, None, None, None, None, None, priority , env.now)
        
        ## gop-level
        self.parent_gop_id = gop_id         # same sequence of gops in two videos may have same same GOP number
        self.unique_gop_id = unique_gop_id  
        
        ##  frame level
        self.frame_h = frame_h
        self.frame_w = frame_w
        self.frame_rate = frame_rate
        self.frame_type =  frame_type 
        self.frame_num_pixels = (self.frame_h * self.frame_w)        
        self.frame_ix_in_gop = frame_ix_in_gop
        if(calc_pri==True):
            self.frame_priority = self.calc_FramePriorityInsideGOP(self.frame_ix_in_gop)    # according to isovic and fohler
        
        #self.priority = priority
        ## gop-level
        self.gop_structure = gop_struct        
        self.period = float(float(len(self.gop_structure))*float(1.0/float(self.frame_rate)))
        
        ## video-level
        self.video_stream_id = video_stream_id
        self.wf_id = wf_id
        self.video_genre = None
        self.IsHeadVideoGop = False   # is this frame in the first video stream GOP
        self.IsTailVideoGop = False   # is this frame in the last video stream GOP
        
        # platform level
        self.dispatched_ibuffid = None
        
        if(calc_deps==True):
            # which other frames/tasks do I need to complete this task ?
            self.frame_dependencies = self.calc_FrameDependencies(self.frame_ix_in_gop, self.id)['dep_gop_frames_ixs']
            self.set_dependencies(self.calc_FrameDependencies(self.frame_ix_in_gop, self.id)['dep_task_ids']) # dependent tasks
        
            # which other frame/task needs this task once it's completed ?
            # when task is finished these dep-pointers will be used to send the
            # completed task to the other cores
            # Note : these only track task_ids
            self.which_frames_needs_me = self.calc_FrameDependencies(self.frame_ix_in_gop, self.id)['which_frame_needs_current_frame']
            self.which_tasks_needs_me = self.calc_FrameDependencies(self.frame_ix_in_gop, self.id)['which_task_needs_current_task']
            self.my_closest_children = self.calc_FrameDependencies(self.frame_ix_in_gop, self.id)['my_closest_children']
            self.my_closest_parent = self.calc_FrameDependencies(self.frame_ix_in_gop, self.id)['my_closest_parent']
            self.non_dep_frames  = self.calc_FrameDependencies(self.frame_ix_in_gop, self.id)['non_dep_frames']
            self.possible_interfering_frame = self.calc_FrameDependencies(self.frame_ix_in_gop, self.id)['possible_interfering_frames']
        
        
        if(calc_cc==True):
            ##  block level specs
            self.block_h = 8
            self.block_w = 8
            #self.B_max = int(round((self.frame_h * self.frame_w) / (self.block_h * self.block_w)))  # max blocks per frame
            self.B_max = int(round( float(self.frame_h * self.frame_w) / float(self.block_h * self.block_w) ))  # max blocks per frame
            self.B_min = 0  # at least 1 block per frame ?
            
            ## block level timing specs (in ms)
            # refer to : 
            # [1]Y. Tan, P. Malani, Q. Qiu, and QingWu, 
            #     'Workload prediction and dynamic voltage scaling for MPEG decoding,'
            #     in Asia and South Pacific Conference on Design Automation, 2006,
            # [2]P. Malani, Y. Tan, and Q. Qiu, 
            # 'Resource-aware High Performance Scheduling for Embedded MPSoCs With the Application of MPEG Decoding,' 
            # in 2007 IEEE International Conference on Multimedia and Expo, 2007
            
            self.M1_t 	= float(SimParams.MPEG_BLOCK_M1_T * SimParams.CPU_EXEC_SPEED_RATIO) 	# used in : I, P, B  
            self.M2_t 	= float(SimParams.MPEG_BLOCK_M2_T * SimParams.CPU_EXEC_SPEED_RATIO) 	# used in : P
            self.M3_t 	= float(SimParams.MPEG_BLOCK_M3_T * SimParams.CPU_EXEC_SPEED_RATIO)	  	# used in : P
            self.M4_t 	= float(SimParams.MPEG_BLOCK_M4_T * SimParams.CPU_EXEC_SPEED_RATIO)		# used in : B  
            self.M5_t 	= float(SimParams.MPEG_BLOCK_M5_T * SimParams.CPU_EXEC_SPEED_RATIO)		# used in : B  
            self.M6_t 	= float(SimParams.MPEG_BLOCK_M6_T * SimParams.CPU_EXEC_SPEED_RATIO)		# used in : B
            self.M7_t 	= float(SimParams.MPEG_BLOCK_M7_T * SimParams.CPU_EXEC_SPEED_RATIO)		# used in : B
            self.M8_t 	= float(SimParams.MPEG_BLOCK_M8_T * SimParams.CPU_EXEC_SPEED_RATIO)		# used in : P, B
            self.M9_t 	= float(SimParams.MPEG_BLOCK_M9_T * SimParams.CPU_EXEC_SPEED_RATIO)		# Run-length coding time : propotional to frame size
            self.M10_t 	= float(SimParams.MPEG_BLOCK_M10_T * SimParams.CPU_EXEC_SPEED_RATIO)	# constant : used when generating the linear regression model
            
            ## task level rts specs - need to calculate
            cc = self.calc_FrameComputationTime(self.frame_type)
            self.set_computationCost(cc)
            self.set_remainingComputationCost(cc)
           
            ## deadline calculation
            dl = (1.0/self.frame_rate)
            self.set_deadline(dl)   # this will be adjusted later        
            
            self.end_to_end_deadline = (float(len(self.gop_structure))/float(self.frame_rate))
            
            max_mem = ((self.frame_h * self.frame_w) * 16)/8  # 16 bit, rgb, assume I_size = P_size = B_size  (in bytes)                                                                  )            
            self.set_maxMemConsumption(max_mem)
            self.set_timeLeftTillCompletion(cc)
            self.set_timeLeftTillDeadline(dl)
        
            self.absDeadline = None
            self.completedTaskSize = max_mem
        
        # worst case execution times of different types of frames - stored for later use
        self.wccIFrame = None
        self.wccPFrame = None
        self.wccBFrame = None
        
        # avg case execution times of different types of frames - stored for later use
        self.avgccIFrame = None
        self.avgccPFrame = None
        self.avgccBFrame = None        
        
        # time which all deps of the tasks were complete and available
        self.deps_allcomplete_time = None        
        
        # relative subtask deadline
        self.relative_deadline = None      
        
        # analytical wcet/wcrt
        self.analytical_wcet = None
        self.analytical_wcrt_with_deps = None
        
        # task size
        self.mpeg_tasksize = self.calc_encoded_mpegframe_size()
    
    def set_wccIFrame(self, wccI):
        self.wccIFrame = wccI
    def set_wccPFrame(self, wccP):
        self.wccPFrame = wccP
    def set_wccBFrame(self, wccB):
        self.wccBFrame = wccB        
    def set_avgccIFrame(self, avgccI):
        self.avgccIFrame = avgccI
    def set_avgccPFrame(self, avgccP):
        self.avgccPFrame = avgccP
    def set_avgccBFrame(self, avgccB):
        self.avgccBFrame = avgccB
    def set_wfid(self, wf_id):
        self.wf_id = wf_id
    def set_isTailVideoGop(self, bool):
        self.IsTailVideoGop = bool
    def set_isHeadVideoGop(self, bool):
        self.IsHeadVideoGop = bool
    def set_analytical_wcet(self, w):
        self.analytical_wcet = w
    def set_analytical_wcrt_with_deps(self, w):
        self.analytical_wcrt_with_deps = w
    def set_dispatched_ibuffid(self,ibuffid):
        self.dispatched_ibuffid = ibuffid
    def set_absDeadline(self, timenow):
        self.absDeadline = timenow + self.deadline
    def set_mpeg_tasksize(self, mts):
        self.mpeg_tasksize = mts
    def set_relative_deadline(self, rd):
        self.relative_deadline = rd
    def set_deps_allcomplete_time(self, dct):
        self.deps_allcomplete_time = dct
        
    def get_absDeadline(self):
        return self.absDeadline
    def get_which_tasks_needs_me(self): # task_ids
        return self.which_tasks_needs_me
    def get_children(self):
        return self.which_tasks_needs_me # task_ids
    def get_parents(self):
        return self.frame_dependencies
    def get_my_closest_children(self):
        return self.my_closest_children
    def get_my_closest_parent(self):
        return self.my_closest_parent
    def get_completedTaskSize(self):
        return self.completedTaskSize    
    def get_frameType(self):
        return self.frame_type
    def get_frameIXinGOP(self):
        return self.frame_ix_in_gop
    def get_parentGopId(self):
        return self.parent_gop_id
    def get_unique_gop_id(self):
        return self.unique_gop_id    
    def get_frame_h(self):
        return self.frame_h
    def get_frame_w(self):
        return self.frame_w    
    def get_framerate(self):
        return self.frame_rate
    def get_gopstructure(self):
        return self.gop_structure
    def get_video_stream_id(self):
        return self.video_stream_id
    def get_wccIFrame(self):
        return self.wccIFrame
    def get_wccPFrame(self):
        return self.wccPFrame
    def get_wccBFrame(self):
        return self.wccBFrame   
    def get_avgccIFrame(self):
        return self.avgccIFrame
    def get_avgccPFrame(self):
        return self.avgccPFrame
    def get_avgccBFrame(self):
        return self.avgccBFrame
    def get_wfid(self):
        return self.wf_id
    def get_non_dep_frames(self):
        return self.non_dep_frames
    def get_end_to_end_deadline(self):
        return self.end_to_end_deadline
    def get_children_frames(self):
        return self.which_frames_needs_me
    def get_isTailVideoGop(self):
        return self.IsTailVideoGop
    def get_isHeadVideoGop(self):
        return self.IsHeadVideoGop
    def get_possible_interfering_frame(self):
        return self.possible_interfering_frame    
    def get_analytical_wcet(self):
        return self.analytical_wcet
    def get_analytical_wcrt_with_deps(self):
        return self.analytical_wcrt_with_deps
    def get_dispatched_ibuffid(self):
        return self.dispatched_ibuffid
    def get_mpeg_tasksize(self):
        return self.mpeg_tasksize
    def get_relative_deadline(self):
        return self.relative_deadline
    def get_deps_allcomplete_time(self):
        return self.deps_allcomplete_time
    
    def __repr__(self):
        debug = "<Task "         
        debug += " type=" + self.type
        debug += " id=" + str(self.id) 
        debug += " cc=" + str(self.computationCost)
        debug += " mmc=" + str(self.maxMemConsumption)
        debug += " sdt=" + str(self.get_scheduledDispatchTime())
        debug += " rt=" + str(self.releaseTime)
        debug += " d=" + str(self.deadline)
        debug += " p=" + str(self.period)
        debug += " pri=" + str(self.priority)
        #debug += " stat=" +  str(self.status)
        #debug += " tltc=" +  str(self.timeLeftTillCompletion)
        #debug += " tltd=" +  str(self.timeLeftTillDeadline)
        debug += " st=" +  str(self.taskStartTime)
        debug += " tct=" +  str(self.taskCompleteTime)
        #debug += " mdf=" +  str(self.missedDeadlineFlag)
        debug += " dt=" +  str(self.dispatchTime)        
        
        # frame specific
        debug += " pgid=" +  str(self.parent_gop_id)
        debug += " frtyp=" +  str(self.frame_type)
        debug += " fr_gop_ix=" +  str(self.frame_ix_in_gop )
        debug += " frpr=" +  str(self.frame_priority)
        #debug += " dep=" +  str(self.dependencies)
        #debug += " fr_dep=" +  str(self.frame_dependencies)
        #debug += " wh_fnm=" +  str(self.which_frames_needs_me)
        #debug += " wh_tnm=" +  str(self.which_tasks_needs_me)
        
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
        debug += " stat='" +  str(self.status)+ "'"
        debug += " tltc='" +  str(self.timeLeftTillCompletion)+ "'"
        debug += " tltd='" +  str(self.timeLeftTillDeadline)+ "'"
        debug += " st='" +  str(self.taskStartTime)+ "'"
        debug += " tct='" +  str(self.taskCompleteTime)+ "'"
        debug += " sdt='" +  str(self.scheduledDispatchTime)+ "'"        
        debug += " mdf='" +  str(self.missedDeadlineFlag)+ "'"        
        debug += " wcc='" +  str(self.worstCaseComputationCost)+ "'"
        
        # frame specific
        debug += " pgid='" +  str(self.parent_gop_id)+ "'"
        debug += " ugid='" +  str(self.unique_gop_id)+ "'"
        debug += " frtyp='" +  str(self.frame_type)+ "'"
        debug += " fr_gop_ix='" +  str(self.frame_ix_in_gop )+ "'"
        debug += " frpr='" +  str(self.frame_priority)+ "'"
        debug += " dep='" +  str(self.dependencies)+ "'"
        debug += " fr_dep='" +  str(self.frame_dependencies)+ "'"
        debug += " wh_fnm='" +  str(self.which_frames_needs_me)+ "'"
        debug += " wh_tnm='" +  str(self.which_tasks_needs_me)+ "'"
                
        # stream specific
        debug += " wfid='" + str(self.wf_id)+ "'"
        debug += " vid='" + str(self.video_stream_id)+ "'"
        
        
        debug += " />"
    
        return debug
    
    
    def _debugShortLabel(self):
        debug = "<Task "
        debug += " id=" + str(self.id)
        debug += " frtyp=" +  str(self.frame_type)
        debug += " dep=" +  str(self.dependencies).replace(","," ")
        debug += " fr_dep=" +  str(self.frame_dependencies).replace(","," ")
        debug += " wh_fnm=" +  str(self.which_frames_needs_me).replace(","," ")
        debug += " wh_tnm=" +  str(self.which_tasks_needs_me).replace(","," ")
        
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
    
    # calculate the deadline, of the frame w.r.t to the gop-index and the frame_type
    # P frames deadline is related to B frames computation cost
    def adjust_deadline(self, all_frames_in_gop):
        
        ix = self.frame_ix_in_gop
       
        B2_IX = 2
        B5_IX = 5
        B8_IX = 8
        
        if(ix == 0):    # I(0)
            dl = (1.0/self.frame_rate)
        elif(ix == 1):  # P(1)
            dl = (2.0/self.frame_rate) - all_frames_in_gop[B2_IX].get_computationCost()
        elif(ix == 2):  # B(2)
            dl = (2.0/self.frame_rate)
        elif(ix == 3):  # B(3)
            dl = (3.0/self.frame_rate)
        elif(ix == 4):  # P(4)
            dl = (5.0/self.frame_rate) - all_frames_in_gop[B5_IX].get_computationCost()
        elif(ix == 5):  # B(5)
            dl = (5.0/self.frame_rate)
        elif(ix == 6):  # B(6)
            dl = (6.0/self.frame_rate)
        elif(ix == 7):  # P(7)
            dl = (8.0/self.frame_rate) - all_frames_in_gop[B8_IX].get_computationCost()
        elif(ix == 8):  # B(8)
            dl = (8.0/self.frame_rate)
        elif(ix == 9):  # B(9)
            dl = (9.0/self.frame_rate)
        elif(ix == 10):  # B(10)
            dl = (10.0/self.frame_rate)
        elif(ix == 11):  # B(11)
            dl = (11.0/self.frame_rate)
        
        self.set_deadline(dl)
    
    
    
    
    # assume constant GOP structure 
    # IBBPBBPBBPBB (display order)
    @staticmethod
    def calc_FramePriorityInsideGOP(ix):
        
        # fixed priority setting - for now..
        # GOP order:       I   P  B  B   P  B  B  P  B  B  B  B    (this is the decoder input order)
        # index    :       0   1  2  3   4  5  6  7  8  9 10 11
        #priority_order = [12, 11, 7, 7, 10, 7, 7, 9, 7, 7, 7, 7]
        priority_order = [12, 11, 4, 7, 10, 3, 5, 9, 2, 6, 1, 8]        
        
        return priority_order[ix]
    
    
    # each frame in the GOP has dependencies
    # I -> none
    # P -> I or P    (1 ref frame)
    # B -> I or P frames (always 2 ref frames)
    # GOP order:       I   P  B  B   P  B  B  P  B  B  B  B    (this is the decoder input order)
    # index    :       0   1  2  3   4  5  6  7  8  9 10 11 
    def calc_FrameDependencies(self, gop_ix, task_id):
        
        # for now we hardcode the dependencies - at the GOP level
        gop_level_dep = {
                        -2 : [], # mmc_rd
                        -1 : [], # mmc_wr
                        0   : [],
                        1   : [0],
                        2   : [0,1],
                        3   : [0,1], 
                        4   : [1],
                        5   : [1,4],
                        6   : [1,4],
                        7   : [4],
                        8   : [4,7],
                        9   : [4,7],
                        10  : [4,7],
                        11  : [4,7],
                        }
        
        
        task_level_dep = {
                        -2 : [], # mmc_rd
                        -1 : [], # mmc_wr
                        0   : [],
                        1   : [task_id-1],
                        2   : [task_id-1, task_id-2],
                        3   : [task_id-2, task_id-3], 
                        4   : [task_id-3],
                        5   : [task_id-1, task_id-4],
                        6   : [task_id-2, task_id-5],
                        7   : [task_id-3],
                        8   : [task_id-1 , task_id-4],
                        9   : [task_id-2,task_id-5],
                        10  : [task_id-3,task_id-6],
                        11  : [task_id-4,task_id-7],
                    }
        
        # B frames are not needed by anyone
        which_task_needs_current_task = {
                        -2 : [], # mmc_rd
                        -1 : [], # mmc_wr
                        0   : [task_id+1, task_id+2, task_id+3],
                        1   : [task_id+1, task_id+2, task_id+3, task_id+4, task_id+5],
                        2   : [],
                        3   : [], 
                        4   : [task_id+1, task_id+2, task_id+3, task_id+4, task_id+5, task_id+6, task_id+7],
                        5   : [],
                        6   : [],
                        7   : [task_id+1, task_id+2, task_id+3, task_id+4],
                        8   : [],
                        9   : [],
                        10  : [],
                        11  : [],                                         
         }
        
        # who are my closest children ?
        my_closest_children = {
                        -2 : [], # mmc_rd
                        -1 : [], # mmc_wr
                        0   : [task_id+1],
                        1   : [task_id+1, task_id+2, task_id+3],
                        2   : [],
                        3   : [], 
                        4   : [task_id+1, task_id+2, task_id+3],
                        5   : [],
                        6   : [],
                        7   : [task_id+1, task_id+2, task_id+3, task_id+4],
                        8   : [],
                        9   : [],
                        10  : [],
                        11  : [],                                         
         }
        
        # who is my closest parent ?
        my_closest_parent = {
                        -2 : None, # mmc_rd
                        -1 : None, # mmc_wr
                        0   : None,
                        1   : 0,
                        2   : 1,
                        3   : 1, 
                        4   : 1,
                        5   : 4,
                        6   : 4,
                        7   : 4,
                        8   : 7,
                        9   : 7,
                        10  : 7,
                        11  : 7,                                         
         }
        
        # B frames are not needed by anyone
        which_frame_needs_current_frame = {
                        -2 : [], # mmc_rd
                        -1 : [], # mmc_wr
                        0   : [1, 2, 3],
                        1   : [2, 3, 4, 5, 6],
                        2   : [],
                        3   : [], 
                        4   : [5, 6, 7, 8, 9, 10, 11],
                        5   : [],
                        6   : [],
                        7   : [8, 9, 10, 11],
                        8   : [],
                        9   : [],
                        10  : [],
                        11  : [],                                         
         }         
        
        # non-dependant frames
        # mainly used for interference set generation, each list will not interfere the frame specified by the key
        non_dep_frames = {
                        -2 : [], # mmc_rd
                        -1 : [], # mmc_wr
                        0   : [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
                        1   : [2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
                        2   : [],
                        3   : [], 
                        4   : [5, 6, 7, 8, 9, 10, 11],
                        5   : [],
                        6   : [],
                        7   : [8, 9, 10, 11],
                        8   : [],
                        9   : [],
                        10  : [],
                        11  : [],
        }
        
        # possible interferers (frames) : if child/parent then frame won't ever interfer
        possible_interfering_frames = {
                        -2 : [], # mmc_rd
                        -1 : [], # mmc_wr
                        0   : [],
                        1   : [],
                        2   : [3, 4, 5, 6, 7, 8, 9, 10, 11],
                        3   : [2, 4, 5, 6, 7, 8, 9, 10, 11], 
                        4   : [2, 3],
                        5   : [2, 3, 6, 7, 8, 9, 10, 11],
                        6   : [2, 3, 5, 7, 8, 9, 10, 11],
                        7   : [2, 3, 5, 6],
                        8   : [2, 3, 5, 6, 9, 10, 11],
                        9   : [2, 3, 5, 6, 8, 10, 11],
                        10  : [2, 3, 5, 6, 8, 9, 11],
                        11  : [2, 3, 5, 6, 8, 9, 10],
        }
        
        dependencies = {
               'dep_gop_frames_ixs'                 : gop_level_dep[gop_ix],
               'dep_task_ids'                       : task_level_dep[gop_ix],
               'which_task_needs_current_task'      : which_task_needs_current_task[gop_ix],
               'which_frame_needs_current_frame'    : which_frame_needs_current_frame[gop_ix],
               'my_closest_children'                : my_closest_children[gop_ix],
               'my_closest_parent'                  : my_closest_parent[gop_ix],
               'non_dep_frames'                     : non_dep_frames[gop_ix],
               'possible_interfering_frames'        : possible_interfering_frames[gop_ix]               
               }
        
        return dependencies
        
    
    
    def calc_encoded_mpegframe_size(self):
        size=0.0
        if self.frame_type == "I":
            size = float(self.frame_w * self.frame_h * 3) * SimParams.MPEG_COMPRESSION_RATIO_IFRAME
        elif self.frame_type == "P":
            size = float(self.frame_w * self.frame_h * 3) * SimParams.MPEG_COMPRESSION_RATIO_PFRAME
        elif self.frame_type == "B":
            size = float(self.frame_w * self.frame_h * 3) * SimParams.MPEG_COMPRESSION_RATIO_BFRAME
        
        return size
    
    ## if we can't decode the current frame we can 
    ## afford to drop this frame + (maybe) some
    ## other frames
    # GOP order:       I   P  B  B   P  B  B  P  B  B  B  B    (this is the decoder input order)
    # index    :       0   1  2  3   4  5  6  7  8  9 10 11 
    def calc_WhichFramesToDrop(self, frame_nodecode_ix):
        
        # for now we hardcode the specific
        # frames that can be dropped
        kill_list = {
                        0   : range(0,SimParams.GOP_LENGTH),
                        1   : range(1,SimParams.GOP_LENGTH),
                        2   : [2],
                        3   : [3], 
                        4   : range(4,SimParams.GOP_LENGTH),
                        5   : [5],
                        6   : [6],
                        7   : range(7,SimParams.GOP_LENGTH),
                        8   : [8],
                        9   : [9],                       
                        10  : [10],
                        11  : [11],
                        }
        
        return kill_list[frame_nodecode_ix]
    
    
    
    ## ASAP (As ealy as possible) release time calculation based on
    ## time now and position in the task_graph (taking into account
    ## precedence tasks)
    def calc_ASAP_ReleaseTime(self, ftype, frame_nodecode_ix, time_now, gop_frames):
        
        release_time = 0
        
        # get the key I/P frames from the gop
        for f in gop_frames:
            if f.get_frameIXinGOP() == 0:
                I0_frame = f
            elif f.get_frameIXinGOP() == 1:
                P1_frame = f
            elif f.get_frameIXinGOP() == 4:
                P4_frame = f
            elif f.get_frameIXinGOP() == 7:
                P7_frame = f
        
        if frame_nodecode_ix == 0:
            release_time = time_now
            
        elif frame_nodecode_ix == 1:
            release_time =  I0_frame.get_releaseTime() + self.wccIFrame
            
        elif frame_nodecode_ix == 2:
            release_time = P1_frame.get_releaseTime() \
                            +  self.wccPFrame
                            
        elif frame_nodecode_ix == 3:
            release_time = P1_frame.get_releaseTime() \
                            +  self.wccPFrame
                            
        elif frame_nodecode_ix == 4:
            release_time = P1_frame.get_releaseTime() \
                            +  self.wccPFrame
                            
        elif frame_nodecode_ix == 5:
            release_time = P4_frame.get_releaseTime() \
                            +  self.wccPFrame
            
        elif frame_nodecode_ix == 6:
            release_time = P4_frame.get_releaseTime() \
                            +  self.wccPFrame
                            
        elif frame_nodecode_ix == 7:
            release_time = P4_frame.get_releaseTime() \
                            +  self.wccPFrame
                            
        elif frame_nodecode_ix == 8:
            release_time = P7_frame.get_releaseTime() \
                            +  self.wccPFrame
                            
        elif frame_nodecode_ix == 9:
            release_time = P7_frame.get_releaseTime() \
                            +  self.wccPFrame
                            
        elif frame_nodecode_ix == 10:
            release_time = P7_frame.get_releaseTime() \
                            +  self.wccPFrame
                            
        elif frame_nodecode_ix == 11:
            release_time = P7_frame.get_releaseTime() \
                            +  self.wccPFrame
        
        
        return release_time
        
        
    def calc_FrameComputationTime(self, ftype):
        
        total_ct = 0.0
        
        # calc computation time for each frame-type        
        if(ftype == "I"):
            total_ct = self._generate_Iframe_ComputationTime()                
        elif(ftype == "P"):
            total_ct = self._generate_PFrame_ComputationTime()                
        elif(ftype == "B"):
            total_ct = self._generate_BFrame_ComputationTime()
        
        elif("MMC" in ftype):
            total_ct = 0.0
                            
        else:
            print os.path.basename(__file__) + ":" + __name__ + ":: Error - unknown frame_type"
            sys.exit(1)        
        
        return total_ct
    
    ######################
    ## helper functions ##
    ######################        
    def _generate_Iframe_ComputationTime(self):
        #PM1_n = float(numpy.random.randint(self.B_min, int(self.B_max)))
        
#         lower=int(float(self.B_max)*0.2)
#         upper=self.B_max
#         mu = int(float(self.B_max)*0.8)
#         sigma = 0.005        
#         truncnorm_obj = stats.truncnorm((lower - mu) / sigma, (upper - mu) / sigma, loc=mu, scale=sigma)
#         PM1_n = truncnorm_obj.rvs(1)[0]
        
        
        PM1_n = numpy.random.normal(float(self.B_max), float(self.B_max)*0.035, 3)[0]     
        while(PM1_n<1):
            PM1_n = numpy.random.normal(float(self.B_max), float(self.B_max)*0.035, 3)[0]
           
        ct =  (PM1_n * (self.M1_t)) + (float(self.frame_num_pixels) * self.M9_t) + self.M10_t
        
        #ct =  (self.B_max * (self.M1_t)) + (float(self.frame_num_pixels) * self.M9_t) + self.M10_t
        return ct 
    
    def _generate_PFrame_ComputationTime(self):
        #print "_generate_PFrame_ComputationTime::Enter"
        
        ct = 0.0        
        # find number of each block types in the frame
        PM1_n = float(numpy.random.randint(self.B_min, round(self.B_max*0.1)))
        PM2_n = float(numpy.random.randint(self.B_min, round(self.B_max*0.2)))
        PM3_n = float(numpy.random.randint(self.B_min, self.B_max))
        PM8_n = float(numpy.random.randint(self.B_min, self.B_max))
        
        # normalise and scale to B_max
        sum = float(PM1_n + PM2_n + PM3_n + PM8_n)
                
        PM1_n = round(float(PM1_n / sum) * float(self.B_max))
        PM2_n = round(float(PM2_n / sum) * float(self.B_max))
        PM3_n = round(float(PM3_n / sum) * float(self.B_max))
        PM8_n = round(float(PM8_n / sum) * float(self.B_max))
        
#        print "---"
#        print "PM1_n :" + str(PM1_n) 
#        print "PM2_n :" + str(PM2_n)
#        print "PM3_n :" + str(PM3_n)
#        print "PM8_n :" + str(PM8_n)
#        print "sum: " + str(numpy.sum([PM1_n, PM2_n, PM3_n, PM8_n]))       
#        print "---"
        
        # calculate total duration
        ct = (PM1_n * self.M1_t) + (PM2_n * self.M2_t) + \
            (PM3_n * self.M3_t) + (PM8_n * self.M8_t) + (float(self.frame_num_pixels) * self.M9_t) + self.M10_t        
        
        return ct
        
    def _generate_BFrame_ComputationTime(self):
        
        #print "_generate_BFrame_ComputationTime::Enter"
        
        ct = 0.0        
        # find number of each block types in the frame
        PM1_n = float(numpy.random.randint(self.B_min, round(self.B_max*0.01)))
        PM4_n = float(numpy.random.randint(self.B_min, round(self.B_max*0.01)))
        PM5_n = float(numpy.random.randint(self.B_min, self.B_max))
        PM6_n = float(numpy.random.randint(self.B_min, round(self.B_max*0.01)))
        PM7_n = float(numpy.random.randint(self.B_min, self.B_max))        
        PM8_n = float(numpy.random.randint(self.B_min, self.B_max))
        
        # normalise and scale to B_max
        sum = float(PM1_n + PM4_n + PM5_n + PM6_n + PM7_n + PM8_n)
        PM1_n = round((PM1_n / sum) * self.B_max) 
        PM4_n = round((PM4_n / sum) * self.B_max)
        PM5_n = round((PM5_n / sum) * self.B_max)
        PM6_n = round((PM6_n / sum) * self.B_max)
        PM7_n = round((PM7_n / sum) * self.B_max)
        PM8_n = round((PM8_n / sum) * self.B_max)
        
#        print "---"
#        print "PM1_n :" + str(PM1_n) 
#        print "PM4_n :" + str(PM4_n)
#        print "PM5_n :" + str(PM5_n)
#        print "PM6_n :" + str(PM6_n)
#        print "PM7_n :" + str(PM7_n)
#        print "PM8_n :" + str(PM8_n)
#        print "sum: " + str(numpy.sum([PM1_n, PM4_n, PM5_n, PM6_n, PM7_n, PM8_n]))
#        print "---"
        
        # calculate total duration
        ct = (PM1_n * self.M1_t) + (PM4_n * self.M4_t) + \
            (PM5_n * self.M5_t) + (PM6_n * self.M6_t) + \
            (PM7_n * self.M7_t) + (PM8_n * self.M8_t) + \
            (float(self.frame_num_pixels) * self.M9_t) + self.M10_t
            
        return ct
    
    
    @staticmethod
    def getStaticComputationCost(frame_h, frame_w, cpu_exec_speed_ratio):
        
        M1_t     = float(SimParams.MPEG_BLOCK_M1_T * cpu_exec_speed_ratio)     # used in : I, P, B  
        M2_t     = float(SimParams.MPEG_BLOCK_M2_T * cpu_exec_speed_ratio)     # used in : P
        M3_t     = float(SimParams.MPEG_BLOCK_M3_T * cpu_exec_speed_ratio)          # used in : P
        M4_t     = float(SimParams.MPEG_BLOCK_M4_T * cpu_exec_speed_ratio)        # used in : B  
        M5_t     = float(SimParams.MPEG_BLOCK_M5_T * cpu_exec_speed_ratio)        # used in : B  
        M6_t     = float(SimParams.MPEG_BLOCK_M6_T * cpu_exec_speed_ratio)        # used in : B
        M7_t     = float(SimParams.MPEG_BLOCK_M7_T * cpu_exec_speed_ratio)        # used in : B
        M8_t     = float(SimParams.MPEG_BLOCK_M8_T * cpu_exec_speed_ratio)        # used in : P, B
        M9_t     = float(SimParams.MPEG_BLOCK_M9_T * cpu_exec_speed_ratio)        # Run-length coding time : propotional to frame size
        M10_t     = float(SimParams.MPEG_BLOCK_M10_T * cpu_exec_speed_ratio)    # constant : used when generating the linear regression model
        
        B_max =  int(round((frame_h * frame_w) / (8*8)))  # max blocks per frame
        B_min = 0
        num_pixels = frame_h * frame_w 
        
        ########################
        # I-frame cost
        ########################        
        I_frame_cost =  (B_max * (M1_t)) + (float(num_pixels) * M9_t) + M10_t
        
        ########################
        # P-frame cost
        ########################        
        PM1_n = float(int(B_max*0.1))
        PM2_n = float(int(B_max*0.1))
        PM3_n = float(int(B_max*0.1))
        PM8_n = float(int(B_max*0.1))
        
        # normalise and scale to B_max
        sum = float(PM1_n + PM2_n + PM3_n + PM8_n)                
        PM1_n = round(float(PM1_n / sum) * float(B_max))
        PM2_n = round(float(PM2_n / sum) * float(B_max))
        PM3_n = round(float(PM3_n / sum) * float(B_max))
        PM8_n = round(float(PM8_n / sum) * float(B_max))
        
        # calculate total duration
        P_frame_cost = (PM1_n * M1_t) + (PM2_n * M2_t) + \
            (PM3_n * M3_t) + (PM8_n * M8_t) + (float(num_pixels) * M9_t) + M10_t
        
        ########################
        # B-frame cost
        ########################                
        # find number of each block types in the frame
        PM1_n = float(int(B_max*0.01))
        PM4_n = float(int(B_max*0.01))
        PM5_n = float(B_max)
        PM6_n = float(int(B_max*0.01))
        PM7_n = float(B_max)        
        PM8_n = float(B_max)
        
        # normalise and scale to B_max
        sum = float(PM1_n + PM4_n + PM5_n + PM6_n + PM7_n + PM8_n)
        PM1_n = round((PM1_n / sum) * B_max) 
        PM4_n = round((PM4_n / sum) * B_max)
        PM5_n = round((PM5_n / sum) * B_max)
        PM6_n = round((PM6_n / sum) * B_max)
        PM7_n = round((PM7_n / sum) * B_max)
        PM8_n = round((PM8_n / sum) * B_max)
        
        # calculate total duration
        B_frame_cost = (PM1_n * M1_t) + (PM4_n * M4_t) + \
            (PM5_n * M5_t) + (PM6_n * M6_t) + \
            (PM7_n * M7_t) + (PM8_n * M8_t) + \
            (float(num_pixels) * M9_t) + M10_t
        
        return (I_frame_cost, P_frame_cost, B_frame_cost)
    
        
    ##########################################
    ## generate the worst-case execution times
    ## for I/P/B frames
    ##########################################
    
    def gen_Iframe_wcc(self):
        ct =  (self.B_max * (self.M1_t)) + (float(self.frame_num_pixels) * self.M9_t) + self.M10_t
        return ct 
    
    def gen_Pframe_wcc(self):
        ct = 0.0        
        # find number of each block types in the frame
        PM1_n = 0.0
        PM2_n = float(self.B_max)
        PM3_n = 0.0
        PM8_n = 0.0
        
        # calculate total duration
        ct = (PM1_n * self.M1_t) + (PM2_n * self.M2_t) + \
            (PM3_n * self.M3_t) + (PM8_n * self.M8_t) + (float(self.frame_num_pixels) * self.M9_t) + self.M10_t       
        
        return ct
    
    def gen_Bframe_wcc(self):
        ct = 0.0   
             
        # find number of each block types in the frame
        PM1_n = 0.0
        PM4_n = 0.0
        PM5_n = 0.0
        PM6_n = float(self.B_max)
        PM7_n = 0.0        
        PM8_n = 0.0
                
        # calculate total duration
        ct = (PM1_n * self.M1_t) + (PM4_n * self.M4_t) + \
            (PM5_n * self.M5_t) + (PM6_n * self.M6_t) + \
            (PM7_n * self.M7_t) + (PM8_n * self.M8_t) + \
            (float(self.frame_num_pixels) * self.M9_t) + self.M10_t
            
        return ct
        
        
    ###############################################
    ## functions to assist schedulability analysis
    ###############################################
    
    def getInterferenceSet(self, allTasks):
        
        subset = []
        
        for each_task in allTasks:
            if(self.get_processingCore() == each_task.get_processingCore()):    # they are mapped on same core 
                if (self.get_id() != each_task.get_id()) and (self.get_priority()<=each_task.get_priority()):   # higher pr task                    
                    if(self.get_unique_gop_id() == each_task.get_unique_gop_id()): # are the tasks in the same gop ?                        
                        subset.append(each_task)                        
                    else:   
                        subset.append(each_task)
                    
        return subset
    
    
    def getInterferenceSet_withPrCnst(self, allTasks):
        
        subset = []
        
        for each_task in allTasks:
            if(self.get_processingCore() == each_task.get_processingCore()):    # they are mapped on same core
                if (self.get_id() != each_task.get_id()) and (self.get_priority()<=each_task.get_priority()):   # higher pr task
                    if(self.get_unique_gop_id() == each_task.get_unique_gop_id()): # are the tasks in the same gop ?
                        if(each_task.get_frameIXinGOP() in self.get_possible_interfering_frame()):  # at a gop level, due to parallelism/precedence, some frames may not interfere
                            subset.append(each_task)                        
                    else:   
                        subset.append(each_task)
                    
        return subset
        
    
    def getResponseTime(self, interferenceSet):
        
        wi = self.get_worstCaseComputationCost()
        wicopy = 0.0
        
        while( (wi != wicopy) and (wi <= self.get_end_to_end_deadline()) ):
            wicopy = wi
            interf = 0.0
            for each_i_task in interferenceSet:
                mult = int(math.ceil(wicopy/each_i_task.get_period()))
                interf +=  float((float(mult) * (1000000000.0 * each_i_task.get_worstCaseComputationCost())))
                
            wi = ((1000000000.0 * self.get_worstCaseComputationCost()) + interf)/1000000000.0            
        
#        if(wi > self.get_end_to_end_deadline()):
#            return sys.float_info.max   
        
        return wi
            
    
    def getUtilization(self):
        util = float(self.get_worstCaseComputationCost()/ self.period)
        return util
    
    
    def isSchedulable(self, taskSet):
        infSet = self.getInterferenceSet(taskSet)
        if(self.getResponseTime(infSet) <= self.get_end_to_end_deadline()):
            return True
        else:
            return False
           
        
    def isLate(self, time_now, lateness_ratio = 1.0):
      
        dispatched_time = self.get_dispatchTime()
        if(time_now > (dispatched_time + float(lateness_ratio * self.get_end_to_end_deadline()))):
            return True
        else:
            return False  
        
    # kao and garcia version - deadline distribution
    def isLate_KG(self, time_now, ddtype="EQF"):
        
        if(ddtype == "EQF"):
            absolute_deadline = self.getEstimatedDeadline_EQF()
        elif(ddtype == "ES"):
            absolute_deadline = self.getEstimatedDeadline_ES()
        else:
            sys.exit("isLate_KG - unknown ddtype")
        
        if(time_now > absolute_deadline):
            return True
        else:
            return False
    
    
    
    # kao and garcia version - deadline distribution (PSP)
    def isLate_Div_x(self, time_now, ddtype="EQF"):
        
        absolute_deadline = self.getEstimatedAbsoluteDeadline_Div_x()
        
        if(time_now > absolute_deadline):
            return True
        else:
            return False
    
    def estimatedLateness_Div_x(self, time_now):        
        absolute_deadline = self.getEstimatedAbsoluteDeadline_Div_x()            
        lateness = time_now - absolute_deadline
        return lateness
            
    def estimatedLateness_KG(self, time_now, ddtype="EQF"):
        if(ddtype == "EQF"):
            absolute_deadline = self.getEstimatedDeadline_EQF()
        elif(ddtype == "ES"):
            absolute_deadline = self.getEstimatedDeadline_ES()
        else:
            sys.exit("estimatedLateness_KG - unknown ddtype")
            
        lateness = time_now - absolute_deadline
        return lateness
    
    def estimatedLateness_ratiobased(self, time_now, lateness_ratio=1.0):        
        dispatched_time = self.get_dispatchTime()        
        lateness = time_now - (dispatched_time + float(lateness_ratio * self.get_end_to_end_deadline()))        
        return lateness
        
    # assume gop structure is the IPBBPBBPBBBB format
    def getCriticalPaths(self):
        critical_paths = \
        [
         [0, 1, 2],
         [0, 1, 3],
         [0, 1, 4, 5],
         [0, 1, 4, 6],
         [0, 1, 4, 7, 8],
         [0, 1, 4, 7, 9],
         [0, 1, 4, 7, 10],
         [0, 1, 4, 7, 11]         
        ]
         
        return critical_paths
    
    
    # assume gop structure is the IPBBPBBPBBBB format
    # we take into account the edges from node-->MMC(dst_task_ix = -1)
    # we take into account the edge from MMC (src_task_ix=-2)-->I_frame_task
    def getCriticalPaths_withMMCDataRDWR(self):
        critical_paths = \
        [                 
         # normal application task graph paths
         [-2, 0, 1, 2, -1],
         [-2, 0, 1, 3, -1],
         [-2, 0, 1, 4, 5, -1],
         [-2, 0, 1, 4, 6, -1],
         [-2, 0, 1, 4, 7, 8, -1],
         [-2, 0, 1, 4, 7, 9, -1],
         [-2, 0, 1, 4, 7, 10, -1],
         [-2, 0, 1, 4, 7, 11, -1],
         
         # i,p frames output to the mmc as well
         [-2, 0, -1],
         [-2, 0, 1, -1],
         [-2, 0, 1, 4, -1],
         [-2, 0, 1, 4, 7, -1]
                  
        ]
         
        return critical_paths
    
    # (absolute deadline) ratio-based
    def getEstimatedAbsoluteDeadline_ratioBased(self, lateness_ratio=SimParams.DYNAMIC_TASK_REMAPPING_TASK_LATE_ESTIM_LATENESS_RATIO):
        
        ai = self.get_dispatchTime()
        rdi = float(lateness_ratio * self.get_end_to_end_deadline()) # relative deadline            
        di =  ai +  rdi
        
        return di
    
    # (relative deadline) ratio-based
    def getEstimatedRelativeDeadline_ratioBased(self, lateness_ratio=SimParams.DYNAMIC_TASK_REMAPPING_TASK_LATE_ESTIM_LATENESS_RATIO):
        rdi = float(lateness_ratio * self.get_end_to_end_deadline()) # relative deadline
        return rdi

    
    
    # B. Kao and H. Garcia-Molina, "Deadline assignment in a distributed soft real-time system,"
    def getEstimatedDeadline_ES(self):
        
        ai = self.get_dispatchTime()
        ci = self.get_worstCaseComputationCost()
        De2e = self.get_end_to_end_deadline()
        
        sum_gop_ci = 0.0
        for each_frame_type in self.get_gopstructure():
            if(each_frame_type == "I"):
                sum_gop_ci += self.get_wccIFrame()
            elif(each_frame_type == "P"):
                sum_gop_ci += self.get_wccPFrame()
            elif(each_frame_type == "B"):
                sum_gop_ci += self.get_wccBFrame()
            
        
        di =  ai +  ci + ((De2e - ai - sum_gop_ci) / ( (len(self.get_gopstructure())-self.get_frameIXinGOP())+1 ))
        
        return di
        
    def getEstimatedDeadline_EQF(self):        
        ai = self.get_dispatchTime()
        ci = self.get_worstCaseComputationCost()
        De2e = self.get_end_to_end_deadline()
        
        # sum of all frames in gop
        sum_gop_ci = 0.0
        for each_frame_type in self.get_gopstructure():
            if(each_frame_type == "I"):
                sum_gop_ci += self.get_wccIFrame()
            elif(each_frame_type == "P"):
                sum_gop_ci += self.get_wccPFrame()
            elif(each_frame_type == "B"):
                sum_gop_ci += self.get_wccBFrame()
            
        # sum of all frames in gop - starting from current frame
        sum_gop_ci_m = 0.0
        for each_frame_type in self.get_gopstructure()[self.get_frameIXinGOP():]:
            if(each_frame_type == "I"):
                sum_gop_ci_m += self.get_wccIFrame()
            elif(each_frame_type == "P"):
                sum_gop_ci_m += self.get_wccPFrame()
            elif(each_frame_type == "B"):
                sum_gop_ci_m += self.get_wccBFrame()
        
        
        di =  ai +  ci + ((De2e - ai - sum_gop_ci) * ( ci/(sum_gop_ci_m)) )
        
        return di
    
    
    def getEstimatedRelativeDeadline_EQF(self, dispatch_time=None):        
        
        if (dispatch_time==None):
            ai = self.get_dispatchTime()
        else:
            ai = dispatch_time
            
        ci = self.get_worstCaseComputationCost()
        De2e = self.get_end_to_end_deadline()
        
        # sum of all frames in gop
        sum_gop_ci = 0.0
        for each_frame_type in self.get_gopstructure():
            if(each_frame_type == "I"):
                sum_gop_ci += self.get_wccIFrame()
            elif(each_frame_type == "P"):
                sum_gop_ci += self.get_wccPFrame()
            elif(each_frame_type == "B"):
                sum_gop_ci += self.get_wccBFrame()
            
        # sum of all frames in gop - starting from current frame
        sum_gop_ci_m = 0.0
        for each_frame_type in self.get_gopstructure()[self.get_frameIXinGOP():]:
            if(each_frame_type == "I"):
                sum_gop_ci_m += self.get_wccIFrame()
            elif(each_frame_type == "P"):
                sum_gop_ci_m += self.get_wccPFrame()
            elif(each_frame_type == "B"):
                sum_gop_ci_m += self.get_wccBFrame()
         
            #print each_frame_type
                
        di =  ai +  ci + ((De2e - ai - sum_gop_ci) * ( ci/(sum_gop_ci_m)) )
        
        print "---"
        print sum_gop_ci_m
        print sum_gop_ci
        print De2e
         
        print "ci=" + str(ci)
        print "di=" + str(di)
        print "ai=" + str(ai)
        
        print self.type, self.get_frameIXinGOP()
        print self.get_gopstructure()
        print self.get_wccIFrame()
        print self.get_wccPFrame()
        print self.get_wccBFrame()
        
        print "---"
        
        return (di - ai)
    
    
    
        
    
    def getEstimatedAbsoluteDeadline_Div_x(self):
        ai = self.get_dispatchTime()
        De2e = self.get_end_to_end_deadline()        
        n = float(len(self.gop_structure))
        x=1.0
        di = (De2e / (n*x)) + ai
        
        return di
    
    
    def getEstimatedRelativeDeadline_Div_x(self):        
        De2e = self.get_end_to_end_deadline()        
        n = float(len(self.gop_structure))
        x=1.0
        di = (De2e / (n*x)) * float(self.get_frameIXinGOP())
        
        return di
    
        
    def getEstimatedSlack_EQF(self):        
        est_slack = self.getEstimatedRelativeDeadline_EQF() - self.get_worstCaseComputationCost()
        return est_slack
    
    