import xml.etree.ElementTree as ET
import re, pathlib

def build_svg():
    lines = []
    lines.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">')
    lines.append('  <title>Toy router simulation: policies and the bound sweep</title>')
    lines.append('  <desc>Comparison of routing policies and backlog bound sweep showing hit rate, latency percentiles, and load imbalance.</desc>')
    lines.append('  <rect width="1600" height="1200" fill="#f5f8f5"/>')
    lines.append('')
    
    # Title
    lines.append('  <!-- ==================== TITLE ==================== -->')
    lines.append('  <text x="800" y="56" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Toy router simulation: policies and the bound sweep</text>')
    lines.append('')
    
    # Subtitle Pill
    lines.append('  <!-- ==================== SUBTITLE PILL ==================== -->')
    lines.append('  <rect x="450" y="76" width="700" height="56" rx="28" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
    lines.append('  <text x="800" y="112" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">toy numbers chosen to show the mechanism</text>')
    lines.append('')
    
    # Setup Container (Node 1)
    # y = 175..269 (h = 94)
    lines.append('  <!-- ==================== SETUP CONTAINER ==================== -->')
    lines.append('  <rect x="50" y="175" width="1500" height="94" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    # Gear Icon at x = 75, y = 194 (56x56)
    lines.append('  <g transform="translate(75, 194)" stroke="#207448" stroke-width="4" fill="none">')
    lines.append('    <circle cx="28" cy="28" r="12"/>')
    lines.append('    <path d="M 28 4 L 28 10 M 28 46 L 28 52 M 4 28 L 10 28 M 46 28 L 52 28 M 11 11 L 15 15 M 41 41 L 45 45 M 11 45 L 15 41 M 41 11 L 45 15"/>')
    lines.append('  </g>')
    # Setup Text (2 lines)
    lines.append('  <text x="155" y="214" font-family="sans-serif" font-size="24" fill="#303a36">')
    lines.append('    <tspan x="155" dy="0">Setup: eight replicas, forty prefixes, one hot prefix with 40 percent of traffic,</tspan>')
    lines.append('    <tspan x="155" dy="33">cache of six prefixes per replica, hit costs 0.10 s and miss 0.50 s</tspan>')
    lines.append('  </text>')
    lines.append('')
    
    # ==================== TABLE 1: LEFT PANEL ====================
    # x = 50..775 (w = 725), y = 312..932 (h = 620)
    lines.append('  <!-- ==================== TABLE 1: POLICIES ==================== -->')
    lines.append('  <rect x="50" y="312" width="725" height="620" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    
    # Header card inside T1: x = 70..755 (w = 685), y = 330..416 (h = 86)
    lines.append('  <rect x="70" y="330" width="685" height="86" rx="10" fill="#e8f1ea"/>')
    # Chip Icon at x = 85, y = 345 (56x56)
    lines.append('  <g transform="translate(85, 345)" stroke="#207448" stroke-width="4" fill="none">')
    lines.append('    <rect x="10" y="10" width="36" height="36" rx="6"/>')
    lines.append('    <line x1="18" y1="4" x2="18" y2="10"/><line x1="28" y1="4" x2="28" y2="10"/><line x1="38" y1="4" x2="38" y2="10"/>')
    lines.append('    <line x1="18" y1="46" x2="18" y2="52"/><line x1="28" y1="46" x2="28" y2="52"/><line x1="38" y1="46" x2="38" y2="52"/>')
    lines.append('    <line x1="4" y1="18" x2="10" y2="18"/><line x1="4" y1="28" x2="10" y2="28"/><line x1="4" y1="38" x2="10" y2="38"/>')
    lines.append('    <line x1="46" y1="18" x2="52" y2="18"/><line x1="46" y1="28" x2="52" y2="28"/><line x1="46" y1="38" x2="52" y2="38"/>')
    lines.append('  </g>')
    # Header text (30px bold, 2 lines)
    lines.append('  <text x="160" y="366" font-family="sans-serif" font-size="28" font-weight="bold" fill="#207448">')
    lines.append('    <tspan x="160" dy="0">Table 1 policy:</tspan>')
    lines.append('    <tspan x="160" dy="32" font-size="24">hit rate, p50 s, p99 s, max over mean load</tspan>')
    lines.append('  </text>')

    # T1 Rows: y positions
    # Row 1: y = 432..532 (h = 100)
    # Row 2: y = 552..652 (h = 100)
    # Row 3: y = 672..772 (h = 100)
    # Row 4: y = 792..892 (h = 100)
    
    # T1 Row 1: round_robin
    lines.append('  <rect x="70" y="432" width="685" height="100" rx="10" fill="#f5f8f5" stroke="#e8f1ea" stroke-width="2"/>')
    lines.append('  <text x="90" y="472" font-family="monospace" font-size="24" fill="#303a36">round_robin 0.46, 0.50, 2.33, 1.00</text>')
    # Visual bar group for row 1
    lines.append('  <rect x="90" y="492" width="138" height="22" rx="4" fill="#207448"/>')
    lines.append('  <rect x="240" y="492" width="163" height="22" rx="4" fill="#c2dac7"/>')
    lines.append('  <rect x="415" y="492" width="70" height="22" rx="4" fill="#207448"/>')

    # T1 Row 2: least_loaded
    lines.append('  <rect x="70" y="552" width="685" height="100" rx="10" fill="#f5f8f5" stroke="#e8f1ea" stroke-width="2"/>')
    lines.append('  <text x="90" y="592" font-family="monospace" font-size="24" fill="#303a36">least_loaded 0.46, 0.50, 1.22, 1.16</text>')
    # Visual bar group for row 2
    lines.append('  <rect x="90" y="612" width="138" height="22" rx="4" fill="#207448"/>')
    lines.append('  <rect x="240" y="612" width="85" height="22" rx="4" fill="#c2dac7"/>')
    lines.append('  <rect x="337" y="612" width="81" height="22" rx="4" fill="#207448"/>')

    # T1 Row 3: cache_only
    lines.append('  <rect x="70" y="672" width="685" height="100" rx="10" fill="#f5f8f5" stroke="#e8f1ea" stroke-width="2"/>')
    lines.append('  <text x="90" y="712" font-family="monospace" font-size="24" fill="#303a36">cache_only 0.98, 0.16, 4.39, 3.80</text>')
    # Visual bar group for row 3
    lines.append('  <rect x="90" y="732" width="294" height="22" rx="4" fill="#207448"/>')
    lines.append('  <rect x="396" y="732" width="219" height="22" rx="4" fill="#c2dac7"/>')
    lines.append('  <rect x="90" y="732" width="0" height="0"/>') # placeholder

    # T1 Row 4: cache_bounded
    lines.append('  <rect x="70" y="792" width="685" height="100" rx="10" fill="#f5f8f5" stroke="#e8f1ea" stroke-width="2"/>')
    lines.append('  <text x="90" y="832" font-family="monospace" font-size="24" fill="#303a36">cache_bounded 0.95, 0.10, 0.50, 2.13</text>')
    # Visual bar group for row 4
    lines.append('  <rect x="90" y="852" width="285" height="22" rx="4" fill="#207448"/>')
    lines.append('  <rect x="387" y="852" width="35" height="22" rx="4" fill="#207448"/>')
    lines.append('  <rect x="434" y="852" width="149" height="22" rx="4" fill="#207448"/>')
    lines.append('')
    
    # ==================== TABLE 2: RIGHT PANEL ====================
    # x = 825..1550 (w = 725), y = 312..932 (h = 620)
    lines.append('  <!-- ==================== TABLE 2: BOUND SWEEP ==================== -->')
    lines.append('  <rect x="825" y="312" width="725" height="620" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2"/>')

    # Header card inside T2: x = 845..1530 (w = 685), y = 330..416 (h = 86)
    lines.append('  <rect x="845" y="330" width="685" height="86" rx="10" fill="#e8f1ea"/>')
    # Clock Icon at x = 860, y = 345 (56x56)
    lines.append('  <g transform="translate(860, 345)" stroke="#207448" stroke-width="4" fill="none">')
    lines.append('    <circle cx="28" cy="28" r="22"/>')
    lines.append('    <polyline points="28,14 28,28 38,28"/>')
    lines.append('  </g>')
    # Header text (30px bold, 2 lines)
    lines.append('  <text x="935" y="366" font-family="sans-serif" font-size="28" font-weight="bold" fill="#207448">')
    lines.append('    <tspan x="935" dy="0">Table 2 bound in seconds</tspan>')
    lines.append('    <tspan x="935" dy="32" font-size="24">of backlog</tspan>')
    lines.append('  </text>')

    # T2 Rows: 5 rows
    # Row 1: y = 432..514 (h = 82)
    # Row 2: y = 526..608 (h = 82)
    # Row 3: y = 620..702 (h = 82) (ORANGE highlighted sweet spot!)
    # Row 4: y = 714..796 (h = 82)
    # Row 5: y = 808..890 (h = 82)

    # T2 Row 1: 0.0
    lines.append('  <rect x="845" y="432" width="685" height="82" rx="10" fill="#f5f8f5" stroke="#e8f1ea" stroke-width="2"/>')
    lines.append('  <text x="865" y="466" font-family="monospace" font-size="24" fill="#303a36">')
    lines.append('    <tspan x="865" dy="0">0.0: hit 0.57, p50 0.22,</tspan>')
    lines.append('    <tspan x="865" dy="30">p99 0.99, max/mean 1.22</tspan>')
    lines.append('  </text>')
    # Visual bar group for row 1
    lines.append('  <rect x="1260" y="448" width="114" height="20" rx="4" fill="#207448"/>')
    lines.append('  <rect x="1385" y="448" width="69" height="20" rx="4" fill="#c2dac7"/>')
    lines.append('  <rect x="1465" y="448" width="40" height="20" rx="4" fill="#207448"/>')

    # T2 Row 2: 0.1
    lines.append('  <rect x="845" y="526" width="685" height="82" rx="10" fill="#f5f8f5" stroke="#e8f1ea" stroke-width="2"/>')
    lines.append('  <text x="865" y="562" font-family="monospace" font-size="24" fill="#303a36">')
    lines.append('    <tspan x="865" dy="0">0.1: 0.89, 0.10,</tspan>')
    lines.append('    <tspan x="865" dy="30">0.52, 1.56</tspan>')
    lines.append('  </text>')
    lines.append('  <rect x="1260" y="542" width="178" height="20" rx="4" fill="#207448"/>')
    lines.append('  <rect x="1448" y="542" width="36" height="20" rx="4" fill="#c2dac7"/>')

    # T2 Row 3: 0.5 (Single ORANGE highlight for optimal bound!)
    lines.append('  <rect x="845" y="620" width="685" height="82" rx="10" fill="#f5f8f5" stroke="#db8129" stroke-width="3"/>')
    lines.append('  <text x="865" y="656" font-family="monospace" font-size="24" fill="#303a36">')
    lines.append('    <tspan x="865" dy="0">0.5: 0.95, 0.10,</tspan>')
    lines.append('    <tspan x="865" dy="30">0.50, 2.13</tspan>')
    lines.append('  </text>')
    lines.append('  <rect x="1260" y="636" width="190" height="20" rx="4" fill="#207448"/>')
    lines.append('  <rect x="1460" y="636" width="35" height="20" rx="4" fill="#207448"/>')

    # T2 Row 4: 2.0
    lines.append('  <rect x="845" y="714" width="685" height="82" rx="10" fill="#f5f8f5" stroke="#e8f1ea" stroke-width="2"/>')
    lines.append('  <text x="865" y="750" font-family="monospace" font-size="24" fill="#303a36">')
    lines.append('    <tspan x="865" dy="0">2.0: 0.98, 0.11,</tspan>')
    lines.append('    <tspan x="865" dy="30">1.68, 3.39</tspan>')
    lines.append('  </text>')
    lines.append('  <rect x="1260" y="730" width="196" height="20" rx="4" fill="#207448"/>')
    lines.append('  <rect x="1466" y="730" width="45" height="20" rx="4" fill="#c2dac7"/>')

    # T2 Row 5: 100 (cache-only)
    lines.append('  <rect x="845" y="808" width="685" height="82" rx="10" fill="#f5f8f5" stroke="#e8f1ea" stroke-width="2"/>')
    lines.append('  <text x="865" y="844" font-family="monospace" font-size="24" fill="#303a36">')
    lines.append('    <tspan x="865" dy="0">100 (cache-only):</tspan>')
    lines.append('    <tspan x="865" dy="30">0.98, 0.16, 4.39, 3.80</tspan>')
    lines.append('  </text>')
    lines.append('  <rect x="1260" y="824" width="196" height="20" rx="4" fill="#207448"/>')
    lines.append('  <rect x="1466" y="824" width="45" height="20" rx="4" fill="#c2dac7"/>')
    lines.append('')

    # Takeaway Bar (Node 4)
    # y = 975..1150 (h = 175)
    lines.append('  <!-- ==================== TAKEAWAY BAR ==================== -->')
    lines.append('  <rect x="50" y="975" width="1500" height="175" rx="14" fill="#207448"/>')
    lines.append('  <text x="800" y="1022" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">')
    lines.append('    <tspan x="800" dy="0">cache-only wins hit rate and loses the tail because</tspan>')
    lines.append('    <tspan x="800" dy="34">one replica carries 3.8 times the average load; least-loaded keeps load flat</tspan>')
    lines.append('    <tspan x="800" dy="34">but wastes the cache; sweep the bound against p99, not hit rate;</tspan>')
    lines.append('    <tspan x="800" dy="34">zero bound behaves like least-loaded, a huge bound like cache-only</tspan>')
    lines.append('  </text>')
    lines.append('</svg>')

    return "\n".join(lines)

svg_str = build_svg()
with open("test_router_side.svg", "w") as f:
    f.write(svg_str)
print("Saved test_router_side.svg")
