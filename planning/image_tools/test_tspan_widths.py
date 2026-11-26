import xml.etree.ElementTree as ET

# Let's inspect Step 1..5 lines and widths:
steps = [
    ("Step 1", [
        ("1 pods Pending with ", False),
        ("FailedScheduling for ", False),
        ("insufficient resources", False)
    ]),
    ("Step 2", [
        ("2 for each node group, simulate ", False),
        ("adding a node from its template: ", False),
        ("would the pod fit", False)
    ]),
    ("Step 3", [
        ("3 expander picks among groups: ", False),
        ("random picks any, least-waste ", False),
        ("leaves the fewest empty seats, ", False),
        ("most-pods carries the most waiting ", False),
        ("pods", False)
    ]),
    ("Step 4", [
        ("4 group size raised within its min ", False),
        ("and max, for example ", False),
        ("--nodes=1:10:worker-auto-scaling-group", True)
    ]),
    ("Step 5", [
        ("5 node joins, scheduler places ", False),
        ("pods", False)
    ])
]

# In Card 1..5: box x=65, w=690 -> box right = 755 px.
for name, lines in steps:
    print(f"\n{name}:")
    for i, (txt, is_m) in enumerate(lines):
        tx = 95 if (name == "Step 4" and i == 2) else 212
        coeff = 0.62 if is_m else 0.60
        w = len(txt) * coeff * 24
        right = tx + w
        pad_r = 755 - right
        print(f"  Line {i+1} [tx={tx}, w={w:.1f}, right={right:.1f}, pad_r={pad_r:.1f}]: '{txt}'")
        assert pad_r >= 16.0, f"Overflow in {name} line {i+1}: pad_r={pad_r:.1f} < 16!"

print("\nALL STEP LINES STRICTLY HAVE PAD_R >= 16 PX!")
