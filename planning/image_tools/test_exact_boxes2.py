# Re-check paddings with the new box widths:
# Box 1: 240
# Box 2: 220
# Box 3: 220
# Box 4: 290
# Box 5: 390
boxes = [
    ("Box 1", 240, [
        ("awk print $1", True, 24),
        ("keep the", False, 24),
        ("client address", False, 24),
        ("field", False, 24),
    ]),
    ("Box 2", 220, [
        ("sort", True, 26),
        ("equal", False, 24),
        ("addresses", False, 24),
        ("become", False, 24),
        ("neighbours", False, 24),
    ]),
    ("Box 3", 220, [
        ("uniq -c", True, 26),
        ("count each", False, 24),
        ("run of", False, 24),
        ("equal lines", False, 24),
    ]),
    ("Box 4", 290, [
        ("awk print $2, $1", True, 24),
        ("put address", False, 24),
        ("first, count", False, 24),
        ("second", False, 24),
    ]),
    ("Box 5", 390, [
        ("sort -k2,2nr -k1,1", True, 24),
        ("awk NR<=5", True, 24),
        ("rank by count,", False, 24),
        ("address breaks ties;", False, 24),
        ("awk instead of head so", False, 24),
        ("pipefail never reports", False, 24),
        ("exit 141", False, 24),
    ])
]

for bname, bw, items in boxes:
    print(f"\n=== {bname} (width={bw}) ===")
    for text, is_mono, fs in items:
        w = len(text) * (0.62 if is_mono else 0.6) * fs
        pad = (bw - w) / 2
        ok = pad >= 16.0
        assert ok, f"FAILED: pad {pad} < 16 for '{text}'"
        print(f"  [{'PASS' if ok else 'FAIL'}] pad={pad:5.1f}px (w={w:5.1f}px): '{text}'")

print("\nALL BOX PADDINGS >= 16PX CONFIRMED!")
