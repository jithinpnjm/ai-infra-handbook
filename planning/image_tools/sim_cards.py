def check_line(text, is_mono, max_w):
    w = sum(14.88 if is_mono else 14.4 for c in text)
    print(f"[{'MONO' if is_mono else 'SANS'}] len={len(text)} w={w:.1f} / {max_w}: {text}")
    return w <= max_w

print("--- Left Card 1 (max_w = 640) ---")
l1_1 = "source .venv/bin/activate puts .venv/bin "
l1_2 = "at the front of PATH and sets VIRTUAL_ENV"
check_line(l1_1, False, 640)
check_line(l1_2, False, 640)

print("\n--- Left Card 2 (max_w = 640) ---")
l2 = "python resolves to the venv interpreter"
check_line(l2, False, 640)

print("\n--- Left Card 3 (max_w = 640) ---")
l3 = "import works"
check_line(l3, False, 640)

print("\n--- Right Card 1 (max_w = 640) ---")
r1 = "no activation, a different PATH"
check_line(r1, False, 640)

print("\n--- Right Card 2 (max_w = 640) ---")
r2_1 = "bare python3 resolves to the "
r2_2 = "system interpreter"
check_line(r2_1, False, 640)
check_line(r2_2, False, 640)

print("\n--- Right Card 3 (max_w = 640) ---")
r3 = "ModuleNotFoundError: No module named x"
check_line(r3, True, 640)
