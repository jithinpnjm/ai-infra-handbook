import xml.etree.ElementTree as ET
import re

tree = ET.parse("p3_0226_lab_ladder.svg")
root = tree.getroot()

print("==================== AUDIT REPORT ====================")

# 1. XML & ViewBox
assert root.tag.endswith("svg"), "Root is not svg"
first_child = root[0].tag.split('}')[-1]
second_child = root[1].tag.split('}')[-1]
assert first_child == "title", f"Expected title, got {first_child}"
assert second_child == "desc", f"Expected desc, got {second_child}"
assert root[0].text == "The twelve lab steps, from a healthy trace to the faults"
assert root.attrib.get("width") == "1600"
assert root.attrib.get("viewBox") == "0 0 1600 1200"
print("[PASS] XML, Title, Desc, and ViewBox (1600x1200)")

# 2. Text extraction and source labels
all_texts = root.findall('.//{http://www.w3.org/2000/svg}text')
all_tspans = root.findall('.//{http://www.w3.org/2000/svg}tspan')

def get_text_content(el):
    parts = []
    if el.text:
        parts.append(el.text)
    for child in el:
        parts.append(get_text_content(child))
        if child.tail:
            parts.append(child.tail)
    return ''.join(parts)

extracted_texts = []
for t in all_texts:
    full_str = get_text_content(t)
    full_str = re.sub(r'\s+', ' ', full_str).strip()
    extracted_texts.append(full_str)

source_labels = [
    "The twelve lab steps, from a healthy trace to the faults",
    "Read a healthy trace",
    "1 Handshake and teardown: curl to local nginx, label SYN, SYN-ACK, ACK, FIN, export with tshark -z follow",
    "2 Filters: five capture filters for SYN only, RST, a port range, DSCP EF and VLAN, verified with tcpdump -d and hit counts, then the same logic as display filters",
    "Inject a fault and compare",
    "3 Retransmissions and loss: tc qdisc add dev veth1 root netem loss 2%, compare with 0% loss",
    "4 MTU black hole: smaller MTU on a router namespace, drop ICMP type 3 code 4, then fix with MSS clamping",
    "5 Zero window: a server that sleeps before it reads",
    "6 TLS: SSLKEYLOGFILE=/tmp/keys.log curl https://localhost, read SNI and ALPN",
    "7 Offload artefacts: TSO and checksum offload on then off",
    "Wider tools",
    "8 Overlay: VXLAN link as in chapter 2.17, Decode As",
    "9 Ring buffer and trigger: tcpdump -C 10 -W 5 plus a stop script",
    "10 BPF tools: tcplife, tcpconnect, tcpretrans, tcpdrop, three bpftrace one-liners",
    "11 Container capture: nsenter, then docker run --network container:NAME nicolaka/netshoot tcpdump",
    "12 Clean up and delete captures, key log and ring-buffer directory",
    "python3 code/part02/packet_capture_bpf_lab.py checks the byte-offset filters, the 8.13 Mpps rate at 100 Gb/s, ring storage with -s 96, and the two-endpoint comparison",
    "The healthy trace from step 1 is the reference that makes the faulty traces stand out"
]

for sl in source_labels:
    norm_sl = re.sub(r'\s+', ' ', sl).strip()
    matches = [t for t in extracted_texts if norm_sl == t]
    assert len(matches) == 1, f"Expected 1 match for '{norm_sl}', got {len(matches)}"

print(f"[PASS] All {len(source_labels)} source labels match 100% exactly and appear once.")

# 3. No extra text
allowed_numbers = [str(i) for i in range(1, 13)]
for t in extracted_texts:
    if t in [re.sub(r'\s+', ' ', s).strip() for s in source_labels]:
        continue
    assert t in allowed_numbers, f"Unexpected text: '{t}'"

print("[PASS] No extra or invented text elements.")

# 4. Forbidden style words
forbidden = ["orange", "green", "grey", "bold", "monospace", "arrow"]
for t in extracted_texts:
    for f in forbidden:
        assert not re.search(r'\b' + f + r'\b', t.lower()), f"Forbidden word '{f}' in text '{t}'"

print("[PASS] No forbidden style words in any text element.")

# 5. Font size check
font_sizes = []
for el in all_texts + all_tspans:
    fs = el.attrib.get('font-size')
    if fs:
        font_sizes.append(float(fs))

assert min(font_sizes) >= 24, f"Font size < 24: {min(font_sizes)}"
print(f"[PASS] Font sizes: min={min(font_sizes)}px, max={max(font_sizes)}px (all >= 24px)")

# 6. Arrow count check
arrow_paths = []
for elem in root.iter('{http://www.w3.org/2000/svg}path'):
    if "marker-end" in elem.attrib or "marker-start" in elem.attrib:
        arrow_paths.append(elem.attrib)
for elem in root.iter('{http://www.w3.org/2000/svg}line'):
    if "marker-end" in elem.attrib or "marker-start" in elem.attrib:
        arrow_paths.append(elem.attrib)

assert len(arrow_paths) == 0, f"Expected 0 arrows, got {len(arrow_paths)}"
print("[PASS] Arrow count: exactly 0 arrows.")

print("\nALL SYSTEM VERIFICATIONS PASSED WITH ZERO ERRORS!")
