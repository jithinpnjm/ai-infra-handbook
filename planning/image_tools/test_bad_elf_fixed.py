def text_width(s, fs=24, is_mono=False):
    rate = 0.62 if is_mono else 0.60
    return len(s) * fs * rate

lines = [
    ("bad ELF", False),
    ("interpreter /", False),
    ("not found for", False),
    ("a file that exists", False),
    ("(glibc binary on", False),
    ("Alpine musl:", False),
    ("/lib64/ld-linux-", True),
    ("x86-64.so.2", True),
    ("missing)", False)
]

print("Checking padding in box of width 310:")
for line, is_mono in lines:
    w = text_width(line, 24, is_mono)
    pad = (310 - w) / 2
    print(f"  '{line}': w={w:.1f}px, pad={pad:.1f}px [{'PASS' if pad >= 16 else 'FAIL'}]")
    assert pad >= 16

print("ALL PASS!")
