import pprint
import sys

import simpy
import itertools

## local imports
import libApplicationModel.Task
from  libBuffer.Buffer import Buffer
from SimParams import SimParams
from libApplicationModel.Task import TaskModel
from libResourceManager.RunTimeTaskManager_TT import RMStatus
from libDebug.Debug import Debug, DebugCat
from libMappingAndScheduling.SemiDynamic.TaskMappingAndPriAssCombinedSchemes import TaskMappingAndPriAssCombinedSchemes

class TaskDispatcher_ClosedLoop_wIBuffering:
    def __init__(self, env, in_buffs, ts, multiple_workflows, period, rm, run_simpy_process=True):
        self.env = env
        self.input_buffers = in_buffs
        self.taskset_pool = ts
        self.multiple_workflows = multiple_workflows
        self.label = "TaskDispatcher"
        self.dispatch_period = period
        self.RM_instance = rm
        
        self.rejectedVideoStreams = []        
        self.total_blocks_dispatched = 0
        
        self.wf_last_dispatched_task_ix = {}
        self.wf_empty_status = {}
        for wf_id,each_wf in enumerate(self.multiple_workflows):
            self.wf_last_dispatched_task_ix[wf_id]=0            
            self.wf_empty_status[wf_id] = False  # is the wf empty ??
        
        # in one invocation, how many tasks should be mapped to the cores
        self.dispatch_block_size = SimParams.TASKDISPATCHER_BLOCK_SIZE                
        
        if(run_simpy_process == True):
            # Start the run process everytime an instance is created.        
            self.processInstance = env.process(self.runMultipleWorkflows_ET())
        
                
    ### assume :
    ## - fixed number of workflows in simulation
    ## - within a workflow jobs will have different arrival rates
    ## - one gop is inserted into each input buff from respective workflows at each event
    def runMultipleWorkflows_ET(self):
        ## wait for a bit before starting - give time for nodes to catch up
        ## due to node's initial start sleep delay 
        yield self.env.timeout(SimParams.TASKDISPATCHER_RESET_DELAY)          
        
        print("%f"%self.env.now + "," + self.label + "," + 'runMultipleWorkflows_ET::, : run starting')
        
        if(len(self.input_buffers) != len(self.multiple_workflows)):
            print("%f"%self.env.now + "," + self.label + "," + 'runMultipleWorkflows_ET::, : NumInputBuffers != NumWorflows')
            sys.exit()
            
        while True:
            
            num_tasks_dispatched_in_this_cycle = 0
            tasks_ids_dispatched_this_cycle = []
            
            for wf_id in xrange(SimParams.NUM_WORKFLOWS):   
                new_video_submitted = False             
                if(self.multiple_workflows[wf_id].tasksNotDispatched(self.wf_empty_status[wf_id]) > 0):
                    
                    ## perform task dispatch - take from pool and put into input buffer
                    # each task has a specified dispatch time, all scheduled dispatched
                    # times matching the current dispatch time is dispatched
                    if(self.InputBuffer_isFull(offset=self.dispatch_block_size, id=wf_id) == False) and \
                    ((self.IsPlatformOverloaded() == False)):
                        
                        # if a new video stream, then check if it can be permitted into the system before releasing first GOP                        
                        self.newVideoStreamACQuery(wf_id)   # this disables submission of rejected video streams           
                        
                        temp_count = 0
                        for task_ix, task in enumerate(self.multiple_workflows[wf_id].get_stream_content()):
                            #print task
                            #print self._canTaskBeDispatched(task)
                            if(self._canTaskBeDispatched(task) == True):                                
                                                                
                                # set the dispatch time of the task
                                #print(self.label + ' : Dispatch time ----------  : %f' % self.env.now)    
                                task.set_dispatchTime(self.env.now)
                                
                                # place in input buffer
                                task.set_dispatched_ibuffid(wf_id)
                                self.input_buffers[wf_id].add_Item(task, task.get_id())
                                self.InputBuffer_put(1, id=wf_id)
                                                                
                                num_tasks_dispatched_in_this_cycle += 1
                                tasks_ids_dispatched_this_cycle.append(task.get_id())
                                temp_count += 1
                                
                                # is task the first frame of a new video ?
                                if(task.get_parentGopId() == 0):                                    
                                    new_video_submitted = True
                                else:
                                    new_video_submitted = False  
                                    
                                # update last dispatched task ix counter 
                                self._updateLastDispatchedCounter(wf_id, task_ix)                             
                        
                        if(temp_count == 12):
                            self.total_blocks_dispatched +=1
                    else:
                        #print "-----"
                        Debug.PPrint("%f"%self.env.now + "," + self.label + "," + 'runMultipleWorkflows_ET::, : InputBuffer FULL!!, inbuffid='+str(wf_id), DebugCat.DEBUG_CAT_TDINFO)
                        #print "InputBuffer_isFull : " + str(self.InputBuffer_isFull(offset=self.dispatch_block_size, id=wf_id))
                        #print "IsPlatformOverloaded : " + str(self.IsPlatformOverloaded())
                        
                        # update dropped tasks tracking in RM
                        self.notifyRM_droppedTasks(wf_id)                        
                        #print "-----"
                        
                else:
                    Debug.PPrint("%f"%self.env.now + "," + self.label + "," + 'runMultipleWorkflows_ET::, : WorkFlow [%d] is empty !!' % (wf_id), DebugCat.DEBUG_CAT_TDINFO)
                    self.wf_empty_status[wf_id] = True
                    
                    # check if it is time to stop the simulation 
                    if(self.RM_instance.endSimulation()==True):
                        Debug.PPrint("%f"%self.env.now + "," + self.label + "," + 'runMultipleWorkflows_ET::, : RM says to END simulation !!', DebugCat.DEBUG_CAT_TDINFO)
                        simpy.core._stop_simulate(1)
                        
                        
            ##### DEBUG #########
