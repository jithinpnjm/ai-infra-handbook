# Total span for staircase: x = 50 to 1380 (1330 px).
# Available height for staircase: y = 330 to 770 (440 px).
#
# We have 6 steps: S1, S2, S3, S4, S5, S6
# We have 5 diamonds: D1, D2, D3, D4, D5
#
# Let's check widths:
# S1..S6: width W_s
# D1..D5: width W_d
# Gaps = G
# 6 * W_s + 5 * W_d + 10 * G = 1330 px.
#
# If W_s = 140, W_d = 80:
# 6 * 140 = 840
# 5 * 80 = 400
# 840 + 400 = 1240 px.
# Remaining for 10 gaps = 1330 - 1240 = 90 px -> G = 9 px.
# But wait! Can W_s = 140 fit "Shadow traffic" with 16px pad?
# Let's test what font-size gives 16px pad:
# At fs = 30: len("traffic") = 7. 7 * 0.6 * 30 = 126 px.
# 126 + 32 = 158 px.
# So at fs = 30, W_s must be >= 158 px!
# What if W_s = 158 px:
# 6 * 158 = 948 px.
# 1330 - 948 = 382 px for 5 diamonds and 10 gaps.
# 382 / 5 = 76.4 px per diamond!
# If diamond is 76 px, can "gates pass" fit?
# "gates" at 24px is 72 px wide! 72 px in 76 px diamond has only 2 px padding!

print("Testing staircase span 1380 math")
