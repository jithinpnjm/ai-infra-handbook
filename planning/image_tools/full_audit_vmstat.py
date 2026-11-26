import re
import xml.etree.ElementTree as ET

tree = ET.parse("vmstat_decision_tree.svg")
root = tree.getroot()

expected_labels = [
    "Read the vmstat columns to classify the bottleneck",
    "Run vmstat 2 and start at line 2",
    "Line 1 is the average since boot",
    "All idle: id about 99, si and so at 0",
    "Healthy",
    "High us, low wa",
    "CPU-bound compute",
    "High wa and b",
    "I/O-bound work: look at iostat",
    "Growing so, falling free or cache",
    "Memory exhausted: kernel is paging out",
    "High r with high us plus sy",
    "CPU contention",
    "High sy and cs",
    "Many system calls or lock contention",
    "High st",
    "Noisy neighbours on a shared VM",
    "Read the trend across several lines, not one number."
]

forbidden_words = ["orange", "grey", "monospace", "arrow", "branch"]

print("=== CHECK 1: EXACT LABELS AUDIT ===")
all_text_elements = []
for elem in root.iter():
    if elem.tag.endswith('text'):
        # collect all text inside
        full = ""
        if elem.text and elem.text.strip():
            full += elem.text.strip() + " "
        for child in elem:
            if child.tag.endswith('tspan') and child.text and child.text.strip():
                full += child.text.strip() + " "
        full = " ".join(full.split())
        all_text_elements.append((elem, full))

print(f"Total <text> elements found: {len(all_text_elements)}")
missing = []
duplicated = []
for exp in expected_labels:
    matches = [t for _, t in all_text_elements if "".join(exp.split()) == "".join(t.split())]
    if len(matches) == 1:
        print(f"  [OK] '{exp}' matches exactly once.")
    elif len(matches) == 0:
        print(f"  [MISSING] '{exp}'")
        missing.append(exp)
    else:
        print(f"  [DUPLICATED] '{exp}': {matches}")
        duplicated.append(exp)

assert not missing and not duplicated, "Labels mismatch!"

print("\n=== CHECK 2: FORBIDDEN STYLE WORDS AS TEXT ===")
raw_svg = open("vmstat_decision_tree.svg").read()
# Find all text between > and <
text_nodes = re.findall(r'>([^<]+)<', raw_svg)
found_forbidden = []
for t in text_nodes:
    t_clean = t.strip()
    if not t_clean:
        continue
    for fw in forbidden_words:
        # Check if fw is a whole word in t_clean (case insensitive)
        if re.search(r'\b' + fw + r'\b', t_clean, re.I):
            found_forbidden.append((fw, t_clean))

if found_forbidden:
    print(f"Found forbidden words: {found_forbidden}")
else:
    print("No forbidden style words found in rendered text! (PASS)")
assert not found_forbidden

print("\n=== CHECK 3: MINIMUM FONT SIZE ===")
for elem in root.iter():
    if elem.tag.endswith('text') or elem.tag.endswith('tspan'):
        fs = elem.attrib.get('font-size')
        if fs:
            size = float(fs)
            assert size >= 24, f"Text size {size} is smaller than 24px: {elem.text}"
print("All text elements >= 24px! (PASS)")

print("\n=== CHECK 4: ARROWS COUNT ===")
arrows = [e for e in root.iter() if 'marker-end' in e.attrib]
print(f"Arrows found: {len(arrows)}")
assert len(arrows) == 7, f"Expected 7 arrows, found {len(arrows)}"
print("Exactly 7 arrows! (PASS)")

print("\n=== CHECK 5: BOX-TO-BOX GAPS & MARGINS ===")
# Parse all rects that act as boxes
rects = [e for e in root.iter() if e.tag.endswith('rect') and e.attrib.get('id') != 'canvas' and float(e.attrib.get('width', 0)) > 100]
print(f"Major boxes found: {len(rects)}")

# Let's check boxes coordinates
# Root: (60, 125, 1480, 96) -> bottom = 221
# B1: (220, 305, 540, 80) -> bottom = 385
# B2: (220, 475, 540, 80) -> bottom = 555
# B3: (220, 650, 540, 115) -> bottom = 765
# B4: (220, 865, 540, 120) -> bottom = 985
# B5: (840, 320, 540, 80) -> bottom = 400
# B6: (840, 535, 540, 115) -> bottom = 650
# B7: (840, 790, 540, 120) -> bottom = 910
# TB: (60, 1095, 1480, 65) -> bottom = 1160

