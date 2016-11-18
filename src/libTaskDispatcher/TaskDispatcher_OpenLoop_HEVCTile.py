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
from libMappingAndScheduling.SemiDynamic.TaskTileMappingAndPriAssCombinedSchemes import TaskTileMappingAndPriAssCombinedSchemes
from TaskDispatcher_ClosedLoop_wIBuffering import TaskDispatcher_ClosedLoop_wIBuffering

class TaskDispatcher_OpenLoop_HEVCTile(TaskDispatcher_ClosedLoop_wIBuffering):
    def __init__(self, env, in_buffs, ts, multiple_workflows, period, rm, ):
        
        TaskDispatcher_ClosedLoop_wIBuffering.__init__(self, env, in_buffs, ts, multiple_workflows, period, rm, run_simpy_process=False)
        self.label = "TaskDispatcher_OpenLoop_HEVCTile"        
        
        self.dispatchqueue_tiletasks = None
        
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
                if(self.multiple_workflows[wf_id].tasksNotDispatched(self.wf_empty_status[wf_id]) > 0):
                    
                    ## perform task dispatch - take from pool and put into input buffer
                    # each task has a specified dispatch time, all scheduled dispatched
                    # times matching the current dispatch time is dispatched
                    if(self.InputBuffer_isFull(offset=self.dispatch_block_size, id=wf_id) == False):
                        
                        # if a new video stream, then check if it can be permitted into the system before releasing first GOP
                        # this also maps and assigns priorities to the gop tasks                        
                        self.newVideoStreamACQuery(wf_id)   # this disables submission of rejected video streams           
                        
                        temp_count = 0
                        for task_ix,task in enumerate(self.multiple_workflows[wf_id].get_stream_content()[self.wf_last_dispatched_task_ix[wf_id]:]):                            
                            if(self._canTaskBeDispatched(task) == True):                                
                                                                
                                # set the dispatch time of the task
                                task.set_dispatchTime(self.env.now)
                                
                                # get tile level tasks of the hevc frame task
                                tile_level_taskslist = self._get_tiletasks_from_dispatchqueue(task.get_id()) 
                                assert(len(tile_level_taskslist)>0), self.label+":: tile_level_taskslist : empty !!"
                                
                                # place each tile level task in input buffer 
                                for each_tile_task in tile_level_taskslist:                                    
                                    each_tile_task.set_dispatchTime(self.env.now)
                                    each_tile_task.set_dispatched_ibuffid(wf_id)
                                    self.input_buffers[wf_id].add_Item(each_tile_task, each_tile_task.get_id())
                                    self.InputBuffer_put(1, id=wf_id)
                                    
                                    #print "dispatched :: ", each_tile_task.get_id()
                                    
                                num_tasks_dispatched_in_this_cycle += 1
                                tasks_ids_dispatched_this_cycle.append(task.get_id())
                                temp_count += 1
                                
                                # update last dispatched task ix counter 
                                self._updateLastDispatchedCounter(wf_id, task_ix)
                        
                        self._clear_tiletask_dispatchqueue()
                        
                        if(temp_count > 1):
                            self.total_blocks_dispatched +=1
                    else:
                        Debug.PPrint("%f"%self.env.now + "," + self.label + "," + 'runMultipleWorkflows::, : InputBuffer FULL!!, inbuffid='+str(wf_id), DebugCat.DEBUG_CAT_TDINFO)                        
                        # update dropped tasks tracking in RM
                        self.notifyRM_droppedTasks(wf_id)           
                else:
                    Debug.PPrint("%f"%self.env.now + "," + self.label + "," + 'runMultipleWorkflows::, : WorkFlow [%d] is empty !!' % (wf_id), DebugCat.DEBUG_CAT_TDINFO)
                    self.wf_empty_status[wf_id] = True
                    
                    # check if it is time to stop the simulation 
                    if(self.RM_instance.endSimulation()==True):
                        Debug.PPrint("%f"%self.env.now + "," + self.label + "," + 'runMultipleWorkflows::, : RM says to END simulation !!', DebugCat.DEBUG_CAT_TDINFO)
                        simpy.core._stop_simulate(1)
                        
                        
            ##### DEBUG #########
