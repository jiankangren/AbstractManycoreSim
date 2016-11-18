import pprint
import sys
import math
#import networkx as nx
import simpy
import matplotlib.pyplot as plt
from datetime import timedelta, datetime

## local imports
from SimParams import SimParams
from libDebug.Debug import Debug, DebugCat



class NoCFlow:
    
    def __init__(self, id, resptaskSrc, resptaskSrcid, resptaskDstid, resptaskDstIxs, source, destination, route,
                 priority, releaseJitter, basicLatency, payload, endTime_wrt_BasicLatency, type=1,
                 payload_metadata=None, creation_time=None):
        self.id = id
        self.type = type
        self.respectiveSrcTask = resptaskSrc
        self.respectiveSrcTaskId = resptaskSrcid
        self.respectiveDstTaskId = resptaskDstid    # this could be a list of taskids
        self.respectiveDstTaskIxs =  resptaskDstIxs # this could be a list of frame indexes
        self.source = source
        self.destination = destination        
        self.route = route
        self.priority = priority        
        self.releaseJitter =  releaseJitter      
        self.basicLatency = basicLatency        
        self.payload = payload        
        self.payload_metadata = payload_metadata
        self.endTime_wrt_BL = endTime_wrt_BasicLatency
        self.period = None                
        self.analytical_wcet = None
        self.analytical_wcet_with_dep = None
        self.actualLatency = None
        self.actualInterferers = []
        
        if creation_time == None:
            self.creation_time = endTime_wrt_BasicLatency-basicLatency
        else:
            self.creation_time = creation_time
            
    
    def __repr__(self):
        debug = "<Flow "
        debug += " id=" + str(self.id)
        debug += " type=" + str(self.type)
        if(self.respectiveSrcTask != None):
            debug += " wfstmids='(" + str(self.respectiveSrcTask.get_wfid()) + "," + str(self.respectiveSrcTask.get_video_stream_id()) + ")'"
        debug += " stid=" + str(self.respectiveSrcTaskId)       
        debug += " dtid=" + str(self.respectiveDstTaskId)
        if(self.respectiveSrcTask != None):
            debug += " ugid=" + str(self.get_respectiveSrcTask().get_unique_gop_id())   # unique gop id of src task
            debug += " stgid=" + str(self.get_respectiveSrcTask().get_frameIXinGOP())  # gop ix of src task 
        debug += " src=" + str(self.source)        
        debug += " dst=" + str(self.destination)
        debug += " route=" + str(self.route)
        debug += " pri=" + str(self.priority)
        debug += " bl=" +  str(self.basicLatency)        
        debug += " al=" +  str(self.actualLatency)
        
        debug += " />"
        
        return debug
    
    
    def toString(self):
        debug = "<Flow "
        debug += " id=" + str(self.id)
        debug += " wfstmids='(" + str(self.get_respectiveSrcTask().get_wfid()) + "," + str(self.get_respectiveSrcTask().get_video_stream_id()) + ")'"
        debug += " stid=" + str(self.respectiveSrcTaskId)       
        debug += " dtid=" + str(self.respectiveDstTaskId)
        debug += " ugid=" + str(self.get_respectiveSrcTask().get_unique_gop_id())   # unique gop id of src task
        debug += " r=" + str(self.route)
        debug += " p=" + str(self.priority)
        debug += " aI=" + str(self.actualInterferers)
        debug += " aL=" +  str(self.actualLatency)
        debug += " />"
        
        return debug
    
    
        
    # minimal version of to-string (for schedulability debug)
    def getSchedulability_toString(self):
        debug = ""
        debug += " id='" + str(self.id)+ "'"
        debug += " wfstmids='(" + str(self.respectiveSrcTask.get_wfid()) + "," + str(self.respectiveSrcTask.get_video_stream_id()) + ")'"
        debug += " stid='" + str(self.respectiveSrcTaskId) + "'"      
        debug += " dtid='" + str(self.respectiveDstTaskId)+ "'"   
        debug += " src='" + str(self.source) + "'"       
        debug += " dst='" + str(self.destination)+ "'"
        debug += " route='" + str(self.route)+ "'"
        debug += " pri='" + str(self.priority)+ "'"
        debug += " p='" + str(self.period)+ "'"
        debug += " j='" + str(self.releaseJitter)+ "'"     
        
        return debug    
        
    
    
    def getFlowHashCode(self):     
        
        flow_type = self.get_type()
        src_task = self.get_respectiveSrcTask()
        dst_task_ixs = self.get_respectiveDstTaskIx()
        
        if (flow_type == FlowType.FLOWTYPE_DATA):             
            src_task_name = "t_" + str(src_task.get_wfid()) + "_" + str(src_task.get_video_stream_id()) + "_" + str(src_task.get_frameIXinGOP())
            dst_task_ixs = "tix_" +  ':'.join([str(x) for x in dst_task_ixs])            
            name = src_task_name + "-->" + dst_task_ixs
            
        elif (flow_type == FlowType.FLOWTYPE_MMCTONODE_DATATRANSFER_RD):
            wf_id = self.get_payload_metadata()['wf_id']
            strm_id = self.get_payload_metadata()['vid_strm_id']
            gop_ix = self.get_payload_metadata()['gop_ix']            
            dst_task_name = "t_" + str(wf_id) + "_" + str(strm_id) + "_" + str(gop_ix)
                        
            name = "MMC" + "-->" + dst_task_name
            
        elif (flow_type == FlowType.FLOWTYPE_MMCTONODE_DATATRANSFER_WR):
            wf_id = self.get_payload_metadata()['wf_id']
            strm_id = self.get_payload_metadata()['vid_strm_id']
            gop_ix = self.get_payload_metadata()['gop_ix']
                        
            src_task_name = "t_" + str(wf_id) + "_" + str(strm_id) + "_" + str(gop_ix)            
            name = src_task_name + "-->" + "MMC"
                                    
        else:
            sys.exit("Error: getFlowHashCode:: unknown type = " + str(flow_type))
        
        return name
        
    def addActualInterferer(self, interf):
        self.actualInterferers.append(interf)
    
    
    
    ## getters/setters    
    def set_extendedLatency(self, extL):
        self.extendedLatency = extL    
    def set_releaseJitter(self, rj):
        self.releaseJitter = rj
    def set_period(self, p):
        self.period = p
    def set_analytical_wcet(self, w):
        self.analytical_wcet = w
    def set_analytical_wcet_with_dep(self, w):
        self.analytical_wcet_with_dep = w
    def set_actualLatency(self, al):
        self.actualLatency = al
    def set_type(self, tp):
        self.type = tp
    
    def set_payload_metadata(self, k, v):
        if k in self.payload_metadata:
            self.payload_metadata[k] = v
        else:
            print "Warning : set_payload_metadata - key not found = " + k
        
    
    
    def get_extendedLatency(self):
        return self.extendedLatency
    def get_intersections(self):
        return self.waitsFor
    def get_respectiveSrcTask(self):
        return self.respectiveSrcTask
    def get_respectiveSrcTaskId(self):
        return self.respectiveSrcTaskId
    def get_respectiveDstTaskId(self):
        return self.respectiveDstTaskId
    def get_respectiveDstTaskIx(self):
        return self.respectiveDstTaskIxs    
    def get_destination(self):
        return self.destination
    def get_source(self):
        return self.source
    def get_priority(self):
        return self.priority
    def get_id(self):
        return self.id
    def get_basicLatency(self):
        return self.basicLatency
    def get_route(self):
        return self.route
    def get_releaseJitter(self):
        return self.releaseJitter
    def get_period(self):
        return self.period
    def get_analytical_wcet(self):
        return self.analytical_wcet
    def get_analytical_wcet_with_dep(self):
        return self.analytical_wcet_with_dep
    def get_type(self):
        return self.type
    def get_payload_metadata(self):
        return self.payload_metadata    
    def get_actualInterferers(self):
        return self.actualInterferers
    def get_payload(self):
        return self.payload
    def getUtilisation(self):
        util = float(self.basicLatency/self.period)
        return util
    def get_creation_time(self):
        return self.creation_time
    def get_endTime_wrt_BL(self):
        return self.endTime_wrt_BL
    
    ###############################################
    ## functions to assist schedulability analysis
    ###############################################
    
    @staticmethod
    def getPriorityFromTask(task_pri, RMInstance, nextid=None):        
        if(nextid==None):
            nextid = RMInstance.flow_table.nextid                
        flw_priority = task_pri + (RMInstance.flow_priority_offset+100) + nextid
        
        return flw_priority
    
    # all traffic flows that :
    # - have higher (or equal) priority than the traffic in question
    # - share at least one link with the  traffic in question    
    def getDirectInterferenceSet(self, all_flows):
        
        subset = []
        
        for each_flw in all_flows:            
            if(self._equals_v2(self, each_flw) == False) and (each_flw.get_priority() <= self.get_priority()):
                if(self._intersects(each_flw, self) > 0):                    
                    subset.append(each_flw)
                
        return subset
    
    
    # all traffic flows that :
    # - have higher (or equal) priority than the traffics that interfere with the traffic in question
    # - don't share links with the  traffic in question    
    def getIndirectInterferenceSet(self, all_flows):
        
        subset = []
        direct = self.getDirectInterferenceSet(all_flows)
        
        for each_flw in all_flows:            
            if(self._equals_v2(self, each_flw) == False) and (each_flw not in direct):                
                for each_d_flw in direct:                    
                    if(each_flw.get_priority() <= each_d_flw.get_priority()) and (self._intersects(each_d_flw, each_flw)>0):                            
                        subset.append(each_flw)
