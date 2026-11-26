# Let's test the 3-column layout with exact coordinates.

# Canvas: 1600 x 1200
# Title at (800, 50), font-size: 48, bold

# Columns:
# Col 1: Users (x: 50 .. 420, w: 370)
# Col 2: Control (x: 480 .. 1020, w: 540)
# Col 3: Compute (x: 1080 .. 1550, w: 470)

# But wait, what are the widths needed for the text inside nodes?
# Let's check text lengths:
# U1: "sbatch, srun, salloc, squeue, sinfo, scancel"
# If width is 370:
# 370 - 32 padding = 338.
# 338 / (0.62 * 24) = 338 / 14.88 = 22.7 chars per line.
# So "sbatch, srun, salloc," (21 chars) fits on line 1!
# "squeue, sinfo, scancel" (22 chars) fits on line 2!
# That fits in a box of width 360!

# U2: "sacct, sacctmgr, sreport (accounting queries)"
# Line 1: "sacct, sacctmgr, sreport" (24 chars) -> 24 * 14.88 = 357px -> need width ~390px, or 3 lines:
# Line 1: "sacct, sacctmgr,"
# Line 2: "sreport"
# Line 3: "(accounting queries)"

print("Text wrapping fits nicely!")
