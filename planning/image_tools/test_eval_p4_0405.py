import re
import xml.etree.ElementTree as ET

def evaluate(svg_path):
    print(f"\n================ EVALUATING {svg_path} ================")
    tree = ET.parse(svg_path)
    root = tree.getroot()
    raw = open(svg_path).read()

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
    assert w == '1600'
    assert vb[0] == '0' and vb[1] == '0' and vb[2] == '1600'
    assert 900 <= float(vb[3]) <= 1200
    assert float(h) == float(vb[3])
    print(f"2. Dimensions {w}x{h}, viewBox {root.get('viewBox')}: PASS")

    # 3. Expected labels
    expected = [
        'Which driver branch wins: a worked run through the stack',
        'transparent sheets: where the top sheet has writing you read it, where it is blank the sheet below shows through',
        'a host_vars file for one node sets nothing',
        'gpu_h100 group sets 550',
        'role default sets an older driver branch',
        'that node gets 550, because the group layer sits above the role default',
        'extra vars on the command line: -e nvidia_driver_branch with a newer value',
        'every host gets that newer value, because extra vars sit at the top of the stack',
        'when a variable has the wrong value, check each layer in order before editing anything: work from the bottom upward, find the lowest layer holding the value you expected, then look at each layer above it until you find the one that replaced it; that is the layer to change, editing any other layer changes nothing',
        'Find the layer that replaced it'
    ]

    text_elems = []
    for el in root.iter('{http://www.w3.org/2000/svg}text'):
        txt = re.sub(r'\s+', ' ', "".join(el.itertext()).strip())
        fs = float(el.attrib.get('font-size', 0))
        assert fs >= 24, f"Text '{txt}' font-size {fs} < 24"
        for tsp in el.iter('{http://www.w3.org/2000/svg}tspan'):
            tfs = tsp.attrib.get('font-size')
            if tfs:
                assert float(tfs) >= 24, f"tspan font-size {tfs} < 24 in '{txt}'"
        text_elems.append((txt, fs))

    found = [t for t, fs in text_elems]
    print(f"3. Found {len(found)} text elements (all >= 24px):")
    for i, (t, fs) in enumerate(text_elems, 1):
        print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

    for exp in expected:
        cnt = found.count(exp)
        assert cnt == 1, f"Expected '{exp}' count={cnt}"
    print(f"   All {len(expected)} expected labels found exactly once: PASS")

    extras = [t for t in found if t not in expected]
    assert len(extras) == 0, f"Found extra texts: {extras}"
    print("   No extra text: PASS")

    # 4. Forbidden words
    banned = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow']
    for t in found:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for word in banned:
            assert word not in words, f"Forbidden word '{word}' found in '{t}'!"
    print("4. Forbidden words check: PASS")

    # 5. Orange check
    orange_matches = re.findall(r'#db8129', raw, re.IGNORECASE)
    print(f"5. Orange #db8129 count: {len(orange_matches)}")
    assert 1 <= len(orange_matches) <= 3, f"Unexpected orange count: {len(orange_matches)}"

    # 6. Arrows count
    lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
    paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
    total_arrows = len(lines) + len(paths)
    print(f"6. Total arrows with marker-end: {total_arrows}")
    assert total_arrows == 0, f"Expected 0 arrows, got {total_arrows}"

    print("\nALL EVALUATION CHECKS PASSED PERFECTLY!")

evaluate("test_candidate.svg")
