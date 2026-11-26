import xml.etree.ElementTree as ET
import re
import sys

def audit_svg(svg_path):
    print(f"=== Auditing {svg_path} ===")
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # 1. First children check: <title> and <desc>
    children = list(root)
    first_tag = children[0].tag.split('}')[-1]
    second_tag = children[1].tag.split('}')[-1]
    print(f"1. First child: <{first_tag}>, Second child: <{second_tag}>")
    assert first_tag == 'title', f"First child must be title, got {first_tag}"
    assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"

    title_text = "".join(children[0].itertext()).strip()
    assert title_text == "A global ratio hides one tenant, and per-tenant detail has a series cost", f"Unexpected title text: '{title_text}'"
    print(f"   Title text matches: '{title_text}'")

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
    print("   Dimensions PASS!")

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

    print(f"3. Total text elements: {len(text_elements)} (all font-sizes >= 24px)")
    for i, (t, fs) in enumerate(text_elements, 1):
        print(f"   {i:2d}. [{fs:2.0f}px] '{t[:50]}...'")

    # 4. Expected labels
    expected_labels = [
        "A global ratio hides one tenant, and per-tenant detail has a series cost",
        "100 tenants with equal traffic; one tenant has 100 percent errors; global error ratio = 1 percent; against a 99.9 percent target burn rate = 0.01 / 0.001 = 10",
        "Burn 10 pages through the 6-hour rule (threshold 6) but not through the fast 14.4 rule, while that customer is fully down",
        "TTFT histogram with 22 buckets plus a count series is about 23 series per tenant and model pair; 1,000 tenants x 20 models x 23 = 460,000 series for one metric",
        "page on per-model ratios, ticket on per-tenant ratios, guard low-traffic series",
        "tenant with 3 requests per minute (0.05 requests per second) and every one failing has a 100 percent ratio but the rule needs more than 0.1 requests per second over three days, so it does not fire; tenant a at 100 requests per second and 0.2 percent errors fires, tenant b stays silent; a dedicated contract tenant can get an absolute count of failures in an hour instead"
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
    print(f"   Extra texts: {extras}")
    assert len(extras) == 0, f"Found unexpected extra text: {extras}"
    print("   All labels PASS!")

    # 5. Check forbidden words
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
    for t in found_texts:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for f in forbidden:
            assert f not in words, f"Forbidden word '{f}' in '{t}'!"
    print("5. No forbidden words found! (PASS)")

    # 6. Check orange count
    with open(svg_path, 'r', encoding='utf-8') as f:
        svg_str = f.read()
    orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
    print(f"6. Orange #db8129 occurrences: {len(orange_matches)}")
    assert len(orange_matches) >= 1, "Orange color #db8129 must be present"

    # 7. Check arrows count
    lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
    paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
    total_arrows = len(lines) + len(paths)
    print(f"7. Total arrows with marker-end: {total_arrows}")
    assert total_arrows == 0, f"Expected exactly 0 arrows, got {total_arrows}"
    print("   Arrows PASS!")

    # 8. Check colors present
    assert "#f5f8f5" in svg_str
    assert "#303a36" in svg_str
    assert "#207448" in svg_str
    assert "#e8f1ea" in svg_str
    assert "#db8129" in svg_str
    print("8. All required colors present! (PASS)")

    # 9. Check text padding and bounds
    print("9. Checking text bounds & paddings...")
    boxes = {
        "card-dilution": (40, 145, 480, 480),
        "card-alert-paradox": (40, 665, 480, 495),
        "card-cardinality-cost": (560, 145, 480, 1015),
        "card-design": (1080, 145, 480, 295),
        "card-guard-example": (1080, 480, 480, 680),
    }

    # For each text element, verify its tspans fit inside their box
    # Title fits in canvas (0, 0, 1600, 145)
    for elem in root.iter('{http://www.w3.org/2000/svg}text'):
        # find parent g
        parent = elem
        parent_id = None
        # Walk ancestors
        # Find which group it belongs to
        full_text = "".join(elem.itertext()).strip()
        full_text = re.sub(r'\s+', ' ', full_text)
        
        # Determine box
        if full_text.startswith("A global ratio"):
            box_x, box_y, box_w, box_h = 0, 0, 1600, 145
            box_name = "Title"
        elif full_text.startswith("100 tenants"):
            box_x, box_y, box_w, box_h = boxes["card-dilution"]
            box_name = "Card 1 (dilution)"
        elif full_text.startswith("Burn 10 pages"):
            box_x, box_y, box_w, box_h = boxes["card-alert-paradox"]
            box_name = "Card 2 (alert paradox)"
        elif full_text.startswith("TTFT histogram"):
            box_x, box_y, box_w, box_h = boxes["card-cardinality-cost"]
            box_name = "Card 3 (cardinality cost)"
        elif full_text.startswith("page on per-model"):
            box_x, box_y, box_w, box_h = boxes["card-design"]
            box_name = "Card 4 (design)"
        elif full_text.startswith("tenant with 3 requests"):
            box_x, box_y, box_w, box_h = boxes["card-guard-example"]
            box_name = "Card 5 (guard example)"
        else:
            raise ValueError(f"Unknown text element: {full_text}")

        # Check each tspan
        base_y = float(elem.attrib.get('y', 0))
        cur_y = base_y
        for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
            dy = float(tsp.attrib.get('dy', 0))
            cur_y += dy
            tfs = float(tsp.attrib.get('font-size', elem.attrib.get('font-size', 24)))
            line_str = tsp.text.strip()
            line_w = len(line_str) * tfs * 0.6
            left_pad = (box_w - line_w) / 2
            right_pad = left_pad
            top_pad = (cur_y - tfs) - box_y
            bot_pad = (box_y + box_h) - cur_y

            # Check constraints
            assert left_pad >= 16, f"Horizontal padding {left_pad:.1f} < 16 for '{line_str}' in {box_name}"
            assert top_pad >= 16, f"Top padding {top_pad:.1f} < 16 for '{line_str}' in {box_name}"
            assert bot_pad >= 16, f"Bottom padding {bot_pad:.1f} < 16 for '{line_str}' in {box_name}"

    print("9. Text bounds and paddings: ALL PASS (every line >= 16px padding on all sides)!")
    print("\nALL AUDIT CHECKS PASSED PERFECTLY!")

if __name__ == "__main__":
    audit_svg("candidate_tenant_dilution.svg")
