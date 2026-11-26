import xml.etree.ElementTree as ET
import re

def test_svg(svg_content):
    root = ET.fromstring(svg_content)
    
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
        fs_val = float(fs.replace('px', ''))
        assert fs_val >= 24, f"Text '{full_text}' font-size {fs_val} < 24!"
        for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
            tfs = tsp.attrib.get('font-size')
            if tfs is not None:
                tfs_val = float(tfs.replace('px', ''))
                assert tfs_val >= 24, f"tspan font-size {tfs_val} < 24 in '{full_text}'"
        text_elements.append((full_text, fs_val))
    
    print(f"\n3. Total text elements: {len(text_elements)} (all font-sizes >= 24px)")
    for i, (t, fs) in enumerate(text_elements, 1):
        print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")
        
    expected_labels = [
        "Drill 3: a liveness probe kills a slow load",
        "what exists",
        "weights load for about 90 seconds ('loading weights 62%' then nothing in the previous logs)",
        "broken probes",
        "liveness initialDelaySeconds 5, periodSeconds 10, failureThreshold 1, no startup probe",
        "first check near 5 s fails, event 'Unhealthy: Liveness probe failed' three times then 'Killing: failed liveness probe, will be restarted'",
        "restart count 40, one restart every four minutes",
        "fixed",
        "startup probe with failureThreshold 30 and period 10 gives a 300 second window",
        "liveness only starts after the startup probe passes",
        "starts at 10 s, doubles, capped at 300 s, resets after ten clean minutes",
        "OOM kill shows Last State Terminated, Reason OOMKilled, Exit Code 137; here Reason is Error and no OOMKilled",
        "liveness answers is this process stuck, not is it ready; slow starters get a startup probe sized to a measured load time"
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
    print("   [PASS] Content fidelity: exactly expected labels, none missing, none extra, none duplicated!")
    
    # 5. Check forbidden style words
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
    for t in found_texts:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for f_word in forbidden:
            assert f_word not in words, f"Forbidden word '{f_word}' found in '{t}'!"
    print("   [PASS] No forbidden words found!")
    
    # 6. Check orange count
    orange_matches = re.findall(r'#db8129', svg_content, re.IGNORECASE)
    print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
    assert 1 <= len(orange_matches) <= 6, f"Unexpected orange count: {len(orange_matches)}"
    print("   [PASS] Orange used only for single most important item!")
    
    print("\nALL SYSTEM CHECKS PASSED!")

if __name__ == "__main__":
    print("Validator ready.")
