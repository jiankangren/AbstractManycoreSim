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

outname="logs/runexp_ol_vs_cl_2_2.out"
nohup python -u RunSim_Exp_ClosedLoop_vs_OpenLoop.py --noc_h=2 --noc_w=2 &> $outname &

outname="logs/runexp_ol_vs_cl_3_3.out"
nohup python -u RunSim_Exp_ClosedLoop_vs_OpenLoop.py --noc_h=3 --noc_w=3 &> $outname &

outname="logs/runexp_ol_vs_cl_4_4.out"
nohup python -u RunSim_Exp_ClosedLoop_vs_OpenLoop.py --noc_h=4 --noc_w=4 &> $outname &

outname="logs/runexp_ol_vs_cl_5_5.out"
nohup python -u RunSim_Exp_ClosedLoop_vs_OpenLoop.py --noc_h=5 --noc_w=5 &> $outname &

outname="logs/runexp_ol_vs_cl_6_6.out"
nohup python -u RunSim_Exp_ClosedLoop_vs_OpenLoop.py --noc_h=6 --noc_w=6 &> $outname &

outname="logs/runexp_ol_vs_cl_7_7.out"
nohup python -u RunSim_Exp_ClosedLoop_vs_OpenLoop.py --noc_h=7 --noc_w=7 &> $outname &

outname="logs/runexp_ol_vs_cl_8_8.out"
nohup python -u RunSim_Exp_ClosedLoop_vs_OpenLoop.py --noc_h=8 --noc_w=8 &> $outname &

outname="logs/runexp_ol_vs_cl_9_9.out"
nohup python -u RunSim_Exp_ClosedLoop_vs_OpenLoop.py --noc_h=9 --noc_w=9 &> $outname &

outname="logs/runexp_ol_vs_cl_10_10.out"
nohup python -u RunSim_Exp_ClosedLoop_vs_OpenLoop.py --noc_h=10 --noc_w=10 &> $outname &