#             if(self.env.now >5):
#                 for i in xrange(SimParams.NUM_INPUTBUFFERS):
#                     print ""
#                     print "inputbuff="+str(i)
#                     print "-----------------"
#                     pprint.pprint(self.input_buffers[i].get_BuffContents())
#                 #pprint.pprint(self.RM_instance.task_mapping_table)
#                 pprint.pprint(self.RM_instance.flow_table.flowEntries)                
#                 pprint.pprint(self.RM_instance.flow_table.fire_rqs_outstanding)
#                 pprint.pprint(self.RM_instance.numTasksInCPUTaskQs())
#                 
#                 sys.exit("TaskDispatcher:: runMultipleWorkflows_ET:: forced stop!!!!")
            #####################
            
                    
            ## all appropriate tasks in all workflows are now dispatched to respective inputbuffers, 
            ## now wake up RM and go to sleep
            if(num_tasks_dispatched_in_this_cycle > 0):
                t_list_str = ', '.join(str(x) for x in tasks_ids_dispatched_this_cycle)
                #Debug.PPrint("%f"%self.env.now + "," + self.label + "," + ('runMultipleWorkflows::, : %d tasks submitted to input buffers  - ' % (num_tasks_dispatched_in_this_cycle)) + t_list_str , DebugCat.DEBUG_CAT_TDINFO)                
                Debug.PPrint("%f"%self.env.now + "," + self.label + "," + ('runMultipleWorkflows::, : %d tasks submitted to input buffers  - ' % (num_tasks_dispatched_in_this_cycle)) + t_list_str , DebugCat.DEBUG_CAT_TDINFO)
                self.wakeUpRM()
            else:
                Debug.PPrint("%f"%self.env.now + "," + self.label + "," + 'runMultipleWorkflows::, : No tasks dispatched !!!!', DebugCat.DEBUG_CAT_TDINFO)
            
            # find when to dispatch next
            next_dispatch_time = self.nextTaskDispatchTime()            
            #Debug.PPrint("%f"%self.env.now + "," + self.label + "," + 'runMultipleWorkflows::, : next dispatch time: %.15f !!' % (next_dispatch_time), DebugCat.DEBUG_CAT_TDINFO)
            
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
                for each_task in self.multiple_workflows[wf_id].get_stream_content()[self.wf_last_dispatched_task_ix[wf_id]:]:        
                    if(
                        (("%.15f" % each_task.get_scheduledDispatchTime()) == ("%.15f" % self.env.now)) and 
                         (each_task.get_frameIXinGOP() == 0)
                       ):
                            task = each_task      
                            break;
            
                if task == None:
                    return False
                else:
                    
                    # get all gop tasks 
                    gop_tasks = self._getVideoStreamGoPTasks_byUGID(task.get_unique_gop_id(), wf_id)
                                                                            
                    # gather specs of video
                    video_specs = self._getVSInfoFromTask(task, gop_tasks=gop_tasks)    
                    
                    # refresh the volative mapping table                    
                    #self.RM_instance.Mapper.volatileTaskMappingTable_RemoveExpiredTasks_TileTasks_v1()
                    
                    
                    ### New video stream start ###
                    # perform mapping
                    # perform priority assignment
                    # perform AC query
                    # return AC query
                    
                    if(task.get_parentGopId() == 0): # this is a start of a new video                        
                        #self._debug_task_info(task) # debug
                        
                        ### Combined mapping and priority assignment schemes ###
                        if(SimParams.COMBINED_MAPPING_AND_PRIASS != TaskMappingAndPriAssCombinedSchemes.TASKMAPPINGANDPRIASSCOMBINED_DISABLED):                            
                            (tile_mapping_result, 
                             tile_pri_assignment, 
                             new_tile_tasklist_dict) = self.RM_instance.taskTileMapperAndPriAssignerCombo.taskTileMappPriAssCombinedSchemeHandler(video_specs)
                            
                            if(tile_mapping_result != None) and (tile_pri_assignment != None) and (len(new_tile_tasklist_dict.keys()) > 0):                                
                                # add the tile tasks to the dispatch queue                                
                                self.dispatchqueue_tiletasks = new_tile_tasklist_dict
                                
                                # usual stuff
                                #self._reassignVideoStreamFramePriorities(video_specs, tile_pri_assignment, check_ugid=True)                                
                                #self.RM_instance.track_MappingAndPriAss(video_specs, tile_mapping_result, tile_pri_assignment)
                                
                                # get ac query                                
                                ac_query_result = self._ACQueryRequestHelper(video_specs, task)         # returns true always (for now)                       
                                return ac_query_result                            
                            else:                                             
                                # disable dispatch of all tasks in video stream
                                self._disableAllTaskDispatchInVS(wf_id, task.get_video_stream_id())
                                # record rejection
                                self.rejectedVideoStreams.append(video_specs)                                
                                Debug.PPrint("%f"%self.env.now + "," + self.label + "," + 
                                             'newVideoStreamACQuery::, : vid_rejected :' + 
                                             str(wf_id) + " - " + str(task.get_video_stream_id()), DebugCat.DEBUG_CAT_TDINFO)                            
                                return False
                        else:
                            sys.exit("newVideoStreamACQuery::error - only combined priass is implemented - 1")
                            
                    ### Continuing stream, new gop ###
                    # perform mapping
                    # perform priority assignment
                    else:
                        
                        ### Combined mapping and priority assignment schemes ###
                        if(SimParams.COMBINED_MAPPING_AND_PRIASS != TaskMappingAndPriAssCombinedSchemes.TASKMAPPINGANDPRIASSCOMBINED_DISABLED):                            
                            (tile_mapping_result, 
                             tile_pri_assignment, 
                             new_tile_tasklist_dict) = self.RM_instance.taskTileMapperAndPriAssignerCombo.taskTileMappPriAssCombinedSchemeHandler(video_specs)                            
                            if(tile_mapping_result != None) and (tile_pri_assignment != None) and (len(new_tile_tasklist_dict.keys()) > 0):                                
                                # add the tile tasks to the dispatch queue                                
                                self.dispatchqueue_tiletasks = new_tile_tasklist_dict
                                
                                # usual stuff
                                #self._reassignVideoStreamFramePriorities(video_specs, tile_pri_assignment, check_ugid=True)                                
                                #self.RM_instance.track_MappingAndPriAss(video_specs, tile_mapping_result, tile_pri_assignment)
                                return True                            
                            else:                                             
                                sys.exit("newVideoStreamACQuery::error - stream admitted, but mapping unsuccessful")
                        else:
                            sys.exit("newVideoStreamACQuery::error - only combined priass is implemented - 2")
            else:
                return True
        else:
            sys.exit("newVideoStreamACQuery:: not implemented yet!")
            
            
            
            
    # for now we admit all video streams        
    def _ACQueryRequestHelper(self, video_specs, sample_task, gop_tasks=None):
        print "_ACQueryRequestHelper:: Disabled - admitting all streams"
        return True
        
    
    #################################################        
    ## Getters
    #################################################
    
    
    #################################################        
    ## Helpers
    #################################################
    def _get_tiletasks_from_dispatchqueue(self, parent_task_id):
        tile_tasks = []
        #print parent_task_id
        #print "len(self.dispatchqueue_tiletasks) : ", len(self.dispatchqueue_tiletasks.keys())
        tile_tasks = self.dispatchqueue_tiletasks[parent_task_id]
        return tile_tasks
    
    def _clear_tiletask_dispatchqueue(self):
        self.dispatchqueue_tiletasks = None
    
    
    
    
    #################################################        
    ## Debug
    #################################################
    
            
