import xml.etree.ElementTree as ET
import re

def build_svg_string():
    H = 1200
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 {H}" width="1600" height="{H}">')
    svg.append('  <title>Top-level code runs in order, a def body runs only when called</title>')
    svg.append('  <desc>Visual explanation of Python module import and execution order: top-level statements run sequentially from top to bottom, def statements bind function names without running their bodies, and forward references succeed only if called after all referenced names are assigned.</desc>')
    svg.append('')
    svg.append('  <defs>')
    svg.append('  </defs>')
    svg.append('')
    svg.append(f'  <!-- Canvas Background -->')
    svg.append(f'  <rect width="1600" height="{H}" fill="#f5f8f5" />')
    svg.append('')
    
    # Title (48px bold)
    # y = 50, 100
    svg.append('  <!-- Title -->')
    svg.append('  <text x="800" y="50" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">')
    svg.append('    <tspan x="800" dy="0">Top-level code runs in order, </tspan>')
    svg.append('    <tspan x="800" dy="50">a def body runs only when called</tspan>')
    svg.append('  </text>')
    svg.append('')

    # Section 1: Rule Box (x: 40 to 1560, w: 1520)
    # y = 125, h = 120 (ends at 245)
    # Line 1: y = 162 (ttop = 162 - 19.2 = 142.8 -> T = 142.8 - 125 = 17.8 px >= 16)
    # Line 2: dy = 30 (y = 192)
    # Line 3: dy = 30 (y = 222 -> tbot = 222 -> B = 245 - 222 = 23.0 px >= 16)
    svg.append('  <!-- Rule Box -->')
    svg.append('  <g id="rule-box">')
    svg.append('    <rect x="40" y="125" width="1520" height="120" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    # Icon: Scroll/Document with rule lines (50x50 at x=65, y=148)
    svg.append('    <g transform="translate(65, 148)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="2" y="2" width="46" height="50" rx="6" fill="#ffffff" />')
    svg.append('      <line x1="12" y1="16" x2="38" y2="16" />')
    svg.append('      <line x1="12" y1="27" x2="38" y2="27" />')
    svg.append('      <line x1="12" y1="38" x2="26" y2="38" />')
    svg.append('    </g>')
    svg.append('    <text x="145" y="162" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="145" dy="0">when Python first imports or reloads a module it runs top-level statements from top to bottom, </tspan>')
    svg.append('      <tspan x="145" dy="30">so top-level code cannot use names assigned lower down; a def body can refer to a name </tspan>')
    svg.append('      <tspan x="145" dy="30">defined later as long as it exists by the time of the call</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('')

    # Gap after rule box = 40 px: y = 245 + 40 = 285
    # Steps: x = 40 to 1180 (w = 1140)
    # Side Col: x = 1220 to 1560 (w = 340)
    # Side Col Header: x = 1220, y = 285, w = 340, h = 65 (ends at 350)
    # Text wrapped to 2 lines so padding >= 16px!
    svg.append('  <!-- Side Column Header -->')
    svg.append('  <g id="side-col-header">')
    svg.append('    <rect x="1220" y="280" width="340" height="80" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('    <text x="1390" y="318" text-anchor="middle" font-family="sans-serif" font-size="25" font-weight="bold" fill="#303a36">')
    svg.append('      <tspan x="1390" dy="0">names assigned </tspan>')
    svg.append('      <tspan x="1390" dy="24">so far</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('')

    # Steps 1 to 5:
    # Let h = 86 for each step box.
    # Gap between step boxes = 22 px.
    # Step 1: y = 370, h = 86 (ends 456)
    # Step 2: y = 478, h = 86 (ends 564)
    # Step 3: y = 586, h = 86 (ends 672)
    # Step 4: y = 694, h = 86 (ends 780)
    # Step 5: y = 802, h = 86 (ends 888)
    # Side Col Row 1: y = 370, h = 86 (ends 456) -> "none"
    # Side Col Rows 2 & 3: y = 478, h = 194 (ends 672) -> "func1"
    # Side Col Rows 4 & 5: y = 694, h = 194 (ends 888) -> "func1, func2"
    # Gap after step 5 = 928 - 888 = 40 px!
    # Extra strip: y = 928, h = 150 (ends 1078)
    # Gap after extra strip = 1108 - 1078 = 30 px, or let's make:
    # Let's adjust slightly:
    # If Step h = 84, gap = 20:
    # Step 1: 365 - 449
    # Step 2: 469 - 553
    # Step 3: 573 - 657
    # Step 4: 677 - 761
    # Step 5: 781 - 865
    # Gap 40 -> Extra strip: 905 - 1055 (h=150)
    # Gap 40 -> Bottom bar: 1095 - 1155 (h=60)
    # Bottom margin = 1200 - 1155 = 45 px!
    
    # Let's check step text inside box (y=365, h=84):
    # Line 1 y = 365 + 38 = 403. ttop = 403 - 26*0.8 = 382.2. Top padding = 382.2 - 365 = 17.2 px >= 16!
    # Line 2 dy = 28 -> y = 431. tbot = 431. Bottom padding = 449 - 431 = 18.0 px >= 16!
    # Left padding: x = 135. Icon ends at 60 + 48 = 108. Padding between icon & text = 27 px >= 16!
    
    # Step 1:
    svg.append('  <!-- Step 1 -->')
    svg.append('  <g id="step-1">')
    svg.append('    <rect x="40" y="365" width="1140" height="84" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('    <g transform="translate(60, 377)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="2" y="4" width="46" height="42" rx="5" fill="#ffffff" />')
    svg.append('      <polyline points="10,18 18,25 10,32" />')
    svg.append('      <line x1="24" y1="32" x2="38" y2="32" />')
    svg.append('    </g>')
    svg.append('    <text x="135" y="403" font-family="sans-serif" font-size="26" fill="#303a36">')
    svg.append('      <tspan x="135" dy="0" font-weight="bold">1 func1()  </tspan>')
    svg.append('      <tspan x="135" dy="28" font-size="24">would raise NameError: func1 not yet assigned</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('')

    # Side Column Row 1: "none"
    svg.append('  <!-- Side Column Row 1: none -->')
    svg.append('  <g id="side-row-1">')
    svg.append('    <rect x="1220" y="365" width="340" height="84" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('    <text x="1390" y="415" text-anchor="middle" font-family="monospace" font-size="25" font-weight="bold" fill="#303a36">none</text>')
    svg.append('  </g>')
    svg.append('')

    # Step 2:
    svg.append('  <!-- Step 2 -->')
    svg.append('  <g id="step-2">')
    svg.append('    <rect x="40" y="469" width="1140" height="84" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('    <g transform="translate(60, 481)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="25" cy="25" r="18" fill="#ffffff" />')
    svg.append('      <circle cx="25" cy="25" r="7" />')
    svg.append('      <line x1="25" y1="3" x2="25" y2="9" /><line x1="25" y1="41" x2="25" y2="47" />')
    svg.append('      <line x1="3" y1="25" x2="9" y2="25" /><line x1="41" y1="25" x2="47" y2="25" />')
    svg.append('    </g>')
    svg.append('    <text x="135" y="507" font-family="sans-serif" font-size="26" fill="#303a36">')
    svg.append('      <tspan x="135" dy="0" font-weight="bold">2 def func1(): print(func2())  </tspan>')
    svg.append('      <tspan x="135" dy="28" font-size="24">binds the name func1; the body does not run</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('')

    # Step 3:
    svg.append('  <!-- Step 3 -->')
    svg.append('  <g id="step-3">')
    svg.append('    <rect x="40" y="573" width="1140" height="84" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('    <g transform="translate(60, 585)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="25" cy="25" r="20" fill="#ffffff" />')
    svg.append('      <polyline points="25,12 25,25 35,25" />')
    svg.append('    </g>')
    svg.append('    <text x="135" y="611" font-family="sans-serif" font-size="26" fill="#303a36">')
    svg.append('      <tspan x="135" dy="0" font-weight="bold">3 func1() here raises </tspan>')
    svg.append('      <tspan x="135" dy="28" font-size="24">NameError: func2 not yet assigned when func1 runs</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('')

    # Side Column Rows 2 & 3 combined: "func1" (spans y=469 to y=657, h=188)
    svg.append('  <!-- Side Column Rows 2 & 3: func1 -->')
    svg.append('  <g id="side-row-2-3">')
    svg.append('    <rect x="1220" y="469" width="340" height="188" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('    <text x="1390" y="571" text-anchor="middle" font-family="monospace" font-size="26" font-weight="bold" fill="#303a36">func1</text>')
    svg.append('  </g>')
    svg.append('')

    # Step 4:
    svg.append('  <!-- Step 4 -->')
    svg.append('  <g id="step-4">')
    svg.append('    <rect x="40" y="677" width="1140" height="84" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('    <g transform="translate(60, 689)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="4" y="6" width="42" height="38" rx="4" fill="#ffffff" />')
    svg.append('      <polyline points="14,18 20,25 14,32" />')
    svg.append('      <line x1="24" y1="32" x2="34" y2="32" />')
    svg.append('    </g>')
    svg.append('    <text x="135" y="726" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">4 def func2(): return &quot;Hello&quot;</text>')
    svg.append('  </g>')
    svg.append('')

    # Step 5 (ORANGE):
    svg.append('  <!-- Step 5 (Orange highlight: success state) -->')
    svg.append('  <g id="step-5">')
    svg.append('    <rect x="40" y="781" width="1140" height="84" rx="10" fill="#e8f1ea" stroke="#db8129" stroke-width="3.5" />')
    svg.append('    <g transform="translate(60, 793)" stroke="#db8129" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="25" cy="25" r="20" fill="#ffffff" />')
    svg.append('      <polyline points="15,25 22,32 35,18" />')
    svg.append('    </g>')
    svg.append('    <text x="135" y="819" font-family="sans-serif" font-size="26" fill="#303a36">')
    svg.append('      <tspan x="135" dy="0" font-weight="bold" fill="#db8129">5 func1() works: </tspan>')
    svg.append('      <tspan x="135" dy="28" font-size="24">both names assigned, prints Hello</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('')

    # Side Column Rows 4 & 5 combined: "func1, func2" (spans y=677 to y=865, h=188)
    svg.append('  <!-- Side Column Rows 4 & 5: func1, func2 -->')
    svg.append('  <g id="side-row-4-5">')
    svg.append('    <rect x="1220" y="677" width="340" height="188" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('    <text x="1390" y="779" text-anchor="middle" font-family="monospace" font-size="26" font-weight="bold" fill="#303a36">func1, func2</text>')
    svg.append('  </g>')
    svg.append('')

    # Gap after steps = 40 px -> y = 865 + 40 = 905.
    # Extra strip (x: 40 to 1560, w: 1520, y: 905, h: 148, bottom: 1053)
    # Line 1 y = 938 (ttop = 938 - 19.2 = 918.8 -> T = 918.8 - 905 = 13.8 px -> let's make y = 942: T = 942 - 19.2 - 905 = 17.8 px >= 16!)
    # Line 2 dy = 28 -> y = 970
    # Line 3 dy = 28 -> y = 998
    # Line 4 dy = 28 -> y = 1026 -> tbot = 1026. Bottom padding = 1053 - 1026 = 27 px >= 16!
    svg.append('  <!-- Extra Strip -->')
    svg.append('  <g id="extra-strip">')
    svg.append('    <rect x="40" y="905" width="1520" height="148" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    svg.append('    <g transform="translate(65, 954)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="6" y="6" width="38" height="38" rx="5" fill="#ffffff" />')
    svg.append('      <line x1="14" y1="2" x2="14" y2="6" /><line x1="25" y1="2" x2="25" y2="6" /><line x1="36" y1="2" x2="36" y2="6" />')
    svg.append('      <line x1="14" y1="44" x2="14" y2="48" /><line x1="25" y1="44" x2="25" y2="48" /><line x1="36" y1="44" x2="36" y2="48" />')
    svg.append('      <line x1="2" y1="14" x2="6" y2="14" /><line x1="2" y1="25" x2="6" y2="25" /><line x1="2" y1="36" x2="6" y2="36" />')
    svg.append('      <line x1="44" y1="14" x2="48" y2="14" /><line x1="44" y1="25" x2="48" y2="25" /><line x1="44" y1="36" x2="48" y2="36" />')
    svg.append('    </g>')
    svg.append('    <text x="145" y="942" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="145" dy="0">Keep import-time work small: no network calls, config file reads, thread starts or </tspan>')
    svg.append('      <tspan x="145" dy="28">heavy imports at the top of a module; in command-line tools move a heavy import into </tspan>')
    svg.append('      <tspan x="145" dy="28">the function that needs it; measure with python -X importtime; module with </tspan>')
    svg.append('      <tspan x="145" dy="28">print(&quot;util loaded&quot;) shows side effects at import time: avoid in libraries</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('')

    # Gap after Extra Strip = 42 px -> y = 1053 + 42 = 1095.
    # Bottom bar (x: 40 to 1560, w: 1520, y: 1095, h: 60, bottom: 1155)
    # y = 1134 (ttop = 1134 - 26*0.8 = 1113.2 -> T = 1113.2 - 1095 = 18.2 px >= 16)
    # tbot = 1134 -> B = 1155 - 1134 = 21 px >= 16!
    svg.append('  <!-- Bottom Takeaway Bar -->')
    svg.append('  <g id="bottom-bar">')
    svg.append('    <rect x="40" y="1095" width="1520" height="60" rx="10" fill="#207448" />')
    svg.append('    <text x="800" y="1134" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">The name must exist by the time of the call, not by the time of the def</text>')
    svg.append('  </g>')
    svg.append('')
    svg.append('</svg>')
    return '\n'.join(svg)

svg_str = build_svg_string()
with open("test_candidate.svg", "w") as f:
    f.write(svg_str)

from audit_pad_strict import check_strict_paddings
check_strict_paddings("test_candidate.svg")
