import pprint
import sys
import itertools
import simpy
import math, random
from operator import itemgetter
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import animation
import time

from SimParams import SimParams
from libDebug.Debug import Debug, DebugCat





#############################################################################################
## PS Algo main class
#############################################################################################
    
class PSAlgorithmViewer:
    
    def __init__(self, env, RMInstance):
        self.label = "PSAlgorithmViewer"
        self.env = env
        self.RMInstance = RMInstance
        
        # figure instances
        self.fig_ax_pcolors = None
                      
        # process instance
        self.process_instance = None
                
    # initialise algorithm
    def init(self):        
        if(SimParams.PSALGO_VIEWER_ENABLED == True):
            plt.ion()
            
            empty_array = np.array(np.zeros((SimParams.NOC_H, SimParams.NOC_W)))
            
            ## pcolor plots
            # 0-plevel
            # 1-qn-pos
            # 2-qn-count
            # 3-slack amount
            
            mesh_arr = []
            cb_arr = []
            
            f, axarr = plt.subplots(4, 2)
            
            pc_mesh = axarr[0,0].pcolormesh(empty_array, cmap=plt.gray(), vmin=0, vmax=np.amax(empty_array), edgecolors='r')
            mesh_arr.append(pc_mesh)
            axarr[0,0].set_title('plevel')
            cb = f.colorbar(pc_mesh, ax=axarr[0,0])
            cb_arr.append(cb)           
            plt.axis('off')
            
            pc_mesh = axarr[0,1].pcolormesh(empty_array, cmap=plt.gray(), vmin=0, vmax=np.amax(empty_array), edgecolors='r')
            mesh_arr.append(pc_mesh)
            axarr[0,1].set_title('qn-pos')
            cb = f.colorbar(pc_mesh, ax=axarr[0,1])
            cb_arr.append(cb)
            plt.axis('off')
                        
            pc_mesh = axarr[1,0].pcolormesh(empty_array, cmap=plt.gray(), vmin=0, vmax=np.amax(empty_array), edgecolors='r')
            mesh_arr.append(pc_mesh)
            axarr[1,0].set_title('qn-count')
            cb = f.colorbar(pc_mesh, ax=axarr[1,0])
            cb_arr.append(cb)
            plt.axis('off')
            
            pc_mesh = axarr[1,1].pcolormesh(empty_array, cmap=plt.gray(), vmin=0, vmax=np.amax(empty_array), edgecolors='r')
            mesh_arr.append(pc_mesh)
            axarr[1,1].set_title('slack-amnt')
            cb = f.colorbar(pc_mesh, ax=axarr[1,1])            
            cb_arr.append(cb)
            plt.axis('off')
            
            pc_mesh = axarr[2,0].pcolormesh(empty_array, cmap=plt.gray(), vmin=0, vmax=np.amax(empty_array), edgecolors='r')
            mesh_arr.append(pc_mesh)
            axarr[2,0].set_title('nlatetasks(norm)')
            cb = f.colorbar(pc_mesh, ax=axarr[2,0])            
            cb_arr.append(cb)
            plt.axis('off')
            
            pc_mesh = axarr[2,1].pcolormesh(empty_array, cmap=plt.gray(), vmin=0, vmax=np.amax(empty_array), edgecolors='r')
            mesh_arr.append(pc_mesh)
            axarr[2,1].set_title('ntasks')
            cb = f.colorbar(pc_mesh, ax=axarr[2,1])            
            cb_arr.append(cb)
            plt.axis('off')
            
            pc_mesh = axarr[3,0].pcolormesh(empty_array, cmap=plt.gray(), vmin=0, vmax=np.amax(empty_array), edgecolors='r')
            mesh_arr.append(pc_mesh)
            axarr[3,0].set_title('thrhld-qn')
            cb = f.colorbar(pc_mesh, ax=axarr[3,0])            
            cb_arr.append(cb)
            plt.axis('off')
            
            pc_mesh = axarr[3,1].pcolormesh(empty_array, cmap=plt.gray(), vmin=0, vmax=np.amax(empty_array), edgecolors='r')
            mesh_arr.append(pc_mesh)
            axarr[3,1].set_title('imprtd-tasks')
            cb = f.colorbar(pc_mesh, ax=axarr[3,1])            
            cb_arr.append(cb)
            plt.axis('off')
            
            self.fig_ax_pcolors = {                                   
                                   'fig' : f,
                                   'axes': axarr,
                                   'pc_meshes' : mesh_arr,
                                   'col_bars' : cb_arr
                                   }
            
            
            # start process
            self.process_instance = self.env.process(self.updatelevels())
            
    
    def updatelevels(self):      
        
        while True:
            if(self.env.now > 0):            
                # update figure title with timestamp
                title = self._getPSAlgoTimestamps()
                if title != None:
                    self.fig_ax_pcolors['fig'].canvas.set_window_title(title)                
                
                new_data = self._getPcolorData()
