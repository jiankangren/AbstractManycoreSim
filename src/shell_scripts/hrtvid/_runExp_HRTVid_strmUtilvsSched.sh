#!/bin/bash

run_simulation()
{
#AC,MP,CMB,PR
outname="logs/runexp_hrtvid_ac${1}_mp${2}_cmb${3}_pr${4}.out"
nohup python -u RunSim_Exp_HRTVideo_Util_vs_Schedulability_main.py --ac_type=$1 --mp_type=$2 --cmbmppri_type=$3 --pr_type=$4 &> $outname &
}


export PYTHONPATH=$PYTHONPATH:/shared/cssamba0/staffstore/hrm506/simpy-3.0.5/

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
MP=0;CMB=834;PR=4
run_simulation $AC $MP $CMB $PR

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