#            if(self.env.now >121):
#                for i in xrange(SimParams.NUM_INPUTBUFFERS):
#                    print ""
#                    print "inputbuff="+str(i)
#                    print "-----------------"
#                    pprint.pprint(self.input_buffers[i].get_BuffContents())
#                #pprint.pprint(self.RM_instance.task_mapping_table)
#                pprint.pprint(self.RM_instance.flow_table.flowEntries)
#                pprint.pprint(self.RM_instance.flow_table.fire_rqs_outstanding)
#                pprint.pprint(self.RM_instance.numTasksInCPUTaskQs())
#                
#                sys.exit("TaskDispatcher:: runMultipleWorkflows_ET:: forced stop!!!!")
            #####################
            
                    
            ## all appropriate tasks in all workflows are now dispatched to respective inputbuffers, 
            ## now wake up RM and go to sleep
            if(num_tasks_dispatched_in_this_cycle > 0):
                t_list_str = ', '.join(str(x) for x in tasks_ids_dispatched_this_cycle)
                Debug.PPrint("%f"%self.env.now + "," + self.label + "," + ('runMultipleWorkflows_ET::, : %d tasks submitted to input buffers  - ' % (num_tasks_dispatched_in_this_cycle)) + t_list_str , DebugCat.DEBUG_CAT_TDINFO)                
                self.wakeUpRM()
            else:
                Debug.PPrint("%f"%self.env.now + "," + self.label + "," + 'runMultipleWorkflows_ET::, : No tasks dispatched !!!!', DebugCat.DEBUG_CAT_TDINFO)
            
            ## go back to sleep
            #print(self.label + ' : going to sleep  at:  %f' % self.env.now)
            #yield self.env.timeout(self.dispatch_period)
            
            # find when to dispatch next
            next_dispatch_time = self.nextTaskDispatchTime()            
            #Debug.PPrint("%f"%self.env.now + "," + self.label + "," + 'runMultipleWorkflows_ET::, : next dispatch time: %.15f !!' % (next_dispatch_time), DebugCat.DEBUG_CAT_TDINFO)
            
            if next_dispatch_time == None:
                yield self.env.timeout(self.dispatch_period)
            else:
                yield self.env.timeout(next_dispatch_time - self.env.now)
            
    
    
    def _updateLastDispatchedCounter(self, wf_id, task_ix):
        self.wf_last_dispatched_task_ix[wf_id] = task_ix
               
    # goes through all the workflows and finds the task that should be dispatched soonest, based on
    # current time
    def nextTaskDispatchTime(self):
        
        #print "nextTaskDispatchTime:: Enter"
        
        tmptasks_only_dt = []
        for wf_id, each_wf_val in enumerate(self.multiple_workflows):        
            if(self.wf_empty_status[wf_id]==False):
                for each_task in each_wf_val.get_stream_content()[self.wf_last_dispatched_task_ix[wf_id]+1:]:
                    if ( float("%.15f"%each_task.get_scheduledDispatchTime()) > float("%.15f"%self.env.now) ):                    
    #                    print "now: %.20f" % self.env.now
    #                    print "each_task.get_scheduledDispatchTime: %.20f" % each_task.get_scheduledDispatchTime()
                        tmptasks_only_dt.append(each_task.get_scheduledDispatchTime())
                        break
                    
        #sorted_tmptasks = sorted(tmptasks, key=lambda x: x.get_scheduledDispatchTime(), reverse=False)
        #tmptasks_only_dt = [t.get_scheduledDispatchTime() for t in tmptasks]
        
