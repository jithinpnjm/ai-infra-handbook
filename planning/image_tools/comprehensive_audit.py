import xml.etree.ElementTree as ET
import re

def comprehensive_audit(svg_path):
    tree = ET.parse(svg_path)
    root = tree.getroot()

    print(f"=== COMPREHENSIVE AUDIT: {svg_path} ===\n")

    # 1. First children check: <title> and <desc>
    assert len(root) >= 2, "Root must have at least 2 children"
    tag0 = root[0].tag.split('}')[-1]
    tag1 = root[1].tag.split('}')[-1]
    assert tag0 == 'title', f"First child must be <title>, got <{tag0}>"
    assert tag1 == 'desc', f"Second child must be <desc>, got <{tag1}>"
    print("[PASS] 1. First children are <title> and <desc>.")

    # 2. Canvas dimensions and viewBox
    w = root.attrib.get('width')
    h = root.attrib.get('height')
    vb = root.attrib.get('viewBox')
    assert w == "1600", f"Width must be 1600, got {w}"
    vb_parts = [float(x) for x in vb.split()]
    assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600, f"Invalid viewBox: {vb}"
    assert 900 <= vb_parts[3] <= 1200, f"Height must be between 900 and 1200, got {vb_parts[3]}"
    assert int(h) == int(vb_parts[3]), f"height {h} != viewBox height {vb_parts[3]}"
    print(f"[PASS] 2. Dimensions valid: width={w}, height={h}, viewBox='{vb}'.")

    # 3. Label exactness check
    expected_labels = [
        "Detecting throttling, and why thread pools sized from nproc make it worse",
        "Detect throttling",
        "usage_usec, user_usec, system_usec, nr_periods, nr_throttled, throttled_usec, nr_bursts, burst_usec",
        "compare nr_throttled with nr_periods and check throttled_usec",
        "container_cpu_cfs_throttled_periods_total and container_cpu_cfs_periods_total",
        "cpu.pressure (PSI)",
        "The oversubscription trap",
        "64 CPUs",
        "cpu.max = 200000 100000 (2 CPUs)",
        "nproc = 64",
        "the quota is burned early in each period, then every thread pauses even though other CPUs are idle",
        "Go: automaxprocs (GOMAXPROCS)",
        "Java: -XX:ActiveProcessorCount",
        "OpenMP: OMP_NUM_THREADS",
        "Python: os.cpu_count() reports the host, pass the limit in",
        "Kernels before 5.4 (slice-expiry fix) could throttle even with unused quota: use a recent kernel",
        "cpu.max.burst (kernel 5.14 and later) lets a group save unused quota for short bursts",
        "Inside a container, nproc and /proc/cpuinfo still show the host unless you use lxcfs or a runtime that understands limits",
        "Average usage can look healthy while the pauses hide inside each period"
    ]

    text_nodes = list(root.iter('{http://www.w3.org/2000/svg}text'))
    found_labels = []
    for el in text_nodes:
        # Join text and tspans with single spaces
        raw = " ".join("".join(el.itertext()).split())
        found_labels.append(raw)

    print(f"\n--- Checking Labels (Expected: {len(expected_labels)}, Found: {len(found_labels)}) ---")
    for exp in expected_labels:
        cnt = found_labels.count(exp)
        assert cnt == 1, f"Expected label '{exp}' count={cnt} (must be 1)"
        print(f"  [OK] '{exp}'")
    
    extras = [l for l in found_labels if l not in expected_labels]
    assert len(extras) == 0, f"Found unexpected extra text labels: {extras}"
    print("[PASS] 3. Every expected label appears exactly once, no extras.")

    # 4. Check banned style words in text
    banned = ["orange", "green", "grey", "gray", "bold", "monospace", "arrow"]
    for l in found_labels:
        words = re.findall(r'\b[A-Za-z]+\b', l.lower())
        for b in banned:
            assert b not in words, f"Banned style word '{b}' found in label: '{l}'"
    print("[PASS] 4. No banned styling words present in text.")

    # 5. Font size check
    for el in text_nodes:
        fs = float(el.attrib.get('font-size', '0'))
        full_text = " ".join("".join(el.itertext()).split())
        assert fs >= 24, f"Text '{full_text}' font-size {fs} < 24 px!"
        for tsp in el.iter('{http://www.w3.org/2000/svg}tspan'):
            tfs = tsp.attrib.get('font-size')
            if tfs:
                assert float(tfs) >= 24, f"tspan font-size {tfs} < 24 px in '{full_text}'"
    print("[PASS] 5. All text elements have font-size >= 24 px.")

    # 6. Geometric padding check for every text line against bounding boxes and icons
    rects = []
    for el in root.iter('{http://www.w3.org/2000/svg}rect'):
        rx = float(el.attrib.get('x', 0))
        ry = float(el.attrib.get('y', 0))
        rw = float(el.attrib.get('width', 0))
        rh = float(el.attrib.get('height', 0))
        if rw > 0 and rh > 0 and rw < 1600:
            rects.append((rx, ry, rx + rw, ry + rh, el))

    # Icons bounding boxes
    icons = []
    for g in root.iter('{http://www.w3.org/2000/svg}g'):
        tr = g.attrib.get('transform', '')
        m = re.match(r'translate\(\s*([\d\.-]+)\s*,\s*([\d\.-]+)\s*\)', tr)
        if m:
            gx, gy = float(m.group(1)), float(m.group(2))
            # Outline icon size ~ 56x56
            icons.append((gx, gy, gx + 56, gy + 56))

    print(f"\n--- Checking Geometric Paddings & Clearances ---")
    all_pad_ok = True
    for el in text_nodes:
        fs = float(el.attrib.get('font-size', 24))
        ff = el.attrib.get('font-family', 'sans-serif')
        rate = 0.62 if 'monospace' in ff else 0.60
        anchor = el.attrib.get('text-anchor', 'start')

        tspans = el.findall('{http://www.w3.org/2000/svg}tspan')
        lines = []
        if tspans:
            cur_y = float(el.attrib.get('y', 0))
            for ts in tspans:
                txt = ts.text or ""
                if not txt.strip():
                    continue
                tx = float(ts.attrib.get('x', el.attrib.get('x', 0)))
                t_font = ts.attrib.get('font-family', ff)
                t_rate = 0.62 if 'monospace' in t_font else rate
                t_fs = float(ts.attrib.get('font-size', fs))
                if 'y' in ts.attrib:
                    cur_y = float(ts.attrib['y'])
                elif 'dy' in ts.attrib:
                    cur_y += float(ts.attrib['dy'])
                lines.append((txt, tx, cur_y, t_rate, t_fs))
        else:
            txt = "".join(el.itertext()).strip()
            tx = float(el.attrib.get('x', 0))
            ty = float(el.attrib.get('y', 0))
            lines.append((txt, tx, ty, rate, fs))

        for txt, tx, ty, t_rate, t_fs in lines:
            tw = len(txt) * t_rate * t_fs
            if anchor == 'middle':
                tl = tx - tw / 2
                tr = tx + tw / 2
            else:
                tl = tx
                tr = tx + tw
            ttop = ty - t_fs * 0.8
            tbot = ty

            # Find innermost containing rect
            containing = [r for r in rects if r[0] <= tl + 0.1 and r[1] <= ttop + 0.1 and r[2] >= tr - 0.1 and r[3] >= tbot - 0.1]
            if containing:
                containing.sort(key=lambda r: (r[2]-r[0])*(r[3]-r[1]))
                best = containing[0]
                pad_l = tl - best[0]
                pad_r = best[2] - tr
                pad_t = ttop - best[1]
                pad_b = best[3] - tbot
                if pad_l < 15.9 or pad_r < 15.9 or pad_t < 15.9 or pad_b < 15.9:
                    print(f"WARN box pad: '{txt}': L={pad_l:.1f}, R={pad_r:.1f}, T={pad_t:.1f}, B={pad_b:.1f} (in rect {best[:4]})")
                    all_pad_ok = False
            
            # Check icon clearance
            for ix1, iy1, ix2, iy2 in icons:
                # If bounding boxes intersect
                if not (tr < ix1 or tl > ix2 or tbot < iy1 or ttop > iy2):
                    print(f"FAIL icon collision: '{txt}' collides with icon ({ix1}, {iy1}, {ix2}, {iy2})")
                    all_pad_ok = False
                else:
                    # Check if too close (< 16px) when horizontally or vertically aligned
                    # Horizontal overlap
                    h_overlap = not (tr < ix1 or tl > ix2)
                    v_overlap = not (tbot < iy1 or ttop > iy2)
                    if h_overlap:
                        # clearance vertically
                        v_gap = min(abs(ttop - iy2), abs(iy1 - tbot))
                        if v_gap < 15.9:
                            print(f"WARN icon v_gap {v_gap:.1f} < 16: '{txt}' and icon ({ix1}, {iy1}, {ix2}, {iy2})")
                            all_pad_ok = False
                    if v_overlap:
                        # clearance horizontally
                        h_gap = min(abs(tl - ix2), abs(ix1 - tr))
                        if h_gap < 15.9:
                            print(f"WARN icon h_gap {h_gap:.1f} < 16: '{txt}' and icon ({ix1}, {iy1}, {ix2}, {iy2})")
                            all_pad_ok = False

    if all_pad_ok:
        print("[PASS] 6. All text lines have padding >= 16px and safe clearance from icons!")
    else:
        print("[FAIL] 6. Some paddings or clearances were violated.")

    print("\n=== AUDIT COMPLETE ===")
    return all_pad_ok

if __name__ == '__main__':
    import sys
    fname = sys.argv[1] if len(sys.argv) > 1 else "candidate_throttling.svg"
    comprehensive_audit(fname)
