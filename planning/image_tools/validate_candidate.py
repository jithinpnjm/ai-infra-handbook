import re
import xml.etree.ElementTree as ET
import pathlib

tree = ET.parse("test_candidate.svg")
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
assert width == "1600"
assert viewBox.startswith("0 0 1600 ")
vb_parts = [float(x) for x in viewBox.split()]
assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
assert 900 <= vb_parts[3] <= 1200
assert int(height) == int(vb_parts[3])

# 3. Check font-size >= 24
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
    "Socket buffers: what to raise, what to leave alone, and why",
    "send buffer: unacknowledged data on the send side",
    "receive buffer: data the application has not read yet",
    "Linux autotunes both within limits",
    "net.ipv4.tcp_rmem and tcp_wmem: min default max in bytes, for example 4096 131072 6291456",
    "net.core.rmem_max and wmem_max: cap for explicit SO_RCVBUF and SO_SNDBUF",
    "net.ipv4.tcp_mem: system-wide pages, low, pressure, high",
    "tcp_moderate_rcvbuf: receive autotuning (1)",
    "tcp_notsent_lowat: limit unsent data queued in the send buffer, reduces latency and bufferbloat, for example 131072",
    "For 10 to 100 Gb/s long paths raise the maxima",
    "tcp_rmem 4096 131072 134217728",
    "tcp_wmem 4096 65536 134217728",
    "rmem_max = wmem_max = 134217728",
    "Do not",
    "setting SO_RCVBUF or SO_SNDBUF in an application disables autotuning for that socket, almost always a mistake",
    "huge buffers on short-RTT paths add memory pressure and queueing delay: bufferbloat",
    "a 128 MB buffer on each of thousands of connections exhausts RAM; tcp_mem guards against it",
    "Same rack 100 Gb/s 20 microseconds: 250 KB; Same DC 100 Gb/s 100 microseconds: 1.25 MB; Metro 10 Gb/s 2 ms: 2.5 MB; Cross-continent 10 Gb/s 70 ms: 87.5 MB; Intercontinental 10 Gb/s 180 ms: 225 MB",
    "Choose buffer sizes from the BDP of the path you use, and leave autotuning on"
]

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
        print(f"   [OK] count=1: '{exp[:40]}...'")

assert all_ok, "Some expected labels failed count == 1 check!"

extras = [t for t in found_texts if t not in expected_labels]
print(f"\nExtra texts: {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"

# 5. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"

print("\n5. No forbidden words found! (PASS)")

# 6. Check orange count
svg_str = pathlib.Path("test_candidate.svg").read_text()
orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 6, f"Unexpected orange count: {len(orange_matches)}"

# 7. Check arrows count
markers = root.findall('.//{http://www.w3.org/2000/svg}marker')
print(f"\n7. Markers count: {len(markers)}")

print("\nALL AUTOMATED TESTS PASSED PERFECTION!")
