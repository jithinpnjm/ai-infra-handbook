import xml.etree.ElementTree as ET
import re, json, pathlib

def build_svg(H=1020):
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 {H}" width="1600" height="{H}">')
    svg.append('  <title>Prefill and decode pools, split only when interference is measured</title>')
    svg.append('  <desc>Architecture comparison showing colocated prefill and decode on one GPU causing streaming stalls, versus a split design with router, prefill pool, decode pool, KV cache transfer, and backpressure.</desc>')
    svg.append('')
    svg.append('  <defs>')
    svg.append('    <!-- Green Arrowhead 18px -->')
    svg.append('    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    svg.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />')
    svg.append('    </marker>')
    svg.append('    <!-- Orange Arrowhead 18px -->')
    svg.append('    <marker id="arrow-orange" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    svg.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#db8129" />')
    svg.append('    </marker>')
    svg.append('  </defs>')
    svg.append('')
    svg.append(f'  <!-- Background -->')
    svg.append(f'  <rect width="1600" height="{H}" fill="#f5f8f5" />')
    svg.append('')
    svg.append('  <!-- Title (48px bold, 2 lines to fit comfortably with >=40px margins) -->')
    svg.append('  <text x="800" y="80" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">')
    svg.append('    <tspan x="800" dy="0">Prefill and decode pools, </tspan>')
    svg.append('    <tspan x="800" dy="54">split only when interference is measured</tspan>')
    svg.append('  </text>')
    svg.append('')

    # ==================== TOP: COLOCATED GPU ====================
    # Container box: x=50, y=175, width=1500, height=295
    svg.append('  <!-- Top: Colocated GPU container -->')
    svg.append('  <g id="colocated-gpu">')
    svg.append('    <rect x="50" y="175" width="1500" height="295" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('')
    # GPU Chip outline icon at x=75, y=193 (56x56)
    svg.append('    <!-- GPU Chip Icon (56px, stroke 4, #207448) -->')
    svg.append('    <g transform="translate(75, 193)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="8" y="8" width="40" height="40" rx="4" />')
    svg.append('      <rect x="16" y="16" width="24" height="24" rx="2" fill="#ffffff" />')
    svg.append('      <line x1="18" y1="2" x2="18" y2="8" />')
    svg.append('      <line x1="28" y1="2" x2="28" y2="8" />')
    svg.append('      <line x1="38" y1="2" x2="38" y2="8" />')
    svg.append('      <line x1="18" y1="48" x2="18" y2="54" />')
    svg.append('      <line x1="28" y1="48" x2="28" y2="54" />')
    svg.append('      <line x1="38" y1="48" x2="38" y2="54" />')
    svg.append('      <line x1="2" y1="18" x2="8" y2="18" />')
    svg.append('      <line x1="2" y1="28" x2="8" y2="28" />')
    svg.append('      <line x1="2" y1="38" x2="8" y2="38" />')
    svg.append('      <line x1="48" y1="18" x2="54" y2="18" />')
    svg.append('      <line x1="48" y1="28" x2="54" y2="28" />')
    svg.append('      <line x1="48" y1="38" x2="54" y2="38" />')
    svg.append('    </g>')
    svg.append('')
    # Colocated title
    svg.append('    <text x="150" y="231" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Colocated: prefill and decode share one GPU</text>')
    svg.append('')
    # Stacked bar 1: Long prefill: compute heavy
    svg.append('    <!-- Stacked Bar 1: Prefill -->')
    svg.append('    <rect x="75" y="263" width="1450" height="58" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg.append('    <text x="800" y="300" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448">Long prefill: compute heavy</text>')
    svg.append('')
    # Red zigzag and stall label
    svg.append('    <!-- Red Zigzag & Stall Label between bars -->')
    # Left zigzag
    svg.append('    <path d="M 75 358 L 95 346 L 115 370 L 135 346 L 155 370 L 175 346 L 195 370 L 215 346 L 235 370 L 255 346 L 275 370 L 295 346 L 315 370 L 335 346 L 355 370 L 375 346 L 395 370 L 415 346 L 435 370 L 455 346 L 475 370 L 495 346 L 515 370 L 535 346 L 555 370 L 575 358" fill="none" stroke="#d9383a" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />')
    # Center badge for label
    svg.append('    <rect x="580" y="329" width="440" height="58" rx="8" fill="#ffffff" stroke="#d9383a" stroke-width="2" />')
    svg.append('    <text x="800" y="366" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#d9383a">Streaming users see a stall</text>')
    # Right zigzag
    svg.append('    <path d="M 1025 358 L 1045 346 L 1065 370 L 1085 346 L 1105 370 L 1125 346 L 1145 370 L 1165 346 L 1185 370 L 1205 346 L 1225 370 L 1245 346 L 1265 370 L 1285 346 L 1305 370 L 1325 346 L 1345 370 L 1365 346 L 1385 370 L 1405 346 L 1425 370 L 1445 346 L 1465 370 L 1485 346 L 1505 370 L 1525 358" fill="none" stroke="#d9383a" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />')
    svg.append('')
    # Stacked bar 2: Decode: memory-bandwidth heavy, one token at a time
    svg.append('    <!-- Stacked Bar 2: Decode -->')
    svg.append('    <rect x="75" y="396" width="1450" height="58" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg.append('    <text x="800" y="433" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448">Decode: memory-bandwidth heavy, one token at a time</text>')
    svg.append('  </g>')
    svg.append('')

    # ==================== BOTTOM: SPLIT DESIGN ====================
    # Router box on the left: x=50, y=590, width=110, height=150
    # Pool 1 (Prefill pool): x=220, y=535, width=370, height=260
    # Pool 2 (Decode pool): x=1180, y=535, width=370, height=260
    svg.append('  <!-- Split Design Section -->')
    svg.append('  <g id="split-pools">')
    svg.append('')
    # Router Box (outline node icon inside)
    svg.append('    <!-- Router Box (no text, 56px router icon inside) -->')
    svg.append('    <rect x="50" y="590" width="110" height="150" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2.5" />')
    # Router icon at x=77, y=637
    svg.append('    <g transform="translate(77, 637)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="4" y="14" width="48" height="28" rx="6" />')
    svg.append('      <line x1="14" y1="28" x2="18" y2="28" />')
    svg.append('      <line x1="26" y1="28" x2="30" y2="28" />')
    svg.append('      <line x1="38" y1="28" x2="42" y2="28" />')
    svg.append('      <line x1="16" y1="14" x2="16" y2="6" />')
    svg.append('      <line x1="40" y1="14" x2="40" y2="6" />')
    svg.append('      <circle cx="16" cy="5" r="2" fill="#207448" />')
    svg.append('      <circle cx="40" cy="5" r="2" fill="#207448" />')
    svg.append('    </g>')
    svg.append('')

    # Pool 1: Prefill pool: picks by cache and load
    svg.append('    <!-- Pool 1: Prefill Pool -->')
    svg.append('    <rect x="220" y="535" width="370" height="260" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />')
    # Pool 1 icon (Compute / Chip icon) at x=377, y=555
    svg.append('    <g transform="translate(377, 555)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="10" y="10" width="36" height="36" rx="4" />')
    svg.append('      <path d="M 22 28 L 34 28 M 28 22 L 28 34" />')
    svg.append('      <line x1="18" y1="2" x2="18" y2="10" />')
    svg.append('      <line x1="38" y1="2" x2="38" y2="10" />')
    svg.append('      <line x1="18" y1="46" x2="18" y2="54" />')
    svg.append('      <line x1="38" y1="46" x2="38" y2="54" />')
    svg.append('      <line x1="2" y1="18" x2="10" y2="18" />')
    svg.append('      <line x1="2" y1="38" x2="10" y2="38" />')
    svg.append('      <line x1="46" y1="18" x2="54" y2="18" />')
    svg.append('      <line x1="46" y1="38" x2="54" y2="38" />')
    svg.append('    </g>')
    svg.append('    <text x="405" y="652" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36">')
    svg.append('      <tspan x="405" dy="0">Prefill pool: </tspan>')
    svg.append('      <tspan x="405" dy="36">picks by cache </tspan>')
    svg.append('      <tspan x="405" dy="36">and load</tspan>')
    svg.append('    </text>')
    svg.append('')

    # Pool 2: Decode pool: picks by free KV memory
    svg.append('    <!-- Pool 2: Decode Pool -->')
    svg.append('    <rect x="1180" y="535" width="370" height="260" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />')
    # Pool 2 icon (Memory / Storage grid icon) at x=1337, y=555
    svg.append('    <g transform="translate(1337, 555)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="8" y="12" width="40" height="32" rx="4" />')
    svg.append('      <line x1="8" y1="28" x2="48" y2="28" />')
    svg.append('      <line x1="28" y1="12" x2="28" y2="44" />')
    svg.append('      <circle cx="18" cy="20" r="2.5" fill="#207448" />')
    svg.append('      <circle cx="38" cy="20" r="2.5" fill="#207448" />')
    svg.append('      <circle cx="18" cy="36" r="2.5" fill="#207448" />')
    svg.append('      <circle cx="38" cy="36" r="2.5" fill="#207448" />')
    svg.append('    </g>')
    svg.append('    <text x="1365" y="652" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36">')
    svg.append('      <tspan x="1365" dy="0">Decode pool: </tspan>')
    svg.append('      <tspan x="1365" dy="36">picks by free </tspan>')
    svg.append('      <tspan x="1365" dy="36">KV memory</tspan>')
    svg.append('    </text>')
    svg.append('')

    # ==================== ARROWS & CONNECTIONS ====================
    # Arrow 1: Router -> Pool 1
    svg.append('    <!-- Arrow 1: Router to Pool 1 -->')
    svg.append('    <line x1="160" y1="665" x2="220" y2="665" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />')
    svg.append('')

    # Arrow 2: Router -> Pool 2 (goes over Pool 1 at y=500)
    svg.append('    <!-- Arrow 2: Router to Pool 2 -->')
    svg.append('    <path d="M 105 590 V 500 H 1365 V 535" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />')
    svg.append('')

    # Between Pool 1 and Pool 2:
    # Forward Arrow 3: Pool 1 -> Pool 2 at y=615
    # Backward Arrow 4: Pool 2 -> Pool 1 at y=715 (orange outline)
    svg.append('    <!-- Inter-pool flow & Backpressure -->')
    # Label above forward arrow: KV cache moved between pools, needs a fast link
    svg.append('    <text x="885" y="558" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">')
    svg.append('      <tspan x="885" dy="0">KV cache moved between pools, </tspan>')
    svg.append('      <tspan x="885" dy="28">needs a fast link</tspan>')
    svg.append('    </text>')
    svg.append('    <!-- Arrow 3: Forward Pool 1 to Pool 2 -->')
    svg.append('    <line x1="590" y1="615" x2="1180" y2="615" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />')
    svg.append('')
    # Note on the arrow: Keep prefill and decode inside one fast domain where possible
    svg.append('    <!-- Small note on the arrow -->')
    svg.append('    <text x="885" y="654" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="885" dy="0">Keep prefill and decode inside </tspan>')
    svg.append('      <tspan x="885" dy="28">one fast domain where possible</tspan>')
    svg.append('    </text>')
    svg.append('')
    # Arrow 4: Backward Pool 2 to Pool 1 with Orange Outline
    svg.append('    <!-- Arrow 4: Backward Backpressure Pool 2 to Pool 1 (Orange Outline) -->')
    svg.append('    <line x1="1180" y1="715" x2="590" y2="715" stroke="#db8129" stroke-width="4" marker-end="url(#arrow-orange)" />')
    svg.append('')
    # Label below backward arrow: Backpressure: decode queue full, prefill slows down
    svg.append('    <text x="885" y="752" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#db8129">')
    svg.append('      <tspan x="885" dy="0">Backpressure: decode queue full, </tspan>')
    svg.append('      <tspan x="885" dy="28">prefill slows down</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('')

    # ==================== BOTTOM TAKEAWAY BAR ====================
    # Start colocated with chunked prefill. Split when p99 inter-token latency is dominated by prefill interference.
    svg.append('  <!-- Bottom Takeaway Bar -->')
    svg.append('  <g id="takeaway-bar">')
    svg.append(f'    <rect x="50" y="874" width="1500" height="98" rx="14" fill="#207448" stroke="#207448" stroke-width="2" />')
    svg.append(f'    <text x="800" y="918" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">')
    svg.append(f'      <tspan x="800" dy="0">Start colocated with chunked prefill. </tspan>')
    svg.append(f'      <tspan x="800" dy="34">Split when p99 inter-token latency is dominated by prefill interference.</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('</svg>')

    return '\n'.join(svg)

svg_file = "candidate_prefill_decode.svg"
pathlib.Path(svg_file).write_text(build_svg(1020))
print("Saved candidate SVG with H=1020.")
