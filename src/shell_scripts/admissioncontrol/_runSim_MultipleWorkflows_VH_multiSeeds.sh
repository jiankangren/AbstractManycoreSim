#!/bin/bash

export PYTHONPATH=$PYTHONPATH:/shared/cssamba0/staffstore/hrm506/simpy-3.0.5/

rm -f *.out
rm -f logs/*.out


random_seed_array=(81665 33749 43894 53784 26358 80505 83660 22817 70263 29917 \
26044 6878 66093 69541 5558 \
76891 22250 69433 42198 18065 \
74076 98652 21149 50399 64217 \
44117 57824 42267 83200 99108 \
95928 53864 44289 77379 80521 \
88117 23327 73337 94064 31982)

####### make the folders #######

for seed in "${random_seed_array[@]}"
do
	dirname="experiment_data/vs_ac_test/seed_${seed}"
	mkdir $dirname
done




for seed in "${random_seed_array[@]}"
do


	###########################################
	# No-AC + deterministic-AC + vh-AC + kg-AC
	###########################################
	for i in {8,16}
	  do
		 outname="logs/runsim_allexp_seed_${seed}_${i}.out"
		 nohup python -u RunSim.py -t Exp_ACTest_MultiWorkflow_VH \
		 --wf_num=$i \
		 --test_none=1 \
		 --test_determ=1 \
		 --test_vh_single=0 \
		 --test_vh_range=1 \
		 --forced_seed=$seed \
		 --test_kg=1 &> $outname &
	  
	  done
	
	

 done	# end of seed loop
