import pprint
import sys
import itertools
import simpy
import math, random
from operator import itemgetter
import numpy as np


from SimParams import SimParams
from libDebug.Debug import Debug, DebugCat
from libNoCModel.NoCFlow import NoCFlow, FlowType
from libMappingAndScheduling.Decentralised.PSAlgorithmViewer import PSAlgorithmViewer


#############################################################################################
## PS Algo main class
#############################################################################################
    
class PSAlgorithm:
    
    def __init__(self, env, RMInstance):
        self.label = "PSAlgorithm"
        self.env = env
        self.RMInstance = RMInstance
                
        self.process_instance_rundiff = None
        self.process_instance_rundecay = None
        
        self.psalgo_started = False
        self.psalgo_start_time = 0.0
        
        # ps algo viewer
        self.psalgoviewer = PSAlgorithmViewer(self.env, self.RMInstance)
        
        # tracking related
        self.track_nodepsprops = []
        self.track_propcycles = []
        self.track_decaycycles = []
                
    # initialise algorithm
    def init(self):        
        if(SimParams.PSALGO_ENABLED == True):
            #self.setInitialQueenNodes()                
            self.process_instance_rundiff = self.env.process(self.runPSDifferentiation())
            self.process_instance_rundecay = self.env.process(self.runPSDecay())
            
            # tracking snapshot
            self.process_snapshot = self.env.process(self.track_NodePSProps())
            
            self.psalgo_started = True
            self.psalgo_start_time = self.env.now
    
    
    def conditionalInit(self):
        if(self.psalgo_started == False):
            self.init()
            self.psalgoviewer.init()
        else:
            i=1
            

       
    
    def setInitialQueenNodes(self):
        Debug.PPrint("%f"%self.env.now + "," + self.label + "," + "setInitialQueenNodes::," + "Enter", DebugCat.DEBUG_CAT_PSALGO)
        
        if(SimParams.PSALGO_INITQNCOUNT > SimParams.NUM_NODES):
            sys.exit("setInitialQueenNodes:: Error")
        else:
            #random_node_ids = np.random.randint(0, high=len(self.RMInstance.node_network.get_Nodes())-1, size=SimParams.PSALGO_INITQNCOUNT)
            random_qn_ids = SimParams.PSALGO_HARDCODE_QN_LOCATIONS            
            for each_node_id in random_qn_ids:
                each_node = self.RMInstance.node_network.get_Nodes()[each_node_id]                
                each_node.psalgoprops.node_type = PSAlgorithmNodetype.QUEEN_BEE
                
                # what type of hormone to use ? fixed/dynamic (e.g. based on slacks ?)                
                each_node.psalgoprops.pheramone_level = SimParams.PSALGO_INITIALHORMONEAMNT_QUEEN
                
    
                
    def initialQNSelectionandHormonePropagation(self):
        Debug.PPrint("%f"%self.env.now + "," + self.label + "," + "initialQNSelectionandHormonePropagation::," + "Enter", DebugCat.DEBUG_CAT_PSALGO)
        
        # find nodes with initial queen status
        initial_queen_nodes = [each_node for each_node in self.RMInstance.node_network.get_Nodes() 
                               if (each_node.psalgoprops.node_type == PSAlgorithmNodetype.QUEEN_BEE)]
        
        num_flows_added = []
        for each_node in initial_queen_nodes:
            each_node.psalgoprops.node_type = PSAlgorithmNodetype.QUEEN_BEE
            each_node.psalgoprops.track_qn_count +=1
            each_node.psalgoprops.pheramone_level = SimParams.PSALGO_INITIALHORMONEAMNT_QUEEN
    
            # now propagate hormone to neighbours        
            dose = {"qn_hop_distance": 0, "p_dose": SimParams.PSALGO_HQN, 'qn_pos': each_node.get_id()}
            temp_num_flows_added = each_node.psalgoprops.broadcastToNeighbours(dose)
            num_flows_added.extend(temp_num_flows_added)
                
        # update the table (one update for all)
        if(len(num_flows_added) > 0):
            self.RMInstance.flow_table.updateTable(fire=True)   # one update for many additions 
                
  
    # PS Differentiation Cycle - TIME-TRIGGERED
    def runPSDifferentiation(self): 
        Debug.PPrint("%f"%self.env.now + "," + self.label + "," + "runPSDifferentiation::," + "Enter", DebugCat.DEBUG_CAT_PSALGO)       
        while True:
            Debug.PPrint("%f"%self.env.now + "," + self.label + "," + "runPSDifferentiation::," + "new cycle", DebugCat.DEBUG_CAT_PSALGO)
            self.track_propcycles.append(self.env.now)
            if(self.env.now > self.psalgo_start_time):            
                # run the ps propagation for every node
                for each_node in self.RMInstance.node_network.get_Nodes():
                    each_node.psalgoprops.cycleDifferentiation()
            
                # one update for all of the above
                self.RMInstance.flow_table.updateTable(fire=True)
            
            # first simulation time unit
            else:
                self.initialQNSelectionandHormonePropagation()
                
            # wait for TQN seconds
            yield self.env.timeout(SimParams.PSALGO_TQN)            
            #self.track_NodePSProps()
            
            # update ps-viewer
            #self.RMInstance.PSAlgoViewer.updatePlevel()
   
    # PS Hormone Decay Cycle - TIME-TRIGGERED
    def runPSDecay(self):
        Debug.PPrint("%f"%self.env.now + "," + self.label + "," + "runPSDecay::," + "Enter", DebugCat.DEBUG_CAT_PSALGO)
        while True:
            Debug.PPrint("%f"%self.env.now + "," + self.label + "," + "runPSDecay::," + "new cycle", DebugCat.DEBUG_CAT_PSALGO)
            self.track_decaycycles.append(self.env.now)
            if(self.env.now > self.psalgo_start_time): 
                # run the decay cycle for every node
                for each_node in self.RMInstance.node_network.get_Nodes():
                    each_node.psalgoprops.cycleDecay()
            
            # wait for TDECAY seconds
            yield self.env.timeout(SimParams.PSALGO_TDECAY)
            
            # update ps-viewer
            #self.RMInstance.PSAlgoViewer.updatePlevel()
    
    ########################################################
    ## tracking related
    ########################################################
    def track_NodePSProps(self):
        
        if(SimParams.TRACK_PSALGO_SNAPSHOT == True):
            while True:
                all_nodes_entry = []
                for each_node in self.RMInstance.node_network.get_Nodes():
                    single_node_entry = {
                              "t" : self.env.now,
                              "nid" : each_node.get_id(),
                              "plevel" : each_node.psalgoprops.pheramone_level,
                              "ntype" : each_node.psalgoprops.node_type,
                              "qncount" : each_node.psalgoprops.track_qn_count,
                              "thrqn" : each_node.psalgoprops.threshold_qn
                              }
                    
                    all_nodes_entry.append(single_node_entry)
                self.track_nodepsprops.append(all_nodes_entry)
                
                # wait before continuing
                yield self.env.timeout(SimParams.PSALGO_MONITOR_SNAPSHOT_PERIOD)
    
    
    
    

