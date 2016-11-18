class TaskMappingSchemes:
    
    TASKMAPPINGSCHEMES_NONE                                         = 0     # this will give error
    
    TASKMAPPINGSCHEMES_RANDOM                                       = 1
    TASKMAPPINGSCHEMES_SHORTEST_TQ                                  = 2
    TASKMAPPINGSCHEMES_HIGHEST_THROUGHPUT                           = 3
    TASKMAPPINGSCHEMES_LOWEST_THROUGHPUT                            = 4    
    TASKMAPPINGSCHEMES_LOWEST_REMAININGWCCC                         = 5 # lowest remaining worst-case computation cost
    TASKMAPPINGSCHEMES_HIGHEST_REMAININGWCCC                        = 6 # highest remaining worst-case computation cost
    TASKMAPPINGSCHEMES_HYB_SHORTESTTQ_AND_LOWESTREMAININGWCCC       = 7 # lowest tq + remaining worst-case computation cost
    TASKMAPPINGSCHEMES_HYB_SHORTESTTQ_AND_LOWESTREMAININGAVGCCC     = 8 # lowest tq + remaining avg-case computation cost
    TASKMAPPINGSCHEMES_HYB_SHORTESTTQ_AND_RANDOM                    = 9 # lowest tq + random selection
    
    TASKMAPPINGSCHEMES_LOWEST_UTILISATION                           = 10 # lowest node utilisation (Ci/Ti) (worst-case)
    TASKMAPPINGSCHEMES_LOWEST_UTILISATION_NEARESTPARENT             = 11 # lowest node utilisation, with nearest node to parent task (takes into account DAG, i.e communication)
    
    
    TASKMAPPINGSCHEMES_SHORTEST_TQ_VIARUNTIMEAPP                    = 12 # same as shortest task queue, but looks at the rm's runtime app information
    TASKMAPPINGSCHEMES_CUSTOM_LOADFROMFILE                          = 13 # load the mapping from a file
    
    
    # below are experimental/ideas    
    TASKMAPPINGSCHEMES_HIGHEST_BLOCKINGRATE     = 100 # how do we do this one ?? :(
    
    