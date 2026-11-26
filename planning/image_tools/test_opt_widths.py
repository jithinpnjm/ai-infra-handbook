# Let's find optimal column widths and wrapping

# Check the raw strings:
# Col 1:
# 1. ModuleNotFoundError: No module named x
# 2. ImportError: cannot import name y from x
# 3. AttributeError: module x has no attribute
# 4. attempted relative import with no known parent package
# 5. externally-managed-environment
# 6. ResolutionImpossible
# 7. Works in shell, fails in cron or systemd
# 8. GLIBC_2.xx not found or illegal instruction
# 9. CUDA driver version is insufficient
# 10. numpy.core.multiarray failed to import
# 11. Slow imports or startup
# 12. Different behaviour on two nodes

# Col 2:
# 1. wrong interpreter or venv, not installed, typo, wrong directory
# 2. version mismatch, circular import or shadowing
# 3. shadowed module (random.py, requests.py) or old version
# 4. running a package file as a script
# 5. PEP 668 on system Python
# 6. conflicting constraints
# 7. different PATH, interpreter or env
# 8. wheel built for newer glibc or CPU
# 9. wheel CUDA runtime newer than driver
# 10. NumPy 1 and 2 mismatch
# 11. heavy top-level imports, network filesystem
# 12. unpinned dependency drift

# Col 3:
# 1. which python, python -m pip show x, activate venv, print sys.path
# 2. check x.__file__ and version, look for local x.py
# 3. rename file, remove __pycache__
# 4. python -m pkg.module
# 5. venv, pipx, distribution package
# 6. read the chain, relax pins, pip install -vv, separate environments
# 7. absolute venv python path, Environment=, log sys.executable
# 8. matching manylinux tag or container, build from source
# 9. upgrade driver or use cu118
# 10. align versions, rebuild extensions
# 11. -X importtime, lazy imports, local copy, container
# 12. lockfile, hashes, image digests, pip freeze diff

# Total table width = 1520 (x from 40 to 1560)
# Let's see: can we wrap lines into 2 lines for each cell?
# If every cell is at most 2 lines, then row height can be around 68-72px!
# 12 rows * 70px = 840px!
# 840px + title + deeper tools + bottom bar = 840 + 80 + 70 + 60 = 1050px <= 1200px!