#############################################################################################
## PSAlgorithmProps : essential properties of the ps algo
#############################################################################################
class PSAlgorithmProps:
    
    def __init__(self, env, node):
        
        self.label = "PSAlgorithmProps"
        self.env = env
        self.node = node
        self.pheramone_level = float(SimParams.PSALGO_INITIALHORMONEAMNT_WORKER)  # initial hormone amount
        self.node_type = PSAlgorithmNodetype.WORKER_BEE
        self.nearest_queens_list = {}
        self.threshold_qn = float(SimParams.PSALGO_THRESHOLDQN)
        
        # irrelevant
        self.lifetime = 0.0 # needed ??
        
        # for tracking
        self.track_qn_count = 0
        self.track_cycledecay = []
        self.track_cycleDiff = []
    
    
    ## getters
    def get_pheramone_level(self):
        return self.pheramone_level
    def get_node_type(self):
        return self.node_type
    def get_nearest_queens_list(self):
        return self.nearest_queens_list
    def get_nearest_queen_pos(self):
        q_pos = [each_q['qn_pos'] for each_q in self.nearest_queens_list.values()]
        return q_pos
    def get_qn_count(self):
        return self.track_qn_count
    def get_threshold_qn(self):
        return self.threshold_qn
    
    ## setters
    def set_pheramone_level(self, pl):
        self.pheramone_level = pl        
    def set_node_type(self, nt):
        self.node_type = nt
        
        
    
    
    ## debug
    def __repr__(self):        
        debug = "<PSAlgoProp "
        debug += " nid=" + str(self.node.get_id())
        debug += " plvl=" + str(self.pheramone_level)
        debug += " ntype=" + str(self.node_type)
        debug += " />"
        
        return debug
    
    # Pheramone propagation cycle (spread pheramone to others) - EVENT-TRIGGERED
    # triggered when the pheromone dose is received
    def cyclePSPropagation(self, hd):
        Debug.PPrint("%f"%self.env.now + "," + self.label + "," + "cyclePSPropagation::," + "Enter", DebugCat.DEBUG_CAT_PSALGO)
        if(hd["qn_hop_distance"] < SimParams.PSALGO_THRESHOLDHOPCOUNT):
            self.pheramone_level += float(hd["p_dose"])    # receive new hormone dose
            self.updateNearestQueenList(hd) # update the queen list
            # broadcast
            new_hd = {"qn_hop_distance" : hd["qn_hop_distance"]+1, 
                      "p_dose" : float(hd["p_dose"]*SimParams.PSALGO_KHOPDECAY), 
                      'qn_pos': hd['qn_pos'],
                      "qn_tq_info" : hd['qn_tq_info'],
                      "node_traversal" : hd["node_traversal"] + [self.node.get_id()]
                      }
            
            # only send out a new hormone to neighbours if the hop count is below threshold
            if(new_hd["qn_hop_distance"] < SimParams.PSALGO_THRESHOLDHOPCOUNT):           
                num_flows_added = self.broadcastToNeighbours(new_hd)
                # update the table
                if(len(num_flows_added) > 0):
                    self.node.resource_manager_instance.flow_table.updateTable(fire=True)   # one update for many additions        
        else:
            # do nothing
            i=1
    
    # Pheramone differentiation (decide if node type is going to change) - TIME-TRIGGERED
    def cycleDifferentiation(self):        
        Debug.PPrint("%f"%self.env.now + "," + self.label + "," + "cycleDifferentiation::," + "Enter", DebugCat.DEBUG_CAT_PSALGO)
        self.clearNearestQueenList()
                
        # establish threshold - either dynamic or static
        if(SimParams.PSALGO_DYNAMIC_THRESHOLDQN_ENABLED == True):   # dynamic         
            #normalised_cum_slack = self.node.calculate_SystemSlack_viaTQ()
            normalised_cum_slack = self.node.calculate_SystemSlack_wrt_est_relD(normalised=True)
                    
            if(normalised_cum_slack>0): # increase
                # if normalised cumulative slack is larger than zero we increase the threshold
                self.threshold_qn = float(self.threshold_qn) * float(1.0+float(normalised_cum_slack*SimParams.PSALGO_DYNAMIC_THRESHOLDQN_RATIO[0]))
                
                # in case ph level is zero
                if self.pheramone_level == 0:
                    self.pheramone_level = 0.000001
                    
                if(float(self.threshold_qn)/float(self.pheramone_level)) > 10.0:
                        self.threshold_qn = float(self.pheramone_level) * 10.0
                        
            else: # decrease
                self.threshold_qn = self.pheramone_level * SimParams.PSALGO_DYNAMIC_THRESHOLDQN_RATIO[1] # definitely do not become a queen
            
        else:   # static
            self.threshold_qn = self.threshold_qn
       
        # differentiate if queen/worker
        if (self.pheramone_level < self.threshold_qn):
            self.node_type = PSAlgorithmNodetype.QUEEN_BEE
            self.track_qn_count += 1
            # set hormone level for a queen
            #self.pheramone_level = SimParams.PSALGO_INITIALHORMONEAMNT_QUEEN           
            # broadcast
            dose = {
                    "qn_hop_distance" : 0, 
                    "p_dose" : SimParams.PSALGO_HQN, 
                    "qn_pos" : self.node.get_id(),
                    "qn_tq_info" : [t for t in self.node.get_SystemSlack_MappedTasks()],
                    "node_traversal" : [self.node.get_id()] 
                    }
            self.broadcastToNeighbours(dose)
        else:
            self.node_type = PSAlgorithmNodetype.WORKER_BEE
        
        self.track_cycleDiff.append(
                                    {
                                     'time' : self.env.now,
                                     'latenessinfo' : self.node.min_max_avg_TaskLatenessinTQ_KG() 
                                     }
                                    )

    
