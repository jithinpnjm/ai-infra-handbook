# Let's test the geometry with gap = 270
col1_left = 50
col1_right = 680
col1_w = 630
col1_cx = (col1_left + col1_right) / 2 # 365

col2_left = 950
col2_right = 1550
col2_w = 600

gap_x1 = col1_right # 680
gap_x2 = col2_left  # 950
gap_w = gap_x2 - gap_x1 # 270
gap_cx = (gap_x1 + gap_x2) / 2 # 815

print(f"Col 1: {col1_left} to {col1_right} (w={col1_w}), center={col1_cx}")
print(f"Col 2: {col2_left} to {col2_right} (w={col2_w})")
print(f"Gap: {gap_x1} to {gap_x2} (w={gap_w}), center={gap_cx}")

# Let's check horizontal labels:
labels_h = [
    ("data descriptor", 24),
    ("yes", 24),
    ("yes", 24),
    ("yes", 24)
]
for lbl, sz in labels_h:
    w = len(lbl) * 0.6 * sz
    pad = (gap_w - w) / 2
    print(f"Label '{lbl}': w={w:.1f}px, padding on each side={pad:.1f}px")
    assert pad >= 16, f"Padding too small for {lbl}"

print("All horizontal labels fit with >= 16px padding!")
