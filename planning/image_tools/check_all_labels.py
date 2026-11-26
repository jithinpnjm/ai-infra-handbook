all_labels = [
    # Title
    "Which startup stage produced this error message",
    # Stages
    "shell fork and execve",
    "kernel checks the file and picks a format handler",
    "ELF loader maps LOAD segments, builds the stack",
    "PT_INTERP: kernel maps ld.so, execution starts in the dynamic linker",
    "ld.so loads DT_NEEDED libraries, relocates, runs constructors",
    "_start, __libc_start_main, main",
    # Errors
    "Exec format error (wrong CPU architecture such as x86-64 on aarch64, or a script without shebang)",
    "exit 126 found but not executable",
    "exit 127 not found",
    "bad ELF interpreter / not found for a file that exists (glibc binary on Alpine musl: /lib64/ld-linux-x86-64.so.2 missing)",
    "libcuda.so.1: cannot open shared object file",
    "error while loading shared libraries: libnccl.so.2",
    "version GLIBC_2.34 not found",
    "version GLIBCXX_3.4.30 not found",
    "CUDA error: no kernel image is available for execution on the device",
    "Illegal instruction (SIGILL, exit 132)",
    "segfault exit 139",
    # First checks
    "file and readelf -h",
    "readelf -l | grep interpreter",
    "ldd, ldconfig -p, LD_DEBUG=libs",
    "strace -f for the last failed call"
]

print(f"Total labels: {len(all_labels)}")
for i, l in enumerate(all_labels, 1):
    print(f"{i:2d}. {l}")
