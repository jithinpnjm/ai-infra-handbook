import xml.etree.ElementTree as ET
import re
import pathlib

def test_svg(filename):
    svg_str = pathlib.Path(filename).read_text()
    tree = ET.parse(filename)
    root = tree.getroot()

    # 1. First children check: <title> and <desc>
    children = list(root)
    first_tag = children[0].tag.split('}')[-1]
    second_tag = children[1].tag.split('}')[-1]
    print(f"1. First child: <{first_tag}>, Second child: <{second_tag}>")
    assert first_tag == 'title', f"First child must be title, got {first_tag}"
    assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"

    # 2. Canvas size check
    viewBox = root.attrib.get("viewBox")
    width = root.attrib.get("width")
    height = root.attrib.get("height")
    print(f"2. viewBox: {viewBox}, width: {width}, height: {height}")
    assert width == "1600"
    vb_parts = [float(x) for x in viewBox.split()]
    assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
    assert 900 <= vb_parts[3] <= 1200, f"Height {vb_parts[3]} outside [900, 1200]"
    assert int(height) == int(vb_parts[3])

    # 3. Check text elements and font-size >= 24
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
        "One slow rail slows every rank, because synchronous training waits for the slowest member",
        "healthy rail",
        "slow rail",
        "AllReduce barrier: every rank waits for the slowest",
        "Dirty or failing optic",
        "low DOM Rx power",
        "high pre-FEC bit error rate, rx_corrected_bits rising",
        "CRC errors and RDMA go-back-N retransmissions",
        "The link never goes down, so link-down alerts stay green.",
        "Alert on FEC and CRC trends, low DOM power and per-rail retransmits. Drain the node, then clean or replace the optic.",
        "Watch trends in error counters, not only link state."
    ]

    found_texts = [t for t, fs in text_elements]

    print(f"\n4. Checking {len(expected_labels)} expected labels:")
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

    # 5. Check orange usage
    orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
    print(f"\n5. Orange #db8129 occurrences: {len(orange_matches)}")
    assert 1 <= len(orange_matches) <= 4, f"Unexpected orange count: {len(orange_matches)}"

    # 6. Check arrows count
    lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
    paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
    total_arrows = len(lines) + len(paths)
    print(f"\n6. Total arrows with marker-end: {total_arrows}")
    assert total_arrows == 3, f"Expected exactly 3 arrows, got {total_arrows}"

    print("\nALL VERIFICATIONS PASSED PERFECTLY!")

if __name__ == "__main__":
    test_svg("test_slow_rail.svg")
