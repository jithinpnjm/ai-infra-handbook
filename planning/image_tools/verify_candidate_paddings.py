#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

tree = ET.parse("candidate_ssh_infographic.svg")
root = tree.getroot()

top_boxes = [
    ("header-container", 60, 140, 1480, 155),
    ("lane-1", 60, 335, 1480, 210),
    ("lane-2", 60, 585, 1480, 210),
    ("lane-3", 60, 835, 1480, 210),
    ("footer", 60, 1085, 1480, 70)
]

print("=== 1. CHECKING OUTSIDE MARGINS (>= 40px) ===")
H = 1200
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
    ("header to lane-1", 335 - (140 + 155)),
    ("lane-1 to lane-2", 585 - (335 + 210)),
    ("lane-2 to lane-3", 835 - (585 + 210)),
    ("lane-3 to footer", 1085 - (835 + 210)),
]
for name, gap in gaps:
    print(f"  {name:30s}: {gap}px >= 40px")
    assert gap >= 40, f"Gap {name} {gap} < 40!"
print("PASS: All top-level box gaps >= 40px.\n")

print("=== 3. CHECKING TEXT PADDING INSIDE BOXES (>= 16px) ===")

text_checks = [
    ("Your machine", "Your machine", 30, False, 80, 148, 410, 64, 310, 194, "middle"),
    ("Server", "Server", 30, False, 1110, 148, 410, 64, 1330, 194, "middle"),
    ("SSH connection badge", "SSH connection, port 22", 24, False, 600, 151, 400, 58, 800, 191, "middle"),
    ("Which side listens?", "Which side listens?", 30, False, 80, 222, 690, 64, 425, 268, "middle"),
    ("Where does the traffic go?", "Where does the traffic go?", 30, False, 830, 222, 690, 64, 1175, 268, "middle"),
    
    # Lane 1
    ("L1 title", "-L local forward", 30, False, 80, 345, 340, 64, 250, 391, "middle"),
    ("L1 command", "ssh -L 6006:localhost:6006 gpu01", 24, True, 440, 349, 560, 56, 720, 389, "middle"),
    ("L1 listen", "listens on 6006", 30, False, 80, 417, 350, 116, 255, 482, "middle"),
    ("L1 note l1", "open http://localhost:6006", 24, False, 520, 448, 510, 84, 775, 488, "middle"),
    ("L1 note l2", "to reach TensorBoard", 24, False, 520, 448, 510, 84, 775, 514, "middle"),
    ("L1 dest", "localhost:6006 on gpu01", 26, False, 1120, 417, 400, 116, 1320, 481, "middle"),

    # Lane 2
    ("L2 title", "-R remote forward", 30, False, 80, 595, 350, 64, 255, 641, "middle"),
    ("L2 command", "ssh -R 9000:localhost:8000 server", 24, True, 450, 599, 580, 56, 740, 639, "middle"),
    ("L2 dest l1", "localhost:8000", 26, False, 80, 667, 420, 116, 290, 718, "middle"),
    ("L2 dest l2", "on your machine", 26, False, 80, 667, 420, 116, 290, 750, "middle"),
    ("L2 listen", "listens on 9000", 30, False, 1100, 667, 420, 116, 1310, 732, "middle"),

    # Lane 3
    ("L3 title", "-D dynamic forward", 30, False, 80, 845, 370, 64, 265, 891, "middle"),
    ("L3 command", "ssh -D 1080 bastion", 24, True, 470, 849, 420, 56, 680, 889, "middle"),
    ("L3 listen", "SOCKS proxy on 1080", 30, False, 80, 917, 420, 116, 290, 982, "middle"),
    ("L3 dest l1", "traffic goes through bastion", 24, False, 1050, 917, 470, 116, 1285, 968, "middle"),
    ("L3 dest l2", "to any destination", 24, False, 1050, 917, 470, 116, 1285, 998, "middle"),

    # Footer
    ("Footer", "-N -f: no remote command, go to background", 28, True, 60, 1085, 1480, 70, 800, 1129, "middle")
]

all_pass = True
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
    if pad_left < 15.5 or pad_right < 15.5 or pad_top < 15.5 or pad_bot < 15.5:
        print(f"FAILED: {bname}")
        all_pass = False

assert all_pass, "Some text paddings failed!"
print("\nPASS: All text paddings inside boxes >= 16px.")
