import xml.etree.ElementTree as ET
import re
import subprocess
import pathlib

svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>How many GPU nodes? Sweep the reservations and reuse a node when one ends</title>
  <desc>SVG infographic explaining GPU node reservation sweeping and node reuse algorithm with timeline visualization, overlap analysis, and min-heap tracking.</desc>

  <!-- Background -->
  <rect width="1600" height="1200" fill="#f5f8f5" />

  <!-- Title -->
  <text x="800" y="52" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">How many GPU nodes? Sweep the reservations</tspan>
    <tspan x="800" dy="54">and reuse a node when one ends</tspan>
  </text>

  <!-- ==================== TOP CONTAINER: TIMELINE & LANES ==================== -->
  <g id="timeline-container">
    <rect x="50" y="135" width="1500" height="325" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2" />

    <!-- Node 1 Header Card -->
    <g id="lane-node-1">
      <rect x="70" y="152" width="230" height="68" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
      <!-- GPU Chip Icon (56x56 outline, green stroke 4) -->
      <g transform="translate(85, 158)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="10" y="10" width="36" height="36" rx="6" />
        <rect x="18" y="18" width="20" height="20" stroke-width="3" />
        <line x1="18" y1="4" x2="18" y2="10" />
        <line x1="28" y1="4" x2="28" y2="10" />
        <line x1="38" y1="4" x2="38" y2="10" />
        <line x1="18" y1="46" x2="18" y2="52" />
        <line x1="28" y1="46" x2="28" y2="52" />
        <line x1="38" y1="46" x2="38" y2="52" />
        <line x1="4" y1="18" x2="10" y2="18" />
        <line x1="4" y1="28" x2="10" y2="28" />
        <line x1="4" y1="38" x2="10" y2="38" />
        <line x1="46" y1="18" x2="52" y2="18" />
        <line x1="46" y1="28" x2="52" y2="28" />
        <line x1="46" y1="38" x2="52" y2="38" />
      </g>
      <text x="155" y="197" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Node 1</text>
    </g>

    <!-- Node 2 Header Card -->
    <g id="lane-node-2">
      <rect x="70" y="290" width="230" height="68" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
      <!-- GPU Chip Icon (56x56 outline, green stroke 4) -->
      <g transform="translate(85, 296)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="10" y="10" width="36" height="36" rx="6" />
        <rect x="18" y="18" width="20" height="20" stroke-width="3" />
        <line x1="18" y1="4" x2="18" y2="10" />
        <line x1="28" y1="4" x2="28" y2="10" />
        <line x1="38" y1="4" x2="38" y2="10" />
        <line x1="18" y1="46" x2="18" y2="52" />
        <line x1="28" y1="46" x2="28" y2="52" />
        <line x1="38" y1="46" x2="38" y2="52" />
        <line x1="4" y1="18" x2="10" y2="18" />
        <line x1="4" y1="28" x2="10" y2="28" />
        <line x1="4" y1="38" x2="10" y2="38" />
        <line x1="46" y1="18" x2="52" y2="18" />
        <line x1="46" y1="28" x2="52" y2="28" />
        <line x1="46" y1="38" x2="52" y2="38" />
      </g>
      <text x="155" y="335" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Node 2</text>
    </g>

    <!-- Lane Dividers / Guideline tracks -->
    <line x1="330" y1="186" x2="1500" y2="186" stroke="#e8f1ea" stroke-width="38" stroke-linecap="round" />
    <line x1="330" y1="324" x2="1500" y2="324" stroke="#e8f1ea" stroke-width="38" stroke-linecap="round" />

    <!-- Shaded Overlap Band (Hours 2 to 4: x=564 to x=798) -->
    <rect x="564" y="148" width="234" height="214" rx="8" fill="#fef6ed" stroke="#db8129" stroke-width="2.5" stroke-dasharray="6 4" />

    <!-- Three Bars -->
    <!-- Bar A '(0, 4)' on Node 1 (Hours 0 to 4: x=330 to x=798) -->
    <g id="bar-a">
      <rect x="330" y="164" width="468" height="44" rx="8" fill="#207448" />
      <text x="564" y="196" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">(0, 4)</text>
    </g>

    <!-- Bar B '(2, 6)' on Node 2 (Hours 2 to 6: x=564 to x=1032) -->
    <g id="bar-b">
      <rect x="564" y="302" width="468" height="44" rx="8" fill="#207448" />
      <text x="798" y="334" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">(2, 6)</text>
    </g>

    <!-- Bar C '(8, 10)' on Node 1 (Hours 8 to 10: x=1266 to x=1500) -->
    <g id="bar-c">
      <rect x="1266" y="164" width="234" height="44" rx="8" fill="#207448" />
      <text x="1383" y="196" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">(8, 10)</text>
    </g>

    <!-- Overlap Callout Box & Label (The single orange item) -->
    <g id="overlap-label-card">
      <rect x="361" y="223" width="640" height="64" rx="8" fill="#ffffff" stroke="#db8129" stroke-width="2.5" />
      <text x="681" y="249" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#db8129">
        <tspan x="681" dy="0">A and B overlap,</tspan>
        <tspan x="681" dy="28">they need separate nodes</tspan>
      </text>
    </g>

    <!-- Timeline Horizontal Axis Line -->
    <line x1="330" y1="375" x2="1500" y2="375" stroke="#303a36" stroke-width="3" />

    <!-- Timeline Tick Marks and Hour Labels (0 to 10) -->
    <!-- Tick 0 -->
    <line x1="330" y1="365" x2="330" y2="379" stroke="#303a36" stroke-width="3" />
    <text x="330" y="410" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">0</text>
    <!-- Tick 1 -->
    <line x1="447" y1="365" x2="447" y2="379" stroke="#303a36" stroke-width="3" />
    <text x="447" y="410" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">1</text>
    <!-- Tick 2 -->
    <line x1="564" y1="365" x2="564" y2="379" stroke="#303a36" stroke-width="3" />
    <text x="564" y="410" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">2</text>
    <!-- Tick 3 -->
    <line x1="681" y1="365" x2="681" y2="379" stroke="#303a36" stroke-width="3" />
    <text x="681" y="410" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">3</text>
    <!-- Tick 4 -->
    <line x1="798" y1="365" x2="798" y2="379" stroke="#303a36" stroke-width="3" />
    <text x="798" y="410" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">4</text>
    <!-- Tick 5 -->
    <line x1="915" y1="365" x2="915" y2="379" stroke="#303a36" stroke-width="3" />
    <text x="915" y="410" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">5</text>
    <!-- Tick 6 -->
    <line x1="1032" y1="365" x2="1032" y2="379" stroke="#303a36" stroke-width="3" />
    <text x="1032" y="410" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">6</text>
    <!-- Tick 7 -->
    <line x1="1149" y1="365" x2="1149" y2="379" stroke="#303a36" stroke-width="3" />
    <text x="1149" y="410" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">7</text>
    <!-- Tick 8 -->
    <line x1="1266" y1="365" x2="1266" y2="379" stroke="#303a36" stroke-width="3" />
    <text x="1266" y="410" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">8</text>
    <!-- Tick 9 -->
    <line x1="1383" y1="365" x2="1383" y2="379" stroke="#303a36" stroke-width="3" />
    <text x="1383" y="410" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">9</text>
    <!-- Tick 10 -->
    <line x1="1500" y1="365" x2="1500" y2="379" stroke="#303a36" stroke-width="3" />
    <text x="1500" y="410" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">10</text>
  </g>

  <!-- ==================== LEFT COLUMN: ALGORITHM WALKTHROUGH ==================== -->
  <!-- Step 1 -->
  <g id="step-1">
    <rect x="50" y="485" width="880" height="105" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <g transform="translate(72, 510)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <line x1="8" y1="14" x2="32" y2="14" />
      <line x1="8" y1="28" x2="24" y2="28" />
      <line x1="8" y1="42" x2="18" y2="42" />
      <polyline points="38,24 46,32 38,40" />
      <line x1="46" y1="32" x2="46" y2="10" />
    </g>
    <text x="145" y="546" font-family="ui-monospace, monospace" font-size="25" font-weight="bold" fill="#303a36">1 Sort by start: (0, 4), (2, 6), (8, 10)</text>
  </g>

  <!-- Step 2 -->
  <g id="step-2">
    <rect x="50" y="608" width="880" height="105" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <g transform="translate(72, 633)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="8" y="10" width="40" height="36" rx="6" />
      <line x1="8" y1="24" x2="48" y2="24" />
      <circle cx="18" cy="17" r="2" fill="#207448" />
      <circle cx="26" cy="17" r="2" fill="#207448" />
      <polyline points="22,38 28,44 40,32" stroke-width="3" />
    </g>
    <text x="145" y="654" font-family="ui-monospace, monospace" font-size="24" fill="#303a36">
      <tspan x="145" dy="0" font-weight="bold">2 (0, 4):</tspan>
      <tspan dy="0"> no node in use, open node,</tspan>
      <tspan x="145" dy="34">heap of end times = 4</tspan>
    </text>
  </g>

  <!-- Step 3 -->
  <g id="step-3">
    <rect x="50" y="731" width="880" height="105" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <g transform="translate(72, 756)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="8" width="34" height="28" rx="4" />
      <rect x="16" y="20" width="34" height="28" rx="4" />
      <line x1="28" y1="34" x2="38" y2="34" />
      <line x1="33" y1="29" x2="33" y2="39" />
    </g>
    <text x="145" y="777" font-family="ui-monospace, monospace" font-size="24" fill="#303a36">
      <tspan x="145" dy="0" font-weight="bold">3 (2, 6):</tspan>
      <tspan dy="0"> earliest end 4 is after start 2,</tspan>
      <tspan x="145" dy="34">open a second node, heap = 4, 6</tspan>
    </text>
  </g>

  <!-- Step 4 -->
  <g id="step-4">
    <rect x="50" y="854" width="880" height="105" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <g transform="translate(72, 879)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 44 22 A 16 16 0 1 0 46 32" />
      <polyline points="46,18 46,26 38,26" />
      <circle cx="28" cy="28" r="6" />
    </g>
    <text x="145" y="900" font-family="ui-monospace, monospace" font-size="24" fill="#303a36">
      <tspan x="145" dy="0" font-weight="bold">4 (8, 10):</tspan>
      <tspan dy="0"> earliest end 4 is at or before start 8,</tspan>
      <tspan x="145" dy="34">reuse that node, heap = 6, 10</tspan>
    </text>
  </g>

  <!-- Step 5 -->
  <g id="step-5">
    <rect x="50" y="977" width="880" height="105" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <g transform="translate(72, 1002)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="20" />
      <polyline points="18,28 25,35 38,20" stroke-width="4" />
    </g>
    <text x="145" y="1023" font-family="ui-monospace, monospace" font-size="24" fill="#303a36">
      <tspan x="145" dy="0" font-weight="bold">5 Answer:</tspan>
      <tspan dy="0"> the heap holds 2 end times,</tspan>
      <tspan x="145" dy="34">so 2 nodes</tspan>
    </text>
  </g>

  <!-- ==================== RIGHT COLUMN: SIDE NOTE & ALTERNATE METHOD ==================== -->
  <!-- Side Note Box -->
  <g id="box-side-note">
    <rect x="970" y="485" width="580" height="260" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <!-- Clock / Timer Icon (56x56 outline, green stroke 4) -->
    <g transform="translate(1000, 505)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="22" />
      <polyline points="28,14 28,28 40,28" />
      <line x1="28" y1="2" x2="28" y2="6" />
      <line x1="28" y1="50" x2="28" y2="54" />
      <line x1="2" y1="28" x2="6" y2="28" />
      <line x1="50" y1="28" x2="54" y2="28" />
    </g>
    <text x="1000" y="605" font-family="sans-serif" font-size="25" fill="#303a36">
      <tspan x="1000" dy="0" font-weight="bold">Half-open [start, end):</tspan>
      <tspan x="1000" dy="38">a job ending at 10 frees its node</tspan>
      <tspan x="1000" dy="38">for one starting at 10</tspan>
    </text>
  </g>

  <!-- Alternate Method Box -->
  <g id="box-alternate-method">
    <rect x="970" y="770" width="580" height="312" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <!-- Event Sweep / Lightning Icon (56x56 outline, green stroke 4) -->
    <g transform="translate(1000, 792)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <polyline points="32,6 12,30 26,30 20,50 44,24 30,24 36,6" stroke-linejoin="miter" />
    </g>
    <text x="1000" y="888" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1000" dy="0" font-weight="bold">Event sweep: +1 at each start,</tspan>
      <tspan x="1000" dy="35">-1 at each end, at equal times</tspan>
      <tspan x="1000" dy="35">the end sorts before the start,</tspan>
      <tspan x="1000" dy="35">the maximum running total</tspan>
      <tspan x="1000" dy="35">is the answer</tspan>
    </text>
  </g>

  <!-- ==================== TAKEAWAY BAR ==================== -->
  <g id="takeaway-bar">
    <rect x="50" y="1115" width="1500" height="65" rx="12" fill="#207448" />
    <text x="800" y="1156" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">First ask whether reservations are per node or pooled, because that changes the whole model.</text>
  </g>
</svg>'''

with open("test_gpu_sweep.svg", "w") as f:
    f.write(svg)

print("SVG written to test_gpu_sweep.svg")
