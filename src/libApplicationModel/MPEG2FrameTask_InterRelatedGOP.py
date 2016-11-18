import pprint
import sys, os
import random
import time
import math
import numpy

## local imports
from Task import Task
from SimParams import SimParams
from MPEG2FrameTask import MPEG2FrameTask

class MPEG2FrameTask_InterRelatedGOP(MPEG2FrameTask):
    
    
    # static array
    PARALLEL_TASK_GOP_IX = [2,3,4,  5,6,7,  8,9,10,11]
    PARALLEL_TASK_CORE_RESET = [1,4,7]
    
    
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
                 priority = None, \
                 previous_gop_tasks = None,
                 gop_cc_deviation = None):
        
        ## pass params to parent class
        MPEG2FrameTask.__init__(self, env, id, \
                                frame_h, frame_w, frame_rate, frame_type, frame_ix_in_gop, \
                                unique_gop_id, gop_id, gop_struct, \
                                video_stream_id, wf_id, \
                                priority) 
        
        self.type = "MPGFrameIRGOP-"+frame_type
        
        self.prev_gop_tasks = previous_gop_tasks
        self.devFromPrevGOP = self.deviateFromPreviousGOP()
        self.gop_cc_deviation = gop_cc_deviation
        
        ## task level rts specs - need to calculate
        cc = self.calc_FrameComputationTime_interelatedGOP(self.frame_type)
        self.set_computationCost(cc)
        self.set_remainingComputationCost(cc)
        self.set_timeLeftTillCompletion(cc)
        
        
   
    # return true/false based on deviation probability
    # if true that means there will be a spike or dip in execution cost
    @staticmethod
    def deviateFromPreviousGOP():        
        return (numpy.random.random() < SimParams.MPEG2FRAMETASK_COMPCOST_DEVIATION_PROBABILITY)
    
    
    @staticmethod
    def  gopCCDeviationRatio():
        dr = numpy.random.uniform(SimParams.MPEG2FRAMETASK_COMPCOST_DEVIATION_CC_RANGE[0], 
                                       SimParams.MPEG2FRAMETASK_COMPCOST_DEVIATION_CC_RANGE[1])
        
        dev_rat = float(dr * (1.0 if numpy.random.random()<0.5 else -1.0))
        
        return dev_rat
    
    def calc_FrameComputationTime_interelatedGOP(self, ftype):
        
        total_ct = 0.0
        ct = None
        
        # calc computation time for each frame-type        
        if(ftype == "I"):
            total_ct = self._generate_Iframe_ComputationTime()                
        elif(ftype == "P"):
            total_ct = self._generate_PFrame_ComputationTime()                
        elif(ftype == "B"):
            total_ct = self._generate_BFrame_ComputationTime()                
        else:
            print os.path.basename(__file__) + ":" + __name__ + ":: Error - unknown frame_type"
            sys.exit(1)       
                       
            
        # perform usual calculation model
        if(self.parent_gop_id > 0):
            if(self.prev_gop_tasks != None):                        
                prev_gop_frame_exec_cost = self.prev_gop_tasks[self.frame_ix_in_gop].get_computationCost()
            else:
                sys.exit("Error: calc_FrameComputationTime_interelatedGOP:: prev gop not provided")
            # check if this gop would be a MAJOR deviation
            if(self.gop_cc_deviation['decision'] == True):
                # radically change the execution time (spike or dip)
                #cc_deviation = prev_gop_frame_exec_cost * self.gop_cc_deviation['dev_rat']
                ct = prev_gop_frame_exec_cost + float(prev_gop_frame_exec_cost * self.gop_cc_deviation['dev_rat'])
                                
#                 # either increase or decrease the comp.cost
#                 if(numpy.random.random()<0.5): 
#                     ct =  prev_gop_frame_exec_cost + cc_deviation
#                 else: 
#                     ct =  prev_gop_frame_exec_cost - cc_deviation                
                            
            # MINOR deviation so change the execution cost slightly
            else:
                # here deviation can be negative or positive
                cc_deviation = prev_gop_frame_exec_cost * numpy.random.uniform(SimParams.MPEG2FRAMETASK_COMPCOST_INTERGOP_CC_RANGE[0], 
                                                                               SimParams.MPEG2FRAMETASK_COMPCOST_INTERGOP_CC_RANGE[1])                
                if(numpy.random.random()<0.5):                
                    ct = prev_gop_frame_exec_cost + cc_deviation
                else:
                    ct = prev_gop_frame_exec_cost - cc_deviation
                
        else:        
            ct =  total_ct       
        
        if(ct<0.0):
            sys.exit('Error: calc_FrameComputationTime_interelatedGOP:: error - negative comp cost')
        
        
        return ct 
            
            
    
    ######################
    ## helper functions ##
    ######################        
    
        
   