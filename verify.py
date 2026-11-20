import xml.etree.ElementTree as ET
import re

tree = ET.parse("output.svg")
root = tree.getroot()

# Check font sizes
ns = {'svg': 'http://www.w3.org/2000/svg'}
all_texts = root.findall('.//svg:text', ns)
print(f"Total text elements: {len(all_texts)}")

font_sizes = []
for t in all_texts:
    fs = int(t.attrib.get('font-size', '0'))
    text_content = "".join(t.itertext())
    print(f"Text [{fs}px]: '{text_content}'")
    if fs < 24:
        print(f"ERROR: Font size {fs} < 24px in text: {text_content}")

source_labels = [
    "Inside host cannot reach Internet",
    "Has IP, gateway, DNS?",
    "(DHCP / static)",
    "DHCP: tcpdump 67/68, relay, pool, VLAN, rogue server",
    "ping gateway ok?",
    "L2/ARP problems (chapter 2.3)",
    "Gateway forwards?",
    "ip_forward, FORWARD policy",
    "Enable forwarding; allow in FORWARD chain",
    "tcpdump on outside iface:",
    "source translated?",
    "Missing/incorrect SNAT/masquerade rule (wrong -o, -s); rule order",
    "Upstream routing/filtering; asymmetric path; wrong outside IP",
    "conntrack drop (table full, timeouts), rp_filter, FORWARD rules"
]

edge_labels = [
    "no",
    "yes",
    "no",
    "yes",
    "no",
    "yes",
    "source still private",
    "translated, no reply",
    "reply arrives, not delivered"
]

print("\n--- Verifying Source Labels ---")
full_text = " ".join("".join(t.itertext()) for t in all_texts)
for sl in source_labels:
    # simplify whitespace
    clean_sl = " ".join(sl.split())
    # check if words match
    words = clean_sl.split()
    found = all(w in full_text for w in words)
    print(f"[{found}] '{clean_sl}'")
    if not found:
        print(f"  ERROR: Missing in svg: {clean_sl}")

print("\n--- Verifying Edge Labels ---")
for el in edge_labels:
    found = el in full_text
    print(f"[{found}] '{el}'")