#                print "----"
#                pprint.pprint(new_data)
#                print "----"
                
                # plevels
                if(np.amin(new_data['newdata_plevels']) == np.amax(new_data['newdata_plevels'])):
                    if(np.amin(new_data['newdata_plevels']) > np.amax(new_data['newdata_plevels'])):                        
                        val_min = np.amax(new_data['newdata_plevels'])
                        val_max = 0.0
                    else:
                        val_min = 0.0  
                        val_max = np.amax(new_data['newdata_plevels'])
                else:
                    val_min = np.amin(new_data['newdata_plevels'])  
                    val_max = np.amax(new_data['newdata_plevels'])
                self.fig_ax_pcolors['pc_meshes'][0].set_array(new_data['newdata_plevels'].ravel())
                self.fig_ax_pcolors['pc_meshes'][0].set_clim(vmin=val_min, vmax=val_max)
                self.fig_ax_pcolors['col_bars'][0].set_clim(vmin=val_min, vmax=val_max)
                plt.draw()
                self.fig_ax_pcolors['col_bars'][0].draw_all()
                
                # qnpos
                self.fig_ax_pcolors['pc_meshes'][1].set_array(new_data['newdata_qnpos'].ravel())
                self.fig_ax_pcolors['pc_meshes'][1].set_clim(vmin=1, vmax=2)            
                self.fig_ax_pcolors['col_bars'][1].set_clim(vmin=1, vmax=2)
                plt.draw()
                self.fig_ax_pcolors['col_bars'][1].draw_all()
                
                # qncount                
                if(np.amin(new_data['newdata_qncount']) == np.amax(new_data['newdata_qncount'])):
                    if(np.amin(new_data['newdata_qncount']) > np.amax(new_data['newdata_qncount'])):                        
                        val_min = np.amax(new_data['newdata_qncount'])
                        val_max = 0.0
                    else:
                        val_min = 0.0  
                        val_max = np.amax(new_data['newdata_qncount'])
                else:
                    val_min = np.amin(new_data['newdata_qncount'])  
                    val_max = np.amax(new_data['newdata_qncount'])
                self.fig_ax_pcolors['pc_meshes'][2].set_array(new_data['newdata_qncount'].ravel())
                self.fig_ax_pcolors['pc_meshes'][2].set_clim(vmin=val_min, vmax=val_max)            
                self.fig_ax_pcolors['col_bars'][2].set_clim(vmin=val_min, vmax=val_max)
                plt.draw()
                self.fig_ax_pcolors['col_bars'][2].draw_all()                
                
                # slack
                if(np.amin(new_data['newdata_slack']) == np.amax(new_data['newdata_slack'])):
                    if(np.amin(new_data['newdata_slack']) > np.amax(new_data['newdata_slack'])):       
                        val_min = np.amax(new_data['newdata_slack'])
                        val_max = 0.0
                    else:
                        
                        val_min = 0.0  
                        val_max = np.amax(new_data['newdata_slack'])
                else:
                    val_min = np.amin(new_data['newdata_slack'])  
                    val_max = np.amax(new_data['newdata_slack'])
                self.fig_ax_pcolors['pc_meshes'][3].set_array(new_data['newdata_slack'].ravel())
                self.fig_ax_pcolors['pc_meshes'][3].set_clim(vmin=val_min, vmax=val_max)        
                self.fig_ax_pcolors['col_bars'][3].set_clim(vmin=val_min, vmax=val_max)
                plt.draw()
                self.fig_ax_pcolors['col_bars'][3].draw_all()
                
                # numlatetasks
                if(np.amin(new_data['newdata_numlatetasks']) == np.amax(new_data['newdata_numlatetasks'])):
                    if(np.amin(new_data['newdata_numlatetasks']) > np.amax(new_data['newdata_numlatetasks'])):                        
                        val_min = np.amax(new_data['newdata_numlatetasks'])
                        val_max = 0.0
                    else:
                        val_min = 0.0  
                        val_max = np.amax(new_data['newdata_numlatetasks'])
                else:
                    val_min = np.amin(new_data['newdata_numlatetasks'])  
                    val_max = np.amax(new_data['newdata_numlatetasks'])
                self.fig_ax_pcolors['pc_meshes'][4].set_array(new_data['newdata_numlatetasks'].ravel())
                self.fig_ax_pcolors['pc_meshes'][4].set_clim(vmin=val_min, vmax=val_max)        
                self.fig_ax_pcolors['col_bars'][4].set_clim(vmin=val_min, vmax=val_max)
                plt.draw()
                self.fig_ax_pcolors['col_bars'][4].draw_all()
                
                # numtasks
                if(np.amin(new_data['newdata_tqsize']) == np.amax(new_data['newdata_tqsize'])):
                    if(np.amin(new_data['newdata_tqsize']) > np.amax(new_data['newdata_tqsize'])):                        
                        val_min = np.amax(new_data['newdata_tqsize'])
                        val_max = 0.0
                    else:
                        val_min = 0.0  
                        val_max = np.amax(new_data['newdata_tqsize'])
                else:
                    val_min = np.amin(new_data['newdata_tqsize'])  
                    val_max = np.amax(new_data['newdata_tqsize'])
                self.fig_ax_pcolors['pc_meshes'][5].set_array(new_data['newdata_tqsize'].ravel())
                self.fig_ax_pcolors['pc_meshes'][5].set_clim(vmin=val_min, vmax=val_max)        
                self.fig_ax_pcolors['col_bars'][5].set_clim(vmin=val_min, vmax=val_max)
                plt.draw()
                self.fig_ax_pcolors['col_bars'][5].draw_all()
                
                # thresholdqn