#        if len(sorted_tmptasks) > 0:
#            return sorted_tmptasks[0].get_scheduledDispatchTime()
#        else:
#            return None

        if len(tmptasks_only_dt) > 0:
            return min(tmptasks_only_dt)
        else:
            return None
            
             
    
    
    ## notify RM of the tasks that could not be dispatched, because of overloaded platform
    # this is called when the task is ready to be dispatched (and dispatchDisabled is false) , but system is overloaded
    def notifyRM_droppedTasks(self, wf_id):
        
        #Debug.PPrint("%f"%self.env.now + "," + self.label + "," + 'notifyRM_droppedTasks::, : Enter', DebugCat.DEBUG_CAT_TDDROPPEDTASKS)
        
        dropped_task_list = []
        
        dropping_whole_video = False
        
        for task in self.multiple_workflows[wf_id].get_stream_content():
            if(self._canTaskBeDispatched(task) == True):    # task can be dispatched, but input buffers or TQs are full
                #print "here -- 1"
                if(task.get_parentGopId() == 0): # if dropping the start gop of a video stream, then drop the full video stream
                    
                    Debug.PPrint("%f"%self.env.now + "," + self.label + "," + 'notifyRM_droppedTasks::, : first gop of video stream skipped :' + str(wf_id) + " - " + str(task.get_video_stream_id()), DebugCat.DEBUG_CAT_TDDROPPEDTASKS)
                    
                    # disable disapatch of all tasks in video stream
                    full_video_tasks = self._disableAllTaskDispatchInVS(wf_id, task.get_video_stream_id())                    
                    dropped_task_list.extend(full_video_tasks)
                    
                    dropping_whole_video = True
                    
                    # record rejection
                    self.rejectedVideoStreams.append(self._getVSInfoFromTask(task))
                else:
                    Debug.PPrint("%f"%self.env.now + "," + self.label + "," + 'notifyRM_droppedTasks::, : dropping %d tasks' % (len(dropped_task_list)) , DebugCat.DEBUG_CAT_TDDROPPEDTASKS)
                    dropped_task_list.append(task)
