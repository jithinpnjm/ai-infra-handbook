#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

def audit_svg(svg_path):
    print(f"Auditing {svg_path}...")
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # 1. Structure check: First children must be title and desc
    children = list(root)
    first_tag = children[0].tag.split('}')[-1]
    second_tag = children[1].tag.split('}')[-1]
    print(f"1. Structure: Child 0: <{first_tag}>, Child 1: <{second_tag}>")
    assert first_tag == 'title', f"First child must be title, got {first_tag}"
    assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"
    print("   [PASS] <title> and <desc> are the first children.")

    # 2. Dimensions check
    width = root.get('width')
    viewBox = root.get('viewBox')
    height = root.get('height')
    print(f"2. Dimensions: width={width}, height={height}, viewBox={viewBox}")
    assert width == "1600"
    assert viewBox.startswith("0 0 1600 ")
    vb_parts = [float(x) for x in viewBox.split()]
    assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
    assert 900 <= vb_parts[3] <= 1200
    assert int(height) == int(vb_parts[3])
    print("   [PASS] Canvas dimensions valid.")

    # 3. Check font-size >= 24 on all text and tspans
    text_elements = []
    for elem in root.iter('{http://www.w3.org/2000/svg}text'):
        full_text = "".join(elem.itertext()).strip()
        full_text = re.sub(r'\s+', ' ', full_text)
        fs = elem.attrib.get('font-size')
        assert fs is not None, f"Missing font-size on text '{full_text}'"
        fs_val = float(fs.replace('px', ''))
        assert fs_val >= 24, f"Text '{full_text}' font-size {fs_val} < 24!"
        for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
            tfs = tsp.attrib.get('font-size')
            if tfs is not None:
                tfs_val = float(tfs.replace('px', ''))
                assert tfs_val >= 24, f"tspan font-size {tfs_val} < 24 in '{full_text}'"
        text_elements.append((full_text, fs_val))

    print(f"\n3. Total text elements: {len(text_elements)} (all font-sizes >= 24px)")
    for i, (t, fs) in enumerate(text_elements, 1):
        print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

    # 4. Expected labels
    expected_labels = [
        "Hedging buys tail latency with GPU time",
        "request is slow because one replica is slow; after a short delay (only on a per-try timeout) send a second copy to another replica without cancelling the first; use whichever answers first; cancel the loser at once",
        "hedge at the 95th percentile: duplicates 5 percent of requests, p99 from 4.02 to 3.57, about 11 percent better",
        "hedge at the 90th: duplicates 10 percent, p99 from 4.01 to 3.30, about 18 percent better",
        "gain per duplicate is modest and shrinks as the delay grows",
        "a hedge repeats the whole prefill on a second GPU and holds KV cache until the loser is cancelled; 5 percent duplicates is roughly 5 percent more prefill work; a fleet at 80 percent utilisation moves to about 84 percent and queueing delay rises steeply near the top; independence fails exactly when you need hedging most",
        "hedge only before the first token, only for tail time to first token, only below a fleet utilisation threshold, only inside the retry budget"
    ]

    found_texts = [t for t, fs in text_elements]
    print(f"\n4. Checking {len(expected_labels)} expected labels against {len(found_texts)} found:")
    all_ok = True
    for exp in expected_labels:
        cnt = found_texts.count(exp)
        ok = (cnt == 1)
        if not ok:
            all_ok = False
        print(f"   [{'OK' if ok else 'FAIL'}] count={cnt}: '{exp[:45]}...'")

    assert all_ok, "Some expected labels failed count == 1 check!"

    extras = [t for t in found_texts if t not in expected_labels]
    print(f"\nExtra texts: {extras}")
    assert len(extras) == 0, f"Found unexpected extra text: {extras}"
    assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"
    print("   [PASS] Exactly the expected labels, each occurring once!")

    # 5. Check forbidden words
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
    for t in found_texts:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for f in forbidden:
            assert f not in words, f"Forbidden word '{f}' in '{t}'!"
    print("   [PASS] No forbidden words found.")

    # 6. Check orange count
    with open(svg_path, 'r', encoding='utf-8') as f:
        svg_str = f.read()
    orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
    print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
    assert 1 <= len(orange_matches) <= 4, f"Unexpected orange count: {len(orange_matches)}"
    print("   [PASS] Orange used sparingly (1-4 occurrences).")

    # 7. Check required colors
    assert "#f5f8f5" in svg_str
    assert "#303a36" in svg_str
    assert "#207448" in svg_str
    assert "#e8f1ea" in svg_str
    assert "#db8129" in svg_str
    print("   [PASS] All required palette colors present.")

    # 8. Paddings & Bounds check
    print("\n8. Checking text paddings and bounds...")
    boxes = {
        "left-column": (40, 100, 480, 750),
        "middle-column": (560, 100, 480, 750),
        "right-column": (1080, 100, 480, 750),
        "rule-box": (40, 890, 1520, 150)
    }

    for gid, (bx, by, bw, bh) in boxes.items():
        g = root.find(f".//*[@id='{gid}']")
        assert g is not None, f"Group {gid} not found"
        for text in g.findall('{http://www.w3.org/2000/svg}text'):
            base_fs = float(text.attrib.get('font-size', '24').replace('px',''))
            base_x = float(text.attrib.get('x', '0'))
            base_y = float(text.attrib.get('y', '0'))
            tspans = text.findall('{http://www.w3.org/2000/svg}tspan')
            if not tspans:
                tspans = [text]
            cur_y = base_y
            for tsp in tspans:
                t = (tsp.text or "").strip()
                if not t: continue
                fs = float(tsp.attrib.get('font-size', str(base_fs)).replace('px',''))
                tx = float(tsp.attrib.get('x', str(base_x)))
                dy = float(tsp.attrib.get('dy', '0'))
                cur_y += dy
                anchor = tsp.attrib.get('text-anchor', text.attrib.get('text-anchor', 'start'))
                w = len(t) * 0.60 * fs

                if anchor == 'middle':
                    x_left = tx - w / 2.0
                    x_right = tx + w / 2.0
                elif anchor == 'end':
                    x_left = tx - w
                    x_right = tx
                else:
                    x_left = tx
                    x_right = tx + w

                # Check horizontal bounds
                pad_left = x_left - bx
                pad_right = (bx + bw) - x_right
                assert pad_left >= 16, f"Left padding violation in {gid}: {pad_left:.1f}px < 16px on '{t}'"
                assert pad_right >= 16, f"Right padding violation in {gid}: {pad_right:.1f}px < 16px on '{t}'"

                # Check vertical bounds
                pad_top = (cur_y - fs) - by
                pad_bottom = (by + bh) - cur_y
                assert pad_top >= 16, f"Top padding violation in {gid}: {pad_top:.1f}px < 16px on '{t}'"
                assert pad_bottom >= 16, f"Bottom padding violation in {gid}: {pad_bottom:.1f}px < 16px on '{t}'"

    print("   [PASS] All text lines strictly satisfy >= 16px padding on all sides!")
    print("\nALL AUDIT CHECKS PASSED PERFECTLY!")

if __name__ == "__main__":
    audit_svg("test_candidate.svg")
