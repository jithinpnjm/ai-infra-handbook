# Ladders: y = 152 to 642 (height = 490)
# Container 1: x = 40 to 780 (width = 740)
# Container 2: x = 820 to 1560 (width = 740)

# Inside Container:
# Header: y = 152 to 196 (height 44). Header bar fill="#e8f1ea".
# Title: font-size 30 bold fill="#207448".
# For Col 1: "Which file is read (first found wins, never merged)"
# For Col 2: "Which value wins"

# Available vertical space for cards:
# Cards start at y = 208, end at y = 630.
# Available height = 630 - 208 = 422 px!

# In Ladder 1:
# Card 1 (Step 1): height 64px
# Card 2 (Step 2): height 174px
# Card 3 (Step 3): height 56px
# Card 4 (Step 4): height 56px
# Gaps between cards: 3 gaps of 12px = 36px.
# Total height = 64 + 174 + 56 + 56 + 36 = 386px <= 422px!
# Remaining padding = 422 - 386 = 36px (18px top, 18px bottom).

# In Ladder 2:
# 4 cards:
# If each card has height 80px:
# 4 * 80 + 3 * 16 (gaps) = 320 + 48 = 368px <= 422px!
# Or if each card has height 86px:
# 4 * 86 + 3 * 18 = 344 + 54 = 398px <= 422px!

print("Ladder cards fit with generous spacing!")
