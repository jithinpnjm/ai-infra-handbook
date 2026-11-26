import xml.etree.ElementTree as ET

tree = ET.parse("test_full_candidate.svg")
root = tree.getroot()

# Let's inspect all text and tspan elements
lines = []
for el in root.iter():
    tag = el.tag.split('}')[-1]
    if tag == 'text':
        # could have direct text or tspans
        direct = el.text.strip() if el.text else ""
        if direct:
            lines.append((direct, el.attrib, el))
        for child in el:
            ctag = child.tag.split('}')[-1]
            if ctag == 'tspan':
                ctxt = child.text.strip() if child.text else ""
                if ctxt:
                    # inherit attributes
                    attr = dict(el.attrib)
                    attr.update(child.attrib)
                    lines.append((ctxt, attr, child))

print(f"Total lines: {len(lines)}")
for txt, attr, el in lines:
    font_family = attr.get('font-family', 'sans-serif')
    font_size = float(attr.get('font-size', '24'))
    is_mono = 'mono' in font_family.lower()
    char_width = (0.62 if is_mono else 0.6) * font_size
    est_width = len(txt) * char_width
    x = float(attr.get('x', '0'))
    text_anchor = attr.get('text-anchor', 'start')
    
    if text_anchor == 'middle':
        left = x - est_width / 2
        right = x + est_width / 2
    else:
        left = x
        right = x + est_width
        
    print(f"[{'MONO' if is_mono else 'SANS'} {font_size}px] len={len(txt):2d} est_w={est_width:6.1f} bounds=({left:6.1f}, {right:6.1f}) : '{txt[:45]}'")
    # Check if right > 1560 or left < 40
    assert left >= 38.0, f"Left margin violated by: {txt}"
    assert right <= 1562.0, f"Right margin violated by: {txt}"

print("\nALL LINES SATISFY CONSERVATIVE WIDTH CHECKS!")
