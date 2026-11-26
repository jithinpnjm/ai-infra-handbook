import xml.etree.ElementTree as ET
import re

svg_code = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1080" width="1600" height="1080">
  <title>Deleted but open: the name is gone, the blocks stay until the descriptor closes</title>
  <desc>Visual explanation of deleted open files and rescue procedure.</desc>
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#207448" />
    </marker>
  </defs>
  <rect x="0" y="0" width="1600" height="1080" fill="#f5f8f5" />

  <!-- Title -->
  <text x="800" y="58" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">Deleted but open: the name is gone, </tspan>
    <tspan x="800" dy="54">the blocks stay until the descriptor closes</tspan>
  </text>

  <!-- Step 1 Box -->
  <rect x="40" y="150" width="350" height="420" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
  <circle cx="86" cy="196" r="24" fill="#207448" />
  <text x="86" y="205" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">1</text>
  
  <!-- Icon 1: Log file -->
  <g transform="translate(310, 168)">
    <path d="M 6 0 L 32 0 L 46 14 L 46 54 L 6 54 Z" fill="#ffffff" stroke="#207448" stroke-width="3" stroke-linejoin="round" />
    <path d="M 32 0 L 32 14 L 46 14" fill="none" stroke="#207448" stroke-width="3" stroke-linejoin="round" />
    <line x1="14" y1="22" x2="38" y2="22" stroke="#207448" stroke-width="2.5" stroke-linecap="round" />
    <line x1="14" y1="32" x2="38" y2="32" stroke="#207448" stroke-width="2.5" stroke-linecap="round" />
    <line x1="14" y1="42" x2="28" y2="42" stroke="#207448" stroke-width="2.5" stroke-linecap="round" />
  </g>
  <line x1="60" y1="240" x2="370" y2="240" stroke="#207448" stroke-width="1.5" opacity="0.3" />

  <text x="215" y="330" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="215" dy="0">a process opens </tspan>
    <tspan x="215" dy="36">app.log and writes </tspan>
    <tspan x="215" dy="36">20 MB</tspan>
  </text>

  <!-- Arrow 1 to 2 -->
  <line x1="390" y1="360" x2="430" y2="360" stroke="#207448" stroke-width="3" marker-end="url(#arrow)" />

  <!-- Step 2 Box -->
  <rect x="430" y="150" width="350" height="420" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
  <circle cx="476" cy="196" r="24" fill="#207448" />
  <text x="476" y="205" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">2</text>

  <!-- Icon 2: Trash can -->
  <g transform="translate(700, 168)">
    <line x1="6" y1="14" x2="48" y2="14" stroke="#207448" stroke-width="3" stroke-linecap="round" />
    <path d="M 21 14 L 21 8 L 33 8 L 33 14" fill="none" stroke="#207448" stroke-width="3" stroke-linejoin="round" />
    <path d="M 12 14 L 16 52 L 38 52 L 42 14" fill="#ffffff" stroke="#207448" stroke-width="3" stroke-linejoin="round" />
    <line x1="21" y1="22" x2="22" y2="44" stroke="#207448" stroke-width="2.5" stroke-linecap="round" />
    <line x1="27" y1="22" x2="27" y2="44" stroke="#207448" stroke-width="2.5" stroke-linecap="round" />
    <line x1="33" y1="22" x2="32" y2="44" stroke="#207448" stroke-width="2.5" stroke-linecap="round" />
  </g>
  <line x1="450" y1="240" x2="760" y2="240" stroke="#207448" stroke-width="1.5" opacity="0.3" />

  <text x="605" y="300" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">rm removes the name</text>

  <text x="605" y="365" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">link count 0</text>

  <text x="605" y="440" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="605" dy="0">ls and du no longer </tspan>
    <tspan x="605" dy="36">see the file</tspan>
  </text>

  <!-- Arrow 2 to 3 -->
  <line x1="780" y1="360" x2="820" y2="360" stroke="#207448" stroke-width="3" marker-end="url(#arrow)" />

  <!-- Step 3 Box (Orange Highlight) -->
  <rect x="820" y="150" width="350" height="420" rx="14" fill="#fff8f2" stroke="#db8129" stroke-width="3" />
  <circle cx="866" cy="196" r="24" fill="#207448" />
  <text x="866" y="205" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">3</text>

  <!-- Icon 3: Descriptor slot -->
  <g transform="translate(1090, 168)">
    <rect x="2" y="10" width="50" height="36" rx="6" fill="#ffffff" stroke="#db8129" stroke-width="3" />
    <line x1="18" y1="10" x2="18" y2="46" stroke="#db8129" stroke-width="2.5" />
    <line x1="34" y1="10" x2="34" y2="46" stroke="#db8129" stroke-width="2.5" />
    <path d="M 23 28 L 44 28 M 38 22 L 44 28 L 38 34" fill="none" stroke="#db8129" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
  </g>
  <line x1="840" y1="240" x2="1150" y2="240" stroke="#db8129" stroke-width="1.5" opacity="0.3" />

  <text x="995" y="290" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="995" dy="0">the process </tspan>
    <tspan x="995" dy="30">still holds the </tspan>
    <tspan x="995" dy="30">descriptor, so df </tspan>
    <tspan x="995" dy="30">still counts </tspan>
    <tspan x="995" dy="30">the blocks</tspan>
  </text>

  <text x="995" y="495" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#db8129"><tspan x="995" dy="0">/tmp/.../</tspan><tspan x="995" dy="30">app.log (deleted)</tspan></text>

  <!-- Arrow 3 to 4 -->
  <line x1="1170" y1="360" x2="1210" y2="360" stroke="#207448" stroke-width="3" marker-end="url(#arrow)" />

  <!-- Step 4 Box -->
  <rect x="1210" y="150" width="350" height="420" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
  <circle cx="1256" cy="196" r="24" fill="#207448" />
  <text x="1256" y="205" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">4</text>

  <!-- Icon 4: Broom -->
  <g transform="translate(1480, 168)">
    <line x1="44" y1="4" x2="25" y2="30" stroke="#207448" stroke-width="4.5" stroke-linecap="round" />
    <path d="M 12 34 L 6 52 L 36 52 L 32 34 Z" fill="#ffffff" stroke="#207448" stroke-width="3" stroke-linejoin="round" />
    <line x1="16" y1="40" x2="15" y2="48" stroke="#207448" stroke-width="2.5" stroke-linecap="round" />
    <line x1="22" y1="36" x2="22" y2="48" stroke="#207448" stroke-width="2.5" stroke-linecap="round" />
    <line x1="28" y1="38" x2="29" y2="48" stroke="#207448" stroke-width="2.5" stroke-linecap="round" />
  </g>
  <line x1="1230" y1="240" x2="1540" y2="240" stroke="#207448" stroke-width="1.5" opacity="0.3" />

  <text x="1385" y="295" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="1385" dy="0">rescue, copy out, </tspan>
    <tspan x="1385" dy="32">then truncate </tspan>
    <tspan x="1385" dy="32">through </tspan>
    <tspan x="1385" dy="32">/proc/PID/fd/N</tspan>
  </text>

  <text x="1385" y="500" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">df used space falls</text>

  <!-- Command Block under Step 4 -->
  <rect x="1210" y="610" width="350" height="210" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
  
  <text x="1385" y="655" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36"><tspan x="1385" dy="0">copy what you need </tspan><tspan x="1385" dy="30">out of /proc/PID/fd/N</tspan></text>
  
  <text x="1385" y="730" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#207448">: &gt; /proc/PID/fd/N</text>
  
  <text x="1385" y="770" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36"><tspan x="1385" dy="0">the process </tspan><tspan x="1385" dy="28">keeps writing</tspan></text>

  <!-- Lasting fix box under the whole row -->
  <rect x="40" y="860" width="1520" height="80" rx="12" fill="#edf1ee" stroke="#7a8c82" stroke-width="2" />
  <text x="800" y="910" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36">lasting fix: make the writer reopen its file after rotation</text>

  <!-- Takeaway bar -->
  <rect x="40" y="980" width="1520" height="64" rx="10" fill="#207448" />
  <text x="800" y="1022" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">The space comes back when the last descriptor closes or the file is truncated.</text>

</svg>'''

with open('perfect_candidate.svg', 'w') as f:
    f.write(svg_code)
print("Updated perfect_candidate.svg")
