import xml.etree.ElementTree as ET
import re
import json

def audit(svg_path):
    print(f"=== Auditing {svg_path} ===")
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # 1. Structure: <title> and <desc>
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
    assert viewBox == f"0 0 1600 {height}"
    H_val = float(height)
    assert 900 <= H_val <= 1200

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

    print(f"\n3. Total text elements: {len(text_elements)}")
    for i, (t, fs) in enumerate(text_elements, 1):
        print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

    # 4. Expected labels
    specs = json.load(open('specs/p3_01_17.json'))
    spec = [s for s in specs if s['name'] == 'p3-0117-meminfo-breakdown'][0]
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
    print("\n6. Forbidden style words check: PASS")

    # 7. Orange usage
    raw = open(svg_path).read()
    orange_matches = re.findall(r'#db8129', raw, re.IGNORECASE)
    print(f"\n7. Orange #db8129 count: {len(orange_matches)}")
    assert len(orange_matches) == 1, f"Orange count {len(orange_matches)} != 1"
    print("   PASS: Orange used exactly once for circling available.")

    # 8. Check arrows
    lines_with_marker = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if e.attrib.get('marker-end')]
    paths_with_marker = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if e.attrib.get('marker-end')]
    total_arrows = len(lines_with_marker) + len(paths_with_marker)
    print(f"\n8. Total arrows: {total_arrows} (expected 0)")
    assert total_arrows == 0, f"Expected 0 arrows, got {total_arrows}"

    # 9. Outside margins on rects (>= 40px)
    print(f"\n9. Checking outside margins on rects (>= 40px):")
    for r in root.iter('{http://www.w3.org/2000/svg}rect'):
        rx = float(r.attrib.get('x', '0'))
        ry = float(r.attrib.get('y', '0'))
        rw = float(r.attrib.get('width', '0'))
        rh = float(r.attrib.get('height', '0'))
        if rw < 1600 and rw > 100:
            lm = rx
            rm = 1600 - (rx + rw)
            tm = ry
            bm = H_val - (ry + rh)
            assert lm >= 39.9, f"Left margin {lm} < 40 for rect w={rw}"
            assert rm >= 39.9, f"Right margin {rm} < 40 for rect w={rw}"
            assert tm >= 39.9, f"Top margin {tm} < 40 for rect w={rw}"
            assert bm >= 39.9, f"Bottom margin {bm} < 40 for rect w={rw}"
            print(f"   [PASS] Rect x={rx}, y={ry}, w={rw}, h={rh}: lm={lm:.1f}, rm={rm:.1f}, tm={tm:.1f}, bm={bm:.1f}")

    print("   PASS: Outside margins >= 40px for all rects.")

if __name__ == "__main__":
    audit("test_candidate_meminfo.svg")
