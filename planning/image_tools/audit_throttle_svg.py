import xml.etree.ElementTree as ET
import re
import subprocess

tree = ET.parse("candidate_throttling.svg")
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
assert len(extras) == 0, f"Found unexpected extras: {extras}"

print("\n=== ALL ASSERTIONS PASSED ===")

