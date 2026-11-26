#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re, sys, pathlib

expected_labels = [
    "Keeping the GPU, its NIC and its CPUs on one NUMA node",
    "NUMA node 0",
    "NUMA node 1",
    "Aligned",
    "GPU, NIC VF or RDMA device, and the pod's CPUs all on NUMA node 0",
    "transfers stay inside the node; fast",
    "Misaligned",
    "pod CPUs on node 0 but the NIC on node 1",
    "every transfer crosses the link between sockets and takes the slower road",
    "how to keep them together",
    "kubelet Topology Manager with the single-numa-node or best-effort policy, together with the CPU Manager and the device plugins",
    "Verify after the pod starts: nvidia-smi topo -m, ibdev2netdev",
    "same on the host: pin test CPUs to the NUMA node of the NIC",
    "A scheduler can place CPUs on one node and the network card on the other, so check the placement after the pod starts"
]

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
    assert 900 <= vb_parts[3] <= 1200, f"Height {vb_parts[3]} outside 900..1200"
    assert int(height) == int(vb_parts[3]), f"height {height} != viewBox height {vb_parts[3]}"

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
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
    for t in found_texts:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for w in words:
            assert w not in forbidden, f"Forbidden word '{w}' found in text: '{t}'"

    print("\n6. Forbidden words check: PASS!")

    # 6. Arrows count
    arrows = [el for el in root.iter() if 'marker-end' in el.attrib]
    print(f"\n7. Arrow count: {len(arrows)}")
    assert len(arrows) == 0, f"Expected 0 arrows, got {len(arrows)}"
    print("[PASS] Exactly 0 arrows present.")

    # 7. Check orange usage: 1 to 4 occurrences of #db8129
    svg_str = pathlib.Path(svg_path).read_text(encoding="utf-8")
    orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
    print(f"\n8. Orange #db8129 occurrences: {len(orange_matches)}")
    assert 1 <= len(orange_matches) <= 4, f"Unexpected orange count: {len(orange_matches)}"

    # 8. Check all required colors present
    for c in ["#f5f8f5", "#303a36", "#207448", "#e8f1ea", "#db8129"]:
        assert c in svg_str, f"Missing required color: {c}"
    print("[PASS] All required colors present.")

    print("\n=== ALL AUDIT CHECKS PASSED PERFECTLY! ===")

if __name__ == '__main__':
    audit('test_candidate_numa.svg')
