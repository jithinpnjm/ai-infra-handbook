import xml.etree.ElementTree as ET
import re, subprocess

tree = ET.parse('test_candidate.svg')
root = tree.getroot()

# Check title and desc
children = list(root)
print("Child 0:", children[0].tag)
print("Child 1:", children[1].tag)
assert children[0].tag.endswith('title')
assert children[1].tag.endswith('desc')

with open('test_candidate.svg') as f:
    svg_text = f.read()

# Check font sizes
font_sizes = [int(s) for s in re.findall(r'font-size="(\d+)"', svg_text)]
print(f"Total font-size attributes: {len(font_sizes)}, min: {min(font_sizes)}, max: {max(font_sizes)}")
assert min(font_sizes) >= 24, f"Font size < 24 found: {min(font_sizes)}"

# Check required labels
required_labels = [
    "Top-down and bottom-up checklist",
    "Top-down (application symptom to wire)",
    "process listening",
    "ss -tulpn",
    "connect test",
    "nc -zv host port",
    "refusal versus timeout",
    "DNS",
    "getent hosts",
    "dig",
    "route and source",
    "ip route get <dst>",
    "ip rule",
    "rp_filter",
    "firewall",
    "nft list ruleset",
    "conntrack",
    "neighbours",
    "ip neigh",
    "arping",
    "interface",
    "ip -s link",
    "ethtool -S",
    "capture packets at both ends",
    "Bottom-up goes the other way",
    "link up",
    "speed and FEC",
    "errors",
    "ring buffers",
    "IRQ and CPU",
    "Application reports the failure: go top-down. Counters already rising: go bottom-up"
]

all_text_elements = []
for elem in root.iter():
    if elem.tag.endswith('text') or elem.tag.endswith('tspan'):
        # Gather text
        txt = "".join(elem.itertext()).strip()
        if txt:
            all_text_elements.append(txt)

print(f"Total text strings extracted: {len(all_text_elements)}")

# Check each required label
missing = []
for lbl in required_labels:
    # Check if exact label is present
    # Either exact match in one element, or in svg_text
    found = False
    for txt in all_text_elements:
        if lbl in txt:
            found = True
            break
    if not found:
        missing.append(lbl)

print("Missing labels:", missing)
assert len(missing) == 0

# Check duplication
# Ensure each required label appears exactly once
dups = []
for lbl in required_labels:
    count = 0
    for txt in all_text_elements:
        # Check how many times lbl appears in all_text_elements
        if lbl == txt or (lbl in txt and len(txt) - len(lbl) < 10):
            count += 1
    if count != 1:
        print(f"Label '{lbl}' count = {count}")
        dups.append((lbl, count))

print("Duplication check:", dups)

# Render to PNG using Google Chrome
cmd = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "--headless",
    "--disable-gpu",
    "--screenshot=test_chrome.png",
    "--window-size=1600,1200",
    "test_candidate.svg"
]
res = subprocess.run(cmd, capture_output=True, text=True)
print("Chrome exit code:", res.returncode)
print("Rendered screenshot saved to test_chrome.png")
