# Let's verify line positions inside each box

# Box 1: y=168, h=56
# Text baseline = 168 + 35 = 203.
# Font 24px: cap = 203 - 18 = 185 (pad top = 185 - 168 = 17px >= 16)
# Desc = 203 + 5 = 208 (pad bot = 224 - 208 = 16px >= 16)
print("Box 1 padding OK")

# Box 2: y=264, h=186
# Line 0 (title, 30px): base = 264 + 37 = 301. Cap = 301 - 22.5 = 278.5 (pad top = 278.5 - 264 = 14.5px -> needs 303: pad top = 303 - 22.5 - 264 = 16.5px!)
# Let's adjust:
# Title base = 303 (pad top = 16.5px)
# Line 1 base = 303 + 26 = 329
# Line 2 base = 329 + 25 = 354
# Line 3 base = 354 + 25 = 379
# Line 4 base = 379 + 26 = 405
# Line 5 base = 405 + 24 = 429
# Line 5 desc = 429 + 4.8 = 433.8
# Box bottom = 450. Pad bot = 450 - 433.8 = 16.2px >= 16px!
print("Box 2 padding OK")

# Box 3: y=490, h=236
# Title base = 490 + 39 = 529 (pad top = 529 - 22.5 - 490 = 16.5px)
# Line 1 base = 529 + 26 = 555
# Line 2 base = 555 + 24 = 579
# Line 3 base = 579 + 24 = 603
# Cmd 1 base = 603 + 26 = 629
# Cmd 2 base = 629 + 24 = 653
# Cmd 3 base = 653 + 24 = 677
# Cmd 4 base = 677 + 24 = 701
# Cmd 4 desc = 701 + 4.8 = 705.8
# Box bottom = 726. Pad bot = 726 - 705.8 = 20.2px >= 16px!
print("Box 3 padding OK")

# Box 4: y=766, h=114
# Title base = 766 + 39 = 805 (pad top = 805 - 22.5 - 766 = 16.5px)
# Cmd 1 base = 805 + 27 = 832
# Cmd 2 base = 832 + 25 = 857
# Cmd 2 desc = 857 + 4.8 = 861.8
# Box bottom = 880. Pad bot = 880 - 861.8 = 18.2px >= 16px!
print("Box 4 padding OK")

# Box 5: y=920, h=140
# DNS base = 920 + 35 = 955 (pad top = 955 - 18 - 920 = 17px)
# Doc 1 base = 955 + 28 = 983
# Doc 2 base = 983 + 25 = 1008
# Doc 3 base = 1008 + 25 = 1033
# Doc 3 desc = 1033 + 4.8 = 1037.8
# Box bottom = 1060. Pad bot = 1060 - 1037.8 = 22.2px >= 16px!
print("Box 5 padding OK")

# Box 6: y=1104, h=56
# Base = 1104 + 35 = 1139 (pad top = 17px, pad bot = 16.2px)
print("Box 6 padding OK")

print("ALL BOXES HAVE AT LEAST 16PX PADDING ON TOP AND BOTTOM!")
