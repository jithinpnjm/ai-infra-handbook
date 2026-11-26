import xml.etree.ElementTree as ET
import re

def validate(svg_path):
    tree = ET.parse(svg_path)
    root = tree.getroot()
    ns = {'svg': 'http://www.w3.org/2000/svg'}

    # 1. Root checks
    assert root.tag.endswith('svg')
    assert root.attrib.get('width') == '1600'
    vb = [float(x) for x in root.attrib.get('viewBox').split()]
    assert vb[0] == 0 and vb[1] == 0 and vb[2] == 1600 and 900 <= vb[3] <= 1200
    H = vb[3]

    # 2. First children <title> and <desc>
    assert root[0].tag.endswith('title')
    assert root[1].tag.endswith('desc')
    title_text = root[0].text.strip()
    assert title_text == "A failed prediction is information: the node 17 example"

    # 3. Text font-size >= 24
    for text_el in root.iter('{http://www.w3.org/2000/svg}text'):
        fs = float(text_el.attrib.get('font-size', '0'))
        tspans = list(text_el.iter('{http://www.w3.org/2000/svg}tspan'))
        if fs == 0 and tspans:
            fs = float(tspans[0].attrib.get('font-size', '0'))
        full = " ".join("".join(text_el.itertext()).split())
        assert fs >= 24, f"Text '{full}' has font-size {fs} < 24"
        for ts in tspans:
            tfs = ts.attrib.get('font-size')
            if tfs is not None:
                assert float(tfs) >= 24, f"tspan in '{full}' has font-size {tfs} < 24"

    # 4. Check labels
    expected_labels = [
        "A failed prediction is information: the node 17 example",
        "Question: why are training steps on node 17 slow, and only that node?",
        "Hypothesis: its data loader is starved by a slow local NVMe",
        "Prediction: iostat will show high await on that device, and GPU sm activity will drop in lockstep",
        "Test: look",
        "Result",
        "Prediction fails: await is normal and the data loader queue is full, so the GPU is waiting in NCCL; the NVMe is not the cause",
        "new hypothesis, such as a slow NIC link",
        "Experimental example: does disabling NUMA balancing raise throughput?",
        "prediction: smaller run-to-run variance and fewer page faults",
        "A/B comparison on identical nodes, same data, pinned clocks, confidence intervals",
        "if no effect, revert it and write down that you tried",
        "Elimination is also an answer: a resource with low utilisation, no saturation and no errors removes that resource from the search; document negative findings so other teams do not re-check the same dead end",
        "A failed prediction is information, not a wasted trip"
    ]

    found_texts = []
    for el in root.iter('{http://www.w3.org/2000/svg}text'):
        combined = " ".join("".join(el.itertext()).split())
        found_texts.append(combined)

    for exp in expected_labels:
        cnt = found_texts.count(exp)
        assert cnt == 1, f"Expected '{exp}' exactly once, got {cnt}"

    # Check that extra texts are only short step numbers
    for ft in found_texts:
        if ft not in expected_labels:
            assert ft in ['1', '2', '3', '4', '5'], f"Unexpected text: '{ft}'"

    # 5. Check no banned styling words
    banned = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow']
    for ft in found_texts:
        words = re.findall(r'\b[A-Za-z]+\b', ft.lower())
        for b in banned:
            assert b not in words, f"Banned styling word '{b}' found in text: '{ft}'"

    # 6. Check arrows
    arrows = [el for el in root.iter() if 'marker-end' in el.attrib]
    assert len(arrows) == 5, f"Expected 5 arrows, got {len(arrows)}"

    print("All validations PASSED!")

if __name__ == '__main__':
    validate('test_node17_infographic.svg')
