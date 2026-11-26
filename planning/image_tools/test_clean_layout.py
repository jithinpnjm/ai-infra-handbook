# Search for optimal grid layouts
import networkx as nx

edges = [
    ("Start", "Provisioned"),
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
    ("Decommissioned", "End"),
]

# Let's consider what the diagram represents:
# Top part: Provisioning -> Configuration -> Validation -> Ready
# Right part: Ready -> Cordoned -> Draining
# Bottom part / Remediation:
# Draining -> Maintenance -> Validating (short loop)
# Draining -> Quarantined -> Provisioned (longer loop)
# Exit: Ready -> Decommissioned -> End

# What if:
# Row 1 (Top):
# Provisioned, Configured, Validating
# Row 2 (Middle):
# Quarantined, Maintenance, Ready, Decommissioned
# Row 3 (Bottom):
# (empty / channel), Draining, Cordoned

print("Checking this layout...")
# Let's test the connections:
pos = {
    "Start": (-0.8, 0),
    "Provisioned": (0, 0),
    "Configured": (1, 0),
    "Validating": (2, 0),
    "Maintenance": (2, 1),
    "Ready": (3, 0),
    "Decommissioned": (4, 0),
    "End": (4.8, 0),
    "Cordoned": (3, 1),
    "Draining": (3, 2),
    "Quarantined": (0, 2),
}

# Let's check:
# 1. Start -> Provisioned: horizontal right
# 2. Provisioned -> Configured: horizontal right
# 3. Configured -> Validating: horizontal right
# 4. Validating -> Ready: horizontal right
# 5. Ready -> Decommissioned: horizontal right
# 6. Decommissioned -> End: horizontal right
# 7. Ready -> Cordoned: vertical down from (3,0) to (3,1)
# 8. Cordoned -> Draining: vertical down from (3,1) to (3,2)
# 9. Draining -> Maintenance: from (3,2) up-left to (2,1):
#    Goes left from (3,2) to (2,2), then UP to (2,1)
# 10. Maintenance -> Validating: straight UP from (2,1) to (2,0)
# 11. Draining -> Quarantined: from (3,2) goes LEFT along y=2.5 or y=2 straight to (0,2)!
# 12. Quarantined -> Provisioned: straight UP from (0,2) to (0,0)!

print("Checking intersections in this layout:")
# Let's verify:
# Path 10: Maintenance(2,1) -> Validating(2,0): segment x=2, y from 1 down to 0
# Path 11: Draining(3,2) -> Quarantined(0,2): segment y=2, x from 3 down to 0
# Wait! Does segment y=2 intersect segment x=2, y in [0, 1]?
# NO! Because y=2 is BELOW y in [0, 1]!
# Look at that: y=2 does NOT intersect y in [0, 1]!
# Path 12: Quarantined(0,2) -> Provisioned(0,0): segment x=0, y from 2 down to 0.
# Does x=0 intersect anything? No, it's at x=0!
print("ZERO INTERSECTIONS! Completely planar!")
