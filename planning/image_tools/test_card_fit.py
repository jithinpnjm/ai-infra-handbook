# Let's test the 5 steps of scale up with top-row circle and icon:
# Card width: 700 (x=60 to 760). Available text width: 700 - 2 * 25 = 650 px.

def est_w(s, fs=24, is_mono=False):
    return len(s) * (0.62 if is_mono else 0.60) * fs

steps = [
    ("Step 1", [
        ("1 pods Pending with FailedScheduling", False),
        ("for insufficient resources", False)
    ]),
    ("Step 2", [
        ("2 for each node group, simulate adding a", False),
        ("node from its template: would the pod fit", False)
    ]),
    ("Step 3", [
        ("3 expander picks among groups: random picks any,", False),
        ("least-waste leaves the fewest empty seats,", False),
        ("most-pods carries the most waiting pods", False)
    ]),
    ("Step 4", [
        ("4 group size raised within its min and max,", False),
        ("for example --nodes=1:10:worker-auto-scaling-group", True)
    ]),
    ("Step 5", [
        ("5 node joins, scheduler places pods", False)
    ])
]

print("Testing 650 px width:")
for name, lines in steps:
    print(name)
    for l, is_m in lines:
        w = est_w(l, 24, is_m)
        fits = w <= 650
        print(f"  [{w:5.1f} / 650 | {'OK' if fits else 'FAIL'}] {l}")
        assert fits

print("\nALL 5 STEPS FIT PERFECTLY IN 650 PX!")
