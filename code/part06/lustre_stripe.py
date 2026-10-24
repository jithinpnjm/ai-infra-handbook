#!/usr/bin/env python3
"""RAID0-style Lustre striping model: which OST holds which byte range, and what parallelism a request gets.

Layout (documented behaviour of 'raid0'): the file is cut into stripe_size chunks assigned round-robin to
stripe_count OST objects. Offset -> chunk = off // stripe_size -> stripe slot = chunk % stripe_count.
Also models a composite (PFL) layout given as components [(end_offset_or_None, count, size), ...].
"""
import sys


def slot(off, size, count):
    return (off // size) % count


def per_ost_bytes(file_size, size, count):
    per = [0] * count
    off = 0
    while off < file_size:
        n = min(size, file_size - off)
        per[slot(off, size, count)] += n
        off += n
    return per


def request_osts(off, length, size, count):
    """OST slots touched by a read/write of [off, off+length)."""
    s = set()
    cur = off
    while cur < off + length:
        s.add(slot(cur, size, count))
        cur = (cur // size + 1) * size
    return sorted(s)


def pfl_layout(file_size, components):
    """components: list of (end, count, size); returns [(start, end, count, size)] clipped to file size."""
    out, start = [], 0
    for end, count, size in components:
        e = file_size if end is None else min(end, file_size)
        if e > start:
            out.append((start, e, count, size))
        start = e
        if start >= file_size:
            break
    return out


if __name__ == "__main__":
    MiB = 1 << 20
    print("1 GiB file, stripe_size 1 MiB, stripe_count 4: bytes per OST object (MiB)")
    print([b // MiB for b in per_ost_bytes(1024 * MiB, MiB, 4)])
    print("First 8 chunks -> OST slot:", [slot(i * MiB, MiB, 4) for i in range(8)])
    print("A 3 MiB read at offset 2.5 MiB touches slots:", request_osts(int(2.5 * MiB), 3 * MiB, MiB, 4))
    print("A 512 KiB read at offset 0 touches slots:", request_osts(0, MiB // 2, MiB, 4), "(one OST: small I/O does not parallelise)")
    comps = [(4 * MiB, 1, MiB), (64 * MiB, 4, MiB), (None, 16, 4 * MiB)]   # like: -E 4M -c 1 -E 64M -c 4 -E -1 -c 16 -S 4M
    print("\nPFL layout for a 1 GiB file:")
    for st, en, c, sz in pfl_layout(1024 * MiB, comps):
        print(f"  [{st // MiB:>5} MiB, {en // MiB:>5} MiB)  stripe_count={c:<3} stripe_size={sz // MiB} MiB")
