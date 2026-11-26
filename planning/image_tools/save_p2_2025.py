import xml.etree.ElementTree as ET
import re
import subprocess
import pathlib

svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1050" width="1600" height="1050">
  <title>Summing counters before rate hides the restart</title>
  <desc>Visual comparison showing why summing counters before rate hides pod restarts while taking rate per series first correctly preserves the reset and yields the true fleet rate.</desc>

  <defs>
    <marker id="arrow-green" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="9" markerHeight="9" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#207448" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1600" height="1050" fill="#f5f8f5" />

  <!-- Title -->
  <text x="800" y="75" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Summing counters before rate hides the restart</text>

  <!-- ==================== LEFT PANEL (WRONG) ==================== -->
  <rect x="50" y="130" width="720" height="650" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2" />

  <!-- Left Header Icon: Outline Alert Box -->
  <g transform="translate(75, 150)">
    <circle cx="28" cy="28" r="24" fill="none" stroke="#207448" stroke-width="4" />
    <line x1="28" y1="14" x2="28" y2="30" stroke="#207448" stroke-width="4" stroke-linecap="round" />
    <circle cx="28" cy="40" r="3" fill="#207448" />
  </g>

  <!-- Left Header Text -->
  <text x="145" y="186" font-family="sans-serif" font-size="32" font-weight="bold" fill="#207448">Wrong: sum first, then rate</text>

  <!-- Left Chart Box (Two counter lines over time) -->
  <rect x="75" y="225" width="670" height="260" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />

  <!-- Axes & Grid -->
  <line x1="120" y1="445" x2="710" y2="445" stroke="#d5dfd8" stroke-width="2" />
  <line x1="120" y1="260" x2="120" y2="445" stroke="#d5dfd8" stroke-width="2" />
  <line x1="120" y1="352" x2="710" y2="352" stroke="#e8f1ea" stroke-width="1.5" stroke-dasharray="4 4" />
  <line x1="415" y1="260" x2="415" y2="445" stroke="#d5dfd8" stroke-width="1.5" stroke-dasharray="3 3" />

  <!-- Pod A Counter Line (climbs to 100, drops to 0 at restart, resumes) -->
  <path d="M 120 352 L 415 260 L 415 445 L 710 352" fill="none" stroke="#207448" stroke-width="4" stroke-linejoin="round" />
  <circle cx="415" cy="260" r="6" fill="#207448" />
  <circle cx="415" cy="445" r="6" fill="#207448" />

  <!-- Pod B Counter Line (climbs steadily by 100) -->
  <path d="M 120 445 L 415 352 L 710 260" fill="none" stroke="#207448" stroke-width="4" stroke-dasharray="8 6" stroke-linejoin="round" />
  <circle cx="415" cy="352" r="6" fill="#207448" />
  <circle cx="710" cy="260" r="6" fill="#207448" />

  <!-- Arrow down from chart to flat total line -->
  <line x1="410" y1="485" x2="410" y2="525" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />

  <!-- Flat Total Line Card (Orange Outline) -->
  <rect x="75" y="535" width="670" height="220" rx="12" fill="#ffffff" stroke="#db8129" stroke-width="3.5" />

  <!-- Flat Total Line Visualization -->
  <line x1="120" y1="575" x2="700" y2="575" stroke="#db8129" stroke-width="5" stroke-linecap="round" />

  <!-- Flat line label -->
  <text x="410" y="625" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36">
    <tspan x="410" dy="0">Sum stays flat:</tspan>
    <tspan x="410" dy="34">the reset is invisible</tspan>
  </text>

  <!-- Note on lost work -->
  <text x="410" y="700" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="410" dy="0">The work pod A did before</tspan>
    <tspan x="410" dy="32">the restart is lost</tspan>
  </text>


  <!-- ==================== RIGHT PANEL (RIGHT) ==================== -->
  <rect x="830" y="130" width="720" height="650" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2" />

  <!-- Right Header Icon: Checkmark Shield -->
  <g transform="translate(855, 145)">
    <path d="M 28 6 L 50 14 C 50 32 40 48 28 54 C 16 48 6 32 6 14 Z" fill="none" stroke="#207448" stroke-width="4" stroke-linejoin="round" />
    <path d="M 18 28 L 25 35 L 38 20" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" />
  </g>

  <!-- Right Header Text -->
  <text x="925" y="172" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">
    <tspan x="925" dy="0">Right: rate per series, then</tspan>
    <tspan x="925" dy="36">sum by the labels you keep</tspan>
  </text>

  <!-- Right Top Box: Two counter lines with per-series rate step -->
  <rect x="855" y="225" width="670" height="235" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />

  <!-- Mini Chart for Pod A with rate transformation -->
  <path d="M 885 295 L 1000 260 L 1000 330 L 1115 295" fill="none" stroke="#207448" stroke-width="3" stroke-linejoin="round" />
  <circle cx="1000" cy="260" r="4" fill="#207448" />
  <circle cx="1000" cy="330" r="4" fill="#207448" />
  <line x1="1135" y1="295" x2="1195" y2="295" stroke="#207448" stroke-width="2" stroke-dasharray="4 3" marker-end="url(#arrow-green)" />
  <rect x="1205" y="270" width="300" height="50" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  <path d="M 1225 295 L 1340 295" stroke="#207448" stroke-width="4" stroke-linecap="round" />
  <circle cx="1282" cy="295" r="5" fill="#207448" />

  <!-- Mini Chart for Pod B with rate transformation -->
  <path d="M 885 415 L 1000 380 L 1115 345" fill="none" stroke="#207448" stroke-width="3" stroke-dasharray="6 4" stroke-linejoin="round" />
  <circle cx="1000" cy="380" r="4" fill="#207448" />
  <circle cx="1115" cy="345" r="4" fill="#207448" />
  <line x1="1135" y1="380" x2="1195" y2="380" stroke="#207448" stroke-width="2" stroke-dasharray="4 3" marker-end="url(#arrow-green)" />
  <rect x="1205" y="355" width="300" height="50" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  <path d="M 1225 380 L 1340 380" stroke="#207448" stroke-width="4" stroke-dasharray="6 4" stroke-linecap="round" />
  <circle cx="1282" cy="380" r="5" fill="#207448" />

  <!-- Arrow down from rate steps to sum box -->
  <line x1="1190" y1="460" x2="1190" y2="495" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />

  <!-- Sum Box -->
  <rect x="910" y="505" width="560" height="85" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="3" />
  <text x="1190" y="558" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#207448">sum by the labels you keep</text>

  <!-- Arrow down from sum box to result line -->
  <line x1="1190" y1="590" x2="1190" y2="625" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />

  <!-- Green Result Line Card -->
  <rect x="855" y="635" width="670" height="120" rx="12" fill="#ffffff" stroke="#207448" stroke-width="3" />
  <line x1="895" y1="670" x2="1485" y2="670" stroke="#207448" stroke-width="6" stroke-linecap="round" />
  <text x="1190" y="726" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448">Fleet rate, reset handled per pod</text>


  <!-- ==================== BOTTOM FORMULA STRIP ==================== -->
  <rect x="50" y="820" width="1500" height="180" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2" />

  <!-- Formula Monospace Chip -->
  <rect x="80" y="845" width="790" height="60" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
  <text x="475" y="885" text-anchor="middle" font-family="monospace" font-size="26" font-weight="bold" fill="#207448">sum by (labels you keep) (rate(counter))</text>

  <!-- Bottom Note (wrapped into tspans) -->
  <text x="475" y="935" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
    <tspan x="475" dy="0">Rate per series, sum by the labels</tspan>
    <tspan x="475" dy="32">you want to keep, then divide.</tspan>
  </text>

  <!-- Divider -->
  <line x1="905" y1="840" x2="905" y2="980" stroke="#207448" stroke-width="1.5" stroke-dasharray="6 4" />

  <!-- Ratio Note Card -->
  <rect x="935" y="845" width="585" height="130" rx="12" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
  <text x="1227" y="888" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="1227" dy="0">Numerator and denominator summed</tspan>
    <tspan x="1227" dy="32">separately, then divided.</tspan>
    <tspan x="1227" dy="32">Never average ratios.</tspan>
  </text>
</svg>'''

with open("test_p2_2025.svg", "w") as f:
    f.write(svg_content)

print("Saved test_p2_2025.svg")
