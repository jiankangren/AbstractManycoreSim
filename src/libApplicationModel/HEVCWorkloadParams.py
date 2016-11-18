import numpy as np
import sys

####################################################################################
# Workload parameters for HEVC
# ============================
# We have collected data from 5 realistic and 1 synthetic video stream.
#
# (ACTION) Action - Heavy panning/camera movement, frequent scene changes.   
# (DOC) Documentary -  Natural scenery, medium movement scenes, 
#                 fade in/out, grayscale to colour transitions.
# (SPORT) Sport -  camera perspective mostly on field, camera panning, 
#          occasional close-ups on players/spectators. 
#          Large amounts of common single colour background, 
#          combined text and video.     
# (SPEECH) Speech - Constant, non-uniform background; uni-camera and 
#          single person perspective, head/shoulder movement.
# (ANIM) Animation -  Wide range of colours, moderate scene changes.
# (PRN) PseudoRandomNoise - random coloured pixels, Low compression 
#                     efficiency, useful for simulating worst-case 
#                     characteristics
####################################################################################

HEVCWLPARAMS_TYPES_OF_VIDEOS = [ 'ACTION', 'DOC', 'SPORT', 'SPEECH', 'ANIM' ]


HEVCWLPARAMS_GOPLEN_MIN_MAX = (15, 27)

# ========================================
# Contiguous B-frame ratios
# This depends on how many max. bframes 
# there can be. For now, we do for:
# max_b : 4
# ========================================
HEVCWLPARAMS_CONTIG_BFRAMES_PROBS = {                               
                               4 : { # contig : 1,2,3,4
                                    'ACTION' : [0.25, 0.25, 0.29, 0.21],                      
                                    'DOC' :    [0.005, 0.49, 0.505, 0.00],
                                    #'DOC' :    [0.105, 0.347, 0.451, 0.097],
                                    'SPORT' :  [0.1, 0.2, 0.3, 0.4],
                                    'SPEECH' : [0.05, 0.2, 0.5, 0.25],
                                    'ANIM' : [0.1, 0.2, 0.45, 0.25] 
                                    },
                               }

def HEVCWLPARAMS_POSSIBLE_GOP_SIZES(min_Gopsize, max_Gopsize):
    possible_contig_bframs = HEVCWLPARAMS_CONTIG_BFRAMES_PROBS.keys()    
    poss_gop_sizes = []
    for each_bmax in possible_contig_bframs:
        for N in np.arange(min_Gopsize, max_Gopsize+1):
            if (N-1) % (each_bmax+1) == 0:                
                poss_gop_sizes.append(N)
            else:
                pass        
    return poss_gop_sizes
    
    
    
    
# ========================================
# Reference distance
# 2nd order polynomial function 
# ========================================
def HEVCWLPARAMS_REFDIST_PARAMS(x, vid_k):
    if vid_k == 'ACTION':              
        y = (0.03) + (-0.3)*x + (0.76)*(x**2)
            
    elif vid_k == 'DOC':
        y = (0.04) + (-0.34)*x + (0.83)*(x**2)
         
    elif vid_k == 'SPORT':
        y = (0.03) + (-0.27)*x + (0.71)*(x**2)
         
    elif vid_k == 'SPEECH':
        y = (0.02) + (-0.24)*x + (0.67)*(x**2)
         
    elif vid_k == 'ANIM':             
        y = (0.04) + (-0.36)*x + (0.84)*(x**2)
    else:
        y = None
    
    return y


# if the reference distance restriction is 1-fwd, 1-bwd (1,2,3)
HEVCWLPARAMS_REFDIST__FWD1_BWD1_RATIOS = {'ACTION' : [0.176, 0.684, 0.14],
                                          'DOC' :    [0.194, 0.752, 0.054], 
                                          'SPORT' :  [0.116, 0.711, 0.173],
                                          'SPEECH' : [0.061, 0.806, 0.132],
                                          'ANIM' : [0.145, 0.753, 0.102] 
                                        }



# ========================================
# CU decoding time
# I/P/B CU : weibull dist [a,c,scale,loc]
# Skip CU : 10th order polynomial
# ========================================

