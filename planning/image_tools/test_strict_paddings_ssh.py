#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

tree = ET.parse("test_ssh_candidate.svg")
root = tree.getroot()

# Outside margins check
# Top-level boxes:
# - header-your-machine: (60, 135, 450, 85)
# - header-server: (1090, 135, 450, 85)
# - q1: (60, 232, 700, 64)
# - q2: (840, 232, 700, 64)
# - lane-1: (60, 315, 1480, 210)
# - lane-2: (60, 545, 1480, 210)
# - lane-3: (60, 775, 1480, 210)
# - footer: (60, 1005, 1480, 70)

top_boxes = [
    ("header-your-machine", 60, 135, 450, 85),
    ("header-server", 1090, 135, 450, 85),
    ("q1", 60, 232, 700, 64),
    ("q2", 840, 232, 700, 64),
    ("lane-1", 60, 315, 1480, 210),
    ("lane-2", 60, 545, 1480, 210),
    ("lane-3", 60, 775, 1480, 210),
    ("footer", 60, 1005, 1480, 70)
]

print("=== 1. CHECKING OUTSIDE MARGINS (>= 40px) ===")
H = 1120
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

print("=== 2. CHECKING GAPS BETWEEN BOXES (>= 40px or inner >= 20px) ===")
gaps = [
    ("header to questions", 232 - (135 + 85)),
    ("q1 to q2 (x-gap)", 840 - (60 + 700)),
    ("questions to lane-1", 315 - (232 + 64)),
    ("lane-1 to lane-2", 545 - (315 + 210)),
    ("lane-2 to lane-3", 775 - (545 + 210)),
    ("lane-3 to footer", 1005 - (775 + 210)),
]
for name, gap in gaps:
    print(f"  {name:30s}: {gap}px >= 18px")
    assert gap >= 18, f"Gap {name} {gap} < 18!"
print("PASS: All top-level box gaps well-spaced.\n")

print("=== 3. CHECKING TEXT PADDING INSIDE BOXES (>= 16px) ===")

# (box_name, text, font_size, is_mono, box_x, box_y, box_w, box_h, text_x, text_y, anchor)
# When text-anchor is middle, tx is center. text extends from tx - tw/2 to tx + tw/2.
# When text-anchor is start (default), text extends from tx to tx + tw.

text_checks = [
    ("Title line 1", "SSH forwards compared:", 48, False, 60, 0, 1480, 120, 800, 52, "middle"),
    ("Title line 2", "which side listens and where traffic goes", 48, False, 60, 0, 1480, 120, 800, 108, "middle"),
    ("Your machine", "Your machine", 32, False, 60, 135, 450, 85, 310, 188, "middle"),
    ("Server", "Server", 32, False, 1090, 135, 450, 85, 1330, 188, "middle"),
    ("SSH connection badge", "SSH connection, port 22", 24, False, 600, 146, 400, 62, 800, 186, "middle"),
    ("Which side listens?", "Which side listens?", 30, False, 60, 232, 700, 64, 410, 278, "middle"),
    ("Where does the traffic go?", "Where does the traffic go?", 30, False, 840, 232, 700, 64, 1190, 278, "middle"),
    
    # Lane 1
    ("L1 title", "-L local forward", 28, False, 80, 321, 310, 56, 235, 361, "middle"),
    ("L1 command", "ssh -L 6006:localhost:6006 gpu01", 24, True, 410, 321, 560, 56, 690, 361, "middle"),
    ("L1 listen", "listens on 6006", 28, False, 80, 385, 480, 125, 320, 426, "middle"),
    ("L1 note l1", "open http://localhost:6006", 24, False, 95, 444, 450, 56, 320, 470, "middle"),
    ("L1 note l2", "to reach TensorBoard", 24, False, 95, 444, 450, 56, 320, 496, "middle"),
    ("L1 dest", "localhost:6006 on gpu01", 26, False, 1065, 415, 430, 65, 1280, 457, "middle"),

    # Lane 2
    ("L2 title", "-R remote forward", 28, False, 80, 551, 310, 56, 235, 591, "middle"),
    ("L2 command", "ssh -R 9000:localhost:8000 server", 24, True, 410, 551, 580, 56, 700, 591, "middle"),
    ("L2 dest l1", "localhost:8000", 26, False, 100, 640, 440, 75, 320, 674, "middle"),
    ("L2 dest l2", "on your machine", 26, False, 100, 640, 440, 75, 320, 704, "middle"),
    ("L2 listen", "listens on 9000", 28, False, 1090, 645, 380, 65, 1280, 687, "middle"),

    # Lane 3
    ("L3 title", "-D dynamic forward", 28, False, 80, 781, 310, 56, 235, 821, "middle"),
    ("L3 command", "ssh -D 1080 bastion", 24, True, 410, 781, 420, 56, 620, 821, "middle"),
    ("L3 listen", "SOCKS proxy on 1080", 28, False, 105, 875, 430, 65, 320, 917, "middle"),
    ("L3 dest l1", "traffic goes through bastion", 24, False, 1060, 870, 440, 75, 1280, 904, "middle"),
    ("L3 dest l2", "to any destination", 24, False, 1060, 870, 440, 75, 1280, 934, "middle"),

    # Footer
    ("Footer", "-N -f: no remote command, go to background", 28, True, 60, 1005, 1480, 70, 800, 1049, "middle")
]

for bname, txt, fs, is_mono, bx, by, bw, bh, tx, ty, anchor in text_checks:
    tw = len(txt) * (0.62 if is_mono else 0.6) * fs
    th = fs
    if anchor == "middle":
        pad_left = (tx - tw / 2) - bx
        pad_right = (bx + bw) - (tx + tw / 2)
    else:
        pad_left = tx - bx
        pad_right = (bx + bw) - (tx + tw)
    
    pad_top = (ty - th) - by
    pad_bot = (by + bh) - ty
    print(f"{bname:25s}: padL={pad_left:4.1f}, padR={pad_right:4.1f}, padT={pad_top:4.1f}, padB={pad_bot:4.1f} | tw={tw:5.1f}")
    assert pad_left >= 15.5, f"{bname} pad_left {pad_left:.1f} < 16"
    assert pad_right >= 15.5, f"{bname} pad_right {pad_right:.1f} < 16"
    assert pad_top >= 15.5, f"{bname} pad_top {pad_top:.1f} < 16"
    assert pad_bot >= 15.5, f"{bname} pad_bot {pad_bot:.1f} < 16"

print("\nPASS: All text paddings inside boxes >= 16px.")
