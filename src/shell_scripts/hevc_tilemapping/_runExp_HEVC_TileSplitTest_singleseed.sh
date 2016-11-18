#!/bin/bash

export PYTHONPATH=$PYTHONPATH:/shared/cssamba0/staffstore/hrm506/simpy-3.0.5/
export PYTHONPATH=$PYTHONPATH:/shared/cssamba0/staffstore/hrm506/networkx-1.10/networkx-1.10


#rm -f ../*.out
#rm -f *.out
#rm -f ../logs/*.out

cd ..

seed = 18065
outname="logs/runexp_hevc_splittest_simple_seed_${seed}.out"
nohup python -u RunSim_Exp_HEVCTileSplitTest.py --forced_seed=$seed &> $outname &

