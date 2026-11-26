#!/usr/bin/env python3

box_widths = [240, 240, 250, 260]
gaps = [175, 175, 180]
assert sum(box_widths) + sum(gaps) == 1520

print("Total matches 1520 exactly!")

# Box 4:
b4_lines = [
    ("Inode C: type, ", 24, False),
    ("permissions, ", 24, False),
    ("owner, size, ", 24, False),
    ("times, link ", 24, False),
    ("count, pointers ", 24, False),
    ("to data blocks", 24, False)
]

for t, fs, is_mono in b4_lines:
    w = len(t) * fs * (0.62 if is_mono else 0.6)
    pad = (260 - w) / 2
    print(f"pad={pad:.1f}px (w={w:.1f}px) | '{t}'")
    assert pad >= 16.0

print("Box 4 PASSES ALL LINES WITH >= 16px PADDING!")
