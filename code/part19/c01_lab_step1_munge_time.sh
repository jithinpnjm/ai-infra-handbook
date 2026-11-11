#!/bin/bash
# Every node, controller included
sudo apt-get install -y munge chrony
sudo systemctl enable --now munge chrony
# Controller: distribute the key to every compute node and check time
for n in compute-001 compute-002 compute-003; do
    sudo scp /etc/munge/munge.key "$n":/etc/munge/
done
chronyc tracking   # expect: System time offset near zero on all nodes
