import re
import xml.etree.ElementTree as ET

tree = ET.parse("output.svg")
root = tree.getroot()

# Check namespace and tags
assert root.tag.endswith("svg"), "Root must be svg"
assert root.attrib.get("viewBox") == "0 0 1600 1200", f"viewBox is {root.attrib.get('viewBox')}"
assert root.attrib.get("width") == "1600"
assert root.attrib.get("height") == "1200"

# First children must be <title> and <desc>
first_two = [elem.tag.split("}")[-1] for elem in list(root)[:2]]
assert first_two == ["title", "desc"], f"First two elements must be title and desc, got: {first_two}"

# Extract all text from SVG
source_labels = [
    "Two state-table limits that look like random timeouts: SNAT ports and conntrack",
    "Case 1: SNAT port exhaustion",
    "about 5,000 containers connect through one NAT IP to one database IP and port",
    "one source IP has about 60,000 usable ephemeral ports per destination IP and port; each connection to that one database needs its own source port on the gateway",
    "ports run out, new connections get no mapping and time out; the database is healthy, CPU is low, dmesg shows no conntrack drops",
    "a car park with a fixed number of spaces: the traffic is not heavy but all the spaces are taken",
    "add NAT gateway IPs and ports (Cloud NAT port allocation), use a pooler such as PgBouncer, shorten TIME_WAIT, reuse connections",
    "count the tuple dimensions: source IP, destination IP and port",
    "Case 3: Conntrack table full",
    "busy Kubernetes nodes, intermittent timeouts for new connections, CPU and bandwidth fine",
    "dmesg: nf_conntrack: table full, dropping packet; conntrack -C equals nf_conntrack_max; conntrack -S shows insert_failed",
    "established timeout of 5 days keeps dead flows forever; table too small for the load",
    "established connections keep working, only new ones fail",
    "raise the max and hash size, lower timeouts, find chatty clients, notrack for DNS and east-west flows",
    "Capacity limits in state tables look like random packet loss"
]

# Check each <text> element and reconstruct its content
text_elements = root.findall(".//{http://www.w3.org/2000/svg}text")
found_labels = []

for te in text_elements:
    # Gather tspans or direct text
    tspans = te.findall("{http://www.w3.org/2000/svg}tspan")
    if tspans:
        full_text = " ".join([ts.text.strip() for ts in tspans if ts.text])
    else:
        full_text = te.text.strip() if te.text else ""
    found_labels.append(full_text)
    
    # Check font size
    fsize = te.attrib.get("font-size")
    assert fsize is not None, f"Missing font-size on {full_text}"
    fsize_val = float(fsize)
    assert fsize_val >= 24, f"Font size {fsize_val} < 24 px on text: {full_text}"

print(f"Total <text> elements in SVG: {len(found_labels)}")
print("Found labels:")
for i, l in enumerate(found_labels, 1):
    print(f"  {i}. {l}")

# Check exact 1-to-1 match with source_labels
assert len(found_labels) == len(source_labels), f"Count mismatch: found {len(found_labels)}, expected {len(source_labels)}"

for sl in source_labels:
    assert sl in found_labels, f"Missing source label: {sl}"
    count = found_labels.count(sl)
    assert count == 1, f"Label duplicated ({count} times): {sl}"

for fl in found_labels:
    assert fl in source_labels, f"Invented label found: {fl}"

# Check for banned style words like 'orange', 'green', 'grey', 'bold', 'monospace', 'arrow' appearing as text
forbidden_style_words = ["orange", "green", "grey", "arrow"]
for fl in found_labels:
    words = [w.lower().strip(".,;:()") for w in fl.split()]
    for fsw in forbidden_style_words:
        assert fsw not in words, f"Forbidden style word '{fsw}' found in text: {fl}"

print("\n--- ALL VALIDATION CHECKS PASSED PERFECTLY! ---")
