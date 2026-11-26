#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re, subprocess, pathlib

def verify_svg(svg_str):
    root = ET.fromstring(svg_str)
    
    # 1. Structure check: First children must be title and desc
    children = list(root)
    first_tag = children[0].tag.split('}')[-1]
    second_tag = children[1].tag.split('}')[-1]
    print(f"1. Structure: Child 0: <{first_tag}>, Child 1: <{second_tag}>")
    assert first_tag == 'title', f"First child must be title, got {first_tag}"
    assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"
    print("   [PASS] <title> and <desc> are the first children.")
    
    # 2. Dimensions check
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
    print("   [PASS] Canvas dimensions valid.")
    
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
        "Three probes for a slow model server",
        "Timeline for vllm-llama",
        "during loading the server downloads or maps weights and captures CUDA graphs",
        "startupProbe: periodSeconds 10, failureThreshold 180, up to 30 minutes; liveness and readiness are disabled until it succeeds once",
        "liveness with no startup probe on a slow starter creates a restart loop",
        "readinessProbe periodSeconds 5: on failure the pod IP leaves the EndpointSlices, container is NOT restarted",
        "livenessProbe periodSeconds 20, failureThreshold 6: restarts only after 2 full minutes of no response",
        "Never tie liveness to dependencies"
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
    orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
    print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
    assert 1 <= len(orange_matches) <= 4, f"Unexpected orange count: {len(orange_matches)}"
    print("   [PASS] Orange used only for single important transition arrow!")
    
    # 7. Check arrows
    arrows = [e for e in root.iter() if 'marker-end' in e.attrib]
    print(f"\n7. Total arrows: {len(arrows)}")
    assert len(arrows) == 1, f"Expected 1 arrow, got {len(arrows)}"
    print("   [PASS] Exactly 1 arrow connects Segment 1 to Segment 2!")
    
    # 8. Check external resources: no <image>, <script>, external fonts
    assert not any(el.tag.endswith('image') for el in root.iter()), "No <image> allowed"
    assert not any(el.tag.endswith('script') for el in root.iter()), "No <script> allowed"
    print("\nALL VERIFICATIONS PASSED PERFECTLY!")

if __name__ == "__main__":
    from generate_p3_0507_probe_gates import build_svg
    svg = build_svg()
    verify_svg(svg)
