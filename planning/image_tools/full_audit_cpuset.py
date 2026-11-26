import re
import xml.etree.ElementTree as ET
import asyncio
from playwright.async_api import async_playwright
import pathlib

svg_path = "test_candidate_cpuset.svg"
tree = ET.parse(svg_path)
root = tree.getroot()

print("=== 1. STRUCTURE AND HEADERS ===")
children = list(root)
t0 = children[0].tag.split('}')[-1]
t1 = children[1].tag.split('}')[-1]
assert t0 == 'title', f"Child 0 must be <title>, got <{t0}>"
assert t1 == 'desc', f"Child 1 must be <desc>, got <{t1}>"
print(f"Child 0: <{t0}> -> '{children[0].text}'")
print(f"Child 1: <{t1}> -> '{children[1].text}'")

width = root.get('width')
height = root.get('height')
viewBox = root.get('viewBox')
print(f"Dimensions: width={width}, height={height}, viewBox={viewBox}")
assert width == "1600", f"Width must be 1600, got {width}"
assert height == "1200", f"Height must be 1200, got {height}"
assert viewBox == "0 0 1600 1200", f"viewBox must be '0 0 1600 1200', got {viewBox}"

print("\n=== 2. TEXT FONT SIZES ===")
text_elements = []
for el in root.iter('{http://www.w3.org/2000/svg}text'):
    fs = float(el.attrib.get('font-size', '0'))
    combined = " ".join("".join(el.itertext()).split())
    assert fs >= 24, f"Text '{combined}' font-size {fs} < 24!"
    for ts in el.findall('{http://www.w3.org/2000/svg}tspan'):
        tfs = float(ts.attrib.get('font-size', fs))
        assert tfs >= 24, f"tspan in '{combined}' font-size {tfs} < 24!"
    text_elements.append((combined, fs))

print(f"Total text elements: {len(text_elements)} (all font-sizes >= 24px)")

print("\n=== 3. EXPECTED CONTENT LABELS ===")
expected_labels = [
    # Title
    "cpuset says where, quota says how much, weight says how fairly",
    # Column 1
    "cpuset: where may it run?",
    "cpuset.cpus and cpuset.mems (effective values in cpuset.cpus.effective and cpuset.mems.effective)",
    "a hard allow-list, no throttling; an empty cpuset.cpus inherits the parent's",
    "a job that must run on cores 4 to 7; Slurm task/cgroup and the Kubernetes CPU Manager use cpusets for exclusive cores",
    # Column 2
    "quota (cpu.max): how much time?",
    "cpu.max = $MAX $PERIOD in microseconds (200000 100000 = 2 CPUs worth)",
    "a job that may run on any cores as long as it gets 4 CPUs worth of time",
    # Column 3
    "weight (cpu.weight): how fairly under contention?",
    "cpu.weight 1 to 10000, default 100; v1 cpu.shares default 1024",
    "invisible on an idle machine, never wastes capacity, never limits alone; Kubernetes CPU request becomes shares or weight",
    # Bottom strip
    "v2 partitions: cpuset.cpus.partition set to root or isolated makes a group with exclusive CPUs, a runtime alternative to isolcpus",
    # Bottom bar
    "Choose placement, ceiling or proportion by what the job needs"
]

found_texts = [t for t, fs in text_elements]
for idx, exp in enumerate(expected_labels, 1):
    cnt = found_texts.count(exp)
    assert cnt == 1, f"Label {idx} '{exp}' found {cnt} times (expected exactly 1)!"
    print(f"  [PASS] Label {idx:2d} (count=1): '{exp[:50]}...'")

print(f"\nAll {len(expected_labels)} content labels matched exactly once!")

print("\n=== 4. EXTRAS AND FORBIDDEN WORDS ===")
all_allowed = set(expected_labels)
extras = [t for t in found_texts if t not in all_allowed]
assert len(extras) == 0, f"Unexpected extra text: {extras}"
assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"
print("PASS: Zero unexpected extra text elements.")

forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"
print("PASS: No forbidden style words in any text element.")

