#!/usr/bin/env python3
import asyncio
import xml.etree.ElementTree as ET
from playwright.async_api import async_playwright

SVG_CONTENT = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1100" width="1600" height="1100">
  <title>BGP path attribute categories</title>
  <desc>Visual categorization of BGP path attributes into Well-known mandatory, Well-known discretionary, Optional transitive, and Optional non-transitive with meanings, examples, and note chips.</desc>

  <rect width="1600" height="1100" fill="#f5f8f5"/>

  <!-- Title -->
  <text x="50" y="80" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">BGP path attribute categories</text>

  <!-- Row 1: Well-known mandatory (Orange highlight: single most important item) -->
  <g id="row-well-known-mandatory">
    <rect x="50" y="130" width="1020" height="210" rx="16" fill="#e8f1ea" stroke="#db8129" stroke-width="4"/>
    
    <!-- Shield Icon (56x56 outline, stroke 4, orange #db8129) -->
    <g transform="translate(80, 165)" stroke="#db8129" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 28 6 L 50 14 V 30 C 50 44 28 54 28 54 C 28 54 6 44 6 30 V 14 Z"/>
      <line x1="28" y1="20" x2="28" y2="34"/>
      <circle cx="28" cy="42" r="2" fill="#db8129"/>
    </g>
    
    <text x="160" y="175" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Well-known mandatory</text>
    <text x="160" y="215" font-family="sans-serif" font-size="24" fill="#303a36">must be understood and present in every UPDATE</text>
    
    <!-- Examples -->
    <g transform="translate(160, 248)">
      <rect x="0" y="0" width="140" height="52" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <text x="70" y="34" font-family="monospace" font-size="24" fill="#303a36" text-anchor="middle">ORIGIN</text>

      <rect x="160" y="0" width="160" height="52" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <text x="240" y="34" font-family="monospace" font-size="24" fill="#303a36" text-anchor="middle">AS_PATH</text>

      <rect x="340" y="0" width="170" height="52" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <text x="425" y="34" font-family="monospace" font-size="24" fill="#303a36" text-anchor="middle">NEXT_HOP</text>
    </g>
  </g>

  <!-- Row 2: Well-known discretionary -->
  <g id="row-well-known-discretionary">
    <rect x="50" y="370" width="1020" height="210" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
    
    <!-- Checkbox Icon (56x56 outline, stroke 4, green #207448) -->
    <g transform="translate(80, 405)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="8" width="44" height="44" rx="8"/>
      <path d="M 16 30 L 25 39 L 40 18"/>
    </g>
    
    <text x="160" y="415" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Well-known discretionary</text>
    <text x="160" y="455" font-family="sans-serif" font-size="24" fill="#303a36">understood, may be omitted</text>
    
    <!-- Examples -->
    <g transform="translate(160, 488)">
      <rect x="0" y="0" width="200" height="52" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <text x="100" y="34" font-family="monospace" font-size="24" fill="#303a36" text-anchor="middle">LOCAL_PREF</text>

      <rect x="220" y="0" width="290" height="52" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <text x="365" y="34" font-family="monospace" font-size="24" fill="#303a36" text-anchor="middle">ATOMIC_AGGREGATE</text>
    </g>
  </g>

  <!-- Note Chip 1: LOCAL_PREF -->
  <g id="note-local-pref">
    <rect x="1100" y="370" width="450" height="210" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <text x="1130" y="435" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan font-family="monospace">LOCAL_PREF: </tspan><tspan>higher wins,</tspan>
      <tspan x="1130" dy="42">default 100,</tspan>
      <tspan x="1130" dy="42">travels only inside an AS</tspan>
    </text>
  </g>

  <!-- Row 3: Optional transitive -->
  <g id="row-optional-transitive">
    <rect x="50" y="610" width="1020" height="210" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
    
    <!-- Share/Transit Icon (56x56 outline, stroke 4, green #207448) -->
    <g transform="translate(80, 645)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="16" cy="28" r="8"/>
      <circle cx="40" cy="14" r="8"/>
      <circle cx="40" cy="42" r="8"/>
      <line x1="23" y1="24" x2="33" y2="18"/>
      <line x1="23" y1="32" x2="33" y2="38"/>
    </g>
    
    <text x="160" y="655" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Optional transitive</text>
    <text x="160" y="695" font-family="sans-serif" font-size="24" fill="#303a36">passed along if unknown</text>
    
    <!-- Examples -->
    <g transform="translate(160, 728)">
      <rect x="0" y="0" width="180" height="52" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <text x="90" y="34" font-family="monospace" font-size="24" fill="#303a36" text-anchor="middle">COMMUNITY</text>

      <rect x="200" y="0" width="200" height="52" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <text x="300" y="34" font-family="monospace" font-size="24" fill="#303a36" text-anchor="middle">AGGREGATOR</text>

      <rect x="420" y="0" width="270" height="52" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <text x="555" y="34" font-family="monospace" font-size="24" fill="#303a36" text-anchor="middle">Large Community</text>
    </g>
  </g>

  <!-- Row 4: Optional non-transitive -->
  <g id="row-optional-non-transitive">
    <rect x="50" y="850" width="1020" height="210" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
    
    <!-- Funnel/Drop Icon (56x56 outline, stroke 4, green #207448) -->
    <g transform="translate(80, 885)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 8 12 L 48 12 L 32 30 V 46 L 24 40 V 30 Z"/>
    </g>
    
    <text x="160" y="895" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Optional non-transitive</text>
    <text x="160" y="935" font-family="sans-serif" font-size="24" fill="#303a36">dropped if not understood</text>
    
    <!-- Examples -->
    <g transform="translate(160, 968)">
      <rect x="0" y="0" width="100" height="52" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <text x="50" y="34" font-family="monospace" font-size="24" fill="#303a36" text-anchor="middle">MED</text>

      <rect x="120" y="0" width="245" height="52" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <text x="242" y="34" font-family="monospace" font-size="24" fill="#303a36" text-anchor="middle">ORIGINATOR_ID</text>

      <rect x="385" y="0" width="235" height="52" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <text x="502" y="34" font-family="monospace" font-size="24" fill="#303a36" text-anchor="middle">CLUSTER_LIST</text>
    </g>
  </g>

  <!-- Note Chip 2: MED -->
  <g id="note-med">
    <rect x="1100" y="850" width="450" height="210" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <text x="1130" y="960" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan font-family="monospace">MED: </tspan><tspan>lower wins</tspan>
    </text>
  </g>
</svg>'''

async def main():
    with open("test_bgp_attrs.svg", "w") as f:
        f.write(SVG_CONTENT)
    print("Wrote test_bgp_attrs.svg")

    # XML checks
    root = ET.fromstring(SVG_CONTENT)
    assert root[0].tag.endswith("title"), "First child must be title"
    assert root[1].tag.endswith("desc"), "Second child must be desc"
    print("Passed title & desc check")

    # Collect all text strings from all text and tspan elements
    texts = []
    for elem in root.iter('{http://www.w3.org/2000/svg}text'):
        # iterate text
        full = "".join(elem.itertext()).strip()
        texts.append(full)
    print(f"Total <text> elements: {len(texts)}")
    for t in texts:
        print(f" - {t}")

    # Check font sizes
    for elem in root.iter('{http://www.w3.org/2000/svg}text'):
        fs = float(elem.attrib.get("font-size", 0))
        assert fs >= 24, f"Font size {fs} < 24!"
    print("Passed font size check (>= 24 everywhere)")

    # Run Playwright to check actual rendered text bounds and padding
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(f"file://{__import__('os').path.abspath('test_bgp_attrs.svg')}")
        
        # Take screenshot for visual inspection
        await page.screenshot(path="test_bgp_attrs.png")
        print("Took screenshot test_bgp_attrs.png")

        # Check all bounding boxes inside boxes
        # Check that canvas has 40px margin
        text_nodes = await page.query_selector_all("text")
        for node in text_nodes:
            box = await node.bounding_box()
            txt = await node.text_content()
            # Check margins
            assert box['x'] >= 40, f"Text '{txt}' x={box['x']} < 40 margin"
            assert box['x'] + box['width'] <= 1560, f"Text '{txt}' right={box['x'] + box['width']} > 1560"
            assert box['y'] >= 0, f"Text '{txt}' y={box['y']} < 0"
            assert box['y'] + box['height'] <= 1100, f"Text '{txt}' bottom={box['y'] + box['height']} > 1100"

        await browser.close()
    print("ALL CHECKS PASSED!")

if __name__ == "__main__":
    asyncio.run(main())
