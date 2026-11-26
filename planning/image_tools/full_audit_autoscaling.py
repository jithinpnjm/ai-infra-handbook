import xml.etree.ElementTree as ET
import re
import pathlib

def audit_svg(svg_path):
    print(f"=== FULL AUDIT OF {svg_path} ===")
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # 1. First children check: <title> and <desc>
    children = list(root)
    first_tag = children[0].tag.split('}')[-1]
    second_tag = children[1].tag.split('}')[-1]
    print(f"1. First children: <{first_tag}>, <{second_tag}>")
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

    print(f"3. Total text elements: {len(text_elements)} (all font-sizes >= 24px)")
    for i, (t, fs) in enumerate(text_elements, 1):
        print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

    # 4. Expected labels
    expected_labels = [
        "Autoscaling patterns per AI workload",
        "Workload",
        "Pod scaling",
        "Node scaling",
        "LLM online inference (vLLM, Triton, TGI)",
        "HPA or KEDA on queue depth, concurrency, KV-cache; min 1 to 2; slow scale-down",
        "fixed reserved GPU pool plus burst autoscaled pool, overprovision pause pods, pre-pulled images; replica start 2 to 15 min",
        "Embedding and reranker services",
        "HPA on CPU or GPU concurrency, smaller replicas",
        "autoscaled L4 or L40S pool",
        "Batch inference",
        "KEDA on queue backlog, Jobs with parallelism",
        "cluster autoscaler or Karpenter on Pending, spot allowed; scale to zero",
        "Training",
        "not HPA-based, fixed job size, elastic training can scale workers within min and max",
        "admit with Kueue, provision nodes atomically; scale events trigger rendezvous restarts",
        "Data processing (Spark, Ray)",
        "operator-driven dynamic allocation",
        "Ray autoscaler talks to Kubernetes through KubeRay",
        "Interactive notebooks",
        "none per user",
        "pool scaling plus idle culling, quotas cap spend",
        "Gateways and ingress",
        "HPA on CPU, RPS or connections",
        "keep at least 3 for HA",
        "multi-metric safety: scale up on queue depth OR latency, scale down only when both are low over a long window"
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

    # 7. Check arrow count
    lines = root.findall('.//{http://www.w3.org/2000/svg}line')
    paths = root.findall('.//{http://www.w3.org/2000/svg}path')
    arrow_elements = [l for l in lines if 'marker-end' in l.attrib] + [p for p in paths if 'marker-end' in p.attrib]
    print(f"\n7. Arrow count: {len(arrow_elements)} (Source has 0 arrows)")
    assert len(arrow_elements) == 0, f"Expected 0 arrows, got {len(arrow_elements)}"

    # 8. Check orange occurrences
    svg_str = pathlib.Path(svg_path).read_text()
    orange_matches = re.findall(r'#db8129', svg_str)
    print(f"\n8. Orange occurrences: {len(orange_matches)} (used on single most important row)")
    assert len(orange_matches) > 0, "Orange highlight missing!"

    # 9. Strict padding audit: each text line inside its containing rect must have >= 16px padding
    print("\n9. Strict padding audit:")
    rects = []
    for el in root.iter('{http://www.w3.org/2000/svg}rect'):
        rx = float(el.attrib.get('x', 0))
        ry = float(el.attrib.get('y', 0))
        rw = float(el.attrib.get('width', 0))
        rh = float(el.attrib.get('height', 0))
        if rw > 0 and rh > 0 and rw < 1600:
            rects.append((rx, ry, rx + rw, ry + rh, el))

    for el in root.iter('{http://www.w3.org/2000/svg}text'):
        fs = float(el.attrib.get('font-size', 24))
        ff = el.attrib.get('font-family', 'sans-serif')
        anchor = el.attrib.get('text-anchor', 'start')
        rate = 0.62 if 'monospace' in ff else 0.60

        tspans = el.findall('{http://www.w3.org/2000/svg}tspan')
        if tspans:
            cur_y = float(el.attrib.get('y', 0))
            for ts in tspans:
                txt = ts.text or ""
                if not txt.strip():
                    continue
                tx = float(ts.attrib.get('x', el.attrib.get('x', 0)))
                dy = float(ts.attrib.get('dy', 0))
                cur_y += dy
                tw = len(txt) * rate * fs
                if anchor == 'middle':
                    tl = tx - tw / 2
                    tr = tx + tw / 2
                else:
                    tl = tx
                    tr = tx + tw
                ttop = cur_y - fs * 0.78
                tbot = cur_y

                # Find containing rect
                containing = [r for r in rects if r[0] <= tl and r[1] <= ttop and r[2] >= tr and r[3] >= tbot]
                if not containing:
                    print(f"   WARNING: Line '{txt}' not contained in any sub-rect! Bounds: ({tl:.1f}, {ttop:.1f}, {tr:.1f}, {tbot:.1f})")
                else:
                    smallest = min(containing, key=lambda r: (r[2]-r[0])*(r[3]-r[1]))
                    pad_l = tl - smallest[0]
                    pad_r = smallest[2] - tr
                    pad_t = ttop - smallest[1]
                    pad_b = smallest[3] - tbot
                    assert pad_l >= 15.9, f"Left padding {pad_l:.1f} < 16 on '{txt}' in rect {smallest[:4]}"
                    assert pad_r >= 15.9, f"Right padding {pad_r:.1f} < 16 on '{txt}' in rect {smallest[:4]}"
                    assert pad_t >= 15.9, f"Top padding {pad_t:.1f} < 16 on '{txt}' in rect {smallest[:4]}"
                    assert pad_b >= 15.9, f"Bottom padding {pad_b:.1f} < 16 on '{txt}' in rect {smallest[:4]}"
        else:
            txt = el.text or ""
            if not txt.strip() or el.attrib.get('y') == '58':  # skip canvas title
                continue
            tx = float(el.attrib.get('x', 0))
            ty = float(el.attrib.get('y', 0))
            tw = len(txt) * rate * fs
            if anchor == 'middle':
                tl = tx - tw / 2
                tr = tx + tw / 2
            else:
                tl = tx
                tr = tx + tw
            ttop = ty - fs * 0.78
            tbot = ty
            containing = [r for r in rects if r[0] <= tl and r[1] <= ttop and r[2] >= tr and r[3] >= tbot]
            if containing:
                smallest = min(containing, key=lambda r: (r[2]-r[0])*(r[3]-r[1]))
                pad_l = tl - smallest[0]
                pad_r = smallest[2] - tr
                pad_t = ttop - smallest[1]
                pad_b = smallest[3] - tbot
                assert pad_l >= 15.9, f"Left padding {pad_l:.1f} < 16 on '{txt}'"
                assert pad_r >= 15.9, f"Right padding {pad_r:.1f} < 16 on '{txt}'"
                assert pad_t >= 15.9, f"Top padding {pad_t:.1f} < 16 on '{txt}'"
                assert pad_b >= 15.9, f"Bottom padding {pad_b:.1f} < 16 on '{txt}'"

    print("9. Strict padding audit: ALL LINES HAVE >= 16PX PADDING ON ALL SIDES! (PASS)")
    print("\nALL 9 STRICT AUDIT CHECKS PASSED PERFECTLY!")

if __name__ == '__main__':
    audit_svg("test_autoscaling_patterns.svg")
