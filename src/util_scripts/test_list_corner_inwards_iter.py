# change the order of a list outer corners to inwards           
def _get_corner_inwards_list_values(generic_list):
    result_list = []
    len_generic_list = len(generic_list)-1
    if len(generic_list)%2 == 0: # even
        for ix, x in enumerate(generic_list):
            i = ix
            j = len_generic_list-ix
            if j > i:
                result_list.append(generic_list[i])
                result_list.append(generic_list[j])
            else:                    
                break;
    else: # odd
        for ix, x in enumerate(generic_list):
            i = ix
            j = len_generic_list-ix
            if i < len_generic_list/2:
                result_list.append(generic_list[i])
                result_list.append(generic_list[j])
            elif i == len_generic_list/2:
                result_list.append(generic_list[i])
                break;
            else:                    
                break;
                
    assert(len(result_list) == len(generic_list))
    assert(set(result_list) == set(generic_list))
    
    return result_list



###### main #######
x = [1,2,3,4,5,6]

print _get_corner_inwards_list_values(x)