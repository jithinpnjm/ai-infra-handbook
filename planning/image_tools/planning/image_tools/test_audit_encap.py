#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re
import pathlib
import asyncio
from playwright.async_api import async_playwright

svg_file = "planning/image_tools/test_encap.svg"
print(f"Auditing {svg_file}...")
tree = ET.parse(svg_file)
root = tree.getroot()

# 1. First children check: <title> and <desc>
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. First child: <{first_tag}>, Second child: <{second_tag}>")
assert first_tag == 'title', f"First child must be title, got {first_tag}"
assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"

# Title text check
title_text = "".join(children[0].itertext()).strip()
print(f"   Title text: '{title_text}'")
assert title_text == "Encapsulation overhead and ECMP entropy", f"Unexpected title text: {title_text}"

# 2. Dimensions
width = root.get('width')
viewBox = root.get('viewBox')
height = root.get('height')
print(f"2. Dimensions: width={width}, height={height}, viewBox={viewBox}")
assert width == "1600", f"Expected width 1600, got {width}"
assert viewBox.startswith("0 0 1600 "), f"viewBox must start with '0 0 1600 ', got {viewBox}"
vb_parts = [float(x) for x in viewBox.split()]
assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
assert 900 <= vb_parts[3] <= 1200, f"Height {vb_parts[3]} outside 900-1200 range"
assert int(height) == int(vb_parts[3]), f"height {height} != viewBox height {vb_parts[3]}"

# 3. Check font-size >= 24 on all text and tspans
text_elements = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = "".join(elem.itertext()).strip()
    full_text = re.sub(r'\s+', ' ', full_text)
    fs = elem.attrib.get('font-size')
    assert fs is not None, f"Missing font-size on text '{full_text}'"
    size = float(fs)
    assert size >= 24, f"Text '{full_text}' font-size {size} < 24!"
    for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
        tfs = tsp.attrib.get('font-size')
        if tfs is not None:
            assert float(tfs) >= 24, f"tspan font-size {tfs} < 24 in '{full_text}'"
    text_elements.append((full_text, size))

print(f"\n3. Total text elements: {len(text_elements)} (all font-sizes >= 24px)")
for i, (t, fs) in enumerate(text_elements, 1):
    print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

# 4. Expected labels
expected_labels = [
    "Encapsulation overhead and ECMP entropy",
    "Horizontal bar chart of overhead in bytes (IPv4 underlay)",
    "GRE 24 B",
    "IPIP 20 B",
    "VXLAN 50 B (outer Ethernet 14 + IP 20 + UDP 8 + VXLAN 8)",
    "GENEVE 50+ B",
    "MPLS 4 B per label",
    "WireGuard 60 B",
    "IPsec ESP about 50 to 73 B",
    "UDP-based: ECMP entropy from outer source port",
    "no ports: all traffic between two endpoints hashes to one path",
    "VXLAN is L2 over UDP/4789, GENEVE UDP/6081"
]

found_texts = [t for t, fs in text_elements]

print(f"\n4. Checking {len(expected_labels)} expected labels against {len(found_texts)} found:")
all_ok = True
for exp in expected_labels:
    cnt = found_texts.count(exp)
    ok = (cnt == 1)
    if not ok:
        all_ok = False
    print(f"   [{'OK' if ok else 'FAIL'}] count={cnt}: '{exp}'")

assert all_ok, "Some expected labels failed count == 1 check!"

extras = [t for t in found_texts if t not in expected_labels]
print(f"\n5. Extras count: {len(extras)}")
if extras:
    print("   Unexpected extras:", extras)
assert len(extras) == 0, f"Unexpected extra texts found: {extras}"
assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"

# 5. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for w in words:
        assert w not in forbidden, f"Forbidden word '{w}' found in text: '{t}'"

print("\n6. Forbidden words check: PASS!")

# 6. Check orange count
svg_str = pathlib.Path(svg_file).read_text(encoding="utf-8")
orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"\n7. Orange #db8129 occurrences: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 4, f"Unexpected orange count: {len(orange_matches)}"

# 7. Check arrows count
lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
total_arrows = len(lines) + len(paths)
print(f"\n8. Total arrows with marker-end: {total_arrows}")
assert total_arrows == 0, f"Expected 0 arrows, got {total_arrows}"

# 8. Check Playwright bounding box render
async def check_playwright():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1600, "height": 980})
        svg_url = pathlib.Path(svg_file).resolve().as_uri()
        await page.goto(svg_url)
        
        # Take a screenshot to /tmp/test_encap.png
        await page.screenshot(path="/tmp/test_encap.png")
        print("\n9. Screenshot saved to /tmp/test_encap.png")
        
        texts = await page.eval_on_selector_all("text", """elements => {
            return elements.map(el => {
                const rect = el.getBoundingClientRect();
                return {
                    text: el.textContent.trim(),
                    x: rect.x,
                    y: rect.y,
                    right: rect.right,
                    bottom: rect.bottom,
                    width: rect.width,
                    height: rect.height
                };
            });
        }""")
        
        print("\n10. Text bounding box validation:")
        for t in texts:
            print(f"   text: '{t['text']}' -> x={t['x']:.1f}, right={t['right']:.1f}, width={t['width']:.1f}")
            assert t['x'] >= 40, f"Text '{t['text']}' overflows left margin ({t['x']} < 40)"
            assert t['right'] <= 1560, f"Text '{t['text']}' overflows right margin ({t['right']} > 1560)"
            
        await browser.close()
        print("\nALL PLAYWRIGHT BOUNDING BOX CHECKS PASSED!")

asyncio.run(check_playwright())
print("\nALL AUDIT CHECKS PASSED PERFECTLY!")
