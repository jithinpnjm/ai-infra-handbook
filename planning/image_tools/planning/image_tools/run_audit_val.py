import xml.etree.ElementTree as ET
import re

def audit(svg_path):
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

    # 4. Check expected labels
    expected_labels = [
        "Checking which variable value is used",
        "which value is used",
        "ansible-inventory --host",
        "debug var",
        "-vvv",
        "grep",
        "extra vars with -e sit at the top of the stack and role vars/ also beats inventory",
        "type",
        "var | type_debug shows str, int, bool, list, dict",
        "render template",
        "ansible localhost -m template with -e @vars.yml",
        "inspect /tmp/out",
        "condition",
        "debug msg of the when expression",
        "-vv false_condition",
        "gpu_count 8 from -e is a number, from a CSV it is the text 8 and the when comparison fails"
    ]
    step_numbers = {"1", "2", "3", "4"}

    found_texts = [t for t, fs in text_elements]
    print(f"\n4. Checking expected labels:")
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
    assert len(found_texts) == len(expected_labels) + len(step_numbers), f"Total count mismatch"

    # 5. Check forbidden words
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
    for t in found_texts:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for f in forbidden:
            assert f not in words, f"Forbidden word '{f}' in '{t}'!"
    print("\n5. No forbidden words found! (PASS)")

    # 6. Check orange count
    raw_svg = open(svg_path).read()
    orange_matches = re.findall(r'#db8129', raw_svg, re.IGNORECASE)
    print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
    assert len(orange_matches) == 1, f"Expected exactly 1 orange usage, got {len(orange_matches)}"

    # 7. Check arrows count
    lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib or "marker-start" in e.attrib]
    paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib or "marker-start" in e.attrib]
    total_arrows = len(lines) + len(paths)
    print(f"\n7. Total arrows with markers: {total_arrows}")
    assert total_arrows == 0, f"Expected exactly 0 arrows, got {total_arrows}"

    # 8. External resources check
    assert not any(el.tag.endswith('image') for el in root.iter()), "No <image> allowed"
    assert not any(el.tag.endswith('script') for el in root.iter()), "No <script> allowed"
    assert "http://" not in raw_svg.replace("http://www.w3.org/2000/svg", ""), "No external URLs"
    assert "https://" not in raw_svg, "No external URLs"
    print("\n8. No external images, scripts or fonts: PASS!")

    print("\nALL STRICT AUDIT CHECKS PASSED PERFECTLY!")

if __name__ == "__main__":
    audit("test_candidate_val.svg")
