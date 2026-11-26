import math

# We want to design the SVG with width 1600, height 960 (or 1000).
# Let's test coordinates.
W = 1600
H = 960

# Centers of the 3 circles:
# Triangle:
# Top-Left: Closed
# Top-Right: Open
# Bottom-Center: Half-open
R = 160

c_closed = (400, 340)
c_open = (1200, 340)
c_half = (800, 750)

# Let's check distances:
# Closed to Open: dx = 800, dy = 0.
# Open to Half: dx = -400, dy = 410. dist = 572.8
# Half to Closed: dx = -400, dy = -410. dist = 572.8
# Perfectly isosceles triangle!

print(f"Triangle dimensions: base={c_open[0]-c_closed[0]}, height={c_half[1]-c_closed[1]}")
