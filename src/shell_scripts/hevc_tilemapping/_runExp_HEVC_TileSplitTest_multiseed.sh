#!/bin/bash

export PYTHONPATH=$PYTHONPATH:/shared/cssamba0/staffstore/hrm506/simpy-3.0.5/
export PYTHONPATH=$PYTHONPATH:/shared/cssamba0/staffstore/hrm506/networkx-1.10/networkx-1.10


#rm -f ../*.out
#rm -f *.out
#rm -f ../logs/*.out

cd ..

full_random_seed_array=(81665 33749 43894 26358 80505 \
83660 22817 70263 29917 26044 \
5558 76891 22250 42198 18065 \
74076 98652 21149 50399 64217)

temp_seed_array=(18065 70263 26044 29917 80505 81665)


for seed in "${full_random_seed_array[@]}"
do

	outname="logs/runexp_hevc_splittest_simple_seed_${seed}.out"
	nohup python -u RunSim_Exp_HEVCTileSplitTest.py --forced_seed=$seed &> $outname &

done
