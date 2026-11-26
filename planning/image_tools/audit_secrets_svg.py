import xml.etree.ElementTree as ET
import re

tree = ET.parse("test_candidate_secrets.svg")
root = tree.getroot()

# 1. First children check: <title> and <desc>
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
assert first_tag == 'title', f"First child must be title, got {first_tag}"
assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"
title = root.find('{http://www.w3.org/2000/svg}title')
desc = root.find('{http://www.w3.org/2000/svg}desc')
assert title.text == "Where a secret can leak in Terraform"
assert desc.text == "Where a secret can leak in Terraform"
print("1. First child <title> and second child <desc>: PASS")

# 2. Dimensions
width = root.get('width')
height = root.get('height')
viewBox = root.get('viewBox')
assert width == "1600"
vb_parts = [float(x) for x in viewBox.split()]
assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
assert 900 <= vb_parts[3] <= 1200
assert int(height) == int(vb_parts[3])
print(f"2. Dimensions width={width}, height={height}, viewBox={viewBox}: PASS")

# 3. Check font-size >= 24
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

print(f"3. Total text elements: {len(text_elements)} (all font-sizes >= 24px)")

# 4. Expected labels
expected_labels = [
    "Where a secret can leak in Terraform",
    "Secret passed to a resource: Terraform must know the value to manage the resource, and whatever it knows it may write down",
    "state file is plain text unless the provider protects it",
    "state bucket: private, encrypted at rest, access controlled; protect it as if it held every password",
    "generated credentials end up in state; convenient because Terraform can read the credential back next run, and the same convenience makes the state a target",
    "write-only arguments in a sensitive object",
    "ephemeral variables declared with ephemeral = true",
    "ephemeral resources",
    "a saved plan file holds the full configuration and may hold sensitive values: treat it as sensitive",
    "say what the state holds, who can read it and what you would change; do not claim the older pattern is safe",
    "prefer write-only or ephemeral secrets"
]

found_texts = [t for t, fs in text_elements]
assert len(found_texts) == len(expected_labels), f"Expected {len(expected_labels)} texts, got {len(found_texts)}"

all_ok = True
for exp in expected_labels:
    cnt = found_texts.count(exp)
    ok = (cnt == 1)
    if not ok:
        all_ok = False
    print(f"   [{'OK' if ok else 'FAIL'}] count={cnt}: '{exp[:50]}...'")

assert all_ok, "Some expected labels failed count == 1 check!"
print("4. All expected labels present exactly once: PASS")

# 5. Check zero extra words
def get_text_exact(elem):
    text = elem.text or ""
    for child in elem:
        text += get_text_exact(child)
        if child.tail:
            text += child.tail
    return text

root_copy = ET.parse("test_candidate_secrets.svg").getroot()
root_copy.remove(root_copy.find('{http://www.w3.org/2000/svg}title'))
root_copy.remove(root_copy.find('{http://www.w3.org/2000/svg}desc'))
rem_text = " ".join(get_text_exact(root_copy).split())
for l in expected_labels:
    norm_l = " ".join(l.split())
    rem_text = rem_text.replace(norm_l, "", 1)
rem_text = " ".join(rem_text.split())
assert rem_text == "", f"Extra text found: '{rem_text}'"
print("5. Exactly zero extra words: PASS")

# 6. Check forbidden style words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"
print("6. No forbidden words found: PASS")

# 7. Check orange count: exactly 1
with open("test_candidate_secrets.svg") as f:
    raw_svg = f.read()
orange_matches = re.findall(r'#db8129', raw_svg, re.IGNORECASE)
print(f"7. Orange #db8129 occurrences: {len(orange_matches)}")
assert len(orange_matches) == 1, f"Expected exactly 1 orange usage, got {len(orange_matches)}"

# 8. Check arrows count: exactly 2
lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
total_arrows = len(lines) + len(paths)
print(f"8. Total arrows with marker-end: {total_arrows}")
assert total_arrows == 2, f"Expected exactly 2 arrows, got {total_arrows}"

print("\nALL 8 STRICT CHECKS PASSED PERFECTLY!")
