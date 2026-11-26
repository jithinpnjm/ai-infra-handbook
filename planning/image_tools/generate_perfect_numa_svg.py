#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re, sys, pathlib

def build_svg():
    W = 1600
    H = 1080

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
    svg.append('  <title>Keeping the GPU, its NIC and its CPUs on one NUMA node</title>')
    svg.append('  <desc>Visual infographic explaining NUMA topology alignment in Kubernetes GPU nodes, comparing aligned pod placement inside NUMA node 0 with misaligned placement crossing the socket interconnect, and configuring the Topology Manager.</desc>')
    svg.append('')
    svg.append('  <!-- Canvas Background -->')
    svg.append(f'  <rect width="{W}" height="{H}" fill="#f5f8f5"/>')
    svg.append('')

    # ==================== TITLE ====================
    # 48px bold, centered at x=800, y=52
    svg.append('  <!-- ==================== TITLE ==================== -->')
    svg.append('  <text x="800" y="52" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">')
    svg.append('    <tspan x="800" dy="0">Keeping the GPU, its NIC and its CPUs </tspan>')
    svg.append('    <tspan x="800" dy="54">on one NUMA node</tspan>')
    svg.append('  </text>')
    svg.append('')

    # ==================== SOCKET HEADERS ====================
    # Socket 0: x=40..485 (w=445)
    # Socket 1: x=535..980 (w=445)
    # Interconnect link: x=485..535 (w=50)

    # Socket 0 Header: NUMA node 0
    svg.append('  <!-- ==================== SOCKET HEADERS ==================== -->')
    svg.append('  <!-- Socket 0 Header: NUMA node 0 -->')
    svg.append('  <g id="socket-0-header">')
    svg.append('    <rect x="40" y="140" width="445" height="74" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>')
    # Outline Chip Icon (48px) at x=56, y=153
    svg.append('    <g transform="translate(56, 153)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="8" y="8" width="32" height="32" rx="6" fill="#ffffff"/>')
    svg.append('      <line x1="16" y1="2" x2="16" y2="8"/><line x1="24" y1="2" x2="24" y2="8"/><line x1="32" y1="2" x2="32" y2="8"/>')
    svg.append('      <line x1="16" y1="40" x2="16" y2="46"/><line x1="24" y1="40" x2="24" y2="46"/><line x1="32" y1="40" x2="32" y2="46"/>')
    svg.append('      <line x1="2" y1="16" x2="8" y2="16"/><line x1="2" y1="24" x2="8" y2="24"/><line x1="2" y1="32" x2="8" y2="32"/>')
    svg.append('      <line x1="40" y1="16" x2="46" y2="16"/><line x1="40" y1="24" x2="46" y2="24"/><line x1="40" y1="32" x2="46" y2="32"/>')
    svg.append('    </g>')
    svg.append('    <text x="125" y="187" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">NUMA node 0</text>')
    svg.append('  </g>')
    svg.append('')

    # Socket 1 Header: NUMA node 1
    svg.append('  <!-- Socket 1 Header: NUMA node 1 -->')
    svg.append('  <g id="socket-1-header">')
    svg.append('    <rect x="535" y="140" width="445" height="74" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>')
    # Outline Chip Icon (48px) at x=551, y=153
    svg.append('    <g transform="translate(551, 153)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="8" y="8" width="32" height="32" rx="6" fill="#ffffff"/>')
    svg.append('      <line x1="16" y1="2" x2="16" y2="8"/><line x1="24" y1="2" x2="24" y2="8"/><line x1="32" y1="2" x2="32" y2="8"/>')
    svg.append('      <line x1="16" y1="40" x2="16" y2="46"/><line x1="24" y1="40" x2="24" y2="46"/><line x1="32" y1="40" x2="32" y2="46"/>')
    svg.append('      <line x1="2" y1="16" x2="8" y2="16"/><line x1="2" y1="24" x2="8" y2="24"/><line x1="2" y1="32" x2="8" y2="32"/>')
    svg.append('      <line x1="40" y1="16" x2="46" y2="16"/><line x1="40" y1="24" x2="46" y2="24"/><line x1="40" y1="32" x2="46" y2="32"/>')
    svg.append('    </g>')
    svg.append('    <text x="620" y="187" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">NUMA node 1</text>')
    svg.append('  </g>')
    svg.append('')

    # Hardware Socket Interconnect Link (Link between sockets)
    svg.append('  <!-- Hardware Socket Interconnect Link (link between them) -->')
    svg.append('  <g id="interconnect-link">')
    svg.append('    <rect x="485" y="165" width="50" height="24" rx="4" fill="#207448"/>')
    svg.append('    <line x1="488" y1="177" x2="532" y2="177" stroke="#ffffff" stroke-width="3" stroke-dasharray="4 3"/>')
    svg.append('  </g>')
    svg.append('')

    # ==================== PANEL: ALIGNED ====================
    # x=40, y=228, w=940, h=318
    svg.append('  <!-- ==================== PANEL: ALIGNED ==================== -->')
    svg.append('  <g id="panel-aligned">')
    svg.append('    <rect x="40" y="228" width="940" height="318" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2.5"/>')
    svg.append('    <rect x="40" y="228" width="940" height="66" rx="16" fill="#e8f1ea"/>')
    svg.append('    <line x1="40" y1="294" x2="980" y2="294" stroke="#207448" stroke-width="1.5"/>')
    # Outline check icon (48px)
    svg.append('    <g transform="translate(56, 237)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="24" cy="24" r="20" fill="#ffffff"/>')
    svg.append('      <polyline points="15,24 22,31 33,17"/>')
    svg.append('    </g>')
    svg.append('    <text x="125" y="274" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Aligned</text>')
    svg.append('')

    # Aligned Node 0: Placement Card
    # x=60, y=308, w=410, h=154
    svg.append('    <!-- Aligned Node 0: Placement Card -->')
    svg.append('    <rect x="60" y="308" width="410" height="154" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
    svg.append('    <text x="80" y="348" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="80" dy="0">GPU, NIC VF or </tspan>')
    svg.append('      <tspan x="80" dy="30">RDMA device, and the </tspan>')
    svg.append('      <tspan x="80" dy="30">pod\'s CPUs all on </tspan>')
    svg.append('      <tspan x="80" dy="30">NUMA node 0</tspan>')
    svg.append('    </text>')
    svg.append('')

    # Aligned Node 0: Transfers outcome
    # x=60, y=472, w=410, h=62
    svg.append('    <!-- Aligned Node 0: Transfers outcome -->')
    svg.append('    <rect x="60" y="472" width="410" height="62" rx="10" fill="#207448"/>')
    svg.append('    <text x="265" y="513" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">')
    svg.append('      <tspan x="265" dy="-14">transfers stay inside </tspan>')
    svg.append('      <tspan x="265" dy="28">the node; fast</tspan>')
    svg.append('    </text>')
    svg.append('')

    # Aligned Node 1 Area: Socket 1 idle from pod traffic
    # x=550, y=308, w=410, h=226
    svg.append('    <!-- Aligned Node 1 Area: Socket 1 idle from pod traffic -->')
    svg.append('    <rect x="550" y="308" width="410" height="226" rx="12" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" stroke-dasharray="6 6"/>')
    svg.append('    <g transform="translate(730, 401)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round">')
    svg.append('      <circle cx="25" cy="25" r="20" stroke-dasharray="4 4"/>')
    svg.append('      <line x1="15" y1="25" x2="35" y2="25"/>')
    svg.append('    </g>')
    svg.append('  </g>')
    svg.append('')

    # ==================== PANEL: MISALIGNED (ORANGE) ====================
    # x=40, y=560, w=940, h=310
    # Exactly 3 occurrences of #db8129: container stroke, icon stroke, title fill
    svg.append('  <!-- ==================== PANEL: MISALIGNED (ORANGE) ==================== -->')
    svg.append('  <g id="panel-misaligned">')
    svg.append('    <rect x="40" y="560" width="940" height="310" rx="16" fill="#fff9f2" stroke="#db8129" stroke-width="3"/>')
    svg.append('    <rect x="40" y="560" width="940" height="70" rx="16" fill="#fbeede"/>')
    svg.append('    <line x1="40" y1="630" x2="980" y2="630" stroke="#207448" stroke-width="1.5"/>')
    # Outline warning icon in orange (48px)
    svg.append('    <g transform="translate(56, 571)" stroke="#db8129" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 24 6 L 42 38 L 6 38 Z" fill="#ffffff"/>')
    svg.append('      <line x1="24" y1="18" x2="24" y2="27"/><circle cx="24" cy="33" r="2" fill="#207448"/>')
    svg.append('    </g>')
    svg.append('    <text x="125" y="606" font-family="sans-serif" font-size="30" font-weight="bold" fill="#db8129">Misaligned</text>')
    svg.append('')

    # Misaligned Node 0: Pod CPUs placement
    # x=60, y=638, w=410, h=100
    svg.append('    <!-- Misaligned Node 0: Pod CPUs placement -->')
    svg.append('    <rect x="60" y="638" width="410" height="100" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    svg.append('    <text x="80" y="678" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="80" dy="0">pod CPUs on node 0 </tspan>')
    svg.append('      <tspan x="80" dy="32">but the NIC on node 1</tspan>')
    svg.append('    </text>')
    svg.append('')

    # Misaligned Cross-Socket Transfer Path
    # x=60, y=750, w=900, h=106
    svg.append('    <!-- Misaligned Cross-Socket Transfer Path -->')
    svg.append('    <rect x="60" y="750" width="900" height="106" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    svg.append('    <text x="510" y="794" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">')
    svg.append('      <tspan x="510" dy="0">every transfer crosses the link between sockets </tspan>')
    svg.append('      <tspan x="510" dy="34">and takes the slower road</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('')

    # ==================== RIGHT PANEL: HOW TO KEEP THEM TOGETHER ====================
    # x=1020, y=140, w=540, h=730
    svg.append('  <!-- ==================== RIGHT PANEL: HOW TO KEEP THEM TOGETHER ==================== -->')
    svg.append('  <g id="panel-right">')
    svg.append('    <rect x="1020" y="140" width="540" height="730" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>')
    svg.append('    <rect x="1020" y="140" width="540" height="76" rx="16" fill="#ffffff"/>')
    svg.append('    <line x1="1020" y1="216" x2="1560" y2="216" stroke="#207448" stroke-width="1.5"/>')
    # Outline Gear / Config icon (36px) at x=1030, y=160
    svg.append('    <g transform="translate(1030, 160)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="18" cy="18" r="8"/>')
    svg.append('      <path d="M 18 4 L 18 8 M 18 28 L 18 32 M 4 18 L 8 18 M 28 18 L 32 18 M 8 8 L 11 11 M 25 25 L 28 28 M 8 28 L 11 25 M 25 11 L 28 8"/>')
    svg.append('    </g>')
    svg.append('    <text x="1075" y="188" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">how to keep them together</text>')
    svg.append('')

    # Right Card 1: kubelet Topology Manager with the single-numa-node or best-effort policy, together with the CPU Manager and the device plugins
    # x=1045, y=232, w=490, h=194
    svg.append('    <!-- Right Card 1: Topology Manager Policy -->')
    svg.append('    <rect x="1045" y="232" width="490" height="194" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    svg.append('    <text x="1065" y="272" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="1065" dy="0">kubelet Topology Manager </tspan>')
    svg.append('      <tspan x="1065" dy="30">with the single-numa-node </tspan>')
    svg.append('      <tspan x="1065" dy="30">or best-effort policy, </tspan>')
    svg.append('      <tspan x="1065" dy="30">together with the CPU Manager </tspan>')
    svg.append('      <tspan x="1065" dy="30">and the device plugins</tspan>')
    svg.append('    </text>')
    svg.append('')

    # Right Card 2: Verify after the pod starts: nvidia-smi topo -m, ibdev2netdev
    # x=1045, y=442, w=490, h=184
    svg.append('    <!-- Right Card 2: Verification Commands -->')
    svg.append('    <rect x="1045" y="442" width="490" height="184" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    svg.append('    <text x="1065" y="484" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="1065" dy="0" font-family="sans-serif">Verify after the pod starts: </tspan>')
    svg.append('      <tspan x="1065" dy="42" font-family="monospace" font-weight="bold" fill="#207448">nvidia-smi topo -m, </tspan>')
    svg.append('      <tspan x="1065" dy="36" font-family="monospace" font-weight="bold" fill="#207448">ibdev2netdev</tspan>')
    svg.append('    </text>')
    svg.append('')

    # Right Card 3: same on the host: pin test CPUs to the NUMA node of the NIC
    # x=1045, y=642, w=490, h=212
    svg.append('    <!-- Right Card 3: Host Pinning Note -->')
    svg.append('    <rect x="1045" y="642" width="490" height="212" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    svg.append('    <text x="1065" y="694" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="1065" dy="0">same on the host: </tspan>')
    svg.append('      <tspan x="1065" dy="36">pin test CPUs to the </tspan>')
    svg.append('      <tspan x="1065" dy="36">NUMA node of the NIC</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('')

    # ==================== BOTTOM BAR: TAKEAWAY ====================
    # x=40, y=905, w=1520, h=135
    svg.append('  <!-- ==================== BOTTOM BAR: TAKEAWAY ==================== -->')
    svg.append('  <g id="bottom-takeaway-bar">')
    svg.append('    <rect x="40" y="905" width="1520" height="135" rx="14" fill="#207448"/>')
    svg.append('    <text x="800" y="960" text-anchor="middle" font-family="sans-serif" font-size="25" font-weight="bold" fill="#ffffff">')
    svg.append('      <tspan x="800" dy="0">A scheduler can place CPUs on one node and the network card on the other, </tspan>')
    svg.append('      <tspan x="800" dy="36">so check the placement after the pod starts</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('</svg>')

    return "\n".join(svg)

content = build_svg()
pathlib.Path("test_candidate_numa.svg").write_text(content, encoding="utf-8")
print("Saved updated test_candidate_numa.svg")
