#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re
import pathlib

def audit(svg_path):
    print(f"=== Auditing {svg_path} ===")
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # 1. First children check: <title> and <desc>
    children = list(root)
    first_tag = children[0].tag.split('}')[-1]
    second_tag = children[1].tag.split('}')[-1]
    print(f"1. Children: <{first_tag}>, <{second_tag}>")
    assert first_tag == "title", f"First child must be <title>, got <{first_tag}>"
    assert second_tag == "desc", f"Second child must be <desc>, got <{second_tag}>"
    title_text = "".join(children[0].itertext()).strip()
    assert title_text == "The rsync trailing slash: contents versus the directory itself"
    print("   PASS: First children are <title> and <desc>")

    # 2. Dimensions and canvas check
    width = root.attrib.get("width")
    height = root.attrib.get("height")
    viewBox = root.attrib.get("viewBox")
    print(f"2. Dimensions: width={width}, height={height}, viewBox={viewBox}")
    assert width == "1600", f"Width must be 1600, got {width}"
    assert viewBox.startswith("0 0 1600 "), f"viewBox must start with '0 0 1600 ', got {viewBox}"
    vb_parts = [float(x) for x in viewBox.split()]
    assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
    assert 900 <= vb_parts[3] <= 1200, f"Height {vb_parts[3]} outside 900..1200"
    assert float(height) == vb_parts[3], f"height {height} != viewBox height {vb_parts[3]}"
    print("   PASS: Canvas dimensions and viewBox valid")

    # 3. Text font-size >= 24px everywhere
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

    # 4. Expected labels fidelity
    expected_labels = [
        "The rsync trailing slash: contents versus the directory itself",
        "data",
        "a.pt",
        "b.pt",
        "/scratch/data",
        "rsync -a data/ gpu01:/scratch/data",
        "/scratch/data/a.pt",
        "/scratch/data/b.pt",
        "contents copied into the destination",
        "rsync -a data gpu01:/scratch/data",
        "/scratch/data/data/a.pt",
        "/scratch/data/data/b.pt",
        "the directory itself, nested copy",
        "scp -r data gpu01:/scratch/data",
        "/scratch/data/data/a.pt",
        "/scratch/data/data/b.pt",
        "also copies every byte again, even when nothing changed",
        "rsync -avhn --delete data/ gpu01:/scratch/data/ (dry run)",
        "read the list",
        "run again without -n",
        "--delete makes the destination match the source; an empty source deletes the destination contents"
    ]
    step_numbers = {"1", "2", "3"}

    found_texts = [t for t, fs in text_elements]
    print(f"\n4. Checking {len(expected_labels)} expected labels against {len(found_texts)} found:")
    
    all_ok = True
    for exp in set(expected_labels):
        expected_cnt = expected_labels.count(exp)
        cnt = found_texts.count(exp)
        ok = (cnt == expected_cnt)
        if not ok:
            all_ok = False
        print(f"   [{'OK' if ok else 'FAIL'}] count={cnt} (expected {expected_cnt}): '{exp[:60]}...'")

    assert all_ok, "Some expected labels failed count check!"
    print("   PASS: All expected labels found with exact counts")

    # 5. Extras check
    extras = [t for t in found_texts if t not in expected_labels and t not in step_numbers]
    print(f"5. Extras count: {len(extras)}")
    if extras:
        print("   Unexpected extras:", extras)
    assert len(extras) == 0, f"Unexpected extra texts found: {extras}"
    assert len(found_texts) == len(expected_labels) + len(step_numbers), f"Text count {len(found_texts)} != {len(expected_labels) + len(step_numbers)}"
    print("   PASS: Zero extra text elements")

    for s in step_numbers:
        cnt = found_texts.count(s)
        assert cnt == 1, f"Step number '{s}' count {cnt} != 1"
    print("   PASS: All step numbers 1, 2, 3 present exactly once")

    # 6. Forbidden words check
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
    for t in found_texts:
        if t in step_numbers:
            continue
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for f in forbidden:
            assert f not in words, f"Forbidden word '{f}' in '{t}'!"
    print("6. PASS: No forbidden words found")

    # 7. Check arrow count
    arrows = list(root.iter('{http://www.w3.org/2000/svg}line'))
    arrow_lines = [l for l in arrows if 'marker-end' in l.attrib]
    paths_with_marker = [p for p in root.iter('{http://www.w3.org/2000/svg}path') if 'marker-end' in p.attrib]
    total_arrows = len(arrow_lines) + len(paths_with_marker)
    print(f"7. Total arrows: {total_arrows} (expected 0)")
    assert total_arrows == 0, f"Expected 0 arrows, found {total_arrows}"
    print("   PASS: Arrow count matches source (0 arrows)")

    # 8. Orange usage check
    raw_svg = pathlib.Path(svg_path).read_text()
    oranges = re.findall(r'#db8129', raw_svg, re.IGNORECASE)
    print(f"8. Orange #db8129 occurrences: {len(oranges)}")
    assert len(oranges) == 1, f"Expected exactly 1 orange usage, got {len(oranges)}"
    print("   PASS: Orange used exactly once (on Card B outline)")

    # 9. External resources check
    assert not any(el.tag.endswith('image') for el in root.iter()), "No <image> allowed"
    assert not any(el.tag.endswith('script') for el in root.iter()), "No <script> allowed"
    print("9. PASS: No external images or scripts")

    print("\nALL AUDIT CHECKS PASSED PERFECTLY!")

if __name__ == "__main__":
    audit("test_rsync_candidate.svg")
