import re
import xml.etree.ElementTree as ET

tree = ET.parse("planning/image_tools/test_generated_accept.svg")
root = tree.getroot()

# 1. First children check: <title> and <desc>
tag1 = root[0].tag.split('}')[-1]
tag2 = root[1].tag.split('}')[-1]
print(f"1. First children: <{tag1}>, <{tag2}>")
assert tag1 == "title", f"First child must be <title>, got <{tag1}>"
assert tag2 == "desc", f"Second child must be <desc>, got <{tag2}>"
print("PASS: First children are <title> and <desc>")

# 2. Canvas dimensions and viewBox
vb = root.attrib.get("viewBox", "").split()
w = root.attrib.get("width")
h = root.attrib.get("height")
print(f"2. Canvas: width={w}, height={h}, viewBox={vb}")
assert float(w) == 1600, f"Width {w} != 1600"
assert 900 <= float(h) <= 1200, f"Height {h} not in [900, 1200]"
assert float(vb[2]) == 1600, f"viewBox width {vb[2]} != 1600"
assert float(vb[3]) == float(h), f"viewBox height {vb[3]} != height {h}"
print("PASS: Canvas dimensions are correct")

# 3. Minimum font size >= 24
text_font_sizes = []
for elem in root.iter():
    if elem.tag.endswith('text') or elem.tag.endswith('tspan'):
        fs = elem.attrib.get('font-size')
        if fs:
            text_font_sizes.append(float(fs))
print(f"3. Font sizes in text/tspan: min={min(text_font_sizes)}, max={max(text_font_sizes)}")
assert min(text_font_sizes) >= 24, f"Found font-size {min(text_font_sizes)} < 24!"
print("PASS: No text smaller than 24 px")

# 4. Forbidden style words check
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
text_nodes = []
for elem in root.iter():
    if elem.tag.endswith('text'):
        full = "".join(elem.itertext()).strip()
        full = re.sub(r'\s+', ' ', full)
        text_nodes.append(full)

print(f"\nExtracted {len(text_nodes)} text nodes:")
for i, t in enumerate(text_nodes, 1):
    print(f"  {i:2d}: '{t}'")

found_banned = []
for t in text_nodes:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        if f in words:
            found_banned.append((f, t))
assert len(found_banned) == 0, f"Found banned style words: {found_banned}"
print("PASS: Zero banned style words printed as text")

# 5. Required content labels check
raw_svg = open("planning/image_tools/test_generated_accept.svg").read()
cleaned_text = ' '.join(re.sub(r'<[^>]+>', ' ', raw_svg).split())
cleaned_text = cleaned_text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")

required_labels = [
    "Socket activation: Accept=true versus Accept=false",
    "Client connects to port 22222",
    "echo.socket: ListenStream=22222 (systemd holds the listening socket)",
    "Accept=true",
    "systemd itself calls accept() for each connection",
    "it starts a NEW instance per connection named 'echo@<n>-<local>-<peer>.service'",
    "the service file is a template 'echo@.service' with 'StandardInput=socket' and 'ExecStart=/bin/cat'",
    "the connection is the service's standard input and output so it does not need to know it is a network",
    "suits only simple services",
    "Accept=false (default)",
    "systemd passes the LISTENING socket to one service 'echo.service' (not a template)",
    "the service calls accept() itself and keeps control until it exits",
    "it receives the descriptor in $LISTEN_FDS starting at descriptor 3 through sd_listen_fds()",
    "real servers that understand socket activation use this form",
    "sudo systemctl start echo.socket",
    "ss -ltn | grep 22222",
    "echo hi | nc localhost 22222",
    "systemctl list-sockets",
    "With Accept=false the service must support the handoff"
]

print("\n--- Verifying Required Content Labels ---")
for req in required_labels:
    norm_req = ' '.join(req.split())
    assert norm_req in cleaned_text, f"Missing required label in SVG: '{norm_req}'"
    cnt = text_nodes.count(norm_req)
    assert cnt == 1, f"Expected '{norm_req}' to appear exactly once in text nodes, got {cnt}!"

print("PASS: All 19 required labels present and appear exactly once in text nodes!")

# 6. Colors check
palette = ["#f5f8f5", "#303a36", "#207448", "#e8f1ea", "#db8129"]
for c in palette:
    assert c in raw_svg, f"Required color {c} missing from SVG!"
print("PASS: All required palette colors present")

