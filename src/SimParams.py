
import sys

## local imports
from libProcessingElement.LocalScheduler import LocalRRScheduler,    \
                        LocalEDFScheduler, \
                        LocalMPEG2FrameEDFScheduler, \
                        LocalMPEG2FrameListScheduler, \
                        LocalMPEG2FramePriorityScheduler, \
                        LocalMPEG2FramePriorityScheduler_WithDepCheck

from libApplicationModel.Task import TaskModel
from libResourceManager.AdmissionControllerOptions import AdmissionControllerOptions

from libMappingAndScheduling.SemiDynamic.TaskMappingSchemes import TaskMappingSchemes
from libMappingAndScheduling.SemiDynamic.TaskSemiDynamicPrioritySchemes import TaskSemiDynamicPrioritySchemes
from libMappingAndScheduling.SemiDynamic.TaskMappingAndPriAssCombinedSchemes import TaskMappingAndPriAssCombinedSchemes
from libMappingAndScheduling.Decentralised.TaskRemapDecentSchemes import TaskRemapDecentSchemes
from libMappingAndScheduling.FullyDynamic.TaskMappingSchemesFullyDyn import TaskMappingSchemesFullyDyn


from libResourceManager.RMTypes import RMTypes
from libProcessingElement.CPUTypes import CPUTypes
from libResourceManager.Mapper.MapperTypes import MapperTypes
from libTaskDispatcher.TDTypes import TDTypes


class SimParams(object):    
   
    ##################
    ## sim specific ##
    ##################
    SIM_RUNTIME = 100
    
    ##################
    ## temporary    ##
    ##################
    FR25_GOPLEN12_E2EDEADLINE = float(12.0/25.0)
    
    ########################
    ## workflows specific ##
    ########################
    NUM_WORKFLOWS = 4
    WFGEN_MIN_VIDS_PER_WF = 1
    WFGEN_MAX_VIDS_PER_WF = 1   # how many videos per streambuffer ?
    WFGEN_MIN_GOPS_PER_VID = 20 
    WFGEN_MAX_GOPS_PER_VID = 20 # how long is a video going to be ?
    WFGEN_MAX_INTER_VIDEO_GAP = float(FR25_GOPLEN12_E2EDEADLINE * 1.0) # what is the max gap between videos ?
    WFGEN_MIN_INTER_VIDEO_GAP = float(FR25_GOPLEN12_E2EDEADLINE * 1.0) # what is the min gap between videos ?    
    
    WFGEN_INITIAL_VID_GAP_MIN = float(FR25_GOPLEN12_E2EDEADLINE * 0.0)
    WFGEN_INITIAL_VID_GAP_MAX = float(FR25_GOPLEN12_E2EDEADLINE * 0.5) # low values make sure all wfs starts roughly at the same time
    
    WFGEN_INITIAL_VID_EQUAL_FOR_ALL_VIDS = True
    
    ##################################
    ## Simulation main entity types ##
    ##################################
    SIM_ENTITY_RESOURCEMANAGER_CLASS    = RMTypes.CLOSEDLOOP_DEFAULT
    SIM_ENTITY_CPUNODE_CLASS            = CPUTypes.CLOSEDLOOP_DEFAULT
    SIM_ENTITY_MAPPER_CLASS             = MapperTypes.CLOSEDLOOP_DEFAULT
    SIM_ENTITY_TASKDISPATCHER_CLASS     = TDTypes.CLOSEDLOOP_DEFAULT  
    
    #####################
    ## buffer specific ##
    #####################
    NUM_INPUTBUFFERS = NUM_WORKFLOWS
    INPUT_BUFF_SIZE = sys.maxint    # input buffer size per workflow
    INPUT_BUFF_SAFE_LEVEL = sys.maxint-100
    OUTPUT_BUFF_SIZE = sys.maxint
    
    #####################
    ## task dispatcher ##
    #####################
    TASKDISPATCH_RATE = float(float(12.0/25.0) * 1.0)
    #TASKDISPATCH_RATE_MAX = float(FR25_GOPLEN12_E2EDEADLINE * 1.3) # max gap between consecutive gops    (multiples of e2e deadline)
    #TASKDISPATCH_RATE_MIN = float(FR25_GOPLEN12_E2EDEADLINE * 1.0) # min gap between consecutive gops   (multiples of e2e deadline)

    TASKDISPATCH_RATE_MAX = 1.1 # max gap between consecutive gops    (multiples of e2e deadline)
    TASKDISPATCH_RATE_MIN = 1.0 # min gap between consecutive gops   (multiples of e2e deadline)
        
    TASKDISPATCHER_RESET_DELAY  = 0.000001    # need to start after the nodes
    TASKDISPATCHER_BLOCK_SIZE = 12  # gop size
    # what is the task model ? gop/frame/slice ? etc..
    TASK_MODEL = TaskModel.TASK_MODEL_MHEG2_FRAME_ET_LEVEL    
    #TASK_MODEL = TaskModel.TASK_MODEL_HEVC_FRAME_LEVEL    
    
    #########################
    ## mpeg model specific ##
    #########################    
    GOP_LENGTH = 12
    GOP_STRUCTURE = "IPBBPBBPBBBB"
    GOP_CRITICAL_PATH = "IPPPB"
    
    DEFAULT_END2END_DEADLINE = float(float(12.0/25.0) * 1.0)
    
    FRAME_RATE = 25
    MOVIE_LEN = 0.2   # mins
    FRAME_DEFAULT_W = 720
    FRAME_DEFAULT_H = 480
    NUM_GOPS = int(((MOVIE_LEN*60) * FRAME_RATE) / GOP_LENGTH)  # number of gops (task pool size), e.g. 60 min movie   
    
    #DVB_RESOLUTIONS = [(1920,1080),(1280,720),(720,576),(704,576),(544,576),(528,576),(480,576),(320,240)]
    #DVB_RESOLUTIONS = [(1280,720),(720,576),(704,576),(544,576),(528,576),(480,576),(426,240),(320,240)]
    
    #DVB_RESOLUTIONS = [(854,480),(720,576),(704,576),(544,576),(528,576),(480,576),(426,240),(320,240)]    # no problems for crossbar
    
    #DVB_RESOLUTIONS = [(480,576),(426,240),(320,240)]     # low-res
    #DVB_RESOLUTIONS = [(426,240),(320,240),(240,180),(230,180),(230,173),(176,132)]     # ultra-low-res
    #DVB_RESOLUTIONS = [(528,576),(480,576),(426,240),(320,240),(240,180),(230,180)]     # super-low-res
    
    #DVB_RESOLUTIONS = [(720,576), (544,576), (528,576), (480,576)]     # test
    
    #DVB_RESOLUTIONS = [(544,576), (528,576), (480,576), (426,240), (320,240), (240,180)]     # test
    #DVB_RESOLUTIONS = [(720,576), (544,576), (528,576), (480,576), (426,240), (320,240), (240,180)]     # test
    #DVB_RESOLUTIONS = [(528,576)]     # single-res    
    
    
