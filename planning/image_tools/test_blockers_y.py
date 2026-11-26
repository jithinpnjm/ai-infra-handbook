# Available y for blockers: y=376 to y=905 (529 px)
# Header: icon and text y=388 to y=428 (ends at 432).
# That leaves 905 - 436 = 469 px for 6 cards.
# Heights needed:
# B1 (1 line): h = 52, text_y = 478
# B2 (1 line): h = 52, text_y = 540
# B3 (1 line): h = 52, text_y = 602
# B4 (1 line): h = 52, text_y = 664
# B5 (3 lines): h = 98, text_y = 752
# B6 (2 lines): h = 76, text_y = 856

# Let's check padding for each:
# If B1 has h=52, y=440..492:
# text_y = 473 -> pad_top = 473 - 19.2 - 440 = 13.8 px. (Needs 16 px!)
# To have pad_top >= 16 and pad_bottom >= 16:
# text height = fs * 0.8 (above) + fs * 0.2 (below) = fs = 24 px!
# So minimum card height for 1 line = 16 + 24 + 16 = 56 px!
# At h = 56 px, text_y = y + 16 + 19.2 = y + 35.2 -> say text_y = y + 36.
# Then pad_top = 36 - 19.2 = 16.8 px.
# pad_bottom = 56 - (36 + 4.8) = 15.2 px. (Make h = 58 px! Then pad_top = 16.8, pad_bottom = 17.2 px).

# Card heights:
# B1 (1 line): 58 px
# B2 (1 line): 58 px
# B3 (1 line): 54 px (PDBs)
# B4 (1 line): 54 px
# B5 (3 lines): 16 + 19.2 + 28*2 + 4.8 + 16 = 112 px
# B6 (2 lines): 16 + 19.2 + 28 + 4.8 + 16 = 84 px

# Sum of heights:
# 58 + 58 + 54 + 54 + 112 + 84 = 420 px!
# We have 469 px available!
# 469 - 420 = 49 px gap space for 5 gaps!
# That means gap = 49 / 5 = 9.8 px (approx 10 px each)!
print("Sum of heights:", 58 + 58 + 54 + 54 + 112 + 84)
print("Fits comfortably in 469 px!")
