import math

def test_config(rx, ry, icon_w, icon_h, text_w, text_h, layout="beside", gap=12):
    # Diamond centered at 0, 0
    scale = math.sqrt((1.0/rx)**2 + (1.0/ry)**2)
    
    if layout == "beside":
        total_w = icon_w + gap + text_w
        # icon at x in [-total_w/2, -total_w/2 + icon_w], y in [-icon_h/2, icon_h/2]
        # text at x in [total_w/2 - text_w, total_w/2], y in [-text_h/2, text_h/2]
        pts = [
            (-total_w/2, -icon_h/2), (-total_w/2, icon_h/2),
            (-total_w/2 + icon_w, -icon_h/2), (-total_w/2 + icon_w, icon_h/2),
            (total_w/2 - text_w, -text_h/2), (total_w/2 - text_w, text_h/2),
            (total_w/2, -text_h/2), (total_w/2, text_h/2)
        ]
    elif layout == "stacked":
        total_h = icon_h + gap + text_h
        # icon at x in [-icon_w/2, icon_w/2], y in [-total_h/2, -total_h/2 + icon_h]
        # text at x in [-text_w/2, text_w/2], y in [total_h/2 - text_h, total_h/2]
        pts = [
            (-icon_w/2, -total_h/2), (icon_w/2, -total_h/2),
            (-icon_w/2, -total_h/2 + icon_h), (icon_w/2, -total_h/2 + icon_h),
            (-text_w/2, total_h/2 - text_h), (text_w/2, total_h/2 - text_h),
            (-text_w/2, total_h/2), (text_w/2, total_h/2)
        ]
        
    min_dist = 9999
    for px, py in pts:
        val = abs(px)/rx + abs(py)/ry
        d = (1.0 - val) / scale
        if d < min_dist:
            min_dist = d
    return min_dist

# Let us test with text_w = 11 * 18 = 198px (sans 30px "a succeeds?"), text_h = 30
# and icon_w = 40, icon_h = 40
print("--- BESIDE ---")
for rx in [220, 240, 260, 280, 300]:
    for ry in [70, 80, 90, 100]:
        d = test_config(rx, ry, 40, 40, 198, 30, layout="beside", gap=12)
        if d >= 16.0:
            print(f"PASS beside: rx={rx}, ry={ry} -> min_dist={d:.2f}px")

print("--- STACKED ---")
for rx in [180, 200, 220, 240, 260]:
    for ry in [80, 90, 100, 110, 120]:
        d = test_config(rx, ry, 36, 36, 198, 30, layout="stacked", gap=8)
        if d >= 16.0:
            print(f"PASS stacked: rx={rx}, ry={ry} -> min_dist={d:.2f}px")
