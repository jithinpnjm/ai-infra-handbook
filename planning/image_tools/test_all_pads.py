# Let's test the exact positions and paddings for all 17 boxes:

# Canvas: 1600 x 1200
# Title at y = 55 (font-size 48 bold)

# Box coordinates:
# 1. f1:
# x=40, y=90, w=760, h=110
# text: x=140, y=128, line_height=28
# line 1: "[gpu] "
# line 2: "gpu01 ansible_host=10.0.10.11, " (30 chars)
# line 3: "gpu02 ansible_host=10.0.10.12" (29 chars)
# top_pad = 128 - 19.2 - 90 = 18.8 >= 16
# bot_pad = (90 + 110) - (128 + 2*28 + 6) = 200 - 190 = 10 < 16!
# Ah! Look: 128 + 2*28 + 6 = 190. 200 - 190 = 10.
# If text_y = 125, line_height = 26:
# top_pad = 125 - 19.2 - 90 = 15.8 < 16!
# What if height h = 116?
# If h = 116, text_y = 126, line_height = 26:
# top_pad = 126 - 19.2 - 90 = 16.8 >= 16!
# bot_pad = (90 + 116) - (126 + 52 + 6) = 206 - 184 = 22.0 >= 16!
# Both >= 16!

print("h=116, text_y=126, line_height=26 works!")
