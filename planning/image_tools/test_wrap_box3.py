import re

# Box 3 text:
text = "cluster autoscaler notices pending pods that a node group could fit"

# Box width = 272 px.
# Padding must be >= 16 px on left and right, so max line width <= 272 - 32 = 240 px.
# At fs = 24, sans char width = 0.6 * 24 = 14.4 px.
# Max chars per line = 240 / 14.4 = 16.66 -> 16 chars!

lines_5 = [
    "cluster",
    "autoscaler",
    "notices pending",
    "pods that a",
    "node group could",
    "fit"
]

# Can we do 5 lines?
# "cluster" (7)
# "autoscaler" (10) -> wait, "cluster" + " " + "autoscaler" = 18 chars (18 * 14.4 = 259.2 > 240).
# What if fs = 24 for the text?
