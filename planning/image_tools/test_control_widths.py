# Let's test the widths of Control plane components:
# Available width: x = 250 to 1520 (1270 px)
# REST / BACKUP: x = 250 .. 580 (w = 330)
# Gap REST/BACKUP -> CTLD: 50px
# CTLD: x = 630 .. 1030 (w = 400)
# Gap CTLD -> DBD: 80px
# DBD: x = 1110 .. 1310 (w = 200)
# Gap DBD -> DB: 30px
# DB: x = 1340 .. 1520 (w = 180)

# Wait, what are the text lengths in DBD and DB?
# DBD:
# Line 1: "slurmdbd, port 6819" (19 chars * 14.88 = 282 px) -> need w >= 320px!
# DB:
# Line 1: "MariaDB / MySQL" (15 chars * 14.4 = 216 px) -> need w >= 260px!

# If DBD and DB need w >= 320 and w >= 260:
# Total width needed for DBD and DB = 320 + 260 + 40 = 620 px!
# Then x = 250 + 330 + 50 + 400 + 80 + 620 = 1730 > 1520!
#
# BUT WAIT!
# What if DB is BELOW DBD?
# If DB is BELOW DBD:
# DBD: x = 1120 .. 1500 (w = 380, h = 130) -> 380 is MORE than enough for 282px!
# DB:  x = 1120 .. 1500 (w = 380, h = 130) -> 380 is MORE than enough for 216px!
# AND the gap between CTLD (ends at 1030) and DBD (starts at 1120) is 90px (or CTLD ends at 950, gap = 170px)!
# AND how does MUNGE connect to DBD?
# Let's check:
# If DB is below DBD:
# How does MUNGE connect to DBD?
# MUNGE is in Tier 3 (below Control plane)!
# If DB is at y = 490..620:
# MUNGE is at y = 730..910!
# Can MUNGE -> DBD go along the side of DB or through DB?
# Never through a node!
# Can MUNGE -> DBD go up the gap between CTLD and DB?
# The gap between CTLD (ends at 950) and DB (starts at 1120) is 170px wide!
# From MUNGE (at x=1030), straight UP through that 170px wide gap to y=400, then right into DBD left edge!
# BUT WAIT! What enters DBD left edge at y=400?
# CTLD -> DBD!
# So if CTLD -> DBD is entering DBD left edge from x=950 to x=1120,
# then a vertical arrow going up to DBD left edge would INTERSECT CTLD -> DBD!
# AHA! That's why DB below DBD has a crossing if MUNGE enters from the left!

print("Crucial observation: we must keep the path to DBD crossing-free!")
