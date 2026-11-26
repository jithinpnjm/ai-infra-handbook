from sim_full_audit import audit_card

fix_top = 540
fix_h = 130
lines = [
    ("call the interpreter by absolute path: /path/to/.venv/bin/python -m pip install requests; ", 140, fix_top + 36),
    ("systemd ExecStart=/opt/myops/.venv/bin/myops with Environment=PYTHONUNBUFFERED=1, ", 140, fix_top + 68),
    ("a dedicated user and ProtectSystem= hardening from chapter 1.15; log sys.executable", 140, fix_top + 100)
]
audit_card("Fix Box", 40, fix_top, 1520, fix_h, lines, is_mono=True)
