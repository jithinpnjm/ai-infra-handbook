import math

def dist_to_diamond(px, py, cx, cy, rx, ry):
    dx = abs(px - cx)
    dy = abs(py - cy)
    scale = math.sqrt((1.0/rx)**2 + (1.0/ry)**2)
    val = dx/rx + dy/ry
    return (1.0 - val) / scale

# Left diamond: cx=405, cy=305, rx=250, ry=80
# group centered at 405: icon at 292.5..328.5, y=287..323
# text at 342.5..517.5, y=286..321
pts_left = [
    ("text top-left", 342.5, 286.0), ("text top-right", 517.5, 286.0),
    ("text bot-left", 342.5, 321.0), ("text bot-right", 517.5, 321.0),
    ("icon top-left", 292.5, 287.0), ("icon top-right", 328.5, 287.0),
    ("icon bot-left", 292.5, 323.0), ("icon bot-right", 328.5, 323.0)
]
print("--- Centered Left Diamond (rx=250, ry=80) ---")
for name, px, py in pts_left:
    d = dist_to_diamond(px, py, 405, 305, 250, 80)
    print(f"Left {name:15s} ({px:6.1f}, {py:6.1f}): dist = {d:5.2f}px ({'PASS' if d>=16 else 'FAIL'})")

