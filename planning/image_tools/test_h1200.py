# Heights of Left column cards with:
# R1: 2 lines -> 82px
# R2: 5 lines -> 166px
# R3: 2 lines -> 82px
# R4: 2 lines -> 82px
# R5: 3 lines -> 110px
# R6: 3 lines -> 110px
# R7: 2 lines -> 82px

cards = [82, 166, 82, 82, 110, 110, 82]
print("Sum of cards:", sum(cards))
total_left = sum(cards) + 6 * 10 + 70 # 6 gaps of 10px, header 70px
print("Total Left column height:", total_left)

# Canvas y budget for H=1200:
# y=0..35 top margin
# y=48 Title (48px)
# y=75..125 Opening story (height 50)
# y=140..966 Left column (height 826)
# y=982..1092 Bottom panel (height 110)
# y=1108..1168 Bottom bar (height 60)
# y=1168..1200 bottom margin (32px)
print("Total SVG height:", 1168 + 32)