print("\n=== 5. ORANGE COLOR USAGE ===")
svg_str = open(svg_path).read()
oranges = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"Orange #db8129 count: {len(oranges)}")
assert len(oranges) == 1, f"Orange count {len(oranges)} != 1 (must be used exactly once on cpuset column)!"
print("PASS: Orange #db8129 used exactly once on cpuset column.")

print("\n=== 6. PLAYWRIGHT BOUNDING BOX AUDIT ===")
async def run_playwright_audit():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1600, "height": 1200})
        svg_url = pathlib.Path(svg_path).resolve().as_uri()
        await page.goto(svg_url)
        await page.screenshot(path="test_candidate_cpuset.png")
        print("Saved screenshot to test_candidate_cpuset.png")

        # Get all text elements bounding rects
        results = await page.eval_on_selector_all("text", """elements => {
            return elements.map(el => {
                const r = el.getBoundingClientRect();
                return {
                    text: el.textContent.replace(/\\s+/g, ' ').trim(),
                    x: r.x,
                    y: r.y,
                    width: r.width,
                    height: r.height,
                    right: r.right,
                    bottom: r.bottom
                };
            });
        }""")

        # Get all rect bounding rects
        rect_boxes = await page.eval_on_selector_all("rect", """elements => {
            return elements.map(el => {
                const r = el.getBoundingClientRect();
                return {
                    id: el.id || el.getAttribute('id') || '',
                    x: r.x,
                    y: r.y,
                    width: r.width,
                    height: r.height,
                    right: r.right,
                    bottom: r.bottom,
                    fill: el.getAttribute('fill'),
                    stroke: el.getAttribute('stroke')
                };
            });
        }""")

        await browser.close()

        print(f"\nRendered {len(results)} text bounding boxes:")
        for i, res in enumerate(results, 1):
            print(f"  {i:2d}. [{res['width']:.1f} x {res['height']:.1f} at ({res['x']:.1f}, {res['y']:.1f}) right={res['right']:.1f}] '{res['text'][:40]}...'")
            # Check canvas margins (40px)
            assert res['x'] >= 40, f"Text '{res['text'][:30]}' x={res['x']} < 40!"
            assert res['right'] <= 1560, f"Text '{res['text'][:30]}' right={res['right']} > 1560!"
            assert res['y'] >= 40, f"Text '{res['text'][:30]}' y={res['y']} < 40!"
            assert res['bottom'] <= 1160, f"Text '{res['text'][:30]}' bottom={res['bottom']} > 1160!"

        # Check box paddings: find corresponding card rect for each text
        print("\nVerifying padding inside enclosing cards:")
        # For each card text, find enclosing card rect:
        for res in results:
            # find smallest rect containing this text box with some tolerance
            containing_rects = []
            for rb in rect_boxes:
                # ignore canvas rect (width 1600, height 1200)
                if rb['width'] >= 1590:
                    continue
                # check if rb contains res
                if rb['x'] <= res['x'] + 2 and rb['right'] >= res['right'] - 2 and rb['y'] <= res['y'] + 2 and rb['bottom'] >= res['bottom'] - 2:
                    containing_rects.append(rb)
            
            if containing_rects:
                # pick smallest by area
                containing_rects.sort(key=lambda r: r['width'] * r['height'])
                enc = containing_rects[0]
                pad_l = res['x'] - enc['x']
                pad_r = enc['right'] - res['right']
                pad_t = res['y'] - enc['y']
                pad_b = enc['bottom'] - res['bottom']
                print(f"  Text '{res['text'][:25]}...' inside rect w={enc['width']:.0f},h={enc['height']:.0f}: pads: left={pad_l:.1f}, right={pad_r:.1f}, top={pad_t:.1f}, bottom={pad_b:.1f}")
                assert pad_l >= 14, f"Pad left {pad_l} < 14 for '{res['text'][:30]}'"
                assert pad_r >= 14, f"Pad right {pad_r} < 14 for '{res['text'][:30]}'"
                assert pad_t >= 14, f"Pad top {pad_t} < 14 for '{res['text'][:30]}'"
                assert pad_b >= 14, f"Pad bottom {pad_b} < 14 for '{res['text'][:30]}'"

        print("\nALL PLAYWRIGHT CHECKS PASSED PERFECTLY!")

asyncio.run(run_playwright_audit())
