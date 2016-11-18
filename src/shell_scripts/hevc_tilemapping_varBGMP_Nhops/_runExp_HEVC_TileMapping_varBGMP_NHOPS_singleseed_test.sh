#!/bin/bash

run_simulation()
{
#CONFIG, CMB, SEED, NHOPS_H, NHOPS_M, NHOPS_L
outname="logs/runexp_hevc_bgmpnhops_conf_${1}_cmb${2}_mmemp${3}_seed${4}_nhops_h${5}_m${6}_l${7}.out"
nohup python -u RunSim_Exp_HEVCTile_BGClustering_Mapping_varNHops.py \
--wl_config=$1 --cmbmppri_type=$2 --memp_select=$3 --forced_seed=$4 \
--nhgt_h=$5 --nhgt_m=$6 --nhgt_l=$7 &> $outname &

}

export PYTHONPATH=$PYTHONPATH:/shared/storage/cs/staffstore/hrm506/simpy-3.0.5/
export PYTHONPATH=$PYTHONPATH:/shared/storage/cs/staffstore/hrm506/networkx-1.10/networkx-1.10

#rm -f ../*.out
#rm -f *.out
#rm -f ../logs/*.out

cd ../..

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

fixed_seed=43894

nhgt_h=8
nhgt_m=6
nhgt_l=8


run_simulation $config2 $cmb_type $mpsel_type $fixed_seed $nhgt_h $nhgt_m $nhgt_l
