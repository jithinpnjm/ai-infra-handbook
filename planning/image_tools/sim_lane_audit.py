from sim_full_audit import audit_card

print("=== Left Lane Cards ===")
# Left Card 1
audit_card("Left Card 1", 58, 222, 704, 76, [
    ("source .venv/bin/activate puts .venv/bin ", 76, 250),
    ("at the front of PATH and sets VIRTUAL_ENV", 76, 280)
])

# Left Card 2
audit_card("Left Card 2", 58, 308, 704, 64, [
    ("python resolves to the venv interpreter", 76, 348)
])

# Left Card 3
audit_card("Left Card 3", 58, 382, 704, 64, [
    ("import works", 76, 422)
])

print("\n=== Right Lane Cards ===")
# Right Card 1
audit_card("Right Card 1", 838, 222, 704, 64, [
    ("no activation, a different PATH", 856, 262)
])

# Right Card 2
audit_card("Right Card 2", 838, 296, 704, 76, [
    ("bare python3 resolves to the ", 856, 326),
    ("system interpreter", 856, 354)
])

# Right Card 3
audit_card("Right Card 3", 838, 382, 704, 64, [
    ("ModuleNotFoundError: No module named x", 856, 422)
], is_mono=True)

