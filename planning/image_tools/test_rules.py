import re
import xml.etree.ElementTree as ET

tree = ET.parse("output.svg")
root = tree.getroot()

# 1. First children: title and desc
tag1 = root[0].tag.split('}')[-1]
tag2 = root[1].tag.split('}')[-1]
print(f"First children: <{tag1}>, <{tag2}>")
assert tag1 == "title", "First child must be <title>"
assert tag2 == "desc", "Second child must be <desc>"

# 2. Extract all text content
texts = []
font_sizes = []

def walk(el):
    if el.tag.endswith('text') or el.tag.endswith('tspan'):
        # get text
        t = (el.text or "").strip()
        if t:
            texts.append(t)
            fs = el.attrib.get('font-size')
            if fs:
                font_sizes.append((t, int(fs)))
    for child in el:
        walk(child)

walk(root)

print("\n--- All text elements in SVG ---")
for t, fs in font_sizes:
    print(f"[{fs}px] {t}")

# Check minimum font size >= 24
for t, fs in font_sizes:
    assert fs >= 24, f"Text '{t}' has font-size {fs} < 24!"
print("\n[PASS] No text smaller than 24 px.")

# Check required labels from content:
required_labels = [
    "Generic resources (GRES)",
    "1. Node GRES Discovery (slurmd -G)",
    "gres.conf: AutoDetect=nvml",
    "Type, File, Cores, Links, MIG",
    "slurm.conf: GresTypes=gpu",
    "NodeName=gpu[01-16] Gres=gpu:h100:8",
    "slurmctld (select/cons_tres)",
    "Tracks GRES, NUMA Sockets & NVLink",
    "2. Isolation & Task Binding (slurmstepd)",
    "cgroup.conf: ConstrainDevices=yes",
    "Allows only /dev/nvidia3, /dev/nvidia7",
    "--gpus-per-task=1 / --gpu-bind=closest",
    "Rank 0 -> CVD=0; Rank 1 -> CVD=1"
]

print("\n--- Verifying required labels ---")
normalized_texts = [t.replace("&amp;", "&").replace("&gt;", ">").replace("&lt;", "<") for t in texts]
# remove title and desc from label check if needed, but title is "Generic resources (GRES)"
for req in required_labels:
    count = normalized_texts.count(req)
    print(f"Label '{req}': count={count}")
    assert count == 1, f"Expected '{req}' to appear exactly once, got {count}!"

print("[PASS] All required labels present exactly once.")

# Check for banned style words printed as text:
banned_words = ["orange", "green", "grey", "gray", "bold", "monospace", "arrow"]
for t in texts:
    for bw in banned_words:
        # check if bw is standalone word in text (not substring of something legitimate)
        words = re.findall(r'\b[A-Za-z]+\b', t.lower())
        assert bw not in words, f"Banned word '{bw}' found in text: '{t}'"

print("[PASS] No style instruction words printed as text.")

# Check arrows count
# Arrows in SVG: paths with marker-end
arrow_paths = [el for el in root.iter() if 'marker-end' in el.attrib]
print(f"\nArrow paths count: {len(arrow_paths)}")
assert len(arrow_paths) == 4, f"Expected exactly 4 arrows, got {len(arrow_paths)}"
print("[PASS] Exactly 4 arrows present.")

# Check colors
with open("output.svg") as f:
    raw = f.read()

assert "#f5f8f5" in raw, "Background #f5f8f5 missing"
assert "#303a36" in raw, "Text #303a36 missing"
assert "#207448" in raw, "Main green #207448 missing"
assert "#e8f1ea" in raw, "Light green panels #e8f1ea missing"
assert "#db8129" in raw, "Orange #db8129 missing"
print("[PASS] All required palette colors present.")

# Check orange usage: "one orange #db8129 used only for the single most important item or arrow."
# Let's count where #db8129 appears
orange_matches = re.findall(r'#db8129', raw)
print(f"Orange #db8129 occurrences: {len(orange_matches)}")
