import xml.etree.ElementTree as ET
import re

def validate_svg(svg_path):
    print(f"=== Validating {svg_path} ===")
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
    assert width == "1600"
    assert viewBox.startswith("0 0 1600 ")
    vb_parts = [float(x) for x in viewBox.split()]
    assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
    assert 900 <= vb_parts[3] <= 1200
    assert int(height) == int(vb_parts[3])

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
        "Five ways a trace can mislead you",
        "Asymmetric paths",
        "traceroute shows only the forward path; the return path can differ and the round trip includes it; run mtr from both ends",
        "ECMP and load balancers",
        "different probes may take different equal-cost paths, so you see hops from several routers or inconsistent paths; flow-aware tools keep the 5-tuple constant: paris-traceroute, dublin-traceroute, or mtr with fixed ports",
        "MPLS and tunnels",
        "hops can be hidden when the TTL is not propagated, or label stacks shown",
        "NAT and cloud networks",
        "virtual routers do not decrement the TTL or respond, so a cloud VPC trace typically shows only the first and last hops",
        "Probes are small, 60 bytes each",
        "problems that affect only large packets, such as MTU problems, will not show up; use tracepath or ping -M do -s",
        "forward path (shown)",
        "return path (not shown)",
        "Use the right tool for the question: a trace shows hops, not the packet sizes that fit"
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

    # 5. Check arrows:
    markers = root.findall('.//{http://www.w3.org/2000/svg}marker')
    print(f"\n5. Markers defined: {len(markers)}")
    paths_with_marker = []
    for elem in root.iter():
        me = elem.attrib.get('marker-end')
        if me:
            paths_with_marker.append((elem.tag.split('}')[-1], me))
    print(f"   Paths with marker-end: {len(paths_with_marker)}")
    for p in paths_with_marker:
        print(f"     {p}")
    assert len(paths_with_marker) == 2, f"Expected exactly 2 arrows, got {len(paths_with_marker)}"

    print("\nALL CHECKS PASSED PERFECTLY!")

validate_svg("test_out.svg")
