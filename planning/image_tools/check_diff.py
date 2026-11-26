#!/usr/bin/env python3
import re

target_r1c2 = "nvidia-smi --query-gpu=index,name,temperature.gpu,utilization.gpu,memory.used,memory.total,power.draw,ecc.errors.uncorrected.volatile.total --format=csv,noheader,nounits: one CSV line per GPU; nvidia-smi -q -x for XML"

row1_col2_lines = [
    "nvidia-smi --query-gpu=index,name,",
    "temperature.gpu,utilization.gpu,",
    "memory.used,memory.total,power.draw,",
    "ecc.errors.uncorrected.volatile.total",
    "--format=csv,noheader,nounits: one CSV line",
    "per GPU; nvidia-smi -q -x for XML"
]

reconstructed = " ".join([l.strip() for l in row1_col2_lines])
print("Target:       ", repr(target_r1c2))
print("Reconstructed:", repr(reconstructed))
print("Match?", reconstructed == target_r1c2)
if reconstructed != target_r1c2:
    for i, (c1, c2) in enumerate(zip(target_r1c2, reconstructed)):
        if c1 != c2:
            print(f"Diff at {i}: target={repr(c1)} vs recon={repr(c2)}")
            print(f"Target slice: {repr(target_r1c2[i-10:i+10])}")
            print(f"Recon  slice: {repr(reconstructed[i-10:i+10])}")
            break
