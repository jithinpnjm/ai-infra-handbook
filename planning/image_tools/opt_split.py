#!/usr/bin/env python3

text11 = "all GPUs present, driver and CUDA versions, memory, processes, power draw versus cap, temperature, throttle reasons (nvidia-smi -q -d PERFORMANCE)"
words = text11.split()

best = None
min_max_len = 999

for i in range(1, len(words)-1):
    for j in range(i+1, len(words)):
        l1 = " ".join(words[:i])
        l2 = " ".join(words[i:j])
        l3 = " ".join(words[j:])
        max_l = max(len(l1), len(l2), len(l3))
        if max_l < min_max_len:
            min_max_len = max_l
            best = (l1, l2, l3)

print(f"Optimal 3-line split (max chars = {min_max_len}):")
print(f"1: '{best[0]}' (len={len(best[0])}, w={len(best[0])*14.4:.1f})")
print(f"2: '{best[1]}' (len={len(best[1])}, w={len(best[1])*14.4:.1f})")
print(f"3: '{best[2]}' (len={len(best[2])}, w={len(best[2])*14.4:.1f})")
