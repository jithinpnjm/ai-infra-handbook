import re
import xml.etree.ElementTree as ET

svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>Statistics traps: the harmonic mean, the average that describes no request, and a bounded gain</title>
  <desc>Statistics traps: the harmonic mean, the average that describes no request, and a bounded gain</desc>

  <!-- Background -->
  <rect width="1600" height="1200" fill="#f5f8f5" />

  <!-- Main Title -->
  <text x="800" y="52" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">Statistics traps: the harmonic mean, the average</tspan>
    <tspan x="800" dy="56">that describes no request, and a bounded gain</tspan>
  </text>

  <!-- ==================== CARD 1 ==================== -->
  <rect x="40" y="145" width="480" height="735" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
  
  <!-- Card 1 Header: Icon + Title -->
  <g transform="translate(65, 160)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <path d="M 10 44 A 20 20 0 1 1 46 44" />
    <line x1="28" y1="32" x2="38" y2="18" />
    <circle cx="28" cy="32" r="3" fill="#207448" />
  </g>
  <text x="135" y="185" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">
    <tspan x="135" dy="0">Harmonic mean</tspan>
    <tspan x="135" dy="36">for rates</tspan>
  </text>

  <!-- Card 1 Box 1: send rates -->
  <rect x="60" y="245" width="440" height="85" rx="10" fill="#ffffff" stroke="#c0d4c6" stroke-width="1.5" />
  <text x="80" y="280" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="80" dy="0">send 100 MB at 50 MB/s,</tspan>
    <tspan x="80" dy="32">then 700 MB at 10 MB/s</tspan>
  </text>

  <!-- Card 1 Box 2: time bar -->
  <rect x="60" y="345" width="440" height="120" rx="10" fill="#ffffff" stroke="#c0d4c6" stroke-width="1.5" />
  <g transform="translate(80, 362)">
    <rect x="0" y="0" width="30" height="24" rx="4" fill="#207448" />
    <rect x="35" y="0" width="365" height="24" rx="4" fill="#72a88a" />
  </g>
  <text x="80" y="418" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="80" dy="0">segment 1 takes 2 s,</tspan>
    <tspan x="80" dy="32">segment 2 takes 70 s</tspan>
  </text>

  <!-- Card 1 Box 3: formula -->
  <rect x="60" y="480" width="440" height="90" rx="10" fill="#ffffff" stroke="#c0d4c6" stroke-width="1.5" />
  <text x="80" y="516" font-family="monospace" font-size="24" font-weight="bold" fill="#207448">
    <tspan x="80" dy="0">800 / (100/50 + 700/10)</tspan>
    <tspan x="80" dy="34">= 11.1 MB/s</tspan>
  </text>

  <!-- Card 1 Box 4: crossed-out arithmetic mean (Orange highlight) -->
  <rect x="60" y="585" width="440" height="65" rx="10" fill="#fef8f2" stroke="#db8129" stroke-width="2" />
  <text x="280" y="626" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#db8129">arithmetic mean 30 MB/s</text>
  <line x1="90" y1="618" x2="470" y2="618" stroke="#db8129" stroke-width="3" stroke-linecap="round" />

  <!-- Card 1 Box 5: note -->
  <rect x="60" y="665" width="440" height="195" rx="10" fill="#ffffff" stroke="#c0d4c6" stroke-width="1.5" />
  <text x="80" y="698" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="80" dy="0">arithmetic mean suits</tspan>
    <tspan x="80" dy="30">additive quantities,</tspan>
    <tspan x="80" dy="30">harmonic mean suits rates,</tspan>
    <tspan x="80" dy="30">geometric mean suits</tspan>
    <tspan x="80" dy="30">multiplicative effects such</tspan>
    <tspan x="80" dy="30">as stacked speed-ups</tspan>
  </text>

  <!-- ==================== CARD 2 ==================== -->
  <rect x="560" y="145" width="480" height="735" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

  <!-- Card 2 Header: Icon + Title -->
  <g transform="translate(585, 160)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <path d="M 8 46 L 14 46 C 18 46 20 20 23 20 C 26 20 28 44 33 44 C 37 44 39 30 42 30 C 44 30 46 46 48 46" />
    <line x1="6" y1="48" x2="50" y2="48" stroke-width="3" />
  </g>
  <text x="655" y="185" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">
    <tspan x="655" dy="0">A bimodal</tspan>
    <tspan x="655" dy="36">average</tspan>
  </text>

  <!-- Card 2 Box 1: histogram with clusters and average marker -->
  <rect x="580" y="245" width="440" height="185" rx="10" fill="#ffffff" stroke="#c0d4c6" stroke-width="1.5" />
  <!-- baseline axis -->
  <line x1="605" y1="390" x2="995" y2="390" stroke="#303a36" stroke-width="2.5" stroke-linecap="round" />
  <!-- cluster 1: cache hits -->
  <text x="662" y="274" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">cache hits</text>
  <rect x="618" y="340" width="16" height="50" rx="3" fill="#207448" />
  <rect x="640" y="295" width="16" height="95" rx="3" fill="#207448" />
  <rect x="662" y="282" width="16" height="108" rx="3" fill="#207448" />
  <rect x="684" y="310" width="16" height="80" rx="3" fill="#207448" />
  <rect x="706" y="355" width="16" height="35" rx="3" fill="#207448" />
  <!-- average marker sitting between clusters where no request lives -->
  <polygon points="792,274 808,274 800,287" fill="#303a36" />
  <line x1="800" y1="287" x2="800" y2="390" stroke="#303a36" stroke-width="3" stroke-dasharray="5,4" />
  <!-- cluster 2: misses -->
  <text x="926" y="325" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">misses</text>
  <rect x="882" y="355" width="16" height="35" rx="3" fill="#207448" />
  <rect x="904" y="335" width="16" height="55" rx="3" fill="#207448" />
  <rect x="926" y="342" width="16" height="48" rx="3" fill="#207448" />
  <rect x="948" y="368" width="16" height="22" rx="3" fill="#207448" />

  <!-- Card 2 Box 2: drowning quote -->
  <rect x="580" y="445" width="440" height="120" rx="10" fill="#ffffff" stroke="#c0d4c6" stroke-width="1.5" />
  <text x="600" y="480" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="600" dy="0">The man drowned in a</tspan>
    <tspan x="600" dy="32">river with an average</tspan>
    <tspan x="600" dy="32">depth of six inches</tspan>
  </text>

  <!-- Card 2 Box 3: percentiles and straggler -->
  <rect x="580" y="580" width="440" height="280" rx="10" fill="#ffffff" stroke="#c0d4c6" stroke-width="1.5" />
  <text x="600" y="612" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="600" dy="0">ask for the distribution;</tspan>
    <tspan x="600" dy="28">use percentiles p50, p90,</tspan>
    <tspan x="600" dy="28">p95, p99, p99.9; in</tspan>
    <tspan x="600" dy="28">distributed training the</tspan>
    <tspan x="600" dy="28">slowest rank, the</tspan>
    <tspan x="600" dy="28">straggler, sets the step</tspan>
    <tspan x="600" dy="28">time, so the maximum and</tspan>
    <tspan x="600" dy="28">tail across ranks matter</tspan>
    <tspan x="600" dy="28">more than the mean</tspan>
  </text>

  <!-- ==================== CARD 3 ==================== -->
  <rect x="1080" y="145" width="480" height="735" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

  <!-- Card 3 Header: Icon + Title -->
  <g transform="translate(1105, 160)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <ellipse cx="28" cy="14" rx="18" ry="7" />
    <path d="M 10 14 V 42 C 10 47 46 47 46 42 V 14" />
    <path d="M 10 28 C 10 33 46 33 46 28" />
  </g>
  <text x="1175" y="185" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">
    <tspan x="1175" dy="0">Quantify a gain</tspan>
    <tspan x="1175" dy="36">before you act</tspan>
  </text>

  <!-- Card 3 Box 1: quantify gain -->
  <rect x="1100" y="245" width="440" height="240" rx="10" fill="#ffffff" stroke="#c0d4c6" stroke-width="1.5" />
  <text x="1120" y="280" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="1120" dy="0">a request takes 10 ms and</tspan>
    <tspan x="1120" dy="32">9 ms of it is disk;</tspan>
    <tspan x="1120" dy="32">replacing the reads with</tspan>
    <tspan x="1120" dy="32">a cache that costs 10</tspan>
    <tspan x="1120" dy="32">microseconds gives</tspan>
    <tspan x="1120" dy="32">10 / 1.01 = 9.9x at best</tspan>
  </text>

  <!-- Card 3 Box 2: note -->
  <rect x="1100" y="500" width="440" height="175" rx="10" fill="#ffffff" stroke="#c0d4c6" stroke-width="1.5" />
  <text x="1120" y="540" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="1120" dy="0">make sure the latency</tspan>
    <tspan x="1120" dy="32">you cut is on the</tspan>
    <tspan x="1120" dy="32">synchronous path, not</tspan>
    <tspan x="1120" dy="32">in background work</tspan>
  </text>

  <!-- ==================== BOTTOM STRIP ==================== -->
  <rect x="40" y="905" width="1520" height="135" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
  <g transform="translate(65, 942)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <path d="M 22 8 L 34 8 M 25 8 V 20 L 10 44 C 8 47 11 50 15 50 L 41 50 C 45 50 48 47 46 44 L 31 20 V 8" />
    <line x1="16" y1="38" x2="40" y2="38" stroke-width="3" />
  </g>
  <text x="140" y="962" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="140" dy="0">Experiments: repeat, report the median and the spread, control clocks, thermal state,</tspan>
    <tspan x="140" dy="36">cache state and neighbours; a 3% difference with 5% run-to-run variation is noise</tspan>
  </text>

  <!-- ==================== BOTTOM TAKEAWAY BAR ==================== -->
  <rect x="40" y="1065" width="1520" height="85" rx="12" fill="#207448" />
  <g transform="translate(65, 1079)" stroke="#ffffff" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="28" cy="28" r="22" />
    <polyline points="18 28 25 35 38 20" />
  </g>
  <text x="800" y="1118" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">Before you claim a win, check the distribution and repeat the run</text>
</svg>"""

with open("candidate_stats.svg", "w") as f:
    f.write(svg_content)

print("Saved candidate_stats.svg")
