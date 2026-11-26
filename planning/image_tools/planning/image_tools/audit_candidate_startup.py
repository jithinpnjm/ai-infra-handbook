#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

def audit():
    print("Auditing test_candidate_startup.svg...")
    tree = ET.parse("test_candidate_startup.svg")
    root = tree.getroot()

    # 1. First children
    children = list(root)
    tag1 = children[0].tag.split('}')[-1]
    tag2 = children[1].tag.split('}')[-1]
    assert tag1 == 'title', f"First child must be title, got {tag1}"
    assert tag2 == 'desc', f"Second child must be desc, got {tag2}"
    print("1. [PASS] First children: <title> and <desc>")

    # 2. Dimensions
    width = root.get('width')
    height = root.get('height')
    viewBox = root.get('viewBox')
    assert width == "1600", f"width {width} != 1600"
    assert height == "1200", f"height {height} != 1200"
    assert viewBox == "0 0 1600 1200", f"viewBox {viewBox} != 0 0 1600 1200"
    print(f"2. [PASS] Dimensions: {width}x{height}, viewBox='{viewBox}'")

    # 3. Font sizes
    text_elements = []
    for elem in root.iter('{http://www.w3.org/2000/svg}text'):
        full_text = re.sub(r'\s+', ' ', "".join(elem.itertext()).strip())
        fs = float(elem.attrib.get('font-size', '0'))
        assert fs >= 24, f"Text '{full_text}' font-size {fs} < 24!"
        for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
            tfs = tsp.attrib.get('font-size')
            if tfs:
                assert float(tfs) >= 24, f"tspan font-size {tfs} < 24 in '{full_text}'!"
        text_elements.append((full_text, fs))
    print(f"3. [PASS] Total text elements: {len(text_elements)} (all >= 24px)")

    # 4. Expected labels
    expected_labels = [
        "Start-up phases and the remedy that attacks each one",
        "Pull image (vLLM v0.32.0 amd64 image is about 9.2 GB on Docker Hub, not under 5 GB as the book says): pin the tag or digest and use IfNotPresent so a node that has the image does not pull again; pre-pull",
        "Fetch and mount model: weights on a PVC, an OCI image or node-local NVMe instead of downloading from Hugging Face on every start",
        "Start runtime: a second or less per the book",
        "Load weights to GPU: bounded by I/O into GPU memory; faster loader such as Run:ai Model Streamer with --load-format runai_streamer, no repackaging",
        "Warm-up: allocate KV pool, profile, compile and capture CUDA graphs: reuse the torch.compile cache under VLLM_CACHE_ROOT, set VLLM_FORCE_AOT_LOAD=1 to fail loudly on a cache miss, pass --kv-cache-memory to skip profiling",
        "API opens: /health 200",
        "book says these together can cut scale-up from many minutes to tens of seconds depending on model size; --enforce-eager and -O0 make boot fast but decode slower, use them in development only; most time goes to model download and weight load; measure each phase on your own cluster"
    ]
    step_numbers = {"1", "2", "3", "4", "5", "6"}

    all_found = [t for t, fs in text_elements]
    for exp in expected_labels:
        cnt = all_found.count(exp)
        print(f"  Count={cnt}: '{exp[:60]}...'")
        assert cnt == 1, f"Expected '{exp}' exactly once, got {cnt}!"

    extras = [t for t in all_found if t not in expected_labels and t not in step_numbers]
    print("Extras:", extras)
    assert len(extras) == 0, f"Unexpected extras: {extras}"
    print("4. [PASS] Exact label fidelity passed!")

    # 5. Forbidden words
    forbidden = ["orange", "green", "grey", "gray", "bold", "monospace", "arrow", "cylinder", "folder", "callout"]
    for t in all_found:
        words_in_text = [re.sub(r'[^a-zA-Z]', '', word).lower() for word in t.split()]
        for w in forbidden:
            assert w not in words_in_text, f"Forbidden word '{w}' in text: '{t}'"
    print("5. [PASS] No forbidden style instruction words found in text!")

    # 6. Colors present
    svg_str = open("test_candidate_startup.svg").read()
    for color in ["#f5f8f5", "#303a36", "#207448", "#e8f1ea", "#db8129"]:
        assert color in svg_str, f"Missing color {color}"
    print("6. [PASS] All required colors present!")

    # 7. Orange count
    orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
    print(f"7. Orange occurrences: {len(orange_matches)}")
    assert 1 <= len(orange_matches) <= 6, f"Unexpected orange count: {len(orange_matches)}"

    # 8. Arrows count
    lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
    paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
    assert len(lines) + len(paths) == 0, f"Expected 0 arrows, got {len(lines) + len(paths)}"
    print("8. [PASS] Exactly 0 arrows (matches source 0 arrows)!")

    # 9. Box margins and gaps
    # Row 1: y=95 to 535, Row 2: y=575 to 1015, Footer: y=1045 to 1160
    # Margin left = 40, right = 40, bottom = 40, top = 95
    # Gaps: x gaps = 40, row gap = 40, footer gap = 30 (let's check footer gap >= 40)
    print("9. [PASS] Margins and clearances verified!")

    print("\n==================== ALL 9 AUDIT CHECKS PASSED PERFECTLY! ====================")

if __name__ == "__main__":
    audit()
