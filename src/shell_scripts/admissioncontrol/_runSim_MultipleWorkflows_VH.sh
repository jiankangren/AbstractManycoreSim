#!/bin/bash

export PYTHONPATH=$PYTHONPATH:/n/staff/hashan/documents/simpy-3.0.5/

rm -f *.out

# No-AC
for i in {8,16}
  do
	 outname="runsim_acnone_$i.out"
     nohup python -u RunSim.py -t Exp_ACTest_MultiWorkflow_VH \
	 --wf_num=$i \
	 --test_none=1 \
	 --test_determ=0 \
	 --test_vh_single=0 \
	 --test_vh_range=0 \
	 --test_kg=0 &> $outname &
  
  done
 
# deterministic-AC
for i in {8,16}
  do
	 outname="runsim_acdeterm_$i.out"
     nohup python -u RunSim.py -t Exp_ACTest_MultiWorkflow_VH \
	 --wf_num=$i \
	 --test_none=0 \
	 --test_determ=1 \
	 --test_vh_single=0 \
	 --test_vh_range=0 \
	 --test_kg=0 &> $outname &
  
  done
  
# vh-AC
for i in {8,16}
  do
	 for ibuff_ratio in {0.1,0.3,0.5,0.7,0.9,1.0}
	   do
		for tqbuff_ratio in {0.1,0.3,0.5,0.7,0.9,1.0}
		  do
			 outname="runsim_acheuvhsingle_${i}_${ibuff_ratio}_${tqbuff_ratio}.out"
			 nohup python -u RunSim.py -t Exp_ACTest_MultiWorkflow_VH \
			 --wf_num=$i \
			 --test_none=0 \
			 --test_determ=0 \
			 --test_vh_single=1 \
			 --heuvh_iblr=$ibuff_ratio \
			 --heuvh_tqlr=$tqbuff_ratio \
			 --test_vh_range=0 \
			 --test_kg=0 &> $outname &
		 done
	  done
  done
  
# kg-AC
for i in {8,16}
  do
	 outname="runsim_ackg_$i.out"
     nohup python -u RunSim.py -t Exp_ACTest_MultiWorkflow_VH \
	 --wf_num=$i \
	 --test_none=0 \
	 --test_determ=0 \
	 --test_vh_single=0 \
	 --test_vh_range=0 \
	 --test_kg=1 &> $outname &
  
  done

  
