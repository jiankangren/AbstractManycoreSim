import pprint
import sys

import simpy

## local imports
import libApplicationModel.Task
from libBuffer.Buffer import Buffer
from SimParams import SimParams
from libApplicationModel.Task import TaskModel
from libResourceManager.RunTimeTaskManager_TT import RMStatus
from libDebug.Debug import Debug, DebugCat
from libMappingAndScheduling.SemiDynamic.TaskMappingAndPriAssCombinedSchemes import TaskMappingAndPriAssCombinedSchemes
from TaskDispatcher_ClosedLoop_wIBuffering import TaskDispatcher_ClosedLoop_wIBuffering

class TaskDispatcher_PSAlgo(TaskDispatcher_ClosedLoop_wIBuffering):
    def __init__(self, env, in_buffs, ts, multiple_workflows, period, rm, ):
        
        TaskDispatcher_ClosedLoop_wIBuffering.__init__(self, env, in_buffs, ts, multiple_workflows, period, rm, run_simpy_process=False)
        self.label = "TaskDispatcher_PSAlgo"
        
        
        # Start the run process everytime an instance is created.        
        self.processInstance = env.process(self.runMultipleWorkflows())
        
                
    ### assume :
    ## - fixed number of workflows in simulation
    ## - within a workflow jobs will have different arrival rates
    ## - one gop is inserted into each input buff from respective workflows at each event
    def runMultipleWorkflows(self):
        ## wait for a bit before starting - give time for nodes to catch up
        ## due to node's initial start sleep delay 
        yield self.env.timeout(SimParams.TASKDISPATCHER_RESET_DELAY)          
        
        print("%f"%self.env.now + "," + self.label + "," + 'runMultipleWorkflows::, : run starting')
        
        if(len(self.input_buffers) != len(self.multiple_workflows)):
            print("%f"%self.env.now + "," + self.label + "," + 'runMultipleWorkflows::, : NumInputBuffers != NumWorflows')
            sys.exit()
            
        while True:
            
            num_tasks_dispatched_in_this_cycle = 0
            tasks_ids_dispatched_this_cycle = []
            
            for wf_id in xrange(SimParams.NUM_WORKFLOWS):   
                new_video_submitted = False             
                if(self.multiple_workflows[wf_id].tasksNotDispatched() > 0):
                    
                    ## perform task dispatch - take from pool and put into input buffer
                    # each task has a specified dispatch time, all scheduled dispatched
                    # times matching the current dispatch time is dispatched
                    if(self.InputBuffer_isFull(offset=self.dispatch_block_size, id=wf_id) == False):
                        
                        # if a new video stream, then check if it can be permitted into the system before releasing first GOP                        
                        self.newVideoStreamACQuery(wf_id)   # this disables submission of rejected video streams           
                        
                        temp_count = 0
                        for task in self.multiple_workflows[wf_id].get_stream_content():
                            #print task
                            #print self._canTaskBeDispatched(task)
                            if(self._canTaskBeDispatched(task) == True):                                
                                                                
                                # set the dispatch time of the task
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
                        
                        if(temp_count == 12):
                            self.total_blocks_dispatched +=1
                    else:
                        Debug.PPrint("%f"%self.env.now + "," + self.label + "," + 'runMultipleWorkflows_ET::, : InputBuffer FULL!!, inbuffid='+str(wf_id), DebugCat.DEBUG_CAT_TDINFO)                        
                        # update dropped tasks tracking in RM
                        self.notifyRM_droppedTasks(wf_id)           
                else:
                    Debug.PPrint("%f"%self.env.now + "," + self.label + "," + 'runMultipleWorkflows_ET::, : WorkFlow [%d] is empty !!' % (wf_id), DebugCat.DEBUG_CAT_TDINFO)
                    
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
            
            # find when to dispatch next
            next_dispatch_time = self.nextTaskDispatchTime()            
            #Debug.PPrint("%f"%self.env.now + "," + self.label + "," + 'runMultipleWorkflows_ET::, : next dispatch time: %.15f !!' % (next_dispatch_time), DebugCat.DEBUG_CAT_TDINFO)
            
            if next_dispatch_time == None:
                yield self.env.timeout(self.dispatch_period)
            else:
                yield self.env.timeout(next_dispatch_time - self.env.now)
            
   
    # admission control query    
    # check with RM if the video can be admitted to the system
    # - RM has to : map, assign priorities, and decide AC
        #print "newVideoStreamACQuery:: Enter, wf_id=%d" % (wf_id)        
    def newVideoStreamACQuery(self, wf_id, task=None, video_stream = None):
        
        if(video_stream == None):
                        
            if(task==None): # need to find the task to be dispatched now
                for each_task in self.multiple_workflows[wf_id].get_stream_content():        
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
                                # disable dispatch of all tasks in video stream
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
        
    
    
    #################################################        
    ## Getters
    #################################################
    
    
    #################################################        
    ## Debug
    #################################################
    
            
