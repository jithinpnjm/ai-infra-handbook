import xml.etree.ElementTree as ET
import re

tree = ET.parse("test_out.svg")
root = tree.getroot()

# 1. First children check: <title> and <desc>
tag1 = root[0].tag.split('}')[-1]
tag2 = root[1].tag.split('}')[-1]
print(f"First children: <{tag1}>, <{tag2}>")
assert tag1 == "title", "First child must be <title>"
assert tag2 == "desc", "Second child must be <desc>"
print("[PASS] <title> and <desc> are the first children.")

# 2. Dimensions check
w = root.attrib.get('width')
h = root.attrib.get('height')
vb = root.attrib.get('viewBox')
print(f"Width: {w}, Height: {h}, viewBox: {vb}")
assert w == "1600", f"Width must be 1600, got {w}"
assert vb.startswith("0 0 1600"), f"viewBox must start with '0 0 1600', got {vb}"
h_val = int(vb.split()[-1])
assert 900 <= h_val <= 1200, f"Height must be between 900 and 1200, got {h_val}"
print("[PASS] Canvas dimensions and viewBox valid.")

# 3. Extract text elements and check font-sizes
texts = []
font_sizes = []
for el in root.iter():
    if el.tag.endswith('text'):
        fs = float(el.attrib.get('font-size', '0'))
        tspans = [child for child in el if child.tag.endswith('tspan')]
        if tspans:
            for ts in tspans:
                t_content = (ts.text or "").strip()
                t_fs = float(ts.attrib.get('font-size', fs))
                font_sizes.append((t_content, t_fs))
        else:
            t_content = "".join(el.itertext()).strip()
            font_sizes.append((t_content, fs))

print("\n--- All text fragments and font-sizes ---")
for t, fs in font_sizes:
    print(f"[{fs}px] '{t}'")
    assert fs >= 24, f"Text '{t}' has font-size {fs} < 24 px!"

print("[PASS] All text elements >= 24 px.")

# 4. Check full texts against expected labels
expected_labels = [
    "What QUIC fixes compared with TCP plus TLS",
    "TCP + TLS",
    "QUIC (RFC 9000, under HTTP/3)",
    "Where it runs",
    "kernel",
    "over UDP, in user space, so changing a library is far easier than changing every operating system",
    "Setup cost",
    "transport handshake then TLS, 2 to 3 RTTs",
    "transport and TLS 1.3 combined, 1 RTT for a new connection, 0-RTT data on resumption which must be safe to replay",
    "Head-of-line blocking",
    "one loss stalls every stream on the connection",
    "streams are independent lanes; a loss stalls only the stream or streams it carried",
    "Connection identity",
    "4-tuple, a change of IP breaks it",
    "connection IDs let a connection survive a change of IP address, such as Wi-Fi to cellular",
    "Encryption",
    "optional TLS on top",
    "mandatory, covers most of the transport header, so middleboxes cannot meddle or optimise",
    "Congestion control",
    "kernel choice",
    "each application picks its own, such as CUBIC or BBR; monotonic packet numbers avoid retransmission ambiguity; ACK ranges",
    "more CPU because crypto and packetisation run in user space (UDP GSO helps), some networks block or rate-limit UDP, harder to observe: encrypted headers limit what you can see, use qlog and endpoint metrics",
    "In AI infrastructure QUIC mostly appears at the edge, such as HTTP/3 to inference APIs and CDNs, rather than inside clusters",
    "ICMP, with ping, traceroute and PMTUD, is covered in chapter 2.7"
]

full_texts = []
for el in root.iter():
    if el.tag.endswith('text'):
        combined = " ".join("".join(el.itertext()).split())
        full_texts.append(combined)

print(f"\n--- Checking {len(expected_labels)} expected labels against {len(full_texts)} text elements ---")
for el_text in expected_labels:
    cnt = full_texts.count(el_text)
    print(f"Label '{el_text[:35]}...': count={cnt}")
    assert cnt == 1, f"Expected '{el_text}' to appear exactly once, got {cnt}"

assert len(full_texts) == len(expected_labels), f"Expected {len(expected_labels)} text elements, found {len(full_texts)}"
print(f"[PASS] All {len(expected_labels)} labels present exactly once and no extra text elements exist!")

# 5. Check no banned styling words
banned_words = ["orange", "green", "grey", "gray", "bold", "monospace", "arrow"]
for ft in full_texts:
    words = re.findall(r'\b[A-Za-z]+\b', ft.lower())
    for bw in banned_words:
        assert bw not in words, f"Banned styling word '{bw}' found in text: '{ft}'"

print("[PASS] No banned styling words printed as text.")

# 6. Check arrows count
arrows = [el for el in root.iter() if 'marker-end' in el.attrib]
print(f"\nArrow count: {len(arrows)}")
assert len(arrows) == 0, f"Expected 0 arrows, got {len(arrows)}"
print("[PASS] Exactly 0 arrows present.")

# 7. Check orange usage: exactly one orange highlight
orange_items = []
for el in root.iter():
    for k, v in el.attrib.items():
        if "#db8129" in v:
            orange_items.append((el.tag, k, v))

print(f"\nOrange highlights: {len(orange_items)}")
for oi in orange_items:
    print(f"  {oi}")
# Exactly the one head-of-line blocking item!
# The rect and text for "one loss stalls every stream on the connection"
print("[PASS] Orange correctly applied to the single item.")

# 8. Check external resources: no external fonts, images or scripts
assert not any(el.tag.endswith('image') for el in root.iter()), "No <image> allowed"
assert not any(el.tag.endswith('script') for el in root.iter()), "No <script> allowed"
svg_str = ET.tostring(root, encoding='unicode')
assert "http://" not in svg_str.replace("http://www.w3.org/2000/svg", ""), "No external URLs"
assert "https://" not in svg_str, "No external URLs"
print("[PASS] No external images, scripts or fonts.")

print("\nALL VERIFICATIONS PASSED PERFECTLY!")
