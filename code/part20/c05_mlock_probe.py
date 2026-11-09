#!/usr/bin/env python3
"""Find how much memory this process may pin (mlock) before the kernel says no.

CUDA pinned host memory is page-locked memory. An unprivileged process may lock only
RLIMIT_MEMLOCK bytes. mlock(2): ENOMEM means the limit was exceeded, EPERM means the
caller lacked CAP_IPC_LOCK. A process with CAP_IPC_LOCK is not limited, so run this
as a normal user or in a container without that capability.
Usage: python3 c05_mlock_probe.py [MiB MiB ...]
"""
import ctypes
import errno
import mmap
import resource
import sys

MIB = 1024 * 1024


def probe(sizes_mib, try_lock):
    """try_lock(size_bytes) returns 0 on success or an errno. Stops at the first failure."""
    result = []
    for size in sizes_mib:
        code = try_lock(size * MIB)
        result.append((size, errno.errorcode.get(code, "OK") if code else "OK"))
        if code:
            break
    return result


def real_lock(size):
    libc = ctypes.CDLL(None, use_errno=True)
    libc.mlock.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
    region = mmap.mmap(-1, size)
    address = ctypes.addressof(ctypes.c_char.from_buffer(region))
    ok = libc.mlock(address, size) == 0
    code = 0 if ok else ctypes.get_errno()
    if ok:
        libc.munlock(address, size)
    region.close()
    return code


if __name__ == "__main__":
    soft, hard = resource.getrlimit(resource.RLIMIT_MEMLOCK)
    print("RLIMIT_MEMLOCK soft=%s hard=%s (bytes, -1 = unlimited)" % (
        soft if soft != resource.RLIM_INFINITY else -1,
        hard if hard != resource.RLIM_INFINITY else -1))
    wanted = [int(x) for x in sys.argv[1:]] or [1, 8, 64, 512]
    for size, outcome in probe(wanted, real_lock):
        print("mlock %5d MiB -> %s" % (size, outcome))
