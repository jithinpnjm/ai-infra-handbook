from sim_full_audit import audit_card

rules_top = 906
rules_h = 148
rules_lines = [
    ("python -m pip, not bare pip; one environment per project; recreate rather than repair; ", 140, rules_top + 34),
    ("rebuild after upgrading the base Python since a venv borrows its interpreter; ", 140, rules_top + 64),
    ("never sudo pip install: PEP 668 externally-managed-environment, use venv, ", 140, rules_top + 94),
    ("pipx or distribution packages; --system-site-packages weakens isolation", 140, rules_top + 124)
]
audit_card("Rules Strip", 40, rules_top, 1520, rules_h, rules_lines)
