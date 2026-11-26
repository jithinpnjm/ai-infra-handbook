import re
import xml.etree.ElementTree as ET
import subprocess
import pathlib

svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1140" width="1600" height="1140">
  <title>Pipelining: 104 cycles instead of 500</title>
  <desc>Visual comparison between sequential execution without a pipeline requiring 500 cycles and overlapped pipelined execution requiring 104 cycles across five conveyor stages.</desc>

  <!-- Background -->
  <rect width="100%" height="100%" fill="#f5f8f5"/>

  <!-- Title (48px bold) -->
  <text x="800" y="58" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Pipelining: 104 cycles instead of 500</text>

  <!-- Formula line above the lanes -->
  <rect x="490" y="100" width="620" height="46" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
  <text x="800" y="132" text-anchor="middle" font-family="monospace" font-size="26" font-weight="bold" fill="#207448">Total cycles = K * (N - 1) + S</text>

  <!-- ==================== TOP LANE: WITHOUT A PIPELINE ==================== -->
  <g id="top-lane">
    <!-- Container -->
    <rect x="50" y="186" width="1500" height="376" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>

    <!-- Lane Icon (Sequential Conveyor: single item on line, 56px, stroke 4, #207448) -->
    <g transform="translate(75, 204)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="8" width="48" height="28" rx="6" fill="#ffffff"/>
      <line x1="4" y1="22" x2="52" y2="22"/>
      <circle cx="16" cy="38" r="4" fill="#207448"/>
      <circle cx="40" cy="38" r="4" fill="#207448"/>
      <rect x="18" y="12" width="16" height="10" rx="2" fill="#207448"/>
    </g>

    <!-- Top Lane Title (32px bold) -->
    <text x="145" y="234" font-family="sans-serif" font-size="32" font-weight="bold" fill="#207448">Without a pipeline</text>

    <!-- Stage 1 Box -->
    <rect x="75" y="258" width="265" height="130" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <circle cx="115" cy="290" r="22" fill="#207448"/>
    <text x="115" y="298" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">1</text>
    <!-- Stage 1 Icon: memory chip -->
    <g transform="translate(265, 272)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round">
      <rect x="4" y="6" width="28" height="24" rx="3" fill="#e8f1ea"/>
      <line x1="10" y1="2" x2="10" y2="6"/>
      <line x1="18" y1="2" x2="18" y2="6"/>
      <line x1="26" y1="2" x2="26" y2="6"/>
      <line x1="10" y1="30" x2="10" y2="34"/>
      <line x1="18" y1="30" x2="18" y2="34"/>
      <line x1="26" y1="30" x2="26" y2="34"/>
    </g>
    <text x="207" y="342" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
      <tspan x="207" dy="0">load from</tspan>
      <tspan x="207" dy="28">memory</tspan>
    </text>

    <!-- Stage 2 Box -->
    <rect x="371" y="258" width="265" height="130" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <circle cx="411" cy="290" r="22" fill="#207448"/>
    <text x="411" y="298" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">2</text>
    <!-- Stage 2 Icon: sliders / align -->
    <g transform="translate(561, 272)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round">
      <line x1="6" y1="10" x2="30" y2="10"/>
      <line x1="6" y1="18" x2="30" y2="18"/>
      <line x1="6" y1="26" x2="30" y2="26"/>
      <circle cx="14" cy="10" r="3" fill="#207448"/>
      <circle cx="24" cy="18" r="3" fill="#207448"/>
      <circle cx="16" cy="26" r="3" fill="#207448"/>
    </g>
    <text x="503" y="342" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
      <tspan x="503" dy="0">normalize</tspan>
      <tspan x="503" dy="28">mantissas</tspan>
    </text>

    <!-- Stage 3 Box -->
    <rect x="667" y="258" width="265" height="130" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <circle cx="707" cy="290" r="22" fill="#207448"/>
    <text x="707" y="298" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">3</text>
    <!-- Stage 3 Icon: math adder plus -->
    <g transform="translate(857, 272)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round">
      <circle cx="18" cy="18" r="14" fill="#e8f1ea"/>
      <line x1="18" y1="11" x2="18" y2="25"/>
      <line x1="11" y1="18" x2="25" y2="18"/>
    </g>
    <text x="799" y="356" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">add</text>

    <!-- Stage 4 Box -->
    <rect x="963" y="258" width="265" height="130" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <circle cx="1003" cy="290" r="22" fill="#207448"/>
    <text x="1003" y="298" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">4</text>
    <!-- Stage 4 Icon: checkmark / precision shield -->
    <g transform="translate(1153, 272)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 6 8 L 18 4 L 30 8 V 18 C 30 26 18 32 18 32 C 18 32 6 26 6 18 Z" fill="#e8f1ea"/>
      <polyline points="12,17 16,21 24,13"/>
    </g>
    <text x="1095" y="356" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">correct</text>

    <!-- Stage 5 Box -->
    <rect x="1259" y="258" width="265" height="130" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <circle cx="1299" cy="290" r="22" fill="#207448"/>
    <text x="1299" y="298" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">5</text>
    <!-- Stage 5 Icon: write back to storage -->
    <g transform="translate(1449, 272)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="6" width="24" height="24" rx="3" fill="#e8f1ea"/>
      <line x1="12" y1="12" x2="24" y2="12"/>
      <line x1="12" y1="18" x2="24" y2="18"/>
      <line x1="12" y1="24" x2="18" y2="24"/>
    </g>
    <text x="1391" y="342" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
      <tspan x="1391" dy="0">write result</tspan>
      <tspan x="1391" dy="28">back</tspan>
    </text>

    <!-- Top Conveyor Track & Single Active Element Movement -->
    <g transform="translate(75, 408)">
      <!-- Conveyor track -->
      <line x1="0" y1="20" x2="1449" y2="20" stroke="#207448" stroke-width="3" stroke-dasharray="8 6"/>
      <!-- Stages 1 to 4 idle indicator marks -->
      <rect x="112" y="6" width="40" height="28" rx="4" fill="#ffffff" stroke="#207448" stroke-width="1.5" stroke-dasharray="4 3"/>
      <rect x="408" y="6" width="40" height="28" rx="4" fill="#ffffff" stroke="#207448" stroke-width="1.5" stroke-dasharray="4 3"/>
      <rect x="704" y="6" width="40" height="28" rx="4" fill="#ffffff" stroke="#207448" stroke-width="1.5" stroke-dasharray="4 3"/>
      <rect x="1000" y="6" width="40" height="28" rx="4" fill="#ffffff" stroke="#207448" stroke-width="1.5" stroke-dasharray="4 3"/>
      <!-- Active element 1 in stage 5 -->
      <rect x="1296" y="4" width="52" height="32" rx="6" fill="#207448" stroke="#175333" stroke-width="2"/>
      <!-- Waiting element 2 outside stage 1 (waiting line) -->
      <line x1="-15" y1="-4" x2="-15" y2="44" stroke="#207448" stroke-width="2"/>
      <rect x="-65" y="4" width="40" height="32" rx="6" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    </g>

    <!-- Label Under Top Lane -->
    <rect x="440" y="482" width="720" height="52" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <text x="800" y="516" text-anchor="middle" font-family="sans-serif" font-size="25" font-weight="bold" fill="#207448">500 cycles for N = 100 elements with S = 5</text>
  </g>

  <!-- ==================== BOTTOM LANE: WITH A PIPELINE ==================== -->
  <g id="bottom-lane">
    <!-- Container -->
    <rect x="50" y="602" width="1500" height="398" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>

    <!-- Lane Icon (Pipelined Conveyor: overlapping items, 56px, stroke 4, #207448) -->
    <g transform="translate(75, 620)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="8" width="48" height="28" rx="6" fill="#ffffff"/>
      <line x1="4" y1="22" x2="52" y2="22"/>
      <circle cx="16" cy="38" r="4" fill="#207448"/>
      <circle cx="40" cy="38" r="4" fill="#207448"/>
      <rect x="8" y="12" width="10" height="10" rx="2" fill="#207448"/>
      <rect x="23" y="12" width="10" height="10" rx="2" fill="#207448"/>
      <rect x="38" y="12" width="10" height="10" rx="2" fill="#207448"/>
    </g>

    <!-- Bottom Lane Title (32px bold) -->
    <text x="145" y="650" font-family="sans-serif" font-size="32" font-weight="bold" fill="#207448">With a pipeline</text>

    <!-- Pipelined Stages & Staircase Grid -->
    <!-- Row 1: First element full pass (ORANGE HIGHLIGHT: S cycles pipeline fill time) -->
    <rect x="75" y="674" width="1449" height="72" rx="10" fill="#fffaf5" stroke="#db8129" stroke-width="2.5"/>
    <text x="800" y="700" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#db8129">pipeline fill time (S cycles)</text>
    <!-- Five green blocks for element 1 traversing stages 1 to 5 -->
    <rect x="181" y="708" width="52" height="28" rx="6" fill="#207448"/>
    <rect x="477" y="708" width="52" height="28" rx="6" fill="#207448"/>
    <rect x="773" y="708" width="52" height="28" rx="6" fill="#207448"/>
    <rect x="1069" y="708" width="52" height="28" rx="6" fill="#207448"/>
    <rect x="1365" y="708" width="52" height="28" rx="6" fill="#207448"/>

    <!-- Row 2: Element 2 enters one stage behind (stages 1 to 4) -->
    <rect x="181" y="756" width="52" height="28" rx="6" fill="#207448"/>
    <rect x="477" y="756" width="52" height="28" rx="6" fill="#207448"/>
    <rect x="773" y="756" width="52" height="28" rx="6" fill="#207448"/>
    <rect x="1069" y="756" width="52" height="28" rx="6" fill="#207448"/>

    <!-- Row 3: Element 3 enters one stage behind (stages 1 to 3) -->
    <rect x="181" y="794" width="52" height="28" rx="6" fill="#207448"/>
    <rect x="477" y="794" width="52" height="28" rx="6" fill="#207448"/>
    <rect x="773" y="794" width="52" height="28" rx="6" fill="#207448"/>

    <!-- Row 4: Element 4 enters one stage behind (stages 1 to 2) -->
    <rect x="181" y="832" width="52" height="28" rx="6" fill="#207448"/>
    <rect x="477" y="832" width="52" height="28" rx="6" fill="#207448"/>

    <!-- Row 5: Element 5 enters one stage behind (stage 1) -->
    <rect x="181" y="870" width="52" height="28" rx="6" fill="#207448"/>

    <!-- Label Under Bottom Lane -->
    <rect x="360" y="918" width="880" height="52" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <text x="800" y="952" text-anchor="middle" font-family="sans-serif" font-size="25" font-weight="bold" fill="#207448">104 cycles = K x (N - 1) + S, with K = 1, N = 100, S = 5</text>
  </g>

  <!-- ==================== PLAIN NOTE AT THE BOTTOM ==================== -->
  <rect x="420" y="1040" width="760" height="48" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
  <text x="800" y="1072" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">pipelining is a different idea from vectorization</text>
</svg>'''

with open("candidate.svg", "w") as f:
    f.write(svg_content)

print("Wrote candidate.svg")
