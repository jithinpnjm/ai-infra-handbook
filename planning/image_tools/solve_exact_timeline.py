import re

centers = {
    "U": 148.0,
    "A": 311.0,
    "S": 474.0,
    "K": 637.0,
    "R": 800.0,
    "C": 963.0,
    "V": 1126.0,
    "D": 1289.0,
    "X": 1452.0
}

# Source of each step circle
step_src = {
    1: "U", 2: "A", 3: "S", 4: "A", 5: "K", 6: "K", 7: "K", 8: "K",
    9: "R", 10: "K", 11: "K", 12: "R", 13: "K", 14: "U", 15: "A",
    16: "K", 17: "K", 18: "K", 19: "K"
}

# Cards widths and heights
cards_info = {
    1: {"w": 741.0, "h": 28.0, "x": 182.0, "pos": "above"},
    2: {"w": 424.0, "h": 28.0, "x": 345.0, "pos": "above"},
    3: {"w": 256.0, "h": 50.0, "x": 184.0, "pos": "below"}, # below arrow 3!
    4: {"w": 424.0, "h": 28.0, "x": 345.0, "pos": "above"},
    5: {"w": 486.0, "h": 50.0, "x": 705.0, "pos": "self"}, # to right of loop
    6: {"w": 669.0, "h": 28.0, "x": 671.0, "pos": "above"},
    7: {"w": 640.0, "h": 28.0, "x": 671.0, "pos": "above"},
    8: {"w": 223.0, "h": 28.0, "x": 671.0, "pos": "above"},
    9: {"w": 367.0, "h": 28.0, "x": 834.0, "pos": "above"},
    10: {"w": 396.0, "h": 28.0, "x": 671.0, "pos": "above"},
    11: {"w": 842.0, "h": 28.0, "x": 671.0, "pos": "above"},
    12: {"w": 612.0, "h": 28.0, "x": 834.0, "pos": "above"},
    13: {"w": 556.0, "h": 50.0, "x": 47.0, "pos": "above"}, # leftward arrow from K to A
    14: {"w": 180.0, "h": 28.0, "x": 182.0, "pos": "above"},
    15: {"w": 453.0, "h": 28.0, "x": 345.0, "pos": "above"},
    16: {"w": 482.0, "h": 28.0, "x": 671.0, "pos": "above"},
    17: {"w": 597.0, "h": 28.0, "x": 671.0, "pos": "above"},
    18: {"w": 252.0, "h": 28.0, "x": 671.0, "pos": "above"},
    19: {"w": 424.0, "h": 28.0, "x": 179.0, "pos": "above"}, # leftward arrow from K to A
}

note_info = {"w": 875.0, "h": 56.0, "x": 607.0}

def test_config(cy):
    # Check time order
    for i in range(1, 19):
        if cy[i+1] <= cy[i]:
            return False, f"Time order violated between {i} and {i+1}"
    
    # Check circles on same X distance >= 48
    for src in ["U", "A", "S", "K", "R"]:
        steps = [i for i in range(1, 20) if step_src[i] == src]
        for a in range(len(steps) - 1):
            s1 = steps[a]
            s2 = steps[a+1]
            if cy[s2] - cy[s1] < 48.0:
                return False, f"Circles {s1} and {s2} on {src} distance {cy[s2] - cy[s1]} < 48"
    
    # Card bounding boxes
    rects = {}
    for i in range(1, 20):
        info = cards_info[i]
        w, h, x, pos = info["w"], info["h"], info["x"], info["pos"]
        if pos == "above":
            y = cy[i] - h - 4.0
        elif pos == "below":
            y = cy[i] + 4.0
        elif pos == "self":
            y = cy[i] - 25.0
        rects[i] = (x, y, w, h)
    
    # Note rect
    # Note is between step 13 and 14
    # Must be below circle 13
    y_note = cy[13] + 28.0 # circle 13 bottom is cy[13]+24
    h_note = note_info["h"]
    w_note = note_info["w"]
    x_note = note_info["x"]
    rects["note"] = (x_note, y_note, w_note, h_note)
    
    # Circle 14 top must be below note
    if cy[14] - 24.0 < y_note + h_note + 4.0:
        return False, f"Circle 14 too close to note"
        
    # Check circle vs card collision
    for i in range(1, 20):
        c_cx = centers[step_src[i]]
        c_cy = cy[i]
        r = 24.0
        for rk, (rx, ry, rw, rh) in rects.items():
            # overlap check
            h_overlap = not (c_cx + r <= rx or c_cx - r >= rx + rw)
            v_overlap = not (c_cy + r <= ry or c_cy - r >= ry + rh)
            if h_overlap and v_overlap:
                return False, f"Circle {i} (cx={c_cx}, cy={c_cy}) collides with Rect {rk} (x={rx}, y={ry}, w={rw}, h={rh})"
                
    # Check rect vs rect collision
    for k1 in rects:
        x1, y1, w1, h1 = rects[k1]
        for k2 in rects:
            if k1 >= k2: continue
            x2, y2, w2, h2 = rects[k2]
            h_overlap = not (x1 + w1 <= x2 or x1 >= x2 + w2)
            v_overlap = not (y1 + h1 <= y2 or y1 >= y2 + h2)
            if h_overlap and v_overlap:
                return False, f"Rect {k1} collides with Rect {k2}"
                
    # Check bottom margin
    if cy[19] + 24.0 > 1160.0:
        return False, f"Bottom edge {cy[19] + 24.0} > 1160.0"
        
    return True, "ALL OK"

