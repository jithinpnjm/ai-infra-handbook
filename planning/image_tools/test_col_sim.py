#!/usr/bin/env python3
import re

# Comprehensive layout verification script

# Canvas
CANVAS_W = 1600
CANVAS_H = 1080 # Let's test 1080
MARGIN_X = 40

# Columns
b1_x = 40
b1_w = 250

gap1_x = b1_x + b1_w # 290
gap1_w = 140

b2_x = gap1_x + gap1_w # 430
b2_w = 270

gap2_x = b2_x + b2_w # 700
gap2_w = 140

b3_x = gap2_x + gap2_w # 840
b3_w = 320

gap3_x = b3_x + b3_w # 1160
gap3_w = 130

b4_x = gap3_x + gap3_w # 1290
b4_w = 270

assert b4_x + b4_w == 1600 - MARGIN_X, f"Total width {b4_x + b4_w} != 1560"
print(f"Col 1: [{b1_x} .. {b1_x+b1_w}] (w={b1_w})")
print(f"Gap 1: [{gap1_x} .. {gap1_x+gap1_w}] (w={gap1_w})")
print(f"Col 2: [{b2_x} .. {b2_x+b2_w}] (w={b2_w})")
print(f"Gap 2: [{gap2_x} .. {gap2_x+gap2_w}] (w={gap2_w})")
print(f"Col 3: [{b3_x} .. {b3_x+b3_w}] (w={b3_w})")
print(f"Gap 3: [{gap3_x} .. {gap3_x+gap3_w}] (w={gap3_w})")
print(f"Col 4: [{b4_x} .. {b4_x+b4_w}] (w={b4_w})")

def test_box_lines(box_name, box_w, lines_info):
    print(f"\n--- Testing {box_name} (width {box_w} px) ---")
    all_ok = True
    for text, fs, is_mono in lines_info:
        coeff = 0.62 if is_mono else 0.6
        w = len(text) * fs * coeff
        pad = (box_w - w) / 2
        ok = pad >= 16.0
        if not ok:
            all_ok = False
        print(f"  [{'PASS' if ok else 'FAIL'}] pad={pad:5.1f}px (w={w:5.1f}px) fs={fs} mono={is_mono} | '{text}'")
    return all_ok

# Box 1 lines:
b1_lines = [
    ("Root directory /", 24, False), # 16 chars * 24 * 0.6 = 230.4 -> pad = (250 - 230.4)/2 = 9.8 FAIL!
]
# Wait! Let's see: if Root directory / fails 250 px, what if it's 2 lines:
b1_lines_wrapped = [
    ("Root directory ", 24, False), # 15 chars * 24 * 0.6 = 216 -> pad = (250 - 216)/2 = 17 px PASS!
    ("/", 24, True),
    ("home -> inode A", 24, True), # 15 chars * 24 * 0.62 = 223.2 -> pad = (250 - 223.2)/2 = 13.4 FAIL!
]
print("B1 lines test:")
test_box_lines("B1 wrapped", b1_w, b1_lines_wrapped)
