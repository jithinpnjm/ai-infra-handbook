import re
import xml.etree.ElementTree as ET

with open("output.svg") as f:
    svg_content = f.read()

root = ET.fromstring(svg_content)

def text_width(text, font_size, is_mono):
    return len(text) * font_size * (0.62 if is_mono else 0.60)

# Traverse tree and keep track of cumulative transforms
def audit_node(el, cur_tx, cur_ty):
    # parse transform
    t_str = el.attrib.get('transform', '')
    tx, ty = 0.0, 0.0
    m = re.search(r'translate\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)', t_str)
    if m:
        tx, ty = float(m.group(1)), float(m.group(2))
    
    new_tx = cur_tx + tx
    new_ty = cur_ty + ty
    
    tag = el.tag.split('}')[-1]
    if tag == 'text':
        cls = el.attrib.get('class', '')
        x = float(el.attrib.get('x', 0)) + new_tx
        y = float(el.attrib.get('y', 0)) + new_ty
        text = el.text or ''
        anchor = el.attrib.get('text-anchor', 'start')
        
        font_size = 24
        is_mono = False
        if 'title' in cls and 'section' not in cls and 'host' not in cls:
            font_size = 48
        elif 'section-title' in cls:
            font_size = 30
        elif 'circle-text' in cls:
            font_size = 26
        elif 'mono-text' in cls:
            font_size = 24
            is_mono = True
        
        w = text_width(text, font_size, is_mono)
        if anchor == 'middle':
            x1 = x - w / 2.0
            x2 = x + w / 2.0
        else:
            x1 = x
            x2 = x + w
        
        # Cap height and descender
        y1 = y - font_size * 0.75
        y2 = y + font_size * 0.20
        
        print(f"Text '{text[:22]:<22}' -> x1={x1:6.1f}, x2={x2:6.1f}, y1={y1:6.1f}, y2={y2:6.1f}")
        
        # Check canvas bounds (1600x1200 with 40 margin)
        assert x1 >= 40.0 - 1e-3, f"Text '{text[:25]}' overflows canvas left: x1={x1}"
        assert x2 <= 1560.0 + 1e-3, f"Text '{text[:25]}' overflows canvas right: x2={x2}"
        assert y1 >= 40.0 - 1e-3, f"Text '{text[:25]}' overflows canvas top: y1={y1}"
        assert y2 <= 1160.0 + 1e-3, f"Text '{text[:25]}' overflows canvas bottom: y2={y2}"

    for child in el:
        audit_node(child, new_tx, new_ty)

audit_node(root, 0.0, 0.0)
print("AUDIT SUCCESS: All text elements strictly inside 1600x1200 canvas with >= 40px margins!")
