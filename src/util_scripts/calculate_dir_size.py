import pprint
import sys, os
import re


DATA_DIR = '../experiment_data/mapping_and_pri_schemes'


for dirname, dirnames, filenames in os.walk(DATA_DIR):
    
    # print path to all subdirectories first.
    for subdirname in dirnames:
        if "seed" in subdirname:
            full_subdirname =  os.path.join(dirname, subdirname)
            
            # check files in subdir
            for dirname, dirnames, filenames in os.walk(DATA_DIR+"/"+subdirname):
                total_size = 0
                for f in filenames:
                    fp = os.path.join(dirname, f)
                    total_size += os.path.getsize(fp)
                
                print dirname
                print float((total_size/1024)/1024);
                

