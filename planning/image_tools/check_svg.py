import re
import xml.etree.ElementTree as ET

tree = ET.parse("test_output.svg")
root = tree.getroot()

# Collect all text in SVG
all_text_elements = root.findall(".//{http://www.w3.org/2000/svg}text")

def get_text_recursive(elem):
    text = elem.text or ""
    for child in elem:
        text += " " + get_text_recursive(child)
        if child.tail:
            text += " " + child.tail
    return " ".join(text.split())

full_svg_text = " ".join([get_text_recursive(t) for t in all_text_elements])

labels = [
    "Splitting a slow request into parts, with the expected values",
    "Name lookup (DNS): dig +stats, can time out for tens of seconds",
    "Path round trip: ping, mtr, rtt in ss -ti",
    "TCP connection (handshake): tcpconnlat, curl -w time_connect",
    "First byte: server think time plus the RTT: curl -w time_starttransfer",
    "Per-request application latency: application tracing",
    "Connection life span: short-lived connections multiply the handshake cost",
    "curl -w timing variables, dig +stats, tcpconnlat, tcpdump timestamps, the rtt field from ss -ti, mtr, application tracing",
    "Expected values",
    "rack-local 100G: tens of microseconds",
    "same-DC: 0.2 to 0.6 ms",
    "cross-continent: 40 to 180 ms",
    "a user says the internal app is slow, but only from one office: split the wait into parts and find which one grows before changing anything",
    "File copy starts fast then sits at a fixed speed: ss -ti shows rwnd_limited as a large share of time, the receiver's window is holding the sender back; fix the receiving side (larger receive buffer or faster reads)",
    "rwnd_limited, cwnd_limited, sndbuf_limited, app_limited tell you which factor bounds each connection",
    "Break latency into parts, and find the part that grows"
]

print("--- LABEL VERIFICATION ---")
for l in labels:
    # normalize spaces and check
    norm_l = " ".join(l.split())
    # check if each token sequence exists in order
    words = norm_l.split()
    pattern = r"\s*".join([re.escape(w) for w in words])
    match = re.search(pattern, full_svg_text)
    if match:
        print(f"MATCH: {l[:50]}...")
    else:
        print(f"FAILED TO MATCH: {l}")

print("\n--- CHECK FOR FORBIDDEN STYLE WORDS AS LITERAL TEXT ---")
for word in ["orange", "green", "grey", "gray", "bold", "monospace"]:
    matches = re.findall(rf"\b{word}\b", full_svg_text, re.IGNORECASE)
    if matches:
        print(f"FORBIDDEN WORD FOUND in text: {word}")
    else:
        print(f"Clean: no literal '{word}' in text.")

print("\n--- FONT SIZE AUDIT ---")
# Check all font-size attributes
min_font = 999
for elem in root.iter():
    fs = elem.attrib.get("font-size")
    if fs:
        fs_val = float(fs)
        if fs_val < min_font:
            min_font = fs_val
        if fs_val < 24:
            print(f"ERROR: font size {fs_val} < 24 px in {elem.tag} {elem.attrib}")

print(f"Minimum font size found: {min_font} px (must be >= 24)")
