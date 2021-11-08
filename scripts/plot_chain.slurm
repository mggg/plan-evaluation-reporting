#!/bin/bash
#SBATCH --job-name="Plot" # Job name
#SBATCH --time=2-00:00:00 # days-hh:mm:ss
#SBATCH --nodes=1 # how many computers do we need?
#SBATCH --ntasks-per-node=1 # how many cores per node do we need?
#SBATCH --mem=64000 # how many MB of memory do we need (16GB here)
#SBATCH --partition=largemem #largemem #preempt # which queue to use

python ../run_gallery.py Pennsylvania state_house --ensemble_dir /cluster/home/gschoe01/plan-evaluation-reporting/Pennsylvania/ensemble_stats/ --output_dir /cluster/home/gschoe01/plan-evaluation-reporting/plots/PA_1108
