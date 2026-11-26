import xml.etree.ElementTree as ET
import re

svg_path = "test_candidate_build2.svg"
tree = ET.parse(svg_path)
root = tree.getroot()

# 1. First children check: <title> and <desc>
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. First child: <{first_tag}>, Second child: <{second_tag}>")
assert first_tag == 'title', f"First child must be title, got {first_tag}"
assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"
assert children[0].text == "Reading data off the wire: decode, then deserialize"
assert children[1].text == "Reading data off the wire: decode, then deserialize"

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
    "Reading data off the wire: decode, then deserialize",
    "bytes arrive",
    'decode into a UTF-8 string, for example {"vendors":["Cisco","Juniper","Arista"]}',
    "deserialize with json.loads() into native structures: a Python dict and list",
    "serialize first",
    "encode",
    "Markup languages like HTML annotate documents for rendering; data serialization formats represent typed data structures across languages",
    'XML: tags, attributes, xmlns namespaces; query with XPath such as //device/model or //device[@name="leaf"]/model, or XQuery; validate with XSD (xmlschema)',
    "JSON: lighter; validate with JSON Schema: $schema https://json-schema.org/draft/2020-12/schema, minLength, maxLength, minimum 1, maximum 4094, IPv4 pattern regexes through jsonschema.validate()",
    "Protocol Buffers: binary, .proto files compiled with protoc, validated with protoc-gen-validate; FlatBuffers: read fields straight from the byte buffer; for high-throughput RPCs such as gRPC telemetry",
    "pickle: Python only, unsafe on untrusted bytes",
    "screen scraping show interfaces em0 breaks when a vendor changes the spacing; ask for structured output: show interfaces em0 | display xml, or JSON",
    "Network Programmability and Automation chapter 8",
    "Structured data beats fragile screen scraping"
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

# 5. Check forbidden style instruction words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"

print("\n6. No forbidden words found! (PASS)")

# 6. Check orange count
with open(svg_path, 'r', encoding='utf-8') as f:
    svg_str = f.read()
orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"\n7. Orange #db8129 occurrences: {len(orange_matches)}")
assert len(orange_matches) == 1, f"Expected exactly 1 orange match, got {len(orange_matches)}"

# 7. Check arrows count
lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
total_arrows = len(lines) + len(paths)
print(f"\n8. Total arrows with marker-end: {total_arrows}")
assert total_arrows == 3, f"Expected exactly 3 arrows, got {total_arrows}"

# 8. Check colors present
assert "#f5f8f5" in svg_str
assert "#303a36" in svg_str
assert "#207448" in svg_str
assert "#e8f1ea" in svg_str
print("\n9. Palette colors verified! (PASS)")

# 9. Strict paddings audit
print("\n10. Strict paddings audit:")
rects = []
for el in root.iter('{http://www.w3.org/2000/svg}rect'):
    rx = float(el.attrib.get('x', 0))
    ry = float(el.attrib.get('y', 0))
    rw = float(el.attrib.get('width', 0))
    rh = float(el.attrib.get('height', 0))
    if rw > 0 and rh > 0 and rw < 1600:
        rects.append((rx, ry, rx + rw, ry + rh, el))

pad_passed = True
for el in root.iter('{http://www.w3.org/2000/svg}text'):
    fs = float(el.attrib.get('font-size', 24))
    ff = el.attrib.get('font-family', 'sans-serif')
    anchor = el.attrib.get('text-anchor', 'start')
    rate = 0.62 if 'monospace' in ff else 0.60

    tspans = el.findall('{http://www.w3.org/2000/svg}tspan')
    if tspans:
        cur_y = float(el.attrib.get('y', 0))
        for ts in tspans:
            txt = ts.text or ""
            if not txt.strip():
                continue
            tx = float(ts.attrib.get('x', el.attrib.get('x', 0)))
            dy = float(ts.attrib.get('dy', 0))
            cur_y += dy
            tw = len(txt) * rate * fs
            if anchor == 'middle':
                tl = tx - tw / 2
                tr = tx + tw / 2
            else:
                tl = tx
                tr = tx + tw
            ttop = cur_y - fs * 0.8
            tbot = cur_y

            # Find smallest rect containing this line
            containing = [r for r in rects if r[0] <= tl and r[1] <= ttop and r[2] >= tr and r[3] >= tbot]
            if containing:
                containing.sort(key=lambda r: (r[2]-r[0])*(r[3]-r[1]))
                best = containing[0]
                pad_l = tl - best[0]
                pad_r = best[2] - tr
                pad_t = ttop - best[1]
                pad_b = best[3] - tbot
                if pad_l < 15.9 or pad_r < 15.9 or pad_t < 15.9 or pad_b < 15.9:
                    print(f"WARN padding: '{txt}' in rect {best[:4]}: L={pad_l:.1f}, R={pad_r:.1f}, T={pad_t:.1f}, B={pad_b:.1f}")
                    pad_passed = False
    else:
        txt = "".join(el.itertext()).strip()
        if not txt:
            continue
        tx = float(el.attrib.get('x', 0))
        ty = float(el.attrib.get('y', 0))
        tw = len(txt) * rate * fs
        if anchor == 'middle':
            tl = tx - tw / 2
            tr = tx + tw / 2
        else:
            tl = tx
            tr = tx + tw
        ttop = ty - fs * 0.8
        tbot = ty

        containing = [r for r in rects if r[0] <= tl and r[1] <= ttop and r[2] >= tr and r[3] >= tbot]
        if containing:
            containing.sort(key=lambda r: (r[2]-r[0])*(r[3]-r[1]))
            best = containing[0]
            pad_l = tl - best[0]
            pad_r = best[2] - tr
            pad_t = ttop - best[1]
            pad_b = best[3] - tbot
            if pad_l < 15.9 or pad_r < 15.9 or pad_t < 15.9 or pad_b < 15.9:
                print(f"WARN padding: '{txt}' in rect {best[:4]}: L={pad_l:.1f}, R={pad_r:.1f}, T={pad_t:.1f}, B={pad_b:.1f}")
                pad_passed = False

