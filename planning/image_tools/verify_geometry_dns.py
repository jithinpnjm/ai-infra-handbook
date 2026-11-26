import re
import xml.etree.ElementTree as ET

tree = ET.parse("test_candidate_dns.svg")
root = tree.getroot()

def est_width(txt, fs, is_mono):
    coeff = 0.62 if is_mono else 0.6
    return len(txt) * fs * coeff

# Check each card's lines
# Boxes:
# Card 1: rect x=50, y=110, w=730, h=340 -> right=780, bottom=450. Icon at (75, 130, w=56, h=56) -> right=131, bottom=186
# Card 2: rect x=820, y=110, w=730, h=340 -> right=1550, bottom=450. Icon at (845, 130, w=56, h=56) -> right=901, bottom=186
# Card 3: rect x=50, y=480, w=730, h=330 -> right=780, bottom=810. Icon at (75, 500, w=56, h=56) -> right=131, bottom=556
# Card 4: rect x=820, y=480, w=730, h=330 -> right=1550, bottom=810. Icon at (845, 500, w=56, h=56) -> right=901, bottom=556
# dnsConfig: rect x=50, y=845, w=1500, h=125 -> right=1550, bottom=970. Icon at (75, 878, w=56, h=56) -> right=131, bottom=934
# Callout: rect x=50, y=1000, w=1500, h=100 -> right=1550, bottom=1100. Icon at (75, 1022, w=56, h=56) -> right=131, bottom=1078

print("=== CHECKING PADDINGS AND OVERLAPS ===")
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    elem_fs = float(elem.attrib.get('font-size', '24'))
    for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
        txt = tsp.text
        if not txt:
            continue
        fs = float(tsp.attrib.get('font-size', elem_fs))
        is_mono = (tsp.attrib.get('font-family') == 'monospace')
        x = float(tsp.attrib.get('x', elem.attrib.get('x', '0')))
        y = float(tsp.attrib.get('y', elem.attrib.get('y', '0')))
        w = est_width(txt, fs, is_mono)
        right = x + w
        print(f"tspan: x={x:4.0f}, y={y:4.0f}, w={w:5.1f}, right={right:6.1f}, fs={fs:2.0f} | '{txt.strip()}'")

