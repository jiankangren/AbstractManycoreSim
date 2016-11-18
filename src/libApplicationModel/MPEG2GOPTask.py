import pprint
import sys, os
import random
import time

## local imports
from Task import Task
from SimParams import SimParams



class MPEG2GOPTask(Task):
    
    
    
    def __init__(self, env, id, frame_h= 1152, frame_w = 1440, frame_rate = 25, gop_size = SimParams.GOP_LENGTH , \
                 gop_struct = SimParams.GOP_STRUCTURE,
                 priority = 1,
                 seed = time.time()):
        
        
        ## pass params to parent class
        Task.__init__(self, env, "MPEG2GOPTask", id, None, None, None, None, None, priority )
        
        ##  frame level
        self.frame_h = frame_h
        self.frame_w = frame_w
        self.frame_rate = frame_rate        
        
        ##  gop specific
        self.gop_length = gop_size
        self.gop_struct = gop_struct
        self.gop_size_bytes = self.gop_length * (self.frame_h * self.frame_w)       
        
        ##  block level specs
        self.block_h = 8
        self.block_w = 8
        self.B_max = int(round((self.frame_h * self.frame_w) / (self.block_h * self.block_w)))  # max blocks per frame
        self.B_min = 1  # at least 1 block per frame
        
        ## block level timing specs (in ms)
        # refer to : 
        # [1]Y. Tan, P. Malani, Q. Qiu, and QingWu, 
        #     'Workload prediction and dynamic voltage scaling for MPEG decoding,'
        #     in Asia and South Pacific Conference on Design Automation, 2006,
        # [2]P. Malani, Y. Tan, and Q. Qiu, 
        # 'Resource-aware High Performance Scheduling for Embedded MPSoCs With the Application of MPEG Decoding,' 
        # in 2007 IEEE International Conference on Multimedia and Expo, 2007
        
        self.M1_t = 0.000050
        self.M2_t = 0.000002
        self.M3_t = 0.000001
        self.M4_t = 0.000005
        self.M5_t = 0.000009
        self.M6_t = 0.000006
        self.M7_t = 0.000003
        self.M8_t = 0.000001
        self.M9_t = 0.000015  # Run-length coding time : propotional to frame size
        
        ## task level rts specs - need to calculate
        cc = self.calc_GOPComputationTime()
        self.set_computationCost(cc)
        dl = float(self.gop_length) * (1.0/self.frame_rate)
        #print float(self.gop_length) * (1.0/self.frame_rate)
        self.set_deadline(dl)
        
        max_mem = (((self.frame_h * self.frame_w) * self.gop_length) * (16)/8)  # 16 bit, rgb, assume I_size = P_size = B_size  # in bytes                                                                     )
        self.set_maxMemConsumption(max_mem)
        
        self.set_timeLeftTillCompletion(cc)
        self.set_timeLeftTillDeadline(dl)
        
        ## randomiser specific
        self._gop_rand_seed = seed + self.id
        #print self._gop_rand_seed
        
        
        
    def calc_GOPComputationTime(self):
        
        total_ct = 0
        
        # calc computation time for each frame-type
        for each_frame in self.gop_struct:
            if(each_frame == "I"):
                total_ct += self._generate_Iframe_ComputationTime()                
            elif(each_frame == "P"):
                total_ct += self._generate_PFrame_ComputationTime()                
            elif(each_frame == "B"):
                total_ct += self._generate_BFrame_ComputationTime()                
            else:
                print os.path.basename(__file__) + ":" + __name__ + ":: Error - unknown frame_type"
                sys.exit(1)        
        
        return total_ct
    
    ## helper functions ##        
    def _generate_Iframe_ComputationTime(self):
        ct =  (self.B_max * (self.M1_t)) + self.M9_t
        return ct 
    
    def _generate_PFrame_ComputationTime(self):
        ct = 0.0        
        # find number of each block types in the frame
        PM1_n = float(random.randint(self.B_min, self.B_max))
        PM2_n = float(random.randint(self.B_min, self.B_max))
        PM3_n = float(random.randint(self.B_min, self.B_max))
        PM8_n = float(random.randint(self.B_min, self.B_max))
        
        # normalise and scale to B_max
        sum = float(PM1_n + PM2_n + PM3_n + PM8_n)
                
        PM1_n = float(PM1_n / sum) * float(self.B_max)
        PM2_n = float(PM2_n / sum) * float(self.B_max)
        PM3_n = float(PM3_n / sum) * float(self.B_max)
        PM8_n = float(PM8_n / sum) * float(self.B_max)
        
        # calculate total duration
        ct = (PM1_n * self.M1_t) + (PM2_n * self.M2_t) + \
            (PM3_n * self.M3_t) + (PM8_n * self.M8_t) + self.M9_t        
        
        return ct
        
    def _generate_BFrame_ComputationTime(self):
        ct = 0.0        
        # find number of each block types in the frame
        PM1_n = float(random.randint(self.B_min, self.B_max))
        PM4_n = float(random.randint(self.B_min, self.B_max))
        PM5_n = float(random.randint(self.B_min, self.B_max))
        PM6_n = float(random.randint(self.B_min, self.B_max))
        PM7_n = float(random.randint(self.B_min, self.B_max))        
        PM8_n = float(random.randint(self.B_min, self.B_max))
        
        # normalise and scale to B_max
        sum = float(PM1_n + PM4_n + PM5_n + PM6_n + PM7_n + PM8_n)
        PM1_n = (PM1_n / sum) * self.B_max 
        PM4_n = (PM4_n / sum) * self.B_max
        PM5_n = (PM5_n / sum) * self.B_max
        PM6_n = (PM6_n / sum) * self.B_max
        PM7_n = (PM7_n / sum) * self.B_max
        PM8_n = (PM8_n / sum) * self.B_max
        
        # calculate total duration
        ct = (PM1_n * self.M1_t) + (PM4_n * self.M4_t) + \
            (PM5_n * self.M5_t) + (PM6_n * self.M6_t) + \
            (PM7_n * self.M7_t) + (PM8_n * self.M8_t) + \
            + self.M9_t
            
        return ct
        
        
        


        
        
        