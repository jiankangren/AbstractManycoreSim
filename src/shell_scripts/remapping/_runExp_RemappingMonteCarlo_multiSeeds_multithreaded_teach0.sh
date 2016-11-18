#!/bin/bash

export PYTHONPATH=$PYTHONPATH:/shared/cssamba0/staffstore/hrm506/simpy-3.0.5/

#rm -f ../*.out
#rm -f *.out
#rm -f ../logs/*.out


random_seed_array=(26044 29917 83200 99108 73337 \
                    43894 5558 74076 21149 77379)


####### move to correct dir level ######
cd ..


####### make the folders #######
for seed in "${random_seed_array[@]}"
do
	dirname="experiment_data/remapping_psbased_montecarlo/seed_${seed}"
	mkdir -p $dirname
done


####### run script #######
outname="logs/runexp_remappingmc_teach0.out"
nohup python -u RunSim_Exp_PSBasedRemapping_MCTest_main_multithreaded.py &> $outname &
