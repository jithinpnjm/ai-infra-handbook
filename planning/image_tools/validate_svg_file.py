import re
import xml.etree.ElementTree as ET

# Read the SVG
tree = ET.parse("kubelet.svg")
root = tree.getroot()

# Check namespace
ns = {"svg": "http://www.w3.org/2000/svg"}

# 1. Check title and desc are first children
first_child = root[0].tag.split('}')[-1]
second_child = root[1].tag.split('}')[-1]
print(f"First child: <{first_child}>, Second child: <{second_child}>")
assert first_child == "title", f"Expected title, got {first_child}"
assert second_child == "desc", f"Expected desc, got {second_child}"

# 2. Check title content
title_text = root[0].text
print(f"Title text: '{title_text}'")
assert title_text == "What the kubelet does"

# 3. Check width and viewBox
width = root.attrib.get("width")
height = root.attrib.get("height")
viewBox = root.attrib.get("viewBox")
print(f"Width: {width}, Height: {height}, viewBox: {viewBox}")
assert width == "1600"
assert viewBox == "0 0 1600 1200"

# 4. Check all required text strings
# Collect all text from all <text> elements
texts = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = "".join(elem.itertext()).strip()
    texts.append(full_text)

# Also check font-sizes
font_sizes = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    fs = float(elem.attrib.get("font-size", 0))
    font_sizes.append((fs, "".join(elem.itertext()).strip()))

print(f"Total <text> elements: {len(font_sizes)}")
for fs, txt in font_sizes:
    if fs < 24:
        print(f"ERROR: Text '{txt}' has font-size {fs} < 24!")
assert all(fs >= 24 for fs, _ in font_sizes), "Found font size < 24!"
print("SUCCESS: No text smaller than 24px anywhere!")

# 5. Check all arrows:
# Arrows are paths with marker-end="url(#arrow)"
arrow_paths = []
for elem in root.iter('{http://www.w3.org/2000/svg}path'):
    if elem.attrib.get("marker-end") == "url(#arrow)":
        arrow_paths.append(elem.attrib.get("d"))

print(f"Total arrow paths: {len(arrow_paths)}")
assert len(arrow_paths) == 13, f"Expected 13 arrows, got {len(arrow_paths)}"
print("SUCCESS: Exactly 13 arrows!")

# 6. Check required content strings are accounted for:
source_labels = [
    "Pod sources",
    "API server (watch pods with spec.nodeName=this node)",
    "Static pod manifests dir",
    "HTTP manifest URL (rare)",
    "Pod manager / config merge",
    "Per-pod workers (syncPod)",
    "Volume manager\n(CSI, emptyDir, configmap...)",
    "Resource managers\nCPU / memory / topology / device",
    "CRI client → containerd/CRI-O",
    "Prober (startup/readiness/liveness)",
    "PLEG: relist container states → events",
    "Status manager → API server",
    "Eviction manager (node pressure)",
    "Image GC / container GC",
    "cAdvisor/cgroup stats → /metrics, /stats/summary",
    "Node lease + node status heartbeats",
    "Kubelet HTTPS server :10250\n(logs, exec, attach, port-forward, metrics, pods)"
]

combined_all_text = " ".join(texts)
for sl in source_labels:
    # Normalize whitespace
    words = sl.split()
    found = True
    for w in words:
        if w not in combined_all_text:
            print(f"ERROR: Word '{w}' from label '{sl}' not found in SVG!")
            found = False
    if found:
        print(f"  OK: '{sl[:30]}...' found")

# 7. Check no forbidden style words as text:
forbidden = ["orange", "green", "grey", "bold", "monospace", "arrow"]
for t in texts:
    for f in forbidden:
        # Check if whole word f is in t
        if re.search(r'\b' + f + r'\b', t.lower()):
            print(f"ERROR: Forbidden word '{f}' found in text '{t}'!")

print("All automated checks completed successfully!")
