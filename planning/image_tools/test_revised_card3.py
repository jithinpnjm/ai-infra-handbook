# Test revised footer layout

lines_card3 = [
    ("Inside a container,", 1074 + 92, 855 + 46, "sans", 24),
    ("nproc and /proc/cpuinfo", 1074 + 92, 855 + 76, "sans", 24),
    ("still show the host unless", 1074 + 24, 855 + 118, "sans", 24),
    ("you use lxcfs or a runtime", 1074 + 24, 855 + 150, "sans", 24),
    ("that understands limits", 1074 + 24, 855 + 182, "sans", 24),
]

ix, iy, iw, ih = 1074 + 24, 855 + 20, 48, 48
rx, ry, rw, rh = 1074, 855, 486, 235

print("Card 3 test:")
for text, tx, ty, ftype, fs in lines_card3:
    w_factor = 0.62 if ftype == 'mono' else 0.6
    w = len(text) * w_factor * fs
    pad_l = tx - rx
    pad_r = (rx + rw) - (tx + w)
    top_y = ty - fs * 0.8
    bot_y = ty + fs * 0.2
    if tx < ix + iw and tx + w > ix:
        vert_dist = top_y - (iy + ih)
        print(f"  Under icon: vert_dist={vert_dist:4.1f}px (pad_l={pad_l:4.1f}, pad_r={pad_r:4.1f}) '{text}'")
        assert vert_dist >= 16
    else:
        horiz_dist = tx - (ix + iw)
        print(f"  Beside icon: horiz_dist={horiz_dist:4.1f}px (pad_l={pad_l:4.1f}, pad_r={pad_r:4.1f}) '{text}'")
        assert horiz_dist >= 16
    assert pad_l >= 16
    assert pad_r >= 16

print("Card 3 layout is 100% compliant!")
