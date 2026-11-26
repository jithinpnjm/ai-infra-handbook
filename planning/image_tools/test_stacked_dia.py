import math

def check_pad_stacked(rx, ry, text, fs=30, iw=32, ih=32, gap=6):
    scale = math.sqrt((1.0/rx)**2 + (1.0/ry)**2)
    tw = len(text) * fs * 0.6
    th = fs
    total_h = ih + gap + th
    # icon at top
    pts = [
        (-iw/2, -total_h/2), (iw/2, -total_h/2),
        (-iw/2, -total_h/2 + ih), (iw/2, -total_h/2 + ih),
        (-tw/2, total_h/2 - th), (tw/2, total_h/2 - th),
        (-tw/2, total_h/2), (tw/2, total_h/2)
    ]
    min_d = 9999
    for px, py in pts:
        val = abs(px)/rx + abs(py)/ry
        d = (1.0 - val) / scale
        if d < min_d:
            min_d = d
    return min_d

# tw for "a succeeds?" (11 chars) is 198px (half is 99px)
# tw for "b succeeded?" (13 chars) is 234px (half is 117px)
for rx in [160, 170, 180, 190, 200]:
    for ry in [80, 90, 100, 110]:
        d1 = check_pad_stacked(rx, ry, "a succeeds?", fs=30, iw=32, ih=32, gap=6)
        d2 = check_pad_stacked(rx, ry, "b succeeded?", fs=30, iw=32, ih=32, gap=6)
        if d1 >= 16.0 and d2 >= 16.0:
            print(f"PASS stacked: rx={rx}, ry={ry}: d1={d1:.2f}px, d2={d2:.2f}px")
            break
