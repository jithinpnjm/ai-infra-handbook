import re, subprocess, pathlib
import xml.etree.ElementTree as ET

svg_code = pathlib.Path("test_output.svg").read_text()

# 1. Parse XML
root = ET.fromstring(svg_code)
print("1. Valid XML: PASS")

# 2. Check title and desc
children = list(root)
assert children[0].tag.endswith('title'), "First child must be title"
assert children[1].tag.endswith('desc'), "Second child must be desc"
print("2. Title and desc as first children: PASS")

# 3. Check font sizes
font_sizes = [int(s) for s in re.findall(r'font-size="(\d+)"', svg_code)]
print(f"Font sizes used: {sorted(set(font_sizes))}")
assert all(fs >= 24 for fs in font_sizes), f"Found font size < 24: {[f for f in font_sizes if f < 24]}"
print("3. Font sizes >= 24px: PASS")

# 4. Check banned style instruction words as text
banned = ["orange", "green", "grey", "gray", "bold", "monospace", "arrow"]
# Extract all text elements
all_texts = []
for t in root.iter('{http://www.w3.org/2000/svg}text'):
    txt = " ".join("".join(t.itertext()).split())
    if txt: all_texts.append(txt)

print(f"Total text elements: {len(all_texts)}")
for t in all_texts:
    # check each word
    words = [w.strip("(),:;.'\"").lower() for w in t.split()]
    for b in banned:
        if b in words:
            print(f"WARNING: Banned style word '{b}' found in text: '{t}'")

# 5. Check labels from prompt
required_labels = [
    "What a network namespace owns",
    "host",
    "red",
    "default",
    "own interfaces",
    "own IP addresses",
    "own routing tables",
    "own ARP and ND neighbour tables",
    "own netfilter rules",
    "own conntrack table",
    "own /proc/net",
    "two containers can both serve on port 8080: each has its own port space",
    "ip netns add red",
    "ip netns exec red ip link",
    "(only a down loopback at first)",
    "ip -n red link set lo up",
    "nsenter -t <pid> -n ip addr",
    "enters a container namespace by PID"
]

full_svg_text = " ".join(all_texts)
for req in required_labels:
    assert req in full_svg_text, f"Missing label: '{req}'"
    print(f"  [FOUND] '{req}'")

print("All required labels present: PASS")

# 6. Check Chrome render
d = pathlib.Path('/tmp/svgcheck')
d.mkdir(exist_ok=True)
H = 1200
res = subprocess.run([
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '--headless=new',
    '--disable-gpu',
    '--hide-scrollbars',
    f'--window-size=1600,{H}',
    f'--screenshot={d}/n25-netns.png',
    f'file://{pathlib.Path("test_output.svg").resolve()}'
], capture_output=True)
print("Chrome returncode:", res.returncode)
print(f"Rendered PNG saved to {d}/n25-netns.png")
