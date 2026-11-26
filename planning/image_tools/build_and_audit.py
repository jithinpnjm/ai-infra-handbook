#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

def build_svg():
    bg = "#f5f8f5"
    text_color = "#303a36"
    main_green = "#207448"
    panel_bg = "#e8f1ea"
    orange = "#db8129"
    card_bg = "#ffffff"
    card_stroke = "#207448"
    card_orange_stroke = "#db8129"
    card_orange_bg = "#fffaf5"

    svg_parts = []
    svg_parts.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">')
    svg_parts.append('  <title>Bridge CNI versus routed CNI on one node</title>')
    svg_parts.append('  <desc>Bridge CNI versus routed CNI on one node</desc>')
    svg_parts.append('  <defs>')
    svg_parts.append('    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="14" markerHeight="14" orient="auto">')
    svg_parts.append(f'      <path d="M 2 3 L 16 9 L 2 15 Z" fill="{main_green}" />')
    svg_parts.append('    </marker>')
    svg_parts.append('  </defs>')
    svg_parts.append(f'  <rect width="1600" height="1200" fill="{bg}" />')

    # Main Diagram Title (48px bold)
    svg_parts.append(f'  <text x="800" y="56" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="{text_color}">Bridge CNI versus routed CNI on one node</text>')

    # ==========================================
    # PANEL 1: Bridge-based CNI (x=40, y=90, w=740, h=585)
    # ==========================================
    svg_parts.append('  <g id="panel-1">')
    svg_parts.append(f'    <rect x="40" y="90" width="740" height="585" rx="14" fill="{panel_bg}" stroke="{main_green}" stroke-width="2" />')

    # Icon: Bridge / Switch (56x56 at 65, 115)
    svg_parts.append(f'    <g transform="translate(65, 115)" stroke="{main_green}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg_parts.append('      <rect x="2" y="6" width="52" height="34" rx="4" />')
    svg_parts.append('      <line x1="12" y1="23" x2="44" y2="23" />')
    svg_parts.append('      <circle cx="16" cy="23" r="3" fill="#207448" />')
    svg_parts.append('      <circle cx="28" cy="23" r="3" fill="#207448" />')
    svg_parts.append('      <circle cx="40" cy="23" r="3" fill="#207448" />')
    svg_parts.append('      <line x1="16" y1="26" x2="16" y2="34" />')
    svg_parts.append('      <line x1="28" y1="26" x2="28" y2="34" />')
    svg_parts.append('      <line x1="40" y1="26" x2="40" y2="34" />')
    svg_parts.append('    </g>')

    # Title: Bridge-based CNI (bridge, Flannel host-gw) (30px bold)
    svg_parts.append(f'    <text font-family="sans-serif" font-size="30" font-weight="bold" fill="{main_green}">')
    svg_parts.append('      <tspan x="135" y="134">Bridge-based CNI</tspan>')
    svg_parts.append('      <tspan x="135" y="168">(bridge, Flannel host-gw)</tspan>')
    svg_parts.append('    </text>')

    # Node 1: pod A eth0 (a veth)
    svg_parts.append(f'    <rect x="80" y="190" width="660" height="60" rx="8" fill="{card_bg}" stroke="{card_stroke}" stroke-width="2" />')
    svg_parts.append(f'    <text x="410" y="226" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="{text_color}">pod A eth0 (a veth)</text>')

    # Arrow 1 -> Node 2
    svg_parts.append(f'    <line x1="410" y1="250" x2="410" y2="270" stroke="{main_green}" stroke-width="3" marker-end="url(#arrow-green)" />')

    # Node 2: host-side vethXXX on bridge cni0
    svg_parts.append(f'    <rect x="80" y="272" width="660" height="60" rx="8" fill="{card_bg}" stroke="{card_stroke}" stroke-width="2" />')
    svg_parts.append(f'    <text x="410" y="308" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="{text_color}">host-side vethXXX on bridge cni0</text>')

    # Arrow 2 -> Node 3
    svg_parts.append(f'    <line x1="410" y1="332" x2="410" y2="352" stroke="{main_green}" stroke-width="3" marker-end="url(#arrow-green)" />')

    # Node 3: pod B\'s veth
    svg_parts.append(f'    <rect x="80" y="354" width="660" height="60" rx="8" fill="{card_bg}" stroke="{card_stroke}" stroke-width="2" />')
    svg_parts.append(f'    <text x="410" y="390" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="{text_color}">pod B\'s veth</text>')

    # Arrow 3 -> Node 4
    svg_parts.append(f'    <line x1="410" y1="414" x2="410" y2="434" stroke="{main_green}" stroke-width="3" marker-end="url(#arrow-green)" />')

    # Node 4: pod B
    svg_parts.append(f'    <rect x="80" y="436" width="660" height="60" rx="8" fill="{card_bg}" stroke="{card_stroke}" stroke-width="2" />')
    svg_parts.append(f'    <text x="410" y="472" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="{text_color}">pod B</text>')

    # Note Card: the node\'s pod CIDR such as 10.244.1.0/24 is local and the bridge IP is the gateway
    svg_parts.append(f'    <rect x="80" y="516" width="660" height="130" rx="10" fill="{card_bg}" stroke="{card_stroke}" stroke-width="2" />')
    svg_parts.append(f'    <text font-family="sans-serif" font-size="24" fill="{text_color}" text-anchor="middle">')
    svg_parts.append('      <tspan x="410" y="554">the node\'s pod CIDR such as</tspan>')
    svg_parts.append('      <tspan x="410" y="584">10.244.1.0/24 is local and the</tspan>')
    svg_parts.append('      <tspan x="410" y="614">bridge IP is the gateway</tspan>')
    svg_parts.append('    </text>')
    svg_parts.append('  </g>')

    # ==========================================
    # PANEL 2: Routed CNI (Calico) (x=820, y=90, w=740, h=585)
    # ==========================================
    svg_parts.append('  <g id="panel-2">')
    svg_parts.append(f'    <rect x="820" y="90" width="740" height="585" rx="14" fill="{panel_bg}" stroke="{orange}" stroke-width="3" />')

    # Icon: Router (56x56 at 845, 115)
    svg_parts.append(f'    <g transform="translate(845, 115)" stroke="{orange}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg_parts.append('      <circle cx="28" cy="28" r="22" />')
    svg_parts.append('      <line x1="28" y1="12" x2="28" y2="44" />')
    svg_parts.append('      <line x1="12" y1="28" x2="44" y2="28" />')
    svg_parts.append('      <polyline points="23,17 28,12 33,17" />')
    svg_parts.append('      <polyline points="23,39 28,44 33,39" />')
    svg_parts.append('      <polyline points="17,23 12,28 17,33" />')
    svg_parts.append('      <polyline points="39,23 44,28 39,33" />')
    svg_parts.append('    </g>')

    # Title: Routed CNI (Calico) (30px bold)
    svg_parts.append(f'    <text x="915" y="145" font-family="sans-serif" font-size="30" font-weight="bold" fill="{orange}">Routed CNI (Calico)</text>')

    # Card 1: no bridge
    svg_parts.append(f'    <rect x="860" y="185" width="660" height="60" rx="8" fill="{card_orange_bg}" stroke="{card_orange_stroke}" stroke-width="2" />')
    svg_parts.append(f'    <text x="1190" y="221" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="{text_color}">no bridge</text>')

    # Card 2: each pod gets a /32 route on the host, such as 10.244.1.5 dev caliXXXX scope link
    svg_parts.append(f'    <rect x="860" y="259" width="660" height="90" rx="8" fill="{card_bg}" stroke="{card_stroke}" stroke-width="2" />')
    svg_parts.append(f'    <text font-family="sans-serif" font-size="24" fill="{text_color}" text-anchor="middle">')
    svg_parts.append('      <tspan x="1190" y="296">each pod gets a /32 route on the host,</tspan>')
    svg_parts.append('      <tspan x="1190" y="326">such as 10.244.1.5 dev caliXXXX scope link</tspan>')
    svg_parts.append('    </text>')

    # Card 3: proxy ARP answers the pod\'s ARP request for its default gateway at 169.254.1.1
    svg_parts.append(f'    <rect x="860" y="363" width="660" height="90" rx="8" fill="{card_bg}" stroke="{card_stroke}" stroke-width="2" />')
    svg_parts.append(f'    <text font-family="sans-serif" font-size="24" fill="{text_color}" text-anchor="middle">')
    svg_parts.append('      <tspan x="1190" y="400">proxy ARP answers the pod\'s ARP request</tspan>')
    svg_parts.append('      <tspan x="1190" y="430">for its default gateway at 169.254.1.1</tspan>')
    svg_parts.append('    </text>')

    # Card 4: pod, veth, host routing, veth, pod
    svg_parts.append(f'    <rect x="860" y="467" width="660" height="60" rx="8" fill="{card_bg}" stroke="{card_stroke}" stroke-width="2" />')
    svg_parts.append(f'    <text x="1190" y="503" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="{text_color}">pod, veth, host routing, veth, pod</text>')

    # Card 5 (Lab line): pod default route via 169.254.1.1 dev eth0 onlink; proxy_arp on the host-side veths
    svg_parts.append(f'    <rect x="860" y="541" width="660" height="120" rx="8" fill="{card_bg}" stroke="{card_stroke}" stroke-width="2" />')
    svg_parts.append(f'    <text font-family="sans-serif" font-size="24" fill="{text_color}" text-anchor="middle">')
    svg_parts.append('      <tspan x="1190" y="578">pod default route via 169.254.1.1</tspan>')
    svg_parts.append('      <tspan x="1190" y="608">dev eth0 onlink;</tspan>')
    svg_parts.append('      <tspan x="1190" y="638">proxy_arp on the host-side veths</tspan>')
    svg_parts.append('    </text>')
    svg_parts.append('  </g>')

    # ==========================================
    # BOTTOM STRIP: Cross-node overlay vs routed (x=40, y=700, w=1520, h=250)
    # ==========================================
    svg_parts.append('  <g id="bottom-strip">')
    svg_parts.append(f'    <rect x="40" y="700" width="1520" height="250" rx="12" fill="{panel_bg}" stroke="{main_green}" stroke-width="2" />')
    svg_parts.append(f'    <text font-family="sans-serif" font-size="24" fill="{text_color}" text-anchor="middle">')
    svg_parts.append('      <tspan x="800" y="738">Cross-node: overlay (VXLAN, IPIP, Geneve) wraps the packet in an outer packet</tspan>')
    svg_parts.append('      <tspan x="800" y="768">addressed to the other node: a route such as 10.244.2.0/24 via flannel.1, tunl0 or</tspan>')
    svg_parts.append('      <tspan x="800" y="798">vxlan.calico, encapsulated in UDP or IP-in-IP; costs: MTU, CPU, pod IPs the fabric</tspan>')
    svg_parts.append('      <tspan x="800" y="828">cannot see. Routed: node 1 holds 10.244.2.0/24 via &lt;node2 IP&gt; (static config, BIRD</tspan>')
    svg_parts.append('      <tspan x="800" y="858">or the CNI daemon); needs L2 adjacency for host-gw, or a fabric learning pod</tspan>')
    svg_parts.append('      <tspan x="800" y="888">prefixes over BGP; best performance, pod IPs visible in the fabric for firewalling</tspan>')
    svg_parts.append('      <tspan x="800" y="918">and monitoring. Cloud-native: pod IPs come from the VPC subnet</tspan>')
    svg_parts.append('    </text>')
    svg_parts.append('  </g>')

    # ==========================================
    # DEBUG COMMANDS: (x=40, y=970, w=1520, h=90)
    # 3 command chips:
    # Cmd 1: x=40, w=420
    # Cmd 2: x=480, w=480
    # Cmd 3: x=980, w=580
    # ==========================================
    svg_parts.append('  <g id="debug-commands">')
    # Cmd 1
    svg_parts.append(f'    <rect x="40" y="970" width="420" height="90" rx="10" fill="{card_bg}" stroke="{card_stroke}" stroke-width="2" />')
    svg_parts.append(f'    <text x="250" y="1020" text-anchor="middle" font-family="monospace" font-size="24" fill="{text_color}">ip route | grep 10.244</text>')

    # Cmd 2
    svg_parts.append(f'    <rect x="480" y="970" width="480" height="90" rx="10" fill="{card_bg}" stroke="{card_stroke}" stroke-width="2" />')
    svg_parts.append(f'    <text x="720" y="1020" text-anchor="middle" font-family="monospace" font-size="24" fill="{text_color}">bridge fdb show dev flannel.1</text>')

    # Cmd 3
    svg_parts.append(f'    <rect x="980" y="970" width="580" height="90" rx="10" fill="{card_bg}" stroke="{card_stroke}" stroke-width="2" />')
    svg_parts.append(f'    <text font-family="monospace" font-size="24" fill="{text_color}" text-anchor="middle">')
    svg_parts.append('      <tspan x="1270" y="1006">tcpdump -ni eth0 udp port 8472</tspan>')
    svg_parts.append('      <tspan x="1270" y="1036">(Flannel, Cilium VXLAN) or 4789</tspan>')
    svg_parts.append('    </text>')
    svg_parts.append('  </g>')

    # ==========================================
    # BOTTOM BAR: Takeaway (x=40, y=1080, w=1520, h=70)
    # ==========================================
    svg_parts.append('  <g id="bottom-bar">')
    svg_parts.append(f'    <rect x="40" y="1080" width="1520" height="70" rx="12" fill="{panel_bg}" stroke="{main_green}" stroke-width="2" />')
    svg_parts.append(f'    <text x="800" y="1121" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="{main_green}">Same pod to pod result, two different data paths</text>')
    svg_parts.append('  </g>')

    svg_parts.append('</svg>')
    return "\n".join(svg_parts)

if __name__ == "__main__":
    content = build_svg()
    with open("candidate.svg", "w", encoding="utf-8") as f:
        f.write(content)
    print("Saved candidate.svg successfully!")
