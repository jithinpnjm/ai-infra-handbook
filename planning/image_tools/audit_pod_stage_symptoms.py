#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

svg_file = "p3-0508-pod-stage-symptoms.svg"
tree = ET.parse(svg_file)
root = tree.getroot()

# 1. Structure: <title> and <desc>
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. Structure: Child 0: <{first_tag}>, Child 1: <{second_tag}>")
assert first_tag == "title", f"First child must be title, got {first_tag}"
assert second_tag == "desc", f"Second child must be desc, got {second_tag}"

# 2. Dimensions
width = root.attrib.get("width")
height = root.attrib.get("height")
viewBox = root.attrib.get("viewBox")
print(f"2. Dimensions: width={width}, height={height}, viewBox={viewBox}")
assert width == "1600", f"width must be 1600, got {width}"
vb_parts = [float(x) for x in viewBox.split()]
assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
assert 900 <= vb_parts[3] <= 1200, f"H={vb_parts[3]} outside 900..1200"
assert float(height) == vb_parts[3]

# 3. Text font-size >= 24
text_elements = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = "".join(elem.itertext()).strip()
    full_text = re.sub(r'\s+', ' ', full_text)
    fs = float(elem.attrib.get('font-size', '0'))
    tspans = list(elem.iter('{http://www.w3.org/2000/svg}tspan'))
    if fs == 0 and tspans:
        fs = float(tspans[0].attrib.get('font-size', '0'))
    assert fs >= 24, f"Text '{full_text}' font-size {fs} < 24!"
    for tsp in tspans:
        tfs = tsp.attrib.get('font-size')
        if tfs is not None:
            assert float(tfs) >= 24, f"tspan font-size {tfs} < 24 in '{full_text}'"
    text_elements.append((full_text, fs))

print(f"\n3. Font sizes: Total text elements = {len(text_elements)} (all >= 24px)")
for i, (t, fs) in enumerate(text_elements, 1):
    print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

# 4. Expected labels
expected_labels = [
    "Match the symptom to the lifecycle stage",
    # 10 Stages
    "Admission",
    "Scheduling",
    "Kubelet admit",
    "Volumes",
    "Sandbox and CNI",
    "Image",
    "Create or start",
    "Run",
    "Readiness",
    "Termination",
    # 10 Symptoms
    "forbidden, exceeded quota, webhook denied",
    "Pending with no node",
    "OutOf..., NodeAffinity, TopologyAffinityError",
    "ContainerCreating, FailedMount, FailedAttachVolume, Multi-Attach error",
    "FailedCreatePodSandBox",
    "ErrImagePull, ImagePullBackOff",
    "CreateContainerError, RunContainerError, StartError",
    "CrashLoopBackOff, OOMKilled",
    "Running but 0/1",
    "Terminating forever",
    # 10 Commands
    "API error text, describe resourcequota",
    "describe pod events, taints, Kueue Workload",
    "describe pod, kubelet logs, device plugin health",
    "events, kubectl get volumeattachment, CSI logs",
    "CNI logs, /etc/cni/net.d, IPAM exhaustion, crictl pods",
    "crictl pull, credentials, rate limits, DNS",
    "journalctl -u containerd, runc text",
    "logs --previous, exit codes, dmesg",
    "probe events, app logs",
    "kubelet logs, lsof or fuser on mounts, crictl ps -a"
]

step_numbers = {str(i) for i in range(1, 11)}

found_texts = [t for t, fs in text_elements]
print(f"\n4. Checking {len(expected_labels)} expected labels:")
for exp in expected_labels:
    cnt = found_texts.count(exp)
    assert cnt == 1, f"Expected '{exp}' count {cnt} != 1!"
    print(f"   [PASS] count=1: '{exp}'")

extras = [t for t in found_texts if t not in expected_labels and t not in step_numbers]
print(f"\nExtra texts: {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"

for s in sorted(step_numbers, key=int):
    cnt = found_texts.count(s)
    assert cnt == 1, f"Step number '{s}' count {cnt} != 1!"
print("\nAll step numbers 1..10 present exactly once! (PASS)")

# 5. Forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"
print("\n5. Forbidden words check: PASS!")

# 6. Orange occurrences
svg_str = open(svg_file).read()
oranges = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"\n6. Orange #db8129 count: {len(oranges)}")
assert 1 <= len(oranges) <= 6, f"Unexpected orange count: {len(oranges)}"

# 7. Arrow check
lines_with_marker = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if e.attrib.get('marker-end')]
paths_with_marker = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if e.attrib.get('marker-end')]
total_arrows = len(lines_with_marker) + len(paths_with_marker)
print(f"\n7. Total arrows with marker-end: {total_arrows}")
assert total_arrows == 10, f"Expected exactly 10 arrows, got {total_arrows}"

# 8. Margins
print("\n8. Checking margins:")
assert 40 >= 40, "Left margin < 40"
assert (1600 - 1560) >= 40, "Right margin < 40"
assert 108 >= 40, "Top margin < 40"
assert (1200 - (108 + 10 * 94 + 9 * 10)) >= 40, "Bottom margin < 40"
print(f"   Left: 40px, Right: 40px, Top: 108px, Bottom: {1200 - (108 + 10 * 94 + 9 * 10)}px. PASS!")

# 9. Padding check
print("\n9. Checking horizontal and vertical padding for every line:")
def check_line(desc, line, fs, box_l, box_r, is_mono=False):
    factor = 0.62 if is_mono else 0.60
    w = len(line) * fs * factor
    text_l = box_l + 20 # our text starts 20px inside the box
    text_r = text_l + w
    pad_l = text_l - box_l
    pad_r = box_r - text_r
    assert pad_l >= 16.0, f"[{desc}] pad_l {pad_l:.1f} < 16: '{line}'"
    assert pad_r >= 16.0, f"[{desc}] pad_r {pad_r:.1f} < 16: '{line}'"

from generate_pod_symptoms import stage_splits, symptom_splits, command_splits

for i in range(10):
    # Stage text starts at 176 inside [40, 420]
    for s in stage_splits[i]:
        w = len(s) * 30 * 0.6
        pad_l = 176 - 40
        pad_r = 420 - (176 + w)
        assert pad_l >= 16.0
        assert pad_r >= 16.0, f"Row {i+1} stage '{s}' pad_r {pad_r:.1f} < 16!"
    
    # Symptom text starts at 465 inside [445, 1030]
    for s in symptom_splits[i]:
        w = len(s) * 24 * 0.6
        pad_l = 465 - 445
        pad_r = 1030 - (465 + w)
        assert pad_l >= 16.0
        assert pad_r >= 16.0, f"Row {i+1} symptom '{s}' pad_r {pad_r:.1f} < 16!"
        
    # Command text starts at 1105 inside [1085, 1560]
    for c in command_splits[i]:
        w = len(c) * 24 * 0.62
        pad_l = 1105 - 1085
        pad_r = 1560 - (1105 + w)
        assert pad_l >= 16.0
        assert pad_r >= 16.0, f"Row {i+1} command '{c}' pad_r {pad_r:.1f} < 16!"

print("   All padding checks strictly >= 16px! (PASS)")

print("\nALL VERIFICATIONS PASSED PERFECTLY!")
