import re
import xml.etree.ElementTree as ET

def audit(svg_path):
    print(f"=== AUDITING {svg_path} ===")
    tree = ET.parse(svg_path)
    root = tree.getroot()
    raw = open(svg_path).read()

    # 1. Structure: <title> and <desc> are first children
    children = list(root)
    t1 = children[0].tag.split('}')[-1]
    t2 = children[1].tag.split('}')[-1]
    print(f"1. Children 0 & 1: <{t1}>, <{t2}>")
    assert t1 == "title", f"First child must be title, got {t1}"
    assert t2 == "desc", f"Second child must be desc, got {t2}"

    # 2. Dimensions & viewBox
    w = root.get("width")
    h = root.get("height")
    vb = root.get("viewBox").split()
    print(f"2. Width: {w}, Height: {h}, viewBox: {root.get('viewBox')}")
    assert w == "1600", f"Width must be 1600, got {w}"
    assert vb[0] == "0" and vb[1] == "0" and vb[2] == "1600"
    assert 900 <= float(vb[3]) <= 1200
    assert float(h) == float(vb[3])

    # 3. Text elements & font sizes >= 24 px
    font_sizes = []
    text_elements = []
    for el in root.iter('{http://www.w3.org/2000/svg}text'):
        txt = re.sub(r'\s+', ' ', "".join(el.itertext()).strip())
        fs = float(el.attrib.get('font-size', 0))
        assert fs >= 24, f"Text '{txt}' font-size {fs} < 24!"
        for tsp in el.iter('{http://www.w3.org/2000/svg}tspan'):
            tfs = tsp.attrib.get('font-size')
            if tfs is not None:
                assert float(tfs) >= 24, f"tspan font-size {tfs} < 24 in '{txt}'!"
        font_sizes.append(fs)
        text_elements.append((txt, fs))

    print(f"3. All {len(text_elements)} text elements have font-size >= 24px (min={min(font_sizes)}, max={max(font_sizes)}).")

    # 4. Banned style words
    banned = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'callout', 'sub-line', 'subline', 'takeaway']
    for t, fs in text_elements:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for bw in banned:
            assert bw not in words, f"Forbidden word '{bw}' found in text: '{t}'"
    print("4. Banned styling words: PASS (none present)")

    # 5. Expected labels presence
    expected_labels = [
        "Worked example: masking numbers to rank distinct errors",
        "grep -i error train.log",
        "10:20:01 ERROR NCCL timeout on rank 3",
        "10:31:09 ERROR NCCL timeout on rank 5",
        "10:40:00 ERROR CUDA out of memory on gpu=2",
        "WARN loss spike",
        "sed -E s/[0-9]+/N/g",
        "N:N:N ERROR NCCL timeout on rank N",
        "N:N:N ERROR CUDA out of memory on gpu=N",
        "sort",
        "uniq -c",
        "2 N:N:N ERROR NCCL timeout on rank N",
        "1 N:N:N ERROR CUDA out of memory on gpu=N",
        "sort -rn | head",
        "groups the two identical NCCL lines next to each other",
        "ranks them with the count 2 line first",
        "Masking the numbers makes different ranks the same message, so uniq can count them"
    ]
    cleaned_all = " ".join(re.sub(r'<[^>]+>', ' ', raw).split())
    for lbl in expected_labels:
        assert lbl in cleaned_all, f"Expected label missing: '{lbl}'"
    print(f"5. All {len(expected_labels)} expected content labels found in SVG text: PASS")

    # 6. Arrows count
    lines_arr = [l for l in root.iter('{http://www.w3.org/2000/svg}line') if 'marker-end' in l.attrib]
    paths_arr = [p for p in root.iter('{http://www.w3.org/2000/svg}path') if 'marker-end' in p.attrib]
    total_arrows = len(lines_arr) + len(paths_arr)
    print(f"6. Total arrows with marker-end: {total_arrows}")
    assert total_arrows == 4, f"Expected 4 arrows between 5 stages, got {total_arrows}"

    # 7. Orange usage
    orange_occurrences = re.findall(r'#db8129', raw, re.IGNORECASE)
    print(f"7. Orange #db8129 occurrences: {len(orange_occurrences)}")
    assert len(orange_occurrences) == 1, f"Expected exactly 1 orange highlight, got {len(orange_occurrences)}"

    # 8. No external images, scripts, fonts
    assert not any(el.tag.endswith('image') for el in root.iter()), "No <image> allowed"
    assert not any(el.tag.endswith('script') for el in root.iter()), "No <script> allowed"
    assert "http://" not in raw.replace("http://www.w3.org/2000/svg", ""), "No external URLs"
    assert "https://" not in raw, "No external URLs"
    print("8. No external images, scripts or fonts: PASS")

    # 9. Check number circles
    digits = [t for t, fs in text_elements if t.isdigit()]
    assert sorted(digits) == ["1", "2", "3", "4", "5"], f"Expected number circles 1-5, got {digits}"
    print("9. Number circles 1 to 5: PASS")

    print("\nALL AUDIT CHECKS PASSED PERFECTLY!")

if __name__ == '__main__':
    audit('test_pipeline.svg')
