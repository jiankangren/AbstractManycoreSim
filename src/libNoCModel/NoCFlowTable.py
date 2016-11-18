import pprint
import json
import sys
#import networkx as nx
import simpy
import matplotlib.pyplot as plt
import numpy as np
import copy


## local imports
from SimParams import SimParams
from NoCFlow import NoCFlow, FlowType
from NoCFlowTableEntry import NoCFlowTableEntry
from libDebug.Debug import Debug, DebugCat
from libApplicationModel.Task import TaskStatus

class NoCFLWTBL_RMStatus:
    RM_SLEEPING       = 1     # i.e sleeping
    RM_BUSYWAITING    = 2     # i.e waiting for someone else/resource
    RM_BUSY           = 3     # i.e busy computing
    RM_ACTIVE         = 4     # i.e. ready and doing work    
    NODE_JUSTWOKEUP   = 5


class NoCFlowTable:
    
    def __init__(self, env, RMInstance, RMMapper, NNInstance):
        self.flowEntries = {}
        self.nextid = 0
        self.env  = env
        self.mutex = simpy.Container(self.env, capacity=1, init=0)
        self.RMInstance = RMInstance
        self.RMMapper = RMMapper
        self.NodeNetworkInstance = NNInstance
        self.label = "NoCFlowTable"
        self.fire_rqs_outstanding = 0   
        
        # for tracking
        self.track_flows_completed = []
        self.track_flows_added = {}
        self.track_firing_requests = {}
        #self.numWaitingFlows = 0
        #self.numActiveFlows = 0        
        
        self.track_num_flows_too_short = 0 # when basic latency is less than x^-10 
    
    def getIntersectingLinks(self, flow1, flow2):
        return list(set(flow1.route).intersection(set(flow2.route)))
    
    
    # NB: higher the pri number, lower the priority
    def addFlow(self, flow, releaseTime, timeRemaining):        
       
        Debug.PPrint("%.15f"%self.env.now + "," + self.label + "," + 'addFlow::, flow_id=[%d], ftype=%d ' % (flow.get_id(), flow.get_type()), DebugCat.DEBUG_CAT_NOCFLWTBLINFO)
        #print flow
        
        # create a flow table entry
        newFlowEntry = NoCFlowTableEntry(self.env, flow, releaseTime)        
        newFlow = newFlowEntry.getFlow()
        
        # set remaining time
        newFlowEntry.setRemainingTime(timeRemaining)
        
        if( self._trunc(timeRemaining, 10) == self._trunc(releaseTime, 10)):
            self.track_num_flows_too_short+=1
        
        # check interfering flows
        for fte_k, fte in self.flowEntries.iteritems():
            existingFlowEntry = fte 
            existingFlow = fte.getFlow()
            intersects = self.getIntersectingLinks(newFlow, existingFlow)
            
            if( len(intersects) > 0): # has interference
                if(existingFlow.get_priority() <= newFlow.get_priority()):   # existing flow 
                    newFlowEntry.addInterferenceSource(existingFlowEntry)
                    newFlowEntry.getFlow().addActualInterferer(existingFlowEntry.getFlow().get_id())
                else:
                    self.flowEntries[fte_k].addInterferenceSource(newFlowEntry)       
                    self.flowEntries[fte_k].getFlow().addActualInterferer(newFlowEntry.getFlow().get_id())                         
            else:
                # no interference
                i=1             
        
        # add to the flow table
        if(flow.get_id() not in self.flowEntries):            
            self.flowEntries[flow.get_id()] = newFlowEntry
            self.nextid += 1
            self.track_addedFlows(newFlowEntry)
        else:
            sys.exit(self.label + "::addFlow: Error!")            
        
        # update link utilisation
        if SimParams.TRACK_NOCLINKUTIL == True:
            flw_links =  flow.get_route()
            for each_link in flw_links:
                each_link.addFlow(flow)
            

        
        
        
    def removeFlow(self, flow_tbl_entry):
        
        Debug.PPrint("%.15f"%self.env.now + "," + self.label + "," + 'removeFlow::, flow_id=[%d], ftype=%d ' % (flow_tbl_entry.getFlow().get_id(), flow_tbl_entry.getFlow().get_type()), DebugCat.DEBUG_CAT_NOCFLWTBLINFO)
        
        temp_flow_storage = None
        temp_flow_storage = flow_tbl_entry.getFlow()
        
        flw_id = flow_tbl_entry.getFlow().get_id() 
        if(flw_id in self.flowEntries):            
            
            # what is this flows' actual latency ? (should be lower than WCET!)
            actual_latency = self.env.now - self.flowEntries[flw_id].getReleaseTime()
            self.flowEntries[flw_id].getFlow().set_actualLatency(actual_latency)            
            
            ## debug ##
            if(SimParams.LOG_OUTPUT_NOCFLOWINFO == True):
                self._writeToLog('flowinfo.txt', self.flowEntries[flw_id].getFlow().toString())                    
            ###########
            
            self.flowEntries[flw_id].setRemovalTime(self.env.now)            
            del self.flowEntries[flw_id]
            
            # track
            self.track_completedFlow(flow_tbl_entry) 
            
            # update the interference of the other flows
            for fte_k, fte in self.flowEntries.iteritems():
                self.flowEntries[fte_k].removeInterferenceSource(flow_tbl_entry)            
            
            # notify completion of the flow
            new_released_tasks = self.handlerFlowComplete(temp_flow_storage)            
            
            # update link utilisation
            if SimParams.TRACK_NOCLINKUTIL == True:            
                flw_links =  flow_tbl_entry.getFlow().get_route()
                for each_link in flw_links:                
                    each_link.removeFlow(flow_tbl_entry.getFlow())
                    
            return new_released_tasks
            
        else:
            sys.exit(self.label + "::removeFlow: Error, flow not found, flw_id=%d, ftype=%d!" %(flw_id, flow_tbl_entry.getFlow().get_type()))
      
    
    # handles the completion of different flow types
    def handlerFlowComplete(self, flow):
        
        new_released_tasks = []
        
        ###################
        ###### DATA #######
        if(flow.get_type() == FlowType.FLOWTYPE_DATA):
            new_released_tasks = self.RMMapper.DataFlowComplete(flow)
        
        elif(flow.get_type() == FlowType.FLOWTYPE_DATA_HEVC):
            new_released_tasks = self.RMMapper.DataFlowComplete(flow)
        
        #####################
        ###### PSALGO #######    
        elif(flow.get_type() == FlowType.FLOWTYPE_PSALGOSIGNALLING):
            # call the destination nodes ps-algo propagation cycle
            when_to_interrupt = self.env.now + SimParams.SYNCH_TIME_OFFSET
            self.env.process(self.callPSAlgoafterDelay(when_to_interrupt, flow))        
        
        elif(flow.get_type() == FlowType.FLOWTYPE_PSALGOSIGNALLING_QUEENSTAT_REQ):
            src_id = flow.get_source() 
            dst_id = flow.get_destination() 
            #print str(self.env.now) + ":: handlerFlowComplete :: FLOWTYPE_PSALGOSIGNALLING_QUEENSTAT_REQ, src=" + str(src_id) + ", dst=" + str(dst_id)
            when_to_interrupt = self.env.now + SimParams.SYNCH_TIME_OFFSET
            self.env.process(self.callPSAlgoQueenStatReqafterDelay(when_to_interrupt, flow))                        
                    
        elif(flow.get_type() == FlowType.FLOWTYPE_PSALGOSIGNALLING_QUEENSTAT_REP):
            src_id = flow.get_source()
            dst_id = flow.get_destination() 
            i=1 # do nothing for now
            #print str(self.env.now) + ":: handlerFlowComplete :: FLOWTYPE_PSALGOSIGNALLING_QUEENSTAT_RE, src=" + str(src_id) + ", dst=" + str(dst_id)
            
        
        ########################
        ###### REMAPPING #######    
        elif(flow.get_type() == FlowType.FLOWTYPE_REMAPPING_NOTIFY_DISPATCHER):
            # notify the RM that a task has completed processing (update task-mapping-table ?)
            new_released_tasks = self.RMInstance.received_Remapping_Request(flow.get_payload_metadata())
        
        ######################################
        ###### MASTER-SLAVE SIGNALLING #######
        elif(flow.get_type() == FlowType.FLOWTYPE_MASTERSLAVESIGNALLING_TASKCOMPLETE):
            # notify the RM that a task has completed processing (update task-mapping-table ?)
            new_released_tasks = self.RMMapper.MSSignallingFlowComplete(flow, flow.get_type())
            
        elif(flow.get_type() == FlowType.FLOWTYPE_MASTERSLAVESIGNALLING_FLOWCOMPLETE):
            # notify the RM that the flow has completed processing
            new_released_tasks = self.RMMapper.MSSignallingFlowComplete(flow, flow.get_type())
        
        #############################
        ###### MMC DATA RD/WR #######
        elif(flow.get_type() == FlowType.FLOWTYPE_MMCTONODE_DATATRANSFER_RD):
            # notify the RM mmc data read has completed
            new_released_tasks = self.RMInstance.putTaskToNodeTQ(flow)
            
        elif(flow.get_type() == FlowType.FLOWTYPE_MMCTONODE_DATATRANSFER_WR):            
            node = flow.get_payload_metadata()['src_node']            
            # notify node that mmc data write has completed
            new_released_tasks = node.sendTaskToOutputBuffAfterMMCWRFlowCompletion(flow)
        
        ##################
        ###### CCP #######
        elif(flow.get_type() == FlowType.FLOWTYPE_CCP_SN_CM_UPDATE_TASKCOMPLETE):
            # get cluster manager 
            cm_node_id = flow.get_destination()
            self.RMInstance.node_network.get_Nodes()[cm_node_id].ccpprops.updateSlaveMonitorInfo_taskCompleteMsgFlowReceived(flow)
            new_released_tasks = []    
            
        elif(flow.get_type() == FlowType.FLOWTYPE_CCP_LOANREQUEST):
            when_to_interrupt = self.env.now + SimParams.CCP_SYNCH_TIME_OFFSET
            self.env.process(self.callCCP_LoanReq_AfterDelay(when_to_interrupt, flow))
        
        elif(flow.get_type() == FlowType.FLOWTYPE_CCP_LOANDELIVERY):            
            when_to_interrupt = self.env.now + SimParams.CCP_SYNCH_TIME_OFFSET
            self.env.process(self.callCCP_LoanDel_AfterDelay(when_to_interrupt, flow))
            
        elif(flow.get_type() == FlowType.FLOWTYPE_CCP_LOANRELEASE):
            when_to_interrupt = self.env.now + SimParams.CCP_SYNCH_TIME_OFFSET
            self.env.process(self.callCCP_LoanRel_AfterDelay(when_to_interrupt, flow))
            
        else:
            sys.exit("handlerFlowComplete:: Error")
        
        return new_released_tasks
        
    
    
    def callPSAlgoafterDelay(self, when_to_call, flow):
        delay = when_to_call - self.env.now
        if(delay > 0):
            yield self.env.timeout(delay)   # delay  
            
            dst_node_id = flow.get_destination()
            self.RMInstance.node_network.get_Nodes()[dst_node_id].psalgoprops.cyclePSPropagation(flow.payload_metadata['ps_hd'])
    
    def callPSAlgoQueenStatReqafterDelay(self, when_to_call, flow):
        delay = when_to_call - self.env.now
        if(delay > 0):
            yield self.env.timeout(delay)   # delay  
            
            #print "callPSAlgoQueenStatReqafterDelay :: after yield"
            dst_node_id = flow.get_destination()
            self.RMInstance.node_network.get_Nodes()[dst_node_id].psalgoprops.receivedQueenStatusMessageRequest(flow)
            
    
    def callCCP_LoanReq_AfterDelay(self, when_to_call, flow):
        delay = when_to_call - self.env.now
        if(delay > 0):
            yield self.env.timeout(delay)   # delay  
            cluster_manager_id = flow.get_destination()
            self.RMInstance.node_network.get_Nodes()[cluster_manager_id].ccpprops.loanRequest_receivedMsg(flow)
                
    def callCCP_LoanDel_AfterDelay(self, when_to_call, flow):
        delay = when_to_call - self.env.now
        if(delay > 0):
            yield self.env.timeout(delay)   # delay

            cluster_manager_id = flow.get_destination()
            self.RMInstance.node_network.get_Nodes()[cluster_manager_id].ccpprops.loanDelivery_receivedMsg(flow)

    
    def callCCP_LoanRel_AfterDelay(self, when_to_call, flow):
        delay = when_to_call - self.env.now
        if(delay > 0):
            yield self.env.timeout(delay)   # delay
            cluster_manager_id = flow.get_destination()
            self.RMInstance.node_network.get_Nodes()[cluster_manager_id].ccpprops.loanRelease_receiveMsg(flow)

    
    def interruptRMAfterDelay(self, when_to_interrupt, finished_flw_ids):
        
        delay = when_to_interrupt - self.env.now
        
        if(delay > 0):
            yield self.env.timeout(delay)   # delay   
        
            if(self.RMInstance.status == NoCFLWTBL_RMStatus.RM_SLEEPING):
                Debug.PPrint("%.15f"%self.env.now + "," + self.label + "," +'interruptRMAfterDelay::, interrupting RM (finished_flw_id=' + str(finished_flw_ids), DebugCat.DEBUG_CAT_INTERRUPT)
                self.RMInstance.processInstance.interrupt("NOCFLOW-"+str(finished_flw_ids))
    
            
    def updateTable(self, fire=False):
        
        Debug.PPrint("%.15f"%self.env.now + "," + self.label + "," + 'updateTable::', DebugCat.DEBUG_CAT_NOCFLWTBLINFO)   

        finished_flw_ids = []        
        fired = False
        
        # create list of flows in decreasing order of priority
