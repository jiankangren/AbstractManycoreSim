import pprint
import sys
import math
from collections import OrderedDict
import numpy as np

#import networkx as nx
import matplotlib.pyplot as plt

## local imports
from SimParams import SimParams


class NoC:
    def __init__(self, node_list, noc_w, noc_h):
        
        self.node_list = node_list        
        self.noc_w = noc_w
        self.noc_h = noc_h
        
        # a list of links - each link will have 2 nodes attached to it (src, dest)        
        self.links = []
        self.links_hashtable = {}
        self.node_positions = {}
        self.node_pos_tuples = {}
        self.node_neighbours = {}
        
        # mmc nodes list
        self.mmc_node_ids = []
        
        
        ## structures used for fast access
        # a structure containing the hop count from each node to another node (precalculated)
        self.precal_hopcount_table = {}
        self.precal_nodesinhopcounts_table = {}
        self.precal_route_table = {} # all routes for source and destinations
        self.all_node_ids = {}
        self.xy_network_max_hops = (SimParams.NOC_W-1) + (SimParams.NOC_H-1)
        
        
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
                        link = NOCLink(link_id, self.node_list[temp_node_ix].get_id(), self.node_list[temp_node_ix+1].get_id())  
                        link.set_data_dir(self.setLinkDataDir(link))                  
                        self.links.append(link)
                        self.links_hashtable[str(temp_node_ix)+"-"+str(temp_node_ix+1)] = link
                        link_id += 1
                        # direction 2
                        link = NOCLink(link_id, self.node_list[temp_node_ix+1].get_id(), self.node_list[temp_node_ix].get_id())
                        link.set_data_dir(self.setLinkDataDir(link))                    
                        self.links.append(link)
                        self.links_hashtable[str(temp_node_ix+1)+"-"+str(temp_node_ix)] = link
                        link_id += 1
                                                
                else:
                    ## top node cnx
                    # direction 1
                    link = NOCLink(link_id, self.node_list[temp_node_ix].get_id(), self.node_list[temp_node_ix-self.noc_w].get_id())
                    link.set_data_dir(self.setLinkDataDir(link))
                    self.links.append(link)
                    self.links_hashtable[str(temp_node_ix)+"-"+str(temp_node_ix-self.noc_w)] = link
                    link_id += 1
                    # direction 2
                    link = NOCLink(link_id, self.node_list[temp_node_ix-self.noc_w].get_id(), self.node_list[temp_node_ix].get_id())
                    link.set_data_dir(self.setLinkDataDir(link))
                    self.links.append(link)
                    self.links_hashtable[str(temp_node_ix-self.noc_w)+"-"+str(temp_node_ix)] = link
                    link_id += 1
                    
                    if(ix_x != self.noc_w-1):   # special case for the last column
                        ## right node cnx
                        # direction 1
                        link = NOCLink(link_id, self.node_list[temp_node_ix].get_id(), self.node_list[temp_node_ix+1].get_id())
                        link.set_data_dir(self.setLinkDataDir(link))
                        self.links.append(link)
                        self.links_hashtable[str(temp_node_ix)+"-"+str(temp_node_ix+1)] = link
                        link_id += 1
                        # direction 2
                        link = NOCLink(link_id, self.node_list[temp_node_ix+1].get_id(), self.node_list[temp_node_ix].get_id())
                        link.set_data_dir(self.setLinkDataDir(link))
                        self.links.append(link)
                        self.links_hashtable[str(temp_node_ix+1)+"-"+str(temp_node_ix)] = link
                        link_id += 1
                        
                        
                        
        ### construct local links
        if(SimParams.NOC_MODEL_LOCAL_LINK == True):
            
            ## for every node we add a local-core node 
            ## this is a bit wrong, because technically a node is a local
            ## core, but its a bad design anyway. so basically :
            ## local_node : referes to the actual processor
            ## node : refers to the router
            
            for each_node in self.node_list:                    
                local_node_id = "L" + str(each_node.get_id()) 
                node_id = each_node.get_id()
                
                # outward direction (node --> router)
                link = NOCLink(link_id, local_node_id, node_id)
                link.set_data_dir(self.setLinkDataDir(link))
                self.links.append(link)
                self.links_hashtable[str(local_node_id)+"-"+str(node_id)] = link
                link_id += 1
                
                # inward direction (node <-- router)
                link = NOCLink(link_id, node_id, local_node_id)
                link.set_data_dir(self.setLinkDataDir(link))
                self.links.append(link)
                self.links_hashtable[str(node_id)+"-"+str(local_node_id)] = link
                link_id += 1
        
        
        ### construct links between routers and MMCs
        if (SimParams.MMC_MODEL_AS_EXT_COMPONENTS == True):            
            # populate mmc nodes
            all_mmc_connected_nodes = self.get_MMCConnectedNodeIds()
            
            for each_mmc_node_conn_id in all_mmc_connected_nodes:
                self.mmc_node_ids.append("MMC"+ str(each_mmc_node_conn_id)) # this list will be used later
                
            # construct links for mmcs
            for each_mmc_node_conn_id in self.mmc_node_ids:                
                mmc_node_id = each_mmc_node_conn_id
                router_id = each_mmc_node_conn_id.replace("MMC","")
                
                # mmc-->router
                link = NOCLink(link_id, mmc_node_id, router_id)
                link.set_data_dir(self.setLinkDataDir(link))
                self.links.append(link)
                self.links_hashtable[str(mmc_node_id)+"-"+str(router_id)] = link
                link_id += 1
                
                # router-->mmc
                link = NOCLink(link_id, router_id, mmc_node_id)
                link.set_data_dir(self.setLinkDataDir(link))
                self.links.append(link)
                self.links_hashtable[str(router_id)+"-"+str(mmc_node_id)] = link
                link_id += 1
        
        
        ### precalculate hops                
        self.all_node_ids = range(len(self.node_list))
        self.precalcHopCounts()
        self.precalcNodesInHopCounts()
        self.precalcRouteTable()
          
        ## testing
        #pprint.pprint(self.precal_hopcount_table)
        #pprint.pprint(self.precal_nodesinhopcounts_table)        
        #print "len(self.links_hashtable.keys()) : " , len(self.links_hashtable.keys())
        #print "len(self.links) : ", len(self.links)        
        #sys.exit()
        
        
    
    
    def __repr__(self):
        debug = "<NoC2DMesh" + "\n"
        for each_link in self.links:
            debug += "\t" + each_link.toString() + "\n"
            
        debug += "/>"
            
        return debug
    
    
    def get_mmc_node_ids(self):
        return self.mmc_node_ids
    
    # determine which PEs are connected to the MMCs
    def get_MMCConnectedNodeIds(self):                
        mmc_connected_nodes = []
        if SimParams.MMC_CONTROLLER_NUM_PER_SIDE != 1:
            sys.exit("get_MMCConnectedNodeIds:: Error ! not implmented yet.. (MMC_CONTROLLER_NUM_PER_SIDE)")
        else:
            # for each boundary get the nodes connected to the mmc
            for each_mmc_boundary in SimParams.MMC_CONTROLLER_LOCATIONS:
                node_ids = self.getBoundaryNodes(each_mmc_boundary.upper())
                if SimParams.MMC_CONTROLLER_NUM_PORTS == 2:                
                    # two ports per side per controller, we assume only 1 mmc per side
                    ix_nid_div_2 = float(len(node_ids))/2.0                
                    if SimParams.NOC_W % 2 == 0: # even
                        side_mmc_connected_nodes_ids = [node_ids[int(ix_nid_div_2-1)], node_ids[int(ix_nid_div_2)]]                     
                    else: # odd
                        side_mmc_connected_nodes_ids = [node_ids[int(ix_nid_div_2-1)], node_ids[int(ix_nid_div_2)]]
                    
                    for each_nid in side_mmc_connected_nodes_ids:
                        if each_nid not in mmc_connected_nodes:
                            mmc_connected_nodes.append(each_nid)
                else:
                    sys.exit("get_MMCConnectedNodeIds:: Error ! not implmented yet.. (MMC_CONTROLLER_NUM_PORTS)")
        
        return mmc_connected_nodes
    
    
    
    
    def findNeighbourDirection(self, src_nid, dst_nid):
        for k,v in self.node_neighbours[src_nid].iteritems():
            if v == dst_nid: 
                return k
            else: 
                pass            
        sys.exit("unknown src_nid, dst_nid, no relationship : " + str(src_nid) + str(dst_nid))
        
    
    def setLinkDataDir(self, link_obj):
        (src_nid, dst_nid) = link_obj.get_src_dst()
        
        # local links
        if "L" in str(src_nid):
            dir = "LOCAL_O"
        elif "L" in str(dst_nid):
            dir = "LOCAL_I"
            
        # mmc links
        elif ("MMC" in str(src_nid)) or ("MMC" in str(dst_nid)):            
            if "MMC" in str(src_nid):
                io_dir = "MMC_O"
                node_border = self.isNodeInBoundary(int(src_nid.replace("MMC", "")))[0]        
            elif "MMC" in str(dst_nid):
                io_dir = "MMC_I"
                node_border = self.isNodeInBoundary(int(dst_nid.replace("MMC", "")))[0]
            else:
                sys.exit("setLinkDataDir: Error - 1 : " + str(src_nid) + ", " + str(dst_nid))
                
            dir =   node_border + "_" + io_dir
            
        else:
            dir = self.findNeighbourDirection(src_nid, dst_nid)
        
        return dir
    
    # precalculated hop counts from one node to another
    def precalcHopCounts(self):
        for each_node_x in self.node_list:
            nid_x = each_node_x.get_id()
            self.precal_hopcount_table[nid_x] = {}
            for each_node_xx in self.node_list:                
                nid_xx = each_node_xx.get_id()                
                self.precal_hopcount_table[nid_x][nid_xx] = len(self.getRouteHopCount(nid_x,nid_xx))
                                
            # from each node to mmc
            for each_mmc_id in self.mmc_node_ids:
                self.precal_hopcount_table[nid_x][each_mmc_id] = len(self.getRouteHopCount(nid_x,each_mmc_id))
            
            
    
    # precalculated table of all nodes in each hop count from every node    
    def precalcNodesInHopCounts(self):
        self.xy_network_max_hops
        for each_node_x in self.node_list:
            nid_x = each_node_x.get_id() 
            self.precal_nodesinhopcounts_table[nid_x] = OrderedDict()
            
            max_hop_count_for_nid_x = np.max([v for k,v in self.precal_hopcount_table[nid_x].iteritems() if "MMC" not in str(k)])
            
            for nhops in xrange(1,max_hop_count_for_nid_x+1): # until max hop count
                nhop_nodes = self.getNodesNHops(nid_x, nhops)
                # remove current node id
                nhop_nodes = [nid for nid in nhop_nodes if nid != nid_x]
                self.precal_nodesinhopcounts_table[nid_x][nhops] = nhop_nodes
                
                
                
                    
    # precalculate table of all routes for node combinations
    def precalcRouteTable(self):
        for each_node_i in self.node_list:
            for each_node_j in self.node_list:
                key = (each_node_i.get_id(), each_node_j.get_id())            
                self.precal_route_table[key] = self.getRouteXY(each_node_i.get_id(), each_node_j.get_id())
        
        # mmc->node routes
        for each_node_i in self.node_list:
            for mmc_i in self.mmc_node_ids:
                key = (mmc_i, each_node_i.get_id())
                self.precal_route_table[key] = self.getRouteXY(mmc_i, each_node_i.get_id())
                
        # node->mmc routes
        for each_node_i in self.node_list:
            for mmc_i in self.mmc_node_ids:
                key = (each_node_i.get_id(), mmc_i)
                self.precal_route_table[key] = self.getRouteXY(each_node_i.get_id(), mmc_i)

        
    
    def getLinksConnectedToNode(self, node_id):
        links_connected_to_node = []
        for each_link in self.links:
            src_dst_nodeids = [n.get_id() for n in each_link.get_src_dst()]
            
            if(node_id in src_dst_nodeids):
                if each_link.get_id() not in links_connected_to_node:
                    links_connected_to_node.append(each_link)
                    
        return links_connected_to_node
            
     
    def getNeighbours(self, node_id):
        return self.node_neighbours[node_id]
               
    def getNeighbourNodeIds(self, node_id):
        nn_ids = [x for x in self.node_neighbours[node_id].values() if x != None]
        return nn_ids    
    
    
    def getBoundaryNodes(self, boundary_key):        
        list_of_nodes = []        
        for each_node in self.node_list:
            if(self.node_neighbours[each_node.get_id()][boundary_key] == None):
                list_of_nodes.append(each_node.get_id())
        return list_of_nodes
    
    def isNodeInBoundary(self, nid):
        boundaries = []
        for each_boundary_lbl, b_nodes in self.node_neighbours[nid].iteritems():
            if b_nodes == None:
                boundaries.append(each_boundary_lbl)
            else:
                pass
        return boundaries
                
    
    
    def getNodeXYpos(self, node_id):
        xpos = self.node_positions[node_id]['x_pos']
        ypos = self.node_positions[node_id]['y_pos']
        return (xpos, ypos)             
            
    
    
    def getNeighboursTwoHop(self, node_id, hop_count=2):
        nn_ids = [x for x in self.node_neighbours[node_id].values() if x != None] # first iteration
        
        neighbours_list = []
        neighbours_list.extend(nn_ids)
        
        # second iteration
        for each_n in nn_ids:
            temp_nn_ids = [x for x in self.node_neighbours[each_n].values() if x != None]
            neighbours_list.extend(temp_nn_ids)
        
        # remove duplicates
        neighbours_list = list(set(neighbours_list))
        
        # remove current node id
        neighbours_list = [nid for nid in neighbours_list if nid != node_id]
        
        return neighbours_list
    
    # get nodes that are N hops away from target node
    def getNodesNHops(self, target_node_id, hop_count):
        assert(target_node_id != None)        
        if  hop_count == 0 : return []
        
