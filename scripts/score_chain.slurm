#!/bin/bash
#SBATCH --job-name="ScoreEnsemble-PlanAnalysis" # Job name
#SBATCH --time=2-00:00:00 # days-hh:mm:ss
#SBATCH --nodes=1 # how many computers do we need?
#SBATCH --ntasks-per-node=1 # how many cores per node do we need?
#SBATCH --mem=5000 # how many MB of memory do we need (5GB here)
#SBATCH --output="/cluster/home/jmatth03/plan-evaluation/%x.%A_%a.txt" # where to save the output file.
#SBATCH --partition=largemem #largemem #preempt # which queue to use

source ~/.bashrc  # need to set up the normal environment.
echo running on: `hostname` # print some info about where we are running

# cd into the correct directory
cd $HOME
cd plan-evaluation

if [ $3 == 1 ]
then
    echo "county"
    python collect_scores.py ${1} ${2} 100000 --county_aware #$SLURM_ARRAY_TASK_ID # run the python code with the arguments. 
else
    echo "neutral"
    python collect_scores.py ${1} ${2} 100000 #$SLURM_ARRAY_TASK_ID # run the python code with the arguments. 
fi