#         flows_list =[]
#         for fte_key, fte in self.flowEntries.iteritems():
#             flows_list.append((fte_key, fte))        
        
        flows_list =self.flowEntries.items()       
        flows_list_pri_sorted = sorted(flows_list, key=lambda x: x[1].getFlow().get_priority(), reverse=False)
                
        # check if the flow table entry has completed
        for each_fte in flows_list_pri_sorted:            
            each_fte_flow = each_fte[1]
            each_fte_flow_key = each_fte[0]
            
            # active flows
            if(each_fte_flow.active == True):
                # checks whether current flow completed transmission
                # if true, remove it from the main flow table
                
#                 #### debug ###
#                 if(each_fte_flow_key == 1256):
#                     print "1256:: i_flws :"
#                     print each_fte_flow
#                     print [k for k in self.flowEntries.keys()]
#                     print "%.15f" % self._trunc(each_fte_flow.getRemainingTime(), 10)
#                     print "%.15f" % self._trunc(self.env.now-each_fte_flow.getLastActivationTime(), 10)
#                 ############# 
                
                
                #if(round(each_fte_flow.getRemainingTime(),11) <= round(self.env.now-each_fte_flow.getLastActivationTime(), 11)):
                if( self._trunc(each_fte_flow.getRemainingTime(), 10) <= self._trunc(self.env.now-each_fte_flow.getLastActivationTime(), 10)):
                    new_released_tasks = self.removeFlow(each_fte_flow)    
                    #print [k for k in self.flowEntries.keys()]
                    if(len(new_released_tasks) > 0):
                        finished_flw_ids.append(each_fte_flow.getFlow().get_id())                
                    # add task to the dep buffer of the dst node
                    self._flowComplete_putToNodeDepBuff(each_fte_flow.getFlow())
                    
                    
                else:   ## TODO: ASK JH
                            
                    # check if any of the intersecting flows have become active
                    # if true, update current flow as inactive and update its remaining time
                    each_fte_interferrence_flows = each_fte_flow.getInterferenceFlows()
                    env_now_trunc = self._trunc(self.env.now, 10)
                    
                    for fte in each_fte_interferrence_flows:
                        fte_isActive = fte.active
                        if((fte_isActive == True) or 
                        (fte_isActive == False and ( self._trunc(fte.getReleaseTime(), 10) ==  env_now_trunc))):    # incase the interfering flow was release just now
                            #each_fte_flow.setInactive()
                            self.flowEntries[each_fte_flow_key].setInactive()
                            #rt = float(each_fte_flow.getRemainingTime() - (self.env.now - each_fte_flow.getLastActivationTime()))                            
                            rt = self._trunc(each_fte_flow.getRemainingTime() - (self.env.now-each_fte_flow.getLastActivationTime()), 11)  
                            #each_fte_flow.setRemainingTime(rt)
                            self.flowEntries[each_fte_flow_key].setRemainingTime(rt)
                            
                            break;
                
            # inactive flows
            else:
                
                # checks whether all interfering flows became inactive (or terminated)
                # if true, set current flow as active
                
                each_fte_interferrence_flows = each_fte_flow.getInterferenceFlows()
                
                ### debug ###
