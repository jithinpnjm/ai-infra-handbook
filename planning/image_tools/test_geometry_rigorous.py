import xml.etree.ElementTree as ET

tree = ET.parse("output.svg")
root = tree.getroot()

rects = []
for g in root.iter('{http://www.w3.org/2000/svg}rect'):
    x = g.get('x')
    y = g.get('y')
    w = g.get('width')
    h = g.get('height')
    if x is not None and y is not None:
        rects.append((float(x), float(y), float(w), float(h)))

print(f"Total rects found (excluding background): {len(rects)-1}")

# Background is at index 0 (x=None or x=0, y=0, w=1600, h=1200)
# Let's inspect all boxes:
boxes = [r for r in rects if r[2] < 1600]

min_x = min(b[0] for b in boxes)
max_x = max(b[0] + b[2] for b in boxes)
min_y = min(b[1] for b in boxes)
max_y = max(b[1] + b[3] for b in boxes)

print(f"Boxes X bounds: {min_x} to {max_x} -> Margins: left={min_x}, right={1600 - max_x}")
print(f"Boxes Y bounds: {min_y} to {max_y} -> Margins: top={min_y}, bottom={1200 - max_y}")

if min_x >= 40 and (1600 - max_x) >= 40 and (1200 - max_y) >= 40:
    print("OUTSIDE MARGIN CHECK: PASSED (all >= 40px)")
else:
    print("OUTSIDE MARGIN CHECK: FAILED!")

# Check vertical gaps between rows:
# Left column boxes:
left_boxes = sorted([b for b in boxes if b[0] == 40 and b[2] == 715], key=lambda b: b[1])
for i in range(len(left_boxes)-1):
    gap = left_boxes[i+1][1] - (left_boxes[i][1] + left_boxes[i][3])
    print(f"Left col gap between Row {i+1} and {i+2}: {gap}px")
    assert gap >= 40

# Gap to Guard strip:
guard_rect = [b for b in boxes if b[1] == 940][0]
gap_r5_guard = guard_rect[1] - (left_boxes[-1][1] + left_boxes[-1][3])
print(f"Gap between Row 5 and Guard strip: {gap_r5_guard}px")
assert gap_r5_guard >= 40

# Gap to Bottom bar:
bottom_rect = [b for b in boxes if b[1] == 1105][0]
gap_guard_bottom = bottom_rect[1] - (guard_rect[1] + guard_rect[3])
print(f"Gap between Guard strip and Bottom bar: {gap_guard_bottom}px")
assert gap_guard_bottom >= 40

# Gap between Left and Right columns:
right_boxes = sorted([b for b in boxes if b[0] == 845 and b[2] == 715], key=lambda b: b[1])
col_gap = right_boxes[0][0] - (left_boxes[0][0] + left_boxes[0][2])
print(f"Horizontal gap between columns: {col_gap}px")
assert col_gap >= 40

print("ALL GAPS >= 40PX: VERIFIED!")
