import pprint, sys

import math
import numpy as np
import matplotlib.pyplot as plt
#plt.style.use('bmh_rosh')
from mpl_toolkits.mplot3d import Axes3D
import scipy.stats
from matplotlib.colors import ListedColormap, NoNorm
from matplotlib import mlab
from itertools import cycle # for automatic markers
import matplotlib.patches as patches


from matplotlib.font_manager import FontProperties
from matplotlib.ticker import FuncFormatter
import matplotlib

import matplotlib as mpl
import matplotlib.cm as cm

## local imports
import Task
import libBuffer.Buffer
from SimParams import SimParams
from TaskSet import TaskSet



class Workflow:
    def __init__(self, env, stream_id, stream_resolution, stream_fr, stream_gop_struct):
        
        self.env = env
        # one-to-one mapping between workflows and inputbuffers
        self.stream_content = None
        self.stream_content_backup = None
        
        self.stream_id = stream_id
        self.stream_resolution = stream_resolution   # tuple
        self.stream_fr = stream_fr   # framerate
        self.stream_gop_struct = stream_gop_struct        
    
    def populateWorkflow(self):
        # e.g. 1 hr movie, 25fps, 12 gop len = running_time * fps / average_GOP_size
        taskset = TaskSet(self.env)
        
        task_start_id = self.stream_id * (SimParams.NUM_GOPS * SimParams.GOP_LENGTH)
        gop_start_id = (SimParams.NUM_GOPS * self.stream_id)
        
        taskset.generateMPEG2FrameTaskSet(SimParams.NUM_GOPS, task_start_id , gop_start_id,
                                          frame_w=self.stream_resolution[0],
                                          frame_h=self.stream_resolution[1])
        
        # set the worst-case exuction time for all tasks in the task_pool
        taskset.set_worstCaseComputationTime_alltasks()
        
        self.stream_content = list(taskset.taskList)
        self.stream_content_backup = list(taskset.taskList)
        
        return len(self.stream_content)
        
        
    def removeTask(self, task, ix):        
        del self.stream_content[ix]
    def isEmpty(self):
        if(len(self.stream_content)> 0): return False
        else: return True    
    
    def tasksNotDispatched(self, empty_status):
        if(empty_status == True): 
            return 0
        else:
            count = 0
            for each_task in  self.stream_content:
                if(each_task.get_dispatchTime() == None) and (self.env.now <= each_task.get_scheduledDispatchTime()) :
                    count += 1
                    break                
            return count
        
    # calculate the total tiles in each VS, each Frame
    def getTotalTiles(self):
        num_tiles = 0
        if SimParams.HEVC_TILELEVEL_SPLITTING_ENABLE == True:            
            for each_task in self.stream_content:
                num_tiles += each_task.getNumSubTasksTiles()            
            return num_tiles
        else:
            return num_tiles
                
                
    
        
    ## getters ##
    def get_Task(self):
        return self.stream_content.pop(0)    # return first item
    def get_stream_content(self):
        return self.stream_content
    
    ## setters ##
    def set_stream_content(self, sc):
        self.stream_content = sc
        self.stream_content_backup = sc
    
    
    
                   
                   
    #############################
    # Standalone functions
    #############################                   
    @staticmethod
    def dumpWorkflowsToFile(all_workflows, fname="workflows.xml"):       
        file = open(fname, "w")        
        file.write("<Workflows>")        
        for each_workflow in all_workflows:        
            file.write("<TaskSet>")            
            for each_task in each_workflow.stream_content :
                file.write( each_task._debugLongXML() )
                file.write("\n")        
            file.write("</TaskSet>")        
        file.write("</Workflows>")            
        file.close()
    
    @staticmethod    
    def plot_TaskComputationCostHistogram(list_workflows, fig_id, ftype="all", wf_ids = range(SimParams.NUM_WORKFLOWS)):
        print "plot_TaskComputationCostHistogram:: Enter"
        nrows = int(math.ceil(len(wf_ids) / 2.))
        print nrows
        if(nrows<2): nrows=2        
        fig = plt.figure(fig_id+100)
        
        for ix,each_wf_id in enumerate(wf_ids):
            
            print ix
            
            hist_data = []
            for each_task in list_workflows[each_wf_id].stream_content_backup:
                if(ftype == "all"):
                    hist_data.append(each_task.get_computationCost())
                else:
                    if each_task.get_frameType() == ftype:
                        hist_data.append(each_task.get_computationCost())
            
            print len(hist_data)
            
            print "unique values : ", len(set(hist_data))
            print "max_val : ", np.max(hist_data)
            print "min_val : ", np.min(hist_data)
                        
            plt.subplot(nrows, 2, ix+1)
            fig.canvas.set_window_title('TaskComputationCostHistogram - ' + ftype)
            count, bins, ignored = plt.hist(hist_data, alpha=0.5, color='g', bins=int(len(list_workflows[each_wf_id].stream_content_backup)/1), normed=1)
            plt.plot(bins, np.ones_like(bins), linewidth=2, color='r')
            plt.grid(True)
            print "finished generating plot"
    
    
    @staticmethod    
    # step plot with all types of frames overlapping histograms
    # assumes single wf ==> single vid
    def plot_TaskComputationCostHistogram_step(list_workflows, fig_id, wf_ids = range(SimParams.NUM_WORKFLOWS)):
        
        def to_percent(y, position):
            # Ignore the passed in position. This has the effect of scaling the default
            # tick locations.
            s = str(100 * y)        
            # The percent symbol needs escaping in latex
            if matplotlib.rcParams['text.usetex'] is True:
                return s + r'$\%$'
            else:
                return s + '%'
    
        
        temp_cols = ['#FF8585', '#85FF85', '#8585FF']
        temp_cols = ['r','g','b']
        
        print "plot_TaskComputationCostHistogram:: Enter"
        f, axarr = plt.subplots(len(wf_ids))        
        f.canvas.set_window_title('TaskComputationCostHistogram')
        
        for ix,each_wf_id in enumerate(wf_ids):            
            print ix
            vid_res = "%dx%d" % (list_workflows[each_wf_id].stream_content_backup[0].get_frame_w(),
                            list_workflows[each_wf_id].stream_content_backup[0].get_frame_h()
                            )
            
            I_frame_compcost_dist = []
            P_frame_compcost_dist = []
            B_frame_compcost_dist = []
            
            for each_task in list_workflows[each_wf_id].stream_content_backup:
                ftype = each_task.get_frameType()
                if (ftype == "I") : I_frame_compcost_dist.append(each_task.get_computationCost())
                elif (ftype == "P") : P_frame_compcost_dist.append(each_task.get_computationCost())
                elif (ftype == "B") : B_frame_compcost_dist.append(each_task.get_computationCost())
                else: sys.exit("undefined frame type")
                
            print "I_frame_compcost_dist",len(I_frame_compcost_dist), np.max(I_frame_compcost_dist), np.min(I_frame_compcost_dist)
            print "P_frame_compcost_dist",len(P_frame_compcost_dist), np.max(P_frame_compcost_dist), np.min(P_frame_compcost_dist)
            print "B_frame_compcost_dist",len(B_frame_compcost_dist), np.max(B_frame_compcost_dist), np.min(B_frame_compcost_dist)
            
            all_ftypes_data = [I_frame_compcost_dist, P_frame_compcost_dist, B_frame_compcost_dist]
            
            
