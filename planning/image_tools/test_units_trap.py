import xml.etree.ElementTree as ET
import re
import subprocess
import pathlib

svg_code = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1000" width="1600" height="1000">
  <title>Requests, limits and the m versus M trap</title>
  <desc>Visual explanation of Kubernetes container resource requests as guaranteed minimums, resource limits as maximum allowances, and the thousandfold difference between lowercase m and uppercase M units.</desc>

  <defs>
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1600" height="1000" fill="#f5f8f5" />

  <!-- Title -->
  <text x="800" y="58" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36" text-anchor="middle">Requests, limits and the m versus M trap</text>

  <!-- Top Row: Left Card (requests) -->
  <g id="card-requests">
    <rect x="60" y="100" width="720" height="270" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="3" />
    
    <!-- Container box icon with request bar and limit bar -->
    <g transform="translate(85, 120)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="0" y="0" width="56" height="56" rx="8" />
      <line x1="8" y1="46" x2="48" y2="46" stroke-width="3" />
      <line x1="8" y1="16" x2="48" y2="16" stroke-width="2" stroke-dasharray="3,3" />
      <rect x="12" y="24" width="14" height="22" rx="2" fill="#207448" stroke="none" />
      <rect x="30" y="16" width="14" height="30" rx="2" stroke-width="2.5" stroke-dasharray="3,2" />
    </g>

    <text x="160" y="162" font-family="sans-serif" font-size="34" font-weight="bold" fill="#303a36">requests</text>

    <!-- Chip 1: cpu: 500m, half a CPU -->
    <rect x="85" y="195" width="670" height="60" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="420" y="235" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36" text-anchor="middle">cpu: 500m, half a CPU</text>

    <!-- Chip 2: memory: 128Mi -->
    <rect x="85" y="275" width="670" height="60" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="420" y="315" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36" text-anchor="middle">memory: 128Mi</text>
  </g>

  <!-- Top Row: Right Card (limits) -->
  <g id="card-limits">
    <rect x="820" y="100" width="720" height="270" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="3" />
    
    <!-- Limit ceiling icon -->
    <g transform="translate(845, 120)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="0" y="0" width="56" height="56" rx="8" />
      <line x1="8" y1="12" x2="48" y2="12" stroke-width="4" />
      <rect x="20" y="12" width="16" height="34" rx="2" fill="#207448" stroke="none" />
      <line x1="8" y1="46" x2="48" y2="46" stroke-width="3" />
    </g>

    <text x="920" y="162" font-family="sans-serif" font-size="34" font-weight="bold" fill="#303a36">limits</text>

    <!-- Note on limits card -->
    <rect x="845" y="195" width="670" height="140" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="1180" y="277" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36" text-anchor="middle">the most the container may use</text>
  </g>

  <!-- Units Comparison: Row 1 (Lowercase m = milli) -->
  <g id="row-lowercase">
    <rect x="60" y="410" width="1480" height="165" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="3" />
    
    <!-- Scale icon for tiny fraction -->
    <g transform="translate(85, 430)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="22" cy="22" r="16" />
      <line x1="34" y1="34" x2="48" y2="48" />
      <circle cx="22" cy="22" r="4" fill="#207448" stroke="none" />
    </g>

    <!-- Column 1: Lowercase m = milli & example 400m -->
    <text x="160" y="465" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Lowercase m = milli</text>
    
    <rect x="160" y="495" width="180" height="55" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="250" y="534" font-family="monospace" font-size="28" font-weight="bold" fill="#207448" text-anchor="middle">400m</text>

    <!-- Column 2: Meaning -->
    <rect x="740" y="430" width="770" height="125" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="1125" y="504" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36" text-anchor="middle">a small fraction of one unit</text>
  </g>

  <!-- Bridge Arrow between Row 1 and Row 2 -->
  <g id="bridge-connection">
    <line x1="250" y1="575" x2="250" y2="655" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />
    <rect x="290" y="594" width="340" height="42" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="460" y="624" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36" text-anchor="middle">Factor of a thousand</text>
  </g>

  <!-- Units Comparison: Row 2 (Uppercase M = mega) -->
  <g id="row-uppercase">
    <!-- Orange outline as specified for the single most important item -->
    <rect x="60" y="655" width="1480" height="165" rx="14" fill="#ffffff" stroke="#db8129" stroke-width="4" />
    
    <!-- Warning icon -->
    <g transform="translate(85, 675)" stroke="#303a36" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <polygon points="28,4 52,48 4,48" />
      <line x1="28" y1="18" x2="28" y2="32" stroke-width="3" />
      <circle cx="28" cy="40" r="2.5" fill="#303a36" stroke="none" />
    </g>

    <!-- Column 1: Uppercase M = mega & example 400M -->
    <text x="160" y="710" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Uppercase M = mega</text>
    
    <rect x="160" y="740" width="180" height="55" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="250" y="779" font-family="monospace" font-size="28" font-weight="bold" fill="#303a36" text-anchor="middle">400M</text>

    <!-- Column 2: Meaning -->
    <rect x="740" y="675" width="770" height="125" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="1125" y="749" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36" text-anchor="middle">a thousand times larger than 400m</text>
  </g>

  <!-- Bottom Takeaway Bar -->
  <g id="takeaway-bar">
    <rect x="60" y="865" width="1480" height="75" rx="12" fill="#207448" />
    <text x="800" y="913" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">Requests belong to each container. The Pod total is the sum of its containers.</text>
  </g>
</svg>'''

pathlib.Path("test_output.svg").write_text(svg_code)
print("Saved test_output.svg")
