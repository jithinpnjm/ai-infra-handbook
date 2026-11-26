import re
import xml.etree.ElementTree as ET

tree = ET.parse("candidate_accept.svg")
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
raw_svg = open("candidate_accept.svg").read()
# Find all font-size declarations (ignore the tiny 14px in icon decoration if any, or wait! Are all font sizes in text elements >= 24?)
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
cleaned_text = ' '.join(re.sub(r'<[^>]+>', ' ', raw_svg).split())
# normalize &lt; &gt; &amp;
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
    # 1. Membership in cleaned full SVG text (as in run_full_suite.py)
    assert norm_req in cleaned_text, f"Missing required label in SVG: '{norm_req}'"
    # 2. Exactly once among SVG text nodes (as in test_rules.py)
    cnt = text_nodes.count(norm_req)
    print(f"Checking text node count for '{norm_req}': count={cnt}")
    assert cnt == 1, f"Expected '{norm_req}' to appear exactly once in text nodes, got {cnt}!"

print("PASS: All 19 required labels present and appear exactly once in text nodes!")

# 6. Colors check
palette = ["#f5f8f5", "#303a36", "#207448", "#e8f1ea", "#db8129"]
for c in palette:
    assert c in raw_svg, f"Required color {c} missing from SVG!"
print("PASS: All required palette colors present (#f5f8f5, #303a36, #207448, #e8f1ea, #db8129)")

# 7. Check arrow marker usage
arrow_elements = [el for el in root.iter() if 'marker-end' in el.attrib]
print(f"Arrow elements with marker-end: {len(arrow_elements)}")
for el in arrow_elements:
    print(f"  {el.tag.split('}')[-1]}: {el.attrib.get('marker-end')}")

print("\nALL AUTOMATED TESTS PASSED CLEANLY!")
