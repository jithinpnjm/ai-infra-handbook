from sim_full_audit import audit_card

checks_y = 664
c_card1_y = checks_y + 12 # 676
c_card1_h = 84
c_card2_y = c_card1_y + c_card1_h + 10 # 770
c_card2_h = 84

# Checks container: x=40, y=664, width=1520, height=202 (bottom=866)
# Usable space:
# Icon at x=64..120 (56px)
# Left column cards: x=136, width=540 (ends at 676)
# Right column cards: x=696, width=844 (ends at 1540)

print("=== Checks Strip Cards ===")
# Card 1 (Left Col, Row 1): which python
audit_card("Check 1", 136, c_card1_y, 540, c_card1_h, [
    ("which python", 156, c_card1_y + 48)
], is_mono=True)

# Card 2 (Left Col, Row 2): python -m pip show x
audit_card("Check 2", 136, c_card2_y, 540, c_card2_h, [
    ("python -m pip show x", 156, c_card2_y + 48)
], is_mono=True)

# Card 3 (Right Col, Row 1): python -c "import sys; print(sys.prefix, sys.base_prefix)" (they differ inside a venv)
audit_card("Check 3", 696, c_card1_y, 844, c_card1_h, [
    ("python -c \"import sys; print(sys.prefix, ", 716, c_card1_y + 34),
    ("sys.base_prefix)\" (they differ inside a venv)", 716, c_card1_y + 62)
])

# Card 4 (Right Col, Row 2): python -m site shows sys.path, user site and whether a venv is active
audit_card("Check 4", 696, c_card2_y, 844, c_card2_h, [
    ("python -m site shows sys.path, user site ", 716, c_card2_y + 34),
    ("and whether a venv is active", 716, c_card2_y + 62)
])
