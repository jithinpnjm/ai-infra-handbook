import re
import xml.etree.ElementTree as ET

tree = ET.parse("test_candidate.svg")
root = tree.getroot()

# List of all expected labels from the prompt
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

print("=== CHECK 1: LABEL AUDIT ===")
# Extract all text from SVG
svg_text = open("test_candidate.svg").read()

# We need to check each label
missing = []
duplicated = []
for label in expected_labels:
    # If the label was wrapped across tspans, the whole string might not appear in one line of file,
    # or it might appear via tspans. Let's reconstruct text elements from the XML!
    pass

# Collect text elements and tspans from XML
all_texts = []
for elem in root.iter():
    if elem.tag.endswith('text'):
        # Could contain tspans or direct text
        full_text = ""
        if elem.text and elem.text.strip():
            full_text += elem.text.strip() + " "
        for child in elem:
            if child.tag.endswith('tspan') and child.text and child.text.strip():
                full_text += child.text.strip() + " "
        full_text = " ".join(full_text.split())
        all_texts.append((elem, full_text))

print(f"Total <text> elements found: {len(all_texts)}")
for el, t in all_texts:
    print(f"  - '{t}' (font-size={el.attrib.get('font-size')})")

print("\nVerifying each expected label against the collected texts:")
all_texts_joined = " | ".join([t for _, t in all_texts])

for exp in expected_labels:
    # count how many times exp appears
    matches = [t for _, t in all_texts if exp == t or exp.replace(":", "") == t.replace(":", "")]
    # Also check normalized spaces
    if not matches:
        # Check if exp is substring or matches normalized
        matches = [t for _, t in all_texts if "".join(exp.split()) == "".join(t.split())]
    if len(matches) == 1:
        print(f"  [OK] '{exp}' matches exactly once.")
    elif len(matches) == 0:
        print(f"  [MISSING] '{exp}' NOT FOUND!")
        missing.append(exp)
    else:
        print(f"  [DUPLICATED] '{exp}' matches {len(matches)} times: {matches}")
        duplicated.append(exp)

if not missing and not duplicated:
    print("ALL 18 LABELS PRESENT EXACTLY ONCE!")
else:
    print("ERRORS IN LABELS!")

print("\n=== CHECK 2: FONT SIZES ===")
too_small = []
for elem in root.iter():
    if elem.tag.endswith('text') or elem.tag.endswith('tspan'):
        fs = elem.attrib.get('font-size')
        if fs:
            size = float(fs)
            if size < 24:
                too_small.append((elem.text, size))
if too_small:
    print(f"Found text smaller than 24px: {too_small}")
else:
    print("All text is >= 24px! (PASS)")

print("\n=== CHECK 3: ARROWS COUNT ===")
paths = [e for e in root.iter() if e.tag.endswith('path') and 'marker-end' in e.attrib]
lines = [e for e in root.iter() if e.tag.endswith('line') and 'marker-end' in e.attrib]
total_arrows = len(paths) + len(lines)
print(f"Total arrows with marker-end: {total_arrows}")
if total_arrows == 7:
    print("Exactly 7 arrows found! (PASS)")
else:
    print(f"Expected 7 arrows, found {total_arrows}!")

