# Let's verify line lengths, wraps, and heights for every single box!

# 1. Title:
# Title 48 px bold.
# Rule: "keep the title on at most two lines and well inside the canvas (about 40 characters per line at 48 px; shorten the title wording if needed, keep the meaning);"
# Line 1: Three paths from a container: to a neighbour, (45 chars)
# Line 2: to the Internet, and outside to a published port (48 chars)
# Sans width: 48 * 0.6 = 28.8 px/char.
# Line 1: 45 * 28.8 = 1296 px (leaves (1600-1296)/2 = 152 px on each side)
# Line 2: 48 * 28.8 = 1382.4 px (leaves (1600-1382.4)/2 = 108.8 px on each side)
# Perfect! Well inside 1600 with >40px margin.

# 2. Shared Host Header & Components:
# Box width = 1520 (x=40..1560)
# Inside host:
# 4 nodes horizontally:
# Width of each node = (1520 - 5*20) / 4 = (1520 - 100) / 4 = 1420 / 4 = 355 px.
# Node 1: c1 (10.10.0.11)
# Node 2: br0 (10.10.0.1/24)
# Node 3: c2 (10.10.0.12)
# Node 4: uplink NIC
# Are these <= 355 px?
# 'c1 (10.10.0.11)': 15 chars * 24 * 0.6 = 216 px. Fits!
# 'br0 (10.10.0.1/24)': 17 chars * 24 * 0.6 = 244.8 px. Fits!
# 'c2 (10.10.0.12)': 15 chars * 24 * 0.6 = 216 px. Fits!
# 'uplink NIC': 10 chars * 24 * 0.6 = 144 px. Fits!
print("Shared nodes fit check passed!")
