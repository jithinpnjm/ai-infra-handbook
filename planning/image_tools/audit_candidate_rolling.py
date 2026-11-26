import re
import xml.etree.ElementTree as ET

tree = ET.parse("test_candidate.svg")
root = tree.getroot()

# 1. First children
tag1 = root[0].tag.split('}')[-1]
tag2 = root[1].tag.split('}')[-1]
print(f"1. First children: <{tag1}>, <{tag2}>")
assert tag1 == "title", f"Expected <title>, got <{tag1}>"
assert tag2 == "desc", f"Expected <desc>, got <{tag2}>"
print("   PASS: First children are <title> and <desc>")

# 2. Dimensions
w = root.attrib.get('width')
h = root.attrib.get('height')
vb = root.attrib.get('viewBox')
print(f"2. Dimensions: width={w}, height={h}, viewBox={vb}")
assert w == "1600"
assert vb.startswith("0 0 1600")
H = int(vb.split()[-1])
assert 900 <= H <= 1200
print("   PASS: Canvas dimensions and viewBox valid")

# 3. Text font sizes
full_texts = []
font_sizes = []
for el in root.iter('{http://www.w3.org/2000/svg}text'):
    fs = float(el.attrib.get('font-size', '0'))
    combined = " ".join("".join(el.itertext()).split())
    full_texts.append(combined)
    font_sizes.append((combined, fs))
    for ts in el.findall('{http://www.w3.org/2000/svg}tspan'):
        t_fs = float(ts.attrib.get('font-size', fs))
        t_content = " ".join("".join(ts.itertext()).split())
        if t_content:
            font_sizes.append((t_content, t_fs))

print(f"3. Text elements count: {len(full_texts)}")
for t, fs in font_sizes:
    assert fs >= 24, f"Font size {fs} < 24 for '{t}'"
print("   PASS: All text and tspan elements >= 24 px")

# 4. Banned style words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
found_banned = []
for ft in full_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', ft.lower())
    for f in forbidden:
        if f in words:
            found_banned.append((f, ft))
assert len(found_banned) == 0, f"Found banned style words: {found_banned}"
print("   PASS: Zero banned words printed as text")

# 5. Required source labels
source_labels = [
    "Restarting eight replicas at once leaves a zero-capacity gap",
    "70 billion parameters x 2 bytes = 140 GB; shared source 14 GB per second",
    "all eight restart together: 8 x 140 / 14 = 80 s each under the equal-share model, endpoint has no capacity during that window; retries in the gap make the first minute after recovery worse",
    "small groups, at least X+1 replicas keep serving; weights staged on local disk so the source stops being the shared bottleneck; one replica alone needs 10 s",
    "measure the load time in the startup log and use that number in your answer; saying you will measure first is more credible than a number you cannot defend; the gap is the window to plan for, not the steady state"
]

print("5. Checking source labels:")
for sl in source_labels:
    cnt = full_texts.count(sl)
    print(f"   '{sl[:45]}...': count = {cnt}")
    assert cnt == 1, f"Expected '{sl}' count=1, got {cnt}"

assert len(full_texts) == len(source_labels), f"Expected {len(source_labels)} text elements, got {len(full_texts)}: {set(full_texts) - set(source_labels)}"
print("   PASS: Exactly 5 source labels present, none duplicated, none invented!")

# 6. Orange usage
raw_svg = open("test_candidate.svg").read()
orange_matches = re.findall(r'#db8129', raw_svg, re.IGNORECASE)
print(f"6. Orange (#db8129) count: {len(orange_matches)}")
assert len(orange_matches) >= 1

timeline_a_elem = root.find('.//*[@id="timeline-a"]')
timeline_a_str = ET.tostring(timeline_a_elem, encoding="unicode")
timeline_a_oranges = re.findall(r'#db8129', timeline_a_str, re.IGNORECASE)
assert len(timeline_a_oranges) == len(orange_matches), "Orange must only be used on Timeline A (single most important item)"
print("   PASS: Orange strictly isolated to Timeline A")

# 7. Paddings and clearances inside boxes
# Check line widths inside containers
print("7. Testing text line widths:")
for el in root.iter('{http://www.w3.org/2000/svg}text'):
    fs = float(el.attrib.get('font-size', '24'))
    tspans = el.findall('{http://www.w3.org/2000/svg}tspan')
    if tspans:
        for ts in tspans:
            t = ts.text or ""
            t = t.strip()
            w = len(t) * 0.6 * fs
            print(f"   Line ({len(t):2d} chars, {w:.1f}px): '{t}'")
            assert w <= 1360, f"Line too wide: {w}px > 1360px"
    else:
        t = (el.text or "").strip()
        w = len(t) * 0.6 * fs
        print(f"   Line ({len(t):2d} chars, {w:.1f}px): '{t}'")
        assert w <= 1360, f"Line too wide: {w}px > 1360px"

print("   PASS: All text lines fit with conservative width factor 0.6")
print("\nALL AUDIT CHECKS PASSED PERFECTLY!")
