import xml.etree.ElementTree as ET
import re, subprocess, pathlib

svg_path = "candidate_ca_perfect.svg"
tree = ET.parse(svg_path)
root = tree.getroot()

# 1. Structure
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
assert first_tag == 'title', f"First child must be title, got {first_tag}"
assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"
assert children[0].text == "Cluster Autoscaler: what triggers a node and what blocks its removal"
assert children[1].text == "Cluster Autoscaler: what triggers a node and what blocks its removal"

# 2. Dimensions
width = root.get('width')
height = root.get('height')
viewBox = root.get('viewBox')
assert width == "1600"
vb = [float(x) for x in viewBox.split()]
assert vb[0] == 0 and vb[1] == 0 and vb[2] == 1600
assert 900 <= vb[3] <= 1200
assert int(height) == int(vb[3])

# 3. Text font-size >= 24
text_elems = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    fs = elem.attrib.get('font-size')
    assert fs is not None, f"Missing font-size on text: {elem.text}"
    size = float(fs)
    assert size >= 24, f"Font size {size} < 24 on text: {elem.text}"
    full_text = " ".join("".join(elem.itertext()).split())
    text_elems.append((full_text, size))
    for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
        tfs = tsp.attrib.get('font-size')
        if tfs:
            assert float(tfs) >= 24, f"tspan font size {tfs} < 24 in '{full_text}'"

print(f"3. All {len(text_elems)} text elements have font-size >= 24 px (PASS)")

# 4. Expected labels
expected_labels = [
    "Cluster Autoscaler: what triggers a node and what blocks its removal",
    "Scale-up lane",
    "1 pods Pending with FailedScheduling for insufficient resources",
    "2 for each node group, simulate adding a node from its template: would the pod fit",
    "3 expander picks among groups: random picks any, least-waste leaves the fewest empty seats, most-pods carries the most waiting pods",
    "4 group size raised within its min and max, for example --nodes=1:10:worker-auto-scaling-group",
    "5 node joins, scheduler places pods",
    "Scale-down lane",
    "node utilisation (requests against allocatable) below --scale-down-utilization-threshold 0.5 for --scale-down-unneeded-time 10 min, then drain and remove",
    "Blockers list",
    "pods without controllers",
    "emptyDir local storage unless annotated",
    "PDBs",
    "kube-system pods",
    "annotation cluster-autoscaler.kubernetes.io/safe-to-evict false",
    "recently added node (scale-down-delay-after-add)",
    "Limits",
    "reacts only to Pending pods; assumes homogeneous node groups; does not understand gang all-or-nothing needs",
    "GPU settings",
    "--gpu-total, burst pools min 0, --balance-similar-node-groups"
]

step_numbers = {"1", "2", "3", "4", "5"}

found_texts = [t for t, fs in text_elems]
all_ok = True
for exp in expected_labels:
    cnt = found_texts.count(exp)
    if cnt != 1:
        all_ok = False
        print(f"FAILED: count={cnt} for '{exp}'")
assert all_ok, "Some expected labels failed count == 1 check!"

extras = [t for t in found_texts if t not in expected_labels and t not in step_numbers]
assert len(extras) == 0, f"Found unexpected extra text: {extras}"

for s in step_numbers:
    cnt = found_texts.count(s)
    assert cnt == 1, f"Step number {s} count {cnt} != 1!"

print("4. All labels and step numbers present exactly once! (PASS)")

# 5. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
found_forbidden = []
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        if f in words:
            found_forbidden.append((f, t))
assert len(found_forbidden) == 0, f"Forbidden words found: {found_forbidden}"
print("5. No forbidden words! (PASS)")

# 6. Check orange count
raw = open(svg_path).read()
oranges = re.findall(r'#db8129', raw, re.IGNORECASE)
print(f"6. Orange #db8129 occurrences: {len(oranges)}")
assert 1 <= len(oranges) <= 6

# 7. Check arrows count
lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
total_arrows = len(lines) + len(paths)
print(f"7. Arrows found: {total_arrows}")
assert total_arrows == 4, f"Expected 4 arrows, got {total_arrows}"

# 8. Check colors present
assert "#f5f8f5" in raw
assert "#303a36" in raw
assert "#207448" in raw
assert "#e8f1ea" in raw
assert "#db8129" in raw
print("8. All required colors present! (PASS)")

lanes_y = 128
bottom_y = 970

# 9. Deep padding and card containment check
# Define all card rectangles (x, y, w, h)
cards = {
    "step-1": (65, lanes_y + 66, 690, 118),
    "step-2": (65, lanes_y + 202, 690, 118),
    "step-3": (65, lanes_y + 338, 690, 174),
    "step-4": (65, lanes_y + 530, 690, 132),
    "step-5": (65, lanes_y + 680, 690, 96),
    "cond-box": (845, lanes_y + 66, 690, 174),
    "blocker-1": (862, lanes_y + 316, 656, 58),
    "blocker-2": (862, lanes_y + 380, 656, 58),
    "blocker-3": (862, lanes_y + 444, 656, 58),
    "blocker-4": (862, lanes_y + 508, 656, 58),
    "blocker-5": (862, lanes_y + 572, 656, 114),
    "blocker-6": (862, lanes_y + 692, 656, 86),
    "limits-card": (65, bottom_y + 60, 690, 118),
    "gpu-card": (845, bottom_y + 60, 690, 118),
}

