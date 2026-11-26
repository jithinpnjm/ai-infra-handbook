import xml.etree.ElementTree as ET
import re
import pathlib
import sys

svg_file = "test_collections_output.svg"
tree = ET.parse(svg_file)
root = tree.getroot()

print("=== 1. Structure Check ===")
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"Child 0: <{first_tag}>, Child 1: <{second_tag}>")
assert first_tag == "title", f"First child must be title, got {first_tag}"
assert second_tag == "desc", f"Second child must be desc, got {second_tag}"

print("\n=== 2. Dimensions Check ===")
viewBox = root.attrib.get("viewBox")
width = root.attrib.get("width")
height = root.attrib.get("height")
print(f"viewBox: {viewBox}, width: {width}, height: {height}")
assert width == "1600"
vb_parts = [float(x) for x in viewBox.split()]
assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
assert 900 <= vb_parts[3] <= 1200
assert float(height) == vb_parts[3]

print("\n=== 3. Font-size >= 24px Check ===")
text_elements = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = "".join(elem.itertext()).strip()
    full_text = re.sub(r'\s+', ' ', full_text)
    fs = elem.attrib.get('font-size')
    assert fs is not None, f"Missing font-size on text '{full_text}'"
    size = float(fs)
    assert size >= 24, f"Text '{full_text}' font-size {size} < 24!"
    for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
        tfs = tsp.attrib.get('font-size')
        if tfs is not None:
            assert float(tfs) >= 24, f"tspan font-size {tfs} < 24 in '{full_text}'"
    text_elements.append((full_text, size))

print(f"Total text elements: {len(text_elements)} (all font-sizes >= 24px)")
for i, (t, fs) in enumerate(text_elements, 1):
    print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

print("\n=== 4. Expected Labels Check ===")
expected_labels = [
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

found_texts = [t for t, fs in text_elements]
print(f"Found texts count: {len(found_texts)}")

all_ok = True
for exp in expected_labels:
    cnt = found_texts.count(exp)
    ok = (cnt == 1)
    if not ok:
        all_ok = False
    print(f"   [{'OK' if ok else 'FAIL'}] count={cnt}: '{exp}'")

assert all_ok, "Some expected labels failed count == 1 check!"

extras = [t for t in found_texts if t not in expected_labels]
print(f"\n5. Extras count: {len(extras)}")
if extras:
    print("   Unexpected extras:", extras)
assert len(extras) == 0, f"Unexpected extra texts found: {extras}"
assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"

print("\n=== 6. Forbidden Words Check ===")
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for w in words:
        assert w not in forbidden, f"Forbidden word '{w}' found in text: '{t}'"

print("PASS: No forbidden style words printed as text.")

print("\n=== 7. Color Palette Check ===")
svg_str = pathlib.Path(svg_file).read_text()
for col in ["#f5f8f5", "#303a36", "#207448", "#e8f1ea", "#db8129"]:
    assert col in svg_str, f"Color {col} missing!"

orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"Orange #db8129 occurrences: {len(orange_matches)}")
assert len(orange_matches) >= 1, "Orange not used!"

print("\n=== 8. Arrow count check ===")
# Prompt has 0 arrows described
arrow_paths = [el for el in root.iter() if 'marker-end' in el.attrib]
print(f"Arrows found: {len(arrow_paths)} (expected 0)")
assert len(arrow_paths) == 0, "No arrows were in the source specification!"

print("\nALL AUDIT CHECKS PASSED!")
