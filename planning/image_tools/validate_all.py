import xml.etree.ElementTree as ET
import re

tree = ET.parse("node_lifecycle.svg")
root = tree.getroot()

print("XML is well-formed.")

# Check all text elements
text_elements = root.findall(".//{http://www.w3.org/2000/svg}text")
print(f"Total text elements: {len(text_elements)}")

font_sizes = []
for t in text_elements:
    fs = int(t.attrib.get("font-size", 0))
    font_sizes.append(fs)
    text_content = "".join(t.itertext()).strip()
    if fs < 24:
        print(f"ERROR: Text element '{text_content}' has font-size {fs} < 24!")

print(f"Min font-size: {min(font_sizes)}, Max font-size: {max(font_sizes)}")

# Source labels:
SOURCE_TRANSITIONS = [
    "bare metal/VM created (image, BMC/PXE or cloud API)",
    "OS, kernel, drivers, runtime, kubelet (Ansible/image)",
    "join cluster tainted \"validating\"",
    "health gates pass (GPU diag, NCCL, network, storage)",
    "maintenance or suspected fault",
    "evict pods respecting PDBs/checkpoints",
    "upgrade, repair, reboot",
    "re-validate",
    "validation failed → hardware repair queue",
    "repaired/reimaged",
    "remove (RMA, scale-in)"
]

SOURCE_NODES = [
    "Provisioned",
    "Configured",
    "Validating",
    "Ready",
    "Cordoned",
    "Draining",
    "Maintenance",
    "Quarantined",
    "Decommissioned"
]

all_text_concat = " ".join("".join(t.itertext()).strip() for t in text_elements)
print("\nVerifying Source Nodes in SVG:")
for n in SOURCE_NODES:
    count = len(re.findall(r'\b' + re.escape(n) + r'\b', all_text_concat))
    print(f"  {n:15}: count = {count}")
    assert count == 1, f"Node {n} count is {count}, expected 1!"

print("\nVerifying Source Transitions in SVG:")
# Each transition was split into lines. Let's verify that the concatenated lines of each badge match exactly:
for st in SOURCE_TRANSITIONS:
    # remove punctuation / whitespace normalization for matching
    norm_st = re.sub(r'\s+', ' ', st).strip()
    # Check if words in order exist
    pattern = r'\s*'.join(re.escape(w) for w in norm_st.split())
    match = re.search(pattern, all_text_concat)
    print(f"  '{norm_st[:35]}...': found = {match is not None}")
    assert match is not None, f"Transition '{st}' not found in SVG!"

print("\nAll source labels verified successfully!")
