import pprint
import sys
#import networkx as nx
import simpy
import matplotlib.pyplot as plt

## local imports
from SimParams import SimParams


class NoCFlowTableEntry:
    
    def __init__(self, env, flow, releaseTime):
        
        self.env = env
        self.flow = flow
        self.releaseTime = releaseTime
        self.active = False
        self.lastActivationTime = 0.0
        self.remainingTime = 0.0
        self.waitsFor = {}  # a dict of flowentries
        self.removalTime = 0.0
        
        self.label = "NoCFlowTableEntry::id=" + str(self.flow.get_id())
        
    
    def __repr__(self):
        
        debug = "<NoCFTE "         
        debug += " f_id=" + str(self.flow.get_id())
        debug += " f_type=" + str(self.flow.get_type())        
        debug += " f_pr=" + str(self.flow.get_priority())
        debug += " stsk->dtsk=" + str(self.flow.get_respectiveSrcTaskId()) + "->"+ str(self.flow.get_respectiveDstTaskId())
        debug += " sn->dn=" + str(self.flow.get_source()) + "->"+ str(self.flow.get_destination())
        debug += " rt=%.15f" % self.releaseTime
        debug += " a=" + str(self.active)
        debug += " lat=%.15f" % self.lastActivationTime
        debug += " rmt=%.15f5" % self.remainingTime
        
        wf = [x.getFlow().get_id() for x in self.waitsFor.values()]
        debug += " wf=" + str(wf)
        
        debug += " />"   
        
        return debug
    
    
    
    def getFlow(self):
        return self.flow
    
    def setActive(self):
        self.active = True
        self.lastActivationTime = self.env.now    
        
    def setInactive(self):
        self.checkSanityOnInactivation()
        self.active = False
    
    def checkSanityOnInactivation(self):
        for each_interferrer in self.waitsFor.values():
            if each_interferrer.active == True :
                if (each_interferrer.flow.get_priority() > self.flow.get_priority()):
                    sys.exit( self.label+ ": checkSanityOnInactivation: Error!")
    
    def setRemainingTime(self, rt):
        self.remainingTime = rt
    def setRemovalTime(self,remt):
        self.removalTime = remt
    
    def addInterferenceSource(self, intS):
        #self.waitsFor.append(intS)
        k = "%d_%f" % (intS.getFlow().get_id(), intS.getReleaseTime())                
        self.waitsFor[k]=intS
        
    def removeInterferenceSource(self, intS):         
        #if intS in self.waitsFor: self.waitsFor.remove(intS)
        k = "%d_%f" % (intS.getFlow().get_id(), intS.getReleaseTime())
        if k in self.waitsFor:
            del self.waitsFor[k]
    
    def compareTo(self, fte):
        if(fte.flow.get_priority() < self.flow.get_priority()): 
            return -1
        elif(fte.flow.get_priority() > self.flow.get_priority()):
            return 1
        else:
            return 0            
    
    def getLastActivationTime(self):
        return self.lastActivationTime
    def getReleaseTime(self):
        return self.releaseTime
    def getRemainingTime(self):
        return self.remainingTime    
    def getInterferenceFlows(self):
        return self.waitsFor.values()
    def getRemovalTime(self):
        return self.removalTime
    def isActive(self):
        return self.active