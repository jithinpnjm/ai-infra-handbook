#!/usr/bin/env python3
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

    title_text = children[0].text.strip()
    desc_text = children[1].text.strip()
    assert title_text == "Three checks before a template reaches a server", f"Wrong title: {title_text}"
    # Verify title is not repeated in desc
    assert "Three checks before a template reaches a server" not in desc_text, "Title must not be repeated in desc!"

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
        "Three checks before a template reaches a server",
        "the render succeeds, the service refuses to start, and the log says the config is malformed on line 14",
        "render offline with realistic data",
        "jinja2 Python API with a fixtures file",
        'ansible localhost -m ansible.builtin.template -a "src=nccl.conf.j2 dest=/tmp/out" -e @vars.yml --diff',
        "one-task playbook",
        'ansible -m debug -a "msg={{ ... }}"',
        "compare with the golden file",
        "render representative data including empty lists and missing optional keys; the expected file is reviewed once and committed; any template change shows as a diff; stress inputs: an empty list, a missing optional key, a host with zero GPUs; snapshot tests catch stray whitespace",
        "validate with the target's own parser",
        "nginx -t, visudo -cf, sshd -t, slurmd -C or scontrol checks, kubeconform, promtool check rules, python -c import yaml; yaml.safe_load(...)",
        "A surprise on Monday becomes a failed test on Friday"
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
    print(f"\nExtra texts: {extras}")
    assert len(extras) == 0, f"Found unexpected extra text: {extras}"
    assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"

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
    assert 1 <= len(orange_matches) <= 8, f"Unexpected orange count: {len(orange_matches)}"

    # 7. Check arrows count
    lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
    paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
    total_arrows = len(lines) + len(paths)
    print(f"\n7. Total arrows with marker-end: {total_arrows}")
    assert total_arrows == 2, f"Expected exactly 2 pipeline arrows, got {total_arrows}"

    # 8. Check colors present
    assert "#f5f8f5" in svg_str
    assert "#303a36" in svg_str
    assert "#207448" in svg_str
    assert "#e8f1ea" in svg_str
    assert "#db8129" in svg_str
    print("\n8. All required colors present! (PASS)")

    # 9. Check external resources: no <image>, <script>, external fonts
    assert not any(el.tag.endswith('image') for el in root.iter()), "No <image> allowed"
    assert not any(el.tag.endswith('script') for el in root.iter()), "No <script> allowed"
    print("\n9. No external images or scripts! (PASS)")

    print("\nALL AUDIT CHECKS PASSED PERFECTLY!")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        audit_svg(sys.argv[1])
    else:
        print("Usage: python3 audit_three_checks.py <svg_file>")