#                    else:
#                        print "---"
#                        pprint.pprint(each_flw)
#                        pprint.pprint(each_d_flw)
#                        print "---"
        return subset    
    
    
    # all traffic flows that :
    # - have higher (or equal) priority than the traffic in question
    # - share at least one link with the  traffic in question
    # - flows of child tasks will not interfere with flows of parent task - precedence constraints
    # - low pri values are higher priorities
    def getDirectInterferenceSet_withPrCnst(self, all_flows):
        #print "getDirectInterferenceSet_withPrCnst: enter : len(all_flows)=" + str(len(all_flows))
        subset = []
        
        subset_hashcodes = []
        
        ## debug
#         print "++++++++++"
#         print "all_flows::"
#         for eachf in all_flows:
#             print eachf.getFlowHashCode()
#         print "++++++++++"        
        ## debug
        
        for each_flw in all_flows:            
            if(self._equals_v2(self, each_flw) == False) and (each_flw.get_priority() <= self.get_priority()):
                if(self._intersects(each_flw, self) > 0):
                    if(self._isFlowAnInterferer_v2(each_flw) == True):
                        flw_hashcode = each_flw.getFlowHashCode() + "_" + str(each_flw.get_priority())
                        if(flw_hashcode not in subset_hashcodes):
                            subset.append(each_flw)
                            subset_hashcodes.append(flw_hashcode) # update
                        else: # flw already added to subset
                            i=1
                        
                
        return subset
    
    
    # all traffic flows that :
    # - have higher (or equal) priority than the traffics that interfere with the traffic in question
    # - don't share links with the  traffic in question
    # - flows of child tasks will not interfere with flows of parent task - precedence constraints
    def getIndirectInterferenceSet_withPrCnst(self, all_flows):
        #print "getIndirectInterferenceSet_withPrCnst: enter : len(all_flows)=" + str(len(all_flows))
        
        subset = []
        subset_hashcodes = []
        direct = self.getDirectInterferenceSet_withPrCnst(all_flows)
        
        for each_flw in all_flows:            
            if(self._equals_v2(self, each_flw) == False) and (each_flw not in direct):
                for each_d_flw in direct:
                    #print "getIndirectInterferenceSet:: here - 1"
                    if(each_flw.get_priority() <= each_d_flw.get_priority()) and (self._intersects(each_d_flw, each_flw)>0):
                        if(self._isFlowAnInterferer_v2(each_flw) == True):                            
                            flw_hashcode = each_flw.getFlowHashCode() + "_" + str(each_flw.get_priority())
                            if(flw_hashcode not in subset_hashcodes):
                                subset.append(each_flw)
                                subset_hashcodes.append(flw_hashcode) # update
                            else: # flw already added to subset
                                i=1
                        
        return subset
    
    
    ### INCORRECT !!!!
    # this checks the following conditions to determine if the given flow truly does interfer (w.r.t precedences):
    # - is the given flow's source task a parent or child of the current flows' source task    
    def _isFlowAnInterferer_v1(self, flow):
        
        result = True
        
        if(flow.get_type() == FlowType.FLOWTYPE_DATA):        
            Ti = self.get_respectiveSrcTask()
            Tj = flow.get_respectiveSrcTask()
            
            if(Ti.get_unique_gop_id() == Tj.get_unique_gop_id()):    # so they are in the same taskset, so maybe they don't intefere    
            
                Tj_childframes = Ti.get_children_frames()
                Tj_childframes = Tj.get_children_frames()
                
                # is the source task the same ? (because there can be more than one flow released by the same source task)
                if(Ti.get_id() != Tj.get_id()):               
                    # now find if the src tasks are child/parent            
                    if(Tj.get_frameIXinGOP() not in Ti.get_possible_interfering_frame()):
                        result = False             
        
        return result    
        
    
    def _isFlowAnInterferer_null(self, flow):
        return True
    
    def _isFlowAnInterferer(self, flow):
        
        if(flow.get_type() == FlowType.FLOWTYPE_DATA):      
        
            Ti = self.get_respectiveSrcTask()   
            Tj = flow.get_respectiveSrcTask()
            
            Ti_dst_ix = self.get_respectiveDstTaskId()   
            Tj_dst_ix = flow.get_respectiveDstTaskId()
            
            ## we can only do a easy test if the flow is to only 1 dst task        
            if(Ti.get_unique_gop_id() == Tj.get_unique_gop_id()):
                
                if(len(Ti_dst_ix) > 1) or (len(Tj_dst_ix) > 1):
                    return True
                else:
                
                
                    if( Ti_dst_ix[0] in [2, 3, 5, 6, 8, 9, 10, 11]): # if dst task is a B-frame
                        return True
                    elif(Tj_dst_ix[0] in [2, 3, 5, 6, 8, 9, 10, 11]): # if dst task is a B-frame
                        return True
                    else:
                        # if I0->P1 case : only interfers with anything from I0
                        if ((Ti.get_frameIXinGOP() == 0) and (Ti_dst_ix[0] == 1)) and \
                        (Tj.get_frameIXinGOP() != 0):
                                return False
                       
                        # P1->P4 vs. I0-> P1 case
                        elif ((Ti.get_frameIXinGOP() == 1) and (Ti_dst_ix[0] == 4)) and \
                        ((Tj.get_frameIXinGOP() == 0) and (Tj_dst_ix[0] == 1)):
                            return False
                        
                        # P1->P4 vs. any flow originating from P4, or P7
                        elif ((Ti.get_frameIXinGOP() == 1) and (Ti_dst_ix[0] == 4)) and \
                        (Tj.get_frameIXinGOP() in [4, 7]):
                            return False
                        
                        # P4->P7 vs. I0->P1 case
                        elif ((Ti.get_frameIXinGOP() == 4) and (Ti_dst_ix[0] == 7)) and \
                        ((Tj.get_frameIXinGOP() == 0) and (Tj_dst_ix[0] == 1)):
                            return False
                            
                        # P4->P7 vs. P1->P4 case
                        elif ((Ti.get_frameIXinGOP() == 4) and (Ti_dst_ix[0] == 7)) and \
                        ((Tj.get_frameIXinGOP() == 1) and (Tj_dst_ix[0] == 4)):
                            return False                    
                        
                        # P4->P7 vs. any flow originating from P7
                        elif ((Ti.get_frameIXinGOP() == 4) and (Ti_dst_ix[0] == 7)) and \
                        (Tj.get_frameIXinGOP() in [7]):
                            return False
                        
                        
                        # Any flow originating from P7 will not interfer with I0->P1
                        elif ((Ti.get_frameIXinGOP() == 7)) and \
                        ((Tj.get_frameIXinGOP() == 0) and (Tj_dst_ix[0] == 1)):
                            return False
                        
                        
                        # Any flow originating from P7 will not interfer with P1->P4
                        elif ((Ti.get_frameIXinGOP() == 7)) and \
                        ((Tj.get_frameIXinGOP() == 1) and (Tj_dst_ix[0] == 4)):
                            return False
                        
                        
                        # Any flow originating from P7 will not interfer with P4->P7
                        elif ((Ti.get_frameIXinGOP() == 7)) and \
                        ((Tj.get_frameIXinGOP() == 4) and (Tj_dst_ix[0] == 7)):
                            return False
                        
                        else:
                            return True                        
            else:
                return True
            
        else:
            return True
            
    
    
    # we are trying to see if 'flow' interferes with current flow
    def _isFlowAnInterferer_v2(self, flow):
        
        #print "_isFlowAnInterferer_v2:: Enter"
        
        ## if the flow is not a data flow then interference is TRUE
        if((flow.get_type() == FlowType.FLOWTYPE_DATA) and
           (self.get_type() == FlowType.FLOWTYPE_DATA)):
            
                # if the source and dest task is not set then throw error
                if((flow.get_respectiveSrcTask == None) or
                    (flow.get_respectiveDstTaskIx == None)):
                    sys.exit("Error: _isFlowAnInterferer_v2 :: Error - 1")
                            
                if((self.get_respectiveSrcTask == None) or
                    (self.get_respectiveDstTaskIx == None)):
                    sys.exit("Error: _isFlowAnInterferer_v2 :: Error - 2")
                
            
                Ti = self.get_respectiveSrcTask()   
                Tj = flow.get_respectiveSrcTask()
                
                Ti_src_ix =  Ti.get_frameIXinGOP()
                Tj_src_ix =  Tj.get_frameIXinGOP()
                
                Ti_dst_ids = self.get_respectiveDstTaskId()   
                Tj_dst_ids = flow.get_respectiveDstTaskId()
                
                Ti_dst_ixs = self.get_respectiveDstTaskIx()
                Tj_dst_ixs = flow.get_respectiveDstTaskIx()
                            
                # first check if flow is from the same gop - else inteference is TRUE        
                if(Ti.get_unique_gop_id() == Tj.get_unique_gop_id()):
                    
                    # source = I0
                    if(Ti_src_ix == 0):
                        # dest includes P1
                        if( len(set(Ti_dst_ixs) & set([1])) >0 ):                            
                            # if the other flow doest start with I0
                            if(Tj_src_ix != 0):
                                return False
                            else:
                                return True
                        # dest is a B-frame    
                        else:
                            return True
                    
                    
                    # source = P1
                    elif(Ti_src_ix == 1):
                        # dest includes P4
                        if( len(set(Ti_dst_ixs) & set([4])) >0 ):
                            # flow (I0->P1)
                            if(Tj_src_ix == 0) and (len(set(Tj_dst_ixs) & set([1]))>0):
                                return False
                            elif(Tj_src_ix in [4,7]): # any flow starting from P4/P7
                                return False
                            else:
                                return True
                            
                        # dest is a B-frame
                        else:
                            # flow (I0->P1)
                            if(Tj_src_ix == 0) and (len(set(Tj_dst_ixs) & set([1]))>0):
                                return False
                            else:
                                return True
                        
                    
                    
                    # source = P4
                    elif(Ti_src_ix == 4):
                        # dest includes P7
                        if( len(set(Ti_dst_ixs) & set([7])) >0 ):
                            # flows (I0->P1) 
                            if(Tj_src_ix == 0) and (len(set(Tj_dst_ixs) & set([1]))>0):
                                return False
                            # flows (P1->P4) 
                            elif( (Tj_src_ix == 1) and (len(set(Tj_dst_ixs) & set([4]))>0)): 
                                return False                            
                            # any flow starting from P7
                            elif(Tj_src_ix in [7]):
                                return False                            
                            else:
                                return True                        
                        
                        # dest is a B-frame
                        else:
                            # flow (I0->P1)
                            if(Tj_src_ix == 0) and (len(set(Tj_dst_ixs) & set([1]))>0):
                                return False
                            # flows (P1->P4) 
                            elif( (Tj_src_ix == 1) and (len(set(Tj_dst_ixs) & set([4]))>0)):
                                return False
                            else:
                                return True
                        
                    
                    # source = P7
                    elif(Ti_src_ix == 7):
                        # flows (I0->P1) 
                        if(Tj_src_ix == 0) and (len(set(Tj_dst_ixs) & set([1]))>0):
                            return False
                        # flows (P1->P4) 
                        elif( (Tj_src_ix == 1) and (len(set(Tj_dst_ixs) & set([4]))>0)): 
                            return False
                        # flows (P4->P7)  
                        elif( (Tj_src_ix == 4) and (len(set(Tj_dst_ixs) & set([7]))>0)):
                            return False
                        else:
                            return True
                    
                    
                    # flow cant start with any other frame
                    else:
                        print "Ti_src_ix : " + str(Ti_src_ix)
                        sys.exit("Error: _isFlowAnInterferer_v2 :: Error - 3")
                else:
                    return True
            
        else:
            return True
    
    
    
    
    # latency when no interference is present
    def getBasicLatency(self):
        
        cost = 0.0        
        num_flits = math.ceil(self.payload/SimParams.NOC_FLIT_BYTES)
        route = self.route
        num_hops = float(len(route))                
        
        # old version
        #cost = ((num_hops * SimParams.NOC_ARBITRATION_COST) + num_flits) * SimParams.NOC_PERIOD  
        
        routers = num_hops - 1
        cost = (float(num_hops) * SimParams.NOC_PERIOD) + \
                (float(routers) * SimParams.NOC_ARBITRATION_COST) + \
                (float(num_flits) * SimParams.NOC_PERIOD)
        
        
        # basiclatency = (hopLatency * hops) + (routingLatency * routers) + (hopLatency * (payload));    
        
        return cost
    
    @staticmethod
    def getCommunicationCost(payload, num_hops, noc_period, arb_cost):
        cost = 0.0        
        #num_flits = math.ceil(payload/SimParams.NOC_FLIT_BYTES)
        num_flits = math.ceil(payload/SimParams.NOC_FLIT_BYTES)
        
        # old version
        #cost = ((num_hops * arb_cost) + num_flits) * noc_period
        
        routers = num_hops - 1
        cost = (float(num_hops) * noc_period) + \
                (float(routers) * arb_cost) + \
                (float(num_flits) * noc_period)  
        
        return cost
        
        
    # calculates the worst case communication latency only considering the direct interference
    def getDirectInterferenceWorstCaseLatency(self, all_flows):
        
        wl = self.getBasicLatency()
        sdi = self.getDirectInterferenceSet_withPrCnst(all_flows)
                
        wlcopy = 0.0
        while((wl != wlcopy) and (wl <= self.get_period())):
            wlcopy = wl
            interf = 0.0
    
            for each_sdi in sdi:
                flowj = each_sdi
                mult = 0.0
                # Previous WC + release jitter (of the higher priority flow)
                mult = math.ceil((wlcopy+flowj.get_releaseJitter())/flowj.get_period())
                # Finds the number of times the higher priority flow "hits" this flow
                interf +=  (mult * (1000000000.0 * flowj.getBasicLatency()))
            
            # The current iteration is the sum of all interferences + the computation time of the current flow
            wl = ((1000000000.0 * self.getBasicLatency()) + interf)/1000000000.0
            
        # Add to the worst-case the release jitter of the task
        # This defines the actual response-time of the task
        wl += self.get_releaseJitter()
                
        # considering deadline = period
