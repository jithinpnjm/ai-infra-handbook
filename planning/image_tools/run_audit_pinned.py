import xml.etree.ElementTree as ET
import re, json, pathlib

def audit(svg_path):
    print(f"=== Auditing {svg_path} ===")
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # 1. First children check: <title> and <desc>
    children = list(root)
    first_tag = children[0].tag.split('}')[-1]
    second_tag = children[1].tag.split('}')[-1]
    print(f"1. Children: <{first_tag}>, <{second_tag}>")
    assert first_tag == "title", f"First child must be <title>, got <{first_tag}>"
    assert second_tag == "desc", f"Second child must be <desc>, got <{second_tag}>"
    print("   PASS: First children are <title> and <desc>")

    # 2. Dimensions and canvas check
    width = root.attrib.get("width")
    height = root.attrib.get("height")
    viewBox = root.attrib.get("viewBox")
    print(f"2. Dimensions: width={width}, height={height}, viewBox={viewBox}")
    assert width == "1600", f"Width must be 1600, got {width}"
    assert viewBox.startswith("0 0 1600 "), f"viewBox must start with '0 0 1600 ', got {viewBox}"
    vb_parts = [float(x) for x in viewBox.split()]
    assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
    assert 900 <= vb_parts[3] <= 1200, f"Height {vb_parts[3]} outside 900..1200"
    assert float(height) == vb_parts[3], f"height {height} != viewBox height {vb_parts[3]}"
    print("   PASS: Canvas dimensions and viewBox valid")

    # 3. Text font-size >= 24px everywhere
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

    # 4. Expected labels fidelity
    data = json.load(open('specs/p3_01_17.json'))
    spec_item = [x for x in data if x.get('name') == 'p3-0117-pinned-path'][0]
    expected_labels = [spec_item['title']] + re.findall(r"'([^']*)'", spec_item['spec'])
    
    found_texts = [t for t, fs in text_elements]
    print(f"\n4. Checking {len(expected_labels)} expected labels against {len(found_texts)} found:")
    
    for exp in set(expected_labels):
        exp_norm = re.sub(r'\s+', ' ', exp)
        expected_cnt = expected_labels.count(exp)
        cnt = found_texts.count(exp_norm)
        print(f"   [{'PASS' if cnt == expected_cnt else 'FAIL'}] count={cnt} (expected {expected_cnt}): '{exp[:60]}...'")
        assert cnt == expected_cnt, f"Expected '{exp}' count {expected_cnt}, got {cnt}"

    assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"
    print("   PASS: All expected labels found with exact counts!")

    # 5. Extras check
    norm_expected = [re.sub(r'\s+', ' ', exp) for exp in expected_labels]
    extras = [t for t in found_texts if t not in norm_expected]
    print(f"\n5. Extras count: {len(extras)}")
    if extras:
        print("   Unexpected extras:", extras)
    assert len(extras) == 0, f"Unexpected extra texts found: {extras}"
    print("   PASS: Zero extra text elements")

    # 6. Forbidden words check
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
    for t in found_texts:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for f in forbidden:
            assert f not in words, f"Forbidden word '{f}' in '{t}'!"
    print("\n6. PASS: No forbidden words found")

    # 7. Orange count
    svg_str = open(svg_path).read()
    orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
    print(f"\n7. Orange #db8129 occurrences: {len(orange_matches)}")
    assert 1 <= len(orange_matches) <= 8, f"Unexpected orange count: {len(orange_matches)}"
    print("   PASS: Orange used selectively")

    # 8. Check arrows count
    lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
    paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
    total_arrows = len(lines) + len(paths)
    print(f"\n8. Total arrows: {total_arrows}")
    assert total_arrows == 5, f"Expected 5 arrows, got {total_arrows}"
    print("   PASS: Arrow count matches source (5 arrows)")

    # 9. Required colors check
    assert "#f5f8f5" in svg_str
    assert "#303a36" in svg_str
    assert "#207448" in svg_str
    assert "#e8f1ea" in svg_str
    assert "#db8129" in svg_str
    print("\n9. PASS: All required colors present")

    # 10. Check no image / script
    assert not any(el.tag.endswith('image') for el in root.iter()), "No <image> allowed"
    assert not any(el.tag.endswith('script') for el in root.iter()), "No <script> allowed"
    print("\n10. PASS: Fully self-contained vector")

    print("\n==========================================")
    print("ALL AUDIT CHECKS PASSED WITH 100% SUCCESS!")
    print("==========================================")

if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else 'candidate_pinned_path.svg'
    audit(target)
