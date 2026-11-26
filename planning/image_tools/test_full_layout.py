import sys

# Let's check dimensions for H = 1200
# Canvas: 1600 x 1200
# Margins: 40px all around (x from 40 to 1560, total width 1520)

# Let's plan vertical allocation:
# Y = 40..110: Title (48px bold, 2 lines)
# Title line 1: y = 76 (baseline)
# Title line 2: y = 124 (baseline)
# Total title area = y 40 to 135.

# Now between Title and Host container: gap = 25px
# Host container starts at y = 160.
# What is inside Host?
# Or is Host container containing the 3 lanes?
# "Three horizontal lanes sharing a host with bridge br0 (10.10.0.1/24), containers c1 (10.10.0.11) and c2 (10.10.0.12), and an uplink NIC."

# Let's see: If Host is an outer container or top section:
# What if the top section inside Host is the 4 shared nodes:
# Node 1: c1 (10.10.0.11)
# Node 2: br0 (10.10.0.1/24)
# Node 3: c2 (10.10.0.12)
# Node 4: uplink NIC
# Height of shared node bar = 80px (y = 175 to 255)

# Then 3 horizontal lanes:
# Lane 1:
# Title: "c1 to c2 on the same bridge" (30px)
# Text & Note
# Lane 2:
# Title: "c1 to the Internet" (30px)
# Text & 4 commands
# Lane 3:
# Title: "host:8080 to c1:80" (30px)
# 2 commands
# Footer + Docker note
# Bottom bar: "A container is only a namespace plus a cable"

# Let's calculate total height required!
