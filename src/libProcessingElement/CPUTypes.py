

class CPUTypes:
    # open loop systems
    OPENLOOP                          = 1    
    OPENLOOP_STATIC_SCHEDULED         = 2
    OPENLOOP_WITH_DISTREMAPPING       = 3
    OPENLOOP_WITH_PSALGOREMAPPING     = 4
    OPENLOOP_HEVC_FRAME_LEVEL         = 5
    OPENLOOP_HEVC_TILE_LEVEL         = 6
    
    
    # closed loop systems
    CLOSEDLOOP_DEFAULT                = 10
    CLOSEDLOOP_WITH_DISTREMAPPING     = 11
    CLOSEDLOOP_WITHOUT_IBUFFERING      = 12 
    CLOSEDLOOP_WITH_IBUFFERING         = 13
    
    # fully distributed
    FULLYDIST_PSALGO_FULLDYNAMIC        = 20
    FULLYDIST_PSALGO_SEMIDYNAMIC        = 21
    
    
    