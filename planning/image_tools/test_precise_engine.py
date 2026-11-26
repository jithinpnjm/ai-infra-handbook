import re
import xml.etree.ElementTree as ET

title_text = "Import and install errors: symptom, likely cause, first fix"

# 12 rows:
rows_data = [
    # Row 1
    (
        "ModuleNotFoundError: No module named x",
        ["ModuleNotFoundError:", "No module named x"],
        "wrong interpreter or venv, not installed, typo, wrong directory",
        ["wrong interpreter or venv,", "not installed, typo,", "wrong directory"],
        "which python, python -m pip show x, activate venv, print sys.path",
        ["which python, python -m pip", "show x, activate venv,", "print sys.path"],
        True # orange highlight
    ),
    # Row 2
    (
        "ImportError: cannot import name y from x",
        ["ImportError: cannot import", "name y from x"],
        "version mismatch, circular import or shadowing",
        ["version mismatch, circular", "import or shadowing"],
        "check x.__file__ and version, look for local x.py",
        ["check x.__file__ and version,", "look for local x.py"],
        False
    ),
    # Row 3
    (
        "AttributeError: module x has no attribute",
        ["AttributeError: module x", "has no attribute"],
        "shadowed module (random.py, requests.py) or old version",
        ["shadowed module (random.py,", "requests.py) or old version"],
        "rename file, remove __pycache__",
        ["rename file, remove __pycache__"],
        False
    ),
    # Row 4
    (
        "attempted relative import with no known parent package",
        ["attempted relative import", "with no known parent package"],
        "running a package file as a script",
        ["running a package file", "as a script"],
        "python -m pkg.module",
        ["python -m pkg.module"],
        False
    ),
    # Row 5
    (
        "externally-managed-environment",
        ["externally-managed-environment"],
        "PEP 668 on system Python",
        ["PEP 668 on system Python"],
        "venv, pipx, distribution package",
        ["venv, pipx, distribution package"],
        False
    ),
    # Row 6
    (
        "ResolutionImpossible",
        ["ResolutionImpossible"],
        "conflicting constraints",
        ["conflicting constraints"],
        "read the chain, relax pins, pip install -vv, separate environments",
        ["read the chain, relax pins, pip", "install -vv, separate environments"],
        False
    ),
    # Row 7
    (
        "Works in shell, fails in cron or systemd",
        ["Works in shell, fails", "in cron or systemd"],
        "different PATH, interpreter or env",
        ["different PATH, interpreter", "or env"],
        "absolute venv python path, Environment=, log sys.executable",
        ["absolute venv python path,", "Environment=, log sys.executable"],
        False
    ),
    # Row 8
    (
        "GLIBC_2.xx not found or illegal instruction",
        ["GLIBC_2.xx not found or", "illegal instruction"],
        "wheel built for newer glibc or CPU",
        ["wheel built for newer", "glibc or CPU"],
        "matching manylinux tag or container, build from source",
        ["matching manylinux tag or", "container, build from source"],
        False
    ),
    # Row 9
    (
        "CUDA driver version is insufficient",
        ["CUDA driver version is", "insufficient"],
        "wheel CUDA runtime newer than driver",
        ["wheel CUDA runtime", "newer than driver"],
        "upgrade driver or use cu118",
        ["upgrade driver or use cu118"],
        False
    ),
    # Row 10
    (
        "numpy.core.multiarray failed to import",
        ["numpy.core.multiarray", "failed to import"],
        "NumPy 1 and 2 mismatch",
        ["NumPy 1 and 2 mismatch"],
        "align versions, rebuild extensions",
        ["align versions, rebuild extensions"],
        False
    ),
    # Row 11
    (
        "Slow imports or startup",
        ["Slow imports or startup"],
        "heavy top-level imports, network filesystem",
        ["heavy top-level imports,", "network filesystem"],
        "-X importtime, lazy imports, local copy, container",
        ["-X importtime, lazy imports,", "local copy, container"],
        False
    ),
    # Row 12
    (
        "Different behaviour on two nodes",
        ["Different behaviour on", "two nodes"],
        "unpinned dependency drift",
        ["unpinned dependency drift"],
        "lockfile, hashes, image digests, pip freeze diff",
        ["lockfile, hashes, image digests,", "pip freeze diff"],
        False
    )
]

strip_text = "pip debug --verbose, pipdeptree, pip index versions pkg, ldd on torch libraries, strace -f -e trace=openat python -c import x"
strip_lines = [
    "pip debug --verbose, pipdeptree, pip index versions pkg,",
    "ldd on torch libraries, strace -f -e trace=openat python -c import x"
]

bottom_bar_text = "Read the error line first, then find the matching row"

# Column widths:
col1_w = 480
col2_w = 470
col3_w = 570
total_w = col1_w + col2_w + col3_w
assert total_w == 1520

print(f"Table width: {total_w}")

# Check string reconstructions:
for i, (f1, l1, f2, l2, f3, l3, is_o) in enumerate(rows_data, 1):
    r1 = " ".join(l1)
    r2 = " ".join(l2)
    r3 = " ".join(l3)
    assert r1 == f1, f"Row {i} Col 1 mismatch: '{r1}' != '{f1}'"
    assert r2 == f2, f"Row {i} Col 2 mismatch: '{r2}' != '{f2}'"
    assert r3 == f3, f"Row {i} Col 3 mismatch: '{r3}' != '{f3}'"

assert " ".join(strip_lines) == strip_text
print("All string reconstructions match exact source labels!")


# Table geometry:
# Table x from 40 to 1560
# Col 1: 40 to 520 (width 480)
# Col 2: 520 to 990 (width 470)
# Col 3: 990 to 1560 (width 570)

# In each column, text x start:
# Col 1: 40 + 24 = 64
# Col 2: 520 + 24 = 544
# Col 3: 990 + 24 = 1014

# Let's verify horizontal bounds for every line:
for i, (f1, l1, f2, l2, f3, l3, is_o) in enumerate(rows_data, 1):
    for line in l1:
        w = len(line) * 24 * 0.60 # sans
        right_pad = 480 - 24 - w
        assert right_pad >= 16, f"Row {i} Col 1 right_pad={right_pad:.1f} < 16 for '{line}'"
    for line in l2:
        w = len(line) * 24 * 0.60 # sans
        right_pad = 470 - 24 - w
        assert right_pad >= 16, f"Row {i} Col 2 right_pad={right_pad:.1f} < 16 for '{line}'"
    for line in l3:
        w = len(line) * 24 * 0.62 # mono
        right_pad = 570 - 24 - w
        assert right_pad >= 16, f"Row {i} Col 3 right_pad={right_pad:.1f} < 16 for '{line}'"

print("Horizontal padding >= 16px verified for all rows!")

# Now check Deeper tools strip:
# Strip box: x = 40, width = 1520.
# Left margin: 24px (x = 64).
for line in strip_lines:
    w = len(line) * 24 * 0.62 # mono
    right_pad = 1520 - 24 - w
    print(f"Strip line: '{line}' w={w:.1f}px, right_pad={right_pad:.1f}px")
    assert right_pad >= 16

# Bottom bar:
# Box: x = 40, width = 1520. Text centered at x = 800.
bb_w = len(bottom_bar_text) * 30 * 0.60 # sans 30px bold
bb_pad = (1520 - bb_w) / 2
print(f"Bottom bar: w={bb_w:.1f}px, pad={bb_pad:.1f}px")
assert bb_pad >= 16

