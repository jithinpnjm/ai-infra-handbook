# Let's check each inner box:

boxes = [
    # Panel 1:
    ("P1 Code", 60, 270, 440, 252, 304, 7, 32, "mono"),
    ("P1 Output", 60, 542, 440, 124, 576, 3, 32, "mono"),
    ("P1 Note", 60, 686, 440, 338, 720, 10, 31, "sans"),
    
    # Panel 2:
    ("P2 Code", 580, 270, 440, 176, 308, 4, 34, "mono"),
    ("P2 Note", 580, 476, 440, 246, 514, 6, 34, "sans"),
    ("P2 Other", 580, 752, 440, 186, 790, 4, 34, "sans"),
    
    # Panel 3:
    ("P3 Found", 1100, 270, 440, 196, 306, 5, 32, "mono"),
    ("P3 Failure", 1100, 490, 440, 228, 526, 6, 32, "mono"),
    ("P3 Reason", 1100, 742, 440, 228, 778, 6, 32, "sans"),
]

for name, bx, by, bw, bh, first_y, n_lines, line_h, font_type in boxes:
    fs = 24
    cap_h = 17 # typical cap height for 24px
    descent = 6 # typical descent below baseline
    top_pad = first_y - cap_h - by
    last_y = first_y + (n_lines - 1) * line_h
    bottom_pad = (by + bh) - (last_y + descent)
    print(f"[{name}] top_pad={top_pad}px, bottom_pad={bottom_pad}px (box_h={bh})")
    assert top_pad >= 16, f"[{name}] top_pad {top_pad} < 16px!"
    assert bottom_pad >= 16, f"[{name}] bottom_pad {bottom_pad} < 16px!"

print("\nAll inner box top and bottom paddings strictly >= 16px! (PASS)")
