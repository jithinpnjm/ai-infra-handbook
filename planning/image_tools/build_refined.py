import xml.etree.ElementTree as ET
import re
import pathlib
import asyncio
from playwright.async_api import async_playwright

def build_perfect_svg():
    W = 1600
    H = 1150
    
    parts = []
    parts.append('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ''' + str(W) + ''' ''' + str(H) + '''" width="''' + str(W) + '''" height="''' + str(H) + '''">
  <title>a &amp;&amp; b || c is not an if/else</title>
  <desc>Two side-by-side flow diagrams comparing if-then-else with the and-or construct, showing that c runs even though a succeeded when b fails.</desc>

  <defs>
    <!-- Green marker (18px) -->
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="''' + str(W) + '''" height="''' + str(H) + '''" fill="#f5f8f5" />

  <!-- Title (48px bold) -->
  <text x="800" y="58" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="48" font-weight="bold" fill="#303a36"><tspan font-family="ui-monospace, monospace">a &amp;&amp; b || c</tspan> is not an if/else</text>

  <!-- ========================================== -->
  <!-- LEFT PANEL: if a; then b; else c; fi       -->
  <!-- ========================================== -->
  <rect x="50" y="95" width="720" height="585" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  
  <!-- Left Header -->
  <text x="410" y="140" text-anchor="middle" font-family="ui-monospace, monospace" font-size="30" font-weight="bold" fill="#207448">if a; then b; else c; fi</text>

  <!-- Left Arrows (drawn behind nodes) -->
  <!-- 1. start -> diamond 'a succeeds?' -->
  <line x1="410" y1="210" x2="410" y2="238" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- 2. diamond -> box 'b' (yes) -->
  <path d="M 220 305 L 240 305 L 240 385" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
  <text x="215" y="295" text-anchor="end" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#207448">yes</text>

  <!-- 3. diamond -> box 'c' (no) -->
  <path d="M 600 305 L 580 305 L 580 385" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
  <text x="605" y="295" text-anchor="start" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#303a36">no</text>

  <!-- 4. box 'b' -> end -->
  <path d="M 240 475 L 240 545 L 320 545" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- 5. box 'c' -> end -->
  <path d="M 580 475 L 580 545 L 500 545" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- Left Nodes -->
  <!-- Node: start (center 410, 178, w=160, h=64) -->
  <g id="left-start">
    <rect x="330" y="146" width="160" height="64" rx="32" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <polygon points="352,168 352,188 368,178" fill="none" stroke="#207448" stroke-width="3" stroke-linejoin="round" />
    <text x="418" y="187" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#303a36">start</text>
  </g>

  <!-- Node: diamond 'a succeeds?' (center 410, 305, w=380, h=130) -->
  <g id="left-diamond-a">
    <polygon points="410,240 600,305 410,370 220,305" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <!-- Test/Condition outline icon (56px) on left of text -->
    <g transform="translate(265, 287)" stroke="#207448" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="18" cy="18" r="14" />
      <path d="M 14 13 C 14 9, 22 9, 22 14 C 22 18, 18 18, 18 22" />
      <circle cx="18" cy="27" r="1.5" fill="#207448" />
    </g>
    <text x="425" y="314" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#303a36">a succeeds?</text>
  </g>

  <!-- Node: box 'b' (x=140, y=385, w=200, h=90) -->
  <g id="left-box-b">
    <rect x="140" y="385" width="200" height="90" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <g transform="translate(158, 403)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="2" y="4" width="48" height="42" rx="6" />
      <line x1="2" y1="16" x2="50" y2="16" stroke-width="2.5" />
      <polyline points="12,26 20,33 12,40" stroke-width="3" />
      <line x1="24" y1="40" x2="38" y2="40" stroke-width="3" />
    </g>
    <text x="260" y="442" text-anchor="middle" font-family="ui-monospace, monospace" font-size="34" font-weight="bold" fill="#303a36">b</text>
  </g>

  <!-- Node: box 'c' (x=480, y=385, w=200, h=90) -->
  <g id="left-box-c">
    <rect x="480" y="385" width="200" height="90" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <g transform="translate(498, 403)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="2" y="4" width="48" height="42" rx="6" />
      <line x1="2" y1="16" x2="50" y2="16" stroke-width="2.5" />
      <polyline points="12,26 20,33 12,40" stroke-width="3" />
      <line x1="24" y1="40" x2="38" y2="40" stroke-width="3" />
    </g>
    <text x="600" y="442" text-anchor="middle" font-family="ui-monospace, monospace" font-size="34" font-weight="bold" fill="#303a36">c</text>
  </g>

  <!-- Node: end (center 410, 545, w=160, h=64) -->
  <g id="left-end">
    <rect x="330" y="513" width="160" height="64" rx="32" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <circle cx="355" cy="545" r="11" fill="none" stroke="#207448" stroke-width="3" />
    <circle cx="355" cy="545" r="4" fill="#207448" />
    <text x="418" y="554" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#303a36">end</text>
  </g>

  <!-- ========================================== -->
  <!-- RIGHT PANEL: a && b || c                   -->
  <!-- ========================================== -->
  <rect x="830" y="95" width="720" height="585" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  
  <!-- Right Header -->
  <text x="1190" y="140" text-anchor="middle" font-family="ui-monospace, monospace" font-size="30" font-weight="bold" fill="#207448">a &amp;&amp; b || c</text>

  <!-- Right Arrows (drawn behind nodes) -->
  <!-- 1. start -> diamond 'a succeeds?' -->
  <line x1="1020" y1="210" x2="1020" y2="238" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- 2. diamond 1 -> box 'b' (yes) -->
  <line x1="1020" y1="335" x2="1020" y2="368" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
  <text x="1037" y="354" text-anchor="start" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#207448">yes</text>

  <!-- 3. box 'b' -> diamond 2 'b succeeded?' -->
  <line x1="1020" y1="440" x2="1020" y2="474" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- 4. diamond 2 -> end (yes) -->
  <line x1="1020" y1="588" x2="1020" y2="610" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
  <text x="1037" y="602" text-anchor="start" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#207448">yes</text>

  <!-- 5. diamond 1 -> box 'c' (labelled 'a failed') -->
  <!-- leaves diamond 1 right vertex (1185, 285) -> right to 1375, down to top of box c (1375, 365) -->
  <path d="M 1185 285 L 1375 285 L 1375 365" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
  <text x="1275" y="273" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#303a36">a failed</text>

  <!-- 6. diamond 2 -> box 'c' (labelled 'b failed') -->
  <!-- leaves diamond 2 right vertex (1185, 540) -> right to 1375, up to bottom of box c (1375, 510) -->
  <path d="M 1185 540 L 1375 540 L 1375 510" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
  <text x="1275" y="568" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#303a36">b failed</text>

  <!-- Right Nodes -->
  <!-- Node: start (center 1020, 178, w=160, h=64) -->
  <g id="right-start">
    <rect x="940" y="146" width="160" height="64" rx="32" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <polygon points="962,168 962,188 978,178" fill="none" stroke="#207448" stroke-width="3" stroke-linejoin="round" />
    <text x="1028" y="187" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#303a36">start</text>
  </g>

  <!-- Node: diamond 1 'a succeeds?' (center 1020, 285, w=330, h=96) -->
  <g id="right-diamond-a">
    <polygon points="1020,237 1185,285 1020,333 855,285" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <g transform="translate(890, 272)" stroke="#207448" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="13" cy="13" r="10" />
      <path d="M 10 9 C 10 6, 16 6, 16 10 C 16 13, 13 13, 13 16" />
      <circle cx="13" cy="20" r="1" fill="#207448" />
    </g>
    <text x="1035" y="294" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="25" font-weight="bold" fill="#303a36">a succeeds?</text>
  </g>

  <!-- Node: box 'b' (x=935, y=368, w=170, h=72) -->
  <g id="right-box-b">
    <rect x="935" y="368" width="170" height="72" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <g transform="translate(950, 381)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="2" y="4" width="44" height="38" rx="5" />
      <line x1="2" y1="14" x2="46" y2="14" stroke-width="2.5" />
      <polyline points="10,23 17,29 10,35" stroke-width="2.5" />
      <line x1="21" y1="35" x2="33" y2="35" stroke-width="2.5" />
    </g>
    <text x="1035" y="415" text-anchor="middle" font-family="ui-monospace, monospace" font-size="32" font-weight="bold" fill="#303a36">b</text>
  </g>

  <!-- Node: diamond 2 'b succeeded?' (center 1020, 540, w=330, h=96) -->
  <g id="right-diamond-b">
    <polygon points="1020,492 1185,540 1020,588 855,540" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <g transform="translate(885, 527)" stroke="#207448" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="13" cy="13" r="10" />
      <path d="M 10 9 C 10 6, 16 6, 16 10 C 16 13, 13 13, 13 16" />
      <circle cx="13" cy="20" r="1" fill="#207448" />
    </g>
    <text x="1035" y="549" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="25" font-weight="bold" fill="#303a36">b succeeded?</text>
  </g>

  <!-- Node: end (center 1020, 642, w=160, h=64) -->
  <g id="right-end">
    <rect x="940" y="610" width="160" height="64" rx="32" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <circle cx="965" cy="642" r="11" fill="none" stroke="#207448" stroke-width="3" />
    <circle cx="965" cy="642" r="4" fill="#207448" />
    <text x="1028" y="651" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#303a36">end</text>
  </g>

  <!-- Node: box 'c' (ORANGE OUTLINED) with 'c runs even though a succeeded' -->
  <!-- x=1220, y=365, w=310, h=145 -->
  <g id="right-box-c">
    <rect x="1220" y="365" width="310" height="145" rx="14" fill="#fff9f3" stroke="#db8129" stroke-width="3.5" />
    <!-- Warning outline icon in orange -->
    <g transform="translate(1238, 412)" stroke="#db8129" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <polygon points="25,5 48,43 2,43" />
      <line x1="25" y1="18" x2="25" y2="30" stroke-width="3.5" />
      <line x1="25" y1="36" x2="25" y2="38" stroke-width="4" />
    </g>
    <!-- Label: 'c' -->
    <text x="1305" y="415" font-family="ui-monospace, monospace" font-size="34" font-weight="bold" fill="#303a36">c</text>
    <!-- Label: 'c runs even though a succeeded' -->
    <text x="1305" y="457" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#db8129">
      <tspan x="1305" dy="0">c runs even though</tspan>
      <tspan x="1305" dy="28">a succeeded</tspan>
    </text>
  </g>

  <!-- ========================================== -->
  <!-- BELOW: LIST OF GOOD ONE-LINE GUARDS        -->
  <!-- ========================================== -->
  <rect x="50" y="705" width="1500" height="300" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2.5" />

  <!-- Guard 1: [ -d "$d" ] || mkdir -p "$d" -->
  <g id="guard-1">
    <rect x="75" y="720" width="1450" height="64" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />
    <g transform="translate(95, 734)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 4 8 L 14 8 L 18 14 L 32 14 A 3 3 0 0 1 35 17 L 35 31 A 3 3 0 0 1 32 34 L 4 34 A 3 3 0 0 1 1 31 L 1 11 A 3 3 0 0 1 4 8 Z" />
    </g>
    <text x="155" y="761" font-family="ui-monospace, monospace" font-size="25" font-weight="bold" fill="#303a36">[ -d "$d" ] || mkdir -p "$d"</text>
  </g>

  <!-- Guard 2: command -v nvidia-smi >/dev/null || exit 0 -->
  <g id="guard-2">
    <rect x="75" y="790" width="1450" height="64" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />
    <g transform="translate(95, 804)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="6" width="24" height="24" rx="4" />
      <circle cx="18" cy="18" r="5" />
      <line x1="12" y1="1" x2="12" y2="6" />
      <line x1="24" y1="1" x2="24" y2="6" />
      <line x1="12" y1="30" x2="12" y2="35" />
      <line x1="24" y1="30" x2="24" y2="35" />
      <line x1="1" y1="12" x2="6" y2="12" />
      <line x1="1" y1="24" x2="6" y2="24" />
      <line x1="30" y1="12" x2="35" y2="12" />
      <line x1="30" y1="24" x2="35" y2="24" />
    </g>
    <text x="155" y="831" font-family="ui-monospace, monospace" font-size="25" font-weight="bold" fill="#303a36">command -v nvidia-smi &gt;/dev/null || exit 0</text>
  </g>

  <!-- Guard 3: cd "$dir" || exit 1 -->
  <g id="guard-3">
    <rect x="75" y="860" width="1450" height="64" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />
    <g transform="translate(95, 874)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <polyline points="6,26 18,10 30,26" />
      <line x1="18" y1="12" x2="18" y2="32" />
    </g>
    <text x="155" y="901" font-family="ui-monospace, monospace" font-size="25" font-weight="bold" fill="#303a36">cd "$dir" || exit 1</text>
  </g>

  <!-- Guard 4: [ -z "$x" ] && { echo "empty" >&2; exit 1; } -->
  <g id="guard-4">
    <rect x="75" y="930" width="1450" height="64" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />
    <g transform="translate(95, 944)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 18 4 L 32 9 C 32 23 18 32 18 32 C 18 32 4 23 4 9 Z" />
      <polyline points="12,17 16,21 24,13" />
    </g>
    <text x="155" y="971" font-family="ui-monospace, monospace" font-size="25" font-weight="bold" fill="#303a36">[ -z "$x" ] &amp;&amp; &#123; echo "empty" &gt;&amp;2; exit 1; &#125;</text>
  </g>

  <!-- ========================================== -->
  <!-- BOTTOM NOTE / TAKEAWAY BAR                 -->
  <!-- ========================================== -->
  <rect x="50" y="1025" width="1500" height="70" rx="14" fill="#207448" />
  <text x="800" y="1069" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#ffffff">&amp;&amp; runs the next command only if the last one succeeded; || only if it failed</text>
</svg>''')
    return "".join(parts)

pathlib.Path("candidate_and_or_trap.svg").write_text(build_perfect_svg())
print("Regenerated candidate_and_or_trap.svg successfully.")
