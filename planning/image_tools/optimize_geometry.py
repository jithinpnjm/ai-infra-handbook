import xml.etree.ElementTree as ET

# We will optimize the box positions and heights:
# In Column 1 (x=40, y=135, w=480, h=560):
#   Card 1 (methods): 3 lines (y, y+32, y+64). Total text height = 64 + fs + 0.25*fs = 94px.
#     With 18px top pad, 18px bot pad: Card height = 94 + 36 = 130px.
#     text y = ry + 18 + fs = ry + 42.
#     bot_y = (ry + 42 + 64) + 6 = ry + 112.
#     pad_b = ry + 130 - (ry + 112) = 18px. Perfect!

#   Card 2 (status codes): 2 lines (y, y+32). Text height = 32 + 24 + 6 = 62px.
#     Card height = 62 + 36 = 98px.
#     text y = ry + 18 + 24 = ry + 42.
#     bot_y = ry + 42 + 32 + 6 = ry + 80.
#     pad_b = ry + 98 - (ry + 80) = 18px. Perfect!

#   Card 3 (exceptions): 5 lines (y, y+30, y+60, y+90, y+120). Text height = 120 + 24 + 6 = 150px.
#     Card height = 150 + 36 = 186px.
#     text y = ry + 18 + 24 = ry + 42.
#     bot_y = ry + 42 + 120 + 6 = ry + 168.
#     pad_b = ry + 186 - (ry + 168) = 18px. Perfect!

# Total col 1 cards: 130 + 98 + 186 = 414px.
# Gaps: 15px.
# Header: 135 to 215 (80px).
# Card 1: 220 to 350 (h=130)
# Card 2: 362 to 460 (h=98)
# Card 3: 472 to 658 (h=186)
# Bottom of Card 3: 658. Column bottom: 685 (margin 27px).

# In Column 2 (x=560, y=135, w=480, h=560):
#   Card 1 (4xx status): 4 lines (y, y+32, y+64, y+96). Text height = 96 + 30 = 126px.
#     Card height = 126 + 36 = 162px.
#     text y = ry + 42.
#     bot_y = ry + 42 + 96 + 6 = ry + 144.
#     pad_b = ry + 162 - (ry + 144) = 18px.
#   Card 2 (POST without idempotency): 2 lines (y, y+32). Text height = 32 + 30 = 62px.
#     Card height = 98px.
#     text y = ry + 42.

# In Column 3 (x=1080, y=135, w=480, h=560):
#   We have 5 cards!
#   Card 1: retry_if_exception (2 lines, dy=28). Text height = 28 + 30 = 58px.
#     Card height = 58 + 34 = 92px.
#     text y = ry + 41. (pad_t = 41 - 24 = 17, bot_y = ry + 41 + 28 + 6 = ry + 75, pad_b = 92 - 75 = 17).
#   Card 2: wait_exponential_jitter (4 lines, dy=28). Text height = 3*28 + 30 = 114px.
#     Card height = 114 + 34 = 148px.
#     text y = ry + 41.
#   Card 3: stop_after (2 lines, dy=28). Text height = 58px.
#     Card height = 92px.
#   Card 4: before_sleep_log (2 lines, dy=28). Text height = 58px.
#     Card height = 92px.
#   Card 5: reraise=True (1 line). Text height = 30px.
#     Card height = 30 + 34 = 64px.
#     text y = ry + 41.
# Total height in Col 3: 92 + 148 + 92 + 92 + 64 = 488px.
# Plus gaps between cards: 5 cards have 4 gaps. 4 * 10 = 40px.
# 488 + 40 = 528px!
# Plus header 75px -> total 603px!
# So Column height can be 620px! (y=130 to 750, h=620).

print("Computing exact geometry...")
