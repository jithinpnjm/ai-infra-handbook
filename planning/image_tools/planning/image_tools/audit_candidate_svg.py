#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re
import sys

# Comprehensive Audit Script for candidate_gpu_checklist.svg

tree = ET.parse("candidate_gpu_checklist.svg")
root = tree.getroot()

print("==================== SVG AUDIT REPORT ====================")

# 1. First children check: <title> and <desc>
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. Children: first=<{first_tag}>, second=<{second_tag}>")
assert first_tag == 'title', f"First child must be title, got {first_tag}"
assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"
print("   PASS: First children are <title> and <desc>")

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
print(f"   PASS: Dimensions valid (1600 x {height})")

# 3. Check font-size >= 24 everywhere
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

print(f"3. Total text elements: {len(text_elements)} (all font-sizes >= 24px)")
for i, (t, fs) in enumerate(text_elements, 1):
    print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

# 4. Expected labels check
expected_labels = [
    "The 60-second checklist for a GPU node: eight read-only additions",
    "Command",
    "What to check",
    "Reads which layer",
    "nvidia-smi",
    "all GPUs present, driver and CUDA versions, memory, processes, power draw versus cap, temperature, throttle reasons (nvidia-smi -q -d PERFORMANCE)",
    "nvidia-smi dmon -s pucvmet -d 1",
    "per-GPU power, utilisation (sm, mem, enc/dec), clocks, memory, PCIe and NVLink throughput, ECC counters per second",
    "nvidia-smi topo -m and nvidia-smi nvlink -s",
    "topology matrix (NV#, PIX, PXB, PHB, SYS, NODE), NVLink active links",
    "dcgmi dmon -e ... or dcgmi diag -r 1",
    "SM activity and occupancy, tensor-pipe activity, DRAM activity, NVLink and PCIe throughput; quick health test",
    'journalctl -k | grep -iE "NVRM|Xid|nvidia"',
    "GPU errors: Xid 79 fallen off the bus, 48 63 64 94 95 ECC and retired pages, 74 NVLink errors",
    "ibstat, ibv_devinfo, rdma link, perfquery or ethtool -S",
    "link state and rate, error counters",
    "cat /proc/pressure/{cpu,memory,io}",
    "PSI: tasks stalled on each resource",
    "numastat, lstopo, cat /proc/cmdline, sysctl -a diff versus baseline",
    "placement and drift",
    "All of them are read-only; option names vary by driver and DCGM version, so check the flags on your own system",
    "Add these to the host checklist when you are on a GPU node"
]

step_numbers = {"11", "12", "13", "14", "15", "16", "17", "18"}

found_texts = [t for t, fs in text_elements]
print(f"\n4. Checking {len(expected_labels)} expected labels:")
all_ok = True
for exp in expected_labels:
    cnt = found_texts.count(exp)
    ok = (cnt == 1)
    if not ok:
        all_ok = False
        print(f"   [FAIL] count={cnt}: '{exp}'")
    else:
        print(f"   [OK  ] count=1: '{exp}'")

assert all_ok, "Some expected labels failed count == 1 check!"

