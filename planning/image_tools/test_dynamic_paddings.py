import xml.etree.ElementTree as ET

tree = ET.parse("output.svg")
root = tree.getroot()

nodes = [
    "node-q1",
    "node-module",
    "node-q2",
    "node-raw",
    "node-q3",
    "node-shell",
    "node-command",
    "node-injection",
    "node-q-script",
    "node-script",
    "guard-strip",
    "bottom-bar"
]

all_pad_ok = True

for nid in nodes:
    el = root.find(f".//*[@id='{nid}']")
    rect_el = el.find('{http://www.w3.org/2000/svg}rect')
    rx = float(rect_el.get('x'))
    ry = float(rect_el.get('y'))
    rw = float(rect_el.get('width'))
    rh = float(rect_el.get('height'))
    
    text_el = el.find('{http://www.w3.org/2000/svg}text')
    tx = float(text_el.get('x'))
    ty = float(text_el.get('y'))
    anchor = text_el.get('text-anchor', 'start')
    
    tspans = text_el.findall('{http://www.w3.org/2000/svg}tspan')
    if tspans:
        lines = []
        curr_y = ty
        for ts in tspans:
            dy = float(ts.get('dy', 0))
            curr_y += dy
            fs = float(ts.get('font-size', text_el.get('font-size', 24)))
            txt = ts.text.strip()
            lines.append((txt, fs, curr_y))
    else:
        fs = float(text_el.get('font-size', 24))
        txt = text_el.text.strip()
        lines = [(txt, fs, ty)]
        
    print(f"\n--- Node: {nid} (rect x={rx}, y={ry}, w={rw}, h={rh}) ---")
    
    # Top padding:
    top_y = lines[0][2] - 0.72 * lines[0][1]
    top_pad = top_y - ry
    
    # Bottom padding:
    bot_y = lines[-1][2] + 0.22 * lines[-1][1]
    bot_pad = (ry + rh) - bot_y
    
    print(f"  Vertical: top_pad={top_pad:.1f}px, bot_pad={bot_pad:.1f}px")
    if top_pad < 16.0 or bot_pad < 16.0:
        print(f"  FAILED VERTICAL PADDING in {nid}! (needs >=16px)")
        all_pad_ok = False
        
    for idx, (txt, fs, y_base) in enumerate(lines, 1):
        line_w = len(txt) * 0.6 * fs
        if anchor == 'middle':
            left_x = tx - line_w / 2
            right_x = tx + line_w / 2
        else:
            left_x = tx
            right_x = tx + line_w
        left_pad = left_x - rx
        right_pad = (rx + rw) - right_x
        icon_gap = left_x - (rx + 74)
        
        ok = (left_pad >= 16.0) and (right_pad >= 16.0) and (icon_gap >= 14.0 or anchor == 'middle')
        print(f"  Line {idx} (fs={fs}px, w={line_w:.1f}px): left_pad={left_pad:.1f}px, right_pad={right_pad:.1f}px [{'OK' if ok else 'FAIL'}]")
        if not ok:
            print(f"  FAILED HORIZONTAL PADDING in {nid} line {idx}!")
            all_pad_ok = False

if all_pad_ok:
    print("\nALL NODES DYNAMICALLY PASSED RIGOROUS PADDING CHECKS!")
else:
    print("\nSOME DYNAMIC PADDING CHECKS FAILED!")