#            else:
#                print "---"
#                print task.get_id()
#                print task.get_scheduledDispatchTime()
#                print task.get_dispatchDisabled()
#                print self.env.now
#                print "---"
                
        if(len(dropped_task_list) > 0):
            
            # dropping a normal job(s)
            if(dropping_whole_video == False):
                Debug.PPrint("%f"%self.env.now + "," + self.label + "," + 'notifyRM_droppedTasks::, : dropping %d tasks' % (len(dropped_task_list)) , DebugCat.DEBUG_CAT_TDDROPPEDTASKS)
                self.RM_instance.addDroppedTask(dropped_task_list, wf_id)
            
            # is this part of the last gop of the video stream ? if so signal RM to remove video stream from runtime app
            if(dropped_task_list[0].get_isTailVideoGop() == True):
                vs_id = dropped_task_list[0].get_video_stream_id()                
                Debug.PPrint("%f"%self.env.now + "," + self.label + "," + 'notifyRM_droppedTasks::, : last gop of video stream skipped :' + str(wf_id) + " - " + str(vs_id), DebugCat.DEBUG_CAT_TDDROPPEDTASKS)
                self.RM_instance.RuntimeApp_removeStream(wf_id, vs_id)
                       
    
    def wakeUpRM(self):
        ## now need to wake up resource manager if sleeping
        if(self.RM_instance.status == RMStatus.RM_SLEEPING):
            Debug.PPrint("%f"%self.env.now + "," + self.label + "," + 'runMultipleWorkflows_ET::, : interrupting RM ', DebugCat.DEBUG_CAT_INTERRUPT)
            self.RM_instance.processInstance.interrupt("TaskDispatcher")
    
    
    
    def _canTaskBeDispatched(self, task):
        if(
           ( ("%.15f"%task.get_scheduledDispatchTime()) == ("%.15f"%self.env.now)) and
           (task.get_dispatchDisabled() == False)           
           ):
            return True
        else:
            return False
    
    def _isNewVideoStream(self, wf_id):
        for each_task in self.multiple_workflows[wf_id].get_stream_content():        
            if ( ("%.15f"%each_task.get_scheduledDispatchTime()) == ("%.15f"%self.env.now)):
                task = each_task                        
                break;
            
        if task == None:
            return False
        else:               
            if(task.get_parentGopId() == 0): # this is a start of a new video
                return True
            else:
                return False
        
    # admission control query    
    # check with RM if the video can be admitted to the system
    # - RM has to : map, assign priorities, and decide AC
    def newVideoStreamACQuery(self, wf_id, task=None, video_stream = None):
        #print "newVideoStreamACQuery:: Enter, wf_id=%d" % (wf_id)        
        
        if(video_stream == None):
                        
            if(task==None): # need to find the task to be dispatched now
                for each_task in self.multiple_workflows[wf_id].get_stream_content():        
                    
                    # debug #
