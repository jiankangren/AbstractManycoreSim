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


from SimParams import SimParams
from libNoCModel.NoCFlow import FlowType



NOC_X = 6
NOC_Y = 6
NUM_NODES = NOC_X*NOC_Y


def plot_Network_Plevel_colormap(show_text=True, dump_fname = None):
    
    print "plot_Network_Plevel_colormap"
    
    # cleanup any log files
    try:
        if(dump_fname != None):
            os.remove(dump_fname)
    except OSError:
        pass
    
    # get data
    fname = "../test__psalgonodeprops.js"    
    json_data=open(fname)
    psalgonodeprops_data = json.load(json_data)
        
    # plot
    fig = plt.figure()
    fig.canvas.set_window_title('plot_Network_Plevel_colormap')
    
    num_snapshots = len(psalgonodeprops_data)
    
    subplots_x = int(math.ceil(math.sqrt(num_snapshots)))
    subplots_y = subplots_x
    
    for each_snapshot_ix in xrange(1,(subplots_x*subplots_y)):        
        if(each_snapshot_ix < num_snapshots):
            all_snapshot_data = [each_node['plevel'] for each_node in psalgonodeprops_data[each_snapshot_ix-1]]
            all_snapshot_data_reshaped = np.reshape(all_snapshot_data, (NOC_X, NOC_Y))            
            all_snapshot_data_max = max(all_snapshot_data)
            
            ax = plt.subplot(subplots_x,subplots_y,each_snapshot_ix, aspect='equal')            
            plt.pcolor(all_snapshot_data_reshaped, cmap=plt.gray(), vmin=0, vmax=all_snapshot_data_max)
            subplot_title = psalgonodeprops_data[each_snapshot_ix-1][0]['t']
            plt.title(subplot_title)
            plt.colorbar()
                        
            # text
            if(show_text == True):
                ind_array = np.arange(0., np.float(NOC_X), 1.)
                x, y = np.meshgrid(ind_array, ind_array)
                
                i=0
                for x_val, y_val in zip(x.flatten(), y.flatten()):
                    c = all_snapshot_data[i]
                    ax.text(x_val, y_val, c, va='center', ha='center', fontsize=10, color='r')
                    i+=1
            
            
            xticks_labels = [str(x) for x in range(0,NOC_X)]
            yticks_labels = [str(x) for x in range(0,NOC_Y)]
            # put the major ticks at the middle of each cell
            ax.set_xticks(np.arange(NOC_X)+0.5, minor=False)
            ax.set_yticks(np.arange(NOC_Y)+0.5, minor=False)
            
            # want a more natural, table-like display
            ax.invert_yaxis()
            ax.xaxis.tick_top()
            
            ax.set_xticklabels(xticks_labels, minor=False)
            ax.set_yticklabels(yticks_labels, minor=False)
            
            # output plevel values to file
            if(dump_fname != None):
                logFile=open(dump_fname, 'a')                
                logFile.write("---------- time = %f \n" % subplot_title)
                pprint.pprint(all_snapshot_data_reshaped, logFile)
                logFile.write("----------\n\n")
                
            
            

    #plt.draw()
    #plt.tight_layout()
    
    
    
    
    

def plot_Network_QN_colormap():
    
    print "plot_Network_QN_colormap"
    
    # get data
    fname = "../test__psalgonodeprops.js"    
    json_data=open(fname)
    psalgonodeprops_data = json.load(json_data)
        
    # plot
    fig = plt.figure()
    fig.canvas.set_window_title('plot_Network_QN_colormap')
    
    num_snapshots = len(psalgonodeprops_data)
    
    subplots_x = int(math.ceil(math.sqrt(num_snapshots)))
    subplots_y = subplots_x
    
    for each_snapshot_ix in xrange(1,(subplots_x*subplots_y)):        
        if(each_snapshot_ix < num_snapshots):
            all_snapshot_data = [1 if each_node['ntype']==1 else 0 for each_node in psalgonodeprops_data[each_snapshot_ix-1]]
            all_snapshot_data_reshaped = np.reshape(all_snapshot_data, (NOC_X, NOC_Y))            
            #pprint.pprint(all_snapshot_data_reshaped)
            all_snapshot_data_max = max(all_snapshot_data)
            
            ax = plt.subplot(subplots_x,subplots_y,each_snapshot_ix, aspect='equal')            
            plt.pcolor(all_snapshot_data_reshaped, cmap=plt.gray(), vmin=0, vmax=all_snapshot_data_max)
            plt.title(psalgonodeprops_data[each_snapshot_ix-1][0]['t'])
            #plt.colorbar()
            #plt.grid(True)
            
            xticks_labels = [str(x) for x in range(0,NOC_X)]
            yticks_labels = [str(x) for x in range(0,NOC_Y)]
            # put the major ticks at the middle of each cell
            ax.set_xticks(np.arange(NOC_X)+0.5, minor=False)
            ax.set_yticks(np.arange(NOC_Y)+0.5, minor=False)
            
            # want a more natural, table-like display
            ax.invert_yaxis()
            ax.xaxis.tick_top()
            
            ax.set_xticklabels(xticks_labels, minor=False)
            ax.set_yticklabels(yticks_labels, minor=False)

    
