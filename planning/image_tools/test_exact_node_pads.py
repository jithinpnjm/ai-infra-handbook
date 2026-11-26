#!/usr/bin/env python3
import xml.etree.ElementTree as ET

def test_paddings():
    tree = ET.parse("candidate.svg")
    root = tree.getroot()

    # Define all boxes: name -> (x1, y1, x2, y2)
    boxes = {
        "panel-1": (40, 95, 780, 595),
        "p1-node1": (80, 180, 740, 226),
        "p1-node2": (80, 248, 740, 294),
        "p1-node3": (80, 316, 740, 362),
        "p1-node4": (80, 384, 740, 430),
        "p1-note": (80, 450, 740, 570),
        "panel-2": (820, 95, 1560, 595),
        "p2-card1": (860, 180, 1520, 226),
        "p2-card2": (860, 238, 1520, 312),
        "p2-card3": (860, 324, 1520, 398),
        "p2-card4": (860, 410, 1520, 458),
        "p2-card5": (860, 470, 1520, 570),
        "bottom-strip": (40, 625, 1560, 875),
        "cmd1": (40, 905, 460, 1000),
        "cmd2": (480, 905, 960, 1000),
        "cmd3": (980, 905, 1560, 1000),
        "bottom-bar": (40, 1030, 1560, 1105)
    }

    print("Checking text paddings against boxes...")
    # List of checks: (box_key, text, font_size, is_mono, anchor, x_pos, y_pos)
    checks = [
        # Title in panel 1:
        ("panel-1", "Bridge-based CNI", 30, False, "start", 135, 132),
        ("panel-1", "(bridge, Flannel host-gw)", 30, False, "start", 135, 164),
        # P1 nodes (centered at 410, box 80..740)
        ("p1-node1", "pod A eth0 (a veth)", 24, False, "middle", 410, 211),
        ("p1-node2", "host-side vethXXX on bridge cni0", 24, False, "middle", 410, 279),
        ("p1-node3", "pod B's veth", 24, False, "middle", 410, 347),
        ("p1-node4", "pod B", 24, False, "middle", 410, 415),
        # P1 note (centered at 410, box 80..740)
        ("p1-note", "the node's pod CIDR such as", 24, False, "middle", 410, 486),
        ("p1-note", "10.244.1.0/24 is local and the", 24, False, "middle", 410, 518),
        ("p1-note", "bridge IP is the gateway", 24, False, "middle", 410, 550),
        # Panel 2 title (start at 915, box 820..1560)
        ("panel-2", "Routed CNI (Calico)", 30, False, "start", 915, 148),
        # P2 cards (centered at 1190, box 860..1520)
        ("p2-card1", "no bridge", 24, False, "middle", 1190, 211),
        ("p2-card2", "each pod gets a /32 route on the host,", 24, False, "middle", 1190, 268),
        ("p2-card2", "such as 10.244.1.5 dev caliXXXX scope link", 24, False, "middle", 1190, 298),
        ("p2-card3", "proxy ARP answers the pod's ARP request", 24, False, "middle", 1190, 354),
        ("p2-card3", "for its default gateway at 169.254.1.1", 24, False, "middle", 1190, 384),
        ("p2-card4", "pod, veth, host routing, veth, pod", 24, False, "middle", 1190, 442),
        ("p2-card5", "pod default route via 169.254.1.1", 24, False, "middle", 1190, 500),
        ("p2-card5", "dev eth0 onlink;", 24, False, "middle", 1190, 530),
        ("p2-card5", "proxy_arp on the host-side veths", 24, False, "middle", 1190, 560),
        # Bottom strip (centered at 800, box 40..1560)
        ("bottom-strip", "Cross-node: overlay (VXLAN, IPIP, Geneve) wraps the packet in an outer packet", 24, False, "middle", 800, 660),
        ("bottom-strip", "addressed to the other node: a route such as 10.244.2.0/24 via flannel.1, tunl0 or", 24, False, "middle", 800, 692),
        ("bottom-strip", "vxlan.calico, encapsulated in UDP or IP-in-IP; costs: MTU, CPU, pod IPs the fabric", 24, False, "middle", 800, 724),
        ("bottom-strip", "cannot see. Routed: node 1 holds 10.244.2.0/24 via <node2 IP> (static config, BIRD", 24, False, "middle", 800, 756),
        ("bottom-strip", "or the CNI daemon); needs L2 adjacency for host-gw, or a fabric learning pod", 24, False, "middle", 800, 788),
        ("bottom-strip", "prefixes over BGP; best performance, pod IPs visible in the fabric for firewalling", 24, False, "middle", 800, 820),
        ("bottom-strip", "and monitoring. Cloud-native: pod IPs come from the VPC subnet", 24, False, "middle", 800, 852),
        # Debug commands
        ("cmd1", "ip route | grep 10.244", 24, True, "middle", 250, 960),
        ("cmd2", "bridge fdb show dev flannel.1", 24, True, "middle", 720, 960),
        ("cmd3", "tcpdump -ni eth0 udp port 8472", 24, True, "middle", 1270, 945),
        ("cmd3", "(Flannel, Cilium VXLAN) or 4789", 24, True, "middle", 1270, 977),
        # Bottom bar
        ("bottom-bar", "Same pod to pod result, two different data paths", 24, False, "middle", 800, 1076)
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

        # vertical padding (approximate text ascent/descent: ascent ~ 0.8 * fs, descent ~ 0.2 * fs)
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

test_paddings()
