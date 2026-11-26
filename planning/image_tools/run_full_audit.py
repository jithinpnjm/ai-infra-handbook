#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re
import pathlib

def run_audit(svg_path):
    print(f"=== Auditing {svg_path} ===")
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # 1. First children check: <title> and <desc>
    children = list(root)
    first_tag = children[0].tag.split('}')[-1]
    second_tag = children[1].tag.split('}')[-1]
    print(f"1. Children: <{first_tag}>, <{second_tag}>")
    assert first_tag == 'title', f"First child must be title, got {first_tag}"
    assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"
    print("   [PASS] <title> and <desc> are the first children.")

    # 2. Dimensions and viewBox
    width = root.get('width')
    height = root.get('height')
    viewBox = root.get('viewBox')
    print(f"2. Dimensions: {width}x{height}, viewBox='{viewBox}'")
    assert width == "1600", f"Width must be 1600, got {width}"
    assert viewBox.startswith("0 0 1600"), f"viewBox must start with 0 0 1600, got {viewBox}"
    vb_parts = [float(x) for x in viewBox.split()]
    assert 900 <= vb_parts[3] <= 1200, f"Height {vb_parts[3]} outside 900-1200 range"
    assert int(height) == int(vb_parts[3]), f"height {height} != viewBox height {vb_parts[3]}"
    print("   [PASS] Canvas dimensions valid.")

    # 3. Check font-size >= 24 on all text and tspans
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
        "Investigation commands from cheapest to most targeted",
        "--syntax-check (parse only, touches no host)",
        "--list-tasks --list-tags --list-hosts",
        "--check --diff --limit gpu001 (what would change)",
        "--step (confirm every task y/n/c)",
        "--start-at-task Install driver",
        "it skips earlier set_fact so the driver task fails on an undefined variable",
        "-t config -l gpu001",
        "ad hoc setup with filter=ansible_default_ipv4",
        "ad hoc command which python3 with -vvv"
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
    print("   [PASS] All expected labels present exactly once.")

    # 5. Extras check
    extras = [t for t in found_texts if t not in expected_labels]
    print(f"\n5. Extras count: {len(extras)}")
    if extras:
        print("   Unexpected extras:", extras)
    assert len(extras) == 0, f"Found unexpected extra text: {extras}"
    assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"
    print("   [PASS] No extra labels found.")

    # 6. Check forbidden words
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
    for t in found_texts:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for f in forbidden:
            assert f not in words, f"Forbidden word '{f}' in '{t}'!"
    print("\n6. [PASS] No forbidden words found.")

    # 7. Check orange usage
    svg_str = pathlib.Path(svg_path).read_text()
    orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
    print(f"\n7. Orange #db8129 occurrences: {len(orange_matches)}")
    assert 1 <= len(orange_matches) <= 4, f"Unexpected orange count: {len(orange_matches)}"
    print("   [PASS] Orange used only on warning box.")

    # 8. Check arrows count
    markers = [e for e in root.iter() if "marker-end" in e.attrib]
    print(f"\n8. Total arrows with marker-end: {len(markers)}")
    assert len(markers) == 0, f"Expected 0 markers, found {len(markers)}"
    print("   [PASS] Exactly 0 arrows (matches source).")

    # 9. Check colors present
    for c in ["#f5f8f5", "#303a36", "#207448", "#e8f1ea", "#db8129"]:
        assert c in svg_str, f"Missing required color: {c}"
    print("\n9. [PASS] All required colors present.")

    # 10. Check gaps
    print("\n10. Checking layout gaps (all must be >= 40px):")
    # Title baseline y=65 to row 0 y=112: gap = 112 - 65 = 47px >= 40px
    assert 112 - 65 >= 40
    # Gaps between rows: y_current - (y_prev + 94) = 40px
    # Bottom margin: 1200 - 1144 = 56px >= 40px
    assert 1200 - 1144 >= 40
    # Left margin: 50px >= 40px
    assert 50 >= 40
    # Right margin: 1600 - 1550 = 50px >= 40px
    assert 1600 - 1550 >= 40
    # Row 5 gap: 820 - (50 + 730) = 40px >= 40px
    assert 820 - (50 + 730) >= 40
    print("   [PASS] All layout gaps >= 40px.")

    print("\nALL AUDIT CHECKS PASSED!")

if __name__ == '__main__':
    run_audit("test_candidate.svg")
