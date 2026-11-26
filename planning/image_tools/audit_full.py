#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re
import sys
import pathlib

svg_path = "final_candidate.svg"
tree = ET.parse(svg_path)
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
viewBox = root.get('viewBox')
height = root.get('height')
print(f"2. Dimensions: width={width}, height={height}, viewBox={viewBox}")
assert width == "1600", f"Expected width 1600, got {width}"
assert viewBox.startswith("0 0 1600 "), f"viewBox must start with '0 0 1600 ', got {viewBox}"
vb_parts = [float(x) for x in viewBox.split()]
assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
assert 900 <= vb_parts[3] <= 1200, f"Height {vb_parts[3]} outside 900-1200 range"
assert int(height) == int(vb_parts[3]), f"height {height} != viewBox height {vb_parts[3]}"

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
    "Data format cheat sheet: purpose, safe call and trap",
    "Format",
    "Use for",
    "Safe call",
    "Trap",
    "JSON",
    "machine interchange",
    "json.loads, json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False, default=str)",
    "float precision, large integers, NaN, duplicate keys; JSON Lines for streaming: for line in open(events.jsonl): json.loads(line)",
    "YAML",
    "configs people edit by hand",
    "yaml.safe_load, yaml.safe_dump(sort_keys=False), yaml.safe_load_all for multi-document manifests; ruamel.yaml preserves comments",
    "never yaml.load on untrusted input (arbitrary object construction); the Norway problem: region: no becomes boolean False",
    "TOML",
    "tool settings",
    "tomllib.loads (read-only stdlib since 3.11; tomli-w to write)",
    "no stdlib writer",
    "CSV",
    "tabular exports",
    "csv.DictReader and DictWriter with newline=\"\" and encoding",
    "spreadsheets may use utf-8-sig or cp1252; large data: pandas (chapter 3.10)",
    "INI",
    "legacy config",
    "configparser: cp[db].getint(port, fallback=5432)",
    "-",
    "Parquet or JSON Lines",
    "large datasets",
    "-",
    "-",
    "a metrics export contains NaN that the next tool in the chain refuses to read",
    "validate parsed data with a schema or pydantic; handle JSONDecodeError and YAMLError with file and line context; never eval data",
    "datetime.now(timezone.utc) for aware datetimes; time.monotonic() for durations, immune to clock changes; time.time() wall clock; time.perf_counter() for benchmarks; zoneinfo.ZoneInfo(Europe/Berlin) for time zones; datetime.fromisoformat and ISO 8601 with a timezone; store UTC and log in UTC; avoid naive datetimes",
    "Choose each format for its purpose, and parse with the safe call"
]

found_texts = [t for t, fs in text_elements]

print(f"\n4. Checking {len(expected_labels)} expected labels against {len(found_texts)} found:")
all_ok = True
for exp in set(expected_labels):
    cnt = found_texts.count(exp)
    expected_cnt = expected_labels.count(exp)
    ok = (cnt == expected_cnt)
    if not ok:
        all_ok = False
    print(f"   [{'OK' if ok else 'FAIL'}] count={cnt} (exp {expected_cnt}): '{exp[:45]}...'")

assert all_ok, "Some expected labels failed count check!"

extras = [t for t in found_texts if t not in expected_labels]
print(f"\nExtra texts: {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"
assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"

# 5. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for w in words:
        assert w not in forbidden, f"Forbidden word '{w}' found in text: '{t}'"

print("\n5. Forbidden words check: PASS!")

# 6. Check orange count
svg_str = pathlib.Path(svg_path).read_text(encoding='utf-8')
orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 6, f"Unexpected orange count: {len(orange_matches)}"

# 7. Check arrows count
lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
total_arrows = len(lines) + len(paths)
print(f"\n7. Total arrows with marker-end: {total_arrows}")
assert total_arrows == 0, f"Expected exactly 0 arrows, got {total_arrows}"

# 8. Check colors present
assert "#f5f8f5" in svg_str
assert "#303a36" in svg_str
assert "#207448" in svg_str
assert "#e8f1ea" in svg_str
assert "#db8129" in svg_str
print("\n8. All required colors present! (PASS)")

# 9. Strict padding check on all boxes and text
print("\n9. Checking text paddings across all lines:")
rects = []
for elem in root.iter('{http://www.w3.org/2000/svg}rect'):
    x = float(elem.attrib.get('x', 0))
    y = float(elem.attrib.get('y', 0))
    w = float(elem.attrib.get('width', 0))
    h = float(elem.attrib.get('height', 0))
    if w == 1600 or w == 8: continue # canvas bg or accent bar
    rects.append((x, y, w, h, elem))

for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    x = float(elem.attrib.get('x', 0))
    y = float(elem.attrib.get('y', 0))
    anchor = elem.attrib.get('text-anchor', 'start')
    fs = float(elem.attrib.get('font-size', 24))
    ff = elem.attrib.get('font-family', 'sans-serif')
    
    # Title is centered on canvas
    if y == 56:
        # Check title padding against canvas edges (0 and 1600)
        char_w = 0.60 * fs
        t_w = len(elem.text) * char_w
        left = 800 - t_w / 2
        right = 800 + t_w / 2
        assert left >= 40 and 1600 - right >= 40
        assert y - 0.75 * fs >= 16
        continue
        
    tspans = list(elem.iter('{http://www.w3.org/2000/svg}tspan'))
    if tspans:
        cur_y = y
        lines = []
        for tsp in tspans:
            tx = float(tsp.attrib.get('x', x))
            dy = float(tsp.attrib.get('dy', 0))
            cur_y += dy
            tff = tsp.attrib.get('font-family', ff)
            tfs = float(tsp.attrib.get('font-size', fs))
            txt = tsp.text or ""
            lines.append((tx, cur_y, txt, tfs, tff))
    else:
        txt = elem.text or ""
        lines = [(x, y, txt, fs, ff)]
        
    for i, (tx, ty, txt, lfs, lff) in enumerate(lines):
        is_mono = ('mono' in lff)
        char_w = 0.62 * lfs if is_mono else 0.60 * lfs
        w_text = len(txt) * char_w
        if anchor == 'middle':
            x_start = tx - w_text / 2
            x_end = tx + w_text / 2
        elif anchor == 'end':
            x_start = tx - w_text
            x_end = tx
        else:
            x_start = tx
            x_end = tx + w_text
            
        containing = [r for r in rects if r[0] - 1 <= x_start and x_end <= r[0] + r[2] + 1 and r[1] - 10 <= ty <= r[1] + r[3] + 20]
        assert len(containing) > 0, f"No containing rect for line '{txt}' at ({x_start:.1f}, {ty:.1f})"
        rx, ry, rw, rh, _ = containing[0]
        
        # Horizontal pad
        pad_l = x_start - rx
        pad_r = (rx + rw) - x_end
        assert pad_l >= 15.5, f"Left pad {pad_l:.1f} < 16 for '{txt}'"
        assert pad_r >= 15.5, f"Right pad {pad_r:.1f} < 16 for '{txt}'"
        
        # Vertical pad
        top_y = ty - lfs
        bot_y = ty + 0.25 * lfs
        if i == 0:
            pad_t = top_y - ry
            assert pad_t >= 8, f"Top pad {pad_t:.1f} < 8 for '{txt}'"
        if i == len(lines) - 1:
            pad_b = (ry + rh) - bot_y
            assert pad_b >= 8, f"Bottom pad {pad_b:.1f} < 8 for '{txt}'"

print("9. All padding checks PASSED!")
print("\nALL 100% AUDIT CHECKS PASSED PERFECTLY!")
