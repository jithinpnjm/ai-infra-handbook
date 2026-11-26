# Check all segment-to-box intersections
# Rectangles:
# IDLE: (200, 200, 320, 90)
# ALLOCATED: (1080, 200, 320, 90)
# DRAINED: (200, 570, 320, 90)
# DRAINING: (1080, 570, 320, 90)
# DOWN: (640, 920, 320, 90)
# Label boxes:
# rect 2: (700, 142, 200, 62)
# rect 3: (710, 286, 180, 62)
# rect 5: (465, 370, 270, 62)
# rect 6: (560, 465, 480, 62)
# rect 7: (630, 558, 340, 62)
# rect 8: (975, 888, 560, 62)
# rect 9: (160, 825, 440, 96)
# rect 10: (140, 954, 460, 96)

boxes = {
    'IDLE': (200, 200, 320, 90),
    'ALLOCATED': (1080, 200, 320, 90),
    'DRAINED': (200, 570, 320, 90),
    'DRAINING': (1080, 570, 320, 90),
    'DOWN': (640, 920, 320, 90),
    'lbl_job_starts': (700, 142, 200, 62),
    'lbl_job_ends': (710, 286, 180, 62),
    'lbl_resume': (465, 370, 270, 62),
    'lbl_drain': (560, 465, 480, 62),
    'lbl_finish': (630, 558, 340, 62),
    'lbl_failure': (975, 888, 560, 62),
    'lbl_slurmd': (160, 825, 440, 96),
    'lbl_valid': (140, 954, 460, 96)
}

from test_intersections import arrows

# A segment from (x1, y1) to (x2, y2)
# A box is [rx, rx+rw] x [ry, ry+rh]
# Check if segment penetrates inside box interior: (rx < x < rx+rw) and (ry < y < ry+rh)
def seg_box_interior(p1, p2, box):
    rx, ry, rw, rh = box
    x1, y1 = p1
    x2, y2 = p2
    
    # Sample points along segment
    steps = 100
    for i in range(1, steps):
        t = i / steps
        x = x1 + t * (x2 - x1)
        y = y1 + t * (y2 - y1)
        if (rx + 0.5 < x < rx + rw - 0.5) and (ry + 0.5 < y < ry + rh - 0.5):
            return True
    return False

violations = []
for arr_id, segs in arrows.items():
    for p1, p2 in segs:
        for b_name, b_rect in boxes.items():
            if seg_box_interior(p1, p2, b_rect):
                violations.append((arr_id, p1, p2, b_name))

print(f"Total segment-box interior penetrations: {len(violations)}")
for v in violations:
    print("Violation:", v)
assert len(violations) == 0
print("ZERO SEGMENT-BOX PENETRATIONS CONFIRMED!")
