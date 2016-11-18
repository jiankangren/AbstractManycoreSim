#!/bin/bash

export PYTHONPATH=$PYTHONPATH:/shared/cssamba0/staffstore/hrm506/simpy-3.0.5/

#rm -f ../*.out
#rm -f *.out
#rm -f ../logs/*.out

noc_size=(7 10 12 20 32)

####### move to correct dir level ######
cd ..



####### run python script for all seeds (individual instances) #######
for nocsize in "${noc_size[@]}"
do
	###########################################
	# multiple mapping and priority schemes
	###########################################
	outname="logs/runexp_remappingbasic_ns_${nocsize}.out"

	nohup python -u RunSim_Exp_PSBasedRemapping.py -t Exp_RemappingBasic \
		 --noc_w=$nocsize --noc_h=$nocsize &> $outname &


 done	# end of seed loop
