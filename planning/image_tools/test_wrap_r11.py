#!/usr/bin/env python3

text11 = "all GPUs present, driver and CUDA versions, memory, processes, power draw versus cap, temperature, throttle reasons (nvidia-smi -q -d PERFORMANCE)"

# Let's try 3 lines:
# Line 1:
l1 = "all GPUs present, driver and CUDA versions,"
# Line 2:
l2 = "memory, processes, power draw versus cap,"
# Line 3:
l3 = "temperature, throttle reasons (nvidia-smi -q -d PERFORMANCE)"

print(f"l1: len={len(l1)}, width={len(l1)*14.4:.1f}")
print(f"l2: len={len(l2)}, width={len(l2)*14.4:.1f}")
print(f"l3: len={len(l3)}, width={len(l3)*14.4:.1f}")

# Check l3: 60 chars * 14.4 = 864 px! That's too long!
# What if:
# Line 1:
l1 = "all GPUs present, driver and CUDA versions, memory, processes," # 62 chars
# 62 * 14.4 = 892.8 px!
