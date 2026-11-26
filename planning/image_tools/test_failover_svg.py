#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

def verify_svg_candidate(svg_content):
    root = ET.fromstring(svg_content)
    
    # 1. Structure check: First children must be title and desc
    children = list(root)
    first_tag = children[0].tag.split('}')[-1]
    second_tag = children[1].tag.split('}')[-1]
    print(f"1. Structure check: First child <{first_tag}>, Second child <{second_tag}>")
    assert first_tag == 'title', f"First child must be title, got {first_tag}"
    assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"

    # 2. Canvas size check
    viewBox = root.attrib.get("viewBox")
    width = root.attrib.get("width")
    height = root.attrib.get("height")
    print(f"2. Canvas: viewBox={viewBox}, width={width}, height={height}")
    assert width == "1600"
    vb_parts = [float(x) for x in viewBox.split()]
    assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
    assert 900 <= vb_parts[3] <= 1200
    assert int(height) == int(vb_parts[3])

    # 3. Font size check: >= 24 on all text and tspans
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
        "Failover capacity: utilisation must leave room for the survivors",
        "Two regions each at utilisation u: one fails, the survivor carries 2u, so u must stay below 50 percent minus headroom or the failover just moves the outage",
        "Three regions: survivors carry 1.5u each, so u can be up to about 66 percent",
        "Inside one region of N replicas: losing one replica adds 1 / (N - 1) load to the rest; X plus 1 sizing pays for it",
        "failover is a policy question before it is a routing question: ask the tenant's contract what may leave the region; store an allowed-region list per tenant and the router may only retry inside it; a retry that crosses the line is itself a data transfer; logs and traces also carry data",
        "dedicated endpoints choose a region, EU or US, with data residency; residency is fixed at endpoint creation and cross-region failover should be opt-in per tenant; Nebius has not published its failover design"
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
            assert f not in words, f"Forbidden word '{f}' found in '{t}'!"

    print("\n5. Forbidden words check: PASS (none found)")

    # 6. Check orange count
    orange_matches = re.findall(r'#db8129', svg_content, re.IGNORECASE)
    print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
    assert 1 <= len(orange_matches) <= 4, f"Unexpected orange count: {len(orange_matches)}"

    # 7. Check arrows count
    lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
    paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
    total_arrows = len(lines) + len(paths)
    print(f"\n7. Total arrows with marker-end: {total_arrows}")
    assert total_arrows == 0, f"Expected 0 arrows, got {total_arrows}"

    # 8. Check colors present
    assert "#f5f8f5" in svg_content
    assert "#303a36" in svg_content
    assert "#207448" in svg_content
    assert "#e8f1ea" in svg_content
    assert "#db8129" in svg_content
    print("\n8. All required colors present! (PASS)")

    print("\nALL SVG CHECKS PASSED PERFECTLY!")

if __name__ == '__main__':
    print("Verifier ready.")
