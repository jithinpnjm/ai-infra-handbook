def est_w(s, fs=24, is_mono=False):
    return len(s) * (0.62 if is_mono else 0.60) * fs

blockers = [
    ("B1", [("pods without controllers", False)]),
    ("B2", [("emptyDir local storage unless annotated", False)]),
    ("B3", [("PDBs", False)]),
    ("B4", [("kube-system pods", False)]),
    ("B5", [
        ("annotation", False),
        ("cluster-autoscaler.kubernetes.io/safe-to-evict false", True)
    ]),
    ("B6", [
        ("recently added node", False),
        ("(scale-down-delay-after-add)", True)
    ])
]

# Wait, in B5:
# "cluster-autoscaler.kubernetes.io/safe-to-evict false" is 52 chars!
# 52 * 14.88 = 773 px! That's > 650 px!
# Let's see how B5 can be split:
# "annotation cluster-autoscaler.kubernetes.io/" (43 chars * 14.88 = 640 px <= 650 px!)
# "safe-to-evict false" (19 chars * 14.88 = 282.7 px <= 650 px!)
# Or 3 lines:
# "annotation" (10 chars)
# "cluster-autoscaler.kubernetes.io/" (33 chars * 14.88 = 491 px)
# "safe-to-evict false" (19 chars * 14.88 = 282.7 px)

b5_lines = [
    ("annotation", False),
    ("cluster-autoscaler.kubernetes.io/", True),
    ("safe-to-evict false", True)
]

print("Testing B5 lines:")
for l, is_m in b5_lines:
    w = est_w(l, 24, is_m)
    print(f"  [{w:5.1f} / 650 | {'OK' if w <= 650 else 'FAIL'}] {l}")
    assert w <= 650

print("\nTesting other blockers:")
for name, lines in blockers:
    if name == "B5": continue
    print(name)
    for l, is_m in lines:
        w = est_w(l, 24, is_m)
        print(f"  [{w:5.1f} / 650 | {'OK' if w <= 650 else 'FAIL'}] {l}")
        assert w <= 650

print("\nALL BLOCKERS FIT PERFECTLY!")
