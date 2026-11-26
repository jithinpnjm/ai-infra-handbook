import xml.etree.ElementTree as ET

svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 980" width="1600" height="980">
  <title>Two hosts share a subnet when the mask strips them to the same network</title>
  <desc>A two-row comparison demonstrating how subnet masks determine whether hosts share a subnet: Host A matches 10.20.36.0/22 for direct ARP delivery, while Host B results in a different network and routes to the gateway.</desc>

  <defs>
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1600" height="980" fill="#f5f8f5" />

  <!-- Title: 48px bold -->
  <text x="800" y="58" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">Two hosts share a subnet when the mask</tspan>
    <tspan x="800" dy="54">strips them to the same network</tspan>
  </text>

  <!-- ==================== TOP ROW: HOST A ==================== -->
  <rect x="40" y="148" width="1040" height="244" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />

  <!-- Box 1: Address A -->
  <rect x="64" y="164" width="460" height="100" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
  <g transform="translate(80, 186)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <!-- Server / Host Icon (56x56) -->
    <rect x="4" y="6" width="48" height="18" rx="4" />
    <rect x="4" y="32" width="48" height="18" rx="4" />
    <circle cx="12" cy="15" r="2" fill="#207448" />
    <circle cx="20" cy="15" r="2" fill="#207448" />
    <circle cx="12" cy="41" r="2" fill="#207448" />
    <circle cx="20" cy="41" r="2" fill="#207448" />
    <line x1="36" y1="15" x2="44" y2="15" />
    <line x1="36" y1="41" x2="44" y2="41" />
  </g>
  <text x="156" y="204" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36">
    <tspan x="156" dy="0">Address A: </tspan>
    <tspan x="156" dy="34">10.20.37.130</tspan>
  </text>

  <!-- Box 2: Mask -->
  <rect x="548" y="164" width="508" height="100" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
  <g transform="translate(564, 186)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <!-- Filter / Mask Icon (56x56) -->
    <path d="M 6 10 L 50 10 L 34 30 L 34 46 L 22 46 L 22 30 Z" />
  </g>
  <text x="640" y="204" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36">
    <tspan x="640" dy="0">Mask: /22 </tspan>
    <tspan x="640" dy="34">(third octet 252)</tspan>
  </text>

  <!-- Grouping lines and Arrow down to Box 3 -->
  <path d="M 294 264 L 294 284 L 802 284 L 802 264" fill="none" stroke="#207448" stroke-width="3" />
  <line x1="548" y1="284" x2="548" y2="308" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- Box 3: A AND mask = 10.20.36.0 network -->
  <rect x="200" y="310" width="696" height="66" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
  <g transform="translate(216, 318)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <!-- Logic Gate / CPU Calculation Icon (46x46) -->
    <rect x="4" y="4" width="38" height="38" rx="6" />
    <path d="M 12 16 L 23 23 L 12 30" />
    <line x1="23" y1="30" x2="33" y2="30" />
  </g>
  <text x="278" y="352" font-family="monospace" font-size="26" font-weight="bold" fill="#303a36">A AND mask = 10.20.36.0 network</text>

  <!-- ==================== BOTTOM ROW: HOST B ==================== -->
  <rect x="40" y="412" width="1040" height="244" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />

  <!-- Box 4: Address B -->
  <rect x="300" y="430" width="496" height="100" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
  <g transform="translate(320, 452)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <!-- Server / Host Icon (56x56) -->
    <rect x="4" y="6" width="48" height="18" rx="4" />
    <rect x="4" y="32" width="48" height="18" rx="4" />
    <circle cx="12" cy="15" r="2" fill="#207448" />
    <circle cx="20" cy="15" r="2" fill="#207448" />
    <circle cx="12" cy="41" r="2" fill="#207448" />
    <circle cx="20" cy="41" r="2" fill="#207448" />
    <line x1="36" y1="15" x2="44" y2="15" />
    <line x1="36" y1="41" x2="44" y2="41" />
  </g>
  <text x="395" y="470" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36">
    <tspan x="395" dy="0">Address B: </tspan>
    <tspan x="395" dy="34">10.20.40.1</tspan>
  </text>

  <!-- Arrow down to Box 5 -->
  <line x1="548" y1="530" x2="548" y2="573" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- Box 5: B AND mask = 10.20.40.0 network (Orange Outline) -->
  <rect x="200" y="575" width="696" height="66" rx="10" fill="#ffffff" stroke="#db8129" stroke-width="4" />
  <g transform="translate(216, 583)" stroke="#db8129" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <!-- Logic Gate / CPU Calculation Icon (46x46) -->
    <rect x="4" y="4" width="38" height="38" rx="6" />
    <path d="M 12 16 L 23 23 L 12 30" />
    <line x1="23" y1="30" x2="33" y2="30" />
  </g>
  <text x="278" y="617" font-family="monospace" font-size="26" font-weight="bold" fill="#303a36">B AND mask = 10.20.40.0 network</text>

  <!-- ==================== SIDE NOTE: SUBNET RANGE ==================== -->
  <rect x="1120" y="148" width="440" height="508" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  <g transform="translate(1312, 185)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <!-- Network Subnet Bracket / Range Icon (56x56) -->
    <rect x="4" y="6" width="48" height="44" rx="6" />
    <line x1="4" y1="20" x2="52" y2="20" />
    <circle cx="16" cy="34" r="4" fill="#207448" />
    <circle cx="40" cy="34" r="4" fill="#207448" />
    <line x1="20" y1="34" x2="36" y2="34" />
  </g>
  <rect x="1140" y="275" width="400" height="350" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
  <text x="1165" y="350" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
    <tspan x="1165" dy="0">10.20.36.0/22 covers </tspan>
    <tspan x="1165" dy="48">third octets 36 to 39, </tspan>
    <tspan x="1165" dy="48">so 10.20.36.0 to </tspan>
    <tspan x="1165" dy="48">10.20.39.255</tspan>
  </text>

  <!-- ==================== BOTTOM RESULT BOXES ==================== -->
  <!-- Left Result: Direct ARP -->
  <rect x="40" y="685" width="740" height="145" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  <g transform="translate(68, 730)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <!-- Green Tick Circle Icon (56x56) -->
    <circle cx="28" cy="28" r="24" />
    <polyline points="16,28 24,36 40,20" />
  </g>
  <text x="148" y="746" font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448">
    <tspan x="148" dy="0">Same network as 10.20.36.0/22: </tspan>
    <tspan x="148" dy="42">direct on the link (ARP)</tspan>
  </text>

  <!-- Right Result: Gateway -->
  <rect x="820" y="685" width="740" height="145" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2" />
  <g transform="translate(848, 730)" stroke="#c0392b" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <!-- Red Cross Circle Icon (56x56) -->
    <circle cx="28" cy="28" r="24" />
    <line x1="18" y1="18" x2="38" y2="38" />
    <line x1="38" y1="18" x2="18" y2="38" />
  </g>
  <text x="928" y="746" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">
    <tspan x="928" dy="0">Different network: </tspan>
    <tspan x="928" dy="42">send to the gateway</tspan>
  </text>

  <!-- ==================== TAKEAWAY BAR / CAPTION ==================== -->
  <rect x="40" y="860" width="1520" height="75" rx="12" fill="#207448" />
  <text x="800" y="907" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">Every host runs this check for every packet it sends.</text>
</svg>
"""

with open("test_candidate.svg", "w") as f:
    f.write(svg_content.strip())

print("Wrote updated test_candidate.svg")
