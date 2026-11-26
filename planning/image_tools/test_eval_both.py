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
        "From a pod name to the node's directory and ID",
        "kubectl: pod trainer-0 in namespace training",
        "Node stores logs by namespace, name and pod UID",
        "/var/log/pods/<namespace>_<name>_<UID>",
        "Runtime knows the container by an ID",
        "crictl ps -a",
        "Inspect the sandbox and container",
        "crictl inspectp <pod-id>",
        "crictl inspect <ctr-id>",
        "Logs",
        "crictl logs --tail 100 <ctr-id>",
        "journalctl -u kubelet -u containerd --since -30 min",
        "Walk the chain once, and it becomes easy to repeat."
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
    print(f"3. Found {len(found)} text elements (all >= 24px).")

    for exp in expected:
        cnt = found.count(exp)
        assert cnt == 1, f"Expected '{exp}' count={cnt}"
    print("   All 13 expected labels found exactly once: PASS")

    extras = [t for t in found if t not in expected]
    assert len(extras) == 0, f"Found extra texts: {extras}"
    print("   No extra text: PASS")

    # 4. Forbidden words
    banned = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow']
    for t in found:
        words = [w.strip("(),:;.'\"").lower() for w in t.split()]
        for b in banned:
            assert b not in words, f"Banned word '{b}' in '{t}'"
    print("4. No banned style words: PASS")

    # 5. Orange highlight
    oranges = re.findall(r'#db8129', raw, re.I)
    print(f"5. Orange #db8129 count: {len(oranges)}")
    assert 1 <= len(oranges) <= 3

    # 6. Arrows count
    markers = [e for e in root.iter() if 'marker-end' in e.attrib]
    print(f"6. Markers count: {len(markers)}")
    assert len(markers) in [3, 4], f"Unexpected markers count: {len(markers)}"

    print("ALL EVALUATION CHECKS PASSED!")

