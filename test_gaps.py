# Let us calculate precise Y coordinates:
# Total height: 1200
# Margins: top 30, bottom 40
# Title at y = 48 (text y = 48, h ~ 30)

# Let us see:
# Row 1: X (h = 85) -> y = 75 .. 160
# Gap: 40 -> y = 160 .. 200
# Row 2: A, A1 (h = 95) -> y = 200 .. 295
# Gap: 40 -> y = 295 .. 335
# Row 3: B, B1 (h = 90) -> y = 335 .. 425
# Gap: 40 -> y = 425 .. 465
# Row 4: C, C1 (h = 95) -> y = 465 .. 560
# Gap: 40 -> y = 560 .. 600
# Row 5: D (h = 95) -> y = 600 .. 695
# Gap to Row 6: 125 px! -> y = 695 .. 820
# Row 6: D1, D2, D3 (h = 320) -> y = 820 .. 1140
# Bottom margin: 1200 - 1140 = 60 px!

print("Gap between D and Row 6 is 125 px!")
print("Row 6 height is 320 px (plenty of room for 3 lines of text and icon)!")