#    # Pheramone differentiation (decide if node type is going to change) - TIME-TRIGGERED
#    def cycleDifferentiation(self):        
#        Debug.PPrint("%f"%self.env.now + "," + self.label + "," + "cycleDifferentiation::," + "Enter", DebugCat.DEBUG_CAT_PSALGO)
#        self.clearNearestQueenList()
#                
#        # establish threshold - either dynamic or static
#        if(SimParams.PSALGO_DYNAMIC_THRESHOLDQN_ENABLED == True):   # static         
#            normalised_cum_slack = self.node.calculate_SystemSlack(normalised=True, return_all_norm_cumslack_list=True)
#            proportion_of_late_tasks_in_tq = self.node.proportionOfLateTasksInTQ(lateness_ratio=SimParams.DYNAMIC_TASK_REMAPPING_TASK_LATE_ESTIM_LATENESS_RATIO)
#            if(len(normalised_cum_slack)>1):
#                self.threshold_qn = self._getDynamicThresholdQN(normalised_cum_slack[-1], normalised_cum_slack[-2], proportion_of_late_tasks_in_tq)
#            else:
#                self.threshold_qn = self._getDynamicThresholdQN(normalised_cum_slack[-1], 0.0, proportion_of_late_tasks_in_tq)
#                
#        else:   # static
#            self.threshold_qn = self.threshold_qn
#       
#        # differentiate if queen/worker
#        if (self.pheramone_level < self.threshold_qn):
#            self.node_type = PSAlgorithmNodetype.QUEEN_BEE
#            self.track_qn_count += 1
#            # set hormone level for a queen
#            #self.pheramone_level = SimParams.PSALGO_INITIALHORMONEAMNT_QUEEN           
#            # broadcast
#            dose = {
#                    "qn_hop_distance" : 0, 
#                    "p_dose" : SimParams.PSALGO_HQN, 
#                    "qn_pos" : self.node.get_id(),
#                    "qn_tq_info" : [t for t in self.node.get_SystemSlack_MappedTasks()] 
#                    }
#            self.broadcastToNeighbours(dose)
#        else:
#            self.node_type = PSAlgorithmNodetype.WORKER_BEE
#        
#        self.track_cycleDiff.append(
#                                    {
#                                     'time' : self.env.now,
#                                     'latenessinfo' : self.node.min_max_avg_TaskLatenessinTQ_KG() 
#                                     }
#                                    )
    
    
            
    # periodic decay of the pheramone level of each node  - TIME-TRIGGERED      
    def cycleDecay(self):
        Debug.PPrint("%f"%self.env.now + "," + self.label + "," + "cycleDecay::," + "Enter", DebugCat.DEBUG_CAT_PSALGO)
        
        if(SimParams.PSALGO_DYNAMIC_KTIMEDECAY_ENABLED == True):    # dynamic
            normalised_cum_slack = self.node.calculate_SystemSlack(normalised=True)
            reduction_ratio = self._getDynamicKTimedDecayRatio(normalised_cum_slack)     
                
            self.pheramone_level = float(float(self.pheramone_level) * reduction_ratio)  
            self.track_cycledecay.append(
                                         {
                                          'norm_slack':normalised_cum_slack,
                                          'red_ratio' : reduction_ratio
                                          }                                     
                                         )
        else: # static
            self.pheramone_level = float(float(self.pheramone_level) * SimParams.PSALGO_KTIMEDECAY)
            
              
    
    def broadcastToNeighbours(self, dose):
        Debug.PPrint("%f"%self.env.now + "," + self.label + "," + "broadcastToNeighbours::," + "Enter", DebugCat.DEBUG_CAT_PSALGO)       
        #pprint.pprint(dose)
        
        neighbours = self.node.resource_manager_instance.interconnect.getNeighbours(self.node.get_id())
        
        if(SimParams.PSALGO_LIMIT_HORMONE_PROPAGATION == True):
            nodes_in_hormone_traversal_list = dose["node_traversal"]
        else:
            nodes_in_hormone_traversal_list = []
        
        num_flows_added = []        
        for neighbour_direction, each_neighbour_node_id in neighbours.iteritems():
            if(each_neighbour_node_id != None):
                if each_neighbour_node_id not in nodes_in_hormone_traversal_list:
                    each_neighbour = self.node.resource_manager_instance.node_network.get_Nodes()[each_neighbour_node_id]
                    #each_neighbour.psalgoprops.cyclePSPropagation(dose)
                    
                    #if(each_neighbour.psalgoprops.get_node_type() != PSAlgorithmNodetype.QUEEN_BEE):
                    # construct and add signal communication to flow table
                    (newpsflow, bl) = self.constructPSFlow(dose, each_neighbour.get_id())
                    # add to the flow table
                    self.node.resource_manager_instance.flow_table.addFlow(newpsflow, self.env.now, bl)                        
                    num_flows_added.append(newpsflow.get_id())
        
        return num_flows_added
        
    
    def constructPSFlow(self, dose, neighbour_node_id):
        
        # construct new flow        
        src_nodeid = self.node.get_id()
        dst_nodeid = neighbour_node_id
        nextid = self.node.resource_manager_instance.flow_table.nextid                    
        route = self.node.resource_manager_instance.interconnect.getRouteXY(src_nodeid, dst_nodeid)
        priority = SimParams.PSALGO_FLOWBASEPRIORITY + nextid
        #priority = nextid
        basicLatency = self.node.resource_manager_instance.interconnect.getRouteCostXY(src_nodeid, 
                                                                                       dst_nodeid,
                                                                                       SimParams.PSALGO_PSFLOWPAYLOADSIZE)
        relase_time = self.env.now
        payload = SimParams.PSALGO_PSFLOWPAYLOADSIZE
        endTime_wrt_BL = relase_time + basicLatency
        payload_metadata  = {'ps_hd' : dose }     # ps-dose information   
        
        newflow = NoCFlow(nextid,
                          None, None, None, None,
                          src_nodeid, dst_nodeid, route,
                          priority, 
                          None, 
                          basicLatency, payload, endTime_wrt_BL, 
                          type=FlowType.FLOWTYPE_PSALGOSIGNALLING,
                          payload_metadata=payload_metadata)        
        
        return (newflow, basicLatency)
         
        
    def updateNearestQueenList(self, dose):        
        # which queen sent this ph dose ?
        src_queen_node_id = dose['qn_pos']
        src_queen_tq_info = dose['qn_tq_info']
        src_queen_key = dose['qn_pos']
                
        # check and add to queen list
        if( (src_queen_node_id not in self.nearest_queens_list) and
            (src_queen_node_id != self.node.get_id()) 
            ): 
        
            new_q_entry = {
                     'update_time' : self.env.now,
                     'qn_pos' : src_queen_node_id,
                     'qn_tq_info' :  src_queen_tq_info,
                     }
            self.nearest_queens_list[src_queen_key] = new_q_entry

    
    def clearNearestQueenList(self):
        self.nearest_queens_list = {}
        
            
    
    
    def _getDynamicKTimedDecayRatio(self, normalised_cum_slack):
        reduction_ratio = 0.0
        if (normalised_cum_slack > 0.0):
            if(normalised_cum_slack >=1.0): # this should be an error !!                
                sys.exit("PSAlgorithmProps::_getDynamicKTimedDecayRatio:Error - normalised cum slack is > 1")
            else:   # between 0 and 1 (normal operation - node has some slack !)
                reduction_ratio = float((SimParams.PSALGO_KTIMEDECAY) * float(1.0-normalised_cum_slack))
        
        elif (normalised_cum_slack < 0.0): # negative, therefore increase pheromone or keep constant, hence decrease chance of becoming queen            
            reduction_ratio = 1.0
                      
        elif (normalised_cum_slack == 0.0):
            reduction_ratio = normalised_cum_slack
            
        else: 
            print "normalised_cum_slack=" + str(normalised_cum_slack)
            sys.exit("PSAlgorithmProps::_getDynamicKTimedDecayRatio:Error - strange normalised_cum_slack")
        
        return reduction_ratio
        
