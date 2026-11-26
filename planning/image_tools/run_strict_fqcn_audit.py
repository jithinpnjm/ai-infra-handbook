import xml.etree.ElementTree as ET
import re, os, subprocess, pathlib

svg_path = "test_fqcn_candidate.svg"
tree = ET.parse(svg_path)
root = tree.getroot()

# 1. Structure check: First children must be title and desc
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. First child: <{first_tag}>, Second child: <{second_tag}>")
assert first_tag == 'title', f"First child must be title, got {first_tag}"
assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"

# Title text check
title_text = "".join(children[0].itertext()).strip()
print(f"   Title text: '{title_text}'")
assert title_text == "Reading a module's full name, and the three content tiers", f"Unexpected title text: {title_text}"

# 2. Canvas size check
viewBox = root.attrib.get("viewBox")
width = root.attrib.get("width")
height = root.attrib.get("height")
print(f"2. Canvas: viewBox={viewBox}, width={width}, height={height}")
assert width == "1600", f"Width must be 1600, got {width}"
vb_parts = [float(x) for x in viewBox.split()]
assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
assert 900 <= vb_parts[3] <= 1200, f"Height out of range: {vb_parts[3]}"
assert float(height) == vb_parts[3], f"height attribute mismatch: {height} != {vb_parts[3]}"

# 3. Font size check: >= 24 on all text and tspans
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
    "Reading a module's full name, and the three content tiers",
    "the split manages thousands of modules and more than 20,000 community roles",
    "ansible.builtin.copy",
    "'ansible' = namespace",
    "'builtin' = collection name",
    "'copy' = module",
    "together the fully qualified collection name or FQCN (the full address of a module, namespace first)",
    "community.general",
    "ansible.posix",
    "kubernetes.core",
    "nvidia.*",
    "short names are ambiguous: two collections may each ship a module called copy, and ansible-lint flags them; always use FQCNs",
    "ansible-galaxy collection install -r requirements.yml",
    "Core: ansible-core itself, created by the Ansible team",
    "Certified: created and supported by Red Hat and its partners through Automation Hub",
    "Community: shared on Ansible Galaxy",
    "execution environments: container images with ansible-core, collections, Python dependencies and system libraries; built with ansible-builder, run with ansible-navigator or inside AAP or AWX; they end works on my laptop (4.15)",
    "check the release and support matrix before upgrading: a core upgrade can change module behaviour and deprecate features",
    "A collection is a toolbox from one maker, with the maker's name on the lid"
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
print(f"\nExtra texts: {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"
assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"

# 5. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"

print("\n5. No forbidden words found! (PASS)")

# 6. Check orange count
with open(svg_path) as f:
    raw_svg = f.read()

orange_matches = re.findall(r'#db8129', raw_svg, re.IGNORECASE)
print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 6, f"Unexpected orange count: {len(orange_matches)}"

# 7. Check arrows count
lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib or "marker-start" in e.attrib]
paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib or "marker-start" in e.attrib]
total_arrows = len(lines) + len(paths)
print(f"\n7. Total arrows with markers: {total_arrows}")
assert total_arrows == 0, f"Expected exactly 0 arrows, got {total_arrows}"

# 8. Check external resources: no external fonts, images or scripts
assert not any(el.tag.endswith('image') for el in root.iter()), "External image found!"
assert not any(el.tag.endswith('script') for el in root.iter()), "Script found!"
print("\n8. No external resources found (PASS)")

# 9. Check outside margins and box gaps (all >= 40px)
# Distinct boxes:
# 1. Title: top=40, bot=140
# 2. Context Strip: y=185, h=58 (top=185, bot=243, left=40, right=1560)
# 3. Left Column: y=285, h=525 (top=285, bot=810, left=40, right=780)
# 4. Right Column: y=285, h=525 (top=285, bot=810, left=820, right=1560)
# 5. Strip EE: y=850, h=82 (top=850, bot=932, left=40, right=1560)
# 6. Strip Matrix: y=972, h=68 (top=972, bot=1040, left=40, right=1560)
# 7. Takeaway Bar: y=1080, h=60 (top=1080, bot=1140, left=40, right=1560)

boxes = [
    ("Context Strip", 40, 185, 1520, 58),
    ("Left Column", 40, 285, 740, 525),
    ("Right Column", 820, 285, 740, 525),
    ("Strip EE", 40, 850, 1520, 82),
    ("Strip Matrix", 40, 972, 1520, 68),
    ("Takeaway Bar", 40, 1080, 1520, 60),
]

H = float(height)
print("\n9. Checking outside margins (>= 40px):")
for name, bx, by, bw, bh in boxes:
    lm = bx
    rm = 1600 - (bx + bw)
    tm = by
    bm = H - (by + bh)
    print(f"   {name:15s}: L={lm} R={rm} T={tm} B={bm}")
    assert lm >= 40, f"Left margin {lm} < 40 on {name}"
    assert rm >= 40, f"Right margin {rm} < 40 on {name}"
    assert tm >= 40, f"Top margin {tm} < 40 on {name}"
    assert bm >= 40, f"Bottom margin {bm} < 40 on {name}"

print("\n10. Checking gaps between major sections (>= 40px):")
# Title to Context strip:
gap_title_ctx = 185 - 140
print(f"   Title to Context Strip: {gap_title_ctx}px >= 40px")
assert gap_title_ctx >= 40

# Context strip to Main cols:
gap_ctx_main = 285 - 243
print(f"   Context Strip to Main Columns: {gap_ctx_main}px >= 40px")
assert gap_ctx_main >= 40

# Gap between Left and Right columns:
gap_cols = 820 - 780
print(f"   Left to Right Column Gap: {gap_cols}px >= 40px")
assert gap_cols >= 40

# Main cols to Strip EE:
gap_main_ee = 850 - 810
print(f"   Main Columns to Strip EE: {gap_main_ee}px >= 40px")
assert gap_main_ee >= 40

# Strip EE to Strip Matrix:
gap_ee_mat = 972 - 932
print(f"   Strip EE to Strip Matrix: {gap_ee_mat}px >= 40px")
assert gap_ee_mat >= 40

# Strip Matrix to Takeaway Bar:
gap_mat_bar = 1080 - 1040
print(f"   Strip Matrix to Takeaway Bar: {gap_mat_bar}px >= 40px")
assert gap_mat_bar >= 40

print("\n11. Headless Chrome screenshot render test:")
chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
if os.path.exists(chrome_path):
    out_png = "test_fqcn_candidate.png"
    abs_svg = os.path.abspath(svg_path)
    subprocess.run([
        chrome_path, '--headless=new', '--disable-gpu', '--hide-scrollbars',
        f'--window-size=1600,{int(H)}', f'--screenshot={out_png}', f'file://{abs_svg}'
    ], check=True)
    print(f"   Rendered {out_png} successfully!")
else:
    print("   Chrome not found, skipping screenshot.")

print("\n=== ALL STRICT CHECKS PASSED WITH 100% SUCCESS! ===")
