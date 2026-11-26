import xml.etree.ElementTree as ET
import re
import pathlib

def audit(svg_path):
    print(f"Auditing {svg_path}...")
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # 1. First children check: <title> and <desc>
    children = list(root)
    first_tag = children[0].tag.split('}')[-1]
    second_tag = children[1].tag.split('}')[-1]
    print(f"1. First child: <{first_tag}>, Second child: <{second_tag}>")
    assert first_tag == 'title', f"First child must be title, got {first_tag}"
    assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"

    # Check title text
    title_text = "".join(children[0].itertext()).strip()
    expected_title = "GPUs sit idle in the timeline: seven questions, each answered by a measurement"
    assert title_text == expected_title, f"Unexpected title text: '{title_text}'"
    print(f"   Title text matches: '{title_text}'")

    # 2. Dimensions
    width = root.get('width')
    viewBox = root.get('viewBox')
    height = root.get('height')
    print(f"2. Dimensions: width={width}, height={height}, viewBox={viewBox}")
    assert width == "1600", f"Expected width 1600, got {width}"
    assert viewBox == "0 0 1600 1200", f"Expected viewBox '0 0 1600 1200', got {viewBox}"
    assert height == "1200", f"Expected height 1200, got {height}"

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
        "GPUs sit idle in the timeline: seven questions, each answered by a measurement",
        "idle gap (bubble): time between kernels or collectives",
        "Is the data loader the bottleneck? Empty queue, busy workers, a busy iostat, a slow network filesystem",
        "Is the CPU the limiter? Single-thread Python launch overhead, torch ops launching tiny kernels",
        "fix: CUDA graphs or compile",
        "Is host memory pinned, is the PCIe link at x16, is the NUMA placement right?",
        "Is communication exposed, meaning not overlapped with compute?",
        "Is a straggler rank late: thermal throttle, bad link, noisy neighbour?",
        "Is the checkpoint blocking the step?",
        "Is GPU-Util high while SM activity is low? Many small kernels",
        "Outcome metrics to read first",
        "throughput (tokens/s or samples/s per GPU and aggregate)",
        "step time breakdown: data wait, H2D, forward, backward, exposed communication, optimizer, checkpoint",
        "MFU",
        "scaling efficiency = throughput(N) / (N x throughput(1))",
        "goodput = GPU-hours of useful work / GPU-hours paid, excluding restarts, failures, checkpoint stalls, stragglers and idle waiting",
        "cost: USD per million tokens or per training run",
        "Answer each question with a measurement rather than an opinion"
    ]

    step_numbers = {"1", "2", "3", "4", "5", "6", "7"}
    found_texts = [t for t, fs in text_elements]

    print(f"\n4. Checking {len(expected_labels)} expected labels against found texts:")
    all_ok = True
    for exp in expected_labels:
        cnt = found_texts.count(exp)
        ok = (cnt == 1)
        if not ok:
            all_ok = False
        print(f"   [{'OK' if ok else 'FAIL'}] count={cnt}: '{exp}'")
    assert all_ok, "Some expected labels failed count == 1 check!"

    extras = [t for t in found_texts if t not in expected_labels and t not in step_numbers]
    print(f"\nExtra texts: {extras}")
    assert len(extras) == 0, f"Found unexpected extra text: {extras}"

    for s in step_numbers:
        cnt = found_texts.count(s)
        assert cnt == 1, f"Step number {s} count {cnt} != 1!"

    # 5. Check forbidden words
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
    for t in found_texts:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for f in forbidden:
            assert f not in words, f"Forbidden word '{f}' in '{t}'!"

    print("\n5. No forbidden words found! (PASS)")

    # 6. Check orange count
    svg_str = pathlib.Path(svg_path).read_text()
    orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
    print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
    assert 1 <= len(orange_matches) <= 4, f"Unexpected orange count: {len(orange_matches)}"

    # 7. Check colors present
    assert "#f5f8f5" in svg_str
    assert "#303a36" in svg_str
    assert "#207448" in svg_str
    assert "#e8f1ea" in svg_str
    assert "#db8129" in svg_str
    print("7. All required colors present! (PASS)")

    # 8. Check arrows count
    lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
    paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
    total_arrows = len(lines) + len(paths)
    print(f"\n8. Total arrows with marker-end: {total_arrows} (expected: 0)")
    assert total_arrows == 0, f"Expected 0 arrows, got {total_arrows}"

    print("\nALL AUDIT CHECKS PASSED PERFECTLY!")

audit("test_candidate_gpu_starvation.svg")
