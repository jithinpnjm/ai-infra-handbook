# Let's optimize:
# Canvas: 1600 x 1200
# Top: Title at y = 54. Ascent ~ 36px -> top of title at y = 18.
# Wait, margin to top edge: 40px outside margin rule:
# "Leave at least 40 px between boxes and 40 px outside margin."
# That means boxes should be at least 40px from canvas edges (x >= 40, x + w <= 1560, y >= 40, y + h <= 1160).
# Box x = 50 >= 40!
# Box x + w = 50 + 1500 = 1550 <= 1560!
# Row 1 by = 98 >= 40!
# Row 7 by + bh <= 1160!
# So we have from y = 98 to 1158 (60px bottom margin!).

boxes = [
    # (name, box_x, box_y, box_w, box_h, text_x, [y_lines], text_w_max, icon_y)
    ("gate_latency", 50, 98, 730, 118, 154, [144, 178], 518.4, 129),
    ("gate_quality", 820, 98, 730, 118, 924, [134, 166, 198], 532.8, 129),
    ("rule_1", 50, 256, 1500, 160, 154, [292, 324, 356, 388], 1238.4, 308),
    ("rule_2", 50, 456, 1500, 72, 154, [501], 892.8, 464),
    ("rule_3", 50, 568, 1500, 102, 154, [610, 642], 1267.2, 591),
    ("rule_4", 50, 710, 1500, 72, 154, [755], 547.2, 718),
    ("rule_cache", 50, 822, 730, 160, 154, [858, 890, 922, 954], 561.6, 874),
    ("rule_router", 820, 822, 730, 160, 924, [874, 906, 938], 576.0, 874),
    ("reason", 50, 1022, 1500, 110, 154, [1068, 1102], 1195.2, 1049)
]

all_pass = True
print("=== CHECKING ALL PADDINGS AND GAPS ===")

for i in range(len(boxes)):
    name, bx, by, bw, bh, tx, y_lines, tw, iy = boxes[i]
    icon_gap = tx - (bx + 80)
    right_pad = (bx + bw) - (tx + tw)
    top_pad = (y_lines[0] - 19) - by
    bot_pad = (by + bh) - (y_lines[-1] + 6)
    
    # icon padding
    icon_top_pad = iy - by
    icon_bot_pad = (by + bh) - (iy + 56)
    
    print(f"\n{name}:")
    print(f"  Icon gap: {icon_gap:.1f}px, Right pad: {right_pad:.1f}px")
    print(f"  Top pad: {top_pad:.1f}px, Bot pad: {bot_pad:.1f}px")
    print(f"  Icon top: {icon_top_pad:.1f}px, Icon bot: {icon_bot_pad:.1f}px")
    
    if min(icon_gap, right_pad, top_pad, bot_pad, icon_top_pad, icon_bot_pad) < 16:
        print("  FAILED PADDING CHECK!")
        all_pass = False

print("\n=== CHECKING GAPS BETWEEN ROWS ===")
row_ends = [
    ("Row 1 (Gates)", 98, 118),
    ("Row 2 (Rule 1)", 256, 160),
    ("Row 3 (Rule 2)", 456, 72),
    ("Row 4 (Rule 3)", 568, 102),
    ("Row 5 (Rule 4)", 710, 72),
    ("Row 6 (Rules cache/router)", 822, 160),
    ("Row 7 (Takeaway)", 1022, 110)
]

for i in range(len(row_ends) - 1):
    r1_name, r1_y, r1_h = row_ends[i]
    r2_name, r2_y, r2_h = row_ends[i+1]
    gap = r2_y - (r1_y + r1_h)
    print(f"Gap between {r1_name} and {r2_name}: {gap}px (need >= 40)")
    if gap < 40:
        all_pass = False

H = 1200
last_y = row_ends[-1][1] + row_ends[-1][2]
bot_margin = H - last_y
print(f"\nBottom canvas margin: {bot_margin}px (need >= 40)")
if bot_margin < 40:
    all_pass = False

print(f"\nOVERALL RESULT: {'PASS' if all_pass else 'FAIL'}")
