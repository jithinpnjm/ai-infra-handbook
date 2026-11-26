import math

def check_pad(rx, ry, lines, fs=30, icon_w=32, icon_h=32, icon_pos="above", gap=6):
    scale = math.sqrt((1.0/rx)**2 + (1.0/ry)**2)
    # calculate line widths
    line_widths = [len(l) * fs * 0.6 for l in lines]
    max_tw = max(line_widths)
    total_th = len(lines) * fs + (len(lines) - 1) * 4
    
    if icon_pos == "above":
        total_h = icon_h + gap + total_th
        pts = [
            (-icon_w/2, -total_h/2), (icon_w/2, -total_h/2),
            (-icon_w/2, -total_h/2 + icon_h), (icon_w/2, -total_h/2 + icon_h)
        ]
        curr_y = -total_h/2 + icon_h + gap
        for lw in line_widths:
            pts.extend([
                (-lw/2, curr_y), (lw/2, curr_y),
                (-lw/2, curr_y + fs), (lw/2, curr_y + fs)
            ])
            curr_y += fs + 4
    elif icon_pos == "beside":
        total_w = icon_w + gap + max_tw
        pts = [
            (-total_w/2, -icon_h/2), (-total_w/2, icon_h/2),
            (-total_w/2 + icon_w, -icon_h/2), (-total_w/2 + icon_w, icon_h/2)
        ]
        curr_y = -total_th/2
        for lw in line_widths:
            x_start = -total_w/2 + icon_w + gap
            pts.extend([
                (x_start, curr_y), (x_start + lw, curr_y),
                (x_start, curr_y + fs), (x_start + lw, curr_y + fs)
            ])
            curr_y += fs + 4
    elif icon_pos == "none": # if icon is outside or not in diamond
        curr_y = -total_th/2
        pts = []
        for lw in line_widths:
            pts.extend([
                (-lw/2, curr_y), (lw/2, curr_y),
                (-lw/2, curr_y + fs), (lw/2, curr_y + fs)
            ])
            curr_y += fs + 4

    min_d = 9999
    for px, py in pts:
        val = abs(px)/rx + abs(py)/ry
        d = (1.0 - val) / scale
        if d < min_d:
            min_d = d
    return min_d

# Let us test single line: "a succeeds?" (len 11, fs=30)
# and "b succeeded?" (len 13, fs=30)
print("Single line beside:")
for rx in [160, 170, 180, 190, 200]:
    for ry in [60, 70, 80, 90]:
        d1 = check_pad(rx, ry, ["a succeeds?"], fs=30, icon_w=28, icon_h=28, icon_pos="beside", gap=8)
        d2 = check_pad(rx, ry, ["b succeeded?"], fs=30, icon_w=28, icon_h=28, icon_pos="beside", gap=8)
        if d1 >= 16 and d2 >= 16:
            print(f"PASS rx={rx}, ry={ry}: d1={d1:.1f}, d2={d2:.1f}")

print("\nTwo lines (stacked text, icon above):")
# "a" / "succeeds?" and "b" / "succeeded?"
for rx in [140, 150, 160, 170]:
    for ry in [75, 80, 85, 90]:
        d1 = check_pad(rx, ry, ["a", "succeeds?"], fs=30, icon_w=24, icon_h=24, icon_pos="above", gap=6)
        d2 = check_pad(rx, ry, ["b", "succeeded?"], fs=30, icon_w=24, icon_h=24, icon_pos="above", gap=6)
        if d1 >= 16 and d2 >= 16:
            print(f"PASS 2-line rx={rx}, ry={ry}: d1={d1:.1f}, d2={d2:.1f}")
