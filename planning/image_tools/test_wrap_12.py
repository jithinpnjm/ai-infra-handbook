rows = [
    # (col1, col2, col3)
    (
        ["ModuleNotFoundError:", "No module named x"],
        ["wrong interpreter or venv, not", "installed, typo, wrong directory"],
        ["which python, python -m pip show x,", "activate venv, print sys.path"]
    ),
    (
        ["ImportError: cannot import", "name y from x"],
        ["version mismatch, circular", "import or shadowing"],
        ["check x.__file__ and version,", "look for local x.py"]
    ),
    (
        ["AttributeError: module x", "has no attribute"],
        ["shadowed module (random.py,", "requests.py) or old version"],
        ["rename file, remove __pycache__"]
    ),
    (
        ["attempted relative import with", "no known parent package"],
        ["running a package file as a script"],
        ["python -m pkg.module"]
    ),
    (
        ["externally-managed-environment"],
        ["PEP 668 on system Python"],
        ["venv, pipx, distribution package"]
    ),
    (
        ["ResolutionImpossible"],
        ["conflicting constraints"],
        ["read the chain, relax pins, pip", "install -vv, separate environments"]
    ),
    (
        ["Works in shell, fails in cron", "or systemd"],
        ["different PATH, interpreter or env"],
        ["absolute venv python path,", "Environment=, log sys.executable"]
    ),
    (
        ["GLIBC_2.xx not found or", "illegal instruction"],
        ["wheel built for newer glibc or CPU"],
        ["matching manylinux tag or", "container, build from source"]
    ),
    (
        ["CUDA driver version is", "insufficient"],
        ["wheel CUDA runtime newer", "than driver"],
        ["upgrade driver or use cu118"]
    ),
    (
        ["numpy.core.multiarray", "failed to import"],
        ["NumPy 1 and 2 mismatch"],
        ["align versions, rebuild extensions"]
    ),
    (
        ["Slow imports or startup"],
        ["heavy top-level imports,", "network filesystem"],
        ["-X importtime, lazy imports,", "local copy, container"]
    ),
    (
        ["Different behaviour on", "two nodes"],
        ["unpinned dependency drift"],
        ["lockfile, hashes, image digests,", "pip freeze diff"]
    )
]

col1_w = 460
col2_w = 480
col3_w = 580

def check_line(text, max_w, is_mono):
    factor = 0.62 if is_mono else 0.60
    w = len(text) * 24 * factor
    pad = (max_w - w) / 2
    return w, max_w - w, pad

print("Checking lines...")
all_ok = True
for i, (c1, c2, c3) in enumerate(rows, 1):
    print(f"\nRow {i}: (c1={len(c1)}, c2={len(c2)}, c3={len(c3)})")
    for l in c1:
        w, rem, pad = check_line(l, col1_w, True) # assume mono or sans
        if rem < 32:
            print(f"  FAIL c1: '{l}' w={w:.1f} rem={rem:.1f}")
            all_ok = False
        else:
            print(f"  OK c1: '{l}' len={len(l)} w={w:.1f} rem={rem:.1f} pad={pad:.1f}")
    for l in c2:
        w, rem, pad = check_line(l, col2_w, False) # sans
        if rem < 32:
            print(f"  FAIL c2: '{l}' w={w:.1f} rem={rem:.1f}")
            all_ok = False
        else:
            print(f"  OK c2: '{l}' len={len(l)} w={w:.1f} rem={rem:.1f} pad={pad:.1f}")
    for l in c3:
        w, rem, pad = check_line(l, col3_w, True) # mono
        if rem < 32:
            print(f"  FAIL c3: '{l}' w={w:.1f} rem={rem:.1f}")
            all_ok = False
        else:
            print(f"  OK c3: '{l}' len={len(l)} w={w:.1f} rem={rem:.1f} pad={pad:.1f}")

assert all_ok
print("\nALL LINES FIT IN THEIR COLUMNS WITH AT LEAST 16PX PADDING!")
