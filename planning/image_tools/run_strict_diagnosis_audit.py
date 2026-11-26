import xml.etree.ElementTree as ET
import re
import sys

def audit(svg_path):
    print(f"=== Auditing {svg_path} ===")
    tree = ET.parse(svg_path)
    root = tree.getroot()
    
    # 1. First children
    children = list(root)
    first_tag = children[0].tag.split('}')[-1]
    second_tag = children[1].tag.split('}')[-1]
    print(f"1. Children: <{first_tag}>, <{second_tag}>")
    assert first_tag == "title", f"Expected title, got {first_tag}"
    assert second_tag == "desc", f"Expected desc, got {second_tag}"
    
    # 2. Dimensions
    w = float(root.attrib["width"])
    h = float(root.attrib["height"])
    vb = [float(x) for x in root.attrib["viewBox"].split()]
    print(f"2. Dimensions: W={w}, H={h}, viewBox={vb}")
    assert w == 1600, f"Expected width 1600, got {w}"
    assert 900 <= h <= 1200, f"Expected height in [900, 1200], got {h}"
    assert vb == [0, 0, 1600, h], f"viewBox mismatch: {vb}"
    
    # 3. Font sizes >= 24
    text_elements = []
    for elem in root.iter('{http://www.w3.org/2000/svg}text'):
        full_text = "".join(elem.itertext()).strip()
        full_text = re.sub(r'\s+', ' ', full_text)
        fs = float(elem.attrib.get('font-size', '0'))
        tspans = list(elem.iter('{http://www.w3.org/2000/svg}tspan'))
        if fs == 0 and tspans:
            fs = float(tspans[0].attrib.get('font-size', '0'))
        assert fs >= 24, f"Text '{full_text}' font-size {fs} < 24"
        for tsp in tspans:
            tfs = tsp.attrib.get('font-size')
            if tfs is not None:
                assert float(tfs) >= 24, f"tspan font-size {tfs} < 24 in '{full_text}'"
        text_elements.append((full_text, fs, elem))
    print(f"3. All {len(text_elements)} text elements have font-size >= 24px (PASS)")
    
    # 4. Expected labels
    expected_labels = [
        "Which diagnosis tool answers which question",
        "Question",
        "Tool",
        "Where is every thread stuck right now?",
        "faulthandler.enable(), faulthandler.dump_traceback_later(timeout, repeat=True), kill -SIGUSR1 with faulthandler.register",
        "Look at a running process without changing its code",
        "py-spy dump, py-spy top, py-spy record",
        "What threads and tasks exist?",
        "threading.enumerate(), sys._current_frames(), asyncio.all_tasks(), psutil.Process().num_threads()",
        "Sockets and descriptors",
        "ss -s, lsof -p",
        "System calls and CPU",
        "strace -f -p, perf",
        "Where memory grows",
        "tracemalloc",
        "Health metrics to track",
        "in-flight tasks, queue depth, latency percentiles",
        "symptom, then faulthandler dump or py-spy dump, then the cause in the pitfall table",
        "Sample the live process before you guess"
    ]
    
    found_texts = [t for t, fs, el in text_elements]
    print(f"\n4. Checking {len(expected_labels)} expected labels against {len(found_texts)} found:")
    all_ok = True
    for exp in expected_labels:
        cnt = found_texts.count(exp)
        ok = (cnt == 1)
        if not ok:
            all_ok = False
        print(f"   [{'OK' if ok else 'FAIL'}] count={cnt}: '{exp}'")
    assert all_ok, "Some expected labels failed count == 1"
    
    extras = [t for t in found_texts if t not in expected_labels]
    print(f"   Extras: {extras}")
    assert len(extras) == 0, f"Found extra labels: {extras}"
    print("   All 19 labels matched exactly 1-to-1! (PASS)")
    
    # 5. Forbidden words
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'callout', 'takeaway']
    for t in found_texts:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for f in forbidden:
            assert f not in words, f"Forbidden word '{f}' in '{t}'"
    print("\n5. No forbidden style words in text! (PASS)")
    
    # 6. Orange check
    with open(svg_path, 'r', encoding='utf-8') as f:
        svg_str = f.read()
    orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
    print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
    assert 1 <= len(orange_matches) <= 6, f"Orange count out of range: {len(orange_matches)}"
    
    # 7. Arrows check
    markers = [e for e in root.iter() if "marker-end" in e.attrib]
    print(f"7. Arrow markers count: {len(markers)}")
    assert len(markers) == 0, f"Expected 0 arrows, got {len(markers)}"
    
    # 8. Paddings check
    print("\n8. Checking paddings inside boxes (>= 16px):")
    # Table rects:
    # Col 1: x=40, w=580. Icon at x=56, icon right = 56 + 48 = 104. Text starts at x=116.
    # Text right bound = 40 + 580 = 620. Right padding = 620 - (text_x + text_w).
    # Col 2: x=640, w=920. Text starts at x=664. Right bound = 640 + 920 = 1560.
    # Chain strip: x=40, w=1520. Icon x=58, icon right = 58 + 48 = 106. Text x=116. Right bound = 1560.
    # Bottom bar: x=40, w=1520. Centered at 800.
    
    for full_text, fs, el in text_elements:
        ff = el.attrib.get('font-family', 'sans-serif')
        factor = 0.62 if 'mono' in ff else 0.60
        tspans = list(el.iter('{http://www.w3.org/2000/svg}tspan'))
        lines = []
        if tspans:
            for tsp in tspans:
                lines.append((tsp.text.strip(), float(tsp.attrib.get('x', el.attrib.get('x', 0)))))
        else:
            lines.append((full_text, float(el.attrib.get('x', 0))))
            
        for line_str, x_pos in lines:
            line_w = len(line_str) * fs * factor
            if line_str == "Which diagnosis tool answers which question":
                # Title
                pad_l = (800 - line_w/2) - 0
                pad_r = 1600 - (800 + line_w/2)
                assert pad_l >= 40 and pad_r >= 40
            elif line_str == "Question":
                pad_l = (40 + 580/2 - line_w/2) - 40
                pad_r = (40 + 580) - (40 + 580/2 + line_w/2)
                assert pad_l >= 16 and pad_r >= 16
            elif line_str == "Tool":
                pad_l = (640 + 920/2 - line_w/2) - 640
                pad_r = (640 + 920) - (640 + 920/2 + line_w/2)
                assert pad_l >= 16 and pad_r >= 16
            elif line_str == "Sample the live process before you guess":
                pad_l = (800 - line_w/2) - 40
                pad_r = 1560 - (800 + line_w/2)
                assert pad_l >= 16 and pad_r >= 16
            elif "symptom, then faulthandler" in line_str:
                pad_l = x_pos - (40 + 18 + 40)
                pad_r = 1560 - (x_pos + line_w)
                print(f"   Chain strip: line_w={line_w:.1f}, pad_l={pad_l:.1f}, pad_r={pad_r:.1f}")
                assert pad_l >= 16 and pad_r >= 16
            elif x_pos < 640:
                # Left box: x=40..620. Icon right = 40 + 16 + 48 = 104.
                pad_l = x_pos - 104
                pad_r = 620 - (x_pos + line_w)
                print(f"   Q box: '{line_str}' pad_l={pad_l:.1f}, pad_r={pad_r:.1f}")
                assert pad_l >= 16, f"pad_l < 16: {pad_l} for '{line_str}'"
                assert pad_r >= 16, f"pad_r < 16: {pad_r} for '{line_str}'"
            else:
                # Right box: x=640..1560.
                pad_l = x_pos - 640
                pad_r = 1560 - (x_pos + line_w)
                print(f"   Tool box: '{line_str}' pad_l={pad_l:.1f}, pad_r={pad_r:.1f}")
                assert pad_l >= 16, f"pad_l < 16: {pad_l} for '{line_str}'"
                assert pad_r >= 16, f"pad_r < 16: {pad_r} for '{line_str}'"
                
    print("\nALL STRICT AUDITS PASSED!")

audit("test_diagnosis_candidate.svg")
