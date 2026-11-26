import re
import xml.etree.ElementTree as ET

def generate_svg():
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1160" width="1600" height="1160">
  <title>A lossless Ethernet class needs every piece set the same, end to end</title>
  <desc>Infographic explaining end-to-end lossless Ethernet configuration, checklist, failure modes, InfiniBand contrast, and rail-optimised fabric.</desc>

  <defs>
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />
    </marker>
    <marker id="arrow-orange" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#db8129" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1600" height="1160" fill="#f5f8f5" />

  <!-- Title -->
  <text x="40" y="75" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="40" dy="0">A lossless Ethernet class needs</tspan>
    <tspan x="40" dy="54">every piece set the same, end to end</tspan>
  </text>

  <!-- ==================== LEFT COLUMN: CHECKLIST & CHAIN ==================== -->

  <!-- Checklist Container Box -->
  <rect x="40" y="160" width="1020" height="395" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

  <!-- Checklist Item 1 -->
  <g id="check-1">
    <circle cx="72" cy="195" r="14" fill="#207448" />
    <path d="M 67 195 L 70 199 L 77 191" stroke="#ffffff" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round" />
    <text x="102" y="193" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="102" dy="0">PFC (802.1Qbb) for the RoCE priority, on the NIC and on</tspan>
      <tspan x="102" dy="30">every switch</tspan>
    </text>
  </g>

  <!-- Checklist Item 2 -->
  <g id="check-2">
    <circle cx="72" cy="265" r="14" fill="#207448" />
    <path d="M 67 265 L 70 269 L 77 261" stroke="#ffffff" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round" />
    <text x="102" y="273" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="102" dy="0">ECN marking with DCQCN or similar rate control</tspan>
    </text>
  </g>

  <!-- Checklist Item 3 -->
  <g id="check-3">
    <circle cx="72" cy="325" r="14" fill="#207448" />
    <path d="M 67 325 L 70 329 L 77 321" stroke="#ffffff" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round" />
    <text x="102" y="333" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="102" dy="0">DSCP and PCP trust and mapping set correctly</tspan>
    </text>
  </g>

  <!-- Checklist Item 4 -->
  <g id="check-4">
    <circle cx="72" cy="385" r="14" fill="#207448" />
    <path d="M 67 385 L 70 389 L 77 381" stroke="#ffffff" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round" />
    <text x="102" y="383" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="102" dy="0">buffer allocation and headroom sized for each port speed</tspan>
      <tspan x="102" dy="30">and cable length</tspan>
    </text>
  </g>

  <!-- Checklist Item 5 -->
  <g id="check-5">
    <circle cx="72" cy="460" r="14" fill="#207448" />
    <path d="M 67 460 L 70 464 L 77 456" stroke="#ffffff" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round" />
    <text x="102" y="455" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="102" dy="0">per-port counters watched: CRC, FEC uncorrected, symbol</tspan>
      <tspan x="102" dy="30">errors, PFC pause counts per priority, ECN-marked packets,</tspan>
      <tspan x="102" dy="30">buffer occupancy, link flaps, optical power (DOM)</tspan>
    </text>
  </g>

  <!-- ==================== HORIZONTAL CHAIN ==================== -->

  <!-- Chain Node 1: NIC -->
  <g id="node-nic-1">
    <rect x="40" y="580" width="156" height="210" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- NIC Icon: PCIe board / network interface -->
    <g transform="translate(90, 598)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="4" width="48" height="34" rx="4" />
      <line x1="12" y1="38" x2="12" y2="48" />
      <line x1="24" y1="38" x2="24" y2="48" />
      <line x1="36" y1="38" x2="36" y2="48" />
      <circle cx="28" cy="21" r="6" />
    </g>
    <text x="118" y="700" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">
      <tspan x="118" dy="0">NIC</tspan>
    </text>
  </g>

  <!-- Chain Arrow 1 -->
  <line x1="200" y1="685" x2="252" y2="685" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- Chain Node 2: Leaf switch port -->
  <g id="node-leaf-1">
    <rect x="256" y="580" width="156" height="210" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Leaf Switch Icon -->
    <g transform="translate(306, 598)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="8" width="48" height="36" rx="4" />
      <line x1="14" y1="26" x2="42" y2="26" />
      <polyline points="20,20 14,26 20,32" />
      <polyline points="36,20 42,26 36,32" />
    </g>
    <text x="334" y="675" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">
      <tspan x="334" dy="0">Leaf</tspan>
      <tspan x="334" dy="36">switch</tspan>
      <tspan x="334" dy="36">port</tspan>
    </text>
  </g>

  <!-- Chain Arrow 2 -->
  <line x1="416" y1="685" x2="468" y2="685" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- Chain Node 3: Spine switch port -->
  <g id="node-spine">
    <rect x="472" y="580" width="156" height="210" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Spine Switch Icon -->
    <g transform="translate(522, 598)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="6" width="48" height="40" rx="4" />
      <line x1="12" y1="18" x2="44" y2="34" />
      <line x1="12" y1="34" x2="44" y2="18" />
      <circle cx="28" cy="26" r="4" fill="#207448" />
    </g>
    <text x="550" y="675" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">
      <tspan x="550" dy="0">Spine</tspan>
      <tspan x="550" dy="36">switch</tspan>
      <tspan x="550" dy="36">port</tspan>
    </text>
  </g>

  <!-- Chain Arrow 3 -->
  <line x1="632" y1="685" x2="684" y2="685" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- Chain Node 4: Leaf switch port -->
  <g id="node-leaf-2">
    <rect x="688" y="580" width="156" height="210" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Leaf Switch Icon -->
    <g transform="translate(738, 598)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="8" width="48" height="36" rx="4" />
      <line x1="14" y1="26" x2="42" y2="26" />
      <polyline points="20,20 14,26 20,32" />
      <polyline points="36,20 42,26 36,32" />
    </g>
    <text x="766" y="675" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">
      <tspan x="766" dy="0">Leaf</tspan>
      <tspan x="766" dy="36">switch</tspan>
      <tspan x="766" dy="36">port</tspan>
    </text>
  </g>

  <!-- Chain Arrow 4 -->
  <line x1="848" y1="685" x2="900" y2="685" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- Chain Node 5: NIC -->
  <g id="node-nic-2">
    <rect x="904" y="580" width="156" height="210" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- NIC Icon: PCIe board / network interface -->
    <g transform="translate(954, 598)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="4" width="48" height="34" rx="4" />
      <line x1="12" y1="38" x2="12" y2="48" />
      <line x1="24" y1="38" x2="24" y2="48" />
      <line x1="36" y1="38" x2="36" y2="48" />
      <circle cx="28" cy="21" r="6" />
    </g>
    <text x="982" y="700" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">
      <tspan x="982" dy="0">NIC</tspan>
    </text>
  </g>

  <!-- Bar underneath spanning the whole chain -->
  <g id="bar-under-chain">
    <rect x="40" y="805" width="1020" height="52" rx="10" fill="#207448" />
    <text x="550" y="839" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">
      <tspan x="550" dy="0">the lossless class works only end to end</tspan>
    </text>
  </g>

  <!-- ==================== RIGHT PANEL ==================== -->

  <!-- Failure 1 Box -->
  <g id="box-failure-1">
    <rect x="1100" y="160" width="460" height="155" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Failure Arrow 1 (green) -->
    <line x1="1125" y1="195" x2="1125" y2="280" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
    <text x="1150" y="210" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1150" dy="0">PFC missing on one switch</tspan>
      <tspan x="1150" dy="32">port: drops, and RDMA</tspan>
      <tspan x="1150" dy="32">retransmits are costly</tspan>
    </text>
  </g>

  <!-- Failure 2 Box (Orange emphasis) -->
  <g id="box-failure-2">
    <rect x="1100" y="335" width="460" height="155" rx="12" fill="#fdf6ee" stroke="#db8129" stroke-width="2.5" />
    <!-- Failure Arrow 2 (orange) -->
    <line x1="1125" y1="370" x2="1125" y2="455" stroke="#db8129" stroke-width="3.5" marker-end="url(#arrow-orange)" />
    <text x="1150" y="395" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1150" dy="0">misconfigured the other</tspan>
      <tspan x="1150" dy="32">way: pause storms and</tspan>
      <tspan x="1150" dy="32">deadlocks</tspan>
    </text>
  </g>

  <!-- Side contrast: InfiniBand -->
  <g id="box-infiniband">
    <rect x="1100" y="510" width="460" height="347" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- InfiniBand Network Fabric Icon: clearly at top with plenty of clearance -->
    <g transform="translate(1302, 526)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="6" />
      <circle cx="44" cy="12" r="6" />
      <circle cx="28" cy="42" r="6" />
      <line x1="17" y1="15" x2="25" y2="37" />
      <line x1="39" y1="15" x2="31" y2="37" />
      <line x1="18" y1="12" x2="38" y2="12" />
    </g>
    <!-- Text completely below the icon (starts at y=615, icon bottom is at 580) -->
    <text x="1130" y="612" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1130" dy="0">InfiniBand: credit-based flow</tspan>
      <tspan x="1130" dy="32">control per virtual lane,</tspan>
      <tspan x="1130" dy="32">lossless by construction; LIDs</tspan>
      <tspan x="1130" dy="32">and GIDs replace MACs and IPs;</tspan>
      <tspan x="1130" dy="32">the Subnet Manager programs</tspan>
      <tspan x="1130" dy="32">forwarding tables</tspan>
    </text>
  </g>

  <!-- ==================== FOOTER ==================== -->
  <g id="box-footer">
    <rect x="40" y="877" width="1520" height="150" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <text x="70" y="922" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="70" dy="0">Rail-optimised: one NIC per GPU, often its own subnet, VLAN or VRF; 8 x 400G back end;</tspan>
      <tspan x="70" dy="34">a single x4 link at 100G instead of 400G slows the whole job because collectives</tspan>
      <tspan x="70" dy="34">move at the speed of the slowest participant</tspan>
    </text>
  </g>

  <!-- ==================== BOTTOM BAR ==================== -->
  <g id="box-bottom-bar">
    <rect x="40" y="1047" width="1520" height="60" rx="12" fill="#207448" />
    <text x="800" y="1085" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">
      <tspan x="800" dy="0">Treat a PFC change on one switch as a change to the whole fabric</tspan>
    </text>
  </g>

</svg>'''
    return svg

open("candidate_lossless.svg", "w").write(generate_svg())
print("Saved candidate_lossless.svg")
