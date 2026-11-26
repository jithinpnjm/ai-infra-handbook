# Right container: y = 165 to 880 (h = 715)
# Header/inner padding:
# Let's say top padding = 20 -> y_start = 185
# Bottom padding = 20 -> y_end = 860
# Usable height = 860 - 185 = 675 px!

# Let's check how many rows:
# Row 1 (y: 185 to 260, h = 75):
#   Col 1: Item 1 "len(inv) is 52" (1 line)
#   Col 2: Item 5 "inv[:3] first three nodes" (1 line)
# Gap: 15 px
# Row 2 (y: 275 to 355, h = 80):
#   Col 1: Item 2 "inv[0] == Node(slot=01, rack=r1)" (2 lines)
#   Col 2: Item 3 "inv[-1] == Node(slot=13, rack=r4)" (2 lines)
# Gap: 15 px
# Row 3 (y: 370 to 450, h = 80):
#   Col 1: Item 4 "choice(inv) random selection" (2 lines)
#   Col 2: Item 7 "for node in inv and reversed(inv)" (2 lines)
# Gap: 15 px
# Row 4 (y: 465 to 580, h = 115):
#   Col 1: Item 6 "inv[12::13] slot 13 of every rack: start at index 12, step 13" (3 lines)
#   Col 2: Item 8 "Node(07, r2) in inv is True, Node(07, r9) in inv is False (a sequential scan)" (4 lines)
# Gap: 15 px
# Row 5 (y: 595 to 705, h = 110):
#   Wide card (w = 780):
#   Item 9: "sorted(inv, key=drain_order): slot position times the number of racks plus rack priority from RACK_PRIORITY = r4:3, r3:2, r2:1, r1:0, so slot 01 of r1 ranks 0 and slot 13 of r4 ranks 51" (3-4 lines)
# Gap: 15 px
# Row 6 (y: 720 to 800, h = 80):
#   Wide card (w = 780) or centered card:
#   Item 10: "random.shuffle(inv) needs __setitem__" (1-2 lines)
# Wait! y ends at 800!
# Remaining space: 860 - 800 = 60 px!

print("Testing exact coordinates...")
y = 185
rows = [
    ("Row 1", 75),
    ("Row 2", 80),
    ("Row 3", 80),
    ("Row 4", 125),
    ("Row 5", 145),
    ("Row 6", 80)
]

cur_y = 185
for name, h in rows:
    print(f"{name}: y = {cur_y} to {cur_y + h} (h = {h})")
    cur_y += h + 15

print(f"Total end y: {cur_y - 15}. Container bottom: 880. Clearance at bottom: {880 - (cur_y - 15)} px!")
