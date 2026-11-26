import xml.etree.ElementTree as ET
import asyncio
from playwright.async_api import async_playwright
import os

def build_svg():
    H = 1200
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 {H}" width="1600" height="{H}">')
    svg.append('  <title>Two methods in, a whole sequence out: NodeInventory and Fleet</title>')
    svg.append('  <desc>Visual infographic demonstrating how implementing __len__ and __getitem__ provides complete sequence behaviors for NodeInventory, contrasted with abc.Sequence inheritance in Fleet.</desc>')
    svg.append('')
    
    # Defs: marker for arrow
    svg.append('  <defs>')
    svg.append('    <marker id="arrowhead" markerWidth="16" markerHeight="12" refX="16" refY="6" orient="auto">')
    svg.append('      <polygon points="0 0, 16 6, 0 12" fill="#207448" />')
    svg.append('    </marker>')
    svg.append('  </defs>')
    svg.append('')
    
    # Canvas Background
    svg.append('  <!-- Canvas Background -->')
    svg.append(f'  <rect width="1600" height="{H}" fill="#f5f8f5" />')
    svg.append('')
    
    # Title (48px bold)
    # y = 40 to 115
    svg.append('  <!-- Title -->')
    svg.append('  <text x="800" y="62" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">')
    svg.append('    <tspan x="800" dy="0">Two methods in, a whole sequence out: </tspan>')
    svg.append('    <tspan x="800" dy="52">NodeInventory and Fleet</tspan>')
    svg.append('  </text>')
    svg.append('')
    
    # Left column: x = 40 to 460 (w = 420)
    # Box 1 (Left box, orange highlight): y = 155 to 445 (h = 290)
    svg.append('  <!-- Left Box: You write only __len__ and __getitem__ (orange) -->')
    svg.append('  <g id="left-box">')
    svg.append('    <rect x="40" y="155" width="420" height="290" rx="16" fill="#fff7f0" stroke="#db8129" stroke-width="3" />')
    # Icon: Python code brackets / method contract (56x56 at x=222, y=185)
    svg.append('    <g transform="translate(222, 185)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="2" y="2" width="52" height="52" rx="10" fill="#ffffff" />')
    svg.append('      <polyline points="18,20 10,28 18,36" />')
    svg.append('      <polyline points="38,20 46,28 38,36" />')
    svg.append('      <line x1="30" y1="16" x2="26" y2="40" />')
    svg.append('    </g>')
    svg.append('    <text x="250" y="300" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">')
    svg.append('      <tspan x="250" dy="0">You write only</tspan>')
    svg.append('      <tspan x="250" dy="44">__len__ and</tspan>')
    svg.append('      <tspan x="250" dy="44">__getitem__</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('')
    
    # Box 2 (Second box: Fleet): y = 485 to 885 (h = 400)
    # Gap from Box 1: 485 - 445 = 40 px!
    svg.append('  <!-- Second Box: Fleet(abc.Sequence) -->')
    svg.append('  <g id="second-box-fleet">')
    svg.append('    <rect x="40" y="485" width="420" height="400" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    # Icon: Abstract Base Class inheritance hierarchy (56x56 at x=222, y=515)
    svg.append('    <g transform="translate(222, 515)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="14" y="2" width="28" height="20" rx="4" fill="#ffffff" />')
    svg.append('      <line x1="28" y1="22" x2="28" y2="34" />')
    svg.append('      <line x1="12" y1="34" x2="44" y2="34" />')
    svg.append('      <line x1="12" y1="34" x2="12" y2="42" />')
    svg.append('      <line x1="44" y1="34" x2="44" y2="42" />')
    svg.append('      <rect x="2" y="42" width="20" height="14" rx="3" fill="#ffffff" />')
    svg.append('      <rect x="34" y="42" width="20" height="14" rx="3" fill="#ffffff" />')
    svg.append('    </g>')
    svg.append('    <text x="250" y="630" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="250" dy="0">index, count, iteration,</tspan>')
    svg.append('      <tspan x="250" dy="36">in, reversed come from</tspan>')
    svg.append('      <tspan x="250" dy="36">the base class;</tspan>')
    svg.append('      <tspan x="250" dy="36">__getitem__ returns Fleet</tspan>')
    svg.append('      <tspan x="250" dy="36">for a slice</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('')
    
    # Arrow from Left box to the Column of Behaviours:
    # From (460, 300) to (700, 300), length = 240 px
    svg.append('  <!-- Arrow to column of behaviours: you get for free -->')
    svg.append('  <g id="arrow-free">')
    svg.append('    <line x1="460" y1="300" x2="700" y2="300" stroke="#207448" stroke-width="4" marker-end="url(#arrowhead)" />')
    svg.append('    <text x="580" y="280" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">you get for free</text>')
    svg.append('  </g>')
    svg.append('')
    
    # Right container (Column of behaviours): x = 700 to 1560 (w = 860, y = 155 to 885, h = 730)
    svg.append('  <!-- Right Container: Column of behaviours -->')
    svg.append('  <g id="right-container">')
    svg.append('    <rect x="700" y="155" width="860" height="730" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    
    # Row 1 (y = 168, h = 96):
    # Card 1 (Item 1): "len(inv) is 52"
    svg.append('    <!-- Card 1: len(inv) is 52 -->')
    svg.append('    <rect x="720" y="168" width="400" height="96" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="920" y="224" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#303a36">len(inv) is 52</text>')
    
    # Card 5 (Item 5): "inv[:3] first three nodes"
    svg.append('    <!-- Card 5: inv[:3] first three nodes -->')
    svg.append('    <rect x="1140" y="168" width="400" height="96" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="1340" y="210" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="1340" dy="0" font-family="monospace" font-weight="bold">inv[:3]</tspan>')
    svg.append('      <tspan x="1340" dy="30">first three nodes</tspan>')
    svg.append('    </text>')
    
    # Row 2 (y = 274, h = 96, gap = 10):
    # Card 2 (Item 2): "inv[0] == Node(slot=01, rack=r1)"
    svg.append('    <!-- Card 2: inv[0] == Node(slot=01, rack=r1) -->')
    svg.append('    <rect x="720" y="274" width="400" height="96" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="920" y="316" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="920" dy="0" font-weight="bold">inv[0] ==</tspan>')
    svg.append('      <tspan x="920" dy="30">Node(slot=01, rack=r1)</tspan>')
    svg.append('    </text>')
    
    # Card 3 (Item 3): "inv[-1] == Node(slot=13, rack=r4)"
    svg.append('    <!-- Card 3: inv[-1] == Node(slot=13, rack=r4) -->')
    svg.append('    <rect x="1140" y="274" width="400" height="96" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="1340" y="316" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="1340" dy="0" font-weight="bold">inv[-1] ==</tspan>')
    svg.append('      <tspan x="1340" dy="30">Node(slot=13, rack=r4)</tspan>')
    svg.append('    </text>')
    
    # Row 3 (y = 380, h = 96, gap = 10):
    # Card 4 (Item 4): "choice(inv) random selection"
    svg.append('    <!-- Card 4: choice(inv) random selection -->')
    svg.append('    <rect x="720" y="380" width="400" height="96" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="920" y="422" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="920" dy="0" font-family="monospace" font-weight="bold">choice(inv)</tspan>')
    svg.append('      <tspan x="920" dy="30">random selection</tspan>')
    svg.append('    </text>')
    
    # Card 7 (Item 7): "for node in inv and reversed(inv)"
    svg.append('    <!-- Card 7: for node in inv and reversed(inv) -->')
    svg.append('    <rect x="1140" y="380" width="400" height="96" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="1340" y="422" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="1340" dy="0">for node in inv</tspan>')
    svg.append('      <tspan x="1340" dy="30">and reversed(inv)</tspan>')
    svg.append('    </text>')
    
    # Row 4 (y = 486, h = 148, gap = 10):
    # Card 6 (Item 6): "inv[12::13] slot 13 of every rack: start at index 12, step 13"
    svg.append('    <!-- Card 6: inv[12::13] slot 13 of every rack: start at index 12, step 13 -->')
    svg.append('    <rect x="720" y="486" width="400" height="148" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="920" y="534" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="920" dy="0" font-family="monospace" font-weight="bold">inv[12::13] </tspan><tspan font-family="sans-serif">slot 13 of</tspan>')
    svg.append('      <tspan x="920" dy="30">every rack: start at</tspan>')
    svg.append('      <tspan x="920" dy="30">index 12, step 13</tspan>')
    svg.append('    </text>')
    
    # Card 8 (Item 8): "Node(07, r2) in inv is True, Node(07, r9) in inv is False (a sequential scan)"
    svg.append('    <!-- Card 8: Node(07, r2) in inv is True, Node(07, r9) in inv is False (a sequential scan) -->')
    svg.append('    <rect x="1140" y="486" width="400" height="148" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="1340" y="524" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="1340" dy="0">Node(07, r2) in inv</tspan>')
    svg.append('      <tspan x="1340" dy="28">is True, Node(07, r9)</tspan>')
    svg.append('      <tspan x="1340" dy="28">in inv is False</tspan>')
    svg.append('      <tspan x="1340" dy="28">(a sequential scan)</tspan>')
    svg.append('    </text>')
    
    # Row 5 (y = 644, h = 152, gap = 10, wide w = 820):
    # Card 9 (Item 9): sorted(inv, key=drain_order)...
    svg.append('    <!-- Card 9: sorted(inv, key=drain_order)... -->')
    svg.append('    <rect x="720" y="644" width="820" height="152" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="1130" y="683" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="1130" dy="0">sorted(inv, key=drain_order): slot position times the</tspan>')
    svg.append('      <tspan x="1130" dy="28">number of racks plus rack priority from RACK_PRIORITY</tspan>')
    svg.append('      <tspan x="1130" dy="28">= r4:3, r3:2, r2:1, r1:0, so slot 01 of r1 ranks 0 and</tspan>')
    svg.append('      <tspan x="1130" dy="28">slot 13 of r4 ranks 51</tspan>')
    svg.append('    </text>')
    
    # Row 6 (y = 806, h = 68, gap = 10, wide w = 820):
    # Card 10 (Item 10): random.shuffle(inv) needs __setitem__
    svg.append('    <!-- Card 10: random.shuffle(inv) needs __setitem__ (not free) -->')
    svg.append('    <rect x="720" y="806" width="820" height="68" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" stroke-dasharray="6,4" />')
    svg.append('    <text x="1130" y="848" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#303a36">random.shuffle(inv) needs __setitem__</text>')
    svg.append('  </g>')
    svg.append('')
    
    # Footnote panel: x = 40, y = 925, w = 1520, h = 130
    # Gap from Right container: 925 - 885 = 40 px!
    svg.append('  <!-- Footnote Panel -->')
    svg.append('  <g id="footnote-panel">')
    svg.append('    <rect x="40" y="925" width="1520" height="130" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    # Icon: Document / standard library reference (56x56 at x=70, y=962)
    svg.append('    <g transform="translate(70, 962)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="4" y="2" width="48" height="52" rx="6" fill="#ffffff" />')
    svg.append('      <line x1="14" y1="16" x2="42" y2="16" />')
    svg.append('      <line x1="14" y1="28" x2="42" y2="28" />')
    svg.append('      <line x1="14" y1="40" x2="30" y2="40" />')
    svg.append('    </g>')
    svg.append('    <text x="160" y="966" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="160" dy="0">for built-in list or str, len(x) reads a size field in the C structure directly</tspan>')
    svg.append('      <tspan x="160" dy="32">in constant time; collections.abc: Iterable needs __iter__, Sized needs __len__,</tspan>')
    svg.append('      <tspan x="160" dy="32">Container needs __contains__; Sequence, Mapping and Set specialise them</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('')
    
    # Bottom bar (takeaway): x = 40, y = 1095, w = 1520, h = 65
    # Gap from Footnote: 1095 - 1055 = 40 px!
    # Bottom margin: 1200 - 1160 = 40 px!
    svg.append('  <!-- Bottom Takeaway Bar -->')
    svg.append('  <g id="bottom-bar">')
    svg.append('    <rect x="40" y="1095" width="1520" height="65" rx="10" fill="#207448" />')
    svg.append('    <text x="800" y="1136" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">Anything with the right methods plugs in</text>')
    svg.append('  </g>')
    svg.append('')
    
    svg.append('</svg>')
    return '\n'.join(svg)

svg_str = build_svg()
with open("test_perfect.svg", "w") as f:
    f.write(svg_str)

# Test rendered paddings with Playwright:
boxes = {
    2: (40, 155, 420, 290, "Left box"),
    3: (40, 485, 420, 400, "Second box Fleet"),
    5: (720, 168, 400, 96, "Card 1"),
    6: (1140, 168, 400, 96, "Card 5"),
    7: (720, 274, 400, 96, "Card 2"),
    8: (1140, 274, 400, 96, "Card 3"),
    9: (720, 380, 400, 96, "Card 4"),
    10: (1140, 380, 400, 96, "Card 7"),
    11: (720, 486, 400, 148, "Card 6"),
    12: (1140, 486, 400, 148, "Card 8"),
    13: (720, 644, 820, 152, "Card 9"),
    14: (720, 806, 820, 68, "Card 10"),
    15: (40, 925, 1520, 130, "Footnote"),
    16: (40, 1095, 1520, 65, "Bottom bar")
}

async def check():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width': 1600, 'height': 1200})
        cwd = os.getcwd()
        svg_url = f'file://{cwd}/test_perfect.svg'
        await page.goto(svg_url)
        
        text_elems = await page.query_selector_all('text')
        all_passed = True
        for i, el in enumerate(text_elems, 1):
            if i not in boxes:
                continue
            bx, by, bw, bh, name = boxes[i]
            tb = await el.bounding_box()
            pad_left = tb['x'] - bx
            pad_right = (bx + bw) - (tb['x'] + tb['width'])
            pad_top = tb['y'] - by
            pad_bottom = (by + bh) - (tb['y'] + tb['height'])
            
            min_pad = min(pad_left, pad_right, pad_top, pad_bottom)
            ok = min_pad >= 16.0
            if not ok:
                all_passed = False
            status = "PASS" if ok else "FAIL"
            print(f"[{status}] {name:20s}: L={pad_left:4.1f}, R={pad_right:4.1f}, T={pad_top:4.1f}, B={pad_bottom:4.1f} | min={min_pad:4.1f} px")
            
        await browser.close()
        return all_passed

passed = asyncio.run(check())
print("\nOverall Padding Result:", "ALL PASS" if passed else "FAILED")
