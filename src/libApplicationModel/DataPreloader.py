import pprint
import sys
import math, random
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import scipy.stats
from matplotlib.colors import ListedColormap, NoNorm
from matplotlib import mlab
from itertools import cycle # for automatic markers

import matplotlib.cm as cm
from matplotlib.font_manager import FontProperties

import pickle

## local imports


class DataPreloader():
    hevc_random_ctu= None
    dirname = "hevc_pregen_data_files/"
    
    @staticmethod
    def preload_data_files(fname="hevc_pregen_data_files/pregen_pus/hevc_probmodel_generate_PU_per_CTU_200ctus.p"):
        print "preload_data_files::Enter"
        DataPreloader.hevc_random_ctu = pickle.load( open( fname, "rb" ) )
        
    @staticmethod    
    def dump_frame_data_file(data_obj, file_info, file_dir="hevc_pregen_data_files/"):        
        fname = "HEVCFramePickleDataFile_%d_%d_%d_%d_%d_.p" % (file_info['wf_id'],
                                                        file_info['strm_id'],
                                                        file_info['ugid'],
                                                        file_info['frame_ix'],
                                                        file_info['rand_seed'])
        
        pickle.dump(data_obj, open( file_dir+fname, "wb" ))
        
    
    
    @staticmethod    
    def load_frame_data_file(file_info, file_dir="hevc_pregen_data_files/"):
        fname = "HEVCFramePickleDataFile_%d_%d_%d_%d_%d_.p" % (file_info['wf_id'],
                                                                file_info['strm_id'],
                                                                file_info['ugid'],
                                                                file_info['frame_ix'],
                                                                file_info['rand_seed'])        
        
        data_obj = pickle.load( open( file_dir+fname, "rb" ) )
        return data_obj