# Let us calculate total height needed for stacked layout:

# Title & Subtitle:
# Title at y=52, fs=48
# Subtitle Pill:
#   rect: x=450, y=72, w=700, h=60, rx=30
#   text: x=800, y=110, fs=24, bold, centered
#   Pill bottom = 132.

# Gap: 40px -> y = 172
# Setup Container:
#   rect: x=50, y=172, w=1500, h=94, rx=14
#   Icon: 75, 191, 56x56
#   Text: x=155, y=210, 2 lines, dy=32
#   Setup bottom = 266.

# Gap: 40px -> y = 306
# Table 1 Container:
#   rect: x=50, y=306, w=1500, h=H_t1, rx=14
#   Header: rect x=66, y=318, w=1468, h=60, rx=10
#           Icon: 75, 320, 56x56
#           Text: x=155, y=357, fs=30, bold
#   Row 1: rect x=66, y=384, w=1468, h=56, rx=8; text y=420
#   Row 2: rect x=66, y=444, w=1468, h=56, rx=8; text y=480
#   Row 3: rect x=66, y=504, w=1468, h=56, rx=8; text y=540
#   Row 4: rect x=66, y=564, w=1468, h=56, rx=8; text y=600
#   Bottom of Row 4 = 564 + 56 = 620.
#   Container bottom pad: 12px -> H_t1 = 632 - 306 = 326px.
#   Table 1 bottom = 632.

# Gap: 40px -> y = 672
# Table 2 Container:
#   rect: x=50, y=672, w=1500, h=H_t2, rx=14
#   Header: rect x=66, y=684, w=1468, h=60, rx=10
#           Icon: 75, 686, 56x56
#           Text: x=155, y=723, fs=30, bold
#   Row 1: rect x=66, y=750, w=1468, h=56, rx=8; text y=786
#   Row 2: rect x=66, y=810, w=1468, h=56, rx=8; text y=846
#   Row 3: rect x=66, y=870, w=1468, h=56, rx=8; text y=906
#   Row 4: rect x=66, y=930, w=1468, h=56, rx=8; text y=966
#   Row 5: rect x=66, y=990, w=1468, h=56, rx=8; text y=1026
#   Bottom of Row 5 = 990 + 56 = 1046.
#   Container bottom pad: 12px -> H_t2 = 1058 - 672 = 386px.
#   Table 2 bottom = 1058.

# Gap: 40px -> y = 1098
# Takeaway bar:
# y = 1098. Canvas ends at 1200.
# 1200 - 1098 = 102px.
# But margin at bottom must be >= 40px!
# 1200 - 40 = 1160.
# So Takeaway bar can only be 1160 - 1098 = 62px high!
# Can 4 lines of Takeaway text fit in 62px?
# NO! 4 lines of 24px text need at least 110px!
print("With 40px gaps between all 4 containers, Table 1 and Table 2 stacked overflows 1200!")
