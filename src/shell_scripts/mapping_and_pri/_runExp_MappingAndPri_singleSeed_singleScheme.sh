#!/bin/bash

export PYTHONPATH=$PYTHONPATH:/shared/cssamba0/staffstore/hrm506/simpy-3.0.5/

rm -f ../*.out
rm -f *.out
rm -f ../logs/*.out


#random_seed_array=(81665 33749 43894 53784 26358 80505 83660 22817 70263 29917 \
#26044 6878 66093 69541 5558 \
#76891 22250 69433 42198 18065 \
#74076 98652 21149 50399 64217 \
#44117 57824 42267 83200 99108 \
#95928 53864 44289 77379 80521 \
#88117 23327 73337 94064 31982)

single_seed=81665

####### move to correct dir level ######
cd ..


####### make the folder #######
dirname="experiment_data/mapping_and_pri_schemes/seed_${single_seed}"
mkdir -p $dirname



####### run python script for all seeds (individual instances) #######

###########################################
# multiple mapping and priority schemes
###########################################
for i in {8,12}
  do

	mp_sch=8

	for pr_sch in {0,1,2,3,4}
		do
		 outname="logs/runexp_mappingandpri_seed_${single_seed}_${i}.out"
		 nohup python -u RunSim_Exp_MappingAndPriority.py -t Exp_MappingAndPri \
		 --wf_num=$i \
		 --forced_seed=$single_seed\
		 --run_full_fact_schemes=0 \
		 --pri_ass_scheme=$pr_sch	\
		 --mapping_scheme=$mp_sch &> $outname &
		done

  done

