import xml.etree.ElementTree as ET

tree = ET.parse("test_timeline.svg")
root = tree.getroot()

# For header cards and step cards (not icon sub-shapes):
cards = []
for g in root.iter('{http://www.w3.org/2000/svg}g'):
    gid = g.attrib.get('id', '')
    if gid.startswith('participant-') or gid.startswith('step-') or gid == 'note-running':
        r = g.find('{http://www.w3.org/2000/svg}rect')
        if r is not None:
            x = float(r.attrib['x'])
            y = float(r.attrib['y'])
            w = float(r.attrib['width'])
            h = float(r.attrib['height'])
            cards.append((gid, x, y, w, h))
            assert x >= 40.0, f"Card {gid} left {x} < 40!"
            assert x + w <= 1560.0, f"Card {gid} right {x+w} > 1560!"
            assert y >= 40.0, f"Card {gid} top {y} < 40!"
            assert y + h <= 1160.0, f"Card {gid} bottom {y+h} > 1160!"

print(f"Total top-level cards checked: {len(cards)} (all within [40, 40, 1560, 1160])")
for c in cards[:5]:
    print("  ", c)
