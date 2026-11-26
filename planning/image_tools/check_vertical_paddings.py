# Verify vertical clearances

boxes = [
    # (name, box_y, box_h, [(text, y, fs), ...])
    ("Card 1 cpustat", 245, 155, [
        ("line 1", 285, 24),
        ("line 2", 325, 24),
        ("line 3", 365, 24)
    ]),
    ("Card 2 rule", 415, 115, [
        ("line 1", 460, 25),
        ("line 2", 496, 25)
    ]),
    ("Card 3 cadvisor", 545, 145, [
        ("line 1", 632, 24),
        ("line 2", 668, 24)
    ]),
    ("Card 4 psi", 705, 105, [
        ("line 1", 766, 28)
    ]),
    ("Host box header", 245, 185, [
        ("64 CPUs", 288, 30)
    ]),
    ("Container box inside host", 315, 105, [
        ("cpu.max", 348, 24)
    ]),
    ("nproc badge", 365, 42, [
        ("nproc", 395, 24)
    ]),
    ("Result card", 450, 130, [
        ("line 1", 484, 24),
        ("line 2", 516, 24),
        ("line 3", 548, 24),
        ("line 4", 570, 24)
    ]),
    ("Fix Row 1", 602, 42, [("Go", 631, 24)]),
    ("Fix Row 2", 652, 42, [("Java", 681, 24)]),
    ("Fix Row 3", 702, 42, [("OpenMP", 731, 24)]),
    ("Fix Row 4", 752, 54, [("Python 1", 774, 24), ("Python 2", 798, 24)]),
    ("Footer 1", 855, 235, [
        ("line 1", 905, 24),
        ("line 2", 948, 24),
        ("line 3", 984, 24),
        ("line 4", 1020, 24)
    ]),
    ("Footer 2", 855, 235, [
        ("line 1", 905, 24),
        ("line 2", 948, 24),
        ("line 3", 984, 24),
        ("line 4", 1020, 24)
    ]),
    ("Footer 3", 855, 235, [
        ("line 1", 905, 24),
        ("line 2", 944, 24),
        ("line 3", 978, 24),
        ("line 4", 1012, 24),
        ("line 5", 1046, 24)
    ]),
    ("Bottom bar", 1110, 65, [("Takeaway", 1152, 25)])
]

print("Checking vertical clearances:")
all_vert_pass = True
for name, by, bh, lines in boxes:
    # Text baseline is at y. Font ascender is ~0.75*fs, descender is ~0.25*fs
    first_top = lines[0][1] - lines[0][2] * 0.75
    last_bot = lines[-1][1] + lines[-1][2] * 0.25
    pad_top = first_top - by
    pad_bot = (by + bh) - last_bot
    min_pad = min(pad_top, pad_bot)
    status = "PASS" if min_pad >= 14 else "FAIL"
    if status == "FAIL":
        all_vert_pass = False
    print(f"[{status}] {name:25s}: pad_top={pad_top:4.1f}px, pad_bot={pad_bot:4.1f}px (min={min_pad:4.1f}px)")

print("\nALL VERTICAL CLEARANCES PASS:", all_vert_pass)
