#!/bin/bash
# Each compute node
sudo apt-get install -y munge slurm-wlm
# copy munge key, slurm.conf, cgroup.conf and gres.conf from the controller
sudo systemctl enable --now slurmd
# Controller: confirm
sinfo -l   # expected: compute nodes idle, GPU GRES visible
