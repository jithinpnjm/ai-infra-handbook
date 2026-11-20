def check_text_fit(name, box_w, box_h, lines, font_sizes, font_types, icon_w=0):
    avail_w = box_w - icon_w - 32 # 16px padding on each side minimum
    print(f"Checking {name}: box {box_w}x{box_h}, avail_w={avail_w}")
    for line, sz, t in zip(lines, font_sizes, font_types):
        rate = 0.62 if t == "mono" else 0.6
        w = len(line) * sz * rate
        fits = w <= avail_w
        print(f"  [{fits}] '{line}' len={len(line)} w={w:.1f}px (avail {avail_w}px)")
        if not fits:
            print(f"    ERROR: overflow in {name}!")

# D1, D2, D3 have icon centered on top, so full box width is available minus padding
box_w_D = 460
check_text_fit("D1", box_w_D, 260, 
               ["Missing/incorrect", "SNAT/masquerade rule", "(wrong -o, -s); rule order"],
               [24, 24, 24], ["sans", "sans", "mono"], icon_w=0)

check_text_fit("D2", box_w_D, 260, 
               ["Upstream routing/filtering;", "asymmetric path;", "wrong outside IP"],
               [24, 24, 24], ["sans", "sans", "sans"], icon_w=0)

check_text_fit("D3", box_w_D, 260, 
               ["conntrack drop", "(table full, timeouts),", "rp_filter, FORWARD rules"],
               [24, 24, 24], ["mono", "sans", "mono"], icon_w=0)

# Edge labels
print("\nEdge labels:")
labels = [
    ("no", 24),
    ("yes", 24),
    ("source still private", 24),
    ("translated, no reply", 24),
    ("reply arrives, not delivered", 24)
]
for lbl, sz in labels:
    w = len(lbl) * sz * 0.6
    print(f"'{lbl}': w={w:.1f}px (badge width should be >= {w + 32:.1f}px)")


print("\nLeft and right boxes (width=680, icon_w=80):")
check_text_fit("X", 680, 100, ["Inside host cannot reach Internet"], [30], ["sans"], icon_w=80)
check_text_fit("A", 680, 100, ["Has IP, gateway, DNS?", "(DHCP / static)"], [30, 24], ["sans", "sans"], icon_w=80)
check_text_fit("A1", 680, 100, ["DHCP: tcpdump 67/68, relay,", "pool, VLAN, rogue server"], [26, 24], ["mono", "sans"], icon_w=80)
check_text_fit("B", 680, 100, ["ping gateway ok?"], [30], ["sans"], icon_w=80)
check_text_fit("B1", 680, 100, ["L2/ARP problems (chapter 2.3)"], [28], ["sans"], icon_w=80)
check_text_fit("C", 680, 100, ["Gateway forwards?", "ip_forward, FORWARD policy"], [30, 24], ["sans", "mono"], icon_w=80)
check_text_fit("C1", 680, 100, ["Enable forwarding;", "allow in FORWARD chain"], [28, 24], ["sans", "mono"], icon_w=80)
check_text_fit("D", 700, 100, ["tcpdump on outside iface:", "source translated?"], [26, 30], ["mono", "sans"], icon_w=80)

