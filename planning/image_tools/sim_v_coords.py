# Let's test exact coordinates:

# Title: y=38, 92
# Row 1: y = 140 .. 270 (h = 130)
# Gap Row 1 -> Row 2 = 40
# Row 2: y = 310 .. 760 (h = 450)
# Gap Row 2 -> Row 3 = 40
# Row 3: y = 800 .. 1040 (h = 240)
# Gap Row 3 -> Row 4 = 40
# Row 4: y = 1080 .. 1150 (h = 70)
# Margin to bottom: 1200 - 1150 = 50 >= 40!

print(f"Row 1 bottom: 270")
print(f"Row 2 top: 310, gap = {310 - 270}")
print(f"Row 2 bottom: 760")
print(f"Row 3 top: 800, gap = {800 - 760}")
print(f"Row 3 bottom: 1040")
print(f"Row 4 top: 1080, gap = {1080 - 1040}")
print(f"Row 4 bottom: 1150, bottom margin = {1200 - 1150}")
