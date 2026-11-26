import xml.etree.ElementTree as ET

tree = ET.parse("test_candidate_v2.svg")
root = tree.getroot()

group_boxes = {}
for g in root.iter('{http://www.w3.org/2000/svg}g'):
    gid = g.attrib.get('id')
    if not gid:
        continue
    rect = g.find('{http://www.w3.org/2000/svg}rect')
    if rect is not None:
        rx = float(rect.attrib['x'])
        ry = float(rect.attrib['y'])
        rw = float(rect.attrib['width'])
        rh = float(rect.attrib['height'])
        group_boxes[gid] = (rx, ry, rw, rh)

flaw_boxes = {
    'card-streetlight': (56.0, 368.0, 568.0, 48.0),
    'card-random-change': (56.0, 650.0, 568.0, 76.0),
    'card-blame-someone-else': (56.0, 950.0, 568.0, 102.0)
}

def get_font_size(elem, parent=None):
    if 'font-size' in elem.attrib:
        return float(elem.attrib['font-size'])
    if parent is not None and 'font-size' in parent.attrib:
        return float(parent.attrib['font-size'])
    return 24.0

for gid, (bx, by, bw, bh) in group_boxes.items():
    g = root.find(f".//*[@id='{gid}']")
    for text_el in g.iter('{http://www.w3.org/2000/svg}text'):
        base_y = float(text_el.attrib.get('y', by))
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
            
            target_by, target_bh = by, bh
            if gid in flaw_boxes and curr_y > flaw_boxes[gid][1]:
                target_by, target_bh = flaw_boxes[gid][1], flaw_boxes[gid][3]
            
            # y is baseline: top of font is curr_y - fs, bottom is curr_y + fs*0.2
            top_pad = (curr_y - fs) - target_by
            bot_pad = (target_by + target_bh) - curr_y
            print(f"{gid} | '{content[:20]}' | baseline={curr_y:.1f}, top_pad={top_pad:.1f}, bot_pad={bot_pad:.1f}")
