import numpy as np
import pprint

def _generate_list_of_random_nums(N, sum):
        result = []
        for i in xrange(N):
            rn = np.sum(result)
            c = np.random.randint(rn, sum+2-rn)
            result.append(c)
        
        final_sum = np.sum(result)
        
        assert(final_sum == sum), "calc_sum=%d" % final_sum
        
        return result


def _generate_list_of_random_nums_v2(N, sum):
        result = []

	rn = np.random.randint(1,sum, size=N)
	
	print rn

	sum_rn = np.sum(rn)
	
	rn = rn/sum
	
        final_sum = np.sum(rn)


        assert(final_sum == sum), "calc_sum=%d" % final_sum

	return rn

def _generate_list_of_random_nums_v3(N, sum):
	result = [0]*N

	ix = 0
	while(np.sum(result) < sum):
	    if(np.random.rand()>0.5):
		result[ix]+=1
	    
            ix+=1
	    if ix==N:
		ix=0


        final_sum = np.sum(result)
        assert(final_sum == sum), "calc_sum=%d" % final_sum

	return result








#pprint.pprint(_generate_list_of_random_nums(10, 100))
#pprint.pprint(_generate_list_of_random_nums_v2(10, 100))
pprint.pprint(_generate_list_of_random_nums_v3(100, 1000))


