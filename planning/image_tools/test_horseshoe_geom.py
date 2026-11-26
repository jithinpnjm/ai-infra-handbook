# Complete geometric verification of horseshoe layout
import math

# Canvas: width = 1600, height = 1150
# Let's define the node coordinates and dimensions:
# State boxes: width = 280, height = 96
BW = 280
BH = 96

# Positions (center_x, center_y):
# Top row (y = 200):
#   Provisioned: x = 240
#   Configured:  x = 760
#   Validating:  x = 1260
# Middle row (y = 560):
#   Quarantined: x = 240
#   Maintenance: x = 760
#   Ready:       x = 1260
# Bottom row (y = 920):
#   (empty / return track)
#   Draining:    x = 760
#   Cordoned:    x = 1260
# Exit row / right wing:
#   Decommissioned: x = 1260, y = 380? Or x = 1450?
# Wait! Let's check where Decommissioned is placed!

print("Testing coordinates...")
