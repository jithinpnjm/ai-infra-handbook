def est_w(s, fs=24, is_mono=False):
    return len(s) * (0.62 if is_mono else 0.60) * fs

limits = [
    ("reacts only to Pending pods; assumes", False),
    ("homogeneous node groups; does not", False),
    ("understand gang all-or-nothing needs", False)
]

gpu = [
    ("--gpu-total, burst pools min 0,", False),
    ("--balance-similar-node-groups", True)
]

print("Testing Limits:")
for l, is_m in limits:
    w = est_w(l, 24, is_m)
    print(f"  [{w:5.1f} / 650 | {'OK' if w <= 650 else 'FAIL'}] {l}")
    assert w <= 650

print("Testing GPU settings:")
for l, is_m in gpu:
    w = est_w(l, 24, is_m)
    print(f"  [{w:5.1f} / 650 | {'OK' if w <= 650 else 'FAIL'}] {l}")
    assert w <= 650

print("Bottom panels PASS!")
