# Let's see what happens if there are 6 columns:
# Col 1: Stage 1
# Col 2: Stage 2
# Col 3: Stage 3
# Col 4: Stage 4
# Col 5: Stage 5
# Col 6: Stage 6

# But wait! Where do the error messages go if there are 6 columns?
# The errors are:
# Stage 1/2:
#   - Exec format error (wrong CPU architecture such as x86-64 on aarch64, or a script without shebang)
#   - exit 126 found but not executable
#   - exit 127 not found
# Stage 4:
#   - bad ELF interpreter / not found for a file that exists (glibc binary on Alpine musl: /lib64/ld-linux-x86-64.so.2 missing)
# Stage 5:
#   - libcuda.so.1: cannot open shared object file
#   - error while loading shared libraries: libnccl.so.2
#   - version GLIBC_2.34 not found
#   - version GLIBCXX_3.4.30 not found
# Stage 6 and after:
#   - CUDA error: no kernel image is available for execution on the device
#   - Illegal instruction (SIGILL, exit 132)
#   - segfault exit 139

# And first check lines:
# - file and readelf -h
# - readelf -l | grep interpreter
# - ldd, ldconfig -p, LD_DEBUG=libs
# - strace -f for the last failed call

print("Total error groups: 4")
print("Total first checks: 4")
