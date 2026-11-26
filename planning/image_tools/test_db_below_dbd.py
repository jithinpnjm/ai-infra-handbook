# If DB is below DBD:
# DBD: x = 1120 .. 1480 (w=360), y = 330 .. 450 (h=120)
# DB:  x = 1120 .. 1480 (w=360), y = 495 .. 615 (h=120)
# Arrow DBD -> DB: straight down from (1300, 450) to (1300, 495)
# Arrow CTLD -> DBD: from (790, 390) to (1120, 390), length = 330px!
# Label: "job and usage records" centered at (955, 375), length ~280px -> spans x in [815, 1095]!
# Completely clear of CTLD (ends at 790) and DBD (starts at 1120)!

print("DBD and DB stacked vertically is vastly cleaner!")
