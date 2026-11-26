import xml.etree.ElementTree as ET
import re
import pathlib

svg_path = "candidate_429.svg"
print(f"=== Auditing {svg_path} ===")
tree = ET.parse(svg_path)
root = tree.getroot()

# 1. Structure check: First children must be title and desc
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. Structure check: First child <{first_tag}>, Second child <{second_tag}>")
assert first_tag == 'title', f"First child must be title, got {first_tag}"
assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"

# 2. Canvas size check
viewBox = root.attrib.get("viewBox")
width = root.attrib.get("width")
height = root.attrib.get("height")
print(f"2. Canvas: viewBox={viewBox}, width={width}, height={height}")
assert width == "1600", f"Expected width 1600, got {width}"
assert viewBox.startswith("0 0 1600 "), f"viewBox must start with '0 0 1600 ', got {viewBox}"
vb_parts = [float(x) for x in viewBox.split()]
assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
assert 900 <= vb_parts[3] <= 1200, f"Height {vb_parts[3]} outside 900..1200 range"
assert int(height) == int(vb_parts[3]), f"height {height} != viewBox height {vb_parts[3]}"
print("   Dimensions PASS!")

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
    print(f"   {i:2d}. [{fs:2.0f}px] '{t[:60]}...'")

# 4. Expected labels
expected_labels = [
    "The same 429 can be good or bad for the SLO",
    "gateway refused with 429 because the whole pool was full: your own capacity failed the customer: count as BAD",
    "gateway refused with 429 because the customer went past their own quota: the customer chose to exceed the agreed limit: count as NOT bad",
    "Both carry the same status code and land on opposite sides of the SLO; the cause label on the gateway counter separates them",
    "Dedicated endpoint: availability target such as 99.9 percent plus TTFT while traffic is within provisioned capacity; exclude load above the contracted capacity from the SLI; slice alerts per endpoint",
    "Serverless endpoint: looser latency targets with fairness limits and 429 responses as the control; count overload 429 as bad, quota 429 as not bad; slice alerts per model, tickets per tenant",
    "a customer sending 3 times their provisioned traffic and TTFT rising is not your breach",
    "table is the author's reasoning, Nebius has not published its SLO terms"
]

found_texts = [t for t, fs in text_elements]
print(f"\n4. Checking {len(expected_labels)} expected labels against {len(found_texts)} found:")
all_ok = True
for exp in expected_labels:
    cnt = found_texts.count(exp)
    ok = (cnt == 1)
    if not ok:
        all_ok = False
        print(f"   [FAIL] count={cnt}: '{exp}'")
    else:
        print(f"   [OK] '{exp[:50]}...'")

assert all_ok, "Some expected labels failed count == 1 check!"

extras = [t for t in found_texts if t not in expected_labels]
print(f"\nExtra texts: {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"
assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"
print("   Content fidelity: PASS!")

# 5. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"

print("\n5. No forbidden words found! (PASS)")

# 6. Check orange count
with open(svg_path, 'r', encoding='utf-8') as f:
    svg_str = f.read()
orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 6, f"Unexpected orange count: {len(orange_matches)}"
print("   Orange count: PASS!")

# 7. Check arrows count
lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
total_arrows = len(lines) + len(paths)
print(f"\n7. Total arrows with marker-end: {total_arrows}")
assert total_arrows == 0, f"Expected exactly 0 arrows, got {total_arrows}"
print("   Arrows count: PASS!")

# 8. Check colors present
for col in ["#f5f8f5", "#303a36", "#207448", "#e8f1ea", "#db8129"]:
    assert col in svg_str.lower(), f"Missing color {col}"
print("\n8. All required colors present! (PASS)")

# 9. Clearance and padding checks for text inside rects
cards = ['card-path-a', 'card-path-b', 'card-central-insight', 'card-dedicated-endpoint', 'card-serverless-endpoint', 'card-example', 'card-footer']

print("\n=== 9. Box clearances ===")
for cid in cards:
    g = root.find(f".//*[@id='{cid}']")
    rect = g.find('{http://www.w3.org/2000/svg}rect')
    bx = float(rect.attrib['x'])
    by = float(rect.attrib['y'])
    bw = float(rect.attrib['width'])
    bh = float(rect.attrib['height'])
    
    txt_elem = g.find('{http://www.w3.org/2000/svg}text')
    tspans = txt_elem.findall('{http://www.w3.org/2000/svg}tspan')
    fs = float(txt_elem.attrib.get('font-size', 24))
    tx = float(txt_elem.attrib.get('x', 0))
    ty = float(txt_elem.attrib.get('y', 0))
    anchor = txt_elem.attrib.get('text-anchor', 'start')
    
    curr_y = ty
    min_pad_l = 9999
    min_pad_r = 9999
    
    lines_to_check = []
    if tspans:
        for i, tsp in enumerate(tspans):
            dy = float(tsp.attrib.get('dy', 0))
            if i > 0:
                curr_y += dy
            t_text = "".join(tsp.itertext()).strip()
            t_fs = float(tsp.attrib.get('font-size', fs))
            t_len = len(t_text) * 0.6 * t_fs
            lines_to_check.append((t_text, t_fs, t_len, curr_y))
    else:
        t_text = "".join(txt_elem.itertext()).strip()
        t_len = len(t_text) * 0.6 * fs
        lines_to_check.append((t_text, fs, t_len, ty))
        
    top_y = lines_to_check[0][3] - lines_to_check[0][1]
    bot_y = lines_to_check[-1][3]
    pad_t = top_y - by
    pad_b = (by + bh) - bot_y
    
    for t_text, t_fs, t_len, ly in lines_to_check:
        if anchor == 'middle':
            lx1 = tx - t_len / 2
            lx2 = tx + t_len / 2
        else:
            lx1 = tx
            lx2 = tx + t_len
        pad_l = lx1 - bx
        pad_r = (bx + bw) - lx2
        min_pad_l = min(min_pad_l, pad_l)
        min_pad_r = min(min_pad_r, pad_r)
        
    print(f"{cid:25s}: pad_l={min_pad_l:5.1f} pad_r={min_pad_r:5.1f} pad_t={pad_t:5.1f} pad_b={pad_b:5.1f}")
    assert min_pad_l >= 16, f"{cid} min_pad_l {min_pad_l} < 16!"
    assert min_pad_r >= 16, f"{cid} min_pad_r {min_pad_r} < 16!"
    assert pad_t >= 16, f"{cid} pad_t {pad_t} < 16!"
    assert pad_b >= 16, f"{cid} pad_b {pad_b} < 16!"

print("\nALL CLEARANCES AND AUDIT CHECKS PASSED WITH FLYING COLORS!")
