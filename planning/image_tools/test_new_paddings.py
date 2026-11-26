#!/usr/bin/env python3

def test_complete_paddings():
    # Boxes:
    boxes = {
        "panel-1": (40, 90, 780, 675),
        "p1-node1": (80, 190, 740, 250),
        "p1-node2": (80, 272, 740, 332),
        "p1-node3": (80, 354, 740, 414),
        "p1-node4": (80, 436, 740, 496),
        "p1-note": (80, 516, 740, 646),
        "panel-2": (820, 90, 1560, 675),
        "p2-card1": (860, 185, 1520, 245),
        "p2-card2": (860, 259, 1520, 349),
        "p2-card3": (860, 363, 1520, 453),
        "p2-card4": (860, 467, 1520, 527),
        "p2-card5": (860, 541, 1520, 661),
        "bottom-strip": (40, 700, 1560, 950),
        "cmd1": (40, 970, 460, 1060),
        "cmd2": (480, 970, 960, 1060),
        "cmd3": (980, 970, 1560, 1060),
        "bottom-bar": (40, 1080, 1560, 1150)
    }

    checks = [
        # Panel 1 header
        ("panel-1", "Bridge-based CNI", 30, False, "start", 135, 134),
        ("panel-1", "(bridge, Flannel host-gw)", 30, False, "start", 135, 168),
        # P1 nodes
        ("p1-node1", "pod A eth0 (a veth)", 24, False, "middle", 410, 226),
        ("p1-node2", "host-side vethXXX on bridge cni0", 24, False, "middle", 410, 308),
        ("p1-node3", "pod B's veth", 24, False, "middle", 410, 390),
        ("p1-node4", "pod B", 24, False, "middle", 410, 472),
        # P1 note
        ("p1-note", "the node's pod CIDR such as", 24, False, "middle", 410, 554),
        ("p1-note", "10.244.1.0/24 is local and the", 24, False, "middle", 410, 584),
        ("p1-note", "bridge IP is the gateway", 24, False, "middle", 410, 614),
        # Panel 2 header
        ("panel-2", "Routed CNI (Calico)", 30, False, "start", 915, 145),
        # P2 cards
        ("p2-card1", "no bridge", 24, False, "middle", 1190, 221),
        ("p2-card2", "each pod gets a /32 route on the host,", 24, False, "middle", 1190, 296),
        ("p2-card2", "such as 10.244.1.5 dev caliXXXX scope link", 24, False, "middle", 1190, 326),
        ("p2-card3", "proxy ARP answers the pod's ARP request", 24, False, "middle", 1190, 400),
        ("p2-card3", "for its default gateway at 169.254.1.1", 24, False, "middle", 1190, 430),
        ("p2-card4", "pod, veth, host routing, veth, pod", 24, False, "middle", 1190, 503),
        ("p2-card5", "pod default route via 169.254.1.1", 24, False, "middle", 1190, 578),
        ("p2-card5", "dev eth0 onlink;", 24, False, "middle", 1190, 608),
        ("p2-card5", "proxy_arp on the host-side veths", 24, False, "middle", 1190, 638),
        # Bottom strip
        ("bottom-strip", "Cross-node: overlay (VXLAN, IPIP, Geneve) wraps the packet in an outer packet", 24, False, "middle", 800, 738),
        ("bottom-strip", "addressed to the other node: a route such as 10.244.2.0/24 via flannel.1, tunl0 or", 24, False, "middle", 800, 768),
        ("bottom-strip", "vxlan.calico, encapsulated in UDP or IP-in-IP; costs: MTU, CPU, pod IPs the fabric", 24, False, "middle", 800, 798),
        ("bottom-strip", "cannot see. Routed: node 1 holds 10.244.2.0/24 via <node2 IP> (static config, BIRD", 24, False, "middle", 800, 828),
        ("bottom-strip", "or the CNI daemon); needs L2 adjacency for host-gw, or a fabric learning pod", 24, False, "middle", 800, 858),
        ("bottom-strip", "prefixes over BGP; best performance, pod IPs visible in the fabric for firewalling", 24, False, "middle", 800, 888),
        ("bottom-strip", "and monitoring. Cloud-native: pod IPs come from the VPC subnet", 24, False, "middle", 800, 918),
        # Debug commands
        ("cmd1", "ip route | grep 10.244", 24, True, "middle", 250, 1020),
        ("cmd2", "bridge fdb show dev flannel.1", 24, True, "middle", 720, 1020),
        ("cmd3", "tcpdump -ni eth0 udp port 8472", 24, True, "middle", 1270, 1006),
        ("cmd3", "(Flannel, Cilium VXLAN) or 4789", 24, True, "middle", 1270, 1036),
        # Bottom bar
        ("bottom-bar", "Same pod to pod result, two different data paths", 24, False, "middle", 800, 1121)
    ]

    all_passed = True
    for box_name, text, fs, is_mono, anchor, x_pos, y_pos in checks:
        bx1, by1, bx2, by2 = boxes[box_name]
        factor = 0.62 if is_mono else 0.60
        w = len(text) * factor * fs
        if anchor == "middle":
            x_left = x_pos - w / 2
            x_right = x_pos + w / 2
        else: # start
            x_left = x_pos
            x_right = x_pos + w

        pad_left = x_left - bx1
        pad_right = bx2 - x_right

        top = y_pos - 0.8 * fs
        bottom = y_pos + 0.2 * fs
        pad_top = top - by1
        pad_bottom = by2 - bottom

        min_pad = min(pad_left, pad_right, pad_top, pad_bottom)
        status = "PASS" if min_pad >= 16 else "FAIL"
        if status == "FAIL":
            all_passed = False
        print(f"[{status}] '{text[:35]}...' in {box_name}: w={w:5.1f} | pad_l={pad_left:4.1f}, pad_r={pad_right:4.1f}, pad_t={pad_top:4.1f}, pad_b={pad_bottom:4.1f} | min={min_pad:4.1f}")

    assert all_passed, "Some padding checks failed!"
    print("\nALL PADDING CHECKS PASSED (min_pad >= 16px everywhere)!")

test_complete_paddings()
