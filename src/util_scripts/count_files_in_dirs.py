import pprint
import sys, os
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

DATA_DIR = '../experiment_data/remapping_psbased_montecarlo'



total_count = 0
for dirname, dirnames, filenames in os.walk(DATA_DIR):
    # print path to all subdirectories first.
    for subdirname in dirnames:
        if "seed" in subdirname:
            full_subdirname =  os.path.join(dirname, subdirname)
            
            #print full_subdirname
            
            # check files in subdir
            
            count_wf8 = 0
            count_wf12 = 0
            count_wf16 = 0
            
            
            for dirname, dirnames, filenames in os.walk(DATA_DIR+"/"+subdirname):
                png_count = 0
                for each_fname in filenames:
                    #pprint.pprint(each_fname)                    
                    if "resultssummary" in each_fname:
                        png_count += 1
                        total_count += 1
                        
                        # count wf specific files
                        if ("wf8" in each_fname):
                            count_wf8+=1
                        elif ("wf12" in each_fname):
                            count_wf12+=1
                        elif ("wf16" in each_fname):
                            count_wf16+=1
                        
                        
                
            
            print dirname + " : *.png count = " + str(png_count) + ", wf8="+str(count_wf8) + \
                                                                    ", wf12="+str(count_wf12) + \
                                                                    ", wf16="+str(count_wf16)


print "Total count = " + str(total_count)
            

