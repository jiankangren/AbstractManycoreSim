#!/bin/bash

run_simulation()
{
#CONFIG, CMB, SEED
outname="logs/runexp_hevc_tile_mapping_highccrtest_${1}_cmb${2}_seed${3}.out"
nohup python -u RunSim_Exp_HEVCTile_Mapping_highCCR.py --wl_config=$1 --cmbmppri_type=$2 --forced_seed=$3 &> $outname &
}

export PYTHONPATH=$PYTHONPATH:/shared/storage/cs/staffstore/hrm506/simpy-3.0.5/
export PYTHONPATH=$PYTHONPATH:/shared/storage/cs/staffstore/hrm506/networkx-1.10/networkx-1.10
export PYTHONPATH=$PYTHONPATH:/shared/storage/cs/staffstore/hrm506/decorator-4.0.2/src/

#rm -f ../*.out
#rm -f *.out
#rm -f ../logs/*.out

cd ..
cd ..

full_random_seed_array=(81665 33749 43894 53784 26358 \
80505 83660 22817 70263 29917 \
26044 6878 66093 69541 5558 \
76891 22250 69433 42198 18065 \
74076 98652 21149 50399 64217 \
44117 57824 42267 83200 99108 \
95928 53864 44289 77379 80521)

temp_seed_array=(18065 70263)
batch0_random_seed_array=(81665 33749 43894 53784 26358)
#batch0a_random_seed_array=(53784 26358 43894)
batch1_random_seed_array=(80505 83660 22817 70263 29917)
batch2_random_seed_array=(26044 6878 66093 69541 5558)
batch3a_random_seed_array=(76891 22250 69433)
batch3b_random_seed_array=(42198 18065)
batch4_random_seed_array=(74076 98652 21149 50399 64217)
batch5_random_seed_array=(44117 57824 42267 83200 99108)
batch6_random_seed_array=(95928 53864 44289 77379 80521)

config1="WL1"
config2="WL2"
config3="WL3"

#cmb_list=(905 903) # mappers batch0
#cmb_list=(907 914) # mappers batch1
#cmb_list=(912 910 ) # mappers batch2
#cmb_list=(915 908 911) # mappers batch3

cmb_list=(905 903 907 914 912 910 915 908 911) # all mappers
#cmb_list=(905 903 914 912 910 915 907 911) # all mappers


for seed in "${batch0_random_seed_array[@]}"
do
	for cmb in "${cmb_list[@]}"
	do
		#run_simulation $config1 $cmb $seed
		run_simulation $config2 $cmb $seed
		#run_simulation $config3 $cmb $seed

	done
done

