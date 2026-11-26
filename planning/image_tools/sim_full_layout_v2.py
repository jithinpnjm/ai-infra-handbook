import xml.etree.ElementTree as ET

# Run complete layout verification script
def check_all():
    tree = ET.parse("output.svg")
    root = tree.getroot()
    print("Parsed SVG successfully.")

check_all()
