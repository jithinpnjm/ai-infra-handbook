import xml.etree.ElementTree as ET
import re

svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 900" width="1600" height="900">
  <title>Start with the simple idea</title>
  <desc>Visual flowchart illustrating the four-stage power and heat chain for AI infrastructure: Utility and UPS, 3-Phase Rack PDUs, GPU Server, and Heat Rejection.</desc>
  <defs>
    <!-- Arrowhead Green (18px) -->
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1600" height="900" fill="#f5f8f5" />

  <!-- Title (48px bold) -->
  <text x="800" y="75" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Start with the simple idea</text>

  <!-- ==================== FLOW ARROWS ==================== -->
  <!-- Arrow 1: Box 1 to Box 2 -->
  <line x1="390" y1="465" x2="430" y2="465" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />

  <!-- Arrow 2: Box 2 to Box 3 -->
  <line x1="780" y1="465" x2="820" y2="465" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />

  <!-- Arrow 3: Box 3 to Box 4 -->
  <line x1="1170" y1="465" x2="1210" y2="465" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />

  <!-- ==================== BOX 1: Utility / Generator + UPS ==================== -->
  <g id="node-grid">
    <rect x="40" y="150" width="350" height="630" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    
    <!-- Step Number Circle (r=24) -->
    <circle cx="215" cy="205" r="24" fill="#207448" />
    <text x="215" y="214" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">1</text>
    
    <!-- Power / Generator / UPS Outline Icon (56px) -->
    <g transform="translate(187, 248)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="10" y="14" width="36" height="36" rx="5" />
      <line x1="20" y1="8" x2="20" y2="14" />
      <line x1="36" y1="8" x2="36" y2="14" />
      <polyline points="30,20 22,32 32,32 26,44" />
    </g>

    <!-- Node Title -->
    <text x="215" y="365" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">
      <tspan x="215" dy="0">1. Utility / </tspan>
      <tspan x="215" dy="42">Generator + UPS</tspan>
    </text>

    <!-- Secondary Panel -->
    <rect x="60" y="475" width="310" height="265" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />
    <text x="215" y="585" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">
      <tspan x="215" dy="0">apcupsd (:3551) + </tspan>
      <tspan x="215" dy="36">Staged haltall</tspan>
    </text>
  </g>

  <!-- ==================== BOX 2: 3-Phase Rack PDUs ==================== -->
  <g id="node-pdu">
    <rect x="430" y="150" width="350" height="630" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    
    <!-- Step Number Circle (r=24) -->
    <circle cx="605" cy="205" r="24" fill="#207448" />
    <text x="605" y="214" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">2</text>
    
    <!-- Rack PDU Outline Icon (56px) -->
    <g transform="translate(577, 248)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="14" y="6" width="28" height="44" rx="4" />
      <circle cx="28" cy="16" r="3" fill="#207448" />
      <circle cx="28" cy="28" r="3" fill="#207448" />
      <circle cx="28" cy="40" r="3" fill="#207448" />
      <line x1="28" y1="50" x2="28" y2="54" />
    </g>

    <!-- Node Title -->
    <text x="605" y="365" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">
      <tspan x="605" dy="0">2. 3-Phase </tspan>
      <tspan x="605" dy="42">Rack PDUs (N=2)</tspan>
    </text>

    <!-- Secondary Panel -->
    <rect x="450" y="475" width="310" height="265" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />
    <text x="605" y="585" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">
      <tspan x="605" dy="0">sqrt(3) * V * I * </tspan>
      <tspan x="605" dy="36">0.80 * 0.95</tspan>
    </text>
  </g>

  <!-- ==================== BOX 3: GPU Server (Orange Highlight) ==================== -->
  <g id="node-server">
    <!-- Orange highlighted container -->
    <rect x="820" y="150" width="350" height="630" rx="16" fill="#ffffff" stroke="#db8129" stroke-width="3" />
    
    <!-- Step Number Circle (r=24, orange highlight) -->
    <circle cx="995" cy="205" r="24" fill="#db8129" />
    <text x="995" y="214" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">3</text>
    
    <!-- GPU Server Outline Icon (56px) -->
    <g transform="translate(967, 248)" stroke="#db8129" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="10" y="10" width="36" height="36" rx="5" />
      <rect x="18" y="18" width="20" height="20" rx="2" fill="#e8f1ea" />
      <line x1="18" y1="4" x2="18" y2="10" /><line x1="28" y1="4" x2="28" y2="10" /><line x1="38" y1="4" x2="38" y2="10" />
      <line x1="18" y1="46" x2="18" y2="52" /><line x1="28" y1="46" x2="28" y2="52" /><line x1="38" y1="46" x2="38" y2="52" />
      <line x1="4" y1="18" x2="10" y2="18" /><line x1="4" y1="28" x2="10" y2="28" /><line x1="4" y1="38" x2="10" y2="38" />
      <line x1="46" y1="18" x2="52" y2="18" /><line x1="46" y1="28" x2="52" y2="28" /><line x1="46" y1="38" x2="52" y2="38" />
    </g>

    <!-- Node Title -->
    <text x="995" y="350" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">
      <tspan x="995" dy="0">3. GPU Server </tspan>
      <tspan x="995" dy="40">(DGX B200 </tspan>
      <tspan x="995" dy="40">14.3 kW)</tspan>
    </text>

    <!-- Secondary Panel -->
    <rect x="840" y="475" width="310" height="265" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />
    <text x="995" y="585" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="995" dy="0">6 PSUs </tspan>
      <tspan x="995" dy="36">(5-of-6 </tspan>
      <tspan x="995" dy="36">N+1 Required)</tspan>
    </text>
  </g>

  <!-- ==================== BOX 4: Heat Rejection ==================== -->
  <g id="node-cool">
    <rect x="1210" y="150" width="350" height="630" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    
    <!-- Step Number Circle (r=24) -->
    <circle cx="1385" cy="205" r="24" fill="#207448" />
    <text x="1385" y="214" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">4</text>
    
    <!-- Heat Rejection / Cooling Fan Outline Icon (56px) -->
    <g transform="translate(1357, 248)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="22" />
      <circle cx="28" cy="28" r="5" fill="#207448" />
      <path d="M 28 23 C 28 14 35 14 35 19 C 35 23 31 23 28 23 Z" />
      <path d="M 33 28 C 42 28 42 35 37 35 C 33 35 33 31 33 28 Z" />
      <path d="M 28 33 C 28 42 21 42 21 37 C 21 33 25 33 28 33 Z" />
      <path d="M 23 28 C 14 28 14 21 19 21 C 23 21 23 25 23 28 Z" />
    </g>

    <!-- Node Title -->
    <text x="1385" y="350" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">
      <tspan x="1385" dy="0">4. Heat </tspan>
      <tspan x="1385" dy="40">Rejection </tspan>
      <tspan x="1385" dy="40">(100% of Watts)</tspan>
    </text>

    <!-- Secondary Panel -->
    <rect x="1230" y="475" width="310" height="265" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />
    <text x="1385" y="585" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1385" dy="0">Air (150 CFM/kW) or </tspan>
      <tspan x="1385" dy="36">Cold-Plate CDU</tspan>
    </text>
  </g>
</svg>"""

with open("test_simple_idea.svg", "w") as f:
    f.write(svg)

print("Wrote test_simple_idea.svg")
