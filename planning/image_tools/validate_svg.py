import re
import xml.etree.ElementTree as ET

# 1. Parse XML
tree = ET.parse("output.svg")
root = tree.getroot()
print("1. XML parsing: SUCCESS")

# 2. Check title and desc are first children
first_two = [elem.tag.split("}")[-1] for elem in list(root)[:2]]
print(f"2. First children: {first_two}")
assert first_two == ["title", "desc"], "First two elements must be title and desc!"

# 3. Check width, height, viewBox
w = root.attrib.get("width")
h = root.attrib.get("height")
vb = root.attrib.get("viewBox")
print(f"3. Dimensions: width={w}, height={h}, viewBox='{vb}'")
assert w == "1600" and h == "1200" and vb == "0 0 1600 1200"

# 4. Extract all text content from the SVG
def get_all_text_elements(elem):
    texts = []
    for t in elem.iter():
        if t.tag.endswith("text") or t.tag.endswith("tspan"):
            if t.text and t.text.strip():
                texts.append((t.text.strip(), t.attrib))
    return texts

all_texts = get_all_text_elements(root)
print(f"4. Found {len(all_texts)} text/tspan nodes.")

# Let's reconstruct full text lines and check font sizes
min_font_size = 999
for text, attr in all_texts:
    fs = attr.get("font-size")
    if fs:
        val = float(re.sub(r"[^\d.]", "", fs))
        min_font_size = min(min_font_size, val)
print(f"5. Minimum font size across all text elements: {min_font_size}px")
assert min_font_size >= 24, f"Found text smaller than 24px: {min_font_size}px!"

# 5. Check exact labels from prompt
exact_labels = [
    "Why a published Docker port ignores your firewall rule",
    "Client on the office network or anywhere",
    "Host NIC",
    "netfilter chains",
    "Docker's own NAT and FORWARD rules (DOCKER chain) are inserted ahead of the rules managed by ufw or firewalld",
    "container port 80",
    "published port 8080 answers from anywhere",
    "ufw or firewalld rule that should block the port",
    "restrict a port with the DOCKER-USER chain",
    "bind the port to a specific address (for example 127.0.0.1:8080:80)",
    "if a published port must stay private on a shared host, restrict it in DOCKER-USER before you publish it",
    "Docker network modes",
    "bridge: private subnet, veth per container, NAT outbound, -p publishes via DNAT; user-defined bridges add DNS-based name resolution and isolation",
    "host: shares the host namespace, no isolation, no NAT, best performance, ports conflict with host: NCCL or HPC containers",
    "none: only loopback",
    "container:NAME: shares another container's namespace (how a Kubernetes pod works)",
    "overlay: VXLAN across Docker hosts (Swarm)",
    "macvlan or ipvlan: container on the physical network",
    "CNM: sandbox (the namespace config), endpoint (the attachment, typically a veth), network (a group of endpoints); local drivers bridge, host, none, macvlan, ipvlan; global driver overlay needs a key-value store",
    "default subnet 172.17.0.0/16 may overlap corporate or VPN ranges: set default-address-pools in /etc/docker/daemon.json",
    "docker network ls; docker network inspect bridge; iptables -t nat -S DOCKER; bridge fdb show br docker0",
    "Docker inserts its own rules ahead of the firewall's rules"
]

with open("output.svg") as f:
    svg_raw = f.read()

stripped = re.sub(r"<[^>]+>", " ", svg_raw)
stripped = re.sub(r"\s+", " ", stripped).strip()

print("\n6. Checking presence of all 22 exact labels:")
missing = []
for label in exact_labels:
    norm_label = re.sub(r"\s+", " ", label).strip()
    if norm_label in stripped:
        print(f"  FOUND: {norm_label[:50]}...")
    else:
        print(f"  MISSING: {norm_label}")
        missing.append(norm_label)

assert len(missing) == 0, f"Missing labels: {missing}"

# 7. Check color orange usage
orange_matches = re.findall(r'#db8129', svg_raw, re.IGNORECASE)
print(f"\n7. Occurrences of #db8129 (orange): {len(orange_matches)}")
assert len(orange_matches) == 3, f"Expected exactly 3 occurrences of #db8129 (marker, line, text), found {len(orange_matches)}"

# 8. Check marker IDs
markers_defined = set(re.findall(r'<marker[^>]+id="([^"]+)"', svg_raw))
markers_used = set(re.findall(r'marker-end="url\(#([^)]+)\)"', svg_raw))
print(f"\n8. Markers defined: {markers_defined}")
print(f"   Markers used: {markers_used}")
for m in markers_used:
    assert m in markers_defined, f"Marker #{m} used but not defined!"

# 9. Check style words
style_words = ["orange", "green", "grey", "gray", "bold", "monospace", "arrow"]
bad_matches = []
for elem in root.iter():
    if elem.tag.endswith("text") or elem.tag.endswith("tspan"):
        if elem.text:
            for word in style_words:
                if re.search(r'\b' + word + r'\b', elem.text, re.IGNORECASE):
                    bad_matches.append((elem.tag, elem.text, word))
print(f"\n9. Style instruction words in visible text: {len(bad_matches)}")
assert len(bad_matches) == 0, f"Found style words: {bad_matches}"

print("\n==========================================")
print("ALL TESTS AND QUALITY CHECKS PASSED 100%!!")
print("==========================================")
