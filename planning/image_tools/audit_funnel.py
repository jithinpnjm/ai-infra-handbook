import xml.etree.ElementTree as ET
import re

with open("test_slowness_funnel.svg") as f:
    svg_content = f.read()

root = ET.fromstring(svg_content)
ns = {"svg": "http://www.w3.org/2000/svg"}

# 1. First children check: <title> and <desc>
first = root[0].tag.split("}")[-1]
second = root[1].tag.split("}")[-1]
print(f"First tag: {first}, second tag: {second}")
assert first == "title"
assert second == "desc"

# 2. Dimensions check:
assert root.attrib.get("width") == "1600"
viewBox = root.attrib.get("viewBox")
print("viewBox:", viewBox)
assert viewBox.startswith("0 0 1600")

# 3. Text font-size check: >= 24px everywhere
font_sizes = []
for elem in root.iter("{http://www.w3.org/2000/svg}text"):
    fs = elem.attrib.get("font-size")
    if fs:
        font_sizes.append((float(fs), "".join(elem.itertext()).strip()))
    for tspan in elem.iter("{http://www.w3.org/2000/svg}tspan"):
        tfs = tspan.attrib.get("font-size")
        if tfs:
            font_sizes.append((float(tfs), "".join(tspan.itertext()).strip()))

print(f"Checked {len(font_sizes)} font sizes.")
for fs, text in font_sizes:
    if fs < 24:
        print(f"ERROR: font size {fs} < 24 on text: '{text}'")
assert all(fs >= 24 for fs, _ in font_sizes), "Found font size < 24px!"
print("SUCCESS: All font sizes >= 24px!")

# 4. Check forbidden style words as text:
forbidden = ["orange", "green", "grey", "bold", "monospace", "arrow"]
all_texts = []
for elem in root.iter("{http://www.w3.org/2000/svg}text"):
    full_t = re.sub(r'\s+', ' ', "".join(elem.itertext()).strip())
    all_texts.append(full_t)
    for f in forbidden:
        if re.search(r'\b' + f + r'\b', full_t.lower()):
            print(f"ERROR: Forbidden word '{f}' found in text: '{full_t}'")
            raise AssertionError(f"Forbidden word {f}")

print("SUCCESS: No forbidden style words in any text!")

# 5. Check all source labels are present and exact:
source_labels = [
    "Slowness is a funnel: measure it, find the limit, find the segment, then split loss from delay",
    "Quantify: throughput, latency percentiles, retransmit rate, against baseline and line rate or BDP",
    "Find the limit: ss -ti limiter flags, CPU and softirq, NIC drops, PFC, ECN, MTU",
    "Find the segment: iperf3 or ib_write_bw between pairs, halving the path",
    "Loss or latency: nstat and tcpretrans for loss, ss -ti and ping for RTT",
    "One flow or all flows: ECMP hash collisions, elephant flows, single-core limits",
    "Step 6: compare with a healthy node",
    "Each step removes part of the search space before the next one starts."
]

for label in source_labels:
    # Check if label appears in all_texts or can be found exactly
    found = False
    for t in all_texts:
        if label in t:
            found = True
            break
    if not found:
        print(f"FAILED TO FIND EXACT LABEL: '{label}'")
        print("Available texts:", all_texts)
        raise AssertionError(f"Label missing: {label}")
    else:
        print(f"FOUND: '{label[:40]}...'")

print("SUCCESS: All source labels present exactly!")
