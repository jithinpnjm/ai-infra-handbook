# Card 5, 2, 3, 4, 7 text height is 58 px.
# In a box of height 96 px: total padding = 96 - 58 = 38 px.
# Perfectly centered: top pad = 19 px, bottom pad = 19 px!

# Let's test the baselines:
# Box y:
# Row 1 (h=96): y = 168 to 264
# Row 2 (h=96): y = 274 to 370
# Row 3 (h=96): y = 380 to 476
# Row 4 (h=148): y = 486 to 634
# Row 5 (h=154): y = 644 to 798
# Row 6 (h=70): y = 808 to 878
# Container ends at 886!

# Baselines:
# Row 1:
# Card 1 (1 line, text h=28): box y=168, h=96. Center y = 168 + 48 = 216. Baseline y = 224.
# Card 5 (2 lines, text h=58, dy=30): box y=168, h=96. Top pad = 19 -> text top at 187. Baseline y = 208, second line y = 238. Text bottom at 245. Pad bottom = 264 - 245 = 19!

# Row 2 (box y=274, h=96):
# Card 2, 3 (2 lines, text h=58, dy=30): Baseline y = 314, dy=30 -> second line at 344. Top pad: 314 - 21 (cap) - 274 = 19. Bottom: 370 - (344 + 7) = 19!

# Row 3 (box y=380, h=96):
# Card 4, 7 (2 lines, text h=58, dy=30): Baseline y = 420, dy=30 -> second line at 450.

# Row 4 (box y=486, h=148):
# Card 6 (3 lines, dy=30): text h = 88. Pad = (148 - 88)/2 = 30 px. Baseline y = 538.
# Card 8 (4 lines, dy=28): text h = 112. Pad = (148 - 112)/2 = 18 px. Top text at 486 + 18 = 504. Baseline y = 525, dy=28, 28, 28 -> 553, 581, 609. Bottom text at 616. Pad bottom: 634 - 616 = 18 px!

# Row 5 (box y=644, h=154):
# Card 9 (4 lines, dy=28): text h = 112. Pad = (154 - 112)/2 = 21 px. Baseline y = 687.

# Row 6 (box y=808, h=70):
# Card 10 (1 line, text h=28): Pad = (70 - 28)/2 = 21 px. Baseline y = 850.

print("Tuning planned successfully.")
