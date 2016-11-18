#!/bin/bash

export PYTHONPATH=$PYTHONPATH:/n/staff/hashan/documents/simpy-3.0.5/



for i in {8..19..2}
  do
	 outname="runsim$i.out"
     nohup python -u RunSim.py -t Exp_ACTest_MultiWorkflow -w $i &> $outname &
  
  done
  
  