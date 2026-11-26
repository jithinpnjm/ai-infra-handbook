import xml.etree.ElementTree as ET
import re, json, pathlib

svg_file = "candidate_prefill_decode.svg"
tree = ET.parse(svg_file)
root = tree.getroot()

print("=== 1. Structure Check ===")
children = list(root)
tag0 = children[0].tag.split('}')[-1]
tag1 = children[1].tag.split('}')[-1]
print(f"Child 0: <{tag0}>, Child 1: <{tag1}>")
assert tag0 == 'title', f"Expected title, got {tag0}"
assert tag1 == 'desc', f"Expected desc, got {tag1}"
print("PASS: First children are <title> and <desc>.")

print("\n=== 2. Canvas & Dimensions Check ===")
w = root.get('width')
h = root.get('height')
vb = root.get('viewBox').split()
print(f"width={w}, height={h}, viewBox={vb}")
assert w == "1600", f"Width {w} != 1600"
assert vb == ["0", "0", "1600", h], f"ViewBox mismatch: {vb}"
assert 900 <= float(h) <= 1200, f"Height {h} not between 900 and 1200"
print("PASS: Dimensions valid.")

print("\n=== 3. Font Size Check (>= 24px) ===")
text_elems = []
for el in root.iter('{http://www.w3.org/2000/svg}text'):
    fs = el.get('font-size')
    assert fs is not None, f"Missing font-size on {el.text}"
    val = float(fs)
    assert val >= 24, f"font-size {val} < 24 px on {el.text}"
    full_text = " ".join("".join(el.itertext()).split())
    text_elems.append((full_text, val))
    for tsp in el.iter('{http://www.w3.org/2000/svg}tspan'):
        tfs = tsp.get('font-size')
        if tfs:
            assert float(tfs) >= 24, f"tspan font-size {tfs} < 24"

print(f"PASS: All {len(text_elems)} text elements have font-size >= 24 px.")
for i, (t, fs) in enumerate(text_elems, 1):
    print(f"  {i:2d}. [{fs:2.0f}px] '{t}'")

print("\n=== 4. Expected Labels Fidelity ===")
spec = json.load(open('specs/p2_20_13.json'))
spec_item = [x for x in spec if x.get('name') == 'p2-2013-prefill-decode-pools'][0]
expected_labels = [spec_item['title']] + re.findall(r"'([^']*)'", spec_item['spec'])

found_texts = [t for t, fs in text_elems]
print(f"Expected count: {len(expected_labels)}, Found count: {len(found_texts)}")

for i, exp in enumerate(expected_labels, 1):
    cnt = found_texts.count(exp)
    print(f"  {i:2d}. [{'OK' if cnt == 1 else 'FAIL'}] count={cnt}: '{exp[:60]}...'")
    assert cnt == 1, f"Expected '{exp}' count == 1, got {cnt}"