#                if(np.amin(new_data['newdata_thresholdqn']) == np.amax(new_data['newdata_thresholdqn'])):
#                    if(np.amin(new_data['newdata_thresholdqn']) > np.amax(new_data['newdata_thresholdqn'])):                        
#                        val_min = np.amax(new_data['newdata_thresholdqn'])
#                        val_max = 0.0
#                    else:
#                        val_min = 0.0  
#                        val_max = np.amax(new_data['newdata_thresholdqn'])
#                else:
                val_min = np.amin(new_data['newdata_thresholdqn'])  
                val_max = np.amax(new_data['newdata_thresholdqn'])
                    
                print val_min
                print val_max
                    
                self.fig_ax_pcolors['pc_meshes'][6].set_array(new_data['newdata_thresholdqn'].ravel())
                self.fig_ax_pcolors['pc_meshes'][6].set_clim(vmin=val_min, vmax=val_max)        
                self.fig_ax_pcolors['col_bars'][6].set_clim(vmin=val_min, vmax=val_max)
                plt.draw()
                self.fig_ax_pcolors['col_bars'][6].draw_all()
                
                # imported tasks
                if(np.amin(new_data['newdata_numimportedtasks']) == np.amax(new_data['newdata_numimportedtasks'])):
                    if(np.amin(new_data['newdata_numimportedtasks']) > np.amax(new_data['newdata_numimportedtasks'])):                        
                        val_min = np.amax(new_data['newdata_numimportedtasks'])
                        val_max = 0.0
                    else:
                        val_min = 0.0  
                        val_max = np.amax(new_data['newdata_numimportedtasks'])
                else:
                    val_min = np.amin(new_data['newdata_numimportedtasks'])  
                    val_max = np.amax(new_data['newdata_numimportedtasks'])
                self.fig_ax_pcolors['pc_meshes'][7].set_array(new_data['newdata_numimportedtasks'].ravel())
                self.fig_ax_pcolors['pc_meshes'][7].set_clim(vmin=val_min, vmax=val_max)        
                self.fig_ax_pcolors['col_bars'][7].set_clim(vmin=val_min, vmax=val_max)
                plt.draw()
                self.fig_ax_pcolors['col_bars'][7].draw_all()
                
