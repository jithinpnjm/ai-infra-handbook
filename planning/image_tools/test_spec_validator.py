#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

def audit_svg_content(svg_str):
    # Strip comments
    clean_svg = re.sub(r'<!--.*?-->', '', svg_str, flags=re.S)
    root = ET.fromstring(clean_svg)
    
    # 1. First children check: <title> and <desc>
    tag1 = root[0].tag.split('}')[-1]
    tag2 = root[1].tag.split('}')[-1]
    print(f"First children: <{tag1}>, <{tag2}>")
    assert tag1 == "title", "First child must be <title>"
    assert tag2 == "desc", "Second child must be <desc>"
    
    # 2. Dimensions check
    w = root.attrib.get('width')
    vb = root.attrib.get('viewBox')
    print(f"Width: {w}, viewBox: {vb}")
    assert w == "1600", f"Width must be 1600, got {w}"
    assert vb.startswith("0 0 1600"), f"viewBox must start with '0 0 1600', got {vb}"
    h_val = int(vb.split()[-1])
    assert 900 <= h_val <= 1200, f"Height must be between 900 and 1200, got {h_val}"
    
    # 3. Extract text elements and check font-sizes
    full_texts = []
    font_sizes = []
    for el in root.iter('{http://www.w3.org/2000/svg}text'):
        fs = float(el.attrib.get('font-size', '0'))
        combined = " ".join("".join(el.itertext()).split())
        full_texts.append(combined)
        font_sizes.append((combined, fs))
        # check child tspans
        for ts in el.findall('{http://www.w3.org/2000/svg}tspan'):
            t_fs = float(ts.attrib.get('font-size', fs))
            t_content = " ".join("".join(ts.itertext()).split())
            if t_content:
                font_sizes.append((t_content, t_fs))
    
    print(f"\nTotal <text> elements: {len(full_texts)}")
    for t, fs in font_sizes:
        assert fs >= 24, f"Text '{t}' has font-size {fs} < 24 px!"
    print("[PASS] All text elements >= 24 px.")
    
    # 4. Check banned styling words
    banned_words = ["orange", "green", "grey", "gray", "bold", "monospace", "arrow"]
    for ft in full_texts:
        words = re.findall(r'\b[A-Za-z]+\b', ft.lower())
        for bw in banned_words:
            assert bw not in words, f"Banned styling word '{bw}' found in text: '{ft}'"
    print("[PASS] No banned styling words in text.")
    
    # 5. Check exact spec labels
    spec_labels = [
        "Topology-aware routing keeps requests in the zone",
        "default",
        "a client in zone A may land on endpoints in any zone, crossing zone boundaries (extra latency and cost)",
        "trafficDistribution PreferClose (earlier: annotation service.kubernetes.io/topology-mode Auto)",
        "EndpointSlice hints with forZones keep the request inside zone A while it has endpoints",
        "zone A",
        "zone B",
        "zone C",
        "client",
        "endpoints",
        "if a zone has no endpoints or endpoints are unbalanced, traffic falls back to cluster-wide routing",
        "zone labels on nodes and enough endpoints in each zone",
        "parcel goes to the depot in the same town until it is empty",
        "check each zone has endpoints before turning it on, then watch where requests land"
    ]
    
    print("\n--- Checking spec labels count in SVG ---")
    for sl in spec_labels:
        cnt = full_texts.count(sl)
        print(f"'{sl[:40]}...': count={cnt}")
        assert cnt == 1, f"Expected '{sl}' to appear exactly once, got {cnt}"
    
    print("[PASS] All spec labels present exactly once.")
    
    # Check no extra text elements
    assert len(full_texts) == len(spec_labels), f"Expected {len(spec_labels)} text elements, got {len(full_texts)}: {set(full_texts) - set(spec_labels)}"
    print("[PASS] Exactly 14 text elements, none duplicated, none invented!")
    
    return True

if __name__ == "__main__":
    print("Validator ready.")
