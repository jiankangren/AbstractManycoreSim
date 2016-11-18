

##########################################################################################################################
# Possible Admission Controller options
##########################################################################################################################
class AdmissionControllerOptions:
    AC_OPTION_NONE                          = 0 # no admission control
    AC_OPTION_HEURISTIC_ONLY                = 1 # perform heuristic based tests only
    AC_OPTION_HEURISTIC_THRESHOLDED         = 2 # perform heuristic based tests - but with thresholded values 
    AC_OPTION_HEURISTIC_KAO_DEADLINE_EQF    = 3 # perform heuristic based tests - but deadlines are calculated from kao and garcia method (EQF)
    AC_OPTION_HEURISTIC_KAO_DEADLINE_ES     = 4 # perform heuristic based tests - but deadlines are calculated from kao and garcia method (ES)
    AC_OPTION_SCHEDTEST_ONLY                = 5 # perform E2ERTA tests only
    AC_OPTION_HYB_HEU_SCHD_V1               = 6 # perform a hybrid version of the schedulability analysis and heuristic based tests
    AC_OPTION_HYB_HEU_SCHD_V2               = 7 # perform a hybrid version of the heuristic based tests and schedulability analysis (reverse)
    AC_OPTION_SCHEDTEST_TASKSONLY_ONLY      = 8 # perform E2ERTA tests (tasks only)
    AC_OPTION_SCHEDTEST_DIRECT_TO_CRITICALPATH      = 9 # perform E2ERTA tests (got to critical path tests directly)
    AC_OPTION_NONE_WITH_SCHEDTEST           = 10    # perform no admission control but with schedulability test
    
    AC_OPTION_SCHEDTEST_DIRECT_TO_CRITICALPATH_WITHMMC      = 11 # perform E2ERTA tests (got to critical path tests directly) (mmc data transfers taken into account)
    AC_OPTION_NONE_WITH_SCHEDTEST_WITHMMC                   = 12    # perform no admission control but with schedulability test (mmc data transfers taken into account)
    AC_OPTION_NONE_WITH_WITHMMC                             = 13    # perform no admission control but with schedulability test (mmc data transfers taken into account)
    AC_OPTION_NONE_WITH_LASTVS_SCHEDTEST_WITHMMC            = 14    # perform no admission control but with schedulability test (only when the last vid stream is admitted)