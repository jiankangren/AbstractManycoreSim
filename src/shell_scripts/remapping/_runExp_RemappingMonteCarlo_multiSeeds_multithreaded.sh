#!/bin/bash

export PYTHONPATH=$PYTHONPATH:/shared/cssamba0/staffstore/hrm506/simpy-3.0.5/

#rm -f ../*.out
#rm -f *.out
#rm -f ../logs/*.out


#random_seed_array=(26044 29917 83200 99108 73337 \
#                    43894 5558 74076 21149 77379)

random_seed_array=(81665 33749 43894 53784 26358 \
80505 83660 22817 70263 29917 \
26044 6878 66093 69541 5558 \
76891 22250 69433 42198 18065 \
74076 98652 21149 50399 64217 \
44117 57824 42267 83200 99108 \
95928 53864 44289 77379 80521 \
88117 23327 73337 94064 31982)



####### move to correct dir level ######
cd ..


####### make the folders #######
for seed in "${random_seed_array[@]}"
do
	dirname="experiment_data/remapping_psbased_montecarlo/seed_${seed}"
	mkdir -p $dirname
done


####### run script #######
outname="logs/runexp_remappingmc.out"
nohup python -u RunSim_Exp_PSBasedRemapping_MCTest_main_multithreaded.py &> $outname &
