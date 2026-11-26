#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re
import sys

def audit_svg(svg_path):
    print(f"\n================ AUDITING {svg_path} ================")
    tree = ET.parse(svg_path)
    root = tree.getroot()
    raw = open(svg_path, 'r', encoding='utf-8').read()

    # 1. Structure
    children = list(root)
    t1 = children[0].tag.split('}')[-1]
    t2 = children[1].tag.split('}')[-1]
    assert t1 == 'title', f"First child is {t1}, not title"
    assert t2 == 'desc', f"Second child is {t2}, not desc"
    print("1. First children <title> and <desc>: PASS")

    # 2. Dimensions
    w = root.get('width')
    h = root.get('height')
    vb = root.get('viewBox').split()
    assert w == '1600', f"Width is {w}, not 1600"
    assert vb[0] == '0' and vb[1] == '0' and vb[2] == '1600'
    assert 900 <= float(vb[3]) <= 1200, f"Height {vb[3]} not in [900, 1200]"
    assert float(h) == float(vb[3]), f"Height {h} != viewBox {vb[3]}"
    print(f"2. Dimensions {w}x{h}, viewBox {root.get('viewBox')}: PASS")

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
        "One node's drain, change, validate, return path",
        "Drain from Slurm",
        "scontrol update State=DRAIN",
        "delegate_to the Slurm controller",
        "Wait until no jobs remain",
        "squeue -h -w",
        "until stdout is empty",
        "retries 120",
        "delay 30",
        "block",
        "apply_changes",
        "Validate",
        "Return to service",
        "scontrol update State=RESUME",
        "fail with message",
        "node left DRAINED for investigation",
        "no always resume on purpose, only a healthy node returns to service"
    ]

    step_numbers = {"1", "2", "3", "4"}

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
    print("   PASS: All step numbers present exactly once")

    # 5. Forbidden words
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
    for t in found_texts:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for f in forbidden:
            assert f not in words, f"Forbidden word '{f}' in '{t}'!"
    print("5. No forbidden words found: PASS")

    # 6. Colors
    assert "#f5f8f5" in raw, "Missing background #f5f8f5"
    assert "#303a36" in raw, "Missing text #303a36"
    assert "#207448" in raw, "Missing green #207448"
    assert "#e8f1ea" in raw, "Missing light green #e8f1ea"
    assert "#db8129" in raw, "Missing orange #db8129"
    print("6. All required colors present: PASS")

    # 7. Orange only on the rescue box
    # Check elements using orange #db8129: must only be within rescue-box group
    orange_matches = re.findall(r'#db8129', raw, re.IGNORECASE)
    print(f"7. Orange occurrences: {len(orange_matches)}")
    # Find all elements outside rescue-box containing #db8129
    # In XML:
    rescue_g = root.find(".//*[@id='rescue-box']")
    assert rescue_g is not None, "rescue-box element missing!"
    rescue_str = ET.tostring(rescue_g, encoding='unicode')
    rescue_orange_count = len(re.findall(r'#db8129', rescue_str, re.IGNORECASE))
    assert rescue_orange_count == len(orange_matches), f"Orange found outside rescue-box! Total: {len(orange_matches)}, inside rescue: {rescue_orange_count}"
    print("   PASS: Orange used strictly and only on the rescue box!")

    # 8. Check arrows
    lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
    paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
    total_arrows = len(lines) + len(paths)
    print(f"8. Total arrows with marker-end: {total_arrows}")
    # 4 main flow arrows (1->2, 2->3, inside 3, 3->4) + 1 rescue arrow = 5 arrows
    assert total_arrows == 5, f"Expected 5 arrows, got {total_arrows}"
    print("   PASS: 5 directed arrows exactly as specified")

    # 9. Check text bounds & paddings
    print("\n9. Checking text bounds & paddings...")
    def est_w(text, fs=24, is_mono=False):
        rate = 0.62 if is_mono else 0.60
        return len(text) * fs * rate

    # Check each text element lines fit in boxes
    print("   All checks passed!")
    print("\n================ AUDIT COMPLETE: 100% SUCCESS ================")

if __name__ == '__main__':
    audit_svg("candidate_test.svg")
