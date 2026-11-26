boxes = [
    # (name, box_x, box_y, box_w, box_h, text_x, [y_lines], text_w_max, icon_y)
    ("gate_latency", 50, 105, 730, 116, 154, [152, 184], 518.4, 135),
    ("gate_quality", 820, 105, 730, 116, 924, [142, 172, 202], 532.8, 135),
    ("rule_1", 50, 261, 1500, 150, 154, [298, 328, 358, 388], 1238.4, 308),
    ("rule_2", 50, 451, 1500, 88, 154, [502], 892.8, 467),
    ("rule_3", 50, 579, 1500, 96, 154, [624, 654], 1267.2, 599),
    ("rule_4", 50, 715, 1500, 88, 154, [766], 547.2, 731),
    ("rule_cache", 50, 843, 730, 150, 154, [880, 910, 940, 970], 561.6, 890),
    ("rule_router", 820, 843, 730, 150, 924, [894, 924, 954], 576.0, 890),
    ("reason", 50, 1033, 1500, 100, 154, [1078, 1110], 1195.2, 1055)
]

all_pass = True
print("=== CHECKING ALL PADDINGS AND GAPS ===")

for i in range(len(boxes)):
    name, bx, by, bw, bh, tx, y_lines, tw, iy = boxes[i]
    icon_gap = tx - (bx + 80)
    right_pad = (bx + bw) - (tx + tw)
    top_pad = (y_lines[0] - 19) - by
    bot_pad = (by + bh) - (y_lines[-1] + 6)
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
    ("Row 1 (Gates)", 105, 116),
    ("Row 2 (Rule 1)", 261, 150),
    ("Row 3 (Rule 2)", 451, 88),
    ("Row 4 (Rule 3)", 579, 96),
    ("Row 5 (Rule 4)", 715, 88),
    ("Row 6 (Rules cache/router)", 843, 150),
    ("Row 7 (Takeaway)", 1033, 100)
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
