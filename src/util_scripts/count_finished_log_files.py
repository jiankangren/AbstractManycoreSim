import pprint
import sys, os

DATA_DIR = '../logs'

for dirname, dirnames, filenames in os.walk(DATA_DIR):
    
    count_completed = 0
    count_incomplete = 0
    count_complete_wf8 = 0
    count_complete_wf12 = 0
    count_complete_wf16 = 0
    
    for each_fname in filenames:
        fname = dirname+ "/" + each_fname 
        #print fname
        
        if "seed" in each_fname:         
            # open and read last line
            with open(fname, 'rb') as fh:            
                last = fh.readlines()[-1]
                
                if "dumping" in last:
                    print fname + " :: Completed"
                    count_completed+=1
                    
                    if ("_8.out" in fname):
                        count_complete_wf8+=1
                    elif ("_12.out" in fname):
                        count_complete_wf12+=1
                    elif ("_16.out" in fname):
                        count_complete_wf16+=1
                        
                    
                else:
                    count_incomplete+=1
    
    print "------"
    print "Total complete: " + str(count_completed)
    print "Total incomplete: " + str(count_incomplete)
    print "Total complete_wf8: " + str(count_complete_wf8)
    print "Total complete_wf12: " + str(count_complete_wf12)
    print "Total complete_wf16: " + str(count_complete_wf16)
                    
        
    
    