#    def _getDynamicThresholdQN(self, current_normalised_cum_slack, prev_normalised_cum_slack):
#        thresholdQN = 0.0
#        if (normalised_cum_slack > 0.0):
#            if(normalised_cum_slack >=1.0): # this should be an error !!
#                sys.exit("PSAlgorithmProps::_getThresholdQNRatio:Error - normalised cum slack is > 1")
#            else: # between 0 and 1 (normal operation - node has some slack ! hence increase the threshold)
#                thresholdQN = float(self.threshold_qn * float(1.0+normalised_cum_slack)) 
#                #thresholdQN = float(self.threshold_qn * 1.1)
#        elif (normalised_cum_slack < 0.0): # there is a negative slack, hence decrease the threshold
#            if (normalised_cum_slack > -1.0): # node is over-utilised
#                thresholdQN = float(self.threshold_qn * float(1.0-normalised_cum_slack))             
#            else: # node is super over-utilised, but maybe so are the others ?
#                thresholdQN = float(self.threshold_qn * 0.9)
#            
#                
#        elif (normalised_cum_slack == 0.0):            
#            thresholdQN = self.threshold_qn
#            
#        else: 
#            print "normalised_cum_slack=" + str(normalised_cum_slack)
#            sys.exit("PSAlgorithmProps::_getDynamicThresholdQN:Error - strange normalised_cum_slack")
#        
#        return round(thresholdQN,2)
    
    
    
    def _getDynamicThresholdQN(self, current_normalised_cum_slack, prev_normalised_cum_slack, proportion_of_late_tasks_in_tq):
        thresholdQN = 0.0
        
        if (current_normalised_cum_slack > 0.0):
            if(current_normalised_cum_slack >=1.0): # this should be an error !!
                sys.exit("PSAlgorithmProps::_getThresholdQNRatio:Error - normalised cum slack is > 1")
            else: # between 0 and 1 (normal operation - node has some slack ! hence increase the threshold)
                thresholdQN = float(float(self.threshold_qn) * float(SimParams.PSALGO_DYNAMIC_THRESHOLDQN_RATIO[1])) 
                #thresholdQN = float(self.threshold_qn * 1.1)
                
        elif (current_normalised_cum_slack < 0.0): # there is a negative slack, hence decrease the threshold
            thresholdQN = float(float(self.threshold_qn) * float(SimParams.PSALGO_DYNAMIC_THRESHOLDQN_RATIO[0])) 
            
            
