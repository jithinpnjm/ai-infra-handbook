#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re
import pathlib

def audit(svg_path="param_path_candidate.svg"):
    print(f"Auditing {svg_path}...")
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # 1. First children: title and desc
    children = list(root)
    tag1 = children[0].tag.split('}')[-1]
    tag2 = children[1].tag.split('}')[-1]
    assert tag1 == 'title', f"First child must be title, got {tag1}"
    assert tag2 == 'desc', f"Second child must be desc, got {tag2}"
    print("1. [PASS] First children: <title> and <desc>")

    # 2. Dimensions
    width = root.get('width')
    height = root.get('height')
    viewBox = root.get('viewBox')
    assert width == "1600", f"width {width} != 1600"
    assert height == "1200", f"height {height} != 1200"
    assert viewBox == "0 0 1600 1200", f"viewBox {viewBox} != 0 0 1600 1200"
    print(f"2. [PASS] Dimensions: {width}x{height}, viewBox='{viewBox}'")

    # 3. Font sizes >= 24px
    text_elements = []
    for elem in root.iter('{http://www.w3.org/2000/svg}text'):
        full_text = re.sub(r'\s+', ' ', "".join(elem.itertext()).strip())
        fs = float(elem.attrib.get('font-size', '0'))
        assert fs >= 24, f"Text '{full_text}' font-size {fs} < 24!"
        for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
            tfs = tsp.attrib.get('font-size')
            if tfs:
                assert float(tfs) >= 24, f"tspan font-size {tfs} < 24 in '{full_text}'!"
        text_elements.append((full_text, fs))
    print(f"3. [PASS] Total text elements: {len(text_elements)} (all >= 24px)")

    # 4. Expected labels
    expected_labels = [
        "Cutting a path apart with parameter expansion, no external commands",
        "/data/run42",
        "/",
        "model.final",
        ".",
        "ckpt",
        "${path##*/}",
        "removes the longest matching prefix up to the last slash: result 'model.final.ckpt' (same as basename)",
        "${path%/*}",
        "removes the shortest matching suffix starting at the last slash: result '/data/run42' (same as dirname)",
        "${path%.*}",
        "removes the shortest suffix starting at the last dot: result '/data/run42/model.final'",
        "${path##*.}",
        "removes the longest prefix up to the last dot: result 'ckpt'",
        "# / ## remove shortest / longest prefix",
        "% / %% remove shortest / longest suffix",
        "${#path} length",
        "${var:-default}",
        "${var:=default}",
        "${var:?message}"
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
    print(f"Extras: {extras}")
    assert len(extras) == 0, f"Unexpected extra texts found: {extras}"
    assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"
    print("4. [PASS] Exact label fidelity passed!")

    # 5. Forbidden words
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
    for t in found_texts:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for w in forbidden:
            assert w not in words, f"Forbidden word '{w}' found in text: '{t}'"
    print("5. [PASS] No forbidden words found in text!")

    # 6. Colors present
    svg_str = pathlib.Path(svg_path).read_text(encoding="utf-8")
    for color in ["#f5f8f5", "#303a36", "#207448", "#e8f1ea", "#db8129"]:
        assert color in svg_str, f"Missing color {color}"
    print("6. [PASS] All required colors present!")

    # 7. Orange count
    orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
    print(f"7. Orange occurrences: {len(orange_matches)}")
    assert 1 <= len(orange_matches) <= 6, f"Unexpected orange count: {len(orange_matches)}"

    # 8. Arrows count
    lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
    paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
    assert len(lines) + len(paths) == 0, f"Expected 0 arrows, got {len(lines) + len(paths)}"
    print("8. [PASS] Exactly 0 arrows (matches source 0 arrows)!")

    print("\n==================== ALL CHECKS PASSED! ====================")

if __name__ == "__main__":
    audit()