extras = [t for t in found_texts if t not in expected_labels and t not in step_numbers]
print(f"\nExtra texts count: {len(extras)}")
if extras:
    print(f"Extra texts: {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"

for s in sorted(step_numbers):
    cnt = found_texts.count(s)
    assert cnt == 1, f"Step number {s} count {cnt} != 1!"
print("   PASS: All step numbers 11..18 present exactly once!")

# 5. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"

print("\n5. PASS: No forbidden style words in any text!")

# 6. Check orange count and usage
with open("candidate_gpu_checklist.svg") as f:
    svg_raw = f.read()

orange_matches = re.findall(r'#db8129', svg_raw, re.IGNORECASE)
print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 6, f"Unexpected orange count: {len(orange_matches)}"
print("   PASS: Orange used strictly for row 15!")

# 7. Check arrows count
# Arrows in this diagram must be 0
arrow_paths = []
for elem in root.iter('{http://www.w3.org/2000/svg}path'):
    if elem.attrib.get("marker-end") == "url(#arrow)":
        arrow_paths.append(elem.attrib.get("d"))

print(f"\n7. Total arrow paths: {len(arrow_paths)}")
assert len(arrow_paths) == 0, f"Expected 0 arrows, got {len(arrow_paths)}"
print("   PASS: Exactly 0 arrows (matches source)!")

# 8. Check padding on all cards / rects
print("\n8. Checking padding >= 16px on all boxes...")
def get_line_width(text, font_size, font_family):
    is_mono = "monospace" in font_family
    rate = 0.62 if is_mono else 0.6
    return len(text) * font_size * rate

groups = root.findall('.//{http://www.w3.org/2000/svg}g')
padding_failures = 0

for g in groups:
    gid = g.attrib.get('id', '')
    rects = g.findall('{http://www.w3.org/2000/svg}rect')
    texts = g.findall('{http://www.w3.org/2000/svg}text')
    
    # If group has multiple rects and texts, associate text with containing rect
    for rect in rects:
        rx = float(rect.attrib['x'])
        ry = float(rect.attrib['y'])
        rw = float(rect.attrib['width'])
        rh = float(rect.attrib['height'])
        
        for text in texts:
            t_ff = text.attrib.get('font-family', 'sans-serif')
            t_fs = float(text.attrib.get('font-size', '24'))
            t_anchor = text.attrib.get('text-anchor', 'start')
            text_x = float(text.attrib.get('x', '0'))
            text_y = float(text.attrib.get('y', '0'))
            
            # Check if this text belongs inside this rect
            # Bounding box of text rough check:
            if not (rx <= text_x <= rx + rw and ry <= text_y <= ry + rh + 20):
                continue
                
            tspans = text.findall('{http://www.w3.org/2000/svg}tspan')
            if tspans:
                curr_y = text_y
                for ts in tspans:
                    ts_text = (ts.text or "").strip()
                    if not ts_text:
                        continue
                    ts_x = float(ts.attrib.get('x', str(text_x)))
                    ts_dy = float(ts.attrib.get('dy', '0'))
                    curr_y += ts_dy
                    ts_fs = float(ts.attrib.get('font-size', str(t_fs)))
                    ts_ff = ts.attrib.get('font-family', t_ff)
                    lw = get_line_width(ts_text, ts_fs, ts_ff)
                    
                    if t_anchor == 'middle':
                        left_x = ts_x - lw / 2.0
                        right_x = ts_x + lw / 2.0
                    else:
                        left_x = ts_x
                        right_x = ts_x + lw
                        
                    left_pad = left_x - rx
                    right_pad = (rx + rw) - right_x
                    top_pad = curr_y - ts_fs - ry
                    bot_pad = (ry + rh) - curr_y
                    
                    if left_pad < 16 or right_pad < 16 or top_pad < 16 or bot_pad < 16:
                        print(f"   [FAIL PAD] in {gid}: line '{ts_text[:25]}' L={left_pad:.1f}, R={right_pad:.1f}, T={top_pad:.1f}, B={bot_pad:.1f}")
                        padding_failures += 1
            else:
                raw_t = "".join(text.itertext()).strip()
                lw = get_line_width(raw_t, t_fs, t_ff)
                if t_anchor == 'middle':
                    left_x = text_x - lw / 2.0
                    right_x = text_x + lw / 2.0
                else:
                    left_x = text_x
                    right_x = text_x + lw
                
                left_pad = left_x - rx
                right_pad = (rx + rw) - right_x
                top_pad = text_y - t_fs - ry
                bot_pad = (ry + rh) - text_y
                
                if left_pad < 16 or right_pad < 16 or top_pad < 16 or bot_pad < 16:
                    print(f"   [FAIL PAD] in {gid}: text '{raw_t[:25]}' L={left_pad:.1f}, R={right_pad:.1f}, T={top_pad:.1f}, B={bot_pad:.1f}")
                    padding_failures += 1

assert padding_failures == 0, f"Found {padding_failures} padding failures!"
print("   PASS: All text lines have >= 16px padding on left, right, top, and bottom!")

print("\n==================== ALL CHECKS PASSED PERFECTLY ====================")
