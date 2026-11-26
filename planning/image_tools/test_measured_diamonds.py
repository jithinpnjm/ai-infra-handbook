import math

def dist_to_diamond(px, py, cx, cy, rx, ry):
    dx = abs(px - cx)
    dy = abs(py - cy)
    scale = math.sqrt((1.0/rx)**2 + (1.0/ry)**2)
    val = dx/rx + dy/ry
    return (1.0 - val) / scale

print("--- LEFT DIAMOND ---")
# cx=405, cy=305, rx=220, ry=65
# text: x in [342.6, 517.4], y in [286.0, 321.0]
# icon: x in [250, 286], y in [287, 323]
pts_left = [
    ("text top-left", 342.6, 286.0), ("text top-right", 517.4, 286.0),
    ("text bot-left", 342.6, 321.0), ("text bot-right", 517.4, 321.0),
    ("icon top-left", 250, 287), ("icon top-right", 286, 287),
    ("icon bot-left", 250, 323), ("icon bot-right", 286, 323)
]
for name, px, py in pts_left:
    d = dist_to_diamond(px, py, 405, 305, 220, 65)
    print(f"Left {name:15s} ({px:6.1f}, {py:6.1f}): dist = {d:5.2f}px ({'PASS' if d>=16 else 'FAIL'})")

print("\n--- RIGHT DIAMOND 1 (a succeeds?) ---")
# cx=1025, cy=285, rx=200, ry=50
# text: x in [952.6, 1127.4], y in [266.0, 301.0]
# icon: translate(885, 271), size 28x28 -> x in [885, 913], y in [271, 299]
pts_right_1 = [
    ("text top-left", 952.6, 266.0), ("text top-right", 1127.4, 266.0),
    ("text bot-left", 952.6, 301.0), ("text bot-right", 1127.4, 301.0),
    ("icon top-left", 885, 271), ("icon top-right", 913, 271),
    ("icon bot-left", 885, 299), ("icon bot-right", 913, 299)
]
for name, px, py in pts_right_1:
    d = dist_to_diamond(px, py, 1025, 285, 200, 50)
    print(f"Right1 {name:15s} ({px:6.1f}, {py:6.1f}): dist = {d:5.2f}px ({'PASS' if d>=16 else 'FAIL'})")

print("\n--- RIGHT DIAMOND 2 (b succeeded?) ---")
# cx=1025, cy=530, rx=200, ry=58
# text: x in [942.1, 1137.9], y in [511.0, 546.0]
# icon: translate(875, 516), size 28x28 -> x in [875, 903], y in [516, 544]
pts_right_2 = [
    ("text top-left", 942.1, 511.0), ("text top-right", 1137.9, 511.0),
    ("text bot-left", 942.1, 546.0), ("text bot-right", 1137.9, 546.0),
    ("icon top-left", 875, 516), ("icon top-right", 903, 516),
    ("icon bot-left", 875, 544), ("icon bot-right", 903, 544)
]
for name, px, py in pts_right_2:
    d = dist_to_diamond(px, py, 1025, 530, 200, 58)
    print(f"Right2 {name:15s} ({px:6.1f}, {py:6.1f}): dist = {d:5.2f}px ({'PASS' if d>=16 else 'FAIL'})")
