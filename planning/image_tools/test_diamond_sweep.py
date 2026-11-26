import math

def check_diamond_exact(rx, ry, title, fs=30, icon_w=32, icon_h=32, gap=10):
    scale = math.sqrt((1.0/rx)**2 + (1.0/ry)**2)
    tw = len(title) * fs * 0.6
    total_w = icon_w + gap + tw
    pts = [
        (-total_w/2, -icon_h/2), (-total_w/2, icon_h/2),
        (-total_w/2 + icon_w, -icon_h/2), (-total_w/2 + icon_w, icon_h/2),
        (total_w/2 - tw, -fs/2), (total_w/2 - tw, fs/2),
        (total_w/2, -fs/2), (total_w/2, fs/2)
    ]
    min_d = 9999
    for px, py in pts:
        val = abs(px)/rx + abs(py)/ry
        d = (1.0 - val) / scale
        if d < min_d:
            min_d = d
    return min_d

for rx in [190, 195, 200, 205, 210]:
    for ry in [75, 80, 85, 90, 95]:
        d_a = check_diamond_exact(rx, ry, "a succeeds?", fs=30, icon_w=28, icon_h=28, gap=8)
        d_b = check_diamond_exact(rx, ry, "b succeeded?", fs=30, icon_w=28, icon_h=28, gap=8)
        if d_a >= 16.0 and d_b >= 16.0:
            print(f"PASS rx={rx}, ry={ry}: d_a={d_a:.2f}px, d_b={d_b:.2f}px")
            break
