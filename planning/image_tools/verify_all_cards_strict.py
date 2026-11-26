# Full card layout and padding tester for all 4 columns

def text_width(s, fs=24, is_mono=False):
    rate = 0.62 if is_mono else 0.60
    return len(s) * fs * rate

# 4 columns:
# Col 1: width 360, card width 320
# Col 2: width 340, card width 310
# Col 3: width 360, card width 320 (Orange)
# Col 4: width 340, card width 310

cards = {
    "col1": {
        "card_w": 320,
        "items": [
            {
                "full": "Exec format error (wrong CPU architecture such as x86-64 on aarch64, or a script without shebang)",
                "lines": [
                    ("Exec format error", False),
                    ("(wrong CPU", False),
                    ("architecture such", False),
                    ("as x86-64 on", False),
                    ("aarch64, or a script", False),
                    ("without shebang)", False)
                ]
            },
            {
                "full": "exit 126 found but not executable",
                "lines": [
                    ("exit 126 found but", False),
                    ("not executable", False)
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
        ]
    },
    "col2": {
        "card_w": 310,
        "items": [
            {
                "full": "bad ELF interpreter / not found for a file that exists (glibc binary on Alpine musl: /lib64/ld-linux-x86-64.so.2 missing)",
                "lines": [
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
            },
            {
                "full": "readelf -l | grep interpreter",
                "lines": [
                    ("readelf -l |", True),
                    ("grep interpreter", True)
                ]
            }
        ]
    },
    "col3": {
        "card_w": 320,
        "items": [
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
        ]
    },
    "col4": {
        "card_w": 310,
        "items": [
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
                    ("Illegal", False),
                    ("instruction", False),
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
}

print("=== CHECKING ALL COLUMNS AND CARDS ===")
all_pass = True
for col_id, col_data in cards.items():
    cw = col_data["card_w"]
    print(f"\n--- {col_id} (card width: {cw}) ---")
    for item in col_data["items"]:
        # Check text reconstruction
        # Handle the hyphen break in col2
        if col_id == "col2" and "/lib64/ld-linux-" in [l for l, _ in item["lines"]]:
            # Custom check for col2
            recon = ""
            for l, _ in item["lines"]:
                if l == "/lib64/ld-linux-":
                    recon += l
                elif l == "x86-64.so.2":
                    recon += l + " "
                else:
                    recon += l + " "
            recon = " ".join(recon.split())
        else:
            recon = " ".join(l for l, _ in item["lines"])
        
        if recon != item["full"]:
            print(f"MISMATCH in {item['full']}:")
            print(f"  Exp: '{item['full']}'")
            print(f"  Got: '{recon}'")
            all_pass = False
        else:
            print(f"PASS MATCH: '{item['full'][:40]}...'")
        
        # Check padding
        for line, is_mono in item["lines"]:
            w = text_width(line, 24, is_mono)
            pad = (cw - w) / 2
            ok = pad >= 16.0
            print(f"  '{line}': w={w:.1f}px, pad={pad:.1f}px [{'PASS' if ok else 'FAIL'}]")
            if not ok:
                all_pass = False

assert all_pass, "Checks failed!"
print("\nALL CARDS PASS STRICT FIDELITY AND >= 16px PADDING CHECKS!")
