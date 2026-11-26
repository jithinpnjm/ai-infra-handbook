labels = [
    ("Reading a wheel filename and deciding between wheel and sdist", 48, False),
    ("name-version-pythontag-abitag-platformtag", 28, True),
    ("numpy-1.26.4-cp311-cp311-manylinux_2_17_x86_64.whl", 26, True),
    ("numpy: name", 24, False),
    ("1.26.4: version", 24, False),
    ("cp311: Python tag (CPython 3.11)", 24, False),
    ("cp311: ABI tag", 24, False),
    ("manylinux_2_17_x86_64: platform tag (x86_64 Linux, glibc-compatible)", 24, False),
    ("py3-none-any: pure Python, installs anywhere", 24, False),
    ("manylinux: runs on most Linux distributions with a compatible glibc", 24, False),
    ("musllinux: Alpine, which uses musl instead", 24, False),
    ("abi3: the stable ABI", 24, False),
    ("+cu121: local version label (PEP 440) marking a CUDA build, used by PyTorch index wheels", 24, False),
    ("aarch64: Grace and other ARM hosts, some packages have no wheels", 24, False),
    ("pip finds a compatible wheel?", 30, False),
    ("yes", 24, False),
    ("unzip, no build step, fast", 26, False),
    ("no", 24, False),
    ("builds from the sdist: needs compilers and headers; the usual reason an install takes 10 minutes or fails in a slim container", 24, False),
    ("python -m build makes dist/myops-0.3.1.tar.gz (sdist) and dist/myops-0.3.1-py3-none-any.whl (wheel)", 24, True),
    ("python -m pip debug --verbose lists the supported tags", 24, True),
    ("pip download --only-binary=:all: --platform manylinux2014_aarch64 ...", 24, True),
    ("Check the tags of every wheel you plan to ship against the machines that will install it", 26, False),
]

for text, fs, is_mono in labels:
    char_factor = 0.62 if is_mono else 0.60
    est_w = len(text) * fs * char_factor
    print(f"[{fs}px {'mono' if is_mono else 'sans'}] len={len(text):2d} est_w={est_w:6.1f}px | '{text}'")
