#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

def audit_diagram(path):
    print(f"=== Auditing {path} ===")
    tree = ET.parse(path)
    root = tree.getroot()
    
    # 1. First children check: <title> and <desc>
    children = list(root)
    t1 = children[0].tag.split('}')[-1]
    t2 = children[1].tag.split('}')[-1]
    print(f"1. Children: 0=<{t1}>, 1=<{t2}>")
    assert t1 == 'title', f"Child 0 must be title, got {t1}"
    assert t2 == 'desc', f"Child 1 must be desc, got {t2}"
    print("   [PASS] <title> and <desc> are first children.")
    
    # 2. Dimensions
    w = root.get('width')
    h = root.get('height')
    vb = root.get('viewBox')
    print(f"2. Dimensions: width={w}, height={h}, viewBox='{vb}'")
    assert w == "1600", f"width must be 1600, got {w}"
    assert h == "1200", f"height must be 1200, got {h}"
    assert vb == "0 0 1600 1200", f"viewBox must be '0 0 1600 1200', got {vb}"
    print("   [PASS] Dimensions match 1600x1200.")
    
    # 3. Check font sizes
    text_nodes = []
    for el in root.iter('{http://www.w3.org/2000/svg}text'):
        fs = float(el.attrib.get('font-size', 0))
        assert fs >= 24, f"Text has font-size {fs} < 24!"
        for tsp in el.iter('{http://www.w3.org/2000/svg}tspan'):
            tfs = tsp.attrib.get('font-size')
            if tfs is not None:
                assert float(tfs) >= 24, f"tspan has font-size {tfs} < 24!"
        
        full_text = "".join(el.itertext()).strip()
        full_text = re.sub(r'\s+', ' ', full_text)
        text_nodes.append((full_text, fs))
        
    print(f"3. All {len(text_nodes)} text elements have font-size >= 24px. [PASS]")
    
    # 4. Check expected labels
    expected_labels = [
        "IPv4 and IPv6 headers side by side: what moved, what went away",
        "IPv4 header, 20 bytes minimum",
        "IPv6 header, 40 bytes fixed",
        "Version 4",
        "IHL: header length in 32-bit words, 5 means 20 bytes",
        "DSCP (6 bits) and ECN (2 bits)",
        "Total Length up to 65,535",
        "Identification, Flags (DF, MF), Fragment Offset: fragmentation lives in the base header; routers may fragment unless DF is set",
        "TTL: drops by one per router, at 0 the router drops the packet and sends ICMP Time Exceeded",
        "Protocol: 6 TCP, 17 UDP, 1 ICMP, 47 GRE, 50 ESP, 89 OSPF",
        "Header checksum: recomputed at every hop because the TTL changes",
        "source and destination 32-bit addresses",
        "options (rare)",
        "Version 4 bits",
        "Traffic Class 8 bits = DSCP 6 + ECN 2",
        "Flow Label 20 bits: helps routers keep a flow on one path when ECMP spreads traffic",
        "Payload Length 16",
        "Next Header 8: extension headers chained (hop-by-hop, routing, fragment, destination options, AH, ESP)",
        "Hop Limit 8: plays the role of the TTL",
        "source and destination 128-bit addresses",
        "no header checksum (link and transport layers cover errors)",
        "no fragmentation fields in the base header: only the source host may fragment, through an extension header; routers never do",
        "TTL to Hop Limit",
        "Protocol to Next Header",
        "DSCP+ECN to Traffic Class",
        "A fixed header keeps hardware parsing simple, and extension headers keep the design flexible"
    ]
    
    found_texts = [t for t, fs in text_nodes]
    print(f"4. Checking {len(expected_labels)} expected labels:")
    missing = []
    duplicates = []
    for exp in expected_labels:
        c = found_texts.count(exp)
        if c == 0:
            missing.append(exp)
            print(f"   [MISSING] '{exp}'")
        elif c > 1:
            duplicates.append(exp)
            print(f"   [DUPLICATE ({c}x)] '{exp}'")
        else:
            print(f"   [OK] '{exp}'")
            
    assert len(missing) == 0, f"Missing {len(missing)} labels: {missing}"
    assert len(duplicates) == 0, f"Duplicate labels: {duplicates}"
    
    # Check if there are any extra text elements
    extras = [t for t in found_texts if t not in expected_labels]
    print(f"   Extra text elements: {len(extras)}")
    assert len(extras) == 0, f"Extra text elements found: {extras}"
    print("   [PASS] Every label present exactly once, no extra labels!")
    
    # 5. Check padding using audit_pad_strict logic
    from audit_pad_strict import check_strict_paddings
    check_strict_paddings(path)
    print("   [PASS] Strict paddings passed!")

audit_diagram("test_candidate_v4_v6.svg")
