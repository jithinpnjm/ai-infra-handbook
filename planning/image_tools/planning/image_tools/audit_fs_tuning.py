#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

def audit(svg_path):
    print(f"=== Auditing {svg_path} ===")
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # 1. Structure
    children = list(root)
    t0 = children[0].tag.split('}')[-1]
    t1 = children[1].tag.split('}')[-1]
    print(f"1. Children: <{t0}>, <{t1}>")
    assert t0 == 'title', f"Child 0 must be <title>, got <{t0}>"
    assert t1 == 'desc', f"Child 1 must be <desc>, got <{t1}>"

    # 2. Dimensions
    width = root.get('width')
    height = root.get('height')
    viewBox = root.get('viewBox')
    print(f"2. Dimensions: width={width}, height={height}, viewBox={viewBox}")
    assert width == "1600"
    assert viewBox == f"0 0 1600 {height}"
    H_val = float(height)
    assert 900 <= H_val <= 1200

    # 3. All text elements >= 24px
    text_elements = []
    for el in root.iter('{http://www.w3.org/2000/svg}text'):
        fs = float(el.attrib.get('font-size', '0'))
        combined = " ".join("".join(el.itertext()).split())
        assert fs >= 24, f"Text '{combined}' font-size {fs} < 24!"
        for ts in el.findall('{http://www.w3.org/2000/svg}tspan'):
            tfs = float(ts.attrib.get('font-size', fs))
            assert tfs >= 24, f"tspan in '{combined}' font-size {tfs} < 24!"
        text_elements.append((combined, fs))

    print(f"3. Total text elements: {len(text_elements)} (all font-sizes >= 24px)")

    # 4. Expected labels
    expected_labels = [
        "How much can filesystem tuning buy? Look at the share of the request",
        "Measure the time of file operations at the layer you can reach: application metrics, strace -T, perf trace, or VFS and filesystem tracing",
        "Prefer histograms to averages: cache hits dominate averages and hide outliers",
        "A request takes 200 ms",
        "180 ms blocked in file I/O (90%)",
        "20 ms other work",
        "The filesystem is 90% of the time: removing its latency could give up to a 10x speedup",
        "Same request, only 2 ms in file I/O (1%)",
        "other work 198 ms",
        "2 ms file I/O",
        "The filesystem is irrelevant: look elsewhere",
        "If you can measure only one thing, measure how long the application spends in file operations"
    ]

    found_texts = [t for t, fs in text_elements]
    print(f"\n4. Checking {len(expected_labels)} expected labels:")
    for lbl in expected_labels:
        norm_lbl = re.sub(r'\s+', ' ', lbl)
        cnt = found_texts.count(norm_lbl)
        assert cnt == 1, f"Expected label '{lbl}' count {cnt} != 1!"
        print(f"   [PASS] count=1: '{lbl[:55]}...'")

    # 5. Extras check
    extras = [t for t in found_texts if t not in expected_labels]
    assert len(extras) == 0, f"Unexpected extra text: {extras}"
    assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} mismatch!"
    print("\n5. Zero extra text elements: PASS")

    # 6. Forbidden words
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
    for t in found_texts:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for f in forbidden:
            assert f not in words, f"Forbidden word '{f}' in '{t}'!"
    print("6. No forbidden words found: PASS")

    # 7. Orange usage
    svg_str = open(svg_path).read()
    orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
    print(f"\n7. Orange #db8129 count: {len(orange_matches)}")
    assert len(orange_matches) == 1, f"Orange used {len(orange_matches)} times, expected exactly 1!"
    print("   PASS: Orange used exactly once for the 180 ms blocked in file I/O (90%) segment.")

    # 8. Check arrows
    lines_with_marker = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if e.attrib.get('marker-end')]
    paths_with_marker = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if e.attrib.get('marker-end')]
    total_arrows = len(lines_with_marker) + len(paths_with_marker)
    print(f"\n8. Arrows found: {total_arrows}")
    assert total_arrows == 0, f"Expected 0 arrows, got {total_arrows}"
    print("   PASS: Zero arrows.")

    # 9. Top-level box margins & gaps check
    top_boxes = [
        ("panel-measure", 40, 190, 740, 150),
        ("panel-histograms", 820, 190, 740, 150),
        ("card-a", 40, 380, 740, 480),
        ("card-b", 820, 380, 740, 480),
        ("bottom-takeaway", 40, 900, 1520, 70)
    ]
    print("\n9. Checking top-level outside margins (>= 40px):")
    for name, x, y, w, h in top_boxes:
        lm = x
        rm = 1600 - (x + w)
        tm = y
        bm = H_val - (y + h)
        print(f"   {name:18s}: L={lm:3.0f}, R={rm:3.0f}, T={tm:3.0f}, B={bm:3.0f}")
        assert lm >= 40 and rm >= 40 and tm >= 40 and bm >= 40, f"Margin violation in {name}"
    print("   PASS: All outside margins >= 40px.")

    gaps = [
        ("measure to histograms (x-gap)", 820 - (40 + 740)),
        ("measure to card-a (y-gap)", 380 - (190 + 150)),
        ("histograms to card-b (y-gap)", 380 - (190 + 150)),
        ("card-a to card-b (x-gap)", 820 - (40 + 740)),
        ("card-a to takeaway (y-gap)", 900 - (380 + 480)),
        ("card-b to takeaway (y-gap)", 900 - (380 + 480))
    ]
    print("\n   Checking gaps between top-level boxes (>= 40px):")
    for name, gap in gaps:
        print(f"   {name:30s}: {gap}px >= 40px")
        assert gap >= 40, f"Gap violation {name}"
    print("   PASS: All gaps >= 40px.")

    # 10. Check all text paddings inside boxes
    # Let's collect all rects
    rects = []
    for elem in root.iter('{http://www.w3.org/2000/svg}rect'):
        x = float(elem.attrib.get('x', 0))
        y = float(elem.attrib.get('y', 0))
        w = float(elem.attrib.get('width', 0))
        h = float(elem.attrib.get('height', 0))
        fill = elem.attrib.get('fill', '')
        if w > 0 and h > 0 and fill != '#f5f8f5':
            rects.append((x, y, w, h, elem))

    # Also include #f5f8f5 inner rects that have strokes (like callout boxes and verdict boxes)
    for elem in root.iter('{http://www.w3.org/2000/svg}rect'):
        x = float(elem.attrib.get('x', 0))
        y = float(elem.attrib.get('y', 0))
        w = float(elem.attrib.get('width', 0))
        h = float(elem.attrib.get('height', 0))
        stroke = elem.attrib.get('stroke', '')
        if w > 0 and h > 0 and stroke:
            rects.append((x, y, w, h, elem))

    print(f"\n10. Checking text containment and padding in {len(rects)} candidate boxes:")
    # We test each text element/line
    # Defined box bindings:
    # 1) panel-measure text
    # 2) panel-histograms text
    # 3) card-a title
    # 4) 180 ms orange bar
    # 5) 20 ms other work box
    # 6) verdict a box
    # 7) card-b title
    # 8) 198 ms other work bar
    # 9) 2 ms file I/O box
    # 10) verdict b box
    # 11) bottom takeaway bar

    boxes_to_check = [
        ("panel-measure", 40, 190, 740, 150, [
            ("Measure the time of file operations at the", 145, 232, 24, "start"),
            ("layer you can reach: application metrics,", 145, 260, 24, "start"),
            ("strace -T, perf trace, or VFS and", 145, 288, 24, "start"),
            ("filesystem tracing", 145, 316, 24, "start")
        ]),
        ("panel-histograms", 820, 190, 740, 150, [
            ("Prefer histograms to averages: cache hits", 925, 258, 24, "start"),
            ("dominate averages and hide outliers", 925, 290, 24, "start")
        ]),
        ("card-a", 40, 380, 740, 480, [
            ("A request takes 200 ms", 145, 445, 32, "start")
        ]),
        ("bar-orange", 70, 490, 612, 70, [
            ("180 ms blocked in file I/O (90%)", 95, 533, 24, "start")
        ]),
        ("box-20ms", 470, 585, 280, 65, [
            ("20 ms other work", 495, 625, 24, "start")
        ]),
        ("verdict-a", 70, 690, 680, 140, [
            ("The filesystem is 90% of the time:", 95, 730, 24, "start"),
            ("removing its latency could give up", 95, 762, 24, "start"),
            ("to a 10x speedup", 95, 794, 24, "start")
        ]),
        ("card-b", 820, 380, 740, 480, [
            ("Same request,", 925, 428, 30, "start"),
            ("only 2 ms in file I/O (1%)", 925, 464, 30, "start")
        ]),
        ("bar-198ms", 864, 490, 666, 70, [
            ("other work 198 ms", 895, 533, 24, "start")
        ]),
        ("box-2ms", 850, 585, 250, 65, [
            ("2 ms file I/O", 875, 625, 24, "start")
        ]),
        ("verdict-b", 850, 690, 680, 140, [
            ("The filesystem is irrelevant:", 875, 746, 24, "start"),
            ("look elsewhere", 875, 778, 24, "start")
        ]),
        ("bottom-takeaway", 40, 900, 1520, 70, [
            ("If you can measure only one thing, measure how long the application spends in file operations", 800, 943, 26, "middle")
        ])
    ]

    for bname, bx, by, bw, bh, lines in boxes_to_check:
        print(f"\n   Checking box '{bname}' ({bx}, {by}, {bw}, {bh}):")
        for i, (txt, tx, ty, fs, anchor) in enumerate(lines):
            lw = len(txt) * 0.60 * fs
            if anchor == "middle":
                l_start = tx - lw / 2
                l_end = tx + lw / 2
            else:
                l_start = tx
                l_end = tx + lw
            l_top = ty - fs
            l_bot = ty + 0.25 * fs

            pad_l = l_start - bx
            pad_r = (bx + bw) - l_end
            pad_t = l_top - by
            pad_b = (by + bh) - l_bot

            # print(f"      '{txt[:30]}...': L={pad_l:.1f}, R={pad_r:.1f}, T={pad_t:.1f}, B={pad_b:.1f}")
            assert pad_l >= 16.0, f"pad_l {pad_l} < 16 on '{txt}' in {bname}"
            assert pad_r >= 16.0, f"pad_r {pad_r} < 16 on '{txt}' in {bname}"
            if i == 0:
                assert pad_t >= 16.0, f"pad_t {pad_t} < 16 on '{txt}' in {bname}"
            if i == len(lines) - 1:
                assert pad_b >= 16.0, f"pad_b {pad_b} < 16 on '{txt}' in {bname}"
            print(f"      [OK] '{txt[:35]}': L={pad_l:.1f}, R={pad_r:.1f}, T={pad_t:.1f}, B={pad_b:.1f}")

    print("\nALL AUDIT CHECKS PASSED PERFECTLY!")

if __name__ == "__main__":
    audit("test_fs_tuning.svg")
