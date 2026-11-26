import re, pathlib, asyncio
from playwright.async_api import async_playwright

def build_perfect_svg():
    W = 1600
    H = 1150
    
    parts = []
    parts.append(f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
  <title>a &amp;&amp; b || c is not an if/else</title>
  <desc>Two side-by-side flow diagrams comparing if-then-else with the and-or construct, showing that c runs even though a succeeded when b fails.</desc>

  <defs>
    <!-- Green marker (18px) -->
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="{W}" height="{H}" fill="#f5f8f5" />

  <!-- Title (48px bold) -->
  <text x="800" y="58" text-anchor="middle" font-size="48" font-weight="bold" fill="#303a36"><tspan font-family="ui-monospace, monospace">a &amp;&amp; b || c</tspan><tspan font-family="system-ui, -apple-system, sans-serif"> is not an if/else</tspan></text>

  <!-- ========================================== -->
  <!-- LEFT PANEL: if a; then b; else c; fi       -->
  <!-- ========================================== -->
  <rect x="40" y="95" width="710" height="690" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  
  <!-- Left Header -->
  <text x="395" y="140" text-anchor="middle" font-family="ui-monospace, monospace" font-size="30" font-weight="bold" fill="#207448">if a; then b; else c; fi</text>

  <!-- Left Arrows (drawn behind nodes) -->
  <!-- 1. start -> diamond 'a succeeds?' -->
  <line x1="395" y1="222" x2="395" y2="242" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- 2. diamond -> box 'b' (yes) -->
  <path d="M 145 320 L 230 320 L 230 415" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
  <text x="140" y="310" text-anchor="end" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#207448">yes</text>

  <!-- 3. diamond -> box 'c' (no) -->
  <path d="M 645 320 L 560 320 L 560 415" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
  <text x="650" y="310" text-anchor="start" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#303a36">no</text>

  <!-- 4. box 'b' -> end -->
  <path d="M 230 515 L 230 635 L 300 635" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- 5. box 'c' -> end -->
  <path d="M 560 515 L 560 635 L 490 635" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- Left Nodes -->
  <!-- Node: start (center 395, 185, w=180, h=74) -->
  <g id="left-start">
    <rect x="305" y="148" width="180" height="74" rx="37" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <polygon points="328,175 328,195 344,185" fill="none" stroke="#207448" stroke-width="3.5" stroke-linejoin="round" />
    <text x="408" y="195" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">start</text>
  </g>

  <!-- Node: diamond 'a succeeds?' (center 395, 320, rx=250, ry=78 -> w=500, h=156) -->
  <g id="left-diamond-a">
    <polygon points="395,242 645,320 395,398 145,320" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <!-- Decision/condition icon beside title -->
    <g transform="translate(285, 302)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="18" cy="18" r="15" />
      <path d="M 14 12 C 14 7, 22 7, 22 13 C 22 17, 18 17, 18 22" />
      <circle cx="18" cy="27" r="1.5" fill="#207448" />
    </g>
    <text x="428" y="330" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">a succeeds?</text>
  </g>

  <!-- Node: box 'b' (x=125, y=415, w=210, h=100) -->
  <g id="left-box-b">
    <rect x="125" y="415" width="210" height="100" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <g transform="translate(145, 441)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="2" y="4" width="48" height="42" rx="6" />
      <line x1="2" y1="16" x2="50" y2="16" stroke-width="2.5" />
      <polyline points="12,26 20,33 12,40" stroke-width="3" />
      <line x1="24" y1="40" x2="38" y2="40" stroke-width="3" />
    </g>
    <text x="250" y="477" text-anchor="middle" font-family="ui-monospace, monospace" font-size="34" font-weight="bold" fill="#303a36">b</text>
  </g>

  <!-- Node: box 'c' (x=455, y=415, w=210, h=100) -->
  <g id="left-box-c">
    <rect x="455" y="415" width="210" height="100" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <g transform="translate(475, 441)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="2" y="4" width="48" height="42" rx="6" />
      <line x1="2" y1="16" x2="50" y2="16" stroke-width="2.5" />
      <polyline points="12,26 20,33 12,40" stroke-width="3" />
      <line x1="24" y1="40" x2="38" y2="40" stroke-width="3" />
    </g>
    <text x="580" y="477" text-anchor="middle" font-family="ui-monospace, monospace" font-size="34" font-weight="bold" fill="#303a36">c</text>
  </g>

  <!-- Node: end (center 395, 635, w=180, h=74) -->
  <g id="left-end">
    <rect x="305" y="598" width="180" height="74" rx="37" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <circle cx="333" cy="635" r="13" fill="none" stroke="#207448" stroke-width="3.5" />
    <circle cx="333" cy="635" r="4.5" fill="#207448" />
    <text x="408" y="645" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">end</text>
  </g>

  <!-- ========================================== -->
  <!-- RIGHT PANEL: a && b || c                   -->
  <!-- ========================================== -->
  <rect x="780" y="95" width="780" height="690" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  
  <!-- Right Header -->
  <text x="1170" y="140" text-anchor="middle" font-family="ui-monospace, monospace" font-size="30" font-weight="bold" fill="#207448">a &amp;&amp; b || c</text>

  <!-- Right Arrows (drawn behind nodes) -->
  <!-- 1. start -> diamond 'a succeeds?' -->
  <line x1="1015" y1="222" x2="1015" y2="238" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- 2. diamond 1 -> box 'b' (yes) -->
  <line x1="1015" y1="360" x2="1015" y2="395" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
  <text x="1032" y="382" text-anchor="start" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#207448">yes</text>

  <!-- 3. box 'b' -> diamond 2 'b succeeded?' -->
  <line x1="1015" y1="475" x2="1015" y2="500" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- 4. diamond 2 -> end (yes) -->
  <line x1="1015" y1="640" x2="1015" y2="675" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
  <text x="1032" y="662" text-anchor="start" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#207448">yes</text>

  <!-- 5. diamond 1 -> box 'c' (labelled 'a failed') -->
  <!-- leaves diamond 1 right vertex (1235, 300) -> right to 1400, down to top of box c (1400, 375) -->
  <path d="M 1235 300 L 1400 300 L 1400 375" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
  <text x="1310" y="288" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#303a36">a failed</text>

  <!-- 6. diamond 2 -> box 'c' (labelled 'b failed') -->
  <!-- leaves diamond 2 right vertex (1235, 570) -> right to 1400, up to bottom of box c (1400, 545) -->
  <path d="M 1235 570 L 1400 570 L 1400 545" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
  <text x="1310" y="595" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#303a36">b failed</text>

  <!-- Right Nodes -->
  <!-- Node: start (center 1015, 185, w=180, h=74) -->
  <g id="right-start">
    <rect x="925" y="148" width="180" height="74" rx="37" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <polygon points="948,175 948,195 964,185" fill="none" stroke="#207448" stroke-width="3.5" stroke-linejoin="round" />
    <text x="1028" y="195" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">start</text>
  </g>

  <!-- Node: diamond 1 'a succeeds?' (center 1015, 300, rx=220, ry=60 -> w=440, h=120) -->
  <g id="right-diamond-a">
    <polygon points="1015,240 1235,300 1015,360 795,300" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <g transform="translate(905, 284)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="16" cy="16" r="13" />
      <path d="M 13 11 C 13 6, 19 6, 19 12 C 19 15, 16 15, 16 19" />
      <circle cx="16" cy="24" r="1.5" fill="#207448" />
    </g>
    <text x="1048" y="310" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">a succeeds?</text>
  </g>

  <!-- Node: box 'b' (x=915, y=395, w=200, h=80) -->
  <g id="right-box-b">
    <rect x="915" y="395" width="200" height="80" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <g transform="translate(935, 416)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="2" y="4" width="44" height="38" rx="5" />
      <line x1="2" y1="14" x2="46" y2="14" stroke-width="2.5" />
      <polyline points="10,23 17,29 10,35" stroke-width="2.5" />
      <line x1="21" y1="35" x2="33" y2="35" stroke-width="2.5" />
    </g>
    <text x="1035" y="448" text-anchor="middle" font-family="ui-monospace, monospace" font-size="34" font-weight="bold" fill="#303a36">b</text>
  </g>

  <!-- Node: diamond 2 'b succeeded?' (center 1015, 570, rx=220, ry=70 -> w=440, h=140) -->
  <g id="right-diamond-b">
    <polygon points="1015,500 1235,570 1015,640 795,570" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <g transform="translate(895, 554)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="16" cy="16" r="13" />
      <path d="M 13 11 C 13 6, 19 6, 19 12 C 19 15, 16 15, 16 19" />
      <circle cx="16" cy="24" r="1.5" fill="#207448" />
    </g>
    <text x="1048" y="580" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">b succeeded?</text>
  </g>

  <!-- Node: end (center 1015, 715, w=180, h=74) -->
  <g id="right-end">
    <rect x="925" y="678" width="180" height="74" rx="37" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <circle cx="953" cy="715" r="13" fill="none" stroke="#207448" stroke-width="3.5" />
    <circle cx="953" cy="715" r="4.5" fill="#207448" />
    <text x="1028" y="725" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">end</text>
  </g>

  <!-- Node: box 'c' (ORANGE OUTLINED) with 'c runs even though a succeeded' -->
  <!-- x=1270, y=375, w=260, h=170 -->
  <g id="right-box-c">
    <rect x="1270" y="375" width="260" height="170" rx="14" fill="#fff9f3" stroke="#db8129" stroke-width="3.5" />
    <!-- Warning outline icon in orange -->
    <g transform="translate(1288, 420)" stroke="#db8129" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <polygon points="24,4 46,42 2,42" />
      <line x1="24" y1="17" x2="24" y2="29" stroke-width="3.5" />
      <line x1="24" y1="35" x2="24" y2="37" stroke-width="4" />
    </g>
    <!-- Label: 'c' -->
    <text x="1350" y="418" font-family="ui-monospace, monospace" font-size="34" font-weight="bold" fill="#303a36">c</text>
    <!-- Label: 'c runs even though a succeeded' -->
    <text x="1350" y="456" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#db8129">
      <tspan x="1350" dy="0">c runs even </tspan>
      <tspan x="1350" dy="28">though </tspan>
      <tspan x="1350" dy="28">a succeeded</tspan>
    </text>
  </g>

  <!-- ========================================== -->
  <!-- BELOW: LIST OF GOOD ONE-LINE GUARDS        -->
  <!-- ========================================== -->
  <rect x="50" y="810" width="1500" height="235" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2.5" />

  <!-- Guard 1: [ -d "$d" ] || mkdir -p "$d" -->
  <g id="guard-1">
    <rect x="65" y="822" width="1470" height="50" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />
    <g transform="translate(85, 832)" stroke="#207448" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 3 6 L 11 6 L 15 11 L 26 11 A 2 2 0 0 1 28 13 L 28 24 A 2 2 0 0 1 26 26 L 3 26 A 2 2 0 0 1 1 24 L 1 8 A 2 2 0 0 1 3 6 Z" />
    </g>
    <text x="135" y="857" font-family="ui-monospace, monospace" font-size="25" font-weight="bold" fill="#303a36">[ -d "$d" ] || mkdir -p "$d"</text>
  </g>

  <!-- Guard 2: command -v nvidia-smi >/dev/null || exit 0 -->
  <g id="guard-2">
    <rect x="65" y="878" width="1470" height="50" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />
    <g transform="translate(85, 888)" stroke="#207448" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="5" y="5" width="20" height="20" rx="3" />
      <circle cx="15" cy="15" r="4" />
      <line x1="10" y1="1" x2="10" y2="5" />
      <line x1="20" y1="1" x2="20" y2="5" />
      <line x1="10" y1="25" x2="10" y2="29" />
      <line x1="20" y1="25" x2="20" y2="29" />
      <line x1="1" y1="10" x2="5" y2="10" />
      <line x1="1" y1="20" x2="5" y2="20" />
      <line x1="25" y1="10" x2="29" y2="10" />
      <line x1="25" y1="20" x2="29" y2="20" />
    </g>
    <text x="135" y="913" font-family="ui-monospace, monospace" font-size="25" font-weight="bold" fill="#303a36">command -v nvidia-smi &gt;/dev/null || exit 0</text>
  </g>

  <!-- Guard 3: cd "$dir" || exit 1 -->
  <g id="guard-3">
    <rect x="65" y="934" width="1470" height="50" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />
    <g transform="translate(85, 944)" stroke="#207448" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <polyline points="5,21 15,8 25,21" />
      <line x1="15" y1="10" x2="15" y2="26" />
    </g>
    <text x="135" y="969" font-family="ui-monospace, monospace" font-size="25" font-weight="bold" fill="#303a36">cd "$dir" || exit 1</text>
  </g>

  <!-- Guard 4: [ -z "$x" ] && {{ echo "empty" >&2; exit 1; }} -->
  <g id="guard-4">
    <rect x="65" y="990" width="1470" height="50" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />
    <g transform="translate(85, 1000)" stroke="#207448" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 15 3 L 26 7 C 26 19 15 26 15 26 C 15 26 4 19 4 7 Z" />
      <polyline points="10,14 13,17 20,10" />
    </g>
    <text x="135" y="1025" font-family="ui-monospace, monospace" font-size="25" font-weight="bold" fill="#303a36">[ -z "$x" ] &amp;&amp; &#123; echo "empty" &gt;&amp;2; exit 1; &#125;</text>
  </g>

  <!-- ========================================== -->
  <!-- BOTTOM NOTE / TAKEAWAY BAR                 -->
  <!-- ========================================== -->
  <rect x="50" y="1065" width="1500" height="65" rx="14" fill="#207448" />
  <text x="800" y="1107" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#ffffff">&amp;&amp; runs the next command only if the last one succeeded; || only if it failed</text>
</svg>''')
    return "".join(parts)

svg_str = build_perfect_svg()
pathlib.Path("candidate_and_or_trap.svg").write_text(svg_str)
print("Updated candidate_and_or_trap.svg successfully.")
