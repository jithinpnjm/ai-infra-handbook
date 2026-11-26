# Check all 32 grids for transition badge clearances
import itertools

states = [
    "Provisioned", "Configured", "Validating",
    "Ready", "Cordoned", "Draining",
    "Maintenance", "Quarantined", "Decommissioned"
]

edges = [
    ("Provisioned", "Configured"),
    ("Configured", "Validating"),
    ("Validating", "Ready"),
    ("Ready", "Cordoned"),
    ("Cordoned", "Draining"),
    ("Draining", "Maintenance"),
    ("Maintenance", "Validating"),
    ("Draining", "Quarantined"),
    ("Quarantined", "Provisioned"),
    ("Ready", "Decommissioned"),
]

# Let's inspect each of the 32 grids:
# Which grid has Provisioned at a position where Start [*] has plenty of space?
# If Provisioned is at (0,1) (top-center):
# Start [*] can be at (0,0) (top-left) or far left!
# Then Start -> Provisioned has a 300-500px runway!
# Let's check which grids have Provisioned at (0,1) or (1,0) or (0,0):

print("Checking grids...")
