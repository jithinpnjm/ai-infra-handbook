# Test layout architectures for 9 states + 2 terminals
# Label lengths:
labels = {
    ("Start", "Provisioned"): "bare metal/VM created (image, BMC/PXE or cloud API)", # 51
    ("Provisioned", "Configured"): "OS, kernel, drivers, runtime, kubelet (Ansible/image)", # 53
    ("Configured", "Validating"): "join cluster tainted \"validating\"", # 33
    ("Validating", "Ready"): "health gates pass (GPU diag, NCCL, network, storage)", # 52
    ("Ready", "Cordoned"): "maintenance or suspected fault", # 30
    ("Cordoned", "Draining"): "evict pods respecting PDBs/checkpoints", # 38
    ("Draining", "Maintenance"): "upgrade, repair, reboot", # 23
    ("Maintenance", "Validating"): "re-validate", # 11
    ("Draining", "Quarantined"): "validation failed → hardware repair queue", # 41
    ("Quarantined", "Provisioned"): "repaired/reimaged", # 17
    ("Ready", "Decommissioned"): "remove (RMA, scale-in)", # 22
    ("Decommissioned", "End"): "", # 0
}

# Notice:
# 3 super-long labels:
# 1. bare metal/VM created (image, BMC/PXE or cloud API) [51 chars]
# 2. OS, kernel, drivers, runtime, kubelet (Ansible/image) [53 chars]
# 3. health gates pass (GPU diag, NCCL, network, storage) [52 chars]
# 4. validation failed → hardware repair queue [41 chars]
# 5. evict pods respecting PDBs/checkpoints [38 chars]
# 6. join cluster tainted "validating" [33 chars]

# A 2-line badge for 53 chars:
# Line 1: OS, kernel, drivers, runtime, (30 chars = 432 px)
# Line 2: kubelet (Ansible/image) (23 chars = 331 px)
# Width = 470 px, Height = 76 px.

# A 3-line badge for 53 chars:
# Line 1: OS, kernel, drivers, (20 chars = 288 px)
# Line 2: runtime, kubelet (16 chars = 230 px)
# Line 3: (Ansible/image) (15 chars = 216 px)
# Width = 320 px, Height = 104 px!
print("3-line badge width is 320px!")
