import re

svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>Five AI fabrics against the layers: which one carries what</title>
  <desc>Five AI fabrics against the layers: which one carries what</desc>

  <!-- Background -->
  <rect width="1600" height="1200" fill="#f5f8f5"/>

  <!-- Title (well inside canvas, 2 lines) -->
  <text x="40" y="70" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="40" dy="0">Five AI fabrics against the layers:</tspan>
    <tspan x="40" dy="56">which one carries what</tspan>
  </text>

  <!-- COLUMN HEADERS -->
  <!-- Col 1 Header: L1/L2 -->
  <rect x="355" y="165" width="250" height="55" rx="8" fill="#207448"/>
  <text x="480" y="203" font-family="sans-serif" font-size="30" font-weight="bold" fill="#ffffff" text-anchor="middle">
    <tspan x="480" dy="0">L1/L2</tspan>
  </text>

  <!-- Col 2 Header: L3 -->
  <rect x="615" y="165" width="250" height="55" rx="8" fill="#207448"/>
  <text x="740" y="203" font-family="sans-serif" font-size="30" font-weight="bold" fill="#ffffff" text-anchor="middle">
    <tspan x="740" dy="0">L3</tspan>
  </text>

  <!-- Col 3 Header: L4 and transport -->
  <rect x="875" y="165" width="365" height="55" rx="8" fill="#207448"/>
  <text x="1057" y="203" font-family="sans-serif" font-size="30" font-weight="bold" fill="#ffffff" text-anchor="middle">
    <tspan x="1057" dy="0">L4 and transport</tspan>
  </text>

  <!-- ==================== ROW 1: Ethernet with TCP ==================== -->
  <!-- Row 1 Fabric Header -->
  <rect x="40" y="235" width="305" height="155" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <text x="56" y="272" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">
    <tspan x="56" dy="0">Ethernet with</tspan>
    <tspan x="56" dy="34">TCP (front end,</tspan>
    <tspan x="56" dy="34">storage,</tspan>
    <tspan x="56" dy="34">control plane)</tspan>
  </text>

  <!-- Row 1, Col 1: Ethernet 25/100/400 GbE -->
  <rect x="355" y="235" width="250" height="155" rx="8" fill="#ffffff" stroke="#c2d6c6" stroke-width="2"/>
  <text x="375" y="302" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="375" dy="0">Ethernet</tspan>
    <tspan x="375" dy="32">25/100/400 GbE</tspan>
  </text>

  <!-- Row 1, Col 2: IP (BGP/ECMP in Clos) -->
  <rect x="615" y="235" width="250" height="155" rx="8" fill="#ffffff" stroke="#c2d6c6" stroke-width="2"/>
  <text x="635" y="302" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="635" dy="0">IP (BGP/ECMP</tspan>
    <tspan x="635" dy="32">in Clos)</tspan>
  </text>

  <!-- Row 1, Col 3: TCP and UDP in the kernel; CUBIC or BBR -->
  <rect x="875" y="235" width="365" height="155" rx="8" fill="#ffffff" stroke="#c2d6c6" stroke-width="2"/>
  <text x="895" y="302" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="895" dy="0">TCP and UDP in the</tspan>
    <tspan x="895" dy="32">kernel; CUBIC or BBR</tspan>
  </text>

  <!-- ==================== ROW 2: RoCE v2 ==================== -->
  <!-- Row 2 Fabric Header -->
  <rect x="40" y="402" width="305" height="155" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <text x="56" y="490" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">
    <tspan x="56" dy="0">RoCE v2</tspan>
  </text>

  <!-- Row 2, Col 1: Lossless Ethernet (PFC, ECN, DCB) -->
  <rect x="355" y="402" width="250" height="155" rx="8" fill="#ffffff" stroke="#c2d6c6" stroke-width="2"/>
  <text x="375" y="456" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="375" dy="0">Lossless</tspan>
    <tspan x="375" dy="30">Ethernet</tspan>
    <tspan x="375" dy="30">(PFC, ECN, DCB)</tspan>
  </text>

  <!-- Row 2, Col 2: IP, routable -->
  <rect x="615" y="402" width="250" height="155" rx="8" fill="#ffffff" stroke="#c2d6c6" stroke-width="2"/>
  <text x="635" y="485" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="635" dy="0">IP, routable</tspan>
  </text>

  <!-- Row 2, Col 3 (ORANGE HIGHLIGHT): UDP 4791 plus IB transport (BTH) in the NIC; RDMA verbs bypass the kernel stack -->
  <rect x="875" y="402" width="365" height="155" rx="8" fill="#fff7ed" stroke="#db8129" stroke-width="3"/>
  <text x="895" y="442" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="895" dy="0">UDP 4791 plus IB</tspan>
    <tspan x="895" dy="28">transport (BTH) in the</tspan>
    <tspan x="895" dy="28">NIC; RDMA verbs bypass</tspan>
    <tspan x="895" dy="28">the kernel stack</tspan>
  </text>

  <!-- ==================== ROW 3: InfiniBand ==================== -->
  <!-- Row 3 Fabric Header -->
  <rect x="40" y="569" width="305" height="180" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <text x="56" y="668" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">
    <tspan x="56" dy="0">InfiniBand</tspan>
  </text>

  <!-- Row 3, Col 1: IB link layer, credit-based, virtual lanes -->
  <rect x="355" y="569" width="250" height="180" rx="8" fill="#ffffff" stroke="#c2d6c6" stroke-width="2"/>
  <text x="375" y="637" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="375" dy="0">IB link layer,</tspan>
    <tspan x="375" dy="30">credit-based,</tspan>
    <tspan x="375" dy="30">virtual lanes</tspan>
  </text>

  <!-- Row 3, Col 2: IB network layer, GIDs, LIDs inside subnets, GRH across -->
  <rect x="615" y="569" width="250" height="180" rx="8" fill="#ffffff" stroke="#c2d6c6" stroke-width="2"/>
  <text x="635" y="609" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="635" dy="0">IB network</tspan>
    <tspan x="635" dy="28">layer, GIDs,</tspan>
    <tspan x="635" dy="28">LIDs inside</tspan>
    <tspan x="635" dy="28">subnets, GRH</tspan>
    <tspan x="635" dy="28">across</tspan>
  </text>

  <!-- Row 3, Col 3: IB transport RC/UD in the NIC; Subnet Manager computes forwarding tables -->
  <rect x="875" y="569" width="365" height="180" rx="8" fill="#ffffff" stroke="#c2d6c6" stroke-width="2"/>
  <text x="895" y="623" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="895" dy="0">IB transport RC/UD in</tspan>
    <tspan x="895" dy="28">the NIC; Subnet</tspan>
    <tspan x="895" dy="28">Manager computes</tspan>
    <tspan x="895" dy="28">forwarding tables</tspan>
  </text>

  <!-- ==================== ROW 4: NVLink / NVSwitch ==================== -->
  <!-- Row 4 Fabric Header -->
  <rect x="40" y="761" width="305" height="145" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <text x="56" y="828" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">
    <tspan x="56" dy="0">NVLink /</tspan>
    <tspan x="56" dy="34">NVSwitch</tspan>
  </text>

  <!-- Row 4, Col 1: proprietary GPU-to-GPU links -->
  <rect x="355" y="761" width="250" height="145" rx="8" fill="#ffffff" stroke="#c2d6c6" stroke-width="2"/>
  <text x="375" y="817" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="375" dy="0">proprietary</tspan>
    <tspan x="375" dy="28">GPU-to-GPU</tspan>
    <tspan x="375" dy="28">links</tspan>
  </text>

  <!-- Row 4, Col 2: no IP, memory-semantic -->
  <rect x="615" y="761" width="250" height="145" rx="8" fill="#ffffff" stroke="#c2d6c6" stroke-width="2"/>
  <text x="635" y="831" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="635" dy="0">no IP,</tspan>
    <tspan x="635" dy="30">memory-semantic</tspan>
  </text>

  <!-- Row 4, Col 3: load/store and DMA between GPUs -->
  <rect x="875" y="761" width="365" height="145" rx="8" fill="#ffffff" stroke="#c2d6c6" stroke-width="2"/>
  <text x="895" y="831" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="895" dy="0">load/store and DMA</tspan>
    <tspan x="895" dy="30">between GPUs</tspan>
  </text>

  <!-- ==================== ROW 5: PCIe ==================== -->
  <!-- Row 5 Fabric Header -->
  <rect x="40" y="918" width="305" height="135" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <text x="56" y="995" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">
    <tspan x="56" dy="0">PCIe</tspan>
  </text>

  <!-- Row 5, Col 1: serial links, TLPs -->
  <rect x="355" y="918" width="250" height="135" rx="8" fill="#ffffff" stroke="#c2d6c6" stroke-width="2"/>
  <text x="375" y="977" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="375" dy="0">serial links,</tspan>
    <tspan x="375" dy="30">TLPs</tspan>
  </text>

  <!-- Row 5, Col 2: a bus -->
  <rect x="615" y="918" width="250" height="135" rx="8" fill="#ffffff" stroke="#c2d6c6" stroke-width="2"/>
  <text x="635" y="993" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="635" dy="0">a bus</tspan>
  </text>

  <!-- Row 5, Col 3: GPU-NIC-CPU paths; locality matters -->
  <rect x="875" y="918" width="365" height="135" rx="8" fill="#ffffff" stroke="#c2d6c6" stroke-width="2"/>
  <text x="895" y="977" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="895" dy="0">GPU-NIC-CPU paths;</tspan>
    <tspan x="895" dy="30">locality matters</tspan>
  </text>

  <!-- ==================== RIGHT STRIP: NCCL hierarchy ==================== -->
  <!-- Outer Container -->
  <rect x="1265" y="165" width="295" height="888" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>

  <!-- Right Strip Header -->
  <rect x="1265" y="165" width="295" height="55" rx="8" fill="#207448"/>
  <text x="1412" y="203" font-family="sans-serif" font-size="30" font-weight="bold" fill="#ffffff" text-anchor="middle">
    <tspan x="1412" dy="0">NCCL hierarchy</tspan>
  </text>

  <!-- Right Strip Item 1: NVLink inside the node -->
  <rect x="1278" y="245" width="269" height="235" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <g stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" fill="none">
    <rect x="1384" y="275" width="56" height="56" rx="6"/>
    <circle cx="1412" cy="303" r="14"/>
    <line x1="1397" y1="265" x2="1397" y2="275"/>
    <line x1="1427" y1="265" x2="1427" y2="275"/>
    <line x1="1397" y1="331" x2="1397" y2="341"/>
    <line x1="1427" y1="331" x2="1427" y2="341"/>
  </g>
  <text x="1412" y="390" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36" text-anchor="middle">
    <tspan x="1412" dy="0">NVLink inside</tspan>
    <tspan x="1412" dy="30">the node</tspan>
  </text>

  <!-- Right Strip Item 2: NIC and fabric between nodes -->
  <rect x="1278" y="510" width="269" height="235" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <g stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" fill="none">
    <rect x="1384" y="540" width="56" height="42" rx="4"/>
    <line x1="1398" y1="561" x2="1404" y2="561"/>
    <line x1="1420" y1="561" x2="1426" y2="561"/>
    <path d="M 1394 582 L 1394 602 L 1430 602 L 1430 582"/>
  </g>
  <text x="1412" y="655" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36" text-anchor="middle">
    <tspan x="1412" dy="0">NIC and fabric</tspan>
    <tspan x="1412" dy="30">between nodes</tspan>
  </text>

  <!-- Right Strip Item 3: TCP sockets as the fallback and for bootstrap -->
  <rect x="1278" y="775" width="269" height="255" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <g stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" fill="none">
    <circle cx="1397" cy="815" r="14"/>
    <circle cx="1427" cy="845" r="14"/>
    <path d="M 1407 825 L 1417 835"/>
  </g>
  <text x="1412" y="910" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36" text-anchor="middle">
    <tspan x="1412" dy="0">TCP sockets as the</tspan>
    <tspan x="1412" dy="30">fallback and for</tspan>
    <tspan x="1412" dy="30">bootstrap</tspan>
  </text>

  <!-- ==================== BOTTOM BAR ==================== -->
  <rect x="40" y="1080" width="1520" height="75" rx="8" fill="#207448"/>
  <text x="800" y="1127" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff" text-anchor="middle">
    <tspan x="800" dy="0">When a collective runs slowly, first find out which link in this hierarchy it is using</tspan>
  </text>
</svg>'''

with open("perfect_fabrics.svg", "w") as f:
    f.write(svg.strip())
print("Saved perfect_fabrics.svg")
