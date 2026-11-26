from optimize_splits import wrap_text

labels = [
    # Row 1
    "PCIe (GPU, NIC, NVMe)",
    "nvidia-smi dmon PCIe rx/tx versus link capability; lspci -vv link speed and width",
    "(indirect) copy stalls",
    "AER errors in dmesg, Xid 79, replay counters",
    # Row 2
    "GPU compute (SMs, tensor cores)",
    "DCGM SM activity and occupancy, tensor activity, nsys",
    "work queued behind other streams or processes; MPS or time-slice contention",
    "Xid errors; ECC errors; thermal or power throttling reasons",
    # Row 3
    "GPU memory (HBM) capacity",
    "nvidia-smi memory used and total; allocator stats",
    "allocation failures or OOM; unified-memory oversubscription (page migration traffic)",
    "ECC single and double bit, retired pages, row-remapping failures",
    # Row 4
    "NVLink and NVSwitch",
    "nvidia-smi nvlink, DCGM NVLink bandwidth versus peak",
    "stalls visible in profiler timelines",
    "NVLink CRC and replay errors, Xid 74, fabric manager health",
    # Row 5
    "Power and thermal",
    "nvidia-smi power draw versus limit, ipmitool sdr, turbostat",
    "clock throttling due to power cap or thermal reasons",
    "thermal or power faults in the BMC SEL",
    # Footnote, Callout, Bottom bar
    "GPU memory bandwidth: DCGM DRAM activity (saturation indirect)",
    "A table with three honest blanks teaches you more than a table filled with guesses: every blank is a known unknown",
    "Fill this table in for your platform"
]

print("--- Testing Col 0 wrapping (max_chars = 15) ---")
for r in [0, 4, 8, 12, 16]:
    text = labels[r]
    wrapped = wrap_text(text, 15)
    print(f"Original: {text}")
    print(f"Wrapped ({len(wrapped)} lines): {wrapped}")
    assert " ".join(wrapped) == text

print("\n--- Testing Cells wrapping (max_chars = 23) ---")
for idx in range(len(labels)):
    if idx in [0, 4, 8, 12, 16, 20, 21, 22]:
        continue
    text = labels[idx]
    wrapped = wrap_text(text, 23)
    print(f"[{idx}] Wrapped ({len(wrapped)} lines): {wrapped}")
    for l in wrapped:
        if len(l) > 23:
            print(f"  WARNING: line > 23: '{l}' (len={len(l)})")
    assert " ".join(wrapped) == text
