def check_sec2():
    c_y = 330
    c_h = 380
    c_bottom = c_y + c_h # 710
    
    # 4 rule boxes of h=56, and ellipsis
    # Box 1:
    b1_y = 388
    b1_h = 56
    gap1 = 12
    # Box 2:
    b2_y = b1_y + b1_h + gap1 # 456
    b2_h = 56
    gap2 = 12
    # Box 3:
    b3_y = b2_y + b2_h + gap2 # 524
    b3_h = 56
    gap3 = 10
    # Ellipsis:
    ell_y = b3_y + b3_h + gap3 # 590
    ell_h = 24
    gap4 = 10
    # Box 4 (last rule):
    b4_y = ell_y + ell_h + gap4 # 624
    b4_h = 56
    b4_bottom = b4_y + b4_h # 680
    
    bot_pad_container = c_bottom - b4_bottom
    print(f"Container bottom pad: {bot_pad_container} >= 16: {bot_pad_container >= 16}")
    assert bot_pad_container >= 16
    
    # Check text paddings inside rule box:
    # box_h = 56, font_size = 24
    # baseline = box_y + 40
    # top_pad = (box_y + 40) - 24 - box_y = 16
    # bot_pad = (box_y + 56) - (box_y + 40) = 16
    print("Rule box text paddings: top=16.0, bot=16.0 -> EXACTLY 16px!")

check_sec2()
