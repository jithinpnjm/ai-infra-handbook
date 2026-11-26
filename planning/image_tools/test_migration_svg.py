import re
import xml.etree.ElementTree as ET

def check_svg(svg_str):
    root = ET.fromstring(svg_str)
    
    # 1. Structure
    children = list(root)
    t1 = children[0].tag.split('}')[-1]
    t2 = children[1].tag.split('}')[-1]
    assert t1 == 'title', f"First child is {t1}, not title"
    assert t2 == 'desc', f"Second child is {t2}, not desc"
    print("1. <title> and <desc> first: PASS")

    # 2. Dimensions
    w = root.get('width')
    h = root.get('height')
    vb = root.get('viewBox').split()
    assert w == '1600', f"Width is {w}"
    assert vb[0] == '0' and vb[1] == '0' and vb[2] == '1600'
    assert 900 <= float(vb[3]) <= 1200, f"Height {vb[3]} out of bounds"
    assert float(h) == float(vb[3])
    print(f"2. Dimensions {w}x{h}, viewBox {root.get('viewBox')}: PASS")

    # 3. Expected labels
    expected = [
        'Expand and contract migration during a rolling update',
        'old code',
        'new code',
        'both reading one database',
        'Phase 1 expand: add the new piece in a way old code ignores',
        'Phase 2 move the code over with serial rolling, old and new run side by side',
        'Phase 3 contract: later remove the old piece',
        'a migration that removes a column old code still uses breaks old code mid-rollout',
        'alembic upgrade head runs once with run_once on the first host'
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
    assert len(found) == len(expected), f"Count mismatch: {len(found)} != {len(expected)}"
    print("   No extra text: PASS")

    # 4. Forbidden words
    banned = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
    for t in found:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for f in banned:
            assert f not in words, f"Forbidden word '{f}' in '{t}'"
    print("4. Forbidden words check: PASS")

    # 5. Orange check
    orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
    print(f"5. Orange count: {len(orange_matches)}")
    assert 1 <= len(orange_matches) <= 8, f"Orange count {len(orange_matches)} out of bounds"
    print("   Orange check: PASS")

    # 6. Colors present
    for c in ["#f5f8f5", "#303a36", "#207448", "#e8f1ea", "#db8129"]:
        assert c in svg_str, f"Missing color {c}"
    print("6. Colors present: PASS")

print("Audit helper ready")
