import re

# Canvas: 1600 x 1080
W_CANVAS = 1600
H_CANVAS = 1080

# Container: x=40, y=180, w=1520, h=830
CONT_X = 40
CONT_Y = 180
CONT_W = 1520
CONT_H = 830

# Job boxes: w=380, h=450, y=280
# Box 1 (lint): x=70
# Box 2 (molecule): x=610
# Box 3 (gpu-hw): x=1150
BOX_Y = 280
BOX_W = 380
BOX_H = 450

BOX1_X = 70
BOX2_X = 610
BOX3_X = 1150

GAP1 = BOX2_X - (BOX1_X + BOX_W) # 610 - 450 = 160
GAP2 = BOX3_X - (BOX2_X + BOX_W) # 1150 - 990 = 160

print(f"Gap 1: {GAP1}px, Gap 2: {GAP2}px. Equal: {GAP1 == GAP2}")
assert GAP1 == 160
assert GAP2 == 160

# Arrow from lint to molecule:
# From right edge of Box 1 (450) to left edge of Box 2 (610)
ARROW_X1 = BOX1_X + BOX_W # 450
ARROW_X2 = BOX2_X          # 610
ARROW_Y = 505

print(f"Arrow: ({ARROW_X1}, {ARROW_Y}) -> ({ARROW_X2}, {ARROW_Y}) length = {ARROW_X2 - ARROW_X1}px")

# Notes under boxes:
# Molecule note: under Box 2, x=610, y=760, w=380, h=100
# GPU-HW note: under Box 3, x=1150, y=760, w=380, h=210

print("Layout coordinates valid!")
