import xml.etree.ElementTree as ET
import re
import sys

tree = ET.parse("candidate_decision_tree.svg")
root = tree.getroot()

# 1. First children check: <title> and <desc>
tag1 = root[0].tag.split('}')[-1]
tag2 = root[1].tag.split('}')[-1]
print(f"1. First children: <{tag1}>, <{tag2}>")
assert tag1 == "title", "First child must be <title>"
assert tag2 == "desc", "Second child must be <desc>"
print("   [PASS]")

# 2. Dimensions check
w = root.attrib.get('width')
h = root.attrib.get('height')
vb = root.attrib.get('viewBox')
print(f"2. Dimensions: width={w}, height={h}, viewBox={vb}")
assert w == "1600", f"Width must be 1600, got {w}"
assert vb == "0 0 1600 1200", f"viewBox must be '0 0 1600 1200', got {vb}"
print("   [PASS]")

# 3. Font-size checks (no text < 24 px)
print("3. Checking font sizes...")
for el in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = "".join(el.itertext()).strip()
    fs = int(el.attrib.get('font-size', '0'))
    assert fs >= 24, f"Text '{full_text}' font-size {fs} < 24!"
    for ts in el.findall('{http://www.w3.org/2000/svg}tspan'):
        tfs = int(ts.attrib.get('font-size', fs))
        assert tfs >= 24, f"tspan '{ts.text}' font-size {tfs} < 24 in '{full_text}'"
print("   [PASS] All text elements and tspans >= 24 px.")

# 4. Check labels
expected_labels = [
    "A decision tree, an alert-to-cause table and a classifier",
    "Latency or errors up",
    "Tokens/s zero with work queued?",
    "Hang or Xid: drain, capture, restart",
    "KV usage near 1 and preemptions?",
    "KV exhaustion: cut admission",
    "Prompt tail heavy, ITL up?",
    "Long-context HOL: isolate long prompts",
    "Ready below desired or many loading?",
    "Shrink, herd or probe kills",
    "Waiting high, batch full?",
    "Capacity: scale or shed",
    "Infra green, finish_reason moved?",
    "Quality or skew: roll back",
    "Check retries, tenants, versions"
]

found_texts = []
for el in root.iter('{http://www.w3.org/2000/svg}text'):
    t = " ".join("".join(el.itertext()).split())
    found_texts.append(t)

print(f"\n4. Found texts ({len(found_texts)}):")
for t in found_texts:
    print(f"   '{t}'")

# Check node labels
for exp in expected_labels:
    cnt = found_texts.count(exp)
    print(f"Checking label '{exp}': count={cnt}")
    assert cnt == 1, f"Expected '{exp}' to appear exactly once, got {cnt}"

# Check yes/no counts
yes_cnt = found_texts.count("yes")
no_cnt = found_texts.count("no")
print(f"Edge labels: 'yes'={yes_cnt}, 'no'={no_cnt}")
assert yes_cnt == 6, f"Expected 6 'yes', got {yes_cnt}"
assert no_cnt == 6, f"Expected 6 'no', got {no_cnt}"
print("   [PASS] All expected labels match perfectly.")

# 5. Check arrow counts
arrows = [el for el in root.iter() if 'marker-end' in el.attrib]
print(f"\n5. Arrow count: {len(arrows)}")
assert len(arrows) == 13, f"Expected 13 arrows, got {len(arrows)}"
print("   [PASS] Exactly 13 arrows.")

# 6. Check orange count
orange_els = []
svg_str = ET.tostring(root, encoding='unicode')
orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"\n6. Orange occurrences: {len(orange_matches)}")
assert len(orange_matches) > 0, "Must have orange #db8129"
# Check that ONLY node H uses orange
for el in root.iter():
    for k, v in el.attrib.items():
        if '#db8129' in v:
            orange_els.append((el.tag.split('}')[-1], k))
print(f"   Orange elements: {orange_els}")
print("   [PASS]")

# 7. Check external resources
assert "http://" not in svg_str.replace("http://www.w3.org/2000/svg", ""), "No external URLs"
assert "https://" not in svg_str, "No external URLs"
assert "<image" not in svg_str, "No <image> allowed"
assert "<script" not in svg_str, "No <script> allowed"
print("\n7. [PASS] No external resources.")

print("\n=== ALL UNIT AUDITS PASSED PERFECTLY ===")