def plot_Network_QNCount_colormap():
    
    print "plot_Network_QNCount_colormap"
    
    # get data
    fname = "../test__psalgonodeprops.js"    
    json_data=open(fname)
    psalgonodeprops_data = json.load(json_data)
        
    # plot
    fig = plt.figure()
    fig.canvas.set_window_title('plot_Network_QNCount_colormap')
    
    num_snapshots = len(psalgonodeprops_data)
    
    subplots_x = int(math.ceil(math.sqrt(num_snapshots)))
    subplots_y = subplots_x
    
    for each_snapshot_ix in xrange(1,(subplots_x*subplots_y)):        
        if(each_snapshot_ix < num_snapshots):
            all_snapshot_data = [each_node['qncount'] for each_node in psalgonodeprops_data[each_snapshot_ix-1]]
            all_snapshot_data_reshaped = np.reshape(all_snapshot_data, (NOC_X, NOC_Y))            
            #pprint.pprint(all_snapshot_data_reshaped)
            all_snapshot_data_max = max(all_snapshot_data)
            
            ax = plt.subplot(subplots_x,subplots_y,each_snapshot_ix, aspect='equal')            
            plt.pcolor(all_snapshot_data_reshaped, cmap=plt.gray(), vmin=0, vmax=all_snapshot_data_max)
            plt.title(psalgonodeprops_data[each_snapshot_ix-1][0]['t'])
            plt.colorbar()
            #plt.grid(True)
            
            xticks_labels = [str(x) for x in range(0,NOC_X)]
            yticks_labels = [str(x) for x in range(0,NOC_Y)]
            # put the major ticks at the middle of each cell
            ax.set_xticks(np.arange(NOC_X)+0.5, minor=False)
            ax.set_yticks(np.arange(NOC_Y)+0.5, minor=False)
            
            # want a more natural, table-like display
            ax.invert_yaxis()
            ax.xaxis.tick_top()
            
            ax.set_xticklabels(xticks_labels, minor=False)
            ax.set_yticklabels(yticks_labels, minor=False)
            
            
def plot_PSCommsFlows():
    
    print "plot_PSFlows"
    
    # get data
    fname = "../test__flwcompleted.js"    
    json_data=open(fname)
    psalgo_flwscompleted = json.load(json_data)    
    
    # filter out flows
    all_ps_flows = []
    for each_flw in psalgo_flwscompleted:
        if(each_flw['type'] == FlowType.FLOWTYPE_PSALGOSIGNALLING):
            all_ps_flows.append(each_flw)
    
    
    # plot
    fig = plt.figure()
    fig.canvas.set_window_title('plot_PSCommsFlows')
    # draw timeline    
    plt.axes()
           
    # plot flows per node (x-axis : time)
    for each_node_id in xrange(0,NOC_X*NOC_Y):
        node_specific_flows = [f for f in all_ps_flows if(f['src'] == each_node_id)]
        
        for each_flow in node_specific_flows:
            
            pprint.pprint(each_flow)
            
            src_node_id = each_flow['src']
            dst_node_id = each_flow['dst']
            start_time = float(each_flow['st']*10000000.0)            
            end_time = float(each_flow['et']*10000000.0)
            fid = each_flow['id']
            
            line_x0 = start_time
            line_x1 = end_time         
            line_y0 = src_node_id
            line_y1 = dst_node_id
            line_width = line_x1 -line_x0
            
            print line_width
            print line_x0
            print line_x1
            
            line = plt.Line2D((line_x0, line_x1), (line_y0, line_y1), lw=5, marker='x')    
            #sys.exit()            
            plt.gca().add_line(line)
            #annotation = str(fid) + " , ->" + str(dst_node_id)
            #plt.text((line_x0+(line_width/2)), line_y0+0.01, annotation, fontsize=8, zorder=12)
            
    plt.axis('auto')
    plt.minorticks_on()    
    plt.grid(True, which='both')        
            
        
    
