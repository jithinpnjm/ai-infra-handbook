import xml.etree.ElementTree as ET
import re
import sys

def audit(svg_path):
    print(f"=== Auditing {svg_path} ===")
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # 1. Structure
    children = list(root)
    tag0 = children[0].tag.split('}')[-1]
    tag1 = children[1].tag.split('}')[-1]
    print(f"1. Children: <{tag0}>, <{tag1}>")
    assert tag0 == 'title', f"Child 0 must be title, got {tag0}"
    assert tag1 == 'desc', f"Child 1 must be desc, got {tag1}"

    # 2. Dimensions
    w = root.get('width')
    h = root.get('height')
    vb = root.get('viewBox').split()
    print(f"2. Dimensions: {w}x{h}, viewBox={' '.join(vb)}")
    assert w == '1600', f"Width {w} != 1600"
    assert vb[0] == '0' and vb[1] == '0' and vb[2] == '1600'
    assert 900 <= float(vb[3]) <= 1200, f"Height {vb[3]} not in [900, 1200]"
    assert float(h) == float(vb[3]), f"Height {h} != viewBox {vb[3]}"

    # 3. Text elements & font sizes
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

    print(f"3. All {len(text_elements)} text elements have font-size >= 24px: PASS")
    for i, (t, fs) in enumerate(text_elements, 1):
        print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

    # 4. Expected labels
    expected_labels = [
        "KEDA: the switch and the dimmer",
        "Stage A",
        "zero to one: the switch, handled by KEDA operator (a plain HPA cannot scale to zero because the formula multiplies by zero)",
        "Stage B",
        "one to N: the dimmer, handled by the HPA that KEDA creates, fed by KEDA metrics adapter on the External Metrics API",
        "ScaledObject batch-embed",
        "minReplicaCount 0",
        "maxReplicaCount 50",
        "pollingInterval 15",
        "cooldownPeriod 300 (quiet time before one to zero)",
        "scaleDown stabilizationWindowSeconds 600",
        "kafka lagThreshold 200",
        "prometheus query sum vllm:num_requests_waiting threshold 5",
        "cron 0 8 to 0 20 Monday to Friday desiredReplicas 4 (pre-warm business hours)",
        "the largest desired count across active triggers wins, so cron acts as a floor in business hours",
        "ScaledJob transcribe-job",
        "one short Job per queued message, aws-sqs-queue queueLength 1, maxReplicaCount 20, strategy accurate",
        "ScaledObject",
        "keeps a long-running Deployment and changes its size",
        "scale-to-zero on a GPU service costs a cold start; fine for a nightly batch job, painful for a person typing in chat"
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
    print(f"\nExtra texts count: {len(extras)}")
    if extras:
        print(f"Extra texts: {extras}")
    assert len(extras) == 0, f"Found unexpected extra text: {extras}"

    # 5. Check forbidden words
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
    for t in found_texts:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for f in forbidden:
            assert f not in words, f"Forbidden word '{f}' in '{t}'!"
    print("\n5. No forbidden words found! PASS")

    # 6. Check orange count (#db8129)
    raw_svg = open(svg_path).read()
    orange_matches = re.findall(r'#db8129', raw_svg, re.IGNORECASE)
    print(f"\n6. Orange (#db8129) matches: {len(orange_matches)}")
    assert 1 <= len(orange_matches) <= 4, f"Unexpected orange count: {len(orange_matches)}"

    # 7. Check arrows
    markers = re.findall(r'marker-end', raw_svg)
    print(f"\n7. Arrow markers count: {len(markers)}")
    assert len(markers) == 1, f"Expected exactly 1 arrow between Stage A and Stage B, got {len(markers)}"

    print("\n=======================================================")
    print(">>> ALL STRICT AUDIT CHECKS PASSED PERFECTLY (100%) <<<")
    print("=======================================================")

audit("test_keda_candidate.svg")
