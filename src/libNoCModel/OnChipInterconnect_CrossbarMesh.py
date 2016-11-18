import pprint
import sys
import math
#import networkx as nx
import matplotlib.pyplot as plt

## local imports
from SimParams import SimParams


class CrossbarMesh:
    def __init__(self, node_list, noc_w, noc_h):
        
        self.node_list = node_list
        self.noc_w = noc_w
        self.noc_h = noc_h
        
        # a list of links - each link will have 2 nodes attached to it (src, dest)        
        self.links = []
        self.node_positions = {}
        self.node_pos_tuples = {}
        self.node_neighbours = {}
        
        
    def construct(self):
        # we need to connect all nodes passed into the network
        # two nodes are connected via 2 links (full-duplex)
        
        if((self.noc_w * self.noc_h) != len(self.node_list)):
            sys.exit("NoC2DMesh::constructNoC : ERROR  - (noc_w * noc_h) != len(node_list)")
                
        
        ## construct the node-config dicts
        for ix_y in xrange(0, self.noc_h):
            for ix_x in xrange(0, self.noc_w):
                temp_node_ix = (ix_y*self.noc_w) + ix_x
                
                dict_key = self.node_list[temp_node_ix].get_id()
                
                ## positions
                self.node_positions[dict_key] = {'x_pos': ix_x, 
                                                 'y_pos': ix_y,
                                                }
                self.node_pos_tuples[dict_key] = (ix_x, ix_y)
                
                ## neighbours
                # need to treat special case for border nodes
                if(ix_y == 0):  # TOP ROW
                    if(ix_x == self.noc_w-1):
                        # top right corner
                        self.node_neighbours[dict_key] = {'WEST'    :  self.node_list[temp_node_ix-1].get_id(),
                                                          'EAST'    :  None,
                                                          'NORTH'   :  None,
                                                          'SOUTH'   :  self.node_list[temp_node_ix+self.noc_w].get_id()
                                                          }
                    elif(ix_x == 0):
                        # top left corner
                        self.node_neighbours[dict_key] = {'WEST'    :  None,
                                                          'EAST'    :  self.node_list[temp_node_ix+1].get_id(),
                                                          'NORTH'   :  None,
                                                          'SOUTH'   :  self.node_list[temp_node_ix+self.noc_w].get_id()
                                                          }
                    else:   
                        # other nodes in top row
                        self.node_neighbours[dict_key] = {'WEST'    :  self.node_list[temp_node_ix-1].get_id(),
                                                          'EAST'    :  self.node_list[temp_node_ix+1].get_id(),
                                                          'NORTH'   :  None,
                                                          'SOUTH'   :  self.node_list[temp_node_ix+self.noc_w].get_id()
                                                          }
                elif(ix_y == self.noc_h-1): # BOTTOM ROW
                    if(ix_x == self.noc_w-1):
                        # bottom right corner
                        self.node_neighbours[dict_key] = {'WEST'    :  self.node_list[temp_node_ix-1].get_id(),
                                                          'EAST'    :  None,
                                                          'NORTH'   :  self.node_list[temp_node_ix-self.noc_w].get_id(),
                                                          'SOUTH'   :  None
                                                          }
                    elif(ix_x == 0):
                        # bottom left corner
                        self.node_neighbours[dict_key] = {'WEST'    :  None,
                                                          'EAST'    :  self.node_list[temp_node_ix+1].get_id(),
                                                          'NORTH'   :  self.node_list[temp_node_ix-self.noc_w].get_id(),
                                                          'SOUTH'   :  None
                                                          }
                    else:   
                        # other nodes in bottom row
                        self.node_neighbours[dict_key] = {'WEST'    :  self.node_list[temp_node_ix-1].get_id(),
                                                          'EAST'    :  self.node_list[temp_node_ix+1].get_id(),
                                                          'NORTH'   :  self.node_list[temp_node_ix-self.noc_w].get_id(),
                                                          'SOUTH'   :  None
                                                          }
                    
                else:   # MIDDLE ROWS
                    # last column
                    if(ix_x == self.noc_w-1):
                        self.node_neighbours[dict_key] = {'WEST'    :  self.node_list[temp_node_ix-1].get_id(),
                                                          'EAST'    :  None,
                                                          'NORTH'   :  self.node_list[temp_node_ix-self.noc_w].get_id(),
                                                          'SOUTH'   :  self.node_list[temp_node_ix+self.noc_w].get_id()
                                                          }
                    # first column
                    elif(ix_x == 0):
                        self.node_neighbours[dict_key] = {'WEST'    :  None,
                                                          'EAST'    :  self.node_list[temp_node_ix+1].get_id(),
                                                          'NORTH'   :  self.node_list[temp_node_ix-self.noc_w].get_id(),
                                                          'SOUTH'   :  self.node_list[temp_node_ix+self.noc_w].get_id()
                                                          }
                        
                    # all other columns
                    else:
                        self.node_neighbours[dict_key] = {'WEST'    :  self.node_list[temp_node_ix-1].get_id(),
                                                          'EAST'    :  self.node_list[temp_node_ix+1].get_id(),
                                                          'NORTH'   :  self.node_list[temp_node_ix-self.noc_w].get_id(),
                                                          'SOUTH'   :  self.node_list[temp_node_ix+self.noc_w].get_id()
                                                          }
                    
                
        
        ## construct the links
        link_id = 0
        for ix_y in xrange(0, self.noc_h):
            for ix_x in xrange(0, self.noc_w):
                
                temp_node_ix = (ix_y*self.noc_w) + ix_x
                
                # special case for first row - no top connections
                if(ix_y == 0):
                    if(ix_x != self.noc_w-1):   # special case for the last column
                        # direction 1
                        link = NOCLink(link_id, self.node_list[temp_node_ix], self.node_list[temp_node_ix+1])                    
                        self.links.append(link)
                        link_id += 1
                        # direction 2
                        link = NOCLink(link_id, self.node_list[temp_node_ix+1], self.node_list[temp_node_ix])                    
                        self.links.append(link)
                        link_id += 1                        
                else:
                    ## top node cnx
                    # direction 1
                    link = NOCLink(link_id, self.node_list[temp_node_ix], self.node_list[temp_node_ix-self.noc_w])
                    self.links.append(link)
                    link_id += 1
                    # direction 2
                    link = NOCLink(link_id, self.node_list[temp_node_ix-self.noc_w], self.node_list[temp_node_ix])
                    self.links.append(link)
                    link_id += 1
                    
                    if(ix_x != self.noc_w-1):   # special case for the last column
                        ## right node cnx
                        # direction 1
                        link = NOCLink(link_id, self.node_list[temp_node_ix], self.node_list[temp_node_ix+1])
                        self.links.append(link)
                        link_id += 1
                        # direction 2
                        link = NOCLink(link_id, self.node_list[temp_node_ix+1], self.node_list[temp_node_ix])
                        self.links.append(link)
                        link_id += 1
                    
                
    def __repr__(self):
        debug = "<NoC2DMesh" + "\n"
        for each_link in self.links:
            debug += "\t" + each_link.toString() + "\n"
            
        debug += "/>"
            
        return debug
    
    
    # get cost for a given route 
    # this is used to determine how much
    # delay should be induced to pass data of {size}
    # from src-->dst
    def getRouteCost(self, src_id, dst_id, data_size_bytes):
        
        #print "getRouteCost : src_id="+ str(src_id) + ", dst_id="+ str(dst_id)
        
        cost = 0
        
        num_flits = math.ceil(data_size_bytes/SimParams.NOC_FLIT_BYTES)        
        num_hops = 1
        
        # old version
        #cost = ((num_hops * SimParams.NOC_ARBITRATION_COST) + num_flits) * SimParams.NOC_PERIOD  
        
        routers = num_hops - 1
        cost = (float(num_hops) * SimParams.NOC_PERIOD) + \
                (float(routers) * SimParams.NOC_ARBITRATION_COST) + \
                (float(num_flits) * SimParams.NOC_PERIOD)
        
        return cost
    
    
    
    # get cost for a given route 
    # this is used to determine how much
    # delay should be induced to pass data of {size}
    # from src-->dst
    def getRouteCostXY(self, src_id, dst_id, data_size_bytes):
        
        #print "getRouteCost : src_id="+ str(src_id) + ", dst_id="+ str(dst_id)        
        cost = 0
        
        num_flits = math.ceil(data_size_bytes/SimParams.NOC_FLIT_BYTES)
        route = self.getRouteXY(src_id, dst_id)
        num_hops = len(route)
        
        # old version
        #cost = ((num_hops * SimParams.NOC_ARBITRATION_COST) + num_flits) * SimParams.NOC_PERIOD
        
        routers = num_hops - 1
        cost = (float(num_hops) * SimParams.NOC_PERIOD) + \
                (float(routers) * SimParams.NOC_ARBITRATION_COST) + \
                (float(num_flits) * SimParams.NOC_PERIOD)        
        
        return cost                 
    
    # given a source, dest nodes, find the route taken
    # for now we use XY routing
    def getRouteXY(self, source_node_id, dest_node_id):
        
        #print "getRouteXY : source_node_id="+ str(source_node_id) + ", dest_node_id="+ str(dest_node_id)
                
        # get x,y pos of given nodes
        src_x = self.node_positions[source_node_id]['x_pos']
        src_y = self.node_positions[source_node_id]['y_pos']        
        dest_x = self.node_positions[dest_node_id]['x_pos']
        dest_y = self.node_positions[dest_node_id]['y_pos']
        
        # traverse the network until dest node is found
        # every iteration add link to route
        route = []
        found_node = 0
        curr_node_pointer = source_node_id
        next_node_pointer = None        
        while(found_node == 0):
            
            ## next hop ??
            next_node_pointer = self._nextHopXY(curr_node_pointer, dest_node_id)
           
            # is this the destination ?
            if(next_node_pointer == dest_node_id):
                found_node = 1  # yes !!
                link = self._findLink(curr_node_pointer, next_node_pointer)
                route.append(link)
            else:
                found_node = 0
                link = self._findLink(curr_node_pointer, next_node_pointer)
                route.append(link)
                # swap current<-> next
                curr_node_pointer = next_node_pointer
            
        
        return route
    
    
    def _printRoute(self, route):
        for each_link in route:
            print each_link.toString()
    
    # given a current node/router and a destination source
    # find the next hop router
    def _nextHopXY(self, current_id, dest_id):
        
        #print "_nextHopXY : source_node_id="+ str(current_id) + ", dest_node_id="+ str(dest_id)
        
        # get x,y pos of given nodes
        curr_x = self.node_positions[current_id]['x_pos']
        curr_y = self.node_positions[current_id]['y_pos']        
        dest_x = self.node_positions[dest_id]['x_pos']
        dest_y = self.node_positions[dest_id]['y_pos']
        
        # depending on the direction , select next router/node port
        if(curr_x > dest_x): # west
            return self.node_neighbours[current_id]['WEST']            
        elif(curr_x < dest_x): # east
            return self.node_neighbours[current_id]['EAST']
        else:    # same x-cord
            if(curr_y > dest_y): # north
                return self.node_neighbours[current_id]['NORTH']            
            elif(curr_y < dest_y): # south
                return self.node_neighbours[current_id]['SOUTH']
            else:   # local port!! (error)
                return None
        
       
    
    # given a source, dest of two neighbouring nodes
    # find the link they are connected by
    def _findLink(self, source, dest):
        for each_link in self.links:
            if((each_link.source_node.get_id() == source) and (each_link.dest_node.get_id() == dest)):
                return each_link
        
        return None
    
    
    
    
    ## test this class
    def testNetwork(self):
        
        # print NoC
        print "NOC structure"
        print "============="
        print self
        
        # check routing
        print "Testing routing"
        print "==============="        
        
        # top         
        src = 4
        dst = 1
        print "src="+str(src)+ ", dst="+ str(dst)
        self._printRoute(self.getRoute(src, dst))
        print ""
                
        # down         
        src = 4
        dst = 7
        print "src="+str(src)+ ", dst="+ str(dst)
        self._printRoute(self.getRoute(src, dst))
        print ""
        
        # left         
        src = 4
        dst = 3
        print "src="+str(src)+ ", dst="+ str(dst)
        self._printRoute(self.getRoute(src, dst))
        print ""
        
        # right         
        src = 4
        dst = 5
        print "src="+str(src)+ ", dst="+ str(dst)
        self._printRoute(self.getRoute(src, dst))
        print ""
    
        # top-right         
        src = 4
        dst = 2
        print "src="+str(src)+ ", dst="+ str(dst)
        self._printRoute(self.getRoute(src, dst))
        print ""
        
        # top-left         
        src = 4
        dst = 0
        print "src="+str(src)+ ", dst="+ str(dst)
        self._printRoute(self.getRoute(src, dst))
        print ""
        
        # bot-right         
        src = 4
        dst = 8
        print "src="+str(src)+ ", dst="+ str(dst)
        self._printRoute(self.getRoute(src, dst))
        print ""
        
        # bot-left         
        src = 4
        dst = 6
        print "src="+str(src)+ ", dst="+ str(dst)
        self._printRoute(self.getRoute(src, dst))
        print ""
        
        

       
        
        
            
            

class NOCLink:
    def __init__(self, id, source, dest):
        self.id = id
        self.source_node = source
        self.dest_node = dest
        
    def toString(self):
        debug = "<NOCLink "
        debug += " id=(" + str(self.id) + ")"
        debug += " src=" + str(self.source_node.get_id())  
        debug += " dest=" + str(self.dest_node.get_id())        
        debug += " />"   
        
        return debug
        
    
        

class NOCRouter:
    PORT_EAST   = 0; 
    PORT_WEST   = 1;
    PORT_NORTH  = 2; 
    PORT_SOUTH  = 3; 
    PORT_LOCAL  = 4;
    
    def __init__(self, lnk_east, lnk_west, lnk_north, lnk_south, lnk_local):
        self.link_east  = lnk_east
        self.link_west  = lnk_west
        self.link_north = lnk_north
        self.link_south = lnk_south
        self.link_local = lnk_local

    def arbitration(self):
        return None

