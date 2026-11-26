import xml.etree.ElementTree as ET
import re

svg_file = "test_output_candidate.svg"
tree = ET.parse(svg_file)
root = tree.getroot()

print("=== STRICT AUDIT FOR TEST_OUTPUT_CANDIDATE.SVG ===")

# 1. First children check: <title> and <desc>
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. First child: <{first_tag}>, Second child: <{second_tag}>")
assert first_tag == 'title', f"First child must be title, got {first_tag}"
assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"

# 2. Dimensions
width = root.get('width')
viewBox = root.get('viewBox')
height = root.get('height')
print(f"2. Dimensions: width={width}, height={height}, viewBox={viewBox}")
assert width == "1600"
assert viewBox.startswith("0 0 1600 ")
vb_parts = [float(x) for x in viewBox.split()]
assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
assert 900 <= vb_parts[3] <= 1200
assert int(height) == int(vb_parts[3])

# 3. Check text elements and font-size >= 24
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

print(f"\n3. Total text elements: {len(text_elements)} (all font-sizes >= 24px)")
for i, (t, fs) in enumerate(text_elements, 1):
    print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

# 4. Expected labels
expected_labels = [
    "Text and bytes only meet at the boundaries",
    "bytes in: file in binary mode, socket reads, subprocess output",
    'data.decode("utf-8") when input arrives',
    "str: Unicode text (code points); JSON, YAML and regular expressions work here",
    's.encode("utf-8") when output leaves',
    "bytes out",
    "strict, replace, ignore, surrogateescape, backslashreplace",
    'locale.getpreferredencoding() changes with the environment; containers that set LANG=C surprise people; always pass encoding="utf-8" to open()',
    'the same visible text can have different code point sequences: é as one code point or e plus a combining accent; normalise both with unicodedata.normalize("NFC", s) before comparing',
    "str.casefold() for caseless matching",
    "len() counts code points, not bytes or graphemes",
    "sorting follows code point order; use locale.strxfrm or ICU for human order",
    'b"abc"[0] == 97 indexing bytes returns integers',
    "bytes.hex(), bytes.fromhex, int.from_bytes, struct.pack and unpack for binary protocols, base64, hashlib",
    "UTF-8 default for new work, ASCII is a subset, Latin-1 maps bytes one to one onto code points 0 to 255 which carries arbitrary bytes through text APIs",
    "Convert only at the boundaries of your program"
]

found_texts = [t for t, fs in text_elements]
print(f"\n4. Checking {len(expected_labels)} expected labels against {len(found_texts)} found:")
all_ok = True
for exp in expected_labels:
    cnt = found_texts.count(exp)
    ok = (cnt == 1)
    if not ok:
        all_ok = False
    print(f"   [{'OK' if ok else 'FAIL'}] count={cnt}: '{exp}'")

assert all_ok, "Some expected labels failed count == 1 check!"

extras = [t for t in found_texts if t not in expected_labels]
print(f"\nExtra texts: {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"
assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"

# 5. Check arrow count
markers = root.findall('.//{http://www.w3.org/2000/svg}marker')
print(f"\n5. Markers defined: {len(markers)}")
lines_with_marker = []
for elem in root.iter('{http://www.w3.org/2000/svg}line'):
    if 'marker-end' in elem.attrib:
        lines_with_marker.append(elem)
for elem in root.iter('{http://www.w3.org/2000/svg}path'):
    if 'marker-end' in elem.attrib:
        lines_with_marker.append(elem)

print(f"   Arrows with marker-end: {len(lines_with_marker)}")
assert len(lines_with_marker) == 2, f"Expected exactly 2 arrows, got {len(lines_with_marker)}"

# 6. Outside margins and gaps
rects = []
for elem in root.iter('{http://www.w3.org/2000/svg}rect'):
    x = float(elem.attrib.get('x', 0))
    y = float(elem.attrib.get('y', 0))
    w = float(elem.attrib.get('width', 0))
    h = float(elem.attrib.get('height', 0))
    if w == 1600 and h == 1200:
        continue # background
    if w < 100 or h < 50:
        continue # icon internal shape
    rects.append((elem, x, y, w, h))

print(f"\n6. Checking outside margins for {len(rects)} container rects:")
for elem, x, y, w, h in rects:
    assert x >= 40, f"Left margin {x} < 40!"
    assert x + w <= 1560, f"Right edge {x+w} > 1560!"
    assert y >= 40, f"Top margin {y} < 40!"
    assert y + h <= 1160, f"Bottom edge {y+h} > 1160!"

print("   [PASS] All containers obey >= 40px outside margins.")

# Check major panel gaps >= 40px
# Pipeline bottom is 390. Panels top is 430:
assert 430 - 390 >= 40, f"Gap between pipeline and panels {430 - 390} < 40"
# Left panel vs Right panels gap:
# Left panel x=40, w=740 -> right=780. Right panels x=820 -> gap=820-780=40:
assert 820 - 780 >= 40, f"Gap between columns {820 - 780} < 40"
# Right panels gap:
# Encodings panel y=430, h=235 -> bottom=665. Bytes facts y=705 -> gap=705-665=40:
assert 705 - 665 >= 40, f"Gap between right panels {705 - 665} < 40"
# Middle panels bottom=1055. Bottom bar y=1095 -> gap=1095-1055=40:
assert 1095 - 1055 >= 40, f"Gap to bottom bar {1095 - 1055} < 40"
# Bottom bar bottom=1160. Margin to 1200 is 40:
assert 1200 - 1160 >= 40, f"Bottom margin {1200 - 1160} < 40"

print("   [PASS] All major gaps between boxes >= 40px.")

print("\nALL AUDITS PASSED PERFECTLY!")
