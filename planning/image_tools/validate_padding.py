import xml.etree.ElementTree as ET

tree = ET.parse('test_principles.svg')
root = tree.getroot()

card_bounds = {
    'card-1': (40, 160, 480, 280),
    'card-2': (560, 160, 480, 280),
    'card-3': (1080, 160, 480, 280),
    'card-4': (40, 480, 480, 280),
    'card-5': (560, 480, 480, 280),
    'card-6': (1080, 480, 480, 280),
    'card-7': (40, 800, 480, 280),
    'card-8': (560, 800, 480, 280),
    'card-9': (1080, 800, 480, 280),
}

# In each card, icon is translated to (card_x + 20, card_y + 18) with size ~44x44
# So icon bounding box is (card_x + 20, card_y + 18, 44, 44)
for card_id, (cx, cy, cw, ch) in card_bounds.items():
    card_group = root.find(f".//*[@id='{card_id}']")
    icon_box = (cx + 20, cy + 18, 44, 44)
    print(f"\n--- Checking {card_id} ---")
    
    # Check all text elements in this card
    for text_elem in card_group.findall('{http://www.w3.org/2000/svg}text'):
        base_fs = float(text_elem.attrib.get('font-size', '24'))
        base_ff = text_elem.attrib.get('font-family', 'sans-serif')
        base_x = float(text_elem.attrib.get('x', '0'))
        base_y = float(text_elem.attrib.get('y', '0'))
        
        # If it has tspans
        tspans = text_elem.findall('{http://www.w3.org/2000/svg}tspan')
        if not tspans:
            # Single line
            line_txt = text_elem.text or ""
            w = len(line_txt) * (0.62 if base_ff == 'monospace' else 0.6) * base_fs
            left = base_x
            right = left + w
            top = base_y - base_fs * 0.8
            bottom = base_y + base_fs * 0.2
            
            # verify padding
            assert left >= cx + 16, f"Padding fail left: {line_txt} left={left} < {cx+16}"
            assert right <= cx + cw - 16, f"Padding fail right: {line_txt} right={right} > {cx+cw-16}"
            assert top >= cy + 16, f"Padding fail top: {line_txt} top={top} < {cy+16}"
            assert bottom <= cy + ch - 16, f"Padding fail bottom: {line_txt} bottom={bottom} > {cy+ch-16}"
            
            # verify icon overlap
            # overlap if not (right < icon_box[0] or left > icon_box[0]+icon_box[2] or bottom < icon_box[1] or top > icon_box[1]+icon_box[3])
            overlap = not (right < icon_box[0] or left > icon_box[0]+icon_box[2] or bottom < icon_box[1] or top > icon_box[1]+icon_box[3])
            assert not overlap, f"Overlap with icon: {line_txt}"
            print(f"  Line: '{line_txt}' -> pad_l={left-cx:.1f}, pad_r={cx+cw-right:.1f}, pad_t={top-cy:.1f}, pad_b={cy+ch-bottom:.1f}")
        else:
            cur_y = base_y
            for ts in tspans:
                x_attr = ts.attrib.get('x')
                if x_attr:
                    cur_x = float(x_attr)
                dy_attr = ts.attrib.get('dy', '0')
                cur_y += float(dy_attr)
                
                # Check inner tspans if any
                line_w = 0
                line_txt = ""
                # ElementTree iterates children and text
                def get_tspan_width_and_text(elem, parent_fs, parent_ff):
                    w = 0
                    t = elem.text or ""
                    fs = float(elem.attrib.get('font-size', parent_fs))
                    ff = elem.attrib.get('font-family', parent_ff)
                    w += len(t) * (0.62 if ff == 'monospace' else 0.6) * fs
                    for child in elem:
                        child_w, child_t = get_tspan_width_and_text(child, fs, ff)
                        w += child_w
                        t += child_t
                        if child.tail:
                            tail_txt = child.tail
                            w += len(tail_txt) * (0.62 if ff == 'monospace' else 0.6) * fs
                            t += tail_txt
                    return w, t

                line_w, line_txt = get_tspan_width_and_text(ts, base_fs, base_ff)
                left = cur_x
                right = left + line_w
                top = cur_y - base_fs * 0.8
                bottom = cur_y + base_fs * 0.2
                
                assert left >= cx + 16, f"Padding fail left: '{line_txt}' left={left} < {cx+16}"
                assert right <= cx + cw - 16, f"Padding fail right: '{line_txt}' right={right} > {cx+cw-16} (pad={cx+cw-right})"
                assert top >= cy + 16, f"Padding fail top: '{line_txt}' top={top} < {cy+16}"
                assert bottom <= cy + ch - 16, f"Padding fail bottom: '{line_txt}' bottom={bottom} > {cy+ch-16}"
                
                overlap = not (right < icon_box[0] or left > icon_box[0]+icon_box[2] or bottom < icon_box[1] or top > icon_box[1]+icon_box[3])
                assert not overlap, f"Overlap with icon: '{line_txt}' (x={left}..{right}, y={top}..{bottom}) vs icon {icon_box}"
                print(f"  Line: '{line_txt}' -> pad_l={left-cx:.1f}, pad_r={cx+cw-right:.1f}, pad_t={top-cy:.1f}, pad_b={cy+ch-bottom:.1f}")

print("\n✓ ALL TEXT LINES FIT WITH AT LEAST 16PX PADDING AND NO ICON OVERLAP!")
