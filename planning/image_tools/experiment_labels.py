#!/usr/bin/env python3
import sys

labels = {
    "title": "Same cluster, four different numbers",
    "subtitle": "Worked example from code/part06/flops.py with the printed values.",
    "formula": "Rpeak GFLOP/s = nodes times sockets times cores times GHz times FP64 FLOPs per cycle per core",
    "pipeline": "vector N=1000: 1004 cycles pipelined versus 5000 unpipelined, 4.98 times",
    "bar1": "CPU cluster Rpeak: 100 nodes times 2 sockets times 64 cores times 2.4 GHz times 32 FLOPs per cycle (dual AVX-512 FMA) = 983.0 TFLOP/s; with 16 FLOPs per cycle 491.5 TFLOP/s",
    "bar2": "illustrative 800-GPU cluster FP64 Rpeak: 48.0 PFLOP/s",
    "bar3": "HPL efficiency if Rmax is 38 PF: 38 divided by 48 = 79 percent",
    "bar4": "AI peak BF16 dense, illustrative: 800 PFLOP/s; at 40 percent MFU: 320 PFLOP/s",
    "footer": "the same 800 GPUs are 48 PF in FP64 and 800 PF in BF16; the number you can use is smaller again after real efficiency; MFU is HPL efficiency for AI: how much of the accelerator peak the training step turns into useful math; count useful FLOPs per step, divide by step time, compare to peak at the training precision"
}

for k, v in labels.items():
    print(f"{k}: len={len(v)} chars")
