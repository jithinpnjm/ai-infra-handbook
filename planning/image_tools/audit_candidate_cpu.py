import xml.etree.ElementTree as ET
import re
import subprocess
import os

tree = ET.parse("generate_candidate_cpu.svg")
root = tree.getroot()

# 1. Structure check: First children must be title and desc
children = list(root)
tag1 = children[0].tag.split('}')[-1]
tag2 = children[1].tag.split('}')[-1]
print(f"1. Structure: Child 0: <{tag1}>, Child 1: <{tag2}>")
assert tag1 == "title", "First child must be <title>"
assert tag2 == "desc", "Second child must be <desc>"
print("   [PASS] <title> and <desc> are first children.")

# 2. Dimensions check
width = root.get('width')
viewBox = root.get('viewBox')
height = root.get('height')
print(f"2. Dimensions: width={width}, height={height}, viewBox={viewBox}")
assert width == "1600"
vb_parts = [float(x) for x in viewBox.split()]
assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
assert 900 <= vb_parts[3] <= 1200, f"Height must be 900..1200, got {vb_parts[3]}"
assert float(height) == vb_parts[3]
print("   [PASS] Canvas dimensions valid.")

# 3. Extract text and check font sizes
def get_full_text(elem):
    text = elem.text or ""
    for child in elem:
        text += get_full_text(child)
        text += child.tail or ""
    return text

text_elements = []
for t in root.iter("{http://www.w3.org/2000/svg}text"):
    content = " ".join(get_full_text(t).split())
    fs = int(t.attrib.get('font-size', 24))
    text_elements.append((content, fs))

print(f"\n3. Font sizes: Total text elements = {len(text_elements)} (all font-sizes >= 24px)")
for i, (txt, fs) in enumerate(text_elements, 1):
    print(f"   {i:2d}. [{fs:2d}px] {txt}")
    assert fs >= 24, f"Text '{txt}' has font-size {fs} < 24!"

# 4. Check forbidden words
forbidden_words = ["orange", "green", "grey", "gray", "bold", "monospace", "arrow", "cylinder", "folder", "icon", "callout", "sub-line", "subline", "takeaway"]
for txt, fs in text_elements:
    words = re.findall(r'\b[A-Za-z]+\b', txt.lower())
    for fw in forbidden_words:
        assert fw not in words, f"Forbidden word '{fw}' found in text: '{txt}'"
print("   [PASS] No style instruction words printed as text.")

# 5. Check expected labels
expected_labels = [
    "A CPU limit of 1 and five busy threads",
    "limit 1 CPU = 100 ms of CPU time per 100 ms period regardless of thread count",
    "cpu.stat nr_throttled counts it",
    "Timeline of one 100 ms CFS period",
    "the shared budget of 100 ms of CPU time is used up in the first 20 ms (5 threads times 20 ms)",
    "throttled for the remaining 80 ms even though the node may have idle CPU",
    "the next period starts and the budget refreshes",
    "average looks fine, tail latency grows; requests arriving late in a period wait",
    "default timeoutSeconds 1 on a throttled pod can fail a healthy liveness probe past 1000 ms and restart a healthy container; raise timeoutSeconds to 5 to 10 seconds"
]

all_svg_texts = [txt for txt, fs in text_elements]
print(f"\n4. Checking {len(expected_labels)} expected labels against {len(all_svg_texts)} found:")
for req in expected_labels:
    count = all_svg_texts.count(req)
    print(f"   [{'OK' if count == 1 else 'FAIL'}] count={count}: '{req[:50]}...'")
    assert count == 1, f"Expected '{req}' to appear exactly once, got {count}!"

extras = [t for t in all_svg_texts if t not in expected_labels]
print(f"\n   Extra texts: {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"
assert len(text_elements) == len(expected_labels), f"Text count {len(text_elements)} != {len(expected_labels)}"
print("   [PASS] Exact label count matches: 9 labels, 9 text elements.")

# 6. Check arrows count
lines_with_marker = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if e.attrib.get('marker-end')]
paths_with_marker = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if e.attrib.get('marker-end')]
total_arrows = len(lines_with_marker) + len(paths_with_marker)
print(f"\n5. Total arrows with marker-end: {total_arrows}")
assert total_arrows == 0, f"Expected 0 arrows, got {total_arrows}"
print("   [PASS] Exactly 0 arrows.")

# 7. Check color palette and orange count
with open("generate_candidate_cpu.svg") as f:
    raw = f.read()

assert "#f5f8f5" in raw, "Missing background #f5f8f5"
assert "#303a36" in raw, "Missing text #303a36"
assert "#207448" in raw, "Missing green #207448"
assert "#e8f1ea" in raw, "Missing light green #e8f1ea"
assert "#db8129" in raw, "Missing orange #db8129"

orange_count = len(re.findall(r'#db8129', raw, re.IGNORECASE))
print(f"\n6. Orange occurrences: {orange_count}")
assert orange_count == 1, f"Expected orange to be used exactly once, got {orange_count}"
print("   [PASS] Orange used only once for the single most important item.")

# 8. Render screenshot with headless Chrome
chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
res = subprocess.run([
    chrome_path,
    "--headless=new",
    "--disable-gpu",
    "--hide-scrollbars",
    "--window-size=1600,1020",
    "--screenshot=/tmp/generate_candidate_cpu.png",
    f"file://{os.path.abspath('generate_candidate_cpu.svg')}"
], capture_output=True, text=True)

assert os.path.exists("/tmp/generate_candidate_cpu.png"), "Chrome screenshot failed to generate!"
print("\n[PASS] Headless Chrome rendered /tmp/generate_candidate_cpu.png successfully.")
