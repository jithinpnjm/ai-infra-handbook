#!/usr/bin/env python3
import xml.etree.ElementTree as ET

tree = ET.parse("planning/image_tools/test_algo_pick.svg")
root = tree.getroot()

print("Auditing all bounding boxes and text paddings...")

# Let's verify every text element and its tspans:
# For each text/tspan:
# compute width = len(text) * 0.60 * fs
# anchor = middle (all texts in boxes are text-anchor="middle" except the header which is start at x=1256, panel w=380)
# Check left and right bounds relative to containing box!

all_boxes = []

# Collect all rects:
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

# Now for each text element:
texts = list(root.iter('{http://www.w3.org/2000/svg}text'))
print(f"Total text elements: {len(texts)}")

failures = []

for text in texts:
    fs = float(text.attrib['font-size'])
    anchor = text.attrib.get('text-anchor', 'start')
    
    tspans = text.findall('{http://www.w3.org/2000/svg}tspan')
    if not tspans:
        # Single line text
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
        
        # Find containing rect:
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
            print(f"PASS (single): '{t_str}' pad=({pad_l:.1f}, {pad_r:.1f}, {pad_t:.1f}, {pad_b:.1f})")
            if min(pad_l, pad_r) < 16.0:
                failures.append(f"Horiz pad < 16: '{t_str}' ({pad_l:.1f}, {pad_r:.1f})")
            if min(pad_t, pad_b) < 0:
                failures.append(f"Vertical overflow: '{t_str}' ({pad_t:.1f}, {pad_b:.1f})")
        else:
            # Maybe title
            if "Pick the algorithm" in t_str:
                print(f"Title at y={ty} on canvas 1600 (w={w:.1f}) -> pad_l={x_start:.1f}, pad_r={1600-x_end:.1f}")
            else:
                failures.append(f"No containing box found for single text '{t_str}' at ({tx}, {ty})")
    else:
        # Multiple tspans
        base_x = float(text.attrib.get('x', 0))
        cur_y = float(text.attrib.get('y', 0))
        for tsp in tspans:
            t_str = tsp.text.strip()
            tsp_x = float(tsp.attrib.get('x', base_x))
            dy = float(tsp.attrib.get('dy', 0))
            cur_y += dy
            w = len(t_str) * 0.60 * fs
            if anchor == 'middle':
                x_start = tsp_x - w / 2
                x_end = tsp_x + w / 2
            else:
                x_start = tsp_x
                x_end = tsp_x + w
            
            top_y = cur_y - fs
            bot_y = cur_y + 0.25 * fs
            
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
                print(f"PASS (tspan): '{t_str}' pad=({pad_l:.1f}, {pad_r:.1f}, {pad_t:.1f}, {pad_b:.1f})")
                if min(pad_l, pad_r) < 16.0:
                    failures.append(f"Horiz pad < 16: '{t_str}' ({pad_l:.1f}, {pad_r:.1f})")
                if min(pad_t, pad_b) < 0:
                    failures.append(f"Vertical overflow: '{t_str}' ({pad_t:.1f}, {pad_b:.1f})")
            else:
                failures.append(f"No containing box found for tspan '{t_str}' at ({tsp_x}, {cur_y})")

print(f"\nTotal checks done. Failures: {len(failures)}")
for f in failures:
    print(f"  FAILED: {f}")

assert len(failures) == 0, "Some text checks failed!"
print("\nALL TEXT LINES PERFECTLY BOUNDED AND PADDED!")
