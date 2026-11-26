import xml.etree.ElementTree as ET
import re
import sys

def audit(svg_path):
    print(f"=== Auditing {svg_path} ===")
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # 1. First children: <title> and <desc>
    children = list(root)
    first_tag = children[0].tag.split('}')[-1]
    second_tag = children[1].tag.split('}')[-1]
    print(f"1. Children tags: 1=<{first_tag}>, 2=<{second_tag}>")
    assert first_tag == 'title', f"First child must be title, got {first_tag}"
    assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"

    # 2. Dimensions
    width = root.get('width')
    viewBox = root.get('viewBox')
    height = root.get('height')
    print(f"2. Dimensions: width={width}, height={height}, viewBox={viewBox}")
    assert width == "1600", f"width must be 1600, got {width}"
    assert viewBox.startswith("0 0 1600 "), f"viewBox must start with '0 0 1600 ', got {viewBox}"
    vb_parts = [float(x) for x in viewBox.split()]
    assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
    assert 900 <= vb_parts[3] <= 1200, f"Height {vb_parts[3]} outside 900-1200"
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
        "Burn rate arithmetic and the three alerts, one row checked by hand",
        "burn_rate = error_ratio / (1 - SLO)",
        "budget_consumed = burn_rate x alert_window / SLO_period",
        "hours_to_empty = SLO_period_hours / burn_rate",
        "burn rate 1 uses exactly the whole budget by the end of the window; 2 uses it in half the time; 99.9 percent SLO with 1 percent errors is burn 10, empties a 30-day budget in 72 hours",
        "Page | 1 h long, 5 min short | burn 14.4 | threshold 0.0144 | 2 percent of budget | 50 hours to empty",
        "Page | 6 h long, 30 min short | burn 6 | 0.006 | 5 percent | 120 hours",
        "Ticket | 3 days long, 6 h short | burn 1 | 0.001 | 10 percent | 720 hours",
        "row 1: 14.4 x 1 / 720 = 0.02 = 2 percent",
        "row 2: 6 x 6 / 720 = 5 percent",
        "row 3: 1 x 72 / 720 = 10 percent",
        "threshold = burn rate x 0.001",
        "short window is a rule of thumb of one twelfth of the long window; no for: clause because the two windows already do the pending delay"
    ]

    found_texts = [t for t, fs in text_elements]

    print(f"\n4. Checking {len(expected_labels)} expected labels against {len(found_texts)} found:")
    all_ok = True
    for exp in expected_labels:
        cnt = found_texts.count(exp)
        ok = (cnt == 1)
        if not ok:
            all_ok = False
        print(f"   [{'OK' if ok else 'FAIL'}] count={cnt}: '{exp[:50]}...'")

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
    assert 1 <= len(orange_matches) <= 4, f"Unexpected orange count: {len(orange_matches)}"

    # 7. Check arrows count
    lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
    paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
    total_arrows = len(lines) + len(paths)
    print(f"\n7. Total arrows with marker-end: {total_arrows}")
    assert total_arrows == 0, f"Expected exactly 0 arrows, got {total_arrows}"

    print("\nALL AUDIT CHECKS PASSED PERFECTLY!")

audit("candidate_burn_rate.svg")
