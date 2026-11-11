#!/bin/bash
# Adjust the gpu partition at runtime (slurm.conf in Section 3 defines the same policy)
scontrol update partitionname=gpu MaxTime=72:00:00 State=UP
scontrol update partitionname=gpu Default=YES
