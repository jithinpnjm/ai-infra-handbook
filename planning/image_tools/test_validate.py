import xml.etree.ElementTree as ET
import re

tree = ET.parse("perfect.svg")
root = tree.getroot()

# Check XML namespace & tag
print("Root tag:", root.tag)

# Check width, height, viewBox
print("Width:", root.attrib.get("width"))
print("Height:", root.attrib.get("height"))
print("viewBox:", root.attrib.get("viewBox"))

# Check title and desc are first children
first_two = [elem.tag.split("}")[-1] for elem in list(root)[:2]]
print("First two elements:", first_two)
assert first_two == ["title", "desc"], f"Expected ['title', 'desc'], got {first_two}"

# Check forbidden style instruction words in any text/tspan content
style_words = ["orange", "green", "grey", "monospace", "arrow"]
# Note: "bold" shouldn't appear as text content, only attribute
all_text_elements = root.findall(".//{http://www.w3.org/2000/svg}text")
all_tspan_elements = root.findall(".//{http://www.w3.org/2000/svg}tspan")

print(f"Total <text> elements: {len(all_text_elements)}")
print(f"Total <tspan> elements: {len(all_tspan_elements)}")

forbidden_found = []
for el in list(all_text_elements) + list(all_tspan_elements):
    txt = (el.text or "").strip()
    for w in style_words:
        if re.search(r'\b' + w + r'\b', txt, re.IGNORECASE):
            forbidden_found.append((w, txt))

print("Forbidden words found in text content:", forbidden_found)
assert len(forbidden_found) == 0, f"Found forbidden style words: {forbidden_found}"

# Check font sizes
font_sizes = []
for el in list(all_text_elements) + list(all_tspan_elements):
    fs = el.attrib.get("font-size")
    if fs:
        font_sizes.append(int(fs))
print("Font sizes used:", set(font_sizes))
assert min(font_sizes) >= 24, f"Found font size smaller than 24: {min(font_sizes)}"

# Check exact source labels match
source_labels = [
    "Symptom to first guess, and the second source that confirms it",
    "Pattern in the capture",
    "First guess",
    "Confirm with",
    "SYN at the server, no SYN-ACK back",
    "server firewall or a full listen queue",
    "firewall counters, nstat ListenOverflows, solisten",
    "SYN-ACK at the server but not at the client",
    "return path, asymmetric route or NAT",
    "conntrack, route check",
    "Data with repeated retransmissions and no ICMP",
    "MTU black hole or a stateful device that drops",
    "path MTU, firewall counters",
    "Duplicate ACKs and SACK",
    "loss on the path",
    "ss -ti, tcpretrans",
    "RST from a different TTL",
    "a middlebox",
    "compare TTL against normal peer packets",
    "Long idle then reset",
    "a timeout",
    "conntrack and NAT timers",
    "Gaps of exactly 200 ms or 1 s",
    "RTO or delayed ACK",
    "tcpstates, ss -ti",
    "DNS answers after 5 s",
    "resolver timeout",
    "repeat the query",
    "ClientHello then nothing",
    "TLS interception or an MTU problem; post-quantum key shares make ClientHellos large",
    "check path MTU",
    "Pause frames at multi-kHz rates on one priority",
    "a PFC storm",
    "switch counters per priority",
    "ECN-marked packets arrive but no CNP comes back",
    "NIC DCQCN probably misconfigured",
    "NIC settings",
    "A guess that a second source agrees with is a conclusion; one nothing else supports is only a hypothesis"
]

# Extract all text from each <text> element (joining tspans)
extracted_texts = []
for t in all_text_elements:
    parts = []
    if t.text and t.text.strip():
        parts.append(t.text.strip())
    for ts in t.findall("{http://www.w3.org/2000/svg}tspan"):
        if ts.text and ts.text.strip():
            parts.append(ts.text.strip())
    extracted_texts.append(" ".join(parts))

print(f"\nExtracted {len(extracted_texts)} visual text strings.")
missing = []
for sl in source_labels:
    if sl not in extracted_texts:
        missing.append(sl)

print("Missing labels:", missing)
assert len(missing) == 0, f"Missing source labels: {missing}"

# Check for duplicates or extra labels
print("Checking for duplicate or unexpected labels...")
from collections import Counter
counts = Counter(extracted_texts)
duplicates = [k for k, v in counts.items() if v > 1]
print("Duplicates:", duplicates)
assert len(duplicates) == 0, f"Duplicate labels found: {duplicates}"

extras = [txt for txt in extracted_texts if txt not in source_labels]
print("Extra labels:", extras)
assert len(extras) == 0, f"Extra labels found: {extras}"

print("\nALL VALIDATION CHECKS PASSED PERFECTLY!")
