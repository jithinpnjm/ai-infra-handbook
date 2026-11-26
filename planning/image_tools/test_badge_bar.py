# Centre badge:
# x=380, y=508, w=840, h=70, rx=35
badge_txt = "A method gives you a shape, not a guarantee"
w_badge = len(badge_txt) * (0.6 * 26) # 670.8 px
left_pad = 800 - w_badge / 2 - 380
right_pad = (380 + 840) - (800 + w_badge / 2)
bl = 550
top_pad = (bl - 26) - 508
bottom_pad = (508 + 70) - (bl + 0.25 * 26)
print(f"Badge: left={left_pad:.1f}, right={right_pad:.1f}, top={top_pad:.1f}, bottom={bottom_pad:.1f}")
assert left_pad >= 16 and right_pad >= 16 and top_pad >= 16 and bottom_pad >= 16

# Bottom bar:
# x=50, y=1120, w=1500, h=66, rx=14
bar_txt = "Check that your fix explains the bulk of the symptom before you close an investigation"
w_bar = len(bar_txt) * (0.6 * 24) # 1238.4 px
left_pad = 800 - w_bar / 2 - 50
right_pad = 1550 - (800 + w_bar / 2)
bl_bar = 1161
top_pad = (bl_bar - 24) - 1120
bottom_pad = (1120 + 66) - (bl_bar + 0.25 * 24)
print(f"Bottom bar: left={left_pad:.1f}, right={right_pad:.1f}, top={top_pad:.1f}, bottom={bottom_pad:.1f}")
assert left_pad >= 16 and right_pad >= 16 and top_pad >= 16 and bottom_pad >= 16
print("Both Badge and Bottom bar passed!")
