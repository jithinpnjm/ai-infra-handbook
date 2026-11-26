import xml.etree.ElementTree as ET
import re
import pathlib

def audit_svg(svg_path):
    print(f"Auditing {svg_path}...")
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # 1. First children check: <title> and <desc>
    children = list(root)
    first_tag = children[0].tag.split('}')[-1]
    second_tag = children[1].tag.split('}')[-1]
    print(f"1. Children: <{first_tag}>, <{second_tag}>")
    assert first_tag == "title", f"First child must be <title>, got <{first_tag}>"
    assert second_tag == "desc", f"Second child must be <desc>, got <{second_tag}>"

    # 2. Dimensions and canvas check
    width = root.attrib.get("width")
    height = root.attrib.get("height")
    viewBox = root.attrib.get("viewBox")
    print(f"2. Dimensions: width={width}, height={height}, viewBox={viewBox}")
    assert width == "1600"
    vb_parts = [float(x) for x in viewBox.split()]
    assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
    assert 900 <= vb_parts[3] <= 1200
    assert float(height) == vb_parts[3]

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

    print(f"\n3. Total text elements: {len(text_elements)} (all font-sizes >= 24px)")
    for i, (t, fs) in enumerate(text_elements, 1):
        print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

    # 4. Expected labels fidelity
    expected_labels = [
        "A long loop must look alive: the four UX tools and Ctrl+C",
        "Need",
        "Feature",
        "Long loop with no progress looks like a hang",
        "progress bar",
        "Waiting on something",
        "spinner",
        "Watch a changing state",
        "--watch polls and redraws the screen",
        "Stream new output",
        "--follow",
        "Operation that finishes asynchronously",
        "--wait and --timeout flags; poll the status endpoint with backoff like kubectl rollout status",
        "User presses Ctrl+C",
        "catch KeyboardInterrupt, clean up, return exit code 130",
        "start operation",
        "poll status with backoff",
        "done, or --timeout reached",
        "exit code",
        "progress and spinners go to stderr and only on a terminal",
        "Think of the person running your tool at 3 a.m."
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
    svg_str = pathlib.Path(svg_path).read_text(encoding="utf-8")
    orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
    print(f"\n7. Orange #db8129 occurrences: {len(orange_matches)}")
    assert 1 <= len(orange_matches) <= 8, f"Unexpected orange count: {len(orange_matches)}"

    # 8. Check colors present
    assert "#f5f8f5" in svg_str
    assert "#303a36" in svg_str
    assert "#207448" in svg_str
    assert "#e8f1ea" in svg_str
    assert "#db8129" in svg_str
    print("\n8. All required colors present! (PASS)")

    # 9. Check arrows count
    lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
    paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
    total_arrows = len(lines) + len(paths)
    print(f"\n9. Total arrows with marker-end: {total_arrows}")
    assert total_arrows == 3, f"Expected 3 arrows, got {total_arrows}"

    # 10. Check external resources
    assert not any(el.tag.endswith('image') for el in root.iter()), "No <image> allowed"
    assert not any(el.tag.endswith('script') for el in root.iter()), "No <script> allowed"
    assert "http://" not in svg_str.replace("http://www.w3.org/2000/svg", ""), "No external URLs"
    assert "https://" not in svg_str, "No external URLs"
    print("\n10. External resources check: PASS")

    print("\n=== ALL AUDIT CHECKS PASSED PERFECTLY! ===")

if __name__ == "__main__":
    audit_svg("planning/image_tools/candidate_long_running_ux.svg")
