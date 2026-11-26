# Test line breaks for all 12 transitions
def text_width(s, fs=24, is_mono=False):
    factor = 0.62 if is_mono else 0.60
    return len(s) * fs * factor

transitions = [
    # 1. Start -> Provisioned
    ("T1", "bare metal/VM created (image, BMC/PXE or cloud API)", [
        "bare metal/VM created",
        "(image, BMC/PXE",
        "or cloud API)"
    ]),
    
    # 2. Provisioned -> Configured
    ("T2", "OS, kernel, drivers, runtime, kubelet (Ansible/image)", [
        "OS, kernel, drivers,",
        "runtime, kubelet",
        "(Ansible/image)"
    ]),
    
    # 3. Configured -> Validating
    ("T3", 'join cluster tainted "validating"', [
        'join cluster tainted',
        '"validating"'
    ]),
    
    # 4. Validating -> Ready
    ("T4", "health gates pass (GPU diag, NCCL, network, storage)", [
        "health gates pass",
        "(GPU diag, NCCL,",
        "network, storage)"
    ]),
    
    # 5. Ready -> Cordoned
    ("T5", "maintenance or suspected fault", [
        "maintenance or",
        "suspected fault"
    ]),
    
    # 6. Cordoned -> Draining
    ("T6", "evict pods respecting PDBs/checkpoints", [
        "evict pods respecting",
        "PDBs/checkpoints"
    ]),
    
    # 7. Draining -> Maintenance
    ("T7", "upgrade, repair, reboot", [
        "upgrade, repair,",
        "reboot"
    ]),
    
    # 8. Maintenance -> Validating
    ("T8", "re-validate", [
        "re-validate"
    ]),
    
    # 9. Draining -> Quarantined
    ("T9", "validation failed → hardware repair queue", [
        "validation failed →",
        "hardware repair queue"
    ]),
    
    # 10. Quarantined -> Provisioned
    ("T10", "repaired/reimaged", [
        "repaired/reimaged"
    ]),
    
    # 11. Ready -> Decommissioned
    ("T11", "remove (RMA, scale-in)", [
        "remove",
        "(RMA, scale-in)"
    ]),
]

for code, full_label, lines in transitions:
    # Check that joining lines with space reproduces the full label exactly!
    reconstructed = " ".join(lines)
    assert reconstructed == full_label, f"Mismatch in {code}: '{reconstructed}' != '{full_label}'"
    max_w = max(text_width(line, 24) for line in lines)
    print(f"{code}: {len(lines)} lines, max_w={max_w:5.1f}px | '{lines[0]}'")

print("\nAll reconstructions match original labels 100%!")
