import subprocess

svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1130" width="1600" height="1130">
  <title>Five steps for a memory problem, changing one thing at a time</title>
  <desc>A diagnostic roadmap for memory problems: USE check, workload characterisation, differential diagnosis of growth versus leak, static setup inspection, and systematic tuning changing one setting at a time.</desc>

  <defs>
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />
    </marker>
    <marker id="arrow-orange" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#db8129" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1600" height="1130" fill="#f5f8f5" />

  <!-- Title -->
  <text x="800" y="52" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">Five steps for a memory problem, </tspan>
    <tspan x="800" dy="54">changing one thing at a time</tspan>
  </text>

  <!-- ================= TIER 1 ================= -->

  <!-- STEP 1 BOX -->
  <g id="step-1-box">
    <rect x="60" y="145" width="680" height="190" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="3" />
    <!-- Numbered circle 1 -->
    <circle cx="106" cy="191" r="24" fill="#207448" />
    <text x="106" y="200" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="28" font-weight="bold" fill="#ffffff">1</text>
    <!-- Chip icon -->
    <g transform="translate(150, 163)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="10" y="10" width="36" height="36" rx="6" />
      <rect x="18" y="18" width="20" height="20" />
      <line x1="18" y1="2" x2="18" y2="10" />
      <line x1="28" y1="2" x2="28" y2="10" />
      <line x1="38" y1="2" x2="38" y2="10" />
      <line x1="18" y1="46" x2="18" y2="54" />
      <line x1="28" y1="46" x2="28" y2="54" />
      <line x1="38" y1="46" x2="38" y2="54" />
      <line x1="2" y1="18" x2="10" y2="18" />
      <line x1="2" y1="28" x2="10" y2="28" />
      <line x1="2" y1="38" x2="10" y2="38" />
      <line x1="46" y1="18" x2="54" y2="18" />
      <line x1="46" y1="28" x2="54" y2="28" />
      <line x1="46" y1="38" x2="54" y2="38" />
    </g>
    <!-- Step 1 label text -->
    <text x="226" y="200" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#207448">
      <tspan x="226" dy="0">USE check: </tspan>
      <tspan x="106" dy="58" font-size="26" font-weight="normal" fill="#303a36">utilisation, saturation, errors</tspan>
    </text>
  </g>

  <!-- Arrow Step 1 -> Step 2 -->
  <line x1="740" y1="240" x2="856" y2="240" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />

  <!-- STEP 2 BOX -->
  <g id="step-2-box">
    <rect x="860" y="145" width="680" height="190" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="3" />
    <!-- Numbered circle 2 -->
    <circle cx="906" cy="191" r="24" fill="#207448" />
    <text x="906" y="200" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="28" font-weight="bold" fill="#ffffff">2</text>
    <!-- Window icon -->
    <g transform="translate(950, 163)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="6" width="48" height="42" rx="6" />
      <line x1="4" y1="18" x2="52" y2="18" />
      <circle cx="12" cy="12" r="2" fill="#207448" />
      <circle cx="18" cy="12" r="2" fill="#207448" />
      <circle cx="24" cy="12" r="2" fill="#207448" />
      <line x1="12" y1="30" x2="28" y2="30" />
      <line x1="12" y1="38" x2="40" y2="38" />
    </g>
    <!-- Step 2 label text -->
    <text x="1026" y="200" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#207448">
      <tspan x="1026" dy="0">Characterise: </tspan>
      <tspan x="906" dy="50" font-size="24" font-weight="normal" fill="#303a36">kernel or user memory, cache or anonymous, </tspan>
      <tspan x="906" dy="38" font-size="24" font-weight="normal" fill="#303a36">top RSS, cgroup limits</tspan>
    </text>
  </g>

  <!-- ================= TRANSITION TIER 1 -> TIER 2 ================= -->
  <!-- Arrow Step 2 -> Step 3 Diamond -->
  <path d="M 1200 335 V 375 H 230 V 476" fill="none" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />

  <!-- ================= TIER 2 ================= -->

  <!-- STEP 3 DIAMOND -->
  <g id="step-3-diamond">
    <polygon points="230,480 370,595 230,710 90,595" fill="#e8f1ea" stroke="#207448" stroke-width="3.5" stroke-linejoin="round" />
    <!-- Numbered circle 3 -->
    <circle cx="230" cy="480" r="24" fill="#207448" />
    <text x="230" y="489" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="28" font-weight="bold" fill="#ffffff">3</text>
    <!-- Diamond text -->
    <text x="230" y="582" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">
      <tspan x="230" dy="0">Growth or </tspan>
      <tspan x="230" dy="36">leak?</tspan>
    </text>
  </g>

  <!-- Upper arrow from Diamond to Upper Box -->
  <path d="M 370 595 H 430 V 495 H 856" fill="none" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />
  <!-- Upper arrow label: 3 clean balanced lines -->
  <text x="635" y="435" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#207448">
    <tspan x="635" dy="0">Growth: normal use </tspan>
    <tspan x="635" dy="30">at a higher rate, or </tspan>
    <tspan x="635" dy="30">a cache warming up</tspan>
  </text>

  <!-- UPPER BOX (Green box) -->
  <g id="upper-box">
    <rect x="860" y="430" width="680" height="135" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="3" />
    <text x="1200" y="490" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#207448">
      <tspan x="1200" dy="0">Check the configuration, </tspan>
      <tspan x="1200" dy="38" font-size="24" font-weight="normal" fill="#303a36">cache sizes and allocator</tspan>
    </text>
  </g>

  <!-- Lower arrow from Diamond to Lower Box (Orange outline / stroke) -->
  <path d="M 370 595 H 430 V 695 H 856" fill="none" stroke="#db8129" stroke-width="4" marker-end="url(#arrow-orange)" />
  <!-- Lower arrow label: 2 clean balanced lines -->
  <text x="635" y="650" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#db8129">
    <tspan x="635" dy="0">Leak: allocated </tspan>
    <tspan x="635" dy="32">and never freed, a bug</tspan>
  </text>

  <!-- LOWER BOX (Leak path) -->
  <g id="lower-box">
    <rect x="860" y="625" width="680" height="145" rx="16" fill="#ffffff" stroke="#207448" stroke-width="3" />
    <text x="1200" y="675" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#303a36">
      <tspan x="1200" dy="0">Find the allocation path: </tspan>
      <tspan x="1200" dy="42" font-family="ui-monospace, Menlo, Consolas, monospace" font-size="24" font-weight="normal" fill="#303a36">memleak, jemalloc or tcmalloc profiling, </tspan>
      <tspan x="1200" dy="34" font-family="ui-monospace, Menlo, Consolas, monospace" font-size="24" font-weight="normal" fill="#303a36">tracemalloc, memray</tspan>
    </text>
  </g>

  <!-- ================= TRANSITION TIER 2 -> TIER 3 ================= -->
  <!-- Arrow Upper Box -> Step 4 -->
  <path d="M 1540 497 H 1565 V 805 H 300 V 841" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
  <!-- Arrow Lower Box -> Step 4 -->
  <path d="M 1100 770 V 820 H 450 V 841" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- ================= TIER 3 ================= -->

  <!-- STEP 4 BOX -->
  <g id="step-4-box">
    <rect x="60" y="845" width="680" height="180" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="3" />
    <!-- Numbered circle 4 -->
    <circle cx="106" cy="891" r="24" fill="#207448" />
    <text x="106" y="900" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="28" font-weight="bold" fill="#ffffff">4</text>
    <!-- Gear icon -->
    <g transform="translate(150, 863)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="14" />
      <path d="M 28 6 L 28 14 M 28 42 L 28 50 M 6 28 L 14 28 M 42 28 L 50 28 M 12.4 12.4 L 18.1 18.1 M 37.9 37.9 L 43.6 43.6 M 12.4 43.6 L 18.1 37.9 M 37.9 18.1 L 43.6 12.4" />
    </g>
    <!-- Step 4 label text -->
    <text x="226" y="898" font-family="system-ui, -apple-system, sans-serif" font-size="28" font-weight="bold" fill="#207448">
      <tspan x="226" dy="0">Check the static setup: </tspan>
      <tspan x="106" dy="48" font-size="24" font-weight="normal" fill="#303a36">DIMMs, NUMA mode, huge pages, </tspan>
      <tspan x="106" dy="36" font-size="24" font-weight="normal" fill="#303a36">overcommit, limits, allocator</tspan>
    </text>
  </g>

  <!-- Arrow Step 4 -> Step 5 -->
  <line x1="740" y1="935" x2="856" y2="935" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />

  <!-- STEP 5 BOX (Orange outline) -->
  <g id="step-5-box">
    <rect x="860" y="845" width="680" height="180" rx="16" fill="#ffffff" stroke="#db8129" stroke-width="3.5" />
    <!-- Numbered circle 5 -->
    <circle cx="906" cy="891" r="24" fill="#207448" />
    <text x="906" y="900" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="28" font-weight="bold" fill="#ffffff">5</text>
    <!-- Step 5 label text -->
    <text x="960" y="920" font-family="system-ui, -apple-system, sans-serif" font-size="34" font-weight="bold" fill="#db8129">
      <tspan x="960" dy="0">Tune last, </tspan>
      <tspan x="960" dy="50" font-size="30" font-weight="bold" fill="#303a36">one change at a time</tspan>
    </text>
  </g>

  <!-- ================= TAKEAWAY BAR ================= -->
  <g id="takeaway-bar">
    <rect x="60" y="1045" width="1480" height="60" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <text x="800" y="1084" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="28" font-weight="bold" fill="#207448">A memory investigation goes wrong when three settings change at once.</text>
  </g>
</svg>'''

with open("test_memory2.svg", "w") as f:
    f.write(svg_content)

print("Saved test_memory2.svg")
