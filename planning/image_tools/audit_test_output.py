import xml.etree.ElementTree as ET
import re
import subprocess
import pathlib

svg_path = "test_output.svg"
tree = ET.parse(svg_path)
root = tree.getroot()

print("=== 1. First children check: <title> and <desc> ===")
children = list(root)
tag1 = children[0].tag.split('}')[-1]
tag2 = children[1].tag.split('}')[-1]
print(f"Child 0: <{tag1}>, Child 1: <{tag2}>")
assert tag1 == "title", f"First child must be title, got {tag1}"
assert tag2 == "desc", f"Second child must be desc, got {tag2}"
print("   [PASS] <title> and <desc> are first children.")

print("\n=== 2. Dimensions and viewBox ===")
w = root.attrib.get('width')
h = root.attrib.get('height')
vb = root.attrib.get('viewBox')
print(f"Width: {w}, Height: {h}, viewBox: {vb}")
assert w == "1600"
assert vb.startswith("0 0 1600 ")
vb_parts = [float(x) for x in vb.split()]
assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
assert 900 <= vb_parts[3] <= 1200
assert float(h) == vb_parts[3]
print("   [PASS] Dimensions valid.")

print("\n=== 3. Font-size >= 24px ===")
text_elements = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = " ".join("".join(elem.itertext()).split())
    fs = elem.attrib.get('font-size')
    assert fs is not None, f"Missing font-size on text '{full_text}'"
    size = float(fs)
    assert size >= 24, f"Text '{full_text}' font-size {size} < 24!"
    for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
        tfs = tsp.attrib.get('font-size')
        if tfs is not None:
            assert float(tfs) >= 24, f"tspan font-size {tfs} < 24 in '{full_text}'"
    text_elements.append((full_text, size))

print(f"Total text elements: {len(text_elements)} (all font-sizes >= 24px)")
for i, (t, fs) in enumerate(text_elements, 1):
    print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

print("\n=== 4. Expected labels match ===")
expected_labels = [
    "Busy is not the same as useful",
    "Dashboard utilisation 95 percent",
    "requests finished on time",
    "requests finished too late to help anyone",
    "retries",
    "preempted requests whose cache was thrown away",
    "Goodput",
    "goodput QPS = QPS x fraction of requests within the objective",
    "cost per good token = cost per token / fraction within the objective",
    "if 5 percent of requests miss the objective, goodput is 95 percent of throughput and the cost of a good token rises by about 5 percent",
    "0.4 second p90 time to first token and 0.04 second p90 time per output token",
    "report goodput not throughput when comparing configurations, and name the latency objectives applied; do not push for full use if the latency objective is broken",
    "fraction of paid GPU time spent at the planned load, not the nvidia-smi figure"
]

found_texts = [t for t, fs in text_elements]
all_ok = True
for exp in expected_labels:
    cnt = found_texts.count(exp)
    ok = (cnt == 1)
    if not ok:
        all_ok = False
    print(f"   [{'OK' if ok else 'FAIL'}] count={cnt}: '{exp}'")
assert all_ok, "Some expected labels failed count == 1 check!"

extras = [t for t in found_texts if t not in expected_labels]
print(f"Extra texts: {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"
assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"
print("   [PASS] Every expected label appears exactly once, and zero extras.")

print("\n=== 5. Forbidden style words ===")
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"
print("   [PASS] No forbidden words found in text.")

print("\n=== 6. Orange count ===")
svg_str = pathlib.Path(svg_path).read_text()
oranges = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"Orange #db8129 count: {len(oranges)}")
assert len(oranges) == 1, f"Expected exactly 1 orange usage, got {len(oranges)}"
print("   [PASS] Exactly 1 orange element.")

print("\n=== 7. Arrows count ===")
lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
total_arrows = len(lines) + len(paths)
print(f"Total arrows: {total_arrows}")
assert total_arrows == 0, f"Expected exactly 0 arrows, got {total_arrows}"
print("   [PASS] Exactly 0 arrows.")

