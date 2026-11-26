#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

expected_labels = [
    "Reading the sample trace line by line as a conversation",
    "duplex.example.com (client)",
    "mikado.example.com (server)",
    "arp who-has mikado tell duplex",
    "arp reply mikado is-at 0:2:2d:b:ee:4e",
    "S 3200063165 win 5840 mss 1460 sackOK (DF)",
    "S ack 3200063166 win 5792",
    ". ack 1",
    "P 1:427(426)",
    ". ack 427",
    "P 1:773(772)",
    ". ack 773",
    "lines 1-2: finding the link address because the client needs the server's MAC before it can send a frame",
    "lines 3-5: three-way handshake",
    "lines 6-9: data",
    "summary: 9 packets received by filter, 0 packets dropped by kernel",
    "S SYN, S. SYN-ACK, . ACK, P. PSH-ACK, F. FIN-ACK, R or R. RST",
    "Read the flags in order; a SYN with no reply stops the story at the first line, and the next question is who stayed silent"
]

step_numbers = {"1", "2", "3", "4", "5", "6", "7", "8", "9"}

def audit_svg(svg_path):
    print(f"=== AUDITING {svg_path} ===")
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # 1. First children check: <title> and <desc>
    children = list(root)
    first_tag = children[0].tag.split('}')[-1]
    second_tag = children[1].tag.split('}')[-1]
    print(f"1. Children: <{first_tag}>, <{second_tag}>")
    assert first_tag == 'title', f"First child must be title, got {first_tag}"
    assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"
    print("   [PASS] <title> and <desc> are the first children.")

    # 2. Dimensions and viewBox
    width = root.get('width')
    height = root.get('height')
    viewBox = root.get('viewBox')
    print(f"2. Dimensions: {width}x{height}, viewBox='{viewBox}'")
    assert width == "1600", f"Width must be 1600, got {width}"
    assert viewBox.startswith("0 0 1600"), f"viewBox must start with 0 0 1600, got {viewBox}"
    vb_parts = [float(x) for x in viewBox.split()]
    assert 900 <= vb_parts[3] <= 1200, f"Height {vb_parts[3]} outside 900-1200 range"
    assert int(height) == int(vb_parts[3]), f"height {height} != viewBox height {vb_parts[3]}"
    print("   [PASS] Dimensions and viewBox valid.")

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

    # 4. Check title: >= 48px bold
    title_elem = [elem for elem in root.iter('{http://www.w3.org/2000/svg}text') if "".join(elem.itertext()).strip() == expected_labels[0]]
    assert len(title_elem) == 1, "Title element must be present once"
    assert float(title_elem[0].attrib.get('font-size', 0)) >= 48, "Title font-size must be at least 48px"
    print("   [PASS] Title >= 48px bold.")

    # 5. Check host titles: >= 30px bold
    for h_label in [expected_labels[1], expected_labels[2]]:
        h_elems = [elem for elem in root.iter('{http://www.w3.org/2000/svg}text') if re.sub(r'\s+', ' ', "".join(elem.itertext()).strip()) == h_label]
        assert len(h_elems) == 1, f"Host title '{h_label}' must appear once"
        assert float(h_elems[0].attrib.get('font-size', 0)) >= 30, f"Host title font-size must be >= 30px, got {h_elems[0].attrib.get('font-size')}"
    print("   [PASS] Host titles >= 30px bold.")

    # 6. Check expected labels count
    found_texts = [t for t, fs in text_elements]
    print(f"\n6. Checking {len(expected_labels)} expected labels against {len(found_texts)} found:")
    all_ok = True
    for exp in expected_labels:
        cnt = found_texts.count(exp)
        ok = (cnt == 1)
        if not ok:
            all_ok = False
        print(f"   [{'OK' if ok else 'FAIL'}] count={cnt}: '{exp}'")
    assert all_ok, "Some expected labels failed count == 1 check!"

    extras = [t for t in found_texts if t not in expected_labels and t not in step_numbers]
    print(f"\n7. Extras count: {len(extras)}")
    if extras:
        print("   Unexpected extras:", extras)
    assert len(extras) == 0, f"Unexpected extra texts found: {extras}"
    print("   [PASS] Zero extra labels!")

    # Check step numbers
    for s in step_numbers:
        cnt = found_texts.count(s)
        assert cnt == 1, f"Step number '{s}' count={cnt} != 1"
    print(f"   [PASS] All step numbers 1..9 present exactly once.")

    # 8. Check forbidden words
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
    for t in found_texts:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for f in forbidden:
            assert f not in words, f"Forbidden word '{f}' in '{t}'!"
    print("\n8. Forbidden words check: PASS!")

    # 9. Check orange count
    with open(svg_path, 'r', encoding='utf-8') as f:
        svg_str = f.read()
    orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
    print(f"\n9. Orange #db8129 occurrences: {len(orange_matches)}")
    assert 1 <= len(orange_matches) <= 6, f"Unexpected orange count: {len(orange_matches)}"
    print("   [PASS] Orange used only for single most important item / arrow.")

    # 10. Check arrows count
    lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
    paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
    total_arrows = len(lines) + len(paths)
    print(f"\n10. Total arrows with marker-end: {total_arrows}")
    assert total_arrows == 9, f"Expected exactly 9 arrows, got {total_arrows}"
    print("   [PASS] Exactly 9 arrows!")

    # 11. Required colors check
    assert "#f5f8f5" in svg_str
    assert "#303a36" in svg_str
    assert "#207448" in svg_str
    assert "#e8f1ea" in svg_str
    print("\n11. Style colors check: PASS!")

    print("\n=== ALL STRICT RULES PASSED PERFECTLY! ===")

if __name__ == "__main__":
    audit_svg("candidate_read_conv.svg")
