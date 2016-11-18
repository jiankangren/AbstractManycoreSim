class TaskTileMappingAndPriAssCombinedSchemes:
    
    TASKTILEMAPPINGANDPRIASSCOMBINED_DISABLED                                       = 0     # this will disable this scheme
    
    # random mapping
    TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_RANDOM                           = 900    # PR:LowestResFirst, MP:select random node
    
    # WITHOUT monitoring - using volatile task mapping Table
    TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_MOSTSLACK_VIA_VTMTBL             = 901    # PR:LowestResFirst, MP:select node that has highest cumulative rem slack.    
    TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_CLUSTLS_MOSTSLACK_VIA_VTMTBL     = 902    # PR:LowestResFirst, MP:use wcrs heuristic, but cluster the tile tasks
    TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_LOWUTIL_VIA_VTMTBL               = 903   # PR:LowestResFirst, MP:select lowest util node 
    TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_LOWMAPPED_VIA_VTMTBL             = 904   # PR:LowestResFirst, MP:select lowest mapped node 
    TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_CLUSTLS_MOSTSLACK_VIA_VTMTBL_V2  = 905   # PR:LowestResFirst, MP:use wcrs heuristic, but cluster the tile tasks (CP-based)
    
    TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_CLUSTLS_MOSTSLACK_VIA_VTMTBL_V2_FAKECP = 906 # same as 905 but with fake CP evaluation
    TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_CLUSTLS_MOSTSLACK_VIA_VTMTBL_V2_NOCCRFAKECP = 907 # same as 906 but no CCR
    TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_LOWUTIL_VIA_VTMTBL_FIRSTFIT      = 908 # similar to 903 but with a single sort
    TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_GROUPEDTILES_VIA_VTMTBL          = 909
    TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_CLUSTLS_MOSTSLACK_VIA_VTMTBL_V2_FF = 910 # similar to 905 but we sort the bins at the start according to low blocked order
    
    TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_CLUSTLS_MOSTSLACK_VIA_VTMTBL_V2_IPBCP  = 911   # # same as 905 but with where (I+P+Generalised_B) = CP
    
    TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_KAUSHIK_PP_V2 = 912 # this is the kaushiks algo, but for any random task graph  
    
    TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_CLUSTLS_MOSTSLACK_VIA_VTMTBL_V3_IPBCP_FLMP  = 913   # # same as 910 but with flexible hop_0 placement. (we don't overload 1 PE with too much blocking)
    
    TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_CLUSTLS_MOSTSLACK_VIA_VTMTBL_V1_HEIRBFRGROUPS  = 914   # # group the tasks according to hierarchical B-fr groups
    
    TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_CLUSTLS_MOSTSLACK_VIA_VTMTBL_V1_HEIRBFRGROUPS_FF = 915 # same as 914, but faster
    
    
    # WITH monitoring - assuming RM gets monitoring feedback (assume RM can access accurate node info)
    TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_LOWUTIL_WITHMONITORING_AVGCC_V1          = 920   # PR:LowestResFirst, MP:select lowest util node (tracked avgcc)
    TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_MOSTSLACK_WITHMONITORING_AVGCC_V1        = 921   # PR:LowestResFirst, MP:select highest cumulative rem slack node (tracked avgcc)
    TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_CLUSTLS_MOSTSLACK_WITHMONITORING_AVGCC   = 922   # PR:LowestResFirst, MP:use wcrs heuristic, but cluster the tile tasks (tracked avgcc)
    
    
    # combined, priority, mapping and mmc selection
    TASKTILEMAPPINGANDPRIASSCOMBINED_PRLOWRESFIRST_NN_MMC_CHILD_OPP_DIR_V1  = 930
    
    