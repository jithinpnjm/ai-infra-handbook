# Let's verify coordinates, text padding, and icon clearance for all nodes.

def check_node(name, bx, by, bw, bh, icon_box, text_lines):
    # icon_box = (ix, iy, iw, ih)
    # text_lines = [(line_text, fs, font_type, tx, ty, align)]
    print(f"Checking {name}...")
    # Check box within canvas
    if bx < 40 or bx + bw > 1560:
        print(f"  WARNING: {name} outside canvas margins! bx={bx}, bw={bw}")
    if by < 40 or by + bh > 1160:
        print(f"  WARNING: {name} outside canvas margins! by={by}, bh={bh}")
        
    ix, iy, iw, ih = icon_box
    # Check icon inside box
    if ix < bx or ix + iw > bx + bw or iy < by or iy + ih > by + bh:
        print(f"  WARNING: {name} icon outside box! icon={icon_box}, box={(bx,by,bw,bh)}")
        
    # Check each text line
    for text, fs, font_type, tx, ty, align in text_lines:
        coeff = 0.62 if font_type == 'mono' else 0.60
        tw = len(text) * coeff * fs
        if align == 'middle':
            lx = tx - tw / 2
            rx = tx + tw / 2
        elif align == 'start':
            lx = tx
            rx = tx + tw
        
        # Check padding from box edge
        if lx - bx < 16 or (bx + bw) - rx < 16:
            print(f"  WARNING: {name} text '{text}' fails box padding! left_pad={lx-bx:.1f}, right_pad={(bx+bw)-rx:.1f}")
            
        # Check overlap with icon:
        # text bounding box: x in [lx, rx], y in [ty - fs, ty + 4]
        # icon bounding box: x in [ix, ix+iw], y in [iy, iy+ih]
        overlap_x = max(lx, ix) < min(rx, ix + iw)
        overlap_y = max(ty - fs, iy) < min(ty + 4, iy + ih)
        if overlap_x and overlap_y:
            print(f"  WARNING: {name} text '{text}' OVERLAPS ICON!")

print("Overlap checker ready")
