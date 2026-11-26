#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

# We will check the paddings of each box
boxes = [
    # Main Title
    {"name": "Title", "box": (40, 20, 1520, 120), "align": "middle",
     "lines": [
         ("Fixing a PMTU black hole: four options", 48, 75, False),
         ("and the ping arithmetic that finds it", 48, 129, False)
     ]},
    
    # Left Header: Four ways to fix a black hole
    {"name": "Left Header", "box": (40, 160, 740, 75), "align": "left", "x_text": 135,
     "lines": [
         ("Four ways to fix a black hole", 30, 214, False)
     ]},

    # Left Card 1
    {"name": "Left Card 1", "box": (60, 246, 700, 96), "align": "left", "x_text": 80,
     "lines": [
         ("1 allow the required ICMP messages", 24, 274, False),
         ("(IPv4 type 3 code 4 Fragmentation Needed,", 24, 302, False),
         ("IPv6 type 2 Packet Too Big)", 24, 330, False)
     ]},

    # Left Card 2
    {"name": "Left Card 2", "box": (60, 352, 700, 126), "align": "left", "x_text": 80,
     "lines": [
         ("2 clamp the TCP MSS on tunnels:", 24, 380, False),
         ("iptables -t mangle -A FORWARD", 24, 408, True),
         ("-p tcp --tcp-flags SYN,RST SYN", 24, 436, True),
         ("-j TCPMSS --clamp-mss-to-pmtu", 24, 464, True)
     ]},

    # Left Card 3
    {"name": "Left Card 3", "box": (60, 488, 700, 66), "align": "left", "x_text": 80,
     "lines": [
         ("3 use a consistent MTU across the path", 24, 530, False)
     ]},

    # Left Card 4
    {"name": "Left Card 4", "box": (60, 564, 700, 82), "align": "left", "x_text": 80,
     "lines": [
         ("4 enable PLPMTUD with", 24, 596, False),
         ("net.ipv4.tcp_mtu_probing", 24, 626, True)
     ]},

    # Right Header: Ping sizes add up to 1500
    {"name": "Right Header", "box": (820, 160, 740, 75), "align": "left", "x_text": 915,
     "lines": [
         ("Ping sizes add up to 1500", 30, 214, False)
     ]},

    # Right Card 1 (IPv4 Bar)
    # Note: bar geometry is inside the card at y=260, h=24. Text begins at y=316.
    {"name": "Right Card 1", "box": (840, 246, 700, 110), "align": "left", "x_text": 860,
     "lines": [
         ("payload 1472 + ICMP 8 + IPv4 20 = 1500", 24, 316, False),
         ("(ping -M do -s 1472)", 24, 344, True)
     ]},

    # Right Card 2 (IPv6 Bar)
    {"name": "Right Card 2", "box": (840, 366, 700, 110), "align": "left", "x_text": 860,
     "lines": [
         ("payload 1452 + ICMP 8 + IPv6 40 = 1500", 24, 436, False),
         ("(ping -6 -M do -s 1452)", 24, 464, True)
     ]},

    # Right Card 3 (MSS at MTU 1500)
    {"name": "Right Card 3", "box": (840, 486, 700, 160), "align": "left", "x_text": 860,
     "lines": [
         ("MSS at MTU 1500:", 24, 522, False),
         ("IPv4 1500 - 20 - 20 = 1460;", 24, 556, False),
         ("IPv6 1500 - 40 - 20 = 1440", 24, 590, False)
     ]},

    # Below: Fragmentation costs
    {"name": "Fragmentation Costs", "box": (40, 680, 1520, 150), "align": "left", "x_text": 140,
     "lines": [
         ("Fragmentation costs: each fragment carries an ID,", 24, 718, False),
         ("an offset in 8-byte units and the MF flag;", 24, 746, False),
         ("lose one fragment and you lose the whole packet; firewalls often drop fragments;", 24, 774, False),
         ("some hardware paths send them to the CPU", 24, 802, False)
     ]},

    # Bottom Strip
    {"name": "Bottom Strip", "box": (40, 850, 1520, 84), "align": "left", "x_text": 135,
     "lines": [
         ("tracepath target, ip route get target,", 24, 885, True),
         ("ss -ti dst target | grep mss pmtu: find the narrow door", 24, 913, True)
     ]},

    # Bottom Bar
    {"name": "Bottom Bar", "box": (40, 954, 1520, 76), "align": "middle",
     "lines": [
         ("If the largest working size is smaller than you expected, you have found a narrow door", 26, 1002, False)
     ]}
]

all_pass = True
for b in boxes:
    name = b["name"]
    bx, by, bw, bh = b["box"]
    align = b.get("align", "left")
    x_text = b.get("x_text", bx + 20)
    
    first_line_top = 9999
    last_line_bottom = -9999
    
    for text_str, fs, y_base, is_mono in b["lines"]:
        char_factor = 0.62 if is_mono else 0.60
        text_w = len(text_str) * fs * char_factor
        
        # calculate left and right bounds
        if align == "middle":
            # centered in box
            cx = bx + bw / 2
            left = cx - text_w / 2
            right = cx + text_w / 2
        else:
            left = x_text
            right = left + text_w
            
        top = y_base - 0.8 * fs
        bottom = y_base + 0.2 * fs
        
        first_line_top = min(first_line_top, top)
        last_line_bottom = max(last_line_bottom, bottom)
        
        # Check horizontal padding
        pad_left = left - bx
        pad_right = (bx + bw) - right
        
        if pad_left < 16:
            print(f"FAIL horizontal left pad in {name}: '{text_str[:30]}' pad_left={pad_left:.1f} < 16")
            all_pass = False
        if pad_right < 16:
            print(f"FAIL horizontal right pad in {name}: '{text_str[:30]}' pad_right={pad_right:.1f} < 16")
            all_pass = False

    pad_top = first_line_top - by
    pad_bottom = (by + bh) - last_line_bottom
    
    if pad_top < 16:
        print(f"FAIL top pad in {name}: pad_top={pad_top:.1f} < 16")
        all_pass = False
    if pad_bottom < 16:
        print(f"FAIL bottom pad in {name}: pad_bottom={pad_bottom:.1f} < 16")
        all_pass = False
        
    print(f"[{'PASS' if all_pass else 'FAIL'}] {name:22s} | TopPad={pad_top:4.1f}px, BotPad={pad_bottom:4.1f}px")

assert all_pass, "Some padding checks failed!"
print("\nALL BOX PADDING CHECKS PASSED >= 16px!")
