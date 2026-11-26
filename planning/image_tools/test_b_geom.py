#!/usr/bin/env python3

def test_full_geometry():
    # Box width = 380px (x=40..420)
    # Bracket 1 text:
    b1_lines = [
        "lines 1-2: finding the ",
        "link address because ",
        "the client needs the ",
        "server's MAC before it ",
        "can send a frame"
    ]
    for l in b1_lines:
        w = len(l) * 0.6 * 24
        pad_x = (380 - w) / 2
        print(f"B1 '{l.strip()}': w={w:.1f}px, pad_x={pad_x:.1f}px")
        assert pad_x >= 16, f"pad_x {pad_x} < 16!"
    
    b1_h = 4 * 25 + 24 # 124px
    pad_y_b1 = (160 - b1_h) / 2
    print(f"B1 pad_y={pad_y_b1:.1f}px")
    assert pad_y_b1 >= 16

    # Bracket 2:
    b2_w = len("three-way handshake") * 0.6 * 24
    pad_x_b2 = (380 - b2_w) / 2
    b2_h = 28 + 24 # 52px
    pad_y_b2 = (100 - b2_h) / 2
    print(f"B2 pad_x={pad_x_b2:.1f}px, pad_y={pad_y_b2:.1f}px")
    assert pad_x_b2 >= 16 and pad_y_b2 >= 16

    # Bracket 3:
    b3_w = len("lines 6-9: data") * 0.6 * 24
    pad_x_b3 = (380 - b3_w) / 2
    pad_y_b3 = (180 - 24) / 2
    print(f"B3 pad_x={pad_x_b3:.1f}px, pad_y={pad_y_b3:.1f}px")
    assert pad_x_b3 >= 16 and pad_y_b3 >= 16

    print("\nALL BRACKET PADDINGS PASS WITH FLYING COLORS!")

test_full_geometry()
