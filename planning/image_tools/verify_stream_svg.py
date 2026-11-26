import re
import xml.etree.ElementTree as ET

def test_svg(svg_str):
    root = ET.fromstring(svg_str)
    
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
        "A silent stream is reset by the middlebox; a heartbeat keeps it alive",
        "0 seconds",
        "0.3 seconds",
        "0.6 seconds",
        "the next write",
        "silent client",
        "last byte",
        "quiet for longer than the idle timeout",
        "middlebox closes idle flow",
        "reset or BrokenPipe",
        "Flags [F.] from the server, then ack from the client, then silence, then Flags [R] at the next client write",
        "heartbeat client",
        "ping every half the idle timeout",
        "still alive",
        "idle timeout",
        "find the lowest idle timeout on the path",
        "send a heartbeat below it with margin",
        "check no hard total duration limit applies",
        "The reset appears only when the client speaks again, so a silent stream looks fine until its next write."
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
    print(f"\n5. Extras count: {len(extras)}")
    if extras:
        print("   Unexpected extras:", extras)
    assert len(extras) == 0, f"Unexpected extra texts found: {extras}"
    
    for num in step_numbers:
        cnt = found_texts.count(num)
        assert cnt == 1, f"Step number '{num}' count is {cnt} != 1"
    print(f"All step numbers {step_numbers} present exactly once! (PASS)")
    
    # 5. Check forbidden words
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
    for t in found_texts:
        if t in step_numbers:
            continue
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for w in words:
            assert w not in forbidden, f"Forbidden word '{w}' found in text: '{t}'"
    print("No forbidden words found! (PASS)")
    
    # 6. Colors check
    for color in ["#f5f8f5", "#303a36", "#207448", "#e8f1ea", "#db8129"]:
        assert color in svg_str, f"Missing color {color}"
    orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
    print(f"Orange #db8129 occurrences: {len(orange_matches)}")
    assert 1 <= len(orange_matches) <= 6, f"Unexpected orange count: {len(orange_matches)}"
    
    # 7. Arrows check
    lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
    paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
    total_arrows = len(lines) + len(paths)
    print(f"Total arrows with marker-end: {total_arrows}")
    assert total_arrows == 1, f"Expected exactly 1 arrow, got {total_arrows}"
    
    print("\nALL AUDIT CHECKS PASSED PERFECTLY!")

print("Loaded verifier module.")
