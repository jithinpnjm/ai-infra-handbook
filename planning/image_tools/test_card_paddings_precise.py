import xml.etree.ElementTree as ET

# Check each card's box boundaries and text boundaries:
# Rule:
# "Estimate widths conservatively: sans 0.6 x font-size per character, monospace 0.62 x font-size per character. Every text line must fit inside its box with at least 16 px padding. Never let text touch or cross a box edge, an icon or an arrow."

# Let's inspect each card:
# Col 1: x in [40, 520], width 480
# Col 2: x in [560, 1040], width 480
# Col 3: x in [1080, 1560], width 480

cards = [
    {
        "name": "Card 1: Asymmetric paths",
        "box": (40, 110, 480, 430), # x, y, w, h
        "icon": (252, 130, 56, 56),
        "title": ("Asymmetric paths", 280, 222, 30, False),
        "body_lines": [
            ("traceroute shows only the", 280, 274, 24, False),
            ("forward path; the return", 280, 308, 24, False),
            ("path can differ and the round", 280, 342, 24, False),
            ("trip includes it; run mtr", 280, 376, 24, False),
            ("from both ends", 280, 410, 24, False)
        ]
    },
    {
        "name": "Centre small drawing",
        "box": (560, 110, 480, 430),
        "fwd_label": ("forward path (shown)", 800, 176, 24, False),
        "fwd_arrow": (648, 226, 952, 226),
        "ret_arrow": (952, 344, 648, 344),
        "ret_label": ("return path (not shown)", 800, 420, 24, False)
    },
    {
        "name": "Card 3: MPLS and tunnels",
        "box": (1080, 110, 480, 430),
        "icon": (1292, 130, 56, 56),
        "title": ("MPLS and tunnels", 1320, 222, 30, False),
        "body_lines": [
            ("hops can be hidden when", 1320, 294, 24, False),
            ("the TTL is not propagated,", 1320, 332, 24, False),
            ("or label stacks shown", 1320, 370, 24, False)
        ]
    },
    {
        "name": "Card 2: ECMP and load balancers",
        "box": (40, 580, 480, 470),
        "icon": (252, 598, 56, 56),
        "title": ("ECMP and load balancers", 280, 688, 30, False),
        "body_lines": [
            ("different probes may take", 280, 734, 24, False),
            ("different equal-cost paths,", 280, 766, 24, False),
            ("so you see hops from several", 280, 798, 24, False),
            ("routers or inconsistent", 280, 830, 24, False),
            ("paths; flow-aware tools keep", 280, 862, 24, False),
            ("the 5-tuple constant:", 280, 894, 24, False),
            ("paris-traceroute,", 280, 926, 24, True),
            ("dublin-traceroute, or mtr", 280, 958, 24, True),
            ("with fixed ports", 280, 990, 24, False)
        ]
    },
    {
        "name": "Card 5: Probes are small, 60 bytes each",
        "box": (560, 580, 480, 470),
        "icon": (772, 598, 56, 56),
        "title_lines": [
            ("Probes are small,", 800, 682, 30, False),
            ("60 bytes each", 800, 718, 30, False)
        ],
        "body_lines": [
            ("problems that affect only", 800, 776, 24, False),
            ("large packets, such as MTU", 800, 812, 24, False),
            ("problems, will not show", 800, 848, 24, False),
            ("up; use tracepath or", 800, 884, 24, False),
            ("ping -M do -s", 800, 920, 24, True)
        ]
    },
    {
        "name": "Card 4: NAT and cloud networks",
        "box": (1080, 580, 480, 470),
        "icon": (1292, 598, 56, 56),
        "title": ("NAT and cloud networks", 1320, 688, 30, False),
        "body_lines": [
            ("virtual routers do not", 1320, 744, 24, False),
            ("decrement the TTL or", 1320, 780, 24, False),
            ("respond, so a cloud VPC", 1320, 816, 24, False),
            ("trace typically shows only", 1320, 852, 24, False),
            ("the first and last hops", 1320, 888, 24, False)
        ]
    }
]

for c in cards:
    print(f"\n--- Checking {c['name']} ---")
    bx, by, bw, bh = c["box"]
    print(f"Box: x=[{bx}, {bx+bw}], y=[{by}, {by+bh}]")
    
    # Check lines
    all_lines = []
    if "title" in c:
        all_lines.append(c["title"])
    if "title_lines" in c:
        all_lines.extend(c["title_lines"])
    if "body_lines" in c:
        all_lines.extend(c["body_lines"])
    if "fwd_label" in c:
        all_lines.append(c["fwd_label"])
    if "ret_label" in c:
        all_lines.append(c["ret_label"])
        
    for txt, cx, cy, fs, mono in all_lines:
        ch_w = 0.62 * fs if mono else 0.6 * fs
        w = len(txt) * ch_w
        left = cx - w / 2
        right = cx + w / 2
        pad_l = left - bx
        pad_r = (bx + bw) - right
        pad_t = (cy - fs) - by
        pad_b = (by + bh) - cy
        
        ok = (pad_l >= 16 and pad_r >= 16 and pad_t >= 16 and pad_b >= 16)
        print(f"  [{'OK' if ok else 'FAIL'}] pad_l={pad_l:.1f}, pad_r={pad_r:.1f}, pad_t={pad_t:.1f}, pad_b={pad_b:.1f} | '{txt}'")
        assert ok, f"Padding violation in '{txt}'!"

print("\nALL PADDING CHECKS PASSED WITH >= 16PX PADDING EVERYWHERE!")
