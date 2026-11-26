# Check if any arrow segment intersects any node box (other than at endpoints)
def segment_intersects_rect(p1, p2, rect):
    # rect = (x, y, w, h)
    rx, ry, rw, rh = rect
    # Check if a point strictly inside the rect is on the segment
    # Or if segment intersects any of the rect's boundaries and enters it
    x1, y1 = p1
    x2, y2 = p2
    
    # Check intermediate points along segment
    steps = 100
    for s in range(1, steps):
        t = s / steps
        px = x1 + t * (x2 - x1)
        py = y1 + t * (y2 - y1)
        if rx < px < rx + rw and ry < py < ry + rh:
            return True
    return False

# Node boxes:
nodes = {
    "LEASE": (40, 110, 350, 150),
    # Note: Sources is a container, API is inside it. LEASE->API enters Sources, which is intended.
    "API": (440, 140, 360, 115),
    "FILE": (825, 140, 330, 115),
    "HTTP": (1180, 140, 360, 115),
    "CAD": (40, 300, 440, 120),
    "PM": (580, 305, 440, 110),
    "IMG": (1120, 305, 440, 110),
    "EV": (40, 460, 440, 115),
    "PW": (560, 455, 480, 130),
    "CRI": (1120, 460, 440, 115),
    "VM": (40, 620, 440, 120),
    "PLEG": (1120, 620, 440, 115),
    "DM": (60, 780, 440, 125),
    "PR": (580, 780, 440, 125),
    "SM": (1100, 780, 440, 125),
    "KAPI": (250, 960, 1100, 150)
}

from test_all_intersections import arrows

has_collision = False
for aname, pts in arrows.items():
    for i in range(len(pts)-1):
        p1, p2 = pts[i], pts[i+1]
        for nname, rect in nodes.items():
            if segment_intersects_rect(p1, p2, rect):
                print(f"COLLISION: Arrow {aname} segment {p1}->{p2} passes through node {nname} {rect}!")
                has_collision = True

if not has_collision:
    print("SUCCESS: NO ARROW PASSES THROUGH ANY NODE!")
