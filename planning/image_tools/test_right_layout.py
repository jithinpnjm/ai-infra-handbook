# Encodings panel: x=820, y=425, w=740, h=230 (ends at 655)
# Gap: 655..695 (40px)
# Bytes facts panel: x=820, y=695, w=740, h=350 (ends at 1045)

# Encodings card:
# x=840, w=700
# y=465, h=150
# lines = 4
# text y starts at 505 (baseline), line height 28: 505, 533, 561, 589
# top of text: 505 - 18 = 487. pad_top: 487 - 465 = 22px
# bottom of text: 589 + 5 = 594. pad_bottom: 615 - 594 = 21px
# pad_y inside card: 21px >= 16px!
# pad inside panel: (230 - 150) / 2 = 40px!

# Bytes facts cards:
# Panel: y=695..1045 (h=350)
# Card 1 (b"abc"[0]...):
# x=840, y=740, w=700, h=95
# lines = 2: y=778, 806. top: 760, bottom: 811.
# pad_top: 760 - 740 = 20px, pad_bottom: 835 - 811 = 24px.
# Gap between cards = 25px
# Card 2 (bytes.hex()...):
# x=840, y=860, w=700, h=135
# lines = 3: y=902, 930, 958. top: 884, bottom: 963.
# pad_top: 884 - 860 = 24px, pad_bottom: 995 - 963 = 32px.
# Panel bottom is 1045. Card 2 ends at 995. pad_bottom: 1045 - 995 = 50px!

print("Right layout math checks out perfectly!")
