# Ladder 1 height = 300px.
# Header: 30px font. Takes up y=0..35.
# Inside Ladder 1: 4 rungs.
# Gaps between rungs: 8px.
# Available height for 4 rungs: 300 - 35 (header) - 15 (header gap) - 10 (bottom pad) - 3*8 (gaps) = 216px.
# 216px / 4 = 54px per rung!
# Rung 1: 48px
# Rung 2: 66px (2 lines: path on line 1, note on line 2)
# Rung 3: 48px
# Rung 4: 48px
# Sum of rungs = 48 + 66 + 48 + 48 = 210px <= 216px!

print("Ladder 1 fits inside 300px perfectly!")

# Ladder 2 height = 260px.
# Header: 30px font. Takes up y=0..35.
# Available height for 4 rungs: 260 - 35 - 15 - 10 - 3*8 = 176px.
# 176px / 4 = 44px per rung!
# In Ladder 2: all 4 rungs are 1 line each!
# Rung 1: 'command-line flags'
# Rung 2: 'environment variables'
# Rung 3: 'config file'
# Rung 4: 'defaults'
# Each rung height = 44px (with 24px font, 10px pad top and bottom).
print("Ladder 2 fits inside 260px perfectly!")
