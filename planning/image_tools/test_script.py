import xml.etree.ElementTree as ET
import re

svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1120" width="1600" height="1120">
  <title>On-link or via the gateway: the first decision a host makes</title>
  <desc>Flowchart showing a host deciding between on-link ARP resolution and the default gateway using subnet masking, with failure cases for too wide and too narrow subnet masks.</desc>

  <defs>
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1600" height="1120" fill="#f5f8f5" />

  <!-- Title -->
  <text x="800" y="58" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">On-link or via the gateway:</tspan>
    <tspan x="800" dy="54">the first decision a host makes</tspan>
  </text>

  <!-- ==================== FLOW SECTION ==================== -->

  <!-- Top Box: Packet to send -->
  <g id="box-packet">
    <rect x="380" y="135" width="840" height="85" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Icon: Network packet / frame header -->
    <g transform="translate(406, 150)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="8" width="48" height="38" rx="6" />
      <line x1="4" y1="20" x2="52" y2="20" />
      <line x1="28" y1="8" x2="28" y2="20" />
      <circle cx="16" cy="33" r="3" fill="#207448" />
      <line x1="26" y1="33" x2="44" y2="33" />
    </g>
    <text x="815" y="188" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Packet to send: my address and the destination address</text>
  </g>

  <!-- Arrow 1: Box -> Step -->
  <line x1="800" y1="220" x2="800" y2="255" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />

  <!-- Step Box: AND each address -->
  <g id="step-and">
    <rect x="400" y="255" width="800" height="80" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Icon: Logic AND gate / bitmask -->
    <g transform="translate(426, 267)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 12 10 L 26 10 A 18 18 0 0 1 26 46 L 12 46 Z" />
      <line x1="4" y1="20" x2="12" y2="20" />
      <line x1="4" y1="36" x2="12" y2="36" />
      <line x1="44" y1="28" x2="52" y2="28" />
    </g>
    <text x="825" y="306" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">AND each address with my subnet mask</text>
  </g>

  <!-- Arrow 2: Step -> Diamond -->
  <line x1="800" y1="335" x2="800" y2="365" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />

  <!-- Diamond: Do the two results match? -->
  <g id="diamond-decision">
    <polygon points="800,365 950,425 800,485 650,425" fill="#e8f1ea" stroke="#207448" stroke-width="3" />
    <text x="800" y="418" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36">
      <tspan x="800" dy="0">Do the two</tspan>
      <tspan x="800" dy="32">results match?</tspan>
    </text>
  </g>

  <!-- Arrow 3: Diamond -> Left outcome (Yes) -->
  <line x1="650" y1="425" x2="580" y2="425" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />
  <text x="615" y="405" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#207448">Yes</text>

  <!-- Left Outcome: Destination is on-link -->
  <g id="outcome-on-link">
    <rect x="60" y="350" width="520" height="150" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Icon: Direct host-to-host Ethernet LAN connection -->
    <g transform="translate(82, 365)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="8" width="18" height="14" rx="3" />
      <rect x="32" y="8" width="18" height="14" rx="3" />
      <line x1="15" y1="22" x2="15" y2="36" />
      <line x1="41" y1="22" x2="41" y2="36" />
      <line x1="6" y1="36" x2="50" y2="36" />
      <circle cx="15" cy="36" r="3" fill="#207448" />
      <circle cx="41" cy="36" r="3" fill="#207448" />
    </g>
    <text x="330" y="400" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36">
      <tspan x="330" dy="0" font-size="30">Destination is on-link:</tspan>
      <tspan x="330" dy="36" font-size="24" font-weight="normal">ARP for the destination itself,</tspan>
      <tspan x="330" dy="32" font-size="24" font-weight="normal">send the frame to its MAC</tspan>
    </text>
  </g>

  <!-- Arrow 4: Diamond -> Right outcome (No) -->
  <line x1="950" y1="425" x2="1020" y2="425" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />
  <text x="985" y="405" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36">No</text>

  <!-- Right Outcome: Gateway -->
  <g id="outcome-gateway">
    <rect x="1020" y="350" width="520" height="150" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Icon: Router / Gateway -->
    <g transform="translate(1042, 365)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="22" />
      <polyline points="20 18 28 10 36 18" />
      <line x1="28" y1="10" x2="28" y2="22" />
      <polyline points="20 38 28 46 36 38" />
      <line x1="28" y1="34" x2="28" y2="46" />
      <line x1="14" y1="28" x2="42" y2="28" />
    </g>
    <text x="1290" y="415" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36">
      <tspan x="1290" dy="0" font-size="30">Send the frame to the</tspan>
      <tspan x="1290" dy="38" font-size="26" font-weight="normal">default gateway's MAC address</tspan>
    </text>
  </g>

  <!-- ==================== FAILURE CASES (SIDE BY SIDE) ==================== -->

  <!-- Left: Mask too wide (Orange Highlight) -->
  <g id="failure-wide">
    <rect x="60" y="540" width="710" height="230" rx="14" fill="#e8f1ea" stroke="#db8129" stroke-width="4" />
    <!-- Icon: Warning alert / broadcast issue (orange) -->
    <g transform="translate(86, 560)" stroke="#db8129" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 28 6 L 50 48 L 6 48 Z" />
      <line x1="28" y1="20" x2="28" y2="32" />
      <circle cx="28" cy="40" r="2" fill="#db8129" />
    </g>
    <text x="160" y="598" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Mask too wide</text>
    <text x="86" y="642" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="86" dy="0">the host treats off-link addresses as on-link</tspan>
      <tspan x="86" dy="34">and ARPs for them; nobody answers;</tspan>
      <tspan x="86" dy="34">symptom: no route to host</tspan>
    </text>
  </g>

  <!-- Right: Mask too narrow -->
  <g id="failure-narrow">
    <rect x="830" y="540" width="710" height="230" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Icon: Detour / ICMP redirect loop -->
    <g transform="translate(856, 560)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 12 44 V 24 A 16 16 0 0 1 44 24 V 44" />
      <polyline points="36 36 44 44 52 36" />
      <circle cx="12" cy="44" r="3" fill="#207448" />
    </g>
    <text x="930" y="598" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Mask too narrow</text>
    <text x="856" y="642" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="856" dy="0">on-link traffic goes to the router instead;</tspan>
      <tspan x="856" dy="34">still works but inefficient,</tspan>
      <tspan x="856" dy="34">and may trigger ICMP redirects</tspan>
    </text>
  </g>

  <!-- ==================== SIDE STRIP ==================== -->
  <g id="side-strip">
    <rect x="60" y="810" width="1480" height="130" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Icon: Terminal window / console diagnostics -->
    <g transform="translate(90, 847)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="6" width="48" height="42" rx="6" />
      <line x1="4" y1="18" x2="52" y2="18" />
      <circle cx="12" cy="12" r="2" fill="#207448" />
      <circle cx="18" cy="12" r="2" fill="#207448" />
      <path d="M 14 26 L 22 32 L 14 38" />
      <line x1="26" y1="38" x2="38" y2="38" />
    </g>
    <text x="175" y="865" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="175" dy="0">Where this check shows: <tspan font-family="monospace">ip neigh</tspan> shows <tspan font-family="monospace">FAILED</tspan> or <tspan font-family="monospace">INCOMPLETE</tspan></tspan>
      <tspan x="175" dy="36">for an address that should have been reached through the gateway</tspan>
    </text>
  </g>

  <!-- ==================== BOTTOM BAR ==================== -->
  <g id="bottom-bar">
    <rect x="60" y="980" width="1480" height="80" rx="12" fill="#207448" />
    <text x="800" y="1030" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">A wrong mask means the host's picture of who is on my street is wrong</text>
  </g>
</svg>'''

with open('test_candidate_p3_0203.svg', 'w') as f:
    f.write(svg_content)

print("Saved test_candidate_p3_0203.svg")
