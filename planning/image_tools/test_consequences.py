w1, w2, w3 = 540, 420, 520
# col 1: 540
t1 = [
    "Pinned pages are unevictable",
    "(counted in Mlocked and",
    "Unevictable and in cgroup accounting)"
]
# let's test t1 lines
for line in t1:
    lw = len(line) * 14.4
    print(f"t1 '{line}': len={len(line)}, w={lw:.1f}, pad={(w1-lw)/2:.1f}")

# col 2: 420
t2 = [
    "Pinning is slow: allocate",
    "once up front, not per batch"
]
for line in t2:
    lw = len(line) * 14.4
    print(f"t2 '{line}': len={len(line)}, w={lw:.1f}, pad={(w2-lw)/2:.1f}")

# col 3: 520
t3 = [
    "Huge pages for pinned buffers",
    "reduce mappings and",
    "registration cost"
]
for line in t3:
    lw = len(line) * 14.4
    print(f"t3 '{line}': len={len(line)}, w={lw:.1f}, pad={(w3-lw)/2:.1f}")