assert pad_passed, "Padding audit failed!"
print("Padding audit passed! (PASS)")

# 10. Check geometry (gaps >= 40, margins >= 40)
print("\n11. Geometry check (margins and gaps):")
vb = [float(x) for x in root.attrib['viewBox'].split()]
W, H = vb[2], vb[3]
panel_rects = []
for child in root:
    tag = child.tag.split('}')[-1]
    if tag == 'rect':
        w = float(child.attrib['width'])
        h = float(child.attrib['height'])
        if w == W and h == H:
            continue
        x = float(child.attrib['x'])
        y = float(child.attrib['y'])
        panel_rects.append({'x': x, 'y': y, 'w': w, 'h': h})
    elif tag == 'g':
        # check if it contains a top-level panel rect
        for gchild in child:
            gtag = gchild.tag.split('}')[-1]
            if gtag == 'rect':
                gw = float(gchild.attrib['width'])
                gh = float(gchild.attrib['height'])
                if gw >= 1000:
                    gx = float(gchild.attrib['x'])
                    gy = float(gchild.attrib['y'])
                    panel_rects.append({'x': gx, 'y': gy, 'w': gw, 'h': gh})
                    break

for i, r in enumerate(panel_rects, 1):
    left_m = r['x']
    right_m = W - (r['x'] + r['w'])
    top_m = r['y']
    bottom_m = H - (r['y'] + r['h'])
    print(f"  Box {i}: x={r['x']}, y={r['y']}, w={r['w']}, h={r['h']} -> margins: L={left_m}, R={right_m}, T={top_m}, B={bottom_m}")
    assert left_m >= 40, f"Box {i} left margin < 40"
    assert right_m >= 40, f"Box {i} right margin < 40"
    assert top_m >= 40, f"Box {i} top margin < 40"
    assert bottom_m >= 40, f"Box {i} bottom margin < 40"

for i in range(len(panel_rects)):
    for j in range(i + 1, len(panel_rects)):
        r1, r2 = panel_rects[i], panel_rects[j]
        v_overlap = max(0, min(r1['y'] + r1['h'], r2['y'] + r2['h']) - max(r1['y'], r2['y']))
        if v_overlap > 0:
            h_gap = max(r1['x'], r2['x']) - min(r1['x'] + r1['w'], r2['x'] + r2['w'])
            print(f"  Boxes {i+1} & {j+1} v_overlap={v_overlap:.1f}px -> h_gap={h_gap:.1f}px")
            assert h_gap >= 39.9, f"h_gap {h_gap} < 40 between boxes {i+1} and {j+1}"
            
        h_overlap = max(0, min(r1['x'] + r1['w'], r2['x'] + r2['w']) - max(r1['x'], r2['x']))
        if h_overlap > 0:
            v_gap = max(r1['y'], r2['y']) - min(r1['y'] + r1['h'], r2['y'] + r2['h'])
            print(f"  Boxes {i+1} & {j+1} h_overlap={h_overlap:.1f}px -> v_gap={v_gap:.1f}px")
            assert v_gap >= 39.9, f"v_gap {v_gap} < 40 between boxes {i+1} and {j+1}"

print("All panels satisfy >= 40px margins and >= 40px gaps! (PASS)")

print("\nALL CHECKS PASSED WITH FLYING COLORS!")
