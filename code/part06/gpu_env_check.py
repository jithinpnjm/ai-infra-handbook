#!/usr/bin/env python3
"""Print what a Slurm job can see of its GPUs: Slurm variables, CUDA_VISIBLE_DEVICES, nvidia-smi -L.
Run it under srun to compare --gres/--gpus-per-task/--gpu-bind variants."""
import os
import shutil
import subprocess

KEYS = ["SLURM_JOB_ID", "SLURM_PROCID", "SLURM_LOCALID", "SLURM_NODEID", "SLURM_JOB_GPUS", "SLURM_STEP_GPUS",
        "SLURM_GPUS", "SLURM_GPUS_ON_NODE", "SLURM_GPUS_PER_NODE", "SLURM_GPUS_PER_TASK", "SLURM_GPU_BIND",
        "CUDA_VISIBLE_DEVICES", "CUDA_DEVICE_ORDER", "NVIDIA_VISIBLE_DEVICES", "GPU_DEVICE_ORDINAL"]

host = os.uname().nodename
for k in KEYS:
    print(f"{host} rank={os.environ.get('SLURM_PROCID', '-')} {k}={os.environ.get(k, '<unset>')}")
if shutil.which("nvidia-smi"):
    out = subprocess.run(["nvidia-smi", "-L"], capture_output=True, text=True)
    for line in out.stdout.splitlines():
        print(f"{host} rank={os.environ.get('SLURM_PROCID', '-')} nvidia-smi: {line}")
else:
    print(f"{host}: nvidia-smi not found (no NVIDIA driver on this machine)")
