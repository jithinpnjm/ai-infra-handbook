import xml.etree.ElementTree as ET

tree = ET.parse("test_candidate_p3_0503.svg")
root = tree.getroot()

print("=== CHECKING TEXT PADDING AND DIMENSIONS ===")

# Check conservative estimates
# sans: 0.6 * font-size per char
# mono: 0.62 * font-size per char

for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    fs = float(elem.attrib['font-size'])
    ff = elem.attrib.get('font-family', '')
    is_mono = 'mono' in ff
    factor = 0.62 if is_mono else 0.6
    
    tspans = elem.findall('{http://www.w3.org/2000/svg}tspan')
    if tspans:
        for tsp in tspans:
            t = tsp.text.strip()
            est_w = len(t) * fs * factor
            print(f"Line (tspan): '{t}' -> len={len(t)}, fs={fs}, est_w={est_w:.1f}px")
    else:
        t = "".join(elem.itertext()).strip()
        est_w = len(t) * fs * factor
        print(f"Line (single): '{t}' -> len={len(t)}, fs={fs}, est_w={est_w:.1f}px")

