# Layout analysis script
stages = [
    (1, "shell fork and execve"),
    (2, "kernel checks the file and picks a format handler"),
    (3, "ELF loader maps LOAD segments, builds the stack"),
    (4, "PT_INTERP: kernel maps ld.so, execution starts in the dynamic linker"),
    (5, "ld.so loads DT_NEEDED libraries, relocates, runs constructors"),
    (6, "_start, __libc_start_main, main"),
]

errors = {
    "Stage 1/2": [
        "Exec format error (wrong CPU architecture such as x86-64 on aarch64, or a script without shebang)",
        "exit 126 found but not executable",
        "exit 127 not found",
    ],
    "Stage 4": [
        "bad ELF interpreter / not found for a file that exists (glibc binary on Alpine musl: /lib64/ld-linux-x86-64.so.2 missing)",
    ],
    "Stage 5": [
        "libcuda.so.1: cannot open shared object file",
        "error while loading shared libraries: libnccl.so.2",
        "version GLIBC_2.34 not found",
        "version GLIBCXX_3.4.30 not found",
    ],
    "Stage 6 and after": [
        "CUDA error: no kernel image is available for execution on the device",
        "Illegal instruction (SIGILL, exit 132)",
        "segfault exit 139",
    ],
}

first_checks = {
    "Stage 1/2": "file and readelf -h",
    "Stage 4": "readelf -l | grep interpreter",
    "Stage 5": "ldd, ldconfig -p, LD_DEBUG=libs",
    "Stage 6 and after": "strace -f for the last failed call",
}

print("=== CHECKING ALL LABELS ===")
for s_num, s_text in stages:
    print(f"Stage {s_num}: {s_text}")

for grp, errs in errors.items():
    print(f"\nGroup: {grp}")
    for e in errs:
        print(f"  Err: {e}")
    print(f"  First check: {first_checks[grp]}")
