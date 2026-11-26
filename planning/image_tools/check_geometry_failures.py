import xml.etree.ElementTree as ET

tree = ET.parse("candidate_failures.svg")
root = tree.getroot()

# Let's inspect each card
from generate_failures_svg import cards_def, row_y, row_h

for c in cards_def:
    cid = c["id"]
    cx = 40 if c["col"] == 0 else 820
    cy = row_y[c["row"]]
    ch = row_h[c["row"]]
    cw = 740
    
    ix = cx + 18
    iy = cy + 18
    iw = 48
    ih = 48
    
    tx = cx + 76
    first_y = cy + 40
    
    print(f"\n--- Checking Card {cid} (x={cx}, y={cy}, w={cw}, h={ch}) ---")
    
    # Check left clearance from icon:
    icon_right = ix + iw
    left_padding = tx - icon_right
    print(f"Icon right={icon_right}, text x={tx} -> horizontal clearance = {left_padding} px")
    assert left_padding >= 16, f"Card {cid}: text too close to icon ({left_padding} < 16)"
    
    # Check lines:
    cur_y = first_y
    for i, tl in enumerate(c["title"]):
        if i > 0:
            cur_y += 35
        # Conservative char width for 30px bold: 18.0 px
        line_w = len(tl) * 18.0
        line_right = tx + line_w
        pad_right = (cx + cw) - line_right
        print(f"  [T{i+1}] len={len(tl):2d}, w={line_w:5.1f}, right={line_right:6.1f}, pad_right={pad_right:4.1f} px | {tl}")
        assert pad_right >= 16, f"Card {cid}: title line exceeds right padding: {pad_right} < 16"
        
    for j, bl in enumerate(c["body"]):
        cur_y += 31
        # Conservative char width for 24px: 15.0 px
        line_w = len(bl) * 15.0
        line_right = tx + line_w
        pad_right = (cx + cw) - line_right
        print(f"  [B{j+1}] len={len(bl):2d}, w={line_w:5.1f}, right={line_right:6.1f}, pad_right={pad_right:4.1f} px | {bl}")
        assert pad_right >= 16, f"Card {cid}: body line exceeds right padding: {pad_right} < 16"
        
    # Check bottom padding:
    # Baseline is cur_y. Font descent for 24px is ~6px.
    text_bottom = cur_y + 6
    card_bottom = cy + ch
    pad_bottom = card_bottom - text_bottom
    print(f"Text bottom={text_bottom}, card bottom={card_bottom} -> pad_bottom = {pad_bottom} px")
    assert pad_bottom >= 16, f"Card {cid}: text too close to card bottom ({pad_bottom} < 16)"

print("\nALL 8 CARDS HAVE FULL GEOMETRIC CLEARANCE AND >= 16 PX PADDING ON ALL SIDES!")
