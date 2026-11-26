import xml.etree.ElementTree as ET
import re

def verify_svg(svg_str):
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
        "Why maxSurge 1 stalls a full GPU pool",
        "Worked example with a node pool of 12 GPUs",
        "maxSurge 1, maxUnavailable 0",
        "3 replicas of 4 GPUs each fill all 12 GPUs",
        "the controller must start a fourth pod first",
        "it needs 4 GPUs that do not exist",
        "pod stays Pending with message '0/N nodes are available: Insufficient nvidia.com/gpu'",
        "maxUnavailable 0 forbids removing an old pod until a replacement is Ready",
        "rollout hangs",
        "maxSurge 0, maxUnavailable 1",
        "one old replica terminates first",
        "frees 4 GPUs",
        "the new replica schedules",
        "repeat",
        "rollout completes with temporarily 2 of 3 serving",
        "progressDeadlineSeconds 1800 because model downloads and CUDA graph capture are slow"
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
    assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"
    
    # 5. Check forbidden words
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
    for t in found_texts:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for f_word in forbidden:
            assert f_word not in words, f"Forbidden word '{f_word}' found in '{t}'!"
    print("\n5. No forbidden words found! (PASS)")
    
    # 6. Check orange count
    orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
    print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
    assert 1 <= len(orange_matches) <= 4, f"Unexpected orange count: {len(orange_matches)}"
    
    print("\nALL VERIFICATIONS PASSED!")

if __name__ == "__main__":
    print("Verifier ready.")
