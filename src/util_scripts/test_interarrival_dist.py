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

all_items = []
for i in xrange(10000):
    dr = random.uniform(1.0*0.48, 1.3*0.48)
    all_items.append(dr)


print np.mean(all_items)
print np.std(all_items)



f = plt.figure()
plt.hist(all_items, bins=100)

plt.show()
