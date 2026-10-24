#!/usr/bin/env python3
"""Tiny storage micro-benchmark: sequential bandwidth, random 4 KiB reads, and metadata rates.
Run it in a directory on the file system you want to characterise (home, scratch, /tmp).
Caches matter: sizes here are small; use --mb 4096 or more on real systems and drop caches/remount between phases."""
import argparse
import os
import random
import tempfile
import time

ap = argparse.ArgumentParser()
ap.add_argument("--dir", default=tempfile.gettempdir())
ap.add_argument("--mb", type=int, default=512, help="size of the big file")
ap.add_argument("--files", type=int, default=20000, help="number of small files")
a = ap.parse_args()
root = tempfile.mkdtemp(dir=a.dir, prefix="iomix-")
big = os.path.join(root, "big.bin")
blk = os.urandom(1 << 20)

t = time.perf_counter()
with open(big, "wb") as f:
    for _ in range(a.mb):
        f.write(blk)
    f.flush()
    os.fsync(f.fileno())
w = time.perf_counter() - t
t = time.perf_counter()
with open(big, "rb") as f:
    while f.read(1 << 20):
        pass
r = time.perf_counter() - t
print(f"sequential write {a.mb / w:8.0f} MB/s (fsync'd)   read {a.mb / r:8.0f} MB/s (likely cached)")

n = 20000
size = os.path.getsize(big)
t = time.perf_counter()
with open(big, "rb", buffering=0) as f:
    for _ in range(n):
        f.seek(random.randrange(0, size - 4096) & ~4095)
        f.read(4096)
rr = time.perf_counter() - t
print(f"random 4 KiB read {n / rr:10.0f} IOPS (likely cached)")

d = os.path.join(root, "small")
os.mkdir(d)
t = time.perf_counter()
for i in range(a.files):
    with open(os.path.join(d, f"f{i}"), "wb") as f:
        f.write(b"x" * 100)
c = time.perf_counter() - t
t = time.perf_counter()
for i in range(a.files):
    os.stat(os.path.join(d, f"f{i}"))
s = time.perf_counter() - t
t = time.perf_counter()
for i in range(a.files):
    os.unlink(os.path.join(d, f"f{i}"))
u = time.perf_counter() - t
print(f"create {a.files / c:9.0f} files/s   stat {a.files / s:9.0f}/s   unlink {a.files / u:9.0f}/s")
os.unlink(big)
os.rmdir(d)
os.rmdir(root)
