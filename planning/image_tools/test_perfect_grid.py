# Verify all boxes with exact 40px margins and 40px gaps

title_top = 76 - 48*0.75 # 40.0
title_l1 = 76
title_l2 = 120
title_bot = 120 + 48*0.16 # 128.0

gap0 = 40.0
b1_y = 168.0 # Shared Host bar
b1_h = 56.0
b1_bot = b1_y + b1_h # 224.0

gap1 = 40.0
b2_y = b1_bot + gap1 # 264.0 (Lane 1)
b2_h = 186.0
b2_bot = b2_y + b2_h # 450.0

gap2 = 40.0
b3_y = b2_bot + gap2 # 490.0 (Lane 2)
b3_h = 236.0
b3_bot = b3_y + b3_h # 726.0

gap3 = 40.0
b4_y = b3_bot + gap3 # 766.0 (Lane 3)
b4_h = 114.0
b4_bot = b4_y + b4_h # 880.0

gap4 = 40.0
b5_y = b4_bot + gap4 # 920.0 (Footer Box)
b5_h = 140.0
b5_bot = b5_y + b5_h # 1060.0

gap5 = 44.0 # can be 40 to 44
b6_y = 1104.0 # Takeaway Bar
b6_h = 56.0
b6_bot = b6_y + b6_h # 1160.0

bot_margin = 1200.0 - b6_bot

print(f"Top margin: {title_top:.1f}")
print(f"Gap 0 (Title to Box 1): {b1_y - title_bot:.1f}")
print(f"Box 1: {b1_y}..{b1_bot} (h={b1_h})")
print(f"Gap 1: {b2_y - b1_bot:.1f}")
print(f"Box 2: {b2_y}..{b2_bot} (h={b2_h})")
print(f"Gap 2: {b3_y - b2_bot:.1f}")
print(f"Box 3: {b3_y}..{b3_bot} (h={b3_h})")
print(f"Gap 3: {b4_y - b3_bot:.1f}")
print(f"Box 4: {b4_y}..{b4_bot} (h={b4_h})")
print(f"Gap 4: {b5_y - b4_bot:.1f}")
print(f"Box 5: {b5_y}..{b5_bot} (h={b5_h})")
print(f"Gap 5: {b6_y - b5_bot:.1f}")
print(f"Box 6: {b6_y}..{b6_bot} (h={b6_h})")
print(f"Bottom margin: {bot_margin:.1f}")

assert title_top >= 40
assert b1_y - title_bot >= 40
assert b2_y - b1_bot >= 40
assert b3_y - b2_bot >= 40
assert b4_y - b3_bot >= 40
assert b5_y - b4_bot >= 40
assert b6_y - b5_bot >= 40
assert bot_margin >= 40
print("EVERY SINGLE MARGIN AND GAP IS AT LEAST 40PX!")
