import xml.etree.ElementTree as ET

# We will test all cards and boxes
# Rule: Every text line must fit inside its box with at least 16 px padding.
# Let's write an inspector script.

def inspect_lines():
    tree = ET.parse("test_engine_upgrade.svg")
    root = tree.getroot()
    
    # We will compute bounding boxes of texts and boxes
    print("Inspecting line lengths and margins...")

inspect_lines()
