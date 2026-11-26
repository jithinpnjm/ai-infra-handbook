#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

expected_labels = [
    "Ordering GPUs against a three-month lead time",
    "Worked chain with assumed inputs",
    "Fleet 400 GPUs, 320 in use, demand growing 8 percent a month, GPU lead time 3 months, headroom policy 20 percent",
    "Demand after the lead time: 320 x 1.08 cubed = 403.1",
    "GPUs needed with headroom: 403.1 x 1.2, rounded up = 484",
    "Order today: 484 - 400 = 84",
    "plan against lead time, not today's load: today's load tells you what is busy now, lead time tells you what you must order now",
    "vendor delays 200 GPUs: redo the same chain"
]

forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']

def test_labels(svg_content):
    root = ET.fromstring(svg_content)
    text_elems = []
    for elem in root.iter('{http://www.w3.org/2000/svg}text'):
        full_text = "".join(elem.itertext()).strip()
        full_text = re.sub(r'\s+', ' ', full_text)
        fs = elem.attrib.get('font-size')
        assert fs is not None, f"Missing font-size on: {full_text}"
        size = float(fs)
        assert size >= 24, f"Font size {size} < 24 on: {full_text}"
        for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
            tfs = tsp.attrib.get('font-size')
            if tfs is not None:
                assert float(tfs) >= 24, f"tspan font-size {tfs} < 24 in '{full_text}'"
        text_elems.append((full_text, size))

    found_texts = [t for t, fs in text_elems]
    print(f"Total text elements found: {len(found_texts)}")
    for i, (t, s) in enumerate(text_elems, 1):
        print(f" {i}. [{s}px] '{t}'")

    for exp in expected_labels:
        cnt = found_texts.count(exp)
        assert cnt == 1, f"Expected label count {cnt} != 1 for '{exp}'"

    extras = [t for t in found_texts if t not in expected_labels]
    assert len(extras) == 0, f"Extras found: {extras}"
    assert len(found_texts) == len(expected_labels), f"Text count mismatch: {len(found_texts)} vs {len(expected_labels)}"

    for t in found_texts:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for f in forbidden:
            assert f not in words, f"Forbidden word '{f}' in '{t}'"

    orange_matches = re.findall(r'#db8129', svg_content, re.IGNORECASE)
    print(f"Orange count: {len(orange_matches)}")
    assert 1 <= len(orange_matches) <= 4, f"Unexpected orange count: {len(orange_matches)}"

    lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
    paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
    total_arrows = len(lines) + len(paths)
    print(f"Total arrows: {total_arrows}")

    print("ALL BASIC AUDIT CHECKS PASS!")

if __name__ == "__main__":
    print("Audit test helper ready.")
