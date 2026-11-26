# Let's test exact line splits and calculate bounding boxes.

col_w = [340, 380, 390, 370] # Total = 1480. 3 gaps of 15px = 45px. 1480 + 45 = 1525. Margin left=38, right=37 -> 1600.
# Or:
# Left margin: 40px
# Table width: 1520px
# 3 gaps of 14px = 42px
# Total columns width = 1520 - 42 = 1478px.
# Col 0 (Resource): 330px
# Col 1 (Utilisation): 380px
# Col 2 (Saturation): 390px
# Col 3 (Errors): 378px
# Sum = 330 + 380 + 390 + 378 = 1478px. Exactly 1478 + 42 = 1520!

# Let's define the line splits for each text:
cell_splits = {
    # Row 1
    (0, 0): ["PCIe (GPU,", "NIC, NVMe)"], # font 30 bold, sans (0.6*30=18)
    (0, 1): [
        "nvidia-smi dmon PCIe rx/tx",
        "versus link capability;",
        "lspci -vv link speed",
        "and width"
    ],
    (0, 2): ["(indirect) copy stalls"],
    (0, 3): [
        "AER errors in dmesg,",
        "Xid 79, replay counters"
    ],
    
    # Row 2
    (1, 0): ["GPU compute", "(SMs, tensor cores)"],
    (1, 1): [
        "DCGM SM activity and",
        "occupancy, tensor",
        "activity, nsys"
    ],
    (1, 2): [
        "work queued behind other",
        "streams or processes; MPS",
        "or time-slice contention"
    ],
    (1, 3): [
        "Xid errors; ECC errors;",
        "thermal or power",
        "throttling reasons"
    ],
    
    # Row 3
    (2, 0): ["GPU memory", "(HBM) capacity"],
    (2, 1): [
        "nvidia-smi memory used",
        "and total; allocator stats"
    ],
    (2, 2): [
        "allocation failures or OOM;",
        "unified-memory oversubscription",
        "(page migration traffic)"
    ],
    (2, 3): [
        "ECC single and double bit,",
        "retired pages,",
        "row-remapping failures"
    ],
    
    # Row 4
    (3, 0): ["NVLink and", "NVSwitch"],
    (3, 1): [
        "nvidia-smi nvlink, DCGM",
        "NVLink bandwidth versus",
        "peak"
    ],
    (3, 2): ["stalls visible in", "profiler timelines"],
    (3, 3): [
        "NVLink CRC and replay",
        "errors, Xid 74, fabric",
        "manager health"
    ],
    
    # Row 5
    (4, 0): ["Power and", "thermal"],
    (4, 1): [
        "nvidia-smi power draw",
        "versus limit, ipmitool sdr,",
        "turbostat"
    ],
    (4, 2): [
        "clock throttling due to",
        "power cap or thermal reasons"
    ],
    (4, 3): [
        "thermal or power faults",
        "in the BMC SEL"
    ]
}

widths = [330, 380, 390, 378]

# Check each cell against padding requirement >= 16px on each side
# Max text width = col_w - 32px
for (r, c), lines in cell_splits.items():
    w_avail = widths[c]
    # For col 0, if icon is beside: icon is 56px + 16px pad + 16px gap = 88px.
    # What if icon is 50px or 48px?
    # Let's check!
    fs = 30 if c == 0 else 24
    is_mono = (c > 0) # be conservative, test with 0.62 if mono
    char_factor = 0.62 if is_mono else 0.6
    char_w = char_factor * fs
    print(f"Cell ({r}, {c}): col_w={w_avail}")
    for line in lines:
        tw = len(line) * char_w
        pad = (w_avail - tw) / 2 # if centered, or w_avail - 16 - tw if left-aligned
        left_pad = 20 # suppose left margin is 20px
        right_pad = w_avail - (left_pad + tw)
        print(f"  Line: '{line}' (len={len(line)}): tw={tw:.1f}px, w_avail={w_avail}px, margin_rem={w_avail - tw:.1f}px")
        if w_avail - tw < 32:
            print(f"    !!! WARNING: Margin too small! Remaining = {w_avail - tw:.1f} < 32")

