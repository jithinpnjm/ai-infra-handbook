import re
import xml.etree.ElementTree as ET

def run_audit(svg_path):
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # 1. First children <title> and <desc>
    children = list(root)
    t0 = children[0].tag.split('}')[-1]
    t1 = children[1].tag.split('}')[-1]
    assert t0 == "title", f"First child is {t0}, expected title"
    assert t1 == "desc", f"Second child is {t1}, expected desc"
    print("PASS: <title> and <desc> are first children.")

    # 2. Dimensions
    w = root.get('width')
    h = root.get('height')
    vb = root.get('viewBox')
    assert w == "1600", f"Width is {w}, expected 1600"
    assert 900 <= int(h) <= 1200, f"Height {h} not between 900 and 1200"
    assert vb == f"0 0 1600 {h}", f"viewBox {vb} mismatch"
    print(f"PASS: Dimensions {w}x{h}, viewBox '{vb}'.")

    # 3. Text font size >= 24
    for elem in root.iter('{http://www.w3.org/2000/svg}text'):
        fs = float(elem.attrib.get('font-size', 0))
        txt = "".join(elem.itertext()).strip()
        assert fs >= 24, f"Text '{txt}' font-size {fs} < 24"
        for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
            tfs = tsp.attrib.get('font-size')
            if tfs:
                assert float(tfs) >= 24, f"tspan '{tsp.text}' font-size {tfs} < 24"
    print("PASS: All text and tspan font-size >= 24px.")

    # 4. Content labels check
    expected_labels = [
        "Borrowing and lending quota inside a cohort",
        "Worked example with the chapter's numbers for ClusterQueue research, flavor h100-ondemand, resource nvidia.com/gpu: nominalQuota 128, borrowingLimit 64, lendingLimit 32; cpu nominalQuota 1024, memory nominalQuota 8Ti.",
        "128 GPUs owned by research",
        "32 GPUs that research may lend out when idle",
        "up to 64 GPUs borrowed from idle quota of other ClusterQueues in cohort gpu-fleet",
        "reclaimWithinCohort Any: take back lent quota from borrowers",
        "borrowWithinCohort policy LowerPriority with maxPriorityThreshold 100",
        "withinClusterQueue LowerPriority",
        "Team A borrows idle quota",
        "Team B submits a job and reclaims its own quota through preemption",
        "watch Workload conditions",
        "WorkloadPriorityClass sets queueing priority independent of pod priority"
    ]
    step_numbers = {"1", "2", "3"}

    text_elems = []
    for elem in root.iter('{http://www.w3.org/2000/svg}text'):
        full_text = re.sub(r'\s+', ' ', "".join(elem.itertext()).strip())
        text_elems.append(full_text)

    for exp in expected_labels:
        c = text_elems.count(exp)
        assert c == 1, f"Expected '{exp}' exactly once, got {c}"
    for sn in step_numbers:
        c = text_elems.count(sn)
        assert c == 1, f"Expected step number '{sn}' exactly once, got {c}"
    
    extras = [t for t in text_elems if t not in expected_labels and t not in step_numbers]
    assert len(extras) == 0, f"Unexpected extra texts: {extras}"
    print(f"PASS: Exactly the {len(expected_labels)} content labels and 3 step numbers present, zero extra words.")

    # 5. Forbidden style words in text
    forbidden = ["orange", "green", "grey", "bold", "monospace", "arrow"]
    for t in text_elems:
        for f in forbidden:
            assert not re.search(r'\b' + f + r'\b', t.lower()), f"Forbidden word '{f}' in '{t}'"
    print("PASS: No forbidden style words in text.")

    # 6. Arrows count
    lines_with_marker = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if e.attrib.get('marker-end')]
    paths_with_marker = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if e.attrib.get('marker-end')]
    assert len(lines_with_marker) + len(paths_with_marker) == 0, "Expected 0 arrows"
    print("PASS: Arrow count is 0.")

    # 7. Single orange used
    raw_svg = open(svg_path).read()
    oranges = re.findall(r'#db8129', raw_svg)
    assert len(oranges) >= 1, "Orange not found"
    print(f"PASS: Orange #db8129 used ({len(oranges)} occurrences in the highlight group).")

    # 8. Canvas margins >= 40px
    canvas_h = int(h)
    for elem in root.iter('{http://www.w3.org/2000/svg}text'):
        fs = float(elem.attrib['font-size'])
        anchor = elem.attrib.get('text-anchor', 'start')
        tspans = elem.findall('{http://www.w3.org/2000/svg}tspan')
        if tspans:
            cur_y = float(elem.attrib.get('y', 0))
            for tsp in tspans:
                dy = float(tsp.attrib.get('dy', 0))
                cur_y += dy
                line_txt = tsp.text.strip()
                lx = float(tsp.attrib.get('x', elem.attrib.get('x', 0)))
                w_line = len(line_txt) * fs * 0.60
                left = lx - w_line / 2.0 if anchor == 'middle' else (lx - w_line if anchor == 'end' else lx)
                right = left + w_line
                top = cur_y - fs * 0.75
                bot = cur_y + 4
                assert left >= 40, f"Left canvas margin violation: {left} < 40 for '{line_txt}'"
                assert right <= 1560, f"Right canvas margin violation: {right} > 1560 for '{line_txt}'"
                assert top >= 40, f"Top canvas margin violation: {top} < 40 for '{line_txt}'"
                assert bot <= canvas_h - 40, f"Bottom canvas margin violation: {bot} > {canvas_h - 40} for '{line_txt}'"
        else:
            line_txt = elem.text.strip()
            lx = float(elem.attrib.get('x', 0))
            ly = float(elem.attrib.get('y', 0))
            w_line = len(line_txt) * fs * 0.60
            left = lx - w_line / 2.0 if anchor == 'middle' else (lx - w_line if anchor == 'end' else lx)
            right = left + w_line
            top = ly - fs * 0.75
            bot = ly + 4
            assert left >= 40, f"Left canvas margin violation: {left} < 40 for '{line_txt}'"
            assert right <= 1560, f"Right canvas margin violation: {right} > 1560 for '{line_txt}'"
            assert top >= 40, f"Top canvas margin violation: {top} < 40 for '{line_txt}'"
            assert bot <= canvas_h - 40, f"Bottom canvas margin violation: {bot} > {canvas_h - 40} for '{line_txt}'"
    print("PASS: Canvas margin >= 40px for every text line.")

    # 9. Box paddings >= 16px and icon non-overlap
    boxes = [
        ("Overview", (40, 125, 1520, 135), (65, 164, 56, 56), [
            ("Worked example with the chapter's numbers for ClusterQueue research, flavor h100-ondemand, ", 835, 167, 24, 'middle'),
            ("resource nvidia.com/gpu: nominalQuota 128, borrowingLimit 64, lendingLimit 32; ", 835, 199, 24, 'middle'),
            ("cpu nominalQuota 1024, memory nominalQuota 8Ti.", 835, 231, 24, 'middle'),
        ]),
        ("Card 1", (70, 385, 450, 195), (267, 400, 56, 44), [
            ("128 GPUs owned by research", 295, 505, 24, 'middle'),
        ]),
        ("Card 2", (560, 385, 450, 195), (757, 400, 56, 44), [
            ("32 GPUs that research ", 785, 490, 24, 'middle'),
            ("may lend out when idle", 785, 522, 24, 'middle'),
        ]),
        ("Card 3", (1050, 385, 460, 195), (1252, 395, 56, 44), [
            ("up to 64 GPUs borrowed ", 1280, 470, 24, 'middle'),
            ("from idle quota of other ", 1280, 498, 24, 'middle'),
            ("ClusterQueues in ", 1280, 526, 24, 'middle'),
            ("cohort gpu-fleet", 1280, 554, 24, 'middle'),
        ]),
        ("Setting 1", (70, 630, 450, 190), (267, 643, 56, 50), [
            ("reclaimWithinCohort Any: ", 295, 720, 24, 'middle'),
            ("take back lent quota ", 295, 750, 24, 'middle'),
            ("from borrowers", 295, 780, 24, 'middle'),
        ]),
        ("Setting 2", (560, 630, 450, 190), (757, 643, 56, 50), [
            ("borrowWithinCohort policy ", 785, 720, 24, 'middle'),
            ("LowerPriority with ", 785, 750, 24, 'middle'),
            ("maxPriorityThreshold 100", 785, 780, 24, 'middle'),
        ]),
        ("Setting 3", (1050, 630, 460, 190), (1252, 643, 56, 50), [
            ("withinClusterQueue ", 1280, 735, 24, 'middle'),
            ("LowerPriority", 1280, 767, 24, 'middle'),
        ]),
        ("Step 1", (70, 850, 450, 190), (271, 863, 48, 48), [
            ("Team A borrows ", 295, 955, 24, 'middle'),
            ("idle quota", 295, 987, 24, 'middle'),
        ]),
        ("Step 2", (560, 850, 450, 190), (761, 863, 48, 48), [
            ("Team B submits a job ", 785, 947, 24, 'middle'),
            ("and reclaims its own quota ", 785, 975, 24, 'middle'),
            ("through preemption", 785, 1003, 24, 'middle'),
        ]),
        ("Step 3", (1050, 850, 460, 190), (1256, 863, 48, 48), [
            ("watch Workload ", 1280, 955, 24, 'middle'),
            ("conditions", 1280, 987, 24, 'middle'),
        ]),
        ("Footer Bar", (40, 1070, 1520, 70), None, [
            ("WorkloadPriorityClass sets queueing priority independent of pod priority", 800, 1114, 24, 'middle'),
        ])
    ]

    for bname, (bx, by, bw, bh), icon_box, lines in boxes:
        for ltxt, lx, ly, fs, anchor in lines:
            w_line = len(ltxt) * fs * 0.60
            left = lx - w_line / 2.0 if anchor == 'middle' else (lx - w_line if anchor == 'end' else lx)
            right = left + w_line
            top = ly - fs * 0.75
            bot = ly + 4

            pl = left - bx
            pr = (bx + bw) - right
            pt = top - by
            pb = (by + bh) - bot

            assert pl >= 16, f"Padding left {pl:.1f} < 16 for '{ltxt}' in {bname}"
            assert pr >= 16, f"Padding right {pr:.1f} < 16 for '{ltxt}' in {bname}"
            assert pt >= 16, f"Padding top {pt:.1f} < 16 for '{ltxt}' in {bname}"
            assert pb >= 16, f"Padding bottom {pb:.1f} < 16 for '{ltxt}' in {bname}"

            if icon_box:
                ix, iy, iw, ih = icon_box
                ir = ix + iw
                ib = iy + ih
                overlap = not (right < ix or left > ir or bot < iy or top > ib)
                assert not overlap, f"Text '{ltxt}' overlaps icon in {bname}!"

    print("PASS: Box paddings >= 16px and zero overlap between text and icons.")
    print("ALL AUDIT CHECKS PASSED PERFECTLY!")

if __name__ == "__main__":
    run_audit("quota_final.svg")