HEVCWLPARAMS_IPB_CU_DECT_PARAMS = {
                  
                  'ACTION' : {
                              'ICU':[1.77E+01, 6.56E-01, 3.05E-06, 0.0],
                              'PCU':[7.47, 1.28, 8.42E-06, 0.0],
                              'BCU':[1.38, 2.55, 4.51E-05, 0.0],
                              
                              'ICU-minmax': [3.19E-06 ,1.91E-04],
                              'PCU-minmax': [3.51E-06 ,6.36E-05],
                              'BCU-minmax': [2.96E-06 ,2.57E-04],
                                                                                 
                              },
                      
                  'DOC' : {                      
                            'ICU':[9.24, 7.43E-01, 5.06E-06, 0.0],
                            'PCU':[3.29, 1.57, 1.58E-05, 0.0],
                            'BCU':[1.38, 2.78, 5.78E-05, 0.0],
                            
                            'ICU-minmax': [3.28E-06 ,1.76E-04],
                            'PCU-minmax': [3.33E-06 ,1.33E-04],
                            'BCU-minmax': [3.08E-06 ,1.75E-04],
                        },

                  'SPORT' : { 
                                'ICU':[2.87E+03, 3.21E-01, 1.02E-08, 0.0],
                                'PCU':[9.12E+02, 4.46E-01, 1.44E-07, 0.0],
                                'BCU':[7.13, 1.35, 1.99E-05, 0.0],
                                
                                'ICU-minmax': [1.11E-06 ,1.12E-04],
                                'PCU-minmax': [2.33E-06 ,7.97E-05],
                                'BCU-minmax': [3.92E-06 ,1.61E-04],
                                
                              },

                  'SPEECH' : {
                                'ICU':[1.23E+03, 3.25E-01, 2.09E-08, 0.0],
                                'PCU':[8.07E+02, 3.93E-01, 1.08E-07, 0.0],
                                'BCU':[6.54, 1.14, 2.49E-05, 0.0],
                                
                                'ICU-minmax': [2.65E-06 ,1.63E-04],
                                'PCU-minmax': [3.31E-06 ,1.33E-04],
                                'BCU-minmax': [3.66E-06 ,2.29E-04],
                                
                              },

                  'ANIM' : {  
                                'ICU':[6.56E+02, 3.08E-01, 1.93E-08, 0.0],
                                'PCU':[3.47E+01, 5.62E-01, 1.49E-06, 0.0],
                                'BCU':[4.74, 9.47E-01, 1.91E-05, 0.0],
                                
                                'ICU-minmax': [2.07E-06 ,1.75E-04],
                                'PCU-minmax': [2.50E-06 ,1.78E-04],
                                'BCU-minmax': [2.16E-06 ,3.58E-04],
                                
                            }
                  }

# params : x-variable, video_label
def HEVCWLPARAMS_SKIP_CU_DECT_PARAMS(x, vid_k, return_minmax=False):
    if vid_k == 'ACTION':
              
#         y = (2.26e54) + (-3.98e50)*x + \
#             (3.01e46)*(x**2) + \
#             (-1.27e42)*(x**3) + \
#             (3.31e37)*(x**4) + \
#             (-5.40e32)*(x**5) + \
#             (5.43e27)*(x**6) + \
#             (-3.08e22)*(x**7) + \
#             (7.54e16)*(x**8) + \
#             (2.44e10)*(x**9) + \
#             (-1.42e5)*(x**10)
                
        SkipCU_minmax= [1.2527836257E-06 ,3.8664376855E-05]
        p =  [2.33814357322593617562E+53, -4.61663565748449267214E+49, 3.86663461910551214598E+45, 
              -1.77897464154305341762E+41, 4.83587894813571206197E+36, -7.62713540223371679833E+31, 
              5.81867582174191100658E+26, 4.02918148876484411392E+20, -4.09472709296633200000E+16, 
              2.44769252846606353760E+11, -2.99085959091212716885E+05]
        
            
    elif vid_k == 'DOC':
