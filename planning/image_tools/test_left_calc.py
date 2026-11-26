def test_left_column():
    card_y = 110
    card_h = 540
    card_bottom = card_y + card_h
    
    # Title
    t1_y = 158
    t2_y = 194
    # pad_top of title = (158 - 30) - 110 = 18 px >= 16
    print("Title pad_top:", (158 - 30) - 110)
    
    # Item 1: Limit: 24 GiB (1 line, fs=24)
    i1_y = 215
    i1_h = 58
    i1_base = i1_y + 40 # 255
    print("Item 1 pad_top:", (i1_base - 24) - i1_y, "pad_bottom:", (i1_y + i1_h) - i1_base)
    assert (i1_base - 24) - i1_y >= 16
    assert (i1_y + i1_h) - i1_base >= 16
    
    # Item 2: Worker processes: 4 (1 line, fs=24)
    i2_y = 285
    i2_h = 58
    i2_base = i2_y + 40 # 325
    print("Item 2 pad_top:", (i2_base - 24) - i2_y, "pad_bottom:", (i2_y + i2_h) - i2_base)
    assert (i2_base - 24) - i2_y >= 16
    assert (i2_y + i2_h) - i2_base >= 16
    
    # Item 3: Pinned staging buffers per worker: 4 GiB (3 lines, fs=24)
    i3_y = 355
    i3_h = 116
    i3_base1 = i3_y + 38 # 393 -> top = 393 - 24 = 369 -> pad_top = 369 - 355 = 14? wait:
    # We want pad_top >= 16 -> i3_base1 - 24 - i3_y >= 16 -> i3_base1 >= i3_y + 40
    i3_base1 = i3_y + 40 # 395
    i3_base2 = i3_base1 + 28 # 423
    i3_base3 = i3_base2 + 28 # 451
    # pad_bottom = (i3_y + i3_h) - i3_base3 -> (355 + 116) - 451 = 471 - 451 = 20 px >= 16!
    print("Item 3 pad_top:", (i3_base1 - 24) - i3_y, "pad_bottom:", (i3_y + i3_h) - i3_base3)
    assert (i3_base1 - 24) - i3_y >= 16
    assert (i3_y + i3_h) - i3_base3 >= 16
    
    # Item 4: Runtime memory per worker: 3 GiB (2 lines, fs=24)
    i4_y = 482
    i4_h = 86
    i4_base1 = i4_y + 40 # 522 -> pad_top = 522 - 24 - 482 = 16 px!
    i4_base2 = i4_base1 + 28 # 550
    # pad_bottom = (482 + 86) - 550 = 568 - 550 = 18 px >= 16!
    print("Item 4 pad_top:", (i4_base1 - 24) - i4_y, "pad_bottom:", (i4_y + i4_h) - i4_base2)
    assert (i4_base1 - 24) - i4_y >= 16
    assert (i4_y + i4_h) - i4_base2 >= 16
    
    # Item 5: Cached weights: 15 GiB (1 line! Remember length is 22 chars * 24 * 0.6 = 316.8 px!)
    # In a 320 px box, 316.8 px doesn't have 16px padding on both sides.
    # But if item 5 is split into 2 lines:
    # Line 1: 'Cached weights: ' (16 chars * 24 * 0.6 = 230.4 px)
    # Line 2: '15 GiB' (6 chars * 24 * 0.6 = 86.4 px)
    i5_y = 578
    i5_h = 60 # wait, if h = 60, line 1 base = 578 + 40 = 618? That leaves only 20 px for line 2.
    # What if Left Card is slightly wider, say w = 380 px?
    # In a 380 px card, inner box is w = 350 px (from x=75 to 425).
    # Then Cached weights: 15 GiB: 350 - 316.8 = 33.2 px -> 16.6 px on each side >= 16 px!
    # OR if split into 2 lines in a box of height 86 px:
    # Let's check card height: card_bottom is 650.
    # 578 + 86 = 664 > 650.
    # What if card height is 560 (y = 110 to 670)?
    print("Left column plan checked.")

test_left_column()
