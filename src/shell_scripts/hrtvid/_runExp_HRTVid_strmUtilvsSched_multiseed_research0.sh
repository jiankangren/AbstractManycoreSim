#!/bin/bash

run_simulation()
{
#AC,MP,CMB,PR
outname="logs/runexp_hrtvid_ac${1}_mp${2}_cmb${3}_pr${4}_seed${5}.out"
nohup python -u RunSim_Exp_HRTVideo_Util_vs_Schedulability_main.py --ac_type=$1 --mp_type=$2 --cmbmppri_type=$3 --pr_type=$4 --forced_seed=$5 &> $outname &
}

export PYTHONPATH=$PYTHONPATH:/shared/cssamba0/staffstore/hrm506/simpy-3.0.5/

full_random_seed_array=(81665 33749 43894 26358 80505 \
83660 22817 70263 29917 26044 \
5558 76891 22250 42198 18065 \
74076 98652 21149 50399 64217 \
44117 57824 42267 83200 99108 \
95928 53864 44289 77379 80521 \
88117 23327 73337 94064 31982 \
6878 66093 69541)

batch1_random_seed_array=(81665 33749 43894 26358 70505 \
83660 22817 70263 29917 26044 \
76891)

batch2_random_seed_array=(50399 64217 \
44117 57824 42267 83200 99108 \
95928 53864 44289)

batch3_random_seed_array=(77379 80521 \
88117 23327 73337 94064 31982 22250)

batch4_random_seed_array=(6878 66093 69541 18065 74076 98652 21149 42198 5558)

small_random_seed_array=(80505 1234)

#rm -f ../*.out
#rm -f *.out
#rm -f ../logs/*.out

cd ..

#############################################################################################################
# No Admission Control (NOAC), fixed priority = 4 (low res first), varying mapping types
#############################################################################################################
#AC=12

# Low-comms_v1 mapping
#MP=0;CMB=840;PR=4
#run_simulation $AC $MP $CMB $PR

# Low-comms_v2 mapping
#MP=0;CMB=841;PR=4
#run_simulation $AC $MP $CMB $PR

# TightFit_v1 mapping
#MP=0;CMB=842;PR=4
#run_simulation $AC $MP $CMB $PR

# Carvalho_BN mapping
#MP=0;CMB=832;PR=4
#run_simulation $AC $MP $CMB $PR

# SingleNode_lowest_utilised mapping
#MP=0;CMB=850;PR=4
#run_simulation $AC $MP $CMB $PR

# Lowest Utilised mapping
#MP=10;CMB=0;PR=4
#run_simulation $AC $MP $CMB $PR

# Shortest TQ(via RTApp) mapping
#MP=12;CMB=0;PR=4
#run_simulation $AC $MP $CMB $PR

# Kaushik - PP
#MP=0;CMB=833;PR=4
#run_simulation $AC $MP $CMB $PR

#############################################################################################################
# Deterministic Admission Control (DAC), fixed priority = 4 (low res first), varying mapping types
#############################################################################################################
AC=11

for seed in "${batch4_random_seed_array[@]}"
do
	# Low-comms_v2 mapping
	#MP=0;CMB=841;PR=4
	#run_simulation $AC $MP $CMB $PR $seed

	# TightFit_v1 mapping
	MP=0;CMB=842;PR=4
	run_simulation $AC $MP $CMB $PR $seed

	# Carvalho_BN mapping
	#MP=0;CMB=834;PR=4
	#run_simulation $AC $MP $CMB $PR $seed

	# Lowest Utilised mapping
	#MP=10;CMB=0;PR=4
	#run_simulation $AC $MP $CMB $PR $seed

	# Shortest TQ(via RTApp) mapping
	MP=12;CMB=0;PR=4
	run_simulation $AC $MP $CMB $PR $seed

	# Kaushik - PP
	MP=0;CMB=833;PR=4
	run_simulation $AC $MP $CMB $PR $seed

done