# Group text elements with their respective cards
text_to_card = [
    ("step-1", "1 pods Pending with FailedScheduling for insufficient resources"),
    ("step-2", "2 for each node group, simulate adding a node from its template: would the pod fit"),
    ("step-3", "3 expander picks among groups: random picks any, least-waste leaves the fewest empty seats, most-pods carries the most waiting pods"),
    ("step-4", "4 group size raised within its min and max, for example --nodes=1:10:worker-auto-scaling-group"),
    ("step-5", "5 node joins, scheduler places pods"),
    ("cond-box", "node utilisation (requests against allocatable) below --scale-down-utilization-threshold 0.5 for --scale-down-unneeded-time 10 min, then drain and remove"),
    ("blocker-1", "pods without controllers"),
    ("blocker-2", "emptyDir local storage unless annotated"),
    ("blocker-3", "PDBs"),
    ("blocker-4", "kube-system pods"),
    ("blocker-5", "annotation cluster-autoscaler.kubernetes.io/safe-to-evict false"),
    ("blocker-6", "recently added node (scale-down-delay-after-add)"),
    ("limits-card", "reacts only to Pending pods; assumes homogeneous node groups; does not understand gang all-or-nothing needs"),
    ("gpu-card", "--gpu-total, burst pools min 0, --balance-similar-node-groups"),
]

for card_id, full_txt in text_to_card:
    cx, cy, cw, ch = cards[card_id]
    # find corresponding text element
    matched = None
    for elem in root.findall('.//{http://www.w3.org/2000/svg}text'):
        txt = " ".join("".join(elem.itertext()).split())
        if txt == full_txt:
            matched = elem
            break
    assert matched is not None, f"Could not find text for {card_id}: {full_txt}"
    
    tspans = matched.findall('{http://www.w3.org/2000/svg}tspan')
    base_x = float(matched.attrib.get('x', 0))
    base_y = float(matched.attrib.get('y', 0))
    base_fs = float(matched.attrib.get('font-size', 24))
    base_fam = matched.attrib.get('font-family', 'sans-serif')
    anchor = matched.attrib.get('text-anchor', 'start')
    
    if not tspans:
        lines = [(full_txt, base_x, base_y, base_fs, base_fam, anchor)]
    else:
        lines = []
        cur_y = base_y
        for tsp in tspans:
            txt = tsp.text or ""
            tx = float(tsp.attrib.get('x', base_x))
            dy = float(tsp.attrib.get('dy', 0))
            cur_y += dy
            tfs = float(tsp.attrib.get('font-size', base_fs))
            tfam = tsp.attrib.get('font-family', base_fam)
            tanch = tsp.attrib.get('text-anchor', anchor)
            lines.append((txt, tx, cur_y, tfs, tfam, tanch))
            
    for l_idx, (txt, lx, ly, lfs, lfam, lanch) in enumerate(lines):
        rate = 0.62 if 'mono' in lfam else 0.60
        w = len(txt) * lfs * rate
        if lanch == 'middle':
            xmin = lx - w/2
            xmax = lx + w/2
        else:
            xmin = lx
            xmax = lx + w
        ytop = ly - lfs * 0.8
        ybot = ly + lfs * 0.2
        pad_l = xmin - cx
        pad_r = (cx + cw) - xmax
        pad_t = ytop - cy
        pad_b = (cy + ch) - ybot
        print(f"[{card_id:12s}] L{l_idx+1} '{txt:38s}': pad_l={pad_l:5.1f}, pad_r={pad_r:5.1f}, pad_t={pad_t:5.1f}, pad_b={pad_b:5.1f}")
        assert pad_l >= 16.0, f"[{card_id}] pad_l {pad_l} < 16 for '{txt}'"
        assert pad_r >= 16.0, f"[{card_id}] pad_r {pad_r} < 16 for '{txt}'"
        assert pad_t >= 16.0, f"[{card_id}] pad_t {pad_t} < 16 for '{txt}'"
        assert pad_b >= 16.0, f"[{card_id}] pad_b {pad_b} < 16 for '{txt}'"

print("\nALL CARDS HAVE AT LEAST 16 PX PADDING ON ALL SIDES! (PASS)")

# 10. Chrome headless render check
png_path = "/tmp/test_ca_check.png"
res = subprocess.run([
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '--headless=new',
    '--disable-gpu',
    '--hide-scrollbars',
    f'--window-size=1600,{int(vb[3])}',
    f'--screenshot={png_path}',
    f'file://{pathlib.Path(svg_path).resolve()}'
], capture_output=True)
print(f"10. Chrome render exit code: {res.returncode}, PNG size: {pathlib.Path(png_path).stat().st_size} bytes")
assert res.returncode == 0, "Chrome failed to render SVG!"

print("\nALL 10 CHECKS PASSED WITH FLYING COLORS!")
