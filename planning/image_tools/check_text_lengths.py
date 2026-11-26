import xml.etree.ElementTree as ET

tree = ET.parse("test_candidate.svg")
root = tree.getroot()

# Check all text elements and tspans
print("Checking text line lengths:")
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    fs = float(elem.attrib.get('font-size', 24))
    tspans = elem.findall('{http://www.w3.org/2000/svg}tspan')
    if not tspans:
        txt = elem.text.strip()
        ff = elem.attrib.get('font-family', 'sans-serif')
        char_w = 0.62 * fs if 'mono' in ff else 0.6 * fs
        width_est = len(txt) * char_w
        print(f"[{fs}px {ff}] '{txt[:35]}...' len={len(txt)} est_width={width_est:.1f}px")
    else:
        for tsp in tspans:
            txt = tsp.text.strip()
            ff = tsp.attrib.get('font-family', elem.attrib.get('font-family', 'sans-serif'))
            tfs = float(tsp.attrib.get('font-size', fs))
            char_w = 0.62 * tfs if 'mono' in ff else 0.6 * tfs
            width_est = len(txt) * char_w
            print(f"  tspan [{tfs}px {ff}] '{txt[:35]}...' len={len(txt)} est_width={width_est:.1f}px")
