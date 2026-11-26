def est_w(s, fs=24, is_mono=False):
    return len(s) * (0.62 if is_mono else 0.60) * fs

lines = [
    ("node utilisation (requests against allocatable)", False), # 47 chars
    ("below --scale-down-utilization-threshold 0.5", True), # 43 chars
    ("for --scale-down-unneeded-time 10 min,", True), # 38 chars
    ("then drain and remove", False) # 21 chars
]

# Wait, let's see what happens if we wrap into 5 lines:
lines_5 = [
    ("node utilisation (requests against", False), # 34 chars = 489.6 px
    ("allocatable) below", False), # 18 chars = 259.2 px
    ("--scale-down-utilization-threshold 0.5", True), # 38 chars * 14.88 = 565.4 px
    ("for --scale-down-unneeded-time 10 min,", True), # 38 chars * 14.88 = 565.4 px
    ("then drain and remove", False) # 21 chars * 14.4 = 302.4 px
]

print("Testing lines_5:")
for l, is_m in lines_5:
    w = est_w(l, 24, is_m)
    print(f"  [{w:5.1f} / 650 | {'OK' if w <= 650 else 'FAIL'}] {l}")
    assert w <= 650
print("lines_5 PASS!")
