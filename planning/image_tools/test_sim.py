#!/usr/bin/env python3
import re

labels = {
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

print(f"Total entries: {len(labels)}")
for k, v in labels.items():
    print(f"{k}: len={len(v)} | {v}")
