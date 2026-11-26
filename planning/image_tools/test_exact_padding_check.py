import re

# Let's test each box and text line's exact clearance:

# 1. Ladder 1 Header:
# Container x=40..780. Header bar y=152..232.
# Text: x=60.
# Line 1: "Which file is read " (len=19, fs=30 sans)
# w1 = 19 * 30 * 0.6 = 342.0. End x = 60 + 342 = 402 <= 780 - 16 = 764. (Pad right = 362px!)
# Line 2: "(first found wins, never merged)" (len=32, fs=30 sans)
# w2 = 32 * 30 * 0.6 = 576.0. End x = 60 + 576 = 636 <= 764. (Pad right = 128px!)
# Baseline y=188, 222. Header bar top=152, bottom=232.
# Line 1 top ~ 188 - 24 = 164 >= 152 + 12. Bottom ~ 222 + 6 = 228 <= 232.

# 2. Ladder 1 Step 1 Card:
# Card: x=60..760 (w=700), y=244..308 (h=64)
# Circle: cx=94, r=24 -> spans x=70..118.
# Icon: x=130..182 (w=52)
# Text: x=202, y=284.
# Line: "ANSIBLE_CONFIG environment variable"
# "ANSIBLE_CONFIG " (15 mono): 15 * 24 * 0.62 = 223.2
# "environment variable" (20 sans): 20 * 24 * 0.6 = 288.0
# Total w = 223.2 + 288.0 = 511.2 px.
# End x = 202 + 511.2 = 713.2 <= 760 - 16 = 744. (Pad right = 30.8px >= 16px!)
# Left pad from icon: 202 - 182 = 20px >= 16px!
# Top pad: 284 - 18 = 266 >= 244 + 16 (22px).
# Bottom pad: 308 - (284 + 5) = 19px >= 16px!

# 3. Ladder 1 Step 2 Card:
# Card: x=60..760 (w=700), y=318..490 (h=172)
# Circle: cx=94, cy=354, r=24.
# Icon: x=130..186, y=326..376.
# Text:
# Line 1: "./ansible.cfg in the current directory "
# x=202, y=352.
# "./ansible.cfg " (14 mono): 14 * 24 * 0.62 = 208.32
# "in the current directory " (25 sans): 25 * 24 * 0.6 = 360.0
# Total w = 208.32 + 360.0 = 568.32. End x = 202 + 568.32 = 770.32 ???
# WAIT! 770.32 > 744!
print(f"WARNING: Ladder 1 Step 2 Line 1 end x = {202 + 568.32} > 744!")

