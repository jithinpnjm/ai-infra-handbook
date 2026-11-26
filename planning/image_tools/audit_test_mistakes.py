import xml.etree.ElementTree as ET
import re
import os
import subprocess

def audit():
    path = "test_mistakes.svg"
    tree = ET.parse(path)
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
    height = root.get('height')
    viewBox = root.get('viewBox')
    print(f"2. Dimensions: width={width}, height={height}, viewBox={viewBox}")
    assert width == "1600", f"width must be 1600, got {width}"
    assert viewBox == "0 0 1600 1200", f"viewBox must be '0 0 1600 1200', got {viewBox}"
    assert height == "1200", f"height must be 1200, got {height}"
    
    # 3. Check text elements and font-size >= 24
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
        
    # 4. Check expected labels
    expected_labels = [
        "Common mistakes in errors, files and subprocesses, grouped",
        "Area",
        "Mistake",
        "Fix",
        "Exceptions",
        "bare except and except Exception: pass; catching too much around too much code loses tracebacks and hides bugs",
        "catch the narrowest exception, log once at the top",
        "Files",
        "writing in place leads to partial writes; declaring success before an fsync; exists-then-create checks leave gaps; no explicit encoding; mixing bytes and str",
        "atomic replace, fsync, attempt then handle, encoding=utf-8",
        "Subprocess",
        "shell=True with interpolated input; missing timeouts; ignored return codes; parsing human-formatted output; secrets in command lines; capturing huge output in memory; pipe deadlocks; unreaped children; os.system, os.popen and the deprecated commands module",
        "argument list, timeout, check, machine-readable output, communicate, wait",
        "Global state",
        "mutating os.environ or os.chdir inside a library affects every caller; assuming the current directory",
        "copy the environment for the child, pass explicit paths",
        "Re-runs",
        "scripts unsafe to re-run",
        "dry-run mode, a lock against overlapping runs, UTC timestamps rather than naive ones",
        "Signals",
        "heavy work in signal handlers; ignoring SIGTERM in containers",
        "set a flag, finish and exit",
        "Untrusted input",
        "extracting tar or zip archives without validating paths; yaml.load or pickle on data from the network",
        "validate member paths, filter=data, safe_load",
        "a cleanup script runs twice because its lock was checked before it was taken, and the second run deletes the checkpoint the first one was writing",
        "A second attempt after a failure should be boring"
    ]
    
    found_texts = [t for t, fs in text_elements]
    print(f"\n4. Checking {len(expected_labels)} expected labels against {len(found_texts)} found:")
    all_ok = True
    for exp in expected_labels:
        cnt = found_texts.count(exp)
        ok = (cnt == 1)
        if not ok:
            all_ok = False
            print(f"   [FAIL] count={cnt}: '{exp}'")
        else:
            print(f"   [OK] '{exp}'")
            
    assert all_ok, "Some expected labels failed count == 1 check!"
    assert len(found_texts) == len(expected_labels), f"Text count mismatch: {len(found_texts)} vs {len(expected_labels)}"
    
    extras = [t for t in found_texts if t not in expected_labels]
    print(f"\nExtra texts: {extras}")
    assert len(extras) == 0, f"Found unexpected extra text: {extras}"
    
    # 5. Check forbidden words in text
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'takeaway']
    for t in found_texts:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for f in forbidden:
            assert f not in words, f"Forbidden word '{f}' in '{t}'!"
    print("\n5. No forbidden words found! (PASS)")
    
    # 6. Check orange count
    svg_str = open(path).read()
    orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
    print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
    assert 1 <= len(orange_matches) <= 6, f"Unexpected orange count: {len(orange_matches)}"
    
    # 7. Check arrows count
    lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
    paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
    total_arrows = len(lines) + len(paths)
    print(f"\n7. Total arrows with marker-end: {total_arrows} (Expected 0)")
    assert total_arrows == 0, f"Expected 0 arrows, got {total_arrows}"
    
    # 8. Check paddings and bounding boxes
    print("\n8. Checking paddings and bounds...")
    rects = []
    for elem in root.iter('{http://www.w3.org/2000/svg}rect'):
        x = float(elem.attrib.get('x', 0))
        y = float(elem.attrib.get('y', 0))
        w = float(elem.attrib.get('width', 0))
        h = float(elem.attrib.get('height', 0))
        fill = elem.attrib.get('fill', '')
        if w > 0 and h > 0 and fill != '#f5f8f5':
            rects.append((x, y, w, h, elem))
            
    failures = []
    for text in root.iter('{http://www.w3.org/2000/svg}text'):
        fs = float(text.attrib['font-size'])
        anchor = text.attrib.get('text-anchor', 'start')
        is_mono = (text.attrib.get('font-family') == 'monospace')
        rate = 0.62 if is_mono else 0.60
        
        tspans = text.findall('{http://www.w3.org/2000/svg}tspan')
        if not tspans:
            t_str = text.text.strip()
            tx = float(text.attrib['x'])
            ty = float(text.attrib['y'])
            w = len(t_str) * rate * fs
            if anchor == 'middle':
                x_start = tx - w / 2
                x_end = tx + w / 2
            else:
                x_start = tx
                x_end = tx + w
            top_y = ty - fs
            bot_y = ty + 0.25 * fs
            
            matching_rect = None
            for rx, ry, rw, rh, elem in rects:
                if rx <= x_start and x_end <= rx + rw and ry <= top_y and bot_y <= ry + rh:
                    matching_rect = (rx, ry, rw, rh)
                    break
            if matching_rect:
                rx, ry, rw, rh = matching_rect
                pad_l = x_start - rx
                pad_r = (rx + rw) - x_end
                pad_t = top_y - ry
                pad_b = (ry + rh) - bot_y
                if min(pad_l, pad_r) < 16.0:
                    failures.append(f"Horiz pad < 16: '{t_str}' ({pad_l:.1f}, {pad_r:.1f})")
                if min(pad_t, pad_b) < 0:
                    failures.append(f"Vertical overflow: '{t_str}' ({pad_t:.1f}, {pad_b:.1f})")
            else:
                failures.append(f"No container for single text '{t_str}'")
        else:
            base_x = float(text.attrib.get('x', 0))
            cur_y = float(text.attrib.get('y', 0))
            for tsp in tspans:
                t_str = tsp.text.strip()
                tsp_x = float(tsp.attrib.get('x', base_x))
                dy = float(tsp.attrib.get('dy', 0))
                cur_y += dy
                w = len(t_str) * rate * fs
                if anchor == 'middle':
                    x_start = tsp_x - w / 2
                    x_end = tsp_x + w / 2
                else:
                    x_start = tsp_x
                    x_end = tsp_x + w
                top_y = cur_y - fs
                bot_y = cur_y + 0.25 * fs
                
                matching_rect = None
                for rx, ry, rw, rh, elem in rects:
                    if rx <= x_start and x_end <= rx + rw and ry <= top_y and bot_y <= ry + rh:
                        matching_rect = (rx, ry, rw, rh)
                        break
                if matching_rect:
                    rx, ry, rw, rh = matching_rect
                    pad_l = x_start - rx
                    pad_r = (rx + rw) - x_end
                    pad_t = top_y - ry
                    pad_b = (ry + rh) - bot_y
                    if min(pad_l, pad_r) < 16.0:
                        failures.append(f"Horiz pad < 16: '{t_str}' ({pad_l:.1f}, {pad_r:.1f})")
                    if min(pad_t, pad_b) < 0:
                        failures.append(f"Vertical overflow: '{t_str}' ({pad_t:.1f}, {pad_b:.1f})")
                else:
                    if "Common mistakes in errors" in t_str or "and subprocesses, grouped" in t_str:
                        # Title on canvas
                        print(f"   [Canvas Title] '{t_str}' pad_l={x_start:.1f}, pad_r={1600-x_end:.1f}")
                    else:
                        failures.append(f"No container for tspan '{t_str}' at ({tsp_x}, {cur_y})")
                        
    print(f"Padding failures: {len(failures)}")
    for f in failures:
        print(f"   FAILED: {f}")
    assert len(failures) == 0, "Padding / bounds audit failed!"
    print("ALL BOUNDS AND PADDINGS PERFECT!")
    
    # 9. Chrome headless render
    chrome_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    if os.path.exists(chrome_path):
        out_png = "/tmp/test_mistakes.png"
        res = subprocess.run([
            chrome_path,
            '--headless=new',
            '--disable-gpu',
            '--hide-scrollbars',
            '--window-size=1600,1200',
            f'--screenshot={out_png}',
            f'file://{os.path.abspath(path)}'
        ], capture_output=True, text=True)
        print(f"\n9. Chrome render exit code: {res.returncode}")
        assert res.returncode == 0, f"Chrome failed: {res.stderr}"
        print(f"Screenshot written to {out_png}")
        
    print("\nALL AUDIT CHECKS PASSED PERFECTLY!")

if __name__ == "__main__":
    audit()
