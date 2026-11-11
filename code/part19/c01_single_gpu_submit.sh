#!/bin/bash
# One H100
sbatch --partition=gpu --gres=gpu:h100:1 --cpus-per-task=16 \
    --mem=64G --time=4:00:00 single_gpu_job.sh
