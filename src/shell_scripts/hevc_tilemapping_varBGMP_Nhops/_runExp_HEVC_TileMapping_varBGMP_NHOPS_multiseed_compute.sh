#!/bin/bash

run_simulation()
{
#CONFIG, CMB, SEED, NHOPS_H, NHOPS_M, NHOPS_L
outname="logs/runexp_hevc_bgmpnhops_conf_${1}_cmb${2}_mmemp${3}_seed${4}_nhops_h${5}_m${6}_l${7}.out"
nohup python -u RunSim_Exp_HEVCTile_BGClustering_Mapping_varNHops.py \
--wl_config=$1 --cmbmppri_type=$2 --memp_select=$3 --forced_seed=$4 \
--nhgt_h=$5 --nhgt_m=$6 --nhgt_l=$7 &> $outname &

}

export OPENBLAS_NUM_THREADS=1
export GOTO_NUM_THREADS=1
export OMP_NUM_THREADS=1
export PYTHONPATH=$PYTHONPATH:/shared/storage/cs/staffstore/hrm506/simpy-3.0.5/
export PYTHONPATH=$PYTHONPATH:/shared/storage/cs/staffstore/hrm506/networkx-1.10/networkx-1.10

#rm -f ../*.out
#rm -f *.out
#rm -f ../logs/*.out

cd ../..

full_random_seed_array=(81665 33749 43894 26358 80505 \
83660 22817 70263 29917 26044 \
5558 76891 22250 42198 18065 \
74076 98652 21149 50399 64217)

temp_seed_array=(33749 43894 26358 80505)

batch0_random_seed_array=(81665 33749 43894 26358 80505)
batch1_random_seed_array=(83660 22817 70263 29917 26044)
batch2_random_seed_array=(5558 76891 22250 42198 18065)
batch3_random_seed_array=(74076 98652 21149 50399 64217)
batch4_random_seed_array=(44117 57824 42267 83200 99108)
batch5_random_seed_array=(95928 53864 44289 77379 80521)
batch6_random_seed_array=(87288	21349 68546 74944 94329)
batch7_random_seed_array=(90611	69799 85870 26771 75638)

config1="WL1"
config2="WL2"
config3="WL3"

# CL=905, CL-IPB=911, CL-IPB-FLMP=913, LU=903, CL-FFI=910, LU-FFI=908, BGROUPS=914
cmb_type=914
# mmcDist=0, mmcLU=1, mmcLM=2, mmcLUDist=3
mpsel_type=0

nhgt_h_list=(1 2 4 6 8)
nhgt_m_list=(1 2 4 6 8)
nhgt_l_list=(1 2 4 6 8)

fixed_seed=26358

for nhgt_h in "${nhgt_h_list[@]}"
do
	for nhgt_m in "${nhgt_m_list[@]}"
	do	
		for nhgt_l in "${nhgt_l_list[@]}"
		do	
			run_simulation $config2 $cmb_type $mpsel_type $fixed_seed $nhgt_h $nhgt_m $nhgt_l
		done
	done
done