#         y = (1.70e49) + (3.71e45)*x + \
#             (-2.46e42)*(x**2) + \
#             (4.21e38)*(x**3) + \
#             (-3.68e34)*(x**4) + \
#             (1.90e30)*(x**5) + \
#             (-6.00e25)*(x**6) + \
#             (1.16e21)*(x**7) + \
#             (-1.29e16)*(x**8) + \
#             (7.13e10)*(x**9) + \
#             (-8.86e4)*(x**10)
        
        p = [-8.74699518023918623891E+49, 3.91793147527981918583E+46, -7.59589452067337684973E+42, 
                8.34546026548032718355E+38, -5.71321752092395417295E+34, 2.52411551191237094309E+30, 
                -7.20954037194251322157E+25, 1.29698206842217273754E+21, -1.37940055079372860000E+16, 
                7.40183880412208709717E+10, -9.14870707158956502099E+04]
                        
        SkipCU_minmax = [1.20E-06,8.04E-05]
         
    elif vid_k == 'SPORT':
#         y = (-2.16e51) + (7.74e47)*(x) + \
#             (-1.20e44)*(x**2) + \
#             (1.05e40)*(x**3) + \
#             (-5.77e35)*(x**4) + \
#             (2.03e31)*(x**5) + \
#             (-4.60e26)*(x**6) + \
#             (6.46e21)*(x**7) + \
#             (-5.21e16)*(x**8) + \
#             (2.05e11)*(x**9) + \
#             (-2.13e5)*(x**10)
        
        p = [-8.53505176354833743084E+50, 3.40873113806894666305E+47, -5.87195389459610174364E+43, 
            5.70619502150166599274E+39, -3.43379804390223323054E+35, 1.32160377244856931359E+31, 
            -3.24330224411818630423E+26, 4.90165476015474527437E+21, -4.22290905081896800000E+16, 
            1.75143830600829040527E+11, -1.82310943569078197470E+05]
        
        SkipCU_minmax = [1.08E-06,7.38E-05]
         
    elif vid_k == 'SPEECH':
#         y = (8.79e53) + (-1.62e50)*x + \
#             (1.25e46)*(x**2) + \
#             (-5.18e41)*(x**3) + \
#             (1.21e37)*(x**4) + \
#             (-1.45e32)*(x**5) + \
#             (3.28e26)*(x**6) + \
#             (1.26e22)*(x**7) + \
#             (-1.45e17)*(x**8) + \
#             (5.89e11)*(x**9) + \
#             (-7.33e5)*(x**10)
        
        p = [5.45041015838136169132E+52, -4.98842553451776425713E+48, -3.55107689375524568499E+44, 
            7.46640624519093191050E+40, -4.80613236907635649377E+36, 1.64778009996635008835E+32, 
            -3.31673069649132588747E+27, 3.93427599573443684598E+22, -2.60680004179287776000E+17, 
            8.50915091461801757812E+11, -9.64819344052529777400E+05]
        
        SkipCU_minmax = [1.88E-06,4.11E-05]
        
         
    elif vid_k == 'ANIM':             
#         y = (-5.83e50) + (2.32e47)*x + \
#             (-3.99e43)*(x**2) + \
#             (3.86e39)*(x**3) + \
#             (-2.32e35)*(x**4) + \
#             (8.91e30)*(x**5) + \
#             (-2.20e26)*(x**6) + \
#             (3.40e21)*(x**7) + \
#             (-3.08e16)*(x**8) + \
#             (1.40e11)*(x**9) + \
#             (-1.64e5)*(x**10)
        
        p = [-1.13182742697692717363E+50, 5.21723557304375090910E+46, -1.03610959483095006567E+43, 
                1.16014015537196897858E+39, -8.05014786868401561857E+34, 3.58442002491885596835E+30, 
                -1.02578049978543625491E+26, 1.83682162679739868774E+21, -1.92475197424764600000E+16, 
                9.95268839293932037354E+10, -1.15980166197533661034E+05]
        
        SkipCU_minmax = [1.25E-06,8.69E-05]
        
    else:
        sys.exit("HEVCWLPARAMS_SKIP_CU_DECT_PARAMS:: Unknown movie")
    
    y = np.polyval(p, x)
    
    if return_minmax==True:
        return (y, SkipCU_minmax)
    else:
        return y


