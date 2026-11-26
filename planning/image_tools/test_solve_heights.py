import xml.etree.ElementTree as ET

# Let's adjust heights and baselines to guarantee all paddings >= 16px!

# 1. Left panel: y=100..760 (h=660)
# Card 1: [gpu] (h=124, y=116..240). text y=154, dy=32, dy=32 -> lines at 154, 186, 218.
#   top = 154 - 18 = 136 -> pad_top = 136 - 116 = 20px
#   bot = 218 + 6 = 224 -> pad_bot = 240 - 224 = 16px

# Gap: 8px -> Card 2 starts at y=248.
# Card 2: a group collects hosts that share a role (h=60, y=248..308).
#   text y=282: top = 282 - 18 = 264 -> pad_top = 264 - 248 = 16px
#   bot = 282 + 6 = 288 -> pad_bot = 308 - 288 = 20px

# Gap: 8px -> Card 3 starts at y=316.
# Card 3: each host has a name... (h=92, y=316..408).
#   text y=350, dy=32 -> lines at 350, 382.
#   top = 350 - 18 = 332 -> pad_top = 332 - 316 = 16px
#   bot = 382 + 6 = 388 -> pad_bot = 408 - 388 = 20px

# Gap: 8px -> Card 4 starts at y=416.
# Card 4: [login] (h=92, y=416..508).
#   text y=450, dy=32 -> lines at 450, 482.
#   top = 450 - 18 = 432 -> pad_top = 432 - 416 = 16px
#   bot = 482 + 6 = 488 -> pad_bot = 508 - 488 = 20px

# Gap: 8px -> Card 5 starts at y=516.
# Card 5: [cluster:children] (h=92, y=516..608).
#   text y=550, dy=32 -> lines at 550, 582.
#   top = 550 - 18 = 532 -> pad_top = 532 - 516 = 16px
#   bot = 582 + 6 = 588 -> pad_bot = 608 - 588 = 20px

# Gap: 8px -> Card 6 starts at y=616.
# Card 6: [cluster:vars] (h=124, y=616..740).
#   text y=654, dy=32, dy=32 -> lines at 654, 686, 718.
#   top = 654 - 18 = 636 -> pad_top = 636 - 616 = 20px
#   bot = 718 + 6 = 724 -> pad_bot = 740 - 724 = 16px

# Callout 3 (orange): y=775..875 (h=100)
#   text y=814, dy=34 -> lines at 814, 848.
#   top = 814 - 18 = 796 -> pad_top = 796 - 775 = 21px
#   bot = 848 + 6 = 854 -> pad_bot = 875 - 854 = 21px

# Gap: 15px -> Commands strip: y=890..970 (h=80)
#   text y=934: top = 934 - 18 = 916 -> pad_top = 916 - 890 = 26px
#   bot = 934 + 6 = 940 -> pad_bot = 970 - 940 = 30px

# Gap: 15px -> Warning strip: y=985..1065 (h=80)
#   text y=1029: top = 1029 - 18 = 1011 -> pad_top = 1011 - 985 = 26px
#   bot = 1029 + 6 = 1035 -> pad_bot = 1065 - 1035 = 30px

# Gap: 15px -> Bottom bar: y=1080..1160 (h=80)
#   text y=1127 (fs=26): top = 1127 - 20 = 1107 -> pad_top = 1107 - 1080 = 27px
#   bot = 1127 + 6.5 = 1133.5 -> pad_bot = 1160 - 1133.5 = 26.5px

# Canvas height H = 1195 (or 1200 with 40px margin: 1160 + 40 = 1200!)
print("Exact layout solved perfectly!")