#         print "--"
#         pprint.pprint(self.precal_hopcount_table)
#         print "--"
        
        result_list = []
        for each_node in self.node_list:
            #route_len = len(self.getRouteHopCount(target_node_id,each_node.get_id()))
            route_len = self.precal_hopcount_table[target_node_id][each_node.get_id()]
                    
            if route_len <=  hop_count:
                result_list.append(each_node.get_id())
        
        # remove duplicates
        result_list = list(set(result_list))
        
        # remove current node id
        result_list = [nid for nid in result_list if nid != target_node_id]
        
        return result_list
    
    
    # get nodes that are N hops away from target node
    def getNodesNHops_fast(self, target_node_id, hop_count, network_size = SimParams.NOC_W, limit_result=-1, truncate_hops=True):
        # checks and quick exit
        assert(target_node_id != None)        
        if  (hop_count == 0) : return []        
        if (hop_count >= self.xy_network_max_hops):
            return list(self.all_node_ids) 
        if (hop_count >= np.max(self.precal_nodesinhopcounts_table[target_node_id].keys())):
            return list(self.all_node_ids)
        
        if hop_count in self.precal_nodesinhopcounts_table[target_node_id]:
            if limit_result == -1:
                return list(self.precal_nodesinhopcounts_table[target_node_id][hop_count])
            elif limit_result > 0:
                sorted_result = sorted(list(self.precal_nodesinhopcounts_table[target_node_id][hop_count])) # sorting to maintain consistent order each time this is called                
                return sorted_result[:limit_result]
            else:
                sys.exit("Error : getNodesNHops_fast - something went wrong - 1")                
        else: # we have gone over the hop limit, get lower hops
            if truncate_hops == True: # we have gone over the hop limit, get lower hops
                new_hop_count = np.max(self.precal_nodesinhopcounts_table[target_node_id].keys())
                return list(self.precal_nodesinhopcounts_table[target_node_id][new_hop_count])
            else:
                sys.exit("Error : getNodesNHops_fast - something went wrong - 2")
            
            
    
    
    # get nodes that are N hops away from target node
    def getNodesExactNHops_fast(self, target_node_id, hop_count, network_size = SimParams.NOC_W, limit_result=-1, truncate_hops=True):
        # checks and quick exit
        assert(target_node_id != None)        
        if  (hop_count == 0) : return []
        if (hop_count <= 1) :
            sys.exit("Error : getNodesExactNHops_fast - hop count too small : %d" % hop_count)
        if (hop_count > self.xy_network_max_hops):
            sys.exit("Error : getNodesExactNHops_fast - hop count too large : %d" % hop_count)
        
        if hop_count in self.precal_nodesinhopcounts_table[target_node_id]:
            superset_nodes = set(self.precal_nodesinhopcounts_table[target_node_id][hop_count])
            subset_nodes = set(self.precal_nodesinhopcounts_table[target_node_id][hop_count-1])
            result_set = superset_nodes - subset_nodes
            
            #print "getNodesExactNHops_fast:: here - 1", pprint.pformat(superset_nodes), pprint.pformat(subset_nodes), pprint.pformat(result_set) 
            
            return list(result_set)
                        
        else:
            if truncate_hops == True: # we have gone over the hop limit, get lower hops                
                new_hop_count = np.max(self.precal_nodesinhopcounts_table[target_node_id].keys())
                superset_nodes = set(self.precal_nodesinhopcounts_table[target_node_id][new_hop_count])
                subset_nodes = set(self.precal_nodesinhopcounts_table[target_node_id][new_hop_count-1])
                result_set = superset_nodes - subset_nodes
                
                #print "getNodesExactNHops_fast:: here - 2", pprint.pformat(superset_nodes), pprint.pformat(subset_nodes), pprint.pformat(result_set)
                
                return list(result_set)                
            else:
                sys.exit("Warning : getNodesExactNHops_fast - something went wrong - 2")
            
    
    
    
    def getInnerNodes_1border(self, border_size=1):
        boundaries = ['NORTH', 'SOUTH', 'WEST', 'EAST']
        boundary_node_ids = []
        for each_boundary_k in boundaries:
            b_nids = self.getBoundaryNodes(each_boundary_k)
            boundary_node_ids.extend(b_nids)
        
        all_network_node_ids = [each_node.get_id() for each_node in self.node_list]        
        node_ids_excluding_boundary = list(set(all_network_node_ids) - set(boundary_node_ids))
        
        return node_ids_excluding_boundary
        
    
    
    # exactly n hops
    def getNodesExactNHops(self, target_node_id, hop_count):
        result_list = []
        for each_node in self.node_list:
            route_len = len(self.getRouteHopCount(target_node_id,each_node.get_id()))            
            if route_len ==  hop_count:
                result_list.append(each_node.get_id())
        
        # remove duplicates
        result_list = list(set(result_list))
        
        # remove current node id
        result_list = [nid for nid in result_list if nid != target_node_id]
                
        return result_list
            
        
    
    
    def getLinks(self):
        return self.links
    
    # get cost for a given route 
    # this is used to determine how much
    # delay should be induced to pass data of {size}
    # from src-->dst
    def getRouteCost(self, src_id, dst_id, data_size_bytes, nhops=1):        
        #print "getRouteCost : src_id="+ str(src_id) + ", dst_id="+ str(dst_id)        
        cost = 0        
        num_flits = math.ceil(data_size_bytes/SimParams.NOC_FLIT_BYTES)        
        num_hops = nhops        
        
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
        
        cost = 0.0
        
        num_flits = math.ceil(data_size_bytes/SimParams.NOC_FLIT_BYTES)
        route = self.getRouteXY(src_id, dst_id)
        num_hops = float(len(route))
        
        # old version
        #cost = float((num_hops * SimParams.NOC_ARBITRATION_COST) + num_flits) * SimParams.NOC_PERIOD
        
        routers = num_hops - 1
        cost = (float(num_hops) * SimParams.NOC_PERIOD) + \
                (float(routers) * SimParams.NOC_ARBITRATION_COST) + \
                (float(num_flits) * SimParams.NOC_PERIOD)        
        
        return cost                 
    
    # given a source, dest nodes, find the route taken
    # for now we use XY routing
    def getRouteXY(self, source_node_id, dest_node_id):    
        #print "getRouteXY : source_node_id="+ str(source_node_id) + ", dest_node_id="+ str(dest_node_id)
        
        if SimParams.MMC_MODEL_AS_EXT_COMPONENTS:
            # filter out any reference to mmcs
            src_nid = int(str(source_node_id).replace("MMC", ""))
            dst_nid = int(str(dest_node_id).replace("MMC", ""))
        
            
        
        # if src and dest nodes are equal, we skip the route search
        if(src_nid != dst_nid):          
            # get x,y pos of given nodes
            src_x = self.node_positions[src_nid]['x_pos']
            src_y = self.node_positions[src_nid]['y_pos']        
            dest_x = self.node_positions[dst_nid]['x_pos']
            dest_y = self.node_positions[dst_nid]['y_pos']
            
            # traverse the network until dest node is found
            # every iteration add link to route
            route = []
            found_node = 0
            curr_node_pointer = src_nid
            next_node_pointer = None        
            while(found_node == 0):                
                ## next hop ??
                next_node_pointer = self._nextHopXY(curr_node_pointer, dst_nid)               
                # is this the destination ?
                if(next_node_pointer == dst_nid):
                    found_node = 1  # yes !!
                    link = self._findLink(curr_node_pointer, next_node_pointer)
                    route.append(link)
                else:
                    found_node = 0
                    link = self._findLink(curr_node_pointer, next_node_pointer)
                    route.append(link)
                    # swap current<-> next
                    curr_node_pointer = next_node_pointer
        else:
            route = []
        
        
        ### handle MMC/local link modelling ###
        ### is this a mmc rd/wr request ? (nb. we dont consider mmc->mmc flows)
        
        if ("MMC" in str(source_node_id)): # mmc-->node
            # first link (mmc->router)
            first_link_outbound = self._findLink(source_node_id, source_node_id.replace("MMC", ""))
            assert(first_link_outbound != None)
            route.insert(0, first_link_outbound) 
            # last link                        
            local_dest_node_id = "L"+str(dest_node_id)
            last_link_inbound = self._findLink(dest_node_id, local_dest_node_id)            
            route.append(last_link_inbound) # last link router->node
        
        elif ("MMC" in str(dest_node_id)): # node-->mmc
            # first link (node->router)
            local_source_node_id = "L"+str(source_node_id)
            first_link_outbound = self._findLink(source_node_id, local_source_node_id)
            route.insert(0, first_link_outbound)
            
            # last link            
            last_link_inbound = self._findLink(dest_node_id.replace("MMC", ""), dest_node_id)
            assert(last_link_inbound != None)        
            route.append(last_link_inbound)
        
        ## if local links is being modelled
        ## then an additional 2 links need to be added
        else:            
            if(SimParams.NOC_MODEL_LOCAL_LINK==True):
                local_source_node_id = "L"+str(source_node_id)
                local_dest_node_id = "L"+str(dest_node_id)
                            
                extra_link_outbound = self._findLink(local_source_node_id, source_node_id)
                extra_link_inbound = self._findLink(dest_node_id, local_dest_node_id)
                
                route.insert(0, extra_link_outbound)
                route.append(extra_link_inbound)            
        
        return route
    
    
    def getPrecalcRouteXY(self, src_nid, dst_nid):
        key = (src_nid, dst_nid)            
        if key in self.precal_route_table:            
            return self.precal_route_table[key]
        else:
            return self.getRouteXY(src_nid, dst_nid)
        
    
    
    def getNodeIdByXYPos(self, xpos, ypos):
        for each_node_k, each_node_v in self.node_positions.iteritems():
            if (each_node_v['x_pos'] == xpos) and (each_node_v['y_pos'] == ypos):
                return each_node_k
        
        return None
    
    def getXYPosByNodeId(self, node_id):
        for each_node_k, each_node_v in self.node_positions.iteritems():
            if node_id == each_node_k:
                return (each_node_v['x_pos'], each_node_v['y_pos'])
        return (None, None)     
    
    
    def getRouteHopCount(self, source_node_id, dest_node_id):
        
        route = self.getRouteXY(source_node_id, dest_node_id)
        
        if(len(route) > 0):
            # remove endpoints
            del route[0]
            del route[-1]
        
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
        links_hashtable_key = str(source)+"-"+str(dest)
        if(links_hashtable_key in self.links_hashtable):
            return self.links_hashtable[links_hashtable_key]
        else:            
            for each_link in self.links:
                if((each_link.source_node_id == source) and (each_link.dest_node_id == dest)):
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
    def __init__(self, id, source_id, dest_id, data_dir=None):
        self.id = id
        self.source_node_id = source_id
        self.dest_node_id = dest_id
        
        self.data_dir = data_dir
        
        self.flows = []
        
        
        # for tracking
        self.completed_flows = []
        self.idle_time = ['idle', 0.0, 0.0]  # idle? , lastupdate, cumulativeidle
        
    def __repr__(self):
        debug = "[" + str(self.source_node_id) + "->" + str(self.dest_node_id) + "]"
        #debug = "." + str(self.id)                
        return debug
    
