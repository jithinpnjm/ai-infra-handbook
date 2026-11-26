# Let's test Row 1 and Row 2 ending at y = 204:
# Title at y = 38
# Row 1: y = 46 to 120 (h = 74)
# Row 2: y = 126 to 200 (h = 74)
# Gap to steps: 200 to 216 = 16 px.
# Step 1 starts at y = 216.

steps_config = [
    {"num": 1, "src": "U", "h": 30},
    {"num": 2, "src": "A", "h": 30},
    {"num": 3, "src": "S", "h": 50},
    {"num": 4, "src": "A", "h": 30},
    {"num": 5, "src": "K", "h": 50},
    {"num": 6, "src": "K", "h": 30},
    {"num": 7, "src": "K", "h": 30},
    {"num": 8, "src": "K", "h": 30},
    {"num": 9, "src": "R", "h": 30},
    {"num": 10, "src": "K", "h": 30},
    {"num": 11, "src": "K", "h": 30},
    {"num": 12, "src": "R", "h": 30},
    {"num": 13, "src": "K", "h": 72},
    {"num": "note", "src": "K", "h": 36},
    {"num": 14, "src": "U", "h": 30},
    {"num": 15, "src": "A", "h": 30},
    {"num": 16, "src": "K", "h": 30},
    {"num": 17, "src": "K", "h": 30},
    {"num": 18, "src": "K", "h": 30},
    {"num": 19, "src": "K", "h": 30}
]

cur_y = 216.0
prev_src = None
prev_k_cy = None

for sc in steps_config:
    src = sc["src"]
    num = sc["num"]
    bh = sc["h"]
    
    # Calculate gap to previous step:
    if prev_src == "K" and src == "K" and num != "note":
        # We need cy - prev_k_cy >= 49.0
        # cy = by + bh/2
        # prev_cy = prev_by + prev_bh/2
        # by - prev_by >= 49 - bh/2 + prev_bh/2
        needed_gap = max(6.0, 49.0 - (bh/2.0) - (prev_bh/2.0))
        cur_y += needed_gap
    else:
        if prev_src is not None:
            cur_y += 6.0
            
    by = cur_y
    cy = by + (bh / 2.0)
    sc["by"] = by
    sc["cy"] = cy
    cur_y += bh
    prev_src = src
    prev_bh = bh
    
    if src == "K" and num != "note":
        if prev_k_cy is not None:
            dist = cy - prev_k_cy
            print(f"Step {str(num):>4} K-dist: {dist:4.1f}px (>=48)")
            assert dist >= 48.9, f"dist {dist} < 49!"
        prev_k_cy = cy

print(f"\nFinal Y ends at: {cur_y:.1f}px")
print(f"Canvas Height: 1200, Bottom margin: {1200.0 - cur_y:.1f}px (>= 40px)")
assert 1200.0 - cur_y >= 40.0, f"Bottom margin {1200.0 - cur_y} < 40!"
print("PERFECT! Bottom margin >= 40px and all K distances >= 49px!")
