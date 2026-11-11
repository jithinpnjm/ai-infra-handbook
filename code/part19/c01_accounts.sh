#!/bin/bash
# Account hierarchy and association
sacctmgr add account name=team-data-science
sacctmgr add user name=alice,bob account=team-data-science

# QoS hard limit (Chapter 6.9)
sacctmgr add qos name=normal priority=10 maxtresperuser=gres/gpu=64

# Fairshare weights (SCL)
sacctmgr modify account team-data-science set fairshare=100
