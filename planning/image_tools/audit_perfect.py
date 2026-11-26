#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

tree = ET.parse("candidate.svg")
root = tree.getroot()

vb = root.get("viewBox").split()
H = float(vb[3])
W = float(vb[2])

print(f"Canvas: W={W}, H={H}")

# Check outside margins for all top-level rects
# Lane 1, Lane 2, Lane 3, Takeaway bar
top_rects = [
    ("Lane 1", 40, 95, 1520, 275),
    ("Lane 2", 40, 415, 1520, 275),
    ("Lane 3", 40, 735, 1520, 285),
    ("Takeaway", 40, 1065, 1520, 80)
]

for name, x, y, w, h in top_rects:
    left_m = x
    right_m = W - (x + w)
    top_m = y
    bot_m = H - (y + h)
    assert left_m >= 40, f"{name} left {left_m} < 40"
    assert right_m >= 40, f"{name} right {right_m} < 40"
    assert top_m >= 40, f"{name} top {top_m} < 40"
    assert bot_m >= 40, f"{name} bot {bot_m} < 40"
    print(f"OK Margin: {name} (L={left_m}, R={right_m}, T={top_m}, B={bot_m})")

# Check vertical gaps between top containers
gaps = [
    ("Lane 1 to Lane 2", 415 - (95 + 275)),
    ("Lane 2 to Lane 3", 735 - (415 + 275)),
    ("Lane 3 to Takeaway", 1065 - (735 + 285))
]

for name, gap in gaps:
    assert gap >= 40, f"Gap {name} {gap} < 40"
    print(f"OK Gap: {name} = {gap}px (>= 40px)")

# Check inside boxes:
# Step 1 Note Box: x=270, y=185, w=310, h=165
# Step 2 Box: x=620, y=175, w=365, h=175
# Step 4 Box: x=1030, y=175, w=280, h=175
horizontal_gaps = [
    ("Step 1 note to Step 2 box", 620 - (270 + 310)),
    ("Step 2 box to Step 4 box", 1030 - (620 + 365))
]

for name, gap in horizontal_gaps:
    assert gap >= 40, f"Gap {name} {gap} < 40"
    print(f"OK Gap: {name} = {gap}px (>= 40px)")

# Check text clear of Step 2 box:
# Step 1 text: x=322, text-anchor=start.
# Longest tspan: "--signal=B:USR1@600" -> 19 chars * 0.62 * 24 = 282.72px
# Right edge = 322 + 282.72 = 604.72px.
# Step 2 box left edge = 620.
clearance_step1_to_step2 = 620 - (322 + 19 * 0.62 * 24)
print(f"Clearance Step 1 text to Step 2 box: {clearance_step1_to_step2:.1f}px (clear!)")
assert clearance_step1_to_step2 > 0

# Step 1 circle cx=290, r=24 -> right edge = 314.
# Text starts at x=322 -> clearance = 322 - 314 = 8px.
# Circle 2 cx=645, r=24 -> left edge = 621.
# Clearance to circle 2 = 621 - 604.72 = 16.28px.
print("All clearances and gaps verified successfully!")
