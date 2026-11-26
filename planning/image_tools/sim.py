# Let's test a complete layout in python with exact coordinates.
# Let's define the canvas: 1600 x 1200.

# Let's see:
# Margin top: 90 (Title at y=55)
# Margin bottom: 40
# Usable height: 1200 - 130 = 1070

# Let's test:
# Subgraph 1: users ("Login / submit nodes")
#   Width: 1500, Height: 180, x: 50, y: 90
#   U1 (left): x: 80, y: 140, w: 680, h: 105
#   U2 (right): x: 800, y: 140, w: 720, h: 105

# Subgraph 2: control ("Control plane")
#   Width: 1500, Height: 380, x: 50, y: 310
#   REST: x: 80, y: 360, w: 320, h: 90
#   BACKUP: x: 80, y: 470, w: 380, h: 90
#   CTLD: x: 490, y: 360, w: 460, h: 150
#   DBD: x: 1000, y: 360, w: 260, h: 130
#   DB: x: 1300, y: 360, w: 220, h: 130

# Subgraph 3: compute ("Compute nodes (data plane)")
#   Width: 980, Height: 440, x: 50, y: 720
#   ...

# Standalone: MUNGE
#   x: 1060, y: 760, w: 480, h: 140

print("Drafting coordinates...")
