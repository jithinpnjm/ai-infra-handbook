def check_sec1():
    box_x = 760
    box_y = 140
    box_w = 800
    box_h = 175
    box_bottom = box_y + box_h
    
    # Title
    t_text = "Implementation options"
    t_fs = 30
    t_x = 860
    t_y = 186
    t_w = len(t_text) * t_fs * 0.6
    
    # Check Title paddings
    pad_top = (t_y - t_fs) - box_y
    pad_left = t_x - box_x
    pad_right = (box_x + box_w) - (t_x + t_w)
    print(f"Title: top={pad_top:.1f}, left={pad_left:.1f}, right={pad_right:.1f}")
    assert pad_top >= 16
    assert pad_left >= 16
    assert pad_right >= 16
    
    # Option 1
    o1_text = "iptables rules (random probability chain)"
    o1_fs = 24
    o1_x = 790
    o1_y = 224
    o1_w = len(o1_text) * o1_fs * 0.6
    pad_o1_left = o1_x - box_x
    pad_o1_right = (box_x + box_w) - (o1_x + o1_w)
    print(f"Option 1: left={pad_o1_left:.1f}, right={pad_o1_right:.1f}, w={o1_w:.1f}")
    assert pad_o1_left >= 16
    assert pad_o1_right >= 16
    
    # Option 2
    o2_text = "IPVS (a real L4 scheduler)"
    o2_fs = 24
    o2_x = 790
    o2_y = 258
    o2_w = len(o2_text) * o2_fs * 0.6
    pad_o2_left = o2_x - box_x
    pad_o2_right = (box_x + box_w) - (o2_x + o2_w)
    print(f"Option 2: left={pad_o2_left:.1f}, right={pad_o2_right:.1f}, w={o2_w:.1f}")
    assert pad_o2_left >= 16
    assert pad_o2_right >= 16
    
    # Option 3
    o3_text = "eBPF replacement such as Cilium"
    o3_fs = 24
    o3_x = 790
    o3_y = 292
    o3_w = len(o3_text) * o3_fs * 0.6
    pad_o3_left = o3_x - box_x
    pad_o3_right = (box_x + box_w) - (o3_x + o3_w)
    pad_o3_bottom = box_bottom - o3_y
    print(f"Option 3: left={pad_o3_left:.1f}, right={pad_o3_right:.1f}, bottom={pad_o3_bottom:.1f}")
    assert pad_o3_left >= 16
    assert pad_o3_right >= 16
    assert pad_o3_bottom >= 16
    print("Section 1 checks PASSED!")

check_sec1()
