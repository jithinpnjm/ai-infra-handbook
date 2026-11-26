# Let's check right panel in height 520px:
# Panel: x=1000..1560 (w=560), y=150..670 (h=520)
# Title: 'Docker network modes' (30px bold)
# Icon: 56px at x=1020, y=165
# Title at x=1090, y=200
# Header area: y=150..220 (70px)
# Usable height for items: 670 - 220 - 15 (bottom padding) = 435px!
# We have 6 items with 17 lines total.
# 17 lines * 24px font size.
# What is the line spacing?
# If line-height is 24px (dy=24), 17 * 24 = 408px!
# 408px < 435px!
print("17 lines * 24px =", 17 * 24, "vs usable 435px")
