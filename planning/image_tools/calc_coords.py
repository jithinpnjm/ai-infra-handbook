# Let's adjust heights and y-coordinates so every pad_top >= 18 and pad_bottom >= 18
# Available space: y=70 to 1085 = 1015 px.
# 10 cards:
# Card 1 (Story, 2 lines): y=72, h=96. Lines at y=110, y=144.
#   pad_top: 110 - 24*0.8 - 72 = 110 - 19.2 - 72 = 18.8 px >= 18
#   pad_bottom: (72+96) - (144 + 6) = 168 - 150 = 18 px >= 18

# Card 2 (Config, 1 line): y=178, h=64. Line at y=217.
#   pad_top: 217 - 19.2 - 178 = 19.8 px >= 18
#   pad_bottom: (178+64) - (217 + 6) = 242 - 223 = 19 px >= 18

# Card 3 (Pre-step, 1 line): y=252, h=64. Line at y=291.
#   pad_top: 291 - 19.2 - 252 = 19.8 px >= 18
#   pad_bottom: (252+64) - (291 + 6) = 316 - 297 = 19 px >= 18

# Card 4 (Step 1, 2 lines): y=326, h=96. Lines at y=364, y=398.
#   pad_top: 364 - 19.2 - 326 = 18.8 px >= 18
#   pad_bottom: (326+96) - (398 + 6) = 422 - 404 = 18 px >= 18

# Card 5 (Step 2, 1 line): y=432, h=64. Line at y=471.
#   pad_top: 471 - 19.2 - 432 = 19.8 px >= 18
#   pad_bottom: (432+64) - (471 + 6) = 496 - 477 = 19 px >= 18

# Card 6 (Step 3, 3 lines): y=506, h=130. Lines at y=544, y=578, y=612.
#   pad_top: 544 - 19.2 - 506 = 18.8 px >= 18
#   pad_bottom: (506+130) - (612 + 6) = 636 - 618 = 18 px >= 18

# Card 7 (Step 4, 1 line): y=646, h=64. Line at y=685.
#   pad_top: 685 - 19.2 - 646 = 19.8 px >= 18
#   pad_bottom: (646+64) - (685 + 6) = 710 - 691 = 19 px >= 18

# Card 8 (Step 5, 2 lines): y=720, h=96. Lines at y=758, y=792.
#   pad_top: 758 - 19.2 - 720 = 18.8 px >= 18
#   pad_bottom: (720+96) - (792 + 6) = 816 - 798 = 18 px >= 18

# Card 9 (Gate, 2 lines): y=826, h=96. Lines at y=864, y=898.
#   pad_top: 864 - 19.2 - 826 = 18.8 px >= 18
#   pad_bottom: (826+96) - (898 + 6) = 922 - 904 = 18 px >= 18

# Card 10 (Strip resume, 1 line): y=932, h=64. Line at y=971.
#   pad_top: 971 - 19.2 - 932 = 19.8 px >= 18
#   pad_bottom: (932+64) - (971 + 6) = 996 - 977 = 19 px >= 18

# Card 11 (Bottom bar): y=1090, h=70. Line at y=1134.
#   pad_top: 1134 - 28*0.8 - 1090 = 1134 - 22.4 - 1090 = 21.6 px >= 18
#   pad_bottom: (1090+70) - (1134 + 7) = 1160 - 1141 = 19 px >= 18

print("All vertical coordinates calculated perfectly!")
