# Let's test the 12 rows and all labels
title = "Import and install errors: symptom, likely cause, first fix"

rows = [
    (
        "ModuleNotFoundError: No module named x",
        "wrong interpreter or venv, not installed, typo, wrong directory",
        "which python, python -m pip show x, activate venv, print sys.path"
    ),
    (
        "ImportError: cannot import name y from x",
        "version mismatch, circular import or shadowing",
        "check x.__file__ and version, look for local x.py"
    ),
    (
        "AttributeError: module x has no attribute",
        "shadowed module (random.py, requests.py) or old version",
        "rename file, remove __pycache__"
    ),
    (
        "attempted relative import with no known parent package",
        "running a package file as a script",
        "python -m pkg.module"
    ),
    (
        "externally-managed-environment",
        "PEP 668 on system Python",
        "venv, pipx, distribution package"
    ),
    (
        "ResolutionImpossible",
        "conflicting constraints",
        "read the chain, relax pins, pip install -vv, separate environments"
    ),
    (
        "Works in shell, fails in cron or systemd",
        "different PATH, interpreter or env",
        "absolute venv python path, Environment=, log sys.executable"
    ),
    (
        "GLIBC_2.xx not found or illegal instruction",
        "wheel built for newer glibc or CPU",
        "matching manylinux tag or container, build from source"
    ),
    (
        "CUDA driver version is insufficient",
        "wheel CUDA runtime newer than driver",
        "upgrade driver or use cu118"
    ),
    (
        "numpy.core.multiarray failed to import",
        "NumPy 1 and 2 mismatch",
        "align versions, rebuild extensions"
    ),
    (
        "Slow imports or startup",
        "heavy top-level imports, network filesystem",
        "-X importtime, lazy imports, local copy, container"
    ),
    (
        "Different behaviour on two nodes",
        "unpinned dependency drift",
        "lockfile, hashes, image digests, pip freeze diff"
    )
]

strip = "pip debug --verbose, pipdeptree, pip index versions pkg, ldd on torch libraries, strace -f -e trace=openat python -c import x"
bottom_bar = "Read the error line first, then find the matching row"

print(f"Number of rows: {len(rows)}")
for i, r in enumerate(rows, 1):
    print(f"Row {i:2d}:")
    print(f"  Col 1 (mono/sans): {len(r[0])} chars | {r[0]}")
    print(f"  Col 2 (sans):      {len(r[1])} chars | {r[1]}")
    print(f"  Col 3 (mono/sans): {len(r[2])} chars | {r[2]}")

print("\nStrip:")
print(f"  {len(strip)} chars | {strip}")

print("\nBottom bar:")
print(f"  {len(bottom_bar)} chars | {bottom_bar}")
