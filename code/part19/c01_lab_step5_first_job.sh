#!/bin/bash
sacctmgr add account name=team-data-science
sacctmgr add user name=alice account=team-data-science
sacctmgr add qos name=normal priority=10 maxtresperuser=gres/gpu=64

sbatch --partition=gpu --gres=gpu:h100:1 --cpus-per-task=16 \
    --mem=64G --time=0:30:00 /path/to/test_gpu.sh
squeue   # expected: job RUNNING on a compute node
sacct -j "$JOBID"   # JOBID from the sbatch output; expected: job COMPLETED with GPU time recorded
