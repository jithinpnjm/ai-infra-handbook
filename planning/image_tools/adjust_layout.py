import xml.etree.ElementTree as ET

# Let's adjust candidate layout for Card 1
# Card 1 height: 875
# Icon + title: y=140..195
# Divider line: y=205
# Log snippet container: y=225..510 (height 285)
#   Inside:
#   Line 1 box: x=88, y=240, width=384, height=110
#   Text: tx=110, y=270, dy=30
#     slurmctld: error:
#     Nodes dgx-h100-14
#     not responding
#   pad_left = 110 - 88 = 22px
#   pad_right = 472 - (110 + 253) = 109px
#   top_pad = (270 - 24) - 240 = 6px? WAIT!
#   In SVG, y is baseline!
#   If font-size is 24, text height is approx from y-20 to y+4.
#   So if text y = 270:
#   Top of text is at y = 270 - 20 = 250.
#   Box top is 240. Top pad = 250 - 240 = 10px.
#   To have top pad >= 16px:
#   First line baseline should be at y = 240 + 16 + 20 = 276 (say y = 276 or 278)!
#   Last line baseline (3 lines): 278 + 30 + 30 = 338.
#   Bottom of text: 338 + 5 = 343.
#   Box bottom: 365. Bottom pad = 365 - 343 = 22px!
#   So box height = 125 (y = 240 to 365)!
