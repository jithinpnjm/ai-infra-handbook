# Verification of all layout parameters and rules

y_title_top = 40
y_title_l1 = 70
y_title_l2 = 112
y_title_bot = 120

# Gap 1: Title to Shared Nodes Bar
gap_title = 28
shared_y = y_title_bot + gap_title # 148
shared_h = 56
shared_bot = shared_y + shared_h # 204

# Gap 2: Shared Nodes Bar to Lane 1
gap_shared = 40
lane1_y = shared_bot + gap_shared # 244
lane1_h = 200
lane1_bot = lane1_y + lane1_h # 444

# Gap 3: Lane 1 to Lane 2
gap_lane1 = 40
lane2_y = lane1_bot + gap_lane1 # 484
lane2_h = 272
lane2_bot = lane2_y + lane2_h # 756

# Gap 4: Lane 2 to Lane 3
gap_lane2 = 40
lane3_y = lane2_bot + gap_lane2 # 796
lane3_h = 122
lane3_bot = lane3_y + lane3_h # 918

# Gap 5: Lane 3 to Footer Box
gap_lane3 = 40
footer_y = lane3_bot + gap_lane3 # 958
footer_h = 136
footer_bot = footer_y + footer_h # 1094

# Gap 6: Footer Box to Takeaway Bar
gap_footer = 40
takeaway_y = footer_bot + gap_footer # 1134
takeaway_h = 46
takeaway_bot = takeaway_y + takeaway_h # 1180

# Bottom margin to canvas height 1220?
# Wait! takeaway_bot = 1180!
# If canvas height is 1200:
# 1200 - 1180 = 20px!
# But bottom margin needs to be 40px! (1200 - 40 = 1160)
# So takeaway_bot MUST be <= 1160!
print("Over budget by:", 1180 - 1160, "px")
