import xml.etree.ElementTree as ET
import re

tree = ET.parse("test_lab_ladder.svg")
root = tree.getroot()

print("--- Check 1: XML Parsing & Structure ---")
assert root.tag.endswith("svg"), "Root is not svg"
first_child = root[0].tag.split('}')[-1]
second_child = root[1].tag.split('}')[-1]
print(f"First child: <{first_child}>, Second child: <{second_child}>")
assert first_child == "title", f"Expected title, got {first_child}"
assert second_child == "desc", f"Expected desc, got {second_child}"

title_text = root[0].text
print(f"Title text: '{title_text}'")
assert title_text == "The twelve lab steps, from a healthy trace to the faults"

width = root.attrib.get("width")
height = root.attrib.get("height")
viewBox = root.attrib.get("viewBox")
print(f"width={width}, height={height}, viewBox={viewBox}")
assert width == "1600"
assert viewBox == "0 0 1600 1200"

print("\n--- Check 2: Font Sizes ---")
all_texts = root.findall('.//{http://www.w3.org/2000/svg}text')
all_tspans = root.findall('.//{http://www.w3.org/2000/svg}tspan')

font_sizes = []
for el in all_texts + all_tspans:
    fs = el.attrib.get('font-size')
    if fs:
        font_sizes.append((float(fs), el.text))

print(f"Total elements with font-size: {len(font_sizes)}")
min_fs = min(fs for fs, _ in font_sizes)
max_fs = max(fs for fs, _ in font_sizes)
print(f"Min font-size: {min_fs}px, Max font-size: {max_fs}px")
assert min_fs >= 24, f"Found font size {min_fs} < 24!"

print("\n--- Check 3: Extract Text & Verify Source Labels ---")
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
    print(f"Label: '{norm_sl[:45]}...' -> Matches: {len(matches)}")
    assert len(matches) == 1, f"Expected exactly 1 match for '{norm_sl}', found {len(matches)}!"

print("\n--- Check 4: Extra text elements check ---")
# The only texts should be: title, 3 groups, prestep, bottom_bar, 12 steps, and numbers 1..12
expected_numbers = [str(i) for i in range(1, 13)]
for t in extracted_texts:
    if t in [re.sub(r'\s+', ' ', s).strip() for s in source_labels]:
        continue
    elif t in expected_numbers:
        continue
    else:
        print(f"UNEXPECTED TEXT: '{t}'")
        assert False, f"Unexpected text: {t}"

print("All extracted text elements strictly accounted for!")

print("\n--- Check 5: Forbidden Style Words Check ---")
forbidden = ["orange", "green", "grey", "bold", "monospace", "arrow"]
for t in extracted_texts:
    for f in forbidden:
        if re.search(r'\b' + f + r'\b', t.lower()):
            print(f"ERROR: Forbidden word '{f}' found in text '{t}'!")
            assert False, f"Forbidden word '{f}' found in text '{t}'"

print("No forbidden style words found in any text element!")

print("\n--- Check 6: Arrow Count Check ---")
arrow_paths = []
for elem in root.iter('{http://www.w3.org/2000/svg}path'):
    if "marker-end" in elem.attrib or "marker-start" in elem.attrib:
        arrow_paths.append(elem.attrib)
for elem in root.iter('{http://www.w3.org/2000/svg}line'):
    if "marker-end" in elem.attrib or "marker-start" in elem.attrib:
        arrow_paths.append(elem.attrib)

print(f"Total arrows: {len(arrow_paths)} (source has 0 arrows)")
assert len(arrow_paths) == 0, f"Expected 0 arrows, found {len(arrow_paths)}"

print("\nALL AUTOMATED VERIFICATION CHECKS PASSED PERFECTLY!")
