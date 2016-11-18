#!/bin/bash
export PYTHONPATH=$PYTHONPATH:/shared/storage/cs/staffstore/hrm506/simpy-3.0.5/
export PYTHONPATH=$PYTHONPATH:/shared/storage/cs/staffstore/hrm506/networkx-1.10/networkx-1.10


#full_random_seed_array=(81665 33749 43894 26358 80505 \
#83660 22817 70263 29917 26044)

full_random_seed_array=(81665 33749 43894 26358 80505 \
83660 22817 70263 29917 26044 \
5558 76891 22250 42198 18065 \
74076 98652 21149 50399 64217)


#full_random_seed_array=(81665 33749 43894 26358 80505 83660)


cd ../../libApplicationModel/



for seed in "${full_random_seed_array[@]}"
do
	outname="../logs/synthworkloadval_seed$seed.out"
	nohup python -u HEVCSyntheticWorkloadValidator.py --seed=$seed --num_gops=20 --nbmax=4 --gop_len=36 &> $outname &
done

