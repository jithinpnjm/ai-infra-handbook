import xml.etree.ElementTree as ET
import re

svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1080" width="1600" height="1080">
  <title>Turning an Xid code into ignore, suspect or drain</title>
  <desc>Flowchart showing the fleet policy for handling NVIDIA GPU Xid errors by catalog action and repeat frequency into ignore, suspect, or drain.</desc>

  <defs>
    <!-- Proportional green arrowhead (18px) -->
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448"/>
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1600" height="1080" fill="#f5f8f5"/>

  <!-- ==================== TITLE ==================== -->
  <text x="800" y="55" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Turning an Xid code into ignore, suspect or drain</text>

  <!-- ==================== START BOX ==================== -->
  <g id="start-box">
    <rect x="680" y="85" width="560" height="80" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5"/>
    <!-- Small chip icon (56px, stroke 3.5, #207448) -->
    <g transform="translate(705, 97)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="10" y="10" width="36" height="36" rx="4"/>
      <line x1="18" y1="4" x2="18" y2="10"/>
      <line x1="28" y1="4" x2="28" y2="10"/>
      <line x1="38" y1="4" x2="38" y2="10"/>
      <line x1="18" y1="46" x2="18" y2="52"/>
      <line x1="28" y1="46" x2="28" y2="52"/>
      <line x1="38" y1="46" x2="38" y2="52"/>
      <line x1="4" y1="18" x2="10" y2="18"/>
      <line x1="4" y1="28" x2="10" y2="28"/>
      <line x1="4" y1="38" x2="10" y2="38"/>
      <line x1="46" y1="18" x2="52" y2="18"/>
      <line x1="46" y1="28" x2="52" y2="28"/>
      <line x1="46" y1="38" x2="52" y2="38"/>
    </g>
    <text x="1000" y="136" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Xid reported on a node</text>
  </g>

  <!-- Arrow 1: Start box -> Step 1 -->
  <line x1="960" y1="165" x2="960" y2="213" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>

  <!-- ==================== STEP 1 DECISION ==================== -->
  <g id="step-1">
    <!-- Number circle 1 -->
    <circle cx="610" cy="180" r="24" fill="#207448"/>
    <text x="610" y="189" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">1</text>

    <!-- Step 1 Box -->
    <rect x="680" y="215" width="560" height="80" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
    <!-- Catalog icon -->
    <g transform="translate(705, 227)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="8" y="8" width="40" height="40" rx="4"/>
      <line x1="16" y1="18" x2="36" y2="18"/>
      <line x1="16" y1="28" x2="36" y2="28"/>
      <line x1="16" y1="38" x2="28" y2="38"/>
    </g>
    <text x="1000" y="266" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Code in the catalog?</text>
  </g>

  <!-- Arrow 2: Step 1 (If no) -> Suspect -->
  <path d="M 680 255 L 200 255 L 200 523" fill="none" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>

  <!-- Arrow 3: Step 1 (If yes) -> Step 2 -->
  <line x1="960" y1="295" x2="960" y2="343" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>

  <!-- ==================== STEP 2 DECISION ==================== -->
  <g id="step-2">
    <!-- Number circle 2 -->
    <circle cx="610" cy="310" r="24" fill="#207448"/>
    <text x="610" y="319" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">2</text>

    <!-- Step 2 Box -->
    <rect x="680" y="345" width="560" height="80" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
    <!-- Gear icon -->
    <g transform="translate(705, 357)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="10"/>
      <path d="M 28 8 L 28 14 M 28 42 L 28 48 M 8 28 L 14 28 M 42 28 L 48 28 M 14 14 L 18 18 M 38 38 L 42 42 M 14 42 L 18 38 M 38 18 L 42 14"/>
    </g>
    <text x="1000" y="396" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Catalog action</text>
  </g>

  <!-- ==================== SUSPECT BOX (COLUMN 1) ==================== -->
  <g id="suspect-node">
    <rect x="40" y="525" width="320" height="225" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5"/>
    <!-- Shield/alert icon -->
    <g transform="translate(172, 545)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 12 10 L 28 4 L 44 10 C 44 32 28 48 28 48 C 28 48 12 32 12 10 Z"/>
      <line x1="28" y1="18" x2="28" y2="30"/>
      <circle cx="28" cy="37" r="1.5" fill="#207448"/>
    </g>
    <text x="200" y="635" text-anchor="middle" font-family="sans-serif" font-size="34" font-weight="bold" fill="#303a36">Suspect</text>
    <text x="200" y="682" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="200" dy="0">never ignore an</tspan>
      <tspan x="200" dy="30">unknown code</tspan>
    </text>
  </g>

  <!-- ==================== BRANCH B: RESTART_APP & REPEAT DECISION (COLUMN 2) ==================== -->
  <!-- Arrow 5: Step 2 -> Repeat Decision -->
  <path d="M 780 425 L 780 455 L 430 455 L 430 573" fill="none" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>

  <!-- Branch B Badge beside Arrow 5 -->
  <rect x="450" y="465" width="280" height="95" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
  <text x="590" y="492" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="590" dy="0" font-weight="bold" fill="#207448">application-level,</tspan>
    <tspan x="590" dy="28" font-weight="bold" fill="#207448">RESTART_APP</tspan>
    <tspan x="590" dy="28">(for example Xid 13, 31, 94)</tspan>
  </text>

  <!-- Repeat Decision Box -->
  <g id="repeat-decision">
    <rect x="410" y="575" width="340" height="175" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
    <!-- Timer/Clock icon placed centered above text -->
    <g transform="translate(556, 587)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="24" cy="24" r="20"/>
      <polyline points="24,10 24,24 34,24"/>
    </g>
    <text x="580" y="662" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
      <tspan x="580" dy="0">Same code three</tspan>
      <tspan x="580" dy="30">times within an hour</tspan>
      <tspan x="580" dy="30">on this node?</tspan>
    </text>
  </g>

  <!-- Memory note beside Repeat Decision -->
  <g id="memory-note">
    <rect x="790" y="605" width="210" height="120" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" stroke-dasharray="6 4"/>
    <!-- Memory RAM chip icon -->
    <g transform="translate(871, 617)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="6" width="48" height="24" rx="3"/>
      <rect x="9" y="11" width="6" height="8" fill="#e8f1ea"/>
      <rect x="19" y="11" width="6" height="8" fill="#e8f1ea"/>
      <rect x="29" y="11" width="6" height="8" fill="#e8f1ea"/>
      <rect x="39" y="11" width="6" height="8" fill="#e8f1ea"/>
      <line x1="11" y1="30" x2="11" y2="36"/>
      <line x1="19" y1="30" x2="19" y2="36"/>
      <line x1="27" y1="30" x2="27" y2="36"/>
      <line x1="35" y1="30" x2="35" y2="36"/>
      <line x1="43" y1="30" x2="43" y2="36"/>
    </g>
    <text x="895" y="675" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="895" dy="0">recent Xid times</tspan>
      <tspan x="895" dy="30">kept per node</tspan>
    </text>
  </g>

  <!-- Arrow 6: Repeat Decision (If no) -> Suspect -->
  <line x1="410" y1="637" x2="362" y2="637" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>

  <!-- Arrow 7: Repeat Decision (If yes) -> Drain -->
  <line x1="580" y1="750" x2="580" y2="788" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>

  <!-- Drain Outcome Box -->
  <g id="drain-box">
    <rect x="450" y="790" width="260" height="110" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5"/>
    <!-- Drain/Exit icon -->
    <g transform="translate(470, 817)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 8 12 L 28 32 L 48 12"/>
      <line x1="28" y1="4" x2="28" y2="44"/>
      <line x1="12" y1="50" x2="44" y2="50"/>
    </g>
    <text x="610" y="858" text-anchor="middle" font-family="sans-serif" font-size="34" font-weight="bold" fill="#303a36">Drain</text>
  </g>

  <!-- ==================== BRANCH A: IGNORE (COLUMN 3) ==================== -->
  <!-- Arrow 4: Step 2 -> Ignore -->
  <path d="M 960 425 L 960 455 L 1025 455 L 1025 788" fill="none" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>

  <!-- Branch A Badge beside Arrow 4 -->
  <rect x="1050" y="525" width="210" height="115" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
  <text x="1155" y="555" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="1155" dy="0" font-weight="bold" fill="#207448">IGNORE</tspan>
    <tspan x="1155" dy="30">(for example</tspan>
    <tspan x="1155" dy="30">Xid 43, 63)</tspan>
  </text>

  <!-- Ignore Outcome Box (Green box) -->
  <g id="ignore-box">
    <rect x="1040" y="790" width="230" height="110" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
    <!-- Pass/Check icon -->
    <g transform="translate(1060, 817)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="22"/>
      <path d="M 18 28 L 25 35 L 38 21"/>
    </g>
    <text x="1180" y="858" text-anchor="middle" font-family="sans-serif" font-size="34" font-weight="bold" fill="#207448">Ignore</text>
  </g>

  <!-- ==================== BRANCH C: RESET/REBOOT/LINK (COLUMN 4) ==================== -->
  <!-- Arrow 8: Step 2 -> Drain at once -->
  <path d="M 1140 425 L 1140 455 L 1295 455 L 1295 788" fill="none" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>

  <!-- Branch C Badge beside Arrow 8 -->
  <rect x="1315" y="495" width="245" height="180" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
  <text x="1437" y="525" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="1437" dy="0" font-weight="bold" fill="#207448">reset, reboot</tspan>
    <tspan x="1437" dy="28" font-weight="bold" fill="#207448">or link</tspan>
    <tspan x="1437" dy="28">(for example</tspan>
    <tspan x="1437" dy="28">Xid 48, 64,</tspan>
    <tspan x="1437" dy="28">79, 95, 119,</tspan>
    <tspan x="1437" dy="28">120, 74)</tspan>
  </text>

  <!-- Drain at once Outcome Box (Single orange highlight box) -->
  <g id="drain-at-once-box">
    <rect x="1310" y="790" width="250" height="110" rx="14" fill="#fff9f2" stroke="#db8129" stroke-width="3"/>
    <text x="1435" y="858" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#db8129">Drain at once</text>
  </g>

  <!-- ==================== GREEN TAKEAWAY BAR ==================== -->
  <g id="takeaway-bar">
    <rect x="40" y="940" width="1520" height="100" rx="14" fill="#207448"/>
    <text x="800" y="983" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">
      <tspan x="800" dy="0">Translate the catalog into ignore, suspect and drain,</tspan>
      <tspan x="800" dy="34">and never ignore a code you do not recognise.</tspan>
    </text>
  </g>
</svg>'''

with open("candidate_clean.svg", "w") as f:
    f.write(svg_content)

print("Saved candidate_clean.svg")
