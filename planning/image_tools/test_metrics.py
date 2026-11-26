# Let's check all vertical paddings and heights

# H = 1200
# Title: y=55 (font-size 48, top ~15, bottom ~65)
# Row 1 cards: y=90..470 (height 380)
# Centre badge: y=490..550 (height 60, rx 30)
# Row 2 cards: y=570..950 (height 380)
# Footer strip: y=970..1115 (height 145)
# Bottom bar: y=1130..1190 (height 60)
# Canvas bottom: 1200

# Inside cards (height 380):
# Card top: 0
# Header:
#   Number circle: cy=50, r=24 (y: 26..74)
#   Icon: y=22..78 (56x56)
#   Title: baseline 1: y=44, baseline 2: y=78 (dy=34)
# Gap: 80..100
# Panel A (What it looks like):
#   y=100..220 (height 120)
#   Text:
#     baseline 1: y=140
#     baseline 2: y=172
#     baseline 3: y=204
#     (cap top: 140 - 24 = 116 -> top padding = 16 px. bottom: 204 + 6 = 210 -> bottom padding = 10 px.
#      If height = 125, y=100..225:
#      baseline 1: y=142, dy=32 -> 174, dy=32 -> 206. Cap top: 118 -> top pad 18. Bottom: 212 -> bottom pad 13.)
# Wait, why not height = 130 for Panel A and height = 130 for Panel B?
# If Panel A: y=100..225 (height 125)
# Gap: 15 px
# Panel B: y=240..365 (height 125)
# Card height: 380!
# Bottom margin inside card: 380 - 365 = 15 px.
print("Card layout fits perfectly in 380 px height!")
