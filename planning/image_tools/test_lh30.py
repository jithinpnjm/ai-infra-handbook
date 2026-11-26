# Let's test with line-height = 30px and font-size = 24px.
# In Col 2:
# Card 1: 13 lines -> (13-1)*30 + 24 = 360 + 24 = 384px text.
# Padding top 20, bot 20 -> 424px.
# Card 2: 3 lines -> (3-1)*30 + 24 = 60 + 24 = 84px text.
# Padding top 20, bot 20 -> 124px.
# Card 3: 7 lines -> (7-1)*30 + 24 = 180 + 24 = 204px text.
# Padding top 20, bot 20 -> 244px.
# Sum = 424 + 124 + 244 = 792px.
# 2 gaps of 15px = 30px -> total 822px!
# Cards start at y = 240, end at y = 240 + 822 = 1062!
# Column background: y = 95 to 1075 (height 980).
# Bottom bar: y = 1095 to 1175 (height 80).
# Margin to bottom: 25px.
# Total height = 1200!

# Now Col 1 with line-height = 30px:
# Card 1: 5 lines -> 4*30 + 24 = 144px text + 40 pad = 184px.
# Card 2: 7 lines -> 6*30 + 24 = 204px text + 40 pad = 244px.
# Card 3: 6 lines -> 5*30 + 24 = 174px text + 40 pad = 214px.
# Card 4: 4 lines -> 3*30 + 24 = 114px text + 40 pad = 154px.
# Sum = 184 + 244 + 214 + 154 = 796px.
# 3 gaps of (822 - 796)/3 = 26/3 = ~8.7px -> say gaps: 9, 8, 9 -> 796 + 26 = 822px!

# Now Col 3 with line-height = 30px:
# Card 1: 2 lines -> 1*30 + 24 = 54px text + 80 pad = 134px.
# Card 2: 4 lines -> 3*30 + 24 = 114px text + 80 pad = 194px.
# Card 3: 4 lines -> 3*30 + 24 = 114px text + 80 pad = 194px.
# Card 4: 5 lines -> 4*30 + 24 = 144px text + 80 pad = 224px.
# Sum = 134 + 194 + 194 + 224 = 746px.
# 3 gaps of (822 - 746)/3 = 76/3 = ~25.3px -> say 25, 26, 25 -> 746 + 76 = 822px!

print("With line-height=30px, every column ends at exactly y=1062!")
