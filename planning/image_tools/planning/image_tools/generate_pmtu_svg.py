#!/usr/bin/env python3

def build_svg():
    canvas_w = 1600
    canvas_h = 1120
    
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {canvas_w} {canvas_h}" width="{canvas_w}" height="{canvas_h}">')
    svg.append('  <title>Fixing a PMTU black hole: four options and the ping arithmetic that finds it</title>')
    svg.append('  <desc>Fixing a PMTU black hole: four options and the ping arithmetic that finds it</desc>')
    
    # Background
    svg.append(f'  <rect x="0" y="0" width="{canvas_w}" height="{canvas_h}" fill="#f5f8f5"/>')
    
    # Title (48px bold, 2 lines, centered at x=800)
    svg.append('  <!-- Title -->')
    svg.append('  <text x="800" y="68" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36" text-anchor="middle">')
    svg.append('    <tspan x="800" dy="0">Fixing a PMTU black hole: four options </tspan>')
    svg.append('    <tspan x="800" dy="54">and the ping arithmetic that finds it</tspan>')
    svg.append('  </text>')
    
    # LEFT PANEL
    svg.append('  <!-- Left Panel: Four ways to fix a black hole -->')
    svg.append('  <rect x="40" y="160" width="740" height="554" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
    
    # Left Header Icon (Shield / Security check)
    svg.append('  <g stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <path d="M 70 190 L 95 180 L 120 190 C 120 215 95 235 95 235 C 95 235 70 215 70 190 Z"/>')
    svg.append('    <path d="M 83 205 L 92 214 L 108 198"/>')
    svg.append('  </g>')
    
    # Left Header Title
    svg.append('  <text x="135" y="212" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Four ways to fix a black hole</text>')
    
    # Left Card 1 (allow ICMP)
    svg.append('  <rect x="60" y="244" width="700" height="118" rx="8" fill="#ffffff" stroke="#c5decb" stroke-width="1.5"/>')
    svg.append('  <text x="80" y="282" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="80" dy="0">1 allow the required ICMP messages </tspan>')
    svg.append('    <tspan x="80" dy="28">(IPv4 type 3 code 4 Fragmentation Needed, </tspan>')
    svg.append('    <tspan x="80" dy="28">IPv6 type 2 Packet Too Big)</tspan>')
    svg.append('  </text>')
    
    # Left Card 2 (clamp MSS)
    svg.append('  <rect x="60" y="376" width="700" height="144" rx="8" fill="#ffffff" stroke="#c5decb" stroke-width="1.5"/>')
    svg.append('  <text x="80" y="414" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="80" dy="0" font-weight="bold">2 clamp the TCP MSS on tunnels: </tspan>')
    svg.append('    <tspan x="80" dy="28" font-family="monospace">iptables -t mangle -A FORWARD </tspan>')
    svg.append('    <tspan x="80" dy="28" font-family="monospace">-p tcp --tcp-flags SYN,RST SYN </tspan>')
    svg.append('    <tspan x="80" dy="28" font-family="monospace">-j TCPMSS --clamp-mss-to-pmtu</tspan>')
    svg.append('  </text>')
    
    # Left Card 3 (consistent MTU)
    svg.append('  <rect x="60" y="532" width="700" height="60" rx="8" fill="#ffffff" stroke="#c5decb" stroke-width="1.5"/>')
    svg.append('  <text x="80" y="570" font-family="sans-serif" font-size="24" fill="#303a36">3 use a consistent MTU across the path</text>')
    
    # Left Card 4 (PLPMTUD)
    svg.append('  <rect x="60" y="604" width="700" height="92" rx="8" fill="#ffffff" stroke="#c5decb" stroke-width="1.5"/>')
    svg.append('  <text x="80" y="642" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="80" dy="0">4 enable PLPMTUD with </tspan>')
    svg.append('    <tspan x="80" dy="28" font-family="monospace">net.ipv4.tcp_mtu_probing</tspan>')
    svg.append('  </text>')

    # RIGHT PANEL
    svg.append('  <!-- Right Panel: Ping sizes add up to 1500 -->')
    svg.append('  <rect x="820" y="160" width="740" height="554" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
    
    # Right Header Icon (Packet / Ping Gauge)
    svg.append('  <g stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <rect x="845" y="186" width="50" height="40" rx="6"/>')
    svg.append('    <line x1="845" y1="202" x2="895" y2="202" stroke-width="3"/>')
    svg.append('    <circle cx="862" cy="216" r="4" fill="#207448"/>')
    svg.append('    <circle cx="878" cy="216" r="4" fill="#207448"/>')
    svg.append('  </g>')
    
    # Right Header Title
    svg.append('  <text x="915" y="212" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Ping sizes add up to 1500</text>')
    
    # Right Card 1 (IPv4 Bar)
    svg.append('  <rect x="840" y="244" width="700" height="126" rx="8" fill="#ffffff" stroke="#c5decb" stroke-width="1.5"/>')
    # Segmented Bar for IPv4
    svg.append('  <g transform="translate(860, 260)">')
    svg.append('    <rect x="0" y="0" width="50" height="20" rx="3" fill="#c5decb" stroke="#207448" stroke-width="1.5"/>')
    svg.append('    <rect x="54" y="0" width="30" height="20" rx="3" fill="#a3caa9" stroke="#207448" stroke-width="1.5"/>')
    svg.append('    <rect x="88" y="0" width="572" height="20" rx="3" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>')
    svg.append('  </g>')
    svg.append('  <text x="860" y="320" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="860" dy="0" font-weight="bold">payload 1472 + ICMP 8 + IPv4 20 = 1500 </tspan>')
    svg.append('    <tspan x="860" dy="28" font-family="monospace">(ping -M do -s 1472)</tspan>')
    svg.append('  </text>')
    
    # Right Card 2 (IPv6 Bar)
    svg.append('  <rect x="840" y="384" width="700" height="126" rx="8" fill="#ffffff" stroke="#c5decb" stroke-width="1.5"/>')
    # Segmented Bar for IPv6
    svg.append('  <g transform="translate(860, 400)">')
    svg.append('    <rect x="0" y="0" width="70" height="20" rx="3" fill="#c5decb" stroke="#207448" stroke-width="1.5"/>')
    svg.append('    <rect x="74" y="0" width="30" height="20" rx="3" fill="#a3caa9" stroke="#207448" stroke-width="1.5"/>')
    svg.append('    <rect x="108" y="0" width="552" height="20" rx="3" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>')
    svg.append('  </g>')
    svg.append('  <text x="860" y="460" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="860" dy="0" font-weight="bold">payload 1452 + ICMP 8 + IPv6 40 = 1500 </tspan>')
    svg.append('    <tspan x="860" dy="28" font-family="monospace">(ping -6 -M do -s 1452)</tspan>')
    svg.append('  </text>')
    
    # Right Card 3 (MSS at MTU 1500)
    svg.append('  <rect x="840" y="524" width="700" height="172" rx="8" fill="#ffffff" stroke="#c5decb" stroke-width="1.5"/>')
    svg.append('  <text x="860" y="562" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="860" dy="0" font-weight="bold">MSS at MTU 1500: </tspan>')
    svg.append('    <tspan x="860" dy="32">IPv4 1500 - 20 - 20 = 1460; </tspan>')
    svg.append('    <tspan x="860" dy="32">IPv6 1500 - 40 - 20 = </tspan><tspan fill="#db8129" font-weight="bold">1440</tspan>')
    svg.append('  </text>')

    # BELOW: Fragmentation costs
    svg.append('  <!-- Below: Fragmentation costs -->')
    svg.append('  <rect x="40" y="734" width="1520" height="146" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
    # CPU chip icon
    svg.append('  <g stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <rect x="66" y="780" width="46" height="46" rx="4"/>')
    svg.append('    <line x1="77" y1="770" x2="77" y2="780" stroke-width="3"/>')
    svg.append('    <line x1="101" y1="770" x2="101" y2="780" stroke-width="3"/>')
    svg.append('    <line x1="77" y1="826" x2="77" y2="836" stroke-width="3"/>')
    svg.append('    <line x1="101" y1="826" x2="101" y2="836" stroke-width="3"/>')
    svg.append('    <line x1="56" y1="793" x2="66" y2="793" stroke-width="3"/>')
    svg.append('    <line x1="56" y1="813" x2="66" y2="813" stroke-width="3"/>')
    svg.append('    <line x1="112" y1="793" x2="122" y2="793" stroke-width="3"/>')
    svg.append('    <line x1="112" y1="813" x2="122" y2="813" stroke-width="3"/>')
    svg.append('    <circle cx="89" cy="803" r="7" stroke-width="2.5"/>')
    svg.append('  </g>')
    svg.append('  <text x="140" y="772" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="140" dy="0" font-weight="bold">Fragmentation costs: each fragment carries an ID, </tspan>')
    svg.append('    <tspan x="140" dy="28">an offset in 8-byte units and the MF flag; </tspan>')
    svg.append('    <tspan x="140" dy="28">lose one fragment and you lose the whole packet; firewalls often drop fragments; </tspan>')
    svg.append('    <tspan x="140" dy="28">some hardware paths send them to the CPU</tspan>')
    svg.append('  </text>')

    # BOTTOM STRIP: tracepath target...
    svg.append('  <!-- Bottom Strip -->')
    svg.append('  <rect x="40" y="900" width="1520" height="92" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    # Terminal icon
    svg.append('  <g stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <rect x="66" y="924" width="48" height="42" rx="4"/>')
    svg.append('    <path d="M 76 938 L 84 945 L 76 952"/>')
    svg.append('    <line x1="88" y1="952" x2="98" y2="952"/>')
    svg.append('  </g>')
    svg.append('  <text x="135" y="938" font-family="monospace" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="135" dy="0">tracepath target, ip route get target, </tspan>')
    svg.append('    <tspan x="135" dy="30">ss -ti dst target | grep mss pmtu: </tspan><tspan font-family="sans-serif" font-weight="bold" fill="#207448">find the narrow door</tspan>')
    svg.append('  </text>')

    # BOTTOM BAR: Takeaway
    svg.append('  <!-- Bottom Bar: Takeaway -->')
    svg.append('  <rect x="40" y="1010" width="1520" height="70" rx="12" fill="#207448"/>')
    svg.append('  <text x="800" y="1052" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff" text-anchor="middle">')
    svg.append('    If the largest working size is smaller than you expected, you have found a narrow door')
    svg.append('  </text>')
    
    svg.append('</svg>')
    return '\n'.join(svg)

svg_str = build_svg()
with open("test_pmtu.svg", "w") as f:
    f.write(svg_str)
print("Updated test_pmtu.svg")