# 7. Check arrow marker usage
arrow_elements = [el for el in root.iter() if 'marker-end' in el.attrib]
print(f"Arrow elements with marker-end: {len(arrow_elements)}")
assert len(arrow_elements) == 9

# 8. Exact padding checks (horizontal and vertical >= 16px)
def get_line_width(text, font_size, font_family):
    is_mono = "monospace" in font_family
    rate = 0.62 if is_mono else 0.6
    return len(text) * font_size * rate

groups = root.findall('.//{http://www.w3.org/2000/svg}g')
failed_pad = False

for g in groups:
    gid = g.attrib.get('id', '')
    rect = g.find('{http://www.w3.org/2000/svg}rect')
    texts = g.findall('{http://www.w3.org/2000/svg}text')
    if rect is not None and texts:
        rx = float(rect.attrib['x'])
        ry = float(rect.attrib['y'])
        rw = float(rect.attrib['width'])
        rh = float(rect.attrib['height'])
        
        all_tops = []
        all_bottoms = []
        for text in texts:
            t_ff = text.attrib.get('font-family', 'sans-serif')
            t_fs = float(text.attrib.get('font-size', '24'))
            tspans = text.findall('{http://www.w3.org/2000/svg}tspan')
            
            if tspans:
                curr_y = float(text.attrib.get('y', '0'))
                for ts in tspans:
                    ts_text = (ts.text or "").strip()
                    if not ts_text:
                        continue
                    ts_x = float(ts.attrib.get('x', text.attrib.get('x', '0')))
                    ts_dy = float(ts.attrib.get('dy', '0'))
                    curr_y += ts_dy
                    ts_fs = float(ts.attrib.get('font-size', t_fs))
                    ts_ff = ts.attrib.get('font-family', t_ff)
                    lw = get_line_width(ts_text, ts_fs, ts_ff)
                    
                    left_pad = ts_x - rx
                    right_pad = (rx + rw) - (ts_x + lw)
                    all_tops.append(curr_y - ts_fs)
                    all_bottoms.append(curr_y)
                    
                    if left_pad < 15.9 or right_pad < 15.9:
                        print(f"[FAIL PAD X] in {gid}: line '{ts_text}' lw={lw:.1f}, left={left_pad:.1f}, right={right_pad:.1f}")
                        failed_pad = True
            else:
                txt = "".join(text.itertext()).strip()
                tx = float(text.attrib.get('x', '0'))
                ty = float(text.attrib.get('y', '0'))
                lw = get_line_width(txt, t_fs, t_ff)
                anchor = text.attrib.get('text-anchor', 'start')
                if anchor == 'middle':
                    left_pad = (tx - lw / 2) - rx
                    right_pad = (rx + rw) - (tx + lw / 2)
                else:
                    left_pad = tx - rx
                    right_pad = (rx + rw) - (tx + lw)
                all_tops.append(ty - t_fs)
                all_bottoms.append(ty)
                if left_pad < 15.9 or right_pad < 15.9:
                    print(f"[FAIL PAD X] in {gid}: text '{txt}' lw={lw:.1f}, left={left_pad:.1f}, right={right_pad:.1f}")
                    failed_pad = True
                    
        min_top = min(all_tops)
        max_bottom = max(all_bottoms)
        top_pad = min_top - ry
        bottom_pad = (ry + rh) - max_bottom
        if top_pad < 15.9 or bottom_pad < 15.9:
            print(f"[FAIL PAD Y] in {gid}: top={top_pad:.1f}, bottom={bottom_pad:.1f}")
            failed_pad = True
        else:
            print(f"[OK PADDING] in {gid}: top={top_pad:.1f}, bottom={bottom_pad:.1f}")

assert not failed_pad, "Padding checks failed!"
print("PASS: All padding checks passed (>= 16px)!")

# 9. Check step 4 vs dashed note gap in Accept=true lane
l1_node4_rect = root.find('.//*[@id="l1-node-4"]/{http://www.w3.org/2000/svg}rect')
l1_note_rect = root.find('.//*[@id="l1-note"]/{http://www.w3.org/2000/svg}rect')
n4_bottom = float(l1_node4_rect.attrib['y']) + float(l1_node4_rect.attrib['height'])
note_top = float(l1_note_rect.attrib['y'])
gap = note_top - n4_bottom
print(f"Gap between Step 4 and dashed note in Accept=true: {gap} px")
assert gap >= 20, f"Gap {gap} < 20 px!"
print("PASS: Step 4 and dashed note have clean separation (gap >= 20px)!")

print("\nALL AUDIT CHECKS PASSED PERFECTLY!")
