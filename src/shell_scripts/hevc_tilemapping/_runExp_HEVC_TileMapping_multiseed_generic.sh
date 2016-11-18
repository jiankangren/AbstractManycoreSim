#!/bin/bash

run_simulation()
{
#CONFIG, CMB, SEED
outname="logs/runexp_hevc_tile_mapping_conf_${1}_cmb${2}_seed${3}.out"
nohup python -u RunSim_Exp_HEVCTile_Mapping.py --wl_config=$1 --cmbmppri_type=$2 --forced_seed=$3 &> $outname &
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

batch0_random_seed_array=(81665 33749 43894 53784 26358 \
80505 83660 22817 70263 29917 \
26044 6878 66093 69541 5558 \
76891)
batch1_random_seed_array=(22250 69433 42198 18065 \
74076 98652 21149 50399 64217 \
44117 57824 42267 83200 99108 \
95928 53864 44289 77379 80521)

config1="WL1"
config2="WL2"
config3="WL3"

teaching0_serv_cmb_list=(920 921)
research0_serv_cmb_list=(922 901)
compute_serv_cmb_list=(903 902)


#cmb_list=(905 903 907 914 912) # primary mappers
#cmb_list=(910 915 908)	# seconday mappers

cmb_list=(905 903 907 914 912 910 915 908 911) # all mappers

for seed in "${batch0_random_seed_array[@]}"
do
	for cmb in "${cmb_list[@]}"
	do
		#run_simulation $config1 $cmb $seed
		run_simulation $config2 $cmb $seed
		#run_simulation $config3 $cmb $seed

	done
done
