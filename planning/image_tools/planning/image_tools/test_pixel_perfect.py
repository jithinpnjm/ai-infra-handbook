#!/usr/bin/env python3

def test_perfect_solution():
    boxes = [
        # SECTION 1: 110 to 290 (h=180)
        ("section-anatomy", (40, 110, 1520, 180), [
            ("name-version-pythontag-abitag-platformtag", "mono", 24, "middle", 800, 150),
            ("numpy-1.26.4-cp311-cp311-manylinux_2_17_x86_64.whl", "mono", 24, "middle", 800, 178),
        ]),
        ("piece-1", (60, 192, 190, 88), [
            ("numpy:", "mono", 24, "middle", 155, 232),
            ("name", "sans", 24, "middle", 155, 258),
        ]),
        ("piece-2", (265, 192, 190, 88), [
            ("1.26.4:", "mono", 24, "middle", 360, 232),
            ("version", "sans", 24, "middle", 360, 258),
        ]),
        ("piece-3", (470, 192, 310, 88), [
            ("cp311: Python tag", "sans", 24, "middle", 625, 232),
            ("(CPython 3.11)", "sans", 24, "middle", 625, 258),
        ]),
        ("piece-4", (795, 192, 190, 88), [
            ("cp311:", "mono", 24, "middle", 890, 232),
            ("ABI tag", "sans", 24, "middle", 890, 258),
        ]),
        ("piece-5", (1000, 192, 540, 88), [
            ("manylinux_2_17_x86_64: platform tag", "sans", 24, "middle", 1270, 232),
            ("(x86_64 Linux, glibc-compatible)", "sans", 24, "middle", 1270, 258),
        ]),

        # SECTION 2: 330 to 605 (h=275)
        ("var-1", (125, 338, 700, 84), [
            ("py3-none-any:", "mono", 24, "middle", 475, 378),
            ("pure Python, installs anywhere", "sans", 24, "middle", 475, 400),
        ]),
        ("var-2", (845, 338, 700, 84), [
            ("manylinux: runs on most Linux distributions", "sans", 24, "middle", 1195, 378),
            ("with a compatible glibc", "sans", 24, "middle", 1195, 400),
        ]),
        ("var-3", (125, 428, 700, 84), [
            ("musllinux:", "mono", 24, "middle", 475, 468),
            ("Alpine, which uses musl instead", "sans", 24, "middle", 475, 490),
        ]),
        ("var-4", (845, 428, 700, 84), [
            ("abi3:", "mono", 24, "middle", 1195, 468),
            ("the stable ABI", "sans", 24, "middle", 1195, 490),
        ]),
        ("var-5", (125, 518, 700, 84), [
            ("+cu121: local version label (PEP 440) marking", "sans", 24, "middle", 475, 558),
            ("a CUDA build, used by PyTorch index wheels", "sans", 24, "middle", 475, 580),
        ]),
        ("var-6", (845, 518, 700, 84), [
            ("aarch64: Grace and other ARM hosts,", "sans", 24, "middle", 1195, 558),
            ("some packages have no wheels", "sans", 24, "middle", 1195, 580),
        ]),

        # SECTION 3: 645 to 835 (h=190)
        ("box-decision", (40, 645, 450, 190), [
            ("pip finds a", "sans", 30, "middle", 280, 725),
            ("compatible wheel?", "sans", 30, "middle", 280, 763),
        ]),
        ("box-yes", (620, 645, 940, 70), [
            ("unzip, no build step, fast", "sans", 28, "middle", 1100, 689),
        ]),
        ("box-no", (620, 720, 940, 114), [
            ("builds from the sdist: needs compilers and headers;", "sans", 24, "middle", 1100, 760),
            ("the usual reason an install takes 10 minutes or", "sans", 24, "middle", 1100, 784),
            ("fails in a slim container", "sans", 24, "middle", 1100, 808),
        ]),

        # SECTION 4: 875 to 1055 (h=180)
        ("tool-1", (56, 878, 1488, 84), [
            ("python -m build makes dist/myops-0.3.1.tar.gz (sdist)", "mono", 24, "middle", 800, 918),
            ("and dist/myops-0.3.1-py3-none-any.whl (wheel)", "mono", 24, "middle", 800, 940),
        ]),
        ("tool-2", (56, 968, 734, 84), [
            ("python -m pip debug --verbose", "mono", 24, "middle", 423, 1008),
            ("lists the supported tags", "sans", 24, "middle", 423, 1030),
        ]),
        ("tool-3", (810, 968, 734, 84), [
            ("pip download --only-binary=:all:", "mono", 24, "middle", 1177, 1008),
            ("--platform manylinux2014_aarch64 ...", "mono", 24, "middle", 1177, 1030),
        ]),

        # SECTION 5: 1095 to 1160 (h=65)
        ("bottom-bar", (40, 1095, 1520, 65), [
            ("Check the tags of every wheel you plan to ship against the machines that will install it", "sans", 26, "middle", 800, 1137),
        ])
    ]

    all_passed = True
    for bid, (bx, by, bw, bh), lines in boxes:
        b_right = bx + bw
        b_bot = by + bh
        for i, (txt, ff, fs, anchor, lx, ly) in enumerate(lines):
            mult = 0.62 if ff == "mono" else 0.60
            lw = len(txt) * fs * mult
            if anchor == "middle":
                l_start = lx - lw / 2
                l_end = lx + lw / 2
            else:
                l_start = lx
                l_end = lx + lw
            l_top = ly - fs
            l_bot = ly + 0.25 * fs
            
            pad_l = l_start - bx
            pad_r = b_right - l_end
            pad_t = l_top - by
            pad_b = b_bot - l_bot
            
            errs = []
            if pad_l < 16.0: errs.append(f"L={pad_l:.1f}<16")
            if pad_r < 16.0: errs.append(f"R={pad_r:.1f}<16")
            if i == 0 and pad_t < 16.0: errs.append(f"T={pad_t:.1f}<16")
            if i == len(lines) - 1 and pad_b < 16.0: errs.append(f"B={pad_b:.1f}<16")
            
            status = "OK"
            if errs:
                status = "FAIL: " + ", ".join(errs)
                all_passed = False
            print(f"[{bid:18s}] '{txt[:26]:26s}' -> L:{pad_l:5.1f} R:{pad_r:5.1f} T:{pad_t:5.1f} B:{pad_b:5.1f} | {status}")

    print(f"\nFinal Result: {'ALL PASSED PERFECTLY!' if all_passed else 'SOME FAILED'}")

test_perfect_solution()
