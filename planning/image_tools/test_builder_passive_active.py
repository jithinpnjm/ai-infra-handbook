import xml.etree.ElementTree as ET
import re

svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>Passive checks find faults, active checks prove a repaired node</title>
  <desc>Comparison of passive hardware telemetry with active dcgmi diag checks across four depth levels, lifecycle placement, and automation exit codes.</desc>

  <!-- Background -->
  <rect width="1600" height="1200" fill="#f5f8f5"/>

  <!-- Title (48px bold) -->
  <text x="800" y="62" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">Passive checks find faults,</tspan>
    <tspan x="800" dy="56">active checks prove a repaired node</tspan>
  </text>

  <!-- Left Box: Passive -->
  <rect x="40" y="145" width="730" height="185" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <g transform="translate(685, 165)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="0" y="0" width="56" height="50" rx="8"/>
    <polyline points="6,25 18,25 24,12 32,38 38,20 44,25 50,25"/>
  </g>
  <text x="70" y="195" font-family="sans-serif" font-size="25" fill="#303a36">
    <tspan x="70" dy="0" font-weight="bold" font-size="28" fill="#207448">Passive: </tspan><tspan font-size="25">reads what hardware already</tspan>
    <tspan x="70" dy="38" font-size="25">reports, always on, cheap, only sees</tspan>
    <tspan x="70" dy="38" font-size="25">faults that already produced an error</tspan>
  </text>

  <!-- Right Box: Active -->
  <rect x="830" y="145" width="730" height="185" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <g transform="translate(1475, 165)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="8" y="8" width="40" height="40" rx="6"/>
    <rect x="18" y="18" width="20" height="20" rx="3" stroke-width="3"/>
    <line x1="16" y1="0" x2="16" y2="8"/><line x1="28" y1="0" x2="28" y2="8"/><line x1="40" y1="0" x2="40" y2="8"/>
    <line x1="16" y1="48" x2="16" y2="56"/><line x1="28" y1="48" x2="28" y2="56"/><line x1="40" y1="48" x2="40" y2="56"/>
    <line x1="0" y1="16" x2="8" y2="16"/><line x1="0" y1="28" x2="8" y2="28"/><line x1="0" y1="40" x2="8" y2="40"/>
    <line x1="48" y1="16" x2="56" y2="16"/><line x1="48" y1="28" x2="56" y2="28"/><line x1="48" y1="40" x2="56" y2="40"/>
  </g>
  <text x="860" y="188" font-family="sans-serif" font-size="25" fill="#303a36">
    <tspan x="860" dy="0" font-weight="bold" font-size="28" fill="#207448">Active: </tspan><tspan font-family="monospace" font-size="25">dcgmi diag </tspan><tspan font-size="25">does work on the</tspan>
    <tspan x="860" dy="34" font-size="25">GPU and compares with a healthy GPU,</tspan>
    <tspan x="860" dy="34" font-size="25">finds weak hardware not yet failed,</tspan>
    <tspan x="860" dy="34" font-size="25">node usually out of service</tspan>
  </text>

  <!-- Table of Levels - Level 1 -->
  <rect x="40" y="355" width="1520" height="92" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
  <g transform="translate(65, 376)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <path d="M 12 6 L 36 6 C 36 28 24 38 24 44 C 24 38 12 28 12 6 Z"/>
    <polyline points="18,22 23,27 31,17"/>
  </g>
  <text x="135" y="392" font-family="sans-serif" font-size="26" fill="#303a36">
    <tspan x="135" dy="0" font-weight="bold" font-size="28" fill="#207448">level 1 </tspan><tspan font-family="monospace" font-size="26">dcgmi diag -r 1: </tspan><tspan font-size="26">software, driver, permissions,</tspan>
    <tspan x="135" dy="36" font-size="25" fill="#506059">under 2.5 seconds</tspan>
  </text>

  <!-- Table of Levels - Level 2 -->
  <rect x="40" y="462" width="1520" height="92" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
  <g transform="translate(65, 483)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="24" cy="25" r="14"/>
    <circle cx="24" cy="25" r="6"/>
    <line x1="24" y1="3" x2="24" y2="9"/><line x1="24" y1="41" x2="24" y2="47"/>
    <line x1="2" y1="25" x2="8" y2="25"/><line x1="40" y1="25" x2="46" y2="25"/>
    <line x1="9" y1="10" x2="14" y2="15"/><line x1="34" y1="35" x2="39" y2="40"/>
    <line x1="9" y1="40" x2="14" y2="35"/><line x1="34" y1="15" x2="39" y2="10"/>
  </g>
  <text x="135" y="499" font-family="sans-serif" font-size="26" fill="#303a36">
    <tspan x="135" dy="0" font-weight="bold" font-size="28" fill="#207448">level 2 </tspan><tspan font-family="monospace" font-size="26">-r 2: </tspan><tspan font-size="26">extended validation,</tspan>
    <tspan x="135" dy="36" font-size="25" fill="#506059">under 2.5 min on 4 GPUs, under 10.5 min on 8</tspan>
  </text>

  <!-- Table of Levels - Level 3 (Orange highlight - the gate proving repair) -->
  <rect x="40" y="569" width="1520" height="92" rx="12" fill="#fff5ec" stroke="#db8129" stroke-width="3"/>
  <g transform="translate(65, 590)" stroke="#db8129" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <polygon points="26,4 12,26 24,26 20,46 36,20 24,20"/>
  </g>
  <text x="135" y="606" font-family="sans-serif" font-size="26" fill="#303a36">
    <tspan x="135" dy="0" font-weight="bold" font-size="28" fill="#db8129">level 3 </tspan><tspan font-family="monospace" font-size="26" fill="#db8129">-r 3: </tspan><tspan font-size="26">stress, power, bandwidth and NCCL tests,</tspan>
    <tspan x="135" dy="36" font-size="25" fill="#506059">under 10 min on 4 GPUs, under 35 min on 8</tspan>
  </text>

  <!-- Table of Levels - Level 4 -->
  <rect x="40" y="676" width="1520" height="92" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
  <g transform="translate(65, 697)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="4" y="10" width="40" height="30" rx="4"/>
    <line x1="14" y1="10" x2="14" y2="40"/><line x1="24" y1="10" x2="24" y2="40"/><line x1="34" y1="10" x2="34" y2="40"/>
    <line x1="4" y1="25" x2="44" y2="25"/>
  </g>
  <text x="135" y="713" font-family="sans-serif" font-size="26" fill="#303a36">
    <tspan x="135" dy="0" font-weight="bold" font-size="28" fill="#207448">level 4 </tspan><tspan font-family="monospace" font-size="26">-r 4: </tspan><tspan font-size="26">adds memory test and power pulse test,</tspan>
    <tspan x="135" dy="36" font-size="25" fill="#506059">under 45 min on 4 GPUs, under 2.25 h on 8</tspan>
  </text>

  <!-- Where each runs Container -->
  <rect x="40" y="785" width="1520" height="235" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <g transform="translate(65, 810)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="16" cy="16" r="10"/>
    <circle cx="16" cy="40" r="10"/>
    <circle cx="40" cy="28" r="10"/>
    <path d="M 26 16 L 30 22 M 26 40 L 30 34"/>
  </g>
  <text x="135" y="835" font-family="sans-serif" font-size="26" fill="#303a36">
    <tspan x="135" dy="0" font-weight="bold" font-size="26">passive: </tspan><tspan font-size="26">continuously on every node;</tspan>
    <tspan x="135" dy="44" font-weight="bold" font-size="26">level 1: </tspan><tspan font-size="26">when a node is about to take traffic;</tspan>
    <tspan x="135" dy="44" font-weight="bold" font-size="26" fill="#db8129">level 3: </tspan><tspan font-size="26">gate when a node leaves repair;</tspan>
    <tspan x="135" dy="44" font-weight="bold" font-size="26">multi-node NCCL test: </tspan><tspan font-size="26">gate for a node joining a training or large tensor-parallel group</tspan>
  </text>

  <!-- Automation note -->
  <rect x="40" y="1040" width="1520" height="95" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2"/>
  <g transform="translate(65, 1065)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="0" y="0" width="48" height="40" rx="6"/>
    <polyline points="10,14 18,20 10,26"/>
    <line x1="22" y1="26" x2="34" y2="26"/>
  </g>
  <text x="135" y="1098" font-family="sans-serif" font-size="26" fill="#303a36">
    <tspan font-family="monospace" font-size="26" font-weight="bold">exit code 0 </tspan><tspan font-size="26">success, </tspan><tspan font-family="monospace" font-size="26" font-weight="bold">226 </tspan><tspan font-size="26">diagnostic ran and reported an error, </tspan><tspan font-size="26">add </tspan><tspan font-family="monospace" font-size="26" font-weight="bold">-j </tspan><tspan font-size="26">for JSON</tspan>
  </text>
</svg>"""

with open("test_passive_active.svg", "w") as f:
    f.write(svg_content)

print("SVG written to test_passive_active.svg")
