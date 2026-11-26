import xml.etree.ElementTree as ET
import re

tree = ET.parse("test_lossless_out.svg")
root = tree.getroot()

# Let's inspect all text elements and check positions
print("Checking text paddings and positions:")
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    x = float(elem.attrib.get('x', 0))
    y = float(elem.attrib.get('y', 0))
    anchor = elem.attrib.get('text-anchor', 'start')
    fs = float(elem.attrib.get('font-size', 24))
    full_text = re.sub(r'\s+', ' ', ''.join(elem.itertext()).strip())
    
    tspans = list(elem.iter('{http://www.w3.org/2000/svg}tspan'))
    cur_y = y
    for tsp in tspans:
        tx = float(tsp.attrib.get('x', x))
        dy = float(tsp.attrib.get('dy', 0))
        cur_y += dy
        t_text = tsp.text or ""
        w = len(t_text) * 0.6 * fs
        if anchor == 'middle':
            left = tx - w/2
            right = tx + w/2
        else:
            left = tx
            right = tx + w
        top = cur_y - fs
        bottom = cur_y
        
        # Check canvas boundaries (40px margin)
        assert left >= 40, f"Text '{t_text}' left {left} < 40!"
        assert right <= 1560, f"Text '{t_text}' right {right} > 1560!"
        assert top >= 40, f"Text '{t_text}' top {top} < 40!"
        assert bottom <= 1120, f"Text '{t_text}' bottom {bottom} > 1120!"
        print(f"  [OK] line: left={left:5.1f}, right={right:6.1f}, top={top:5.1f}, bottom={bottom:5.1f} | '{t_text[:35]}...'")

print("\nALL LINES FIT COMFORTABLY INSIDE CANVAS WITH >= 40PX MARGIN!")
