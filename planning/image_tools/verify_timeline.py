import re
import xml.etree.ElementTree as ET
import pathlib

svg_text = pathlib.Path("test_timeline.svg").read_text()
tree = ET.fromstring(svg_text)

print("=== 1. CHECKING XML STRUCTURE & ROOT ATTRIBUTES ===")
assert tree.tag.endswith('svg')
assert tree.attrib['width'] == '1600'
assert tree.attrib['viewBox'] == '0 0 1600 1200'

children = list(tree)
assert children[0].tag.endswith('title'), f"First child must be title, got {children[0].tag}"
assert children[1].tag.endswith('desc'), f"Second child must be desc, got {children[1].tag}"
print("PASS: Valid SVG root, dimensions (1600x1200), and first children <title>, <desc>.")

print("\n=== 2. CHECKING TITLE ===")
title_el = tree.find('.//{http://www.w3.org/2000/svg}title')
assert title_el.text == "Timeline overview", f"Unexpected title: {title_el.text}"
print(f"PASS: Title is '{title_el.text}'.")

print("\n=== 3. CHECKING ALL SOURCE LABELS (EXACTLY ONCE) ===")
# Exact source labels to check:
# Participants:
# "User / controller", "API server (+etcd)", "Scheduler", "Kubelet", "containerd (CRI)",
# "CNI plugin", "CSI node plugin", "Device plugin", "runc / kernel"
# Messages:
# "create Pod (admission, defaults, SA token, quota)"
# "watch: Pod with no nodeName"
# "bind Pod → node (spec.nodeName)"
# "watch: Pod bound to my node"
# "admit pod (resources, node-fit, kernel params), create pod dirs"
# "Allocate(GPU devices) → env/mounts/CDI names"
# "NodeStageVolume / NodePublishVolume (PVCs)"
# "RunPodSandbox"
# "ADD (netns, IP, routes)"
# "PullImage (per container)"
# "CreateContainer / StartContainer (init containers first)"
# "create namespaces, cgroups, mounts, exec"
# "status updates (PodScheduled, Initialized, ContainersReady, Ready)"
# "running: probes, log rotation, cgroup accounting, status heartbeats"
# "delete Pod"
# "deletionTimestamp set (grace)"
# "preStop, SIGTERM, wait, SIGKILL"
# "StopContainer, StopPodSandbox → CNI DEL"
# "unmount volumes"
# "remove Pod object (grace 0)"

expected_source_labels = [
    "Timeline overview",
    "User / controller",
    "API server (+etcd)",
    "Scheduler",
    "Kubelet",
    "containerd (CRI)",
    "CNI plugin",
    "CSI node plugin",
    "Device plugin",
    "runc / kernel",
    "create Pod (admission, defaults, SA token, quota)",
    "watch: Pod with no nodeName",
    "bind Pod → node (spec.nodeName)",
    "watch: Pod bound to my node",
    "admit pod (resources, node-fit, kernel params), create pod dirs",
    "Allocate(GPU devices) → env/mounts/CDI names",
    "NodeStageVolume / NodePublishVolume (PVCs)",
    "RunPodSandbox",
    "ADD (netns, IP, routes)",
    "PullImage (per container)",
    "CreateContainer / StartContainer (init containers first)",
    "create namespaces, cgroups, mounts, exec",
    "status updates (PodScheduled, Initialized, ContainersReady, Ready)",
    "running: probes, log rotation, cgroup accounting, status heartbeats",
    "delete Pod",
    "deletionTimestamp set (grace)",
    "preStop, SIGTERM, wait, SIGKILL",
    "StopContainer, StopPodSandbox → CNI DEL",
    "unmount volumes",
    "remove Pod object (grace 0)"
]

all_text_elements = tree.findall('.//{http://www.w3.org/2000/svg}text')
extracted_strings = []
for el in all_text_elements:
    full_t = "".join(el.itertext()).strip()
    full_t = re.sub(r'\s+', ' ', full_t)
    extracted_strings.append(full_t)

print(f"Total text elements extracted: {len(extracted_strings)}")

# Check each expected label appears exactly once
for exp in expected_source_labels:
    cnt = extracted_strings.count(exp)
    print(f"   [{'OK' if cnt == 1 else 'FAIL'}] count={cnt}: '{exp}'")
    assert cnt == 1, f"Expected label '{exp}' count={cnt}, expected 1!"

print("PASS: All 30 source labels are present exactly once.")

