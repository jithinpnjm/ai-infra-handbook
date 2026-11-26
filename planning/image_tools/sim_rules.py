def check_line(text, is_mono, max_w):
    w = sum(14.88 if is_mono else 14.4 for c in text)
    print(f"[{'MONO' if is_mono else 'SANS'}] len={len(text)} w={w:.1f} / {max_w}: {text}")
    return w <= max_w

print("--- Rules Strip 4 lines (max_w = 1380) ---")
r_l1 = "python -m pip, not bare pip; one environment per project; recreate rather than repair; "
r_l2 = "rebuild after upgrading the base Python since a venv borrows its interpreter; "
r_l3 = "never sudo pip install: PEP 668 externally-managed-environment, use venv, "
r_l4 = "pipx or distribution packages; --system-site-packages weakens isolation"

all_pass = all([
    check_line(r_l1, False, 1380),
    check_line(r_l2, False, 1380),
    check_line(r_l3, False, 1380),
    check_line(r_l4, False, 1380)
])
print("All pass:", all_pass)
