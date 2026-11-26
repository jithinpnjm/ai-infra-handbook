from test_card_paddings import check_panel

# Card height 360:
# Row 1: y = 125..485
# Header: y = 125..215
# Panel A: y = 220..340 (height 120)
# Panel B: y = 350..472 (height 122)
# Bottom margin inside card: 485 - 472 = 13 px.

# Wait, what if:
# Card height: 362
# Panel A: height 118
# Panel B: height 126
# Gap between header and Panel A: 125 + 92 = 217
# Let's test with exact coordinates:

# Card 1: x=50, y=125, w=720, h=362
# Panel 1-A (2 lines): x=70, y=217, w=680, h=116
# line 1: bl = 217 + 44 = 261
# line 2: bl = 261 + 32 = 293
check_panel(1, 'A', (70, 217, 680, 116), 92, [261, 293], 24, [
    "some resources expose only some of",
    "utilisation, saturation and errors"
])

# Panel 1-B (3 lines): x=70, y=345, w=680, h=128
# line 1: bl = 345 + 40 = 385
# line 2: bl = 385 + 30 = 415
# line 3: bl = 415 + 30 = 445
check_panel(1, 'B', (70, 345, 680, 128), 92, [385, 415, 445], 24, [
    "mark the empty cell as a known unknown and",
    "say so in the report; do not read an",
    "empty cell as healthy"
])

# Bottom of Panel 1-B is 345 + 128 = 473.
# Bottom of Card 1 is 125 + 362 = 487.
# Card bottom padding = 487 - 473 = 14 px.

print("Card 1 in 362 passed!")
