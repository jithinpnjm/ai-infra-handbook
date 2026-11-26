# Let's inspect all cards and lines

def check_card_padding(name, box_x, box_y, box_w, box_h, text_x, text_y, lines, line_dy=30, fs=24):
    box_right = box_x + box_w
    box_bottom = box_y + box_h
    
    print(f"\n=== {name} ===")
    print(f"Box: x={box_x}..{box_right}, y={box_y}..{box_bottom} (w={box_w}, h={box_h})")
    
    # Left padding
    pad_left = text_x - box_x
    print(f"Padding left: {pad_left:.1f} px ({'OK' if pad_left >= 16 else 'FAIL'})")
    assert pad_left >= 16
    
    # Top padding (first line cap height ~ fs * 0.8 above baseline)
    pad_top = (text_y - fs * 0.8) - box_y
    print(f"Padding top: {pad_top:.1f} px ({'OK' if pad_top >= 16 else 'FAIL'})")
    assert pad_top >= 16, f"Padding top {pad_top} < 16!"
    
    # Line widths and right padding
    max_right = 0
    for i, (l, is_m) in enumerate(lines):
        coeff = 0.62 if is_m else 0.60
        w = len(l) * coeff * fs
        right = text_x + w
        pad_r = box_right - right
        print(f"  Line {i+1} [w={w:.1f}, right={right:.1f}, pad_r={pad_r:.1f}]: {l}")
        assert pad_r >= 16, f"Line {i+1} pad_r {pad_r:.1f} < 16!"
        if right > max_right:
            max_right = right
            
    # Bottom padding (last line baseline + descender ~ fs * 0.2 below baseline)
    last_y = text_y + (len(lines) - 1) * line_dy
    pad_bottom = box_bottom - (last_y + fs * 0.2)
    print(f"Padding bottom: {pad_bottom:.1f} px ({'OK' if pad_bottom >= 16 else 'FAIL'})")
    assert pad_bottom >= 16, f"Padding bottom {pad_bottom:.1f} < 16!"

# Let's test Step 2:
step2 = [
    ("2 for each node group, simulate ", False),
    ("adding a node from its template: ", False),
    ("would the pod fit", False)
]
check_card_padding("Step 2", 65, 308, 690, 114, 216, 347, step2, 32, 24)

# Let's test Step 3:
step3 = [
    ("3 expander picks among groups: ", False),
    ("random picks any, least-waste ", False),
    ("leaves the fewest empty seats, ", False),
    ("most-pods carries the most waiting ", False),
    ("pods", False)
]
check_card_padding("Step 3", 65, 448, 690, 162, 216, 482, step3, 31, 24)

# Let's test Step 4:
step4 = [
    ("4 group size raised within its min ", False),
    ("and max, for example ", False),
    ("--nodes=1:10:worker-auto-scaling-group", True)
]
check_card_padding("Step 4", 65, 636, 690, 132, 216, 670, step4, 32, 24)

# Let's test Step 5:
step5 = [
    ("5 node joins, scheduler places ", False),
    ("pods", False)
]
check_card_padding("Step 5", 65, 794, 690, 96, 216, 836, step5, 32, 24)

# Let's test Scale down condition:
sd_lines = [
    ("node utilisation (requests against ", False),
    ("allocatable) below ", False),
    ("--scale-down-utilization-threshold 0.5 ", True),
    ("for --scale-down-unneeded-time 10 min, ", True),
    ("then drain and remove", False)
]
check_card_padding("Scale-down condition", 845, 186, 690, 184, 944, 220, sd_lines, 30, 24)

