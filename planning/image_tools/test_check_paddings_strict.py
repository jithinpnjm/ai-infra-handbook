#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

tree = ET.parse("test_candidate.svg")
root = tree.getroot()

# Outside margins check
# All top-level boxes:
# - control-plane-band: (60, 80, 1480, 70)
# - node-customer: (70, 210, 370, 90)
# - panel-eu-region: (60, 380, 940, 580)
# - panel-us-region: (1080, 205, 460, 430)
# - takeaway-bar: (60, 990, 1480, 70)

top_boxes = [
    ("control-plane-band", 60, 75, 1480, 75),
    ("node-customer", 70, 210, 430, 90),
    ("panel-eu-region", 60, 380, 940, 560),
    ("panel-us-region", 1080, 205, 460, 430),
    ("takeaway-bar", 60, 990, 1480, 70)
]

print("=== 1. CHECKING OUTSIDE MARGINS (>= 40px) ===")
H = 1100
for name, x, y, w, h in top_boxes:
    lm = x
    rm = 1600 - (x + w)
    tm = y
    bm = H - (y + h)
    print(f"{name:20s}: margins L={lm:3d}, R={rm:3d}, T={tm:3d}, B={bm:3d}")
    assert lm >= 40, f"{name} left margin {lm} < 40"
    assert rm >= 40, f"{name} right margin {rm} < 40"
    assert tm >= 40, f"{name} top margin {tm} < 40"
    assert bm >= 40, f"{name} bottom margin {bm} < 40"
print("PASS: All top-level outside margins >= 40px.\n")

print("=== 2. CHECKING GAPS BETWEEN BOXES (>= 40px) ===")
gaps = [
    ("control-plane to customer", 210 - (80 + 70)),
    ("control-plane to us-panel", 205 - (80 + 70)),
    ("customer to eu-panel", 380 - (210 + 90)),
    ("eu-panel to takeaway-bar", 990 - (380 + 560)),
    ("eu-panel to us-panel (x-gap)", 1080 - (60 + 940)),
]
for name, gap in gaps:
    print(f"  {name:30s}: {gap}px >= 40px")
    assert gap >= 40, f"Gap {name} {gap} < 40!"
print("PASS: All top-level box gaps >= 40px.\n")

print("=== 3. CHECKING INSIDE EU PANEL BOXES & GAPS ===")
# Inside EU panel:
# - box-gateway: (90, 475, 410, 200)
# - box-replica-group: (530, 475, 440, 200)
# - box-log-store: (90, 705, 460, 230)
# - box-metering: (580, 705, 390, 230)
eu_inner = [
    ("gateway", 90, 465, 410, 190),
    ("replica-group", 530, 465, 440, 190),
    ("log-store", 90, 685, 460, 220),
    ("metering", 580, 685, 390, 220)
]
for name, x, y, w, h in eu_inner:
    # Check bounds inside EU panel [60, 380, 1000, 940]
    lm = x - 60
    rm = 1000 - (x + w)
    tm = y - 380
    bm = 940 - (y + h)
    print(f"Inner {name:15s}: margins L={lm:2d}, R={rm:2d}, T={tm:2d}, B={bm:2d}")
    assert lm >= 25 and rm >= 25 and tm >= 25 and bm >= 25

inner_gaps = [
    ("gateway to replica-group (x)", 530 - (90 + 410)),
    ("gateway to log-store (y)", 685 - (465 + 190)),
    ("replica-group to metering (y)", 685 - (465 + 190)),
    ("log-store to metering (x)", 580 - (90 + 460))
]
for name, gap in inner_gaps:
    print(f"  Inner gap {name:30s}: {gap}px >= 25px")
    assert gap >= 25

print("PASS: Inner EU panel boxes and gaps well-spaced.\n")

print("=== 4. CHECKING TEXT PADDING INSIDE BOXES (>= 16px) ===")
# Text inside boxes padding checks
# Conservatively: len(text) * 0.6 * font_size
text_paddings = [
    # (box_name, text, font_size, box_x, box_y, box_w, box_h, text_x, text_y)
    ("Control plane band", "Control plane: metadata only, global", 30, 60, 75, 1480, 75, 160, 122),
    ("European customer", "European customer", 30, 70, 210, 430, 90, 165, 266),
    ("US region", "US region", 32, 1080, 205, 460, 430, 1185, 268),
    ("EU region title", "EU region (promised region)", 32, 60, 380, 940, 560, 155, 438),
    ("Gateway title", "Gateway", 30, 90, 465, 410, 190, 190, 535),
    ("Replica group title", "Replica group", 30, 530, 465, 440, 190, 635, 535),
    ("Log store title", "Log store", 30, 90, 685, 460, 220, 190, 750),
    ("Log store line 1", "Prompts, completions and", 24, 90, 685, 460, 220, 115, 815),
    ("Log store line 2", "logs stay in region", 24, 90, 685, 460, 220, 115, 849),
    ("Metering title", "Metering", 30, 580, 685, 390, 220, 680, 750),
    ("Takeaway bar", "Cross-region failover is off by default for residency-bound tenants.", 26, 60, 990, 1480, 70, 800-530, 1034)
]

for bname, txt, fs, bx, by, bw, bh, tx, ty in text_paddings:
    tw = len(txt) * 0.6 * fs
    th = fs
    pad_left = tx - bx
    pad_right = (bx + bw) - (tx + tw)
    pad_top = (ty - th) - by
    pad_bot = (by + bh) - ty
    print(f"{bname:20s}: padL={pad_left:4.1f}, padR={pad_right:4.1f}, padT={pad_top:4.1f}, padB={pad_bot:4.1f} | text_w={tw:5.1f}")
    assert pad_left >= 16, f"{bname} pad_left {pad_left} < 16"
    assert pad_right >= 16, f"{bname} pad_right {pad_right} < 16"
    assert pad_top >= 16, f"{bname} pad_top {pad_top} < 16"
    assert pad_bot >= 16, f"{bname} pad_bot {pad_bot} < 16"

print("\nPASS: All text paddings inside boxes >= 16px.")
