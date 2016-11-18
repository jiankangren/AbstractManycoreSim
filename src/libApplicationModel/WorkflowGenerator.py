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

import pickle

## local imports
import Task
import libBuffer.Buffer
from SimParams import SimParams
from TaskSet import TaskSet
from Task import TaskModel

class WorkflowGenerator():
    
    def __init__(self, env, max_wf, 
                 min_videos_per_wf, max_videos_per_wf,
                  min_gops_per_video, max_gops_per_video, 
                  min_inter_video_gap, max_inter_video_gap, 
                  min_interarrival, max_interarrival):
         
        self.env = env
        self.max_wf = max_wf  
        self.min_videos = min_videos_per_wf    
        self.max_videos = max_videos_per_wf
        self.min_gops_per_video = min_gops_per_video
        self.max_gops_per_video = max_gops_per_video
        self.max_inter_video_gap = max_inter_video_gap
        self.min_inter_video_gap = min_inter_video_gap
        self.min_interarrival = min_interarrival
        self.max_interarrival = max_interarrival        
        self.workflows = {}
      
        # for later use
        self.max_task_priority = None
        self.used_pri_values = []
                
        self.workflows_summary = {}
        
        
    
        
    
    ##################
    # getters/setters
    ##################
    def get_max_task_priority(self):
        return self.max_task_priority
    def get_used_pri_values(self):
        return self.used_pri_values
    
    
        
    def generate_workflows(self):
                
        task_start_id = 0        
        unique_job_start_id = 0        
        
        priority_offset = 0
        
        #print "random.randint(2,100000) : " + str(random.randint(2,100000))
        #print "np.random.randint(2,100000) : " + str(np.random.randint(2,100000))
        
        for each_wf_id in xrange(self.max_wf):
            num_vids = random.randint(self.min_videos, self.max_videos)     # determine number of videos for this workflow       
            
            #initial_gap = random.uniform(SimParams.TASKDISPATCHER_RESET_DELAY, self.max_inter_video_gap*1.5) # initially we want a gap, we don't want all streams to start at once
            
            #initial_gap = 0.00001
            
            if(SimParams.WFGEN_INITIAL_VID_EQUAL_FOR_ALL_VIDS == True): # all wfs have the same initial start rules
                initial_gap = 0.00001 + random.uniform(SimParams.WFGEN_INITIAL_VID_GAP_MIN, SimParams.WFGEN_INITIAL_VID_GAP_MAX)
            else:
                if(each_wf_id == 0):    # wfs have a sequential start offset
                    initial_gap = 0.00001 + random.uniform(SimParams.WFGEN_INITIAL_VID_GAP_MIN, SimParams.WFGEN_INITIAL_VID_GAP_MAX)
                else:
                    # offset = pre wf initial start time
                    offset = self.workflows_summary[each_wf_id-1][0]['starttime']
                    initial_gap = offset + random.uniform(SimParams.WFGEN_INITIAL_VID_GAP_MIN, SimParams.WFGEN_INITIAL_VID_GAP_MAX)
                    
            jobs_start_time = initial_gap   
            
            self.workflows[each_wf_id] = []            
            self.workflows_summary[each_wf_id] = {}
            for each_vid in xrange(num_vids):
                
                # determine video stream resolution
                if(SimParams.DVB_RESOLUTIONS_SELECTED_RANDOM == True):
                    #pprint.pprint(SimParams.DVB_RESOLUTIONS)                    
                    ridx = np.random.choice(range(len(SimParams.DVB_RESOLUTIONS)))
                    resolution = SimParams.DVB_RESOLUTIONS[ridx]
                                                  
                else:                    
                    if(self.max_wf <= len(SimParams.DVB_RESOLUTIONS_FIXED)): # only when there is one vid per wf
                        resolution = SimParams.DVB_RESOLUTIONS_FIXED[each_wf_id]
                    else:
                        print self.max_wf
                        print len(SimParams.DVB_RESOLUTIONS_FIXED)
                        sys.exit('Error: generate_workflows: Error - not enough elements in SimParams.DVB_RESOLUTIONS_FIXED')
                
                
                # determine frame rate for the video
                if SimParams.USE_VIDSTRM_SPECIFIC_FRAMERATE == True:
                    res_total_pixels = resolution[0]*resolution[1]
                    if res_total_pixels in SimParams.RESOLUTION_SPECIFIC_FRAME_RATE:
                        frame_rate = np.random.choice(SimParams.RESOLUTION_SPECIFIC_FRAME_RATE[res_total_pixels])
                    else:
                        sys.exit("Error - resolution not in SimParams.RESOLUTION_SPECIFIC_FRAME_RATE:" + pprint.pformat(resolution))
                
                else:
                    frame_rate = SimParams.FRAME_RATE
                
                
                # generate jobs/gops for the video stream                                
                job_start_id = 0    
                (jobs_list, job_endtime, num_jobs, avg_dt, min_dt) = self._generate_jobs(job_start_id, unique_job_start_id,
                                    task_start_id,
                                    self.min_gops_per_video,                                
                                    self.max_gops_per_video,
                                    each_vid, each_wf_id,
                                    SimParams.GOP_STRUCTURE,
                                    jobs_start_time,
                                    resolution[1],
                                    resolution[0],
                                    frame_rate                                                                    
                                    )
                
                print str(resolution[1]) +  "x" + str(resolution[0])
                
                temp_frames = {}
                temp_gops = []
                for each_task in jobs_list:
                    if(each_task.get_unique_gop_id() not in temp_frames):
                        temp_frames[each_task.get_unique_gop_id()] = [each_task.get_id()]
                        temp_gops.append(each_task.get_unique_gop_id())
                    else:
                        temp_frames[each_task.get_unique_gop_id()].append(each_task.get_id())
                
                self.workflows_summary[each_wf_id][each_vid] = {}
                self.workflows_summary[each_wf_id][each_vid]={
                                                              'starttime' : jobs_start_time,                                                              
                                                              'endtime' : job_endtime,
                                                              'framerate' : jobs_list[0].get_framerate(),
                                                              'avg_dispatch_rate' : avg_dt,
                                                              'min_dispatch_rate' : min_dt,
                                                              'gop_len' : len(jobs_list[0].get_gopstructure()),
                                                              'numgops' : num_jobs,
                                                              'resolution' : resolution,
                                                              'frames' : temp_frames,
                                                              'gops' :  temp_gops                                                           
                                                              }                
                # reset times and ids
                gap = random.uniform(self.min_inter_video_gap, self.max_inter_video_gap)
                jobs_start_time =  job_endtime + gap
                
                #job_start_id += 1
                unique_job_start_id = jobs_list[len(jobs_list)-1].get_unique_gop_id() + 1                
                task_start_id += len(jobs_list)                           
                
                self.workflows[each_wf_id].extend(jobs_list)
                
                # save workflow summary
                if(SimParams.TRACK_WFSUMMARY_PPRINT == True):
                    workflow_logfile=open('workflow_summary.js', 'w')
                    pprint.pprint(self.workflows_summary, workflow_logfile, width=128)
                
            print '%f'%self.env.now + "," + "WorkflowGenerator::, finished generating wf_id = " + str(each_wf_id)
    
    
    def getLastScheduledTask(self):
        tmptasks = []
        for each_wf_key, each_wf_val in self.workflows.iteritems():
            tmptasks.append(each_wf_val[len(each_wf_val)-1])
            
        sorted_tmptasks = sorted(tmptasks, key=lambda x: x.get_scheduledDispatchTime(), reverse=True)        
        return sorted_tmptasks[0]
    
    def getLastScheduledVideoStream(self):
        vs_admission_times = {}
    
        for each_wf_key, each_wf_val in self.workflows_summary.iteritems():
            for each_vid_k, each_vid_v in each_wf_val.iteritems():
                vid_start_time = each_vid_v['starttime']
                temp_k = str(each_wf_key) + "_" + str(each_vid_k)
                vs_admission_times[temp_k] = vid_start_time
                
        # find max starttime
        max_st = max(vs_admission_times.values())
        max_st_k = [vs_k for vs_k, vs_v in vs_admission_times.iteritems() if vs_v == max_st][0]
        
        wf_id = int(max_st_k.split("_")[0])
        vs_id = int(max_st_k.split("_")[1])
        
        return (wf_id, vs_id)
                
    
    def getFirstScheduledTask(self):
        tmptasks = []
        for each_wf_key, each_wf_val in self.workflows.iteritems():
            tmptasks.append(each_wf_val[0])
            
        sorted_tmptasks = sorted(tmptasks, key=lambda x: x.get_scheduledDispatchTime(), reverse=False)        
        return sorted_tmptasks[0]
    
    
    def setTaskPriorities_AllUnique(self):
        # how many tasks have been created in total ?
        task_count = 0
        for each_wf in self.workflows.itervalues():
            task_count += len(each_wf)
            
        # generate unique random numbers, enough for every task generated
        random_unique_pri_list = random.sample(range(1,task_count+1), task_count)
        
        # apply unique priorities for each task in the workflow
        i=0
        for each_wf in self.workflows.itervalues():
            for each_task in each_wf:
                each_task.set_priority(random_unique_pri_list[i])
                i+=1 
                
        # whats the max priority set ?
        self.max_task_priority = max(random_unique_pri_list)       
        
        
    def setTaskPriorities_GroupedByJobs(self):
        i=1
    
    def setTaskPriorities_GroupedByVids(self):
        i=1
           
    # generate all the gops for a video stream        
    def _generate_jobs(self, job_start_id, unique_job_start_id,  
                       task_start_id, min_jobs, max_jobs, video_stream_id, wf_id,
                       gop_struct, jobs_dispatchtime_start, frame_h, frame_w, fps):
                
        num_gops =  random.randint(min_jobs, max_jobs)
        
        # therefore the end-time ?
        job_end_time = jobs_dispatchtime_start + ((float(num_gops) * float(len(gop_struct))) / (float(fps) * 60.0))
                
        taskset = TaskSet(self.env) 
        
        # generate new priorities, excluding the ones already in the pool
        pri_range = self._genRandomNumList(SimParams.GOP_LENGTH,self.used_pri_values)        
        
        # generate multiple gops
        if SimParams.TASKSET_MODEL == TaskModel.TASK_MODEL_MHEG2_FRAME_ET_LEVEL_INTERRELATEDGOPS:
            final_dispatch_time, avg_dt, min_dt = taskset.generateMPEG2FrameInterRelatedGOPTaskSet(num_gops, task_start_id , job_start_id, unique_job_start_id,
                                              taskset_dispatch_start_time = jobs_dispatchtime_start,
                                              video_stream_id = video_stream_id,
                                              wf_id = wf_id,
                                              frame_w=frame_w,
                                              frame_h=frame_h,
                                              frame_rate=fps,
                                              priority_range = pri_range)
            
        elif(SimParams.TASKSET_MODEL == TaskModel.TASK_MODEL_MHEG2_FRAME_ET_LEVEL):
            final_dispatch_time, avg_dt, min_dt = taskset.generateMPEG2FrameTaskSet(num_gops, task_start_id , job_start_id, unique_job_start_id,
                                              taskset_dispatch_start_time = jobs_dispatchtime_start,
                                              video_stream_id = video_stream_id,
                                              wf_id = wf_id,
                                              frame_w=frame_w,
                                              frame_h=frame_h,
                                              frame_rate=fps,
                                              priority_range = pri_range)
        
        
        # adaptive gop, slices/tiles, task splitting, pulevel cc    
        elif(SimParams.TASKSET_MODEL in [TaskModel.TASK_MODEL_HEVC_FRAME_LEVEL, TaskModel.TASK_MODEL_HEVC_TILE_LEVEL] ):  
            pri_range = np.random.randint(10000,size=50)
            final_dispatch_time, avg_dt, min_dt = taskset.generateHEVCFrameTaskSet(num_gops, task_start_id , job_start_id, unique_job_start_id,
                                              taskset_dispatch_start_time = jobs_dispatchtime_start,
                                              video_stream_id = video_stream_id,
                                              wf_id = wf_id,
                                              frame_w=frame_w,
                                              frame_h=frame_h,
                                              frame_rate = fps,
                                              priority_range = pri_range, 
                                              )
        
        # set the worst-case exuction time for all tasks in the task_pool
        taskset.set_worstCaseComputationTime_alltasks()
        