#        if(wl > self.get_period()):
#            return sys.float_info.max
        
        return wl
        
        
        
    
    
    # calculates the worst case communication latency due to direct and indirect interference
    def getWorstCaseLatency(self, all_flows, timeout, recur_depth=None):
        
        #print "getWorstCaseLatency: Enter"
        
        if(SimParams.WCRT_FLOW_USE_LIMITED_RECURSION_DEPTH == True):
            if (recur_depth != None and recur_depth>SimParams.WCRT_FLOW_CALC_MAX_RECURSION_DEPTH):
                return 0.0
            else:
                #print recur_depth
                jj=0
                
        elif(SimParams.WCRT_FLOW_USE_TIMEOUT == True):            
            if timeout != None:
                if datetime.utcnow() > timeout: # if too much time has elapsed then timeout and return zero
                    #print "getWorstCaseLatency: TIMEOUT!"
                    return 0.0
        else:
            x=0 # in trouble..
        
        # possible base case ? if this.priority is higher than all the others, then return basic latency
        flag = True
        for each_flw in all_flows:
            if(each_flw.get_priority() < self.get_priority()):  # lower values are higher
                flag = False
                break            
        
        if(flag == True):
            return self.getBasicLatency() + self.get_releaseJitter()
        else:
        
            wl = self.getBasicLatency()
            sdi = self.getDirectInterferenceSet_withPrCnst(all_flows)
            sii = self.getIndirectInterferenceSet_withPrCnst(all_flows)   
            
            
