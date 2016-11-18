class TaskRemapDecentSchemes:
    
    TASKREMAPPINGDECENTSCHEMES_NONE                                         = 0     # this will give error    
    TASKREMAPPINGDECENTSCHEMES_RANDOM                                       = 1     # remap to any random node
    TASKREMAPPINGDECENTSCHEMES_NEIGHBOUR_HIGHEST_PSLEVEL                    = 2     # remap to the neighbour with the highest pheromone level
    TASKREMAPPINGDECENTSCHEMES_RANDOM_QUEEN                                 = 3     # remap to a random queen
    TASKREMAPPINGDECENTSCHEMES_RANDOM_QUEEN_VIA_SYSSLACK                    = 4 
    TASKREMAPPINGDECENTSCHEMES_LOWESTBLOCKING_QUEEN                         = 5     # remap to queen which will give the lowest blocking factor
    TASKREMAPPINGDECENTSCHEMES_LOWESTBLOCKING_QUEEN_VIA_SYSSLACK            = 6     # remap to queen which will give the lowest blocking factor - look at sysslack not TQ
    TASKREMAPPINGDECENTSCHEMES_RANDOM_NEIGHBOUR                             = 7     # remap to a neighbour randomly
    TASKREMAPPINGDECENTSCHEMES_RANDOM_ANY                                   = 8     # remap to a completely random node
    TASKREMAPPINGDECENTSCHEMES_CCP_REMAPPING                                = 9     # remap using castilhos cluster protocol, perform remapping within cluster
    TASKREMAPPINGDECENTSCHEMES_CENTRAL_REMAPPER_V1                          = 10     # central scheme : node 0, takes decisions periodically.
    
    
    