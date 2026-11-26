#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

# Test the 4-box 240px wide layout with 186px gaps

canvas_w = 1600
margin_x = 40
available_w = canvas_w - 2 * margin_x # 1520

box_w = 245
gap_w = (available_w - 4 * box_w) / 3 # (1520 - 980) / 3 = 540 / 3 = 180 px!

print(f"box_w = {box_w}, gap_w = {gap_w}")

# Let's check positions:
b1_x = margin_x # 40
b1_r = b1_x + box_w # 285

arr1_x1 = b1_r # 285
arr1_x2 = arr1_x1 + gap_w # 465

b2_x = arr1_x2 # 465
b2_r = b2_x + box_w # 710

arr2_x1 = b2_r # 710
arr2_x2 = arr2_x1 + gap_w # 890

b3_x = arr2_x2 # 890
b3_r = b3_x + box_w # 1135

arr3_x1 = b3_r # 1135
arr3_x2 = arr3_x1 + gap_w # 1315

b4_x = arr3_x2 # 1315
b4_r = b4_x + box_w # 1560

assert b4_r == 1600 - margin_x

print(f"B1: [{b1_x}, {b1_r}]")
print(f"Arr 1: [{arr1_x1}, {arr1_x2}] (mid={(arr1_x1+arr1_x2)/2})")
print(f"B2: [{b2_x}, {b2_r}]")
print(f"Arr 2: [{arr2_x1}, {arr2_x2}] (mid={(arr2_x1+arr2_x2)/2})")
print(f"B3: [{b3_x}, {b3_r}]")
print(f"Arr 3: [{arr3_x1}, {arr3_x2}] (mid={(arr3_x1+arr3_x2)/2})")
print(f"B4: [{b4_x}, {b4_r}]")

# Now let's test every line in each box with box_w = 245:
def check_paddings(name, lines):
    print(f"\nChecking {name} (w={box_w}):")
    for text, fs, is_mono in lines:
        coeff = 0.62 if is_mono else 0.6
        w = len(text) * fs * coeff
        pad = (box_w - w) / 2
        ok = pad >= 16.0
        print(f"  [{'PASS' if ok else 'FAIL'}] pad={pad:5.1f}px (w={w:5.1f}px) | '{text}'")
        assert ok, f"Line '{text}' failed padding check: {pad:.1f} < 16"

# Box 1:
# Header: 'Root directory /'
# Row: 'home -> inode A'
b1_lines = [
    ("Root ", 26, False),
    ("directory /", 26, False),
    ("home -> ", 24, True),
    ("inode A", 24, True)
]
check_paddings("Box 1", b1_lines)

# Box 2:
# Header: 'Directory /home (inode A)'
# Row: 'alice -> inode B'
b2_lines = [
    ("Directory ", 26, False),
    ("/home ", 26, True),
    ("(inode A)", 24, False),
    ("alice -> ", 24, True),
    ("inode B", 24, True)
]
check_paddings("Box 2", b2_lines)

# Box 3:
# Header: 'Directory /home/alice (inode B)'
# Row: 'train.py -> inode C'
b3_lines = [
    ("Directory ", 26, False),
    ("/home/alice ", 24, True),
    ("(inode B)", 24, False),
    ("train.py -> ", 24, True),
    ("inode C", 24, True)
]
check_paddings("Box 3", b3_lines)

# Box 4:
# 'Inode C: type, permissions, owner, size, times, link count, pointers to data blocks'
b4_lines = [
    ("Inode C: type, ", 24, False),
    ("permissions, ", 24, False),
    ("owner, size, ", 24, False),
    ("times, link ", 24, False),
    ("count, pointers ", 24, False),
    ("to data blocks", 24, False)
]
check_paddings("Box 4", b4_lines)

# Arrow labels in 180px gap:
def check_gap_clearance(name, lines):
    print(f"\nChecking {name} in gap {gap_w}px:")
    for text, fs, is_mono in lines:
        coeff = 0.62 if is_mono else 0.6
        w = len(text) * fs * coeff
        clearance = (gap_w - w) / 2
        print(f"  [CLEAR] clearance={clearance:5.1f}px (w={w:5.1f}px) | '{text}'")
        assert clearance >= 10, f"Clearance too small: {clearance:.1f}"

check_gap_clearance("Arrow 1", [("look up ", 24, False), ("home", 24, True)])
check_gap_clearance("Arrow 2", [("look up ", 24, False), ("alice", 24, True)])
check_gap_clearance("Arrow 3", [("look up ", 24, False), ("train.py", 24, True)])

print("\nALL BOX PADDINGS AND GAP CLEARANCES PASS WITH FLYING COLORS!")
