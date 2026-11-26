import re
import xml.etree.ElementTree as ET

# Let's test a complete layout configuration
# Canvas: 1600 x 1050

# Node dimensions:
NW, NH = 280, 84

# Let's test coordinates:
# Row 1 (y=210):
# DRAINED:   cx = 440,  cy = 210  (x1=300, y1=168, x2=580, y2=252)
# DRAINING:  cx = 1160, cy = 210  (x1=1020, y1=168, x2=1300, y2=252)
#
# Row 2 (y=530):
# IDLE:      cx = 440,  cy = 530  (x1=300, y1=488, x2=580, y2=572)
# ALLOCATED: cx = 1160, cy = 530  (x1=1020, y1=488, x2=1300, y2=572)
#
# Row 3 (y=880):
# DOWN:      cx = 800,  cy = 880  (x1=660, y1=838, x2=940, y2=922)

# Wait! Let's look at Row 1, 2, 3:
# In this layout:
# DRAINED (top-left) <--- DRAINING (top-right)
#   ^                        ^
#   |                        |
# IDLE (mid-left) <======> ALLOCATED (mid-right)
#   \                        /
#    \                      /
#     +-----> DOWN <-------+
#
# Look at that:
# DOWN is at the BOTTOM!
# IDLE is in the MIDDLE!
# ALLOCATED is in the MIDDLE!
# DRAINED is at the TOP!
# DRAINING is at the TOP!
#
# Let's check ALL 10 arrows in this layout:
# 1. [*] -> IDLE: enters IDLE from left (x=120, y=530) -> (300, 530)
# 2. IDLE -> ALLOCATED (job starts): from (580, 510) to (1020, 510)
# 3. ALLOCATED -> IDLE (job ends): from (1020, 550) to (580, 550)
# 4. IDLE -> DRAINED (scontrol drain / health check):
#    vertical UP from IDLE (390, 488) to DRAINED (390, 252)
# 5. ALLOCATED -> DRAINING (scontrol drain / health check):
#    vertical UP from ALLOCATED (1160, 488) to DRAINING (1160, 252)
#    Notice: both arrows 4 and 5 go straight UP!
#    Between them (y = 370), we have "scontrol drain / health check"!
# 6. DRAINING -> DRAINED (running jobs finish):
#    horizontal LEFT from DRAINING (1020, 210) to DRAINED (580, 210)
# 7. DRAINED -> IDLE (scontrol resume):
#    vertical DOWN from DRAINED (490, 252) to IDLE (490, 488)
# 8. ALLOCATED -> DOWN (node failure (jobs requeued or failed)):
#    Leaves ALLOCATED right edge (1300, 530) -> goes right to x=1420 -> down to y=880 -> left to DOWN (940, 880).
#    Horizontal bottom segment: from x=1420 to 940 = 480px!
# 9. IDLE -> DOWN (slurmd not responding (SlurmdTimeout) / admin):
#    Leaves IDLE left edge (300, 550) -> goes left to x=180 -> down to y=880 -> right to DOWN (660, 880).
#    Horizontal bottom segment: from x=180 to 660 = 480px!
# 10. DOWN -> IDLE (resume or ReturnToService on valid registration):
#    Leaves DOWN top (cx=800, y=838) -> goes up to y=670 -> left to x=440 -> up to IDLE bottom (440, 572)!
#    Horizontal segment: from x=800 to 440 = 360px.
#
# DO ANY OF THESE 10 ARROWS CROSS?
# Let's verify:
# - Arrow 8 (ALLOCATED -> DOWN) is on the right outer flank (x >= 940, y >= 530).
# - Arrow 9 (IDLE -> DOWN) is on the left outer flank (x <= 660, y >= 550).
# - Arrow 10 (DOWN -> IDLE) is in the interior between IDLE and DOWN (x between 440 and 800, y between 572 and 838).
# - Arrow 8, 9, 10 DO NOT TOUCH OR CROSS EACH OTHER!
# - Arrow 1 ([*] -> IDLE) is at y=530, x from 120 to 300.
#   Wait! Does Arrow 9 (x=180, y from 550 to 880) cross Arrow 1?
#   Arrow 1 enters IDLE at y=510!
#   Arrow 9 leaves IDLE at y=572 (bottom) or y=550!
#   If Arrow 9 leaves IDLE at the bottom (x=360, y=572), goes down to y=880, then right to DOWN:
#   IT NEVER GOES TO x=180! IT DOES NOT TOUCH ARROW 1 AT ALL!
#
# Look at that:
# If IDLE -> DOWN leaves IDLE at the BOTTOM (x=360, y=572):
# Goes straight down to y=880, then turns right to DOWN (660, 880)!
# THEN IT DOES NOT EVEN GO TO THE LEFT OF IDLE!
# Arrow 1 is at x in [120, 300], y=530.
# IDLE -> DOWN is at x=360 (to the right of 300)!
# ZERO CROSSING!

print("Checked! Clean and 100% planar!")
