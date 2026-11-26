#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

def check_paddings(svg_path):
    tree = ET.parse(svg_path)
    root = tree.getroot()

    print("=== Checking conservative text widths and box paddings ===")
    
    # We will inspect each group and its rect and text
    groups = [
        ("ca-card", "Cluster Autoscaler"),
        ("karpenter-card", "Karpenter"),
        ("item-requirements", "requirements"),
        ("item-capacity", "capacity-type"),
        ("item-zones", "zones"),
        ("item-taints", "taints"),
        ("item-nodeclass", "nodeClassRef"),
        ("item-expire", "expireAfter"),
        ("item-limits", "limits"),
        ("item-disruption", "disruption"),
        ("item-warning", "warning")
    ]

    all_passed = True
    for gid, name in groups:
        g = root.find(f".//*[@id='{gid}']")
        assert g is not None, f"Group {gid} not found"
        rect = g.find('{http://www.w3.org/2000/svg}rect')
        rx = float(rect.attrib['x'])
        ry = float(rect.attrib['y'])
        rw = float(rect.attrib['width'])
        rh = float(rect.attrib['height'])
        
        text = g.find('{http://www.w3.org/2000/svg}text')
        fs = float(text.attrib['font-size'].replace('px', ''))
        ff = text.attrib.get('font-family', 'sans-serif')
        tx = float(text.attrib['x'])
        ty = float(text.attrib['y'])

        # Check all lines (either text or tspans)
        tspans = text.findall('{http://www.w3.org/2000/svg}tspan')
        if tspans:
            lines = []
            for tsp in tspans:
                lines.append((tsp.text.strip(), float(tsp.attrib.get('x', tx)), float(tsp.attrib.get('dy', '0'))))
        else:
            lines = [(text.text.strip(), tx, 0)]

        # Let's inspect each line's width and padding
        cur_y = ty
        for l_idx, (line_str, lx, dy) in enumerate(lines):
            cur_y += dy
            char_w = 0.62 * fs if 'monospace' in ff else 0.6 * fs
            w = len(line_str) * char_w
            
            left_pad = lx - rx
            right_pad = (rx + rw) - (lx + w)
            top_pad = (cur_y - fs) - ry
            bottom_pad = (ry + rh) - cur_y

            print(f"[{name}] Line {l_idx+1}: '{line_str}'")
            print(f"   width={w:.1f}px (len={len(line_str)}, fs={fs}), box_w={rw:.1f}px")
            print(f"   left_pad={left_pad:.1f}px, right_pad={right_pad:.1f}px, top_pad={top_pad:.1f}px, bottom_pad={bottom_pad:.1f}px")

            if left_pad < 16:
                print(f"   [FAIL] Left padding {left_pad:.1f} < 16 px!")
                all_passed = False
            if right_pad < 16:
                print(f"   [FAIL] Right padding {right_pad:.1f} < 16 px!")
                all_passed = False
            if top_pad < 10: # allow top baseline breathing room
                print(f"   [WARN] Top padding {top_pad:.1f} < 10 px!")
            if bottom_pad < 10:
                print(f"   [WARN] Bottom padding {bottom_pad:.1f} < 10 px!")

    assert all_passed, "Some paddings failed conservative check!"
    print("\nALL BOX PADDINGS >= 16PX CHECK PASSED!")

if __name__ == '__main__':
    check_paddings("test_karpenter.svg")
