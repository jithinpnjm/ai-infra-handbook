#!/usr/bin/env python3
import xml.etree.ElementTree as ET

def check_layout_and_paddings(svg_path):
    tree = ET.parse(svg_path)
    root = tree.getroot()

    boxes = {
        "Two switches cabled together, no IP typed on either end": (40, 110, 940, 175),
        "neighbor swp1 interface remote-as external": (70, 206, 880, 60),
        "32 leaves x 16 spines = 512 links to address by hand": (1020, 110, 540, 175),
        "each interface gets an automatic link-local address fe80::/64": (40, 320, 1520, 115),
        "each side sends IPv6 Router Advertisements and Neighbour Discovery; FRR learns the neighbour link-local address and MAC": (40, 465, 1520, 135),
        "TCP session starts to port 179": (40, 630, 1520, 115),
        "OPEN carries Extended Next Hop Encoding capability (RFC 8950), so IPv4 routes work on a link with no IPv4 address": (40, 775, 1520, 135),
    }

    all_ok = True
    for elem in root.iter('{http://www.w3.org/2000/svg}text'):
        full_text = " ".join("".join(elem.itertext()).split())
        fs = float(elem.attrib['font-size'])
        if full_text in ["1", "2", "3", "4", "BGP unnumbered step by step"]:
            continue

        box = boxes.get(full_text)
        assert box is not None, f"Box missing for '{full_text}'"
        bx, by, bw, bh = box

        tspans = list(elem.iter('{http://www.w3.org/2000/svg}tspan'))
        if not tspans:
            lines = [(full_text, elem.attrib.get('font-family', 'sans-serif'), float(elem.attrib.get('x', 0)), float(elem.attrib.get('y', 0)))]
        else:
            base_y = float(elem.attrib.get('y', 0))
            lines = []
            cur_y = base_y
            for tsp in tspans:
                txt = tsp.text.strip()
                ff = tsp.attrib.get('font-family', elem.attrib.get('font-family', 'sans-serif'))
                tx = float(tsp.attrib.get('x', elem.attrib.get('x', 0)))
                dy = float(tsp.attrib.get('dy', 0))
                cur_y += dy
                lines.append((txt, ff, tx, cur_y))

        for line_txt, ff, tx, ty in lines:
            is_mono = 'mono' in ff
            mult = 0.62 if is_mono else 0.60
            w = len(line_txt) * fs * mult
            left_pad = tx - bx
            right_pad = (bx + bw) - (tx + w)
            top_pad = (ty - fs) - by
            bot_pad = (by + bh) - ty

            print(f"Line '{line_txt}' [{ff}, {fs}px]: w={w:.1f}px")
            print(f"   box: ({bx}, {by}, {bw}, {bh})")
            print(f"   paddings -> L: {left_pad:.1f}px, R: {right_pad:.1f}px, Top: {top_pad:.1f}px, Bot: {bot_pad:.1f}px")

            if left_pad < 16:
                print(f"   FAIL: Left pad {left_pad:.1f} < 16")
                all_ok = False
            if right_pad < 16:
                print(f"   FAIL: Right pad {right_pad:.1f} < 16")
                all_ok = False
            if top_pad < 16:
                print(f"   FAIL: Top pad {top_pad:.1f} < 16")
                all_ok = False
            if bot_pad < 16:
                print(f"   FAIL: Bot pad {bot_pad:.1f} < 16")
                all_ok = False

    assert all_ok, "Some paddings failed!"
    print("\nALL STRICT PADDING CHECKS PASSED!")

if __name__ == "__main__":
    check_layout_and_paddings("candidate_bgp_unnumbered.svg")
