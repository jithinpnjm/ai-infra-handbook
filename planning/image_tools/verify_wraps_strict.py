# Test updated line wrapping for all 4 columns

def text_width(s, fs=24, is_mono=False):
    rate = 0.62 if is_mono else 0.60
    return len(s) * fs * rate

col_widths = {
    "col1": 360,
    "col2": 390,
    "col3": 350,
    "col4": 340
}

cards_data = {
    "col1": [
        {
            "full": "Exec format error (wrong CPU architecture such as x86-64 on aarch64, or a script without shebang)",
            "lines": [
                ("Exec format error", False),
                ("(wrong CPU architecture", False),
                ("such as x86-64 on", False),
                ("aarch64, or a script", False),
                ("without shebang)", False)
            ]
        },
        {
            "full": "exit 126 found but not executable",
            "lines": [
                ("exit 126 found", False),
                ("but not executable", False)
            ]
        },
        {
            "full": "exit 127 not found",
            "lines": [
                ("exit 127 not found", False)
            ]
        },
        {
            "full": "file and readelf -h",
            "lines": [
                ("file and readelf -h", True)
            ]
        }
    ],
    "col2": [
        {
            "full": "bad ELF interpreter / not found for a file that exists (glibc binary on Alpine musl: /lib64/ld-linux-x86-64.so.2 missing)",
            "lines": [
                ("bad ELF interpreter /", False),
                ("not found for a file", False),
                ("that exists", False),
                ("(glibc binary on", False),
                ("Alpine musl:", False),
                ("/lib64/", True),
                ("ld-linux-x86-64.so.2", True),
                ("missing)", False)
            ]
        },
        {
            "full": "readelf -l | grep interpreter",
            "lines": [
                ("readelf -l | grep", True),
                ("interpreter", True)
            ]
        }
    ],
    "col3": [
        {
            "full": "libcuda.so.1: cannot open shared object file",
            "lines": [
                ("libcuda.so.1:", True),
                ("cannot open", False),
                ("shared object file", False)
            ]
        },
        {
            "full": "error while loading shared libraries: libnccl.so.2",
            "lines": [
                ("error while loading", False),
                ("shared libraries:", False),
                ("libnccl.so.2", True)
            ]
        },
        {
            "full": "version GLIBC_2.34 not found",
            "lines": [
                ("version GLIBC_2.34", False),
                ("not found", False)
            ]
        },
        {
            "full": "version GLIBCXX_3.4.30 not found",
            "lines": [
                ("version GLIBCXX_3.4.30", False),
                ("not found", False)
            ]
        },
        {
            "full": "ldd, ldconfig -p, LD_DEBUG=libs",
            "lines": [
                ("ldd, ldconfig -p,", True),
                ("LD_DEBUG=libs", True)
            ]
        }
    ],
    "col4": [
        {
            "full": "CUDA error: no kernel image is available for execution on the device",
            "lines": [
                ("CUDA error: no", False),
                ("kernel image is", False),
                ("available for", False),
                ("execution on", False),
                ("the device", False)
            ]
        },
        {
            "full": "Illegal instruction (SIGILL, exit 132)",
            "lines": [
                ("Illegal instruction", False),
                ("(SIGILL, exit 132)", False)
            ]
        },
        {
            "full": "segfault exit 139",
            "lines": [
                ("segfault exit 139", False)
            ]
        },
        {
            "full": "strace -f for the last failed call",
            "lines": [
                ("strace -f for the", True),
                ("last failed call", True)
            ]
        }
    ]
}

print("=== CHECKING PADDINGS AND RECONSTRUCTIONS ===")
all_pass = True
for col_id, cards in cards_data.items():
    bw = col_widths[col_id]
    print(f"\n--- Column {col_id} (card box width: {bw - 30}) ---")
    card_w = bw - 30 # inside column container
    for card in cards:
        # Check text reconstruction
        reconstructed = " ".join(line for line, _ in card["lines"])
        # Compare token by token
        if reconstructed.split() != card["full"].split():
            print(f"RECONSTRUCTION MISMATCH:")
            print(f"  Exp: '{card['full']}'")
            print(f"  Got: '{reconstructed}'")
            all_pass = False
        else:
            print(f"MATCH: '{card['full'][:40]}...'")
        
        # Check padding
        for line, is_mono in card["lines"]:
            w = text_width(line, 24, is_mono)
            pad = (card_w - w) / 2
            ok = pad >= 16.0
            if not ok:
                print(f"  PAD FAIL in '{line}': w={w:.1f}px, pad={pad:.1f}px < 16 (card_w={card_w})")
                all_pass = False

assert all_pass, "Checks failed!"
print("\nALL RECONSTRUCTIONS MATCH EXACTLY AND ALL PADDINGS >= 16px!")
