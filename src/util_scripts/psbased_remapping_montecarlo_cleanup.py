import pprint
import sys, os
import json
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

MCERROR_FILE = 'Z:/MCASim/experiment_data/remapping_psbased_montecarlo/mcparam_error_.js'


# load file and get the erronous jobs
fname = MCERROR_FILE
json_data=open(fname)
error_files = json.load(json_data)


total_count = 0
for k,v in error_files.iteritems():
    
    
    
    fname_resultssumm = k
    fname_origdata = k.replace("_resultssummary.js", "_originaldata.zip")
    
    print fname_resultssumm
    print fname_origdata
    
    try:
        os.remove(fname_resultssumm)
        os.remove(fname_origdata)
    except Exception, e:
        print e
    
    total_count+=1
    

print "Total count = " + str(total_count)
            