#             weights = [np.ones_like(I_frame_compcost_dist)/float(len(I_frame_compcost_dist)),
#                        np.ones_like(P_frame_compcost_dist)/float(len(P_frame_compcost_dist)),
#                        np.ones_like(B_frame_compcost_dist)/float(len(B_frame_compcost_dist))]
            
            weights = [np.zeros_like(I_frame_compcost_dist) + 1. / float(len(I_frame_compcost_dist)),
                       np.zeros_like(P_frame_compcost_dist) + 1. / float(len(P_frame_compcost_dist)),
                       np.zeros_like(B_frame_compcost_dist) + 1. / float(len(B_frame_compcost_dist))]
            
            
            
            count, bins, ignored = axarr[ix].hist(all_ftypes_data, 
                                                #alpha=1.0, 
                                                #color=['r','g','b'],
                                                color=temp_cols, 
                                                linewidth=2.0, 
                                                histtype='step', fill=False, 
                                                bins=100, weights=weights)
            
            #axarr[ix].set_title(vid_res)
            
#             axarr[ix].text(.5,.9,'res: %s' %(vid_res),
#                             horizontalalignment='center',
#                             transform=axarr[ix].transAxes,
#                             fontsize=12)
#             
            
            
            formatter = FuncFormatter(to_percent)
            axarr[ix].yaxis.set_major_formatter(formatter)
            
            axarr[ix].grid(True)
            
            #axarr[ix].set_ylabel("Normalised frequency (%)")
            
            
            rect_lbl_list = ["I-frame", "P-frame", "B-frame"]        
            rec_r = patches.Rectangle( (0.72, 0.1), 0.2, 0.6, facecolor=temp_cols[0] )
            rec_g = patches.Rectangle( (0.72, 0.1), 0.2, 0.6, facecolor=temp_cols[1] )
            rec_b = patches.Rectangle( (0.72, 0.1), 0.2, 0.6, facecolor=temp_cols[2] )
                              
            rects_list = [rec_r, rec_g, rec_b]
            
            leg = axarr[ix].legend(rects_list, 
                            rect_lbl_list, 
                            ncol=1, 
                            prop={'size':12}, 
                            loc='right center', 
                            bbox_to_anchor=(0.5, 1.05),
                            title='res: %s' %(vid_res)
                            )
            leg.draggable()
            axarr[ix].get_legend().get_title().set_fontsize('12')
            
            
            print "finished generating plot"
        
        axarr[-1].set_xlabel("Frame decoding time (s)")
        #f.text(0.04, 0.5, "Normalised frequency (%)", va='center', rotation='vertical', fontsize=12, color='#5d5d5d') # for ggplot
        f.text(0.01, 0.5, "Normalised frequency (%)", va='center', rotation='vertical', fontsize=14)
    
    @staticmethod    
    def plot_TaskComputationCost(list_workflows, fig_id, ftype="all", wf_ids = range(SimParams.NUM_WORKFLOWS)):
        
        
        nrows = int(math.ceil(len(wf_ids) / 2.))
        print nrows
        if(nrows<2): nrows=2
        #fig, axs = plt.subplots(nrows, 2)
        fig = plt.figure(fig_id+100)
        
        # color based on video stream id
        #norm = mpl.colors.Normalize(vmin=0, vmax=SimParams.WFGEN_MAX_VIDS_PER_WF)
        cmap = mpl.cm.get_cmap('gist_rainbow')
        
        for ix,each_wf_id in enumerate(wf_ids):
            
            compcost = []
            task_ids = []
            stream_specific_cols = []
            
            for each_task in list_workflows[each_wf_id].stream_content_backup:
                if(ftype == "all"):
                    compcost.append(each_task.get_computationCost())
                    task_ids.append(each_task.get_id())
                    stream_specific_cols.append(cmap(1.*each_task.get_parentGopId()/SimParams.WFGEN_MAX_GOPS_PER_VID))
                else:
                    if each_task.get_frameType() == ftype:
                        compcost.append(each_task.get_computationCost())                
                        task_ids.append(each_task.get_id())                     
                        stream_specific_cols.append(cmap(1.*each_task.get_parentGopId()/SimParams.WFGEN_MAX_GOPS_PER_VID)) 
                                
            
            #hist_data = [t.get_computationCost() for t in list_workflows[each_wf_id].stream_content_backup]        
            
            plt.subplot(nrows, 2, ix+1)
            fig.canvas.set_window_title('plot_TaskComputationCost - ' + ftype)            
            plt.scatter(task_ids, compcost, marker='x', color=stream_specific_cols)
            plt.axhline(y=max(compcost),color='k',ls='dashed')
            plt.axhline(y=min(compcost),color='k',ls='dashed')
            plt.grid(True)
        
    
    @staticmethod
    def plot_show():
        plt.show()
       
    