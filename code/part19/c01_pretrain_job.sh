#!/bin/bash
#SBATCH --job-name=pretrain
#SBATCH --partition=gpu
#SBATCH --nodes=2
#SBATCH --gpus-per-node=8
#SBATCH --ntasks-per-node=8
#SBATCH --cpus-per-task=12
#SBATCH --mem=700G
#SBATCH --time=24:00:00
#SBATCH --output=pretrain-%j.out

srun --mpi=pmix python train.py
