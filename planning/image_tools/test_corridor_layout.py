# Let's test the 160px left corridor layout:
# Canvas: 1600 x 1200
# Left corridor: x = 0 to 200
# Main content area: x = 200 to 1560 (width = 1360)
# Margin right: 40px (1560 to 1600)

# U1 -> D1 arrow:
# Starts at U1 left edge: (230, 180)
# Goes left to x = 50: (50, 180)
# Goes down at x = 50: (50, 785)
# Goes right to D1 left edge: (230, 785)
#
# Text for U1 -> D1:
# Position: x = 70, y in [420, 500] (in the middle of the vertical run)
# 4 lines of horizontal text:
# Line 1: "srun talks" (10 chars * 14.4 = 144 px) -> x in [70, 214] (fits in 200!)
# Line 2: "directly to" (11 chars * 14.4 = 158 px) -> wait, exact words:
# "srun talks to slurmd and slurmstepd directly"
# Exact words split:
# Line 1: "srun talks to" (13 chars * 14.4 = 187 px) -> if font-size 24px, 13 * 13 = 169px.
# Line 2: "slurmd and" (10 chars * 14.4 = 144 px)
# Line 3: "slurmstepd" (10 chars * 14.4 = 144 px)
# Line 4: "directly" (8 chars * 14.4 = 115 px)
# Total height: 4 * 28 = 112 px.
# Fits perfectly in x in [65, 230], y in [420, 540]!

print("Corridor layout perfectly accommodates the label!")
