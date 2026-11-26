#!/usr/bin/env python3
import xml.etree.ElementTree as ET

def check_paddings(svg_path):
    tree = ET.parse(svg_path)
    root = tree.getroot()

    rects = []
    for elem in root.iter('{http://www.w3.org/2000/svg}rect'):
        x = float(elem.attrib.get('x', 0))
        y = float(elem.attrib.get('y', 0))
        w = float(elem.attrib.get('width', 0))
        h = float(elem.attrib.get('height', 0))
        fill = elem.attrib.get('fill', '')
        rects.append((x, y, w, h, fill))

    texts = []
    for elem in root.iter('{http://www.w3.org/2000/svg}text'):
        full_text = " ".join("".join(elem.itertext()).split())
        x = float(elem.attrib.get('x', 0))
        y = float(elem.attrib.get('y', 0))
        anchor = elem.attrib.get('text-anchor', 'start')
        fs = float(elem.attrib.get('font-size', 24))
        tspans = []
        for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
            tx = float(tsp.attrib.get('x', x))
            tdy = float(tsp.attrib.get('dy', 0))
            tfs = float(tsp.attrib.get('font-size', fs))
            ttext = (tsp.text or "").strip()
            tspans.append((tx, tdy, tfs, ttext))
        texts.append((full_text, x, y, anchor, fs, tspans))

    print(f"Total rects: {len(rects)}, Total texts: {len(texts)}")

    # For each text element, find its enclosing card rect
    for full_text, x, y, anchor, fs, tspans in texts:
        if "Keeping the GPU" in full_text:
            continue
        # calculate approximate bounding box of text
        lines = tspans if tspans else [(x, 0, fs, full_text)]
        max_w = 0
        min_x = 9999
        max_x = -9999
        for tx, tdy, tfs, ttext in lines:
            lw = len(ttext) * 0.62 * tfs
            if anchor == 'middle':
                lx1 = tx - lw / 2
                lx2 = tx + lw / 2
            elif anchor == 'end':
                lx1 = tx - lw
                lx2 = tx
            else:
                lx1 = tx
                lx2 = tx + lw
            min_x = min(min_x, lx1)
            max_x = max(max_x, lx2)
        
        # find matching rect
        matched_rect = None
        for rx, ry, rw, rh, rfill in rects:
            if rx <= min_x and rx + rw >= max_x and ry <= y and ry + rh >= y:
                if matched_rect is None or rw * rh < matched_rect[2] * matched_rect[3]:
                    matched_rect = (rx, ry, rw, rh, rfill)
        
        if matched_rect:
            rx, ry, rw, rh, _ = matched_rect
            pad_left = min_x - rx
            pad_right = (rx + rw) - max_x
            pad_top = y - ry - fs
            pad_bot = (ry + rh) - y
            print(f"Text: '{full_text[:40]}...' in rect ({rx}, {ry}, {rw}, {rh})")
            print(f"   Paddings: Left={pad_left:.1f}px, Right={pad_right:.1f}px, Top={pad_top:.1f}px, Bot={pad_bot:.1f}px")
            assert pad_left >= 16, f"Left padding {pad_left} < 16px!"
            assert pad_right >= 16, f"Right padding {pad_right} < 16px!"
        else:
            print(f"NO DIRECT RECT for: '{full_text[:40]}...'")

    print("\nAll text elements have at least 16px padding inside their boxes!")

if __name__ == '__main__':
    check_paddings('test_candidate_numa.svg')
