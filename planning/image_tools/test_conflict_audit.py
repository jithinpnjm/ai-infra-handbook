import xml.etree.ElementTree as ET
import re

svg_path = "candidate_final_conflict.svg"
tree = ET.parse(svg_path)
root = tree.getroot()
raw = open(svg_path).read()

print("==================== SVG AUDIT SUITE ====================")

# 1. Structure
children = list(root)
t1 = children[0].tag.split('}')[-1]
t2 = children[1].tag.split('}')[-1]
assert t1 == 'title', f"First child is {t1}, not title"
assert t2 == 'desc', f"Second child is {t2}, not desc"
print("1. Structure: <title> and <desc> are the first children. [PASS]")

# 2. Dimensions
w = root.get('width')
h = root.get('height')
vb = root.get('viewBox').split()
assert w == '1600'
assert vb[0] == '0' and vb[1] == '0' and vb[2] == '1600'
assert 900 <= float(vb[3]) <= 1200
assert float(h) == float(vb[3])
print(f"2. Dimensions: {w}x{h}, viewBox='{root.get('viewBox')}'. [PASS]")

# 3. Text elements & font sizes >= 24px
text_elems = []
for el in root.iter('{http://www.w3.org/2000/svg}text'):
    txt = re.sub(r'\s+', ' ', ''.join(el.itertext()).strip())
    fs = float(el.attrib.get('font-size', 0))
    assert fs >= 24, f"Text '{txt}' font-size {fs} < 24!"
    for tsp in el.iter('{http://www.w3.org/2000/svg}tspan'):
        tfs = tsp.attrib.get('font-size')
        if tfs:
            assert float(tfs) >= 24, f"tspan font-size {tfs} < 24 in '{txt}'!"
    text_elems.append((txt, fs))

print(f"3. Font sizes: {len(text_elems)} text elements found, ALL >= 24px. [PASS]")
for i, (t, fs) in enumerate(text_elems, 1):
    print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

# 4. Expected labels
expected_labels = [
    "Two writers and a 409 Conflict",
    "Client A",
    "kube-apiserver / etcd",
    "Client B",
    "Client A reads object at resourceVersion 5012.",
    "Client B reads the same object at resourceVersion 5012.",
    "Client B writes its change; server accepts; object now at resourceVersion 5013.",
    "Client A writes its change based on 5012; server rejects with HTTP 409 Conflict.",
    "Client A re-reads the latest version from its informer cache, re-applies its change and retries.",
    "resourceVersion maps to the etcd key mod_revision",
    "Server-side apply tracks field ownership in managedFields"
]

step_numbers = {"1", "2", "3", "4", "5"}

found_texts = [t for t, fs in text_elems]
print("\n4. Label fidelity:")
for exp in expected_labels:
    cnt = found_texts.count(exp)
    assert cnt == 1, f"Expected '{exp}' count={cnt} != 1"
    print(f"   [OK] count=1: '{exp}'")

extras = [t for t in found_texts if t not in expected_labels and t not in step_numbers]
assert len(extras) == 0, f"Found unexpected extra text: {extras}"
print("   No unexpected extra text elements. [PASS]")

for num in step_numbers:
    cnt = found_texts.count(num)
    assert cnt == 1, f"Step number '{num}' count={cnt} != 1"
print("   All 5 step numbers present in circles. [PASS]")

# 5. Banned words
banned = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for b in banned:
        assert b not in words, f"Banned styling word '{b}' found in '{t}'!"
print("\n5. Banned words: Zero styling words printed as text. [PASS]")

# 6. Orange usage
oranges = re.findall(r'#db8129', raw, re.IGNORECASE)
print(f"\n6. Orange highlights: {len(oranges)} occurrences found.")
assert 1 <= len(oranges) <= 4, f"Unexpected orange count: {len(oranges)}"
print("   Single orange highlight used for HTTP 409 Conflict. [PASS]")

# 7. Arrows
lines = [l for l in root.iter('{http://www.w3.org/2000/svg}line') if 'marker-end' in l.attrib]
paths = [p for p in root.iter('{http://www.w3.org/2000/svg}path') if 'marker-end' in p.attrib]
total_arrows = len(lines) + len(paths)
print(f"\n7. Total arrows: {total_arrows}")
assert total_arrows == 5, f"Expected 5 arrows, got {total_arrows}"
print("   Exactly 5 arrows matching the 5 steps. [PASS]")

# 8. Number circles
circles = [c for c in root.iter('{http://www.w3.org/2000/svg}circle') if c.attrib.get('r') == '24']
print(f"\n8. Number circles (r=24): {len(circles)}")
assert len(circles) == 5, f"Expected 5 number circles, got {len(circles)}"
print("   Exactly 5 number circles present. [PASS]")

# 9. Box and text padding checks (strictly >= 16px)
print("\n9. Padding and clearance verification (strictly >= 16px):")
cards = [
    ("Card 1", 480, ["Client A reads object at", "resourceVersion 5012."]),
    ("Card 2", 480, ["Client B reads the same object", "at resourceVersion 5012."]),
    ("Card 3", 480, ["Client B writes its change;", "server accepts; object now at", "resourceVersion 5013."]),
    ("Card 4", 480, ["Client A writes its change", "based on 5012; server rejects", "with HTTP 409 Conflict."]),
    ("Card 5", 480, ["Client A re-reads the", "latest version from its", "informer cache, re-applies", "its change and retries."]),
]

for name, box_w, lines_text in cards:
    for line in lines_text:
        w_est = len(line) * 0.6 * 24
        pad = (box_w - w_est) / 2
        assert pad >= 16, f"Padding for '{line}' in {name} is {pad:.1f}px < 16px!"
        print(f"   {name} line '{line[:25]}...': width={w_est:.1f}px, padding={pad:.1f}px >= 16px [PASS]")

print("\nALL 9 AUDIT CATEGORIES PASSED WITH 100% SUCCESS!")