def plot_reportMissingFlows():
    
    print "plot_reportMissingFlows"
    
    # get data
    fname = "../test__flwcompleted.js"    
    json_data=open(fname)
    psalgo_flwscompleted = json.load(json_data)    
    
    fname = "../test__flwsadded.js"    
    json_data=open(fname)
    psalgo_flwsadded = json.load(json_data)   
    
    # filter out flows
    all_ps_flows_added = {}   
    all_ps_flows_completed = {} 
    for each_flw in psalgo_flwsadded:
        if(each_flw['type'] == FlowType.FLOWTYPE_PSALGOSIGNALLING):
            all_ps_flows_added[each_flw['id']] = each_flw
        
    print len(all_ps_flows_added)
            
    for each_flw in psalgo_flwscompleted:
        if(each_flw['type'] == FlowType.FLOWTYPE_PSALGOSIGNALLING):
            all_ps_flows_completed[each_flw['id']] = each_flw
    
    print len(all_ps_flows_completed)
    
    # did the flow complete
    non_completed_flows = []
    for k,v in all_ps_flows_added.iteritems():
        if k not in all_ps_flows_completed:
            non_completed_flows.append(v)
        
    pprint.pprint(non_completed_flows)
    print len(non_completed_flows)
    
    
    
def plot_nodecumslack(fname):
    
    print "plot_nodecumslack"
    
    NUM_NODES =36
    # get data
    fname = fname    
    json_data=open(fname)
    psalgo_nodecumslack = json.load(json_data)    
  
    
    all_cumslack = []
    for each_node in psalgo_nodecumslack.iteritems():        
        #pprint.pprint(each_node[1])
        all_cumslack.append(each_node[1]["norm_cum_slack"])
    
    fig = plt.figure()
    fig.canvas.set_window_title('plot_nodecumslack - ' + fname)
    
     
    for each_node_ix in xrange(NUM_NODES):
        ax1 = plt.subplot(NUM_NODES,1,each_node_ix+1) 
        ax1.plot(all_cumslack[each_node_ix])
        ax1.set_title("CPU-"+str(each_node_ix))


def plot_qnstatus(fname, key='ntype'):
    
    print "plot_qnstatus"
    
    NUM_NODES =36
    # get data
    fname = fname    
    json_data=open(fname)
    psalgo_qnstatus = json.load(json_data)      
    
    node_level_attribute1 = [[] for x in xrange(NUM_NODES)]
    node_level_attribute2 = [[] for x in xrange(NUM_NODES)]
    node_level_attribute3 = [[] for x in xrange(NUM_NODES)]
    node_level_attribute4 = [[] for x in xrange(NUM_NODES)]
    
    all_cumslack = []
    for each_entry in psalgo_qnstatus:        
        for each_node in each_entry:
            print each_node['nid']
            node_level_attribute1[each_node['nid']].append(each_node[key])
            node_level_attribute2[each_node['nid']].append(each_node['plevel'])
            node_level_attribute3[each_node['nid']].append(each_node['qncount'])
            node_level_attribute4[each_node['nid']].append(each_node['ntype']*50)
    
    fig = plt.figure()
    fig.canvas.set_window_title('plot_qnstatus - ' + fname)
    
    for each_node_ix in xrange(NUM_NODES):
        ax1 = plt.subplot(NUM_NODES,1,each_node_ix+1) 
        ax1.plot(node_level_attribute1[each_node_ix])
        #ax1.plot(node_level_attribute2[each_node_ix], color='r')
        #ax1.plot(node_level_attribute3[each_node_ix], color='g')
        #ax1.plot(node_level_attribute4[each_node_ix], color='k')
        
        ax1.set_title("CPU-"+str(each_node_ix))        
   
  

#plot_Network_Plevel_colormap(dump_fname="plot_Network_Plevel_colormap.log", show_text=False)
#plot_Network_QN_colormap()
#plot_Network_QNCount_colormap()
#plot_PSCommsFlows()
#lot_reportMissingFlows()
#plot_nodecumslack("../experiment_data/remapping_psbased/temp/remapping_psbased__2236_061114/seed_99108/RMON_test__nodecumslack.js")
#plot_qnstatus("../experiment_data/remapping_psbased/temp/remapping_psbased__2236_061114/seed_99108/RMON_test__psalgonodeprops.js")

plot_nodecumslack("Z:/MCASim/experiment_data/remapping_psbased/seed_64217/RMON_test__nodecumslack.js")
plot_qnstatus("Z:/MCASim/experiment_data/remapping_psbased/seed_64217/RMON_test__psalgonodeprops.js", key='qncount')

plot_nodecumslack("Z:/MCASim/experiment_data/remapping_psbased/seed_77379/RMON_test__nodecumslack.js")
plot_qnstatus("Z:/MCASim/experiment_data/remapping_psbased/seed_77379/RMON_test__psalgonodeprops.js", key='qncount')

print "finished"
plt.show()
