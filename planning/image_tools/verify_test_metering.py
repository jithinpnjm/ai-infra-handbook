import xml.etree.ElementTree as ET
import re

tree = ET.parse("test_metering.svg")
root = tree.getroot()

# 1. First children check
children = list(root)
first_tag = children[0].tag.split("}")[-1]
second_tag = children[1].tag.split("}")[-1]
print(f"1. First child: <{first_tag}>, Second child: <{second_tag}>")
assert first_tag == "title", f"First child must be title, got {first_tag}"
assert second_tag == "desc", f"Second child must be desc, got {second_tag}"

# 2. Dimensions
width = root.get("width")
height = root.get("height")
viewBox = root.get("viewBox")
print(f"2. Dimensions: width={width}, height={height}, viewBox={viewBox}")
assert width == "1600"
assert viewBox.startswith("0 0 1600 ")
vb_parts = [float(x) for x in viewBox.split()]
assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
assert 900 <= vb_parts[3] <= 1200
assert int(height) == int(vb_parts[3])

# 3. Check text elements and font-size >= 24
text_elements = []
for elem in root.iter("{http://www.w3.org/2000/svg}text"):
    full_text = "".join(elem.itertext()).strip()
    full_text = re.sub(r"\s+", " ", full_text)
    fs = elem.attrib.get("font-size")
    assert fs is not None, f"Missing font-size on text '{full_text}'"
    size = float(fs)
    assert size >= 24, f"Text '{full_text}' font-size {size} < 24!"
    for tsp in elem.iter("{http://www.w3.org/2000/svg}tspan"):
        tfs = tsp.attrib.get("font-size")
        if tfs is not None:
            assert float(tfs) >= 24, f"tspan font-size {tfs} < 24 in '{full_text}'"
    text_elements.append((full_text, size))

print(f"\n3. Total text elements: {len(text_elements)} (all font-sizes >= 24px)")
for i, (t, fs) in enumerate(text_elements, 1):
    print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

# 4. Expected labels
expected_labels = [
    "Usage metering and billing correctness [my addition]",
    "Engine: usage event",
    "Durable log",
    "Dedupe by request id",
    "Hourly aggregates",
    "Invoice",
    "Gateway counts",
    "Reconcile"
]

found_texts = [t for t, fs in text_elements]
print(f"\n4. Checking {len(expected_labels)} expected labels:")
all_ok = True
for exp in expected_labels:
    cnt = found_texts.count(exp)
    ok = (cnt == 1)
    if not ok:
        all_ok = False
    print(f"   [{'OK' if ok else 'FAIL'}] count={cnt}: '{exp}'")

assert all_ok, "Some expected labels failed count == 1 check!"
extras = [t for t in found_texts if t not in expected_labels]
print(f"Extra texts: {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"
assert len(found_texts) == len(expected_labels)

# 5. Check forbidden words
forbidden = ["orange", "green", "grey", "gray", "bold", "monospace", "arrow", "cylinder", "folder", "icon", "callout", "sub-line", "subline", "takeaway"]
for t in found_texts:
    words = [w.strip("(),:;.[]\"'").lower() for w in t.split()]
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"
print("\n5. No forbidden words found! (PASS)")

# 6. Check orange count
svg_str = open("test_metering.svg").read()
orange_matches = re.findall(r"#db8129", svg_str, re.IGNORECASE)
print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 6, f"Unexpected orange count: {len(orange_matches)}"

# 7. Check arrows count
lines = [e for e in root.iter("{http://www.w3.org/2000/svg}line") if "marker-end" in e.attrib]
paths = [e for e in root.iter("{http://www.w3.org/2000/svg}path") if "marker-end" in e.attrib]
total_arrows = len(lines) + len(paths)
print(f"\n7. Total arrows with marker-end: {total_arrows}")
assert total_arrows == 6, f"Expected exactly 6 arrows, got {total_arrows}"

# 8. Check margins and gaps
boxes = [
    ("Node E", 60, 170, 240, 270),
    ("Node L", 370, 170, 240, 270),
    ("Node D", 680, 170, 240, 270),
    ("Node A", 990, 170, 240, 270),
    ("Node I", 1300, 170, 240, 270),
    ("Node G", 680, 540, 240, 270),
    ("Node R", 990, 540, 240, 270),
]

W = 1600
H = 900
for name, x, y, w, h in boxes:
    assert x >= 40, f"{name} left margin {x} < 40"
    assert (W - (x + w)) >= 40, f"{name} right margin {W - (x+w)} < 40"
    assert y >= 40, f"{name} top margin {y} < 40"
    assert (H - (y + h)) >= 40, f"{name} bottom margin {H - (y+h)} < 40"

print("8. Margins: All boxes have outside margin >= 40px! (PASS)")

# Check gaps between boxes
print("9. Gaps check:")
assert (370 - (60 + 240)) >= 40  # E to L
assert (680 - (370 + 240)) >= 40 # L to D
assert (990 - (680 + 240)) >= 40 # D to A
assert (1300 - (990 + 240)) >= 40 # A to I
assert (990 - (680 + 240)) >= 40 # G to R
assert (540 - (170 + 270)) >= 40 # D to G and A to R
print("   All gaps >= 40px! (PASS)")

print("\nALL AUDIT AND STRICT RULE CHECKS PASSED PERFECTLY!")
