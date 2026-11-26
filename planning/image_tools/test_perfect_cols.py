# Test the balanced column widths and lines

def text_width(s, fs=24, is_mono=False):
    rate = 0.62 if is_mono else 0.60
    return len(s) * fs * rate

# Columns:
# Col 1: 320px (card_w = 290)
# Col 2: 460px (card_w = 430) -> fits /lib64/ld-linux-x86-64.so.2 (401.8px) with (430-401.8)/2 = 14.1px in mono, or in sans: (430-388.8)/2 = 20.6px!
# Wait! In Col 2, if card_w = 440: (440 - 401.8)/2 = 19.1px >= 16px in monospace!
# Col 3: 330px (card_w = 300)
# Col 4: 290px (card_w = 260)
# Sum of col widths: 320 + 470 + 330 + 280 = 1400px!
# 3 gaps of 40px = 120px!
# Total = 1520px!

col_widths = {
    "col1": 320,
    "col2": 470,
    "col3": 330,
    "col4": 280
}

card_widths = {
    "col1": 290,
    "col2": 440,
    "col3": 300,
    "col4": 250
}

cards_data = {
    "col1": [
        {
            "full": "Exec format error (wrong CPU architecture such as x86-64 on aarch64, or a script without shebang)",
            "lines": [
                ("Exec format error", False),
                ("(wrong CPU", False),
                ("architecture such as", False),
                ("x86-64 on aarch64, or", False),
                ("a script without", False),
                ("shebang)", False)
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
                ("bad ELF interpreter / not found for", False),
                ("a file that exists (glibc binary on", False),
                ("Alpine musl:", False),
                ("/lib64/ld-linux-x86-64.so.2", True),
                ("missing)", False)
            ]
        },
        {
            "full": "readelf -l | grep interpreter",
            "lines": [
                ("readelf -l | grep interpreter", True)
            ]
        }
    ],
    "col3": [
        {
            "full": "libcuda.so.1: cannot open shared object file",
            "lines": [
                ("libcuda.so.1: cannot", False),
                ("open shared", False),
                ("object file", False)
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
                ("version", False),
                ("GLIBC_2.34", False),
                ("not found", False)
            ]
        },
        {
            "full": "version GLIBCXX_3.4.30 not found",
            "lines": [
                ("version", False),
                ("GLIBCXX_3.4.30", False),
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
    card_w = card_widths[col_id]
    print(f"\n--- Column {col_id} (col_w={col_widths[col_id]}, card_w={card_w}) ---")
    for card in cards:
        reconstructed = " ".join(line for line, _ in card["lines"])
        if reconstructed.split() != card["full"].split():
            print(f"RECONSTRUCTION MISMATCH:")
            print(f"  Exp: '{card['full']}'")
            print(f"  Got: '{reconstructed}'")
            all_pass = False
        else:
            print(f"MATCH: '{card['full'][:45]}...'")
        
        for line, is_mono in card["lines"]:
            w = text_width(line, 24, is_mono)
            pad = (card_w - w) / 2
            ok = pad >= 16.0
            print(f"  '{line}': w={w:.1f}px, pad={pad:.1f}px -> {'PASS' if ok else 'FAIL'}")
            if not ok:
                all_pass = False

assert all_pass, "Checks failed!"
print("\nALL RECONSTRUCTIONS MATCH EXACTLY AND ALL PADDINGS >= 16px!")
