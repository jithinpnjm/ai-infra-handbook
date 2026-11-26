# Let's test the internal layout of Card (w=720, h=360):
# Card top: y_card
# Inside card:
# Header:
#   Number circle: cx = x_card + 48, cy = y_card + 46, r = 24
#   Text number: x = x_card + 48, y = y_card + 55, font-size = 26 bold, text-anchor = middle
#   Title text: x = x_card + 88, font-size = 30 bold
#     Line 1: baseline = y_card + 40
#     Line 2: baseline = y_card + 74 (dy = 34)
#   Icon: translate(x_card + 720 - 48 - 56, y_card + 18) = (x_card + 616, y_card + 18), size 56x56
#
# Check title width against icon:
# Card 1: 'The counter' (11 chars * 18 = 198), 'does not exist' (14 chars * 18 = 252) -> 88 + 252 = 340 < 616 (gap 276px!)
# Card 2: 'The interval' (12 chars * 18 = 216), 'hides the problem' (17 chars * 18 = 306) -> 88 + 306 = 394 < 616 (gap 222px!)
# Card 3: 'The measurement' (15 chars * 18 = 270), 'disturbs the system' (19 chars * 18 = 342) -> 88 + 342 = 430 < 616 (gap 186px!)
# Card 4: 'The first explanation' (21 chars * 18 = 378), 'feels complete' (14 chars * 18 = 252) -> 88 + 378 = 466 < 616 (gap 150px!)

# Panels:
# Panel A (What it looks like):
#   x = x_card + 20, w = 680, h = 118
#   y = y_card + 94 to y_card + 212
#   Inner text: x = x_card + 40 (padding left = 20px)
#   Usable text width: 680 - 40 = 640px.
#
# Panel B (Counter-move):
#   x = x_card + 20, w = 680, h = 126
#   y = y_card + 222 to y_card + 348
#   Inner text: x = x_card + 40
#
# Bottom of card is y_card + 360 (padding below Panel B = 360 - 348 = 12px, or make card height 365 -> padding = 17px).

print("Check complete!")
