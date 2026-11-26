# Layout simulation 1
import matplotlib.pyplot as plt

# Let's define the positions of all 11 entities (9 nodes + 2 terminals)
# Coordinates in [0, 1600] x [0, 1100]

positions = {
    "Start": (180, 110),
    "Provisioned": (180, 260),
    "Configured": (180, 560),
    "Validating": (180, 860),
    "Ready": (700, 560),
    "Decommissioned": (700, 860),
    "End": (700, 1020),
    "Cordoned": (1200, 260),
    "Draining": (1200, 560),
    "Maintenance": (1200, 860),
    "Quarantined": (700, 260),
}

# Let's trace the edges:
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

print("Simulating paths...")
