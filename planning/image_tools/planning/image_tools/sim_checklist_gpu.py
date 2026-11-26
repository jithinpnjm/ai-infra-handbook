#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

# Test script to design and verify the layout

title_lines = [
    "The 60-second checklist for a GPU node: ",
    "eight read-only additions"
]

col_headers = [
    ("Command", 540),
    ("What to check", 680),
    ("Reads which layer", 260)
]

# Rows data: (num, cmd_lines, desc_lines, is_orange)
rows = [
    (
        11,
        ["nvidia-smi"],
        [
            "all GPUs present, driver and CUDA versions, memory,",
            "processes, power draw versus cap, temperature,",
            "throttle reasons (nvidia-smi -q -d PERFORMANCE)"
        ],
        False
    ),
    (
        12,
        ["nvidia-smi dmon", "-s pucvmet -d 1"],
        [
            "per-GPU power, utilisation (sm, mem, enc/dec),",
            "clocks, memory, PCIe and NVLink throughput,",
            "ECC counters per second"
        ],
        False
    ),
    (
        13,
        ["nvidia-smi topo -m and", "nvidia-smi nvlink -s"],
        [
            "topology matrix (NV#, PIX, PXB, PHB, SYS, NODE),",
            "NVLink active links"
        ],
        False
    ),
    (
        14,
        ["dcgmi dmon -e ... or", "dcgmi diag -r 1"],
        [
            "SM activity and occupancy, tensor-pipe activity,",
            "DRAM activity, NVLink and PCIe throughput;",
            "quick health test"
        ],
        False
    ),
    (
        15,
        ["journalctl -k |", 'grep -iE "NVRM|Xid|nvidia"'],
        [
            "GPU errors: Xid 79 fallen off the bus,",
            "48 63 64 94 95 ECC and retired pages,",
            "74 NVLink errors"
        ],
        True  # ORANGE
    ),
    (
        16,
        ["ibstat, ibv_devinfo,", "rdma link, perfquery or", "ethtool -S"],
        [
            "link state and rate, error counters"
        ],
        False
    ),
    (
        17,
        ["cat /proc/pressure/", "{cpu,memory,io}"],
        [
            "PSI: tasks stalled on each resource"
        ],
        False
    ),
    (
        18,
        ["numastat, lstopo,", "cat /proc/cmdline,", "sysctl -a diff", "versus baseline"],
        [
            "placement and drift"
        ],
        False
    )
]

footer_lines = [
    "All of them are read-only; option names vary by driver and DCGM version, ",
    "so check the flags on your own system"
]

bottom_bar_text = "Add these to the host checklist when you are on a GPU node"

# Check label fidelity
print("Verifying exact strings against expected...")
# Expected raw strings:
expected_raw = {
    "title": "The 60-second checklist for a GPU node: eight read-only additions",
    "col1": "Command",
    "col2": "What to check",
    "col3": "Reads which layer",
    "r11_c": "nvidia-smi",
    "r11_d": "all GPUs present, driver and CUDA versions, memory, processes, power draw versus cap, temperature, throttle reasons (nvidia-smi -q -d PERFORMANCE)",
    "r12_c": "nvidia-smi dmon -s pucvmet -d 1",
    "r12_d": "per-GPU power, utilisation (sm, mem, enc/dec), clocks, memory, PCIe and NVLink throughput, ECC counters per second",
    "r13_c": "nvidia-smi topo -m and nvidia-smi nvlink -s",
    "r13_d": "topology matrix (NV#, PIX, PXB, PHB, SYS, NODE), NVLink active links",
    "r14_c": "dcgmi dmon -e ... or dcgmi diag -r 1",
    "r14_d": "SM activity and occupancy, tensor-pipe activity, DRAM activity, NVLink and PCIe throughput; quick health test",
    "r15_c": 'journalctl -k | grep -iE "NVRM|Xid|nvidia"',
    "r15_d": "GPU errors: Xid 79 fallen off the bus, 48 63 64 94 95 ECC and retired pages, 74 NVLink errors",
    "r16_c": "ibstat, ibv_devinfo, rdma link, perfquery or ethtool -S",
    "r16_d": "link state and rate, error counters",
    "r17_c": "cat /proc/pressure/{cpu,memory,io}",
    "r17_d": "PSI: tasks stalled on each resource",
    "r18_c": "numastat, lstopo, cat /proc/cmdline, sysctl -a diff versus baseline",
    "r18_d": "placement and drift",
    "footer": "All of them are read-only; option names vary by driver and DCGM version, so check the flags on your own system",
    "bottom_bar": "Add these to the host checklist when you are on a GPU node"
}

# Verify title
t_joined = "".join(title_lines)
assert t_joined == expected_raw["title"], f"Title mismatch: got '{t_joined}'"

# Verify footer
f_joined = "".join(footer_lines)
assert f_joined == expected_raw["footer"], f"Footer mismatch: got '{f_joined}'"

for num, c_lines, d_lines, _ in rows:
    # join c_lines
    # Notice for row 17: "cat /proc/pressure/" + "{cpu,memory,io}" without space
    if num == 17:
        c_joined = "".join(c_lines)
    else:
        c_joined = " ".join([l.strip() for l in c_lines])
    exp_c = expected_raw[f"r{num}_c"]
    assert c_joined == exp_c, f"Row {num} command mismatch: got '{c_joined}' vs exp '{exp_c}'"
    
    d_joined = " ".join([l.strip() for l in d_lines])
    exp_d = expected_raw[f"r{num}_d"]
    assert d_joined == exp_d, f"Row {num} desc mismatch: got '{d_joined}' vs exp '{exp_d}'"

print("All raw string concatenations match 100%!")
