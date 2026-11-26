# Let's verify the exact arithmetic:
title_baseline = 76 # fs 48
# In Chromium, fs 48 bold:
# ascent = 35px, descent = 10px
# top of text = 76 - 35 = 41px >= 40px margin!
# bottom of text = 76 + 10 = 86px.
# gap below title = 126 - 86 = 40px!

# Rungs:
# Rung 1: y = 126, h = 96 (ends at 222)
# Gap 1->2: 40px -> Rung 2 starts at 262
# Rung 2: y = 262, h = 96 (ends at 358)
# Gap 2->3: 40px -> Rung 3 starts at 398
# Rung 3: y = 398, h = 96 (ends at 494)
# Gap 3->4: 40px -> Rung 4 starts at 534
# Rung 4: y = 534, h = 118 (ends at 652)
# Gap 4->5: 40px -> Rung 5 starts at 692
# Rung 5: y = 692, h = 96 (ends at 788)
# Gap 5->6: 40px -> Rung 6 starts at 828
# Rung 6: y = 828, h = 96 (ends at 924)
# Gap 6->7: 40px -> Rung 7 starts at 964
# Rung 7: y = 964, h = 96 (ends at 1060)
# Gap to takeaway bar: 1100 - 1060 = 40px!
# Takeaway bar: y = 1100, h = 60 (ends at 1160)
# Bottom margin: 1200 - 1160 = 40px!

print("Vertical coordinates:")
print("Title baseline:", title_baseline)
print("Takeaway bar: 1100 to 1160")
rungs = [
    ("Rung 1", 126, 96),
    ("Rung 2", 262, 96),
    ("Rung 3", 398, 96),
    ("Rung 4", 534, 118),
    ("Rung 5", 692, 96),
    ("Rung 6", 828, 96),
    ("Rung 7", 964, 96),
]
for i in range(len(rungs)):
    name, y, h = rungs[i]
    print(f"{name}: y={y}..{y+h} (h={h})")
    if i < len(rungs) - 1:
        next_y = rungs[i+1][1]
        gap = next_y - (y + h)
        print(f"  Gap {gap}px (>=40: {gap>=40})")
        assert gap >= 40
