import xml.etree.ElementTree as ET

def verify_box_padding(box_name, box_rect, text_bbox):
    bx, by, bw, bh = box_rect
    tx0, ty0, tx1, ty1 = text_bbox
    
    pad_left = tx0 - bx
    pad_right = (bx + bw) - tx1
    pad_top = ty0 - by
    pad_bottom = (by + bh) - ty1
    
    print(f"{box_name:25s}: L={pad_left:5.1f}, R={pad_right:5.1f}, T={pad_top:5.1f}, B={pad_bottom:5.1f}")
    assert pad_left >= 16.0, f"{box_name}: pad_left {pad_left:.1f} < 16"
    assert pad_right >= 16.0, f"{box_name}: pad_right {pad_right:.1f} < 16"
    assert pad_top >= 16.0, f"{box_name}: pad_top {pad_top:.1f} < 16"
    assert pad_bottom >= 16.0, f"{box_name}: pad_bottom {pad_bottom:.1f} < 16"

print("Padding check function ready")