#                self.fig_ax_pcolors['axes'][0,0].draw_artist(self.fig_ax_pcolors['pc_meshes'][0])
#                self.fig_ax_pcolors['axes'][0,1].draw_artist(self.fig_ax_pcolors['pc_meshes'][1])
#                self.fig_ax_pcolors['axes'][1,0].draw_artist(self.fig_ax_pcolors['pc_meshes'][2])
#                self.fig_ax_pcolors['axes'][1,1].draw_artist(self.fig_ax_pcolors['pc_meshes'][3])
                
                if(SimParams.PSALGO_VIEWER_BLOCKONUSERINPUT == True):
                    foo = raw_input("- press any key to continue -\n")
                    plt.pause(0.01)
                    time.sleep(0.01)
                else:
                    plt.pause(0.01)
                    time.sleep(0.01)
                
                
                plt.show()                
            
            #print "here 00000000000000"
            
            # wait for TQN seconds
            yield self.env.timeout(SimParams.PSALGO_VIEWER_SAMPLERATE)      
            
            
    def _getPcolorData(self):         
        
        all_node_plevels= []
        all_node_qnpos = []
        all_node_qncount = []
        all_node_slack = []
        all_node_numlatetasks = []
        all_node_tqsize = []
        all_node_thresholdqn = []
        all_node_numimportedtasks = []
        all_node_norm_numlatetasks = []
        for each_node in self.RMInstance.node_network.get_Nodes():
               
            # plevels
            all_node_plevels.append(each_node.psalgoprops.get_pheramone_level()) 
            
            # qn pos
            all_node_qnpos.append(each_node.psalgoprops.get_node_type()) 
            
            # qncount
            all_node_qncount.append(each_node.psalgoprops.get_qn_count()) 
            
            # slack amount
            all_node_slack.append(each_node.calculate_SystemSlack(normalised=True)) 
            
            # number of late tasks
            num_late_tasks = each_node.numLateTasksInTQ(lateness_ratio=SimParams.DYNAMIC_TASK_REMAPPING_TASK_LATE_ESTIM_LATENESS_RATIO)
            all_node_numlatetasks.append(num_late_tasks)
                             
            # number of tasks in tq
            all_node_tqsize.append(each_node.get_NumTasksInTQ()) 
            
            # thresholdqn
            all_node_thresholdqn.append(each_node.psalgoprops.get_threshold_qn()) 
            
            # imported tasks - due to remapping
            all_node_numimportedtasks.append(each_node.totalImportedTasks()) 
            
            # normalised_num_late_tasks
            if each_node.get_NumTasksInTQ() >0:
                all_node_norm_numlatetasks.append(float(float(num_late_tasks)/float(each_node.get_NumTasksInTQ())))
            else:
                all_node_norm_numlatetasks.append(float(0.0))
                            
        all_node_plevels_reshaped = np.array(np.reshape(all_node_plevels, (SimParams.NOC_H, SimParams.NOC_W)))
        all_node_qnpos_reshaped = np.array(np.reshape(all_node_qnpos, (SimParams.NOC_H, SimParams.NOC_W)))
        all_node_qncount_reshaped = np.array(np.reshape(all_node_qncount, (SimParams.NOC_H, SimParams.NOC_W)))
        all_node_slack_reshaped = np.array(np.reshape(all_node_slack, (SimParams.NOC_H, SimParams.NOC_W)))
        all_node_numlatetasks_reshaped = np.array(np.reshape(all_node_numlatetasks, (SimParams.NOC_H, SimParams.NOC_W)))
        all_node_tqsize_reshaped = np.array(np.reshape(all_node_tqsize, (SimParams.NOC_H, SimParams.NOC_W)))
        all_node_thresholdqn_reshaped = np.array(np.reshape(all_node_thresholdqn, (SimParams.NOC_H, SimParams.NOC_W)))
        all_node_numimportedtasks_reshaped = np.array(np.reshape(all_node_numimportedtasks, (SimParams.NOC_H, SimParams.NOC_W)))
        all_node_norm_numlatetasks_reshaped = np.array(np.reshape(all_node_norm_numlatetasks, (SimParams.NOC_H, SimParams.NOC_W)), dtype=float)
     
        result = {
                  'newdata_plevels' : all_node_plevels_reshaped,
                  'newdata_qnpos' : all_node_qnpos_reshaped,
                  'newdata_qncount' : all_node_qncount_reshaped,
                  'newdata_slack' : all_node_slack_reshaped,
                  'newdata_numlatetasks' : all_node_norm_numlatetasks_reshaped,
                  'newdata_tqsize' : all_node_tqsize_reshaped,
                  'newdata_thresholdqn' : all_node_thresholdqn_reshaped,
                  'newdata_numimportedtasks' : all_node_numimportedtasks_reshaped,                  
                  }
        
        return result
            
    def _getPSAlgoTimestamps(self):
        # get number of prop cycles executed
        num_propcycles = len(self.RMInstance.PSAlgo.track_propcycles)
        last_propcycle = self.RMInstance.PSAlgo.track_propcycles[-1] if len(self.RMInstance.PSAlgo.track_propcycles)>0 else None
        
        # get number of decay cycles executed
        num_decaycycles = len(self.RMInstance.PSAlgo.track_decaycycles)
        last_decaycycle = self.RMInstance.PSAlgo.track_decaycycles[-1] if len(self.RMInstance.PSAlgo.track_decaycycles)>0 else None
        
        title = "Time: " + str(self.env.now) + ", prop: " + str(num_propcycles) + "[" + str(last_propcycle) + "]" + \
                ", dec: " + str(num_decaycycles) + "[" + str(last_decaycycle) + "]"
        
        return title
    
    