#                 if(each_fte_flow_key == 195):
#                     print "195:: i_flws :"
#                     pprint.pprint(each_fte_interferrence_flows)
#                     print str(finished_flw_ids)
                #############                
                
#                 allInactive = True                
#                 for fte in each_fte_interferrence_flows:
#                     if(fte.isActive() == True):
#                         allInactive = False
#                         #break   # TODO: ASK JHR
                
                # are all int.flows inactive ?                
                if any([fte.active for fte in each_fte_interferrence_flows]):
                    allInactive = False
                else:
                    allInactive = True
            
                if(allInactive == True):
                    #each_fte_flow.setActive()
                    self.flowEntries[each_fte_flow_key].setActive()                    
                    if(fire==True):   
                
#                         #### debug ###
#                         if(each_fte_flow_key == 1256):
#                             print "firing---"
#                             print "1256:: i_flws :"
#                             print each_fte_flow
#                             print "%.15f" % each_fte_flow.getRemainingTime()
#                             print "%.15f" % self.env.now
                            
                        fire_time = (each_fte_flow.getRemainingTime()+0.0000000001)
                        #print "going to check _checkFiringRequestOverflow"
                        if(self._checkFiringRequestOverflow(fire_time, each_fte_flow.getFlow())==False):
                            self.env.process(self.addFiringRequest(fire_time, each_fte_flow.getFlow()))
                            fired = True
                            self.fire_rqs_outstanding += 1
                    
