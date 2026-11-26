# Pure python DAG / Bellman-Ford longest path solver to find minimum valid cy values!
# We have lower bound cy[1] >= 260.
# And a set of difference constraints of the form: cy[j] - cy[i] >= diff  =>  cy[j] >= cy[i] + diff
# We can find the minimum valid cy for all nodes!

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

step_src = {
    1: "U", 2: "A", 3: "S", 4: "A", 5: "K", 6: "K", 7: "K", 8: "K",
    9: "R", 10: "K", 11: "K", 12: "R", 13: "K", 14: "U", 15: "A",
    16: "K", 17: "K", 18: "K", 19: "K"
}

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
    13: {"w": 556.0, "h": 50.0, "x": 47.0, "pos": "above"},
    14: {"w": 180.0, "h": 28.0, "x": 182.0, "pos": "above"},
    15: {"w": 453.0, "h": 28.0, "x": 345.0, "pos": "above"},
    16: {"w": 482.0, "h": 28.0, "x": 671.0, "pos": "above"},
    17: {"w": 597.0, "h": 28.0, "x": 671.0, "pos": "above"},
    18: {"w": 252.0, "h": 28.0, "x": 671.0, "pos": "above"},
    19: {"w": 424.0, "h": 28.0, "x": 179.0, "pos": "above"},
}

diffs = [] # (i, j, min_diff) => cy[j] >= cy[i] + min_diff

# 1. Time order
for i in range(1, 19):
    diffs.append((i, i+1, 32.0))

# 2. Same participant distance >= 48
for src in ["U", "A", "S", "K", "R"]:
    steps = [i for i in range(1, 20) if step_src[i] == src]
    for a in range(len(steps) - 1):
        diffs.append((steps[a], steps[a+1], 48.0))

# 3. Card-circle non-overlap constraints:
for i in range(1, 20):
    c_cx = centers[step_src[i]]
    for j in range(1, 20):
        if i == j: continue
        info = cards_info[j]
        rx = info["x"]
        rw = info["w"]
        rh = info["h"]
        pos = info["pos"]
        # check horizontal overlap
        if not (c_cx + 24.0 <= rx or c_cx - 24.0 >= rx + rw):
            # Horizontally overlapping!
            if pos == "above":
                if i < j:
                    diffs.append((i, j, 32.0 + rh))
                elif i > j:
                    diffs.append((j, i, 28.0))
            elif pos == "below":
                if i < j:
                    diffs.append((i, j, 28.0))
                elif i > j:
                    diffs.append((j, i, 32.0 + rh))

# Note between 13 and 14:
diffs.append((13, 14, 28.0 + 56.0 + 32.0))

# Run Bellman-Ford
cy = {i: 264.0 for i in range(1, 20)}
for _ in range(100):
    updated = False
    for i, j, d in diffs:
        if cy[j] < cy[i] + d:
            cy[j] = cy[i] + d
            updated = True
    if not updated:
        break

print(f"Minimum cy[19]: {cy[19]}")
print(f"Bottom circle edge: {cy[19] + 24.0} (limit is 1160.0)")
for i in range(1, 20):
    print(f"cy[{i:2d}] = {cy[i]:.1f}")

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
    y_note = cy[13] + 28.0
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
            h_overlap = not (c_cx + r <= rx or c_cx - r >= rx + rw)
            v_overlap = not (c_cy + r <= ry or c_cy - r >= ry + rh)
            if h_overlap and v_overlap:
                return False, f"Circle {i} (cx={c_cx}, cy={c_cy}) collides with Rect {rk} (x={rx}, y={ry}, w={rw}, h={rh})"
                
    # Check rect vs rect collision
    for k1 in rects:
        x1, y1, w1, h1 = rects[k1]
        for k2 in rects:
            if k1 == k2: continue
            x2, y2, w2, h2 = rects[k2]
            h_overlap = not (x1 + w1 <= x2 or x1 >= x2 + w2)
            v_overlap = not (y1 + h1 <= y2 or y1 >= y2 + h2)
            if h_overlap and v_overlap:
                return False, f"Rect {k1} collides with Rect {k2}"
                
    if cy[19] + 24.0 > 1160.0:
        return False, f"Bottom edge {cy[19] + 24.0} > 1160.0"
        
    return True, "ALL OK"

ok, msg = test_config(cy)
print(f"Audit result: {ok}, {msg}")
