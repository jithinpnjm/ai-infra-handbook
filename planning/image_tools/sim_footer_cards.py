# Simulate footer cards geometry

cards = [
    {
        "id": "card-1",
        "rx": 40, "ry": 855, "rw": 486, "rh": 235,
        "icon": (40 + 24, 855 + 20, 48, 48), # x, y, w, h -> bottom is 855+68=923
        "lines": [
            ("Kernels before 5.4", 40 + 92, 855 + 52, "sans", 24),
            ("(slice-expiry fix) could", 40 + 24, 855 + 104, "sans", 24),
            ("throttle even with unused", 40 + 24, 855 + 138, "sans", 24),
            ("quota: use a recent kernel", 40 + 24, 855 + 172, "sans", 24),
        ]
    },
    {
        "id": "card-2",
        "rx": 557, "ry": 855, "rw": 486, "rh": 235,
        "icon": (557 + 24, 855 + 20, 48, 48),
        "lines": [
            ("cpu.max.burst", 557 + 92, 855 + 52, "mono", 24),
            ("(kernel 5.14 and later)", 557 + 24, 855 + 104, "sans", 24),
            ("lets a group save unused", 557 + 24, 855 + 138, "sans", 24),
            ("quota for short bursts", 557 + 24, 855 + 172, "sans", 24),
        ]
    },
    {
        "id": "card-3",
        "rx": 1074, "ry": 855, "rw": 486, "rh": 235,
        "icon": (1074 + 24, 855 + 20, 48, 48),
        "lines": [
            ("Inside a container,", 1074 + 92, 855 + 52, "sans", 24),
            ("nproc and /proc/cpuinfo", 1074 + 24, 855 + 92, "sans", 24), # wait, 5 lines in card 3!
            ("still show the host unless", 1074 + 24, 855 + 126, "sans", 24),
            ("you use lxcfs or a runtime", 1074 + 24, 855 + 160, "sans", 24),
            ("that understands limits", 1074 + 24, 855 + 194, "sans", 24),
        ]
    }
]

print("Simulating footer cards...")
for c in cards:
    rx, ry, rw, rh = c['rx'], c['ry'], c['rw'], c['rh']
    ix, iy, iw, ih = c['icon']
    icon_bottom = iy + ih
    print(f"\n{c['id']}: icon bottom={icon_bottom}")
    for text, tx, ty, ftype, fs in c['lines']:
        w_factor = 0.62 if ftype == 'mono' else 0.6
        w = len(text) * w_factor * fs
        pad_l = tx - rx
        pad_r = (rx + rw) - (tx + w)
        top_y = ty - fs * 0.8
        bot_y = ty + fs * 0.2
        # Check if text is beside icon or below icon
        overlap_icon = False
        if tx < ix + iw and tx + w > ix:
            # Horizontally overlaps icon
            if top_y < iy + ih and bot_y > iy:
                overlap_icon = True
            vert_dist = top_y - (iy + ih)
            print(f"  Line below icon: vert_dist={vert_dist:4.1f}px (pad_l={pad_l:4.1f}, pad_r={pad_r:4.1f}) '{text}'")
        else:
            horiz_dist = tx - (ix + iw)
            print(f"  Line beside icon: horiz_dist={horiz_dist:4.1f}px (pad_l={pad_l:4.1f}, pad_r={pad_r:4.1f}) '{text}'")
        assert pad_l >= 16, f"pad_l {pad_l} < 16"
        assert pad_r >= 16, f"pad_r {pad_r} < 16"
        assert not overlap_icon, f"Overlaps icon: {text}"
