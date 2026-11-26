import xml.etree.ElementTree as ET

tree = ET.parse("final_svg.svg")
root = tree.getroot()

group_boxes = {
    'card-streetlight': (40, 140, 600, 265),
    'card-random-change': (40, 445, 600, 265),
    'card-blame-someone-else': (40, 750, 600, 310),
    'node-problem-statement': (680, 140, 880, 135),
    'node-scientific-method': (680, 315, 420, 575),
    'test-observational': (1140, 315, 420, 135),
    'test-experimental': (1140, 490, 420, 195),
    'test-negative': (1140, 725, 420, 165),
    'node-diagnosis-cycle': (680, 930, 880, 130),
    'bottom-takeaway-bar': (40, 1100, 1520, 60)
}

flaw_boxes = {
    'card-streetlight': (56.0, 342.0, 568.0, 50.0),
    'card-random-change': (56.0, 622.0, 568.0, 74.0),
    'card-blame-someone-else': (56.0, 924.0, 568.0, 120.0)
}

def get_font_size(elem, parent=None):
    if 'font-size' in elem.attrib:
        return float(elem.attrib['font-size'])
    if parent is not None and 'font-size' in parent.attrib:
        return float(parent.attrib['font-size'])
    return 24.0

all_good = True
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
            
            top_pad = (curr_y - fs) - target_by
            bot_pad = (target_by + target_bh) - curr_y
            
            if top_pad < 15.0 or bot_pad < 15.0:
                print(f"WARN PADDING: {gid} | '{content[:20]}' | baseline={curr_y:.1f}, top_pad={top_pad:.1f}, bot_pad={bot_pad:.1f}")
                all_good = False
            else:
                print(f"OK: {gid} | '{content[:20]}' | top_pad={top_pad:.1f}, bot_pad={bot_pad:.1f}")

if all_good:
    print("\nALL VERTICAL PADDING CHECKS PASSED (>= 15px)!")
