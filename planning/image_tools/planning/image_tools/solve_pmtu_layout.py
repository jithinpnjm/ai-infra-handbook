#!/usr/bin/env python3
# Layout solver for PMTU black hole infographic
# Canvas: 1600 x 1180 (within 900-1200 range)

# Margins: 40px left and right (content width = 1520, x from 40 to 1560)
# Gap between left and right panels = 40px
# Panel width = (1520 - 40) / 2 = 740px
# Left panel: x = 40, width = 740 (40 to 780)
# Right panel: x = 820, width = 740 (820 to 1560)
# Inside panels: inner card width = 696px (x from 62 to 758, and 842 to 1538)

def solve():
    # Title
    title_box = (40, 20, 1520, 125)
    title_lines = [
        ("Fixing a PMTU black hole: four options", 48, 68),
        ("and the ping arithmetic that finds it", 48, 122)
    ]
    
    # Panels y: 165
    panel_y = 165
    panel_h = 515 # 165 to 680
    
    # Left Header: y = 165, h = 65
    left_header_box = (40, 165, 740, 65)
    left_header_line = ("Four ways to fix a black hole", 30, 208, 135)
    
    # Left Card 1: 3 lines
    # y = 238, h = 108
    c1_box = (62, 238, 696, 108)
    c1_lines = [
        ("1 allow the required ICMP messages", 24, 268, 82),
        ("(IPv4 type 3 code 4 Fragmentation Needed,", 24, 298, 82),
        ("IPv6 type 2 Packet Too Big)", 24, 328, 82)
    ]
    
    # Left Card 2: 4 lines
    # y = 356, h = 138
    c2_box = (62, 356, 696, 138)
    c2_lines = [
        ("2 clamp the TCP MSS on tunnels:", 24, 386, 82, False),
        ("iptables -t mangle -A FORWARD", 24, 416, 82, True),
        ("-p tcp --tcp-flags SYN,RST SYN", 24, 446, 82, True),
        ("-j TCPMSS --clamp-mss-to-pmtu", 24, 476, 82, True)
    ]
    
    # Left Card 3: 1 line
    # y = 504, h = 64
    c3_box = (62, 504, 696, 64)
    c3_lines = [
        ("3 use a consistent MTU across the path", 24, 542, 82, False)
    ]
    
    # Left Card 4: 2 lines
    # y = 578, h = 90
    c4_box = (62, 578, 696, 90)
    c4_lines = [
        ("4 enable PLPMTUD with", 24, 610, 82, False),
        ("net.ipv4.tcp_mtu_probing", 24, 642, 82, True)
    ]
    # End of Left Panel content = 578 + 90 = 668 < 680 (12px padding inside panel)
    
    # Right Header: y = 165, h = 65
    right_header_box = (820, 165, 740, 65)
    right_header_line = ("Ping sizes add up to 1500", 30, 208, 915)
    
    # Right Card 1: visual bar + 2 text lines
    # y = 238, h = 120
    # visual bar at y = 250, h = 20
    # text starts at y = 300
    r1_box = (842, 238, 696, 122)
    r1_lines = [
        ("payload 1472 + ICMP 8 + IPv4 20 = 1500", 24, 305, 862, False),
        ("(ping -M do -s 1472)", 24, 337, 862, True)
    ]
    
    # Right Card 2: visual bar + 2 text lines
    # y = 370, h = 122
    r2_box = (842, 370, 696, 122)
    r2_lines = [
        ("payload 1452 + ICMP 8 + IPv6 40 = 1500", 24, 437, 862, False),
        ("(ping -6 -M do -s 1452)", 24, 469, 862, True)
    ]
    
    # Right Card 3: 3 lines
    # y = 502, h = 166
    r3_box = (842, 502, 696, 166)
    r3_lines = [
        ("MSS at MTU 1500:", 24, 538, 862, False),
        ("IPv4 1500 - 20 - 20 = 1460;", 24, 578, 862, False),
        ("IPv6 1500 - 40 - 20 = 1440", 24, 618, 862, False)
    ]
    # End of Right Panel content = 502 + 166 = 668 < 680
    
    # Fragmentation Costs Box
    # y = 698, h = 166
    frag_box = (40, 698, 1520, 166)
    frag_lines = [
        ("Fragmentation costs: each fragment carries an ID,", 24, 734, 140, False),
        ("an offset in 8-byte units and the MF flag;", 24, 764, 140, False),
        ("lose one fragment and you lose the whole packet; firewalls often drop fragments;", 24, 794, 140, False),
        ("some hardware paths send them to the CPU", 24, 824, 140, False)
    ]
    
    # Bottom Strip
    # y = 880, h = 92
    strip_box = (40, 880, 1520, 92)
    strip_lines = [
        ("tracepath target, ip route get target,", 24, 915, 135, True),
        ("ss -ti dst target | grep mss pmtu: find the narrow door", 24, 947, 135, True)
    ]
    
    # Bottom Bar
    # y = 988, h = 76
    bar_box = (40, 988, 1520, 76)
    bar_lines = [
        ("If the largest working size is smaller than you expected, you have found a narrow door", 26, 1034, 800, False)
    ]
    # Canvas height = 988 + 76 + 40 = 1104!
    canvas_h = 1104
    
    return [
        {"name": "Title", "box": title_box, "align": "middle", "lines": [(t, fs, yb, 800, False) for t, fs, yb in title_lines]},
        {"name": "Left Header", "box": left_header_box, "align": "left", "lines": [(left_header_line[0], left_header_line[1], left_header_line[2], left_header_line[3], False)]},
        {"name": "Left Card 1", "box": c1_box, "align": "left", "lines": [(t, fs, yb, x, False) for t, fs, yb, x in c1_lines]},
        {"name": "Left Card 2", "box": c2_box, "align": "left", "lines": [(t, fs, yb, x, is_m) for t, fs, yb, x, is_m in c2_lines]},
        {"name": "Left Card 3", "box": c3_box, "align": "left", "lines": [(t, fs, yb, x, is_m) for t, fs, yb, x, is_m in c3_lines]},
        {"name": "Left Card 4", "box": c4_box, "align": "left", "lines": [(t, fs, yb, x, is_m) for t, fs, yb, x, is_m in c4_lines]},
        {"name": "Right Header", "box": right_header_box, "align": "left", "lines": [(right_header_line[0], right_header_line[1], right_header_line[2], right_header_line[3], False)]},
        {"name": "Right Card 1", "box": r1_box, "align": "left", "lines": [(t, fs, yb, x, is_m) for t, fs, yb, x, is_m in r1_lines]},
        {"name": "Right Card 2", "box": r2_box, "align": "left", "lines": [(t, fs, yb, x, is_m) for t, fs, yb, x, is_m in r2_lines]},
        {"name": "Right Card 3", "box": r3_box, "align": "left", "lines": [(t, fs, yb, x, is_m) for t, fs, yb, x, is_m in r3_lines]},
        {"name": "Frag Costs", "box": frag_box, "align": "left", "lines": [(t, fs, yb, x, is_m) for t, fs, yb, x, is_m in frag_lines]},
        {"name": "Bottom Strip", "box": strip_box, "align": "left", "lines": [(t, fs, yb, x, is_m) for t, fs, yb, x, is_m in strip_lines]},
        {"name": "Bottom Bar", "box": bar_box, "align": "middle", "lines": [(t, fs, yb, x, is_m) for t, fs, yb, x, is_m in bar_lines]},
    ], canvas_h

all_items, canvas_h = solve()
all_passed = True
for it in all_items:
    bx, by, bw, bh = it["box"]
    for text, fs, y_base, x_pos, is_mono in it["lines"]:
        cf = 0.62 if is_mono else 0.60
        text_w = len(text) * fs * cf
        if it["align"] == "middle":
            x_left = x_pos - text_w / 2
            x_right = x_pos + text_w / 2
        else:
            x_left = x_pos
            x_right = x_pos + text_w
            
        y_top = y_base - 0.8 * fs
        y_bottom = y_base + 0.2 * fs
        
        pl = x_left - bx
        pr = (bx + bw) - x_right
        pt = y_top - by
        pb = (by + bh) - y_bottom
        
        ok = min(pl, pr, pt, pb) >= 16.0
        if not ok:
            all_passed = False
        status = "PASS" if ok else "FAIL"
        print(f"{it['name'][:20]:<20} | {pl:5.1f} | {pr:5.1f} | {pt:5.1f} | {pb:5.1f} | {status} ({text[:20]}...)")

assert all_passed, "Some items failed padding >= 16px!"
print(f"\nSUCCESS! All paddings >= 16px! Canvas height: {canvas_h}")
