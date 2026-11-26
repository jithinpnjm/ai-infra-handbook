import xml.etree.ElementTree as ET
import re
import sys

def audit_svg(svg_path):
    print(f"Auditing {svg_path}...")
    tree = ET.parse(svg_path)
    root = tree.getroot()

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
    assert width == "1600", f"Expected width 1600, got {width}"
    assert viewBox.startswith("0 0 1600 "), f"viewBox must start with '0 0 1600 ', got {viewBox}"
    vb_parts = [float(x) for x in viewBox.split()]
    assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
    assert 900 <= vb_parts[3] <= 1200, f"Height {vb_parts[3]} outside 900-1200 range"
    assert int(height) == int(vb_parts[3]), f"height {height} != viewBox height {vb_parts[3]}"

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
        "How the parser resolves gpu01 and gpu02 from node_defaults",
        "forty identical GPU machines: change one shared value and thirty-nine entries need no edit",
        "parser reads defaults: &node_defaults with gpus: 8, os: ubuntu-22.04, tags: [h100] and stores it under the name node_defaults",
        "gpu01: <<: *node_defaults copies gpus 8, os and tags into the node",
        "gpu02: the same copy first, then the local key gpus: 4 replaces the copied 8",
        "the override wins because the local key comes after the merge",
        "gpu01: gpus 8, os ubuntu-22.04, tags [h100]",
        "gpu02: gpus 4, os ubuntu-22.04, tags [h100]",
        "anchors work inside a single file only, not across files; << is a YAML 1.1 convention supported by PyYAML and Kubernetes tooling, not part of the YAML 1.2 core, and not every parser honours it; overused anchors make diffs harder, a reviewer has to scroll to the top to learn what the node contains, and chains of anchors make it longer; higher-level reuse: GitLab extends and GitHub Actions reusable workflows",
        "The local key after the merge wins"
    ]

    step_numbers = {"1", "2", "3"}

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

    extras = [t for t in found_texts if t not in expected_labels and t not in step_numbers]
    print(f"\nExtra texts: {extras}")
    assert len(extras) == 0, f"Found unexpected extra text: {extras}"

    for s in step_numbers:
        cnt = found_texts.count(s)
        assert cnt == 1, f"Step number {s} count {cnt} != 1!"

    # 5. Check forbidden words
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
    for t in found_texts:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for f in forbidden:
            assert f not in words, f"Forbidden word '{f}' in '{t}'!"

    print("\n5. No forbidden words found! (PASS)")

    # 6. Check orange count
    with open(svg_path, 'r', encoding='utf-8') as f:
        svg_str = f.read()
    orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
    print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
    assert 1 <= len(orange_matches) <= 4, f"Unexpected orange count: {len(orange_matches)}"

    # 7. Check arrows count
    lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
    paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
    total_arrows = len(lines) + len(paths)
    print(f"\n7. Total arrows with marker-end: {total_arrows}")
    assert total_arrows == 0, f"Expected exactly 0 arrows, got {total_arrows}"

    # 8. Check colors present
    assert "#f5f8f5" in svg_str
    assert "#303a36" in svg_str
    assert "#207448" in svg_str
    assert "#e8f1ea" in svg_str
    assert "#db8129" in svg_str
    print("\n8. All required colors present! (PASS)")

    # 9. Check text padding and bounds
    print("\n9. Checking text bounds & paddings...")
    def est_w(text, fs=24, is_mono=False):
        rate = 0.62 if is_mono else 0.60
        return len(text) * fs * rate

    for elem in root.iter('{http://www.w3.org/2000/svg}text'):
        # Check all tspans
        fs = float(elem.attrib.get('font-size', 24))
        for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
            t = tsp.text or ""
            w = est_w(t, fs)
            # Just print long ones
            if w > 400:
                print(f"   [tspan w={w:.1f}px]: '{t[:40]}...'")

    print("\nALL AUDIT CHECKS PASSED PERFECTLY!")

if __name__ == '__main__':
    audit_svg("test_p4_0404.svg")
