#!/usr/bin/env python3

svg_template = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 960" width="1600" height="960">
  <title>Metadata, data and the parallel file system idea</title>
  <desc>Visual infographic explaining how parallel file systems separate metadata operations from distributed data storage across multiple clients and servers.</desc>

  <defs>
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448"/>
    </marker>
    <marker id="arrow-orange" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#db8129"/>
    </marker>
  </defs>

  <!-- Background Canvas -->
  <rect width="1600" height="960" fill="#f5f8f5"/>

  <!-- Diagram Title (48px bold) -->
  <text x="800" y="68" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Metadata, data and the parallel file system idea</text>

  <!-- ==================== CLIENT 1 ==================== -->
  <g id="node-c1">
    <rect x="60" y="170" width="380" height="120" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
    <!-- Window / Client Outline Icon (56px, stroke 4) -->
    <g transform="translate(90, 202)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="2" y="2" width="52" height="44" rx="6"/>
      <line x1="2" y1="16" x2="54" y2="16" stroke-width="3"/>
      <circle cx="12" cy="9" r="2.5" fill="#207448" stroke="none"/>
      <circle cx="20" cy="9" r="2.5" fill="#207448" stroke="none"/>
      <polyline points="14,26 22,32 14,38" stroke-width="3"/>
      <line x1="26" y1="38" x2="40" y2="38" stroke-width="3"/>
    </g>
    <text x="175" y="242" font-family="sans-serif" font-size="32" font-weight="bold" fill="#303a36">Client 1</text>
  </g>

  <!-- ==================== CLIENT 2 ==================== -->
  <g id="node-c2">
    <rect x="60" y="440" width="380" height="120" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
    <!-- Window / Client Outline Icon (56px, stroke 4) -->
    <g transform="translate(90, 472)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="2" y="2" width="52" height="44" rx="6"/>
      <line x1="2" y1="16" x2="54" y2="16" stroke-width="3"/>
      <circle cx="12" cy="9" r="2.5" fill="#207448" stroke="none"/>
      <circle cx="20" cy="9" r="2.5" fill="#207448" stroke="none"/>
      <polyline points="14,26 22,32 14,38" stroke-width="3"/>
      <line x1="26" y1="38" x2="40" y2="38" stroke-width="3"/>
    </g>
    <text x="175" y="512" font-family="sans-serif" font-size="32" font-weight="bold" fill="#303a36">Client 2</text>
  </g>

  <!-- ==================== CLIENT N ==================== -->
  <g id="node-c3">
    <rect x="60" y="710" width="380" height="120" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
    <!-- Window / Client Outline Icon (56px, stroke 4) -->
    <g transform="translate(90, 742)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="2" y="2" width="52" height="44" rx="6"/>
      <line x1="2" y1="16" x2="54" y2="16" stroke-width="3"/>
      <circle cx="12" cy="9" r="2.5" fill="#207448" stroke="none"/>
      <circle cx="20" cy="9" r="2.5" fill="#207448" stroke="none"/>
      <polyline points="14,26 22,32 14,38" stroke-width="3"/>
      <line x1="26" y1="38" x2="40" y2="38" stroke-width="3"/>
    </g>
    <text x="175" y="782" font-family="sans-serif" font-size="32" font-weight="bold" fill="#303a36">Client N</text>
  </g>

  <!-- ==================== CLIENT FEEDERS AND BUS ==================== -->
  <!-- Horizontal feeder lines from Client boxes to vertical bus -->
  <line x1="440" y1="230" x2="580" y2="230" stroke="#207448" stroke-width="4" stroke-linecap="round"/>
  <line x1="440" y1="500" x2="580" y2="500" stroke="#207448" stroke-width="4" stroke-linecap="round"/>
  <line x1="440" y1="770" x2="580" y2="770" stroke="#207448" stroke-width="4" stroke-linecap="round"/>

  <!-- Vertical distribution spine extending slightly past top and bottom branch points -->
  <line x1="580" y1="200" x2="580" y2="800" stroke="#207448" stroke-width="4" stroke-linecap="round"/>

  <!-- Junction dots on the bus spine -->
  <circle cx="580" cy="230" r="5" fill="#207448"/>
  <circle cx="580" cy="500" r="5" fill="#207448"/>
  <circle cx="580" cy="770" r="5" fill="#207448"/>
  <circle cx="580" cy="420" r="5" fill="#207448"/>
  <circle cx="580" cy="600" r="5" fill="#207448"/>

  <!-- ==================== ARROWS FROM BUS TO TARGETS ==================== -->
  <!-- Arrow 1: To Metadata Service (Orange Highlight) -->
  <line x1="580" y1="220" x2="978" y2="220" stroke="#db8129" stroke-width="4" marker-end="url(#arrow-orange)"/>

  <!-- Arrow 2: To Data Server 1 -->
  <line x1="580" y1="420" x2="978" y2="420" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>

  <!-- Arrow 3: To Data Server 2 -->
  <line x1="580" y1="600" x2="978" y2="600" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>

  <!-- Arrow 4: To Data Server M -->
  <line x1="580" y1="780" x2="978" y2="780" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>

  <!-- ==================== METADATA SERVICE (ORANGE HIGHLIGHT) ==================== -->
  <g id="node-mds">
    <rect x="980" y="140" width="560" height="160" rx="14" fill="#ffffff" stroke="#db8129" stroke-width="3.5"/>
    <!-- Gear Outline Icon (56px, stroke 4, orange) -->
    <g transform="translate(1015, 192)" stroke="#db8129" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="14"/>
      <path d="M 28 4 L 28 12 M 28 44 L 28 52 M 4 28 L 12 28 M 44 28 L 52 28 M 11 11 L 17 17 M 39 39 L 45 45 M 11 45 L 17 39 M 39 17 L 45 11"/>
      <circle cx="28" cy="28" r="5" fill="#db8129" stroke="none"/>
    </g>
    <text x="1095" y="206" font-family="sans-serif" font-size="32" font-weight="bold" fill="#db8129">Metadata service</text>
    <text x="1095" y="252" font-family="sans-serif" font-size="24" fill="#303a36">names, permissions, layouts</text>
  </g>

  <!-- ==================== MDS - D1 CONNECTION (NO ARROWHEAD) ==================== -->
  <line x1="1260" y1="300" x2="1260" y2="360" stroke="#207448" stroke-width="3.5" stroke-dasharray="8 6"/>

  <!-- ==================== DATA SERVER 1 ==================== -->
  <g id="node-d1">
    <rect x="980" y="360" width="560" height="120" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
    <!-- Disk Cylinder Icon (56px, stroke 3.5) -->
    <g transform="translate(1015, 392)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <ellipse cx="28" cy="14" rx="22" ry="7"/>
      <path d="M 6 14 v 14 a 22 7 0 0 0 44 0 v -14"/>
      <path d="M 6 28 v 14 a 22 7 0 0 0 44 0 v -14"/>
    </g>
    <text x="1095" y="432" font-family="sans-serif" font-size="32" font-weight="bold" fill="#303a36">Data server 1</text>
  </g>

  <!-- ==================== DATA SERVER 2 ==================== -->
  <g id="node-d2">
    <rect x="980" y="540" width="560" height="120" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
    <!-- Disk Cylinder Icon (56px, stroke 3.5) -->
    <g transform="translate(1015, 572)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <ellipse cx="28" cy="14" rx="22" ry="7"/>
      <path d="M 6 14 v 14 a 22 7 0 0 0 44 0 v -14"/>
      <path d="M 6 28 v 14 a 22 7 0 0 0 44 0 v -14"/>
    </g>
    <text x="1095" y="612" font-family="sans-serif" font-size="32" font-weight="bold" fill="#303a36">Data server 2</text>
  </g>

  <!-- ==================== DATA SERVER M ==================== -->
  <g id="node-d3">
    <rect x="980" y="720" width="560" height="120" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
    <!-- Disk Cylinder Icon (56px, stroke 3.5) -->
    <g transform="translate(1015, 752)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <ellipse cx="28" cy="14" rx="22" ry="7"/>
      <path d="M 6 14 v 14 a 22 7 0 0 0 44 0 v -14"/>
      <path d="M 6 28 v 14 a 22 7 0 0 0 44 0 v -14"/>
    </g>
    <text x="1095" y="792" font-family="sans-serif" font-size="32" font-weight="bold" fill="#303a36">Data server M</text>
  </g>
</svg>"""

with open("output_pfs.svg", "w") as f:
    f.write(svg_template)

print("Saved output_pfs.svg")
