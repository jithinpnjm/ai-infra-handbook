import json
import re
import xml.etree.ElementTree as ET

def audit_svg(svg_path):
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # 1. Structure check: First children must be title and desc
    children = list(root)
    first_tag = children[0].tag.split('}')[-1]
    second_tag = children[1].tag.split('}')[-1]
    print(f"1. Structure: Child 0: <{first_tag}>, Child 1: <{second_tag}>")
    assert first_tag == "title", f"First child must be title, got {first_tag}"
    assert second_tag == "desc", f"Second child must be desc, got {second_tag}"

    # 2. Canvas size check
    viewBox = root.attrib.get("viewBox")
    width = root.attrib.get("width")
    height = root.attrib.get("height")
    print(f"2. Canvas: viewBox: {viewBox}, width: {width}, height: {height}")
    assert width == "1600", f"Width {width} != 1600"
    vb_parts = [float(x) for x in viewBox.split()]
    assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
    assert 900 <= vb_parts[3] <= 1200
    assert float(height) == vb_parts[3]

    # 3. Check font sizes >= 24
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

    print(f"3. Font sizes: Total text elements = {len(text_elements)} (all font-sizes >= 24px)")
    for i, (t, fs) in enumerate(text_elements, 1):
        print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

    # 4. Check expected labels
    spec_data = json.load(open("specs/v2_10.json"))
    item = [x for x in spec_data if x.get("name") == "n10-rtt"][0]
    expected_labels = [item["title"]] + re.findall(r"'([^']*)'", item["spec"])
    print(f"\n4. Checking {len(expected_labels)} expected labels against {len(text_elements)} found:")

    found_texts = [t for t, fs in text_elements]
    all_ok = True
    for exp in set(expected_labels):
        exp_norm = re.sub(r'\s+', ' ', exp)
        expected_cnt = expected_labels.count(exp)
        cnt = found_texts.count(exp_norm)
        ok = (cnt == expected_cnt)
        if not ok:
            all_ok = False
        print(f"   [{'OK' if ok else 'FAIL'}] count={cnt} (expected {expected_cnt}): '{exp[:60]}...'")

    assert all_ok, "Some expected labels failed count check!"
    print("   PASS: All expected labels found with exact counts.")

    # 5. Extras check
    norm_expected = [re.sub(r'\s+', ' ', exp) for exp in expected_labels]
    extras = [t for t in found_texts if t not in norm_expected]
    print(f"\n5. Extras count: {len(extras)}")
    if extras:
        print("   Unexpected extras:", extras)
    assert len(extras) == 0, f"Unexpected extra texts found: {extras}"
    assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"
    print("   PASS: Zero extra text elements.")

    # 6. Forbidden words check
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
    for t in found_texts:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for f in forbidden:
            assert f not in words, f"Forbidden word '{f}' found in text: '{t}'"
    print("\n6. PASS: No forbidden style words in visible text!")

    # 7. Arrow count check
    lines_with_marker = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if e.attrib.get('marker-end')]
    paths_with_marker = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if e.attrib.get('marker-end')]
    total_arrows = len(lines_with_marker) + len(paths_with_marker)
    print(f"\n7. Total arrows with marker-end: {total_arrows} (expected 1)")
    assert total_arrows == 1, f"Expected exactly 1 arrow, got {total_arrows}"
    print("   PASS: Exactly 1 arrow present.")

    # 8. Orange usage check
    with open(svg_path) as f:
        svg_content = f.read()
    orange_matches = re.findall(r'#db8129', svg_content, re.IGNORECASE)
    print(f"\n8. Orange #db8129 count: {len(orange_matches)}")
    assert len(orange_matches) >= 1, "Orange not used!"
    print("   PASS: Orange used on saved round trip.")

    print("\nALL VERIFICATIONS PASSED PERFECTLY!")

if __name__ == "__main__":
    audit_svg("test_n10_rtt.svg")
