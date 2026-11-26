# Let's verify padding >= 16px strictly taking into account font ascent (19px) and descent (6px) for 24px font.

boxes = [
    # (name, box_x, box_y, box_w, box_h, text_x, [y_lines], text_w_max)
    ("gate_latency", 50, 110, 730, 120, 154, [155, 189], 518.4),
    ("gate_quality", 820, 110, 730, 120, 924, [146, 177, 208], 532.8),
    ("rule_1", 50, 270, 1500, 165, 154, [308, 340, 372, 404], 1238.4),
    ("rule_2", 50, 475, 1500, 75, 154, [520], 892.8),
    ("rule_3", 50, 590, 1500, 105, 154, [633, 665], 1267.2),
    ("rule_4", 50, 735, 1500, 75, 154, [780], 547.2),
    ("rule_cache", 50, 850, 730, 165, 154, [888, 920, 952, 984], 561.6),
    ("rule_router", 820, 850, 730, 165, 924, [904, 936, 968], 576.0),
    ("reason", 50, 1055, 1500, 110, 154, [1100, 1134], 1195.2)
]

print("=== CHECKING ALL PADDINGS AND GAPS ===")
all_pass = True

for i in range(len(boxes)):
    name, bx, by, bw, bh, tx, y_lines, tw = boxes[i]
    
    # Left padding from text start to box left
    # But note: icon is between box_x and text_x!
    # Icon width = 56px, at bx + 24 -> ends at bx + 80.
    # Text starts at tx = bx + 104 -> gap from icon is 24px >= 16px!
    icon_gap = tx - (bx + 80)
    
    # Right padding
    right_pad = (bx + bw) - (tx + tw)
    
    # Top padding (ascent ~ 19px for fs=24)
    top_pad = (y_lines[0] - 19) - by
    
    # Bottom padding (descent ~ 6px for fs=24)
    bot_pad = (by + bh) - (y_lines[-1] + 6)
    
    print(f"\n{name}:")
    print(f"  Icon gap: {icon_gap:.1f}px (need >= 16)")
    print(f"  Right pad: {right_pad:.1f}px (need >= 16)")
    print(f"  Top pad: {top_pad:.1f}px (need >= 16)")
    print(f"  Bottom pad: {bot_pad:.1f}px (need >= 16)")
    
    if min(icon_gap, right_pad, top_pad, bot_pad) < 16:
        print("  FAILED PADDING CHECK!")
        all_pass = False

print("\n=== CHECKING GAPS BETWEEN ROWS ===")
row_ends = [
    ("Row 1 (Gates)", 110, 120),
    ("Row 2 (Rule 1)", 270, 165),
    ("Row 3 (Rule 2)", 475, 75),
    ("Row 4 (Rule 3)", 590, 105),
    ("Row 5 (Rule 4)", 735, 75),
    ("Row 6 (Rules cache/router)", 850, 165),
    ("Row 7 (Takeaway)", 1055, 110)
]

for i in range(len(row_ends) - 1):
    r1_name, r1_y, r1_h = row_ends[i]
    r2_name, r2_y, r2_h = row_ends[i+1]
    gap = r2_y - (r1_y + r1_h)
    print(f"Gap between {r1_name} and {r2_name}: {gap}px (need >= 40)")
    if gap < 40:
        all_pass = False

last_y = row_ends[-1][1] + row_ends[-1][2]
H = 1200
bot_margin = H - last_y
print(f"\nBottom canvas margin: {bot_margin}px (need >= 40)")
if bot_margin < 40:
    all_pass = False

print(f"\nOVERALL RESULT: {'PASS' if all_pass else 'FAIL'}")