# #             ## debug ##
#             print "----------------"
#             print "target_flow = " + self.getFlowHashCode() + ", " + "+".join([r.__repr__() for r in self.get_route()]) + ", " + str(self.get_priority())  + ", " + \
#                         str(self.get_payload_metadata()['wf_id']) + ", " + str(self.get_payload_metadata()['vid_strm_id']) + ", " + str(self.get_payload_metadata()['gop_ix'])
#      
#             print "sdi flows"            
#             for each_sdi in sdi:
#                 print each_sdi.getFlowHashCode() + ", " + "+".join([r.__repr__() for r in each_sdi.get_route()]) + ", " + str(each_sdi.get_priority()) + ", " + \
#                         str(each_sdi.get_payload_metadata()['wf_id']) + ", " + str(each_sdi.get_payload_metadata()['vid_strm_id']) + ", " + str(each_sdi.get_payload_metadata()['gop_ix'])
#      
#             print "----------------"
# #             ## debug ##
            
                     
            
            if(len(sdi) == 0):
                return wl + self.get_releaseJitter()
            
            else:
                flows = {}
                
                for each_sdi in sdi:
                    sdj = each_sdi.getDirectInterferenceSet_withPrCnst(sii)
                    
                    if(len(sdj)>0):
                        # If there is indirect interference, calculate it:
                        # worst-case response time for the flow minus its basic latency
                        recur_depth +=1                        
                        flows[each_sdi.get_id()] = each_sdi.getWorstCaseLatency(all_flows, timeout, recur_depth=recur_depth) - each_sdi.getBasicLatency()
                    else:
                        flows[each_sdi.get_id()] = 0.0        
                
                wlcopy = 0.0
                while((wl != wlcopy) and (wl <= self.get_period())):
                    wlcopy = wl
                    interf = 0.0
                    
                    for each_sdi in sdi:
                        flowj = each_sdi
                        
                        mult = 0.0
                        jitter = flows[flowj.get_id()]
                        
