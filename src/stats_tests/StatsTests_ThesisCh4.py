import sys, os, csv, pprint, math

from collections import OrderedDict
import numpy as np
import random
import shutil
import math
import scipy.stats
import itertools
from itertools import cycle # for automatic markers
import json
from operator import itemgetter


EXP_DATA_FOLDER = 'Z:/Simulator_versions_perExperiment/ThesisTechCh4/src/experiment_data/vs_ac_test/'



###################################################################################################
#    stat tests
###################################################################################################
# we only check the 
def get_vs_stats():
    vs_bs_fname = EXP_DATA_FOLDER + "data_ACTest_Results_VidStats_HeuVar.js"
    json_data=open(vs_bs_fname)
    file_data = json.load(json_data)



###################################
#    HELPERS
###################################





###################################
#    MAIN
###################################


print "finished"


