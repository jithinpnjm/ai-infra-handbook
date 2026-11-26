import math

def check_diamond_with_icon(rx, ry, title, fs=30, iw=52, ih=52, gap=10):
    scale = math.sqrt((1.0/rx)**2 + (1.0/ry)**2)
    tw = len(title) * fs * 0.6
    total_w = iw + gap + tw
    pts = [
        (-total_w/2, -ih/2), (-total_w/2, ih/2),
        (-total_w/2 + iw, -ih/2), (-total_w/2 + iw, ih/2),
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

for rx in [220, 230, 240, 250, 260]:
    for ry in [85, 90, 95, 100, 105]:
        d_a = check_diamond_with_icon(rx, ry, "a succeeds?", fs=30, iw=48, ih=48, gap=10)
        d_b = check_diamond_with_icon(rx, ry, "b succeeded?", fs=30, iw=48, ih=48, gap=10)
        if d_a >= 16.0 and d_b >= 16.0:
            print(f"PASS with 48px icon: rx={rx}, ry={ry}: d_a={d_a:.2f}px, d_b={d_b:.2f}px")
            break
