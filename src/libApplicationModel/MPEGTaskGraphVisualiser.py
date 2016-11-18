import pprint
import sys, os
import math, random
import numpy as np
import bisect
import itertools
import networkx as nx
import matplotlib.pyplot as plt
from collections import Counter, Sequence
from collections import OrderedDict

# local imports
from AdaptiveGoPGenerator import AdaptiveGoPGenerator


def _get_fr_node_col(fr_type):
    if fr_type == "I":
        col = "#FFB2B2"
    elif fr_type == "P":
        col = "#B2FFB2"
    elif fr_type == "B":
        col = "#B2B2FF"
    elif fr_type == "b":
        col = "#B2B2FF"
        
    return col

def createGraph(DG, frameLevelRefs):
    ':type DG: DiGraph'
    
    for each_node_k, each_node_v in frameLevelRefs.iteritems():        
        fwd_pred_ref_frames = each_node_v['fwd_pred']
        bwd_pred_ref_frames = each_node_v['bwd_pred']
                
        if(fwd_pred_ref_frames != None):        
            for each_frame in fwd_pred_ref_frames:
                ref_node_label = each_frame['fr'] + str(each_frame['frix'])
                DG.add_edge(ref_node_label, each_node_k)                
                
        if (bwd_pred_ref_frames != None):        
            for each_frame in bwd_pred_ref_frames:
                ref_node_label = each_frame['fr'] + str(each_frame['frix'])
                DG.add_edge(ref_node_label, each_node_k)
       
    # colorize
    for each_node_k, each_node_v in frameLevelRefs.iteritems():
        ftype = AdaptiveGoPGenerator.nxLabel2Frame(each_node_k)['ftype']
        DG.node[each_node_k]['fillcolor']=_get_fr_node_col(ftype)
        DG.node[each_node_k]['style']='filled'
        DG.node[each_node_k]['fontsize']='30'
        DG.node[each_node_k]['arrowsize']="10.0"
         
                
    return DG
    

def checkZeroPredecessors(DG):
    nodes_list = nx.nodes(DG)
    
    num_nodes_with_zero_preds = []
    for each_node in nodes_list:        
        if (len(DG.predecessors(each_node)) == 0) and ("I" not in each_node):
            num_nodes_with_zero_preds.append(each_node)
            
    return len(num_nodes_with_zero_preds)
        




def showGraph(DG):

    ':type DG: DiGraph'
    
    # Need to create a layout when doing
    # separate calls to draw nodes and edges
    pos = nx.spring_layout(DG)
    #nx.draw_networkx_nodes(DG, pos, cmap=plt.get_cmap('jet'), node_color = values)
    nx.draw(DG, pos, arrows=True, with_labels=True)
    plt.show()
    

# write dot file to use with graphviz
# run "dot -Tpng test.dot >test.png"
def output_png(DG, lbl, dir = "/home/rosh/Documents/EngD/Papers/Paper_HEVC/generated_tgs/", format="png"):    
    dot_fname = dir+'tg_test_'+lbl+'.dot'
    png_fname =  dir+'tg_test_'+lbl+'.' + format 
    
    nx.write_dot(DG,dot_fname)
    
    cmd = "dot -T" + format +" "+ dot_fname + " >" + png_fname    
    print cmd
    os.system(cmd)



#######################################
# MAIN
#######################################



if __name__ == "__main__":

    #random.seed(1234)
    #np.random.seed(1234)
    
    M=8; N=M*3
    #M=8; N=24
    #M=2; N=4
    
    #M = random.choice([2,4,8,16])
    #N = M*random.choice(2,3)
    
    # randGoP_M = random.choice([2,4,8,16])
    # if(randGoP_M<16):
    #     randGoP_N = randGoP_M*random.choice([2,3])
    # else:
    #     randGoP_N = randGoP_M*2
    
    
    print "M=",M
    print "N=",N
    
    numPframerefs = 1
    numBframerefs = (1,1) # per direction
    
    NUM_GOPS = 11
    
    
    correct_graphs = []
    correct_nx_graphs = []
    incorrect_graphs = []
    gops_generated =0
    while(gops_generated < NUM_GOPS):   
        
        # create
        AGG = AdaptiveGoPGenerator(M, N, numPframerefs, numBframerefs)
        AGG.verifyAndRecreateGoP()
        
        if AGG not in correct_graphs:
            correct_graphs.append(AGG)
            
            # add to networkx
            DG = nx.DiGraph()
            DG = createGraph(DG, AGG.frameLevelRefs)
            correct_nx_graphs.append(DG)
            
            gops_generated+=1
            
            print gops_generated
    #     if ( len(list(nx.simple_cycles(DG))) == 0) and \
    #         (AGG.numNodesWithoutRefs()==0) and \
    #         (checkZeroPredecessors(DG)==0):
    #             if (AGG not in correct_graphs):
    #                 correct_graphs.append(AGG)
    #                 correct_nx_graphs.append(DG)
    #             
    #     else:
    #         if (AGG not in incorrect_graphs):
    #             incorrect_graphs.append(AGG)
        
        #pprint.pprint( list(nx.simple_cycles(DG)))
    
        #showGraph(DG)
        #print i
    
    print "--"
    print len (correct_graphs)
    print len (incorrect_graphs)
    
    #for n in correct_nx_graphs[0].nodes():
    #    print n , ", parents:: ", correct_nx_graphs[0].predecessors(n),  ":: children: " , correct_nx_graphs[0].successors(n)
        
    #pprint.pprint(nx.topological_sort(correct_nx_graphs[0]))
    
    #showGraph(correct_nx_graphs[0])
    
    
    
    # output 10 graphs
    num_images = 10
    for i in xrange(num_images):
        lbl = "%d_%d_%d" %(M,N,i)
        output_png(correct_nx_graphs[i], lbl)
    
    
    
