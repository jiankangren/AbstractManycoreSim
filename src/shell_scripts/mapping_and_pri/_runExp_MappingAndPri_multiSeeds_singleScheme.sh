#!/bin/bash

export PYTHONPATH=$PYTHONPATH:/shared/cssamba0/staffstore/hrm506/simpy-3.0.5/

rm -f ../*.out
rm -f *.out
rm -f ../logs/*.out


random_seed_array=(81665 33749 43894 53784 26358 80505 83660 22817 70263 29917 \
26044 6878 66093 69541 5558 \
76891 22250 69433 42198 18065 \
74076 98652 21149 50399 64217 \
44117 57824 42267 83200 99108 \
95928 53864 44289 77379 80521 \
88117 23327 73337 94064 31982)

#single_seed = 12345

####### move to correct dir level ######
cd ..


####### make the folders #######
for seed in "${random_seed_array[@]}"
do
	dirname="experiment_data/mapping_and_pri_schemes/seed_${seed}"
	mkdir -p $dirname
done



####### run python script for all seeds (individual instances) #######
for seed in "${random_seed_array[@]}"
do
	###########################################
	# multiple mapping and priority schemes
	###########################################
	for i in {8,12}
	  do
		 outname="logs/runexp_mappingandpri_seed_${seed}_${i}.out"
		 nohup python -u RunSim_Exp_MappingAndPriority.py -t Exp_MappingAndPri \
		 --wf_num=$i \
		 --forced_seed=$seed \
		 --run_full_fact_schemes=0 \
		 --pri_ass_scheme=891	\
		 --mapping_scheme=891 &> $outname &

	  done
 done	# end of seed loop