#            # if more than xx% of the tasks are late, then we start to treat the cumslack in a different way
#            if(proportion_of_late_tasks_in_tq > 0.7):
#                delta = current_normalised_cum_slack - prev_normalised_cum_slack
#                if (np.abs(delta)>1.0): 
#                    delta = 1.0 # cap the delta to 1
#                
#                if(delta>0.0):  # positive
#                    thresholdQN = float(float(self.threshold_qn) * float(1.0+np.abs(delta)))
#                else: # negative
#                    thresholdQN = float(float(self.threshold_qn) * float(1.0-np.abs(delta)))
#            else:
#                thresholdQN = float(float(self.threshold_qn) * SimParams.PSALGO_DYNAMIC_THRESHOLDQN_RATIO[0])
                
                
        elif (current_normalised_cum_slack == 0.0):            
            thresholdQN = self.threshold_qn
            
        else: 
            print "normalised_cum_slack=" + str(current_normalised_cum_slack)
            sys.exit("PSAlgorithmProps::_getDynamicThresholdQN:Error - strange normalised_cum_slack")
        
        return round(thresholdQN,2)
    
    
    
    # send status request to all queens in list
    def sendQueenStatusMessageRequest(self, q_list):
        if len(q_list) > 0:
            for each_q_node_id in q_list:
                
                # construct new flow        
                src_nodeid = self.node.get_id()
                dst_nodeid = each_q_node_id
                nextid = self.node.resource_manager_instance.flow_table.nextid                    
                route = self.node.resource_manager_instance.interconnect.getRouteXY(src_nodeid, dst_nodeid)
                priority = SimParams.PSALGO_FLOWBASEPRIORITY + nextid
                #priority = nextid
                basicLatency = self.node.resource_manager_instance.interconnect.getRouteCostXY(src_nodeid, 
                                                                                               dst_nodeid,
                                                                                               1) # 1 byte
                relase_time = self.env.now
                payload = 1 # 1 byte
                endTime_wrt_BL = relase_time + basicLatency
                payload_metadata  = {'worker_node_id' : self.node.get_id() }     # some info about queen remapping status   
                
                newflow = NoCFlow(nextid,
                                  None, None, None, None,
                                  src_nodeid, dst_nodeid, route,
                                  priority, 
                                  None, 
                                  basicLatency, payload, endTime_wrt_BL, 
                                  type=FlowType.FLOWTYPE_PSALGOSIGNALLING_QUEENSTAT_REQ,
                                  payload_metadata=payload_metadata)        
                
                
                self.node.lock_RM_FLWtbl()        
                # add to the flow table        
                self.node.resource_manager_instance.flow_table.addFlow(newflow, self.env.now, basicLatency)
                self.node.release_RM_FLWtbl()        
            
            # update the table        
            self.node.resource_manager_instance.flow_table.updateTable(fire=True)
    
    
    
    
    # once a queen status remapping status req message is received, send a reply
    def receivedQueenStatusMessageRequest(self, flw_payload):
        # construct new flow        
        src_nodeid = self.node.get_id()
        dst_nodeid = flw_payload.get_payload_metadata()['worker_node_id']
        nextid = self.node.resource_manager_instance.flow_table.nextid                    
        route = self.node.resource_manager_instance.interconnect.getRouteXY(src_nodeid, dst_nodeid)
        priority = SimParams.PSALGO_FLOWBASEPRIORITY + nextid
        #priority = nextid
        basicLatency = self.node.resource_manager_instance.interconnect.getRouteCostXY(src_nodeid, 
                                                                                       dst_nodeid,
                                                                                       1) # 1 byte
        relase_time = self.env.now
        payload = 1 # 1 byte
        endTime_wrt_BL = relase_time + basicLatency
        payload_metadata  = {'null' : None }     # some info about queen remapping status   
        
        newflow = NoCFlow(nextid,
                          None, None, None, None,
                          src_nodeid, dst_nodeid, route,
                          priority, 
                          None, 
                          basicLatency, payload, endTime_wrt_BL, 
                          type=FlowType.FLOWTYPE_PSALGOSIGNALLING_QUEENSTAT_REP,
                          payload_metadata=payload_metadata)    
        
        self.node.lock_RM_FLWtbl()        
        # add to the flow table        
        self.node.resource_manager_instance.flow_table.addFlow(newflow, self.env.now, basicLatency)
        self.node.release_RM_FLWtbl()        
        
        # update the table        
        self.node.resource_manager_instance.flow_table.updateTable(fire=True)
            
    
    
    
    
    
    
#############################################################################################
## PSAlgorithmProps : node types
#############################################################################################

class PSAlgorithmNodetype:
    
    NONE        = 0    
    WORKER_BEE  = 1
    QUEEN_BEE   = 2
    