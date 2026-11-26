import xml.etree.ElementTree as ET
import re

def build_and_test():
    W = 1600
    H = 1170

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

    # Title: 48px bold
    svg.append('  <!-- 1. Title -->')
    svg.append('  <text x="40" y="86" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">')
    svg.append('    <tspan x="40" dy="0">A lossless Ethernet class needs</tspan>')
    svg.append('    <tspan x="40" dy="54">every piece set the same, end to end</tspan>')
    svg.append('  </text>')

    # -------------------------------------------------------------
    # LEFT COLUMN: x = 40 to 1020 (width = 980)
    # -------------------------------------------------------------
    
    # Checklist Container: y = 175 to 570 (height = 395)
    svg.append('  <!-- Checklist Container -->')
    svg.append('  <rect x="40" y="175" width="980" height="395" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')

    def draw_tick(cx, cy):
        return f'<circle cx="{cx}" cy="{cy}" r="14" fill="#207448" /><path d="M {cx-6} {cy} L {cx-2} {cy+5} L {cx+7} {cy-5}" stroke="#ffffff" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round" />'

    # Checklist Item 1: y = 190, h = 66
    svg.append('  <rect x="55" y="190" width="950" height="66" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append(f'  {draw_tick(85, 223)}')
    svg.append('  <text x="115" y="217" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="115" dy="0">PFC (802.1Qbb) for the RoCE priority, on the NIC and on</tspan>')
    svg.append('    <tspan x="115" dy="28">every switch</tspan>')
    svg.append('  </text>')

    # Checklist Item 2: y = 266, h = 48
    svg.append('  <rect x="55" y="266" width="950" height="48" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append(f'  {draw_tick(85, 290)}')
    svg.append('  <text x="115" y="298" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="115" dy="0">ECN marking with DCQCN or similar rate control</tspan>')
    svg.append('  </text>')

    # Checklist Item 3: y = 324, h = 48
    svg.append('  <rect x="55" y="324" width="950" height="48" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append(f'  {draw_tick(85, 348)}')
    svg.append('  <text x="115" y="356" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="115" dy="0">DSCP and PCP trust and mapping set correctly</tspan>')
    svg.append('  </text>')

    # Checklist Item 4: y = 382, h = 66
    svg.append('  <rect x="55" y="382" width="950" height="66" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append(f'  {draw_tick(85, 415)}')
    svg.append('  <text x="115" y="409" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="115" dy="0">buffer allocation and headroom sized for each port speed</tspan>')
    svg.append('    <tspan x="115" dy="28">and cable length</tspan>')
    svg.append('  </text>')

    # Checklist Item 5: y = 458, h = 98
    svg.append('  <rect x="55" y="458" width="950" height="98" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append(f'  {draw_tick(85, 507)}')
    svg.append('  <text x="115" y="485" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="115" dy="0">per-port counters watched: CRC, FEC uncorrected, symbol</tspan>')
    svg.append('    <tspan x="115" dy="28">errors, PFC pause counts per priority, ECN-marked packets,</tspan>')
    svg.append('    <tspan x="115" dy="28">buffer occupancy, link flaps, optical power (DOM)</tspan>')
    svg.append('  </text>')

    # Horizontal chain: y = 590 to 795 (height = 205)
    node_w = 150
    node_h = 205
    chain_y = 590
    node_xs = [40, 247.5, 455, 662.5, 870]

    # Node 1: NIC
    svg.append('  <!-- Node 1: NIC -->')
    svg.append(f'  <rect x="{node_xs[0]}" y="{chain_y}" width="{node_w}" height="{node_h}" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    svg.append(f'  <g transform="translate({node_xs[0] + 47}, {chain_y + 20})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <rect x="4" y="4" width="48" height="40" rx="4" />')
    svg.append('    <line x1="14" y1="44" x2="14" y2="52" /><line x1="22" y1="44" x2="22" y2="52" /><line x1="30" y1="44" x2="30" y2="52" /><line x1="38" y1="44" x2="38" y2="52" />')
    svg.append('    <circle cx="28" cy="24" r="8" />')
    svg.append('  </g>')
    svg.append(f'  <text x="{node_xs[0] + 75}" y="{chain_y + 135}" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36" text-anchor="middle">')
    svg.append('    <tspan x="{}" dy="0">NIC</tspan>'.format(node_xs[0] + 75))
    svg.append('  </text>')

    # Arrow 1: Node 1 -> Node 2
    x1_arr = node_xs[0] + node_w
    x2_arr = node_xs[1]
    y_arr = chain_y + 102.5
    svg.append(f'  <line x1="{x1_arr}" y1="{y_arr}" x2="{x2_arr}" y2="{y_arr}" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />')

    # Node 2: Leaf switch port
    svg.append('  <!-- Node 2: Leaf switch port -->')
    svg.append(f'  <rect x="{node_xs[1]}" y="{chain_y}" width="{node_w}" height="{node_h}" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    svg.append(f'  <g transform="translate({node_xs[1] + 47}, {chain_y + 16})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <rect x="4" y="8" width="48" height="34" rx="4" />')
    svg.append('    <line x1="12" y1="25" x2="44" y2="25" />')
    svg.append('    <polyline points="18,19 12,25 18,31" />')
    svg.append('    <polyline points="38,19 44,25 38,31" />')
    svg.append('  </g>')
    svg.append(f'  <text x="{node_xs[1] + 75}" y="{chain_y + 105}" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36" text-anchor="middle">')
    svg.append('    <tspan x="{}" dy="0">Leaf</tspan>'.format(node_xs[1] + 75))
    svg.append('    <tspan x="{}" dy="34">switch</tspan>'.format(node_xs[1] + 75))
    svg.append('    <tspan x="{}" dy="34">port</tspan>'.format(node_xs[1] + 75))
    svg.append('  </text>')

    # Arrow 2: Node 2 -> Node 3
    x1_arr = node_xs[1] + node_w
    x2_arr = node_xs[2]
    svg.append(f'  <line x1="{x1_arr}" y1="{y_arr}" x2="{x2_arr}" y2="{y_arr}" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />')

    # Node 3: Spine switch port
    svg.append('  <!-- Node 3: Spine switch port -->')
    svg.append(f'  <rect x="{node_xs[2]}" y="{chain_y}" width="{node_w}" height="{node_h}" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    svg.append(f'  <g transform="translate({node_xs[2] + 47}, {chain_y + 16})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <rect x="4" y="6" width="48" height="38" rx="4" />')
    svg.append('    <line x1="12" y1="18" x2="44" y2="18" /><line x1="12" y1="32" x2="44" y2="32" />')
    svg.append('    <circle cx="28" cy="25" r="4" fill="#207448" />')
    svg.append('  </g>')
    svg.append(f'  <text x="{node_xs[2] + 75}" y="{chain_y + 105}" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36" text-anchor="middle">')
    svg.append('    <tspan x="{}" dy="0">Spine</tspan>'.format(node_xs[2] + 75))
    svg.append('    <tspan x="{}" dy="34">switch</tspan>'.format(node_xs[2] + 75))
    svg.append('    <tspan x="{}" dy="34">port</tspan>'.format(node_xs[2] + 75))
    svg.append('  </text>')

    # Arrow 3: Node 3 -> Node 4
    x1_arr = node_xs[2] + node_w
    x2_arr = node_xs[3]
    svg.append(f'  <line x1="{x1_arr}" y1="{y_arr}" x2="{x2_arr}" y2="{y_arr}" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />')

    # Node 4: Leaf switch port
    svg.append('  <!-- Node 4: Leaf switch port -->')
    svg.append(f'  <rect x="{node_xs[3]}" y="{chain_y}" width="{node_w}" height="{node_h}" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    svg.append(f'  <g transform="translate({node_xs[3] + 47}, {chain_y + 16})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <rect x="4" y="8" width="48" height="34" rx="4" />')
    svg.append('    <line x1="12" y1="25" x2="44" y2="25" />')
    svg.append('    <polyline points="18,19 12,25 18,31" />')
    svg.append('    <polyline points="38,19 44,25 38,31" />')
    svg.append('  </g>')
    svg.append(f'  <text x="{node_xs[3] + 75}" y="{chain_y + 105}" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36" text-anchor="middle">')
    svg.append('    <tspan x="{}" dy="0">Leaf</tspan>'.format(node_xs[3] + 75))
    svg.append('    <tspan x="{}" dy="34">switch</tspan>'.format(node_xs[3] + 75))
    svg.append('    <tspan x="{}" dy="34">port</tspan>'.format(node_xs[3] + 75))
    svg.append('  </text>')

    # Arrow 4: Node 4 -> Node 5
    x1_arr = node_xs[3] + node_w
    x2_arr = node_xs[4]
    svg.append(f'  <line x1="{x1_arr}" y1="{y_arr}" x2="{x2_arr}" y2="{y_arr}" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />')

    # Node 5: NIC
    svg.append('  <!-- Node 5: NIC -->')
    svg.append(f'  <rect x="{node_xs[4]}" y="{chain_y}" width="{node_w}" height="{node_h}" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    svg.append(f'  <g transform="translate({node_xs[4] + 47}, {chain_y + 20})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <rect x="4" y="4" width="48" height="40" rx="4" />')
    svg.append('    <line x1="14" y1="44" x2="14" y2="52" /><line x1="22" y1="44" x2="22" y2="52" /><line x1="30" y1="44" x2="30" y2="52" /><line x1="38" y1="44" x2="38" y2="52" />')
    svg.append('    <circle cx="28" cy="24" r="8" />')
    svg.append('  </g>')
    svg.append(f'  <text x="{node_xs[4] + 75}" y="{chain_y + 135}" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36" text-anchor="middle">')
    svg.append('    <tspan x="{}" dy="0">NIC</tspan>'.format(node_xs[4] + 75))
    svg.append('  </text>')

    # Bar underneath spanning the whole chain: y = 812, h = 55
    svg.append('  <!-- Bar spanning chain -->')
    svg.append('  <rect x="40" y="812" width="980" height="55" rx="10" fill="#207448" />')
    svg.append('  <text x="530" y="847" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff" text-anchor="middle">')
    svg.append('    <tspan x="530" dy="0">the lossless class works only end to end</tspan>')
    svg.append('  </text>')

    # -------------------------------------------------------------
    # RIGHT COLUMN: x = 1060 to 1560 (width = 500)
    # -------------------------------------------------------------

    # Right panel with two failure arrows: y = 175 to 515 (height = 340)
    svg.append('  <!-- Right Panel: Failure modes -->')
    svg.append('  <rect x="1060" y="175" width="500" height="340" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')

    # Failure 1 card: y = 190, h = 135
    svg.append('  <rect x="1078" y="190" width="464" height="135" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    # Failure Arrow 1
    svg.append('  <line x1="1102" y1="210" x2="1102" y2="300" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />')
    # Text beside Arrow 1
    svg.append('  <text x="1126" y="235" font-family="sans-serif" font-size="24" fill="#303a36">')
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

    # Side contrast: InfiniBand: y = 535 to 867 (height = 332)
    svg.append('  <!-- Side Contrast: InfiniBand -->')
    svg.append('  <rect x="1060" y="535" width="500" height="332" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    # InfiniBand outline icon at top: 56x56 (placed at x = 1282, y = 548)
    svg.append('  <g transform="translate(1282, 548)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <rect x="4" y="6" width="48" height="38" rx="6" />')
    svg.append('    <path d="M 14 25 C 20 17, 36 17, 42 25" />')
    svg.append('    <path d="M 14 25 C 20 33, 36 33, 42 25" />')
    svg.append('  </g>')
    # InfiniBand text: wrapped cleanly to max 389px (starts at y = 632)
    svg.append('  <text x="1100" y="632" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="1100" dy="0">InfiniBand: credit-based</tspan>')
    svg.append('    <tspan x="1100" dy="30">flow control per virtual</tspan>')
    svg.append('    <tspan x="1100" dy="30">lane, lossless by</tspan>')
    svg.append('    <tspan x="1100" dy="30">construction; LIDs and GIDs</tspan>')
    svg.append('    <tspan x="1100" dy="30">replace MACs and IPs; the</tspan>')
    svg.append('    <tspan x="1100" dy="30">Subnet Manager programs</tspan>')
    svg.append('    <tspan x="1100" dy="30">forwarding tables</tspan>')
    svg.append('  </text>')

    # -------------------------------------------------------------
    # BOTTOM AREA: x = 40 to 1560 (width = 1520)
    # -------------------------------------------------------------

    # Footer: Rail-optimised: y = 887 to 1047 (height = 160)
    svg.append('  <!-- Footer: Rail-optimised -->')
    svg.append('  <rect x="40" y="887" width="1520" height="160" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('  <g transform="translate(65, 937)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <rect x="4" y="4" width="48" height="48" rx="6" />')
    svg.append('    <circle cx="28" cy="28" r="12" />')
    svg.append('    <line x1="28" y1="4" x2="28" y2="16" /><line x1="28" y1="40" x2="28" y2="52" />')
    svg.append('    <line x1="4" y1="28" x2="16" y2="28" /><line x1="40" y1="28" x2="52" y2="28" />')
    svg.append('  </g>')
    svg.append('  <text x="140" y="934" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="140" dy="0">Rail-optimised: one NIC per GPU, often its own subnet, VLAN or VRF; 8 x 400G back end; a single</tspan>')
    svg.append('    <tspan x="140" dy="34">x4 link at 100G instead of 400G slows the whole job because collectives move at the speed of</tspan>')
    svg.append('    <tspan x="140" dy="34">the slowest participant</tspan>')
    svg.append('  </text>')

    # Bottom bar: Treat a PFC change...: y = 1067 to 1127 (height = 60)
    svg.append('  <!-- Bottom Takeaway Bar -->')
    svg.append('  <rect x="40" y="1067" width="1520" height="60" rx="10" fill="#207448" />')
    svg.append('  <text x="800" y="1105" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff" text-anchor="middle">')
    svg.append('    <tspan x="800" dy="0">Treat a PFC change on one switch as a change to the whole fabric</tspan>')
    svg.append('  </text>')

    svg.append('</svg>')
    return "\n".join(svg)

content = build_and_test()
with open("candidate_lossless_v2.svg", "w") as f:
    f.write(content)

print("Generated candidate_lossless_v2.svg")
