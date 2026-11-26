import xml.etree.ElementTree as ET
import re

def test_svg_string(svg_text):
    root = ET.fromstring(svg_text)
    
    # 1. Structure
    children = list(root)
    first_tag = children[0].tag.split('}')[-1]
    second_tag = children[1].tag.split('}')[-1]
    print(f"1. Structure: Child 0: <{first_tag}>, Child 1: <{second_tag}>")
    assert first_tag == "title", f"First child must be title, got {first_tag}"
    assert second_tag == "desc", f"Second child must be desc, got {second_tag}"
    
    # 2. Canvas
    vb = root.attrib.get("viewBox").split()
    W = float(vb[2])
    H = float(vb[3])
    width = float(root.attrib.get("width"))
    height = float(root.attrib.get("height"))
    print(f"2. Canvas: W={W}, H={H}, width={width}, height={height}")
    assert W == 1600
    assert 900 <= H <= 1200
    assert width == 1600
    assert height == H
    
    # 3. Font sizes >= 24
    text_elements = []
    for elem in root.iter('{http://www.w3.org/2000/svg}text'):
        full_text = "".join(elem.itertext()).strip()
        full_text = re.sub(r'\s+', ' ', full_text)
        fs = float(elem.attrib.get('font-size', '0'))
        tspans = list(elem.iter('{http://www.w3.org/2000/svg}tspan'))
        if fs == 0 and tspans:
            fs = float(tspans[0].attrib.get('font-size', '0'))
        assert fs >= 24, f"Text '{full_text}' font-size {fs} < 24!"
        for tsp in tspans:
            tfs = tsp.attrib.get('font-size')
            if tfs is not None:
                assert float(tfs) >= 24, f"tspan font-size {tfs} < 24 in '{full_text}'"
        text_elements.append((full_text, fs))
    
    print(f"\n3. Font sizes: Total text elements = {len(text_elements)} (all >= 24px)")
    for i, (t, fs) in enumerate(text_elements, 1):
        print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")
        
    # 4. Expected labels
    expected_labels = [
        "Capacity left after a spine fails",
        "capacity kept = (S-1)/S of uplink capacity",
        "S = 32 spines, one down: 96.9%",
        "S = 4 spines, one down: 75%",
        "A 1:1 design stays oversubscribed until the failure is repaired",
        "Work out what survives losing one spine, one leaf and one rail group"
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
    
    # 5. Forbidden words
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
    for t in found_texts:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for f in forbidden:
            assert f not in words, f"Forbidden word '{f}' in '{t}'!"
            
    print("5. Forbidden words check: PASS!")
    
    # 6. Orange check: only used for the single most important item
    oranges = re.findall(r'#db8129', svg_text, re.IGNORECASE)
    print(f"6. Orange count: {len(oranges)}")
    assert 1 <= len(oranges) <= 10, f"Unexpected orange count: {len(oranges)}"
    
    # 7. Check arrows
    lines_with_marker = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if e.attrib.get('marker-end')]
    paths_with_marker = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if e.attrib.get('marker-end')]
    total_arrows = len(lines_with_marker) + len(paths_with_marker)
    print(f"7. Total arrows with marker-end: {total_arrows} (expected 0)")
    assert total_arrows == 0, f"Expected 0 arrows, got {total_arrows}"
    
    print("\nALL VERIFICATIONS PASSED!")

print("Audit script loaded.")