# ========================================
# Scale factors for CU types
# I/P/B/Skip CU 
# ========================================
def _get_scalled_weibull_factor(new_min, new_max):
    wb = np.random.weibull(2, 1000)
    wb_min = np.min(wb)
    wb_max = np.max(wb)    
    ss = [((i-wb_min)/(wb_max-wb_min))*(new_max-new_min) for i in wb]    
    ss_sel = np.random.choice(ss)    
    return ss_sel

# memory related scale factor
HEVCWLPARAMS_MEM_SCALE_FACTOR = 0.6 # only 40% of the calculated time is for instruction retiring

# scaling rule : more memory used : lower the scale factor 
# min, max values need to be given

HEVCWLPARAMS_SCALE_FACTOR = {
                            
                            # as at 13/19/2016 
                            #'ICU' : (0.015, 0.020), # this needs to be low, because we assume not much memory transactions as other CU types
                            #'PCU' : (0.015, 0.030), # P/B Cus will have some variation because of memory  
                            #'BCU' : (0.005, 0.015),
                            #'SkipCU' : (0.0015, 0.0025), # would be much less because no transform computation, only memory                                                          
                            
                            
                            'ICU' : (1.4*HEVCWLPARAMS_MEM_SCALE_FACTOR, 1.5*HEVCWLPARAMS_MEM_SCALE_FACTOR), # this needs to be low, because we assume not much memory transactions as other CU types
                            'PCU' : (1.4*HEVCWLPARAMS_MEM_SCALE_FACTOR, 1.9*HEVCWLPARAMS_MEM_SCALE_FACTOR), # P/B Cus will have some variation because of memory  
                            'BCU' : (1.0*HEVCWLPARAMS_MEM_SCALE_FACTOR, 1.0*HEVCWLPARAMS_MEM_SCALE_FACTOR),
                            'SkipCU' : (1.0*HEVCWLPARAMS_MEM_SCALE_FACTOR, 1.01*HEVCWLPARAMS_MEM_SCALE_FACTOR), # would be much less because no transform computation, only memory
                            
                            
                            
                            ## working for verification ##
#                             'ICU' : np.random.uniform(0.02, 0.025), # this needs to be low, because we assume not much memory transactions as other CU types
#                             'PCU' : np.random.uniform(0.02, 0.035), # P/B Cus will have some variation because of memory  
#                             'BCU' : np.random.uniform(0.01, 0.02),
#                             'SkipCU' : np.random.uniform(0.002, 0.003), # would be much less because no transform computation, only memory                                                          
                             
                             }


# ========================================
# Frame size params
# I/P/B frame : weibull dist [a,c,loc,scale]
# ========================================

