#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

def create_svg():
    svg = []
    svg.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1170" width="1600" height="1170">')
    svg.append('  <title>Expressions: reading values out of the context</title>')
    svg.append('  <desc>Visual infographic explaining Jinja2 expressions, filing cabinet analogy for context access, list indexing, literals, operators, and string concatenation.</desc>')
    svg.append('')
    svg.append('  <!-- Canvas Background -->')
    svg.append('  <rect width="1600" height="1170" fill="#f5f8f5"/>')
    svg.append('')
    svg.append('  <!-- Title: 48px bold -->')
    svg.append('  <text x="800" y="58" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Expressions: reading values out of the context</text>')
    svg.append('')
    
    # ROW 1: Filing-cabinet analogy & Context access (left: x=40..780, w=740), Literals (right: x=820..1560, w=740)
    # Gap between them = 820 - 780 = 40px! Margins = 40px!
    # Height of Row 1 = 440px (y=95 to y=535)
    
    # ==================== ROW 1 LEFT: FILING-CABINET & ACCESS ====================
    # Container box
    svg.append('  <!-- ==================== LEFT PANEL: FILING CABINET ANALOGY ==================== -->')
    svg.append('  <g id="panel-context-access">')
    svg.append('    <rect x="40" y="95" width="740" height="440" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>')
    svg.append('')
    svg.append('    <!-- Filing Cabinet Outline Icon (56x56 px, stroke 4, green) -->')
    svg.append('    <g transform="translate(64, 115)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="6" y="4" width="44" height="48" rx="5"/>')
    svg.append('      <line x1="6" y1="20" x2="50" y2="20"/>')
    svg.append('      <line x1="6" y1="36" x2="50" y2="36"/>')
    svg.append('      <rect x="22" y="10" width="12" height="4" rx="1.5" fill="#207448"/>')
    svg.append('      <rect x="22" y="26" width="12" height="4" rx="1.5" fill="#207448"/>')
    svg.append('      <rect x="22" y="42" width="12" height="4" rx="1.5" fill="#207448"/>')
    svg.append('    </g>')
    svg.append('')
    
    # Filing Cabinet Visual Drawing: A drawer labelled "cluster" pulled out with a folder inside labelled "name"
    # Drawn in pure SVG shapes (no text other than the required labels!)
    svg.append('    <!-- Visual filing cabinet representation beside cards -->')
    svg.append('    <g transform="translate(136, 112)">')
    svg.append('      <!-- Top Drawer Structure -->')
    svg.append('      <rect x="0" y="0" width="620" height="110" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    svg.append('      <!-- Handle & Tab styling -->')
    svg.append('      <rect x="18" y="18" width="180" height="74" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
    svg.append('    </g>')
    
    # Label 2: cluster.name
    svg.append('    <text x="244" y="172" text-anchor="middle" font-family="monospace" font-size="28" font-weight="bold" fill="#207448">cluster.name</text>')
    
    # Label 3: opens the drawer cluster and takes the name folder
    svg.append('    <text x="495" y="157" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="495" dy="0">opens the drawer cluster </tspan>')
    svg.append('      <tspan x="495" dy="32">and takes the name folder</tspan>')
    svg.append('    </text>')
    svg.append('')
    
    # Sub-card 2: cluster["name"] and item form
    svg.append('    <!-- Item Access Card -->')
    svg.append('    <g transform="translate(64, 240)">')
    svg.append('      <rect x="0" y="0" width="692" height="110" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    svg.append('      <rect x="18" y="18" width="230" height="74" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
    svg.append('    </g>')
    # Label 4: cluster["name"]
    # XML encode quotes as &quot;
    svg.append('    <text x="197" y="300" text-anchor="middle" font-family="monospace" font-size="28" font-weight="bold" fill="#207448">cluster[&quot;name&quot;]</text>')
    # Label 5: item form
    svg.append('    <text x="500" y="300" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36">item form</text>')
    svg.append('')
    
    # Sub-card 3: lists and list[0], list[-1], list[1:3]
    svg.append('    <!-- Lists Card -->')
    svg.append('    <g transform="translate(64, 370)">')
    svg.append('      <rect x="0" y="0" width="692" height="142" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    svg.append('    </g>')
    # Label 6: lists (Section Title: 30px bold)
    svg.append('    <text x="94" y="414" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">lists</text>')
    
    # 3 mini badges for list items inside the lists card
    svg.append('    <rect x="88" y="434" width="200" height="60" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.8"/>')
    svg.append('    <text x="188" y="472" text-anchor="middle" font-family="monospace" font-size="26" font-weight="bold" fill="#207448">list[0]</text>')
    
    svg.append('    <rect x="310" y="434" width="200" height="60" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.8"/>')
    svg.append('    <text x="410" y="472" text-anchor="middle" font-family="monospace" font-size="26" font-weight="bold" fill="#207448">list[-1]</text>')
    
    svg.append('    <rect x="532" y="434" width="204" height="60" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.8"/>')
    svg.append('    <text x="634" y="472" text-anchor="middle" font-family="monospace" font-size="26" font-weight="bold" fill="#207448">list[1:3]</text>')
    svg.append('  </g>')
    svg.append('')
    
    # ==================== ROW 1 RIGHT: LITERALS ====================
    svg.append('  <!-- ==================== RIGHT PANEL: LITERALS ==================== -->')
    svg.append('  <g id="panel-literals">')
    svg.append('    <rect x="820" y="95" width="740" height="440" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>')
    svg.append('')
    svg.append('    <!-- Tag / Types Icon (56x56 px, stroke 4, green) -->')
    svg.append('    <g transform="translate(846, 115)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 12 6 L 34 6 L 48 20 L 26 42 L 12 28 Z"/>')
    svg.append('      <circle cx="22" cy="16" r="3.5" fill="#207448"/>')
    svg.append('      <path d="M 30 38 L 44 48 L 48 44"/>')
    svg.append('    </g>')
    svg.append('')
    # Label 10: Literals (Section Title: 30px bold)
    svg.append('    <text x="920" y="152" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Literals</text>')
    svg.append('')
    svg.append('    <!-- Literals content container -->')
    svg.append('    <rect x="846" y="188" width="688" height="324" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    svg.append('')
    # Label 11: strings, numbers, true and false (Python True and False also work), none, lists [1, 2], dicts {a: 1}, tuples
    # Let's wrap this onto 4 lines nicely inside width 688
    # Line 1: "strings, numbers, true and false " (33 chars)
    # Line 2: "(Python True and False also work), " (35 chars)
    # Line 3: "none, lists [1, 2], " (20 chars)
    # Line 4: "dicts {a: 1}, tuples" (20 chars)
    # Total characters: 104
    svg.append('    <text x="1190" y="270" text-anchor="middle" font-family="sans-serif" font-size="28" fill="#303a36">')
    svg.append('      <tspan x="1190" dy="0">strings, numbers, true and false </tspan>')
    svg.append('      <tspan x="1190" dy="48">(Python True and False also work), </tspan>')
    svg.append('      <tspan x="1190" dy="48">none, lists [1, 2], </tspan>')
    svg.append('      <tspan x="1190" dy="48">dicts {a: 1}, tuples</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('')
    
    # ==================== ROW 2: OPERATORS TABLE ====================
    # Gap from Row 1 = 575 - 535 = 40px!
    # Height of Row 2 = 305px (y=575 to y=880)
    svg.append('  <!-- ==================== ROW 2: OPERATORS TABLE ==================== -->')
    svg.append('  <g id="operators-table">')
    svg.append('    <rect x="40" y="575" width="1520" height="305" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>')
    svg.append('')
    svg.append('    <!-- Math / Operators Icon (56x56 px, stroke 4, green) -->')
    svg.append('    <g transform="translate(64, 595)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="6" y="6" width="44" height="44" rx="8"/>')
    svg.append('      <line x1="16" y1="20" x2="26" y2="20"/>')
    svg.append('      <line x1="21" y1="15" x2="21" y2="25"/>')
    svg.append('      <line x1="30" y1="20" x2="40" y2="20"/>')
    svg.append('      <line x1="16" y1="36" x2="26" y2="36"/>')
    svg.append('      <line x1="30" y1="33" x2="40" y2="33"/>')
    svg.append('      <line x1="30" y1="39" x2="40" y2="39"/>')
    svg.append('    </g>')
    svg.append('')
    
    # 2 columns x 3 rows of operator cards
    # Column 1: x=64, width=708
    # Column 2: x=828, width=708
    # Gap between columns = 828 - (64+708) = 56px
    # Row height: 62px, gap between rows: 14px
    # Row 1: y=660
    # Row 2: y=732
    # Row 3: y=804
    
    # Operator 1: arithmetic + - * / // % **
    svg.append('    <!-- Op Row 1, Col 1 -->')
    svg.append('    <rect x="64" y="660" width="708" height="60" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.8"/>')
    svg.append('    <text x="418" y="700" text-anchor="middle" font-family="monospace" font-size="26" font-weight="bold" fill="#303a36">arithmetic + - * / // % **</text>')
    
    # Operator 2: comparison == != < > <= >=
    # XML encode < and > as &lt; and &gt;
    svg.append('    <!-- Op Row 1, Col 2 -->')
    svg.append('    <rect x="828" y="660" width="708" height="60" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.8"/>')
    svg.append('    <text x="1182" y="700" text-anchor="middle" font-family="monospace" font-size="26" font-weight="bold" fill="#303a36">comparison == != &lt; &gt; &lt;= &gt;=</text>')
    
    # Operator 3: logic and or not
    svg.append('    <!-- Op Row 2, Col 1 -->')
    svg.append('    <rect x="64" y="732" width="708" height="60" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.8"/>')
    svg.append('    <text x="418" y="772" text-anchor="middle" font-family="monospace" font-size="26" font-weight="bold" fill="#303a36">logic and or not</text>')
    
    # Operator 4: membership in
    svg.append('    <!-- Op Row 2, Col 2 -->')
    svg.append('    <rect x="828" y="732" width="708" height="60" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.8"/>')
    svg.append('    <text x="1182" y="772" text-anchor="middle" font-family="monospace" font-size="26" font-weight="bold" fill="#303a36">membership in</text>')
    
    # Operator 5: conditional: {{ a if cond else b }}
    svg.append('    <!-- Op Row 3, Col 1 -->')
    svg.append('    <rect x="64" y="804" width="708" height="60" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.8"/>')
    svg.append('    <text x="418" y="844" text-anchor="middle" font-family="monospace" font-size="26" font-weight="bold" fill="#303a36">conditional: {{ a if cond else b }}</text>')
    
    # Operator 6: is applies a test
    svg.append('    <!-- Op Row 3, Col 2 -->')
    svg.append('    <rect x="828" y="804" width="708" height="60" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.8"/>')
    svg.append('    <text x="1182" y="844" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448">is applies a test</text>')
    svg.append('  </g>')
    svg.append('')
    
    # ==================== ROW 3: ORANGE CALLOUT ====================
    # Gap from Row 2 = 920 - 880 = 40px!
    # Height of Callout = 135px (y=920 to y=1055)
    svg.append('  <!-- ==================== ROW 3: ORANGE CALLOUT ==================== -->')
    svg.append('  <g id="callout-tilde">')
    svg.append('    <rect x="40" y="920" width="1520" height="135" rx="14" fill="#fff9f2" stroke="#db8129" stroke-width="3"/>')
    svg.append('')
    svg.append('    <!-- Tilde / String Join Icon in Orange (56x56 px, stroke 4, #db8129) -->')
    svg.append('    <g transform="translate(68, 958)" stroke="#db8129" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="28" cy="28" r="24"/>')
    svg.append('      <path d="M 16 28 C 18 20, 24 20, 28 28 C 32 36, 38 36, 40 28"/>')
    svg.append('    </g>')
    svg.append('')
    
    # Label 18: join strings with ~, not +: ~ always treats its operands as text so a node number of 1 joins cleanly as gpu ~ 1; + tries arithmetic first and mixing text with a number fails
    # Let's wrap onto 3 lines cleanly with trailing spaces in tspans
    # Line 1: "join strings with ~, not +: ~ always treats its operands as text "
    # Line 2: "so a node number of 1 joins cleanly as gpu ~ 1; "
    # Line 3: "+ tries arithmetic first and mixing text with a number fails"
    svg.append('    <text x="144" y="964" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="144" dy="0">join strings with ~, not +: ~ always treats its operands as text </tspan>')
    svg.append('      <tspan x="144" dy="32">so a node number of 1 joins cleanly as gpu ~ 1; </tspan>')
    svg.append('      <tspan x="144" dy="32">+ tries arithmetic first and mixing text with a number fails</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('')
    
    # ==================== ROW 4: BOTTOM TAKEAWAY BAR ====================
    # Gap from Callout = 1085 - 1055 = 30px, Bar height = 65px (y=1080 to y=1145)
    svg.append('  <!-- ==================== ROW 4: BOTTOM TAKEAWAY BAR ==================== -->')
    svg.append('  <g id="bottom-bar">')
    svg.append('    <rect x="40" y="1080" width="1520" height="65" rx="12" fill="#207448"/>')
    svg.append('    <g transform="translate(68, 1092)" stroke="#ffffff" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="20" cy="20" r="16"/>')
    svg.append('      <polyline points="12,20 18,26 28,14"/>')
    svg.append('    </g>')
    # Label 19: Use ~ to join text
    svg.append('    <text x="800" y="1123" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#ffffff">Use ~ to join text</text>')
    svg.append('  </g>')
    svg.append('</svg>')
    
    return "\n".join(svg)

content = create_svg()
with open("test_candidate_expressions.svg", "w") as f:
    f.write(content)
print("Wrote test_candidate_expressions.svg successfully!")