#        print "FLWTBL_AFTER_UPDATE: "
#        print "-----------------------"
#        pprint.pprint(self.flowEntries)
#        print "-----------------------"

        if(len(finished_flw_ids) > 0):                    
            #self.interruptRMAfterDelay(float(self.env.now+SimParams.SYNCH_TIME_OFFSET), -1)
            when_to_interrupt = self.env.now + SimParams.SYNCH_TIME_OFFSET
            self.env.process(self.interruptRMAfterDelay(when_to_interrupt, finished_flw_ids))
        
        # update idle links
        self.updateLinkStatus()
        
        # return result
        if(fired == False):
            if(self.fire_rqs_outstanding == 0):
                #sys.exit("nothing fired")
                #print "=========================>>>>>> nothing fired"
                return False
            else:
                return True
        else:
            return True
        
        
        
                    
    #Truncates/pads a float f to n decimal places without rounding
    def _trunc(self, f, n):        
        if n > 15:
            sys.exit("_trunc: error")        
        s = "%.15f" % f
        ss = s[:-(15-n)]        
        return float(ss)
        
        
        
    
    def addFiringRequest(self, time, by_which_flow):
        
        Debug.PPrint("%.15f"%self.env.now + "," + self.label + "," + 'addFiringRequest:: time_willfire=%.15f, by_which_flow=%d' % (time+self.env.now, by_which_flow.get_id()), DebugCat.DEBUG_CAT_NOCFLWTBLINFO)
        
        if(self._checkFiringRequestOverflow(time, by_which_flow)==False):
            
            # tracking
            self.track_firing_request(time, by_which_flow.get_id())       
            
            yield self.env.timeout(time)   # delay            
            self.fire_rqs_outstanding -= 1        
            
            while(self.RMInstance.flow_table.mutex.level == 1):
                i=1 # busy wait                
            self.RMInstance.flow_table.mutex.put(1)   # obtain lock
            while(self.RMInstance.mutex_tmtbl.level == 1):
                i=1 # busy wait                                                            
            self.RMInstance.mutex_tmtbl.put(1)      # obtain lock
            
            # call update again, if no firing requests were made
            result = self.updateTable(fire=True)
            if(result == False):            
    #            print "FLWTBL_AFTER_UPDATE: "
    #            print "-----------------------"
    #            pprint.pprint(self.flowEntries)
    #            print "-----------------------"        
                
                result = self.updateTable(fire=True)
                
    #            print "FLWTBL_AFTER_UPDATE: "
    #            print "-----------------------"
    #            pprint.pprint(self.flowEntries)
    #            print "-----------------------"
            
            self.RMInstance.mutex_tmtbl.get(1)      # release lock
            self.RMInstance.flow_table.mutex.get(1)   # release lock
    
    
    # are there too many firing requests in the system for the same time ? true/false
    def _checkFiringRequestOverflow(self, ftime, flow):
        
        
        if(flow.get_type in [FlowType.FLOWTYPE_PSALGOSIGNALLING, 
                             FlowType.FLOWTYPE_REMAPPING_NOTIFY_DISPATCHER,               
                             FlowType.FLOWTYPE_CCP_SN_CM_UPDATE_TASKCOMPLETE,              
                             FlowType.FLOWTYPE_CCP_LOANREQUEST,                            
                             FlowType.FLOWTYPE_CCP_LOANDELIVERY,                           
                             FlowType.FLOWTYPE_CCP_LOANRELEASE]):                            
            trunced_ftime = self._trunc(ftime, 10)
    #        print "-- _checkFiringRequestOverflow"
    #        print "%.20f" % trunced_ftime
    #        pprint.pprint(self.track_firing_requests)        
    #        for k,v in self.track_firing_requests.iteritems():
    #            print "%.20f" % k
    #        print "--"
    
            if (trunced_ftime in self.track_firing_requests):
                if(len(self.track_firing_requests[trunced_ftime]) > 0):                
                    return True
                else:                
                    return False
            else:
                return False
        else:
            return False
        
       
        
    def _flowComplete_putToNodeDepBuff(self, completed_flow):
        
        #print "_flowComplete_putToNodeDepBuff: " + str(completed_flow)
        result = True
        if(completed_flow.get_type() == FlowType.FLOWTYPE_DATA):
            dst_node_id = completed_flow.get_destination()        
            dst_node = self.NodeNetworkInstance.get_Nodes()[dst_node_id]            
            task = completed_flow.get_respectiveSrcTask() 
            task.set_status(TaskStatus.TASK_DATA_TRANSMISSION_COMPLETE)           
            result = dst_node.dependencyBuff_put(task)
            
        elif(completed_flow.get_type() == FlowType.FLOWTYPE_DATA_HEVC):
            dst_node_id = completed_flow.get_destination()        
            dst_node = self.NodeNetworkInstance.get_Nodes()[dst_node_id]
            payload_metadata = completed_flow.get_payload_metadata()
            task = completed_flow.get_respectiveSrcTask()
            task.set_status(TaskStatus.TASK_DATA_TRANSMISSION_COMPLETE)
            result = dst_node.dependencyBuff_put(task, payload_metadata['child_id'], payload_metadata['each_child_payload'])
            
            #pprint.pprint(json.dumps(dst_node.dependencyBuff_getAll()))             
            
            assert (len(dst_node.dependencyBuff_getAll().keys()) != 0), "_flowComplete_putToNodeDepBuff:: DepBuffPut failed !!"
    
