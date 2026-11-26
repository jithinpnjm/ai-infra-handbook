#!/usr/bin/env python3

def check_row2_col2():
    lines = [
        "no reply to the SYNs, retried",
        "with exponential backoff",
        "1, 2, 4 seconds and so on;",
        "tcp_syn_retries=6 gives",
        "about 127 seconds"
    ]
    fs = 24
    box_w = 460
    box_h = 180
    
    # check width padding
    for ln in lines:
        w = len(ln) * 0.6 * fs
        pad_x = (box_w - w) / 2
        print(f"w={w:5.1f}px, pad_x={pad_x:4.1f}px: '{ln}'")
        assert pad_x >= 16, f"pad_x {pad_x} < 16 for '{ln}'"
        
    # check height padding
    # 5 lines: dy = 28. y0 = 36.
    # text y coords: 36, 64, 92, 120, 148
    # top of line 1: 36 - 18 = 18px (padding top = 18 >= 16)
    # bottom of line 5: 148 + 6 = 154px (padding bottom = 180 - 154 = 26 >= 16)
    print("Row 2 Col 2 5-line wrap PASSED!")

check_row2_col2()
