# Verify 6 separate boxes with 40px gaps:
# Canvas: 1600 x 1200

title_top = 40
title_l1 = 68
title_l2 = 112
title_bot = 115

gap0 = 40 # title to box 1
b1_y = title_bot + gap0 # 155
b1_h = 50 # Shared Host bar
b1_bot = b1_y + b1_h # 205

gap1 = 40
b2_y = b1_bot + gap1 # 245
b2_h = 195 # Lane 1
b2_bot = b2_y + b2_h # 440

gap2 = 40
b3_y = b2_bot + gap2 # 480
b3_h = 265 # Lane 2
b3_bot = b3_y + b3_h # 745

gap3 = 40
b4_y = b3_bot + gap3 # 785
b4_h = 115 # Lane 3
b4_bot = b4_y + b4_h # 900

gap4 = 40
b5_y = b4_bot + gap4 # 940
b5_h = 135 # Footer box
b5_bot = b5_y + b5_h # 1075

gap5 = 40
b6_y = b5_bot + gap5 # 1115
b6_h = 45 # Takeaway bar
b6_bot = b6_y + b6_h # 1160

margin_bot = 1200 - b6_bot

print("Box 1 (Host bar):", b1_y, "to", b1_bot, "h=", b1_h)
print("Box 2 (Lane 1):", b2_y, "to", b2_bot, "h=", b2_h)
print("Box 3 (Lane 2):", b3_y, "to", b3_bot, "h=", b3_h)
print("Box 4 (Lane 3):", b4_y, "to", b4_bot, "h=", b4_h)
print("Box 5 (Footer):", b5_y, "to", b5_bot, "h=", b5_h)
print("Box 6 (Takeaway):", b6_y, "to", b6_bot, "h=", b6_h)
print("Margin bottom:", margin_bot)
assert margin_bot == 40
print("PERFECT! Every single gap is EXACTLY 40px, bottom margin is EXACTLY 40px!")
