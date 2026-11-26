import re
import xml.etree.ElementTree as ET

def check_all_labels(svg_file):
    tree = ET.parse(svg_file)
    root = tree.getroot()

    text_nodes = []
    for elem in root.iter():
        if elem.tag.endswith("text"):
            # Collect full text inside text (including tspans)
            full_txt = "".join(elem.itertext())
            full_txt = re.sub(r"\s+", " ", full_txt).strip()
            text_nodes.append(full_txt)

    print(f"Total <text> elements: {len(text_nodes)}")
    for i, t in enumerate(text_nodes, 1):
        print(f"  {i:2d}. {t}")

check_all_labels("test_candidate_dns.svg")
