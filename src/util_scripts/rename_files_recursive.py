import pprint
import sys, os
import re
import shutil


#DATA_DIR = '../experiment_data/mapping_and_pri_schemes'
DATA_DIR = "Z:/MCASim/experiment_data/hrt_video/util_vs_sched/"

for dirname, dirnames, filenames in os.walk(DATA_DIR):
    # print path to all subdirectories first.
    for subdirname in dirnames:
        if "seed" in subdirname:
            full_subdirname =  os.path.join(dirname, subdirname)
            
            #print full_subdirname
            
            # check files in subdir
            for subsubdirname, dirnames, filenames in os.walk(DATA_DIR+"/"+subdirname):
                #print " -- " + subsubdirname
                #full_subdirname2 =  os.path.join(dirname, subdirname, subsubdirname)
                if("ac11mp13pr4cmb0" in subsubdirname):                    
                    print subsubdirname
                    #print subsubdirname.replace("ac11mp13pr4cmb0", "ac11mp13pr4cmb0_old")
                    #os.rename(subsubdirname, subsubdirname.replace("ac11mp13pr4cmb0", "ac11mp13pr4cmb0_old2"))
                    
                    #shutil.rmtree(subsubdirname)
                    
                
            
            
            

