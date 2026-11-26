# Let's see how stacked layout fits in 1200 height:
# Canvas: 1600 x 1200.
# We need:
# Title at top (e.g. y=56)
# Subtitle Pill:
#   rect x=450, y=74, w=700, h=56, text at y=110 (T pad = 18, B pad = 14.7 -> h=60, y=72..132, text y=110: T=20, B=16.7!)
# Setup Container:
#   y = 172..266 (h=94). (Gap from Subtitle pill = 172 - 132 = 40px!)
#   Icon: x=75, y=191, w=56, h=56.
#   Text: 2 lines at x=155.
#     Line 1: "Setup: eight replicas, forty prefixes, one hot prefix with 40 percent of traffic,"
#     Line 2: "cache of six prefixes per replica, hit costs 0.10 s and miss 0.50 s"
#     dy=32. Baseline 1 = 210, Baseline 2 = 242.
#     T pad = 210 - 18 - 172 = 20px >= 16px.
#     B pad = (172+94) - (242 + 5.28) = 266 - 247.28 = 18.72px >= 16px.
#     Setup ends at y = 266.

# Gap: 40px -> Table 1 starts at y = 306!
# In Table 1:
# Header:
#   rect x=66, y=318, w=1468, h=52, rx=10
#   Icon: x=75, y=316, 56x56
#   Text: "Table 1 policy: hit rate, p50 s, p99 s, max over mean load", fs=30, bold, at x=155, y=355
#   Top pad: 355 - 0.75*30 - 318 = 355 - 22.5 - 318 = 14.5px < 16px.
#   If rect h=58, y=316..374:
#   Text y=357: Top pad = 357 - 22.5 - 316 = 18.5px >= 16px!
#   Bottom pad = 374 - (357 + 0.22*30) = 374 - 363.6 = 10.4px < 16px.
#   Wait! For fs=30, total height = 22.5 + 6.6 = 29.1px.
#   To have top pad >= 16 and bottom pad >= 16:
#   rect height must be at least 29.1 + 32 = 61.1px -> say 62px!
#   Let's check if h=62 works:
#   rect y=316, h=62 (ends at 378).
#   Text baseline y=355:
#   Top pad = 355 - 22.5 - 316 = 16.5px >= 16px!
#   Bottom pad = 378 - (355 + 6.6) = 378 - 361.6 = 16.4px >= 16px!
#   PERFECT!

print("Header h=62 gives top pad 16.5px and bottom pad 16.4px!")
