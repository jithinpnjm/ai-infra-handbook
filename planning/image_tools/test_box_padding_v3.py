def check_box(name, box_y, box_h, lines):
    ascent0 = lines[0][1] * 0.8
    descent_last = lines[-1][1] * 0.2
    sum_lh = sum([l[2] for l in lines[:-1]])
    text_h = ascent0 + sum_lh + descent_last
    
    extra = box_h - text_h
    pad_top = extra / 2.0
    pad_bot = extra / 2.0
    
    first_baseline = box_y + pad_top + ascent0
    last_baseline = first_baseline + sum_lh
    
    top_edge = first_baseline - ascent0
    bot_edge = last_baseline + descent_last
    
    actual_top = top_edge - box_y
    actual_bot = (box_y + box_h) - bot_edge
    
    print(f"{name:12}: y={box_y:4}..{box_y+box_h:4} (h={box_h:3}), text_h={text_h:5.1f}, pad_top={actual_top:4.1f}, pad_bot={actual_bot:4.1f}, baseline0={first_baseline:5.1f}")
    assert actual_top >= 16.0, f"{name} top padding {actual_top} < 16"
    assert actual_bot >= 16.0, f"{name} bottom padding {actual_bot} < 16"
    return first_baseline

y1 = check_box("Step 1", 72, 102, [
    ("line 1", 30, 34),
    ("line 2", 24, 0)
])

y2 = check_box("Step 2", 184, 204, [
    ("line 1", 30, 32),
    ("line 2", 24, 27),
    ("line 3", 24, 27),
    ("line 4", 24, 27),
    ("line 5", 24, 27),
    ("line 6", 24, 0)
])

y3 = check_box("Step 3", 398, 204, [
    ("line 1", 30, 32),
    ("line 2", 24, 27),
    ("line 3", 24, 27),
    ("line 4", 24, 27),
    ("line 5", 24, 27),
    ("line 6", 24, 0)
])

y4 = check_box("Step 4", 612, 122, [
    ("line 1", 30, 32),
    ("line 2", 24, 28),
    ("line 3", 24, 0)
])

y5 = check_box("Step 5", 744, 122, [
    ("line 1", 30, 32),
    ("line 2", 24, 28),
    ("line 3", 24, 0)
])

ys = check_box("Strip", 878, 218, [
    ("line 1", 24, 26),
    ("line 2", 24, 26),
    ("line 3", 24, 26),
    ("line 4", 24, 26),
    ("line 5", 24, 26),
    ("line 6", 24, 26),
    ("line 7", 24, 0)
])

yb = check_box("Bottom bar", 1108, 60, [
    ("line 1", 25, 0)
])

print("\nSUCCESS: All boxes have padding >= 16px! Total height: 1108 + 60 = 1168 (margin 32px).")
