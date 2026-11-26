from test_card_paddings import check_panel

# Centre badge:
# x=400, y=510, w=800, h=52
# Text: "A method gives you a shape, not a guarantee" (43 chars)
# text-anchor="middle", x=800, baseline=544
# fs = 26 bold
badge_txt = "A method gives you a shape, not a guarantee"
w_badge = len(badge_txt) * (0.6 * 26) # 670.8 px
left_pad = 800 - w_badge / 2 - 400
right_pad = 1200 - (800 + w_badge / 2)
top_pad = (544 - 26) - 510
bottom_pad = 562 - (544 + 0.25 * 26)
print(f"Badge: left={left_pad:.1f}, right={right_pad:.1f}, top={top_pad:.1f}, bottom={bottom_pad:.1f}")
assert left_pad >= 16 and right_pad >= 16 and top_pad >= 16 and bottom_pad >= 16

# Footer strip:
# x=50, y=960, w=1500, h=152
# Lines (4):
# line 1: baseline = 960 + 36 = 996
# line 2: baseline = 996 + 28 = 1024
# line 3: baseline = 1024 + 28 = 1052
# line 4: baseline = 1052 + 28 = 1080
# text_x = 75
check_panel('Footer', 'box', (50, 960, 1500, 152), 75, [996, 1024, 1052, 1080], 24, [
    "Common mistakes: favourite tool first, tunables changed without a hypothesis or baseline,",
    "several changes at once, failed experiments not reverted, trusting GPU-Util or load average as a",
    "verdict, optimising off the critical path, benchmarking the load generator or a warm cache,",
    "ignoring corrected ECC, link retrains and PCIe replays"
])
print("Footer checks passed!")

# Bottom bar:
# x=50, y=1126, w=1500, h=56
# Text: "Check that your fix explains the bulk of the symptom before you close an investigation"
# text-anchor="middle", x=800, baseline = 1162
# fs = 24 bold
bar_txt = "Check that your fix explains the bulk of the symptom before you close an investigation"
w_bar = len(bar_txt) * (0.6 * 24) # 1238.4 px
left_pad = 800 - w_bar / 2 - 50
right_pad = 1550 - (800 + w_bar / 2)
top_pad = (1162 - 24) - 1126
bottom_pad = (1126 + 56) - (1162 + 0.25 * 24)
print(f"Bottom bar: left={left_pad:.1f}, right={right_pad:.1f}, top={top_pad:.1f}, bottom={bottom_pad:.1f}")
assert left_pad >= 16 and right_pad >= 16 and top_pad >= 16 and bottom_pad >= 16
print("Bottom bar checks passed!")