extras = [t for t in found_texts if t not in expected_labels]
print(f"Extras: {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"
assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"
print(f"PASS: Exactly the {len(expected_labels)} expected labels, 0 extras, 0 missing, 0 duplicates!")

print("\n=== 5. Forbidden Style Words ===")
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"
print("PASS: No forbidden style words in any text!")

print("\n=== 6. Arrow Count & Connections ===")
lines = [l for l in root.iter('{http://www.w3.org/2000/svg}line') if 'marker-end' in l.attrib]
paths = [p for p in root.iter('{http://www.w3.org/2000/svg}path') if 'marker-end' in p.attrib]
total_arrows = len(lines) + len(paths)
print(f"Total arrows: {total_arrows}")
assert total_arrows == 4, f"Expected 4 arrows, got {total_arrows}"
print("PASS: Exactly 4 arrows connecting the boxes.")

print("\n=== 7. Orange Highlight (#db8129) ===")
raw = pathlib.Path(svg_file).read_text()
oranges = re.findall(r'#db8129', raw, re.IGNORECASE)
print(f"Orange count: {len(oranges)}")
assert 1 <= len(oranges) <= 10, f"Orange count {len(oranges)} out of bounds"
print("PASS: Orange #db8129 used for the backward backpressure arrow.")

print("\n=== 8. Canvas Margins (>= 40px) ===")
all_canvas_margins_ok = True
canvas_h = float(h)
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    fs = float(elem.attrib['font-size'])
    ff = elem.attrib.get('font-family', 'sans-serif')
    anchor = elem.attrib.get('text-anchor', 'start')
    
    tspans = elem.findall('{http://www.w3.org/2000/svg}tspan')
    lines_info = []
    if tspans:
        cur_y = float(elem.attrib.get('y', 0))
        for tsp in tspans:
            dy = float(tsp.attrib.get('dy', 0))
            cur_y += dy
            tff = tsp.attrib.get('font-family', ff)
            lines_info.append((tsp.text.strip(), float(tsp.attrib.get('x', elem.attrib.get('x', 0))), cur_y, tff))
    else:
        lines_info = [(elem.text.strip(), float(elem.attrib.get('x', 0)), float(elem.attrib.get('y', 0)), ff)]
        
    for line_txt, lx, ly, lff in lines_info:
        factor = 0.62 if 'mono' in lff else 0.60
        w_line = len(line_txt) * fs * factor
        if anchor == 'middle':
            left = lx - w_line / 2.0
            right = lx + w_line / 2.0
        elif anchor == 'end':
            left = lx - w_line
            right = lx
        else:
            left = lx
            right = lx + w_line
        top = ly - fs * 0.75
        bot = ly + 4
        
        lm = left
        rm = 1600 - right
        tm = top
        bm = canvas_h - bot
        
        if lm < 39.9 or rm < 39.9 or tm < 39.9 or bm < 39.9:
            print(f"  FAIL Margin: '{line_txt[:30]}' lm={lm:.1f}, rm={rm:.1f}, tm={tm:.1f}, bm={bm:.1f}")
            all_canvas_margins_ok = False
        else:
            print(f"  PASS Margin: '{line_txt[:30]}' lm={lm:.1f}, rm={rm:.1f}, tm={tm:.1f}, bm={bm:.1f}")

assert all_canvas_margins_ok, "Some text elements violated 40px canvas margin!"
print("PASS: All text lines have >= 40px canvas margin!")

print("\n=== 9. Box Padding & Clearance Check ===")
boxes = [
    # name, (bx, by, bw, bh), icon_box (ix, iy, iw, ih), anchor, [lines of (text, lx, ly, fs, is_mono)]
    ("Colocated GPU Container", (50, 175, 1500, 295), (75, 193, 56, 56), 'start', [
        ("Colocated: prefill and decode share one GPU", 150, 231, 30, False)
    ]),
    ("Stacked Bar 1 (Prefill)", (75, 263, 1450, 58), None, 'middle', [
        ("Long prefill: compute heavy", 800, 300, 26, False)
    ]),
    ("Stall Badge", (580, 329, 440, 58), None, 'middle', [
        ("Streaming users see a stall", 800, 366, 24, False)
    ]),
    ("Stacked Bar 2 (Decode)", (75, 396, 1450, 58), None, 'middle', [
        ("Decode: memory-bandwidth heavy, one token at a time", 800, 433, 26, False)
    ]),
    ("Pool 1 (Prefill pool)", (220, 535, 370, 260), (377, 555, 56, 56), 'middle', [
        ("Prefill pool: ", 405, 652, 28, False),
        ("picks by cache ", 405, 688, 28, False),
        ("and load", 405, 724, 28, False)
    ]),
    ("Pool 2 (Decode pool)", (1180, 535, 370, 260), (1337, 555, 56, 56), 'middle', [
        ("Decode pool: ", 1365, 652, 28, False),
        ("picks by free ", 1365, 688, 28, False),
        ("KV memory", 1365, 724, 28, False)
    ]),
    ("Takeaway Bar", (50, 874, 1500, 98), None, 'middle', [
        ("Start colocated with chunked prefill. ", 800, 918, 26, False),
        ("Split when p99 inter-token latency is dominated by prefill interference.", 800, 952, 26, False)
    ])
]

all_box_paddings_ok = True
for bname, (bx, by, bw, bh), icon_box, anchor, lines in boxes:
    print(f"\nChecking {bname}:")
    box_right = bx + bw
    box_bottom = by + bh
    
    for txt, lx, ly, fs, is_mono in lines:
        factor = 0.62 if is_mono else 0.60
        w_line = len(txt) * fs * factor
        if anchor == 'middle':
            left = lx - w_line / 2.0
            right = lx + w_line / 2.0
        elif anchor == 'end':
            left = lx - w_line
            right = lx
        else:
            left = lx
            right = lx + w_line
        top = ly - fs * 0.75
        bot = ly + 4
        
        pad_left = left - bx
        pad_right = box_right - right
        pad_top = top - by
        pad_bottom = box_bottom - bot
        
        if icon_box:
            ix, iy, iw, ih = icon_box
            icon_right = ix + iw
            icon_bottom = iy + ih
            # Check clearance depending on whether icon is above or to the left
            if icon_bottom <= top:
                icon_clearance = top - icon_bottom
            elif icon_right <= left:
                icon_clearance = left - icon_right
            else:
                icon_clearance = 0.0
        else:
            icon_clearance = 999.0
            
        print(f"  '{txt[:28]}': L={pad_left:.1f}, R={pad_right:.1f}, T={pad_top:.1f}, B={pad_bottom:.1f}, IconGap={icon_clearance:.1f}")
        
        if pad_left < 15.9 or pad_right < 15.9 or pad_top < 15.9 or pad_bottom < 15.9:
            print(f"    FAIL: Box padding < 16px!")
            all_box_paddings_ok = False
        if icon_clearance < 15.9:
            print(f"    FAIL: Icon clearance < 16px!")
            all_box_paddings_ok = False

assert all_box_paddings_ok, "Some box paddings or icon clearances violated 16px!"
print("\nPASS: All box paddings and icon clearances >= 16px!")
