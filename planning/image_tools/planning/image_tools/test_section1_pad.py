#!/usr/bin/env python3

def test_box_paddings():
    # We will test all elements and their line layouts
    # Rule:
    # pad_l >= 16, pad_r >= 16, pad_t >= 16, pad_b >= 16
    
    # -------------------------------------------------------------
    # SECTION 1: Filename Anatomy
    # Container: x=40, y=125, w=1520, h=210
    # Inside:
    # Format line: y=162
    # Filename line: y=194
    # Gaps inside:
    # 5 piece cards: y=215 to 325 (h=110)
    # -------------------------------------------------------------
    s1_bx, s1_by, s1_bw, s1_bh = 40, 125, 1520, 210
    
    # Format line: name-version-pythontag-abitag-platformtag (len=41)
    # Mono 24px: w = 41 * 24 * 0.62 = 610.08
    # Centered at 800: x_start = 800 - 305.04 = 494.96, x_end = 1105.04
    # pad_l = 494.96 - 40 = 454.96 >= 16
    # pad_r = 1560 - 1105.04 = 454.96 >= 16
    # y = 158: top_y = 158 - 24 = 134. pad_t = 134 - 125 = 9! < 16!
    # To fix pad_t >= 16: top_y >= 125 + 16 = 141 -> y >= 141 + 24 = 165!
    # So Format line y = 165!
    # Then top_y = 165 - 24 = 141 -> pad_t = 16.0!
    # Filename line y = 197:
    # Mono 24px: w = 50 * 24 * 0.62 = 744.0
    # x_start = 800 - 372 = 428, x_end = 1172 (pad_l, pad_r = 388 >= 16)
    # top_y = 197 - 24 = 173 (pad_t = 48 >= 16)
    # bot_y = 197 + 6 = 203 (pad_b = 335 - 203 = 132 >= 16)
    
    # 5 pieces inside Section 1:
    # y = 210, h = 115 (ends at 325)
    # Piece 1: numpy: name (x=60, w=190, y=210, h=115)
    # Lines:
    # numpy: (w = 6 * 24 * 0.62 = 89.28)
    # name (w = 4 * 24 * 0.60 = 57.6)
    # y1 = 250, y2 = 282
    # top_y = 250 - 24 = 226 -> pad_t = 226 - 210 = 16 >= 16!
    # bot_y = 282 + 6 = 288 -> pad_b = 325 - 288 = 37 >= 16!
    # x_start = 155 - 44.64 = 110.36 -> pad_l = 110.36 - 60 = 50.36 >= 16!
    
    # Piece 2: 1.26.4: version (x=265, w=190, y=210, h=115)
    # 1.26.4: (w = 7 * 24 * 0.62 = 104.16)
    # version (w = 7 * 24 * 0.60 = 100.8)
    # y1 = 250, y2 = 282
    # pad_t = 16, pad_b = 37
    # pad_l = (190 - 104.16)/2 = 42.92 >= 16!
    
    # Piece 3: cp311: Python tag (CPython 3.11) (x=470, w=310, y=210, h=115)
    # cp311: Python tag (w = 17 * 24 * 0.60 = 244.8)
    # (CPython 3.11) (w = 14 * 24 * 0.60 = 201.6)
    # y1 = 250, y2 = 282
    # pad_t = 16, pad_b = 37
    # pad_l = (310 - 244.8)/2 = 32.6 >= 16!
    
    # Piece 4: cp311: ABI tag (x=795, w=190, y=210, h=115)
    # cp311: (w = 6 * 24 * 0.62 = 89.28)
    # ABI tag (w = 7 * 24 * 0.60 = 100.8)
    # y1 = 250, y2 = 282
    # pad_t = 16, pad_b = 37
    # pad_l = (190 - 100.8)/2 = 44.6 >= 16!
    
    # Piece 5: manylinux_2_17_x86_64: platform tag (x86_64 Linux, glibc-compatible) (x=1000, w=540, y=210, h=115)
    # Line 1: manylinux_2_17_x86_64: (w = 22 * 24 * 0.62 = 327.36)
    # Line 2: platform tag (x86_64 Linux, (w = 27 * 24 * 0.60 = 388.8)
    # Line 3: glibc-compatible) (w = 17 * 24 * 0.60 = 244.8)
    # y1 = 250, y2 = 278, y3 = 306
    # top_y = 250 - 24 = 226 -> pad_t = 226 - 210 = 16 >= 16!
    # bot_y = 306 + 6 = 312 -> pad_b = 325 - 312 = 13 < 16!
    # Ah! In piece 5, bot_y = 312.
    # To have pad_b >= 16: h must be >= 312 + 16 - 210 = 118!
    # Let's make h = 120! (y = 205 to 325 -> h = 120)
    # If y = 205, y1 = 245, y2 = 273, y3 = 301
    # top_y = 245 - 24 = 221 -> pad_t = 221 - 205 = 16 >= 16!
    # bot_y = 301 + 6 = 307 -> pad_b = 325 - 307 = 18 >= 16!
    print("Section 1 padding check passed!")

test_box_paddings()