#     DVB_RESOLUTIONS = [(3840,2160), 
#                        (2048,1080), (1920,1080), 
#                        (1280,720), (720,576), 
#                        (640,480), (544,576), 
#                        (528,576), (480,576),  
#                        (426,240), (320,240), 
#                        (240,180) ]                                                                                                                          
                                                        
#     DVB_RESOLUTIONS = [(3840,2160),
#                        (2048,1080), (1920,1080),
#                        (1280,720), (720,576),
#                        (640,480), (544,576),
#                        (528,576), (480,576),
#                       ]
    
    
    # youtube valid resolutions
    DVB_RESOLUTIONS = [(3840,2160),(2560,1440), 
                       (1920,1080),(1280,720),
                       (854,480),(640,360),
                       (426,240),
                      ]
    
    #DVB_RESOLUTIONS = [(3840,2160),(2560,1440)]
    #DVB_RESOLUTIONS = [(3840,2160),(2560,1440)]
    
    #DVB_RESOLUTIONS = [(3840,2160)]
    #DVB_RESOLUTIONS = [(640,480)]
    
    DVB_RESOLUTIONS_FIXED = []
    DVB_RESOLUTIONS_SELECTED_RANDOM = True
    
    # params to deal with probabilistic workload generation, where subsequent gops are similar in comp.cost
    MPEG2FRAMETASK_COMPCOST_DEVIATION_PROBABILITY = 0.10
    MPEG2FRAMETASK_COMPCOST_DEVIATION_CC_RANGE = (0.10, 0.15) # major deviation (probabilistically) percentage increase/decrease (e.g. 40%)
    MPEG2FRAMETASK_COMPCOST_INTERGOP_CC_RANGE = (+0.005, +0.01) # minor deviation (normal operation) percentages (e.g. 1% increase)
    
    # source : http://www.cs.cf.ac.uk/Dave/Multimedia/Lecture_Examples/Compression/mpegproj/#framesize
    MPEG_COMPRESSION_RATIO_IFRAME =  0.4
    MPEG_COMPRESSION_RATIO_PFRAME =  float(0.4 * 0.1)
    MPEG_COMPRESSION_RATIO_BFRAME =  float(0.4 * 0.02)
        
    # mpeg block level timings
    MPEG_BLOCK_M1_T     = 0.00000800        # used in : I, P, B  
    MPEG_BLOCK_M2_T     = 0.00001100        # used in : P
    MPEG_BLOCK_M3_T     = 0.00000400        # used in : P
    MPEG_BLOCK_M4_T     = 0.00000800        # used in : B  
    MPEG_BLOCK_M5_T     = 0.00000300        # used in : B  
    MPEG_BLOCK_M6_T     = 0.00001400        # used in : B
    MPEG_BLOCK_M7_T     = 0.00000500        # used in : B
    MPEG_BLOCK_M8_T     = 0.00000300        # used in : P, B
    MPEG_BLOCK_M9_T     = 0.000000100       # Run-length coding time : propotional to frame size
    MPEG_BLOCK_M10_T    = -0.00129700       # constant : used when generating the linear regression model
    
    TASKSET_MODEL = TaskModel.TASK_MODEL_HEVC_FRAME_LEVEL
    
     
    RESOLUTION_SPECIFIC_FRAME_RATE = {
                                      (3840*2160) : [60.0],
                                      (2560*1440) : [60.0],
                                      (1920*1080) : [60.0],
                                      (1280*720) : [30.0,60.0],
                                      (854*480) : [30.0,60.0],
                                      (640*360) : [30.0,60.0],
                                      (512*288) : [30.0,60.0],                                      
                                      }
    
    USE_VIDSTRM_SPECIFIC_FRAMERATE = False # above fps will be used if this is enabled
    
    
    ###############################
    ## H264/H265 Model specific
    ###############################
    HEVC_ADAPTIVEGOPGEN_PARAM_M = 8
    HEVC_ADAPTIVEGOPGEN_PARAM_N = 24
    HEVC_ADAPTIVEGOPGEN_PARAM_PFRAME_REFS = 1 # unidir
    HEVC_ADAPTIVEGOPGEN_PARAM_BFRAME_REFS = (1,1) # bidir
    
    HEVC_DUMP_FRAME_DATAFILE = False
    HEVC_LOAD_FRAME_DATAFILE = False
    HEVC_FRAME_GENRAND_SEED = None
    
    # related to tiles, slices etc.
    HEVC_CTU_SIZE = (64*64)
    HEVC_CTU_WIDTH = 64
    
    # the maximum number of slice types in a frame
    HEVC_SLICE_TYPES_MIN_PROPORTIONS = {
                                    "I" : { "Is" : 1.0, "Ps": 0, "Bs": 0 },
                                    "P" : { "Is" : 0.1,  "Ps": 0.5, "Bs": 0 },
                                    "B" : { "Is" : 0.1,  "Ps": 0.1, "Bs": 0.5 },
                                    }
    
    HEVC_SLICES_EQUAL_TILES = True
    
    HEVC_PICTURE_SPECIFIC_LIMITS = {                       
                                          
                                          # ultra-high-res
                                          #8K
                                          (7680*4320)   : {"max_num_slices_standards" : 600,
                                                           "max_num_slices" : 300,
                                                           "max_tiles_rows_cols_standards" : (20, 22),
                                                           "max_tiles_rows" : [3],
                                                           "max_tiles_cols" : [4,5]                                                                                                                      
                                                           },
                                          
                                          #4K : max tiles : 2*3=6, 2*5=10                
                                          (3840*2160)   : {"max_num_slices_standards" : 600,
                                                           "max_num_slices" : 300,
                                                           "max_tiles_rows_cols_standards" : (20, 22),
                                                           "max_tiles_rows" : [2],
                                                           "max_tiles_cols" : [4,5],     
                                                           },
                                    
                                          (2048*1080)   : {"max_num_slices_standards" : 200,
                                                           "max_num_slices" : 100,
                                                           "max_tiles_rows_cols_standards" : (20, 22),
                                                           "max_tiles_rows" : [2],
                                                           "max_tiles_cols" : [2,3],  
                                                           },
                                          
                                          (2560*1440)   : {"max_num_slices_standards" : 200,
                                                           "max_num_slices" : 100,
                                                           "max_tiles_rows_cols_standards" : (20, 22),
                                                           "max_tiles_rows" : [2],
                                                           "max_tiles_cols" : [3],   
                                                           },
                                          
                                          
                                          
                                          # high-res : max tiles : 2*3 = 6, 1*3=3
                                          (1920*1080)   : {"max_num_slices_standards" : 75,
                                                           "max_num_slices" : 50,
                                                           "max_tiles_rows_cols_standards" : (10, 11),
                                                           "max_tiles_rows" : [2],
                                                           "max_tiles_cols" : [2,3],  
                                                           },
                                    
                                          (1280*720)    : {"max_num_slices_standards" : 75,
                                                           "max_num_slices" : 50,
                                                           "max_tiles_rows_cols_standards" : (10, 11),
                                                           "max_tiles_rows" : [2],
                                                           "max_tiles_cols" : [2],  
                                                           },
                                    
                                          
                                    
                                          (720*576)     : {"max_num_slices_standards" : 40,
                                                           "max_num_slices" : 25,
                                                           "max_tiles_rows_cols_standards" : (5, 5),
                                                           "max_tiles_rows" : [1],
                                                           "max_tiles_cols" : [2,3],
                                                           }, 
                                                                                    
                                    
                                          # low-res : max tiles : 2*1 = 2
                                          (854*480)     : {"max_num_slices_standards" : 40,
                                                           "max_num_slices" : 25,
                                                           "max_tiles_rows_cols_standards" : (5, 5),
                                                           "max_tiles_rows" : [1],
                                                           "max_tiles_cols" : [2],  
                                                           },

                                          
                                          (544*576)     : {"max_num_slices_standards" : 30,
                                                           "max_num_slices" : 18,
                                                           "max_tiles_rows_cols_standards" : (5, 5),
                                                           "max_tiles_rows" : [1],
                                                           "max_tiles_cols" : [2],
                                                           },
                                    
                                          (528*576)     : {"max_num_slices_standards" : 30,
                                                           "max_num_slices" : 18,
                                                           "max_tiles_rows_cols_standards" : (5, 5),                                                           
                                                           "max_tiles_rows" : [1],
                                                           "max_tiles_cols" : [2],
                                                           },
                                    
                                          (480*576)     : {"max_num_slices_standards" : 20,
                                                           "max_num_slices" : 12,
                                                           "max_tiles_rows_cols_standards" : (3, 3),                                                           
                                                           "max_tiles_rows" : [1],
                                                           "max_tiles_cols" : [2],
                                                           },
                                    
                                          (640*360)     : {"max_num_slices_standards" : 20,
                                                           "max_num_slices" : 12,
                                                           "max_tiles_rows_cols_standards" : (3, 3),                                                           
                                                           "max_tiles_rows" : [1],
                                                           "max_tiles_cols" : [2],
                                                           },
                                    
                                    
                                           # super-low-res : max tiles : (1)*(1) = 1*1 = 1
                                          (512*288)     : {"max_num_slices_standards" : 20,
                                                           "max_num_slices" : 12,
                                                           "max_tiles_rows_cols_standards" : (3, 3),                                                           
                                                           "max_tiles_rows" : [1],
                                                           "max_tiles_cols" : [2],
                                                           },  
                                                                   
                                          (426*240)     : {"max_num_slices_standards" : 20,
                                                           "max_num_slices" : 12,
                                                           "max_tiles_rows_cols_standards" : (3, 3),                                                           
                                                           "max_tiles_rows" : [1],
                                                           "max_tiles_cols" : [1],
                                                           },
                                    
                                          (320*240)     : {"max_num_slices_standards" : 16,
                                                           "max_num_slices" : 8,
                                                           "max_tiles_rows_cols_standards" : (3, 3),                                                           
                                                           "max_tiles_rows" : [1],
                                                           "max_tiles_cols" : [1], 
                                                           },
                                    
                                          (240*180)     : {"max_num_slices_standards" : 16,
                                                           "max_num_slices" : 8,
                                                           "max_tiles_rows_cols_standards" : (3, 3),                                                           
                                                           "max_tiles_rows" : [1],
                                                           "max_tiles_cols" : [1],
                                                           },
                                    }
    
    
    #HEVC_PU_BLOCK_SIZES_INTRA =  [(64,64), (32, 32), (16,16), (8,8), (4,4)]
    #HEVC_PU_BLOCK_SIZES_INTER =  [(64,64), (32, 32), (16,16), (16,8), (8,8), (8,4), (4,4)]
    
    HEVC_PU_BLOCK_SIZES_INTRA =  [(64,64), (32, 32), (16,16), (8,8), (4,4)]
    HEVC_PU_BLOCK_SIZES_INTER =  [(64,64), (32, 32), (16,16), (8,8)]    
    
    HEVC_PU_BLOCK_SIZES_ALL = [64,32,16,8,4]
    
    
    HEVC_PU_BLOCK_SIZES_PROBABILITY = {                                        
                                          (7680*4320)   : {'intra' : [0.1, 0.1, 0.2, 0.3, 0.3],                                                                                                                      
                                                           'inter' : [0.05, 0.05, 0.1, 0.1, 0.2, 0.2, 0.3]},
                                                           
                                          (3840*2160)   : {'intra' : [0.1, 0.1, 0.2, 0.3, 0.3],                                                                                                                      
                                                           'inter' : [0.05, 0.05, 0.1, 0.1, 0.2, 0.2, 0.3]},
                                          
                                          (2560*1440)   : {'intra' : [0.1, 0.1, 0.2, 0.3, 0.3],                                                                                                                      
                                                           'inter' : [0.05, 0.05, 0.1, 0.1, 0.2, 0.2, 0.3]},
                                          
                                          (2048*1080)   : {'intra' : [0.1, 0.1, 0.2, 0.3, 0.3],                                                                                                                      
                                                           'inter' : [0.05, 0.05, 0.1, 0.1, 0.2, 0.2, 0.3]},
                                          
                                          # high-res
                                          (1920*1080)   : {'intra' : [0.1, 0.1, 0.2, 0.3, 0.3],                                                                                                                      
                                                           'inter' : [0.05, 0.05, 0.1, 0.1, 0.2, 0.2, 0.3]},
                                    
                                          (1280*720)    : {'intra' : [0.1, 0.1, 0.2, 0.3, 0.3],                                                                                                                      
                                                           'inter' : [0.05, 0.05, 0.1, 0.1, 0.2, 0.2, 0.3]},
                                    
                                          (720*576)     : {'intra' : [0.1, 0.1, 0.2, 0.3, 0.3],                                                                                                                      
                                                           'inter' : [0.05, 0.05, 0.1, 0.1, 0.2, 0.2, 0.3]}, 
                                       
                                          (854*480)     : {'intra' : [0.1, 0.1, 0.2, 0.3, 0.3],                                                                                                                      
                                                           'inter' : [0.05, 0.05, 0.1, 0.1, 0.2, 0.2, 0.3]},
                                    
                                          # med-res
                                          (640*480)     : {'intra' : [0.1, 0.1, 0.2, 0.2, 0.4],                                                                                                                      
                                                           'inter' : [0.025, 0.025, 0.5, 0.1, 0.1, 0.3, 0.4]},
                                    
                                          (544*576)     : {'intra' : [0.1, 0.1, 0.2, 0.2, 0.4],                                                                                                                      
                                                           'inter' : [0.025, 0.025, 0.5, 0.1, 0.1, 0.3, 0.4]},
                                    
                                          (528*576)     : {'intra' : [0.1, 0.1, 0.2, 0.2, 0.4],                                                                                                                      
                                                           'inter' : [0.025, 0.025, 0.5, 0.1, 0.1, 0.3, 0.4]},
                                    
                                          (480*576)     : {'intra' : [0.1, 0.1, 0.2, 0.2, 0.4],                                                                                                                      
                                                           'inter' : [0.025, 0.025, 0.5, 0.1, 0.1, 0.3, 0.4]},
                                           
                                           
                                          (640*360)     : {'intra' : [0.1, 0.1, 0.2, 0.2, 0.4],                                                                                                                      
                                                           'inter' : [0.025, 0.025, 0.5, 0.1, 0.1, 0.3, 0.4]},
                                       
                                           # low-res
                                          (512*288)     : {'intra' : [0.05, 0.05, 0.1, 0.3, 0.5],                                                                                                                      
                                                           'inter' : [0.025, 0.025, 0.025, 0.025, 0.1, 0.3, 0.5]},
                                                                           
                                          (426*240)     : {'intra' : [0.05, 0.05, 0.1, 0.3, 0.5],                                                                                                                      
                                                           'inter' : [0.025, 0.025, 0.025, 0.025, 0.1, 0.3, 0.5]},
                                    
                                          (320*240)     : {'intra' : [0.05, 0.05, 0.1, 0.3, 0.5],                                                                                                                      
                                                           'inter' : [0.025, 0.025, 0.025, 0.025, 0.1, 0.3, 0.5]},
                                    
                                          (240*180)     : {'intra' : [0.05, 0.05, 0.1, 0.3, 0.5],                                                                                                                      
                                                           'inter' : [0.025, 0.025, 0.025, 0.025, 0.1, 0.3, 0.5]},
                                       }
    
    
    
    # this is the cc for a block (any block)
    # so basically a CTU split into (8x8) blocks will take longer to process
    # than a CTU split into 32x32
    HEVC_FIXED_BLOCK_WCCC = {
                              "Ipu" : (0.0000001800, 0.0000002000), 
                              "Ppu" : (0.0000000100, 0.0000000200),
                              "Bpu" : (0.0000000500, 0.0000000800)
                              }
    
    HEVC_TILELEVEL_SPLITTING_ENABLE = False 
    
    # used to get the mpeg task size
    HEVC_COMPRESSION_RATIO_IFRAME =  0.2
    HEVC_COMPRESSION_RATIO_PFRAME =  float(0.2 * 0.1)
    HEVC_COMPRESSION_RATIO_BFRAME =  float(0.2 * 0.02)
    
    # enable this to work in reduced memory mode - block level information will be deleted
    HEVC_MODEL_FLUSH_FRAMEBLOCK_INFO = True    
    HEVC_GOPGEN_USEPROBABILISTIC_MODEL = True
    
        
    ###############################
    ## resource manager specific ##
    ###############################    
    #RESOURCEMANAGER_POLL_RATE = 1.0/10000.0
    RESOURCEMANAGER_POLL_RATE = 10.0
    RESOURCEMANAGER_ALLOC_NUM_TASKS = GOP_LENGTH  # how many tasks would the resource manager try to map - at a given instance 
    #RESOURCEMANAGER_MAPPING_POLICY = ? 
    SLACK_FEEDBACK_ENABLED = False    
    SYNCH_TIME_OFFSET = 0.0000001
    #SYNCH_TIME_OFFSET = 0.0
    RESOURCEMANAGER_NODEID = 0
    
    INTERRUPT_NODE_AFTER_DELAY = 0.0000000001
    INTERRUPT_RM_AFTER_DELAY = 0.0000000001
    
    RESOURCEMANAGER_USE_VOLATILE_TMTBL = False
    
    
    #############################################
    ## task mapping and pri assignment related ##
    #############################################    
    MAPPING_PREMAPPING_ENABLED = True    
    # mapping    
    DYNAMIC_TASK_MAPPING_SCHEME =  TaskMappingSchemes.TASKMAPPINGSCHEMES_LOWEST_UTILISATION_NEARESTPARENT
    FULLYDYNAMIC_TASK_MAPPING_SCHEME = TaskMappingSchemesFullyDyn.TASKMAPPINGSCHEMESFULLYDYN_LOWESTUTIL_NEARESTPARENT
    
    DYNAMIC_TASK_MAPPING_FROMFILE_FNAME = "MOGATestbenches\HdVidTestbench_test_4x4_mappingresult.txt"
    
    # pri-assignment    
    DYNAMIC_TASK_PRIASS_SCHEME =  TaskSemiDynamicPrioritySchemes.TASKSEMIDYNAMICPRIORITYSCHEMES_LOWRES_FIRST
    MAX_TASK_PRIORITY = 100000000
    
    # combined mapping and priority assignment
    COMBINED_MAPPING_AND_PRIASS = TaskMappingAndPriAssCombinedSchemes.TASKMAPPINGANDPRIASSCOMBINED_DISABLED
    #COMBINED_MAPPING_AND_PRIASS = TaskMappingAndPriAssCombinedSchemes.TASKMAPPINGANDPRIASSCOMBINED_IMPACTSCORING_V1    
        
    # remapping   
    DYNAMIC_TASK_REMAPPING_SCHEME = TaskRemapDecentSchemes.TASKREMAPPINGDECENTSCHEMES_NEIGHBOUR_HIGHEST_PSLEVEL
    DYNAMIC_TASK_REMAPPING_THRESHOLD = 2 # when you have this amount of late tasks, you start to remap
    DYNAMIC_TASK_REMAPPING_THRESHOLD_PERCENTAGE = 0.1 # when you have this amount of late tasks, you start to remap  
    DYNAMIC_TASK_REMAPPING_SAMPLING_INTERVAL = float(FR25_GOPLEN12_E2EDEADLINE * 4.6)
    DYNAMIC_TASK_REMAPPING_OFFLOAD_NUMTASKS = 1
    DYNAMIC_TASK_REMAPPING_TASK_LATE_ESTIM_LATENESS_RATIO = 0.4
    DYNAMIC_TASK_REMAPPING_MAX_IMPORTS = 1
    DYNAMIC_TASK_REMAPPING_ENABLED = False
    DYNAMIC_TASK_REMAPPING_SAMPLING_INTERVAL_OFFSET = 0.000001
    DYNAMIC_TASK_MAPPING_MODEL_MPTBL_UPDATE_NOTIFICATION = True
        
    
    #############################################
    ## Master slave signalling                 ##
    #############################################
    # paylaods (bytes)
    MS_SIGNALLING_TQCONTENTS_REQ_PAYLOAD = 32
    MS_SIGNALLING_TQCONTENTS_REP_PAYLOAD = 10000
    MS_SIGNALLING_TQSIZE_REQ_PAYLOAD = 32
    MS_SIGNALLING_TQSIZE_REP_PAYLOAD = 32
    MS_SIGNALLING_INTRNODE_NEWTASK_PAYLOAD = 32
    MS_SIGNALLING_INTRRM_ENDTASK_PAYLOAD = 64
    MS_SIGNALLING_INTRRM_ENDFLOW_PAYLOAD = 64
    
    # enable/disable signalling
    MS_SIGNALLING_TYPE_RM2N_REQ_TQINFO_STRMSTART_ENABLE     = False  
    MS_SIGNALLING_TYPE_N2RM_REP_TQINFO_STRMSTART_ENABLE     = False
    MS_SIGNALLING_TYPE_RM2N_REQ_TQINFO_JOBSTART_ENABLE      = False    
    MS_SIGNALLING_TYPE_N2RM_REP_TQINFO_JOBSTART_ENABLE      = False
    MS_SIGNALLING_TYPE_RM2N_REQ_TQSIZE_TASKRELEASE_ENABLE   = False   
    MS_SIGNALLING_TYPE_N2RM_REP_TQSIZE_TASKRELEASE_ENABLE   = False
    MS_SIGNALLING_TYPE_RM2N_INTERRUPT_TASKRELEASE_ENABLE    = False
    MS_SIGNALLING_TYPE_N2RM_INTERRUPT_TASKCOMPLETE_ENABLE   = False
    MS_SIGNALLING_TYPE_N2RM_INTERRUPT_FLOWCOMPLETE_ENABLE   = False
    
    # notify task/flow completion
    MS_SIGNALLING_NOTIFY_TASK_COMPLETE_ENABLE = False
    MS_SIGNALLING_NOTIFY_FLOW_COMPLETE_ENABLE = False    
    
    ###################################
    ## schedulability tests specific ##
    ###################################    
    OUTPUT_SCHED_TEST_LOG = False       
    WCRT_SCHEDULABILITY_TEST_PERCENTAGE = 100.0   # percentage of the schedulability test we look for
    WCRT_FLOW_CALC_TIMEOUT = 3.0*60.0   # this is the max time (mins) allowed to calculate the WCET of all the tasks and flows in the runtime app
    WCRT_FLOW_CALC_MAX_RECURSION_DEPTH=3
    WCRT_FLOW_USE_TIMEOUT = True
    WCRT_FLOW_USE_LIMITED_RECURSION_DEPTH = False
    
    ###################################
    ## Admission controller          ##
    ###################################    
    AC_TEST_OPTION = AdmissionControllerOptions.AC_OPTION_NONE
    
    ## Thresholded heuristic based test variables - system variables ##    
    AC_TEST_IBUFF_TASK_LATENESS_RATIO   = 1.0
    AC_TEST_TQ_TASK_LATENESS_RATIO      = 1.0    
    
    ###################
    ## node specific ##
    ###################
    NUM_NODES = 9
    CPUNODE_TASKQ_SIZE = sys.maxint
    CPUNODE_TASKQ_SAFE_LEVEL = sys.maxint-100
    CPUNODE_DEPENDANCY_BUFF_SIZE = sys.maxint
    CPUNODE_DEPENDANCY_BUFF_SAFE_LEVEL = sys.maxint-100
    CPU_IDLE_SLEEP_TIME = 0.5
    MEMWRITE_FLUSH_WINDOW = 10
    CPUNODE_MONITOR_TASKSET_SLACK = False
    #CPU_EXEC_SPEED_RATIO = 0.0105 # the block level execution values will be scalled up/down based on this ratio
    #CPU_EXEC_SPEED_RATIO = 0.02 # the block level execution values will be scalled up/down based on this ratio
    CPU_EXEC_SPEED_RATIO = 1.0
    
    ##################
    ## NoC specific ##
    ##################
    NOC_W = 3
    NOC_H = 3
    NOC_PERIOD                  =  0.00000001 # 100 MHz
    #NOC_PERIOD                  = 0.0000001 # 10 Mhz
    NOC_FLIT_BYTES              =  128/8            # 128 bits
    NOC_ARBITRATION_COST        =  NOC_PERIOD*7    
    NOC_FLOW_PRIORITY_LEVELS    = 10
    NOC_FLOW_MS_SIGNALLING_PRIORITY = -1    # a very low priority
    NOC_FLOW_MS_SIGNALLING_MAXPRIORITY = (-1*sys.maxint)-1
    NOC_PAYLOAD_4BYTES = 4
    NOC_PAYLOAD_8BYTES = 8
    NOC_PAYLOAD_16BYTES = 16    
    NOC_PAYLOAD_32BYTES = 32
    NOC_PAYLOAD_128BYTES = 128
    NOC_PAYLOAD_256BYTES = 256
    NOC_PAYLOAD_4KB = 4*1024
    NOC_MODEL_LOCAL_LINK = True
    
    ##############################
    ## local scheduler specific ##
    ##############################
    INTERRUPT_FREQ = 65
    LOCAL_SCHEDULER_TYPE =  LocalMPEG2FramePriorityScheduler()    
    
    ##########################
    ## main memory specific ##
    ##########################
    SHARED_MEM_SIZE = 1024 # in MB
    SHARED_MEM_WRITE_TIME_PER_MB = 0.000078125 # DDR3-1600    PC3-12800    12800 MB/s
    MMC_DATAREAD_FLOW_PRIORITY =  (-1*sys.maxint)-1 # max priority
    MMC_DATAWRITE_FLOW_PRIORITY =  0
    MMC_ENABLE_DATATRANSMISSION_MODELLING = True    
    
    # regarding where the MMCs are located
    MMC_CONTROLLER_LOCATIONS = ['north', 'south', 'west', 'east'] # this is very simple (assume all nodes in edges has access to the mmc)
    MMC_CONTROLLER_NUM_PER_SIDE = 1
    MMC_CONTROLLER_NUM_PORTS = 2 # e.g. 2 : means each controller has two ports hence connected to two nodes at the north, south, west..etc.
    MMC_SMART_NODE_SELECTION_ENABLE = False    
    MMC_SMART_NODE_SELECTION_TYPE = 0
    
    # assign mem port at task/job/video level ?
    MMC_PORT_ASSIGNMENT_LEVEL = 0 # {0=task, 1=job, 2=video}    
    
    MMC_MODEL_AS_EXT_COMPONENTS = True
    
    
    ####################################
    ## pheramone algorithm parameters ##
    ####################################
    PSALGO_ENABLED                      = False
    PSALGO_TQN                          = 0.463           # hormone propagation period (sec)
    PSALGO_TDECAY                       = 0.1286          # hormone decay period (sec)    
    PSALGO_INITQNCOUNT                  = 2               # initial queen node count 
    PSALGO_HARDCODE_QN_LOCATIONS        = [2,4,10,13]    
    PSALGO_THRESHOLDQN                  = 9.0             # queen node set hormone threshold (at which level does a node become a queen ?)
    PSALGO_THRESHOLDHOPCOUNT            = 2               # threshold hop count : after a certain number of hops the pheramone won't propagate
    PSALGO_KHOPDECAY                    = 0.25            # hop decay : at every hop, the pheramone decays by this amount
    PSALGO_KTIMEDECAY                   = 0.5             # periodic decay : at every decay cycle, the pheramone level of a node drops by this amount
    PSALGO_HQN                          = 14              # initial queen node pheromone dosage prop
    PSALGO_INITIALHORMONEAMNT_WORKER    = 25              # initial hormone amount for worker nodes
    PSALGO_INITIALHORMONEAMNT_QUEEN     = 25              # initial hormone amount for queen nodes
    PSALGO_USE_DYNAMICHORMONE           = False           # should the algorithm use fixed/dynamic hormone values ?
    PSALGO_FLOWBASEPRIORITY             = (-1*sys.maxint)-1
    PSALGO_PSFLOWPAYLOADSIZE            = 8               # how big is the signalling flow (bytes)
    PSALGO_REMAP_UTIL_THRESHOLD         = 0.58            # when the node reaches this utilisation level, remap 
    PSALGO_MONITOR_SNAPSHOT_PERIOD      = 0.035
    PSALGO_DYNAMIC_KTIMEDECAY_ENABLED   = False
    PSALGO_DYNAMIC_THRESHOLDQN_ENABLED  = True
    PSALGO_DYNAMIC_THRESHOLDQN_RATIO    = [0.1, 0.1]    # increment/decrement
    PSALGO_LIMIT_HORMONE_PROPAGATION    = True 
    PSALGO_MODEL_QSTATUS_CHECK_MSGS     = True
    
    # ps algo real-time viewer
    PSALGO_VIEWER_ENABLED               = False
    PSALGO_VIEWER_SAMPLERATE            = 0.005
    PSALGO_VIEWER_BLOCKONUSERINPUT      = False    
    #PSALGO_HD = [0,0]                   # [distance in hops to the QN that has produced it, actual dosage of the pheromone]
    
    
    ###############################################
    ## Castilhos Cluster Protocol Params         ##
    ###############################################
    CCP_REMAPPING_INTERVAL = 4.8
    CCP_SLAVE_MSG_FLOWPAYLOADSIZE = 8
    CCP_BASIC_MSG_FLOWPAYLOADSIZE = 8
    CCP_FLOWBASEPRIORITY = (-1*sys.maxint)-1
    CCP_CLUSTER_SIZE = [2,5]
    CCP_ENABLE = False
    CCP_LOAN_DELIVERY_MSG_SEND_OFFSET = 0.00000001
    CCP_SYNCH_TIME_OFFSET = 0.00000001
    CCP_LOAN_TASK_AMOUNT = 5    
    CCP_ENABLE_IMPROVEMENT = True
    CCP_REMOTE_SLAVE_HOPCOUNT = 2
    CCP_LM_LOCATION_MIDDLE = True
    
    
    ###############################################
    ## Cluster-tile task mapper parameters       ##
    ###############################################
    CLSTR_TILE_PARAM_CCR_RANGES_LOW = 0.08 # less than this
    CLSTR_TILE_PARAM_CCR_RANGES_MED = (0.08, 0.2) # between these values
    CLSTR_TILE_PARAM_CCR_RANGES_HIGH = 0.2 # higher than this
    CLSTR_TILE_PARAM_KAUSHIKS_ALGO_COMMS_SCALEUP_FACTOR = 9.0 # we use a scale factor because always the (comm. cost < comp. cost)
    
    CLSTR_TILE_PARAM_BGROUP_CCR_RANGES_LOW = 0.08 # less than this
    CLSTR_TILE_PARAM_BGROUP_CCR_RANGES_MED = (0.08, 0.2) # between these values
    CLSTR_TILE_PARAM_BGROUP_CCR_RANGES_HIGH = 0.2 # higher than this
    CLSTR_TILE_PARAM_BGROUP_NGT_HOPS = (4,1,1) # NGT hop count (low, med, high ccr ranges)       
    
    ########################
    ## monitoring         ##
    ########################    
    SIM_MONITOR_SAMPLE_RATE     = 0.2 # nyquist    
    TRACK_NODE_THROUGHPUT       = False
    TRACK_NODE_IDLETIME         = True
    TRACK_NOCLINKUTIL           = False
    TRACK_INPUTBUFF             = False
    TRACK_OUTPUTBUFF            = False
    TRACK_NODESTASKQ            = False
    TRACK_RMTASKRELEASE         = False
    TRACK_MAPPINGANDPRIASSINFO  = True  
    TRACK_TASKEXECTIMELINE      = True 
    TRACK_COMPLETED_FLOWINFO    = True
    TRACK_ADDED_FLOWINFO        = False
    TRACK_PSALGO_SNAPSHOT       = False
    TRACK_PSALGO_METRIC_SLACK   = False
    TRACK_TASK_REMAPPING        = False
    TRACK_WFLEVEL_TASKTIMELINE_PNG_DUMP  = False
    TRACK_WFSUMMARY_PPRINT      = False   
    TRACK_MAPPER_EXECOVERHEAD   = True
    
    #########################
    ## DEBUG Levels on/off ##
    #########################    
    DEBUG_LVL_CAT_INTERRUPT             = False
    DEBUG_LVL_CAT_TRANSMIT              = False
    DEBUG_LVL_CAT_SCHEDANALYSIS         = False
    DEBUG_LVL_CAT_RUNTIMEAPP            = True    
    DEBUG_LVL_CAT_CPUINFO               = True
    DEBUG_LVL_CAT_CPUINFO_VERBOSE       = False
    DEBUG_LVL_CAT_RMINFO                = False
    DEBUG_LVL_CAT_MAPPERINFO            = False
    DEBUG_LVL_CAT_RMINFO_VERBOSE        = False
    DEBUG_LVL_CAT_TDINFO                = True
    DEBUG_LVL_CAT_TDDROPPEDTASKS        = False
    DEBUG_LVL_CAT_NOCFLWTBLINFO         = False
    DEBUG_LVL_CAT_NOCFLWTBLINFO_VERBOSE = False
    DEBUG_LVL_CAT_NOCFLOW               = False # not in use   
    DEBUG_LVL_CAT_LOCALSCHED_PREEMPT    = False
    DEBUG_LVL_CAT_PSALGO                = False
    DEBUG_LVL_CAT_TASKREMAPPING         = False
    DEBUG_LVL_CAT_TASKREMAPPING_NOTIFICATION    = False
    DEBUG_LVL_CAT_MSSIGNALLING          = False
    DEBUG_LVL_CAT_MMCNODEDATATRANSFER   = False
    DEBUG_LVL_CAT_CCPROTOCOL            = False
        
    ## log output - at runtime ##
    LOG_OUTPUT_NOCFLOWINFO                  = False
    LOG_OUTPUT_SCHED_TEST_REPORT            = False
    

    
