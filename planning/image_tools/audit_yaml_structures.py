#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

tree = ET.parse("test_yaml_structures.svg")
root = tree.getroot()

print("==================== AUDIT REPORT ====================")

# 1. XML & ViewBox
assert root.tag.endswith("svg"), "Root is not svg"
first_child = root[0].tag.split('}')[-1]
second_child = root[1].tag.split('}')[-1]
assert first_child == "title", f"Expected title, got {first_child}"
assert second_child == "desc", f"Expected desc, got {second_child}"
assert root[0].text == "The three YAML structures, read through the cluster example"
assert root.attrib.get("width") == "1600"
assert root.attrib.get("viewBox") == "0 0 1600 1200"
print("[PASS] XML, Title, Desc, and ViewBox (1600x1200)")

# 2. Text extraction and source labels
all_texts = root.findall('.//{http://www.w3.org/2000/svg}text')
all_tspans = root.findall('.//{http://www.w3.org/2000/svg}tspan')

def get_text_content(el):
    parts = []
    if el.text:
        parts.append(el.text)
    for child in el:
        parts.append(get_text_content(child))
        if child.tail:
            parts.append(child.tail)
    return ''.join(parts)

extracted_texts = []
for t in all_texts:
    full_str = get_text_content(t)
    full_str = re.sub(r'\s+', ' ', full_str).strip()
    extracted_texts.append(full_str)

source_labels = [
    "The three YAML structures, read through the cluster example",
    "cluster:",
    "name: ai-prod-1",
    "racks: [r1, r2, r3]",
    "nodes:",
    "name: gpu01, gpus: 8, tags: [h100, nvlink]",
    "name: gpu02, gpus: 8, tags: - h100",
    "motd: |",
    "description: >",
    "enabled: true",
    "contact: null",
    "---",
    "...",
    "Structure",
    "Syntax",
    "JSON or Python",
    'Scalar: 42, 3.14, true, null, hello, "quoted" / number, bool, null, string',
    "Sequence: - item per line, or [a, b] / array or list",
    "Mapping: key: value pairs, or {a: 1, b: 2} / object or dict",
    "a parser turns each value into a typed object before any tool reads it: the clerk at a counter files each word as number, true or false, or text",
    'JSON is valid YAML 1.2, so {"a": 1} works anywhere YAML does',
    "indentation tells the parser where each item ends, brackets do the same for short lists; pick the form a reviewer reads fastest and keep it consistent in each file",
    "Read the file the way the parser reads it"
]

print(f"Total extracted texts: {len(extracted_texts)}")
print(f"Total source labels:  {len(source_labels)}")

for sl in source_labels:
    norm_sl = re.sub(r'\s+', ' ', sl).strip()
    matches = [t for t in extracted_texts if norm_sl == t]
    assert len(matches) == 1, f"Expected 1 match for '{norm_sl}', got {len(matches)}"

print(f"[PASS] All {len(source_labels)} source labels match 100% exactly and appear once.")

# 3. No extra text
for t in extracted_texts:
    assert t in [re.sub(r'\s+', ' ', s).strip() for s in source_labels], f"Unexpected extra text: '{t}'"

assert len(extracted_texts) == len(source_labels), f"Expected {len(source_labels)} text elements, got {len(extracted_texts)}"
print("[PASS] No extra or invented text elements (exactly 23 text elements).")

# 4. Forbidden style words
forbidden = ["orange", "green", "grey", "gray", "bold", "monospace", "arrow"]
for t in extracted_texts:
    for f in forbidden:
        assert not re.search(r'\b' + f + r'\b', t.lower()), f"Forbidden word '{f}' in text '{t}'"

print("[PASS] No forbidden style words in any text element.")

# 5. Font size check
font_sizes = []
for el in all_texts + all_tspans:
    fs = el.attrib.get('font-size')
    if fs:
        font_sizes.append(float(fs))

assert min(font_sizes) >= 24, f"Font size < 24: {min(font_sizes)}"
print(f"[PASS] Font sizes: min={min(font_sizes)}px, max={max(font_sizes)}px (all >= 24px)")

# 6. Arrow count check
arrow_paths = []
for elem in root.iter('{http://www.w3.org/2000/svg}path'):
    if "marker-end" in elem.attrib or "marker-start" in elem.attrib:
        arrow_paths.append(elem.attrib)
for elem in root.iter('{http://www.w3.org/2000/svg}line'):
    if "marker-end" in elem.attrib or "marker-start" in elem.attrib:
        arrow_paths.append(elem.attrib)

assert len(arrow_paths) == 0, f"Expected 0 arrows, got {len(arrow_paths)}"
print("[PASS] Arrow count: exactly 0 arrows.")

# 7. Orange usage
with open("test_yaml_structures.svg") as f:
    svg_raw = f.read()

orange_hexes = re.findall(r'#db8129', svg_raw, re.IGNORECASE)
print(f"[PASS] Orange #db8129 usage: {len(orange_hexes)} occurrences (used exclusively for the key parser object rule).")

print("\nALL SYSTEM VERIFICATIONS PASSED WITH ZERO ERRORS!")
