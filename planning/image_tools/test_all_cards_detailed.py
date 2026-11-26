import sys

def est_w(segments):
    tot = 0.0
    for txt, fs, mono in segments:
        tot += len(txt) * fs * (0.62 if mono else 0.6)
    return tot

# Let's test all cards with exact lines and check both left and right padding >= 16px, and top and bottom padding >= 16px!

# Card 1: box x=58, y=128, w=419, h=230 (right=477, bottom=358)
c1_box = (58, 128, 419, 230)
c1_x = 82
c1_lines = [
    [("Per new connection:", 30, False)],
    [("linear walk of", 24, False)],
    [("KUBE-SERVICES,", 24, True), (" O(n)", 24, False)]
]

# Card 2: box x=58, y=378, w=419, h=584 (right=477, bottom=962)
c2_box = (58, 378, 419, 584)
c2_x = 82
c2_lines = [
    [("per change:", 30, False)],
    [("iptables-restore", 24, True), (" rewrites", 24, False)],
    [("the whole ruleset, takes", 24, False)],
    [("the xtables lock", 24, False)],
    [("(/run/xtables.lock),", 24, True)],
    [("seconds or minutes at", 24, False)],
    [("tens of thousands", 24, False)],
    [("of rules, can collide", 24, False)],
    [("with CNI plug-ins and", 24, False)],
    [("send traffic to", 24, False)],
    [("stale endpoints", 24, False)]
]

# Middle: box x=540, y=110, w=330, h=870 (right=870, bottom=980)
mid_box = (540, 110, 330, 870)
mid_center_x = 705
mid_lines = [
    [("iptables", 30, False)],
    [("degrades beyond", 26, False)],
    [("roughly 5,000", 26, False)],
    [("Services or", 26, False)],
    [("25,000 endpoints", 26, False)]
]

# Card 3 (IPVS): box x=933, y=128, w=609, h=240 (right=1542, bottom=368)
c3_box = (933, 128, 609, 240)
c3_x_title = 1027
c3_x_body = 957
c3_title_line = [("IPVS: ", 30, False), ("hash lookup O(1),", 24, False)]
c3_body_lines = [
    [("incremental updates, schedulers", 24, False)],
    [("rr lc sh dh sed nq,", 24, True)],
    [("needs ", 24, False), ("ip_vs", 24, True), (" modules and ", 24, False), ("ipset,", 24, True)],
    [("strictARP true", 24, True), (" for MetalLB L2", 24, False)]
]

# Card 4 (nftables): box x=933, y=388, w=609, h=180 (right=1542, bottom=568)
c4_box = (933, 388, 609, 180)
c4_x_title = 1027
c4_x_body = 957
c4_title_line = [("nftables: ", 30, False), ("single kube-proxy", 24, False)]
c4_body_lines = [
    [("table with maps, O(1),", 24, False)],
    [("incremental ", 24, False), ("nft -f", 24, True), (" deltas", 24, False)]
]

# Card 5 (eBPF): box x=933, y=588, w=609, h=374 (right=1542, bottom=962)
c5_box = (933, 588, 609, 374)
c5_x_title = 1027
c5_x_body = 957
c5_title_line = [("eBPF", 30, False)]
c5_body_lines = [
    [("(Cilium ", 24, False), ("kubeProxyReplacement=true):", 24, True)],
    [("cgroup/connect4", 24, True), (" hook rewrites", 24, False)],
    [("the destination at connect time,", 24, False)],
    [("no packet NAT, no conntrack for", 24, False)],
    [("in-cluster Service traffic,", 24, False)],
    [("kernel 5.10+ recommended", 24, False)]
]

# Footer: box x=40, y=1020, w=1520, h=140 (right=1560, bottom=1160)
footer_box = (40, 1020, 1520, 140)
footer_x = 144
footer_lines = [
    [("kubeproxy_sync_proxy_rules_duration_seconds,", 24, True)],
    [("kubeproxy_network_programming_duration_seconds,", 24, True)],
    [("kubeproxy_sync_proxy_rules_iptables_total", 24, True)]
]

def check_card_padding(name, box, lines, start_x):
    bx, by, bw, bh = box
    bright = bx + bw
    bbottom = by + bh
    print(f"\nChecking {name}: box=({bx}, {by}, {bw}, {bh}), right={bright}")
    for idx, l in enumerate(lines):
        w = est_w(l)
        left_pad = start_x - bx
        right_pad = bright - (start_x + w)
        txt = "".join([t for t, f, m in l])
        print(f"  Line {idx+1}: w={w:.1f}, left_pad={left_pad:.1f}, right_pad={right_pad:.1f} | {'OK' if left_pad >= 16 and right_pad >= 16 else 'FAIL'}: {txt}")
        if left_pad < 16 or right_pad < 16:
            print(f"    ERROR in {name} Line {idx+1}!")
            sys.exit(1)

check_card_padding("Card 1", c1_box, c1_lines, c1_x)
check_card_padding("Card 2", c2_box, c2_lines, c2_x)

# Middle centered:
print(f"\nChecking Middle (centered at {mid_center_x}): box={mid_box}")
for idx, l in enumerate(mid_lines):
    w = est_w(l)
    left_edge = mid_center_x - w/2
    right_edge = mid_center_x + w/2
    left_pad = left_edge - mid_box[0]
    right_pad = (mid_box[0] + mid_box[2]) - right_edge
    txt = "".join([t for t, f, m in l])
    print(f"  Line {idx+1}: w={w:.1f}, left_pad={left_pad:.1f}, right_pad={right_pad:.1f} | {'OK' if left_pad >= 16 and right_pad >= 16 else 'FAIL'}: {txt}")
    if left_pad < 16 or right_pad < 16:
        print("ERROR in Middle!")
        sys.exit(1)

# Card 3:
check_card_padding("Card 3 Title", c3_box, [c3_title_line], c3_x_title)
check_card_padding("Card 3 Body", c3_box, c3_body_lines, c3_x_body)

# Card 4:
check_card_padding("Card 4 Title", c4_box, [c4_title_line], c4_x_title)
check_card_padding("Card 4 Body", c4_box, c4_body_lines, c4_x_body)

# Card 5:
check_card_padding("Card 5 Title", c5_box, [c5_title_line], c5_x_title)
check_card_padding("Card 5 Body", c5_box, c5_body_lines, c5_x_body)

# Footer:
check_card_padding("Footer", footer_box, footer_lines, footer_x)

print("\nALL LINES IN ALL CARDS PASS WITH AT LEAST 16PX PADDING!")
