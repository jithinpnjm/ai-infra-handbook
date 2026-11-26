#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re
import sys
import pathlib

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
        "Reading a wheel filename and deciding between wheel and sdist",
        "name-version-pythontag-abitag-platformtag",
        "numpy-1.26.4-cp311-cp311-manylinux_2_17_x86_64.whl",
        "numpy: name",
        "1.26.4: version",
        "cp311: Python tag (CPython 3.11)",
        "cp311: ABI tag",
        "manylinux_2_17_x86_64: platform tag (x86_64 Linux, glibc-compatible)",
        "py3-none-any: pure Python, installs anywhere",
        "manylinux: runs on most Linux distributions with a compatible glibc",
        "musllinux: Alpine, which uses musl instead",
        "abi3: the stable ABI",
        "+cu121: local version label (PEP 440) marking a CUDA build, used by PyTorch index wheels",
        "aarch64: Grace and other ARM hosts, some packages have no wheels",
        "pip finds a compatible wheel?",
        "unzip, no build step, fast",
        "yes",
        "builds from the sdist: needs compilers and headers; the usual reason an install takes 10 minutes or fails in a slim container",
        "no",
        "python -m build makes dist/myops-0.3.1.tar.gz (sdist) and dist/myops-0.3.1-py3-none-any.whl (wheel)",
        "python -m pip debug --verbose lists the supported tags",
        "pip download --only-binary=:all: --platform manylinux2014_aarch64 ...",
        "Check the tags of every wheel you plan to ship against the machines that will install it"
    ]

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

    extras = [t for t in found_texts if t not in expected_labels]
    print(f"\n5. Extras count: {len(extras)}")
    if extras:
        print("   Unexpected extras:", extras)
    assert len(extras) == 0, f"Unexpected extra texts found: {extras}"
    assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"

    # 5. Check forbidden words
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
    for t in found_texts:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for w in words:
            assert w not in forbidden, f"Forbidden word '{w}' found in text: '{t}'"

    print("\n6. Forbidden words check: PASS!")

    # 6. Check orange count
    svg_str = pathlib.Path(svg_path).read_text(encoding='utf-8')
    orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
    print(f"\n7. Orange #db8129 occurrences: {len(orange_matches)}")
    assert 1 <= len(orange_matches) <= 6, f"Unexpected orange count: {len(orange_matches)}"

    # 7. Check arrows count
    lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
    paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
    total_arrows = len(lines) + len(paths)
    print(f"\n8. Total arrows with marker-end: {total_arrows}")
    assert total_arrows == 2, f"Expected exactly 2 arrows, got {total_arrows}"

    # 8. Check colors present
    assert "#f5f8f5" in svg_str
    assert "#303a36" in svg_str
    assert "#207448" in svg_str
    assert "#e8f1ea" in svg_str
    assert "#db8129" in svg_str
    print("\n9. All required colors present! (PASS)")

    # 9. Check text paddings inside boxes
    print("\n10. Checking text paddings inside boxes...")
    boxes = {
        "section-anatomy": (40, 110, 1520, 180),
        "piece-1": (60, 192, 190, 88),
        "piece-2": (265, 192, 190, 88),
        "piece-3": (470, 192, 310, 88),
        "piece-4": (795, 192, 190, 88),
        "piece-5": (1000, 192, 540, 88),
        "var-1": (125, 338, 700, 84),
        "var-2": (845, 338, 700, 84),
        "var-3": (125, 428, 700, 84),
        "var-4": (845, 428, 700, 84),
        "var-5": (125, 518, 700, 84),
        "var-6": (845, 518, 700, 84),
        "box-decision": (40, 635, 450, 185),
        "box-yes": (620, 635, 940, 70),
        "box-no": (620, 716, 940, 114),
        "tool-1": (56, 878, 1488, 84),
        "tool-2": (56, 968, 734, 80),
        "tool-3": (810, 968, 734, 80),
        "bottom-bar": (40, 1095, 1520, 65),
    }

    for gid, (bx, by, bw, bh) in boxes.items():
        g = root.find(f".//*[@id='{gid}']")
        assert g is not None, f"Group {gid} not found"
        for text in g.findall('{http://www.w3.org/2000/svg}text'):
            base_fs = float(text.attrib.get('font-size', 24))
            base_ff = text.attrib.get('font-family', 'sans-serif')
            tspans = text.findall('{http://www.w3.org/2000/svg}tspan')
            if not tspans:
                tspans = [text]
            for i, tsp in enumerate(tspans):
                t = (tsp.text or "").strip()
                if not t: continue
                fs = float(tsp.attrib.get('font-size', base_fs))
                ff = tsp.attrib.get('font-family', base_ff)
                char_w = 0.62 if 'mono' in ff else 0.60
                w = len(t) * char_w * fs
                anchor = tsp.attrib.get('text-anchor', text.attrib.get('text-anchor', 'start'))
                tx = float(tsp.attrib.get('x', text.attrib.get('x', 0)))
                ty = float(tsp.attrib.get('y', text.attrib.get('y', 0)))
                if anchor == 'middle':
                    x_start = tx - w / 2
                    x_end = tx + w / 2
                elif anchor == 'end':
                    x_start = tx - w
                    x_end = tx
                else:
                    x_start = tx
                    x_end = tx + w

                # Check horizontal padding >= 16px
                assert x_start >= bx + 16, f"Text '{t}' left padding {x_start - bx:.1f} < 16 in {gid}"
                assert x_end <= bx + bw - 16, f"Text '{t}' right padding {bx + bw - x_end:.1f} < 16 in {gid}"

                # Check vertical padding >= 16px
                top_y = ty - fs
                bot_y = ty + 0.25 * fs
                if i == 0:
                    assert top_y >= by + 16, f"Text '{t}' top padding {top_y - by:.1f} < 16 in {gid} (top_y={top_y}, by={by})"
                if i == len(tspans) - 1:
                    assert bot_y <= by + bh - 16, f"Text '{t}' bot padding {by + bh - bot_y:.1f} < 16 in {gid} (bot_y={bot_y}, by+bh={by+bh})"

    print("10. All text elements have >= 16px padding on all sides! (PASS)")

    print("\nALL AUDIT CHECKS PASSED PERFECTLY!")

if __name__ == "__main__":
    audit_svg(sys.argv[1] if len(sys.argv) > 1 else "wheel_decision.svg")
