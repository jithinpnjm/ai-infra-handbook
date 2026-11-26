#!/usr/bin/env python3

# Check wrapping for What to check in Col 2 (w=658, text_start=x+20, text_end <= x+638 => max_w = 618px)
# At 24px sans-serif (14.4 px/char): max chars = 618 / 14.4 = 42.9 chars

desc_splits = {
    11: [
        "all GPUs present, driver and CUDA versions,",
        "memory, processes, power draw versus cap,",
        "temperature, throttle reasons",
        "(nvidia-smi -q -d PERFORMANCE)"
    ],
    12: [
        "per-GPU power, utilisation (sm, mem,",
        "enc/dec), clocks, memory, PCIe and NVLink",
        "throughput, ECC counters per second"
    ],
    13: [
        "topology matrix (NV#, PIX, PXB, PHB, SYS,",
        "NODE), NVLink active links"
    ],
    14: [
        "SM activity and occupancy, tensor-pipe",
        "activity, DRAM activity, NVLink and PCIe",
        "throughput; quick health test"
    ],
    15: [
        "GPU errors: Xid 79 fallen off the bus,",
        "48 63 64 94 95 ECC and retired pages,",
        "74 NVLink errors"
    ],
    16: [
        "link state and rate, error counters"
    ],
    17: [
        "PSI: tasks stalled on each resource"
    ],
    18: [
        "placement and drift"
    ]
}

# Verify that joined strings match the exact source strings
raw_desc = {
    11: "all GPUs present, driver and CUDA versions, memory, processes, power draw versus cap, temperature, throttle reasons (nvidia-smi -q -d PERFORMANCE)",
    12: "per-GPU power, utilisation (sm, mem, enc/dec), clocks, memory, PCIe and NVLink throughput, ECC counters per second",
    13: "topology matrix (NV#, PIX, PXB, PHB, SYS, NODE), NVLink active links",
    14: "SM activity and occupancy, tensor-pipe activity, DRAM activity, NVLink and PCIe throughput; quick health test",
    15: "GPU errors: Xid 79 fallen off the bus, 48 63 64 94 95 ECC and retired pages, 74 NVLink errors",
    16: "link state and rate, error counters",
    17: "PSI: tasks stalled on each resource",
    18: "placement and drift"
}

print("Checking What to check splits:")
all_ok = True
for r in range(11, 19):
    lines = desc_splits[r]
    joined = " ".join([l.strip() for l in lines])
    exp = raw_desc[r]
    if joined != exp:
        print(f"Row {r} MISMATCH:")
        print(f"  Got: '{joined}'")
        print(f"  Exp: '{exp}'")
        all_ok = False
    else:
        max_len = max(len(l) for l in lines)
        max_w = max_len * 14.4
        pad_r = 658 - (20 + max_w)
        print(f"Row {r}: {len(lines)} lines, max_len={max_len} chars ({max_w:.1f}px), pad_R={pad_r:.1f}px")
        if pad_r < 16:
            print(f"  ERROR: pad_R < 16 on row {r}!")
            all_ok = False

if all_ok:
    print("ALL WHAT TO CHECK LINES FIT WITH PADDING >= 16px!")
