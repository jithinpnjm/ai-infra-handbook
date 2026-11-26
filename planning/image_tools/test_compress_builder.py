import xml.etree.ElementTree as ET
import re, subprocess, pathlib

# Let's draft the complete SVG
H = 1080

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 {H}" width="1600" height="{H}">
  <title>Tracing compress on aaa: one variable state per step</title>
  <desc>Trace the example by hand, one line of state per step</desc>

  <defs>
    <!-- Table / Window Icon (56x56) -->
    <g id="icon-table" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="6" width="48" height="44" rx="6" fill="#e8f1ea"/>
      <line x1="4" y1="20" x2="52" y2="20"/>
      <line x1="20" y1="20" x2="20" y2="50"/>
      <line x1="36" y1="20" x2="36" y2="50"/>
      <circle cx="10" cy="13" r="2" fill="#207448"/>
      <circle cx="16" cy="13" r="2" fill="#207448"/>
    </g>

    <!-- Code / Document Icon (56x56) -->
    <g id="icon-code" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="4" width="44" height="48" rx="6" fill="#e8f1ea"/>
      <polyline points="18,22 12,28 18,34"/>
      <polyline points="38,22 44,28 38,34"/>
      <line x1="30" y1="18" x2="26" y2="38"/>
    </g>
  </defs>

  <!-- Background -->
  <rect width="100%" height="100%" fill="#f5f8f5"/>

  <!-- Title (48px bold) -->
  <text x="800" y="62" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Trace the example by hand, one line of state per step.</text>

  <!-- ==================== TABLE GRID ==================== -->
  <g id="table-grid">
    <!-- Outer Table Card Header -->
    <rect x="40" y="105" width="1520" height="58" rx="10" fill="#207448"/>
    
    <!-- Table Header Columns -->
    <!-- Col 1: step (x: 40 to 420, width 380) -->
    <text x="230" y="144" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">step</text>
    
    <!-- Col 2: ch read (x: 420 to 650, width 230) -->
    <line x1="420" y1="105" x2="420" y2="163" stroke="#ffffff" stroke-width="2" stroke-opacity="0.3"/>
    <text x="535" y="144" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">ch read</text>
    
    <!-- Col 3: run_char (x: 650 to 880, width 230) -->
    <line x1="650" y1="105" x2="650" y2="163" stroke="#ffffff" stroke-width="2" stroke-opacity="0.3"/>
    <text x="765" y="144" text-anchor="middle" font-family="monospace" font-size="28" font-weight="bold" fill="#ffffff">run_char</text>
    
    <!-- Col 4: run_len (x: 880 to 1110, width 230) -->
    <line x1="880" y1="105" x2="880" y2="163" stroke="#ffffff" stroke-width="2" stroke-opacity="0.3"/>
    <text x="995" y="144" text-anchor="middle" font-family="monospace" font-size="28" font-weight="bold" fill="#ffffff">run_len</text>
    
    <!-- Col 5: parts (x: 1110 to 1560, width 450) -->
    <line x1="1110" y1="105" x2="1110" y2="163" stroke="#ffffff" stroke-width="2" stroke-opacity="0.3"/>
    <text x="1335" y="144" text-anchor="middle" font-family="monospace" font-size="28" font-weight="bold" fill="#ffffff">parts</text>

    <!-- ==================== ROW 1: start ==================== -->
    <rect x="40" y="168" width="1520" height="95" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <line x1="420" y1="168" x2="420" y2="263" stroke="#207448" stroke-width="1.5" stroke-opacity="0.2"/>
    <line x1="650" y1="168" x2="650" y2="263" stroke="#207448" stroke-width="1.5" stroke-opacity="0.2"/>
    <line x1="880" y1="168" x2="880" y2="263" stroke="#207448" stroke-width="1.5" stroke-opacity="0.2"/>
    <line x1="1110" y1="168" x2="1110" y2="263" stroke="#207448" stroke-width="1.5" stroke-opacity="0.2"/>

    <!-- Row 1: Col 1 -->
    <circle cx="80" cy="215" r="24" fill="#207448"/>
    <text x="80" y="224" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">1</text>
    <text x="125" y="224" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">start</text>

    <!-- Row 1: Col 2 (empty at start) -->

    <!-- Row 1: Col 3 -->
    <text x="765" y="225" text-anchor="middle" font-family="monospace" font-size="32" font-weight="bold" fill="#303a36">a</text>

    <!-- Row 1: Col 4 -->
    <text x="995" y="225" text-anchor="middle" font-family="monospace" font-size="32" font-weight="bold" fill="#303a36">1</text>

    <!-- Row 1: Col 5 -->
    <text x="1335" y="225" text-anchor="middle" font-family="monospace" font-size="28" font-weight="bold" fill="#303a36">empty</text>

    <!-- ==================== ROW 2: step 1 ==================== -->
    <rect x="40" y="268" width="1520" height="95" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <line x1="420" y1="268" x2="420" y2="363" stroke="#207448" stroke-width="1.5" stroke-opacity="0.2"/>
    <line x1="650" y1="268" x2="650" y2="363" stroke="#207448" stroke-width="1.5" stroke-opacity="0.2"/>
    <line x1="880" y1="268" x2="880" y2="363" stroke="#207448" stroke-width="1.5" stroke-opacity="0.2"/>
    <line x1="1110" y1="268" x2="1110" y2="363" stroke="#207448" stroke-width="1.5" stroke-opacity="0.2"/>

    <!-- Row 2: Col 1 -->
    <circle cx="80" cy="315" r="24" fill="#207448"/>
    <text x="80" y="324" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">2</text>
    <text x="125" y="304" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">step 1</text>
    <text x="125" y="336" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">first repeat</text>

    <!-- Row 2: Col 2 -->
    <text x="535" y="304" text-anchor="middle" font-family="monospace" font-size="32" font-weight="bold" fill="#303a36">a</text>
    <text x="535" y="336" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#207448">equal</text>

    <!-- Row 2: Col 3 -->
    <text x="765" y="315" text-anchor="middle" font-family="monospace" font-size="32" font-weight="bold" fill="#303a36">a</text>

    <!-- Row 2: Col 4 -->
    <text x="995" y="315" text-anchor="middle" font-family="monospace" font-size="32" font-weight="bold" fill="#207448">2</text>

    <!-- Row 2: Col 5 -->
    <text x="1335" y="315" text-anchor="middle" font-family="monospace" font-size="28" font-weight="bold" fill="#303a36">empty</text>

    <!-- ==================== ROW 3: step 2 ==================== -->
    <rect x="40" y="368" width="1520" height="95" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <line x1="420" y1="368" x2="420" y2="463" stroke="#207448" stroke-width="1.5" stroke-opacity="0.2"/>
    <line x1="650" y1="368" x2="650" y2="463" stroke="#207448" stroke-width="1.5" stroke-opacity="0.2"/>
    <line x1="880" y1="368" x2="880" y2="463" stroke="#207448" stroke-width="1.5" stroke-opacity="0.2"/>
    <line x1="1110" y1="368" x2="1110" y2="463" stroke="#207448" stroke-width="1.5" stroke-opacity="0.2"/>

    <!-- Row 3: Col 1 -->
    <circle cx="80" cy="415" r="24" fill="#207448"/>
    <text x="80" y="424" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">3</text>
    <text x="125" y="404" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">step 2</text>
    <text x="125" y="436" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">second repeat</text>

    <!-- Row 3: Col 2 -->
    <text x="535" y="404" text-anchor="middle" font-family="monospace" font-size="32" font-weight="bold" fill="#303a36">a</text>
    <text x="535" y="436" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#207448">equal</text>

    <!-- Row 3: Col 3 -->
    <text x="765" y="415" text-anchor="middle" font-family="monospace" font-size="32" font-weight="bold" fill="#303a36">a</text>

    <!-- Row 3: Col 4 -->
    <text x="995" y="415" text-anchor="middle" font-family="monospace" font-size="32" font-weight="bold" fill="#207448">3</text>

    <!-- Row 3: Col 5 -->
    <text x="1335" y="415" text-anchor="middle" font-family="monospace" font-size="28" font-weight="bold" fill="#303a36">empty</text>

    <!-- ==================== ROW 4: after the loop ==================== -->
    <rect x="40" y="468" width="1520" height="95" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <line x1="420" y1="468" x2="420" y2="563" stroke="#207448" stroke-width="1.5" stroke-opacity="0.2"/>
    <line x1="650" y1="468" x2="650" y2="563" stroke="#207448" stroke-width="1.5" stroke-opacity="0.2"/>
    <line x1="880" y1="468" x2="880" y2="563" stroke="#207448" stroke-width="1.5" stroke-opacity="0.2"/>
    <line x1="1110" y1="468" x2="1110" y2="563" stroke="#207448" stroke-width="1.5" stroke-opacity="0.2"/>

    <!-- Row 4: Col 1 -->
    <circle cx="80" cy="515" r="24" fill="#207448"/>
    <text x="80" y="524" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">4</text>
    <text x="125" y="504" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">after the loop</text>
    <text x="125" y="536" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">close the last run</text>

    <!-- Row 4: Col 2 (empty) -->

    <!-- Row 4: Col 3 -->
    <text x="765" y="515" text-anchor="middle" font-family="monospace" font-size="32" font-weight="bold" fill="#303a36">a</text>

    <!-- Row 4: Col 4 -->
    <text x="995" y="515" text-anchor="middle" font-family="monospace" font-size="32" font-weight="bold" fill="#303a36">3</text>

    <!-- Row 4: Col 5 -->
    <text x="1335" y="504" text-anchor="middle" font-family="monospace" font-size="32" font-weight="bold" fill="#207448">a3</text>
    <text x="1335" y="536" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">the last run is appended</text>

    <!-- ==================== ROW 5: final result row ==================== -->
    <rect x="40" y="568" width="1520" height="95" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
    <line x1="420" y1="568" x2="420" y2="663" stroke="#207448" stroke-width="2"/>

    <!-- Row 5: Col 1 -->
    <circle cx="80" cy="615" r="24" fill="#207448"/>
    <text x="80" y="624" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">5</text>
    <text x="125" y="624" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">compare lengths</text>

    <!-- Row 5: Col 2-5 spanning result with green check -->
    <g transform="translate(450, 593)">
      <circle cx="22" cy="22" r="22" fill="#207448"/>
      <polyline points="12,22 19,29 32,14" fill="none" stroke="#ffffff" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
    </g>

    <text x="515" y="624" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">
      <tspan>packed is </tspan>
      <tspan font-family="monospace" fill="#207448">a3</tspan>
      <tspan>, length 2 is less than length 3 of </tspan>
      <tspan font-family="monospace" fill="#207448">aaa</tspan>
      <tspan>, so return </tspan>
      <tspan font-family="monospace" fill="#207448">a3</tspan>
    </text>
  </g>

  <!-- ==================== STRIP FOR aa ==================== -->
  <g id="strip-aa">
    <rect x="40" y="705" width="1520" height="195" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2"/>

    <!-- Outline Code Icon -->
    <use href="#icon-code" x="65" y="720"/>

    <!-- aa badge -->
    <rect x="140" y="722" width="90" height="52" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
    <text x="185" y="758" text-anchor="middle" font-family="monospace" font-size="30" font-weight="bold" fill="#207448">aa</text>

    <!-- aa comparison sentence -->
    <text x="255" y="758" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36">
      <tspan>packed </tspan>
      <tspan font-family="monospace" fill="#207448">a2</tspan>
      <tspan> has length 2, not less than 2, so return </tspan>
      <tspan font-family="monospace" fill="#207448">aa</tspan>
    </text>

    <!-- Single Orange Callout -->
    <rect x="65" y="805" width="1470" height="70" rx="10" fill="#fffaf5" stroke="#db8129" stroke-width="3"/>
    <text x="800" y="848" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#db8129">this is why the comparison is less than and not less than or equal</text>
  </g>

  <!-- ==================== TAKEAWAY BAR ==================== -->
  <rect x="40" y="940" width="1520" height="75" rx="12" fill="#207448"/>
  <text x="800" y="987" text-anchor="middle" font-family="sans-serif" font-size="25" font-weight="bold" fill="#ffffff">The line after the loop closes the last run, and the final comparison keeps the result from growing.</text>
</svg>'''

p = pathlib.Path('test_compress_candidate.svg')
p.write_text(svg)
print("Wrote test_compress_candidate.svg")
