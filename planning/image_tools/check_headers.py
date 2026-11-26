#!/usr/bin/env python3

# Let's test header box dimensions with icon above title
# Box y = 70 to 185 (height = 115)
# Icon: center cx, y = 82, size = 40x40 (from y=82 to y=122)
# Text:
# 1-line title (slurmctld, slurmdbd):
# font-size 30 bold, y = 158
# 2-line title (User on / login node, slurmd on / node A, slurmd on / node B):
# font-size 28 or 30 bold:
# line 1: y = 145
# line 2: y = 175

titles = [
    ["User on", "login node"],
    ["slurmctld"],
    ["slurmdbd"],
    ["slurmd on", "node A"],
    ["slurmd on", "node B"]
]

cx_list = [180, 490, 800, 1110, 1420]
bx_list = [50, 360, 670, 980, 1290]
bw = 260

for i, t in enumerate(titles):
    cx = cx_list[i]
    bx = bx_list[i]
    for line in t:
        w = len(line) * 0.6 * 30
        left = cx - w / 2.0
        right = cx + w / 2.0
        pad_l = left - bx
        pad_r = (bx + bw) - right
        print(f"[{line:12s}] in box {bx}..{bx+bw}: w={w:5.1f}px, pad_l={pad_l:4.1f}px, pad_r={pad_r:4.1f}px (min={min(pad_l, pad_r):.1f}px)")
        assert pad_l >= 16 and pad_r >= 16
print("ALL HEADER TEXT PADDINGS >= 16px!")