print("\n=== 8. External resources ===")
assert not any(el.tag.endswith('image') for el in root.iter()), "No <image> allowed"
assert not any(el.tag.endswith('script') for el in root.iter()), "No <script> allowed"
assert "http://" not in svg_str.replace("http://www.w3.org/2000/svg", ""), "No external URLs"
assert "https://" not in svg_str, "No external URLs"
print("   [PASS] No external images, scripts, or fonts.")

print("\n=== 9. Strict padding checks (>= 16px) ===")
rects = []
for el in root.iter('{http://www.w3.org/2000/svg}rect'):
    rx = float(el.attrib.get('x', 0))
    ry = float(el.attrib.get('y', 0))
    rw = float(el.attrib.get('width', 0))
    rh = float(el.attrib.get('height', 0))
    if rw > 0 and rh > 0 and rw < 1600:
        rects.append((rx, ry, rx + rw, ry + rh, el))

all_pad_passed = True
for el in root.iter('{http://www.w3.org/2000/svg}text'):
    fs = float(el.attrib.get('font-size', 24))
    ff = el.attrib.get('font-family', 'sans-serif')
    anchor = el.attrib.get('text-anchor', 'start')
    rate = 0.62 if 'monospace' in ff else 0.60
    
    tspans = el.findall('{http://www.w3.org/2000/svg}tspan')
    if tspans:
        cur_y = float(el.attrib.get('y', 0))
        for ts in tspans:
            txt = ts.text or ""
            if not txt.strip():
                continue
            tx = float(ts.attrib.get('x', el.attrib.get('x', 0)))
            dy = float(ts.attrib.get('dy', 0))
            cur_y += dy
            tw = len(txt) * rate * fs
            if anchor == 'middle':
                tl = tx - tw / 2
                tr = tx + tw / 2
            else:
                tl = tx
                tr = tx + tw
            ttop = cur_y - fs * 0.8
            tbot = cur_y
            
            containing = [r for r in rects if r[0] <= tl and r[1] <= ttop and r[2] >= tr and r[3] >= tbot]
            if containing:
                containing.sort(key=lambda r: (r[2]-r[0])*(r[3]-r[1]))
                best = containing[0]
                pad_l = tl - best[0]
                pad_r = best[2] - tr
                pad_t = ttop - best[1]
                pad_b = best[3] - tbot
                if pad_l < 15.9 or pad_r < 15.9 or pad_t < 15.9 or pad_b < 15.9:
                    print(f"WARN padding: '{txt}' in rect {best[:4]}: L={pad_l:.1f}, R={pad_r:.1f}, T={pad_t:.1f}, B={pad_b:.1f}")
                    all_pad_passed = False
                else:
                    print(f"   [OK pad] '{txt[:30]}...': L={pad_l:.1f}, R={pad_r:.1f}, T={pad_t:.1f}, B={pad_b:.1f}")
    else:
        txt = "".join(el.itertext()).strip()
        if not txt:
            continue
        tx = float(el.attrib.get('x', 0))
        ty = float(el.attrib.get('y', 0))
        tw = len(txt) * rate * fs
        if anchor == 'middle':
            tl = tx - tw / 2
            tr = tx + tw / 2
        else:
            tl = tx
            tr = tx + tw
        ttop = ty - fs * 0.8
        tbot = ty
        containing = [r for r in rects if r[0] <= tl and r[1] <= ttop and r[2] >= tr and r[3] >= tbot]
        if containing:
            containing.sort(key=lambda r: (r[2]-r[0])*(r[3]-r[1]))
            best = containing[0]
            pad_l = tl - best[0]
            pad_r = best[2] - tr
            pad_t = ttop - best[1]
            pad_b = best[3] - tbot
            if pad_l < 15.9 or pad_r < 15.9 or pad_t < 15.9 or pad_b < 15.9:
                print(f"WARN padding: '{txt}' in rect {best[:4]}: L={pad_l:.1f}, R={pad_r:.1f}, T={pad_t:.1f}, B={pad_b:.1f}")
                all_pad_passed = False
            else:
                print(f"   [OK pad] '{txt[:30]}...': L={pad_l:.1f}, R={pad_r:.1f}, T={pad_t:.1f}, B={pad_b:.1f}")

assert all_pad_passed, "Some paddings were < 16px!"
print("\nALL 9 STRICT AUDIT CHECKS PASSED PERFECTLY!")
