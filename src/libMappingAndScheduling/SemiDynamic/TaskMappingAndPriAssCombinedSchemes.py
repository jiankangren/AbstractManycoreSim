class TaskMappingAndPriAssCombinedSchemes:
    
    TASKMAPPINGANDPRIASSCOMBINED_DISABLED                                       = 0     # this will disable this scheme
    
    TASKMAPPINGANDPRIASSCOMBINED_IMPACTSCORING_V1                               = 800     # PR:LowestResFirst combined with impact scoring mechanism
    TASKMAPPINGANDPRIASSCOMBINED_IMPACTSCORING_V2                               = 801     # PR:LowestResFirst combined with only self-impact
    TASKMAPPINGANDPRIASSCOMBINED_IMPACTSCORING_V3                               = 802     # PR:LowestResFirst combined with only self-impact, only nodetq, only ibuff waiting times
    
    TASKMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_SHRTQFIRST_LEASTBLTIME_V1        = 810     # PR:LowestResFirst, MP:ShortestTQ combined with Least Blocking Time (based on wccc)
    
    TASKMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_LEASERESPTIMEANDCONGESTED_V1     = 820     # PR:LowestResFirst, MP:Node that gives the shortest response time and congested node
    
    # comms aware as well 
    TASKMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_NNWITHLEASTBLOCKING_V1           = 830     # PR:LowestResFirst, MP:NearestNeighbour with lowest blocking
    TASKMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_NNLEASTUTILISED_TOPNPERCENT      = 831     # PR:LowestResFirst, MP:Nearest node with lowest utilisation
    TASKMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_CARVALHO_BN                      = 832     # PR:LowestResFirst, MP:Carvalho: Best neighbour (path load)
    TASKMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_KAUSHIK_PP                       = 833     # PR:LowestResFirst, MP:Kaushik: Preprocessing algo (communication load balance)
    TASKMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_CARVALHO_BN_V2                   = 834     # PR:LowestResFirst, MP:Carvalho: Best neighbour (path load)
    TASKMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_CARVALHO_BN_V3                   = 835     # PR:LowestResFirst, MP:Carvalho: Best neighbour (path load)
    
    
    # hrt-vid
    TASKMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_LOWCOMMUNICATION_V1              = 840     # PR:LowestResFirst, MP:Lowest communication - I,P together, B seperate (lum)
    TASKMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_LOWCOMMUNICATION_V2              = 841     # PR:LowestResFirst, MP:Lowest communication - I, P together, B seperate (tight)
    TASKMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_TIGHTFIT_V1                      = 842     # PR:LowestResFirst, MP:tightly fitting tasks to nodes - version 1
    
    # all on one core
    TASKMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_SINGLENODE_LOWEST_UTIL           = 850     # PR:LowestResFirst, MP:map all the tasks of the stream on one core (the lowest utilised node)
    
    # random 
    TASKMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_RANDOMMAPPING                    = 851     # PR:LowestResFirst, MP:map all the tasks of the stream to random cores
    
    # using volatile task mapping Table
    TASKMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_MOSTSLACK_VIA_VTMTBL             = 860    # PR:LowestResFirst, MP:select task that has highest cumulative rem slack.
    