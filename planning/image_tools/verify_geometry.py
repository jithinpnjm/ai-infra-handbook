import xml.etree.ElementTree as ET
import re

tree = ET.parse("test_candidate.svg")
root = tree.getroot()

vb = [float(x) for x in root.attrib['viewBox'].split()]
W, H = vb[2], vb[3]

# Top-level rects only (not inside <g> icons)
rects = []
for child in root:
    tag = child.tag.split('}')[-1]
    if tag == 'rect':
        w = float(child.attrib['width'])
        h = float(child.attrib['height'])
        if w == W and h == H:
            continue
        x = float(child.attrib['x'])
        y = float(child.attrib['y'])
        rects.append({'x': x, 'y': y, 'w': w, 'h': h})

print(f"Checking {len(rects)} top-level panel rects:")
for i, r in enumerate(rects, 1):
    left_m = r['x']
    right_m = W - (r['x'] + r['w'])
    top_m = r['y']
    bottom_m = H - (r['y'] + r['h'])
    print(f"  Box {i}: x={r['x']}, y={r['y']}, w={r['w']}, h={r['h']} -> margins: L={left_m}, R={right_m}, T={top_m}, B={bottom_m}")
    assert left_m >= 40, f"Box {i} left margin < 40"
    assert right_m >= 40, f"Box {i} right margin < 40"
    assert top_m >= 40, f"Box {i} top margin < 40"
    assert bottom_m >= 40, f"Box {i} bottom margin < 40"

print("\nChecking gaps between non-overlapping boxes:")
for i in range(len(rects)):
    for j in range(i + 1, len(rects)):
        r1, r2 = rects[i], rects[j]
        # Check horizontal gap if they overlap vertically
        v_overlap = max(0, min(r1['y'] + r1['h'], r2['y'] + r2['h']) - max(r1['y'], r2['y']))
        if v_overlap > 0:
            h_gap = max(r1['x'], r2['x']) - min(r1['x'] + r1['w'], r2['x'] + r2['w'])
            print(f"  Boxes {i+1} & {j+1} v_overlap={v_overlap:.1f}px -> h_gap={h_gap:.1f}px")
            assert h_gap >= 40, f"h_gap {h_gap} < 40 between boxes {i+1} and {j+1}"
            
        # Check vertical gap if they overlap horizontally
        h_overlap = max(0, min(r1['x'] + r1['w'], r2['x'] + r2['w']) - max(r1['x'], r2['x']))
        if h_overlap > 0:
            v_gap = max(r1['y'], r2['y']) - min(r1['y'] + r1['h'], r2['y'] + r2['h'])
            print(f"  Boxes {i+1} & {j+1} h_overlap={h_overlap:.1f}px -> v_gap={v_gap:.1f}px")
            assert v_gap >= 40, f"v_gap {v_gap} < 40 between boxes {i+1} and {j+1}"

print("\nAll panels satisfy >= 40px margins and >= 40px gaps!")
