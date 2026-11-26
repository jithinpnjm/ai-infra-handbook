def check_splits():
    # Let's test with exact splits:
    # Col 1: monospace (0.62) or sans (0.60)
    # Col 2: sans (0.60)
    # Col 3: monospace (0.62)

    col1 = [
        ["ModuleNotFoundError:", "No module named x"],
        ["ImportError: cannot import", "name y from x"],
        ["AttributeError: module x", "has no attribute"],
        ["attempted relative import", "with no known parent package"],
        ["externally-managed-", "environment"], # OR 1 line if sans!
        ["ResolutionImpossible"],
        ["Works in shell, fails", "in cron or systemd"],
        ["GLIBC_2.xx not found or", "illegal instruction"],
        ["CUDA driver version is", "insufficient"],
        ["numpy.core.multiarray", "failed to import"],
        ["Slow imports or startup"],
        ["Different behaviour on", "two nodes"]
    ]

    col2 = [
        ["wrong interpreter or venv,", "not installed, typo,", "wrong directory"],
        ["version mismatch, circular", "import or shadowing"],
        ["shadowed module (random.py,", "requests.py) or old version"],
        ["running a package file", "as a script"],
        ["PEP 668 on system Python"],
        ["conflicting constraints"],
        ["different PATH, interpreter", "or env"],
        ["wheel built for newer", "glibc or CPU"],
        ["wheel CUDA runtime", "newer than driver"],
        ["NumPy 1 and 2 mismatch"],
        ["heavy top-level imports,", "network filesystem"],
        ["unpinned dependency drift"]
    ]

    col3 = [
        ["which python, python -m pip", "show x, activate venv,", "print sys.path"],
        ["check x.__file__ and version,", "look for local x.py"],
        ["rename file, remove __pycache__"],
        ["python -m pkg.module"],
        ["venv, pipx, distribution package"],
        ["read the chain, relax pins, pip", "install -vv, separate environments"],
        ["absolute venv python path,", "Environment=, log sys.executable"],
        ["matching manylinux tag or", "container, build from source"],
        ["upgrade driver or use cu118"],
        ["align versions, rebuild extensions"],
        ["-X importtime, lazy imports,", "local copy, container"],
        ["lockfile, hashes, image digests,", "pip freeze diff"]
    ]

    col1_w = 470
    col2_w = 470
    col3_w = 580

    print("Checking Col 1 (mono 24px, 0.62 factor):")
    for i, lines in enumerate(col1, 1):
        for l in lines:
            w = len(l) * 24 * 0.62
            rem = col1_w - 24 - w
            print(f"  R{i:2d}: '{l}' ({len(l)} ch) -> w={w:.1f}px, right_pad={rem:.1f}px")
            assert rem >= 16, f"Col 1 overflow in row {i}: '{l}'"

    print("\nChecking Col 2 (sans 24px, 0.60 factor):")
    for i, lines in enumerate(col2, 1):
        for l in lines:
            w = len(l) * 24 * 0.60
            rem = col2_w - 24 - w
            print(f"  R{i:2d}: '{l}' ({len(l)} ch) -> w={w:.1f}px, right_pad={rem:.1f}px")
            assert rem >= 16, f"Col 2 overflow in row {i}: '{l}'"

    print("\nChecking Col 3 (mono 24px, 0.62 factor):")
    for i, lines in enumerate(col3, 1):
        for l in lines:
            w = len(l) * 24 * 0.62
            rem = col3_w - 24 - w
            print(f"  R{i:2d}: '{l}' ({len(l)} ch) -> w={w:.1f}px, right_pad={rem:.1f}px")
            assert rem >= 16, f"Col 3 overflow in row {i}: '{l}'"

    print("\nALL 3 COLUMNS PASS WITH LEFT PAD 24PX AND RIGHT PAD >= 16PX!")

check_splits()