#             fin_task_id = task.get_id()
#             child_task_id = payload_metadata['child_id']
#             self.RMInstance.lock_RM_TMtbl()                       
#             if(fin_task_id not in self.RMInstance.task_mapping_table[child_task_id]['deps_completed']):
#                 self.RMInstance.task_mapping_table[child_task_id]['deps_completed'].append(fin_task_id)        
#             self.RMInstance.release_RM_TMtbl()            
                 
        if(result == False):
            print("%f"%self.env.now + "," + self.label + "," +'_flowComplete_putToNodeDepBuff::, : node-'+ str(dst_node.get_id()) + ", --- dep_buff is FULL ! ")
            pprint.pprint(dst_node.dependency_buff.get_BuffContents())
            pprint.pprint(self.RMInstance.task_mapping_table)
            sys.exit()
     
            
        
    
    def _findIdleLinks(self):        
        list_all_active_link_ids = []
        # get active flows 
        for each_flow_k,each_flow_v  in self.flowEntries.iteritems():            
            if(each_flow_v.isActive() == True):
                flw_link_ids =  [link.get_id() for link in each_flow_v.getFlow().get_route()]
                list_all_active_link_ids.extend(flw_link_ids)
                
        list_all_idle_links = []   
        for each_link in self.RMInstance.interconnect.getLinks():
            if each_link.get_id() not in list_all_active_link_ids:
                list_all_idle_links.append(each_link)
        
        return list_all_idle_links
    
    
    def getRealTimeLinkInfo(self):
        link_content = {}
        # get active flows 
        for each_flow_k,each_flow_v  in self.flowEntries.iteritems():            
            for link in each_flow_v.getFlow().get_route():
                if link.get_id() not in link_content:
                    link_content[link.get_id()] = [each_flow_v.getFlow()]
                else:                    
                    link_content[link.get_id()].append(each_flow_v.getFlow())
        return link_content
    
    
    def getRealTimeLinkInfo_copy(self):
        copy_rtli = {}
        rtli_tbl = self.getRealTimeLinkInfo()
        for k,v in rtli_tbl.iteritems():
            copy_rtli[k] = []            
            for f in v:
                newflow = NoCFlow(f.get_id(),
                               None, None, None, None, 
                               f.get_source(),  f.get_destination(), 
                               f.get_route(),
                               f.get_priority(), 
                               None, 
                               f.get_basicLatency(), 
                               f.get_payload(),
                               f.get_endTime_wrt_BL(),
                               type=f.get_type(), 
                               creation_time=f.get_creation_time()                         
                               )                        
                copy_rtli[k].append(newflow)        
        return copy_rtli
    
    
    
    
    def updateLinkStatus(self):        
        if SimParams.TRACK_NOCLINKUTIL == True:        
            idle_links = self._findIdleLinks()        
            idle_links_ids = [link.get_id() for link in idle_links]
            
            for each_link in self.RMInstance.interconnect.getLinks():
                if(each_link.get_id() in idle_links_ids):                
                    each_link.addIdleTime('idle', self.env.now)
                else:
                    each_link.addIdleTime('active', self.env.now)
                
    
    
    
    #####################################################
    # NoC traffic table management
    # - VNOCTT : volatile_noc_traffic_table
    #####################################################
    def add_VNOCTT(self, new_flw):
        if SimParams.MMC_SMART_NODE_SELECTION_ENABLE == True:
            flow_route_links = new_flw.get_route()        
            for each_link in flow_route_links:
                tbl_k = each_link.get_id()
                if tbl_k not in self.RMInstance.volatile_noc_traffic_table:
                    self.RMInstance.volatile_noc_traffic_table[tbl_k] = [new_flw]
                else:
                    self.RMInstance.volatile_noc_traffic_table[tbl_k].append(new_flw)
        else:
            pass
    
    def refresh_simple_VNOCTT(self):
        if SimParams.MMC_SMART_NODE_SELECTION_ENABLE == True:
            for each_link_id, link_flw_list in self.RMInstance.volatile_noc_traffic_table.iteritems():
                for ix, each_flw in enumerate(link_flw_list):
                    if each_flw.get_endTime_wrt_BL() > self.env.now:
                        del self.RMInstance.volatile_noc_traffic_table[each_link_id][ix]
        else:
            pass
    
    
    def getVNOCTT_copy(self):
        copy_vnoctt = {}
        for k,v in self.RMInstance.volatile_noc_traffic_table.iteritems():
            copy_vnoctt[k] = []            
            for f in v:
                newflow = NoCFlow(f.get_id(),
                               None, None, None, None, 
                               f.get_source(),  f.get_destination(), 
                               f.get_route(),
                               f.get_priority(), 
                               None, 
                               f.get_basicLatency(), 
                               f.get_payload(),
                               f.get_endTime_wrt_BL(),
                               type=f.get_type(), 
                               creation_time=f.get_creation_time()                         
                               )
                        
                copy_vnoctt[k].append(newflow)
        
        return copy_vnoctt
            
        
        
    
    
    # remove expired flows - take blocking of flows into account
    def refresh_wBlocking_VNOCTT(self):        
        if SimParams.MMC_SMART_NODE_SELECTION_ENABLE == True:
            # get the flows that we predict to be finished
            flws_to_remove = {} # linkid : 
            for each_link_id, link_flw_list in self.RMInstance.volatile_noc_traffic_table.iteritems():
                sorted_flws = sorted(link_flw_list, key=lambda x: x.get_priority())
                self.RMInstance.volatile_noc_traffic_table[each_link_id] = sorted_flws            
                high_pri_flw_reltime = sorted_flws[0].get_creation_time()            
                
                for ix, each_flw in enumerate(sorted_flws):
                    predicted_starttime = high_pri_flw_reltime + np.sum([f.get_basicLatency() for f in sorted_flws[:ix]])
                    elapsed_time = (self.env.now + predicted_starttime)
                    if elapsed_time > each_flw.get_basicLatency():
                        if each_link_id in flws_to_remove: 
                            flws_to_remove[each_link_id].append(ix)
                        else:
                            flws_to_remove[each_link_id] = [ix]
            
            # clear out the volatile flow table
            for k,v in flws_to_remove.iteritems():
                del self.RMInstance.volatile_noc_traffic_table[k][v]
        else:
            pass
                        
                 
    
    ################################
    # setters/getters
    ################################
    def get_flow(self, src_task_id=None, dst_task_id=None, src_node_id=None, dst_node_id=None):
        if (src_task_id != None) and (dst_task_id != None) and (src_node_id != None) and (dst_node_id != None):
            for each_flow_k,each_flow_v  in self.flowEntries.iteritems():
                
                #pprint.pprint(each_flow_v)
                
                if(each_flow_v['flow'].respectiveSrcTaskId == src_task_id) and \
                    (dst_task_id in each_flow_v['flow'].respectiveDstTaskId) and \
                    (each_flow_v['flow'].source == src_node_id) and \
                    (each_flow_v['flow'].destination == dst_node_id):
                        return (each_flow_k,each_flow_v)
            
            return (None, None)
        else:
            return (None, None)
    
    
    
    ################################
    # tracking related
    ################################
    def track_completedFlow(self, flw_entry):
        if(SimParams.TRACK_COMPLETED_FLOWINFO == True):
            
            entry = {
                     #'id' : int(flw_entry.getFlow().get_id()), 
                     'tp' : int(flw_entry.getFlow().get_type()),
                     'pri' : float(flw_entry.getFlow().get_priority()),
                     'pl' : float(flw_entry.getFlow().get_payload()),                      
                     'bl' : float(flw_entry.getFlow().get_basicLatency()), 
                     #'src' : int(flw_entry.getFlow().get_source()), 
                     #'dst' : int(flw_entry.getFlow().get_destination()), 
                     #'src_tid' : flw_entry.getFlow().get_respectiveSrcTaskId(),
                     #'dst_tid' : flw_entry.getFlow().get_respectiveDstTaskId(),
                     #'st' : float(flw_entry.getReleaseTime()), 
                     #'et' : float(flw_entry.getRemovalTime()),
                     'l_var' :  float( (float(flw_entry.getRemovalTime()) - float(flw_entry.getReleaseTime())) - float(flw_entry.getFlow().get_basicLatency()) ),
                     'intfs' : int(len(flw_entry.getFlow().get_actualInterferers())),
                     
                     'r' : str(flw_entry.getFlow().get_route()),
                     'r_len' : len(flw_entry.getFlow().get_route()),
                     #'pm' : str(flw_entry.getFlow().get_payload_metadata())
                     }
            
            self.track_flows_completed.append(entry)
            #print "flow completed - %d " % int(flw_entry.getFlow().get_id())
            
    def track_addedFlows(self, flw_entry):
        if(SimParams.TRACK_ADDED_FLOWINFO == True):
            
            entry = {
                     'id' : flw_entry.getFlow().get_id(), 
                     'type' : flw_entry.getFlow().get_type(),
                     'pri' : flw_entry.getFlow().get_priority(),                      
                     'bl' : flw_entry.getFlow().get_basicLatency(), 
                     'src' : flw_entry.getFlow().get_source(), 
                     'dst' : flw_entry.getFlow().get_destination(), 
                     'src_tid' : flw_entry.getFlow().get_respectiveSrcTaskId(), 
                     'dst_tid' : flw_entry.getFlow().get_respectiveDstTaskId(), 
                     'st' : flw_entry.getReleaseTime(),                     
                     }
            if(flw_entry.getReleaseTime() not in self.track_flows_added):            
                self.track_flows_added[flw_entry.getReleaseTime()] = entry
            else:
                print "WARNING:: track_addedFlows: flows added at the same time.."
                self.track_flows_added[flw_entry.getReleaseTime()] = entry
                
                

    def track_firing_request(self, ftime, fflowid):
        #trunced_ftime = self._trunc(ftime, 10)
        
        trunced_ftime = self._trunc(ftime, 10)
        
#        print "-- track_firing_request"
#        print "%.20f" % trunced_ftime
#        pprint.pprint(self.track_firing_requests)        
#        for k,v in self.track_firing_requests.iteritems():
#            print "%.20f" % k        
#        print "--"        
        
        if trunced_ftime not in self.track_firing_requests:
            self.track_firing_requests[trunced_ftime] = [fflowid]
        else:
            self.track_firing_requests[trunced_ftime].append(fflowid)
            
        
    
    ################################               
    ## helpers
    ################################
    def numEntries(self):
        return len(self.flowEntries)
    

    def _writeToLog(self, fname, data):
        f = open(fname, 'a')
        f.write(data + "\n")
        f.close()
        
    def lock_RM_FLWtbl(self):
        while(self.RMInstance.flow_table.mutex.level == 1):
            i=1 # busy wait                                       
        self.RMInstance.flow_table.mutex.put(1)   # obtain lock   
    
    def release_RM_FLWtbl(self):
        self.RMInstance.flow_table.mutex.get(1) # release lock
        
