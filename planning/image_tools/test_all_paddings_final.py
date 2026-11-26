import xml.etree.ElementTree as ET

tree = ET.parse("p3_0206_connect_errors.svg")
root = tree.getroot()

boxes = [
    # (name, rect_x, rect_y, rect_w, rect_h)
    ("title", 0, 0, 1600, 95),
    ("SYN then RST", 54, 195, 232, 190),
    ("SYN retried", 54, 400, 232, 600),
    ("Error the client sees", 330, 95, 360, 90),
    ("What actually happened on the wire", 705, 95, 480, 90),
    ("Where to look", 1200, 95, 360, 90),
    # Row 1
    ("r1_c1", 330, 195, 360, 190),
    ("r1_c2", 705, 195, 480, 190),
    ("r1_c3", 1200, 195, 360, 190),
    # Row 2
    ("r2_c1", 330, 400, 360, 195),
    ("r2_c2", 705, 400, 480, 195),
    ("r2_c3", 1200, 400, 360, 195),
    # Row 3
    ("r3_c1", 330, 610, 360, 185),
    ("r3_c2", 705, 610, 480, 185),
    ("r3_c3", 1200, 610, 360, 185),
    # Row 4
    ("r4_c1", 330, 810, 360, 190),
    ("r4_c2", 705, 810, 480, 190),
    ("r4_c3", 1200, 810, 360, 190),
    # Bottom bar
    ("bottom_bar", 40, 1025, 1520, 95)
]

for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    txt = " ".join("".join(elem.itertext()).split())
    fs = float(elem.attrib['font-size'])
    tspans = list(elem.iter('{http://www.w3.org/2000/svg}tspan'))
    lines = [t.text.strip() for t in tspans] if tspans else [elem.text.strip()]
    
    box = None
    if "What the client sees" in txt: box = boxes[0]
    elif "A refusal means" in txt: box = boxes[18]
    elif "SYN then RST" in txt: box = boxes[1]
    elif "SYN retried" in txt: box = boxes[2]
    elif "Error the client sees" in txt: box = boxes[3]
    elif "What actually happened" in txt: box = boxes[4]
    elif "Where to look" in txt: box = boxes[5]
    elif "Connection refused" in txt: box = boxes[6]
    elif "a RST came back" in txt: box = boxes[7]
    elif "the listener" in txt: box = boxes[8]
    elif "Connection timed" in txt: box = boxes[9]
    elif "no reply to the SYNs" in txt: box = boxes[10]
    elif "route and firewall" in txt: box = boxes[11]
    elif "No route to host" in txt: box = boxes[12]
    elif "ICMP unreachable" in txt: box = boxes[13]
    elif "the routing table" in txt: box = boxes[14]
    elif "Connection reset" in txt: box = boxes[15]
    elif "a RST during" in txt: box = boxes[16]
    elif "peer crashed" in txt: box = boxes[17]

    assert box is not None, f"Could not find box for '{txt}'"
    b_name, bx, by, bw, bh = box
    
    print(f"\nChecking text: '{txt[:35]}...' in box '{b_name}' (w={bw}, h={bh})")
    for l in lines:
        w = len(l) * 0.6 * fs
        pad_h = (bw - w) / 2 if elem.attrib.get('text-anchor') == 'middle' else (bw - w - 24)
        print(f"   line: '{l}' (len={len(l)}, est_w={w:.1f}, pad_h={pad_h:.1f})")
        assert pad_h >= 16, f"Padding {pad_h:.1f} < 16 on line '{l}' in box '{b_name}'!"

print("\nALL TEXT LINES SATISFY >= 16px PADDING CHECK!")
