import math

def point_to_diamond_dist(px, py, cx, cy, rx, ry):
    # px, py relative to cx, cy
    dx = abs(px - cx)
    dy = abs(py - cy)
    scale = math.sqrt((1.0/rx)**2 + (1.0/ry)**2)
    val = dx/rx + dy/ry
    return (1.0 - val) / scale

# Left diamond: cx=410, cy=305, rx=190, ry=65
# Text: "a succeeds?", fs=30. text-anchor="middle" at x=425, y=314
# BBox approx: x in [326, 524], y in [285, 315] (height 30)
# Icon at translate(265, 287), size 36x36 -> x in [265, 301], y in [287, 323]
corners = [
    # text
    (326, 285), (524, 285), (326, 315), (524, 315),
    # icon
    (265, 287), (301, 287), (265, 323), (301, 323)
]
for px, py in corners:
    d = point_to_diamond_dist(px, py, 410, 305, 190, 65)
    print(f"Point ({px}, {py}): dist = {d:.2f}px")

