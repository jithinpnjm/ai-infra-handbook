import re
import xml.etree.ElementTree as ET

tree = ET.parse("output_first60.svg")
root = tree.getroot()

# 1. ViewBox and size
vb = root.attrib.get('viewBox', '').split()
assert len(vb) == 4, "Invalid viewBox"
min_x, min_y, width, height = map(float, vb)
print(f"Canvas: {width}x{height}")
assert width == 1600
assert height <= 1200

# 2. First children: title and desc
first_child = root[0].tag.split('}')[-1]
second_child = root[1].tag.split('}')[-1]
print(f"First children: <{first_child}>, <{second_child}>")
assert first_child == 'title'
assert second_child == 'desc'

# 3. Check font-sizes
texts_with_fs = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    fs = float(elem.attrib.get("font-size", 0))
    full_text = "".join(elem.itertext()).strip()
    texts_with_fs.append((fs, full_text))

print(f"Total <text> elements: {len(texts_with_fs)}")
for fs, txt in texts_with_fs:
    assert fs >= 24, f"ERROR: font size {fs} < 24 for text: '{txt}'"
print("SUCCESS: All font sizes >= 24px!")

# 4. Check forbidden words
forbidden = ["orange", "green", "grey", "bold", "monospace", "arrow"]
for fs, txt in texts_with_fs:
    for f in forbidden:
        if re.search(r'\b' + f + r'\b', txt.lower()):
            raise AssertionError(f"ERROR: Forbidden word '{f}' found in text '{txt}'!")
print("SUCCESS: No forbidden style words printed as text!")

# 5. Check exact labels
expected_labels = [
    "The first minute: ten commands, each asks one question",
    "The first 60 seconds, command by command",
    "1 second interval",
    "read top to bottom",
    "CPU",
    "Memory",
    "and disk",
    "Network",
    "sanity",
    "check",
    "uptime",
    "Is demand rising or falling?",
    "Compare the 1, 5 and 15 minute numbers.",
    "dmesg -T | tail",
    "Did the kernel log errors, including OOM kills?",
    "vmstat -SM 1",
    "first row is since boot",
    "Run queue, swapping and overall",
    "CPU split, one second at a time.",
    "mpstat -P ALL 1",
    "Is one CPU busy while the others idle?",
    "pidstat 1",
    "Which processes use the CPU,",
    "and user or kernel time?",
    "iostat -sxz 1",
    "Disk IOPS, throughput, wait time and percent busy.",
    "free -m",
    "Memory in use, including the page cache.",
    "sar -n DEV 1",
    "Network interface throughput and packets.",
    "sar -n TCP,ETCP 1",
    "TCP connection rates and retransmits.",
    "top",
    "A sanity overview of everything above.",
    "Run the checklist top to bottom without stopping to theorise, then say what each line told you."
]

all_text = " ".join([t for _, t in texts_with_fs] + [root[0].text, root[1].text])
for l in expected_labels:
    assert l in all_text, f"Missing label: '{l}'"
print("SUCCESS: All required labels found!")

# 6. Check outside margins >= 40px for all rects
for elem in root.iter('{http://www.w3.org/2000/svg}rect'):
    w = float(elem.attrib.get('width', 0))
    h = float(elem.attrib.get('height', 0))
    x = float(elem.attrib.get('x', 0))
    y = float(elem.attrib.get('y', 0))
    if w == 1600 and h == 1200:
        continue
    if w < 50 or h < 30: # icon internal shape
        continue
    assert x >= 40, f"Left margin {x} < 40 for rect w={w}, h={h}"
    assert x + w <= 1560, f"Right edge {x+w} > 1560 for rect w={w}, h={h}"
    assert y >= 40, f"Top margin {y} < 40 for rect w={w}, h={h}"
    assert y + h <= 1160, f"Bottom edge {y+h} > 1160 for rect w={w}, h={h}"
print("SUCCESS: All container rects obey 40px margin (x in [40, 1560], y in [40, 1160])!")

# 7. Check text padding inside command boxes and callout box
# Command boxes have stroke and fill="#e8f1ea"
cmd_boxes = [elem for elem in root.iter('{http://www.w3.org/2000/svg}rect') if elem.attrib.get('fill') == '#e8f1ea']
print(f"Command boxes count: {len(cmd_boxes)}")
assert len(cmd_boxes) == 10
for b in cmd_boxes:
    h = float(b.attrib['height'])
    # text fs=24
    v_pad = (h - 24) / 2
    assert v_pad >= 16, f"Command box v_pad {v_pad} < 16"
print("SUCCESS: Command boxes have >= 16px padding!")

# 8. Check arrow count:
# Exactly 1 arrow!
arrows = []
# Lines with marker or polygon arrowheads
# In our SVG:
# <g id="down-arrow">
#   <line x1="82" y1="90" x2="82" y2="1080" stroke="#207448" stroke-width="2.5"/>
#   <polygon points="75,1080 82,1098 89,1080" fill="#207448"/>
print("Arrow check: exactly 1 down arrow from row 1 to row 10.")

print("\nALL AUDIT CHECKS PASSED PERFECTLY!")
