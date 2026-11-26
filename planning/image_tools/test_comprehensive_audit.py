import xml.etree.ElementTree as ET
import re
import subprocess
import os

tree = ET.parse("test_candidate.svg")
root = tree.getroot()

# 1. First children check:
tag1 = root[0].tag.split('}')[-1]
tag2 = root[1].tag.split('}')[-1]
print(f"First children: <{tag1}>, <{tag2}>")
assert tag1 == "title", "First child must be <title>"
assert tag2 == "desc", "Second child must be <desc>"

# 2. Extract full text from each text element
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

print(f"\n--- Total text elements in SVG: {len(text_elements)} ---")
for i, (txt, fs) in enumerate(text_elements, 1):
    print(f"{i:2d}. [{fs}px] {txt}")

# Check minimum font-size >= 24
for txt, fs in text_elements:
    assert fs >= 24, f"Text '{txt}' has font-size {fs} < 24!"
print("\n[PASS] No text smaller than 24 px.")

# 3. Check forbidden style instruction words
forbidden_words = ["orange", "green", "grey", "gray", "bold", "monospace", "arrow"]
for txt, fs in text_elements:
    words = re.findall(r'\b[A-Za-z]+\b', txt.lower())
    for fw in forbidden_words:
        assert fw not in words, f"Forbidden word '{fw}' found in text: '{txt}'"
print("[PASS] No style instruction words printed as text.")

# 4. Check required labels fidelity
expected_labels = [
    "A CPU limit of 1 and five busy threads",
    "limit 1 CPU = 100 ms of CPU time per 100 ms period regardless of thread count",
    "cpu.stat nr_throttled counts it",
    "Timeline of one 100 ms CFS period",
    "throttled for the remaining 80 ms even though the node may have idle CPU",
    "the shared budget of 100 ms of CPU time is used up in the first 20 ms (5 threads times 20 ms)",
    "the next period starts and the budget refreshes",
    "average looks fine, tail latency grows; requests arriving late in a period wait",
    "default timeoutSeconds 1 on a throttled pod can fail a healthy liveness probe past 1000 ms and restart a healthy container; raise timeoutSeconds to 5 to 10 seconds"
]

all_svg_texts = [txt for txt, fs in text_elements]
print("\n--- Verifying required labels ---")
for req in expected_labels:
    count = all_svg_texts.count(req)
    print(f"Label '{req[:40]}...': count = {count}")
    assert count == 1, f"Expected '{req}' to appear exactly once, got {count}!"

print("[PASS] All required labels present exactly once.")
assert len(text_elements) == len(expected_labels), f"Text elements count {len(text_elements)} != expected {len(expected_labels)}"
print(f"[PASS] Exact label count: {len(expected_labels)} labels, {len(text_elements)} text elements. None missing, none invented.")

# 5. Check arrow count (must be 0)
arrow_paths = [el for el in root.iter() if 'marker-end' in el.attrib]
assert len(arrow_paths) == 0, f"Expected 0 arrows, got {len(arrow_paths)}"
print("[PASS] Exactly 0 arrows present.")

# 6. Check color palette
with open("test_candidate.svg") as f:
    raw = f.read()

assert "#f5f8f5" in raw, "Missing background #f5f8f5"
assert "#303a36" in raw, "Missing text #303a36"
assert "#207448" in raw, "Missing green #207448"
assert "#e8f1ea" in raw, "Missing light green #e8f1ea"
assert "#db8129" in raw, "Missing orange #db8129"
print("[PASS] All required palette colors present.")

# Check orange count (only for single most important item)
orange_count = len(re.findall(r'#db8129', raw))
print(f"Orange occurrences: {orange_count} (on throttled block stroke)")
assert orange_count == 1, f"Expected orange to be used exactly once, got {orange_count}"
print("[PASS] Orange used only once for the single most important item.")

# 7. Render screenshot with headless Chrome
chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
res = subprocess.run([
    chrome_path,
    "--headless=new",
    "--disable-gpu",
    "--hide-scrollbars",
    "--window-size=1600,1000",
    "--screenshot=/tmp/test_candidate.png",
    f"file://{os.path.abspath('test_candidate.svg')}"
], capture_output=True, text=True)

assert os.path.exists("/tmp/test_candidate.png"), "Chrome screenshot failed to generate!"
print("[PASS] Headless Chrome rendered /tmp/test_candidate.png successfully.")
