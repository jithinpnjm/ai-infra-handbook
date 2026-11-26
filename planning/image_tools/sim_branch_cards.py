# Let's test the layout where:
# Left column: x = 50 .. 760 (width 710)
# Right column: x = 840 .. 1550 (width 710)
# 
# In Left column, 4 branches:
# Can an arrow come from Root, enter each row, and point into the outcome box?
# Let's see: what if the arrow starts at the root, goes down a trunk or dedicated line,
# and points to the box?
#
# But wait! Look at the rule:
# "Orthogonal (horizontal and vertical) or gently curved arrows only.
# Arrows must never cross each other, never pass through a node, and never cross a text label.
# If connections would cross, rearrange the nodes so they do not.
# If many nodes connect to one group, draw ONE arrow to the group's container instead of one per node.
# Arrowheads: small and proportional (about 18 px), never larger than the node icons.
# Each arrow ends exactly at the edge of its target."
#
# "Draw exactly the connections the source has: same number of arrows, same direction, same labels. No extra arrows."
# "Below, seven branch boxes in two columns, each with an arrow from the root and a short label."

print("Analyzing arrow paths...")
