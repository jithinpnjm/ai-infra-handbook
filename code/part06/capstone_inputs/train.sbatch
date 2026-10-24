#!/bin/bash
#SBATCH --job-name=train
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=8
#SBATCH --gpus-per-node=8
#SBATCH --cpus-per-gpu=12
#SBATCH --mem=0
#SBATCH --time=12:00:00
#SBATCH --exclusive
#SBATCH --requeue
#SBATCH --signal=B:USR1@300
#SBATCH --output=logs/%x-%j.out
set -euo pipefail
module purge
module load cuda/12.4 
srun --mpi=pmix python train.py
