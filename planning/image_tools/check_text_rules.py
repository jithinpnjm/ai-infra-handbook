import xml.etree.ElementTree as ET

tree = ET.parse('test_candidate_api_batches.svg')
root = tree.getroot()

# Style instruction words to forbid as standalone text or unintended words
forbidden_words = ["orange", "green", "grey", "bold", "monospace", "arrow", "Left", "Right side", "strip", "filter", "Bottom bar"]

# Check all text elements
all_text_elements = list(root.iter('{http://www.w3.org/2000/svg}text'))

print(f"Total <text> elements: {len(all_text_elements)}")

for elem in all_text_elements:
    fs = float(elem.attrib.get('font-size', 0))
    raw = "".join(elem.itertext()).strip()
    print(f"[{fs:2.0f}px] '{raw}'")
    assert fs >= 24, f"Font size {fs} < 24 for: {raw}"
    
    # Check forbidden words
    words = raw.split()
    for w in words:
        clean_w = w.strip("():,;.")
        if clean_w.lower() in ["orange", "grey"]:
            raise AssertionError(f"Forbidden style word found: {clean_w} in '{raw}'")

print("\nSUCCESS: All font sizes >= 24px, no forbidden style words!")
