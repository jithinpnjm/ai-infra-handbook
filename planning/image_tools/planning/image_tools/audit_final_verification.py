import xml.etree.ElementTree as ET
import re

tree = ET.parse("test_final_candidate.svg")
root = tree.getroot()

# 1. Structure: <title> and <desc>
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. Children: <{first_tag}>, <{second_tag}>")
assert first_tag == "title", f"First child must be title, got {first_tag}"
assert second_tag == "desc", f"Second child must be desc, got {second_tag}"

# 2. Dimensions
W = float(root.attrib.get("width"))
H = float(root.attrib.get("height"))
vb = [float(x) for x in root.attrib.get("viewBox").split()]
print(f"2. Dimensions: W={W}, H={H}, viewBox={vb}")
assert W == 1600
assert 900 <= H <= 1200
assert vb == [0, 0, 1600, H]

# 3. Font sizes >= 24
text_elements = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = "".join(elem.itertext()).strip()
    full_text = re.sub(r'\s+', ' ', full_text)
    fs = float(elem.attrib.get('font-size', '0'))
    tspans = list(elem.iter('{http://www.w3.org/2000/svg}tspan'))
    if fs == 0 and tspans:
        fs = float(tspans[0].attrib.get('font-size', '0'))
    assert fs >= 24, f"Font size {fs} < 24 for '{full_text}'"
    for tsp in tspans:
        tfs = tsp.attrib.get('font-size')
        if tfs is not None:
            assert float(tfs) >= 24, f"tspan font size {tfs} < 24"
    text_elements.append((full_text, fs))

print(f"3. Font sizes: Total text elements = {len(text_elements)} (all >= 24px)")

# 4. Expected labels
expected_labels = [
    "Numeric types and the quiet traps they hide",
    "int: arbitrary precision, no overflow; 0x1f, 0o17, 0b101, 1_000_000",
    'float: IEEE 754 double, about 15 to 17 significant digits; 0.1 + 0.2 != 0.3, use math.isclose; float("inf"), nan never equals itself',
    "complex: 3 + 4j, rarely used in infra",
    "bool: subclass of int, True == 1, True + True == 2",
    "decimal.Decimal: exact decimal arithmetic for money and billing; construct from strings",
    "fractions.Fraction: exact rational numbers",
    "Operators",
    "/ is always true division (float)",
    "// floors toward negative infinity: -7 // 2 == -4",
    "% takes the sign of the divisor",
    "divmod(a, b)",
    "round() rounds half to even: round(2.5) == 2",
    "chained comparison 1 <= x < 10",
    "bitwise & | ^ ~ << >> for IP and mask: 0xFF & addr",
    "random is not for security, use secrets",
    "disk_bytes / gib with gib = 1024 ** 3 gives 3577.0 GiB for 3_840_755_982_336 bytes",
    "free_pct = 100 * free / total if total else 0.0 guards divide by zero",
    "timeout = base * 2 ** attempt",
    "pages, rem = divmod(total_items, 100)",
    "Compare floats with tolerance, use // versus / on purpose, remember bool is an int, and use the ipaddress module instead of string IP arithmetic"
]

found_texts = [t for t, fs in text_elements]
print(f"4. Checking {len(expected_labels)} expected labels against {len(found_texts)} found:")
for exp in expected_labels:
    cnt = found_texts.count(exp)
    assert cnt == 1, f"Expected '{exp}' count==1, got {cnt}"

extras = [t for t in found_texts if t not in expected_labels]
print(f"   Extras: {extras}")
assert len(extras) == 0, f"Unexpected extra texts: {extras}"
print("   All expected labels matched 1-to-1! Exactly zero extra texts!")

# 5. Forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'"
print("5. Forbidden words: PASS!")

# 6. Orange check (#db8129)
svg_str = open("test_final_candidate.svg").read()
oranges = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"6. Orange count: {len(oranges)}")
assert 1 <= len(oranges) <= 5, f"Unexpected orange count: {len(oranges)}"

# 7. No arrows
markers = re.findall(r'marker-end', svg_str)
print(f"7. Arrow markers count: {len(markers)}")
assert len(markers) == 0, f"Expected 0 arrows, got {len(markers)}"

# 8. Check no extra words across whole SVG text
raw_text = " ".join("".join(root.itertext()).split())
# remove title and desc from raw_text
t_elem = root.find('{http://www.w3.org/2000/svg}title')
d_elem = root.find('{http://www.w3.org/2000/svg}desc')
t_str = " ".join(t_elem.text.split())
d_str = " ".join(d_elem.text.split())
raw_text = raw_text.replace(t_str, "", 1)
raw_text = raw_text.replace(d_str, "", 1)

rem = raw_text
for lbl in expected_labels:
    norm = " ".join(lbl.split())
    assert norm in rem, f"Could not find label in raw text: '{norm}'"
    rem = rem.replace(norm, "", 1)

rem = rem.strip()
print(f"8. Remaining text after removing all labels: '{rem}'")
assert rem == "", f"Extra text found in SVG: '{rem}'"

print("\n==============================================")
print(">>> ALL 8 STRICT CHECKS PASSED FLAWLESSLY! <<<")
print("==============================================")