HEVCWLPARAMS_IPB_FR_SIZE_PARAMS = {                  
                  'ACTION' : {
                                'I-Fr':  [4.76E+01 , 5.15E-01 , 5.81E-04 , 1.93E-04 ],
                                'P-Fr':  [1.57E+01 , 7.90E-01 , 2.71E-05 , 4.41E-04 ],
                                'B-Fr':  [1.29E+00 , 7.38E-01 , 2.46E-05 , 3.08E-04 ],    
                                
                                'I-Fr-minmax' :[1.18E-03 ,1.90E-02],
                                'P-Fr-minmax' :[3.54E-05 ,1.30E-02],
                                'B-Fr-minmax' :[2.46E-05 ,4.46E-03],       
                              },
                                   
                      
                  'DOC' : {                      
                            'I-Fr':  [1.31E+02 , 4.50E-01 , 0.00 , 1.52E-04 ],
                            'P-Fr':  [1.20E+01 , 5.07E-01 , 0.00 , 1.27E-04 ],
                            'B-Fr':  [1.17E+00 , 7.79E-01 , 1.99E-05 , 2.47E-04 ],
                            
                            'I-Fr-minmax' :[3.61E-04 ,2.98E-02],
                            'P-Fr-minmax' :[2.53E-05 ,2.05E-02],
                            'B-Fr-minmax' :[1.99E-05 ,9.65E-03],
                        },

                  'SPORT' : { 
                                'I-Fr':  [6.05E-01 , 2.74E+00 , 2.74E-03 , 1.81E-02 ],
                                'P-Fr':  [4.15E+00 , 9.49E-01 , 1.45E-04 , 1.56E-03 ],
                                'B-Fr':  [1.16E+00 , 8.88E-01 , 1.92E-05 , 4.15E-04 ],
                                
                                'I-Fr-minmax' :[2.91E-03 ,3.89E-02],
                                'P-Fr-minmax' :[2.17E-05 ,2.46E-02],
                                'B-Fr-minmax' :[1.92E-05 ,1.08E-02],
                            },

                  'SPEECH' : {
                                'I-Fr':  [4.56E-01 , 6.21E+00 , 1.29E-02 , 3.69E-03 ],
                                'P-Fr':  [1.60E+00 , 1.18E+00 , 3.79E-05 , 4.17E-04 ],
                                'B-Fr':  [8.45E+01 , 2.66E-01 , 2.31E-05 , 1.10E-07 ],
                                
                                'I-Fr-minmax' :[1.04E-03 ,1.75E-02],
                                'P-Fr-minmax' :[4.09E-05 ,3.27E-03],
                                'B-Fr-minmax' :[2.42E-05 ,7.56E-04],
                              },

                  'ANIM' : {  
                                'I-Fr':  [3.36E+00 , 1.23E+00 , 0.00 , 1.39E-02 ],
                                'P-Fr':  [5.51E+00 , 4.59E-01 , 2.23E-05 , 1.70E-04 ],
                                'B-Fr':  [9.80E-01 , 7.34E-01 , 3.17E-05 , 2.57E-04 ],
                                
                                'I-Fr-minmax' :[1.02E-04 ,5.83E-02],
                                'P-Fr-minmax' :[3.50E-05 ,3.71E-02],
                                'B-Fr-minmax' :[3.17E-05 ,8.09E-03],
                            }
                  }

# ========================================
# GoP content
# P,B frame numbers : weibull dist [a,c,scale,loc]
# ========================================

HEVCWLPARAMS_GOP_PB_NUM_PARAMS = {                  
                  'ACTION' : [228.16, 0.88, 1.5, 0.0],                      
                  'DOC' : [68.03, 0.72, 1.5, 0.0],
                  'SPORT' : [217.36, 0.91, 1.5, 0.0],
                  'SPEECH' : [542.54, 1.09, 1.5, 0.0],
                  'ANIM' : [52.06, 0.67, 1.5, 0.0]
                  }


# ========================================
# CU size probabilities
# Intra/Inter frame CU sizes
# (nb : may not add up to 100%)
# cu sizes order : 64x64,32x32,16x16,8x8,4x4
# ========================================
HEVCWLPARAMS_CU_SIZE_PROBABILITIES = \
{
      'ACTION' : {
                  'Intra' : [0.049, 0.14, 0.41, 0.34, 0.056],
                  'Inter' : [0.15, 0.335, 0.325, 0.19, 0.0],                  
                  },                      
      'DOC' : {
                  'Intra' : [0.098, 0.262, 0.404, 0.183, 0.053],
                  #'Inter' : [0.321, 0.351, 0.314, 0.11, 0.0],
                  'Inter' : [0.27, 0.31, 0.27, 0.15, 0.0]                  
                  },
      'SPORT' : {
                  'Intra' : [0.038, 0.122, 0.237, 0.363, 0.24],
                  'Inter' : [0.15, 0.28, 0.23, 0.34, 0.0],                  
                  },
      'SPEECH' : {
                  'Intra' : [0.015, 0.041, 0.234, 0.409, 0.301],
                  'Inter' : [0.27, 0.34, 0.275, 0.112, 0.0],                  
                  },
      'ANIM' : {
                  'Intra' : [0.037, 0.116, 0.295, 0.389, 0.164],
                  'Inter' : [0.20, 0.29, 0.18, 0.33, 0.0],                  
                  },                  
}


def _print_cusizeprobs_sum():
    print "_print_cusizeprobs_sum ::"
    for k_m, m in HEVCWLPARAMS_CU_SIZE_PROBABILITIES.iteritems():
        for k_i, i in m.iteritems():
            print "%s, %s, %.3f, %d"% (k_m, k_i, np.sum(i), len(i))

