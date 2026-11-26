import xml.etree.ElementTree as ET
import re

svg_path = "test_candidate_source_of_truth.svg"
tree = ET.parse(svg_path)
root = tree.getroot()

# 1. First children check: <title> and <desc>
children = list(root)
first_tag = children[0].tag.split("}")[-1]
second_tag = children[1].tag.split("}")[-1]
print(f"1. First child: <{first_tag}>, Second child: <{second_tag}>")
assert first_tag == "title", f"First child must be title, got {first_tag}"
assert second_tag == "desc", f"Second child must be desc, got {second_tag}"

# 2. Dimensions
width = root.get("width")
viewBox = root.get("viewBox")
height = root.get("height")
print(f"2. Dimensions: width={width}, height={height}, viewBox={viewBox}")
assert width == "1600"
assert viewBox == "0 0 1600 1200"
assert height == "1200"

# 3. Check font-size >= 24 on all text and tspans
text_elements = []
for elem in root.iter("{http://www.w3.org/2000/svg}text"):
    full_text = "".join(elem.itertext()).strip()
    full_text = re.sub(r"\s+", " ", full_text)
    fs = elem.attrib.get("font-size")
    assert fs is not None, f"Missing font-size on text: {full_text}"
    size = float(fs)
    assert size >= 24, f"Text font-size {size} < 24: {full_text}"
    for tsp in elem.iter("{http://www.w3.org/2000/svg}tspan"):
        tfs = tsp.attrib.get("font-size")
        if tfs is not None:
            assert float(tfs) >= 24, f"tspan font-size {tfs} < 24 in {full_text}"
    text_elements.append((full_text, size))

print(f"\n3. Total text elements: {len(text_elements)}")
for i, (t, fs) in enumerate(text_elements, 1):
    print(f"   {i:2d}. [{fs:2.0f}px] {t}")

# 4. Expected labels
expected_labels = [
    "Who owns the list of machines: the source of truth",
    "inventory (generated)",
    "NetBox or Nautobot: devices, interfaces, IPs, racks, cables and tags",
    "cloud or Terraform state: the cloud side",
    "NVIDIA Base Command Manager (BCM): node categories and provisioning data",
    "the scheduler: Slurm node definitions",
    "a node pulled for RMA last week: the spreadsheet still lists it as healthy, so a driver rollout sends it a job it cannot run; the inventory says gpu77 exists but it was RMA'd",
    "a generated inventory does not drift from the fleet; after a rack is re-cabled and two nodes swap switch ports, a generated inventory reflects the new cabling after its next sync; enables cabling-aware automation such as checking which rail each NIC connects to",
    "treat the inventory source as code: review its changes, validate it for unique names and required fields, and write tests that fail the build when a host lacks a role or rack; a generator that quietly writes an empty rack field looks fine, and the test is the only thing that catches it before the rollout",
    "The difference is who keeps the list true"
]

found_texts = [t for t, fs in text_elements]
print(f"\n4. Checking {len(expected_labels)} expected labels:")
all_ok = True
for exp in expected_labels:
    cnt = found_texts.count(exp)
    ok = (cnt == 1)
    if not ok:
        all_ok = False
    status = "OK" if ok else "FAIL"
    print(f"   [{status}] count={cnt}: {exp[:60]}...")

assert all_ok, "Some expected labels failed count == 1 check!"

extras = [t for t in found_texts if t not in expected_labels]
print(f"\nExtra texts: {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"

# 5. Check forbidden words
forbidden = ["orange", "green", "grey", "gray", "bold", "monospace", "arrow", "cylinder", "folder", "icon", "callout", "sub-line", "subline", "takeaway"]
for t in found_texts:
    words = re.findall(r"\b[a-zA-Z]+\b", t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"

print("\n5. No forbidden words found! (PASS)")

# 6. Check orange count
with open(svg_path, "r", encoding="utf-8") as f:
    svg_str = f.read()
orange_matches = re.findall(r"#db8129", svg_str, re.IGNORECASE)
print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
assert len(orange_matches) >= 1, "Missing orange accent!"

# 7. Check arrows count
arrow_markers = re.findall(r"marker-end=\"url\(#arrow\)\"", svg_str)
print(f"\n7. Total arrows with marker-end: {len(arrow_markers)}")
assert len(arrow_markers) == 4, f"Expected 4 arrows, got {len(arrow_markers)}"

print("\nALL AUDIT CHECKS PASSED PERFECTLY!")