#        if(final_dispatch_time > job_end_time):
#            job_end_time = final_dispatch_time      
        
        job_end_time = final_dispatch_time  
        
        return  (taskset.taskList, job_end_time, num_gops, avg_dt, min_dt)
        
    
    def _remove_dups(self,seq):
        seen = set()
        seen_add = seen.add
        return [ x for x in seq if x not in seen and not seen_add(x)]
        
    
    def dumpWorkflowsToFile(self, fname="workflows.xml"):
       
        file = open(fname, "w")
        
        file.write("<Workflows>")
        
        for each_wf_key, each_wf_values in self.workflows.iteritems():   
            file.write("<workflow id='%d'>" % each_wf_key)
            for each_task in each_wf_values :
                #pprint.pprint(each_task)
                file.write( each_task._debugLongXML() )
                file.write("\n")
            
            file.write("</workflow>")           
        
        file.write("</Workflows>")            
        file.close()
        
    def showTaskTimeLine(self, num_wfs, simon_wf_results_summary = None, fname = 'showTaskTimeLine.png', show_vid_blocks = False):
        
        print "showTaskTimeLine: Enter"
        num_workflows = len(self.workflows.items())
        print "num_workflows=" + str(num_workflows)
        
        fig = plt.figure(dpi=100, figsize=(20.0, float(num_workflows)*1.5))
        #fig = plt.figure()        
        
        annot_text = {
                          "wf_vid_id": [],
                          "x": [],
                          "y" : [],
                          "text" : [],
                          "colour" : []
                          }
        for each_wf_key, each_wf_values in self.workflows.iteritems():                           
            #ax = plt.subplot(1,num_workflows,each_wf_key)
            
            dispatch_times = []
            vid_count = 0
            
            video_start_end_pos = {}
            
            for each_task in each_wf_values :                
                sdt = each_task.get_scheduledDispatchTime()
                dispatch_times.append(round(sdt,2))
                
                
                if(show_vid_blocks == True):                    
                    if(each_task.get_isHeadVideoGop() == True):
                        if vid_count not in video_start_end_pos:
                            video_start_end_pos[vid_count] = {
                                                              'start_x' : round(sdt,2),
                                                              'end_x' : None
                                                              }
                    elif(each_task.get_isTailVideoGop() == True):
                        video_start_end_pos[vid_count]['end_x'] = round(sdt,2)
                
                
                
                if(each_task.get_parentGopId() == 0 and each_task.get_frameIXinGOP() == 0):
                    annot_text["wf_vid_id"].append((each_wf_key, vid_count))
                    annot_text["x"].append(round(sdt,2))
                    annot_text["y"].append(each_wf_key+0.16)                    
                    text = str(each_task.get_frame_w()) + "x" + str(each_task.get_frame_h()) + "\n" + \
                                str(round(self.workflows_summary[each_wf_key][vid_count]['avg_dispatch_rate'],3)) + "\n" + \
                                str(each_task.get_scheduledDispatchTime()) #str(round(self.workflows_summary[each_wf_key][vid_count]['min_dispatch_rate'],3))
                                                                                
                    annot_text["text"].append(text)
                    
                    if(simon_wf_results_summary != None):
                     
                        try:                        
                            if(simon_wf_results_summary[each_wf_key][vid_count]['result'] == True):
                                annot_text["colour"].append('green')
                            else:
                                if(len(simon_wf_results_summary[each_wf_key][vid_count]['gops_in_outbuff']) > 0):
                                    annot_text["colour"].append('#FF00AA')
                                else:
                                    annot_text["colour"].append('#ff0000')
                        except:
                            annot_text["colour"].append("black")
                    
                    vid_count = vid_count + 1
                    
                               
            x = np.round(np.arange(0.0, max(dispatch_times), 0.01), 2)          
            
            ## setting y-axis
            i = 0
            y = [-1] * len(x) 
            for each_x in x:                
                if(each_x in dispatch_times):
                    y[i] = each_wf_key
                i = i+1
            
            # plot
            plt.scatter(x,y, s=2)
            plt.hold(True)
            
