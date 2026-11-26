import re

def est_width(txt, fs=24, is_mono=False):
    coeff = 0.62 if is_mono else 0.6
    return len(txt) * fs * coeff

c2_lines = [
    ("Default (not the default", 30, 920, 1550),
    ("despite the name):", 30, 920, 1550),
    ("inherit the node resolver config from the", 24, 845, 1550),
    ("node resolv.conf or kubelet resolvConf", 24, 845, 1550)
]

for txt, fs, x, box_right in c2_lines:
    w = est_width(txt, fs)
    right_edge = x + w
    pad = box_right - right_edge
    print(f"C2: w={w:5.1f}, right={right_edge:5.1f}, pad={pad:4.1f} | '{txt}'")
    assert pad >= 16, f"Padding violation: {txt}"

print("\nC2 PASS!")