print("Validator ready.")
# Let's write an integer linear programming or constraint search solver for cy[1..19]
import z3

s = z3.Solver()
cy = {i: z3.Real(f"cy_{i}") for i in range(1, 20)}

# Step 1 starts around 260
s.add(cy[1] >= 260.0)

# Time order: cy[i+1] >= cy[i] + min_step_diff
for i in range(1, 19):
    s.add(cy[i+1] >= cy[i] + 32.0)

# Circles on same participant distance >= 48
for src in ["U", "A", "S", "K", "R"]:
    steps = [i for i in range(1, 20) if step_src[i] == src]
    for a in range(len(steps) - 1):
        s1 = steps[a]
        s2 = steps[a+1]
        s.add(cy[s2] >= cy[s1] + 48.0)

# Non-overlap between circles and cards:
# For each circle i (at cx, cy) and card j (at rx, ry, rw, rh):
# If cx + 24 > rx and cx - 24 < rx + rw (they overlap horizontally):
# Then they must NOT overlap vertically:
# Either circle is above card (cy + 24 + 4 <= ry) OR circle is below card (cy - 24 - 4 >= ry + rh)
for i in range(1, 20):
    c_cx = centers[step_src[i]]
    for j in range(1, 20):
        info = cards_info[j]
        rx = info["x"]
        rw = info["w"]
        rh = info["h"]
        pos = info["pos"]
        # check horizontal overlap
        if not (c_cx + 24.0 <= rx or c_cx - 24.0 >= rx + rw):
            # Horizontally overlapping!
            # Card j's ry is a function of cy[j]:
            if pos == "above":
                # ry = cy[j] - rh - 4.0
                # If i < j (circle i is above step j): circle i must be above card j:
                # cy[i] + 24.0 + 4.0 <= cy[j] - rh - 4.0
                if i < j:
                    s.add(cy[i] + 32.0 + rh <= cy[j])
                elif i > j:
                    # circle i is below step j: circle i must be below card j:
                    # cy[i] - 24.0 - 4.0 >= cy[j] - 4.0 (card bottom is cy[j] - 4.0)
                    s.add(cy[i] >= cy[j] + 24.0)
            elif pos == "below":
                # ry = cy[j] + 4.0, card bottom = cy[j] + 4.0 + rh
                if i < j:
                    # circle i above card j:
                    s.add(cy[i] + 28.0 <= cy[j] + 4.0)
                elif i > j:
                    # circle i below card j:
                    s.add(cy[i] - 28.0 >= cy[j] + 4.0 + rh)

# Note constraint:
# y_note = cy[13] + 28.0, h_note = 56.0
# Note extends horizontally from x=607 to 607+875 = 1482.
# Any circle with x in [607..1482]:
# Circle 13 is at K(637). cy[13] + 24 < y_note is satisfied since y_note = cy[13]+28.
# Circle 14 is at U(148) -> x=148 is outside [607..1482]!
# But visually time order: cy[14] should be below note:
s.add(cy[14] >= cy[13] + 28.0 + 56.0 + 32.0)

# Card 19 bottom / Circle 19 bottom <= 1160
s.add(cy[19] <= 1136.0)

if s.check() == z3.sat:
    m = s.model()
    sol = {i: float(m[cy[i]].as_decimal(2).replace('?', '')) for i in range(1, 20)}
    print("SAT! Found solution:")
    for i in range(1, 20):
        print(f"cy[{i:2d}] = {sol[i]}")
    ok, msg = test_config(sol)
    print(f"Validation result: {ok}, {msg}")
else:
    print("UNSAT!")
