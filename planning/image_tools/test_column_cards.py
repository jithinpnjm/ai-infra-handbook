# Test text wrapping for all error messages and first checks in 4 columns

def text_width(s, fs=24, is_mono=False):
    rate = 0.62 if is_mono else 0.60
    return len(s) * fs * rate

# Column widths:
col_widths = {
    "col1": 370,
    "col2": 390,
    "col3": 350,
    "col4": 330
}

# Column 1 (Stage 1/2): width = 370
# Texts:
# 1. Exec format error (wrong CPU architecture such as x86-64 on aarch64, or a script without shebang)
# 2. exit 126 found but not executable
# 3. exit 127 not found
# First check: file and readelf -h

col1_cards = [
    {
        "name": "Exec format error",
        "lines": [
            ("Exec format error", False),
            ("(wrong CPU architecture", False),
            ("such as x86-64 on", False),
            ("aarch64, or a script", False),
            ("without shebang)", False)
        ]
    },
    {
        "name": "exit 126",
        "lines": [
            ("exit 126 found", False),
            ("but not executable", False)
        ]
    },
    {
        "name": "exit 127",
        "lines": [
            ("exit 127 not found", False)
        ]
    },
    {
        "name": "check 1",
        "lines": [
            ("file and readelf -h", True)
        ]
    }
]

# Column 2 (Stage 4): width = 390
# Texts:
# 1. bad ELF interpreter / not found for a file that exists (glibc binary on Alpine musl: /lib64/ld-linux-x86-64.so.2 missing)
# First check: readelf -l | grep interpreter

col2_cards = [
    {
        "name": "bad ELF interpreter",
        "lines": [
            ("bad ELF interpreter / not", False),
            ("found for a file that exists", False),
            ("(glibc binary on Alpine musl:", False),
            ("/lib64/", True),
            ("ld-linux-x86-64.so.2", True),
            ("missing)", False)
        ]
    },
    {
        "name": "check 2",
        "lines": [
            ("readelf -l | grep", True),
            ("interpreter", True)
        ]
    }
]

# Column 3 (Stage 5): width = 350
# Texts:
# 1. libcuda.so.1: cannot open shared object file
# 2. error while loading shared libraries: libnccl.so.2
# 3. version GLIBC_2.34 not found
# 4. version GLIBCXX_3.4.30 not found
# First check: ldd, ldconfig -p, LD_DEBUG=libs

col3_cards = [
    {
        "name": "libcuda",
        "lines": [
            ("libcuda.so.1: cannot open", False),
            ("shared object file", False)
        ]
    },
    {
        "name": "libnccl",
        "lines": [
            ("error while loading shared", False),
            ("libraries: libnccl.so.2", False)
        ]
    },
    {
        "name": "GLIBC",
        "lines": [
            ("version GLIBC_2.34", False),
            ("not found", False)
        ]
    },
    {
        "name": "GLIBCXX",
        "lines": [
            ("version GLIBCXX_3.4.30", False),
            ("not found", False)
        ]
    },
    {
        "name": "check 3",
        "lines": [
            ("ldd, ldconfig -p,", True),
            ("LD_DEBUG=libs", True)
        ]
    }
]

# Column 4 (Stage 6): width = 330
# Texts:
# 1. CUDA error: no kernel image is available for execution on the device
# 2. Illegal instruction (SIGILL, exit 132)
# 3. segfault exit 139
# First check: strace -f for the last failed call

col4_cards = [
    {
        "name": "CUDA error",
        "lines": [
            ("CUDA error: no kernel image", False),
            ("is available for execution", False),
            ("on the device", False)
        ]
    },
    {
        "name": "SIGILL",
        "lines": [
            ("Illegal instruction", False),
            ("(SIGILL, exit 132)", False)
        ]
    },
    {
        "name": "segfault",
        "lines": [
            ("segfault exit 139", False)
        ]
    },
    {
        "name": "check 4",
        "lines": [
            ("strace -f for the", True),
            ("last failed call", True)
        ]
    }
]

all_cols = [
    ("col1", col_widths["col1"], col1_cards),
    ("col2", col_widths["col2"], col2_cards),
    ("col3", col_widths["col3"], col3_cards),
    ("col4", col_widths["col4"], col4_cards)
]

print("=== CHECKING PADDINGS FOR ALL CARDS IN ALL COLUMNS ===")
all_pass = True
for col_name, w_col, cards in all_cols:
    print(f"\n--- {col_name} (width={w_col}) ---")
    for card in cards:
        print(f"Card: {card['name']}")
        for line, is_mono in card["lines"]:
            w = text_width(line, 24, is_mono)
            pad = (w_col - w) / 2
            ok = pad >= 16.0
            print(f"  '{line}': w={w:.1f}px, pad={pad:.1f}px -> {'PASS' if ok else 'FAIL'}")
            if not ok:
                all_pass = False

assert all_pass, "Some paddings failed!"
print("\nALL CARDS PASS STRICT >= 16px PADDING CHECK!")
