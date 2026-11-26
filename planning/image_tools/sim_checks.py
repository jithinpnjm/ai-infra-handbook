def check_line(text, is_mono, max_w):
    w = sum(14.88 if is_mono else 14.4 for c in text)
    print(f"[{'MONO' if is_mono else 'SANS'}] w={w:.1f} / {max_w}: {text}")
    return w <= max_w

# Test line wraps:
print("--- Fix Box (max_w = 1380) ---")
fix_l1 = "call the interpreter by absolute path: /path/to/.venv/bin/python -m pip install requests; "
fix_l2 = "systemd ExecStart=/opt/myops/.venv/bin/myops with Environment=PYTHONUNBUFFERED=1, "
fix_l3 = "a dedicated user and ProtectSystem= hardening from chapter 1.15; log sys.executable"
check_line(fix_l1, True, 1380)
check_line(fix_l2, True, 1380)
check_line(fix_l3, True, 1380)

print("\n--- Rules Strip (max_w = 1380) ---")
r_l1 = "python -m pip, not bare pip; one environment per project; recreate rather than repair; "
r_l2 = "rebuild after upgrading the base Python since a venv borrows its interpreter; never sudo pip install: "
r_l3 = "PEP 668 externally-managed-environment, use venv, pipx or distribution packages; --system-site-packages weakens isolation"
check_line(r_l1, False, 1380)
check_line(r_l2, False, 1380)
check_line(r_l3, False, 1380)

print("\n--- Bottom Bar (max_w = 1440) ---")
b_l1 = "Activation only changes the shell you are sitting in"
check_line(b_l1, False, 1440)
