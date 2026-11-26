import re
import xml.etree.ElementTree as ET

tree = ET.parse("test_timeline.svg")
root = tree.getroot()

# Check bounds of all rects and circles
rects = []
for r in root.iter('{http://www.w3.org/2000/svg}rect'):
    x = float(r.attrib.get('x', 0))
    y = float(r.attrib.get('y', 0))
    w = float(r.attrib.get('width', 0))
    h = float(r.attrib.get('height', 0))
    if w == 1600 and h == 1200: continue # background
    rects.append((x, y, w, h))
    assert x >= 40.0, f"Rect left edge {x} < 40!"
    assert x + w <= 1560.0, f"Rect right edge {x+w} > 1560!"
    assert y >= 40.0, f"Rect top edge {y} < 40!"
    assert y + h <= 1160.0, f"Rect bottom edge {y+h} > 1160!"

circles = []
for c in root.iter('{http://www.w3.org/2000/svg}circle'):
    cx = float(c.attrib.get('cx', 0))
    cy = float(c.attrib.get('cy', 0))
    r = float(c.attrib.get('r', 0))
    if r == 24.0: # step circle
        circles.append((cx, cy, r))
        assert cx - r >= 40.0, f"Circle left edge {cx-r} < 40!"
        assert cx + r <= 1560.0, f"Circle right edge {cx+r} > 1560!"
        assert cy - r >= 40.0, f"Circle top edge {cy-r} < 40!"
        assert cy + r <= 1160.0, f"Circle bottom edge {cy+r} > 1160!"

print(f"Total rects checked: {len(rects)} (all within [40, 40, 1560, 1160])")
print(f"Total step circles checked: {len(circles)} (all within [40, 40, 1560, 1160])")

# Check circle vs card collision
# For each step group:
for g in root.iter('{http://www.w3.org/2000/svg}g'):
    gid = g.attrib.get('id', '')
    if gid.startswith('step-'):
        c = g.find('{http://www.w3.org/2000/svg}circle')
        r = g.find('{http://www.w3.org/2000/svg}rect')
        if c is not None and r is not None:
            cx = float(c.attrib['cx'])
            cy = float(c.attrib['cy'])
            rx = float(r.attrib['x'])
            ry = float(r.attrib['y'])
            rw = float(r.attrib['width'])
            rh = float(r.attrib['height'])
            
            # Check overlap between circle (cx, cy, r=24) and rect [rx, ry, rw, rh]
            # Horizontal overlap:
            h_overlap = not (cx + 24 <= rx or cx - 24 >= rx + rw)
            # Vertical overlap:
            v_overlap = not (cy + 24 <= ry or cy - 24 >= ry + rh)
            
            if h_overlap and v_overlap:
                print(f"ERROR: {gid} circle collides with card! circle=({cx},{cy}) card=[{rx},{ry},{rw},{rh}]")
                assert False, f"{gid} circle collides with card!"

print("PASS: No step circle collides with its own card!")

# Check consecutive circles on the same X:
by_x = {}
for cx, cy, r in circles:
    by_x.setdefault(cx, []).append(cy)

for cx, cys in by_x.items():
    cys.sort()
    for i in range(len(cys) - 1):
        dist = cys[i+1] - cys[i]
        assert dist >= 48.0, f"Circles at cx={cx} have distance {dist} < 48!"

print("PASS: All circles sharing the same X have center distance >= 48px (ZERO circle overlap)!")
print("ALL COMPREHENSIVE CHECKS PASSED!")