#                         print "jitter = " + str(jitter)
#                         print "flowj.get_releaseJitter()=" + str(flowj.get_releaseJitter())                        
#                         print "flowj.get_respectiveSrcTaskId()=" + str(flowj.get_respectiveSrcTaskId())
#                         print "flowj.get_respectiveDstTaskIx()=" + str(flowj.get_respectiveDstTaskIx())
#                         print "flowj.get_respectiveDstTaskId()=" + str(flowj.get_respectiveDstTaskId())
#                         print "flowj.get_type()=" + str(flowj.get_type())
                        
                        if(flowj.get_type()==FlowType.FLOWTYPE_MMCTONODE_DATATRANSFER_RD and flowj.get_releaseJitter() == None):
                            flowj.set_releaseJitter(0.0)
                        #elif(flowj.get_type()==FlowType.FLOWTYPE_MMCTONODE_DATATRANSFER_WR):
                        #    flowj.set_releaseJitter()
                                                             
                        mult = math.ceil((wlcopy+flowj.get_releaseJitter() + jitter)/flowj.get_period())
                        interf +=  (mult * (1000000000.0 * flowj.getBasicLatency()))
                    
                    wl = ((1000000000.0 * self.getBasicLatency()) + interf)/1000000000.0
                
                wl += self.get_releaseJitter()
                
                # considering deadline = period
