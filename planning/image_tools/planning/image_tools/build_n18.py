import re
import xml.etree.ElementTree as ET

def generate_svg():
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1020" viewBox="0 0 1600 1020">
  <title>Capacity left after a spine fails</title>
  <desc>Visual comparison showing capacity kept = (S-1)/S of uplink capacity after a spine failure, comparing 32 spines at 96.9% with 4 spines at 75%.</desc>

  <!-- Background -->
  <rect width="1600" height="1020" fill="#f5f8f5" />

  <!-- Diagram Title -->
  <text x="800" y="65" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Capacity left after a spine fails</text>

  <!-- ==================== FORMULA BANNER ==================== -->
  <rect x="50" y="100" width="1500" height="80" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
  
  <!-- Formula Icon: Math / Logic symbol -->
  <g transform="translate(85, 115)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="4" y="4" width="42" height="42" rx="8" />
    <line x1="14" y1="20" x2="36" y2="20" />
    <line x1="14" y1="30" x2="36" y2="30" />
    <circle cx="25" cy="13" r="2" fill="#207448" />
    <circle cx="25" cy="37" r="2" fill="#207448" />
  </g>

  <!-- Formula Text -->
  <text x="800" y="150" text-anchor="middle" font-family="monospace" font-size="28" font-weight="bold" fill="#303a36">capacity kept = (S-1)/S of uplink capacity</text>

  <!-- ==================== LEFT PANEL: SMALL LEAF WITH UPLINKS ==================== -->
  <rect x="50" y="210" width="480" height="540" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

  <!-- Left Header Icon: Switch / Topology Node -->
  <g transform="translate(262, 230)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="4" y="6" width="48" height="44" rx="6" />
    <circle cx="15" cy="20" r="3" fill="#207448" />
    <circle cx="28" cy="20" r="3" fill="#207448" />
    <circle cx="41" cy="20" r="3" fill="#207448" />
    <line x1="12" y1="36" x2="44" y2="36" />
    <path d="M 20 30 L 12 36 L 20 42" />
    <path d="M 36 30 L 44 36 L 36 42" />
  </g>

  <!-- Top Spine Switches: 3 Healthy, 1 Failed -->
  <!-- Spine 1 -->
  <rect x="85" y="300" width="75" height="46" rx="6" fill="#ffffff" stroke="#207448" stroke-width="3" />
  <circle cx="98" cy="323" r="3" fill="#207448" />
  <circle cx="110" cy="323" r="3" fill="#207448" />
  <circle cx="122" cy="323" r="3" fill="#207448" />
  <circle cx="134" cy="323" r="3" fill="#207448" />
  <circle cx="146" cy="323" r="3" fill="#207448" />

  <!-- Spine 2 -->
  <rect x="185" y="300" width="75" height="46" rx="6" fill="#ffffff" stroke="#207448" stroke-width="3" />
  <circle cx="198" cy="323" r="3" fill="#207448" />
  <circle cx="210" cy="323" r="3" fill="#207448" />
  <circle cx="222" cy="323" r="3" fill="#207448" />
  <circle cx="234" cy="323" r="3" fill="#207448" />
  <circle cx="246" cy="323" r="3" fill="#207448" />

  <!-- Spine 3 -->
  <rect x="285" y="300" width="75" height="46" rx="6" fill="#ffffff" stroke="#207448" stroke-width="3" />
  <circle cx="298" cy="323" r="3" fill="#207448" />
  <circle cx="310" cy="323" r="3" fill="#207448" />
  <circle cx="322" cy="323" r="3" fill="#207448" />
  <circle cx="334" cy="323" r="3" fill="#207448" />
  <circle cx="346" cy="323" r="3" fill="#207448" />

  <!-- Spine 4 (Failed, Dashed & Greyed Out) -->
  <rect x="385" y="300" width="75" height="46" rx="6" fill="#f5f8f5" stroke="#a8b5ac" stroke-width="2.5" stroke-dasharray="5 4" />
  <!-- Red Cross marking failure -->
  <line x1="404" y1="312" x2="442" y2="334" stroke="#c0392b" stroke-width="3" stroke-linecap="round" />
  <line x1="442" y1="312" x2="404" y2="334" stroke="#c0392b" stroke-width="3" stroke-linecap="round" />

  <!-- Uplinks: 3 Solid Green Lines, 1 Greyed Out Dashed Line -->
  <line x1="152" y1="520" x2="122" y2="346" stroke="#207448" stroke-width="4" stroke-linecap="round" />
  <line x1="232" y1="520" x2="222" y2="346" stroke="#207448" stroke-width="4" stroke-linecap="round" />
  <line x1="312" y1="520" x2="322" y2="346" stroke="#207448" stroke-width="4" stroke-linecap="round" />
  <!-- One uplink greyed out -->
  <line x1="392" y1="520" x2="422" y2="346" stroke="#a8b5ac" stroke-width="4" stroke-dasharray="8 6" stroke-linecap="round" />

  <!-- Small Leaf Switch Chassis -->
  <rect x="110" y="520" width="360" height="64" rx="8" fill="#ffffff" stroke="#207448" stroke-width="3" />
  <!-- Uplink ports on leaf top edge -->
  <rect x="140" y="526" width="24" height="12" rx="2" fill="#207448" />
  <rect x="220" y="526" width="24" height="12" rx="2" fill="#207448" />
  <rect x="300" y="526" width="24" height="12" rx="2" fill="#207448" />
  <rect x="380" y="526" width="24" height="12" rx="2" fill="#a8b5ac" />
  <!-- Downlink ports on leaf bottom edge -->
  <rect x="135" y="566" width="16" height="10" rx="1.5" fill="#207448" />
  <rect x="175" y="566" width="16" height="10" rx="1.5" fill="#207448" />
  <rect x="215" y="566" width="16" height="10" rx="1.5" fill="#207448" />
  <rect x="255" y="566" width="16" height="10" rx="1.5" fill="#207448" />
  <rect x="295" y="566" width="16" height="10" rx="1.5" fill="#207448" />
  <rect x="335" y="566" width="16" height="10" rx="1.5" fill="#207448" />
  <rect x="375" y="566" width="16" height="10" rx="1.5" fill="#207448" />
  <rect x="415" y="566" width="16" height="10" rx="1.5" fill="#207448" />

  <!-- Downlinks to Endpoints / Server Block -->
  <line x1="143" y1="584" x2="143" y2="640" stroke="#207448" stroke-width="3" stroke-linecap="round" />
  <line x1="183" y1="584" x2="183" y2="640" stroke="#207448" stroke-width="3" stroke-linecap="round" />
  <line x1="223" y1="584" x2="223" y2="640" stroke="#207448" stroke-width="3" stroke-linecap="round" />
  <line x1="263" y1="584" x2="263" y2="640" stroke="#207448" stroke-width="3" stroke-linecap="round" />
  <line x1="303" y1="584" x2="303" y2="640" stroke="#207448" stroke-width="3" stroke-linecap="round" />
  <line x1="343" y1="584" x2="343" y2="640" stroke="#207448" stroke-width="3" stroke-linecap="round" />
  <line x1="383" y1="584" x2="383" y2="640" stroke="#207448" stroke-width="3" stroke-linecap="round" />
  <line x1="423" y1="584" x2="423" y2="640" stroke="#207448" stroke-width="3" stroke-linecap="round" />

  <!-- Server Endpoints Chassis -->
  <rect x="110" y="640" width="360" height="55" rx="6" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
  <line x1="110" y1="667" x2="470" y2="667" stroke="#e8f1ea" stroke-width="2" />
  <circle cx="130" cy="654" r="3" fill="#207448" />
  <circle cx="145" cy="654" r="3" fill="#207448" />
  <rect x="175" y="648" width="50" height="12" rx="2" fill="#e8f1ea" stroke="#207448" stroke-width="1" />
  <rect x="240" y="648" width="50" height="12" rx="2" fill="#e8f1ea" stroke="#207448" stroke-width="1" />
  <rect x="305" y="648" width="50" height="12" rx="2" fill="#e8f1ea" stroke="#207448" stroke-width="1" />
  <rect x="370" y="648" width="50" height="12" rx="2" fill="#e8f1ea" stroke="#207448" stroke-width="1" />
  <circle cx="130" cy="681" r="3" fill="#207448" />
  <circle cx="145" cy="681" r="3" fill="#207448" />
  <rect x="175" y="675" width="50" height="12" rx="2" fill="#e8f1ea" stroke="#207448" stroke-width="1" />
  <rect x="240" y="675" width="50" height="12" rx="2" fill="#e8f1ea" stroke="#207448" stroke-width="1" />
  <rect x="305" y="675" width="50" height="12" rx="2" fill="#e8f1ea" stroke="#207448" stroke-width="1" />
  <rect x="370" y="675" width="50" height="12" rx="2" fill="#e8f1ea" stroke="#207448" stroke-width="1" />

  <!-- ==================== RIGHT TOP CARD: S = 32 SPINES ==================== -->
  <rect x="570" y="210" width="980" height="250" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

  <!-- Network Switch Icon -->
  <g transform="translate(600, 232)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="4" y="6" width="48" height="44" rx="6" />
    <circle cx="15" cy="20" r="3" fill="#207448" />
    <circle cx="28" cy="20" r="3" fill="#207448" />
    <circle cx="41" cy="20" r="3" fill="#207448" />
    <line x1="14" y1="36" x2="42" y2="36" />
    <path d="M 22 30 L 14 36 L 22 42" />
    <path d="M 34 30 L 42 36 L 34 42" />
  </g>

  <!-- Title: S = 32 spines, one down: 96.9% -->
  <text x="675" y="270" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">S = 32 spines, one down: 96.9%</text>

  <!-- Bar 1 Container & Track (920px wide) -->
  <rect x="600" y="325" width="920" height="75" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
  
  <!-- Bar 1 Filled: 96.875% of 920 = 891.25px (31 slices out of 32) -->
  <rect x="600" y="325" width="891" height="75" rx="12" fill="#207448" />
  <!-- Keep left corners rounded, right edge straight for the boundary -->
  <rect x="612" y="325" width="879" height="75" fill="#207448" />
  
  <!-- 32 Slice divider ticks across the 920px bar (each slice is 28.75px) -->
  <g stroke="#ffffff" stroke-width="1.5" opacity="0.4">
    <line x1="628.75" y1="325" x2="628.75" y2="400" />
    <line x1="657.50" y1="325" x2="657.50" y2="400" />
    <line x1="686.25" y1="325" x2="686.25" y2="400" />
    <line x1="715.00" y1="325" x2="715.00" y2="400" />
    <line x1="743.75" y1="325" x2="743.75" y2="400" />
    <line x1="772.50" y1="325" x2="772.50" y2="400" />
    <line x1="801.25" y1="325" x2="801.25" y2="400" />
    <line x1="830.00" y1="325" x2="830.00" y2="400" />
    <line x1="858.75" y1="325" x2="858.75" y2="400" />
    <line x1="887.50" y1="325" x2="887.50" y2="400" />
    <line x1="916.25" y1="325" x2="916.25" y2="400" />
    <line x1="945.00" y1="325" x2="945.00" y2="400" />
    <line x1="973.75" y1="325" x2="973.75" y2="400" />
    <line x1="1002.50" y1="325" x2="1002.50" y2="400" />
    <line x1="1031.25" y1="325" x2="1031.25" y2="400" />
    <line x1="1060.00" y1="325" x2="1060.00" y2="400" />
    <line x1="1088.75" y1="325" x2="1088.75" y2="400" />
    <line x1="1117.50" y1="325" x2="1117.50" y2="400" />
    <line x1="1146.25" y1="325" x2="1146.25" y2="400" />
    <line x1="1175.00" y1="325" x2="1175.00" y2="400" />
    <line x1="1203.75" y1="325" x2="1203.75" y2="400" />
    <line x1="1232.50" y1="325" x2="1232.50" y2="400" />
    <line x1="1261.25" y1="325" x2="1261.25" y2="400" />
    <line x1="1290.00" y1="325" x2="1290.00" y2="400" />
    <line x1="1318.75" y1="325" x2="1318.75" y2="400" />
    <line x1="1347.50" y1="325" x2="1347.50" y2="400" />
    <line x1="1376.25" y1="325" x2="1376.25" y2="400" />
    <line x1="1405.00" y1="325" x2="1405.00" y2="400" />
    <line x1="1433.75" y1="325" x2="1433.75" y2="400" />
    <line x1="1462.50" y1="325" x2="1462.50" y2="400" />
  </g>
  <!-- 32nd slice (lost spine): light dashed outline -->
  <line x1="1491.25" y1="325" x2="1491.25" y2="400" stroke="#207448" stroke-width="2.5" />
  <rect x="1491.25" y="325" width="28.75" height="75" rx="10" fill="#f5f8f5" stroke="#a8b5ac" stroke-width="1.5" stroke-dasharray="4 3" />

  <!-- ==================== RIGHT BOTTOM CARD: S = 4 SPINES (ORANGE) ==================== -->
  <rect x="570" y="500" width="980" height="250" rx="16" fill="#fdfaf6" stroke="#db8129" stroke-width="3" />

  <!-- Network Switch Icon in Orange -->
  <g transform="translate(600, 522)" stroke="#db8129" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="4" y="6" width="48" height="44" rx="6" />
    <circle cx="15" cy="20" r="3" fill="#db8129" />
    <circle cx="28" cy="20" r="3" fill="#db8129" />
    <circle cx="41" cy="20" r="3" fill="#db8129" />
    <line x1="14" y1="36" x2="42" y2="36" />
    <path d="M 22 30 L 14 36 L 22 42" />
    <path d="M 34 30 L 42 36 L 34 42" />
  </g>

  <!-- Title: S = 4 spines, one down: 75% -->
  <text x="675" y="560" font-family="sans-serif" font-size="30" font-weight="bold" fill="#db8129">S = 4 spines, one down: 75%</text>

  <!-- Bar 2 Container & Track (920px wide) -->
  <rect x="600" y="615" width="920" height="75" rx="12" fill="#ffffff" stroke="#db8129" stroke-width="2.5" />

  <!-- Bar 2 Filled: 75% of 920 = 690px (3 slices out of 4) -->
  <rect x="600" y="615" width="690" height="75" rx="12" fill="#db8129" />
  <rect x="612" y="615" width="678" height="75" fill="#db8129" />

  <!-- 4 Slices (each 230px wide) -->
  <!-- Slice 1 to 2 divider -->
  <line x1="830" y1="615" x2="830" y2="690" stroke="#ffffff" stroke-width="2.5" />
  <!-- Slice 2 to 3 divider -->
  <line x1="1060" y1="615" x2="1060" y2="690" stroke="#ffffff" stroke-width="2.5" />
  <!-- Slice 3 boundary line -->
  <line x1="1290" y1="615" x2="1290" y2="690" stroke="#db8129" stroke-width="3" />

  <!-- Slice 4 (Lost 25% uplink capacity): Hatched / Dashed area -->
  <rect x="1290" y="615" width="230" height="75" rx="12" fill="#fdf6ee" stroke="#db8129" stroke-width="2" stroke-dasharray="6 4" />
  <!-- Hatching lines for lost 25% -->
  <g stroke="#db8129" stroke-width="2" opacity="0.35" stroke-linecap="round">
    <line x1="1315" y1="690" x2="1355" y2="615" />
    <line x1="1355" y1="690" x2="1395" y2="615" />
    <line x1="1395" y1="690" x2="1435" y2="615" />
    <line x1="1435" y1="690" x2="1475" y2="615" />
    <line x1="1475" y1="690" x2="1515" y2="615" />
  </g>

  <!-- ==================== FOOTER CARD ==================== -->
  <rect x="50" y="780" width="1500" height="90" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

  <!-- Info / Shield Icon -->
  <g transform="translate(85, 797)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <path d="M 28 6 L 48 14 V 30 C 48 42 28 50 28 50 C 28 50 8 42 8 30 V 14 Z" />
    <line x1="28" y1="20" x2="28" y2="32" />
    <circle cx="28" cy="39" r="2" fill="#207448" />
  </g>

  <!-- Footer Text -->
  <text x="800" y="836" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36">A 1:1 design stays oversubscribed until the failure is repaired</text>

  <!-- ==================== BOTTOM TAKEAWAY BAR ==================== -->
  <rect x="50" y="900" width="1500" height="80" rx="14" fill="#207448" />
  <text x="800" y="949" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">Work out what survives losing one spine, one leaf and one rail group</text>
</svg>'''
    return svg

svg_data = generate_svg()
with open("test_n18_output.svg", "w", encoding="utf-8") as f:
    f.write(svg_data)

print("Generated test_n18_output.svg successfully.")
