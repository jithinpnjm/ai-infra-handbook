import re
import xml.etree.ElementTree as ET

tree = ET.parse("output.svg")
root = tree.getroot()

# 1. Structure: first children must be title and desc
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. First child: <{first_tag}>, Second child: <{second_tag}>")
assert first_tag == 'title', f"First child must be title, got {first_tag}"
assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"

# 2. Canvas dimensions
width = root.get('width')
height = root.get('height')
viewBox = root.get('viewBox')
print(f"2. Canvas: width={width}, height={height}, viewBox={viewBox}")
assert width == "1600"
assert viewBox.startswith("0 0 1600 ")
vb_parts = [float(x) for x in viewBox.split()]
assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
assert 900 <= vb_parts[3] <= 1200
assert int(height) == int(vb_parts[3])

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

# 4. Expected labels
expected_labels = [
    "Which node tool answers which question",
    "What does the runtime think exists: crictl pods, crictl ps -a, crictl inspectp, crictl inspect (pid, exit code, mounts, resources), crictl logs, crictl stats; ctr -n k8s.io tasks ls",
    "What do the kubelet and runtime say: journalctl -u kubelet -u containerd --since -30 min",
    "Which namespaces does this process live in: lsns -p PID, ls -l /proc/PID/ns, /proc/PID/cgroup; get PID with crictl inspect template info.pid",
    "What is the pod network doing: nsenter -t PID -n ip addr, ip route, ss -tnap, tcpdump",
    "What does the pod filesystem look like: nsenter -t PID -m ls, cat /proc/mounts, df -h",
    "Kernel network counters: ip -s link, nstat, conntrack -S, ethtool -S, iptables-save, nft list ruleset, ipvsadm -Ln",
    "Storage: findmnt, lsblk, df -hT, df -i, iostat -x, fio",
    "CPU, memory, I/O of the process: top -H, pidstat, perf, strace, py-spy, gdb",
    "GPU and fabric: nvidia-smi, dcgmi, journalctl -k grep Xid, lspci -vv, ibstat, all_reduce_perf"
]

found_texts = [t for t, fs in text_elements]

print(f"\n4. Checking {len(expected_labels)} expected labels against {len(found_texts)} found:")
all_ok = True
for exp in expected_labels:
    cnt = found_texts.count(exp)
    ok = (cnt == 1)
    if not ok:
        all_ok = False
    print(f"   [{'OK' if ok else 'FAIL'}] count={cnt}: '{exp}'")

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

# 6. Check colors
with open("output.svg") as f:
    raw = f.read()

assert "#f5f8f5" in raw, "Background #f5f8f5 missing"
assert "#303a36" in raw, "Text #303a36 missing"
assert "#207448" in raw, "Main green #207448 missing"
assert "#e8f1ea" in raw, "Light green panels #e8f1ea missing"
assert "#db8129" in raw, "Orange #db8129 missing"
print("\n7. Color palette check: PASS!")

orange_matches = re.findall(r'#db8129', raw)
print(f"   Orange #db8129 count: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 4, f"Orange count {len(orange_matches)} out of bounds!"

# 7. Check arrows: source has 0 arrows, so output must have 0 arrows
lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
total_arrows = len(lines) + len(paths)
print(f"\n8. Total arrows with marker-end: {total_arrows} (expected 0)")
assert total_arrows == 0, f"Expected 0 arrows, got {total_arrows}"

print("\n=== ALL STRICT SPEC AUDIT CHECKS PASSED PERFECTLY! ===")