#                if(wl > self.get_period()):
#                    return sys.float_info.max
                
                return wl
        
      
        
    
    def _intersects(self, flow1, flow2):
        route_links1 = set(flow1.route)
        route_links2 = set(flow2.route)
        intersecting_links = list(route_links1.intersection(route_links2))
        
# --testing-----------------------------------------------------------------------
#         if (len(intersecting_links) >0) and (len(intersecting_links) < 2): 
#             print "------"
#             print flow1.route
#             print flow2.route
#             print "------"
## --------------------------------------------------------------------------------        
        return len(intersecting_links)
    
    def _equals(self, f2):        
        if(self.get_respectiveSrcTaskId() == f2.get_respectiveSrcTaskId()) and \
        (set(self.get_respectiveDstTaskId()) == set(f2.get_respectiveDstTaskId())) and \
        (self.get_source() == f2.get_source()) and \
        (self.get_route() == f2.get_route()):
            return True
        else:
            return False

    @staticmethod
    def _equals_v2(f1, f2):
        if((f1.get_priority() == f2.get_priority()) and
            (f1.getFlowHashCode() == f2.getFlowHashCode())):
            return True
        else:
            return False
    
####################################
# To manage different types of flows
####################################
class FlowType:
    FLOWTYPE_UNKNOWN                                    = 0
    FLOWTYPE_DATA                                       = 1 # PE to PE
    FLOWTYPE_PSALGOSIGNALLING                           = 2 # PE to PE
    FLOWTYPE_PSALGOSIGNALLING_QUEENSTAT_REQ             = 3 # PE to Queen
    FLOWTYPE_PSALGOSIGNALLING_QUEENSTAT_REP             = 4 # Queen to PE
    FLOWTYPE_MASTERSLAVESIGNALLING                      = 5 
    FLOWTYPE_MASTERSLAVESIGNALLING_TASKCOMPLETE         = 6 # PE to RM 
    FLOWTYPE_MASTERSLAVESIGNALLING_FLOWCOMPLETE         = 7 # PE to RM
    FLOWTYPE_MMCTONODE_DATATRANSFER_RD                  = 8 # MMC to PE (RD)
    FLOWTYPE_MMCTONODE_DATATRANSFER_WR                  = 9 # PE to MMC (WR)
    FLOWTYPE_REMAPPING_NOTIFY_DISPATCHER                = 10 # PE to RM
    FLOWTYPE_CCP_SN_CM_UPDATE_TASKCOMPLETE              = 11 # CC protocol, slave to CM update about task completion
    FLOWTYPE_CCP_LOANREQUEST                            = 12 # CC protocol, CM --> other CMs, loan request
    FLOWTYPE_CCP_LOANDELIVERY                           = 13 # CC protocol, other CMs --> CM, loan delivery
    FLOWTYPE_CCP_LOANRELEASE                            = 14 # CC protocol, CM --> other CMs, loan release    
    FLOWTYPE_DATA_HEVC                                  = 15 # hevc data deps
        
    
    
