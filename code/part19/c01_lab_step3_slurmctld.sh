#!/bin/bash
# Controller
sudo systemctl enable --now slurmctld
sinfo    # expected: controller visible, partition gpu listed
