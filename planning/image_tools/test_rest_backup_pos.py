# Let's test placing REST and BACKUP:
# Who does REST connect to?
# ONLY CTLD! (REST -> CTLD)
# Who does BACKUP connect to?
# ONLY CTLD! (BACKUP <-> CTLD)
# Neither REST nor BACKUP connects to ANYTHING else!
# They only touch CTLD.
#
# If CTLD is at x = 460..860, y = 330..570:
# Where can REST and BACKUP go?
# They can be inside Control plane, to the left or right of CTLD,
# OR BACKUP can be above CTLD or below CTLD!
#
# But wait! If REST and BACKUP are at x = 120..360,
# what is wrong with the arrow U1 -> D1 running along the left margin (at x=40)?
# Let's check:
# Along the left margin, if the text is placed at x=45:
# Can the text be rotated -90 degrees?
# In SVG:
# <text x="-480" y="28" transform="rotate(-90)" font-family="..." font-size="24" fill="#303a36" text-anchor="middle">srun talks to slurmd and slurmstepd directly</text>
# Total length: 44 chars * 14.4 = 633 px.
# The vertical segment is from y=180 to y=780 = 600 px!
# 633 px is slightly longer than 600 px (would extend past the corners)!
#
# What if it's placed horizontally on the arrow?
# Or what if U1 -> D1 has space for horizontal text?
