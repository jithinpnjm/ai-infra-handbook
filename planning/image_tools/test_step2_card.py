# In Step 2:
# Label: "./ansible.cfg in the current directory (honoured only if it is not world-writable: a folder any user can change cannot be trusted)"
# Card width = 700. Card x = 60..760.
# Circle: cx=96, cy=card_y + 36, r=24.
# Icon: 56x56 at x=136..192, y=card_y + 8.
# Text can be:
# Line 1: beside icon?
# From x=208 to x=744 (padding 16 from card right edge 760): width = 536 px.
# But what if circle and icon are on the left, and text is wrapped:
# Line 1 (x=208): "./ansible.cfg in the current " (len=29, 29*14.4=417.6 <= 536)
# Line 2 (x=208): "directory" (len=9)
# What if circle and icon are at the top left, and text starts below them?
# If text starts below circle and icon:
# y=card_y + 75.
# Then text has full card width from x=80 to x=744: 664 px width!
# In 664 px width:
# Line 1: "./ansible.cfg in the current directory"
# len=38. Mono w = 38 * 24 * 0.62 = 565.4 px <= 664 px!
# Line 2: "(honoured only if it is not world-writable: "
# len=44. Sans w = 44 * 24 * 0.6 = 633.6 px <= 664 px!
# Line 3: "a folder any user can change "
# len=29. Sans w = 29 * 24 * 0.6 = 417.6 px <= 664 px!
# Line 4: "cannot be trusted)"
# len=18. Sans w = 18 * 24 * 0.6 = 259.2 px <= 664 px!
# That is 4 lines, all starting at x=80, all <= 633.6 px <= 664 px!
# Padding on left = 80 - 60 = 20 px >= 16 px!
# Padding on right = 760 - (80 + 633.6) = 46.4 px >= 16 px!
# Padding on bottom = at least 16 px!
# Let's check card height:
# Top: circle & icon (height ~60px)
# Gap: 15px
# 4 lines * 28px = 112px
# Bottom pad: 16px
# Total card height = 60 + 15 + 112 + 16 = 203px!
print("Layout with icon on top-left works cleanly!")
