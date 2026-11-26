import xml.etree.ElementTree as ET
import re
import sys

def audit_svg(svg_path):
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

    # 2. Dimensions
    width = root.get('width')
    viewBox = root.get('viewBox')
    height = root.get('height')
    print(f"2. Dimensions: width={width}, height={height}, viewBox={viewBox}")
    assert width == "1600", f"Expected width 1600, got {width}"
    assert viewBox.startswith("0 0 1600 "), f"viewBox must start with '0 0 1600 ', got {viewBox}"
    vb_parts = [float(x) for x in viewBox.split()]
    assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
    assert 900 <= vb_parts[3] <= 1200, f"Height {vb_parts[3]} outside 900-1200 range"
    assert int(height) == int(vb_parts[3]), f"height {height} != viewBox height {vb_parts[3]}"

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
        "Checkpoint before the time limit: SIGUSR1 reaches the batch shell, then the trainer",
        "Job starts",
        "Time limit: SIGTERM, then SIGKILL after KillWait (default 30 s)",
        "#SBATCH --signal=B:USR1@180: Slurm sends SIGUSR1 to the batch shell",
        "Batch shell (script)",
        "trap kill -USR1 $pid; wait $pid USR1",
        "python train.py running in the background (&), pid saved in $pid",
        "wait $pid",
        "Slurm sends SIGUSR1 to the batch shell",
        "trap fires at once because the shell is in wait, not in a foreground command",
        "kill -USR1 forwards the signal to the training process",
        "training writes the checkpoint",
        "wait returns, job ends cleanly",
        "If python train.py ran in the foreground, the shell would defer the trap until it finished",
        "Start long-running children in the background and wait for them"
    ]

    step_numbers = {"1", "2", "3", "4", "5"}

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

    extras = [t for t in found_texts if t not in expected_labels and t not in step_numbers]
    print(f"\nExtra texts: {extras}")
    assert len(extras) == 0, f"Found unexpected extra text: {extras}"

    for s in step_numbers:
        cnt = found_texts.count(s)
        assert cnt == 1, f"Step number {s} count {cnt} != 1!"

    print("   All step numbers 1, 2, 3, 4, 5 present in number circles. (PASS)")

    # 5. Check forbidden words
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
    for t in found_texts:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for f in forbidden:
            assert f not in words, f"Forbidden word '{f}' in '{t}'!"

    print("\n5. No forbidden words found! (PASS)")

    # 6. Check orange count
    with open(svg_path, 'r', encoding='utf-8') as f:
        svg_str = f.read()
    orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
    print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
    assert 1 <= len(orange_matches) <= 8, f"Unexpected orange count: {len(orange_matches)}"

    print("\nALL AUDIT CHECKS PASSED PERFECTLY!")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "test_candidate_job.svg"
    audit_svg(target)
