import xml.etree.ElementTree as ET
import re

svg_path = "test_candidate_retry_classify.svg"
tree = ET.parse(svg_path)
root = tree.getroot()

print(f"=== Validating {svg_path} ===")

# 1. First children check: <title> and <desc>
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. First child: <{first_tag}>, Second child: <{second_tag}>")
assert first_tag == 'title', f"First child must be title, got {first_tag}"
assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"

# 2. Dimensions
width = root.get('width')
viewBox = root.get('viewBox')
height = root.get('height')
print(f"2. Dimensions: width={width}, height={height}, viewBox={viewBox}")
assert width == "1600"
assert viewBox.startswith("0 0 1600 ")
vb_parts = [float(x) for x in viewBox.split()]
assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
assert 900 <= vb_parts[3] <= 1200
assert int(height) == int(vb_parts[3])

# 3. Check font-size >= 24 on all text and tspans
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

# 4. Expected labels
expected_labels = [
    "Which failures to retry: methods, status codes and exceptions",
    "Retry",
    "methods: GET, PUT, DELETE, or a POST with an idempotency key",
    "status codes: 429, 502, 503, 504",
    "exceptions: httpx.ConnectError, ReadTimeout, ConnectTimeout, RemoteProtocolError",
    "Never retry",
    "status 400, 401, 403, 404, 409: the answer will not change between attempts, retrying is a bug",
    "POST without an idempotency key",
    "Policy",
    "retry_if_exception(transient)",
    "wait_exponential_jitter(initial=0.5, max=20): 0.5, 1, 2, 4 and so on, capped, with jitter",
    "stop_after_attempt(6) | stop_after_delay(60)",
    "before_sleep_log(log, WARNING)",
    "reraise=True",
    "honour Retry-After; cap both attempts and total time",
    "delay = min(cap, base * 2**attempt); sleep(random.uniform(0, delay))",
    "backoff: each retry waits longer than the last; jitter: each client adds randomness so many clients that fail together do not retry in lockstep",
    "The only 4xx worth retrying is 429"
]

found_texts = [t for t, fs in text_elements]

print(f"\n4. Checking {len(expected_labels)} expected labels against {len(found_texts)} found:")
all_ok = True
for exp in expected_labels:
    cnt = found_texts.count(exp)
    ok = (cnt == 1)
    if not ok:
        all_ok = False
    print(f"   [{'OK' if ok else 'FAIL'}] count={cnt}: '{exp[:45]}...'")

assert all_ok, "Some expected labels failed count == 1 check!"

extras = [t for t in found_texts if t not in expected_labels]
print(f"\n5. Extras count: {len(extras)}")
if extras:
    print("   Unexpected extras:", extras)
assert len(extras) == 0, f"Unexpected extra texts found: {extras}"
assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"

# 5. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for w in words:
        assert w not in forbidden, f"Forbidden word '{w}' found in text: '{t}'"

print("\n6. Forbidden words check: PASS!")

# 6. Check bounding boxes and paddings >= 16px
print("\n7. Checking text paddings...")
rects = []
for elem in root.iter('{http://www.w3.org/2000/svg}rect'):
    x = float(elem.attrib.get('x', 0))
    y = float(elem.attrib.get('y', 0))
    w = float(elem.attrib.get('width', 0))
    h = float(elem.attrib.get('height', 0))
    fill = elem.attrib.get('fill', '')
    if w > 0 and h > 0 and fill != '#f5f8f5':
        rects.append((x, y, w, h, elem))

padding_failures = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    fs = float(elem.attrib['font-size'])
    ff = elem.attrib.get('font-family', '')
    char_factor = 0.62 if 'mono' in ff else 0.60
    anchor = elem.attrib.get('text-anchor', 'start')
    
    tspans = elem.findall('{http://www.w3.org/2000/svg}tspan')
    if not tspans:
        lines = [(elem.text.strip(), float(elem.attrib['x']), float(elem.attrib['y']))]
    else:
        base_x = float(elem.attrib.get('x', 0))
        cur_y = float(elem.attrib.get('y', 0))
        lines = []
        for tsp in tspans:
            t_str = tsp.text.strip()
            tx = float(tsp.attrib.get('x', base_x))
            dy = float(tsp.attrib.get('dy', 0))
            cur_y += dy
            lines.append((t_str, tx, cur_y))
            
    for t_str, tx, ty in lines:
        w = len(t_str) * char_factor * fs
        if anchor == 'middle':
            x_start = tx - w / 2
            x_end = tx + w / 2
        else:
            x_start = tx
            x_end = tx + w
        top_y = ty - fs
        bot_y = ty + 0.25 * fs
        
        # find matching rect (smallest containing)
        candidates = []
        for rx, ry, rw, rh, r_elem in rects:
            if rx <= x_start and x_end <= rx + rw and ry <= top_y and bot_y <= ry + rh:
                candidates.append((rw * rh, rx, ry, rw, rh, r_elem))
                
        if candidates:
            candidates.sort(key=lambda c: c[0])
            _, rx, ry, rw, rh, _ = candidates[0]
            pad_l = x_start - rx
            pad_r = (rx + rw) - x_end
            pad_t = top_y - ry
            pad_b = (ry + rh) - bot_y
            if min(pad_l, pad_r) < 16.0:
                padding_failures.append(f"Horiz pad < 16: '{t_str}' (L={pad_l:.1f}, R={pad_r:.1f}) in rect [{rx}, {ry}, {rw}, {rh}]")
            if min(pad_t, pad_b) < 0:
                padding_failures.append(f"Vertical overflow: '{t_str}' (T={pad_t:.1f}, B={pad_b:.1f}) in rect [{rx}, {ry}, {rw}, {rh}]")
        else:
            if "Which failures to retry" in t_str or "methods, status codes" in t_str:
                # Title on canvas
                pad_l = x_start
                pad_r = 1600 - x_end
                if min(pad_l, pad_r) < 16.0:
                    padding_failures.append(f"Title margin < 16: '{t_str}'")
            else:
                padding_failures.append(f"No containing rect for '{t_str}' at ({tx}, {ty})")

if padding_failures:
    print(f"FAILED padding checks ({len(padding_failures)}):")
    for f in padding_failures:
        print("  ", f)
else:
    print("ALL PADDING CHECKS PASSED (>= 16px horizontal, no vertical overflow)!")

assert len(padding_failures) == 0, f"{len(padding_failures)} padding failures found!"

print("\n=== ALL CHECKS PASSED PERFECTLY! ===")
