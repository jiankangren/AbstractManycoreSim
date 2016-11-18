#!/bin/bash

export PYTHONPATH=$PYTHONPATH:/shared/cssamba0/staffstore/hrm506/simpy-3.0.5/

#rm -f ../*.out
#rm -f *.out
#rm -f ../logs/*.out

#random_seed_array=(81665 33749 43894 53784 26358 80505 83660 22817 70263 29917 \
#26044 6878 66093 69541 5558 \
#76891 22250 69433 42198 18065 \
#74076 98652 21149 50399 64217 \
#44117 57824 42267 83200 99108 \
#95928 53864 44289 77379 80521 \
#88117 23327 73337 94064 31982 \
#57177 95537 26828 84400 81474 \
#98510 34921 25534 53706 61110 \
#68553 46319 19346 83694 79292 \
#29648 94986 28524 69923 68385)

random_seed_array=(81665 33749 43894 53784 26358 \
80505 83660 22817 70263 29917 \
26044 6878 66093 69541 5558 \
76891 22250 69433 42198 18065 \
74076 98652 21149 50399 64217 \
44117 57824 42267 83200 99108 \
95928 53864 44289 77379 80521 \
88117 23327 73337 94064 31982)


#random_seed_array=(26044 42198)

####### move to correct dir level ######
cd ..


####### make the folders #######
for seed in "${random_seed_array[@]}"
do
	dirname="experiment_data/remapping_psbased/seed_${seed}"
	mkdir -p $dirname
done



####### run python script for all seeds (individual instances) #######
for seed in "${random_seed_array[@]}"
do
	###########################################
	# multiple mapping and priority schemes
	###########################################
	outname="logs/runexp_remappingbasic_seed_${seed}.out"

	nohup python -u RunSim_Exp_PSBasedRemapping.py -t Exp_RemappingBasic \
		 --forced_seed=$seed &> $outname &


 done	# end of seed loop
