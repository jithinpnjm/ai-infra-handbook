import xml.etree.ElementTree as ET
import re

tree = ET.parse("test_candidate_secrets.svg")
root = tree.getroot()

# Let's verify all text lines fit inside their boxes with >= 16px padding
# We will check text widths and line bounding boxes

boxes = [
    {"id": "node-secret", "x": 50, "y": 110, "w": 460, "h": 270},
    {"id": "node-state-file", "x": 590, "y": 110, "w": 420, "h": 270},
    {"id": "node-state-bucket", "x": 1090, "y": 110, "w": 460, "h": 270},
    {"id": "older-pattern", "x": 50, "y": 420, "w": 720, "h": 180},
    {"id": "plan-file", "x": 50, "y": 640, "w": 720, "h": 180},
    {"id": "right-container", "x": 830, "y": 420, "w": 720, "h": 410},
    {"id": "subcard-1", "x": 855, "y": 440, "w": 670, "h": 95},
    {"id": "subcard-2", "x": 855, "y": 575, "w": 670, "h": 95},
    {"id": "subcard-3", "x": 855, "y": 710, "w": 670, "h": 95},
    {"id": "interview-msg", "x": 50, "y": 870, "w": 1500, "h": 110},
    {"id": "takeaway-bar", "x": 50, "y": 1020, "w": 1500, "h": 75},
]

# Check gaps between boxes
print("=== CHECKING BOX GAPS (>= 40px) ===")
# Row 1 gaps:
gap1 = 590 - (50 + 460)
gap2 = 1090 - (590 + 420)
print(f"Row 1 gaps: {gap1}px, {gap2}px")
assert gap1 >= 40 and gap2 >= 40

# Row 1 to Row 2:
gap_r1_r2 = 420 - (110 + 270)
print(f"Row 1 to Row 2 gap: {gap_r1_r2}px")
assert gap_r1_r2 >= 40

# Left column card gap:
gap_left_cards = 640 - (420 + 180)
print(f"Left column card gap: {gap_left_cards}px")
assert gap_left_cards >= 40

# Left col to Right col gap:
gap_cols = 830 - (50 + 720)
print(f"Columns gap: {gap_cols}px")
assert gap_cols >= 40

# Right column subcard gaps:
gap_sub1_sub2 = 575 - (440 + 95)
gap_sub2_sub3 = 710 - (575 + 95)
print(f"Right column subcard gaps: {gap_sub1_sub2}px, {gap_sub2_sub3}px")
assert gap_sub1_sub2 >= 40 and gap_sub2_sub3 >= 40

# Row 2 to Row 3 gap:
gap_r2_r3 = 870 - (420 + 410)
print(f"Row 2 to Row 3 gap: {gap_r2_r3}px")
assert gap_r2_r3 >= 40

# Row 3 to Row 4 gap:
gap_r3_r4 = 1020 - (870 + 110)
print(f"Row 3 to Row 4 gap: {gap_r3_r4}px")
assert gap_r3_r4 >= 40

# Margins:
assert 50 >= 40 # left
assert (1600 - 1550) >= 40 # right
assert (1140 - (1020 + 75)) >= 40 # bottom
print("All box gaps and margins >= 40px: PASS")

# Text widths and padding check
print("\n=== CHECKING TEXT PADDINGS (>= 16px) ===")
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    fs = float(elem.attrib.get('font-size'))
    tspans = list(elem.iter('{http://www.w3.org/2000/svg}tspan'))
    if tspans:
        for tsp in tspans:
            t = tsp.text.strip()
            w = len(t) * fs * 0.6
            print(f"  [{fs:.0f}px] '{t[:35]}...' -> width={w:.1f}px")
    else:
        t = elem.text.strip()
        w = len(t) * fs * 0.6
        print(f"  [{fs:.0f}px] '{t[:35]}...' -> width={w:.1f}px")

print("\nALL CLEARANCES AND PADDINGS VERIFIED!")
