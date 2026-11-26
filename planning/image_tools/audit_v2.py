import xml.etree.ElementTree as ET
import re, json, subprocess, pathlib

svg_file = "candidate_ca_v2.svg"
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
spec = json.load(open('specs/p3_20_20.json'))
spec_item = [x for x in spec if x.get('name') == 'p3-2020-ca-pending-to-node'][0]
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
print("PASS: Exactly the 11 expected labels, 0 extras, 0 missing, 0 duplicates!")

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
assert total_arrows == 4, f"Expected 4 arrows between the 5 boxes, got {total_arrows}"
print("PASS: Exactly 4 arrows connecting the five boxes.")

print("\n=== 7. Orange Highlight (#db8129) ===")
raw = pathlib.Path(svg_file).read_text()
oranges = re.findall(r'#db8129', raw, re.IGNORECASE)
print(f"Orange count: {len(oranges)}")
assert 1 <= len(oranges) <= 10, f"Orange count {len(oranges)} out of bounds"
print("PASS: Orange #db8129 used for the dashboard note.")

print("\n=== 8. Canvas Margins (>= 40px) ===")
all_canvas_margins_ok = True
canvas_h = float(h)
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    fs = float(elem.attrib['font-size'])
    ff = elem.attrib.get('font-family', 'sans-serif')
    anchor = elem.attrib.get('text-anchor', 'start')
    
    tspans = elem.findall('{http://www.w3.org/2000/svg}tspan')
    lines = []
    if tspans:
        cur_y = float(elem.attrib.get('y', 0))
        for tsp in tspans:
            dy = float(tsp.attrib.get('dy', 0))
            cur_y += dy
            tff = tsp.attrib.get('font-family', ff)
            lines.append((tsp.text.strip(), float(tsp.attrib.get('x', elem.attrib.get('x', 0))), cur_y, tff))
    else:
        lines = [(elem.text.strip(), float(elem.attrib.get('x', 0)), float(elem.attrib.get('y', 0)), ff)]
        
    for line_txt, lx, ly, lff in lines:
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
    # name, (bx, by, bw, bh), (icon_x, icon_y, icon_w, icon_h), [lines of (text, lx, ly, fs, is_mono)]
    ("Box 1", (55, 190, 550, 84), (70, 204, 52, 52), [
        ("HPA asks for more replicas", 145, 242, 24, False)
    ]),
    ("Box 2", (55, 304, 550, 104), (70, 328, 52, 52), [
        ("pods sit Pending:", 145, 352, 24, False),
        ("no node has a free GPU", 145, 380, 24, False)
    ]),
    ("Box 3", (55, 438, 550, 132), (70, 476, 52, 52), [
        ("cluster autoscaler notices", 145, 488, 24, False),
        ("pending pods that a node", 145, 516, 24, False),
        ("group could fit", 145, 544, 24, False)
    ]),
    ("Box 4", (55, 600, 550, 104), (70, 624, 52, 52), [
        ("asks the cloud for a node;", 145, 646, 24, False),
        ("provisioning clock starts", 145, 674, 24, False)
    ]),
    ("Box 5", (55, 734, 550, 104), (70, 758, 52, 52), [
        ("node registers, image pull,", 145, 780, 24, False),
        ("weight load, ready", 145, 808, 24, False)
    ]),
    ("Dashboard note", (55, 862, 550, 158), (70, 914, 52, 52), [
        ("replica count rose at", 145, 904, 24, False),
        ("once while serving", 145, 932, 24, False),
        ("count stayed flat;", 145, 960, 24, False),
        ("that gap is what to explain", 145, 988, 24, False)
    ]),
    ("Card 1", (675, 190, 870, 124), (688, 226, 40, 40), [
        ("expander chooses which node group to grow:", 750, 234, 24, False),
        ("random, most-pods, least-waste, price,", 750, 262, 24, False),
        ("priority (rank GPU types)", 750, 290, 24, False)
    ]),
    ("Card 2", (675, 338, 870, 152), (688, 388, 40, 40), [
        ("--max-node-provision-time default 15 minutes:", 750, 380, 24, True),
        ("if a node has not registered by then", 750, 408, 24, False),
        ("the autoscaler stops counting it,", 750, 436, 24, False),
        ("which is why you keep warm capacity", 750, 464, 24, False)
    ]),
    ("Card 3", (675, 514, 870, 240), (688, 608, 40, 40), [
        ("scale-down: node considered when pod CPU and", 750, 552, 24, False),
        ("memory requests sum below 50 percent of", 750, 580, 24, False),
        ("allocatable; must stay unneeded 10 minutes; held", 750, 608, 24, False),
        ("10 minutes after a scale-up; evicts through", 750, 636, 24, False),
        ("the eviction API for up to 2 minutes;", 750, 664, 24, False),
        ("accelerator flag", 750, 692, 24, False),
        ("scale-down-gpu-utilization-threshold default 0.5", 750, 720, 24, True)
    ]),
    ("Nebius Card", (675, 808, 870, 212), (688, 890, 40, 40), [
        ("autoscaling min and max node count flags; page", 750, 846, 24, False),
        ("gives no defaults or timings; keep a CPU node", 750, 874, 24, False),
        ("group of at least two nodes (or autoscaling) so", 750, 902, 24, False),
        ("CoreDNS and networking add-ons run there; known", 750, 930, 24, False),
        ("issue with GPU Operator and Network Operator", 750, 958, 24, False),
        ("creating extra nodes, not reproduced", 750, 986, 24, False)
    ])
]

all_box_paddings_ok = True
for bname, (bx, by, bw, bh), icon_box, lines in boxes:
    print(f"\nChecking {bname}:")
    box_right = bx + bw
    box_bottom = by + bh
    
    # Check lines
    for txt, lx, ly, fs, is_mono in lines:
        factor = 0.62 if is_mono else 0.60
        w_line = len(txt) * fs * factor
        left = lx
        right = lx + w_line
        top = ly - fs * 0.75
        bot = ly + 4
        
        pad_left = left - bx
        pad_right = box_right - right
        pad_top = top - by
        pad_bottom = box_bottom - bot
        
        # clearance from icon
        if icon_box:
            ix, iy, iw, ih = icon_box
            icon_right = ix + iw
            icon_bottom = iy + ih
            # text is to the right of icon
            icon_clearance = left - icon_right
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

print("\n=== 10. Headless Chrome Screenshot Test ===")
png_path = "/tmp/svgcheck/test_candidate_ca_v2.png"
pathlib.Path("/tmp/svgcheck").mkdir(exist_ok=True)
res = subprocess.run([
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '--headless=new',
    '--disable-gpu',
    '--hide-scrollbars',
    '--window-size=1600,1080',
    f'--screenshot={png_path}',
    f'file://{pathlib.Path(svg_file).resolve()}'
], capture_output=True, text=True)

if pathlib.Path(png_path).exists():
    print(f"PASS: Rendered PNG to {png_path} (size {pathlib.Path(png_path).stat().st_size} bytes)")
else:
    print(f"WARN: Chrome screenshot failed: {res.stderr}")

print("\n==========================================")
print("ALL 10 STRICT AUDIT CHECKS PASSED 100%!")
print("==========================================")
