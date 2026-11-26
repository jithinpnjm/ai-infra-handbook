import xml.etree.ElementTree as ET
import re

tree = ET.parse("test_candidate_le.svg")
root = tree.getroot()

# Check all text paddings conservatively:
# Character width estimates:
# sans: 0.6 * font-size
# monospace: 0.62 * font-size

# Let's inspect each card / container and its text
checks = [
    # (box_desc, box_x, box_y, box_w, box_h, text, fs, is_mono)
    ("Left note card", 50, 160, 510, 410, "Each box counts every request", 24, False),
    ("Left note card line 2", 50, 160, 510, 410, "at or under its bound: cumulative", 24, False),
    ("Row 1 card", 915, 185, 610, 170, "Trap: sum by (model)", 30, False),
    ("Row 1 card line 2", 915, 185, 610, 170, "drops le", 30, False),
    ("Row 1 note", 915, 185, 610, 170, "Breaks histogram_quantile", 26, False),
    ("Row 2 card", 915, 375, 610, 170, "Right: sum by (le, model)", 30, False),
    ("Row 2 note line 1", 915, 375, 610, 170, "Keep le in the by clause,", 24, False),
    ("Row 2 note line 2", 915, 375, 610, 170, "then take the quantile once", 24, False),
    ("Pod A", 90, 650, 260, 105, "Pod A buckets", 26, False),
    ("Pod B", 90, 785, 260, 105, "Pod B buckets", 26, False),
    ("Stage rate", 430, 650, 300, 240, "rate", 30, False),
    ("Stage rate line 2", 430, 650, 300, 240, "per series", 30, False),
    ("Stage sum", 810, 650, 310, 240, "sum by", 28, True),
    ("Stage sum line 2", 810, 650, 310, 240, "(le, model)", 28, True),
    ("Stage quantile", 1200, 650, 310, 240, "histogram_quantile", 25, True),
    ("Stage quantile line 2", 1200, 650, 310, 240, "(0.99)", 25, True),
    ("Caption", 50, 980, 1500, 56, "le stands for less than or equal to.", 28, False),
]

for desc, bx, by, bw, bh, text, fs, is_mono in checks:
    factor = 0.62 if is_mono else 0.60
    est_w = len(text) * factor * fs
    print(f"{desc:25s}: text='{text}', est_w={est_w:5.1f}px, box_w={bw}px, margin={(bw - est_w)/2:5.1f}px")
    assert est_w + 32 <= bw, f"Text '{text}' doesn't fit in box width {bw} with >= 16px padding on both sides!"

print("\nALL TEXT FIT CHECKS PASSED CONSERVATIVELY!")