#                    if(wf_id==11) and (each_task.get_parentGopId() == 0) and (each_task.get_unique_gop_id() ==328):
#                        self._debug_task_info(task) # debug
                    # debug #                    
                    
                    if ( ("%.15f" % each_task.get_scheduledDispatchTime()) == ("%.15f" % self.env.now)) and (each_task.get_parentGopId() == 0):
                        task = each_task      
                        break;
            
                if task == None:
                    return False
                else:                
                
                    if(task.get_parentGopId() == 0): # this is a start of a new video
                        
                        #self._debug_task_info(task) # debug
                        
                        # gather specs of video
                        video_specs = self._getVSInfoFromTask(task)
                        
                        ### Combined mapping and priority assignment schemes ###
                        if(SimParams.COMBINED_MAPPING_AND_PRIASS != TaskMappingAndPriAssCombinedSchemes.TASKMAPPINGANDPRIASSCOMBINED_DISABLED):                            
                            (mapping_result, pri_assignment) = self.RM_instance.taskMapperAndPriAssignerCombo.taskMappPriAssCombinedSchemeHandler(video_specs)
                            
                            if(mapping_result != None) and (pri_assignment != None):
                                self._reassignVideoStreamFramePriorities(video_specs, pri_assignment)
                                
                                self.RM_instance.track_MappingAndPriAss(video_specs, mapping_result, pri_assignment)
                                
                                ac_query_result = self._ACQueryRequestHelper(video_specs, task)
                                
                                return ac_query_result
                            
                            else:
                                             
                                # disable disapatch of all tasks in video stream
                                self._disableAllTaskDispatchInVS(wf_id, task.get_video_stream_id())
                                # record rejection
                                self.rejectedVideoStreams.append(video_specs)                                
                                Debug.PPrint("%f"%self.env.now + "," + self.label + "," + 'newVideoStreamACQuery::, : vid_rejected :' + str(wf_id) + " - " + str(task.get_video_stream_id()), DebugCat.DEBUG_CAT_TDINFO)                            
                                return False   
                        
                        
                        ### Individual mapping and priority assignment schemes ###    
                        else:
                            # request the RM to provide an initial mapping                        
                            mapping_result = self.RM_instance.taskPreMapper.taskMappingSchemeHandler(video_specs)
                            
                            if(mapping_result == None): # check if pre-mapping was successful                            
                                # disable disapatch of all tasks in video stream
                                self._disableAllTaskDispatchInVS(wf_id, task.get_video_stream_id())
                                # record rejection
                                self.rejectedVideoStreams.append(video_specs)
                                
                                Debug.PPrint("%f"%self.env.now + "," + self.label + "," + 'newVideoStreamACQuery::, : vid_rejected :' + str(wf_id) + " - " + str(task.get_video_stream_id()), DebugCat.DEBUG_CAT_TDINFO)                            
                                return False                         
                            else:
                                
                                # now assign priorities
                                pri_assignment = self.RM_instance.taskPriAssigner.taskSemiDynPriSchemeHandler(video_specs, mapping_result)
                                
                                # if new priorities are assigned, then re-prioritise the video stream tasks
                                if(pri_assignment != None): 
                                    self._reassignVideoStreamFramePriorities(video_specs, pri_assignment)                            
                                
                                self.RM_instance.track_MappingAndPriAss(video_specs, mapping_result, pri_assignment)
                                self.RM_instance.PSAlgo.conditionalInit()
                                self.RM_instance.startRemapAlgoOnNodes()
                                
                                ac_query_result = self._ACQueryRequestHelper(video_specs, task)
                                
                                return ac_query_result
                    else:
                        sys.exit("newVideoStreamACQuery::error -  not gopid = 0")
                
            else:
                return True
        else:
            sys.exit("newVideoStreamACQuery:: not implemented yet!")
            
    def _ACQueryRequestHelper(self, video_specs, sample_task):
        # tell RM to add the new stream to it's runtime app model - temporary admission
        gop_tasks = self._getVideoStreamGoPTasks(self.env.now, video_specs["wf_id"], sample_task.get_video_stream_id())
        self.RM_instance.RuntimeApp_addStream(video_specs["wf_id"], gop_tasks , self.env.now)    
        
        # perform the admission controller check                       
        result = self.RM_instance.StreamAdmission_NewVideo_ET(video_specs)
       
        if(result == False):    # set all tasks in video to false                            
            # remove previously added stream - reverse admission
            self.RM_instance.RuntimeApp_removeStream(video_specs["wf_id"], video_specs["vid_strm_id"])            
            # disable disapatch of all tasks in video stream
            self._disableAllTaskDispatchInVS(video_specs["wf_id"], sample_task.get_video_stream_id())            
            # record rejection
            self.rejectedVideoStreams.append(video_specs)    
            
            Debug.PPrint("%f"%self.env.now + "," + self.label + "," + '_ACQueryRequestHelper::, : vid_rejected :' + str(video_specs["wf_id"]) + " - " + str(sample_task.get_video_stream_id()), DebugCat.DEBUG_CAT_TDINFO)
            
            return False
        else:
            return True
        
        
    
    def _getVSInfoFromTask(self, task, gop_tasks = None):
        video_specs = {
               "wf_id" : task.get_wfid(),
               "vid_strm_id" : task.get_video_stream_id(),
               "ugid" : task.get_unique_gop_id(),
               "frame_h" : task.get_frame_h(),
               "frame_w" : task.get_frame_w(),
               "fps" : task.get_framerate(),
               "gop_struct" : task.get_gopstructure(),
               "gop_tasks" : gop_tasks,
               "wcc_I" : task.get_wccIFrame(),
               "wcc_P" : task.get_wccPFrame(),
               "wcc_B" : task.get_wccBFrame(),
               "avgcc_I" : task.get_avgccIFrame(),
               "avgcc_P" : task.get_avgccPFrame(),
               "avgcc_B" : task.get_avgccBFrame(),               
               "decoded_frame_size" : task.get_completedTaskSize()                               
               }
        return video_specs
           
    def _disableAllTaskDispatchInVS(self, wf_id, vs_id):
        disabled_list = []
        for each_task in self.multiple_workflows[wf_id].get_stream_content():
            if(each_task.get_video_stream_id() == vs_id):
                if(each_task.get_dispatchDisabled() == False):
                    each_task.set_dispatchDisabled(True)
                    disabled_list.append(each_task)               
        return disabled_list
            
    def IsPlatformOverloaded(self):
        if(self.RM_instance.areNodesOverCapacity() == True): return True
        else: return False
    
    def InputBuffer_isFull(self, offset=0, id=0):
        return (self.input_buffers[id].simpy_container_instance.level >= (self.input_buffers[id].simpy_container_instance.capacity - offset))
    
    def InputBuffer_put(self,n, id=0):
        self.input_buffers[id].simpy_container_instance.put(n)
    
    
    def _getVideoStreamGoPTasks(self, scheduled_dispatch_time, wf_id, stream_id):
        tasks = []        
        for each_task in self.multiple_workflows[wf_id].get_stream_content()[self.wf_last_dispatched_task_ix[wf_id]:]:
            if (("%.15f" % each_task.get_scheduledDispatchTime()) == ("%.15f" % scheduled_dispatch_time)) and \
            (each_task.get_video_stream_id() == stream_id) and \
            (each_task.get_wfid() == wf_id):
                tasks.append(each_task)
        
        return tasks
                
    def _getVideoStreamGoPTasks_byUGID(self, ugid, wf_id):
        gop_tasks = []
        fr_ix = 0
        for each_task in self.multiple_workflows[wf_id].get_stream_content()[self.wf_last_dispatched_task_ix[wf_id]:]:
            if each_task.get_unique_gop_id() == ugid:
                assert (each_task.get_frameIXinGOP() == fr_ix), "_getVideoStreamGoPTasks_byUGID:: Error in frix"
                gop_tasks.append(each_task)
                fr_ix+=1
        return gop_tasks
    
        
    def _reassignVideoStreamFramePriorities(self, video_specs, pri_assignment, check_ugid=False):        
        wf_id = video_specs["wf_id"]
        vs_id = video_specs["vid_strm_id"]        
        ugid = video_specs["ugid"]
                
        # collect all tasks related to that video stream, and change its priority
        for each_task in self.multiple_workflows[wf_id].get_stream_content()[self.wf_last_dispatched_task_ix[wf_id]:]:
            if(each_task.get_video_stream_id() == vs_id):
                if (check_ugid == True): # we check the unique gop id (extra filtering process)
                    if(each_task.get_unique_gop_id() == ugid):
                        each_task.set_priority(pri_assignment[each_task.get_frameIXinGOP()])
                    else:
                        i=1 # nothing
                else: # don't check ugid, just apply priority
                    each_task.set_priority(pri_assignment[each_task.get_frameIXinGOP()]) 
                
            
    
    
    
    #################################################        
    ## Getters
    #################################################
    def get_processInstance(self):
        return self.processInstance     
    
    # are there any tasks scheduled to dispatch in the future, which are not disabled ?
    def _areAllWorkflowsEmpty(self):
        if(False in self.wf_empty_status.values()):
            return False
        else:
            all_workflows_content = list(itertools.chain.from_iterable([sublist.get_stream_content() for sublist in self.multiple_workflows]))
                    
    #        all_workflows_content = [item for sublist in self.multiple_workflows for item in sublist.get_stream_content() 
    #                                 if (item.get_scheduledDispatchTime() >= self.env.now) and (item.get_dispatchDisabled() == False)]
    #        
    #        if(len(all_workflows_content)>0):
    #            count+=1
            count = 0
            for each_task in all_workflows_content:
                if(each_task.get_scheduledDispatchTime() >= self.env.now):
                        if(each_task.get_dispatchDisabled() == False):
                            count += 1
                            break
            
    #        for wf_id in xrange(SimParams.NUM_WORKFLOWS):
    #            for each_task in  self.multiple_workflows[wf_id].get_stream_content():   
    #                if(each_task.get_scheduledDispatchTime() >= self.env.now):
    #                    if(each_task.get_dispatchDisabled() == False):
    #                        count += 1
            
            if(count > 0):
                return False
            else:
                return True
        
    
    #################################################        
    ## Debug
    #################################################
    def _debug_task_info(self, task):
        print "----"
        print "now = %f" % self.env.now
        print "now = %.15f" % self.env.now
        print "id  =" +str(task.get_id())
        print "vsid  =" +str(task.get_video_stream_id())
        print "wfid  =" +str(task.get_wfid())
        print "sdt =%.15f" % task.get_scheduledDispatchTime()
        print "pgid=" + str(task.get_parentGopId())
        print task.get_scheduledDispatchTime() == self.env.now        
        print "----"
        
    
    
            