# ========================================
# CU type probabilities
# P/B frame CU types
# (nb : may not add up to 100%)
# cu types : I_CU, P_CU, B_CU, Skip_CU
# ========================================
HEVCWLPARAMS_CU_TYPE_PROBABILITIES = \
{
      'ACTION' : {
                  'I-fr' : [1.0, 0.0, 0.0, 0.0],
                  'P-fr' : [0.455, 0.235, 0.0, 0.31],
                  'B-fr' : [0.075, 0.194, 0.082, 0.65],                  
                  },                      
      'DOC' : {
                  'I-fr' : [1.0, 0.0, 0.0, 0.0],
                  'P-fr' : [0.22, 0.404, 0.0, 0.377],
                  'B-fr' : [0.041, 0.179, 0.094, 0.686],               
                  },
      'SPORT' : {
                  'I-fr' : [1.0, 0.0, 0.0, 0.0],
                  'P-fr' : [0.175, 0.405, 0.0, 0.42],
                  'B-fr' : [0.015, 0.155, 0.124, 0.704],                  
                  },
      'SPEECH' : {
                  'I-fr' : [1.0, 0.0, 0.0, 0.0],
                  'P-fr' : [0.034, 0.156, 0.0, 0.81],
                  'B-fr' : [0.0, 0.042, 0.024, 0.932],                
                  },
      'ANIM' : {
                  'I-fr' : [1.0, 0.0, 0.0, 0.0],
                  'P-fr' : [0.077, 0.285, 0.0, 0.638],
                  'B-fr' : [0.015, 0.082, 0.05, 0.853],                
                  },                  
}

def _print_cutypeprobs_sum():
    print "_print_cutypeprobs_sum ::"
    for k_m, m in HEVCWLPARAMS_CU_TYPE_PROBABILITIES.iteritems():
        for k_i, i in m.iteritems():
            print "%s, %s, %.3f, %d"% (k_m, k_i, np.sum(i), len(i))



# ========================================
# Reference frame selection probability
# with respect to the frame type
# Target Frame type : P, B
# Possible ref frame types : I, P, B
# ========================================
HEVCWLPARAMS_REFFR_SELECTION_PROBABILITIES = \
{
    # target-fr : [I,P,B]
    "P" : [0.55, 0.45, 0.0],
    "B" : [0.60, 0.30, 0.10]
} 

HEVCWLPARAMS_DATAPAYLOAD_MEDIAN_PROPORTIONS = \
{

      'ACTION' : {
                  'P<-I' : 0.55, 
                  'P<-P' : 0.55,
                  'B<-I' : 0.55,                  
                  'B<-P' : 0.55,
                  'B<-B' : 0.55
                  },                      
      'DOC' : {
                  'P<-I' :  0.90,
                  'P<-P' :  0.80,
                  'B<-I' :  0.70,                
                  'B<-P' :  0.65,
                  'B<-B' :  0.70
                  },   
      'SPORT' : {
                  'P<-I' :  0.90,
                  'P<-P' :  0.80,
                  'B<-I' :  0.70,                
                  'B<-P' :  0.65,
                  'B<-B' :  0.70
                  },   
      'SPEECH' : {
                  'P<-I' :  0.95,
                  'P<-P' :  0.90,
                  'B<-I' :  0.80,                
                  'B<-P' :  0.75,
                  'B<-B' :  0.80
                  },   
      'ANIM' : {
                  'P<-I' :  0.90,
                  'P<-P' :  0.85,
                  'B<-I' :  0.75,                
                  'B<-P' :  0.70,
                  'B<-B' :  0.75
                  },   
}

# ========================================
# If all the CTUs are pregenerated then
# they will need to be swapped to get 
# some randomisation
# ========================================
HEVCWLPARAMS_CTU_SWAP_32_16_COUNT = 20    
HEVCWLPARAMS_CTU_SWAP_32_8_COUNT = 20
HEVCWLPARAMS_CTU_SWAP_32_4_COUNT = 20
HEVCWLPARAMS_CTU_SWAP_16_8_COUNT = 20
HEVCWLPARAMS_CTU_SWAP_8_4_COUNT = 20





#_print_cusizeprobs_sum()
#print "-------"
#_print_cutypeprobs_sum()
#print HEVCWLPARAMS_POSSIBLE_GOP_SIZES(10,37)

