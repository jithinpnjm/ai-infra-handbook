import xml.etree.ElementTree as ET
import re

def audit(svg_path):
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

    # 2. Dimensions
    width = root.get('width')
    viewBox = root.get('viewBox')
    height = root.get('height')
    print(f"2. Dimensions: width={width}, height={height}, viewBox={viewBox}")
    assert width == "1600", f"width must be 1600, got {width}"
    assert viewBox.startswith("0 0 1600 ")
    vb_parts = [float(x) for x in viewBox.split()]
    assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
    assert 900 <= vb_parts[3] <= 1200
    assert int(height) == int(vb_parts[3])

    # 3. Check font-size >= 24 on all text and tspans
    text_elements = []
    for elem in root.iter('{http://www.w3.org/2000/svg}text'):
        full_text = " ".join("".join(elem.itertext()).split())
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
        "Scheduled, then rejected: scheduler and kubelet disagree",
        "kube-scheduler: sees requests, labels, allocatable; not NUMA alignment",
        "places a pod on a node (bind)",
        "kubelet Topology Manager: at admission tries to align CPU, memory and devices on one NUMA node",
        "rejects with TopologyAffinityError because no aligned set exists",
        "Pod ends failed after binding",
        "NodeResourceTopology (NFD) so the scheduler sees NUMA zones",
        "align kubelet policy with NUMA-aware scheduling",
        "DRA with attributes",
        "label nodes topology.example.com/block, /rack, /leaf, /nvlink-domain or use cloud topology.kubernetes.io labels",
        "a job spread over wrong racks loses bandwidth on every all-reduce and nothing in the logs shows an error",
        "NVL72 domain is a rack-scale unit: schedule whole-domain jobs onto one domain"
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
    print(f"\n5. Extras count: {len(extras)}")
    if extras:
        print("   Unexpected extras:", extras)
    assert len(extras) == 0, f"Unexpected extra texts found: {extras}"
    assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"

    # 5. Check forbidden words
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'callout', 'sub-line', 'subline', 'takeaway']
    for t in found_texts:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for w in words:
            assert w not in forbidden, f"Forbidden word '{w}' found in text: '{t}'"

    print("\n6. Forbidden words check: PASS!")

    # 6. Arrows count
    arrows = [el for el in root.iter() if 'marker-end' in el.attrib]
    print(f"\n7. Arrow count: {len(arrows)}")
    assert len(arrows) == 2, f"Expected 2 arrows, got {len(arrows)}"
    print("[PASS] Exactly 2 arrows present.")

    # 7. Check orange usage: exactly one orange highlight in body
    orange_els = []
    for el in root.iter():
        for k, v in el.attrib.items():
            if "#db8129" in v or "arrow-orange" in v:
                orange_els.append((el.tag, k, v))

    print(f"\n8. Orange highlights: {len(orange_els)}")
    for o in orange_els:
        print(f"  {o}")
    body_orange_paths = [el for el in root.iter() if el.tag.endswith('path') and el.attrib.get('stroke') == "#db8129"]
    print(f"Body orange paths: {len(body_orange_paths)}")
    assert len(body_orange_paths) == 1, f"Expected exactly 1 orange item/arrow, got {len(body_orange_paths)}"
    print("[PASS] Exactly one orange item/arrow used.")

    # 8. Check external resources: no external fonts, images or scripts
    assert not any(el.tag.endswith('image') for el in root.iter()), "No <image> allowed"
    assert not any(el.tag.endswith('script') for el in root.iter()), "No <script> allowed"
    svg_str = ET.tostring(root, encoding='unicode')
    assert "http://" not in svg_str.replace("http://www.w3.org/2000/svg", ""), "No external URLs"
    assert "https://" not in svg_str, "No external URLs"
    print("[PASS] No external images, scripts or fonts.")

    print("\nALL AUDIT CHECKS PASSED PERFECTLY!")

if __name__ == "__main__":
    audit("test_candidate.svg")
