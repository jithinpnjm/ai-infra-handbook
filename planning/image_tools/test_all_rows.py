# Let's inspect each row and see if each can fit cleanly
# Col 1: 460 px, Col 2: 480 px, Col 3: 580 px (total = 1520)
# Or let's see what column widths work best when we test all 12 rows!

raw_rows = [
    # 1
    ("ModuleNotFoundError: No module named x",
     "wrong interpreter or venv, not installed, typo, wrong directory",
     "which python, python -m pip show x, activate venv, print sys.path"),
    # 2
    ("ImportError: cannot import name y from x",
     "version mismatch, circular import or shadowing",
     "check x.__file__ and version, look for local x.py"),
    # 3
    ("AttributeError: module x has no attribute",
     "shadowed module (random.py, requests.py) or old version",
     "rename file, remove __pycache__"),
    # 4
    ("attempted relative import with no known parent package",
     "running a package file as a script",
     "python -m pkg.module"),
    # 5
    ("externally-managed-environment",
     "PEP 668 on system Python",
     "venv, pipx, distribution package"),
    # 6
    ("ResolutionImpossible",
     "conflicting constraints",
     "read the chain, relax pins, pip install -vv, separate environments"),
    # 7
    ("Works in shell, fails in cron or systemd",
     "different PATH, interpreter or env",
     "absolute venv python path, Environment=, log sys.executable"),
    # 8
    ("GLIBC_2.xx not found or illegal instruction",
     "wheel built for newer glibc or CPU",
     "matching manylinux tag or container, build from source"),
    # 9
    ("CUDA driver version is insufficient",
     "wheel CUDA runtime newer than driver",
     "upgrade driver or use cu118"),
    # 10
    ("numpy.core.multiarray failed to import",
     "NumPy 1 and 2 mismatch",
     "align versions, rebuild extensions"),
    # 11
    ("Slow imports or startup",
     "heavy top-level imports, network filesystem",
     "-X importtime, lazy imports, local copy, container"),
    # 12
    ("Different behaviour on two nodes",
     "unpinned dependency drift",
     "lockfile, hashes, image digests, pip freeze diff")
]

# Let's test a balanced column width:
# col1_w = 470, col2_w = 470, col3_w = 580 (total = 1520)
col1_w = 470
col2_w = 470
col3_w = 580

# If Col 1 is sans-serif (font-size 24, bold or regular):
# factor = 0.60. Max chars in 1 line with 32px padding: (470-32)/14.4 = 30.4 chars.
# "externally-managed-environment" is 30 chars! 30 * 14.4 = 432 px.
# 470 - 432 = 38 px (19 px padding on left and right!). Fits on 1 line!
# What about "attempted relative import with no known parent package"? (54 chars)
# Line 1: "attempted relative import" (25 chars -> 360 px, pad = 55 px)
# Line 2: "with no known parent package" (28 chars -> 403.2 px, pad = 33.4 px)
# Fits on 2 lines!

# What about Col 2 (470 px, sans-serif, factor = 0.60)?
# Max chars for 1 line: 30.4 chars.
# Row 1: "wrong interpreter or venv, not installed, typo, wrong directory"
# Can be 3 lines:
# "wrong interpreter or venv," (26 chars -> 374.4 px, pad = 47.8 px)
# "not installed, typo," (20 chars -> 288 px, pad = 91 px)
# "wrong directory" (15 chars -> 216 px, pad = 127 px)
# Row 2:
# "version mismatch, circular" (26 chars -> 374.4 px)
# "import or shadowing" (19 chars -> 273.6 px)
# Row 3:
# "shadowed module (random.py," (27 chars -> 388.8 px, pad = 40.6 px)
# "requests.py) or old version" (27 chars -> 388.8 px, pad = 40.6 px)
# Row 4:
# "running a package file" (22 chars -> 316.8 px)
# "as a script" (11 chars -> 158.4 px)
# Row 5:
# "PEP 668 on system Python" (24 chars -> 345.6 px, pad = 62.2 px) -> 1 line!
# Row 6:
# "conflicting constraints" (23 chars -> 331.2 px) -> 1 line!
# Row 7:
# "different PATH, interpreter" (27 chars -> 388.8 px)
# "or env" (6 chars)
# Row 8:
# "wheel built for newer" (21 chars -> 302.4 px)
# "glibc or CPU" (12 chars -> 172.8 px)
# Row 9:
# "wheel CUDA runtime" (18 chars -> 259.2 px)
# "newer than driver" (17 chars -> 244.8 px)
# Row 10:
# "NumPy 1 and 2 mismatch" (22 chars -> 316.8 px) -> 1 line!
# Row 11:
# "heavy top-level imports," (24 chars -> 345.6 px)
# "network filesystem" (18 chars -> 259.2 px)
# Row 12:
# "unpinned dependency drift" (25 chars -> 360 px) -> 1 line!

# What about Col 3 (580 px, mono factor = 0.62)?
# Mono char width = 24 * 0.62 = 14.88 px.
# Max chars for 1 line: (580 - 32) / 14.88 = 36.8 chars.
# Row 1:
# "which python, python -m pip show x," (35 chars -> 35 * 14.88 = 520.8 px, rem = 59.2 px, pad = 29.6 px!)
# "activate venv, print sys.path" (29 chars -> 431.5 px, pad = 74.2 px)
# Row 2:
# "check x.__file__ and version," (29 chars -> 431.5 px)
# "look for local x.py" (19 chars -> 282.7 px)
# Row 3:
# "rename file, remove __pycache__" (31 chars -> 461.3 px, rem = 118.7 px, pad = 59.3 px) -> 1 line!
# Row 4:
# "python -m pkg.module" (20 chars -> 297.6 px) -> 1 line!
# Row 5:
# "venv, pipx, distribution package" (32 chars -> 476.2 px, rem = 103.8 px, pad = 51.9 px) -> 1 line!
# Row 6:
# "read the chain, relax pins, pip" (31 chars -> 461.3 px)
# "install -vv, separate environments" (34 chars -> 505.9 px, rem = 74.1 px, pad = 37.0 px)
# Row 7:
# "absolute venv python path," (26 chars -> 386.9 px)
# "Environment=, log sys.executable" (32 chars -> 476.2 px)
# Row 8:
# "matching manylinux tag or" (25 chars -> 372.0 px)
# "container, build from source" (28 chars -> 416.6 px)
# Row 9:
# "upgrade driver or use cu118" (27 chars -> 401.8 px) -> 1 line!
# Row 10:
# "align versions, rebuild extensions" (34 chars -> 505.9 px) -> 1 line!
# Row 11:
# "-X importtime, lazy imports," (28 chars -> 416.6 px)
# "local copy, container" (21 chars -> 312.5 px)
# Row 12:
# "lockfile, hashes, image digests," (32 chars -> 476.2 px)
# "pip freeze diff" (15 chars -> 223.2 px)

print("Everything fits within 470, 470, 580!")
