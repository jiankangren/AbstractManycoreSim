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

import untangle




### load xml workflow file ###
with open ("../workflows.xml", "r") as myfile:
    xmldata=myfile.read()

wf_data = untangle.parse(xmldata)


fig = plt.figure()

for each_wf in wf_data.Workflows.workflow:
    x_cords = []
    for each_task in each_wf.Task:
        x_cords.append(float(each_task['sdt']))
        
    y_cords = [int(each_wf['id'])] * len(x_cords)
    
    plt.scatter(x_cords, y_cords)
    plt.hold(True)
    
    

plt.show()
    