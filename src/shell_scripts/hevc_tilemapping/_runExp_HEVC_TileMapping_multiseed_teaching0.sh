#!/bin/bash

run_simulation()
{
#CONFIG, CMB, SEED
outname="logs/runexp_hevc_tile_mapping_conf_${1}_cmb${2}_seed${3}.out"
nohup python -u RunSim_Exp_HEVCTile_Mapping.py --wl_config=$1 --cmbmppri_type=$2 --forced_seed=$3 &> $outname &
}

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

temp_seed_array=(18065 70263)

batch0_random_seed_array=(81665 33749 43894 26358 80505)
batch1_random_seed_array=(83660 22817 70263 29917 26044)
batch2_random_seed_array=(5558 76891 22250 42198 18065)
batch3_random_seed_array=(74076 98652 21149 50399 64217)
batch4_random_seed_array=(44117 57824 42267 83200 99108)
batch5_random_seed_array=(95928 53864 44289 77379 80521)
batch6_random_seed_array=(87288	21349 68546	74944 94329)
batch7_random_seed_array=(90611	69799 85870	26771 75638)

config1="WL1"
config2="WL2"
config3="WL3"

teaching0_serv_cmb_list=(920 921)
research0_serv_cmb_list=(922 901)
compute_serv_cmb_list=(903 902)


all_cmb_list=(903 908 905 906 907 909 910)

for seed in "${batch5_random_seed_array[@]}"
do
	for cmb in "${all_cmb_list[@]}"
	do
		#run_simulation $config1 $cmb $seed
		run_simulation $config2 $cmb $seed
		#run_simulation $config3 $cmb $seed

	done
done
