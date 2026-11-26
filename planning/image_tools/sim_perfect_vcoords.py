# Let's test the vertical layout in Python.
# Total height: 1200 px.
# Margins: top 40, bottom 40.
# y = 40 to 1160 (1120 px available).

# Title: y = 50 (font-size 48 bold)
# Gap: 40 px -> y = 90

# Let's see:
# Row 1: y = 90 to 200 (h = 110)
# Gap: 40 px -> y = 240
# Row 2: y = 240 to 350 (h = 110)
# Gap: 40 px -> y = 390
# Row 3: y = 390 to 500 (h = 110)
# Gap: 40 px -> y = 540
# Row 4: y = 540 to 650 (h = 110)
# Gap: 40 px -> y = 690
# Row 5: y = 690 to 800 (h = 110)
# Gap: 40 px -> y = 840
# Row 6 (Guard strip): y = 840 to 970 (h = 130)
# Gap: 40 px -> y = 1010
# Wait! y = 1010 to 1200 is 190 px!
# If Row 6 is at y = 880 to 1020 (h = 140)
# Gap: 40 px -> y = 1060
# Row 7 (Bottom bar): y = 1080 to 1145 (h = 65)
# Bottom margin: 1200 - 1145 = 55 px >= 40 px!

print("Row 1: 90..200 (110)")
print("Gap 1: 40 px")
print("Row 2: 240..350 (110)")
print("Gap 2: 40 px")
print("Row 3: 390..500 (110)")
print("Gap 3: 40 px")
print("Row 4: 540..650 (110)")
print("Gap 4: 40 px")
print("Row 5: 690..800 (110)")
print("Gap 5: 40 px")
print("Row 6: 840..980 (140) [Guard strip]")
print("Gap 6: 40 px")
print("Row 7: 1020..1090 (70) or 1080..1150 (70) [Bottom bar]")
