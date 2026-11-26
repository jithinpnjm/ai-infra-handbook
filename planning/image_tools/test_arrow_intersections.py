import re

# Parse all paths with marker-end
with open("node_lifecycle.svg") as f:
    content = f.read()

paths = re.findall(r'<path d="([^"]+)"[^>]*marker-end="url\(#arrow-green\)"', content)
print(f"Found {len(paths)} arrow paths.")

segments = []
for p_idx, p in enumerate(paths):
    # parse coordinates
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

print(f"Total arrow segments: {len(segments)}")

def ccw(A,B,C):
    return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])

def intersect(A,B,C,D):
    # endpoints touch is allowed if connected
    if A == C or A == D or B == C or B == D:
        return False
    return ccw(A,C,D) != ccw(B,C,D) and ccw(A,B,C) != ccw(A,B,D)

# Check all segment pairs from different paths
crossings = []
for i in range(len(segments)):
    for j in range(i+1, len(segments)):
        s1 = segments[i]
        s2 = segments[j]
        if s1[2] == s2[2]:
            continue # same path
        if intersect(s1[0], s1[1], s2[0], s2[1]):
            crossings.append((s1, s2))

print(f"Total arrow crossings: {len(crossings)}")
for c in crossings:
    print("Crossing between:", c)

assert len(crossings) == 0, "Found arrow crossings!"
print("Zero arrow crossings verified successfully!")
