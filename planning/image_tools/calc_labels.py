# Calculate text widths and paddings
def text_width(s, fs=24, is_mono=False):
    factor = 0.62 if is_mono else 0.60
    return len(s) * fs * factor

labels = [
    # Node titles (fs >= 30, e.g. 30px bold)
    ("Provisioned", 30),
    ("Configured", 30),
    ("Validating", 30),
    ("Ready", 30),
    ("Cordoned", 30),
    ("Draining", 30),
    ("Maintenance", 30),
    ("Quarantined", 30),
    ("Decommissioned", 30),

    # Transition labels (fs >= 24)
    ("bare metal/VM created (image, BMC/PXE or cloud API)", 24),
    ("OS, kernel, drivers, runtime, kubelet (Ansible/image)", 24),
    ('join cluster tainted "validating"', 24),
    ("health gates pass (GPU diag, NCCL, network, storage)", 24),
    ("maintenance or suspected fault", 24),
    ("evict pods respecting PDBs/checkpoints", 24),
    ("upgrade, repair, reboot", 24),
    ("re-validate", 24),
    ("validation failed → hardware repair queue", 24),
    ("repaired/reimaged", 24),
    ("remove (RMA, scale-in)", 24),
]

for label, fs in labels:
    w = text_width(label, fs)
    print(f"[{fs}px] len={len(label):2d} w={w:5.1f}px | '{label}'")
