#!/usr/bin/env python3

def test_3col_variants():
    # 3 columns:
    # Col 1: x = 125, w = 460
    # Col 2: x = 605, w = 460
    # Col 3: x = 1085, w = 460
    # Row 1: y = 380, h = 105
    # Row 2: y = 495, h = 105
    # Total height of Section 2: y = 365 to 615 (h = 250)
    
    items = [
        ("py3-none-any: pure Python, installs anywhere", [
            "py3-none-any:",
            "pure Python, installs anywhere"
        ]),
        ("manylinux: runs on most Linux distributions with a compatible glibc", [
            "manylinux: runs on most",
            "Linux distributions with",
            "a compatible glibc"
        ]),
        ("musllinux: Alpine, which uses musl instead", [
            "musllinux:",
            "Alpine, which uses musl instead"
        ]),
        ("abi3: the stable ABI", [
            "abi3:",
            "the stable ABI"
        ]),
        ("+cu121: local version label (PEP 440) marking a CUDA build, used by PyTorch index wheels", [
            "+cu121: local version label",
            "(PEP 440) marking a CUDA",
            "build, used by PyTorch wheels" # wait, label must be exact!
        ]),
        ("aarch64: Grace and other ARM hosts, some packages have no wheels", [
            "aarch64: Grace and other",
            "ARM hosts, some packages",
            "have no wheels"
        ])
    ]
    
    bw = 460
    for text, lines in items:
        print(f"Item: '{text[:30]}...'")
        for l in lines:
            w = len(l) * 24 * 0.60
            pad = (bw - w) / 2
            print(f"  w={w:5.1f} pad={pad:4.1f} | '{l}'")
            assert pad >= 16

test_3col_variants()
