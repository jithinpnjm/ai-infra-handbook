steps_config = [
    {"num": 1, "src": "U", "h": 32},
    {"num": 2, "src": "A", "h": 32},
    {"num": 3, "src": "S", "h": 52},
    {"num": 4, "src": "A", "h": 32},
    {"num": 5, "src": "K", "h": 52},
    {"num": 6, "src": "K", "h": 32},
    {"num": 7, "src": "K", "h": 32},
    {"num": 8, "src": "K", "h": 32},
    {"num": 9, "src": "R", "h": 32},
    {"num": 10, "src": "K", "h": 32},
    {"num": 11, "src": "K", "h": 32},
    {"num": 12, "src": "R", "h": 32},
    {"num": 13, "src": "K", "h": 76},
    {"num": "note", "src": "K", "h": 38},
    {"num": 14, "src": "U", "h": 32},
    {"num": 15, "src": "A", "h": 32},
    {"num": 16, "src": "K", "h": 32},
    {"num": 17, "src": "K", "h": 32},
    {"num": 18, "src": "K", "h": 32},
    {"num": 19, "src": "K", "h": 32}
]

cur_y = 236.0
gap = 8.0
prev_k_cy = None

for sc in steps_config:
    by = cur_y
    bh = sc["h"]
    cy = by + (bh / 2.0)
    sc["by"] = by
    sc["cy"] = cy
    cur_y += bh + gap
    
    if sc["src"] == "K" and sc["num"] != "note":
        if prev_k_cy is not None:
            dist = cy - prev_k_cy
            print(f"Step {sc['num']:>2} vs prev K: dist = {dist:4.1f}px (need >= 48px)")
        prev_k_cy = cy

