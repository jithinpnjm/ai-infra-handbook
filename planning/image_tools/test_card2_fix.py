# Card 2 coordinates and text lines:
card_x = 60
card_w = 700
card_r = card_x + card_w # 760
card_y = 318
card_h = 184 # let's give it 184px height: y=318..502
# Then Step 3 card can be y=512..568 (h=56), Step 4 card can be y=578..634 (h=56)
# Bottom of ladder 1: 642.

# Let's check text lines in Card 2:
# Icon: x=130..186, y=328..384 (height 56px)
# Circle: cx=94, cy=356, r=24
# Line 1: x=202, y=348: "./ansible.cfg " (14 chars mono)
w1 = 14 * 24 * 0.62
end1 = 202 + w1
pad1 = card_r - end1
print(f"Line 1: end={end1:.1f}, pad_r={pad1:.1f}")

# Line 2: x=202, y=376: "in the current directory " (25 chars sans)
w2 = 25 * 24 * 0.6
end2 = 202 + w2
pad2 = card_r - end2
print(f"Line 2: end={end2:.1f}, pad_r={pad2:.1f}")

# Line 3: x=76, y=412: "(honoured only if it is not world-writable: " (44 chars sans)
w3 = 44 * 24 * 0.6
end3 = 76 + w3
pad3 = card_r - end3
print(f"Line 3: end={end3:.1f}, pad_r={pad3:.1f}")

# Line 4: x=76, y=442: "a folder any user can change " (29 chars sans)
w4 = 29 * 24 * 0.6
end4 = 76 + w4
pad4 = card_r - end4
print(f"Line 4: end={end4:.1f}, pad_r={pad4:.1f}")

# Line 5: x=76, y=472: "cannot be trusted)" (18 chars sans)
w5 = 18 * 24 * 0.6
end5 = 76 + w5
pad5 = card_r - end5
print(f"Line 5: end={end5:.1f}, pad_r={pad5:.1f}")

# Vertical padding:
# Card top = 318
# Line 1 baseline = 348 -> cap height ~ 348 - 18 = 330. Pad top = 330 - 318 = 12px? Wait! Let's check icon top:
# Icon top = 328 -> 328 - 318 = 10px? We want at least 16px!
# If card_y = 318, icon y = 334 (pad = 16px).
# Line 1 baseline = 352 (cap height ~334).
# Line 2 baseline = 380.
# Line 3 baseline = 416.
# Line 4 baseline = 446.
# Line 5 baseline = 476 -> descent ~ 476 + 6 = 482.
# Card bottom = 502 -> pad bottom = 502 - 482 = 20px >= 16px!
print("All paddings >= 16px!")