#            for key,val in video_start_end_pos.iteritems():
#                plt.hlines(each_wf_key, val['start_x'], val['end_x'], linewidth=5, alpha=0.5, color='b') 
#                plt.hold(True) 
               
            #plt.hold(True)
            
        plt.minorticks_on()
        plt.grid(True, which='major', color='b', linestyle='-', alpha=0.2)
        plt.grid(True, which='minor', color='b', linestyle='--', alpha=0.2)
        
        #pprint.pprint(annot_text)
        
        if(simon_wf_results_summary != None):
            for i, x in enumerate(annot_text["x"]):            
                plt.annotate(annot_text["text"][i], (annot_text["x"][i],annot_text["y"][i]), color=annot_text["colour"][i], fontsize=6)
        else:
            for i, x in enumerate(annot_text["x"]):            
                plt.annotate(annot_text["text"][i], (annot_text["x"][i],annot_text["y"][i]), fontsize=6)
        
        print "showTaskTimeLine: saving image : " + fname
        plt.savefig(fname, bbox_inches='tight', dpi=100)
        
        plt.close(fig)
        #plt.show()
        
        
        
            
    @staticmethod
    def plot_show():
        plt.show()
                
            
            
    ######################
    ## helper functions ##
    ######################    
    def _weightedChoice(self, weights, objects):
        #http://stackoverflow.com/questions/10803135/weighted-choice-short-and-simple
        """Return a random item from objects, with the weighting defined by weights 
        (which must sum to 1)."""
        cs = np.cumsum(weights) #An array of the weights, cumulatively summed.
        idx = sum(cs < np.random.rand()) #Find the index of the first weight over a random value.
        return objects[idx]
    
    def _genRandomNumList(self, list_len, exclusion_list):
        
        count = 0
        result = []
        
        max_int = (SimParams.NUM_WORKFLOWS * SimParams.WFGEN_MAX_VIDS_PER_WF * SimParams.GOP_LENGTH) + \
                (SimParams.NUM_WORKFLOWS * SimParams.WFGEN_MAX_VIDS_PER_WF)
        
        while (count < list_len):
            random_num = random.randint(1,max_int)
            
            if(random_num not in exclusion_list):
                result.append(random_num)
                count += 1
                
        if (len(result) < SimParams.GOP_LENGTH):
            sys.exit('Error: _genRandomNumList:: error generating priorities')
        else:
            self.used_pri_values.extend(result)        
            
        return result
            
            
                
                
                
            
        
                
            
                    