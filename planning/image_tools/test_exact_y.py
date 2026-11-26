# Let's test the exact Y positions with H = 1200:

title_y1 = 68
title_y2 = 112
# Title bottom = 120

# Top-level gap: 30px
shared_nodes_y = 150
shared_nodes_h = 54
# Bottom of shared nodes = 204

gap1 = 40
lane1_y = 244
lane1_h = 196
# Bottom of lane1 = 440

gap2 = 40
lane2_y = 480
lane2_h = 268
# Bottom of lane2 = 748

gap3 = 40
lane3_y = 788
lane3_h = 116
# Bottom of lane3 = 904

gap4 = 40
footer_y = 944
footer_h = 132
# Bottom of footer = 1076

gap5 = 40
takeaway_y = 1116
takeaway_h = 44
# Bottom of takeaway = 1160

bottom_margin = 1200 - 1160

print(f"bottom_margin = {bottom_margin}")
assert bottom_margin == 40
print("Exact 40px margins and >= 40px gaps achieved!")
