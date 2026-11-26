#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

def audit_svg(svg_path):
    print(f"=== Comprehensive Audit of {svg_path} ===")
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
    H_val = float(height)
    assert 900 <= H_val <= 1200
    assert viewBox == f"0 0 1600 {height}"

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
    for i, (txt, fs) in enumerate(text_elements, 1):
        print(f"   [{i:2d}] {fs:2.0f}px : '{txt}'")

    # 4. Expected labels
    expected_labels = [
        "Multipath: one LUN, several paths",
        "a SAN LUN",
        "Two HBAs and two switches giving four paths",
        "OS sees four block devices sdb, sdc, sdd, sde",
        "component paths",
        "one device built by multipathd",
        "then LVM and filesystem on top",
        "build filesystems and LVM on the multipath device, never on a component path",
        "exclude paths in the LVM filter",
        "blacklist local disks and virtio disks",
        "multipath -ll"
    ]

    found_texts = [t for t, fs in text_elements]
    print(f"\n4. Checking {len(expected_labels)} expected labels:")
    for lbl in expected_labels:
        norm_lbl = re.sub(r'\s+', ' ', lbl)
        cnt = found_texts.count(norm_lbl)
        assert cnt == 1, f"Expected label '{lbl}' count {cnt} != 1!"
        print(f"   [PASS] count=1: '{lbl}'")

    # 5. Extras check
    extras = [t for t in found_texts if t not in expected_labels]
    assert len(extras) == 0, f"Unexpected extra text: {extras}"
    assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"
    print(f"\n5. Zero extra text elements: PASS (found {len(found_texts)} == expected {len(expected_labels)})")

    # 6. Check forbidden words
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
    for t in found_texts:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for f in forbidden:
            assert f not in words, f"Forbidden word '{f}' in '{t}'!"
    print("\n6. No forbidden words found: PASS")

    # 7. Check orange count
    with open(svg_path, 'r', encoding='utf-8') as f:
        svg_str = f.read()
    orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
    print(f"\n7. Orange #db8129 occurrences: {len(orange_matches)}")
    # Should be in defs (marker) and used for the single arrow
    assert 1 <= len(orange_matches) <= 3, f"Unexpected orange count: {len(orange_matches)}"
    print("   Orange usage: PASS")

    # 8. Canvas Margins (>= 40px)
    print("\n8. Checking Canvas Margins (>= 40px):")
    for elem in root.iter('{http://www.w3.org/2000/svg}text'):
        fs = float(elem.attrib['font-size'])
        ff = elem.attrib.get('font-family', 'sans-serif')
        factor = 0.62 if 'mono' in ff else 0.60
        anchor = elem.attrib.get('text-anchor', 'start')
        
        tspans = elem.findall('{http://www.w3.org/2000/svg}tspan')
        if tspans:
            lines = []
            cur_y = float(elem.attrib.get('y', 0))
            for tsp in tspans:
                dy = float(tsp.attrib.get('dy', 0))
                cur_y += dy
                lines.append((tsp.text.strip(), float(tsp.attrib.get('x', elem.attrib.get('x', 0))), cur_y))
        else:
            lines = [(elem.text.strip(), float(elem.attrib.get('y', 0)))]
            lines = [(elem.text.strip(), float(elem.attrib.get('x', 0)), float(elem.attrib.get('y', 0)))]
            
        for line_txt, lx, ly in lines:
            w = len(line_txt) * fs * factor
            if anchor == 'middle':
                left = lx - w / 2.0
                right = lx + w / 2.0
            elif anchor == 'end':
                left = lx - w
                right = lx
            else:
                left = lx
                right = lx + w
            top = ly - fs * 0.75
            bot = ly + 4
            
            lm = left
            rm = 1600 - right
            tm = top
            bm = H_val - bot
            
            assert lm >= 39.9, f"Left margin violation: '{line_txt}' lm={lm:.1f} < 40"
            assert rm >= 39.9, f"Right margin violation: '{line_txt}' rm={rm:.1f} < 40"
            assert tm >= 39.9, f"Top margin violation: '{line_txt}' tm={tm:.1f} < 40"
            assert bm >= 39.9, f"Bottom margin violation: '{line_txt}' bm={bm:.1f} < 40"
            print(f"   [PASS] Margin: '{line_txt[:30]}' lm={lm:.1f}, rm={rm:.1f}, tm={tm:.1f}, bm={bm:.1f}")

    print("\nALL AUDIT CHECKS PASSED PERFECTLY!")

if __name__ == "__main__":
    audit_svg("multipath.svg")
