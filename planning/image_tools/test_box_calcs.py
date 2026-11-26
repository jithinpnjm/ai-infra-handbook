#!/usr/bin/env python3

boxes = [
    # Box 1: x=325 to 655 (w=330, center=490)
    ("b1", 330, 490, [
        ("PID 1 has no default", 20),
        ("action, so with no", 18),
        ("handler the signal", 18),
        ("is ignored", 10),
    ]),
    # Box 2: x=680 to 950 (w=270, center=815)
    ("b2", 270, 815, [
        ("grace period, 30", 16),
        ("seconds in", 10),
        ("Kubernetes", 10),
        ("by default", 10),
    ]),
    # Box 3: x=975 to 1240 (w=265, center=1107.5)
    ("b3", 265, 1107.5, [
        ("SIGKILL from the", 16),
        ("parent namespace", 16),
    ]),
    # Box 4: x=1265 to 1560 (w=295, center=1412.5)
    ("b4", 295, 1412.5, [
        ("training job loses", 18),
        ("its chance to", 13),
        ("checkpoint", 10),
    ]),
]

for name, bw, center, lines in boxes:
    for txt, length in lines:
        tw = length * 0.6 * 24
        pad = (bw - tw) / 2
        print(f"{name}: '{txt}' length={length} tw={tw:.1f} pad={pad:.1f}px (>=16: {pad>=16})")
