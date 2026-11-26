# Let's test the layout with DOWN at top:
# Title at y = 60.
#
# DOWN:      cx = 800,  cy = 200, w = 260, h = 80 -> [670..930, 160..240]
# IDLE:      cx = 350,  cy = 520, w = 260, h = 80 -> [220..480, 480..560]
# ALLOCATED: cx = 1250, cy = 520, w = 260, h = 80 -> [1120..1380, 480..560]
# DRAINED:   cx = 350,  cy = 850, w = 260, h = 80 -> [220..480, 810..890]
# DRAINING:  cx = 1250, cy = 850, w = 260, h = 80 -> [1120..1380, 810..890]

# Now let's check:
# ALLOCATED -> DOWN: "node failure (jobs requeued or failed)" (len=38, width=547.2px)
# Leaves ALLOCATED top at (1250, 480) -> goes up to y = 300 -> turns left to x = 800 -> goes up to DOWN bottom (800, 240)!
# Look at that horizontal segment:
# y = 300, from x = 1250 to x = 800!
# Length = 1250 - 800 = 450px.
# Wait! 450px is less than 547.2px!
# What if it leaves ALLOCATED right at (1380, 520) -> goes to x = 1520 -> up to y = 200 -> left to DOWN right (930, 200)?
# Horizontal segment: y = 200, from x = 1520 to x = 930!
# Length = 1520 - 930 = 590px!
# 590px > 547.2px!
# Clearance = (590 - 547.2)/2 = 21.4px >= 16px!
# THAT FITS!
#
# Now let's check:
# IDLE -> DOWN: "slurmd not responding (SlurmdTimeout) / admin" (len=45, width=648px)
# Leaves IDLE left at (220, 520) -> goes left to x = 80 -> up to y = 140 -> right to x = 800 -> down to DOWN top (800, 160)!
# Look at that horizontal segment:
# y = 140, from x = 80 to x = 800!
# Length = 800 - 80 = 720px!
# 720px > 648px!
# Clearance = (720 - 648)/2 = 36px >= 16px!
# THAT FITS!
#
# Now let's check:
# DOWN -> IDLE: "resume or ReturnToService on valid registration" (len=47, width=676.8px)
# Where can this go?
# Leaves DOWN left at (670, 200) -> goes left to x = 80?
# Wait! If it goes left to x = 80, that crosses the vertical line at x = 80!
# What if DOWN -> IDLE leaves DOWN bottom at (730, 240) -> goes down to y = 380 -> left to x = 350 -> down to IDLE top (350, 480)?
# Horizontal segment: y = 380, from x = 730 to x = 350.
# Length = 730 - 350 = 380px.
# 380px is too short for 676.8px!

print("Checked.")
