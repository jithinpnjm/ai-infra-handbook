#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re
import json

def audit(svg_path):
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # 1. Structure
    children = list(root)
    t0 = children[0].tag.split('}')[-1]
    t1 = children[1].tag.split('}')[-1]
    print(f"1. Children: <{t0}>, <{t1}>")
    assert t0 == 'title', f"Child 0 must be <title>, got <{t0}>"
    assert t1 == 'desc', f"Child 1 must be <desc>, got <{t1}>"

    # 2. Dimensions
    width = root.get('width')
    height = root.get('height')
    viewBox = root.get('viewBox')
    print(f"2. Dimensions: width={width}, height={height}, viewBox={viewBox}")
    assert width == "1600"
    assert viewBox == "0 0 1600 1200"
    assert height == "1200"

    # 3. Text elements & font sizes >= 24px
    text_elements = []
    for el in root.iter('{http://www.w3.org/2000/svg}text'):
        fs = float(el.attrib.get('font-size', '0'))
        combined = " ".join("".join(el.itertext()).split())
        assert fs >= 24, f"Text '{combined}' font-size {fs} < 24!"
        for ts in el.findall('{http://www.w3.org/2000/svg}tspan'):
            tfs = float(ts.attrib.get('font-size', fs))
            assert tfs >= 24, f"tspan in '{combined}' font-size {tfs} < 24!"
        text_elements.append((combined, fs))

    print(f"3. Total text elements: {len(text_elements)}")
    for i, (t, fs) in enumerate(text_elements, 1):
        print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

    # 4. Expected labels
    spec = json.load(open('specs/p3_01_19.json'))[0]
    expected_labels = [spec['title']] + re.findall(r"'([^']*)'", spec['spec'])
    found_texts = [t for t, fs in text_elements]

    print(f"\n4. Checking {len(expected_labels)} expected labels against {len(found_texts)} found:")
    all_ok = True
    for exp in expected_labels:
        exp_norm = re.sub(r'\s+', ' ', exp)
        cnt = found_texts.count(exp_norm)
        ok = (cnt == 1)
        if not ok:
            all_ok = False
        print(f"   [{'OK' if ok else 'FAIL'}] count={cnt}: '{exp[:50]}...'")

    assert all_ok, "Some expected labels failed count == 1 check!"
    print("   PASS: All expected labels found exactly once.")

    # 5. Extras check
    norm_expected = [re.sub(r'\s+', ' ', exp) for exp in expected_labels]
    extras = [t for t in found_texts if t not in norm_expected]
    print(f"\n5. Extras count: {len(extras)}")
    assert len(extras) == 0, f"Unexpected extra texts found: {extras}"
    assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"
    print("   PASS: Zero extra text elements.")

    # 6. Forbidden words
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
    for t in found_texts:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for f in forbidden:
            assert f not in words, f"Forbidden word '{f}' in '{t}'!"
    print("6. PASS: No forbidden words found.")

    # 7. Check arrow count
    arrows = list(root.iter('{http://www.w3.org/2000/svg}line'))
    arrow_lines = [l for l in arrows if 'marker-end' in l.attrib]
    paths_with_marker = [p for p in root.iter('{http://www.w3.org/2000/svg}path') if 'marker-end' in p.attrib]
    total_arrows = len(arrow_lines) + len(paths_with_marker)
    print(f"\n7. Total arrows: {total_arrows}")
    # Left timeline: 1 start->track1, 1->2, 2->3, 3->4 = 4 arrows
    # Right timeline: 1 start->track2, 1->2, 2->3 = 3 arrows
    # Total = 7 arrows
    assert total_arrows == 7, f"Expected 7 arrows, found {total_arrows}"
    print("   PASS: Arrow count matches source (7 arrows).")

    # 8. Orange usage
    with open(svg_path) as f:
        raw = f.read()
    orange_matches = re.findall(r'#db8129', raw, re.IGNORECASE)
    print(f"\n8. Orange #db8129 count: {len(orange_matches)}")
    assert 1 <= len(orange_matches) <= 10, f"Orange count {len(orange_matches)} out of bounds"
    print("   PASS: Orange used for the shell script timeline.")

    print("\nALL AUDIT CHECKS PASSED PERFECTLY!")

if __name__ == "__main__":
    audit("candidate_p3_0119.svg")
