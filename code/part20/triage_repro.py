#!/usr/bin/env python3
"""Make a small, bounded, self-cleaning load so you can practise the 60 seconds.

Usage:
  triage_repro.py cpu  [--procs N] [--seconds S]   busy loops, default 2 per CPU
  triage_repro.py disk [--mb M] [--seconds S]      fsync'd writes to a temp file
  triage_repro.py mem  [--mb M] [--seconds S]      hold M MB of touched memory
Run it in one terminal and the checklist in another. Ctrl-C stops it.
"""
import argparse
import multiprocessing as mp
import os
import tempfile
import time

MAX_MB = 2048  # refuse anything bigger: this is a drill, not a stress test


def _spin(deadline):
    while time.monotonic() < deadline:
        pass


def cpu(procs, seconds):
    deadline = time.monotonic() + seconds
    workers = [mp.Process(target=_spin, args=(deadline,)) for _ in range(procs)]
    for w in workers:
        w.start()
    for w in workers:
        w.join()
    return procs


def disk(mb, seconds):
    deadline, written = time.monotonic() + seconds, 0
    chunk = os.urandom(1024 * 1024)
    fd, path = tempfile.mkstemp(prefix="triage_disk_")
    try:
        while written < mb and time.monotonic() < deadline:
            os.write(fd, chunk)
            os.fsync(fd)
            written += 1
    finally:
        os.close(fd)
        os.unlink(path)
    return written


def mem(mb, seconds):
    block = bytearray(mb * 1024 * 1024)
    for i in range(0, len(block), 4096):
        block[i] = 1  # touch every page so it is really resident
    time.sleep(seconds)
    return len(block) // (1024 * 1024)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("cpu")
    c.add_argument("--procs", type=int, default=2 * (os.cpu_count() or 1))
    c.add_argument("--seconds", type=float, default=90)
    d = sub.add_parser("disk")
    d.add_argument("--mb", type=int, default=512)
    d.add_argument("--seconds", type=float, default=60)
    m = sub.add_parser("mem")
    m.add_argument("--mb", type=int, default=256)
    m.add_argument("--seconds", type=float, default=60)
    a = ap.parse_args(argv)
    if getattr(a, "mb", 0) > MAX_MB:
        ap.error(f"--mb above {MAX_MB} refused")
    if a.cmd == "cpu":
        return cpu(a.procs, a.seconds)
    if a.cmd == "disk":
        return disk(a.mb, a.seconds)
    return mem(a.mb, a.seconds)


if __name__ == "__main__":
    print("done:", main())
