import re
import xml.etree.ElementTree as ET

with open("output.svg") as f:
    svg_content = f.read()

root = ET.fromstring(svg_content)

# Width factors
def text_width(text, font_size, is_mono):
    return len(text) * font_size * (0.62 if is_mono else 0.60)

# Check all text elements
text_elements = []
for el in root.iter():
    tag = el.tag.split('}')[-1]
    if tag == 'text':
        text_elements.append(el)

print(f"Total <text> elements: {len(text_elements)}")

# Let's inspect each text element's estimated bounds
for el in text_elements:
    cls = el.attrib.get('class', '')
    x = float(el.attrib.get('x', 0))
    y = float(el.attrib.get('y', 0))
    text = el.text or ''
    anchor = 'middle' if 'middle' in cls or el.attrib.get('text-anchor') == 'middle' else 'start'
    
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
    
    # Check canvas bounds (1600x1200 with 40 margin)
    assert x1 >= 40.0 - 1e-3, f"Text '{text[:25]}' overflows canvas left: x1={x1}"
    assert x2 <= 1560.0 + 1e-3, f"Text '{text[:25]}' overflows canvas right: x2={x2}"
    assert y1 >= 40.0 - 1e-3, f"Text '{text[:25]}' overflows canvas top: y1={y1}"
    assert y2 <= 1160.0 + 1e-3, f"Text '{text[:25]}' overflows canvas bottom: y2={y2}"

print("All text elements are strictly inside the 1600x1200 canvas with >= 40px margins!")
