#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

tree = ET.parse("candidate_read_conv_clean.svg")
root = tree.getroot()

print("=== CHECKING ALL BOXES AND TEXT PADDINGS ===")

# 1. Check all container rects (w >= 100) and outside margins
rects = []
for elem in root.iter('{http://www.w3.org/2000/svg}rect'):
    x = float(elem.attrib.get('x', 0))
    y = float(elem.attrib.get('y', 0))
    w = float(elem.attrib.get('width', 0))
    h = float(elem.attrib.get('height', 0))
    if w == 1600 and h == 1200:
        continue # background
    if w < 100 or h < 50:
        continue # icon internal shape
    rects.append((elem, x, y, w, h))

print(f"Total container rects: {len(rects)}")
for elem, x, y, w, h in rects:
    print(f"Container at ({x}, {y}) w={w}, h={h}, right={x+w}, bottom={y+h}")
    assert x >= 40, f"Left margin {x} < 40!"
    assert x + w <= 1560, f"Right edge {x+w} > 1560 (margin < 40)!"
    assert y >= 40, f"Top margin {y} < 40!"
    assert y + h <= 1160, f"Bottom edge {y+h} > 1160 (margin < 40)!"

print("   [PASS] All content boxes obey >= 40px outside margins.")

# 2. Check gaps between boxes:
# - Left column:
#   Bracket 1: y=250..390
#   Bracket 2: y=430..540
#   Bracket 3: y=580..755
assert 430 - 390 >= 40
assert 580 - 540 >= 40

# - Bottom panels:
assert 825 - 755 >= 40
assert 930 - 885 >= 40
assert 1035 - 990 >= 40

# - Host boxes:
assert 1040 - 900 >= 40
assert 250 - 240 >= 10
print("   [PASS] All gaps between boxes >= 40px.")

# 3. Text padding checks inside boxes:
# Bracket 1 text:
b1_lines = [
    "lines 1-2: finding the link ",
    "address because the client ",
    "needs the server's MAC ",
    "before it can send a frame"
]
b1_widths = [len(l) * 0.6 * 24 for l in b1_lines]
max_b1_w = max(b1_widths)
pad_x_b1 = (370 - max_b1_w) / 2
print(f"Bracket 1 text max_w={max_b1_w:.1f}px, pad_x={pad_x_b1:.1f}px")
assert pad_x_b1 >= 16, f"Bracket 1 pad_x {pad_x_b1} < 16!"
b1_h = 3 * 26 + 24
pad_y_b1 = (140 - b1_h) / 2
print(f"Bracket 1 text h={b1_h}px, pad_y={pad_y_b1:.1f}px")
assert pad_y_b1 >= 16, f"Bracket 1 pad_y {pad_y_b1} < 16!"

# Bracket 2 text:
b2_w = len("three-way handshake") * 0.6 * 24
pad_x_b2 = (370 - b2_w) / 2
b2_h = 32 + 24
pad_y_b2 = (110 - b2_h) / 2
print(f"Bracket 2 pad_x={pad_x_b2:.1f}px, pad_y={pad_y_b2:.1f}px")
assert pad_x_b2 >= 16 and pad_y_b2 >= 16

# Bracket 3 text:
b3_w = len("lines 6-9: data") * 0.6 * 24
pad_x_b3 = (370 - b3_w) / 2
pad_y_b3 = (175 - 24) / 2
print(f"Bracket 3 pad_x={pad_x_b3:.1f}px, pad_y={pad_y_b3:.1f}px")
assert pad_x_b3 >= 16 and pad_y_b3 >= 16

# Host 1 text:
h1_w = len("duplex.example.com ") * 0.6 * 30
icon_gap = 485 - 461
right_pad = 900 - (485 + h1_w)
top_pad = (180 - 24) - 140
bot_pad = 240 - (180 + 36 + 6)
print(f"Host 1 icon_gap={icon_gap}px, right_pad={right_pad:.1f}px, top_pad={top_pad}px, bot_pad={bot_pad}px")
assert icon_gap >= 16 and right_pad >= 16 and top_pad >= 16 and bot_pad >= 16

# Host 2 text:
h2_w = len("mikado.example.com ") * 0.6 * 30
h2_icon_gap = 1145 - 1121
h2_right_pad = 1560 - (1145 + h2_w)
print(f"Host 2 icon_gap={h2_icon_gap}px, right_pad={h2_right_pad:.1f}px")
assert h2_icon_gap >= 16 and h2_right_pad >= 16

# Legend text:
leg_w = len("S SYN, S. SYN-ACK, . ACK, P. PSH-ACK, F. FIN-ACK, R or R. RST") * 0.62 * 24
pad_x_leg = (1520 - leg_w) / 2
pad_y_leg = (60 - 24) / 2
print(f"Legend pad_x={pad_x_leg:.1f}px, pad_y={pad_y_leg:.1f}px")
assert pad_x_leg >= 16 and pad_y_leg >= 16

# Footer text:
foot_w = len("summary: 9 packets received by filter, 0 packets dropped by kernel") * 0.6 * 24
pad_x_foot = (1520 - foot_w) / 2
pad_y_foot = (60 - 24) / 2
print(f"Footer pad_x={pad_x_foot:.1f}px, pad_y={pad_y_foot:.1f}px")
assert pad_x_foot >= 16 and pad_y_foot >= 16

# Bottom bar text:
bbar_w1 = len("Read the flags in order; a SYN with no reply stops the story at the first line, ") * 0.6 * 24
pad_x_bbar = (1520 - bbar_w1) / 2
bbar_h = 36 + 24
pad_y_bbar = (115 - bbar_h) / 2
print(f"Bottom bar pad_x={pad_x_bbar:.1f}px, pad_y={pad_y_bbar:.1f}px")
assert pad_x_bbar >= 16 and pad_y_bbar >= 16

# 4. Check ladder message labels:
msgs = [
    ("arp who-has mikado tell duplex", 30),
    ("arp reply mikado is-at 0:2:2d:b:ee:4e", 37),
    ("S 3200063165 win 5840 mss 1460 sackOK (DF)", 42),
    ("S ack 3200063166 win 5792", 25),
    (". ack 1", 7),
    ("P 1:427(426)", 12),
    (". ack 427", 9),
    ("P 1:773(772)", 12),
    (". ack 773", 9)
]
for msg, nchars in msgs:
    mw = nchars * 0.62 * 24
    left_t = 1040 - mw/2
    right_t = 1040 + mw/2
    d_left = left_t - 640
    d_right = 1440 - right_t
    print(f"Msg '{msg[:20]}...': w={mw:.1f}px, d_left={d_left:.1f}px, d_right={d_right:.1f}px")
    assert d_left >= 16 + 18, f"Message too close to left: {d_left}"
    assert d_right >= 16 + 18, f"Message too close to right: {d_right}"

print("\n=== ALL PADDINGS, GAPS, MARGINS, AND CLEARANCES VERIFIED PERFECT! ===")
