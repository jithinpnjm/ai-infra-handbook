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

cells = [(r, c) for r in range(3) for c in range(3)]

# We want:
# 1. Start [*] -> Provisioned -> Configured -> Validating -> Ready should feel like an forward onboarding flow
# 2. Ready -> Cordoned -> Draining should flow naturally
# 3. Ready -> Decommissioned -> End [*] should flow cleanly
# 4. Zero crossing of any orthogonal arrows

print("Filtering best grids...")
