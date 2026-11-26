import math

def check_card(card_name, box, icon_box, lines, font_sizes, font_types, start_x, start_y, line_heights):
    bx, by, bw, bh = box
    ix, iy, iw, ih = icon_box
    
    print(f"\n=== Checking {card_name} ===")
    print(f"Box: x={bx}..{bx+bw}, y={by}..{by+bh}, w={bw}, h={bh}")
    print(f"Icon: x={ix}..{ix+iw}, y={iy}..{iy+ih}")
    
    cur_y = start_y
    for i, line in enumerate(lines):
        fs = font_sizes[i]
        ft = font_types[i]
        char_w = 0.62 * fs if ft == 'mono' else 0.60 * fs
        w = len(line) * char_w
        
        tx = start_x
        ty = cur_y
        
        # Check box bounds
        pad_left = tx - bx
        pad_right = (bx + bw) - (tx + w)
        pad_top = ty - by
        pad_bottom = (by + bh) - ty
        
        # Check icon overlap
        # Text bounding box approx: [tx, ty - fs] to [tx + w, ty + 4]
        text_bbox = (tx, ty - fs, tx + w, ty + 4)
        icon_bbox = (ix, iy, ix + iw, iy + ih)
        
        overlap_x = not (text_bbox[2] < icon_bbox[0] or text_bbox[0] > icon_bbox[2])
        overlap_y = not (text_bbox[3] < icon_bbox[1] or text_bbox[1] > icon_bbox[3])
        has_icon_overlap = overlap_x and overlap_y
        
        print(f"  Line {i+1} [{fs}px {ft}]: \"{line[:30]}...\"")
        print(f"    w={w:.1f}px, pos=({tx}, {ty}), pad_L={pad_left:.1f}, pad_R={pad_right:.1f}, pad_B={pad_bottom:.1f}")
        assert pad_left >= 16, f"pad_left {pad_left} < 16 on line {i+1}"
        assert pad_right >= 16, f"pad_right {pad_right} < 16 on line {i+1}"
        assert pad_bottom >= 16, f"pad_bottom {pad_bottom} < 16 on line {i+1}"
        assert not has_icon_overlap, f"Icon overlap on line {i+1}!"
        
        if i < len(line_heights):
            cur_y += line_heights[i]
    print(f"  ALL LINES IN {card_name} PASS PADDING & BOUNDS CHECKS!")

