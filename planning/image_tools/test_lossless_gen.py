import xml.etree.ElementTree as ET
import re

def generate_svg():
    W = 1600
    H = 1180

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
    svg.append('  <title>A lossless Ethernet class needs every piece set the same, end to end</title>')
    svg.append('  <desc>A lossless Ethernet class needs every piece set the same, end to end: network chain, checklist, failure modes, InfiniBand contrast, and rail-optimised fabric.</desc>')
    
    # Defs
    svg.append('  <defs>')
    svg.append('    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    svg.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />')
    svg.append('    </marker>')
    svg.append('    <marker id="arrow-orange" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    svg.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#db8129" />')
    svg.append('    </marker>')
    svg.append('  </defs>')

    # Background
    svg.append(f'  <rect width="{W}" height="{H}" fill="#f5f8f5" />')

    # Title (48px bold, top >= 40)
    svg.append('  <!-- 1. Title -->')
    svg.append('  <text x="40" y="88" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">')
    svg.append('    <tspan x="40" dy="0">A lossless Ethernet class needs</tspan>')
    svg.append('    <tspan x="40" dy="54">every piece set the same, end to end</tspan>')
    svg.append('  </text>')

    # -------------------------------------------------------------
    # LEFT COLUMN: x = 40 to 1020 (width = 980)
    # -------------------------------------------------------------
    
    # Container for Checklist: y = 165 to 565 (height = 400)
    svg.append('  <!-- Checklist Container -->')
    svg.append('  <rect x="40" y="165" width="980" height="400" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')

    def draw_tick(cx, cy):
        return f'<circle cx="{cx}" cy="{cy}" r="14" fill="#207448" /><path d="M {cx-6} {cy} L {cx-2} {cy+5} L {cx+7} {cy-5}" stroke="#ffffff" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round" />'

    # Checklist Item 1: y = 178, h = 68
    svg.append('  <rect x="55" y="178" width="950" height="68" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append(f'  {draw_tick(85, 212)}')
    svg.append('  <text x="115" y="206" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="115" dy="0">PFC (802.1Qbb) for the RoCE priority, on the NIC and on</tspan>')
    svg.append('    <tspan x="115" dy="28">every switch</tspan>')
    svg.append('  </text>')

    # Checklist Item 2: y = 254, h = 48
    svg.append('  <rect x="55" y="254" width="950" height="48" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append(f'  {draw_tick(85, 278)}')
    svg.append('  <text x="115" y="286" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="115" dy="0">ECN marking with DCQCN or similar rate control</tspan>')
    svg.append('  </text>')

    # Checklist Item 3: y = 310, h = 48
    svg.append('  <rect x="55" y="310" width="950" height="48" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append(f'  {draw_tick(85, 334)}')
    svg.append('  <text x="115" y="342" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="115" dy="0">DSCP and PCP trust and mapping set correctly</tspan>')
    svg.append('  </text>')

    # Checklist Item 4: y = 366, h = 68
    svg.append('  <rect x="55" y="366" width="950" height="68" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append(f'  {draw_tick(85, 400)}')
    svg.append('  <text x="115" y="394" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="115" dy="0">buffer allocation and headroom sized for each port speed</tspan>')
    svg.append('    <tspan x="115" dy="28">and cable length</tspan>')
    svg.append('  </text>')

    # Checklist Item 5: y = 442, h = 108
    svg.append('  <rect x="55" y="442" width="950" height="108" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append(f'  {draw_tick(85, 496)}')
    svg.append('  <text x="115" y="470" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="115" dy="0">per-port counters watched: CRC, FEC uncorrected, symbol</tspan>')
    svg.append('    <tspan x="115" dy="28">errors, PFC pause counts per priority, ECN-marked packets,</tspan>')
    svg.append('    <tspan x="115" dy="28">buffer occupancy, link flaps, optical power (DOM)</tspan>')
    svg.append('  </text>')

    # Horizontal chain of 5 nodes: y = 585 to 780 (height = 195)
    node_w = 150
    node_h = 195
    chain_y = 585
    node_xs = [40, 247.5, 455, 662.5, 870]

    # Node 1: NIC
    svg.append(f'  <!-- Node 1: NIC -->')
    svg.append(f'  <rect x="{node_xs[0]}" y="{chain_y}" width="{node_w}" height="{node_h}" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    svg.append(f'  <g transform="translate({node_xs[0] + 47}, {chain_y + 20})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <rect x="4" y="4" width="48" height="40" rx="4" />')
    svg.append('    <line x1="14" y1="44" x2="14" y2="52" /><line x1="22" y1="44" x2="22" y2="52" /><line x1="30" y1="44" x2="30" y2="52" /><line x1="38" y1="44" x2="38" y2="52" />')
    svg.append('    <circle cx="28" cy="24" r="8" />')
    svg.append('  </g>')
    svg.append(f'  <text x="{node_xs[0] + 75}" y="{chain_y + 130}" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36" text-anchor="middle">')
    svg.append('    <tspan x="{}" dy="0">NIC</tspan>'.format(node_xs[0] + 75))
    svg.append('  </text>')

    # Arrow 1: Node 1 -> Node 2
    x1_arr = node_xs[0] + node_w
    x2_arr = node_xs[1]
    y_arr = chain_y + 97.5
    svg.append(f'  <line x1="{x1_arr}" y1="{y_arr}" x2="{x2_arr}" y2="{y_arr}" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />')

    # Node 2: Leaf switch port
    svg.append(f'  <!-- Node 2: Leaf switch port -->')
    svg.append(f'  <rect x="{node_xs[1]}" y="{chain_y}" width="{node_w}" height="{node_h}" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    svg.append(f'  <g transform="translate({node_xs[1] + 47}, {chain_y + 16})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <rect x="4" y="8" width="48" height="34" rx="4" />')
    svg.append('    <line x1="12" y1="25" x2="44" y2="25" />')
    svg.append('    <polyline points="18,19 12,25 18,31" />')
    svg.append('    <polyline points="38,19 44,25 38,31" />')
    svg.append('  </g>')
    svg.append(f'  <text x="{node_xs[1] + 75}" y="{chain_y + 102}" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36" text-anchor="middle">')
    svg.append('    <tspan x="{}" dy="0">Leaf</tspan>'.format(node_xs[1] + 75))
    svg.append('    <tspan x="{}" dy="34">switch</tspan>'.format(node_xs[1] + 75))
    svg.append('    <tspan x="{}" dy="34">port</tspan>'.format(node_xs[1] + 75))
    svg.append('  </text>')

    # Arrow 2: Node 2 -> Node 3
    x1_arr = node_xs[1] + node_w
    x2_arr = node_xs[2]
    svg.append(f'  <line x1="{x1_arr}" y1="{y_arr}" x2="{x2_arr}" y2="{y_arr}" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />')

    # Node 3: Spine switch port
    svg.append(f'  <!-- Node 3: Spine switch port -->')
    svg.append(f'  <rect x="{node_xs[2]}" y="{chain_y}" width="{node_w}" height="{node_h}" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    svg.append(f'  <g transform="translate({node_xs[2] + 47}, {chain_y + 16})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <rect x="4" y="6" width="48" height="38" rx="4" />')
    svg.append('    <line x1="12" y1="18" x2="44" y2="18" /><line x1="12" y1="32" x2="44" y2="32" />')
    svg.append('    <circle cx="28" cy="25" r="4" fill="#207448" />')
    svg.append('  </g>')
    svg.append(f'  <text x="{node_xs[2] + 75}" y="{chain_y + 102}" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36" text-anchor="middle">')
    svg.append('    <tspan x="{}" dy="0">Spine</tspan>'.format(node_xs[2] + 75))
    svg.append('    <tspan x="{}" dy="34">switch</tspan>'.format(node_xs[2] + 75))
    svg.append('    <tspan x="{}" dy="34">port</tspan>'.format(node_xs[2] + 75))
    svg.append('  </text>')

    # Arrow 3: Node 3 -> Node 4
    x1_arr = node_xs[2] + node_w
    x2_arr = node_xs[3]
    svg.append(f'  <line x1="{x1_arr}" y1="{y_arr}" x2="{x2_arr}" y2="{y_arr}" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />')

    # Node 4: Leaf switch port
    svg.append(f'  <!-- Node 4: Leaf switch port -->')
    svg.append(f'  <rect x="{node_xs[3]}" y="{chain_y}" width="{node_w}" height="{node_h}" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    svg.append(f'  <g transform="translate({node_xs[3] + 47}, {chain_y + 16})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <rect x="4" y="8" width="48" height="34" rx="4" />')
    svg.append('    <line x1="12" y1="25" x2="44" y2="25" />')
    svg.append('    <polyline points="18,19 12,25 18,31" />')
    svg.append('    <polyline points="38,19 44,25 38,31" />')
    svg.append('  </g>')
    svg.append(f'  <text x="{node_xs[3] + 75}" y="{chain_y + 102}" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36" text-anchor="middle">')
    svg.append('    <tspan x="{}" dy="0">Leaf</tspan>'.format(node_xs[3] + 75))
    svg.append('    <tspan x="{}" dy="34">switch</tspan>'.format(node_xs[3] + 75))
    svg.append('    <tspan x="{}" dy="34">port</tspan>'.format(node_xs[3] + 75))
    svg.append('  </text>')

    # Arrow 4: Node 4 -> Node 5
    x1_arr = node_xs[3] + node_w
    x2_arr = node_xs[4]
    svg.append(f'  <line x1="{x1_arr}" y1="{y_arr}" x2="{x2_arr}" y2="{y_arr}" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />')

    # Node 5: NIC
    svg.append(f'  <!-- Node 5: NIC -->')
    svg.append(f'  <rect x="{node_xs[4]}" y="{chain_y}" width="{node_w}" height="{node_h}" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    svg.append(f'  <g transform="translate({node_xs[4] + 47}, {chain_y + 20})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <rect x="4" y="4" width="48" height="40" rx="4" />')
    svg.append('    <line x1="14" y1="44" x2="14" y2="52" /><line x1="22" y1="44" x2="22" y2="52" /><line x1="30" y1="44" x2="30" y2="52" /><line x1="38" y1="44" x2="38" y2="52" />')
    svg.append('    <circle cx="28" cy="24" r="8" />')
    svg.append('  </g>')
    svg.append(f'  <text x="{node_xs[4] + 75}" y="{chain_y + 130}" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36" text-anchor="middle">')
    svg.append('    <tspan x="{}" dy="0">NIC</tspan>'.format(node_xs[4] + 75))
    svg.append('  </text>')

    # Bar underneath spanning the whole chain: y = 795, h = 52
    svg.append('  <!-- Bar spanning chain -->')
    svg.append('  <rect x="40" y="795" width="980" height="52" rx="10" fill="#207448" />')
    svg.append('  <text x="530" y="829" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff" text-anchor="middle">')
    svg.append('    <tspan x="530" dy="0">the lossless class works only end to end</tspan>')
    svg.append('  </text>')

    # -------------------------------------------------------------
    # RIGHT COLUMN: x = 1060 to 1560 (width = 500)
    # -------------------------------------------------------------

    # Right panel with two failure arrows: y = 165 to 515 (height = 350)
    svg.append('  <!-- Right Panel: Failure modes -->')
    svg.append('  <rect x="1060" y="165" width="500" height="350" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')

    # Failure 1 card: y = 180, h = 145
    svg.append('  <rect x="1078" y="180" width="464" height="145" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    # Failure Arrow 1
    svg.append('  <line x1="1102" y1="205" x2="1102" y2="295" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />')
    # Text beside Arrow 1
    svg.append('  <text x="1126" y="226" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="1126" dy="0">PFC missing on one switch</tspan>')
    svg.append('    <tspan x="1126" dy="32">port: drops, and RDMA</tspan>')
    svg.append('    <tspan x="1126" dy="32">retransmits are costly</tspan>')
    svg.append('  </text>')

    # Failure 2 card (orange): y = 345, h = 150
    svg.append('  <rect x="1078" y="345" width="464" height="150" rx="10" fill="#ffffff" stroke="#db8129" stroke-width="2.5" />')
    # Failure Arrow 2 (orange)
    svg.append('  <line x1="1102" y1="375" x2="1102" y2="465" stroke="#db8129" stroke-width="4" marker-end="url(#arrow-orange)" />')
    # Text beside Arrow 2 (orange)
    svg.append('  <text x="1126" y="405" font-family="sans-serif" font-size="24" font-weight="bold" fill="#db8129">')
    svg.append('    <tspan x="1126" dy="0">misconfigured the other</tspan>')
    svg.append('    <tspan x="1126" dy="32">way: pause storms and</tspan>')
    svg.append('    <tspan x="1126" dy="32">deadlocks</tspan>')
    svg.append('  </text>')

    # Side contrast: InfiniBand: y = 535 to 847 (height = 312)
    svg.append('  <!-- Side Contrast: InfiniBand -->')
    svg.append('  <rect x="1060" y="535" width="500" height="312" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    # InfiniBand outline icon at top: 48x40 (placed at x = 1286, y = 545)
    svg.append('  <g transform="translate(1286, 545)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <rect x="4" y="4" width="40" height="32" rx="6" />')
    svg.append('    <path d="M 12 20 C 18 12, 30 12, 36 20" />')
    svg.append('    <path d="M 12 20 C 18 28, 30 28, 36 20" />')
    svg.append('  </g>')
    # InfiniBand text: starts at y = 624 (well below icon at 585, 39px margin!)
    svg.append('  <text x="1100" y="624" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="1100" dy="0">InfiniBand: credit-based</tspan>')
    svg.append('    <tspan x="1100" dy="28">flow control per virtual</tspan>')
    svg.append('    <tspan x="1100" dy="28">lane, lossless by</tspan>')
    svg.append('    <tspan x="1100" dy="28">construction; LIDs and GIDs</tspan>')
    svg.append('    <tspan x="1100" dy="28">replace MACs and IPs; the</tspan>')
    svg.append('    <tspan x="1100" dy="28">Subnet Manager programs</tspan>')
    svg.append('    <tspan x="1100" dy="28">forwarding tables</tspan>')
    svg.append('  </text>')

    # -------------------------------------------------------------
    # BOTTOM AREA: x = 40 to 1560 (width = 1520)
    # -------------------------------------------------------------

    # Footer: Rail-optimised: y = 865 to 1035 (height = 170)
    svg.append('  <!-- Footer: Rail-optimised -->')
    svg.append('  <rect x="40" y="865" width="1520" height="170" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    # Icon for Rail-optimised: GPU / multi-NIC fabric icon (56x56) at x = 60, y = 922
    svg.append('  <g transform="translate(60, 922)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <rect x="4" y="4" width="48" height="48" rx="6" />')
    svg.append('    <circle cx="28" cy="28" r="12" />')
    svg.append('    <line x1="28" y1="4" x2="28" y2="16" /><line x1="28" y1="40" x2="28" y2="52" />')
    svg.append('    <line x1="4" y1="28" x2="16" y2="28" /><line x1="40" y1="28" x2="52" y2="28" />')
    svg.append('  </g>')
    # Footer text: x = 135
    svg.append('  <text x="135" y="915" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="135" dy="0">Rail-optimised: one NIC per GPU, often its own subnet, VLAN or VRF; 8 x 400G</tspan>')
    svg.append('    <tspan x="135" dy="34">back end; a single x4 link at 100G instead of 400G slows the whole job</tspan>')
    svg.append('    <tspan x="135" dy="34">because collectives move at the speed of the slowest participant</tspan>')
    svg.append('  </text>')

    # Bottom bar: Treat a PFC change...: y = 1055 to 1115 (height = 60)
    svg.append('  <!-- Bottom Takeaway Bar -->')
    svg.append('  <rect x="40" y="1055" width="1520" height="60" rx="10" fill="#207448" />')
    svg.append('  <text x="800" y="1093" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff" text-anchor="middle">')
    svg.append('    <tspan x="800" dy="0">Treat a PFC change on one switch as a change to the whole fabric</tspan>')
    svg.append('  </text>')

    svg.append('</svg>')
    return "\n".join(svg)

with open("candidate_lossless.svg", "w") as f:
    f.write(generate_svg())
print("Wrote candidate_lossless.svg")
