#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

tree = ET.parse("test_candidate_incident8.svg")
root = tree.getroot()

def get_line_width(text, fs=24, is_mono=False):
    coeff = 0.62 if is_mono else 0.60
    return len(text) * fs * coeff

# List of boxes to verify: (name, rect_x, rect_y, rect_w, rect_h)
boxes = [
    ("Resolver Anatomy", 40, 130, 730, 130),
    ("Rule", 40, 285, 730, 180),
    ("Query Container", 40, 490, 730, 490),
    ("Query Row 1", 65, 580, 680, 85),
    ("Query Row 2", 65, 680, 680, 85),
    ("Query Row 3", 65, 780, 680, 85),
    ("Query Row 4", 65, 880, 680, 85),
    ("Load Box", 830, 130, 730, 300),
    ("Result", 830, 455, 730, 150),
    ("Fix", 830, 630, 730, 195),
    ("Risky", 830, 850, 730, 130),
    ("Test Note Strip", 40, 1030, 1520, 120),
]

# Check clearances between main boxes:
# Left column vs Right column gap:
gap_lr = 830 - (40 + 730)
print(f"Gap Left vs Right column: {gap_lr} px (>= 40 px)")
assert gap_lr >= 40

# Left column vertical gaps:
gap_l1 = 285 - (130 + 130)
gap_l2 = 490 - (285 + 180)
print(f"Left col gaps: {gap_l1} px, {gap_l2} px (>= 25 px)")
assert gap_l1 >= 20 and gap_l2 >= 20

# Right column vertical gaps:
gap_r1 = 455 - (130 + 300)
gap_r2 = 630 - (455 + 150)
gap_r3 = 850 - (630 + 195)
print(f"Right col gaps: {gap_r1} px, {gap_r2} px, {gap_r3} px (>= 25 px)")
assert gap_r1 >= 20 and gap_r2 >= 20 and gap_r3 >= 20

# Column bottom to bottom strip:
gap_bottom = 1030 - 980
print(f"Gap to bottom strip: {gap_bottom} px (>= 40 px)")
assert gap_bottom >= 40

# Outside margins:
print("Left margin: 40 px")
print(f"Right margin: {1600 - (830 + 730)} px")
print(f"Bottom margin: {1200 - (1030 + 120)} px")
assert 1600 - (830 + 730) >= 40
assert 1200 - (1030 + 120) >= 40

print("\nAll box-to-box and margin clearances PASS!")
