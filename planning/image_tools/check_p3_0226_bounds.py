#!/usr/bin/env python3
import xml.etree.ElementTree as ET

tree = ET.parse("test_candidate_p3_0226.svg")
root = tree.getroot()

rects = []
for elem in root.iter('{http://www.w3.org/2000/svg}rect'):
    x = float(elem.attrib.get('x', 0))
    y = float(elem.attrib.get('y', 0))
    w = float(elem.attrib.get('width', 0))
    h = float(elem.attrib.get('height', 0))
    fill = elem.attrib.get('fill', '')
    if w > 0 and h > 0 and fill != '#f5f8f5':
        rects.append((x, y, w, h, elem))

print(f"Total rect containers: {len(rects)}")

texts = list(root.iter('{http://www.w3.org/2000/svg}text'))
print(f"Total text elements: {len(texts)}")

failures = []

for text in texts:
    fs = float(text.attrib['font-size'])
    anchor = text.attrib.get('text-anchor', 'start')
    
    tspans = text.findall('{http://www.w3.org/2000/svg}tspan')
    if not tspans:
        t_str = text.text.strip()
        tx = float(text.attrib['x'])
        ty = float(text.attrib['y'])
        w = len(t_str) * 0.60 * fs
        if anchor == 'middle':
            x_start = tx - w / 2
            x_end = tx + w / 2
        else:
            x_start = tx
            x_end = tx + w
        
        top_y = ty - fs
        bot_y = ty + 0.25 * fs
        
        matching_rect = None
        for rx, ry, rw, rh, elem in rects:
            if rx <= x_start and x_end <= rx + rw and ry <= top_y and bot_y <= ry + rh:
                matching_rect = (rx, ry, rw, rh)
                break
        
        if matching_rect:
            rx, ry, rw, rh = matching_rect
            pad_l = x_start - rx
            pad_r = (rx + rw) - x_end
            pad_t = top_y - ry
            pad_b = (ry + rh) - bot_y
            print(f"PASS (single): '{t_str[:30]}' pad=({pad_l:.1f}, {pad_r:.1f}, {pad_t:.1f}, {pad_b:.1f})")
            if min(pad_l, pad_r, pad_t, pad_b) < 16:
                print(f"  WARNING: Padding < 16px! min={min(pad_l, pad_r, pad_t, pad_b):.1f}")
                failures.append((t_str, min(pad_l, pad_r, pad_t, pad_b)))
        else:
            print(f"INFO: Title or outer element: '{t_str[:30]}' at ({tx}, {ty})")
    else:
        # Multi-line text
        first_tspan = tspans[0]
        tx = float(first_tspan.attrib.get('x', text.attrib.get('x', 0)))
        ty = float(text.attrib.get('y', 0))
        
        # Check all lines
        cur_y = ty
        all_lines = []
        for ts in tspans:
            dy = float(ts.attrib.get('dy', 0))
            cur_y += dy
            l_str = ts.text.strip()
            l_w = len(l_str) * 0.60 * fs
            if anchor == 'middle':
                xs = tx - l_w / 2
                xe = tx + l_w / 2
            else:
                xs = tx
                xe = tx + l_w
            all_lines.append((l_str, xs, xe, cur_y - fs, cur_y + 0.25 * fs))
        
        overall_xs = min(xs for _, xs, _, _, _ in all_lines)
        overall_xe = max(xe for _, _, xe, _, _ in all_lines)
        overall_yt = min(yt for _, _, _, yt, _ in all_lines)
        overall_yb = max(yb for _, _, _, _, yb in all_lines)
        
        matching_rect = None
        for rx, ry, rw, rh, elem in rects:
            if rx <= overall_xs and overall_xe <= rx + rw and ry <= overall_yt and overall_yb <= ry + rh:
                matching_rect = (rx, ry, rw, rh)
                break
        
        full_t = " ".join(ts.text.strip() for ts in tspans)
        if matching_rect:
            rx, ry, rw, rh = matching_rect
            pad_l = overall_xs - rx
            pad_r = (rx + rw) - overall_xe
            pad_t = overall_yt - ry
            pad_b = (ry + rh) - overall_yb
            print(f"PASS (multi): '{full_t[:30]}' pad=({pad_l:.1f}, {pad_r:.1f}, {pad_t:.1f}, {pad_b:.1f})")
            if min(pad_l, pad_r, pad_t, pad_b) < 16:
                print(f"  WARNING: Padding < 16px! min={min(pad_l, pad_r, pad_t, pad_b):.1f}")
                failures.append((full_t, min(pad_l, pad_r, pad_t, pad_b)))
        else:
            print(f"FAIL (no rect): '{full_t[:30]}' bounds=({overall_xs:.1f}, {overall_xe:.1f}, {overall_yt:.1f}, {overall_yb:.1f})")
            failures.append((full_t, "no matching rect"))

print(f"\nTotal failures/warnings: {len(failures)}")
