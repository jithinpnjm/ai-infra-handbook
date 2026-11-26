import re
import xml.etree.ElementTree as ET

tree = ET.parse("candidate_accept.svg")
root = tree.getroot()

# 1. Check line widths against their containing cards
# For each text/tspan, compute conservative width:
# sans: 0.6 * fs * len, mono: 0.62 * fs * len
# Compare with containing box width.

# Let's inspect every text element with tspans:
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    tspans = elem.findall('{http://www.w3.org/2000/svg}tspan')
    base_fs = float(elem.attrib.get('font-size', 24))
    base_font = elem.attrib.get('font-family', 'sans-serif')
    
    if tspans:
        for ts in tspans:
            t = (ts.text or "").strip()
            if not t:
                continue
            fs = float(ts.attrib.get('font-size', base_fs))
            font = ts.attrib.get('font-family', base_font)
            is_mono = 'monospace' in font
            factor = 0.62 if is_mono else 0.60
            w = len(t) * fs * factor
            print(f"tspan: fs={fs:2.0f} w={w:5.1f} | '{t}'")
    else:
        t = (elem.text or "").strip()
        if not t:
            continue
        is_mono = 'monospace' in base_font
        factor = 0.62 if is_mono else 0.60
        w = len(t) * base_fs * factor
        print(f"text:  fs={base_fs:2.0f} w={w:5.1f} | '{t}'")

# Check arrows
def ccw(A, B, C):
    return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])

def intersect(p1, p2, p3, p4):
    if p1 == p2 or p3 == p4:
        return False
    if p1 == p3 or p1 == p4 or p2 == p3 or p2 == p4:
        return False
    return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4)

# Segments of arrows:
arrow_segments = [
    # Client -> Socket
    ((510, 138), (572, 138)),
    # Socket -> Left Lane
    ((850, 186), (850, 206)),
    ((850, 206), (412, 206)),
    ((412, 206), (412, 218)),
    # Socket -> Right Lane
    ((1250, 186), (1250, 206)),
    ((1250, 206), (1188, 206)),
    ((1188, 206), (1188, 218)),
    # L1: N1 -> N2
    ((412, 396), (412, 418)),
    # L1: N2 -> N3
    ((412, 552), (412, 574)),
    # L1: N3 -> N4
    ((412, 708), (412, 730)),
    # L2: N1 -> N2
    ((1188, 426), (1188, 452)),
    # L2: N2 -> N3
    ((1188, 574), (1188, 600)),
    # L2: N3 -> Note
    ((1188, 744), (1188, 768))
]

crossings = 0
for i in range(len(arrow_segments)):
    for j in range(i + 1, len(arrow_segments)):
        s1 = arrow_segments[i]
        s2 = arrow_segments[j]
        if intersect(s1[0], s1[1], s2[0], s2[1]):
            print(f"CROSSING between {s1} and {s2}!")
            crossings += 1

assert crossings == 0, f"Found {crossings} arrow crossings!"
print(f"\nArrow crossings: {crossings} (PASS)")
