# Check if any arrow segment penetrates the interior of any node box

boxes = {
    "Provisioned":    {"x1": 70,  "y1": 170, "x2": 370, "y2": 300},
    "Configured":     {"x1": 650, "y1": 170, "x2": 950, "y2": 300},
    "Validating":     {"x1": 1230,"y1": 170, "x2": 1530,"y2": 300},
    
    "Quarantined":    {"x1": 70,  "y1": 560, "x2": 370, "y2": 690},
    "Maintenance":    {"x1": 650, "y1": 560, "x2": 950, "y2": 690},
    "Ready":          {"x1": 1230,"y1": 560, "x2": 1530,"y2": 690},
    
    "Draining":       {"x1": 70,  "y1": 950, "x2": 370, "y2": 1080},
    "Cordoned":       {"x1": 650, "y1": 950, "x2": 950, "y2": 1080},
    "Decommissioned": {"x1": 1230,"y1": 950, "x2": 1530,"y2": 1080},
}

import re
with open("node_lifecycle.svg") as f:
    content = f.read()

paths = re.findall(r'<path d="([^"]+)"[^>]*marker-end="url\(#arrow-green\)"', content)

segments = []
for p_idx, p in enumerate(paths):
    pts = []
    tokens = p.split()
    i = 0
    while i < len(tokens):
        cmd = tokens[i]
        if cmd in ['M', 'L']:
            pts.append((float(tokens[i+1]), float(tokens[i+2])))
            i += 3
        else:
            i += 1
    for k in range(len(pts)-1):
        segments.append((pts[k], pts[k+1], p_idx))

# A segment penetrates a box interior if any point strictly inside the segment is strictly inside the box
# For horizontal or vertical segments, this is simple:
penetrations = []
for p1, p2, p_idx in segments:
    x1, y1 = p1
    x2, y2 = p2
    for b_name, b in boxes.items():
        # Check midpoint
        mx, my = (x1 + x2)/2, (y1 + y2)/2
        if b["x1"] < mx < b["x2"] and b["y1"] < my < b["y2"]:
            penetrations.append((b_name, (p1, p2)))

print(f"Total penetrations into node boxes: {len(penetrations)}")
assert len(penetrations) == 0, f"Penetrations found: {penetrations}"
print("Zero box penetrations verified!")
