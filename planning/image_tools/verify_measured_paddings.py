import json

# Measured boxes from test_side_by_side_playwright.py
# Let's map each to its card rect:
cards = [
    ("Title", None, (200.4, 10.0, 1199.2, 55.0)),
    ("Subtitle Pill", (450, 72, 700, 64), (543.3, 90.0, 513.4, 28.0)),
    ("Setup Box", (50, 176, 1500, 94), (155.0, 193.0, 801.8, 61.0)),
    ("Table 1 Header", (70, 328, 685, 96), (160.0, 338.0, 473.5, 69.0)),
    ("T1 Row 1", (70, 438, 685, 110), (90.0, 456.0, 489.7, 28.0)),
    ("T1 Row 2", (70, 560, 685, 110), (90.0, 578.0, 504.1, 28.0)),
    ("T1 Row 3", (70, 682, 685, 110), (90.0, 700.0, 475.3, 28.0)),
    ("T1 Row 4", (70, 804, 685, 110), (90.0, 822.0, 518.5, 28.0)),
    ("Table 2 Header", (845, 328, 685, 96), (935.0, 338.0, 374.5, 69.0)),
    ("T2 Row 1", (845, 434, 685, 92), (865.0, 449.0, 360.1, 61.0)),
    ("T2 Row 2", (845, 534, 685, 84), (865.0, 552.0, 388.9, 28.0)),
    ("T2 Row 3", (845, 626, 685, 84), (865.0, 644.0, 388.9, 28.0)),
    ("T2 Row 4", (845, 718, 685, 84), (865.0, 736.0, 388.9, 28.0)),
    ("T2 Row 5", (845, 810, 685, 92), (865.0, 829.0, 576.1, 28.0)),
    ("Takeaway Bar", (50, 975, 1500, 175), (373.8, 1000.0, 852.4, 130.0))
]

print("=== CHECKING REAL CHROMIUM PADDINGS >= 16.0px ===")
all_pass = True
for name, rect, bbox in cards:
    if rect is None:
        continue
    rx, ry, rw, rh = rect
    bx, by, bw, bh = bbox
    r_right = rx + rw
    r_bottom = ry + rh
    b_right = bx + bw
    b_bottom = by + bh
    
    pad_left = bx - rx
    pad_right = r_right - b_right
    pad_top = by - ry
    pad_bottom = r_bottom - b_bottom
    
    ok = (pad_left >= 16.0 and pad_right >= 16.0 and pad_top >= 16.0 and pad_bottom >= 16.0)
    status = "PASS" if ok else "FAIL"
    if not ok:
        all_pass = False
    print(f"[{status}] {name:15s} | L={pad_left:5.1f}, R={pad_right:5.1f}, T={pad_top:5.1f}, B={pad_bottom:5.1f}")

print(f"\nALL REAL CHROMIUM PADDINGS >= 16px: {all_pass}")
