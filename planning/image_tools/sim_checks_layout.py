def check_line(text, is_mono, max_w):
    w = sum(14.88 if is_mono else 14.4 for c in text)
    print(f"[{'MONO' if is_mono else 'SANS'}] len={len(text)} w={w:.1f} / {max_w}: {text}")
    return w <= max_w

# Option: 2 columns
# Left column: x=140..800 (width=660)
# Right column: x=820..1540 (width=720)
print("=== 2 Column Test ===")
# Left: which python, python -m pip show x
check_line("which python", True, 600)
check_line("python -m pip show x", True, 600)

# Right:
# Item 3:
print("\nItem 3:")
check_line("python -c \"import sys; print(sys.prefix, ", True, 680)
check_line("sys.base_prefix)\" (they differ inside a venv)", False, 680)

# Item 4:
print("\nItem 4:")
check_line("python -m site shows sys.path, user site ", False, 680)
check_line("and whether a venv is active", False, 680)

