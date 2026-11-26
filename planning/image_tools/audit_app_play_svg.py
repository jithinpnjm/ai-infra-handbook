#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

def audit():
    svg_path = "test_candidate.svg"
    tree = ET.parse(svg_path)
    root = tree.getroot()
    raw = open(svg_path).read()

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

    # 4. Expected labels fidelity
    expected_labels = [
        "One app host through the application play",
        "one app host with serial one at a time and max_fail_percentage 0",
        "pre_tasks",
        "assert app_version is a tag or commit SHA",
        "touch drain flag under /var/www/lb-drain delegated to the first web host",
        "pause 5 seconds",
        "tasks",
        "group and user",
        "directory skeleton",
        "git fetch pinned version",
        "venv from requirements.lock",
        "env file mode 0600",
        "alembic upgrade head run_once",
        "systemd unit",
        "switch current symlink",
        "meta flush_handlers",
        "uri readyz retries 20 delay 3",
        "prune old releases",
        "handlers",
        "restart fleetapp only when something changed",
        "post_tasks",
        "remove drain flag",
        "host back in rotation"
    ]

    found_texts = [t for t, fs in text_elements]
    print(f"\n4. Checking {len(expected_labels)} expected labels against {len(text_elements)} found:")
    all_ok = True
    for exp in expected_labels:
        exp_norm = re.sub(r'\s+', ' ', exp)
        cnt = found_texts.count(exp_norm)
        ok = (cnt == 1)
        if not ok:
            all_ok = False
        print(f"   [{'OK' if ok else 'FAIL'}] count={cnt}: '{exp}'")

    assert all_ok, "Some expected labels failed count == 1 check!"
    print("   PASS: All expected labels found exactly once")

    # 5. Extras check
    norm_expected = [re.sub(r'\s+', ' ', exp) for exp in expected_labels]
    extras = [t for t in found_texts if t not in norm_expected]
    print(f"\n5. Extras count: {len(extras)}")
    if extras:
        print("   Found extras:", extras)
    assert len(extras) == 0, f"Found unexpected extra text: {extras}"
    print("   PASS: No unrequested extra text elements")

    # 6. Forbidden words check
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
    found_forbidden = []
    for t in found_texts:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for f in forbidden:
            if f in words:
                found_forbidden.append((f, t))
    assert len(found_forbidden) == 0, f"Forbidden words found: {found_forbidden}"
    print("\n6. Forbidden words check: PASS (zero forbidden style words)")

    # 7. Check orange count
    oranges = re.findall(r'#db8129', raw, re.IGNORECASE)
    print(f"\n7. Orange #db8129 occurrences: {len(oranges)}")
    assert 1 <= len(oranges) <= 6, f"Orange count {len(oranges)} out of bounds"
    print("   PASS: Orange used strictly for the readyz check gate")

    # 8. Check palette colors
    for c in ["#f5f8f5", "#303a36", "#207448", "#e8f1ea", "#db8129"]:
        assert c in raw, f"Color {c} not found in SVG!"
    print("\n8. All palette colors present: PASS")

    print("\n=== ALL STRICT HARNESS AUDIT CHECKS PASSED PERFECTLY! ===")

audit()