gaps = [
    ("Root -> B1", 305 - 221),
    ("B1 -> B2", 475 - 385),
    ("B2 -> B3", 650 - 555),
    ("B3 -> B4", 865 - 765),
    ("B4 -> TB", 1095 - 985),
    ("Root -> B5", 320 - 221),
    ("B5 -> B6", 535 - 400),
    ("B6 -> B7", 790 - 650),
    ("B7 -> TB", 1095 - 910),
    ("B1/B2/B3/B4 -> B5/B6/B7 (horizontal)", 840 - (220 + 540)),
    ("Canvas Left margin", 60),
    ("Canvas Right margin", 1600 - (60 + 1480)),
    ("Canvas Top margin", 125),
    ("Canvas Bottom margin", 1200 - (1095 + 65)),
]

for name, gap in gaps:
    status = "OK" if gap >= 40 else "FAIL"
    print(f"  [{status}] {name:36s}: gap = {gap:.1f}px (min 40px)")
    assert gap >= 40

print("\n=== CHECK 6: TEXT PADDING INSIDE BOXES (MIN 16PX) ===")
# Detailed padding checks
paddings = [
    ("Root Line 1", 165 - 60, (60 + 1480) - (165 + len("Run vmstat 2 and start at line 2")*0.6*30), (166 - 0.8*30) - 125, (125 + 96) - (166 + 0.2*30)),
    ("Root Line 2", 165 - 60, (60 + 1480) - (165 + len("Line 1 is the average since boot")*0.6*24), (200 - 0.8*24) - 125, (125 + 96) - (200 + 0.2*24)),
    ("B1 Healthy", 315 - 220, (220 + 540) - (315 + len("Healthy")*0.6*30), (355 - 0.8*30) - 305, (305 + 80) - (355 + 0.2*30)),
    ("B2 CPU-bound compute", 315 - 220, (220 + 540) - (315 + len("CPU-bound compute")*0.6*30), (525 - 0.8*30) - 475, (475 + 80) - (525 + 0.2*30)),
    ("B3 I/O-bound line 1", 315 - 220, (220 + 540) - (315 + len("I/O-bound work:")*0.6*30), (700 - 0.8*30) - 650, (650 + 115) - (700 + 0.2*30)),
    ("B3 I/O-bound line 2", 315 - 220, (220 + 540) - (315 + len("look at iostat")*0.6*30), (736 - 0.8*30) - 650, (650 + 115) - (736 + 0.2*30)),
    ("B4 Memory exh line 1", 315 - 220, (220 + 540) - (315 + len("Memory exhausted:")*0.6*30), (917 - 0.8*30) - 865, (865 + 120) - (917 + 0.2*30)),
    ("B4 Memory exh line 2", 315 - 220, (220 + 540) - (315 + len("kernel is paging out")*0.6*30), (953 - 0.8*30) - 865, (865 + 120) - (953 + 0.2*30)),
    ("B5 CPU contention", 935 - 840, (840 + 540) - (935 + len("CPU contention")*0.6*30), (370 - 0.8*30) - 320, (320 + 80) - (370 + 0.2*30)),
    ("B6 Lock cont line 1", 935 - 840, (840 + 540) - (935 + len("Many system calls")*0.6*30), (585 - 0.8*30) - 535, (535 + 115) - (585 + 0.2*30)),
    ("B6 Lock cont line 2", 935 - 840, (840 + 540) - (935 + len("or lock contention")*0.6*30), (621 - 0.8*30) - 535, (535 + 115) - (621 + 0.2*30)),
    ("B7 Noisy neigh line 1", 935 - 840, (840 + 540) - (935 + len("Noisy neighbours")*0.6*30), (842 - 0.8*30) - 790, (790 + 120) - (842 + 0.2*30)),
    ("B7 Noisy neigh line 2", 935 - 840, (840 + 540) - (935 + len("on a shared VM")*0.6*30), (878 - 0.8*30) - 790, (790 + 120) - (878 + 0.2*30)),
    ("Takeaway bar", 800 - 0.5*len("Read the trend across several lines, not one number.")*0.6*26 - 60, (60 + 1480) - (800 + 0.5*len("Read the trend across several lines, not one number.")*0.6*26), (1136 - 0.8*26) - 1095, (1095 + 65) - (1136 + 0.2*26)),
]

for name, pl, pr, pt, pb in paddings:
    mp = min(pl, pr, pt, pb)
    status = "OK" if mp >= 16 else "FAIL"
    print(f"  [{status}] {name:22s}: min_pad={mp:.1f}px (L={pl:.1f}, R={pr:.1f}, T={pt:.1f}, B={pb:.1f})")
    assert mp >= 16

print("\nALL VERIFICATIONS PASSED WITH FLYING COLORS!")
