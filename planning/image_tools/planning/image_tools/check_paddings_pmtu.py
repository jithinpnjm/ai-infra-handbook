#!/usr/bin/env python3
import sys

# Define all boxes and lines to verify padding >= 16px
# Format: {"name": str, "box": (x, y, w, h), "lines": [(text, font_size, y_baseline, x, align, is_mono)]}

items = [
    # Title inside canvas margin (40, 0, 1520, 150)
    {
        "name": "Title",
        "box": (40, 0, 1520, 160),
        "lines": [
            ("Fixing a PMTU black hole: four options", 48, 75, 800, "middle", False),
            ("and the ping arithmetic that finds it", 48, 129, 800, "middle", False),
        ]
    },
    # Left Card 1
    {
        "name": "Left Card 1 (allow ICMP)",
        "box": (60, 246, 700, 96),
        "lines": [
            ("1 allow the required ICMP messages", 24, 274, 80, "left", False),
            ("(IPv4 type 3 code 4 Fragmentation Needed,", 24, 302, 80, "left", False),
            ("IPv6 type 2 Packet Too Big)", 24, 330, 80, "left", False),
        ]
    },
    # Left Card 2
    {
        "name": "Left Card 2 (clamp MSS)",
        "box": (60, 352, 700, 126),
        "lines": [
            ("2 clamp the TCP MSS on tunnels:", 24, 380, 80, "left", False),
            ("iptables -t mangle -A FORWARD", 24, 408, 80, "left", True),
            ("-p tcp --tcp-flags SYN,RST SYN", 24, 436, 80, "left", True),
            ("-j TCPMSS --clamp-mss-to-pmtu", 24, 464, 80, "left", True),
        ]
    },
    # Left Card 3
    {
        "name": "Left Card 3 (consistent MTU)",
        "box": (60, 488, 700, 66),
        "lines": [
            ("3 use a consistent MTU across the path", 24, 530, 80, "left", False),
        ]
    },
    # Left Card 4
    {
        "name": "Left Card 4 (PLPMTUD)",
        "box": (60, 564, 700, 82),
        "lines": [
            ("4 enable PLPMTUD with", 24, 596, 80, "left", False),
            ("net.ipv4.tcp_mtu_probing", 24, 626, 80, "left", True),
        ]
    },
    # Left Panel Title
    {
        "name": "Left Panel Title",
        "box": (40, 160, 740, 80),
        "lines": [
            ("Four ways to fix a black hole", 30, 214, 135, "left", False),
        ]
    },
    # Right Panel Title
    {
        "name": "Right Panel Title",
        "box": (820, 160, 740, 80),
        "lines": [
            ("Ping sizes add up to 1500", 30, 214, 915, "left", False),
        ]
    },
    # Right Card 1 (IPv4 Ping)
    {
        "name": "Right Card 1 (IPv4 Ping)",
        "box": (840, 246, 700, 110),
        "lines": [
            ("payload 1472 + ICMP 8 + IPv4 20 = 1500", 24, 316, 860, "left", False),
            ("(ping -M do -s 1472)", 24, 344, 860, "left", True),
        ]
    },
    # Right Card 2 (IPv6 Ping)
    {
        "name": "Right Card 2 (IPv6 Ping)",
        "box": (840, 366, 700, 110),
        "lines": [
            ("payload 1452 + ICMP 8 + IPv6 40 = 1500", 24, 436, 860, "left", False),
            ("(ping -6 -M do -s 1452)", 24, 464, 860, "left", True),
        ]
    },
    # Right Card 3 (MSS at MTU 1500)
    {
        "name": "Right Card 3 (MSS at MTU 1500)",
        "box": (840, 486, 700, 160),
        "lines": [
            ("MSS at MTU 1500:", 24, 522, 860, "left", False),
            ("IPv4 1500 - 20 - 20 = 1460;", 24, 556, 860, "left", False),
            ("IPv6 1500 - 40 - 20 = 1440", 24, 590, 860, "left", False),
        ]
    },
    # Fragmentation costs box
    {
        "name": "Fragmentation costs box",
        "box": (40, 680, 1520, 150),
        "lines": [
            ("Fragmentation costs: each fragment carries an ID,", 24, 718, 140, "left", False),
            ("an offset in 8-byte units and the MF flag;", 24, 746, 140, "left", False),
            ("lose one fragment and you lose the whole packet; firewalls often drop fragments;", 24, 774, 140, "left", False),
            ("some hardware paths send them to the CPU", 24, 802, 140, "left", False),
        ]
    },
    # Bottom Strip (commands)
    {
        "name": "Bottom Strip (commands)",
        "box": (40, 850, 1520, 84),
        "lines": [
            ("tracepath target, ip route get target,", 24, 885, 135, "left", True),
            ("ss -ti dst target | grep mss pmtu: find the narrow door", 24, 913, 135, "left", True),
        ]
    },
    # Bottom Bar (takeaway)
    {
        "name": "Bottom Bar (takeaway)",
        "box": (40, 954, 1520, 76),
        "lines": [
            ("If the largest working size is smaller than you expected, you have found a narrow door", 26, 1002, 800, "middle", False),
        ]
    }
]

all_passed = True

print(f"{'Item':<32} | {'Left':>6} | {'Right':>6} | {'Top':>6} | {'Bottom':>6} | Result")
print("-" * 75)

for it in items:
    bx, by, bw, bh = it["box"]
    for text, fs, y_base, x_pos, align, is_mono in it["lines"]:
        char_factor = 0.62 if is_mono else 0.6
        text_w = len(text) * fs * char_factor
        
        if align == "middle":
            x_left = x_pos - text_w / 2
            x_right = x_pos + text_w / 2
        else:
            x_left = x_pos
            x_right = x_pos + text_w
            
        y_top = y_base - 0.8 * fs
        y_bottom = y_base + 0.2 * fs
        
        pad_left = x_left - bx
        pad_right = (bx + bw) - x_right
        pad_top = y_top - by
        pad_bottom = (by + bh) - y_bottom
        
        ok = min(pad_left, pad_right, pad_top, pad_bottom) >= 16.0
        if not ok:
            all_passed = False
        status = "PASS" if ok else "FAIL"
        print(f"{it['name'][:32]:<32} | {pad_left:6.1f} | {pad_right:6.1f} | {pad_top:6.1f} | {pad_bottom:6.1f} | {status} ({text[:20]}...)")

assert all_passed, "Some text lines failed padding >= 16px check!"
print("\nALL TEXT LINES WITHIN PADDING >= 16px! (STRICT PASS)")
