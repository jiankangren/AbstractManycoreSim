import sys, os, csv, pprint, math

from collections import OrderedDict
import numpy as np
import random
import shutil
import math
import matplotlib
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import scipy.stats
import itertools
from matplotlib.colors import ListedColormap, NoNorm
from matplotlib import mlab
from itertools import cycle # for automatic markers
import json
from operator import itemgetter

import matplotlib.cm as cm
from matplotlib.font_manager import FontProperties

from libNoCModel.NoCFlow import FlowType




###################################################################################################
#    search flw completed files
###################################################################################################
def search_flws_completed_bytype(fname, types=[1]):
    # get communication costs
    json_data=open(fname)
    flwscompleted_file_data = json.load(json_data)
    
    intfs_count = 0.0
    count = 0.0
    found_type_count = 0
    for each_flw_completed in flwscompleted_file_data:
        if(each_flw_completed['type'] in types):
            if(each_flw_completed['intfs'] >2):
                pprint.pprint(each_flw_completed['intfs'])
                intfs_count += float(each_flw_completed['intfs'])
            
            found_type_count +=1
            
        count += 1
              
    print len(flwscompleted_file_data)
    print float(intfs_count/count)
    print "found_type_count = " + str(found_type_count) + ", percentage=" + str(float(float(found_type_count)/float(len(flwscompleted_file_data))))
 






###################################
#    HELPERS
###################################





###################################
#    MAIN
###################################

search_flws_completed_bytype("../experiment_data/remapping_central_dynamic/RMOFF_test__flwcompleted.js", types=[FlowType.FLOWTYPE_MASTERSLAVESIGNALLING_TASKCOMPLETE])



print "finished"


