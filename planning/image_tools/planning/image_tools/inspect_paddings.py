#!/usr/bin/env python3
import xml.etree.ElementTree as ET

# Let's inspect paddings for all text elements in test_candidate_eight_rules.svg

tree = ET.parse("test_candidate_eight_rules.svg")
root = tree.getroot()

boxes = {
    "tile-1": (40, 115, 480, 215),
    "tile-2": (560, 115, 480, 215),
    "tile-3": (1080, 115, 480, 215),
    "tile-8": (40, 370, 480, 200),
    "center-node": (560, 370, 480, 200),
    "tile-4": (1080, 370, 480, 200),
    "tile-7": (40, 610, 480, 320),
    "tile-6": (560, 610, 480, 320),
    "tile-5": (1080, 610, 480, 320),
    "fail-1": (40, 970, 480, 190),
    "fail-2": (560, 970, 480, 190),
    "fail-3": (1080, 970, 480, 190),
}

for gid, (bx, by, bw, bh) in boxes.items():
    g = root.find(f".//*[@id='{gid}']")
    for text in g.findall('{http://www.w3.org/2000/svg}text'):
        base_fs = float(text.attrib.get('font-size', 24))
        tspans = text.findall('{http://www.w3.org/2000/svg}tspan')
        if not tspans:
            tspans = [text]
        for tsp in tspans:
            t = (tsp.text or "").strip()
            if not t: continue
            fs = float(tsp.attrib.get('font-size', base_fs))
            w = len(t) * 0.60 * fs
            anchor = tsp.attrib.get('text-anchor', text.attrib.get('text-anchor', 'start'))
            tx = float(tsp.attrib.get('x', text.attrib.get('x', 0)))
            # check dy or y
            ty = float(tsp.attrib.get('y', text.attrib.get('y', 0)))
            top_y = ty - fs
            bot_y = ty + 0.25 * fs
            top_pad = top_y - by
            bot_pad = by + bh - bot_y
            print(f"[{gid}] '{t[:20]}' top_pad={top_pad:.1f}, bot_pad={bot_pad:.1f}")
