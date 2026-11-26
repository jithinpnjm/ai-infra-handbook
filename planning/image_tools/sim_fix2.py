def check_line(text, is_mono, max_w):
    w = sum(14.88 if is_mono else 14.4 for c in text)
    print(f"[{'MONO' if is_mono else 'SANS'}] len={len(text)} w={w:.1f} / {max_w}: {text}")
    return w <= max_w

print("--- Fix Box 4 lines alternative (max_w = 1360) ---")
f_l1 = "call the interpreter by absolute path: "
f_l2 = "/path/to/.venv/bin/python -m pip install requests; "
f_l3 = "systemd ExecStart=/opt/myops/.venv/bin/myops with Environment=PYTHONUNBUFFERED=1, "
f_l4 = "a dedicated user and ProtectSystem= hardening from chapter 1.15; log sys.executable"

all_pass = all([
    check_line(f_l1, False, 1360),
    check_line(f_l2, True, 1360),
    check_line(f_l3, False, 1360),
    check_line(f_l4, False, 1360)
])
print("All pass:", all_pass)
