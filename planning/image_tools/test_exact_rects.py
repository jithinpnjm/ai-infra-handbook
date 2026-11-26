import xml.etree.ElementTree as ET

tree = ET.parse("final_svg.svg")
root = tree.getroot()

# Let's find all rects in each group
def get_font_size(elem, parent=None):
    if 'font-size' in elem.attrib:
        return float(elem.attrib['font-size'])
    if parent is not None and 'font-size' in parent.attrib:
        return float(parent.attrib['font-size'])
    return 24.0

for g in root.iter('{http://www.w3.org/2000/svg}g'):
    gid = g.attrib.get('id')
    if not gid:
        continue
    rects = g.findall('{http://www.w3.org/2000/svg}rect')
    if not rects:
        continue
    
    # Check text inside each rect
    for text_el in g.iter('{http://www.w3.org/2000/svg}text'):
        base_y = float(text_el.attrib.get('y', 0))
        tspans = text_el.findall('{http://www.w3.org/2000/svg}tspan')
        items = tspans if tspans else [text_el]
        
        curr_y = base_y
        for item in items:
            content = item.text.strip() if item.text else ""
            if not content:
                continue
            fs = get_font_size(item, text_el)
            if 'dy' in item.attrib:
                curr_y += float(item.attrib['dy'])
            elif 'y' in item.attrib:
                curr_y = float(item.attrib['y'])
            
            # Find the innermost rect containing this text's y
            containing_rect = None
            for r in rects:
                ry = float(r.attrib['y'])
                rh = float(r.attrib['height'])
                if ry <= curr_y <= ry + rh:
                    containing_rect = (ry, rh)
                    break
            
            if containing_rect:
                ry, rh = containing_rect
                top_pad = (curr_y - fs) - ry
                bot_pad = (ry + rh) - curr_y
                print(f"{gid:24} | '{content[:20]:20}' | base={curr_y:6.1f} | top={top_pad:4.1f} | bot={bot_pad:4.1f}")
            else:
                print(f"OUTSIDE RECT: {gid} | '{content}' | y={curr_y}")
