import re

# Canvas: 1600 x 1200
# Margins: 40px everywhere

# Title:
# line 1: y = 88 (top ~ 45, fs=48 bold)
# line 2: dy = 54 -> y = 142 (bottom ~ 154)

# Columns: y = 175 to 965 (h = 790)

# Column 1 items:
# Header: icon at y = 190, title at y = 215, dy = 34 -> 249
# Card 1 (File): y = 270, h = 170.
#   text at y = 308 (top = 308 - 20 = 288, pad_t = 18)
#   5 lines with dy=26: 308, 334, 360, 386, 412
#   last line: bottom = 412 + 6 = 418.
#   pad_b = 270 + 170 - 418 = 22 px! (>= 16 px!)

# Card 2 (Picture CPUs): y = 460, h = 95. (y = 460..555)

# Card 3 (Note): y = 575, h = 150. (y = 575..725)
#   text at y = 612 (top = 612 - 20 = 592, pad_t = 17)
#   4 lines with dy=28: 612, 640, 668, 696
#   last line: bottom = 696 + 6 = 702.
#   pad_b = 575 + 150 - 702 = 23 px!

# Card 4 (Use): y = 745, h = 200. (y = 745..945)
#   text at y = 782 (top = 782 - 20 = 762, pad_t = 17)
#   5 lines with dy=28: 782, 810, 838, 866, 894
#   last line: bottom = 894 + 6 = 900.
#   pad_b = 745 + 200 - 900 = 45 px!

# Column 2 items:
# Header: icon at y = 190, title at y = 215, dy = 34 -> 249
# Card 1 (File): y = 270, h = 150. (y = 270..420)
#   text at y = 308
#   4 lines with dy=28: 308, 336, 364, 392 (bottom = 398)
#   pad_b = 420 - 398 = 22 px!
# Card 2 (Picture Gauge): y = 440, h = 175. (y = 440..615)
# Card 3 (Use): y = 635, h = 310. (y = 635..945)
#   text at y = 675
#   3 lines with dy=34: 675, 709, 743 (bottom = 749)
#   pad_b = 945 - 749 = 196 px!

# Column 3 items:
# Header: icon at y = 190, title at y = 215, dy = 34 -> 249, dy = 34 -> 283
# Card 1 (File): y = 305, h = 135. (y = 305..440)
#   text at y = 342
#   3 lines with dy=28: 342, 370, 398 (bottom = 404)
#   pad_b = 440 - 404 = 36 px!
# Card 2 (Picture Sibling bars): y = 460, h = 175. (y = 460..635)
# Card 3 (Note): y = 655, h = 290. (y = 655..945)
#   text at y = 695
#   6 lines with dy=30: 695, 725, 755, 785, 815, 845 (bottom = 851)
#   pad_b = 945 - 851 = 94 px!

# Bottom strip: y = 985, h = 95. (y = 985..1080)
# text at y = 1025, dy = 30 -> 1055 (bottom = 1061, pad_t = 1025-20-985 = 20, pad_b = 1080-1061 = 19)

# Bottom bar: y = 1100, h = 60. (y = 1100..1160)
# text at y = 1139 (top = 1118, bottom = 1145, pad_t = 18, pad_b = 15)

print("Geometry coordinates calculated!")
