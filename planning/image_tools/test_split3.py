#!/usr/bin/env python3

text11 = "all GPUs present, driver and CUDA versions, memory, processes, power draw versus cap, temperature, throttle reasons (nvidia-smi -q -d PERFORMANCE)"
# Total length: 146 chars

# If split into 3 lines:
# line 1:
l1 = "all GPUs present, driver and CUDA versions, memory," # 51 chars
# line 2:
l2 = "processes, power draw versus cap, temperature," # 46 chars
# line 3:
l3 = "throttle reasons (nvidia-smi -q -d PERFORMANCE)" # 48 chars

print(f"l1: {len(l1)} chars, width = {len(l1)*14.4:.1f} px")
print(f"l2: {len(l2)} chars, width = {len(l2)*14.4:.1f} px")
print(f"l3: {len(l3)} chars, width = {len(l3)*14.4:.1f} px")
