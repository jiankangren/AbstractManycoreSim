#!/bin/bash

run_simulation()
{
#CONFIG, CMB, SEED
outname="logs/runexp_hevc_tile_mapping_withmemhighccr_conf_${1}_cmb${2}_memp${3}_seed${4}.out"
nohup python -u RunSim_Exp_HEVCTile_Mapping_withSmartMemHighCCR.py --wl_config=$1 --cmbmppri_type=$2 --memp_select=$3 --forced_seed=$4 &> $outname &
}

#export OPENBLAS_NUM_THREADS=1
#export GOTO_NUM_THREADS=1
#export OMP_NUM_THREADS=1

export PYTHONPATH=$PYTHONPATH:/shared/storage/cs/staffstore/hrm506/simpy-3.0.5/
export PYTHONPATH=$PYTHONPATH:/shared/storage/cs/staffstore/hrm506/networkx-1.10/networkx-1.10

#rm -f ../*.out
#rm -f *.out
#rm -f ../logs/*.out

cd ../..


#### Experimental seeds ####

full_random_seed_array=(81665 33749 43894 53784 26358 \
80505 83660 22817 70263 29917 \
26044 6878 66093 69541 5558 \
76891 22250 69433 42198 18065 \
74076 98652 21149 50399 64217 \
44117 57824 42267 83200 99108 \
95928 53864 44289 77379 80521)


batch0a_random_seed_array=(81665 33749 43894)
batch0b_random_seed_array=(53784 26358)

batch1a_random_seed_array=(80505 83660 22817)
batch1b_random_seed_array=(70263 29917)

batch2a_random_seed_array=(26044 6878 66093)
batch2b_random_seed_array=(69541 5558)

batch3a_random_seed_array=(76891 22250 69433)
batch3b_random_seed_array=(42198 18065)

batch4a_random_seed_array=(74076 98652 21149)
batch4b_random_seed_array=(50399 64217)

batch5a_random_seed_array=(44117 57824 42267)
batch5b_random_seed_array=(83200 99108)

batch6a_random_seed_array=(95928 53864 44289)
batch6b_random_seed_array=(77379 80521)

#### Workload configurations ####
#config1="WL1"
config2="WL2"
#config3="WL3"
#config4="WL4"

#### Mapping types ####
all_cmb_list=(905 914 903 912)

#### MMCP selection types ####
all_memp_types=(0 1 3 31 36 37)


for seed in "${batch2a_random_seed_array[@]}"
do
	for cmb in "${all_cmb_list[@]}"
	do
			for memp in "${all_memp_types[@]}"
			do
				#run_simulation $config1 $cmb $memp $seed
				run_simulation $config2 $cmb $memp $seed
				#run_simulation $config3 $cmb $memp $seed
				#run_simulation $config4 $cmb $memp $seed	
			done
	done
done
