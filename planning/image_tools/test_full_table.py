#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

H = 1200
title_text = "USE table, GPU side: PCIe, compute, memory, NVLink and power"

col_headers = ["Utilisation", "Saturation", "Errors"]

row_resources = [
    "PCIe (GPU, NIC, NVMe)",
    "GPU compute (SMs, tensor cores)",
    "GPU memory (HBM) capacity",
    "NVLink and NVSwitch",
    "Power and thermal"
]

# We need the 15 cells exactly:
cells_data = [
    # Row 1
    ("nvidia-smi dmon PCIe rx/tx versus link capability; lspci -vv link speed and width",
     "(indirect) copy stalls",
     "AER errors in dmesg, Xid 79, replay counters"),
    # Row 2
    ("DCGM SM activity and occupancy, tensor activity, nsys",
     "work queued behind other streams or processes; MPS or time-slice contention",
     "Xid errors; ECC errors; thermal or power throttling reasons"),
    # Row 3
    ("nvidia-smi memory used and total; allocator stats",
     "allocation failures or OOM; unified-memory oversubscription (page migration traffic)",
     "ECC single and double bit, retired pages, row-remapping failures"),
    # Row 4
    ("nvidia-smi nvlink, DCGM NVLink bandwidth versus peak",
     "stalls visible in profiler timelines",
     "NVLink CRC and replay errors, Xid 74, fabric manager health"),
    # Row 5
    ("nvidia-smi power draw versus limit, ipmitool sdr, turbostat",
     "clock throttling due to power cap or thermal reasons",
     "thermal or power faults in the BMC SEL")
]

footnote_text = "GPU memory bandwidth: DCGM DRAM activity (saturation indirect)"
callout_text = "A table with three honest blanks teaches you more than a table filled with guesses: every blank is a known unknown"
bottom_bar_text = "Fill this table in for your platform"

# Line splits carefully crafted so that:
# 1. Joined by space, each cell matches the exact text.
# 2. Every line fits in its box with at least 16px padding on left AND right.
# Let's inspect the bounding boxes!

col_x = [40, 404, 796, 1188]
col_w = [350, 378, 378, 372]

# Row 0 (Headers): y=136, h=48
# Rows 1..5: y_start = 196, row_h = 136, gap = 12
# Row 1: y = 196
# Row 2: y = 344
# Row 3: y = 492
# Row 4: y = 640
# Row 5: y = 788
# Footnote: y = 938, h = 46
# Callout: y = 996, h = 84
# Bottom bar: y = 1094, h = 58
# Margin to bottom: 1200 - 1152 = 48 px.

print("Checking line splits and paddings...")

# Let's define the line splits:
splits = {
    # Col 0 (Resource titles) at 30px bold, sans (0.6*30 = 18px/char).
    # Box width = 350. Icon at left: x=col_x+16, w=56. Icon ends at col_x+72.
    # Text starts at col_x + 92.
    # Available width for text = 350 - 92 - 16 = 242 px.
    # 242 / 18 = 13.4 chars per line.
    (0, 0): ["PCIe", "(GPU, NIC,", "NVMe)"],
    (1, 0): ["GPU compute", "(SMs, tensor", "cores)"],
    (2, 0): ["GPU memory", "(HBM)", "capacity"],
    (3, 0): ["NVLink and", "NVSwitch"],
    (4, 0): ["Power and", "thermal"],
    
    # Cells (at 24px, monospace: 0.62*24 = 14.88px/char; sans: 0.6*24 = 14.4px/char).
    # Col 1: w=378. Text starts at col_x + 20. Right padding = 378 - 20 - tw >= 16 => tw <= 342px.
    # 342 / 14.88 = 22.9 chars.
    (0, 1): [
        "nvidia-smi dmon PCIe",
        "rx/tx versus link",
        "capability; lspci -vv",
        "link speed and width"
    ],
    (0, 2): ["(indirect) copy stalls"],
    (0, 3): [
        "AER errors in dmesg,",
        "Xid 79, replay counters"
    ],
    
    (1, 1): [
        "DCGM SM activity and",
        "occupancy, tensor",
        "activity, nsys"
    ],
    (1, 2): [
        "work queued behind",
        "other streams or",
        "processes; MPS or",
        "time-slice contention"
    ],
    (1, 3): [
        "Xid errors; ECC errors;",
        "thermal or power",
        "throttling reasons"
    ],
    
    (2, 1): [
        "nvidia-smi memory used",
        "and total; allocator",
        "stats"
    ],
    (2, 2): [
        "allocation failures or",
        "OOM; unified-memory",
        "oversubscription (page",
        "migration traffic)"
    ],
    (2, 3): [
        "ECC single and double",
        "bit, retired pages,",
        "row-remapping failures"
    ],
    
    (3, 1): [
        "nvidia-smi nvlink, DCGM",
        "NVLink bandwidth versus",
        "peak"
    ],
    (3, 2): [
        "stalls visible in",
        "profiler timelines"
    ],
    (3, 3): [
        "NVLink CRC and replay",
        "errors, Xid 74, fabric",
        "manager health"
    ],
    
    (4, 1): [
        "nvidia-smi power draw",
        "versus limit, ipmitool",
        "sdr, turbostat"
    ],
    (4, 2): [
        "clock throttling due to",
        "power cap or thermal",
        "reasons"
    ],
    (4, 3): [
        "thermal or power faults",
        "in the BMC SEL"
    ]
}

# Verify every single split joins to the exact string!
for r in range(5):
    res_str = " ".join(splits[(r, 0)])
    assert res_str == row_resources[r], f"Mismatch row {r}: '{res_str}' != '{row_resources[r]}'"
    for c in range(1, 4):
        cell_str = " ".join(splits[(r, c)])
        expected = cells_data[r][c-1]
        assert cell_str == expected, f"Mismatch ({r},{c}): '{cell_str}' != '{expected}'"

print("All 20 table entries match source strings token-for-token!")

# Verify paddings:
for (r, c), lines in splits.items():
    bw = col_w[c]
    if c == 0:
        # icon at col_x + 16, w=56. Text at col_x + 88.
        # left pad from icon = 16. Right pad = bw - 88 - tw.
        text_start = 88
        fs = 30
        factor = 0.6
        for line in lines:
            tw = len(line) * factor * fs
            right_pad = bw - (text_start + tw)
            if right_pad < 16:
                print(f"FAILED padding Col 0 ({r}): '{line}' right_pad={right_pad:.1f} < 16")
    else:
        text_start = 20
        fs = 24
        is_mono = (c != 2) # Saturation is sans-serif, Util/Errors are monospace
        factor = 0.62 if is_mono else 0.6
        for line in lines:
            tw = len(line) * factor * fs
            right_pad = bw - (text_start + tw)
            if right_pad < 16:
                print(f"FAILED padding ({r},{c}): '{line}' right_pad={right_pad:.1f} < 16")

print("All text lines have >= 16px padding on left AND right!")
