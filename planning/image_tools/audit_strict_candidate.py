import xml.etree.ElementTree as ET
import re, subprocess, pathlib

svg_path = "test_candidate_layout.svg"
tree = ET.parse(svg_path)
root = tree.getroot()

# 1. Structure
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. Children: <{first_tag}>, <{second_tag}>")
assert first_tag == 'title', f"First child must be title, got {first_tag}"
assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"
print(f"   <title>: '{children[0].text}'")
print(f"   <desc>:  '{children[1].text}'")
assert children[0].text == "Cluster Autoscaler: what triggers a node and what blocks its removal"
assert children[1].text == "Cluster Autoscaler: what triggers a node and what blocks its removal"

# 2. Dimensions
width = root.get('width')
height = root.get('height')
viewBox = root.get('viewBox')
print(f"2. Dimensions: width={width}, height={height}, viewBox={viewBox}")
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

print(f"\n4. Checking {len(expected_labels)} expected labels:")
all_ok = True
for exp in expected_labels:
    cnt = found_texts.count(exp)
    ok = (cnt == 1)
    if not ok:
        all_ok = False
    print(f"   [{'OK' if ok else 'FAIL'}] count={cnt}: '{exp}'")

assert all_ok, "Some expected labels failed count == 1 check!"

extras = [t for t in found_texts if t not in expected_labels and t not in step_numbers]
print(f"\nExtra texts: {extras}")
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

print(f"5. Forbidden words: {found_forbidden} (PASS)")
assert len(found_forbidden) == 0

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

# 9. Chrome headless render check
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
print(f"9. Chrome render exit code: {res.returncode}, PNG size: {pathlib.Path(png_path).stat().st_size} bytes")
assert res.returncode == 0, "Chrome failed to render SVG!"

print("\nALL AUDIT CHECKS PASSED PERFECTLY!")
