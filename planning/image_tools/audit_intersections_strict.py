import xml.etree.ElementTree as ET
import re

tree = ET.parse("candidate_node_lifecycle.svg")
root = tree.getroot()

# Extract all arrows/paths
paths = []
for p in root.iter('{http://www.w3.org/2000/svg}path'):
    d = p.get('d')
    if d and 'marker-end' in p.attrib:
        paths.append(d)

print(f"Total marker arrows: {len(paths)}")
for i, p in enumerate(paths, 1):
    print(f"Arrow {i:2d}: {p}")

# Parse line segments of each arrow
def parse_path_segments(d):
    tokens = d.strip().split()
    segments = []
    i = 0
    cur_x, cur_y = 0, 0
    while i < len(tokens):
        cmd = tokens[i]
        if cmd == 'M':
            cur_x = float(tokens[i+1])
            cur_y = float(tokens[i+2])
            i += 3
        elif cmd == 'L':
            nx = float(tokens[i+1])
            ny = float(tokens[i+2])
            segments.append(((cur_x, cur_y), (nx, ny)))
            cur_x, cur_y = nx, ny
            i += 3
        elif cmd == 'H':
            nx = float(tokens[i+1])
            segments.append(((cur_x, cur_y), (nx, cur_y)))
            cur_x = nx
            i += 2
        elif cmd == 'V':
            ny = float(tokens[i+1])
            segments.append(((cur_x, cur_y), (cur_x, ny)))
            cur_y = ny
            i += 2
        else:
            i += 1
    return segments

all_segments = []
for idx, p in enumerate(paths):
    segs = parse_path_segments(p)
    all_segments.append((idx, segs))

def ccw(A, B, C):
    return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

def segments_cross(A, B, C, D):
    # Strict crossing (not touching at endpoints)
    if A == C or A == D or B == C or B == D:
        return False
    # If both horizontal or both vertical and overlapping:
    if A[1] == B[1] == C[1] == D[1]:
        # horizontal overlap?
        x1, x2 = min(A[0], B[0]), max(A[0], B[0])
        x3, x4 = min(C[0], D[0]), max(C[0], D[0])
        return max(x1, x3) < min(x2, x4)
    if A[0] == B[0] == C[0] == D[0]:
        y1, y2 = min(A[1], B[1]), max(A[1], B[1])
        y3, y4 = min(C[1], D[1]), max(C[1], D[1])
        return max(y1, y3) < min(y2, y4)
    return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)

# Check all segment pairs between different arrows
crossings = []
for i in range(len(all_segments)):
    for j in range(i + 1, len(all_segments)):
        idx1, segs1 = all_segments[i]
        idx2, segs2 = all_segments[j]
        for s1 in segs1:
            for s2 in segs2:
                if segments_cross(s1[0], s1[1], s2[0], s2[1]):
                    crossings.append((idx1+1, idx2+1, s1, s2))

print(f"\nArrow crossings found: {len(crossings)}")
for c in crossings:
    print(f"  Crossing between Arrow {c[0]} and Arrow {c[1]}: {c[2]} x {c[3]}")

assert len(crossings) == 0, f"Found {len(crossings)} arrow crossings!"
print("ZERO ARROW CROSSINGS CONFIRMED!")

# Now check if any arrow segment penetrates any node box or text badge
rects = []
for r in root.iter('{http://www.w3.org/2000/svg}rect'):
    rx = float(r.get('x'))
    ry = float(r.get('y'))
    rw = float(r.get('width'))
    rh = float(r.get('height'))
    if rw == 1600: continue
    rects.append((rx, ry, rw, rh))

penetrations = []
for idx, segs in all_segments:
    for s in segs:
        (x1, y1), (x2, y2) = s
        for rx, ry, rw, rh in rects:
            # Check if segment goes through the interior of the rect
            # Interior is (rx+1, ry+1, rw-2, rh-2)
            ix1, ix2 = rx + 1, rx + rw - 1
            iy1, iy2 = ry + 1, ry + rh - 1
            # If segment is horizontal
            if y1 == y2:
                if iy1 < y1 < iy2:
                    min_x, max_x = min(x1, x2), max(x1, x2)
                    if max_x > ix1 and min_x < ix2:
                        penetrations.append((idx+1, s, (rx, ry, rw, rh)))
            # If segment is vertical
            elif x1 == x2:
                if ix1 < x1 < ix2:
                    min_y, max_y = min(y1, y2), max(y1, y2)
                    if max_y > iy1 and min_y < iy2:
                        penetrations.append((idx+1, s, (rx, ry, rw, rh)))

print(f"\nBox penetrations found: {len(penetrations)}")
for p in penetrations:
    print(f"  Penetration by Arrow {p[0]}: {p[1]} through rect {p[2]}")

assert len(penetrations) == 0, f"Found {len(penetrations)} box penetrations!"
print("ZERO BOX PENETRATIONS CONFIRMED!")
