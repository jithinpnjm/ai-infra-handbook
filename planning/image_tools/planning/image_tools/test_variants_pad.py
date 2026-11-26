def test_variants_paddings():
    # 2 columns x 3 rows
    # Col 1: x = 60, w = 720
    # Col 2: x = 820, w = 720
    items = [
        # (text, lines)
        ("py3-none-any: pure Python, installs anywhere", [
            "py3-none-any: pure Python, installs anywhere"
        ]),
        ("abi3: the stable ABI", [
            "abi3: the stable ABI"
        ]),
        ("musllinux: Alpine, which uses musl instead", [
            "musllinux: Alpine, which uses musl instead"
        ]),
        ("manylinux: runs on most Linux distributions with a compatible glibc", [
            "manylinux: runs on most Linux distributions",
            "with a compatible glibc"
        ]),
        ("aarch64: Grace and other ARM hosts, some packages have no wheels", [
            "aarch64: Grace and other ARM hosts,",
            "some packages have no wheels"
        ]),
        ("+cu121: local version label (PEP 440) marking a CUDA build, used by PyTorch index wheels", [
            "+cu121: local version label (PEP 440) marking",
            "a CUDA build, used by PyTorch index wheels"
        ]),
    ]

    bw = 720
    for text, lines in items:
        print(f"Item: {text[:35]}...")
        for l in lines:
            w = len(l) * 24 * 0.60
            pad = (bw - w) / 2
            print(f"  w={w:5.1f} | pad={pad:4.1f}px | '{l}'")
            assert pad >= 16, f"Padding {pad} < 16 for line '{l}'"

test_variants_paddings()
