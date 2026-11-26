# Let's test the 2-column layout geometry

# LEFT COLUMN: x = 40, w = 580 (x: 40 .. 620)
# RIGHT COLUMN: x = 660, w = 900 (x: 660 .. 1560)
# Gap between columns = 660 - 620 = 40 px.
# Left margin = 40 px, Right margin = 40 px.

# Title: y = 48, 102. Bottom of title = 112.
# Sections start at y = 140.

# Left column items:
# 1. Flow of five boxes
# Box 1: "HPA asks for more replicas" (26 chars)
# Box 2: "pods sit Pending: no node has a free GPU" (40 chars)
# Box 3: "cluster autoscaler notices pending pods that a node group could fit" (67 chars)
# Box 4: "asks the cloud for a node; provisioning clock starts" (52 chars)
# Box 5: "node registers, image pull, weight load, ready" (46 chars)

# Let's test text lines and heights for each box:
# Inside left box (w = 580):
# Icon on left: x = 60, y = box_y + (h - 56)/2, w = 56, h = 56.
# Text starts at x = 140.
# Available text width = 580 - (140 - 40) - 20 = 460 px.
# At fs = 24, max line chars = 460 / 14.4 = 31.9 chars.

# Box 1:
# Line 1: "HPA asks for more replicas" (26 chars -> 26 * 14.4 = 374.4 px <= 460 px) -> 1 line!
# Box 1 height: 76 px.

# Box 2:
# Line 1: "pods sit Pending:" (17 chars -> 244.8 px)
# Line 2: "no node has a free GPU" (22 chars -> 316.8 px)
# Box 2 height: 96 px.

# Box 3:
# Line 1: "cluster autoscaler notices" (26 chars -> 374.4 px)
# Line 2: "pending pods that a node" (24 chars -> 345.6 px)
# Line 3: "group could fit" (15 chars -> 216 px)
# Box 3 height: 120 px.

# Box 4:
# Line 1: "asks the cloud for a node;" (26 chars -> 374.4 px)
# Line 2: "provisioning clock starts" (25 chars -> 360 px)
# Box 4 height: 96 px.

# Box 5:
# Line 1: "node registers, image pull," (27 chars -> 388.8 px)
# Line 2: "weight load, ready" (18 chars -> 259.2 px)
# Box 5 height: 96 px.

# 4 down arrows between boxes:
# Arrow length = 32 px each.
# Total height of 5 boxes = 76 + 32 + 96 + 32 + 120 + 32 + 96 + 32 + 96 = 612 px!
# Start at y = 140.
# Box 1: 140 .. 216
# Arrow 1: 216 .. 248 (length 32)
# Box 2: 248 .. 344
# Arrow 2: 344 .. 376 (length 32)
# Box 3: 376 .. 496
# Arrow 3: 496 .. 528 (length 32)
# Box 4: 528 .. 624
# Arrow 4: 624 .. 656 (length 32)
# Box 5: 656 .. 752

# Dashboard note:
# Gap = 40 px: y = 792 .. 942 (height = 150 px).
# In 580 px box:
# Text: "replica count rose at once while serving count stayed flat; that gap is what to explain" (87 chars)
# Line 1: "replica count rose at once while" (32 chars * 14.4 = 460.8 px -> make it 3 lines:)
# Line 1: "replica count rose at once" (26 chars -> 374.4 px)
# Line 2: "while serving count stayed flat;" (32 chars -> 460.8 px)
# Line 3: "that gap is what to explain" (27 chars -> 388.8 px)
# Text width <= 460 px.
# Height: 150 px.
# Left column ends at y = 942!

print("Left column ends at 942 px.")

# Now RIGHT COLUMN: x = 660, w = 900 (x: 660 .. 1560)
# Inside right boxes (w = 900):
# Text margin: at least 24 px on left and right -> usable text width = 900 - 48 = 852 px.
# Max chars per line = 852 / 14.4 = 59.1 chars.

# Card 1 (expander): 107 chars
# Line 1: "expander chooses which node group to grow:" (42 chars * 14.4 = 604.8 px)
# Line 2: "random, most-pods, least-waste, price, priority (rank GPU types)" (64 chars -> split:)
# Line 2: "random, most-pods, least-waste, price," (38 chars)
# Line 3: "priority (rank GPU types)" (25 chars)
# 3 lines -> height = 120 px.

# Card 2 (--max-node-provision-time): 152 chars
# Line 1: "--max-node-provision-time default 15 minutes:" (45 chars * 14.88 = 669.6 px)
# Line 2: "if a node has not registered by then the autoscaler" (51 chars * 14.4 = 734.4 px)
# Line 3: "stops counting it, which is why you keep warm capacity" (54 chars * 14.4 = 777.6 px)
# 3 lines -> height = 120 px.

# Card 3 (scale-down): 281 chars
# Line 1: "scale-down: node considered when pod CPU and memory requests" (60 chars -> 52 chars:)
# Line 1: "scale-down: node considered when pod CPU and" (44 chars)
# Line 2: "memory requests sum below 50 percent of allocatable;" (52 chars * 14.4 = 748.8 px)
# Line 3: "must stay unneeded 10 minutes; held 10 minutes after a scale-up;" (64 chars -> split:)
# Line 3: "must stay unneeded 10 minutes; held 10 minutes after a" (54 chars)
# Line 4: "scale-up; evicts through the eviction API for up to 2 minutes;" (62 chars -> 56 chars:)
# Line 4: "scale-up; evicts through the eviction API for up to" (51 chars)
# Line 5: "2 minutes; accelerator flag scale-down-gpu-utilization-threshold" (64 chars -> split:)
# Line 5: "2 minutes; accelerator flag" (27 chars)
# Line 6: "scale-down-gpu-utilization-threshold default 0.5" (48 chars * 14.88 = 714.2 px)
# 6 lines -> height = 210 px.

# Card 4 (Nebius): 270 chars
# Line 1: "autoscaling min and max node count flags; page gives" (52 chars * 14.4 = 748.8 px)
# Line 2: "no defaults or timings; keep a CPU node group of at" (51 chars * 14.4 = 734.4 px)
# Line 3: "least two nodes (or autoscaling) so CoreDNS and" (47 chars * 14.4 = 676.8 px)
# Line 4: "networking add-ons run there; known issue with" (46 chars * 14.4 = 662.4 px)
# Line 5: "GPU Operator and Network Operator creating extra nodes," (55 chars * 14.4 = 792.0 px)
# Line 6: "not reproduced" (14 chars)
# 6 lines -> height = 210 px.

# Heights of right column cards:
# y = 140
# Card 1: 140 .. 260 (h = 120)
# Gap = 24 px
# Card 2: 284 .. 404 (h = 120)
# Gap = 24 px
# Card 3: 428 .. 648 (h = 220)
# Gap = 40 px (between Settings table and Nebius notes)
# Card 4: 688 .. 908 (h = 220)
# Right column ends at 908 px!

print("Right column ends at 908 px.")
