#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re
import pathlib

def audit_hpa_svg(svg_path):
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
        "Which API each HPA metric type reads",
        "Type",
        "Source API",
        "Provider",
        "Example",
        "Resource",
        "metrics.k8s.io",
        "metrics-server from kubelet and cAdvisor",
        "CPU or memory average utilisation relative to requests, or average value",
        "ContainerResource",
        "metrics.k8s.io per container",
        "scale on the app container only, ignoring sidecars",
        "Pods",
        "custom.metrics.k8s.io",
        "via Prometheus Adapter, KEDA or vendor adapters",
        "per-pod requests_in_flight or queue_length_per_pod",
        "Object",
        "custom.metrics.k8s.io for one object",
        "Ingress requests_per_second",
        "External",
        "external.metrics.k8s.io",
        "via KEDA, Prometheus Adapter or cloud adapters",
        "SQS queue length, Pub/Sub backlog, global QPS",
        "utilisation metrics need requests on all containers or the metric is unavailable",
        "memory is a poor scaling signal because it does not fall after load drops",
        "freshness delay: metrics-server scrapes kubelets about every 15 s, custom metrics add the Prometheus scrape interval of 15 to 30 s plus the adapter"
    ]

    all_found = [t for t, fs in text_elements]
    print(f"\n4. Checking {len(expected_labels)} expected labels against {len(all_found)} found:")
    all_ok = True
    for exp in expected_labels:
        cnt = all_found.count(exp)
        ok = (cnt == 1)
        if not ok:
            all_ok = False
        print(f"   [{'OK' if ok else 'FAIL'}] count={cnt}: '{exp}'")

    assert all_ok, "Some expected labels failed count == 1 check!"

    extras = [t for t in all_found if t not in expected_labels]
    print(f"\n5. Extras count: {len(extras)}")
    if extras:
        print("   Unexpected extras:", extras)
    assert len(extras) == 0, f"Unexpected extra texts found: {extras}"
    assert len(all_found) == len(expected_labels), f"Text count {len(all_found)} != {len(expected_labels)}"

    # 6. Check forbidden words
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
    for t in all_found:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for f in forbidden:
            assert f not in words, f"Forbidden word '{f}' in '{t}'!"

    print("\n6. No forbidden words found! (PASS)")

    # 7. Check orange count
    svg_str = pathlib.Path(svg_path).read_text()
    orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
    print(f"\n7. Orange #db8129 occurrences: {len(orange_matches)}")
    assert 1 <= len(orange_matches) <= 4, f"Unexpected orange count: {len(orange_matches)}"

    # 8. Check colors present
    assert "#f5f8f5" in svg_str
    assert "#303a36" in svg_str
    assert "#207448" in svg_str
    assert "#e8f1ea" in svg_str
    assert "#db8129" in svg_str
    print("8. All required colors present! (PASS)")

    # 9. Check arrows
    arrows = [e for e in root.iter() if 'marker-end' in e.attrib]
    print(f"\n9. Total arrows: {len(arrows)} (expected: 0)")
    assert len(arrows) == 0, f"Expected 0 arrows, got {len(arrows)}"

    print("\n=== ALL 9 AUDIT CHECKS PASSED PERFECTLY! ===")

if __name__ == "__main__":
    import sys
    audit_hpa_svg(sys.argv[1] if len(sys.argv) > 1 else "candidate_hpa_metrics.svg")
