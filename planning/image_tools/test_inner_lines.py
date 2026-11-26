# Check text lines in Lane 1 (h=175, y=255..430):
# Title row: y = 255 + 32 = 287 (30px bold font)
# Desc line 1: y = 287 + 30 = 317 (24px font)
# Desc line 2: y = 317 + 28 = 345 (24px font)
# Note line 1: y = 345 + 30 = 375 (24px font)
# Note line 2: y = 375 + 28 = 403 (24px font)
# Bottom of text = 403 + 8 = 411.
# Box bottom = 430. Padding from bottom = 430 - 411 = 19px (>= 16px!).
# Total lines = 5 lines.

# Let's check Lane 2 (h=250, y=470..720):
# Title row: y = 470 + 32 = 502 (30px bold)
# Desc line 1: y = 502 + 28 = 530 (24px)
# Desc line 2: y = 530 + 26 = 556 (24px)
# Desc line 3: y = 556 + 26 = 582 (24px)
# Cmd 1: y = 582 + 28 = 610 (24px mono)
# Cmd 2: y = 610 + 26 = 636 (24px mono)
# Cmd 3: y = 636 + 26 = 662 (24px mono)
# Cmd 4: y = 662 + 26 = 688 (24px mono)
# Bottom of text = 688 + 8 = 696.
# Box bottom = 720. Padding from bottom = 720 - 696 = 24px (>= 16px!).
# Total lines = 8 lines.

# Let's check Lane 3 (h=115, y=760..875):
# Title row: y = 760 + 32 = 792 (30px bold)
# Cmd 1: y = 792 + 30 = 822 (24px mono)
# Cmd 2: y = 822 + 28 = 850 (24px mono)
# Bottom of text = 850 + 8 = 858.
# Box bottom = 875. Padding from bottom = 875 - 858 = 17px (>= 16px!).
# Total lines = 3 lines.

# Let's check Footer box (h=145, y=915..1060):
# DNS line: y = 915 + 32 = 947 (24px mono)
# Docker note line 1: y = 947 + 30 = 977 (24px)
# Docker note line 2: y = 977 + 26 = 1003 (24px)
# Docker note line 3: y = 1003 + 26 = 1029 (24px)
# Bottom of text = 1029 + 8 = 1037.
# Box bottom = 1060. Padding from bottom = 1060 - 1037 = 23px (>= 16px!).

print("ALL text lines fit with >= 16px padding inside boxes!")
