#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

def check_all_paddings(svg_path):
    tree = ET.parse(svg_path)
    root = tree.getroot()

    boxes = {
        "section-anatomy": (40, 135, 1520, 235),
        "piece-1": (60, 230, 190, 125),
        "piece-2": (265, 230, 190, 125),
        "piece-3": (470, 230, 310, 125),
        "piece-4": (795, 230, 190, 125),
        "piece-5": (1000, 230, 540, 125),
        "var-1": (125, 422, 700, 44),
        "var-2": (845, 422, 700, 44),
        "var-3": (125, 472, 700, 44),
        "var-4": (845, 472, 700, 44),
        "var-5": (125, 522, 700, 44),
        "var-6": (845, 522, 700, 44),
        "box-decision": (40, 650, 450, 150),
        "box-yes": (620, 615, 940, 95),
        "box-no": (620, 735, 940, 135),
        "tool-1": (56, 922, 1488, 55),
        "tool-2": (56, 987, 734, 55),
        "tool-3": (810, 987, 734, 55),
        "bottom-bar": (40, 1095, 1520, 65),
    }

    issues = []
    for gid, (bx, by, bw, bh) in boxes.items():
        g = root.find(f".//*[@id='{gid}']")
        if g is None:
            # try to find rect or element directly
            continue
        for text in g.findall('{http://www.w3.org/2000/svg}text'):
            base_fs = float(text.attrib.get('font-size', 24))
            base_ff = text.attrib.get('font-family', 'sans-serif')
            tspans = text.findall('{http://www.w3.org/2000/svg}tspan')
            if not tspans:
                tspans = [text]
            for tsp in tspans:
                t = (tsp.text or "").strip()
                if not t: continue
                fs = float(tsp.attrib.get('font-size', base_fs))
                ff = tsp.attrib.get('font-family', base_ff)
                char_w = 0.62 if 'mono' in ff else 0.60
                w = len(t) * char_w * fs
                anchor = tsp.attrib.get('text-anchor', text.attrib.get('text-anchor', 'start'))
                tx = float(tsp.attrib.get('x', text.attrib.get('x', 0)))
                ty = float(tsp.attrib.get('y', text.attrib.get('y', 0)))
                if anchor == 'middle':
                    x_start = tx - w / 2
                    x_end = tx + w / 2
                elif anchor == 'end':
                    x_start = tx - w
                    x_end = tx
                else:
                    x_start = tx
                    x_end = tx + w

                top_y = ty - fs
                bot_y = ty + 0.25 * fs

                pad_l = x_start - bx
                pad_r = bx + bw - x_end
                pad_t = top_y - by
                pad_b = by + bh - bot_y

                print(f"[{gid}] '{t[:30]}' -> L:{pad_l:.1f} R:{pad_r:.1f} T:{pad_t:.1f} B:{pad_b:.1f}")

                if pad_l < 16: issues.append(f"Left pad {pad_l:.1f} < 16 for '{t}' in {gid}")
                if pad_r < 16: issues.append(f"Right pad {pad_r:.1f} < 16 for '{t}' in {gid}")
                if pad_t < 16: issues.append(f"Top pad {pad_t:.1f} < 16 for '{t}' in {gid}")
                if pad_b < 16: issues.append(f"Bottom pad {pad_b:.1f} < 16 for '{t}' in {gid}")

    print(f"\nTotal issues found: {len(issues)}")
    for iss in issues:
        print("  FAIL:", iss)

check_all_paddings("wheel_decision.svg")
