#!/bin/bash

export PYTHONPATH=$PYTHONPATH:/shared/cssamba0/staffstore/hrm506/simpy-3.0.5/

rm -f ../*.out
rm -f *.out
rm -f ../logs/*.out

cd ..


#noc_sizes=(3 4 7 8 10)

#for i in "${noc_sizes[@]}"
#do
#     outname="logs/runexp_ol_vs_cl_${i}_${i}.out"
#     nohup python -u RunSim_Exp_ClosedLoop_vs_OpenLoop.py --noc_h=$i --noc_w=$i &> $outname &
#done


# nearest neighbour vs lowest util - for different noc sizes

### 2x2
outname="logs/runexp_nntest_2_2_nonnn.out"
nohup python -u RunSim_Exp_NNMapping.py --noc_h=2 --noc_w=2 --mp_sch=10 --pr_sch=4 --com_sch=0 &> $outname &
outname="logs/runexp_nntest_2_2_nn.out"
nohup python -u RunSim_Exp_NNMapping.py --noc_h=2 --noc_w=2 --mp_sch=0 --pr_sch=0 --com_sch=831 &> $outname &

### 3x3
outname="logs/runexp_nntest_3_3_nonnn.out"
nohup python -u RunSim_Exp_NNMapping.py --noc_h=3 --noc_w=3 --mp_sch=10 --pr_sch=4 --com_sch=0 &> $outname &
outname="logs/runexp_nntest_3_3_nn.out"
nohup python -u RunSim_Exp_NNMapping.py --noc_h=3 --noc_w=3 --mp_sch=0 --pr_sch=0 --com_sch=831 &> $outname &

### 4x4
outname="logs/runexp_nntest_4_4_nonnn.out"
nohup python -u RunSim_Exp_NNMapping.py --noc_h=4 --noc_w=4 --mp_sch=10 --pr_sch=4 --com_sch=0 &> $outname &
outname="logs/runexp_nntest_4_4_nn.out"
nohup python -u RunSim_Exp_NNMapping.py --noc_h=4 --noc_w=4 --mp_sch=0 --pr_sch=0 --com_sch=831 &> $outname &

### 6x6
outname="logs/runexp_nntest_6_6_nonnn.out"
nohup python -u RunSim_Exp_NNMapping.py --noc_h=6 --noc_w=6 --mp_sch=10 --pr_sch=4 --com_sch=0 &> $outname &
outname="logs/runexp_nntest_6_6_nn.out"
nohup python -u RunSim_Exp_NNMapping.py --noc_h=6 --noc_w=6 --mp_sch=0 --pr_sch=0 --com_sch=831 &> $outname &

### 8x8
outname="logs/runexp_nntest_8_8_nonnn.out"
nohup python -u RunSim_Exp_NNMapping.py --noc_h=8 --noc_w=8 --mp_sch=10 --pr_sch=4 --com_sch=0 &> $outname &
outname="logs/runexp_nntest_8_8_nn.out"
nohup python -u RunSim_Exp_NNMapping.py --noc_h=8 --noc_w=8 --mp_sch=0 --pr_sch=0 --com_sch=831 &> $outname &

### 9x8
outname="logs/runexp_nntest_9_8_nonnn.out"
nohup python -u RunSim_Exp_NNMapping.py --noc_h=9 --noc_w=8 --mp_sch=10 --pr_sch=4 --com_sch=0 &> $outname &
outname="logs/runexp_nntest_9_8_nn.out"
nohup python -u RunSim_Exp_NNMapping.py --noc_h=9 --noc_w=8 --mp_sch=0 --pr_sch=0 --com_sch=831 &> $outname &

### 10x10
outname="logs/runexp_nntest_10_10_nonnn.out"
nohup python -u RunSim_Exp_NNMapping.py --noc_h=10 --noc_w=10 --mp_sch=10 --pr_sch=4 --com_sch=0 &> $outname &
outname="logs/runexp_nntest_10_10_nn.out"
nohup python -u RunSim_Exp_NNMapping.py --noc_h=10 --noc_w=10 --mp_sch=0 --pr_sch=0 --com_sch=831 &> $outname &