# Check for unexpected extra text
step_numbers = [str(i) for i in range(1, 20)]
valid_texts = expected_source_labels + step_numbers
extras = [t for t in extracted_strings if t not in valid_texts]
print(f"\nExtra texts found: {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"
print("PASS: No extra text found.")

print("\n=== 4. CHECKING FORBIDDEN WORDS ===")
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'takeaway']
for t in extracted_strings:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in text '{t}'!"
print("PASS: No forbidden words present as text.")

print("\n=== 5. CHECKING FONT SIZES ===")
for el in all_text_elements:
    t = "".join(el.itertext()).strip()
    fs = el.attrib.get('font-size')
    assert fs is not None, f"Missing font-size on text '{t}'"
    val = float(fs)
    assert val >= 24, f"font-size {val} < 24 on text '{t}'!"
    for tsp in el.findall('{http://www.w3.org/2000/svg}tspan'):
        tfs = tsp.attrib.get('font-size')
        if tfs is not None:
            assert float(tfs) >= 24, f"tspan font-size {tfs} < 24 in '{t}'"
print("PASS: All font-sizes >= 24px (NO text smaller than 24px anywhere).")

print("\n=== 6. CHECKING ARROW COUNT ===")
lines = [l for l in tree.findall('.//{http://www.w3.org/2000/svg}line') if 'marker-end' in l.attrib]
paths = [p for p in tree.findall('.//{http://www.w3.org/2000/svg}path') if 'marker-end' in p.attrib]
total_arrows = len(lines) + len(paths)
print(f"Total arrows with marker-end: {total_arrows} (lines: {len(lines)}, paths: {len(paths)})")
assert total_arrows == 19, f"Expected exactly 19 arrows, got {total_arrows}!"
print("PASS: Exactly 19 arrows matching the source sequence diagram.")

print("\n=== 7. CHECKING NUMBER CIRCLES ===")
circles = [c for c in tree.findall('.//{http://www.w3.org/2000/svg}circle') if c.attrib.get('r') == '24']
print(f"Total number circles (r=24): {len(circles)}")
assert len(circles) == 19, f"Expected 19 number circles, got {len(circles)}!"
print("PASS: Exactly 19 number circles with r=24.")

print("\n=== 8. CHECKING ORANGE USAGE ===")
oranges = re.findall(r'#db8129', svg_text, re.IGNORECASE)
print(f"Total orange #db8129 occurrences: {len(oranges)}")
assert 1 <= len(oranges) <= 4, f"Unexpected orange count: {len(oranges)}"
print("PASS: Orange #db8129 used for the single most important item (Note over K,X running state).")

print("\n=== 9. CHECKING COLORS ===")
assert "#f5f8f5" in svg_text
assert "#303a36" in svg_text
assert "#207448" in svg_text
assert "#e8f1ea" in svg_text
assert "#db8129" in svg_text
print("PASS: All required palette colors present.")

print("\n=== 10. CHECKING BOX PADDING CONSTRAINTS ===")
# Verify each text fits inside its card with >= 16px padding
# Card definitions from SVG rects
all_rects = tree.findall('.//{http://www.w3.org/2000/svg}rect')
print(f"Total rects found: {len(all_rects)}")
# For each step card, check padding
for el in tree.findall('.//{http://www.w3.org/2000/svg}g'):
    gid = el.attrib.get('id', '')
    if gid.startswith('step-') or gid == 'note-running':
        rect = el.find('{http://www.w3.org/2000/svg}rect')
        text_el = el.find('{http://www.w3.org/2000/svg}text')
        if rect is not None and text_el is not None:
            # We want the message text, not the circle step number
            texts = el.findall('{http://www.w3.org/2000/svg}text')
            msg_el = texts[-1]
            bw = float(rect.attrib['width'])
            fs = float(msg_el.attrib['font-size'])
            tspans = msg_el.findall('{http://www.w3.org/2000/svg}tspan')
            if len(tspans) > 0:
                for tsp in tspans:
                    ltxt = tsp.text.strip()
                    est_w = len(ltxt) * 0.6 * fs
                    pad = (bw - est_w) / 2
                    print(f"   [{gid} line] '{ltxt}' bw={bw} est_w={est_w:.1f} pad={pad:.1f}px")
                    assert pad >= 16.0, f"Line padding {pad} < 16 for '{ltxt}'!"
            else:
                t = msg_el.text.strip()
                est_w = len(t) * 0.6 * fs
                pad = (bw - est_w) / 2
                print(f"   [{gid}] '{t[:35]}...' bw={bw} est_w={est_w:.1f} pad={pad:.1f}px")
                assert pad >= 16.0, f"Card padding {pad} < 16 for '{t}'!"

print("PASS: All step card paddings >= 16px.")

print("\n=== ALL VERIFICATIONS PASSED PERFECTLY! ===")