#    def __eq__(self, other):
#        return self.id == other.id
        
    def toString(self):
        debug = "<NOCLink "
        debug += " id=(" + str(self.id) + ")"
        debug += " src=" + str(self.source_node_id)  
        debug += " dest=" + str(self.dest_node_id)        
        debug += " />"   
        
        return debug
    
    
    def set_data_dir(self, dd):
        self.data_dir = dd
    def get_data_dir(self):
        return self.data_dir
    
    
    def addFlow(self, flow):
        self.flows.append(flow)
    def removeFlow(self, flow):
        if flow in self.flows: self.flows.remove(flow )
        
        # add to completed flows
        self.completed_flows.append(flow.get_id())
        
    def getUtilisation(self):
        linkUtil = 0.0
        for each_flw in self.flows:
            linkUtil += 100*each_flw.getUtilisation()
        
        return linkUtil
    
    def get_id(self):
        return self.id
    
    def get_src_dst(self):
        return (self.source_node_id, self.dest_node_id)
    
    def addIdleTime(self, new_idle_flag, time_now):
        
        current_idle_flag = self.idle_time[0]
        
        if(new_idle_flag == 'idle') and (current_idle_flag == 'active'):
            self.idle_time[0] = 'idle'
            self.idle_time[1] = time_now
            
        elif(new_idle_flag == 'active') and (current_idle_flag == 'idle'):
            self.idle_time[0] = 'idle'
            self.idle_time[1] = time_now
            
        elif(new_idle_flag == 'idle') and (current_idle_flag == 'idle'):
            self.idle_time[0] = 'idle'            
            self.idle_time[2] += time_now - self.idle_time[1]
            self.idle_time[1] = time_now            
            
        elif(new_idle_flag == 'active') and (current_idle_flag == 'active'):
            self.idle_time[0] = 'active'
            self.idle_time[1] = time_now
            
        
    def getAccumulatedIdleTime(self):
        return self.idle_time[2]
    
        

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

