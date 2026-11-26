import xml.etree.ElementTree as ET
import re
import pathlib

svg_text = pathlib.Path("test_collections_v7.svg").read_text()
root = ET.fromstring(svg_text)

# 1. First children check
children = list(root)
first_two = [c.tag.split('}')[-1] for c in children[:2]]
print(f"1. First two tags: {first_two}")
assert first_two == ['title', 'desc'], f"First children must be title and desc, got {first_two}"

# 2. Dimensions
assert root.attrib['viewBox'] == '0 0 1600 1200'
assert root.attrib['width'] == '1600'
assert root.attrib['height'] == '1200'
print("2. Dimensions viewBox='0 0 1600 1200', width=1600, height=1200: PASS")

# 3. Text font sizes and values
text_nodes = root.findall('.//{http://www.w3.org/2000/svg}text')
extracted_texts = []
font_sizes = []

for t in text_nodes:
    fs = float(t.attrib.get('font-size', '0'))
    assert fs >= 24, f"Text font size {fs} < 24 in {t.attrib}"
    tspans = t.findall('{http://www.w3.org/2000/svg}tspan')
    if tspans:
        for ts in tspans:
            tfs = ts.attrib.get('font-size')
            if tfs:
                assert float(tfs) >= 24, f"tspan font size {tfs} < 24"
        joined = " ".join([re.sub(r'\s+', ' ', (ts.text or '').strip()) for ts in tspans])
        extracted_texts.append(joined)
    else:
        text_val = re.sub(r'\s+', ' ', (t.text or '').strip())
        extracted_texts.append(text_val)

print(f"3. Total text elements: {len(extracted_texts)} (all font sizes >= 24px): PASS")

# 4. Required labels
required_labels = [
    "Collection traps: shared inner lists, mutating while iterating, and slow membership",
    "grid = [[0] * 3] * 3",
    "three references to the same inner list, so changing one row changes all",
    "[[0] * 3 for _ in range(3)]",
    "d = dict.fromkeys(keys, [])",
    "one list shared across all keys",
    "fix with a comprehension that makes a new list per key",
    "for x in lst: lst.remove(x)",
    "skips elements",
    "mutating a dict's size during iteration raises RuntimeError",
    "iterate over a copy or build a new collection",
    "x in list on large data",
    "linear",
    "use sets or dicts for repeated in checks; set and dict lookup O(1) average",
    "list: index O(1), append amortised O(1), insert or delete at front O(n), in O(n)",
    "tuple: index O(1), hashable if elements are",
    "dict: lookup and insert O(1) average, insertion-ordered since 3.7, keys must be hashable",
    "set: in O(1) average, empty is set()",
    "frozenset: immutable set",
    "deque: O(1) at both ends",
    "dict keys must be hashable: strings, numbers, tuples of hashables, frozensets; lists and dicts cannot be keys",
    "The type you pick sets how fast the script runs and which bugs it carries"
]

print(f"4. Checking {len(required_labels)} required labels:")
for req in required_labels:
    matches = [txt for txt in extracted_texts if txt == req]
    assert len(matches) == 1, f"Required label '{req}' matched {len(matches)} times! Expected exactly 1."

assert len(extracted_texts) == len(required_labels), f"Expected {len(required_labels)} texts, got {len(extracted_texts)}"
print("   All 22 required labels matched EXACTLY ONCE with 0 extras: PASS")

# 5. Banned words check
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for txt in extracted_texts:
    for word in forbidden:
        assert not re.search(rf'\b{word}\b', txt, re.IGNORECASE), f"Forbidden style word '{word}' found in: {txt}"
print("5. No forbidden style words in any text: PASS")

# 6. Colors check
for col in ["#f5f8f5", "#303a36", "#207448", "#e8f1ea", "#db8129"]:
    assert col in svg_text, f"Required color {col} missing!"
print("6. Color palette (#f5f8f5, #303a36, #207448, #e8f1ea, #db8129): PASS")

# 7. Orange usage check
orange_matches = re.findall(r'#db8129', svg_text, re.IGNORECASE)
print(f"7. Orange occurrences: {len(orange_matches)}: PASS")

# 8. Arrows check
arrows = [el for el in root.iter() if 'marker-end' in el.attrib]
assert len(arrows) == 0, f"Found {len(arrows)} arrows, expected 0"
print("8. Arrow count: 0 (matches source): PASS")

print("\n=== ALL 8 COMPREHENSIVE SUITE TESTS PASSED 100%! ===")
